"""
OCR Client Integration

Provides integration with Tesseract OCR for text extraction
from invoice images with preprocessing and enhancement.
"""

import io
import tempfile
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import pytesseract
from PIL import Image
from pytesseract import TesseractError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OCRClient:
    """
    Client for OCR text extraction using Tesseract

    Handles image preprocessing, text extraction, and confidence scoring
    for invoice processing.
    """

    def __init__(self):
        """Initialize Tesseract OCR client"""
        # Configure Tesseract path if specified
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH

        # Verify Tesseract is available
        try:
            version = pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized", version=str(version))
        except Exception as e:
            logger.error("Failed to initialize Tesseract", error=str(e))
            raise

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy

        Args:
            image_path: Path to input image

        Returns:
            np.ndarray: Preprocessed image array

        Preprocessing steps:
        1. Convert to grayscale
        2. Apply noise reduction
        3. Enhance contrast
        4. Apply threshold/binarization
        5. Deskew if needed
        """
        logger.debug("Starting image preprocessing", image=image_path)

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Apply noise reduction
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        # Enhance contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)

        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        # Deskew image
        deskewed = self._deskew(thresh)

        logger.debug("Image preprocessing completed")
        return deskewed

    def _deskew(self, image: np.ndarray) -> np.ndarray:
        """
        Deskew image by detecting text angle

        Args:
            image: Input image array

        Returns:
            np.ndarray: Deskewed image
        """
        # Find contours
        contours, _ = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return image

        # Get the minimum area rectangle
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        largest_contour = contours[0]

        min_area_rect = cv2.minAreaRect(largest_contour)
        angle = min_area_rect[-1]

        # Handle angle > 45 degrees
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle

        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        return rotated

    def extract_text(
        self,
        image_path: str,
        preprocess: bool = True,
        config: str = "--psm 6",
    ) -> tuple[str, float]:
        """
        Extract text from image using Tesseract OCR

        Args:
            image_path: Path to input image
            preprocess: Whether to preprocess image first
            config: Tesseract configuration string

        Returns:
            tuple: (extracted_text, confidence_score)

        Tesseract configuration options:
        --psm 6: Assume a single uniform block of text
        --oem 3: Use both legacy and LSTM OCR engines
        """
        try:
            # Preprocess image if requested
            if preprocess:
                processed_image = self.preprocess_image(image_path)

                # Save processed image to temp file
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    temp_path = tmp.name
                    cv2.imwrite(temp_path, processed_image)
                    image_to_process = temp_path
            else:
                image_to_process = image_path

            # Extract text with confidence data
            logger.debug("Extracting text with Tesseract", image=image_path)

            data = pytesseract.image_to_data(
                Image.open(image_to_process),
                lang=settings.TESSERACT_LANG,
                config=config,
                output_type=pytesseract.Output.DICT
            )

            # Extract text and calculate confidence
            text_parts = []
            confidences = []

            for i, text in enumerate(data["text"]):
                if text.strip():
                    text_parts.append(text)
                    conf = int(data["conf"][i])
                    if conf > 0:  # Only consider valid confidences
                        confidences.append(conf)

            extracted_text = "\n".join(text_parts)

            # Calculate average confidence (0-100 scale)
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
            else:
                avg_confidence = 0.0

            # Clean up temp file
            if preprocess:
                Path(image_to_process).unlink(missing_ok=True)

            logger.info(
                "Text extraction completed",
                text_length=len(extracted_text),
                confidence=avg_confidence,
            )

            return extracted_text, avg_confidence

        except TesseractError as e:
            logger.error("Tesseract OCR failed", error=str(e))
            raise ValueError(f"OCR processing failed: {str(e)}")
        except Exception as e:
            logger.error("Image processing failed", error=str(e))
            raise

    def validate_image_quality(self, image_path: str) -> dict:
        """
        Validate image quality before OCR processing

        Args:
            image_path: Path to input image

        Returns:
            dict: Validation result with status and issues

        Checks:
        - File exists and is readable
        - Image resolution is sufficient (> 800x600)
        - Image format is supported
        - File size is reasonable (< 10MB)
        """
        issues = []

        try:
            # Check if file exists
            if not Path(image_path).exists():
                return {"status": "invalid", "issues": ["File not found"]}

            # Check file size
            file_size = Path(image_path).stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB
                issues.append("File size exceeds 10MB")

            # Load and check image
            image = Image.open(image_path)

            # Check resolution
            width, height = image.size
            if width < 800 or height < 600:
                issues.append(f"Image resolution too low: {width}x{height}. Minimum: 800x600")

            # Check format
            if image.format not in ["JPEG", "PNG", "JPG"]:
                issues.append(f"Unsupported format: {image.format}. Use JPEG or PNG")

            if issues:
                return {"status": "warning", "issues": issues}
            else:
                return {"status": "valid", "issues": []}

        except Exception as e:
            logger.error("Image validation failed", error=str(e))
            return {"status": "error", "issues": [str(e)]}

    async def extract_text_async(
        self,
        image_path: str,
        preprocess: bool = True,
    ) -> tuple[str, float]:
        """
        Async wrapper for text extraction

        Args:
            image_path: Path to input image
            preprocess: Whether to preprocess image

        Returns:
            tuple: (extracted_text, confidence_score)
        """
        # Run OCR in thread pool to avoid blocking
        import asyncio

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.extract_text(image_path, preprocess)
        )
