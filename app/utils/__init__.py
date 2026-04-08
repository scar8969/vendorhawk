"""
Utility modules for ProcureAI

Provides shared utilities for logging, database operations,
AI client integration, OCR processing, and data validation.
"""

from app.utils.logger import get_logger
from app.utils.database import get_db, init_db
from app.utils.ai_client import AIClient
from app.utils.ocr_client import OCRClient
from app.utils.validators import validate_phone_number, validate_email

__all__ = [
    "get_logger",
    "get_db",
    "init_db",
    "AIClient",
    "OCRClient",
    "validate_phone_number",
    "validate_email",
]
