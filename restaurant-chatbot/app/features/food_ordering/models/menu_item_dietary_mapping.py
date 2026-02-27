"""
MenuItemDietaryMapping Model
=============================
Many-to-many mapping between menu items and dietary types.
Links menu_item table to dietary_types table.
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


class MenuItemDietaryMapping(Base):
    """
    Many-to-many mapping table linking menu items to dietary types.

    Each menu item can have multiple dietary classifications (Vegetarian, Vegan,
    Gluten-Free, etc.), and each dietary type can be associated with multiple menu items.
    """
    __tablename__ = "menu_item_dietary_mapping"

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
    dietary_type_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("dietary_types.dietary_type_id", ondelete="CASCADE"),
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
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="dietary_mappings")
    dietary_type: Mapped["DietaryType"] = relationship("DietaryType", back_populates="menu_item_mappings")
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant")

    __table_args__ = (
        UniqueConstraint('menu_item_id', 'dietary_type_id', name='uq_menu_item_dietary'),
        Index('idx_menu_item_dietary_mapping_item', 'menu_item_id', postgresql_where=func.not_(is_deleted)),
        Index('idx_menu_item_dietary_mapping_dietary', 'dietary_type_id', postgresql_where=func.not_(is_deleted)),
        Index('idx_menu_item_dietary_mapping_restaurant', 'restaurant_id', postgresql_where=func.not_(is_deleted)),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItemDietaryMapping(id='{self.mapping_id}', menu_item='{self.menu_item_id}', dietary='{self.dietary_type_id}')>"


__all__ = ["MenuItemDietaryMapping"]
