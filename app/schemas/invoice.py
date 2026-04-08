"""
Invoice Schemas

Pydantic schemas for invoice-related API requests and responses.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ParsedInvoiceData(BaseModel):
    """Structured invoice data from OCR + Qwen parsing"""

    vendor_name: str = Field(..., description="Vendor name from invoice")
    item_name: str = Field(..., description="Item/product name")
    item_description: Optional[str] = Field(None, description="Detailed description")
    quantity: Decimal = Field(..., gt=0, description="Quantity ordered")
    unit: str = Field(..., description="Unit of measurement (kg, ton, pieces)")
    unit_price: Decimal = Field(..., gt=0, description="Price per unit")
    total_amount: Decimal = Field(..., gt=0, description="Total invoice amount")
    invoice_date: date = Field(..., description="Invoice date")
    gstin: Optional[str] = Field(None, description="GSTIN number")

    class Config:
        json_encoders = {
            Decimal: float,
            date: str,
        }


class PriceComparison(BaseModel):
    """Market price comparison results"""

    market_price: Decimal = Field(..., description="Current market price")
    invoice_price: Optional[Decimal] = Field(None, description="Price paid on invoice")
    overpayment_percent: Decimal = Field(..., description="Overpayment percentage")
    overpayment_amount: Decimal = Field(..., description="Amount overpaid")
    recommendation: str = Field(..., description="Action recommendation")
    market_source: str = Field(..., description="Source of market price")
    price_freshness: str = Field(..., description="Age of market price data")
    from_cache: bool = Field(default=False, description="Whether data is from cache")
    stale: bool = Field(default=False, description="Whether cache data is stale")


class InvoiceUploadResponse(BaseModel):
    """Response model for invoice upload"""

    invoice_id: str = Field(..., description="Generated invoice ID")
    parsed_data: ParsedInvoiceData = Field(..., description="Parsed invoice information")
    image_url: str = Field(..., description="URL to stored invoice image")
    ocr_confidence: float = Field(..., description="OCR confidence score (0-100)")
    processing_time: float = Field(..., description="Processing time in seconds")
    status: str = Field(..., description="Processing status")
    price_comparison: Optional[PriceComparison] = Field(
        None, description="Price comparison results"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "invoice_id": "123e4567-e89b-12d3-a456-426614174000",
                "parsed_data": {
                    "vendor_name": "ABC Steel Traders",
                    "item_name": "MS Steel Rods",
                    "quantity": "100.00",
                    "unit": "kg",
                    "unit_price": "55.00",
                    "total_amount": "5500.00",
                    "invoice_date": "2024-04-08",
                    "gstin": "27ABCDE1234F1Z5"
                },
                "image_url": "https://storage.example.com/invoices/abc123.jpg",
                "ocr_confidence": 95.2,
                "processing_time": 3.2,
                "status": "parsed",
                "price_comparison": {
                    "market_price": "50.00",
                    "invoice_price": "55.00",
                    "overpayment_percent": 10.0,
                    "overpayment_amount": "500.00",
                    "recommendation": "negotiate",
                    "market_source": "MCX",
                    "price_freshness": "2 hours ago"
                }
            }
        }


class InvoiceResponse(BaseModel):
    """Response model for invoice details"""

    invoice_id: str
    factory_id: str
    parsed_data: ParsedInvoiceData
    price_check: Optional[dict] = None
    negotiation: Optional[dict] = None
    created_at: datetime
    status: str


class FactoryInvoicesList(BaseModel):
    """Response model for factory invoices list"""

    invoices: list[InvoiceResponse]
    pagination: dict
