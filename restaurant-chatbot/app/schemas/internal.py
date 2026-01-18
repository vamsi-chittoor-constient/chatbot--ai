"""
Internal system Pydantic models for the Restaurant AI Assistant API.

Provides type-safe request/response models for internal tracking, analytics,
and system management that are typically not exposed via public API but may
be used in admin interfaces or internal tooling.

Includes:
- User internal tracking (preferences, devices, sessions, favorites, browsing)
- Restaurant configuration
- Email logging
- Authentication sessions
- OTP rate limiting
- Abandoned cart/booking recovery
- API key usage analytics
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict, field_validator

from .common import BaseResponse, PaginatedResponse, SortOrder, DateRangeFilter


# ============================================================================
# User Internal Models
# ============================================================================

class UserPreferencesRequest(BaseModel):
    """Request model for user preferences"""
    model_config = ConfigDict(from_attributes=True)

    dietary_preferences: Optional[List[str]] = Field(default_factory=list, description="Dietary preferences")
    food_allergies: Optional[List[str]] = Field(default_factory=list, description="Food allergies")
    preferred_cuisine: Optional[List[str]] = Field(default_factory=list, description="Preferred cuisines")
    notification_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Notification settings")
    ai_preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="AI assistant preferences")


class UserPreferencesResponse(BaseModel):
    """Response model for user preferences"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Preference ID")
    user_id: str = Field(..., description="User ID")
    dietary_preferences: List[str] = Field(default_factory=list, description="Dietary preferences")
    food_allergies: List[str] = Field(default_factory=list, description="Food allergies")
    preferred_cuisine: List[str] = Field(default_factory=list, description="Preferred cuisines")
    notification_preferences: Dict[str, Any] = Field(default_factory=dict, description="Notification settings")
    ai_preferences: Dict[str, Any] = Field(default_factory=dict, description="AI assistant preferences")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class UserDeviceRequest(BaseModel):
    """Request model for user device registration"""
    model_config = ConfigDict(from_attributes=True)

    device_id: str = Field(..., min_length=1, max_length=100, description="Device identifier")
    device_type: Optional[str] = Field(None, max_length=50, description="Device type (mobile, tablet, desktop)")
    device_name: Optional[str] = Field(None, max_length=255, description="Device name")
    os: Optional[str] = Field(None, max_length=50, description="Operating system")
    browser: Optional[str] = Field(None, max_length=100, description="Browser name")
    ip_address: Optional[str] = Field(None, max_length=45, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")


class UserDeviceResponse(BaseModel):
    """Response model for user device"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Record ID")
    user_id: str = Field(..., description="User ID")
    device_id: str = Field(..., description="Device identifier")
    device_type: Optional[str] = Field(None, description="Device type")
    device_name: Optional[str] = Field(None, description="Device name")
    os: Optional[str] = Field(None, description="Operating system")
    browser: Optional[str] = Field(None, description="Browser name")
    ip_address: Optional[str] = Field(None, description="IP address")
    user_agent: Optional[str] = Field(None, description="User agent string")
    last_used_at: Optional[datetime] = Field(None, description="Last used timestamp")
    is_trusted: bool = Field(..., description="Whether device is trusted")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class DeviceTrackingResponse(BaseModel):
    """Response model for device tracking (soft personalization)"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Record ID")
    device_id: str = Field(..., description="Device identifier")
    user_id: Optional[str] = Field(None, description="User ID (None for Tier 2, set for Tier 3)")
    first_seen_at: Optional[datetime] = Field(None, description="First seen timestamp")
    last_seen_at: Optional[datetime] = Field(None, description="Last seen timestamp")
    device_fingerprint: Optional[Dict[str, Any]] = Field(None, description="Device fingerprint data")
    last_order_items: Optional[Dict[str, Any]] = Field(None, description="Last order items")
    preferred_items: Optional[List[str]] = Field(None, description="Preferred menu items")
    is_active: bool = Field(True, description="Whether device is active")


class SessionTokenResponse(BaseModel):
    """Response model for session token"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Token ID")
    user_id: str = Field(..., description="User ID")
    device_id: Optional[str] = Field(None, description="Device ID")
    token: str = Field(..., description="Session token (masked)")
    expires_at: datetime = Field(..., description="Token expiration time")
    is_active: bool = Field(..., description="Whether token is active")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    @field_validator('token')
    @classmethod
    def mask_token(cls, v: str) -> str:
        """Mask token for security - show only first and last 4 chars"""
        if len(v) > 8:
            return f"{v[:4]}...{v[-4:]}"
        return "***"


class UserFavoriteRequest(BaseModel):
    """Request model for adding user favorite"""
    model_config = ConfigDict(from_attributes=True)

    menu_item_id: str = Field(..., description="Menu item ID to favorite")
    notes: Optional[str] = Field(None, max_length=500, description="Personal notes about this favorite")


class UserFavoriteResponse(BaseModel):
    """Response model for user favorite"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Favorite ID")
    user_id: str = Field(..., description="User ID")
    menu_item_id: str = Field(..., description="Menu item ID")
    notes: Optional[str] = Field(None, description="Personal notes")
    created_at: Optional[datetime] = Field(None, description="Added timestamp")


class UserBrowsingHistoryResponse(BaseModel):
    """Response model for user browsing history"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="History ID")
    user_id: str = Field(..., description="User ID")
    menu_item_id: str = Field(..., description="Menu item ID")
    view_count: int = Field(..., description="Number of times viewed")
    last_viewed_at: datetime = Field(..., description="Last viewed timestamp")
    created_at: Optional[datetime] = Field(None, description="First viewed timestamp")


# ============================================================================
# Restaurant Configuration
# ============================================================================

class RestaurantConfigRequest(BaseModel):
    """Request model for restaurant configuration"""
    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=255, description="Restaurant name")
    restaurant_id: Optional[str] = Field(None, max_length=20, description="Restaurant chain/brand identifier (e.g., rest_a24)")
    branch_id: Optional[str] = Field(None, max_length=20, description="Human-readable branch identifier (e.g., branch_000001)")
    branch_name: Optional[str] = Field(None, max_length=255, description="Branch-specific display name")
    branch_code: Optional[str] = Field(None, max_length=10, description="Short branch code (e.g., MAIN, MUM, DEL)")
    description: Optional[str] = Field(None, description="Restaurant description")
    address: Optional[str] = Field(None, description="Restaurant address")
    phone: Optional[str] = Field(None, max_length=15, description="Restaurant phone")
    email: Optional[str] = Field(None, max_length=255, description="Restaurant email")
    business_hours: Dict[str, Any] = Field(..., description="Business hours configuration")
    policies: Optional[Dict[str, Any]] = Field(None, description="Restaurant policies")
    settings: Optional[Dict[str, Any]] = Field(None, description="Restaurant settings")


class RestaurantConfigResponse(BaseModel):
    """Response model for restaurant configuration (matches restaurant_config table)"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Restaurant configuration ID (UUID)")
    name: str = Field(..., description="Restaurant name")
    description: Optional[str] = Field(None, description="Restaurant description")
    address: Optional[str] = Field(None, description="Restaurant address")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    website: Optional[str] = Field(None, description="Website URL")
    logo_url: Optional[str] = Field(None, description="Logo image URL")
    timezone: Optional[str] = Field(None, description="Timezone")
    currency: Optional[str] = Field(None, description="Currency code")
    tax_rate: Optional[Decimal] = Field(None, description="Tax rate percentage")
    service_charge_rate: Optional[Decimal] = Field(None, description="Service charge percentage")
    opening_time: Optional[str] = Field(None, description="Opening time")
    closing_time: Optional[str] = Field(None, description="Closing time")
    is_open: Optional[bool] = Field(None, description="Whether restaurant is currently open")
    settings: Optional[Dict[str, Any]] = Field(None, description="Additional settings (includes business_hours and policies)")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    @field_validator('id', mode='before')
    @classmethod
    def convert_uuid_to_str(cls, v):
        """Convert UUID to string"""
        if v is None:
            return None
        from uuid import UUID
        if isinstance(v, UUID):
            return str(v)
        return v

    @field_validator('opening_time', 'closing_time', mode='before')
    @classmethod
    def convert_time_to_str(cls, v):
        """Convert datetime.time to string (HH:MM:SS format)"""
        if v is None:
            return None
        import datetime
        if isinstance(v, datetime.time):
            return v.isoformat()
        return v


# ============================================================================
# Email & Communication Logging
# ============================================================================

class EmailLogResponse(BaseModel):
    """Response model for email log"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Email log ID")
    user_id: Optional[str] = Field(None, description="User ID")
    recipient_email: str = Field(..., description="Recipient email")
    subject: str = Field(..., description="Email subject")
    status: str = Field(..., description="Email status (queued, sent, failed, bounced)")
    smtp_message_id: Optional[str] = Field(None, description="SMTP message ID")
    opened: bool = Field(default=False, description="Whether email was opened")
    clicked: bool = Field(default=False, description="Whether links were clicked")
    bounced: bool = Field(default=False, description="Whether email bounced")
    sent_at: Optional[datetime] = Field(None, description="Sent timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class EmailLogSearchRequest(BaseModel):
    """Request model for searching email logs"""
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    recipient_email: Optional[str] = Field(None, description="Filter by recipient email")
    status: Optional[str] = Field(None, description="Filter by status")
    date_range: Optional[DateRangeFilter] = Field(None, description="Filter by date range")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")


class EmailLogListResponse(PaginatedResponse[EmailLogResponse]):
    """Paginated response for email logs"""
    pass


# ============================================================================
# Authentication Sessions
# ============================================================================

class AuthSessionResponse(BaseModel):
    """Response model for authentication session"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Session ID")
    device_id: Optional[str] = Field(None, description="Device ID")
    user_id: Optional[str] = Field(None, description="User ID")
    phone_number: Optional[str] = Field(None, description="Phone number (masked)")
    otp_send_count: int = Field(..., description="OTP send count")
    otp_verification_attempts: int = Field(..., description="Verification attempts")
    phone_validation_attempts: int = Field(..., description="Phone validation attempts")
    locked_until: Optional[datetime] = Field(None, description="Locked until timestamp")
    lockout_reason: Optional[str] = Field(None, description="Lockout reason")
    expires_at: Optional[datetime] = Field(None, description="Session expiration")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    @field_validator('phone_number')
    @classmethod
    def mask_phone(cls, v: Optional[str]) -> Optional[str]:
        """Mask phone number for security"""
        if v and len(v) > 4:
            return f"***{v[-4:]}"
        return "****"


class OTPRateLimitResponse(BaseModel):
    """Response model for OTP rate limit"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Rate limit ID")
    phone_number: str = Field(..., description="Phone number (masked)")
    date: str = Field(..., description="Date (YYYY-MM-DD)")
    attempt_count: int = Field(..., description="Number of attempts")
    last_attempt_at: Optional[datetime] = Field(None, description="Last attempt timestamp")
    is_blocked: bool = Field(..., description="Whether phone is blocked")

    @field_validator('phone_number')
    @classmethod
    def mask_phone(cls, v: str) -> str:
        """Mask phone number for security"""
        if len(v) > 4:
            return f"***{v[-4:]}"
        return "****"


# ============================================================================
# Abandoned Cart/Booking Recovery
# ============================================================================

class AbandonedCartResponse(BaseModel):
    """Response model for abandoned cart"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Abandoned cart ID")
    user_id: Optional[str] = Field(None, description="User ID")
    device_id: Optional[str] = Field(None, description="Device ID")
    cart_items: List[Dict[str, Any]] = Field(..., description="Cart items")
    total_amount: Decimal = Field(..., description="Total cart value")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    restored: bool = Field(default=False, description="Whether cart was restored")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class AbandonedCartSearchRequest(BaseModel):
    """Request model for searching abandoned carts"""
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    device_id: Optional[str] = Field(None, description="Filter by device ID")
    min_value: Optional[Decimal] = Field(None, ge=0, description="Minimum cart value")
    restored: Optional[bool] = Field(None, description="Filter by restored status")
    date_range: Optional[DateRangeFilter] = Field(None, description="Filter by date range")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")


class AbandonedCartListResponse(PaginatedResponse[AbandonedCartResponse]):
    """Paginated response for abandoned carts"""
    pass


class AbandonedBookingResponse(BaseModel):
    """Response model for abandoned booking"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Abandoned booking ID")
    user_id: Optional[str] = Field(None, description="User ID")
    device_id: Optional[str] = Field(None, description="Device ID")
    booking_details: Dict[str, Any] = Field(..., description="Booking details")
    booking_date: Optional[str] = Field(None, description="Booking date")
    last_step_completed: Optional[str] = Field(None, description="Last completed step")
    expires_at: datetime = Field(..., description="Expiration timestamp")
    restored: bool = Field(default=False, description="Whether booking was restored")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")


class AbandonedBookingSearchRequest(BaseModel):
    """Request model for searching abandoned bookings"""
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[str] = Field(None, description="Filter by user ID")
    device_id: Optional[str] = Field(None, description="Filter by device ID")
    booking_date: Optional[str] = Field(None, description="Filter by booking date")
    restored: Optional[bool] = Field(None, description="Filter by restored status")
    date_range: Optional[DateRangeFilter] = Field(None, description="Filter by date range")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")


class AbandonedBookingListResponse(PaginatedResponse[AbandonedBookingResponse]):
    """Paginated response for abandoned bookings"""
    pass


# ============================================================================
# API Key Usage Analytics
# ============================================================================

class APIKeyUsageResponse(BaseModel):
    """Response model for API key usage"""
    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Usage record ID")
    restaurant_id: str = Field(..., description="Restaurant ID")
    api_key_hash: str = Field(..., description="API key hash (masked)")
    endpoint: str = Field(..., description="API endpoint")
    method: str = Field(..., description="HTTP method")
    status_code: int = Field(..., description="Response status code")
    response_time_ms: Optional[int] = Field(None, description="Response time in milliseconds")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    created_at: Optional[datetime] = Field(None, description="Request timestamp")

    @field_validator('api_key_hash')
    @classmethod
    def mask_api_key_hash(cls, v: str) -> str:
        """Mask API key hash for security"""
        if len(v) > 8:
            return f"{v[:4]}...{v[-4:]}"
        return "***"


class APIKeyUsageSearchRequest(BaseModel):
    """Request model for searching API key usage"""
    model_config = ConfigDict(from_attributes=True)

    restaurant_id: Optional[str] = Field(None, description="Filter by restaurant ID")
    endpoint: Optional[str] = Field(None, description="Filter by endpoint")
    method: Optional[str] = Field(None, description="Filter by HTTP method")
    status_code: Optional[int] = Field(None, description="Filter by status code")
    date_range: Optional[DateRangeFilter] = Field(None, description="Filter by date range")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")


class APIKeyUsageListResponse(PaginatedResponse[APIKeyUsageResponse]):
    """Paginated response for API key usage"""
    pass


class APIKeyUsageStatsResponse(BaseModel):
    """Response model for API key usage statistics"""
    model_config = ConfigDict(from_attributes=True)

    total_requests: int = Field(..., description="Total number of requests")
    successful_requests: int = Field(..., description="Successful requests (2xx)")
    failed_requests: int = Field(..., description="Failed requests (4xx, 5xx)")
    avg_response_time_ms: Optional[float] = Field(None, description="Average response time")
    requests_by_endpoint: Dict[str, int] = Field(default_factory=dict, description="Requests grouped by endpoint")
    requests_by_status: Dict[str, int] = Field(default_factory=dict, description="Requests grouped by status code")


# Export all internal models
__all__ = [
    # User Preferences
    "UserPreferencesRequest",
    "UserPreferencesResponse",

    # User Devices
    "UserDeviceRequest",
    "UserDeviceResponse",
    "DeviceTrackingResponse",

    # Session Tokens
    "SessionTokenResponse",

    # User Favorites
    "UserFavoriteRequest",
    "UserFavoriteResponse",

    # User Browsing History
    "UserBrowsingHistoryResponse",

    # Restaurant Config
    "RestaurantConfigRequest",
    "RestaurantConfigResponse",

    # Email Logs
    "EmailLogResponse",
    "EmailLogSearchRequest",
    "EmailLogListResponse",

    # Auth Sessions
    "AuthSessionResponse",

    # OTP Rate Limits
    "OTPRateLimitResponse",

    # Abandoned Carts
    "AbandonedCartResponse",
    "AbandonedCartSearchRequest",
    "AbandonedCartListResponse",

    # Abandoned Bookings
    "AbandonedBookingResponse",
    "AbandonedBookingSearchRequest",
    "AbandonedBookingListResponse",

    # API Key Usage
    "APIKeyUsageResponse",
    "APIKeyUsageSearchRequest",
    "APIKeyUsageListResponse",
    "APIKeyUsageStatsResponse",
]
