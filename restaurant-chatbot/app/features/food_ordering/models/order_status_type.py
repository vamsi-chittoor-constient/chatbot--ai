"""
OrderStatusType Model
=====================
Lookup table for order status types (draft, confirmed, preparing, etc.).
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


class OrderStatusType(Base):
    """
    Lookup table for order status types.

    Examples: draft, pending, confirmed, preparing, ready, completed, cancelled
    """
    __tablename__ = "order_status_type"

    order_status_type_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    order_status_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_status_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    order_status_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order_status_is_active: Mapped[bool] = mapped_column(Boolean, default=True)

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
        Index('idx_order_status_type_code', 'order_status_code'),
        Index('idx_order_status_type_active', 'order_status_is_active'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OrderStatusType(code='{self.order_status_code}', name='{self.order_status_name}')>"


__all__ = ["OrderStatusType"]
