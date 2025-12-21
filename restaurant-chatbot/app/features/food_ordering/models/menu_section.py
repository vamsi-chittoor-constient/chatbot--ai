"""
MenuSection Model
=================
Top-level dietary classification (Veg/Non-Veg/Vegan).
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


class MenuSection(Base):
    """
    Top-level dietary classification for menu organization.

    Hierarchy: menu_sections → menu_categories → menu_sub_categories → menu_item
    """
    __tablename__ = "menu_sections"

    menu_section_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    restaurant_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="CASCADE"),
        nullable=False
    )
    section_name: Mapped[str] = mapped_column(String(100), nullable=False)
    section_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    section_status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')
    section_rank: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    section_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_sections")
    categories: Mapped[List["MenuCategory"]] = relationship(
        "MenuCategory",
        back_populates="section",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "section_status IN ('active', 'inactive')",
            name='check_section_status'
        ),
        Index('idx_menu_sections_restaurant', 'restaurant_id', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_sections_status', 'section_status', postgresql_where=text('is_deleted = false')),
        Index('idx_menu_sections_rank', 'section_rank', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuSection(id='{self.menu_section_id}', name='{self.section_name}')>"


__all__ = ["MenuSection"]
