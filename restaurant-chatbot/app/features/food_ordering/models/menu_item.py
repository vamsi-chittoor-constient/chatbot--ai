"""
MenuItem Model
==============
Individual menu items (dishes) - Core product data.
Matches actual database schema with all 34 columns.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean, Integer, Numeric,
    ForeignKey, Index, CheckConstraint,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class MenuItem(Base):
    """
    Individual menu items (dishes) with complete product data.

    Uses menu_item_category_mapping table for category relationships (many-to-many).
    The menu_sub_category_id field is DEPRECATED but kept for backward compatibility.
    """
    __tablename__ = "menu_item"

    # Primary Key
    menu_item_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    restaurant_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )
    menu_sub_category_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_sub_categories.menu_sub_category_id", ondelete="SET NULL"),
        nullable=True,
        comment="DEPRECATED: Use menu_item_category_mapping table instead. Kept for backward compatibility during migration."
    )

    # Basic Info
    menu_item_name: Mapped[str] = mapped_column(String(200), nullable=False)
    menu_item_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Pricing & Quantity
    menu_item_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    menu_item_quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status & Attributes
    menu_item_status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    menu_item_spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    menu_item_in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    menu_item_is_recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_favorite: Mapped[bool] = mapped_column(Boolean, default=False)

    # Operational
    menu_item_minimum_preparation_time: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    menu_item_allow_variation: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_allow_addon: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_is_combo: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_is_combo_parent: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    menu_item_ignore_taxes: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_ignore_discounts: Mapped[bool] = mapped_column(Boolean, default=False)

    # Deprecated/Phase 2 Fields
    menu_item_timings: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="DEPRECATED: Use menu_item_availability_schedule table instead."
    )
    menu_item_tax_id: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)
    menu_item_tax_cgst: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    menu_item_tax_sgst: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    menu_item_packaging_charges: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    menu_item_attribute_id: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)
    menu_item_addon_based_on: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    menu_item_markup_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # NEW: AI-Critical Fields (Added in migration_05)
    menu_item_calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    menu_item_is_seasonal: Mapped[bool] = mapped_column(Boolean, default=False)
    menu_item_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    menu_item_serving_unit: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

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
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_items")
    deprecated_sub_category: Mapped[Optional["MenuSubCategory"]] = relationship(
        "MenuSubCategory",
        foreign_keys=[menu_sub_category_id]
    )
    category_mappings: Mapped[List["MenuItemCategoryMapping"]] = relationship(
        "MenuItemCategoryMapping",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )
    cuisine_mappings: Mapped[List["MenuItemCuisineMapping"]] = relationship(
        "MenuItemCuisineMapping",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )
    availability_schedules: Mapped[List["MenuItemAvailabilitySchedule"]] = relationship(
        "MenuItemAvailabilitySchedule",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )

    # NEW: AI-Critical Relationships (Added in migration_05)
    ingredients: Mapped[List["MenuItemIngredient"]] = relationship(
        "MenuItemIngredient",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )
    allergen_mappings: Mapped[List["MenuItemAllergenMapping"]] = relationship(
        "MenuItemAllergenMapping",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )
    dietary_mappings: Mapped[List["MenuItemDietaryMapping"]] = relationship(
        "MenuItemDietaryMapping",
        back_populates="menu_item",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "menu_item_status IN ('active', 'inactive', 'discontinued')",
            name='check_menu_item_status'
        ),
        CheckConstraint(
            "menu_item_spice_level IN ('none', 'mild', 'medium', 'hot', 'extra_hot') OR menu_item_spice_level IS NULL",
            name='check_spice_level'
        ),
        CheckConstraint("menu_item_price >= 0", name='check_price_positive'),
        Index('idx_menu_item_restaurant', 'restaurant_id', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_item_spice_level', 'menu_item_spice_level', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_item_in_stock', 'menu_item_in_stock', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_item_is_recommended', 'menu_item_is_recommended', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_item_favorite', 'menu_item_favorite', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_item_price', 'menu_item_price', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItem(id='{self.menu_item_id}', name='{self.menu_item_name}', price={self.menu_item_price})>"


__all__ = ["MenuItem"]
