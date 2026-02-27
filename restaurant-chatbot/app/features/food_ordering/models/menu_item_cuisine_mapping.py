"""
MenuItemCuisineMapping Model
=============================
Maps menu items to cuisines (many-to-many).
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
from sqlalchemy.sql import text


class MenuItemCuisineMapping(Base):
    """
    Maps menu items to cuisines (many-to-many).

    Supports filtering items by cuisine type:
    - South Indian, North Indian, Street Food, Chinese/Indo-Chinese, Continental
    """
    __tablename__ = "menu_item_cuisine_mapping"

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
    cuisine_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("cuisines.cuisine_id", ondelete="CASCADE"),
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
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="cuisine_mappings")
    cuisine: Mapped["Cuisine"] = relationship("Cuisine", back_populates="cuisine_mappings")

    __table_args__ = (
        UniqueConstraint(
            'menu_item_id', 'cuisine_id',
            name='unique_item_cuisine'
        ),
        Index('idx_cuisine_mapping_menu_item', 'menu_item_id', postgresql_where=text('is_deleted = false')),
        Index('idx_cuisine_mapping_cuisine', 'cuisine_id', postgresql_where=text('is_deleted = false')),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItemCuisineMapping(item_id='{self.menu_item_id}', cuisine_id='{self.cuisine_id}')>"


__all__ = ["MenuItemCuisineMapping"]
