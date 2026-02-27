"""
PaymentOrder Model
==================
Payment order linking restaurant orders to payment gateway orders.
"""

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean, Integer, Numeric,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE, JSONB

if TYPE_CHECKING:
    from app.features.food_ordering.models.payment_transaction import PaymentTransaction
    from app.features.food_ordering.models.order import Order


class PaymentOrder(Base):
    """
    Payment order linking restaurant orders to payment gateway orders.

    Manages payment links, expiry, and retry logic.
    """
    __tablename__ = "payment_order"

    # Primary Key
    payment_order_id: Mapped[UUID] = mapped_column(
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
    restaurant_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    customer_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    payment_gateway_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("payment_gateway.payment_gateway_id", ondelete="SET NULL"),
        nullable=True
    )

    # Gateway Details
    gateway_order_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_order_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Amount
    order_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    order_currency: Mapped[str] = mapped_column(String(3), default='INR')

    # Payment Link
    payment_link_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_link_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_link_short_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_link_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Retry Logic
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=3)

    # Additional Info
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB, nullable=True)

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
        back_populates="payment_order"
    )
    transactions: Mapped[List["PaymentTransaction"]] = relationship(
        "PaymentTransaction",
        back_populates="payment_order",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index('idx_payment_order_order', 'order_id'),
        Index('idx_payment_order_status', 'payment_order_status'),
        Index('idx_payment_order_link_id', 'payment_link_id'),
        Index('idx_payment_order_gateway', 'payment_gateway_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentOrder(id='{self.payment_order_id}', order='{self.order_id}', status='{self.payment_order_status}')>"


__all__ = ["PaymentOrder"]
