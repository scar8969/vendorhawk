"""
Negotiation Vendor Message Model

Tracks individual vendor communications within a negotiation.
"""

from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class NegotiationVendorMessage(Base):
    """
    Negotiation vendor message model

    Tracks messages sent to individual vendors and their responses
    during a negotiation process.
    """

    __tablename__ = "negotiation_vendor_messages"

    # Primary key
    id: Mapped[str] = mapped_column(
        sa.UUID,
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )

    # Foreign keys
    negotiation_id: Mapped[str] = mapped_column(
        sa.UUID,
        sa.ForeignKey("negotiations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vendor_id: Mapped[str] = mapped_column(
        sa.UUID,
        sa.ForeignKey("vendors.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Message details
    message_sent: Mapped[str] = mapped_column(sa.Text, nullable=False)
    message_sent_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False
    )

    # Response details
    response_received: Mapped[Optional[str]] = mapped_column(sa.Text, nullable=True)
    response_received_at: Mapped[Optional[datetime]] = mapped_column(
        sa.DateTime, nullable=True
    )

    # Pricing and status
    quoted_price: Mapped[Optional[float]] = mapped_column(
        sa.Numeric(10, 2), nullable=True
    )
    counter_offered: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    # Final status
    final_status: Mapped[str] = mapped_column(
        sa.String(20),
        default="pending",
        nullable=False,
    )  # pending, accepted, rejected, no_response

    def __repr__(self) -> str:
        return f"<NegotiationVendorMessage(id={self.id}, vendor_id={self.vendor_id}, status={self.final_status})>"
