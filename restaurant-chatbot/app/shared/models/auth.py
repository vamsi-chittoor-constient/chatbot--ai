"""
Auth Models
===========

Database models for auth feature.

Models in this file:
- OTPVerification
- AuthSession
- OTPRateLimit
"""

import uuid
from app.shared.models.base import (
    Base, func, datetime, Optional, List,
    String, Text, DateTime, Boolean, JSON, Integer,
    ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Decimal, Numeric, Date, Time, ARRAY, Vector,
    relationship, Mapped, mapped_column,
    UserStatus, BookingStatus, OrderStatus, PaymentStatus,
    MessageDirection, MessageChannel, ComplaintStatus
)

def generate_short_id() -> str:
    """Generate a short unique ID (20 chars max)"""
    return str(uuid.uuid4())[:20]


class OTPVerification(Base):
    """
    One-time password verification for phone number and email verification.
    Temporary storage for OTP codes with automatic expiry.
    """
    __tablename__ = "otp_verification"

    id: Mapped[str] = mapped_column(String(20), primary_key=True, default=generate_short_id)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    otp_code: Mapped[str] = mapped_column(String(10), nullable=False)
    purpose: Mapped[str] = mapped_column(String(50), nullable=False)  # 'registration', 'login', 'booking'
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=False), nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False),
                                                          server_default=func.now(), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False),
                                                          server_default=func.now(),
                                                          onupdate=func.now(), nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        Index('idx_otp_phone', 'phone_number'),
        Index('idx_otp_expires', 'expires_at'),
        Index('idx_otp_code', 'otp_code'),
        Index('idx_otp_purpose', 'purpose'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OTPVerification(phone='{self.phone_number[:8]}...', purpose='{self.purpose}')>"





class AuthSession(Base):
    """
    Authentication session tracking for security and rate limiting.

    Persists critical auth state to prevent abuse through browser refresh:
    - Lockout state (prevents bypass by refreshing)
    - OTP send count per session (rate limiting)
    - OTP verification attempts
    - Phone number change audit trail
    - Daily OTP rate limiting

    Keyed by device_id (for anonymous users) or user_id (for authenticated users).
    """
    __tablename__ = "auth_sessions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Session identifier (device_id or user_id)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)

    # OTP rate limiting per session
    otp_send_count: Mapped[int] = mapped_column(Integer, default=0)
    last_otp_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    # OTP verification tracking
    otp_verification_attempts: Mapped[int] = mapped_column(Integer, default=0)

    # Phone validation tracking
    phone_validation_attempts: Mapped[int] = mapped_column(Integer, default=0)

    # Lockout mechanism
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    lockout_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Phone number change audit trail
    previous_phone_numbers: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True, default=[])

    # Session metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                               server_default=func.now(),
                                               onupdate=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)

    __table_args__ = (
        CheckConstraint('device_id IS NOT NULL OR user_id IS NOT NULL',
                       name='auth_session_identifier_check'),
        Index('idx_auth_sessions_device_id', 'device_id'),
        Index('idx_auth_sessions_user_id', 'user_id'),
        Index('idx_auth_sessions_phone_number', 'phone_number'),
        Index('idx_auth_sessions_locked_until', 'locked_until'),
        Index('idx_auth_sessions_expires_at', 'expires_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        identifier = self.device_id[:12] if self.device_id else f"user:{self.user_id[:8]}" if self.user_id else "unknown"
        return f"<AuthSession(id='{self.id[:8]}...', identifier='{identifier}...')>"





class OTPRateLimit(Base):
    """
    Daily OTP rate limiting per phone number.

    Tracks OTP sends across all sessions to prevent SMS abuse.
    Prevents users from bypassing per-session limits by refreshing browser.
    """
    __tablename__ = "otp_rate_limits"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    # Daily tracking
    date: Mapped[datetime] = mapped_column(Date, nullable=False)
    send_count: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    first_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                                   server_default=func.now())
    last_sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                                  server_default=func.now())

    __table_args__ = (
        UniqueConstraint('phone_number', 'date', name='uq_otp_rate_limit_phone_date'),
        Index('idx_otp_rate_limits_phone_date', 'phone_number', 'date'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OTPRateLimit(phone='{self.phone_number[:8]}...', date='{self.date}', count={self.send_count})>"


# Customer Satisfaction Agent Models



