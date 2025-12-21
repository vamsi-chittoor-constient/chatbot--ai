"""
AbandonedBooking Model
======================

Abandoned booking persistence for recovery workflows.
Stores partial booking data when user logs out mid-booking.
"""

from app.shared.models.base import (
    Base, func, datetime, Optional,
    String, DateTime, Boolean, Integer, JSON,
    ForeignKey, Index,
    relationship, Mapped, mapped_column
)


class AbandonedBooking(Base):
    """
    Abandoned booking persistence for recovery workflows.
    Stores partial booking data when user logs out mid-booking.
    """
    __tablename__ = "abandoned_bookings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("user_devices.device_id"), nullable=True, index=True)

    booking_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    party_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    booking_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    abandoned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    restored: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    restored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_to_booking_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    restaurant_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("restaurant_config.id"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    # user: Mapped[Optional["User"]] = relationship("User", back_populates="abandoned_bookings")

    __table_args__ = (
        Index('idx_abandoned_bookings_user_id', 'user_id'),
        Index('idx_abandoned_bookings_device_id', 'device_id'),
        Index('idx_abandoned_bookings_expires_at', 'expires_at'),
        Index('idx_abandoned_bookings_restored', 'restored'),
        Index('idx_abandoned_bookings_date', 'booking_date'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<AbandonedBooking(id='{self.id}', party_size={self.party_size}, restored={self.restored})>"


__all__ = ["AbandonedBooking"]
