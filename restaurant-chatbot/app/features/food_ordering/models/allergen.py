"""
Allergen Model
==============
Allergen lookup table for tracking common food allergens.
Links to menu items via menu_item_allergen_mapping table.
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


class Allergen(Base):
    """
    Allergen lookup table for food allergens (nuts, dairy, gluten, etc.).

    Links to menu items via MenuItemAllergenMapping for many-to-many relationship.
    """
    __tablename__ = "allergens"

    # Primary Key
    allergen_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4()
    )

    # Basic Info
    allergen_name: Mapped[str] = mapped_column(String(255), nullable=False)
    allergen_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    menu_item_mappings: Mapped[List["MenuItemAllergenMapping"]] = relationship(
        "MenuItemAllergenMapping",
        back_populates="allergen",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_allergen_name', 'allergen_name'),
        Index('idx_allergen_deleted', 'is_deleted'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Allergen(id='{self.allergen_id}', name='{self.allergen_name}')>"


__all__ = ["Allergen"]
