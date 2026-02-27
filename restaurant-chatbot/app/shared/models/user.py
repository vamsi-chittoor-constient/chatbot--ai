"""
User Models
===========

Database models for user feature.

Models in this file:
- User
- UserPreferences
- UserDevice
- SessionToken
- UserFavorite
- UserBrowsingHistory
"""

from app.shared.models.base import (
    Base, func, datetime, Optional, List,
    String, Text, DateTime, Boolean, JSON, Integer,
    ForeignKey, UniqueConstraint, Index, CheckConstraint,
    Decimal, Numeric, Date, Time, ARRAY, Vector,
    relationship, Mapped, mapped_column,
    UserStatus, BookingStatus, OrderStatus, PaymentStatus,
    MessageDirection, MessageChannel, ComplaintStatus,
    PG_UUID, text
)


class User(Base):
    """
    User account information and authentication.
    Supports progressive authentication from anonymous to registered users.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    phone_number: Mapped[Optional[str]] = mapped_column(String(20), unique=True, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default=None)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # Security and account lockout
    failure_login_attempt: Mapped[int] = mapped_column(Integer, default=0)
    is_user_temporary_locked: Mapped[bool] = mapped_column(Boolean, default=False)
    temporary_lock_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Personalization fields
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False),
                                                          server_default=func.now(), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False),
                                                          server_default=func.now(),
                                                          onupdate=func.now(), nullable=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    # bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="user")
    # orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user")
    user_preferences: Mapped[Optional["UserPreferences"]] = relationship("UserPreferences",
                                                                        back_populates="user",
                                                                        uselist=False)
    # complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="user")
    # ratings: Mapped[List["Rating"]] = relationship("Rating", back_populates="user")
    # feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="user")
    # waitlist_entries: Mapped[List["Waitlist"]] = relationship("Waitlist", back_populates="user")
    message_logs: Mapped[List["MessageLog"]] = relationship("MessageLog", back_populates="user")
    email_logs: Mapped[List["EmailLog"]] = relationship("EmailLog", back_populates="user")
    # Note: Commented out due to duplicate PaymentOrder class names in codebase
    # (app.shared.models.payment.PaymentOrder vs app.features.food_ordering.models.payment_order.PaymentOrder)
    # payment_orders: Mapped[List["PaymentOrder"]] = relationship("PaymentOrder", back_populates="user")
    # payment_transactions: Mapped[List["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="user")
    # abandoned_carts: Mapped[List["AbandonedCart"]] = relationship("AbandonedCart", back_populates="user")
    # abandoned_bookings: Mapped[List["AbandonedBooking"]] = relationship("AbandonedBooking", back_populates="user")

    __table_args__ = (
        CheckConstraint('phone_number IS NOT NULL OR email IS NOT NULL OR is_anonymous = true',
                       name='user_contact_check'),
        Index('idx_users_phone', 'phone_number'),
        Index('idx_users_email', 'email'),
        Index('idx_users_status', 'status'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        contact = self.phone_number or self.email or "anonymous"
        return f"<User(id='{self.id[:8]}...', contact='{contact}')>"





class UserPreferences(Base):
    """
    User dietary preferences, allergies, and dining preferences.
    Used by agents for personalized recommendations.
    """
    __tablename__ = "user_preferences"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("users.id"), unique=True)
    dietary_restrictions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    allergies: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    favorite_cuisines: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    preferred_seating: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    special_occasions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="user_preferences")

    __table_args__ = (
        Index('idx_user_preferences_user_id', 'user_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<UserPreferences(user_id='{self.user_id[:8]}...')>"





class UserDevice(Base):
    """
    Device tracking for soft personalization (multi-tier identity system).
    Links anonymous device_id to authenticated user_id after first authentication.

    Enables:
    - Tier 1: Anonymous (no device_id)
    - Tier 2: Recognized device (device_id, no auth) - soft personalization
    - Tier 3: Authenticated (session_token or recent OTP) - full personalization
    """
    __tablename__ = "user_devices"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("users.id"), nullable=True)

    # Device fingerprint (optional, for analytics)
    device_fingerprint: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Tracking
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())

    # Soft personalization data (before full auth)
    last_order_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    preferred_items: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    session_tokens: Mapped[List["SessionToken"]] = relationship("SessionToken", back_populates="device")

    __table_args__ = (
        Index('idx_user_devices_device_id', 'device_id'),
        Index('idx_user_devices_user_id', 'user_id'),
        Index('idx_user_devices_device_user', 'device_id', 'user_id'),
        Index('idx_user_devices_last_seen', 'last_seen_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        user_id_str = self.user_id[:8] if self.user_id else 'None'
        return f"<UserDevice(device_id='{self.device_id[:15]}...', user_id='{user_id_str}...')>"





class SessionToken(Base):
    """
    Long-lived session tokens for returning users (30-day expiry).
    Enables frictionless return visits with full personalization.
    Issued after successful OTP authentication.
    """
    __tablename__ = "session_tokens"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)  # Increased from 100 to 512 for JWT tokens
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("user_devices.device_id"),
                                                     nullable=True)

    # Token metadata
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())

    # Security
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    # IP tracking (optional, for security)
    issued_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    last_used_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")
    device: Mapped[Optional["UserDevice"]] = relationship("UserDevice", back_populates="session_tokens")

    __table_args__ = (
        Index('idx_session_tokens_token', 'token'),
        Index('idx_session_tokens_user_id', 'user_id'),
        Index('idx_session_tokens_device_id', 'device_id'),
        Index('idx_session_tokens_expires_at', 'expires_at'),
        Index('idx_session_tokens_token_user', 'token', 'user_id'),
        CheckConstraint('expires_at > issued_at', name='chk_session_token_expiry_valid'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<SessionToken(user_id='{self.user_id[:8]}...', expires={self.expires_at}, revoked={self.is_revoked})>"





class UserFavorite(Base):
    """
    User favorite menu items for quick ordering.
    Enables personalized recommendations and fast reordering.
    """
    __tablename__ = "user_favorites"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    menu_item_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("menu_item.menu_item_id"), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem")

    __table_args__ = (
        UniqueConstraint('user_id', 'menu_item_id', name='unique_user_favorite'),
        Index('idx_user_favorites_user_id', 'user_id'),
        Index('idx_user_favorites_menu_item_id', 'menu_item_id'),
        Index('idx_user_favorites_user_created', 'user_id', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<UserFavorite(user_id='{self.user_id[:8]}...', menu_item_id='{str(self.menu_item_id)[:8]}...')>"





class UserBrowsingHistory(Base):
    """
    User browsing history for menu items.
    Tracks item views for analytics and "Continue browsing" features.
    """
    __tablename__ = "user_browsing_history"

    id: Mapped[str] = mapped_column(
        PG_UUID(as_uuid=False),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    menu_item_id: Mapped[str] = mapped_column(PG_UUID(as_uuid=False), ForeignKey("menu_item.menu_item_id"), nullable=False)

    # View details
    view_count: Mapped[int] = mapped_column(Integer, default=1)
    first_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                      server_default=func.now())
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                     server_default=func.now())

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem")

    __table_args__ = (
        UniqueConstraint('user_id', 'menu_item_id', name='unique_user_browsing_history'),
        Index('idx_user_browsing_history_user_id', 'user_id'),
        Index('idx_user_browsing_history_menu_item_id', 'menu_item_id'),
        Index('idx_user_browsing_history_user_last_viewed', 'user_id', 'last_viewed_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<UserBrowsingHistory(user_id='{self.user_id[:8]}...', menu_item_id='{str(self.menu_item_id)[:8]}...', views={self.view_count})>"


# Restaurant Operations Models



