"""
Base models and enums for the Restaurant AI Assistant.

This module contains:
- Common enums used across features
- Base SQLAlchemy imports
- Shared type definitions
"""

import enum
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Integer, String, Text, DateTime, Boolean, JSON, Date, Time,
    ForeignKey, UniqueConstraint, Index, CheckConstraint, Enum as SQLEnum, Numeric,
    text
)
from decimal import Decimal
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PG_UUID
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.core.database import Base


# ============================================================================
# ENUMS - Shared across features
# ============================================================================

class UserStatus(enum.Enum):
    """User account status"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class BookingStatus(enum.Enum):
    """Table booking status"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class OrderStatus(enum.Enum):
    """Food order status"""
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
    """Payment transaction status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class MessageDirection(enum.Enum):
    """Message direction for communication tracking"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageChannel(enum.Enum):
    """Communication channel types"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"


class ComplaintStatus(enum.Enum):
    """Customer complaint status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"
