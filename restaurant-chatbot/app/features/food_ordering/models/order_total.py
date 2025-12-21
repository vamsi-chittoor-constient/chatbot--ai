"""
OrderTotal Model
================
Order totals and calculations.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    DateTime, Boolean, Numeric,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE

if TYPE_CHECKING:
    from app.features.food_ordering.models.order import Order


class OrderTotal(Base):
    """
    Order totals and calculations.

    Stores all pricing breakdowns for an order.
    """
    __tablename__ = "order_total"

    # Primary Key
    order_total_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Key
    order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("orders.order_id", ondelete="CASCADE"),
        nullable=True
    )

    # Totals
    items_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    addons_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    charges_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    discount_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    tax_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    platform_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    convenience_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    subtotal: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    roundoff_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    total_before_tip: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    tip_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    final_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

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
        back_populates="totals"
    )

    __table_args__ = (
        Index('idx_order_total_order', 'order_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OrderTotal(order='{self.order_id}', final={self.final_amount})>"


__all__ = ["OrderTotal"]
