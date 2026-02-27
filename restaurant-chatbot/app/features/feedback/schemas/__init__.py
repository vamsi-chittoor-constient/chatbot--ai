"""
Feedback Feature Schemas
=========================
Pydantic schemas for feedback, complaint, and satisfaction management.
"""

from app.features.feedback.schemas.satisfaction import (
    # Enums
    ComplaintCategory,
    ComplaintPriority,
    ComplaintStatus,
    SentimentLabel,
    MetricType,
    InteractionType,
    CollectionMethod,

    # Request Models
    ComplaintCreateRequest,
    ComplaintUpdateRequest,
    FeedbackCreateRequest,
    FeedbackDetailsCreateRequest,
    SatisfactionMetricCreateRequest,
    ComplaintSearchRequest,
    FeedbackSearchRequest,
    SatisfactionMetricSearchRequest,

    # Response Models
    ComplaintResponse,
    FeedbackResponse,
    FeedbackDetailsResponse,
    SatisfactionMetricResponse,
    ComplaintResolutionTemplateResponse,

    # List Responses
    ComplaintListResponse,
    FeedbackListResponse,
    SatisfactionMetricListResponse,
    ComplaintResolutionTemplateListResponse,

    # Analytics & Action Responses
    SatisfactionAnalyticsResponse,
    ComplaintCreateResponse,
    FeedbackCreateResponse,
    SatisfactionMetricCreateResponse,
    ComplaintUpdateResponse,
    ComplaintResolutionResponse,
)

__all__ = [
    # Enums
    "ComplaintCategory",
    "ComplaintPriority",
    "ComplaintStatus",
    "SentimentLabel",
    "MetricType",
    "InteractionType",
    "CollectionMethod",

    # Request Models
    "ComplaintCreateRequest",
    "ComplaintUpdateRequest",
    "FeedbackCreateRequest",
    "FeedbackDetailsCreateRequest",
    "SatisfactionMetricCreateRequest",
    "ComplaintSearchRequest",
    "FeedbackSearchRequest",
    "SatisfactionMetricSearchRequest",

    # Response Models
    "ComplaintResponse",
    "FeedbackResponse",
    "FeedbackDetailsResponse",
    "SatisfactionMetricResponse",
    "ComplaintResolutionTemplateResponse",

    # List Responses
    "ComplaintListResponse",
    "FeedbackListResponse",
    "SatisfactionMetricListResponse",
    "ComplaintResolutionTemplateListResponse",

    # Analytics & Actions
    "SatisfactionAnalyticsResponse",
    "ComplaintCreateResponse",
    "FeedbackCreateResponse",
    "SatisfactionMetricCreateResponse",
    "ComplaintUpdateResponse",
    "ComplaintResolutionResponse",
]
