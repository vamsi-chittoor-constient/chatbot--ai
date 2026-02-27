"""
Pydantic schemas for System Utilities.

This module provides type-safe request/response models for system logging,
agent memory, and system monitoring.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseResponse, PaginatedResponse


# Enums

class LogLevel(str, Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AgentType(str, Enum):
    """Agent type enumeration"""
    ORCHESTRATOR = "orchestrator"
    BOOKING_AGENT = "booking_agent"
    COMMUNICATION_AGENT = "communication_agent"
    FOOD_ORDERING_AGENT = "food_ordering_agent"
    FEEDBACK_AGENT = "feedback_agent"
    GENERAL_QUERIES_AGENT = "general_queries_agent"
    USER_MANAGEMENT_AGENT = "user_management_agent"
    USER_PROFILE_AGENT = "user_profile_agent"
    AUTHENTICATION_AGENT = "authentication_agent"


# System Log Schemas

class SystemLogCreateRequest(BaseModel):
    """Request model for creating system logs"""
    level: LogLevel = Field(..., description="Log level")
    message: str = Field(..., min_length=1, max_length=2000, description="Log message")
    component: str = Field(..., max_length=100, description="System component")
    session_id: Optional[str] = Field(None, description="Associated session ID")
    user_id: Optional[str] = Field(None, description="Associated user ID")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")

class SystemLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for system logs"""
    id: str
    level: str
    message: str
    component: str
    session_id: Optional[str]
    user_id: Optional[str]
    context: Optional[Dict[str, Any]]
    created_at: datetime

class AgentMemoryCreateRequest(BaseModel):
    """Request model for creating agent memory"""
    agent_name: AgentType = Field(..., description="Agent identifier")
    session_id: str = Field(..., description="Session identifier")
    memory_type: str = Field(..., max_length=50, description="Type of memory")
    memory_key: str = Field(..., max_length=255, description="Memory key")
    memory_value: Dict[str, Any] = Field(..., description="Memory content")
    ttl_seconds: Optional[int] = Field(None, description="Time to live in seconds")

class AgentMemoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for agent memory"""
    id: str
    agent_name: str
    session_id: str
    memory_type: str
    memory_key: str
    memory_value: Dict[str, Any]
    ttl_seconds: Optional[int]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime]

class AgentMemoryUpdateRequest(BaseModel):
    """Request model for updating agent memory"""
    memory_value: Dict[str, Any] = Field(..., description="Updated memory content")
    ttl_seconds: Optional[int] = Field(None, description="Updated TTL in seconds")


# Search and Filter Schemas

class SystemLogSearchRequest(BaseModel):
    """Request model for searching system logs"""
    level: Optional[LogLevel] = Field(None, description="Filter by log level")
    component: Optional[str] = Field(None, description="Filter by component")
    session_id: Optional[str] = Field(None, description="Filter by session")
    user_id: Optional[str] = Field(None, description="Filter by user")
    message_search: Optional[str] = Field(None, description="Search in log message")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=500, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


class AgentMemorySearchRequest(BaseModel):
    """Request model for searching agent memory"""
    agent_name: Optional[AgentType] = Field(None, description="Filter by agent")
    session_id: Optional[str] = Field(None, description="Filter by session")
    memory_type: Optional[str] = Field(None, description="Filter by memory type")
    memory_key: Optional[str] = Field(None, description="Filter by memory key")
    include_expired: bool = Field(False, description="Include expired memories")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("updated_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


# List Response Models

class SystemLogListResponse(PaginatedResponse):
    """Paginated response for system logs"""
    items: List[SystemLogResponse]


class AgentMemoryListResponse(PaginatedResponse):
    """Paginated response for agent memory"""
    items: List[AgentMemoryResponse]


# Action Response Models

class SystemLogCreateResponse(BaseResponse):
    """Response for system log creation"""
    log: SystemLogResponse


class AgentMemoryCreateResponse(BaseResponse):
    """Response for agent memory creation"""
    memory: AgentMemoryResponse


class AgentMemoryUpdateResponse(BaseResponse):
    """Response for agent memory update"""
    memory: AgentMemoryResponse


# Analytics Response Models

class SystemAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for system analytics"""
    total_logs: int
    error_count: int
    warning_count: int
    info_count: int
    error_rate: float

    # Component breakdown
    logs_by_component: Dict[str, int]
    errors_by_component: Dict[str, int]

    # Agent memory stats
    total_memories: int
    active_memories: int
    expired_memories: int
    memories_by_agent: Dict[str, int]
    memory_usage_by_type: Dict[str, int]

    # Trends
    log_volume_trend: List[Dict[str, Any]]
    error_rate_trend: List[Dict[str, Any]]
    memory_usage_trend: List[Dict[str, Any]]

    # Period
    period_start: datetime
    period_end: datetime

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for session data"""
    id: str
    user_id: Optional[str]
    session_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: datetime

class SessionCreateRequest(BaseModel):
    """Request model for creating sessions"""
    user_id: Optional[str] = Field(None, description="Associated user ID")
    session_data: Dict[str, Any] = Field(default_factory=dict, description="Session data")
    ttl_seconds: int = Field(3600, description="Session TTL in seconds")


class SessionUpdateRequest(BaseModel):
    """Request model for updating sessions"""
    session_data: Dict[str, Any] = Field(..., description="Updated session data")
    extend_ttl: bool = Field(False, description="Whether to extend TTL")


# Monitoring Schemas

class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for health checks"""
    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(..., description="Check timestamp")
    version: str = Field(..., description="Application version")

    # Service statuses
    database: str = Field(..., description="Database status")
    redis: str = Field(..., description="Redis status")

    # External services
    openai: str = Field(..., description="OpenAI API status")
    twilio: str = Field(..., description="Twilio status")
    razorpay: str = Field(..., description="Razorpay status")

    # Performance metrics
    response_time_ms: int = Field(..., description="Response time in milliseconds")
    memory_usage_mb: int = Field(..., description="Memory usage in MB")
