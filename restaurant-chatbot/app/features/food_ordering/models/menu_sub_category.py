"""
MenuSubCategory Model
=====================
Sub-categories under categories (only if >= 10 items).
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean, Integer,
    ForeignKey, Index, CheckConstraint,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE
from sqlalchemy.sql import text


class MenuSubCategory(Base):
    """
    Sub-categories under categories (only created if category has >= 10 items).

    Hierarchy: menu_sections → menu_categories → menu_sub_categories
    Examples: Dosas (under Tiffin), Breads (under Main Course), Juices (under Beverages)
    """
    __tablename__ = "menu_sub_categories"

    menu_sub_category_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    restaurant_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )
    category_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_categories.menu_category_id", ondelete="CASCADE"),
        nullable=False
    )
    sub_category_name: Mapped[str] = mapped_column(String(100), nullable=False)
    sub_category_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sub_category_status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    sub_category_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sub_category_timings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sub_category_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_sub_categories")
    category: Mapped["MenuCategory"] = relationship("MenuCategory", back_populates="sub_categories")
    sub_category_mappings: Mapped[List["MenuItemCategoryMapping"]] = relationship(
        "MenuItemCategoryMapping",
        back_populates="sub_category"
    )

    __table_args__ = (
        CheckConstraint(
            "sub_category_status IN ('active', 'inactive')",
            name='check_sub_category_status'
        ),
        Index('idx_menu_sub_categories_restaurant', 'restaurant_id', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_sub_categories_category', 'category_id', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_sub_categories_status', 'sub_category_status', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_sub_categories_rank', 'sub_category_rank', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuSubCategory(id='{self.menu_sub_category_id}', name='{self.sub_category_name}')>"


__all__ = ["MenuSubCategory"]
