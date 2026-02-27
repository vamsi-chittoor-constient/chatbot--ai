"""
Webhook Service
Handles webhook callbacks from PetPooja
"""

import logging
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.schemas.webhook import OrderCallbackRequest, OrderStatus, PushMenuRequest
from app.services.menu_service import store_menu, MenuServiceError

logger = logging.getLogger(__name__)


class WebhookServiceError(Exception):
    """Custom exception for webhook service errors"""
    pass


async def process_order_callback(callback_data: OrderCallbackRequest) -> Dict[str, Any]:
    """
    Process order status callback from PetPooja

    Args:
        callback_data: Validated callback request data

    Returns:
        Dict containing processing result

    Raises:
        WebhookServiceError: If processing fails (will still return 200 to PetPooja)
    """
    try:
        order_id = callback_data.orderID
        rest_id = callback_data.restID
        status = callback_data.status
        status_name = OrderStatus.get_status_name(status)

        logger.info(f"Processing callback - Order: {order_id}, Restaurant: {rest_id}, Status: {status_name}")

        # Process based on status
        if status == OrderStatus.CANCELLED:
            await handle_order_cancelled(callback_data)

        elif OrderStatus.is_accepted(status):
            await handle_order_accepted(callback_data)

        elif status == OrderStatus.DISPATCHED:
            await handle_order_dispatched(callback_data)

        elif status == OrderStatus.FOOD_READY:
            await handle_food_ready(callback_data)

        elif status == OrderStatus.DELIVERED:
            await handle_order_delivered(callback_data)

        else:
            logger.warning(f"Unknown order status: {status}")

        # Handle order modification
        if callback_data.is_modified:
            await handle_order_modification(callback_data)

        logger.info(f"Callback processed successfully - Order: {order_id}, Status: {status_name}")

        return {
            "success": True,
            "message": "Status updated successfully",
            "order_id": order_id,
            "status": status_name
        }

    except Exception as e:
        logger.error(f"Error processing callback: {str(e)}", exc_info=True)
        # Note: We still return success to prevent PetPooja from retrying
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "order_id": callback_data.orderID
        }


async def handle_order_cancelled(callback_data: OrderCallbackRequest):
    """
    Handle order cancellation

    Status: -1
    """
    order_id = callback_data.orderID
    cancel_reason = callback_data.cancel_reason

    logger.info(f"Order CANCELLED - {order_id}, Reason: {cancel_reason}")

    # TODO: Update order status in database
    # db.execute("""
    #     UPDATE orders
    #     SET status = 'CANCELLED',
    #         cancel_reason = %s,
    #         updated_at = %s
    #     WHERE order_id = %s
    # """, (cancel_reason, datetime.now(), order_id))

    # TODO: Notify customer about cancellation
    # await notify_customer(order_id, f'Order cancelled: {cancel_reason}')

    # TODO: Process refund if payment was completed
    # await process_refund(order_id)

    logger.info(f"Cancellation processed for order: {order_id}")


async def handle_order_accepted(callback_data: OrderCallbackRequest):
    """
    Handle order acceptance

    Status: 1, 2, or 3
    """
    order_id = callback_data.orderID
    prep_time = callback_data.minimum_prep_time

    logger.info(f"Order ACCEPTED - {order_id}, Prep Time: {prep_time} minutes")

    # TODO: Update order status in database
    # db.execute("""
    #     UPDATE orders
    #     SET status = 'ACCEPTED',
    #         prep_time = %s,
    #         updated_at = %s
    #     WHERE order_id = %s
    # """, (prep_time, datetime.now(), order_id))

    # TODO: Notify customer
    # await notify_customer(order_id, f'Order accepted! Prep time: {prep_time} min')

    logger.info(f"Acceptance processed for order: {order_id}")


async def handle_order_dispatched(callback_data: OrderCallbackRequest):
    """
    Handle order dispatch

    Status: 4
    For self-delivery restaurants
    """
    order_id = callback_data.orderID
    rider_name = callback_data.rider_name
    rider_phone = callback_data.rider_phone_number

    logger.info(f"Order DISPATCHED - {order_id}, Rider: {rider_name}, Phone: {rider_phone}")

    # TODO: Update order status in database
    # db.execute("""
    #     UPDATE orders
    #     SET status = 'DISPATCHED',
    #         rider_name = %s,
    #         rider_phone = %s,
    #         dispatched_at = %s
    #     WHERE order_id = %s
    # """, (rider_name, rider_phone, datetime.now(), order_id))

    # TODO: Notify customer
    # await notify_customer(
    #     order_id,
    #     f'Order dispatched! Rider: {rider_name}, Phone: {rider_phone}'
    # )

    logger.info(f"Dispatch processed for order: {order_id}")


async def handle_food_ready(callback_data: OrderCallbackRequest):
    """
    Handle food ready status

    Status: 5
    """
    order_id = callback_data.orderID

    logger.info(f"Order FOOD READY - {order_id}")

    # TODO: Update order status in database
    # db.execute("""
    #     UPDATE orders
    #     SET status = 'FOOD_READY',
    #         food_ready_at = %s
    #     WHERE order_id = %s
    # """, (datetime.now(), order_id))

    # TODO: Notify customer
    # await notify_customer(order_id, 'Your food is ready for pickup!')

    logger.info(f"Food ready processed for order: {order_id}")


async def handle_order_delivered(callback_data: OrderCallbackRequest):
    """
    Handle order delivery completion

    Status: 10
    """
    order_id = callback_data.orderID

    logger.info(f"Order DELIVERED - {order_id}")

    # TODO: Update order status in database
    # db.execute("""
    #     UPDATE orders
    #     SET status = 'DELIVERED',
    #         delivered_at = %s
    #     WHERE order_id = %s
    # """, (datetime.now(), order_id))

    # TODO: Notify customer
    # await notify_customer(order_id, 'Order delivered! Enjoy your meal!')

    # TODO: Send feedback request
    # await request_feedback(order_id)

    logger.info(f"Delivery processed for order: {order_id}")


async def handle_order_modification(callback_data: OrderCallbackRequest):
    """
    Handle order modification by restaurant

    is_modified: True
    """
    order_id = callback_data.orderID

    logger.info(f"Order MODIFIED - {order_id}")

    # TODO: Fetch updated order details from PetPooja if needed
    # TODO: Update order items in database
    # TODO: Notify customer about modification

    logger.info(f"Modification processed for order: {order_id}")


async def process_push_menu(menu_data: PushMenuRequest, db: Session = None) -> Dict[str, Any]:
    """
    Process push menu webhook from PetPooja

    This function is called when PetPooja pushes updated menu data
    after merchant makes changes (item prices, availability, etc.)

    Args:
        menu_data: Validated menu data from PetPooja
        db: Optional database session (for testing)

    Returns:
        Dict containing processing result with counts

    Raises:
        WebhookServiceError: If processing fails (will still return 200 to PetPooja)
    """
    try:
        # Convert Pydantic model to dict for compatibility with existing store_menu function
        menu_dict = menu_data.model_dump(exclude_none=True)

        # Extract menusharingcode from the menu data
        # This menusharingcode is used to lookup the branch via ext_petpooja_restaurant_id
        # Note: ext_petpooja_restaurant_id stores menusharingcode, not the actual restaurantid
        restaurant_id = None
        if menu_dict.get("restaurants") and len(menu_dict["restaurants"]) > 0:
            restaurant_info = menu_dict["restaurants"][0]
            restaurant_details = restaurant_info.get("details", {})

            # Extract menusharingcode from details
            restaurant_id = restaurant_details.get("menusharingcode")

        if not restaurant_id:
            logger.error("PetPooja menusharingcode not found in push menu data")
            raise WebhookServiceError(
                "Menu sharing code is required but not found in push menu data. "
                "Cannot process menu without restaurant identifier."
            )
        logger.info(f"menu_dict menu_dict: {menu_dict}")
        logger.info(f"Processing push menu for menusharingcode: {restaurant_id}")
        logger.info(
            f"Menu data summary - "
            f"Items: {len(menu_dict.get('items', []))}, "
            f"Categories: {len(menu_dict.get('categories', []))}, "
            f"Taxes: {len(menu_dict.get('taxes', []))}, "
            f"Addons: {len(menu_dict.get('addongroups', []))}"
        )

        # Store menu data using existing menu service
        store_result = store_menu(menu_dict, restaurant_id)

        # Extract counts from store result
        counts = store_result.get("counts", {})

        logger.info(
            f"Push menu processed successfully - "
            f"Menusharingcode: {restaurant_id}, "
            f"Items: {counts.get('items', 0)}, "
            f"Categories: {counts.get('categories', 0)}"
        )

        return {
            "success": True,
            "message": "Menu data received and processed successfully",
            "restaurant_id": restaurant_id,
            "items_processed": counts.get("items", 0),
            "categories_processed": counts.get("categories", 0),
            "taxes_processed": counts.get("taxes", 0),
            "addons_processed": counts.get("addon_items", 0),
            "counts": counts
        }

    except MenuServiceError as e:
        logger.error(f"Menu service error during push menu: {str(e)}", exc_info=True)
        # Return success=False but don't raise exception
        # This ensures we return 200 OK to PetPooja
        return {
            "success": False,
            "message": f"Menu data received but processing failed: {str(e)}",
            "items_processed": 0,
            "categories_processed": 0
        }

    except Exception as e:
        logger.error(f"Unexpected error processing push menu: {str(e)}", exc_info=True)
        # Return success=False but don't raise exception
        return {
            "success": False,
            "message": f"Menu data received but processing failed: {str(e)}",
            "items_processed": 0,
            "categories_processed": 0
        }
