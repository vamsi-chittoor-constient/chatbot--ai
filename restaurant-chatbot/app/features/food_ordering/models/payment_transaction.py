"""
PaymentTransaction Model
========================
Individual payment transaction records.
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
    from app.features.food_ordering.models.payment_order import PaymentOrder


class PaymentTransaction(Base):
    """
    Individual payment transaction records.

    Stores gateway response, payment method details, and transaction status.
    """
    __tablename__ = "payment_transaction"

    # Primary Key
    payment_transaction_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    payment_order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("payment_order.payment_order_id", ondelete="CASCADE"),
        nullable=True
    )
    order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("orders.order_id", ondelete="SET NULL"),
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
    order_payment_method_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    payment_status_type_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("payment_status_type.payment_status_type_id", ondelete="SET NULL"),
        nullable=True
    )

    # Gateway IDs
    gateway_payment_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gateway_transaction_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gateway_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment Method Details
    payment_method_details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Amounts
    transaction_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    amount_paid: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    amount_due: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    transaction_currency: Mapped[str] = mapped_column(String(3), default='INR')
    gateway_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    gateway_tax: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    # Failure Details
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    failure_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    error_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Payment Method Info
    bank_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    card_network: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    card_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    card_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    wallet_provider: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    upi_vpa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Customer Contact (from gateway)
    customer_email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_contact: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Gateway Response
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Timestamps
    attempted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    authorized_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

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
    payment_order: Mapped[Optional["PaymentOrder"]] = relationship(
        "PaymentOrder",
        back_populates="transactions"
    )

    __table_args__ = (
        Index('idx_payment_transaction_order', 'order_id'),
        Index('idx_payment_transaction_payment_order', 'payment_order_id'),
        Index('idx_payment_transaction_status', 'payment_status_type_id'),
        Index('idx_payment_transaction_gateway_payment', 'gateway_payment_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentTransaction(id='{self.payment_transaction_id}', gateway_id='{self.gateway_payment_id}')>"


__all__ = ["PaymentTransaction"]
