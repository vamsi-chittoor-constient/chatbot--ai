"""
PaymentRefund Model
===================
Refund records for payment transactions.
"""

from typing import Optional
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean, Numeric,
    ForeignKey, Index,
    Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE, JSONB


class PaymentRefund(Base):
    """
    Refund records for payment transactions.

    Tracks refund status, approval, and processing.
    """
    __tablename__ = "payment_refund"

    # Primary Key
    payment_refund_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    payment_transaction_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("payment_transaction.payment_transaction_id", ondelete="SET NULL"),
        nullable=True
    )
    order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("orders.order_id", ondelete="SET NULL"),
        nullable=True
    )
    order_item_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    payment_order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("payment_order.payment_order_id", ondelete="SET NULL"),
        nullable=True
    )
    payment_gateway_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("payment_gateway.payment_gateway_id", ondelete="SET NULL"),
        nullable=True
    )
    refund_reason_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    refund_status_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )

    # Gateway Details
    gateway_refund_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Amount
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    refund_currency: Mapped[str] = mapped_column(String(3), default='INR')

    # Reason & Notes
    refund_reason_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processing_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Approval
    initiated_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)
    approved_by: Mapped[Optional[UUID]] = mapped_column(UUID_TYPE(as_uuid=True), nullable=True)

    # Gateway Response
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    refund_initiated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    refund_processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    refund_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
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

    __table_args__ = (
        Index('idx_payment_refund_order', 'order_id'),
        Index('idx_payment_refund_transaction', 'payment_transaction_id'),
        Index('idx_payment_refund_gateway', 'gateway_refund_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentRefund(id='{self.payment_refund_id}', amount={self.refund_amount})>"


__all__ = ["PaymentRefund"]
