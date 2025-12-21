"""
SQLAlchemy models for the Restaurant AI Assistant.

This module defines all database models using SQLAlchemy ORM,
including relationships, constraints, and vector support for embeddings.

Models are organized by functional areas:
- User Management
- Restaurant Operations
- Booking System
- Order Management
- Payment Processing
- Communication
- Analytics & Feedback
- System Operations
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Text, DateTime, Boolean, JSON, Date, Time,
    ForeignKey, UniqueConstraint, Index, CheckConstraint, Enum as SQLEnum, Numeric
)
from decimal import Decimal
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import enum

from app.shared.models.base import Base


# Enums for type safety

class UserStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class BookingStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class OrderStatus(enum.Enum):
    DRAFT = "draft"  # Order created but not yet paid (new hybrid flow)
    PENDING = "pending"  # Awaiting payment (legacy - may be deprecated)
    CONFIRMED = "confirmed"  # Payment received, order confirmed
    PREPARING = "preparing"  # Kitchen is preparing the order
    READY = "ready"  # Order ready for pickup/serving
    # DELIVERY FEATURE NOT SUPPORTED - Platform only supports dine-in and takeout
    # OUT_FOR_DELIVERY = "out_for_delivery"
    # DELIVERED = "delivered"
    CANCELLED = "cancelled"  # Order cancelled
    REFUNDED = "refunded"  # Order refunded


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class MessageDirection(enum.Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageChannel(enum.Enum):
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"


class ComplaintStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


# User Management Models

class User(Base):
    """
    User account information and authentication.
    Supports progressive authentication from anonymous to registered users.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
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
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="user")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="user")
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="user")
    user_preferences: Mapped[Optional["UserPreferences"]] = relationship("UserPreferences",
                                                                        back_populates="user",
                                                                        uselist=False)
    complaints: Mapped[List["Complaint"]] = relationship("Complaint", back_populates="user")
    ratings: Mapped[List["Rating"]] = relationship("Rating", back_populates="user")
    feedbacks: Mapped[List["Feedback"]] = relationship("Feedback", back_populates="user")
    waitlist_entries: Mapped[List["Waitlist"]] = relationship("Waitlist", back_populates="user")
    message_logs: Mapped[List["MessageLog"]] = relationship("MessageLog", back_populates="user")
    email_logs: Mapped[List["EmailLog"]] = relationship("EmailLog", back_populates="user")
    payment_orders: Mapped[List["PaymentOrder"]] = relationship("PaymentOrder", back_populates="user")
    payment_transactions: Mapped[List["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="user")
    abandoned_carts: Mapped[List["AbandonedCart"]] = relationship("AbandonedCart", back_populates="user")
    abandoned_bookings: Mapped[List["AbandonedBooking"]] = relationship("AbandonedBooking", back_populates="user")

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

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), unique=True)
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

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)

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

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)  # Increased from 100 to 512 for JWT tokens
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
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

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    menu_item_id: Mapped[str] = mapped_column(String(20), ForeignKey("menu_items.id"), nullable=False)

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
        return f"<UserFavorite(user_id='{self.user_id[:8]}...', menu_item_id='{self.menu_item_id[:8]}...')>"


class UserBrowsingHistory(Base):
    """
    User browsing history for menu items.
    Tracks item views for analytics and "Continue browsing" features.
    """
    __tablename__ = "user_browsing_history"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    menu_item_id: Mapped[str] = mapped_column(String(20), ForeignKey("menu_items.id"), nullable=False)

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
        return f"<UserBrowsingHistory(user_id='{self.user_id[:8]}...', menu_item_id='{self.menu_item_id[:8]}...', views={self.view_count})>"


# Restaurant Operations Models

class Restaurant(Base):
    """
    Restaurant configuration information.
    Matches actual restaurant_config table structure in database.
    Supports multi-branch restaurant chains.
    """
    __tablename__ = "restaurant_config"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    restaurant_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Chain/brand identifier
    branch_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Unique branch identifier
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    branch_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Branch-specific display name
    branch_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Short branch code (MUM, DEL, etc.)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    business_hours: Mapped[dict] = mapped_column(JSON, nullable=False)
    policies: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Restaurant-specific settings (meal times, etc.)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False),
                                                          server_default=func.now(), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False),
                                                          server_default=func.now(),
                                                          onupdate=func.now(), nullable=True)

    # Relationships
    menu_categories: Mapped[List["MenuCategory"]] = relationship("MenuCategory", back_populates="restaurant")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="restaurant")
    tables: Mapped[List["Table"]] = relationship("Table", back_populates="restaurant")

    __table_args__ = ({'extend_existing': True},)

    def __repr__(self) -> str:
        return f"<Restaurant(name='{self.name}')>"


class Table(Base):
    """
    Restaurant table information for booking management.
    """
    __tablename__ = "tables"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"))
    table_number: Mapped[str] = mapped_column(String(20), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    features: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="tables")
    bookings: Mapped[List["Booking"]] = relationship("Booking", back_populates="table")

    __table_args__ = (
        UniqueConstraint('restaurant_id', 'table_number', name='unique_table_per_restaurant'),
        Index('idx_tables_restaurant', 'restaurant_id'),
        Index('idx_tables_capacity', 'capacity'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Table(number='{self.table_number}', capacity={self.capacity})>"


class MenuCategory(Base):
    """
    Menu category organization (Appetizers, Main Course, etc.)
    Supports hierarchical categories via parent_category_id.
    """
    __tablename__ = "menu_categories"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"))
    parent_category_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("menu_categories.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_timings: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category_image_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_categories")
    menu_items: Mapped[List["MenuItem"]] = relationship("MenuItem", back_populates="category")

    __table_args__ = (
        UniqueConstraint('restaurant_id', 'name', name='unique_category_per_restaurant'),
        Index('idx_menu_categories_restaurant', 'restaurant_id'),
        Index('idx_menu_categories_order', 'display_order'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuCategory(name='{self.name}')>"


class MenuItem(Base):
    """
    Individual menu items with pricing and availability.
    Includes vector embeddings for semantic search capabilities.

    Inventory Management (3-column system):
    - total_stock_quantity: Physical count in kitchen (manager updates this)
    - reserved_quantity: Items currently in customer carts (synced from Redis)
    - available_quantity: Can be ordered (calculated: total_stock - reserved)
    """
    __tablename__ = "menu_items"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    category_id: Mapped[str] = mapped_column(String(20), ForeignKey("menu_categories.id"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    ingredients: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    allergens: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    dietary_info: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    spice_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    prep_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    calories: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)
    availability_schedule: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Time-based availability
    availability_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Time slot when available (e.g., "breakfast", "lunch", "dinner")
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False)
    is_seasonal: Mapped[bool] = mapped_column(Boolean, default=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)

    # Inventory management columns (3-column system for real-time tracking)
    total_stock_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
                                                      comment="Physical count in kitchen - set by manager")
    reserved_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
                                                   comment="Items in customer carts - synced from Redis")
    available_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0,
                                                    comment="Can be ordered (total_stock - reserved)")

    # Enhanced availability fields
    day_availability: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    nutrition: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    alternative_recommendations: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    addon: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    category: Mapped["MenuCategory"] = relationship("MenuCategory", back_populates="menu_items")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="menu_item")

    __table_args__ = (
        Index('idx_menu_items_category', 'category_id'),
        Index('idx_menu_items_price', 'price'),
        Index('idx_menu_items_available', 'is_available'),
        Index('idx_menu_items_popular', 'is_popular'),
        Index('idx_menu_items_embedding', 'embedding', postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64},
              postgresql_ops={'embedding': 'vector_cosine_ops'}),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MenuItem(name='{self.name}', price={self.price})>"


# Booking System Models

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
    table_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("tables.id"),
                                                   nullable=True)
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="bookings")
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="bookings")
    table: Mapped[Optional["Table"]] = relationship("Table", back_populates="bookings")

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


# Order Management Models

class Order(Base):
    """
    Food order management - DINE-IN and TAKEOUT ONLY.

    DELIVERY FEATURE NOT SUPPORTED - Platform only supports dine-in and takeout orders.
    """
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(255), ForeignKey("user_devices.device_id"), nullable=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("bookings.id"),
                                                     nullable=True)
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)  # dine_in, takeout ONLY (delivery not supported)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    discount_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_ready_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # DELIVERY FEATURE NOT SUPPORTED - Field kept for database compatibility but not used
    delivery_address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tip_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    contact_phone: Mapped[str] = mapped_column(String(20), nullable=False)

    # Dine-in specific fields
    table_no: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    no_of_persons: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Takeout specific fields
    packing_charges: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    pc_tax_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)

    # Audit trail and payment tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    callback_received_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    booking: Mapped[Optional["Booking"]] = relationship("Booking")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order")
    payments: Mapped[List["Payment"]] = relationship("Payment", back_populates="order")
    payment_order: Mapped[Optional["PaymentOrder"]] = relationship("PaymentOrder", back_populates="order", uselist=False)

    __table_args__ = (
        Index('idx_orders_user', 'user_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_type', 'order_type'),
        Index('idx_orders_date', 'created_at'),
        Index('idx_orders_number', 'order_number'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Order(number='{self.order_number}', total={self.total_amount})>"


class OrderItem(Base):
    """
    Individual items within an order with quantities and customizations.
    """
    __tablename__ = "order_items"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(20), ForeignKey("orders.id"))
    menu_item_id: Mapped[str] = mapped_column(String(20), ForeignKey("menu_items.id"))
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    customizations: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    special_instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    legacy_modifications: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    menu_item: Mapped["MenuItem"] = relationship("MenuItem", back_populates="order_items")

    __table_args__ = (
        Index('idx_order_items_order', 'order_id'),
        Index('idx_order_items_menu_item', 'menu_item_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<OrderItem(menu_item={self.menu_item_id[:8]}..., quantity={self.quantity})>"


# Payment Processing Models

class Payment(Base):
    """
    Payment transaction records with Razorpay integration.
    """
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(20), ForeignKey("orders.id"))
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    refund_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payments")

    __table_args__ = (
        Index('idx_payments_order', 'order_id'),
        Index('idx_payments_status', 'status'),
        Index('idx_payments_razorpay', 'razorpay_payment_id'),
        Index('idx_payments_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Payment(id='{self.id[:8]}...', amount={self.amount}, status={self.status})>"


class PaymentOrder(Base):
    """
    Payment orders linking restaurant orders to Razorpay orders.
    Manages payment links, expiry, and retry logic.
    """
    __tablename__ = "payment_orders"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    order_id: Mapped[str] = mapped_column(String(20), ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)  # Nullable for safety (Tier 1 users should authenticate before payment, but nullable as fallback)
    razorpay_order_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # Amount in paise
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="created", nullable=False)
    payment_link: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_link_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retry_attempts: Mapped[int] = mapped_column(Integer, default=3)
    notes: Mapped[Optional[dict]] = mapped_column(JSON, default=lambda: {})
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(), onupdate=func.now())

    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="payment_order")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="payment_orders")  # Optional since user_id can be null
    payment_transactions: Mapped[List["PaymentTransaction"]] = relationship("PaymentTransaction", back_populates="payment_order")
    retry_attempts: Mapped[List["PaymentRetryAttempt"]] = relationship("PaymentRetryAttempt", back_populates="payment_order")

    __table_args__ = (
        Index('idx_payment_orders_order_id', 'order_id'),
        Index('idx_payment_orders_user_id', 'user_id'),
        Index('idx_payment_orders_razorpay_order_id', 'razorpay_order_id'),
        Index('idx_payment_orders_status', 'status'),
        Index('idx_payment_orders_expires_at', 'expires_at'),
        CheckConstraint('amount > 0', name='chk_payment_order_amount_positive'),
        CheckConstraint("currency IN ('INR', 'USD', 'EUR')", name='chk_payment_order_currency_valid'),
        CheckConstraint('retry_count >= 0 AND retry_count <= max_retry_attempts', name='chk_payment_order_retry_count_valid'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentOrder(id={self.id}, order_id='{self.order_id[:8]}...', amount={self.amount})>"


class PaymentTransaction(Base):
    """
    Individual payment transactions with comprehensive Razorpay data.
    Tracks actual payment attempts and their outcomes.
    """
    __tablename__ = "payment_transactions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    payment_order_id: Mapped[str] = mapped_column(String(20), ForeignKey("payment_orders.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    order_id: Mapped[str] = mapped_column(String(20), ForeignKey("orders.id"), nullable=False)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(255), nullable=False)
    razorpay_signature: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_paid: Mapped[int] = mapped_column(Integer, default=0)
    amount_due: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    method: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # card, upi, netbanking, wallet
    status: Mapped[str] = mapped_column(String(50), default="created")  # created, authorized, captured, failed, refunded
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    gateway_response: Mapped[Optional[dict]] = mapped_column(JSON, default=lambda: {})
    bank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    wallet: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    vpa: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # UPI Virtual Payment Address
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fee: Mapped[int] = mapped_column(Integer, default=0)  # Razorpay fee
    tax: Mapped[int] = mapped_column(Integer, default=0)  # Tax on fee
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(), onupdate=func.now())

    # Relationships
    payment_order: Mapped["PaymentOrder"] = relationship("PaymentOrder", back_populates="payment_transactions")
    user: Mapped["User"] = relationship("User", back_populates="payment_transactions")
    order: Mapped["Order"] = relationship("Order")

    __table_args__ = (
        Index('idx_payment_transactions_payment_order_id', 'payment_order_id'),
        Index('idx_payment_transactions_user_id', 'user_id'),
        Index('idx_payment_transactions_order_id', 'order_id'),
        Index('idx_payment_transactions_razorpay_payment_id', 'razorpay_payment_id'),
        Index('idx_payment_transactions_status', 'status'),
        CheckConstraint('amount > 0', name='chk_payment_transaction_amount_positive'),
        CheckConstraint("currency IN ('INR', 'USD', 'EUR')", name='chk_payment_transaction_currency_valid'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentTransaction(id={self.id}, razorpay_payment_id='{self.razorpay_payment_id}', status={self.status})>"


class WebhookEvent(Base):
    """
    Razorpay webhook events for reliability and debugging.
    Ensures all webhook events are processed exactly once.
    """
    __tablename__ = "webhook_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    account_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    entity_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_webhook_events_event_id', 'event_id'),
        Index('idx_webhook_events_event_type', 'event_type'),
        Index('idx_webhook_events_processed', 'processed'),
        Index('idx_webhook_events_created_at', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<WebhookEvent(id={self.id}, event_type='{self.event_type}', processed={self.processed})>"


class PaymentRetryAttempt(Base):
    """
    Track all payment retry attempts for analytics and debugging.
    """
    __tablename__ = "payment_retry_attempts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    payment_order_id: Mapped[str] = mapped_column(String(20), ForeignKey("payment_orders.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(50))  # attempted, failed, abandoned
    failure_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    attempted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    payment_order: Mapped["PaymentOrder"] = relationship("PaymentOrder", back_populates="retry_attempts")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        Index('idx_payment_retry_attempts_payment_order_id', 'payment_order_id'),
        Index('idx_payment_retry_attempts_user_id', 'user_id'),
        UniqueConstraint('payment_order_id', 'attempt_number', name='uq_payment_retry_attempt'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<PaymentRetryAttempt(id={self.id}, attempt_number={self.attempt_number}, status={self.status})>"


# Communication Models

class Session(Base):
    """
    User sessions for tracking anonymous and authenticated users.
    """
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    session_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                               server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=False), nullable=True)
    last_activity: Mapped[datetime] = mapped_column(DateTime(timezone=False),
                                                   server_default=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="sessions")
    conversations: Mapped[List["Conversation"]] = relationship("Conversation", back_populates="session")

    __table_args__ = (
        Index('idx_sessions_session_id', 'session_id'),
        Index('idx_sessions_user_id', 'user_id'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Session(id='{self.id[:8]}...', session_id='{self.session_id[:8]}...')>"


class Conversation(Base):
    """
    User conversation sessions with AI agents.
    Tracks conversation context and agent handoffs.
    """
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("sessions.id"), nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active")  # Match DB column
    context: Mapped[dict] = mapped_column(JSON, default=dict)  # Match DB column name
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="conversations")
    session: Mapped[Optional["Session"]] = relationship("Session", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship("Message", back_populates="conversation")

    __table_args__ = (
        Index('idx_conversations_user', 'user_id'),
        Index('idx_conversations_session', 'session_id'),
        Index('idx_conversations_status', 'status'),  # Updated to match actual DB column
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        user_id_str = self.user_id[:8] if self.user_id else 'None'
        return f"<Conversation(id='{self.id[:8]}...', user_id='{user_id_str}...')>"


class Message(Base):
    """
    Individual messages in conversations.
    Compatible with LangGraph message format (uses 'role' field).
    """
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(20), ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # user, assistant, system (LangGraph compatible)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    agent_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # Use meta_data to avoid conflict with Base.metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    __table_args__ = (
        Index('idx_messages_conversation', 'conversation_id'),
        Index('idx_messages_role', 'role'),
        Index('idx_messages_agent', 'agent_name'),
        Index('idx_messages_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(role={self.role}, agent={self.agent_name}, content='{content_preview}')>"


# Analytics & Feedback Models

class Complaint(Base):
    """
    Customer complaints and issue tracking.
    Integrates with sentiment analysis for prioritization.
    Supports SLA tracking with started_at and completed_at timestamps.
    """
    __tablename__ = "complaints"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"))
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"),
                                                   nullable=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("bookings.id"),
                                                     nullable=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    ticket_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default="medium")
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    tone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mood: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="open")
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(250), nullable=True)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Audit trail and lifecycle tracking
    created_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="complaints")
    order: Mapped[Optional["Order"]] = relationship("Order")
    booking: Mapped[Optional["Booking"]] = relationship("Booking")

    __table_args__ = (
        Index('idx_complaints_user', 'user_id'),
        Index('idx_complaints_status', 'status'),
        Index('idx_complaints_priority', 'priority'),
        Index('idx_complaints_sentiment', 'sentiment_score'),
        Index('idx_complaints_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Complaint(id='{self.id[:8]}...', title='{self.title[:30]}...', status={self.status})>"


class Rating(Base):
    """
    Customer ratings and feedback for orders and overall experience.
    """
    __tablename__ = "ratings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(20), ForeignKey("users.id"))
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"),
                                                   nullable=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("bookings.id"),
                                                     nullable=True)
    rating_type: Mapped[str] = mapped_column(String(50), nullable=False)  # food, service, ambiance, overall
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    max_rating: Mapped[int] = mapped_column(Integer, default=5)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ratings")
    order: Mapped[Optional["Order"]] = relationship("Order")
    booking: Mapped[Optional["Booking"]] = relationship("Booking")

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= max_rating', name='rating_range_check'),
        Index('idx_ratings_user', 'user_id'),
        Index('idx_ratings_type', 'rating_type'),
        Index('idx_ratings_rating', 'rating'),
        Index('idx_ratings_public', 'is_public'),
        Index('idx_ratings_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Rating(user_id='{self.user_id[:8]}...', type='{self.rating_type}', rating={self.rating})>"


class Feedback(Base):
    """
    General customer feedback table.
    Used for collecting user feedback on various aspects of the service.
    """
    __tablename__ = "feedback"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"), nullable=True)
    booking_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("bookings.id"), nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2), nullable=True)
    sentiment_label: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    feedback_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="feedbacks")
    order: Mapped[Optional["Order"]] = relationship("Order")
    booking: Mapped[Optional["Booking"]] = relationship("Booking")

    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5', name='feedback_rating_check'),
        Index('idx_feedback_user', 'user_id'),
        Index('idx_feedback_order', 'order_id'),
        Index('idx_feedback_booking', 'booking_id'),
        Index('idx_feedback_type', 'feedback_type'),
        Index('idx_feedback_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Feedback(id='{self.id[:8]}...', type='{self.feedback_type}', rating={self.rating})>"


class Waitlist(Base):
    """
    Waitlist for customers when tables are unavailable.
    Alternative to immediate booking when restaurant is at capacity.
    """
    __tablename__ = "waitlist"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    requested_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    party_size: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="waitlist_entries")

    __table_args__ = (
        Index('idx_waitlist_user', 'user_id'),
        Index('idx_waitlist_datetime', 'requested_datetime'),
        Index('idx_waitlist_status', 'status'),
        Index('idx_waitlist_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<Waitlist(id='{self.id[:8]}...', party_size={self.party_size}, status='{self.status}')>"



# System Operations Models

class AgentMemory(Base):
    """
    Persistent storage for agent-specific memory across conversations.
    Supports both short-term and long-term memory with Redis backup.
    """
    __tablename__ = "agent_memory"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)  # Match DB: varchar(50)
    memory_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # expires_at column removed - doesn't exist in database
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint('user_id', 'agent_name', 'memory_type',
                        name='unique_agent_memory_per_user'),
        Index('idx_agent_memory_user', 'user_id'),
        Index('idx_agent_memory_agent', 'agent_name'),
        Index('idx_agent_memory_type', 'memory_type'),
        # Removed expires_at index - column doesn't exist in database
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        user_id_str = self.user_id[:8] if self.user_id else 'None'
        return f"<AgentMemory(user_id='{user_id_str}...', agent='{self.agent_name}', type='{self.memory_type}')>"


class SystemLog(Base):
    """
    System-wide logging for debugging and monitoring.
    Complements application logging with structured database storage.
    """
    __tablename__ = "system_logs"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    level: Mapped[str] = mapped_column(String(10), nullable=False)  # Match DB: varchar(10)
    service: Mapped[str] = mapped_column(String(100), nullable=False)  # Match DB column name
    message: Mapped[str] = mapped_column(Text, nullable=False)
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Use meta_data to avoid conflict with Base.metadata
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False),  # Match DB: timestamp without time zone
                                               server_default=func.now())

    __table_args__ = (
        Index('idx_system_logs_level', 'level'),
        Index('idx_system_logs_service', 'service'),  # Updated to match DB column
        Index('idx_system_logs_created_at', 'created_at'),  # Match DB index name
        # Removed user_id and session_id indices - columns don't exist
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<SystemLog(level='{self.level}', service='{self.service}')>"


class KnowledgeBase(Base):
    """
    Knowledge base for storing FAQs, policies, and other reference documents.
    Supports vector search for semantic similarity matching.
    """
    __tablename__ = "knowledge_base"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)  # OpenAI embeddings
    meta_data: Mapped[dict] = mapped_column(JSON, default=dict)  # Use meta_data to avoid conflict with Base.metadata
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_knowledge_base_type', 'document_type'),
        Index('idx_knowledge_base_category', 'category'),
        Index('idx_knowledge_base_active', 'is_active'),
        Index('idx_knowledge_base_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<KnowledgeBase(id='{self.id[:8]}...', title='{self.title[:30]}...')>"


class MessageTemplate(Base):
    """
    Reusable message templates for communication across different channels.
    Supports variable substitution for personalized messages.
    """
    __tablename__ = "message_templates"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    template_type: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    template_content: Mapped[str] = mapped_column(Text, nullable=False)
    variables: Mapped[list] = mapped_column(JSON, default=list)  # List of variable names
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_message_templates_type', 'template_type'),
        Index('idx_message_templates_channel', 'channel'),
        Index('idx_message_templates_active', 'is_active'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MessageTemplate(name='{self.name}', type='{self.template_type}', channel='{self.channel}')>"


class MessageLog(Base):
    """
    Log of all messages sent through various channels (SMS, Email, WhatsApp).
    Tracks delivery status and retry attempts.
    """
    __tablename__ = "message_logs"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    template_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("message_templates.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    message_type: Mapped[str] = mapped_column(String(100), nullable=False)
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")
    external_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_data: Mapped[dict] = mapped_column(JSON, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="message_logs")
    template: Mapped[Optional["MessageTemplate"]] = relationship("MessageTemplate")

    __table_args__ = (
        Index('idx_message_logs_user', 'user_id'),
        Index('idx_message_logs_channel', 'channel'),
        Index('idx_message_logs_type', 'message_type'),
        Index('idx_message_logs_status', 'status'),
        Index('idx_message_logs_external', 'external_message_id'),
        Index('idx_message_logs_date', 'created_at'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<MessageLog(id='{self.id[:8]}...', channel='{self.channel}', status='{self.status}')>"


class EmailLog(Base):
    """
    Advanced email delivery tracking with bounce, engagement, and unsubscribe management.
    Phase 2 feature for comprehensive email analytics and deliverability monitoring.

    Tracks:
    - Delivery status and bounces
    - Email engagement (opens, clicks)
    - Unsubscribe management
    - Spam reports
    - SMTP provider responses
    """
    __tablename__ = "email_logs"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    message_log_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("message_logs.id"), nullable=True)

    # Email details
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    html_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plain_text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Delivery tracking
    status: Mapped[str] = mapped_column(String(50), default="queued", nullable=False)  # queued, sent, delivered, bounced, failed
    smtp_message_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    smtp_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    smtp_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Bounce handling (Phase 2)
    bounced: Mapped[bool] = mapped_column(Boolean, default=False)
    bounce_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # hard, soft, complaint
    bounce_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Engagement tracking (Phase 2)
    opened: Mapped[bool] = mapped_column(Boolean, default=False)
    first_opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    open_count: Mapped[int] = mapped_column(Integer, default=0)

    clicked: Mapped[bool] = mapped_column(Boolean, default=False)
    first_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    click_count: Mapped[int] = mapped_column(Integer, default=0)
    link_clicks: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # {"url": click_count}

    # Unsubscribe management (Phase 2)
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribe_token: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)

    # Spam tracking (Phase 2)
    spam_reported: Mapped[bool] = mapped_column(Boolean, default=False)
    spam_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Provider tracking
    provider: Mapped[str] = mapped_column(String(50), default="smtp", nullable=False)  # smtp, ses, sendgrid (future)
    provider_metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)

    # Retry tracking
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")
    message_log: Mapped[Optional["MessageLog"]] = relationship("MessageLog")

    __table_args__ = (
        Index('idx_email_logs_user_id', 'user_id'),
        Index('idx_email_logs_recipient', 'recipient_email'),
        Index('idx_email_logs_status', 'status'),
        Index('idx_email_logs_smtp_message_id', 'smtp_message_id'),
        Index('idx_email_logs_bounced', 'bounced'),
        Index('idx_email_logs_opened', 'opened'),
        Index('idx_email_logs_clicked', 'clicked'),
        Index('idx_email_logs_unsubscribed', 'unsubscribed'),
        Index('idx_email_logs_spam_reported', 'spam_reported'),
        Index('idx_email_logs_created_at', 'created_at'),
        Index('idx_email_logs_sent_at', 'sent_at'),
        Index('idx_email_logs_user_status', 'user_id', 'status'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<EmailLog(id='{self.id[:8]}...', recipient='{self.recipient_email}', status='{self.status}')>"


class OTPVerification(Base):
    """
    One-time password verification for phone number and email verification.
    Temporary storage for OTP codes with automatic expiry.
    """
    __tablename__ = "otp_verification"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
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

class CustomerFeedbackDetails(Base):
    """
    Customer feedback and satisfaction tracking for single restaurant.
    Used by CustomerSatisfactionAgent for comprehensive satisfaction tracking.
    """
    __tablename__ = "customer_feedback_details"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Basic feedback info (self-contained for single tenant)
    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"))
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"), nullable=True)
    order_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("orders.id"), nullable=True)

    # Overall feedback
    overall_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 1-5 stars
    feedback_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Detailed ratings breakdown
    food_quality_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    service_speed_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    staff_friendliness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cleanliness_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    value_for_money_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Specific feedback categories
    food_items_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    service_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ambiance_feedback: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Improvement suggestions
    specific_complaints: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    improvement_suggestions: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    would_recommend: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    would_return: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())

    __table_args__ = (
        CheckConstraint('food_quality_rating >= 1 AND food_quality_rating <= 5',
                       name='food_quality_rating_range'),
        CheckConstraint('service_speed_rating >= 1 AND service_speed_rating <= 5',
                       name='service_speed_rating_range'),
        CheckConstraint('staff_friendliness_rating >= 1 AND staff_friendliness_rating <= 5',
                       name='staff_friendliness_rating_range'),
        CheckConstraint('cleanliness_rating >= 1 AND cleanliness_rating <= 5',
                       name='cleanliness_rating_range'),
        CheckConstraint('value_for_money_rating >= 1 AND value_for_money_rating <= 5',
                       name='value_for_money_rating_range'),
        Index('idx_customer_feedback_details_restaurant_id', 'restaurant_id'),
        Index('idx_customer_feedback_details_user_id', 'user_id'),
        Index('idx_customer_feedback_details_would_recommend', 'would_recommend'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<CustomerFeedbackDetails(feedback_id='{self.feedback_id[:8]}...', would_recommend={self.would_recommend})>"


class SatisfactionMetrics(Base):
    """
    Satisfaction metrics tracking for NPS, CSAT, CES scores.
    Used by CustomerSatisfactionAgent for analytics and reporting.
    """
    __tablename__ = "satisfaction_metrics"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"),
                                                  nullable=True)

    # Metric details
    metric_type: Mapped[str] = mapped_column(String(50), nullable=False)  # nps, csat, ces, overall_experience
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_score: Mapped[float] = mapped_column(Numeric(5, 2), default=10.00)

    # Context
    interaction_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # order, booking, support, general
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # order, booking, complaint

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Metadata
    collection_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    additional_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    recorded_date: Mapped[datetime] = mapped_column(Date, server_default=func.current_date())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index('idx_satisfaction_metrics_user_id', 'user_id'),
        Index('idx_satisfaction_metrics_type', 'metric_type'),
        Index('idx_satisfaction_metrics_recorded_date', 'recorded_date'),
        Index('idx_satisfaction_metrics_interaction_type', 'interaction_type'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<SatisfactionMetrics(type='{self.metric_type}', score={self.score}, user_id='{self.user_id[:8] if self.user_id else None}...')>"


class ComplaintResolutionTemplate(Base):
    """
    Template responses for complaint resolution.
    Used by CustomerSatisfactionAgent for consistent complaint handling.
    """
    __tablename__ = "complaint_resolution_templates"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Template details
    template_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Template content
    response_template: Mapped[str] = mapped_column(Text, nullable=False)
    compensation_guidelines: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Usage tracking
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Numeric(5, 2), default=0.00)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_complaint_resolution_templates_category', 'category'),
        Index('idx_complaint_resolution_templates_active', 'is_active'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<ComplaintResolutionTemplate(name='{self.template_name}', category='{self.category}')>"


# General Queries Agent Models

class FAQ(Base):
    """
    Frequently Asked Questions for GeneralQueriesAgent.
    Supports vector search and usage analytics.
    """
    __tablename__ = "faq"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Question details
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Question variations for better matching
    question_variations: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)

    # Metadata
    keywords: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    difficulty_level: Mapped[str] = mapped_column(String(20), default="easy")  # easy, medium, complex

    # Usage statistics
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    last_asked: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    satisfaction_score: Mapped[float] = mapped_column(Numeric(3, 2), default=0.00)

    # Content management
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    display_order: Mapped[int] = mapped_column(Integer, default=100)
    status: Mapped[str] = mapped_column(String(20), default="active")

    # AI enhancement
    embedding: Mapped[Optional[List[float]]] = mapped_column(Vector(1536), nullable=True)
    confidence_threshold: Mapped[float] = mapped_column(Numeric(3, 2), default=0.80)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())

    __table_args__ = (
        Index('idx_faq_category', 'category'),
        Index('idx_faq_keywords', 'keywords', postgresql_using='gin'),
        Index('idx_faq_question_count', 'question_count'),
        Index('idx_faq_featured', 'is_featured', 'display_order'),
        Index('idx_faq_embedding', 'embedding', postgresql_using='hnsw',
              postgresql_with={'m': 16, 'ef_construction': 64}, postgresql_ops={'embedding': 'vector_cosine_ops'}),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<FAQ(category='{self.category}', question='{self.question[:50]}...')>"


class RestaurantPolicy(Base):
    """
    Restaurant policies for GeneralQueriesAgent.
    Manages booking, payment, dietary, and operational policies.
    """
    __tablename__ = "restaurant_policies"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Policy details
    policy_name: Mapped[str] = mapped_column(String(255), nullable=False)
    policy_category: Mapped[str] = mapped_column(String(100), nullable=False)
    policy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Policy content
    short_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_policy: Mapped[str] = mapped_column(Text, nullable=False)
    exceptions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    enforcement_level: Mapped[str] = mapped_column(String(20), default="strict")

    # Policy scope
    applies_to: Mapped[str] = mapped_column(String(50), default="all")
    effective_date: Mapped[datetime] = mapped_column(Date, server_default=func.current_date())
    expiry_date: Mapped[Optional[datetime]] = mapped_column(Date, nullable=True)

    # Legal and compliance
    legal_requirement: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Usage tracking
    reference_count: Mapped[int] = mapped_column(Integer, default=0)
    clarification_requests: Mapped[int] = mapped_column(Integer, default=0)

    # Status
    status: Mapped[str] = mapped_column(String(20), default="active")
    version: Mapped[str] = mapped_column(String(20), default="1.0")

    # Relationships
    related_policies: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String(20)), nullable=True)
    supersedes_policy_id: Mapped[Optional[str]] = mapped_column(String(20),
                                                               ForeignKey("restaurant_policies.id"),
                                                               nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now(),
                                               onupdate=func.now())
    last_reviewed: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Management
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_restaurant_policies_category', 'policy_category'),
        Index('idx_restaurant_policies_status', 'status'),
        Index('idx_restaurant_policies_effective_date', 'effective_date'),
        Index('idx_restaurant_policies_applies_to', 'applies_to'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<RestaurantPolicy(name='{self.policy_name}', category='{self.policy_category}')>"


class QueryAnalytics(Base):
    """
    Query analytics for tracking user questions and agent performance.
    Used by GeneralQueriesAgent for continuous improvement.
    """
    __tablename__ = "query_analytics"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Query details
    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"),
                                                  nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    query_intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Agent response
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    response_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Numeric(5, 3), nullable=True)

    # Response details
    response_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    source_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # User feedback
    user_satisfied: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    required_escalation: Mapped[bool] = mapped_column(Boolean, default=False)
    escalated_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Performance metrics
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    follow_up_questions: Mapped[int] = mapped_column(Integer, default=0)

    # Resolution
    fully_resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    resolution_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                               server_default=func.now())
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User")

    __table_args__ = (
        Index('idx_query_analytics_user_id', 'user_id'),
        Index('idx_query_analytics_session_id', 'session_id'),
        Index('idx_query_analytics_agent_name', 'agent_name'),
        Index('idx_query_analytics_created_at', 'created_at'),
        Index('idx_query_analytics_query_category', 'query_category'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<QueryAnalytics(agent='{self.agent_name}', query='{self.query_text[:50]}...', resolved={self.fully_resolved})>"


class AbandonedCart(Base):
    """
    Abandoned cart persistence for 2-hour restoration window.
    Stores cart state when user logs out or session expires.
    """
    __tablename__ = "abandoned_carts"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"),
                                                   nullable=True, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("user_devices.device_id"),
                                                     nullable=True, index=True)

    cart_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    items_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)

    abandoned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    restored: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    restored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    restaurant_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("restaurant_config.id"),
                                                         nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="abandoned_carts")

    __table_args__ = (
        Index('idx_abandoned_carts_user_id', 'user_id'),
        Index('idx_abandoned_carts_device_id', 'device_id'),
        Index('idx_abandoned_carts_expires_at', 'expires_at'),
        Index('idx_abandoned_carts_restored', 'restored'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<AbandonedCart(id='{self.id}', items={self.items_count}, restored={self.restored})>"


class AbandonedBooking(Base):
    """
    Abandoned booking persistence for recovery workflows.
    Stores partial booking data when user logs out mid-booking.
    """
    __tablename__ = "abandoned_bookings"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    user_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("users.id"),
                                                   nullable=True, index=True)
    device_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("user_devices.device_id"),
                                                     nullable=True, index=True)

    booking_data: Mapped[dict] = mapped_column(JSON, nullable=False)
    party_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    booking_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    abandoned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    restored: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    restored_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_to_booking_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    restaurant_id: Mapped[Optional[str]] = mapped_column(String(20), ForeignKey("restaurant_config.id"),
                                                         nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now(),
                                                  onupdate=func.now())

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="abandoned_bookings")

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


class APIKeyUsage(Base):
    """
    API key usage tracking for analytics and rate limiting.
    Tracks every API request for each restaurant's API key.
    """
    __tablename__ = "api_key_usage"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)

    restaurant_id: Mapped[str] = mapped_column(String(20), ForeignKey("restaurant_config.id"),
                                               nullable=False, index=True)
    api_key_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    request_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now(),
                                                  index=True)

    __table_args__ = (
        Index('idx_api_key_usage_restaurant_id', 'restaurant_id'),
        Index('idx_api_key_usage_created_at', 'created_at'),
        Index('idx_api_key_usage_restaurant_date', 'restaurant_id', 'created_at'),
        Index('idx_api_key_usage_endpoint', 'endpoint'),
        {'extend_existing': True}
    )

    def __repr__(self) -> str:
        return f"<APIKeyUsage(restaurant_id='{self.restaurant_id}', endpoint='{self.endpoint}', status={self.status_code})>"


# Create all table indexes and constraints
def create_database_indexes():
    """
    Additional database indexes for performance optimization.
    These are created separately to maintain readability.
    """
    # Composite indexes for common query patterns
    composite_indexes = [
        # User activity patterns
        Index('idx_users_status_created', User.status, User.created_at),

        # Booking availability queries
        Index('idx_bookings_date_status', Booking.booking_date, Booking.status),
        Index('idx_bookings_restaurant_date', Booking.restaurant_id, Booking.booking_date),

        # Order processing queries
        Index('idx_orders_status_created', Order.status, Order.created_at),
        Index('idx_orders_user_status', Order.user_id, Order.status),

        # Menu search and filtering
        Index('idx_menu_items_available_price', MenuItem.is_available, MenuItem.price),
        Index('idx_menu_items_category_available', MenuItem.category_id, MenuItem.is_available),

        # Message processing patterns
        Index('idx_messages_conv_date', Message.conversation_id, Message.created_at),
        Index('idx_messages_channel_date', Message.channel, Message.created_at),

        # Analytics queries
        Index('idx_complaints_status_priority', Complaint.status, Complaint.priority),
        Index('idx_ratings_type_rating', Rating.rating_type, Rating.rating),

        # Memory management
        Index('idx_agent_memory_user_agent', AgentMemory.user_id, AgentMemory.agent_name),
    ]

    return composite_indexes


# Event listeners will be registered in database/connection.py after engine creation
# to avoid multiple registrations during imports


if __name__ == "__main__":
    # Test model definitions
    print("SQLAlchemy models defined successfully!")
    print(f"Total models: {len(Base.metadata.tables)}")
    print("Available tables:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")
