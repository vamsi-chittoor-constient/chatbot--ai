"""
MenuCategory Model
==================
Course/cuisine-based categories (tiffin, main course, beverages, etc.).
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


class MenuCategory(Base):
    """
    Course/cuisine-based categories for menu organization.

    Hierarchy: menu_sections → menu_categories → menu_sub_categories
    Examples: Tiffin, Main Course, Beverages, Desserts, Snacks, Rice Dishes
    """
    __tablename__ = "menu_categories"

    menu_category_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    restaurant_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=True
    )
    menu_section_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_sections.menu_section_id", ondelete="CASCADE"),
        nullable=True
    )
    menu_category_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    menu_category_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    menu_category_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default='active')
    menu_category_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    menu_category_timings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    menu_category_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ext_petpooja_group_category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

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
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_categories")
    # section: Mapped[Optional["MenuSection"]] = relationship("MenuSection", back_populates="categories")
    sub_categories: Mapped[List["MenuSubCategory"]] = relationship(
        "MenuSubCategory",
        back_populates="category",
        cascade="all, delete-orphan"
    )
    category_mappings: Mapped[List["MenuItemCategoryMapping"]] = relationship(
        "MenuItemCategoryMapping",
        back_populates="category"
    )

    __table_args__ = (
        CheckConstraint(
            "menu_category_status IN ('active', 'inactive')",
            name='check_category_status'
        ),
        Index('idx_menu_categories_restaurant', 'restaurant_id', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_categories_section', 'menu_section_id', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_categories_status', 'menu_category_status', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_categories_rank', 'menu_category_rank', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuCategory(id='{self.menu_category_id}', name='{self.menu_category_name}')>"


__all__ = ["MenuCategory"]
