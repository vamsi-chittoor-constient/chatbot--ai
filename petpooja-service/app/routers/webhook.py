"""
Webhook Router
API endpoints for PetPooja webhooks/callbacks
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
import logging

from app.schemas.webhook import (
    OrderCallbackRequest,
    OrderCallbackResponse,
    StoreStatusRequest,
    StoreStatusResponse,
    UpdateStoreStatusRequest,
    UpdateStoreStatusResponse,
    StockUpdateRequest,
    StockUpdateResponse,
    PushMenuRequest,
    PushMenuResponse
)
from app.services.webhook_service import process_order_callback, process_push_menu
from app.services.store_service import get_store_status, update_store_status_from_webhook
from app.services.stock_service import process_stock_update

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/webhooks/petpooja", tags=["Webhooks"])


@router.post("/order-callback", response_model=OrderCallbackResponse)
async def order_status_callback(
    callback_request: OrderCallbackRequest,
    request: Request
) -> Dict[str, Any]:
    """
    Receive order status updates from PetPooja

    This endpoint is called by PetPooja when order status changes:
    - Status -1: Order cancelled by restaurant
    - Status 1/2/3: Order accepted by restaurant
    - Status 4: Order dispatched (for self-delivery)
    - Status 5: Food ready for pickup
    - Status 10: Order delivered

    IMPORTANT: This endpoint MUST return 200 OK even on errors
    to prevent PetPooja from retrying failed callbacks.

    Configure this URL in your save order request:
    "callback_url": "https://your-domain.com/api/webhooks/petpooja/order-callback"

    Args:
        callback_request: Order status update data from PetPooja
        request: FastAPI request object (for logging)

    Returns:
        Success response

    Example:
        POST /api/webhooks/petpooja/order-callback
        {
            "restID": "123456",
            "orderID": "ORD-12345",
            "status": "1",
            "minimum_prep_time": "20",
            "is_modified": false
        }
    """
    try:
        # Log incoming webhook
        client_host = request.client.host if request.client else "unknown"
        logger.info(
            f"Webhook received from {client_host} - "
            f"Order: {callback_request.orderID}, Status: {callback_request.status}"
        )

        # Process the callback
        result = await process_order_callback(callback_request)

        # ALWAYS return 200 OK to prevent retries
        return OrderCallbackResponse(
            success=result.get("success", True),
            message=result.get("message", "Status updated")
        )

    except Exception as e:
        # Log error but still return 200 OK
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)

        return OrderCallbackResponse(
            success=False,
            message=f"Error processed: {str(e)}"
        )


@router.post("/test")
async def test_webhook( request: Request) -> Dict[str, Any]:
    """
    Test webhook endpoint

    Use this to verify your webhook URL is accessible

    Returns:
        Test response
    """
    print("Webhook test endpoint hit", request)
    return {
        "success": True,
        "message": "Webhook endpoint is working",
        "endpoint": "/api/webhooks/petpooja/order-callback",
        "supported_statuses": {
            "-1": "Cancelled",
            "1/2/3": "Accepted",
            "4": "Dispatched",
            "5": "Food Ready",
            "10": "Delivered"
        }
    }


@router.post("/store-status", response_model=StoreStatusResponse)
async def check_store_status_post(store_request: StoreStatusRequest) -> StoreStatusResponse:
    """
    Check restaurant store status (POST method)

    Called by PetPooja to check if restaurant is open/closed.
    Merchants can check this from their PetPooja dashboard.

    Args:
        store_request: Store status request with restaurant ID

    Returns:
        Store status response with open/closed status

    Example:
        POST /api/webhooks/petpooja/store-status
        {
            "restID": "123456"
        }

        Response:
        {
            "status": "success",
            "store_status": "1",
            "http_code": 200,
            "message": "Store is open"
        }
    """
    try:
        logger.info(f"Store status check (POST) for restaurant: {store_request.restID}")

        # Get store status
        result = await get_store_status(store_request.restID)

        return StoreStatusResponse(**result)

    except Exception as e:
        logger.error(f"Error checking store status: {str(e)}", exc_info=True)

        # Return closed status on error
        return StoreStatusResponse(
            status="failed",
            store_status="0",
            http_code=500,
            message=f"Error: {str(e)}"
        )

@router.post("/pushmenu", response_model=PushMenuResponse)
async def receive_menu_push(
    menu_data: PushMenuRequest,
    request: Request
) -> PushMenuResponse:
    """
    Receive menu push from PetPooja

    PetPooja calls this endpoint whenever merchant makes changes to the menu:
    - Item prices updated
    - New items added/removed
    - Item availability changed
    - Category changes
    - Tax/discount updates

    IMPORTANT: Always returns 200 OK to prevent PetPooja from retrying

    Configure this URL in PetPooja settings:
    "push_menu_url": "https://your-domain.com/api/webhooks/petpooja/pushmenu"

    Args:
        menu_data: Complete menu data from PetPooja
        request: FastAPI request object (for logging)

    Returns:
        Success response with processing counts

    Example Request:
        POST /api/webhooks/petpooja/pushmenu
        {
            "restaurants": [...],
            "ordertypes": [...],
            "categories": [...],
            "items": [...],
            "taxes": [...],
            "success": true,
            "message": "Menu data"
        }

    Example Response:
        {
            "success": true,
            "message": "Menu data received and processed successfully",
            "items_processed": 45,
            "categories_processed": 8
        }
    """
    try:
        # Log incoming webhook
        client_host = request.client.host if request.client else "unknown"
        logger.info(f"Push menu webhook received from {client_host}")

        # Process the menu push
        result = await process_push_menu(menu_data)

        # ALWAYS return 200 OK to prevent retries
        return PushMenuResponse(
            success=result.get("success", True),
            message=result.get("message", "Menu data received and processed successfully"),
            items_processed=result.get("items_processed", 0),
            categories_processed=result.get("categories_processed", 0)
        )

    except Exception as e:
        # Log error but still return 200 OK
        logger.error(f"Push menu processing error: {str(e)}", exc_info=True)

        return PushMenuResponse(
            success=False,
            message=f"Menu data received but error occurred: {str(e)}",
            items_processed=0,
            categories_processed=0
        )
    
@router.get("/store-status", response_model=StoreStatusResponse)
async def check_store_status_get(restID: str) -> StoreStatusResponse:
    """
    Check restaurant store status (GET method)

    Called by PetPooja to check if restaurant is open/closed.
    Merchants can check this from their PetPooja dashboard.

    Args:
        restID: Restaurant ID as query parameter

    Returns:
        Store status response with open/closed status

    Example:
        GET /api/webhooks/petpooja/store-status?restID=123456

        Response:
        {
            "status": "success",
            "store_status": "1",
            "http_code": 200,
            "message": "Store is open"
        }
    """
    try:
        logger.info(f"Store status check (GET) for restaurant: {restID}")

        # Get store status
        result = await get_store_status(restID)

        return StoreStatusResponse(**result)

    except Exception as e:
        logger.error(f"Error checking store status: {str(e)}", exc_info=True)

        # Return closed status on error
        return StoreStatusResponse(
            status="failed",
            store_status="0",
            http_code=500,
            message=f"Error: {str(e)}"
        )


@router.post("/update-store-status", response_model=UpdateStoreStatusResponse)
async def update_store_status_post(update_request: UpdateStoreStatusRequest) -> UpdateStoreStatusResponse:
    """
    Update restaurant store status (POST method)

    Called by PetPooja when merchant turns store on/off from dashboard.
    Merchant clicks "Turn On/Off" button in PetPooja -> calls this endpoint

    Args:
        update_request: Store status update request

    Returns:
        Update confirmation response

    Example:
        POST /api/webhooks/petpooja/update-store-status
        {
            "restID": "123456",
            "store_status": "0",
            "turn_on_time": "2024-01-20 10:00:00",
            "reason": "Temporary closure for maintenance"
        }

        Response:
        {
            "status": "success",
            "store_status": "0",
            "message": "Store closed successfully"
        }
    """
    try:
        logger.info(
            f"Store status update webhook - "
            f"Restaurant: {update_request.restID}, "
            f"Status: {update_request.store_status}"
        )

        # Update store status
        result = await update_store_status_from_webhook(
            restaurant_id=update_request.restID,
            store_status=update_request.store_status,
            turn_on_time=update_request.turn_on_time or "",
            reason=update_request.reason or ""
        )

        return UpdateStoreStatusResponse(**result)

    except Exception as e:
        logger.error(f"Error updating store status: {str(e)}", exc_info=True)

        # Return failed status
        return UpdateStoreStatusResponse(
            status="failed",
            store_status=update_request.store_status,
            message=f"Error: {str(e)}"
        )


@router.get("/update-store-status", response_model=UpdateStoreStatusResponse)
async def update_store_status_get(
    restID: str,
    store_status: str,
    turn_on_time: str = "",
    reason: str = ""
) -> UpdateStoreStatusResponse:
    """
    Update restaurant store status (GET method)

    Called by PetPooja when merchant turns store on/off from dashboard.
    Merchant clicks "Turn On/Off" button in PetPooja -> calls this endpoint

    Args:
        restID: Restaurant ID
        store_status: '1' for Open, '0' for Closed
        turn_on_time: Next opening time (when closing)
        reason: Reason for closing

    Returns:
        Update confirmation response

    Example:
        GET /api/webhooks/petpooja/update-store-status?restID=123456&store_status=0&reason=Maintenance

        Response:
        {
            "status": "success",
            "store_status": "0",
            "message": "Store closed successfully"
        }
    """
    try:
        logger.info(
            f"Store status update webhook (GET) - "
            f"Restaurant: {restID}, "
            f"Status: {store_status}"
        )

        # Update store status
        result = await update_store_status_from_webhook(
            restaurant_id=restID,
            store_status=store_status,
            turn_on_time=turn_on_time,
            reason=reason
        )

        return UpdateStoreStatusResponse(**result)

    except Exception as e:
        logger.error(f"Error updating store status: {str(e)}", exc_info=True)

        # Return failed status
        return UpdateStoreStatusResponse(
            status="failed",
            store_status=store_status,
            message=f"Error: {str(e)}"
        )


@router.post("/stock-update", response_model=StockUpdateResponse)
async def item_stock_update(stock_request: StockUpdateRequest) -> StockUpdateResponse:
    """
    Item/Addon stock update webhook

    Called by PetPooja when restaurant marks items/addons as in-stock or out-of-stock.
    Restaurant staff uses PetPooja POS to mark items unavailable (e.g., "Chicken Burger sold out")

    IMPORTANT: Always returns 200 OK to prevent PetPooja from retrying

    Args:
        stock_request: Stock update request data

    Returns:
        Stock update confirmation

    Example Request:
        POST /api/webhooks/petpooja/stock-update
        {
            "restID": "123456",
            "inStock": false,
            "type": "item",
            "itemID": {
                "0": "item_123",
                "1": "item_456"
            },
            "autoTurnOnTime": "custom",
            "customTurnOnTime": "2025-11-19T18:00:00"
        }

    Example Response:
        {
            "code": "200",
            "status": "success",
            "message": "Stock status updated successfully"
        }

    Auto Turn-On Options:
        - "" (empty): Manual turn-on only
        - "endofday": Auto turn-on at end of day
        - "custom": Turn on at customTurnOnTime
    """
    try:
        logger.info(
            f"Stock update webhook - "
            f"Restaurant: {stock_request.restID}, "
            f"Type: {stock_request.type}, "
            f"InStock: {stock_request.inStock}"
        )

        # Validate request
        if not stock_request.restID or stock_request.type not in ['item', 'addon']:
            return StockUpdateResponse(
                code="400",
                status="failed",
                message="Invalid request: restID and valid type required"
            )

        # Process stock update
        result = await process_stock_update(
            restaurant_id=stock_request.restID,
            in_stock=stock_request.inStock,
            item_type=stock_request.type,
            item_ids_dict=stock_request.itemID,
            auto_turn_on_time=stock_request.autoTurnOnTime or "",
            custom_turn_on_time=stock_request.customTurnOnTime or ""
        )

        # Always return 200 OK to prevent retries
        return StockUpdateResponse(**result)

    except Exception as e:
        logger.error(f"Stock update error: {str(e)}", exc_info=True)

        # Return failed response but still 200 OK
        return StockUpdateResponse(
            code="400",
            status="failed",
            message="Stock status not updated successfully"
        )
