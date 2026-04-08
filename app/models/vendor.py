"""
Vendor Model

Represents suppliers in the vendor database for negotiation.
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class Vendor(Base):
    """
    Vendor model

    Represents a supplier/vendor that can be contacted for
    price negotiations and procurement.
    """

    __tablename__ = "vendors"

    # Primary key
    id: Mapped[str] = mapped_column(
        sa.UUID,
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )

    # Business information
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    phone: Mapped[str] = mapped_column(sa.String(15), nullable=False)

    # Location
    city: Mapped[str] = mapped_column(sa.String(100), nullable=False, index=True)
    state: Mapped[str] = mapped_column(sa.String(100), nullable=False)

    # Commodities supplied
    commodities_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )  # List of commodities: ["steel", "copper"]

    # Performance metrics
    rating: Mapped[float] = mapped_column(
        sa.Numeric(3, 2), default=0.0, nullable=False
    )  # 0.0 to 5.0
    total_negotiations: Mapped[int] = mapped_column(
        sa.Integer, default=0, nullable=False
    )
    avg_response_hours: Mapped[Optional[float]] = mapped_column(
        sa.Numeric(5, 2), nullable=True
    )
    response_rate: Mapped[float] = mapped_column(
        sa.Numeric(5, 2), default=0.0, nullable=False
    )  # Percentage (0-100)

    # Status
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<Vendor(id={self.id}, name={self.name}, city={self.city}, rating={self.rating})>"
