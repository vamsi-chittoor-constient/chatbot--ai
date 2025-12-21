"""
Booking Feature Schemas
=======================
Pydantic schemas for booking-related API requests and responses.
"""

from app.features.booking.schemas.booking import (
    # Table Management
    TableResponse,

    # Request Models
    BookingCreateRequest,
    BookingUpdateRequest,
    BookingStatusUpdateRequest,
    BookingSearchRequest,
    AvailabilityCheckRequest,

    # Response Models
    BookingResponse,
    BookingSummaryResponse,
    AvailabilityResponse,
    WaitlistResponse,

    # List Responses
    BookingListResponse,
    BookingSummaryListResponse,

    # Action Responses
    BookingCreateResponse,
    BookingUpdateResponse,
    BookingCancellationResponse,

    # Statistics
    BookingStatsResponse,
    TableAvailabilityStatsResponse,
)

__all__ = [
    # Table Management
    "TableResponse",

    # Request Models
    "BookingCreateRequest",
    "BookingUpdateRequest",
    "BookingStatusUpdateRequest",
    "BookingSearchRequest",
    "AvailabilityCheckRequest",

    # Response Models
    "BookingResponse",
    "BookingSummaryResponse",
    "AvailabilityResponse",
    "WaitlistResponse",

    # List Responses
    "BookingListResponse",
    "BookingSummaryListResponse",

    # Action Responses
    "BookingCreateResponse",
    "BookingUpdateResponse",
    "BookingCancellationResponse",

    # Statistics
    "BookingStatsResponse",
    "TableAvailabilityStatsResponse",
]
