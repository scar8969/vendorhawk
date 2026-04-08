"""
Invoice Management API

Handles invoice upload, processing, and retrieval.
"""

from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.utils.database import get_db
from app.utils.logger import get_logger

router = APIRouter(prefix="/invoices", tags=["invoices"])
limiter = Limiter(key_func=get_remote_address)
logger = get_logger(__name__)


@router.post("/upload")
@limiter.limit("10/minute")
async def upload_invoice(
    file: UploadFile = File(...),
    factory_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process invoice image

    Flow:
    1. Validate image file
    2. Upload to Supabase Storage
    3. Extract text with Tesseract OCR
    4. Parse with Qwen AI
    5. Store in database
    6. Trigger price check
    7. Return parsed data with price comparison

    Args:
        file: Invoice image file (JPEG/PNG, max 10MB)
        factory_id: Factory UUID (from auth context in production)

    Returns:
        InvoiceUploadResponse with parsed data and price comparison

    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        logger.info("Invoice upload requested", filename=file.filename, factory_id=factory_id)

        # TODO: Implement invoice processing
        # This will be implemented in Phase 2 of development

        return {
            "message": "Invoice upload endpoint - to be implemented",
            "filename": file.filename,
            "factory_id": factory_id,
            "status": "pending_implementation"
        }

    except Exception as e:
        logger.error("Invoice upload failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get invoice details by ID

    Returns complete invoice data including:
    - Parsed invoice information
    - Price check results
    - Negotiation status (if applicable)

    Args:
        invoice_id: Invoice UUID

    Returns:
        InvoiceResponse with complete invoice data

    Raises:
        HTTPException: If invoice not found
    """
    try:
        logger.info("Get invoice requested", invoice_id=invoice_id)

        # TODO: Implement invoice retrieval
        return {
            "message": "Get invoice endpoint - to be implemented",
            "invoice_id": invoice_id,
            "status": "pending_implementation"
        }

    except Exception as e:
        logger.error("Get invoice failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")


@router.get("/factory/{factory_id}")
@limiter.limit("60/minute")
async def get_factory_invoices(
    factory_id: str,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of factory invoices

    Returns invoices for a factory with optional filters:
    - Status filter (processing/parsed/negotiating/completed)
    - Pagination support
    - Sorted by creation date (newest first)

    Args:
        factory_id: Factory UUID
        skip: Number of records to skip (for pagination)
        limit: Records per page (max 100)
        status: Optional status filter

    Returns:
        Paginated list of invoices

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        logger.info("Get factory invoices requested", factory_id=factory_id, skip=skip, limit=limit)

        # TODO: Implement factory invoices retrieval
        return {
            "message": "Get factory invoices endpoint - to be implemented",
            "factory_id": factory_id,
            "skip": skip,
            "limit": limit,
            "status": status,
            "invoices": []
        }

    except Exception as e:
        logger.error("Get factory invoices failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Retrieval failed: {str(e)}")
