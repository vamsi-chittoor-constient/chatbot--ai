"""
Order Model
===========
Main order table for food orders.
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, DateTime, Boolean, Integer,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE

if TYPE_CHECKING:
    from app.features.food_ordering.models.order_item import OrderItem
    from app.features.food_ordering.models.order_total import OrderTotal
    from app.features.food_ordering.models.order_status_history import OrderStatusHistory
    # Commented out to avoid conflict with unified models in app.database.models
    # from app.shared.models.payment import Payment
    from app.features.food_ordering.models.payment_order import PaymentOrder


class Order(Base):
    """
    Main order table.

    Supports dine-in and takeout orders.
    Links to order_type_table, order_source_type, order_status_type via foreign keys.
    """
    __tablename__ = "orders"

    # Primary Key
    order_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    # NOTE: FK to restaurant_table removed from SQLAlchemy model because the
    # Restaurant model uses table "restaurant_config", not "restaurant_table".
    # The DB-level FK constraint still exists.
    restaurant_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    # NOTE: FK to table_booking_info removed from SQLAlchemy model because there is
    # no TableBookingInfo model class loaded. The DB-level FK constraint still exists.
    table_booking_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    order_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("order_type_table.order_type_id", ondelete="SET NULL"),
        nullable=True
    )
    order_source_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("order_source_type.order_source_type_id", ondelete="SET NULL"),
        nullable=True
    )
    order_status_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("order_status_type.order_status_type_id", ondelete="SET NULL"),
        nullable=True
    )

    # Order Identification
    order_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_invoice_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_vr_order_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    order_external_reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
    items: Mapped[List["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    totals: Mapped[Optional["OrderTotal"]] = relationship(
        "OrderTotal",
        back_populates="order",
        uselist=False
    )
    status_history: Mapped[List["OrderStatusHistory"]] = relationship(
        "OrderStatusHistory",
        back_populates="order",
        cascade="all, delete-orphan"
    )
    # Legacy payment relationship (for backward compatibility with app.shared.models.payment)
    # Commented out to avoid conflict with unified models in app.database.models
    # payments: Mapped[List["Payment"]] = relationship(
    #     "Payment",
    #     back_populates="order"
    # )
    # New payment order relationship
    payment_order: Mapped[Optional["PaymentOrder"]] = relationship(
        "PaymentOrder",
        back_populates="order",
        uselist=False
    )

    __table_args__ = (
        Index('idx_orders_restaurant', 'restaurant_id'),
        Index('idx_orders_order_number', 'order_number'),
        Index('idx_orders_status_type', 'order_status_type_id'),
        Index('idx_orders_order_type', 'order_type_id'),
        Index('idx_orders_created_at', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Order(id='{self.order_id}', number={self.order_number})>"


__all__ = ["Order"]
