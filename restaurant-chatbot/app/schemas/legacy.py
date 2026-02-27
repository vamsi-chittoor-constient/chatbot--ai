"""
Pydantic schemas for Legacy Tables.

This module provides type-safe request/response models for legacy database tables
including feedback, knowledge_base, ratings, and waitlist management.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseResponse, PaginatedResponse


# Enums

class FeedbackType(str, Enum):
    """Feedback type enumeration"""
    ORDER = "order"
    BOOKING = "booking"
    GENERAL = "general"
    SERVICE = "service"


class SentimentLabel(str, Enum):
    """Sentiment analysis labels"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class WaitlistStatus(str, Enum):
    """Waitlist status enumeration"""
    WAITING = "waiting"
    NOTIFIED = "notified"
    SEATED = "seated"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


# Feedback Schemas (Legacy)

class FeedbackCreateRequest(BaseModel):
    """Request model for creating legacy feedback"""
    user_id: Optional[str] = Field(None, description="User ID if available")
    order_id: Optional[str] = Field(None, description="Associated order ID")
    booking_id: Optional[str] = Field(None, description="Associated booking ID")
    rating: int = Field(..., ge=1, le=5, description="Rating 1-5 stars")
    review_text: Optional[str] = Field(None, max_length=2000, description="Review text")
    feedback_type: FeedbackType = Field(FeedbackType.GENERAL, description="Type of feedback")

    @validator('rating')
    def validate_rating_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for legacy feedback"""
    id: str
    user_id: Optional[str]
    order_id: Optional[str]
    booking_id: Optional[str]
    rating: int
    review_text: Optional[str]
    sentiment_score: Optional[Decimal]
    sentiment_label: Optional[str]
    feedback_type: Optional[str]
    created_at: Optional[datetime]

class KnowledgeBaseCreateRequest(BaseModel):
    """Request model for creating knowledge base entries"""
    title: str = Field(..., min_length=5, max_length=255, description="Knowledge base title")
    content: str = Field(..., min_length=10, max_length=5000, description="Knowledge base content")
    category: str = Field(..., max_length=100, description="Content category")
    tags: Optional[List[str]] = Field(None, description="Content tags")
    is_active: bool = Field(True, description="Whether entry is active")

class KnowledgeBaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for knowledge base entries"""
    id: str
    title: str
    content: str
    category: str
    tags: Optional[List[str]]
    view_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class RatingCreateRequest(BaseModel):
    """Request model for creating ratings"""
    user_id: str = Field(..., description="User who provided the rating")
    order_id: Optional[str] = Field(None, description="Associated order ID")
    booking_id: Optional[str] = Field(None, description="Associated booking ID")
    rating: int = Field(..., ge=1, le=5, description="Rating value 1-5")
    review: Optional[str] = Field(None, max_length=1000, description="Review text")
    category: Optional[str] = Field(None, max_length=50, description="Rating category")

    @validator('rating')
    def validate_rating_range(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

class RatingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for ratings"""
    id: str
    user_id: str
    order_id: Optional[str]
    booking_id: Optional[str]
    rating: int
    review: Optional[str]
    category: Optional[str]
    created_at: datetime

class WaitlistCreateRequest(BaseModel):
    """Request model for adding to waitlist"""
    user_id: Optional[str] = Field(None, description="User ID if available")
    name: str = Field(..., min_length=2, max_length=100, description="Customer name")
    phone: str = Field(..., min_length=10, max_length=15, description="Customer phone")
    party_size: int = Field(..., ge=1, le=20, description="Party size")
    preferred_table_type: Optional[str] = Field(None, description="Preferred table type")
    special_requests: Optional[str] = Field(None, max_length=500, description="Special requests")

class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for waitlist entries"""
    id: str
    user_id: Optional[str]
    name: str
    phone: str
    party_size: int
    position: int
    estimated_wait_minutes: Optional[int]
    preferred_table_type: Optional[str]
    special_requests: Optional[str]
    status: str
    notified_at: Optional[datetime]
    seated_at: Optional[datetime]
    created_at: datetime

class WaitlistUpdateRequest(BaseModel):
    """Request model for updating waitlist entries"""
    status: Optional[WaitlistStatus] = Field(None, description="Updated status")
    estimated_wait_minutes: Optional[int] = Field(None, description="Updated wait time")
    position: Optional[int] = Field(None, description="Updated position")


# Search and Filter Schemas

class FeedbackSearchRequest(BaseModel):
    """Request model for searching feedback"""
    user_id: Optional[str] = Field(None, description="Filter by user")
    order_id: Optional[str] = Field(None, description="Filter by order")
    booking_id: Optional[str] = Field(None, description="Filter by booking")
    rating_min: Optional[int] = Field(None, ge=1, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=1, le=5, description="Maximum rating")
    feedback_type: Optional[FeedbackType] = Field(None, description="Filter by type")
    sentiment_label: Optional[SentimentLabel] = Field(None, description="Filter by sentiment")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


class KnowledgeBaseSearchRequest(BaseModel):
    """Request model for searching knowledge base"""
    category: Optional[str] = Field(None, description="Filter by category")
    search_text: Optional[str] = Field(None, description="Search in title and content")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    is_active: Optional[bool] = Field(None, description="Filter by active status")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("view_count", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


class WaitlistSearchRequest(BaseModel):
    """Request model for searching waitlist"""
    status: Optional[WaitlistStatus] = Field(None, description="Filter by status")
    party_size_min: Optional[int] = Field(None, description="Minimum party size")
    party_size_max: Optional[int] = Field(None, description="Maximum party size")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("position", description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order")


# List Response Models

class FeedbackListResponse(PaginatedResponse):
    """Paginated response for feedback"""
    items: List[FeedbackResponse]


class KnowledgeBaseListResponse(PaginatedResponse):
    """Paginated response for knowledge base"""
    items: List[KnowledgeBaseResponse]


class RatingListResponse(PaginatedResponse):
    """Paginated response for ratings"""
    items: List[RatingResponse]


class WaitlistListResponse(PaginatedResponse):
    """Paginated response for waitlist"""
    items: List[WaitlistResponse]


# Action Response Models

class FeedbackCreateResponse(BaseResponse):
    """Response for feedback creation"""
    feedback: FeedbackResponse


class KnowledgeBaseCreateResponse(BaseResponse):
    """Response for knowledge base creation"""
    knowledge_base: KnowledgeBaseResponse


class RatingCreateResponse(BaseResponse):
    """Response for rating creation"""
    rating: RatingResponse


class WaitlistCreateResponse(BaseResponse):
    """Response for waitlist creation"""
    waitlist: WaitlistResponse
    estimated_wait_minutes: int
    current_position: int


class WaitlistUpdateResponse(BaseResponse):
    """Response for waitlist update"""
    waitlist: WaitlistResponse


# Analytics Response Models

class LegacyAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for legacy data analytics"""
    # Feedback analytics
    total_feedback: int
    average_rating: float
    rating_distribution: Dict[int, int]
    sentiment_distribution: Dict[str, int]

    # Knowledge base analytics
    total_kb_articles: int
    most_viewed_articles: List[Dict[str, Any]]
    articles_by_category: Dict[str, int]

    # Waitlist analytics
    total_waitlist_entries: int
    average_wait_time_minutes: float
    waitlist_conversion_rate: float
    peak_waitlist_hours: List[int]

    # Period
    period_start: date
    period_end: date
