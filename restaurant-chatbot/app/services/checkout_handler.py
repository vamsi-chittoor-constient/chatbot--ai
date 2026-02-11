"""
Checkout Message Handler
=========================
Intercepts checkout-related messages and handles them deterministically.

This runs BEFORE the main crew agent to ensure checkout is deterministic, not LLM-decided.
"""

import structlog
from typing import Optional, Dict, Any

logger = structlog.get_logger("services.checkout_handler")


async def handle_checkout_message(
    session_id: str,
    message: str
) -> Optional[str]:
    """
    Check if message is checkout-related and handle it deterministically.

    Returns:
        Response message if handled, None if should pass to crew agent
    """
    message_lower = message.lower().strip()

    # ---- Detect checkout intent ----
    is_checkout = any(word in message_lower for word in [
        "checkout", "check out", "place order", "complete order", "finish order"
    ])

    if not is_checkout:
        return None  # Not a checkout message, let crew handle it

    # If message contains item ordering keywords, let crew handle it first
    # (e.g., "I want 1 burger and checkout" - crew needs to add burger first)
    has_ordering_intent = any(word in message_lower for word in [
        "add", "want", "order", "get me", "i'll have", "i will have", "give me",
        "can i have", "can i get", "i'd like", "i would like"
    ])

    if has_ordering_intent and is_checkout:
        # Complex message with both ordering and checkout - let crew handle it
        # Crew will add items, then trigger checkout via tool
        return None

    logger.info(
        "checkout_message_intercepted",
        session_id=session_id,
        message=message_lower
    )

    # Check if cart has items (read from PostgreSQL session_cart, not Redis)
    from app.core.session_events import get_sync_session_tracker
    tracker = get_sync_session_tracker(session_id)
    cart_data = tracker.get_cart_summary()
    if not cart_data or not cart_data.get("items"):
        return "🛒 Your cart is empty! Please add some items before checkout.\n\nWould you like to see our menu?"

    # Default to takeaway - no dine-in option
    from app.features.food_ordering.crew_agent import _checkout_impl

    try:
        result = _checkout_impl("take away", session_id)

        logger.info(
            "checkout_completed_deterministic",
            session_id=session_id,
            order_type="take_away"
        )

        # Trigger payment workflow inline for immediate event delivery
        await _trigger_payment_workflow(session_id)

        return result
    except Exception as e:
        logger.error(
            "checkout_handler_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        return f"❌ Error processing checkout: {str(e)}"


async def _trigger_payment_workflow(session_id: str):
    """
    Trigger payment workflow after checkout completes.

    Reads payment info stored by _checkout_impl in Redis and runs
    the payment workflow inline (awaited) so events are staged before
    the main flush in chat.py.
    """
    try:
        from app.core.redis import get_sync_redis_client
        import json

        redis_client = get_sync_redis_client()
        payment_info_key = f"checkout_payment_info:{session_id}"
        payment_info_data = redis_client.get(payment_info_key)

        if not payment_info_data:
            logger.warning(
                "no_payment_info_after_checkout",
                session_id=session_id
            )
            return

        payment_info = json.loads(payment_info_data)
        order_display_id = payment_info["order_display_id"]
        total = payment_info["total"]

        # Clean up the temporary key
        redis_client.delete(payment_info_key)

        # Read pending order items for receipt generation
        items = None
        order_type = None
        subtotal = None
        packaging_charges = None
        pending_order_key = f"pending_order:{session_id}"
        pending_order_data = redis_client.get(pending_order_key)
        if pending_order_data:
            pending_order = json.loads(pending_order_data)
            items = pending_order.get("items")
            order_type = pending_order.get("order_type")
            subtotal = pending_order.get("subtotal")
            packaging_charges = pending_order.get("packaging_charges")

        # Run payment workflow inline (awaited) - this emits quick replies
        from app.workflows.payment_workflow import run_payment_workflow
        await run_payment_workflow(
            session_id, order_display_id, total,
            items=items, order_type=order_type,
            subtotal=subtotal, packaging_charges=packaging_charges
        )

        logger.info(
            "payment_workflow_triggered_inline",
            session_id=session_id,
            order_id=order_display_id,
            amount=total
        )
    except Exception as e:
        logger.error(
            "payment_workflow_trigger_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )


def is_checkout_message(message: str) -> bool:
    """
    Check if message is checkout-related.

    Returns:
        True if message is about checkout
    """
    message_lower = message.lower().strip()

    # Direct checkout keywords
    if any(word in message_lower for word in [
        "checkout", "check out", "place order", "complete order", "finish order"
    ]):
        return True

    return False
