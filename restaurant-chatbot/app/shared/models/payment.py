"""
Payment Models
==============

Database models for payment feature.

Models in this file:
- Payment
- PaymentOrder
- PaymentTransaction
- WebhookEvent
- PaymentRetryAttempt
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





class PaymentOrder(Base):
    """
    Payment orders linking restaurant orders to Razorpay orders.
    Manages payment links, expiry, and retry logic.
    """
    __tablename__ = "payment_orders"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    order_id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)  # Nullable for safety (Tier 1 users should authenticate before payment, but nullable as fallback)
    razorpay_order_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Amount in paise
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    payment_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_link_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[Optional[dict]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(), onupdate=func.now())

    # Relationships
    # NOTE: Removed back_populates="payment_order" because Order.payment_order
    # references the PaymentOrder from app.features.food_ordering.models.payment_order,
    # not this one. Having back_populates here causes SQLAlchemy mapper conflict.
    order: Mapped["Order"] = relationship("Order")
    user: Mapped[Optional["User"]] = relationship("User")  # Optional since user_id can be null (no back_populates due to duplicate PaymentOrder classes)
    payment_transactions: Mapped[List["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="payment_order")
    retry_attempts: Mapped[List["PaymentRetryAttempt"]] = relationship("PaymentRetryAttempt", back_populates="payment_order")

    __table_args__ = (
        Index('idx_payment_orders_order_id', 'order_id'),
        Index('idx_payment_orders_user_id', 'user_id'),
        Index('idx_payment_orders_razorpay_order_id', 'razorpay_order_id'),
        Index('idx_payment_orders_status', 'status'),
        Index('idx_payment_orders_expires_at', 'expires_at'),
        CheckConstraint('amount > 0', name='chk_payment_order_amount_positive'),
        CheckConstraint("currency IN ('INR', 'USD', 'EUR')", name='chk_payment_order_currency_valid'),
        CheckConstraint('retry_count >= 0 AND retry_count <= max_retry_attempts', name='chk_payment_order_retry_count_valid'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentOrder(id={self.id}, order_id={self.order_id}, amount={self.amount})>"





class PaymentTransaction(Base):
    """
    Individual payment transactions with comprehensive Razorpay data.
    Tracks actual payment attempts and their outcomes.
    """
    __tablename__ = "payment_transactions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    payment_order_id: Mapped[str] = mapped_column(String(20), ForeignKey("payment_orders.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    order_id: Mapped[UUID] = mapped_column(UUID_TYPE(as_uuid=True), ForeignKey("orders.order_id"), nullable=False)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(255), nullable=False)
    razorpay_signature: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_paid: Mapped[int] = mapped_column(Integer, default=0)
    amount_due: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # card, upi, netbanking, wallet
    status: Mapped[str] = mapped_column(String(50), default="created")  # created, authorized, captured, failed, refunded
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, default=lambda: {})
    bank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    wallet: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vpa: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # UPI Virtual Payment Address
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fee: Mapped[int] = mapped_column(Integer, default=0)  # Razorpay fee
    tax: Mapped[int] = mapped_column(Integer, default=0)  # Tax on fee
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(), onupdate=func.now())

    # Relationships
    payment_order: Mapped["PaymentOrder"] = relationship("PaymentOrder", back_populates="payment_transactions")
    user: Mapped["User"] = relationship("User", back_populates="payment_transactions")
    order: Mapped["Order"] = relationship("Order")

    __table_args__ = (
        Index('idx_payment_transactions_payment_order_id', 'payment_order_id'),
        Index('idx_payment_transactions_user_id', 'user_id'),
        Index('idx_payment_transactions_order_id', 'order_id'),
        Index('idx_payment_transactions_razorpay_payment_id', 'razorpay_payment_id'),
        Index('idx_payment_transactions_status', 'status'),
        CheckConstraint('amount > 0', name='chk_payment_transaction_amount_positive'),
        CheckConstraint("currency IN ('INR', 'USD', 'EUR')", name='chk_payment_transaction_currency_valid'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentTransaction(id={self.id}, razorpay_payment_id='{self.razorpay_payment_id}', status={self.status})>"





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
    payment_order: Mapped["PaymentOrder"] = relationship("PaymentOrder", back_populates="retry_attempts")
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



