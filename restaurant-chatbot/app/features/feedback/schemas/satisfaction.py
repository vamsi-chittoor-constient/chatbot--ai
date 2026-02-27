"""
Pydantic schemas for Customer Satisfaction Agent.

This module provides type-safe request/response models for complaint management,
feedback collection, and satisfaction metrics tracking.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, root_validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseResponse, PaginatedResponse


# Enums

class ComplaintCategory(str, Enum):
    """Categories for complaint classification"""
    FOOD_QUALITY = "food_quality"
    SERVICE = "service"
    BILLING = "billing"
    DELIVERY = "delivery"
    BOOKING = "booking"
    STAFF = "staf"
    HYGIENE = "hygiene"
    OTHER = "other"


class ComplaintPriority(str, Enum):
    """Priority levels for complaints"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplaintStatus(str, Enum):
    """Status values for complaints"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class SentimentLabel(str, Enum):
    """Sentiment analysis labels"""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class MetricType(str, Enum):
    """Types of satisfaction metrics"""
    NPS = "nps"
    CSAT = "csat"
    CES = "ces"
    OVERALL_EXPERIENCE = "overall_experience"


class InteractionType(str, Enum):
    """Types of customer interactions"""
    ORDER = "order"
    BOOKING = "booking"
    SUPPORT = "support"
    GENERAL = "general"


class CollectionMethod(str, Enum):
    """Methods for collecting feedback/metrics"""
    AI_CONVERSATION = "ai_conversation"
    AUTOMATED_SURVEY = "automated_survey"
    MANUAL_ENTRY = "manual_entry"
    PROACTIVE_OUTREACH = "proactive_outreach"


# Request Models

class ComplaintCreateRequest(BaseModel):
    """Request model for creating a new complaint"""
    complaint_title: str = Field(..., min_length=5, max_length=255, description="Brief title for the complaint")
    complaint_text: str = Field(..., min_length=10, max_length=2000, description="Detailed complaint description")
    category: ComplaintCategory = Field(..., description="Complaint category")
    subcategory: Optional[str] = Field(None, max_length=100, description="More specific categorization")
    priority: ComplaintPriority = Field(ComplaintPriority.MEDIUM, description="Priority level")
    session_id: Optional[str] = Field(None, max_length=255, description="Session ID for context")
    order_id: Optional[str] = Field(None, description="Related order ID if applicable")
    booking_id: Optional[str] = Field(None, description="Related booking ID if applicable")

class ComplaintUpdateRequest(BaseModel):
    """Request model for updating complaint status or resolution"""
    status: Optional[ComplaintStatus] = Field(None, description="New status")
    resolution_text: Optional[str] = Field(None, max_length=1000, description="Resolution details")
    compensation_offered: Optional[str] = Field(None, max_length=500, description="Compensation details")
    compensation_amount: Optional[Decimal] = Field(None, ge=0, description="Compensation amount")
    assigned_to: Optional[str] = Field(None, max_length=255, description="Staff member assigned")
    escalated_to: Optional[str] = Field(None, max_length=255, description="Escalation target")
    follow_up_required: Optional[bool] = Field(None, description="Whether follow-up is needed")
    follow_up_date: Optional[datetime] = Field(None, description="Scheduled follow-up date")

class FeedbackCreateRequest(BaseModel):
    """Request model for creating customer feedback"""
    overall_rating: int = Field(..., ge=1, le=5, description="Overall rating 1-5")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Written feedback")
    session_id: Optional[str] = Field(None, max_length=255, description="Session ID")
    order_id: Optional[str] = Field(None, description="Related order ID")
    booking_id: Optional[str] = Field(None, description="Related booking ID")

    # Additional ratings
    ai_experience_rating: Optional[int] = Field(None, ge=1, le=5, description="AI experience rating")

    # Feedback categories
    likes: Optional[str] = Field(None, max_length=500, description="What customer liked")
    dislikes: Optional[str] = Field(None, max_length=500, description="What customer disliked")
    suggestions: Optional[str] = Field(None, max_length=500, description="Improvement suggestions")

    # Collection metadata
    collection_method: CollectionMethod = Field(CollectionMethod.AI_CONVERSATION, description="How feedback was collected")
    requires_response: bool = Field(False, description="Whether feedback requires a response")
    is_public: bool = Field(True, description="Whether feedback can be shown publicly")

class FeedbackDetailsCreateRequest(BaseModel):
    """Request model for detailed feedback breakdown"""
    feedback_id: str = Field(..., description="Reference to main feedback record")

    # Detailed ratings
    food_quality_rating: Optional[int] = Field(None, ge=1, le=5, description="Food quality rating")
    service_speed_rating: Optional[int] = Field(None, ge=1, le=5, description="Service speed rating")
    staff_friendliness_rating: Optional[int] = Field(None, ge=1, le=5, description="Staff friendliness rating")
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5, description="Cleanliness rating")
    value_for_money_rating: Optional[int] = Field(None, ge=1, le=5, description="Value for money rating")

    # Detailed feedback
    food_items_feedback: Optional[Dict[str, Any]] = Field(None, description="Specific food items feedback")
    service_feedback: Optional[Dict[str, Any]] = Field(None, description="Service-related feedback")
    ambiance_feedback: Optional[Dict[str, Any]] = Field(None, description="Ambiance feedback")

    # Recommendations
    specific_complaints: Optional[List[str]] = Field(None, description="Specific complaint items")
    improvement_suggestions: Optional[List[str]] = Field(None, description="Improvement suggestions")
    would_recommend: Optional[bool] = Field(None, description="Would recommend to others")
    would_return: Optional[bool] = Field(None, description="Would return as customer")

class SatisfactionMetricCreateRequest(BaseModel):
    """Request model for creating satisfaction metrics"""
    metric_type: MetricType = Field(..., description="Type of metric")
    score: float = Field(..., description="Metric score")
    max_score: float = Field(10.0, description="Maximum possible score")

    # Context
    interaction_type: Optional[InteractionType] = Field(None, description="Type of interaction")
    session_id: Optional[str] = Field(None, max_length=255, description="Session ID")
    reference_id: Optional[str] = Field(None, description="Reference to order/booking/complaint")
    reference_type: Optional[str] = Field(None, description="Type of reference")

    # Classification
    category: Optional[str] = Field(None, max_length=100, description="Metric category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Metric subcategory")

    # Metadata
    collection_method: CollectionMethod = Field(..., description="How metric was collected")
    additional_data: Optional[Dict[str, Any]] = Field(None, description="Additional metric data")

    @validator('score')
    def validate_score_range(cls, v, values):
        max_score = values.get('max_score', 10.0)
        if v < 0 or v > max_score:
            raise ValueError(f'Score must be between 0 and {max_score}')
        return v

class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for complaint data"""
    id: str
    user_id: Optional[str]
    complaint_title: str = Field(alias="title")
    complaint_text: str = Field(alias="description")
    category: str
    subcategory: Optional[str] = None  # This field doesn't exist in SQLAlchemy model
    priority: str
    status: str
    session_id: Optional[str] = None  # This field doesn't exist in SQLAlchemy model
    order_id: Optional[str]
    booking_id: Optional[str]

    # Resolution details
    resolution_text: str = Field(alias="resolution")
    compensation_offered: Optional[str]
    compensation_amount: Optional[Decimal]

    # Assignment
    assigned_to: Optional[str]
    assigned_at: Optional[datetime]
    escalated_to: Optional[str]
    escalated_at: Optional[datetime]
    resolved_at: Optional[datetime]

    # AI analysis
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    urgency_score: Optional[int]
    keywords: Optional[List[str]]

    # Follow-up
    follow_up_required: bool
    follow_up_date: Optional[datetime]
    follow_up_completed: bool

    # Timestamps
    created_at: datetime
    updated_at: datetime

class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for feedback data"""
    id: str
    user_id: Optional[str]
    overall_rating: int
    feedback_text: Optional[str]
    session_id: Optional[str]
    order_id: Optional[str]
    booking_id: Optional[str]

    # Additional ratings
    ai_experience_rating: Optional[int]

    # Feedback categories
    likes: Optional[str]
    dislikes: Optional[str]
    suggestions: Optional[str]

    # Metadata
    collection_method: str
    requires_response: bool
    is_public: bool

    # Response details
    response_text: Optional[str]
    responded_by: Optional[str]
    responded_at: Optional[datetime]

    # AI analysis
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    keywords: Optional[List[str]]

    # Timestamps
    created_at: datetime

class FeedbackDetailsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for detailed feedback"""
    id: str
    feedback_id: str

    # Detailed ratings
    food_quality_rating: Optional[int]
    service_speed_rating: Optional[int]
    staff_friendliness_rating: Optional[int]
    cleanliness_rating: Optional[int]
    value_for_money_rating: Optional[int]

    # Detailed feedback
    food_items_feedback: Optional[Dict[str, Any]]
    service_feedback: Optional[Dict[str, Any]]
    ambiance_feedback: Optional[Dict[str, Any]]

    # Recommendations
    specific_complaints: Optional[List[str]]
    improvement_suggestions: Optional[List[str]]
    would_recommend: Optional[bool]
    would_return: Optional[bool]

    created_at: datetime

class SatisfactionMetricResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for satisfaction metrics"""
    id: str
    user_id: Optional[str]
    metric_type: str
    score: float
    max_score: float

    # Context
    interaction_type: Optional[str]
    session_id: Optional[str]
    reference_id: Optional[str]
    reference_type: Optional[str]

    # Classification
    category: Optional[str]
    subcategory: Optional[str]

    # Metadata
    collection_method: str
    additional_data: Optional[Dict[str, Any]]

    # Timestamps
    created_at: datetime
    recorded_date: date

class ComplaintResolutionTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for complaint resolution templates"""
    id: str
    template_name: str
    category: str
    subcategory: Optional[str]
    response_template: str
    compensation_guidelines: Optional[str]
    escalation_criteria: Optional[str]
    usage_count: int
    success_rate: float
    is_active: bool
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

class ComplaintListResponse(PaginatedResponse):
    """Paginated response for complaints"""
    items: List[ComplaintResponse]


class FeedbackListResponse(PaginatedResponse):
    """Paginated response for feedback"""
    items: List[FeedbackResponse]


class SatisfactionMetricListResponse(PaginatedResponse):
    """Paginated response for satisfaction metrics"""
    items: List[SatisfactionMetricResponse]


class ComplaintResolutionTemplateListResponse(PaginatedResponse):
    """Paginated response for resolution templates"""
    items: List[ComplaintResolutionTemplateResponse]


# Analytics Response Models

class SatisfactionAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for satisfaction analytics"""
    overall_satisfaction_score: float
    total_complaints: int
    resolved_complaints: int
    resolution_rate: float
    average_resolution_time_hours: float
    nps_score: Optional[float]
    csat_score: Optional[float]
    ces_score: Optional[float]

    # Breakdown by category
    complaints_by_category: Dict[str, int]
    feedback_by_rating: Dict[int, int]
    sentiment_distribution: Dict[str, int]

    # Trends
    satisfaction_trend: List[Dict[str, Any]]
    complaint_trend: List[Dict[str, Any]]

    # Period
    period_start: date
    period_end: date

class ComplaintCreateResponse(BaseResponse):
    """Response for complaint creation"""
    complaint: ComplaintResponse


class FeedbackCreateResponse(BaseResponse):
    """Response for feedback creation"""
    feedback: FeedbackResponse


class SatisfactionMetricCreateResponse(BaseResponse):
    """Response for satisfaction metric creation"""
    metric: SatisfactionMetricResponse


class ComplaintUpdateResponse(BaseResponse):
    """Response for complaint update"""
    complaint: ComplaintResponse


class ComplaintResolutionResponse(BaseResponse):
    """Response for complaint resolution"""
    complaint: ComplaintResponse
    resolution_template_used: Optional[str]
    compensation_approved: bool
    escalation_required: bool


# Search Request Models

class ComplaintSearchRequest(BaseModel):
    """Request model for searching complaints"""
    status: Optional[ComplaintStatus] = Field(None, description="Filter by status")
    category: Optional[ComplaintCategory] = Field(None, description="Filter by category")
    priority: Optional[ComplaintPriority] = Field(None, description="Filter by priority")
    assigned_to: Optional[str] = Field(None, description="Filter by assignee")
    user_id: Optional[str] = Field(None, description="Filter by user")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    search_text: Optional[str] = Field(None, description="Search in title and description")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


class FeedbackSearchRequest(BaseModel):
    """Request model for searching feedback"""
    rating_min: Optional[int] = Field(None, ge=1, le=5, description="Minimum rating")
    rating_max: Optional[int] = Field(None, ge=1, le=5, description="Maximum rating")
    user_id: Optional[str] = Field(None, description="Filter by user")
    order_id: Optional[str] = Field(None, description="Filter by order")
    booking_id: Optional[str] = Field(None, description="Filter by booking")
    collection_method: Optional[CollectionMethod] = Field(None, description="Filter by collection method")
    requires_response: Optional[bool] = Field(None, description="Filter by response requirement")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    search_text: Optional[str] = Field(None, description="Search in feedback text")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


class SatisfactionMetricSearchRequest(BaseModel):
    """Request model for searching satisfaction metrics"""
    metric_type: Optional[MetricType] = Field(None, description="Filter by metric type")
    interaction_type: Optional[InteractionType] = Field(None, description="Filter by interaction type")
    user_id: Optional[str] = Field(None, description="Filter by user")
    score_min: Optional[float] = Field(None, description="Minimum score")
    score_max: Optional[float] = Field(None, description="Maximum score")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("recorded_date", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")
