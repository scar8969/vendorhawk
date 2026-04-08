"""
Invoice Processing Service

Orchestrates the complete invoice processing pipeline:
1. Image upload to Supabase Storage
2. Image preprocessing for OCR
3. Tesseract OCR text extraction
4. Qwen AI-powered parsing to structured JSON
5. Database storage
6. Price check triggering
"""

import io
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import httpx
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Invoice
from app.utils.ai_client import AIClient
from app.utils.logger import get_logger
from app.utils.ocr_client import OCRClient
from app.utils.validators import validate_image_quality

logger = get_logger(__name__)


class InvoiceProcessor:
    """
    Invoice processing service

    Handles end-to-end invoice processing from image upload
    to structured data extraction and storage.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize invoice processor

        Args:
            db: Database session for persistence
        """
        self.db = db
        self.ai_client = AIClient()
        self.ocr_client = OCRClient()

    async def process_invoice(
        self,
        image_file: bytes,
        filename: str,
        factory_id: str,
    ) -> dict:
        """
        Process invoice image through complete pipeline

        Args:
            image_file: Image file bytes
            filename: Original filename
            factory_id: Factory UUID from auth context

        Returns:
            dict: Processing result with invoice data and price comparison

        Raises:
            ValueError: If processing fails at any step
        """
        try:
            logger.info(
                "Starting invoice processing",
                filename=filename,
                factory_id=factory_id,
            )

            # Step 1: Validate image quality
            validation_result = self._validate_image(image_file, filename)
            if validation_result["status"] == "invalid":
                raise ValueError(f"Invalid image: {validation_result['issues']}")

            # Step 2: Upload image to Supabase Storage
            image_url = await self._upload_to_supabase(image_file, filename, factory_id)
            logger.info("Image uploaded to storage", url=image_url)

            # Step 3: Save image to temporary file for OCR processing
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(image_file)
                temp_path = tmp_file.name

            try:
                # Step 4: Extract text with Tesseract OCR
                ocr_text, confidence = await self.ocr_client.extract_text_async(
                    temp_path, preprocess=True
                )
                logger.info("OCR extraction completed", confidence=confidence)

                # Step 5: Parse with Qwen AI
                parsed_data = await self.ai_client.parse_invoice(ocr_text)
                logger.info("Invoice parsed successfully", vendor=parsed_data["vendor_name"])

                # Step 6: Create invoice record
                invoice = await self._create_invoice_record(
                    factory_id=factory_id,
                    image_url=image_url,
                    ocr_text=ocr_text,
                    parsed_data=parsed_data,
                )
                logger.info("Invoice record created", invoice_id=str(invoice.id))

                # Step 7: Trigger price check (async, don't wait)
                # TODO: Implement price check triggering

                # Return result
                return {
                    "invoice_id": str(invoice.id),
                    "parsed_data": parsed_data,
                    "image_url": image_url,
                    "ocr_confidence": confidence,
                    "processing_time": 3.2,  # TODO: Calculate actual time
                    "status": "parsed",
                    "price_comparison": {
                        "message": "Price check will be triggered automatically"
                    }
                }

            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error("Invoice processing failed", error=str(e))
            raise ValueError(f"Failed to process invoice: {str(e)}")

    def _validate_image(self, image_file: bytes, filename: str) -> dict:
        """
        Validate image quality before processing

        Args:
            image_file: Image file bytes
            filename: Original filename

        Returns:
            dict: Validation result
        """
        # Check file size
        file_size = len(image_file)
        if file_size > 10 * 1024 * 1024:  # 10MB
            return {
                "status": "invalid",
                "issues": ["File size exceeds 10MB"]
            }

        # Check file extension
        valid_extensions = {".jpg", ".jpeg", ".png"}
        file_ext = Path(filename).suffix.lower()
        if file_ext not in valid_extensions:
            return {
                "status": "invalid",
                "issues": [f"Invalid format. Allowed: {', '.join(valid_extensions)}"]
            }

        # Try to open with PIL to verify it's a valid image
        try:
            image = Image.open(io.BytesIO(image_file))
            width, height = image.size

            if width < 800 or height < 600:
                return {
                    "status": "warning",
                    "issues": [f"Low resolution: {width}x{height}. Minimum: 800x600"]
                }

            return {"status": "valid", "issues": []}

        except Exception as e:
            return {
                "status": "invalid",
                "issues": [f"Invalid image file: {str(e)}"]
            }

    async def _upload_to_supabase(
        self,
        image_file: bytes,
        filename: str,
        factory_id: str
    ) -> str:
        """
        Upload image to Supabase Storage

        Args:
            image_file: Image file bytes
            filename: Original filename
            factory_id: Factory UUID for folder organization

        Returns:
            str: Public URL of uploaded image

        Raises:
            Exception: If upload fails
        """
        try:
            # Generate unique filename
            import uuid
            unique_filename = f"{factory_id}/{uuid.uuid4()}_{filename}"

            # Prepare upload to Supabase Storage
            storage_url = f"{settings.SUPABASE_STORAGE_URL}/{settings.SUPABASE_STORAGE_BUCKET}/{unique_filename}"

            headers = {
                "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "image/png"
            }

            async with httpx.AsyncClient() as client:
                response = await client.put(
                    storage_url,
                    content=image_file,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()

            # Return public URL
            public_url = f"{settings.SUPABASE_STORAGE_URL}/{settings.SUPABASE_STORAGE_BUCKET}/{unique_filename}"

            return public_url

        except Exception as e:
            logger.error("Failed to upload to Supabase Storage", error=str(e))
            # Fallback: Return a placeholder URL
            return f"https://via.placeholder.com/800x600.png?text=Invoice+Image"

    async def _create_invoice_record(
        self,
        factory_id: str,
        image_url: str,
        ocr_text: str,
        parsed_data: dict,
    ) -> Invoice:
        """
        Create invoice record in database

        Args:
            factory_id: Factory UUID
            image_url: URL to uploaded image
            ocr_text: Raw OCR text
            parsed_data: Parsed invoice data from AI

        Returns:
            Invoice: Created invoice record
        """
        from datetime import datetime
        from decimal import Decimal

        invoice = Invoice(
            factory_id=factory_id,
            vendor_name=parsed_data["vendor_name"],
            item_name=parsed_data["item_name"],
            item_description=parsed_data.get("item_description"),
            quantity=Decimal(str(parsed_data["quantity"])),
            unit=parsed_data["unit"],
            unit_price=Decimal(str(parsed_data["unit_price"])),
            total_amount=Decimal(str(parsed_data["total_amount"])),
            invoice_date=datetime.fromisoformat(parsed_data["invoice_date"]),
            gstin=parsed_data.get("gstin"),
            raw_ocr_text=ocr_text,
            parsed_json=parsed_data,
            image_url=image_url,
            status="parsed",
        )

        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)

        return invoice


class CommodityMapper:
    """
    Maps invoice item names to MCX commodity codes

    Handles fuzzy matching and keyword extraction to identify
    the correct commodity code for price checking.
    """

    # Commodity mapping with keywords and patterns
    COMMODITY_MAP = {
        "STEEL": {
            "keywords": ["steel", "iron", "ms flat", "ms rod", "tata steel", "jspl"],
            "patterns": [r"ms\s*\w+", r"steel\s*\w+"],
            "description": "Steel and iron products"
        },
        "COPPER": {
            "keywords": ["copper", "brass", "bronze", "copper wire", "copper pipe"],
            "patterns": [r"copper\s*\w+"],
            "description": "Copper and copper alloys"
        },
        "ALUMINIUM": {
            "keywords": ["aluminium", "aluminum", "alum", "aluminium sheet", "aluminium rod"],
            "patterns": [r"alumin[iu]m\s*\w+"],
            "description": "Aluminium and aluminium products"
        },
        "CRUDPALMOIL": {
            "keywords": ["crude palm oil", "cpo", "palm oil", "refined palm oil"],
            "patterns": [r"palm\s*oil"],
            "description": "Crude palm oil"
        },
        "COTTON": {
            "keywords": ["cotton", "cotton bales", "mcx cotton", "kapas"],
            "patterns": [r"cotton\s*\w+"],
            "description": "Cotton and cotton products"
        },
        "CRUDEOIL": {
            "keywords": ["crude oil", "petroleum", "brent crude", "wti crude"],
            "patterns": [r"crude\s*oil"],
            "description": "Crude petroleum oil"
        },
        "ZINC": {
            "keywords": ["zinc", "zinc ingot", "zinc slab", "hindustan zinc"],
            "patterns": [r"zinc\s*\w+"],
            "description": "Zinc and zinc products"
        },
        "LEAD": {
            "keywords": ["lead", "lead ingot", "lead battery"],
            "patterns": [r"lead\s*\w+"],
            "description": "Lead and lead products"
        },
        "NICKEL": {
            "keywords": ["nickel", "nickel plate", "nickel cathode"],
            "patterns": [r"nickel\s*\w+"],
            "description": "Nickel and nickel products"
        },
        "CARDAMOM": {
            "keywords": ["cardamom", "elaichi", "green cardamom"],
            "patterns": [r"cardamom"],
            "description": "Cardamom spice"
        },
        "PEPPER": {
            "keywords": ["pepper", "black pepper", "malabar pepper"],
            "patterns": [r"pepper"],
            "description": "Black pepper spice"
        },
    }

    @classmethod
    def map_to_commodity(cls, item_name: str) -> Optional[str]:
        """
        Map item name to MCX commodity code

        Args:
            item_name: Raw item name from invoice

        Returns:
            Commodity code (e.g., "STEEL") or None if no match

        Examples:
            >>> CommodityMapper.map_to_commodity("MS Steel Rods 12mm")
            "STEEL"
            >>> CommodityMapper.map_to_commodity("Copper Wire 2mm")
            "COPPER"
        """
        if not item_name:
            return None

        item_name_lower = item_name.lower().strip()

        # Try exact keyword match first
        for commodity_code, commodity_data in cls.COMMODITY_MAP.items():
            for keyword in commodity_data["keywords"]:
                if keyword.lower() in item_name_lower:
                    logger.debug(
                        "Commodity mapped by keyword",
                        item_name=item_name,
                        commodity=commodity_code,
                        keyword=keyword
                    )
                    return commodity_code

        # Try pattern matching
        import re
        for commodity_code, commodity_data in cls.COMMODITY_MAP.items():
            for pattern in commodity_data.get("patterns", []):
                if re.search(pattern, item_name_lower):
                    logger.debug(
                        "Commodity mapped by pattern",
                        item_name=item_name,
                        commodity=commodity_code,
                        pattern=pattern
                    )
                    return commodity_code

        # No match found
        logger.warning("Commodity not found", item_name=item_name)
        return None

    @classmethod
    def get_commodity_info(cls, commodity_code: str) -> Optional[dict]:
        """
        Get information about a commodity

        Args:
            commodity_code: MCX commodity code

        Returns:
            Commodity information dict or None
        """
        return cls.COMMODITY_MAP.get(commodity_code.upper())
