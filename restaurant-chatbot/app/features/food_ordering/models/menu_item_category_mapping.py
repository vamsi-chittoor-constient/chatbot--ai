"""
MenuItemCategoryMapping Model
==============================
Maps menu items to multiple categories/sub-categories (many-to-many).
⚠️ COMPLETELY NEW TABLE - Does not exist in current codebase.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    DateTime, Boolean, Integer,
    ForeignKey, Index, UniqueConstraint,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class MenuItemCategoryMapping(Base):
    """
    Maps menu items to categories and sub-categories (many-to-many).

    Enables:
    - Multi-category items (item can belong to multiple categories)
    - Efficient filtering by category/sub-category hierarchy
    - Primary category designation (one per item)

    Logic:
    - Items with >= 10 siblings: Map to both category AND sub-category
    - Items with < 10 siblings: Map to category only (sub_category_id = NULL)
    """
    __tablename__ = "menu_item_category_mapping"

    mapping_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    restaurant_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )
    menu_item_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_item.menu_item_id", ondelete="CASCADE"),
        nullable=False
    )
    menu_category_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_categories.menu_category_id", ondelete="CASCADE"),
        nullable=False
    )
    menu_sub_category_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_sub_categories.menu_sub_category_id", ondelete="CASCADE"),
        nullable=True,
        comment="NULL if item belongs to category directly (< 10 items)"
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="One category per item should be marked as primary"
    )
    display_rank: Mapped[int] = mapped_column(Integer, default=0)

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
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="category_mappings")
    category: Mapped["MenuCategory"] = relationship("MenuCategory", back_populates="category_mappings")
    sub_category: Mapped[Optional["MenuSubCategory"]] = relationship(
        "MenuSubCategory",
        back_populates="sub_category_mappings"
    )

    __table_args__ = (
        UniqueConstraint(
            'menu_item_id', 'menu_category_id', 'menu_sub_category_id',
            name='unique_item_category_subcategory'
        ),
        Index('idx_mapping_menu_item', 'menu_item_id', postgresql_where=text('is_deleted = false')),
        Index('idx_mapping_category', 'menu_category_id', postgresql_where=text('is_deleted = false')),
        Index('idx_mapping_sub_category', 'menu_sub_category_id', postgresql_where=text('is_deleted = false AND menu_sub_category_id IS NOT NULL')),
        Index('idx_mapping_restaurant', 'restaurant_id', postgresql_where=text('is_deleted = false')),
        Index('idx_mapping_primary', 'menu_item_id', 'is_primary', postgresql_where=text('is_deleted = false AND is_primary = true')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItemCategoryMapping(item_id='{self.menu_item_id}', category_id='{self.menu_category_id}', is_primary={self.is_primary})>"


__all__ = ["MenuItemCategoryMapping"]
