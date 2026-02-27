"""
Feature-Aware Error Handling
============================

Centralized error handling with feature context.

Features:
- Feature-specific error classes
- Error code tracking
- Consistent error responses
- Error logging with context
"""

from typing import Optional, Dict, Any
from app.core.logging_config import get_feature_logger


class FeatureError(Exception):
    """
    Base error class for all feature-specific errors.

    Automatically tracks feature context and error codes.
    """

    def __init__(
        self,
        feature: str,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize feature error.

        Args:
            feature: Feature name (e.g., 'food_ordering', 'booking')
            message: Error message
            error_code: Optional error code for client handling
            details: Additional error details
        """
        self.feature = feature
        self.message = message
        self.error_code = error_code
        self.details = details or {}

        # Log error with feature context
        logger = get_feature_logger(feature)
        logger.error(
            f"FeatureError: {message}",
            error_code=error_code,
            **details
        )

        super().__init__(f"[{feature}] {message}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for API responses"""
        return {
            "feature": self.feature,
            "error": self.message,
            "error_code": self.error_code,
            "details": self.details
        }


# ============================================================================
# FEATURE-SPECIFIC ERROR CLASSES
# ============================================================================

class FoodOrderingError(FeatureError):
    """Errors from food ordering feature"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("food_ordering", message, error_code, details)


# ============================================================================
# GRANULAR FOOD ORDERING ERRORS
# ============================================================================

class MenuItemNotFoundError(FoodOrderingError):
    """Menu item not found in database"""

    def __init__(
        self,
        item_name: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["item_name"] = item_name
        super().__init__(
            f"Menu item '{item_name}' not found",
            error_code=ErrorCodes.RESOURCE_NOT_FOUND,
            details=details
        )


class CartEmptyError(FoodOrderingError):
    """Cart is empty when checkout attempted"""

    def __init__(
        self,
        session_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["session_id"] = session_id
        super().__init__(
            "Cart is empty. Please add items before checkout.",
            error_code=ErrorCodes.INVALID_STATE,
            details=details
        )


class InvalidQuantityError(FoodOrderingError):
    """Invalid quantity specified"""

    def __init__(
        self,
        quantity: Any,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["quantity"] = quantity
        super().__init__(
            f"Invalid quantity: {quantity}. Must be a positive integer.",
            error_code=ErrorCodes.INVALID_INPUT,
            details=details
        )


class CartItemNotFoundError(FoodOrderingError):
    """Item not found in cart"""

    def __init__(
        self,
        item_identifier: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["item_identifier"] = item_identifier
        super().__init__(
            f"Item '{item_identifier}' not found in cart",
            error_code=ErrorCodes.RESOURCE_NOT_FOUND,
            details=details
        )


class CheckoutFailedError(FoodOrderingError):
    """Checkout process failed"""

    def __init__(
        self,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["reason"] = reason
        super().__init__(
            f"Checkout failed: {reason}",
            error_code=ErrorCodes.BUSINESS_RULE_VIOLATION,
            details=details
        )


class PaymentInitiationError(FoodOrderingError):
    """Payment initiation failed"""

    def __init__(
        self,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["reason"] = reason
        super().__init__(
            f"Payment initiation failed: {reason}",
            error_code=ErrorCodes.PAYMENT_GATEWAY_ERROR,
            details=details
        )


class BookingError(FeatureError):
    """Errors from booking feature"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("booking", message, error_code, details)


# ============================================================================
# GRANULAR BOOKING ERRORS
# ============================================================================

class TableNotAvailableError(BookingError):
    """No tables available for requested time/date"""

    def __init__(
        self,
        date: str,
        time: str,
        party_size: int,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({"date": date, "time": time, "party_size": party_size})
        super().__init__(
            f"No tables available for {party_size} guests on {date} at {time}",
            error_code=ErrorCodes.RESOURCE_UNAVAILABLE,
            details=details
        )


class ReservationNotFoundError(BookingError):
    """Reservation not found in database"""

    def __init__(
        self,
        reservation_id: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["reservation_id"] = reservation_id
        super().__init__(
            f"Reservation '{reservation_id}' not found",
            error_code=ErrorCodes.RESOURCE_NOT_FOUND,
            details=details
        )


class InvalidBookingDateError(BookingError):
    """Invalid booking date (past date, too far in future, etc.)"""

    def __init__(
        self,
        date: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({"date": date, "reason": reason})
        super().__init__(
            f"Invalid booking date '{date}': {reason}",
            error_code=ErrorCodes.INVALID_INPUT,
            details=details
        )


class InvalidPartySizeError(BookingError):
    """Invalid party size (too small, too large, or negative)"""

    def __init__(
        self,
        party_size: Any,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details["party_size"] = party_size
        super().__init__(
            f"Invalid party size: {party_size}. Must be between 1 and 20.",
            error_code=ErrorCodes.INVALID_INPUT,
            details=details
        )


class ReservationModificationFailedError(BookingError):
    """Failed to modify existing reservation"""

    def __init__(
        self,
        reservation_id: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        details = details or {}
        details.update({"reservation_id": reservation_id, "reason": reason})
        super().__init__(
            f"Failed to modify reservation '{reservation_id}': {reason}",
            error_code=ErrorCodes.BUSINESS_RULE_VIOLATION,
            details=details
        )


class FeedbackError(FeatureError):
    """Errors from feedback feature"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("feedback", message, error_code, details)


class UserAuthError(FeatureError):
    """Errors from user authentication feature"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("user_auth", message, error_code, details)


class UserProfileError(FeatureError):
    """Errors from user profile feature"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("user_profile", message, error_code, details)


class GeneralQueryError(FeatureError):
    """Errors from general queries feature"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__("general_queries", message, error_code, details)


# ============================================================================
# COMMON ERROR CODES
# ============================================================================

class ErrorCodes:
    """Standard error codes for consistent client handling"""

    # Validation errors (4xx)
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Resource errors (4xx)
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_ALREADY_EXISTS = "RESOURCE_ALREADY_EXISTS"
    RESOURCE_UNAVAILABLE = "RESOURCE_UNAVAILABLE"

    # Authentication errors (401)
    UNAUTHORIZED = "UNAUTHORIZED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"

    # Permission errors (403)
    FORBIDDEN = "FORBIDDEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # Business logic errors (422)
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_STATE = "INVALID_STATE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"

    # External service errors (502/503)
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    PAYMENT_GATEWAY_ERROR = "PAYMENT_GATEWAY_ERROR"
    NOTIFICATION_SERVICE_ERROR = "NOTIFICATION_SERVICE_ERROR"

    # System errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    CACHE_ERROR = "CACHE_ERROR"
