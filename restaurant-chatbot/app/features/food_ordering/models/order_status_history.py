"""
OrderStatusHistory Model
========================
Tracks order status changes over time.
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    Text, DateTime, Boolean,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE

if TYPE_CHECKING:
    from app.features.food_ordering.models.order import Order


class OrderStatusHistory(Base):
    """
    Tracks order status changes.

    Records who changed the status and when.
    """
    __tablename__ = "order_status_history"

    # Primary Key
    order_status_history_id: Mapped[UUID] = mapped_column(
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
    order_status_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("order_status_type.order_status_type_id", ondelete="SET NULL"),
        nullable=True
    )

    # Status Change Details
    order_status_changed_by: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    order_status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    order_status_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        back_populates="status_history"
    )

    __table_args__ = (
        Index('idx_order_status_history_order', 'order_id'),
        Index('idx_order_status_history_status', 'order_status_type_id'),
        Index('idx_order_status_history_changed_at', 'order_status_changed_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OrderStatusHistory(order='{self.order_id}', changed_at='{self.order_status_changed_at}')>"


__all__ = ["OrderStatusHistory"]
