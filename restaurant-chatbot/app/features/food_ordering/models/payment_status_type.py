"""
PaymentStatusType Model
=======================
Lookup table for payment status types.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean,
    Index,
    Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class PaymentStatusType(Base):
    """
    Lookup table for payment status types.

    Examples: pending, authorized, captured, paid, failed, refunded
    """
    __tablename__ = "payment_status_type"

    payment_status_type_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    payment_status_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    payment_status_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payment_status_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_status_is_terminal: Mapped[bool] = mapped_column(Boolean, default=False)

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
        Index('idx_payment_status_type_code', 'payment_status_code'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentStatusType(code='{self.payment_status_code}', name='{self.payment_status_name}')>"


__all__ = ["PaymentStatusType"]
