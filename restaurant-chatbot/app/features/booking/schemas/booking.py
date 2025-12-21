"""
Booking management Pydantic models for the Restaurant AI Assistant API.

Provides type-safe request/response models for table reservations, booking management,
waitlist functionality, and availability checking.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.schemas.common import (
    BaseResponse, PaginatedResponse,
    BookingStatusEnum, PhoneNumberField, EmailField,
    SortOrder, DateRangeFilter
)


# Table Management Models
class TableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for table information"""
    id: str = Field(..., description="Table ID")
    restaurant_id: str = Field(..., description="Restaurant ID")
    table_number: str = Field(..., description="Table number")
    capacity: int = Field(..., description="Table capacity")
    location: Optional[str] = Field(None, description="Table location")
    features: Optional[List[str]] = Field(default_factory=list, description="Table features")
    is_active: bool = Field(..., description="Table availability status")
    is_available: Optional[bool] = Field(None, description="Current availability")
    next_available_time: Optional[datetime] = Field(None, description="Next available time")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

class BookingCreateRequest(BaseModel):
    """Request model for creating a new booking"""
    user_id: str = Field(..., description="User identifier")
    restaurant_id: str = Field(..., description="Restaurant identifier")
    booking_date: datetime = Field(..., description="Booking date and time")
    party_size: int = Field(..., ge=1, le=20, description="Number of people")
    guest_name: str = Field(..., min_length=1, max_length=255, description="Primary guest name")
    contact_phone: PhoneNumberField = Field(..., description="Contact phone number")
    contact_email: Optional[EmailField] = Field(None, description="Contact email address")
    special_requests: Optional[str] = Field(None, max_length=1000, description="Special requests or notes")
    preferred_table_features: Optional[List[str]] = Field(None, description="Preferred table features")

    @field_validator('booking_date')
    @classmethod
    def validate_booking_date(cls, v):
        """Validate booking date is in the future"""
        now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
        if v <= now:
            raise ValueError('Booking date must be in the future')
        return v

    @field_validator('preferred_table_features')
    @classmethod
    def validate_table_features(cls, v):
        """Validate table features"""
        if v is None:
            return v

        valid_features = [
            'window_view', 'private', 'wheelchair_accessible', 'outdoor',
            'quiet_area', 'near_kitchen', 'booth', 'high_top'
        ]

        for feature in v:
            if feature not in valid_features:
                raise ValueError(f'Invalid table feature: {feature}. Valid options: {", ".join(valid_features)}')

        return list(set(v))  # Remove duplicates

class BookingUpdateRequest(BaseModel):
    """Request model for updating a booking"""
    booking_date: Optional[datetime] = Field(None, description="Updated booking date and time")
    party_size: Optional[int] = Field(None, ge=1, le=20, description="Updated party size")
    guest_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Updated guest name")
    contact_phone: Optional[PhoneNumberField] = Field(None, description="Updated contact phone")
    contact_email: Optional[EmailField] = Field(None, description="Updated contact email")
    special_requests: Optional[str] = Field(None, max_length=1000, description="Updated special requests")

    @field_validator('booking_date')
    @classmethod
    def validate_booking_date(cls, v):
        """Validate booking date is in the future"""
        if v is not None:
            now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
            if v <= now:
                raise ValueError('Booking date must be in the future')
        return v

class BookingStatusUpdateRequest(BaseModel):
    """Request model for updating booking status"""
    status: BookingStatusEnum = Field(..., description="New booking status")
    table_id: Optional[str] = Field(None, description="Assigned table ID (for confirmed bookings)")
    notes: Optional[str] = Field(None, max_length=500, description="Status update notes")
    reminder_sent: Optional[bool] = Field(None, description="Mark reminder as sent")

    @model_validator(mode='before')
    @classmethod
    def validate_confirmation_requirements(cls, values):
        """Validate table assignment for confirmed bookings"""
        if isinstance(values, dict):
            status = values.get('status')
            table_id = values.get('table_id')

            if status == BookingStatusEnum.CONFIRMED and not table_id:
                raise ValueError('Table assignment is required when confirming a booking')

        return values

class BookingSearchRequest(BaseModel):
    """Request model for searching bookings"""
    user_id: Optional[str] = Field(None, description="Filter by user")
    restaurant_id: Optional[str] = Field(None, description="Filter by restaurant")
    guest_name: Optional[str] = Field(None, description="Search by guest name")
    contact_phone: Optional[str] = Field(None, description="Search by phone number")
    contact_email: Optional[str] = Field(None, description="Search by email")
    confirmation_code: Optional[str] = Field(None, description="Search by confirmation code")
    status: Optional[BookingStatusEnum] = Field(None, description="Filter by status")
    date_range: Optional[DateRangeFilter] = Field(None, description="Filter by booking date range")
    party_size_min: Optional[int] = Field(None, ge=1, description="Minimum party size")
    party_size_max: Optional[int] = Field(None, ge=1, description="Maximum party size")
    is_waitlisted: Optional[bool] = Field(None, description="Filter by waitlist status")
    table_id: Optional[str] = Field(None, description="Filter by assigned table")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="booking_date", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")


class AvailabilityCheckRequest(BaseModel):
    """Request model for checking table availability"""
    restaurant_id: str = Field(..., description="Restaurant identifier")
    booking_date: datetime = Field(..., description="Desired booking date and time")
    party_size: int = Field(..., ge=1, le=20, description="Number of people")
    duration_minutes: int = Field(default=120, ge=30, le=300, description="Expected booking duration")
    preferred_features: Optional[List[str]] = Field(None, description="Preferred table features")

    @field_validator('booking_date')
    @classmethod
    def validate_booking_date(cls, v):
        """Validate booking date is in the future"""
        now = datetime.now(timezone.utc) if v.tzinfo else datetime.now()
        if v <= now:
            raise ValueError('Booking date must be in the future')
        return v

class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for booking data"""
    id: str = Field(..., description="Booking ID")
    user_id: str = Field(..., description="User ID")
    restaurant_id: str = Field(..., description="Restaurant ID")
    table_id: Optional[str] = Field(None, description="Assigned table ID")
    table_number: Optional[str] = Field(None, description="Table number")
    booking_date: datetime = Field(..., description="Booking date and time")
    party_size: int = Field(..., description="Number of people")
    status: str = Field(..., description="Booking lifecycle status (scheduled/confirmed/completed/no_show)")
    booking_status: str = Field(..., description="Booking modification status (active/modified/cancelled)")
    guest_name: str = Field(..., description="Primary guest name")
    contact_phone: str = Field(..., description="Contact phone number")
    contact_email: Optional[str] = Field(None, description="Contact email")
    special_requests: Optional[str] = Field(None, description="Special requests")
    is_waitlisted: bool = Field(..., description="Waitlist status")
    waitlist_position: Optional[int] = Field(None, description="Position on waitlist")
    confirmation_code: str = Field(..., description="Booking confirmation code")
    reminder_sent: bool = Field(..., description="Reminder notification status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

class BookingSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Condensed response model for booking lists"""
    id: str = Field(..., description="Booking ID")
    booking_date: datetime = Field(..., description="Booking date and time")
    party_size: int = Field(..., description="Party size")
    status: str = Field(..., description="Booking lifecycle status")
    booking_status: str = Field(..., description="Booking modification status (active/modified/cancelled)")
    guest_name: str = Field(..., description="Guest name")
    table_number: Optional[str] = Field(None, description="Table number")
    confirmation_code: str = Field(..., description="Confirmation code")
    is_waitlisted: bool = Field(..., description="Waitlist status")

class AvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for availability checks"""
    restaurant_id: str = Field(..., description="Restaurant ID")
    requested_date: datetime = Field(..., description="Requested booking date")
    party_size: int = Field(..., description="Requested party size")
    is_available: bool = Field(..., description="Whether tables are available")
    available_tables: List[TableResponse] = Field(..., description="Available tables")
    alternative_times: List[datetime] = Field(..., description="Alternative available times")
    waitlist_position: Optional[int] = Field(None, description="Waitlist position if no availability")
    estimated_wait_time: Optional[int] = Field(None, description="Estimated wait time in minutes")

class BookingListResponse(PaginatedResponse[BookingResponse]):
    """Paginated response for booking lists"""
    pass


class BookingSummaryListResponse(PaginatedResponse[BookingSummaryResponse]):
    """Paginated response for condensed booking lists"""
    pass


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for waitlist information"""
    restaurant_id: str = Field(..., description="Restaurant ID")
    booking_date: datetime = Field(..., description="Booking date")
    total_waitlisted: int = Field(..., description="Total people on waitlist")
    estimated_wait_time: int = Field(..., description="Estimated wait time in minutes")
    waitlist_entries: List[BookingSummaryResponse] = Field(..., description="Waitlist bookings")

class BookingCreateResponse(BaseResponse):
    """Response model for booking creation"""
    booking: BookingResponse = Field(..., description="Created booking information")
    is_waitlisted: bool = Field(..., description="Whether booking was added to waitlist")
    available_alternatives: List[datetime] = Field(default_factory=list, description="Alternative time slots")


class BookingUpdateResponse(BaseResponse):
    """Response model for booking updates"""
    booking: BookingResponse = Field(..., description="Updated booking information")
    changes_made: List[str] = Field(..., description="List of fields that were updated")
    requires_confirmation: bool = Field(default=False, description="Whether update requires new confirmation")


class BookingCancellationResponse(BaseResponse):
    """Response model for booking cancellations"""
    booking_id: str = Field(..., description="Cancelled booking ID")
    refund_eligible: bool = Field(..., description="Whether refund is eligible")
    cancellation_fee: Optional[str] = Field(None, description="Cancellation fee if applicable")
    waitlist_promoted: List[str] = Field(default_factory=list, description="Waitlisted bookings promoted")


# Booking Statistics Response Models
class BookingStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for booking statistics"""
    total_bookings: int = Field(..., description="Total number of bookings")
    bookings_by_status: Dict[str, int] = Field(..., description="Bookings grouped by status")
    average_party_size: Optional[float] = Field(None, description="Average party size")
    popular_time_slots: List[Dict[str, Any]] = Field(..., description="Most popular booking times")
    table_utilization: Dict[str, float] = Field(..., description="Table utilization rates")
    waitlist_stats: Dict[str, Any] = Field(..., description="Waitlist statistics")
    no_show_rate: Optional[float] = Field(None, description="No-show rate percentage")

class TableAvailabilityStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for table availability statistics"""
    restaurant_id: str = Field(..., description="Restaurant ID")
    date: datetime = Field(..., description="Statistics date")
    total_tables: int = Field(..., description="Total number of tables")
    occupied_tables: int = Field(..., description="Currently occupied tables")
    reserved_tables: int = Field(..., description="Reserved tables")
    available_tables: int = Field(..., description="Available tables")
    utilization_rate: float = Field(..., description="Table utilization rate")
    peak_hours: List[Dict[str, Any]] = Field(..., description="Peak utilization hours")

