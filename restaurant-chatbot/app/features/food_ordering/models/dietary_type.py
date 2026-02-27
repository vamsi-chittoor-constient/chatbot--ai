"""
DietaryType Model
=================
Dietary type lookup table for tracking dietary preferences and restrictions.
Examples: Vegetarian, Vegan, Gluten-Free, Keto, etc.
Links to menu items via menu_item_dietary_mapping table.
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean,
    Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class DietaryType(Base):
    """
    Dietary type lookup table for dietary preferences and restrictions.

    Links to menu items via MenuItemDietaryMapping for many-to-many relationship.
    """
    __tablename__ = "dietary_types"

    # Primary Key
    dietary_type_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4()
    )

    # Basic Info
    dietary_type_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dietary_type_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    dietary_type_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp()
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)

    # Soft Delete
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    menu_item_mappings: Mapped[List["MenuItemDietaryMapping"]] = relationship(
        "MenuItemDietaryMapping",
        back_populates="dietary_type",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_dietary_type_name', 'dietary_type_name'),
        Index('idx_dietary_type_deleted', 'is_deleted'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<DietaryType(id='{self.dietary_type_id}', name='{self.dietary_type_name}')>"


__all__ = ["DietaryType"]
