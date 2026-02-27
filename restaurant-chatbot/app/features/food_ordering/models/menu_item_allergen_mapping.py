"""
MenuItemAllergenMapping Model
==============================
Many-to-many mapping between menu items and allergens.
Links menu_item table to allergens table.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    DateTime, Boolean,
    ForeignKey, Index, UniqueConstraint,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class MenuItemAllergenMapping(Base):
    """
    Many-to-many mapping table linking menu items to allergens.

    Each menu item can have multiple allergens, and each allergen can be
    associated with multiple menu items.
    """
    __tablename__ = "menu_item_allergen_mapping"

    # Primary Key
    mapping_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    menu_item_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_item.menu_item_id", ondelete="CASCADE"),
        nullable=False
    )
    allergen_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("allergens.allergen_id", ondelete="CASCADE"),
        nullable=False
    )
    restaurant_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )

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
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="allergen_mappings")
    allergen: Mapped["Allergen"] = relationship("Allergen", back_populates="menu_item_mappings")
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant")

    __table_args__ = (
        UniqueConstraint('menu_item_id', 'allergen_id', name='uq_menu_item_allergen'),
        Index('idx_menu_item_allergen_mapping_item', 'menu_item_id', postgresql_where=func.not_(is_deleted)),
        Index('idx_menu_item_allergen_mapping_allergen', 'allergen_id', postgresql_where=func.not_(is_deleted)),
        Index('idx_menu_item_allergen_mapping_restaurant', 'restaurant_id', postgresql_where=func.not_(is_deleted)),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItemAllergenMapping(id='{self.mapping_id}', menu_item='{self.menu_item_id}', allergen='{self.allergen_id}')>"


__all__ = ["MenuItemAllergenMapping"]
