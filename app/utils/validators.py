"""
Input Validation Utilities

Provides validation functions for common input types including
phone numbers, email addresses, and business identifiers.
"""

import re
from typing import Optional

from app.utils.logger import get_logger

logger = get_logger(__name__)


# Indian phone number validation
# Format: +91XXXXXXXXXX or 0XXXXXXXXXX
INDIAN_PHONE_PATTERN = re.compile(
    r"^(\+91|0)?[6-9]\d{9}$"
)

# Email validation pattern
EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)

# GSTIN validation pattern (Indian GST identification number)
# Format: 22AAAAA0000A1Z5 (22 characters)
GSTIN_PATTERN = re.compile(
    r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[A-Z0-9]{1}[Z]{1}[A-Z0-9]{1}$"
)

# Udyam Registration Number pattern
UDYAM_PATTERN = re.compile(
    r"^[A-Z]{2}[0-9]{2}[A-Z]{4}[0-9]{6}$"
)


def validate_phone_number(phone: str) -> tuple[bool, Optional[str]]:
    """
    Validate Indian phone number

    Args:
        phone: Phone number string

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_phone_number("+919876543210")
        (True, None)
        >>> validate_phone_number("9876543210")
        (True, None)
        >>> validate_phone_number("1234567890")
        (False, "Invalid phone number format")
    """
    if not phone:
        return False, "Phone number is required"

    # Remove spaces and dashes
    cleaned_phone = phone.replace(" ", "").replace("-", "")

    if not INDIAN_PHONE_PATTERN.match(cleaned_phone):
        return False, "Invalid Indian phone number format. Use +91XXXXXXXXXX or 0XXXXXXXXXX"

    return True, None


def validate_email(email: str) -> tuple[bool, Optional[str]]:
    """
    Validate email address

    Args:
        email: Email address string

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_email("user@example.com")
        (True, None)
        >>> validate_email("invalid-email")
        (False, "Invalid email format")
    """
    if not email:
        return False, "Email is required"

    if not EMAIL_PATTERN.match(email):
        return False, "Invalid email format"

    return True, None


def validate_gstin(gstin: str) -> tuple[bool, Optional[str]]:
    """
    Validate GST Identification Number (GSTIN)

    Args:
        gstin: GSTIN string

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_gstin("22AAAAA0000A1Z5")
        (True, None)
        >>> validate_gstin("INVALID")
        (False, "Invalid GSTIN format")
    """
    if not gstin:
        return True, None  # GSTIN is optional

    gstin = gstin.upper().strip()

    if not GSTIN_PATTERN.match(gstin):
        return False, "Invalid GSTIN format. Expected: 22AAAAA0000A1Z5"

    # Additional validation: Check checksum
    # (This is a simplified version - full validation requires mod-36 checksum)
    return True, None


def validate_udyam_number(udyam: str) -> tuple[bool, Optional[str]]:
    """
    Validate Udyam Registration Number

    Args:
        udyam: Udyam registration number

    Returns:
        tuple: (is_valid, error_message)
    """
    if not udyam:
        return True, None  # Udyam number is optional

    udyam = udyam.upper().strip()

    if not UDYAM_PATTERN.match(udyam):
        return False, "Invalid Udyam number format. Expected: XX####123456"

    return True, None


def validate_commodity_code(code: str) -> tuple[bool, Optional[str]]:
    """
    Validate MCX commodity code

    Args:
        code: Commodity code

    Returns:
        tuple: (is_valid, error_message)

    Valid codes: STEEL, COPPER, ALUMINIUM, CRUDPALMOIL, COTTON,
                CRUDEOIL, ZINC, LEAD, NICKEL, CARDAMOM, PEPPER
    """
    valid_codes = {
        "STEEL", "COPPER", "ALUMINIUM", "CRUDPALMOIL",
        "COTTON", "CRUDEOIL", "ZINC", "LEAD", "NICKEL",
        "CARDAMOM", "PEPPER"
    }

    if not code:
        return False, "Commodity code is required"

    if code.upper() not in valid_codes:
        return False, f"Invalid commodity code. Valid codes: {', '.join(sorted(valid_codes))}"

    return True, None


def validate_image_file(filename: str, max_size_mb: int = 10) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded image file

    Args:
        filename: Name of uploaded file
        max_size_mb: Maximum file size in MB

    Returns:
        tuple: (is_valid, error_message)
    """
    if not filename:
        return False, "Filename is required"

    # Check file extension
    valid_extensions = {".jpg", ".jpeg", ".png"}
    file_ext = Path(filename).suffix.lower()

    if file_ext not in valid_extensions:
        return False, f"Invalid file format. Allowed: {', '.join(valid_extensions)}"

    return True, None


def validate_quantity(quantity: float) -> tuple[bool, Optional[str]]:
    """
    Validate quantity value

    Args:
        quantity: Quantity value

    Returns:
        tuple: (is_valid, error_message)
    """
    if quantity is None:
        return False, "Quantity is required"

    if quantity <= 0:
        return False, "Quantity must be positive"

    if quantity > 1000000:  # Reasonable upper limit
        return False, "Quantity exceeds maximum allowed value"

    return True, None


def validate_price(price: float) -> tuple[bool, Optional[str]]:
    """
    Validate price value

    Args:
        price: Price value

    Returns:
        tuple: (is_valid, error_message)
    """
    if price is None:
        return False, "Price is required"

    if price < 0:
        return False, "Price cannot be negative"

    if price > 100000000:  # Reasonable upper limit (10 crores)
        return False, "Price exceeds maximum allowed value"

    return True, None


def validate_indian_state(state: str) -> tuple[bool, Optional[str]]:
    """
    Validate Indian state name

    Args:
        state: State name

    Returns:
        tuple: (is_valid, error_message)
    """
    # List of Indian states and union territories
    valid_states = {
        "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
        "Chhattisgarh", "Goa", "Gujarat", "Haryana", "Himachal Pradesh",
        "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh", "Maharashtra",
        "Manipur", "Meghalaya", "Mizoram", "Nagaland", "Odisha",
        "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
        "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
        "Andaman and Nicobar Islands", "Chandigarh", "Dadra and Nagar Haveli and Daman and Diu",
        "Delhi", "Jammu and Kashmir", "Ladakh", "Lakshadweep", "Puducherry"
    }

    if not state:
        return False, "State is required"

    # Case-insensitive comparison
    if state.title() not in valid_states:
        return False, f"Invalid Indian state: {state}"

    return True, None
