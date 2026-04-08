"""
Factory Model

Represents manufacturing factories (MSMEs) using the ProcureAI system.
"""

from datetime import datetime
from typing import Optional

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.database import Base


class Factory(Base):
    """
    Factory/MSME model

    Represents a manufacturing business that uses ProcureAI
    for procurement optimization.
    """

    __tablename__ = "factories"

    # Primary key
    id: Mapped[str] = mapped_column(
        sa.UUID,
        primary_key=True,
        server_default=sa.func.gen_random_uuid(),
    )

    # Contact information
    phone: Mapped[str] = mapped_column(
        sa.String(15),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(sa.String(255), nullable=False)

    # Location
    city: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    state: Mapped[str] = mapped_column(sa.String(100), nullable=False)

    # Business details
    udyam_number: Mapped[Optional[str]] = mapped_column(
        sa.String(20), nullable=True
    )
    materials_json: Mapped[dict] = mapped_column(
        JSONB, nullable=False, default=list
    )  # List of materials: ["steel", "copper", "aluminium"]

    # Status and timestamps
    onboarded_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime, default=sa.func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime,
        default=sa.func.now(),
        onupdate=sa.func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Factory(id={self.id}, name={self.name}, city={self.city})>"
