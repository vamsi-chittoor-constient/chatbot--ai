"""
Payment Models (Legacy)
========================

Legacy payment models. PaymentOrder and PaymentTransaction have been disabled
to avoid SQLAlchemy mapper conflicts with the active models in
app.features.food_ordering.models.

Active models in this file:
- Payment
- WebhookEvent
- PaymentRetryAttempt

Disabled (see food_ordering.models for active versions):
- PaymentOrder → app.features.food_ordering.models.payment_order.PaymentOrder
- PaymentTransaction → app.features.food_ordering.models.payment_transaction.PaymentTransaction
"""

from uuid import UUID

from app.shared.models.base import (
    Base, func, datetime, Optional, List,
    String, Text, DateTime, Boolean, JSON, Integer,
    ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Decimal, Numeric, Date, Time, ARRAY, Vector,
    relationship, Mapped, mapped_column, SQLEnum,
    UserStatus, BookingStatus, OrderStatus, PaymentStatus,
    MessageDirection, MessageChannel, ComplaintStatus
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class Payment(Base):
    """
    Payment transaction records with Razorpay integration.
    """
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    order_id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True), ForeignKey("orders.order_id"))
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    # Commented out back_populates since Order.payments relationship is disabled
    order: Mapped["Order"] = relationship("Order")

    __table_args__ = (
        Index('idx_payments_order', 'order_id'),
        Index('idx_payments_status', 'status'),
        Index('idx_payments_razorpay', 'razorpay_payment_id'),
        Index('idx_payments_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Payment(id='{self.id[:8]}...', amount={self.amount}, status={self.status})>"





# ============================================================================
# LEGACY PaymentOrder - DISABLED to prevent SQLAlchemy mapper conflict
# The active PaymentOrder model is in app.features.food_ordering.models.payment_order
# (table: "payment_order" with UUID keys)
# This legacy class used table "payment_orders" with String keys.
# Importing this module (e.g. for PaymentRetryAttempt) would register both
# classes under the name "PaymentOrder", causing:
#   "Multiple classes found for path 'PaymentOrder' in the registry"
# ============================================================================
# class PaymentOrder(Base):
#     __tablename__ = "payment_orders"
#     ... (removed to avoid mapper conflict)





# ============================================================================
# LEGACY PaymentTransaction - DISABLED to prevent SQLAlchemy mapper conflict
# The active PaymentTransaction model is in app.features.food_ordering.models.payment_transaction
# (table: "payment_transaction" with UUID keys)
# This legacy class used table "payment_transactions" with String keys.
# Importing this module would register both classes under the name
# "PaymentTransaction", causing:
#   "Multiple classes found for path 'PaymentTransaction' in the registry"
# ============================================================================
# class PaymentTransaction(Base):
#     __tablename__ = "payment_transactions"
#     ... (removed to avoid mapper conflict)





class WebhookEvent(Base):
    """
    Razorpay webhook events for reliability and debugging.
    Ensures all webhook events are processed exactly once.
    """
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_webhook_events_event_id', 'event_id'),
        Index('idx_webhook_events_event_type', 'event_type'),
        Index('idx_webhook_events_processed', 'processed'),
        Index('idx_webhook_events_created_at', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent(id={self.id}, event_type='{self.event_type}', processed={self.processed})>"





class PaymentRetryAttempt(Base):
    """
    Track all payment retry attempts for analytics and debugging.
    """
    __tablename__ = "payment_retry_attempts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    payment_order_id: Mapped[str] = mapped_column(String(20), ForeignKey("payment_orders.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # attempted, failed, abandoned
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    # NOTE: payment_order relationship removed - legacy PaymentOrder class disabled
    # to avoid mapper conflict with food_ordering.models.payment_order.PaymentOrder
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index('idx_payment_retry_attempts_payment_order_id', 'payment_order_id'),
        Index('idx_payment_retry_attempts_user_id', 'user_id'),
        UniqueConstraint('payment_order_id', 'attempt_number', name='uq_payment_retry_attempt'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentRetryAttempt(id={self.id}, attempt_number={self.attempt_number}, status={self.status})>"


# Communication Models



