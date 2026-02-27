"""
PaymentGateway Model
====================
Lookup table for payment gateways (Razorpay, etc.).
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, DateTime, Boolean,
    Index,
    Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE, JSONB


class PaymentGateway(Base):
    """
    Lookup table for payment gateways.

    Examples: razorpay, stripe, paytm
    """
    __tablename__ = "payment_gateway"

    payment_gateway_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    payment_gateway_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    payment_gateway_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_gateway_is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    payment_gateway_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

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
        Index('idx_payment_gateway_code', 'payment_gateway_code'),
        Index('idx_payment_gateway_active', 'payment_gateway_is_active'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentGateway(code='{self.payment_gateway_code}', name='{self.payment_gateway_name}')>"


__all__ = ["PaymentGateway"]
