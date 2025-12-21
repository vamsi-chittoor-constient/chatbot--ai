"""
OrderSourceType Model
=====================
Lookup table for order source types (app, web, pos, etc.).
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
from sqlalchemy.dialects.postgresql import UUID as UUID_TYPE


class OrderSourceType(Base):
    """
    Lookup table for order source types.

    Examples: app, web, pos, phone, walk_in
    """
    __tablename__ = "order_source_type"

    order_source_type_id: Mapped[UUID] = mapped_column(
        UUID_TYPE(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    order_source_type_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    order_source_type_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

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
        Index('idx_order_source_type_code', 'order_source_type_code'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OrderSourceType(code='{self.order_source_type_code}', name='{self.order_source_type_name}')>"


__all__ = ["OrderSourceType"]
