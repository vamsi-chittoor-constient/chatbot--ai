"""
Pydantic schemas for General Queries Agent.

This module provides type-safe request/response models for FAQ management,
restaurant policies, and query analytics.
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseResponse, PaginatedResponse


# Enums

class QueryCategory(str, Enum):
    """Categories for general queries"""
    HOURS = "hours"
    LOCATION = "location"
    SERVICES = "services"
    MENU_INFO = "menu_info"
    POLICIES = "policies"
    FACILITIES = "facilities"
    CONTACT = "contact"
    PARKING = "parking"
    ACCESSIBILITY = "accessibility"
    PAYMENT = "payment"
    DELIVERY = "delivery"
    RESERVATIONS = "reservations"
    DIETARY = "dietary"
    OTHER = "other"


class DifficultyLevel(str, Enum):
    """Difficulty levels for FAQ items"""
    EASY = "easy"
    MEDIUM = "medium"
    COMPLEX = "complex"


class FAQStatus(str, Enum):
    """Status values for FAQ items"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"


class PolicyCategory(str, Enum):
    """Categories for restaurant policies"""
    BOOKING = "booking"
    PAYMENT = "payment"
    CANCELLATION = "cancellation"
    DIETARY = "dietary"
    ACCESSIBILITY = "accessibility"
    GENERAL = "general"
    DELIVERY = "delivery"
    HYGIENE = "hygiene"
    PRIVACY = "privacy"
    REFUND = "refund"


class PolicyType(str, Enum):
    """Types of policies"""
    RULE = "rule"
    GUIDELINE = "guideline"
    PROCEDURE = "procedure"
    REQUIREMENT = "requirement"


class EnforcementLevel(str, Enum):
    """Policy enforcement levels"""
    STRICT = "strict"
    FLEXIBLE = "flexible"
    GUIDELINE = "guideline"


class PolicyStatus(str, Enum):
    """Status values for policies"""
    ACTIVE = "active"
    DRAFT = "draft"
    ARCHIVED = "archived"
    UNDER_REVIEW = "under_review"


class ResponseType(str, Enum):
    """Types of agent responses"""
    FAQ_MATCH = "faq_match"
    KNOWLEDGE_BASE = "knowledge_base"
    POLICY_LOOKUP = "policy_lookup"
    WEB_SEARCH = "web_search"
    FALLBACK = "fallback"


class ResolutionMethod(str, Enum):
    """Methods for query resolution"""
    DIRECT_ANSWER = "direct_answer"
    ESCALATION = "escalation"
    CALLBACK_SCHEDULED = "callback_scheduled"
    FOLLOW_UP_REQUIRED = "follow_up_required"


# Request Models

class FAQCreateRequest(BaseModel):
    """Request model for creating FAQ items"""
    question: str = Field(..., min_length=10, max_length=500, description="The question being asked")
    answer: str = Field(..., min_length=10, max_length=2000, description="The answer to the question")
    category: QueryCategory = Field(..., description="Question category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Subcategory for organization")

    # Question variations
    question_variations: Optional[List[str]] = Field(None, description="Alternative ways to ask the same question")

    # Metadata
    keywords: Optional[List[str]] = Field(None, description="Keywords for search optimization")
    difficulty_level: DifficultyLevel = Field(DifficultyLevel.EASY, description="Complexity level")

    # Content management
    is_featured: bool = Field(False, description="Should this FAQ be featured prominently")
    display_order: int = Field(100, ge=1, le=1000, description="Display order priority")
    confidence_threshold: float = Field(0.80, ge=0.0, le=1.0, description="Minimum confidence for auto-response")

class FAQUpdateRequest(BaseModel):
    """Request model for updating FAQ items"""
    question: Optional[str] = Field(None, min_length=10, max_length=500, description="Updated question")
    answer: Optional[str] = Field(None, min_length=10, max_length=2000, description="Updated answer")
    category: Optional[QueryCategory] = Field(None, description="Updated category")
    subcategory: Optional[str] = Field(None, max_length=100, description="Updated subcategory")
    question_variations: Optional[List[str]] = Field(None, description="Updated question variations")
    keywords: Optional[List[str]] = Field(None, description="Updated keywords")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Updated difficulty level")
    is_featured: Optional[bool] = Field(None, description="Updated featured status")
    display_order: Optional[int] = Field(None, ge=1, le=1000, description="Updated display order")
    status: Optional[FAQStatus] = Field(None, description="Updated status")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="Updated confidence threshold")


class RestaurantPolicyCreateRequest(BaseModel):
    """Request model for creating restaurant policies"""
    policy_name: str = Field(..., min_length=5, max_length=255, description="Policy name")
    policy_category: PolicyCategory = Field(..., description="Policy category")
    policy_type: PolicyType = Field(..., description="Type of policy")

    # Policy content
    short_description: str = Field(..., min_length=10, max_length=500, description="Brief policy description")
    full_policy: str = Field(..., min_length=50, max_length=5000, description="Complete policy text")
    exceptions: Optional[str] = Field(None, max_length=1000, description="Policy exceptions")
    enforcement_level: EnforcementLevel = Field(EnforcementLevel.STRICT, description="How strictly to enforce")

    # Policy scope
    applies_to: str = Field("all", description="What this policy applies to")
    effective_date: Optional[date] = Field(None, description="When policy takes effect")
    expiry_date: Optional[date] = Field(None, description="When policy expires")

    # Legal and compliance
    legal_requirement: bool = Field(False, description="Is this legally required")
    compliance_level: Optional[str] = Field(None, max_length=20, description="Compliance requirement level")

    # Relationships
    related_policies: Optional[List[str]] = Field(None, description="IDs of related policies")

class RestaurantPolicyUpdateRequest(BaseModel):
    """Request model for updating restaurant policies"""
    policy_name: Optional[str] = Field(None, min_length=5, max_length=255, description="Updated policy name")
    policy_category: Optional[PolicyCategory] = Field(None, description="Updated category")
    policy_type: Optional[PolicyType] = Field(None, description="Updated type")
    short_description: Optional[str] = Field(None, min_length=10, max_length=500, description="Updated description")
    full_policy: Optional[str] = Field(None, min_length=50, max_length=5000, description="Updated policy text")
    exceptions: Optional[str] = Field(None, max_length=1000, description="Updated exceptions")
    enforcement_level: Optional[EnforcementLevel] = Field(None, description="Updated enforcement level")
    applies_to: Optional[str] = Field(None, description="Updated scope")
    effective_date: Optional[date] = Field(None, description="Updated effective date")
    expiry_date: Optional[date] = Field(None, description="Updated expiry date")
    legal_requirement: Optional[bool] = Field(None, description="Updated legal requirement status")
    compliance_level: Optional[str] = Field(None, max_length=20, description="Updated compliance level")
    status: Optional[PolicyStatus] = Field(None, description="Updated status")
    version: Optional[str] = Field(None, max_length=20, description="Updated version")
    related_policies: Optional[List[str]] = Field(None, description="Updated related policies")


class QueryAnalyticsCreateRequest(BaseModel):
    """Request model for creating query analytics records"""
    query_text: str = Field(..., min_length=1, max_length=1000, description="The user's query")
    query_category: Optional[QueryCategory] = Field(None, description="Categorized query type")
    query_intent: Optional[str] = Field(None, max_length=100, description="Detected intent")

    # Agent response details
    agent_name: str = Field(..., max_length=50, description="Name of responding agent")
    response_type: Optional[ResponseType] = Field(None, description="Type of response")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Response confidence")

    # Response details
    response_text: Optional[str] = Field(None, max_length=2000, description="Agent's response")
    source_id: Optional[str] = Field(None, description="ID of FAQ/policy/knowledge used")
    source_type: Optional[str] = Field(None, max_length=50, description="Type of source used")

    # User feedback
    user_satisfied: Optional[bool] = Field(None, description="Was user satisfied with response")
    required_escalation: bool = Field(False, description="Did query require escalation")
    escalated_to: Optional[str] = Field(None, max_length=50, description="Where query was escalated")

    # Performance metrics
    response_time_ms: Optional[int] = Field(None, ge=0, description="Response time in milliseconds")
    follow_up_questions: int = Field(0, ge=0, description="Number of follow-up questions")

    # Resolution
    fully_resolved: bool = Field(False, description="Was query fully resolved")
    resolution_method: Optional[ResolutionMethod] = Field(None, description="How query was resolved")

    # Context
    session_id: Optional[str] = Field(None, max_length=255, description="Session ID")

class FAQResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for FAQ items"""
    id: str
    question: str
    answer: str
    category: str
    subcategory: Optional[str]
    question_variations: Optional[List[str]]
    keywords: Optional[List[str]]
    difficulty_level: str

    # Usage statistics
    question_count: int
    last_asked: Optional[datetime]
    satisfaction_score: float

    # Content management
    is_featured: bool
    display_order: int
    status: str
    confidence_threshold: float

    # AI enhancement
    embedding: Optional[List[float]]

    # Timestamps
    created_at: datetime
    updated_at: datetime

class RestaurantPolicyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for restaurant policies"""
    id: str
    policy_name: str
    policy_category: str
    policy_type: str

    # Policy content
    short_description: str
    full_policy: str
    exceptions: Optional[str]
    enforcement_level: str

    # Policy scope
    applies_to: str
    effective_date: date
    expiry_date: Optional[date]

    # Legal and compliance
    legal_requirement: bool
    compliance_level: Optional[str]

    # Usage tracking
    reference_count: int
    clarification_requests: int

    # Status
    status: str
    version: str

    # Relationships
    related_policies: Optional[List[str]]
    supersedes_policy_id: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_reviewed: Optional[datetime]

    # Management
    created_by: Optional[str]
    approved_by: Optional[str]
    approved_at: Optional[datetime]

class QueryAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for query analytics"""
    id: str
    user_id: Optional[str]
    session_id: Optional[str]
    query_text: str
    query_category: Optional[str]
    query_intent: Optional[str]

    # Agent response
    agent_name: str
    response_type: Optional[str]
    confidence_score: Optional[float]

    # Response details
    response_text: Optional[str]
    source_id: Optional[str]
    source_type: Optional[str]

    # User feedback
    user_satisfied: Optional[bool]
    required_escalation: bool
    escalated_to: Optional[str]

    # Performance metrics
    response_time_ms: Optional[int]
    follow_up_questions: int

    # Resolution
    fully_resolved: bool
    resolution_method: Optional[str]

    # Timestamps
    created_at: datetime
    resolved_at: Optional[datetime]

class FAQListResponse(PaginatedResponse):
    """Paginated response for FAQ items"""
    items: List[FAQResponse]


class RestaurantPolicyListResponse(PaginatedResponse):
    """Paginated response for restaurant policies"""
    items: List[RestaurantPolicyResponse]


class QueryAnalyticsListResponse(PaginatedResponse):
    """Paginated response for query analytics"""
    items: List[QueryAnalyticsResponse]


# Search Request Models

class FAQSearchRequest(BaseModel):
    """Request model for searching FAQ items"""
    category: Optional[QueryCategory] = Field(None, description="Filter by category")
    subcategory: Optional[str] = Field(None, description="Filter by subcategory")
    difficulty_level: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    status: Optional[FAQStatus] = Field(None, description="Filter by status")
    is_featured: Optional[bool] = Field(None, description="Filter featured items")
    search_text: Optional[str] = Field(None, description="Search in question and answer")
    keywords: Optional[List[str]] = Field(None, description="Search by keywords")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("display_order", description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order")


class RestaurantPolicySearchRequest(BaseModel):
    """Request model for searching restaurant policies"""
    policy_category: Optional[PolicyCategory] = Field(None, description="Filter by category")
    policy_type: Optional[PolicyType] = Field(None, description="Filter by type")
    status: Optional[PolicyStatus] = Field(None, description="Filter by status")
    enforcement_level: Optional[EnforcementLevel] = Field(None, description="Filter by enforcement level")
    applies_to: Optional[str] = Field(None, description="Filter by scope")
    legal_requirement: Optional[bool] = Field(None, description="Filter by legal requirement")
    effective_date_from: Optional[date] = Field(None, description="Filter from effective date")
    effective_date_to: Optional[date] = Field(None, description="Filter to effective date")
    search_text: Optional[str] = Field(None, description="Search in policy text")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("policy_name", description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order")


class QueryAnalyticsSearchRequest(BaseModel):
    """Request model for searching query analytics"""
    agent_name: Optional[str] = Field(None, description="Filter by agent")
    query_category: Optional[QueryCategory] = Field(None, description="Filter by query category")
    response_type: Optional[ResponseType] = Field(None, description="Filter by response type")
    user_satisfied: Optional[bool] = Field(None, description="Filter by satisfaction")
    required_escalation: Optional[bool] = Field(None, description="Filter by escalation requirement")
    fully_resolved: Optional[bool] = Field(None, description="Filter by resolution status")
    date_from: Optional[date] = Field(None, description="Filter from date")
    date_to: Optional[date] = Field(None, description="Filter to date")
    search_text: Optional[str] = Field(None, description="Search in query text")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


# Analytics Response Models

class QueryAnalyticsStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for query analytics statistics"""
    total_queries: int
    resolved_queries: int
    resolution_rate: float
    average_response_time_ms: float
    escalation_rate: float
    satisfaction_rate: float

    # Breakdown by category
    queries_by_category: Dict[str, int]
    queries_by_agent: Dict[str, int]
    response_types_distribution: Dict[str, int]

    # Trends
    query_volume_trend: List[Dict[str, Any]]
    resolution_trend: List[Dict[str, Any]]
    satisfaction_trend: List[Dict[str, Any]]

    # Top performing content
    top_faq_items: List[Dict[str, Any]]
    most_referenced_policies: List[Dict[str, Any]]

    # Period
    period_start: date
    period_end: date

class FAQCreateResponse(BaseResponse):
    """Response for FAQ creation"""
    faq: FAQResponse


class FAQUpdateResponse(BaseResponse):
    """Response for FAQ update"""
    faq: FAQResponse


class RestaurantPolicyCreateResponse(BaseResponse):
    """Response for policy creation"""
    policy: RestaurantPolicyResponse


class RestaurantPolicyUpdateResponse(BaseResponse):
    """Response for policy update"""
    policy: RestaurantPolicyResponse


class QueryAnalyticsCreateResponse(BaseResponse):
    """Response for query analytics creation"""
    analytics: QueryAnalyticsResponse


# Quick Query Models

class QuickQueryRequest(BaseModel):
    """Request model for quick queries (used by the agent)"""
    query: str = Field(..., min_length=1, max_length=500, description="User's question")
    session_id: Optional[str] = Field(None, description="Session context")
    user_id: Optional[str] = Field(None, description="User context")

class QuickQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for quick queries"""
    answer: str = Field(..., description="Answer to the query")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the answer")
    source_type: str = Field(..., description="Source of the answer")
    source_id: Optional[str] = Field(None, description="ID of the source")
    requires_follow_up: bool = Field(False, description="Whether follow-up is suggested")
    suggested_follow_ups: Optional[List[str]] = Field(None, description="Suggested follow-up questions")
    escalation_suggested: bool = Field(False, description="Whether escalation is recommended")
