"""
Order Schemas
Pydantic models for PetPooja Save Order API
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime


# =============================================================================
# Addon Item Schema
# =============================================================================
class AddonItemDetails(BaseModel):
    """Addon item details within an order item"""
    id: str = Field(..., description="Addon item ID from PetPooja menu")
    name: str = Field(..., description="Addon item name")
    group_id: int = Field(..., description="Addon group ID (integer)")
    group_name: str = Field(..., description="Addon group name")
    price: str = Field(..., description="Addon price")
    quantity: str = Field(default="1", description="Addon quantity")


class AddonItem(BaseModel):
    """Addon items container"""
    details: List[AddonItemDetails] = Field(default_factory=list)


# =============================================================================
# Order Item Schema
# =============================================================================
class ItemTax(BaseModel):
    """Tax details for an order item"""
    id: str = Field(..., description="Tax ID")
    name: str = Field(..., description="Tax name")
    tax_percentage: str = Field(..., description="Tax percentage")
    amount: str = Field(..., description="Tax amount")


class OrderItemDetails(BaseModel):
    """Individual order item details"""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Item ID from PetPooja menu")
    name: str = Field(..., description="Item name")
    price: str = Field(..., description="Item base price")
    final_price: str = Field(..., description="Final price after tax/discount")
    quantity: str = Field(..., description="Item quantity")
    tax_inclusive: bool = Field(default=True, description="Whether price includes tax")
    gst_liability: str = Field(default="restaurant", description="GST liability (restaurant/vendor)")
    item_tax: List[ItemTax] = Field(default_factory=list, description="Taxes applied to item")
    item_discount: str = Field(default="", description="Discount on item")
    variation_id: str = Field(default="", description="Variation ID if applicable")
    variation_name: str = Field(default="", description="Variation name if applicable")
    description: str = Field(default="", description="Special instructions")
    addon_item: AddonItem = Field(default_factory=AddonItem, serialization_alias="AddonItem")


class OrderItem(BaseModel):
    """Order items container"""
    details: List[OrderItemDetails] = Field(..., description="List of order items")


# =============================================================================
# Customer Schema
# =============================================================================
class CustomerDetails(BaseModel):
    """Customer information"""
    name: str = Field(..., description="Customer name")
    phone: str = Field(..., description="Customer phone number")
    email: str = Field(default="", description="Customer email")
    address: str = Field(default="", description="Customer address")
    latitude: str = Field(default="", description="Delivery latitude")
    longitude: str = Field(default="", description="Delivery longitude")


class Customer(BaseModel):
    """Customer container"""
    details: CustomerDetails


# =============================================================================
# GST Details Schema
# =============================================================================
class GSTDetail(BaseModel):
    """GST liability breakdown"""
    gst_liable: str = Field(..., description="Who is liable: 'vendor' or 'restaurant'")
    amount: str = Field(..., description="GST amount")


# =============================================================================
# Order Schema
# =============================================================================
class OrderDetails(BaseModel):
    """Order details"""
    orderID: str = Field(..., description="Unique order ID")
    preorder_date: str = Field(default="", description="Preorder date (YYYY-MM-DD)")
    preorder_time: str = Field(default="", description="Preorder time (HH:MM:SS)")
    advanced_order: str = Field(default="N", description="'Y' for advanced order, 'N' for immediate")
    order_type: str = Field(..., description="Order type: H=Delivery, P=Pickup, D=DineIn")
    ondc_bap: str = Field(default="", description="ONDC BAP identifier (empty if not ONDC)")
    payment_type: str = Field(..., description="Payment type: COD, PAID, Prepaid")
    delivery_charges: str = Field(default="0", description="Delivery charges")
    dc_tax_percentage: str = Field(default="0", description="Delivery charge tax percentage")
    dc_tax_amount: str = Field(default="0", description="Delivery charge tax amount")
    dc_gst_details: List[GSTDetail] = Field(default_factory=list, description="Delivery charge GST breakdown")
    packing_charges: str = Field(default="0", description="Packing charges")
    pc_tax_percentage: str = Field(default="0", description="Packing charge tax percentage")
    pc_tax_amount: str = Field(default="0", description="Packing charge tax amount")
    pc_gst_details: List[GSTDetail] = Field(default_factory=list, description="Packing charge GST breakdown")
    service_charge: str = Field(default="0", description="Service charge")
    sc_tax_amount: str = Field(default="0", description="Service charge tax amount")
    discount_total: str = Field(default="0", description="Total discount amount")
    discount_type: str = Field(default="F", description="Discount type: F=Fixed, P=Percentage")
    tax_total: str = Field(..., description="Total tax amount")
    total: str = Field(..., description="Order total amount")
    description: str = Field(default="", description="Order description/notes")
    created_on: str = Field(..., description="Order creation timestamp (YYYY-MM-DD HH:MM:SS)")
    enable_delivery: int = Field(default=1, description="1 to enable delivery, 0 otherwise")
    callback_url: str = Field(default="", description="Webhook callback URL for order updates")
    urgent_order: bool = Field(default=False, description="Whether order is urgent")
    urgent_time: int = Field(default=30, description="Urgent delivery time in minutes")
    table_no: str = Field(default="", description="Table number for dine-in")
    no_of_persons: str = Field(default="0", description="Number of persons for dine-in")
    min_prep_time: int = Field(default=25, description="Minimum preparation time in minutes")
    collect_cash: str = Field(..., description="Cash to collect: '0' for prepaid, total for COD")
    otp: str = Field(default="", description="OTP for delivery/pickup verification")


class Order(BaseModel):
    """Order container"""
    details: OrderDetails


# =============================================================================
# Tax Schema
# =============================================================================
class TaxDetails(BaseModel):
    """Tax information"""
    id: str = Field(..., description="Tax ID")
    title: str = Field(..., description="Tax title/name")
    type: str = Field(..., description="Tax type (P for percentage, F for fixed)")
    price: str = Field(..., description="Tax base amount")
    tax: str = Field(..., description="Tax percentage or amount")
    restaurant_liable_amt: str = Field(default="0", description="Amount restaurant is liable for")


class Tax(BaseModel):
    """Tax container"""
    details: List[TaxDetails] = Field(default_factory=list)


# =============================================================================
# Discount Schema
# =============================================================================
class DiscountDetails(BaseModel):
    """Discount information"""
    id: str = Field(..., description="Discount ID")
    title: str = Field(..., description="Discount title")
    type: str = Field(..., description="Discount type")
    price: str = Field(..., description="Discount amount")


class Discount(BaseModel):
    """Discount container"""
    details: List[DiscountDetails] = Field(default_factory=list)


# =============================================================================
# Restaurant Schema
# =============================================================================
class RestaurantDetails(BaseModel):
    """Restaurant information"""
    res_name: str = Field(default="", description="Restaurant name")
    address: str = Field(default="", description="Restaurant address")
    contact_information: str = Field(default="", description="Restaurant contact info")
    restID: str = Field(..., description="PetPooja restaurant ID")


class Restaurant(BaseModel):
    """Restaurant container"""
    details: RestaurantDetails


# =============================================================================
# Main OrderInfo Schema (Inner wrapper)
# =============================================================================
class OrderInfoInner(BaseModel):
    """Complete order information structure for PetPooja (inner OrderInfo wrapper)"""
    model_config = ConfigDict(populate_by_name=True)

    restaurant: Restaurant = Field(..., serialization_alias="Restaurant")
    customer: Customer = Field(..., serialization_alias="Customer")
    order: Order = Field(..., serialization_alias="Order")
    order_item: OrderItem = Field(..., serialization_alias="OrderItem")
    tax: Tax = Field(default_factory=Tax, serialization_alias="Tax")
    discount: Discount = Field(default_factory=Discount, serialization_alias="Discount")


class OrderInfo(BaseModel):
    """Outer orderinfo container with OrderInfo wrapper"""
    model_config = ConfigDict(populate_by_name=True)

    order_info: OrderInfoInner = Field(..., serialization_alias="OrderInfo")


# =============================================================================
# Save Order Request Schema
# =============================================================================
class SaveOrderRequest(BaseModel):
    """Request body for PetPooja Save Order API"""
    model_config = ConfigDict(populate_by_name=True)

    # Credentials (added by order_client, not in schema output)
    # app_key, app_secret, access_token are added at runtime

    # Order info wrapper
    orderinfo: OrderInfo = Field(..., description="Complete order information")

    # Device identification (root level)
    udid: str = Field(default="", description="Unique device ID")
    device_type: str = Field(default="Web", description="Device type (Web/Android/iOS)")


# =============================================================================
# Response Schemas
# =============================================================================
class SaveOrderResponse(BaseModel):
    """Response from PetPooja Save Order API"""
    success: bool
    message: str
    data: Optional[dict] = None


# =============================================================================
# Update Order Status Schemas
# =============================================================================
class UpdateOrderStatusRequest(BaseModel):
    """
    Request to update order status (cancel order)

    Currently only supports status -1 (Cancel)
    """
    restID: str = Field(..., description="Restaurant ID")
    clientorderID: str = Field(..., description="Your order ID")
    cancelReason: str = Field(..., description="Reason for cancellation")
    status: str = Field(default="-1", description="Status code (-1 for cancel)")
    orderID: Optional[str] = Field(default="", description="PetPooja order ID (deprecated, pass blank)")
    errorCode: Optional[str] = Field(default="", description="Error code if any")


class UpdateOrderStatusResponse(BaseModel):
    """Response from PetPooja Update Order Status API"""
    success: bool
    message: str
    data: Optional[dict] = None
    validation_errors: Optional[dict] = None
