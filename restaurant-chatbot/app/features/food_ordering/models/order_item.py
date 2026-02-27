"""
OrderItem Model
===============
Individual items within an order.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean, Numeric,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE, JSONB

if TYPE_CHECKING:
    from app.features.food_ordering.models.order import Order
    from app.features.food_ordering.models.menu_item import MenuItem


class OrderItem(Base):
    """
    Individual items within an order.

    Contains pricing, customizations, and preparation status.
    """
    __tablename__ = "order_item"

    # Primary Key
    order_item_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=True
    )
    menu_item_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("menu_item.menu_item_id", ondelete="SET NULL"),
        nullable=True
    )
    menu_item_variation_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    category_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    substitute_item_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )

    # Item Details
    sku: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    hsn_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    category_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Pricing
    base_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    discount_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    tax_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    addon_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Availability
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    unavailable_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Customizations
    cooking_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    customizations: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Status Tracking
    item_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    prepared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    served_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
    order: Mapped[Optional["Order"]] = relationship(
        "Order",
        back_populates="items"
    )
    menu_item: Mapped[Optional["MenuItem"]] = relationship(
        "MenuItem",
        foreign_keys=[menu_item_id]
    )

    __table_args__ = (
        Index('idx_order_item_order', 'order_id'),
        Index('idx_order_item_menu_item', 'menu_item_id'),
        Index('idx_order_item_status', 'item_status'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OrderItem(id='{self.order_item_id}', order='{self.order_id}')>"


__all__ = ["OrderItem"]
