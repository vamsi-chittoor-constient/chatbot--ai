"""
Order management Pydantic models for the Restaurant AI Assistant API.

Provides type-safe request/response models for order creation, item management,
payment processing, and order lifecycle operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.schemas.common import (
    BaseResponse, SuccessResponse, PaginatedResponse,
    OrderTypeEnum, OrderStatusEnum, PaymentStatusEnum,
    CurrencyAmount, SortOrder, DateRangeFilter
)


# Order Item Request Models
class OrderItemAddRequest(BaseModel):
    """Request model for adding an item to an order"""
    menu_item_id: str = Field(..., description="Menu item identifier")
    quantity: int = Field(..., ge=1, le=99, description="Item quantity")
    unit_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, description="Override unit price")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Item customizations")
    special_instructions: Optional[str] = Field(None, max_length=500, description="Special preparation instructions")

    @field_validator('unit_price')
    @classmethod
    def validate_unit_price(cls, v):
        """Validate unit price format"""
        if v is None:
            return v
        return round(Decimal(str(v)), 2)

class OrderItemUpdateRequest(BaseModel):
    """Request model for updating an order item"""
    quantity: Optional[int] = Field(None, ge=1, le=99, description="Updated quantity")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Updated customizations")
    special_instructions: Optional[str] = Field(None, max_length=500, description="Updated instructions")

class OrderCreateRequest(BaseModel):
    """Request model for creating a new order"""
    user_id: str = Field(..., description="User identifier")
    booking_id: Optional[str] = Field(None, description="Associated booking ID (for dine-in)")
    order_type: OrderTypeEnum = Field(..., description="Order type")
    contact_phone: str = Field(..., description="Contact phone number for order updates")
    delivery_address: Optional[str] = Field(None, max_length=1000, description="Delivery address (required for delivery)")
    special_instructions: Optional[str] = Field(None, max_length=1000, description="Order-level special instructions")
    tip_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2, description="Tip amount")

    @model_validator(mode='before')
    @classmethod
    def validate_delivery_requirements(cls, values):
        """Validate delivery address for delivery orders"""
        if isinstance(values, dict):
            order_type = values.get('order_type')
            delivery_address = values.get('delivery_address')

            if order_type == OrderTypeEnum.DELIVERY and not delivery_address:
                raise ValueError('Delivery address is required for delivery orders')

        return values

    @field_validator('tip_amount')
    @classmethod
    def validate_tip_amount(cls, v):
        """Validate tip amount format"""
        if v is None:
            return v
        return round(Decimal(str(v)), 2)

class OrderStatusUpdateRequest(BaseModel):
    """Request model for updating order status"""
    status: OrderStatusEnum = Field(..., description="New order status")
    estimated_ready_time: Optional[datetime] = Field(None, description="Estimated ready/delivery time")
    notes: Optional[str] = Field(None, max_length=500, description="Status update notes")

class OrderSearchRequest(BaseModel):
    """Request model for searching orders"""
    user_id: Optional[str] = Field(None, description="Filter by user")
    order_number: Optional[str] = Field(None, description="Search by order number")
    order_type: Optional[OrderTypeEnum] = Field(None, description="Filter by order type")
    status: Optional[OrderStatusEnum] = Field(None, description="Filter by status")
    contact_phone: Optional[str] = Field(None, description="Search by contact phone")
    date_range: Optional[DateRangeFilter] = Field(None, description="Filter by date range")
    amount_min: Optional[Decimal] = Field(None, ge=0, description="Minimum order amount")
    amount_max: Optional[Decimal] = Field(None, ge=0, description="Maximum order amount")

    # Pagination
    page: int = Field(default=1, ge=1, description="Page number")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")

    # Sorting
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: SortOrder = Field(default=SortOrder.DESC, description="Sort order")


# Order Response Models
class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for order item data"""
    id: str = Field(..., description="Order item ID")
    menu_item_id: str = Field(..., description="Menu item ID")
    menu_item_name: Optional[str] = Field(None, description="Menu item name")
    quantity: int = Field(..., description="Item quantity")
    unit_price: Decimal = Field(..., description="Unit price")
    total_price: Decimal = Field(..., description="Total price for this item")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Item customizations")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for order data"""
    id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    booking_id: Optional[str] = Field(None, description="Associated booking ID")
    order_number: str = Field(..., description="Order number")
    order_type: str = Field(..., description="Order type")
    status: str = Field(..., description="Order status")
    subtotal: Decimal = Field(..., description="Subtotal amount")
    tax_amount: Decimal = Field(..., description="Tax amount")
    discount_amount: Decimal = Field(..., description="Discount amount")
    tip_amount: Decimal = Field(..., description="Tip amount")
    total_amount: Decimal = Field(..., description="Total order amount")
    contact_phone: str = Field(..., description="Contact phone")
    delivery_address: Optional[str] = Field(None, description="Delivery address")
    special_instructions: Optional[str] = Field(None, description="Special instructions")
    estimated_ready_time: Optional[datetime] = Field(None, description="Estimated ready time")
    items: Optional[List[OrderItemResponse]] = Field(None, description="Order items")
    item_count: Optional[int] = Field(None, description="Number of items in order")
    created_at: Optional[datetime] = Field(None, description="Order creation time")
    updated_at: Optional[datetime] = Field(None, description="Last update time")

class OrderSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Condensed response model for order lists"""
    id: str = Field(..., description="Order ID")
    order_number: str = Field(..., description="Order number")
    order_type: str = Field(..., description="Order type")
    status: str = Field(..., description="Order status")
    total_amount: Decimal = Field(..., description="Total amount")
    item_count: Optional[int] = Field(None, description="Number of items")
    created_at: Optional[datetime] = Field(None, description="Creation time")

class OrderCalculationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for order cost calculations"""
    subtotal: Decimal = Field(..., description="Items subtotal")
    tax_amount: Decimal = Field(..., description="Tax amount")
    tax_rate: Decimal = Field(..., description="Tax rate applied")
    discount_amount: Decimal = Field(..., description="Discount amount")
    tip_amount: Decimal = Field(..., description="Tip amount")
    total_amount: Decimal = Field(..., description="Final total")
    breakdown: Dict[str, Decimal] = Field(..., description="Detailed cost breakdown")

class OrderListResponse(PaginatedResponse[OrderResponse]):
    """Paginated response for order lists"""
    pass


class OrderSummaryListResponse(PaginatedResponse[OrderSummaryResponse]):
    """Paginated response for condensed order lists"""
    pass


class OrderHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for user order history"""
    user_id: str = Field(..., description="User ID")
    total_orders: int = Field(..., description="Total number of orders")
    total_spent: Decimal = Field(..., description="Total amount spent")
    favorite_items: List[Dict[str, Any]] = Field(..., description="Most ordered items")
    recent_orders: List[OrderSummaryResponse] = Field(..., description="Recent orders")
    order_stats: Dict[str, Any] = Field(..., description="Order statistics")

class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for payment data"""
    id: str = Field(..., description="Payment ID")
    order_id: str = Field(..., description="Order ID")
    razorpay_payment_id: Optional[str] = Field(None, description="Razorpay payment ID")
    razorpay_order_id: Optional[str] = Field(None, description="Razorpay order ID")
    amount: Decimal = Field(..., description="Payment amount")
    currency: str = Field(..., description="Currency code")
    payment_method: Optional[str] = Field(None, description="Payment method")
    status: str = Field(..., description="Payment status")
    failure_reason: Optional[str] = Field(None, description="Failure reason if failed")
    refund_amount: Optional[Decimal] = Field(None, description="Refunded amount")
    processed_at: Optional[datetime] = Field(None, description="Processing timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

class OrderCreateResponse(BaseResponse):
    """Response model for order creation"""
    order: OrderResponse = Field(..., description="Created order information")
    payment_required: bool = Field(..., description="Whether payment is required")
    payment_url: Optional[str] = Field(None, description="Payment gateway URL")


class OrderUpdateResponse(BaseResponse):
    """Response model for order updates"""
    order: OrderResponse = Field(..., description="Updated order information")
    changes_made: List[str] = Field(..., description="List of fields that were updated")


class OrderItemAddResponse(BaseResponse):
    """Response model for adding items to order"""
    order_item: OrderItemResponse = Field(..., description="Added order item")
    order_total: OrderCalculationResponse = Field(..., description="Updated order totals")


class OrderItemUpdateResponse(BaseResponse):
    """Response model for order item updates"""
    order_item: OrderItemResponse = Field(..., description="Updated order item")
    order_total: OrderCalculationResponse = Field(..., description="Updated order totals")
    changes_made: List[str] = Field(..., description="List of fields that were updated")


class OrderStatusHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for order status history"""
    order_id: str = Field(..., description="Order ID")
    status_history: List[Dict[str, Any]] = Field(..., description="Status change history")
    current_status: str = Field(..., description="Current order status")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")

class OrderStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for order statistics"""
    total_orders: int = Field(..., description="Total number of orders")
    orders_by_status: Dict[str, int] = Field(..., description="Orders grouped by status")
    orders_by_type: Dict[str, int] = Field(..., description="Orders grouped by type")
    revenue_total: Decimal = Field(..., description="Total revenue")
    average_order_value: Optional[Decimal] = Field(None, description="Average order value")
    popular_items: List[Dict[str, Any]] = Field(..., description="Most popular menu items")
    peak_hours: Dict[str, int] = Field(..., description="Orders by hour of day")

