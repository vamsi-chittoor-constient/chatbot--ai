"""
Common Pydantic models and base classes for the Restaurant AI Assistant API.

Provides base response models, pagination, validation, and common data types
that are used across all other schema modules.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Generic, TypeVar
from uuid import UUID
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator, GetCoreSchemaHandler, ConfigDict
from pydantic_core import core_schema
from enum import Enum


# Generic type for paginated responses
T = TypeVar('T')


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Base response model for all API responses"""

    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Human-readable response message")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")


class SuccessResponse(BaseResponse):
    """Success response with optional data payload"""
    success: bool = Field(default=True, description="Success indicator")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data payload")


class ErrorResponse(BaseResponse):
    """Error response with error details"""
    success: bool = Field(default=False, description="Success indicator")
    error_code: str = Field(..., description="Machine-readable error code")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Additional error information")


class ValidationErrorResponse(ErrorResponse):
    """Validation error response with field-specific errors"""
    error_code: str = Field(default="VALIDATION_ERROR", description="Error code")
    field_errors: Dict[str, List[str]] = Field(..., description="Field-specific validation errors")


class PaginationInfo(BaseModel):
    """Pagination metadata"""
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    per_page: int = Field(..., ge=1, le=100, description="Items per page")
    total_items: int = Field(..., ge=0, description="Total number of items")
    total_pages: int = Field(..., ge=0, description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

    @model_validator(mode='before')
    @classmethod
    def validate_pagination(cls, values):
        """Validate pagination consistency"""
        if isinstance(values, dict):
            total_items = values.get('total_items', 0)
            per_page = values.get('per_page', 1)
            page = values.get('page', 1)

            if total_items == 0:
                values['total_pages'] = 0
                values['has_next'] = False
                values['has_prev'] = False
            else:
                import math
                total_pages = math.ceil(total_items / per_page)
                values['total_pages'] = total_pages
                values['has_next'] = page < total_pages
                values['has_prev'] = page > 1

        return values


class PaginatedResponse(BaseResponse, Generic[T]):
    """Paginated response with items and pagination info"""
    success: bool = Field(default=True)
    items: List[T] = Field(..., description="List of items for current page")
    pagination: PaginationInfo = Field(..., description="Pagination metadata")


# Common Enums matching database enums
class UserStatusEnum(str, Enum):
    """User status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"
    DELETED = "DELETED"


class BookingStatusEnum(str, Enum):
    """Booking status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class OrderTypeEnum(str, Enum):
    """Order type enumeration"""
    DINE_IN = "dine_in"
    TAKEOUT = "takeout"
    DELIVERY = "delivery"


class OrderStatusEnum(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatusEnum(str, Enum):
    """Payment status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


# Common validation models

class PhoneNumberField(str):
    """Phone number with validation"""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Note: source_type and handler preserved for Pydantic core schema
        _ = source_type, handler

        def validate_phone(v: str) -> str:
            if not isinstance(v, str):
                raise TypeError('Phone number must be string')

            # Remove spaces and formatting
            cleaned = v.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')

            # Require country code
            if not cleaned.startswith('+'):
                raise ValueError('Phone number must start with country code (e.g., +91 for India)')

            # Validate all characters after + are digits
            if not cleaned[1:].isdigit():
                raise ValueError('Phone number can only contain digits after country code')

            # Strict validation for Indian phone numbers (+91)
            if cleaned.startswith('+91'):
                # Indian phone format: +91[6-9][0-9]{9}
                # Total length must be 13 (+91 + 10 digits)
                if len(cleaned) != 13:
                    raise ValueError('Indian phone number must be +91 followed by 10 digits (e.g., +919876543210)')

                # First digit after +91 must be 6-9 (valid mobile prefixes)
                if cleaned[3] not in '6789':
                    raise ValueError('Indian mobile number must start with 6, 7, 8, or 9 after +91')

                return cleaned

            # Generic international validation for non-Indian numbers
            if len(cleaned) < 10 or len(cleaned) > 16:
                raise ValueError('Phone number must be between 10-16 digits')

            return cleaned

        return core_schema.no_info_after_validator_function(
            validate_phone,
            core_schema.str_schema(min_length=10, max_length=16)
        )


class EmailField(str):
    """Email with validation"""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        # Note: source_type and handler preserved for Pydantic core schema
        _ = source_type, handler

        def validate_email(v: str) -> str:
            if not isinstance(v, str):
                raise TypeError('Email must be string')

            import re
            email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_regex, v):
                raise ValueError('Invalid email format')

            return v.lower()

        return core_schema.no_info_after_validator_function(
            validate_email,
            core_schema.str_schema(min_length=5, max_length=254)
        )


class CurrencyAmount(BaseModel):
    """Currency amount with proper decimal handling"""
    amount: Decimal = Field(..., ge=0, description="Amount in currency")
    currency: str = Field(default="INR", description="Currency code")

    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        # Ensure 2 decimal places for currency
        return round(Decimal(str(v)), 2)

    def __str__(self):
        if self.currency == "INR":
            return f"₹{self.amount}"
        else:
            return f"{self.amount} {self.currency}"


# Common filter models
class DateRangeFilter(BaseModel):
    """Date range filtering"""
    start_date: Optional[datetime] = Field(None, description="Start date (inclusive)")
    end_date: Optional[datetime] = Field(None, description="End date (inclusive)")

    @model_validator(mode='before')
    @classmethod
    def validate_date_range(cls, values):
        if isinstance(values, dict):
            start_date = values.get('start_date')
            end_date = values.get('end_date')

            if start_date and end_date and start_date > end_date:
                raise ValueError('Start date must be before or equal to end date')

        return values


class SortOrder(str, Enum):
    """Sort order enumeration"""
    ASC = "asc"
    DESC = "desc"


class CommonSortFields(str, Enum):
    """Common sort fields"""
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    NAME = "name"
    PRICE = "price"


# Health check response
class HealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Health check response"""
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")
    version: str = Field(..., description="API version")
    database_status: str = Field(..., description="Database connection status")
    redis_status: str = Field(..., description="Redis connection status")


# Common request metadata
class RequestMetadata(BaseModel):
    """Common request metadata"""
    user_agent: Optional[str] = Field(None, description="Client user agent")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    session_id: Optional[str] = Field(None, description="Session identifier")
    request_id: Optional[str] = Field(None, description="Request tracking ID")


# Cart response models
class CartItemResponse(BaseModel):
    """Response model for a cart item"""
    model_config = ConfigDict(from_attributes=True)

    item_id: str = Field(..., description="Menu item ID")
    name: str = Field(..., description="Item name")
    price: float = Field(..., description="Item price")
    quantity: int = Field(..., description="Item quantity")
    category: Optional[str] = Field(None, description="Category ID")


class CartResponse(BaseModel):
    """Response model for cart operations"""
    model_config = ConfigDict(from_attributes=True)

    items: List[CartItemResponse] = Field(default_factory=list, description="Cart items")
    item_count: int = Field(..., description="Number of items in cart")
    subtotal: float = Field(..., description="Cart subtotal")
    order_type: Optional[str] = Field(None, description="Order type (dine_in, takeaway, delivery)")
    message: Optional[str] = Field(None, description="Response message")


class CartOperationResponse(BaseModel):
    """Response model for cart add/update/remove operations"""
    model_config = ConfigDict(from_attributes=True)

    action: Optional[str] = Field(None, description="Action performed (added, updated, removed)")
    item_name: Optional[str] = Field(None, description="Item name")
    quantity: Optional[int] = Field(None, description="Item quantity")
    new_quantity: Optional[int] = Field(None, description="New quantity (for updates)")
    item_price: Optional[float] = Field(None, description="Item price")
    item_total: Optional[float] = Field(None, description="Item total (price * quantity)")
    cart_subtotal: Optional[float] = Field(None, description="Cart subtotal")
    cart_item_count: Optional[int] = Field(None, description="Number of items in cart")
    message: Optional[str] = Field(None, description="Response message")


class ExistingCartResponse(BaseModel):
    """Response model for checking existing cart"""
    model_config = ConfigDict(from_attributes=True)

    has_existing_cart: bool = Field(..., description="Whether an existing cart was found")
    items: List[CartItemResponse] = Field(default_factory=list, description="Cart items")
    item_count: int = Field(..., description="Number of items in cart")
    subtotal: float = Field(..., description="Cart subtotal")
    cart_age_minutes: Optional[int] = Field(None, description="Age of cart in minutes")
    message: Optional[str] = Field(None, description="Response message")


# Export all common models
__all__ = [
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "ValidationErrorResponse",
    "PaginationInfo",
    "PaginatedResponse",
    "UserStatusEnum",
    "BookingStatusEnum",
    "OrderTypeEnum",
    "OrderStatusEnum",
    "PaymentStatusEnum",
    "PhoneNumberField",
    "EmailField",
    "CurrencyAmount",
    "DateRangeFilter",
    "SortOrder",
    "CommonSortFields",
    "HealthCheckResponse",
    "RequestMetadata",
    "CartItemResponse",
    "CartResponse",
    "CartOperationResponse",
    "ExistingCartResponse"
]
