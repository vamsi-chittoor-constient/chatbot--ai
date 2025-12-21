"""
MenuItemEnrichedView Model
===========================
Read-only model for menu_items_enriched_view database view.
Provides denormalized menu item data with all relationships for fast querying.
"""

from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base,
    String, Text, DateTime, Boolean, Integer, Numeric,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE, ARRAY


class MenuItemEnrichedView(Base):
    """
    Read-only model for menu_items_enriched_view.

    Denormalized view joining menu_item with all related tables:
    - Category hierarchy (section/category/subcategory)
    - Cuisines (many-to-many)
    - Meal timings (many-to-many)
    - Ingredients
    - Allergens
    - Dietary types

    Use for read operations only. For writes, use MenuItem model.
    """
    __tablename__ = "menu_items_enriched_view"
    __table_args__ = {'info': {'is_view': True}}

    # Primary Key
    menu_item_id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True), primary_key=True)
    restaurant_id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True))

    # Basic Info
    menu_item_name: Mapped[str] = mapped_column(String(200))
    menu_item_description: Mapped[Optional[str]] = mapped_column(Text)
    menu_item_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    menu_item_quantity: Mapped[Optional[int]] = mapped_column(Integer)
    menu_item_status: Mapped[str] = mapped_column(String(20))

    # Attributes
    menu_item_spice_level: Mapped[Optional[str]] = mapped_column(String(20))
    menu_item_in_stock: Mapped[bool] = mapped_column(Boolean)
    menu_item_is_recommended: Mapped[bool] = mapped_column(Boolean)
    menu_item_favorite: Mapped[bool] = mapped_column(Boolean)
    menu_item_minimum_preparation_time: Mapped[Optional[int]] = mapped_column(Integer)

    # Operational Flags
    menu_item_allow_variation: Mapped[bool] = mapped_column(Boolean)
    menu_item_allow_addon: Mapped[bool] = mapped_column(Boolean)
    menu_item_is_combo: Mapped[bool] = mapped_column(Boolean)
    menu_item_is_combo_parent: Mapped[bool] = mapped_column(Boolean)
    menu_item_rank: Mapped[int] = mapped_column(Integer)

    # AI-Critical Fields
    menu_item_calories: Mapped[Optional[int]] = mapped_column(Integer)
    menu_item_is_seasonal: Mapped[bool] = mapped_column(Boolean)
    menu_item_image_url: Mapped[Optional[str]] = mapped_column(String(500))
    menu_item_serving_unit: Mapped[Optional[str]] = mapped_column(String(20))

    # Aggregated Relationships (Arrays from view)
    section: Mapped[Optional[str]] = mapped_column(String(100))
    categories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    subcategories: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    cuisines: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    meal_timings: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    ingredients: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    allergens: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    dietary_types: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))

    # Audit Fields
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_deleted: Mapped[bool] = mapped_column(Boolean)

    def __repr__(self) -> str:
        return f"<MenuItemEnrichedView(id='{self.menu_item_id}', name='{self.menu_item_name}', price={self.menu_item_price})>"


__all__ = ["MenuItemEnrichedView"]
