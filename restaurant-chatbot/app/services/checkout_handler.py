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
    from app.core.agui_events import emit_quick_replies

    message_lower = message.lower().strip()

    # ---- Detect standalone order type selection (follow-up to "dine in or take away?" prompt) ----
    # When checkout handler previously asked "dine in or take away?", the user may respond
    # with just the order type (e.g. "Take Away", "Dine In") without the word "checkout".
    standalone_order_type = None
    if message_lower in ["dine in", "dine-in", "dinein", "dine"]:
        standalone_order_type = "dine_in"
    elif message_lower in ["take away", "takeaway", "take-away", "pickup", "take out"]:
        standalone_order_type = "take_away"

    if standalone_order_type:
        # Verify cart has items before treating as checkout follow-up
        from app.core.session_events import get_sync_session_tracker
        tracker = get_sync_session_tracker(session_id)
        cart_data = tracker.get_cart_summary()
        if cart_data and cart_data.get("items"):
            logger.info(
                "checkout_order_type_followup",
                session_id=session_id,
                order_type=standalone_order_type,
                message=message_lower
            )
            from app.features.food_ordering.crew_agent import _checkout_impl
            try:
                order_type_str = "dine in" if standalone_order_type == "dine_in" else "take away"
                result = _checkout_impl(order_type_str, session_id)
                # Trigger payment workflow inline for immediate event delivery
                await _trigger_payment_workflow(session_id)
                return result
            except Exception as e:
                logger.error(
                    "checkout_followup_failed",
                    session_id=session_id,
                    error=str(e),
                    exc_info=True
                )
                return f"❌ Error processing checkout: {str(e)}"
        # If cart is empty, fall through to normal flow (crew agent will handle)

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

    # Detect order type from message
    order_type = None
    if any(word in message_lower for word in ["dine in", "dine-in", "dinein", "dine"]):
        order_type = "dine_in"
    elif any(word in message_lower for word in ["take away", "takeaway", "take-away", "pickup", "take out"]):
        order_type = "take_away"

    # If order type not specified, ask for it deterministically
    if not order_type:
        emit_quick_replies(session_id, [
            {"label": "Dine In", "action": "checkout dine in", "icon": "dineIn", "variant": "primary"},
            {"label": "Take Away", "action": "checkout take away", "icon": "takeaway", "variant": "primary"},
        ])
        return "🍽️ Would you like to **dine in** or **take away**?"

    # Order type specified - proceed to checkout
    from app.features.food_ordering.crew_agent import _checkout_impl

    try:
        order_type_str = "dine in" if order_type == "dine_in" else "take away"
        result = _checkout_impl(order_type_str, session_id)

        logger.info(
            "checkout_completed_deterministic",
            session_id=session_id,
            order_type=order_type
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
        pending_order_key = f"pending_order:{session_id}"
        pending_order_data = redis_client.get(pending_order_key)
        if pending_order_data:
            pending_order = json.loads(pending_order_data)
            items = pending_order.get("items")
            order_type = pending_order.get("order_type")

        # Run payment workflow inline (awaited) - this emits quick replies
        from app.workflows.payment_workflow import run_payment_workflow
        await run_payment_workflow(
            session_id, order_display_id, total,
            items=items, order_type=order_type
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
    Also matches standalone order type selections (follow-up to checkout prompt).

    Returns:
        True if message is about checkout or is an order type selection
    """
    message_lower = message.lower().strip()

    # Direct checkout keywords
    if any(word in message_lower for word in [
        "checkout", "check out", "place order", "complete order", "finish order"
    ]):
        return True

    # Standalone order type selections (follow-up to "dine in or take away?" prompt)
    if message_lower in ["dine in", "dine-in", "dinein", "dine",
                          "take away", "takeaway", "take-away", "pickup", "take out"]:
        return True

    return False
