"""
Cuisine Model
=============
Lookup table for cuisine types (South Indian, North Indian, Chinese, etc.).
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, DateTime, Boolean,
    Index, CheckConstraint,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class Cuisine(Base):
    """
    Cuisine type reference table.

    Contains: South Indian, North Indian, Street Food/Chaat, Chinese/Indo-Chinese, Continental
    """
    __tablename__ = "cuisines"

    cuisine_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    cuisine_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    cuisine_status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    cuisine_mappings: Mapped[List["MenuItemCuisineMapping"]] = relationship(
        "MenuItemCuisineMapping",
        back_populates="cuisine"
    )

    __table_args__ = (
        CheckConstraint(
            "cuisine_status IN ('active', 'inactive')",
            name='check_cuisine_status'
        ),
        Index('idx_cuisines_name', 'cuisine_name', postgresql_where=text('is_deleted = false')),
        Index('idx_cuisines_status', 'cuisine_status', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Cuisine(id='{self.cuisine_id}', name='{self.cuisine_name}')>"


__all__ = ["Cuisine"]
