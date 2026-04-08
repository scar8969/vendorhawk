"""
Negotiation Model

Represents vendor negotiation processes for invoice price optimization.
"""

from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class Negotiation(Base):
    """
    Negotiation model

    Represents a vendor negotiation process initiated for an
    invoice to find better pricing.
    """

    __tablename__ = "negotiations"

    # Primary key
    id: Mapped[str] = mapped_column(
        sa.UUID,
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )

    # Foreign keys
    invoice_id: Mapped[str] = mapped_column(
        sa.UUID,
        sa.ForeignKey("invoices.id", ondelete="CASCADE"),
        nullable=False,
    )
    factory_id: Mapped[str] = mapped_column(
        sa.UUID,
        sa.ForeignKey("factories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Negotiation details
    commodity: Mapped[str] = mapped_column(sa.String(50), nullable=False)
    quantity: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    unit: Mapped[str] = mapped_column(sa.String(20), nullable=False)
    target_price: Mapped[float] = mapped_column(
        sa.Numeric(10, 2), nullable=False
    )  # Desired price per unit

    # Status tracking
    status: Mapped[str] = mapped_column(
        sa.String(20),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, active, closed, failed

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(sa.DateTime, nullable=True)

    # Results (populated when negotiation completes)
    winning_vendor_id: Mapped[Optional[str]] = mapped_column(
        sa.UUID,
        sa.ForeignKey("vendors.id", ondelete="SET NULL"),
        nullable=True,
    )
    final_price: Mapped[Optional[float]] = mapped_column(
        sa.Numeric(10, 2), nullable=True
    )
    saving_amount: Mapped[Optional[float]] = mapped_column(
        sa.Numeric(12, 2), nullable=True
    )

    def __repr__(self) -> str:
        return f"<Negotiation(id={self.id}, commodity={self.commodity}, status={self.status})>"
