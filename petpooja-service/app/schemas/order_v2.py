"""
Order Schemas V2 - Our Internal API Format
Clean, simple schema for our order API
"""

from pydantic import BaseModel, Field, UUID4, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime


# =============================================================================
# Customer Schema
# =============================================================================
class CustomerInfo(BaseModel):
    """Customer information"""
    name: str = Field(..., min_length=1, max_length=255, description="Customer name")
    phone: str = Field(..., pattern=r'^\d{10}$', description="10-digit phone number")
    email: Optional[str] = Field(None, description="Customer email")
    address: Optional[str] = Field(None, description="Customer address")
    latitude: Optional[float] = Field(None, description="Delivery latitude")
    longitude: Optional[float] = Field(None, description="Delivery longitude")


# =============================================================================
# Order Item Schema
# =============================================================================
class AddonInfo(BaseModel):
    """Addon information"""
    addon_id: UUID4 = Field(..., description="Addon ID from menu_item_addon_item table")
    addon_group_id: UUID4 = Field(..., description="Addon group ID")
    quantity: int = Field(..., ge=1, description="Addon quantity")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Addon price")


class OrderItemInfo(BaseModel):
    """Order item information"""
    menu_item_id: UUID4 = Field(..., description="Menu item ID")
    quantity: int = Field(..., ge=1, description="Item quantity")
    variation_id: Optional[UUID4] = Field(None, description="Variation ID if applicable")
    price: Decimal = Field(..., ge=0, decimal_places=2, description="Base price per unit")
    special_instructions: Optional[str] = Field(None, max_length=500, description="Special instructions")
    addons: List[AddonInfo] = Field(default_factory=list, description="Addons for this item")


# =============================================================================
# Charges Schema
# =============================================================================
class ChargesInfo(BaseModel):
    """Order charges"""
    delivery_charges: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    packing_charges: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    service_charge: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    platform_fee: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    convenience_fee: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    tip_amount: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)


# =============================================================================
# Tax Schema
# =============================================================================
class TaxInfo(BaseModel):
    """Tax information"""
    tax_id: UUID4 = Field(..., description="Tax ID from taxes table")
    tax_name: str = Field(..., description="Tax name (e.g., CGST, SGST)")
    tax_percentage: Decimal = Field(..., ge=0, le=100, decimal_places=2, description="Tax percentage")
    tax_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Tax amount")


# =============================================================================
# Discount Schema
# =============================================================================
class DiscountInfo(BaseModel):
    """Discount information"""
    discount_id: Optional[UUID4] = Field(None, description="Discount ID from discount table")
    discount_code: Optional[str] = Field(None, max_length=50, description="Discount code")
    discount_amount: Decimal = Field(..., ge=0, decimal_places=2, description="Discount amount")
    discount_type: str = Field(..., pattern=r'^(fixed|percentage)$', description="Discount type")


# =============================================================================
# Delivery Info Schema
# =============================================================================
class DeliveryInfoInput(BaseModel):
    """Delivery information"""
    delivery_address_id: Optional[UUID4] = Field(None, description="Saved address ID")
    enable_delivery: bool = Field(default=True, description="Enable delivery")
    delivery_slot: Optional[str] = Field(None, description="Delivery slot (YYYY-MM-DD HH:MM:SS)")
    delivery_otp: Optional[str] = Field(None, max_length=10, description="OTP for delivery")


# =============================================================================
# Dining Info Schema
# =============================================================================
class DiningInfoInput(BaseModel):
    """Dine-in information"""
    table_no: int = Field(..., ge=1, description="Table number")
    no_of_persons: int = Field(..., ge=1, description="Number of persons")


# =============================================================================
# Scheduling Schema
# =============================================================================
class SchedulingInfo(BaseModel):
    """Order scheduling information"""
    is_advanced_order: bool = Field(default=False, description="Is this an advance order")
    preorder_date: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$', description="Preorder date (YYYY-MM-DD)")
    preorder_time: Optional[str] = Field(None, pattern=r'^\d{2}:\d{2}:\d{2}$', description="Preorder time (HH:MM:SS)")
    is_urgent: bool = Field(default=False, description="Is this an urgent order")
    min_prep_time: int = Field(default=20, ge=0, description="Minimum preparation time in minutes")


# =============================================================================
# Notes Schema
# =============================================================================
class OrderNotes(BaseModel):
    """Order notes"""
    special_instructions: Optional[str] = Field(None, max_length=1000)
    kitchen_notes: Optional[str] = Field(None, max_length=1000)
    delivery_notes: Optional[str] = Field(None, max_length=1000)


# =============================================================================
# Main Order Request Schema
# =============================================================================
class CreateOrderRequest(BaseModel):
    """Request body for creating a new order"""

    # Restaurant and order type
    restaurant_id: UUID4 = Field(..., description="Internal restaurant UUID")
    order_type: str = Field(..., pattern=r'^(delivery|pickup|dine_in)$', description="Order type")
    payment_type: str = Field(..., pattern=r'^(cod|prepaid|card)$', description="Payment type")

    # Customer information
    customer: CustomerInfo = Field(..., description="Customer information")

    # Order items
    items: List[OrderItemInfo] = Field(..., min_length=1, description="Order items")

    # Charges, taxes, discounts
    charges: ChargesInfo = Field(default_factory=ChargesInfo, description="Order charges")
    taxes: List[TaxInfo] = Field(default_factory=list, description="Tax breakdown")
    discounts: List[DiscountInfo] = Field(default_factory=list, description="Discounts applied")

    # Order type specific info
    delivery_info: Optional[DeliveryInfoInput] = Field(None, description="Delivery info (required for delivery orders)")
    dining_info: Optional[DiningInfoInput] = Field(None, description="Dining info (required for dine-in orders)")

    # Scheduling
    scheduling: SchedulingInfo = Field(default_factory=SchedulingInfo, description="Order scheduling")

    # Notes
    notes: OrderNotes = Field(default_factory=OrderNotes, description="Order notes")

    # Callback
    callback_url: Optional[str] = Field(None, max_length=500, description="Webhook URL for order updates")

    @field_validator('delivery_info')
    @classmethod
    def validate_delivery_info(cls, v, info):
        """Validate delivery info is provided for delivery orders"""
        if info.data.get('order_type') == 'delivery' and v is None:
            raise ValueError('delivery_info is required for delivery orders')
        return v

    @field_validator('dining_info')
    @classmethod
    def validate_dining_info(cls, v, info):
        """Validate dining info is provided for dine-in orders"""
        if info.data.get('order_type') == 'dine_in' and v is None:
            raise ValueError('dining_info is required for dine_in orders')
        return v


# =============================================================================
# Response Schemas
# =============================================================================
class CreateOrderResponse(BaseModel):
    """Response after creating an order"""
    success: bool
    message: str
    data: Optional[dict] = None
    errors: Optional[dict] = None


class OrderData(BaseModel):
    """Order data in response"""
    order_id: UUID4
    external_order_id: str
    petpooja_sync_status: str
    total_amount: Decimal
    created_at: datetime


# =============================================================================
# Push to POS Request Schema
# =============================================================================
class PushToPosRequest(BaseModel):
    """Request body for pushing an existing order to POS"""
    order_id: UUID4 = Field(..., description="Order ID from orders table")
    restaurant_id: UUID4 = Field(..., description="Restaurant ID")


# =============================================================================
# Update Order Status Request Schema
# =============================================================================
class UpdateOrderStatusRequest(BaseModel):
    """Request body for updating order status at PetPooja"""
    order_id: UUID4 = Field(..., description="Order ID from orders table")
    restaurant_id: UUID4 = Field(..., description="Restaurant ID")
    status: str = Field(..., description="Order status: -1=Cancelled, 0=Pending, 1=Accepted, 2=Food Ready, 3=Dispatched, 4=Delivered")
    cancel_reason: Optional[str] = Field(None, max_length=500, description="Reason for cancellation (required when status is -1)")
