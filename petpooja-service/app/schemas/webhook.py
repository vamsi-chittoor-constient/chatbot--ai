"""
Webhook Schemas
Pydantic models for PetPooja callback/webhook requests
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict


class OrderCallbackRequest(BaseModel):
    """
    Order callback request from PetPooja

    Sent when order status changes on PetPooja POS
    """
    restID: str = Field(..., description="Restaurant ID")
    orderID: str = Field(..., description="Order ID from save order request")
    status: str = Field(..., description="Order status: -1=Cancelled, 1/2/3=Accepted, 4=Dispatched, 5=Food Ready, 10=Delivered")
    cancel_reason: Optional[str] = Field(default="", description="Cancellation reason if status=-1")
    minimum_prep_time: Optional[str] = Field(default="", description="Kitchen preparation time in minutes")
    minimum_delivery_time: Optional[str] = Field(default="", description="Delivery time in minutes")
    rider_name: Optional[str] = Field(default="", description="Delivery rider name (for self-delivery)")
    rider_phone_number: Optional[str] = Field(default="", description="Delivery rider phone number")
    is_modified: bool = Field(default=False, description="Whether order was modified by restaurant")


class OrderCallbackResponse(BaseModel):
    """Response to send back to PetPooja"""
    success: bool = Field(default=True)
    message: str = Field(default="Status updated")


# Order status constants
class OrderStatus:
    """Order status codes from PetPooja"""
    CANCELLED = "-1"
    ACCEPTED_1 = "1"
    ACCEPTED_2 = "2"
    ACCEPTED_3 = "3"
    DISPATCHED = "4"
    FOOD_READY = "5"
    DELIVERED = "10"

    @classmethod
    def is_accepted(cls, status: str) -> bool:
        """Check if status is accepted"""
        return status in [cls.ACCEPTED_1, cls.ACCEPTED_2, cls.ACCEPTED_3]

    @classmethod
    def get_status_name(cls, status: str) -> str:
        """Get human-readable status name"""
        status_map = {
            cls.CANCELLED: "Cancelled",
            cls.ACCEPTED_1: "Accepted",
            cls.ACCEPTED_2: "Accepted",
            cls.ACCEPTED_3: "Accepted",
            cls.DISPATCHED: "Dispatched",
            cls.FOOD_READY: "Food Ready",
            cls.DELIVERED: "Delivered"
        }
        return status_map.get(status, f"Unknown ({status})")


# =============================================================================
# Store Status Schemas
# =============================================================================
class StoreStatusRequest(BaseModel):
    """
    Store status request from PetPooja

    PetPooja calls this to check if restaurant is open/closed
    """
    restID: str = Field(..., description="Restaurant ID")


class StoreStatusResponse(BaseModel):
    """
    Store status response to PetPooja

    Returns current open/closed status of restaurant
    """
    status: str = Field(..., description="Response status: 'success' or 'failed'")
    store_status: str = Field(..., description="Store status: '1' for Open, '0' for Closed")
    http_code: int = Field(default=200, description="HTTP status code")
    message: str = Field(default="Store status retrieved successfully", description="Response message")


# Store status constants
class StoreStatus:
    """Store status codes"""
    OPEN = "1"
    CLOSED = "0"

    @classmethod
    def is_open(cls, status: str) -> bool:
        """Check if store is open"""
        return status == cls.OPEN

    @classmethod
    def get_status_text(cls, status: str) -> str:
        """Get human-readable status"""
        return "Open" if status == cls.OPEN else "Closed"


# =============================================================================
# Update Store Status Schemas
# =============================================================================
class UpdateStoreStatusRequest(BaseModel):
    """
    Update store status request from PetPooja

    Merchant turns store on/off from PetPooja dashboard,
    PetPooja calls this endpoint to notify integration partner
    """
    restID: str = Field(..., description="Restaurant ID")
    store_status: str = Field(..., description="Store status: '1' for Open, '0' for Closed")
    turn_on_time: Optional[str] = Field(default="", description="Next opening time (when turning off)")
    reason: Optional[str] = Field(default="", description="Reason for closing (required when store_status=0)")


class UpdateStoreStatusResponse(BaseModel):
    """
    Update store status response to PetPooja
    """
    status: str = Field(..., description="Response status: 'success' or 'failed'")
    store_status: str = Field(..., description="Store status: '1' for Open, '0' for Closed")
    message: str = Field(default="Store status updated successfully", description="Response message")


# =============================================================================
# Stock Update Schemas
# =============================================================================
class StockUpdateRequest(BaseModel):
    """
    Stock update request from PetPooja

    Called when restaurant marks items/addons as in-stock or out-of-stock
    """
    restID: str = Field(..., description="Restaurant ID")
    inStock: bool = Field(..., description="Stock status: true=available, false=out of stock")
    type: str = Field(..., description="Type: 'item' or 'addon'")
    itemID: dict = Field(..., description="Item/Addon IDs as dict")
    autoTurnOnTime: Optional[str] = Field(default="", description="Auto turn-on time: 'endofday', 'custom', or empty")
    customTurnOnTime: Optional[str] = Field(default="", description="Custom turn-on datetime (when autoTurnOnTime='custom')")


class StockUpdateResponse(BaseModel):
    """
    Stock update response to PetPooja
    """
    code: str = Field(default="200", description="Response code: '200' for success, '400' for failure")
    status: str = Field(..., description="Response status: 'success' or 'failed'")
    message: str = Field(..., description="Response message")


# =============================================================================
# Push Menu Schemas
# =============================================================================
class PushMenuRequest(BaseModel):
    """
    Push menu request from PetPooja

    PetPooja pushes the complete menu to this endpoint whenever
    merchant makes changes in their menu (items, prices, availability, etc.)
    """
    restaurants: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Restaurant information including details, address, contact"
    )
    ordertypes: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Order types (Delivery, Takeaway, Dine-in)"
    )
    categories: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Menu categories"
    )
    parentcategories: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Parent categories for menu organization"
    )
    group_categories: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Category groups (optional)"
    )
    items: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Menu items with prices, descriptions, variations"
    )
    attributes: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Item attributes (Veg, Non-Veg, etc.)"
    )
    taxes: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Tax configurations"
    )
    discounts: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Discount configurations"
    )
    addongroups: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Addon groups and their items"
    )
    variations: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="DEPRECATED - Do not consume. Use item variations instead"
    )
    success: Optional[bool] = Field(default=True, description="Request success status")
    message: Optional[str] = Field(default="", description="Response message from PetPooja")

    class Config:
        json_schema_extra = {
            "example": {
                "restaurants": [
                    {
                        "details": {
                            "restaurantname": "A24 Restaurant",
                            "address": "123 Main St",
                            "contact": "9876543210"
                        }
                    }
                ],
                "ordertypes": [
                    {"ordertypeid": "1", "ordertype": "Delivery"},
                    {"ordertypeid": "2", "ordertype": "Takeaway"}
                ],
                "categories": [
                    {
                        "categoryid": "1",
                        "categoryname": "Starters",
                        "active": "1"
                    }
                ],
                "items": [
                    {
                        "itemid": "123",
                        "itemname": "Chicken Burger",
                        "price": "250",
                        "active": "1"
                    }
                ],
                "taxes": [
                    {
                        "taxid": "1",
                        "taxname": "GST",
                        "tax": "5"
                    }
                ],
                "success": True,
                "message": "Menu data"
            }
        }


class PushMenuResponse(BaseModel):
    """
    Response to send back to PetPooja after receiving menu push
    """
    success: bool = Field(default=True, description="Whether menu was processed successfully")
    message: str = Field(default="Menu data received and processed successfully", description="Response message")
    items_processed: Optional[int] = Field(default=0, description="Number of items processed")
    categories_processed: Optional[int] = Field(default=0, description="Number of categories processed")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Menu data received and processed successfully",
                "items_processed": 45,
                "categories_processed": 8
            }
        }
