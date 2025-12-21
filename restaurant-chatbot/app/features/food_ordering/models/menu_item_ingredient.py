"""
MenuItemIngredient Model
========================
Ingredient tracking for menu items.
Stores ingredient name, quantity, unit, and ranking.
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, DateTime, Boolean, Integer, Numeric,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class MenuItemIngredient(Base):
    """
    Ingredient tracking for menu items with quantity and unit information.

    Each menu item can have multiple ingredients with optional quantity/unit.
    """
    __tablename__ = "menu_item_ingredient"

    # Primary Key
    ingredient_id: Mapped[UUID] = mapped_column(
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
    restaurant_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )

    # Ingredient Info
    ingredient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    ingredient_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    ingredient_unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    ingredient_rank: Mapped[int] = mapped_column(Integer, default=0)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

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
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="ingredients")
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant")

    __table_args__ = (
        Index('idx_menu_item_ingredient_item', 'menu_item_id', postgresql_where=func.not_(is_deleted)),
        Index('idx_menu_item_ingredient_restaurant', 'restaurant_id', postgresql_where=func.not_(is_deleted)),
        Index('idx_menu_item_ingredient_primary', 'is_primary', postgresql_where=func.and_(func.not_(is_deleted), is_primary)),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItemIngredient(id='{self.ingredient_id}', name='{self.ingredient_name}', menu_item='{self.menu_item_id}')>"


__all__ = ["MenuItemIngredient"]
