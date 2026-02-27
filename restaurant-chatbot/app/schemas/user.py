"""
User management Pydantic models for the Restaurant AI Assistant API.

Provides type-safe request/response models for user authentication,
profile management, and user-related operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from .common import (
    BaseResponse, PaginatedResponse,
    UserStatusEnum, PhoneNumberField, EmailField,
    DateRangeFilter, SortOrder
)


# User Request Models
class UserCreateRequest(BaseModel):
    """Request model for creating a new user"""
    phone_number: Optional[PhoneNumberField] = Field(None, description="User's phone number")
    email: Optional[EmailField] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="User's full name")
    password: Optional[str] = Field(None, min_length=8, max_length=128, description="User password")
    dietary_preferences: Optional[List[str]] = Field(default_factory=list, description="Dietary preferences")
    food_allergies: Optional[List[str]] = Field(default_factory=list, description="Food allergies")
    preferred_cuisine: Optional[List[str]] = Field(default_factory=list, description="Preferred cuisine types")
    is_anonymous: bool = Field(default=True, description="Whether user is anonymous")

    @field_validator('dietary_preferences', 'food_allergies', 'preferred_cuisine')
    @classmethod
    def validate_preference_lists(cls, v):
        """Validate preference lists"""
        if v is None:
            return []
        # Remove empty strings and duplicates
        cleaned = list(set([item.strip() for item in v if item.strip()]))
        return cleaned

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Validate password complexity"""
        if v is None:
            return v

        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        # Check for at least one letter and one digit
        has_letter = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_letter and has_digit):
            raise ValueError('Password must contain at least one letter and one digit')

        return v

class UserUpdateRequest(BaseModel):
    """Request model for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated full name")
    email: Optional[EmailField] = Field(None, description="Updated email address")
    dietary_preferences: Optional[List[str]] = Field(None, description="Updated dietary preferences")
    food_allergies: Optional[List[str]] = Field(None, description="Updated food allergies")
    preferred_cuisine: Optional[List[str]] = Field(None, description="Updated preferred cuisine")
    notification_preferences: Optional[Dict[str, Any]] = Field(None, description="Notification settings")
    ai_preferences: Optional[Dict[str, Any]] = Field(None, description="AI assistant preferences")

    @field_validator('dietary_preferences', 'food_allergies', 'preferred_cuisine')
    @classmethod
    def validate_preference_lists(cls, v):
        """Validate preference lists"""
        if v is None:
            return v
        # Remove empty strings and duplicates
        cleaned = list(set([item.strip() for item in v if item.strip()]))
        return cleaned

class UserLoginRequest(BaseModel):
    """Request model for user login"""
    phone_number: Optional[PhoneNumberField] = Field(None, description="Phone number for login")
    email: Optional[EmailField] = Field(None, description="Email for login")
    password: str = Field(..., min_length=1, description="User password")

    @model_validator(mode='before')
    @classmethod
    def validate_login_identifier(cls, values):
        """Ensure either phone_number or email is provided"""
        if isinstance(values, dict):
            phone = values.get('phone_number')
            email = values.get('email')

            if not phone and not email:
                raise ValueError('Either phone_number or email must be provided')

        return values

class UserSearchRequest(BaseModel):
    """Request model for searching users"""
    query: Optional[str] = Field(None, min_length=1, description="Search query")
    phone_number: Optional[PhoneNumberField] = Field(None, description="Search by phone number")
    email: Optional[EmailField] = Field(None, description="Search by email")
    status: Optional[UserStatusEnum] = Field(None, description="Filter by user status")
    is_verified: Optional[bool] = Field(None, description="Filter by verification status")
    created_date_range: Optional[DateRangeFilter] = Field(None, description="Filter by creation date")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")


# User Response Models
class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for user data"""
    id: str = Field(..., description="User ID")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    email: Optional[str] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    status: Optional[str] = Field(None, description="User status")
    is_anonymous: bool = Field(..., description="Whether user is anonymous")
    email_verified: bool = Field(..., description="Email verification status")
    phone_verified: bool = Field(..., description="Phone verification status")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Extended response model for user profile with preferences"""
    id: str = Field(..., description="User ID")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    email: Optional[str] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name")
    status: Optional[str] = Field(None, description="User status")
    is_anonymous: bool = Field(..., description="Whether user is anonymous")
    email_verified: bool = Field(..., description="Email verification status")
    phone_verified: bool = Field(..., description="Phone verification status")

    # Preferences and AI data
    dietary_preferences: Optional[List[str]] = Field(default_factory=list, description="Dietary preferences")
    food_allergies: Optional[List[str]] = Field(default_factory=list, description="Food allergies")
    preferred_cuisine: Optional[List[str]] = Field(default_factory=list, description="Preferred cuisines")
    notification_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Notification settings")
    ai_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="AI assistant preferences")

    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")

class UserListResponse(PaginatedResponse[UserResponse]):
    """Paginated response for user lists"""
    pass


class UserStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for user statistics"""
    total_users: int = Field(..., description="Total number of users")
    verified_users: int = Field(..., description="Number of verified users")
    anonymous_users: int = Field(..., description="Number of anonymous users")
    active_users: int = Field(..., description="Number of active users")
    new_users_today: int = Field(..., description="New users registered today")
    new_users_this_week: int = Field(..., description="New users registered this week")
    new_users_this_month: int = Field(..., description="New users registered this month")


# User Authentication Response Models
class UserLoginResponse(BaseResponse):
    """Response model for successful user login"""
    user: UserResponse = Field(..., description="User information")
    access_token: Optional[str] = Field(None, description="Access token for authentication")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    expires_at: Optional[datetime] = Field(None, description="Token expiration time")


class UserCreateResponse(BaseResponse):
    """Response model for user creation"""
    user: UserResponse = Field(..., description="Created user information")
    verification_required: bool = Field(..., description="Whether verification is required")
    verification_method: Optional[str] = Field(None, description="Required verification method (phone/email)")


class UserUpdateResponse(BaseResponse):
    """Response model for user profile updates"""
    user: UserProfileResponse = Field(..., description="Updated user profile")
    changes_made: List[str] = Field(..., description="List of fields that were updated")


# Export all user models
__all__ = [
    "UserCreateRequest",
    "UserUpdateRequest",
    "UserLoginRequest",
    "UserSearchRequest",
    "UserResponse",
    "UserProfileResponse",
    "UserListResponse",
    "UserStatsResponse",
    "UserLoginResponse",
    "UserCreateResponse",
    "UserUpdateResponse"
]
