"""
Booking Model
=============

Restaurant table booking/reservation management.
Supports waitlist functionality when tables are full.
"""

from app.shared.models.base import (
    Base, func, datetime, Optional,
    String, Text, DateTime, Boolean, Integer, Date, Time,
    ForeignKey, Index, CheckConstraint,
    relationship, Mapped, mapped_column
)


class Booking(Base):
    """
    Restaurant table booking/reservation management.
    Supports waitlist functionality when tables are full.
    """
    __tablename__ = "bookings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("user_devices.device_id"), nullable=True)
    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"))
    table_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("tables.id"), nullable=True)

    # Match actual database schema
    booking_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default='scheduled')  # Lifecycle status (scheduled/confirmed/completed/no_show)
    booking_status: Mapped[str] = mapped_column(String(20), nullable=False, default='active')  # Modification tracking (active/modified/cancelled)
    special_requests: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Additional columns that exist in database
    booking_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)  # Date part only
    booking_time: Mapped[Optional[datetime]] = mapped_column(Time, nullable=True)  # Time part only

    # BookingAgent advanced features - now available in database
    guest_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confirmation_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    is_waitlisted: Mapped[bool] = mapped_column(Boolean, default=False)
    waitlist_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reminder_sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Audit trail and source tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    origin_of_booking: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    # user: Mapped["User"] = relationship("User", back_populates="bookings")
    # restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="bookings")
    # table: Mapped[Optional["Table"]] = relationship("Table", back_populates="bookings")

    __table_args__ = (
        Index('idx_bookings_user', 'user_id'),
        Index('idx_bookings_datetime', 'booking_datetime'),
        Index('idx_bookings_status', 'status'),
        Index('idx_bookings_booking_status', 'booking_status'),
        Index('idx_bookings_device_id', 'device_id'),
        Index('idx_bookings_waitlist', 'is_waitlisted', 'waitlist_position'),
        Index('idx_bookings_confirmation', 'confirmation_code'),
        Index('idx_bookings_guest_name', 'guest_name'),
        CheckConstraint('user_id IS NOT NULL OR device_id IS NOT NULL', name='booking_identity_check'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Booking(id='{self.id[:8]}...', datetime={self.booking_datetime}, party_size={self.party_size})>"


__all__ = ["Booking"]
