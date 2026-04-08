"""
Commodity Price Model

Caches market prices for commodities to reduce external API calls.
"""

from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class CommodityPrice(Base):
    """
    Commodity price cache model

    Stores cached market prices for commodities with expiration
    to reduce external API calls and improve performance.
    """

    __tablename__ = "commodity_prices"

    # Primary key
    id: Mapped[str] = mapped_column(
        sa.UUID,
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )

    # Commodity and location
    commodity_code: Mapped[str] = mapped_column(
        sa.String(20), nullable=False, index=True
    )
    city: Mapped[str] = mapped_column(sa.String(100), nullable=False)

    # Price information
    price: Mapped[float] = mapped_column(sa.Numeric(10, 2), nullable=False)
    source: Mapped[str] = mapped_column(
        sa.String(50), nullable=False
    )  # MCX, Moneycontrol, Agmarknet
    confidence_score: Mapped[float] = mapped_column(
        sa.Numeric(3, 2), nullable=False
    )  # 0.0 to 1.0

    # Timestamps
    fetched_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        sa.DateTime, nullable=False, index=True
    )  # Typically 24 hours later

    def __repr__(self) -> str:
        return f"<CommodityPrice(commodity={self.commodity_code}, city={self.city}, price={self.price})>"
