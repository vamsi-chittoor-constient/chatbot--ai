"""
AbandonedCart Model
===================
Tracks abandoned shopping carts for recovery.
"""

from typing import Optional
from datetime import datetime
from uuid import UUID

from app.shared.models.base import (
    Base, func,
    String, Text, DateTime, Boolean,
    ForeignKey, Index,
    Mapped, mapped_column
)
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE, JSONB


class AbandonedCart(Base):
    """
    Tracks abandoned shopping carts for potential recovery.

    Stores cart data for users who didn't complete checkout.
    """
    __tablename__ = "abandoned_cart"

    # Primary Key
    abandoned_cart_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    # Foreign Keys
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    restaurant_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        ForeignKey("restaurant_table.restaurant_id", ondelete="SET NULL"),
        nullable=True
    )

    # Cart Data
    cart_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    cart_items_count: Mapped[Optional[int]] = mapped_column(default=0)
    cart_total: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Status
    recovery_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    recovery_attempted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    recovered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    recovered_order_id: Mapped[Optional[UUID]] = mapped_column(
        UUID_TYPE(as_uuid=True),
        nullable=True
    )

    # Reason
    abandonment_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_activity: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

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
        Index('idx_abandoned_cart_user', 'user_id'),
        Index('idx_abandoned_cart_session', 'session_id'),
        Index('idx_abandoned_cart_recovery_status', 'recovery_status'),
        Index('idx_abandoned_cart_created', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<AbandonedCart(id='{self.abandoned_cart_id}', items={self.cart_items_count})>"


__all__ = ["AbandonedCart"]
