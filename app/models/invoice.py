"""
Invoice Model

Represents uploaded and processed invoices from factories.
"""

from datetime import datetime, date
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class Invoice(Base):
    """
    Invoice model

    Represents an invoice uploaded by a factory, including
    OCR text, parsed data, and price check results.
    """

    __tablename__ = "invoices"

    # Primary key
    id: Mapped[str] = mapped_column(
        sa.UUID,
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )

    # Foreign key to factory
    factory_id: Mapped[str] = mapped_column(
        sa.UUID,
        sa.ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Vendor and item information (from invoice)
    vendor_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    item_name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    item_description: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)

    # Quantity and pricing
    quantity: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(sa.String(20), nullable=False)  # kg, ton, pieces
    unit_price: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(sa.Numeric(12, 2), nullable=False)

    # Invoice details
    invoice_date: Mapped[date] = mapped_column(sa.Date, nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(sa.String(15), nullable=True)

    # OCR and parsing results
    raw_ocr_text: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    parsed_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    image_url: Mapped[str] = mapped_column(sa.Text, nullable=False)

    # Status tracking
    status: Mapped[str] = mapped_column(
        sa.String(20),
        default="processing",
        nullable=False,
    )  # processing, parsed, price_checked, negotiating, completed

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"<Invoice(id={self.id}, item={self.item_name}, amount={self.total_amount})>"
