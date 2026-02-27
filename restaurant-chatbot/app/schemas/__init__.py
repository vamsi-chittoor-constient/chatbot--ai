"""
Pydantic schemas for the Restaurant AI Assistant API.

This module provides type-safe request/response models that align with
the SQLAlchemy database models while adding API-specific validation
and serialization capabilities.

Schema Organization:
- common.py: Base models, common responses, pagination
- user.py: User authentication and profile management
- menu.py: Menu categories, items, and availability (moved to features/food_ordering/schemas/)
- order.py: Order lifecycle and item management (moved to features/food_ordering/schemas/)
- booking.py: Table reservations and availability (moved to features/booking/schemas/)
- otp.py: OTP verification and SMS validation
- satisfaction.py: Customer satisfaction and complaint management (moved to features/feedback/schemas/)
- queries.py: FAQ and policy management
- payment.py: Payment processing and transactions
- communication.py: Messaging and conversation management
- system.py: System utilities and monitoring
- legacy.py: Legacy table support (feedback, knowledge_base, ratings)
- internal.py: Internal models (preferences, devices, sessions, analytics)

Feature-Specific Schemas (Moved to Features):
- app.features.booking.schemas: Booking-related schemas
- app.features.food_ordering.schemas: Menu and order schemas
- app.features.feedback.schemas: Feedback and satisfaction schemas
"""

# Shared schemas (remain in app/schemas/)
from .common import *
from .user import *
from .otp import *
from .queries import *
from .payment import *
from .communication import *
from .system import *
from .legacy import *
from .internal import *

# Feature-specific schemas (re-exported for backward compatibility)
# from app.features.booking.schemas import *
# from app.features.food_ordering.schemas import *
# from app.features.feedback.schemas import *

__all__ = [
    # Common models
    "BaseResponse",
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse",
    "ValidationErrorResponse",

    # User models
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
    "UserUpdateResponse",

    # Menu models
    "MenuCategoryCreateRequest",
    "MenuCategoryUpdateRequest",
    "MenuCategorySearchRequest",
    "MenuItemCreateRequest",
    "MenuItemUpdateRequest",
    "MenuItemSearchRequest",
    "MenuCategoryResponse",
    "MenuItemResponse",
    "MenuItemSummaryResponse",
    "MenuCategoryListResponse",
    "MenuItemListResponse",
    "MenuItemSummaryListResponse",
    "MenuStatsResponse",
    "MenuCategoryCreateResponse",
    "MenuCategoryUpdateResponse",
    "MenuItemCreateResponse",
    "MenuItemUpdateResponse",
    "MenuBulkUpdateResponse",
    "FullMenuResponse",

    # Order models
    "OrderItemAddRequest",
    "OrderItemUpdateRequest",
    "OrderCreateRequest",
    "OrderStatusUpdateRequest",
    "OrderSearchRequest",
    "OrderItemResponse",
    "OrderResponse",
    "OrderSummaryResponse",
    "OrderCalculationResponse",
    "OrderListResponse",
    "OrderSummaryListResponse",
    "OrderHistoryResponse",
    "PaymentResponse",
    "OrderCreateResponse",
    "OrderUpdateResponse",
    "OrderItemAddResponse",
    "OrderItemUpdateResponse",
    "OrderStatusHistoryResponse",
    "OrderStatsResponse",

    # Booking models
    "TableResponse",
    "BookingCreateRequest",
    "BookingUpdateRequest",
    "BookingStatusUpdateRequest",
    "BookingSearchRequest",
    "AvailabilityCheckRequest",
    "BookingResponse",
    "BookingSummaryResponse",
    "AvailabilityResponse",
    "BookingListResponse",
    "BookingSummaryListResponse",
    "WaitlistResponse",
    "BookingCreateResponse",
    "BookingUpdateResponse",
    "BookingCancellationResponse",
    "BookingStatsResponse",
    "TableAvailabilityStatsResponse",

    # OTP models
    "OTPCreateRequest",
    "OTPValidateRequest",
    "OTPResendRequest",
    "OTPResponse",
    "OTPValidationResponse",
    "OTPCreateResponse",
    "OTPValidateResponse",
    "OTPResendResponse",
    "OTPStatsResponse",
    "OTPHealthCheckResponse",

    # Internal models
    "UserPreferencesRequest",
    "UserPreferencesResponse",
    "UserDeviceRequest",
    "UserDeviceResponse",
    "DeviceTrackingResponse",
    "SessionTokenResponse",
    "UserFavoriteRequest",
    "UserFavoriteResponse",
    "UserBrowsingHistoryResponse",
    "RestaurantConfigRequest",
    "RestaurantConfigResponse",
    "EmailLogResponse",
    "EmailLogSearchRequest",
    "EmailLogListResponse",
    "AuthSessionResponse",
    "OTPRateLimitResponse",
    "AbandonedCartResponse",
    "AbandonedCartSearchRequest",
    "AbandonedCartListResponse",
    "AbandonedBookingResponse",
    "AbandonedBookingSearchRequest",
    "AbandonedBookingListResponse",
    "APIKeyUsageResponse",
    "APIKeyUsageSearchRequest",
    "APIKeyUsageListResponse",
    "APIKeyUsageStatsResponse",
]
