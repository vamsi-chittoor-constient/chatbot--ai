"""
Pydantic schemas for Communication System.

This module provides type-safe request/response models for conversation management,
message handling, and multi-channel communication.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, ConfigDict
from enum import Enum

from app.schemas.common import BaseResponse, PaginatedResponse


# Enums

class MessageDirection(str, Enum):
    """Message direction enumeration"""
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class MessageChannel(str, Enum):
    """Communication channel enumeration"""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"


class ConversationStatus(str, Enum):
    """Conversation status enumeration"""
    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    ARCHIVED = "archived"


# Conversation Schemas

class ConversationCreateRequest(BaseModel):
    """Request model for creating conversations"""
    user_id: Optional[str] = Field(None, description="User ID if authenticated")
    session_id: str = Field(..., description="Session identifier")
    channel: MessageChannel = Field(MessageChannel.CHAT, description="Communication channel")
    context: Optional[Dict[str, Any]] = Field(None, description="Initial conversation context")

class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for conversations"""
    id: str
    user_id: Optional[str]
    session_id: str
    channel: str
    status: str
    context: Optional[Dict[str, Any]]
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

class MessageCreateRequest(BaseModel):
    """Request model for creating messages"""
    conversation_id: str = Field(..., description="Associated conversation ID")
    direction: MessageDirection = Field(..., description="Message direction")
    content: str = Field(..., min_length=1, max_length=4000, description="Message content")
    agent_name: Optional[str] = Field(None, description="Name of agent that generated message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional message metadata")

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for messages"""
    id: str
    conversation_id: str
    direction: str
    content: str
    agent_name: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

class MessageLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for message logs"""
    id: str
    message_id: str
    log_level: str
    log_message: str
    context: Optional[Dict[str, Any]]
    created_at: datetime

class MessageTemplateCreateRequest(BaseModel):
    """Request model for creating message templates"""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    channel: MessageChannel = Field(..., description="Target channel")
    template_text: str = Field(..., min_length=1, max_length=2000, description="Template content")
    variables: Optional[List[str]] = Field(None, description="Template variables")
    category: Optional[str] = Field(None, max_length=50, description="Template category")
    is_active: bool = Field(True, description="Whether template is active")

class MessageTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for message templates"""
    id: str
    name: str
    channel: str
    template_text: str
    variables: Optional[List[str]]
    category: Optional[str]
    usage_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

class ConversationSearchRequest(BaseModel):
    """Request model for searching conversations"""
    user_id: Optional[str] = Field(None, description="Filter by user")
    session_id: Optional[str] = Field(None, description="Filter by session")
    channel: Optional[MessageChannel] = Field(None, description="Filter by channel")
    status: Optional[ConversationStatus] = Field(None, description="Filter by status")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("updated_at", description="Sort field")
    sort_order: Optional[str] = Field("desc", description="Sort order")


class MessageSearchRequest(BaseModel):
    """Request model for searching messages"""
    conversation_id: Optional[str] = Field(None, description="Filter by conversation")
    direction: Optional[MessageDirection] = Field(None, description="Filter by direction")
    agent_name: Optional[str] = Field(None, description="Filter by agent")
    content_search: Optional[str] = Field(None, description="Search in message content")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")

    # Pagination
    page: int = Field(1, ge=1, description="Page number")
    page_size: int = Field(50, ge=1, le=200, description="Items per page")

    # Sorting
    sort_by: Optional[str] = Field("created_at", description="Sort field")
    sort_order: Optional[str] = Field("asc", description="Sort order")


# List Response Models

class ConversationListResponse(PaginatedResponse):
    """Paginated response for conversations"""
    items: List[ConversationResponse]


class MessageListResponse(PaginatedResponse):
    """Paginated response for messages"""
    items: List[MessageResponse]


class MessageTemplateListResponse(PaginatedResponse):
    """Paginated response for message templates"""
    items: List[MessageTemplateResponse]


# Action Response Models

class ConversationCreateResponse(BaseResponse):
    """Response for conversation creation"""
    conversation: ConversationResponse


class MessageCreateResponse(BaseResponse):
    """Response for message creation"""
    message_data: MessageResponse


class ConversationUpdateResponse(BaseResponse):
    """Response for conversation update"""
    conversation: ConversationResponse


# Analytics Response Models

class CommunicationAnalyticsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for communication analytics"""
    total_conversations: int
    active_conversations: int
    completed_conversations: int
    total_messages: int
    average_messages_per_conversation: float
    average_response_time_seconds: float

    # Channel breakdown
    conversations_by_channel: Dict[str, int]
    messages_by_channel: Dict[str, int]
    response_times_by_channel: Dict[str, float]

    # Agent performance
    messages_by_agent: Dict[str, int]
    response_times_by_agent: Dict[str, float]

    # Trends
    conversation_volume_trend: List[Dict[str, Any]]
    response_time_trend: List[Dict[str, Any]]

    # Period
    period_start: datetime
    period_end: datetime

class QuickMessageRequest(BaseModel):
    """Request model for sending quick messages"""
    session_id: str = Field(..., description="Session identifier")
    content: str = Field(..., min_length=1, max_length=1000, description="Message content")
    channel: MessageChannel = Field(MessageChannel.CHAT, description="Communication channel")

class QuickMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for quick messages"""
    message_id: str = Field(..., description="Created message ID")
    conversation_id: str = Field(..., description="Associated conversation ID")
    delivered: bool = Field(..., description="Whether message was delivered")
    delivery_timestamp: datetime = Field(..., description="When message was delivered")
