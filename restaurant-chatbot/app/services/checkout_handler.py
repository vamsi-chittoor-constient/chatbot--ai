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
    from app.core.redis import get_cart_sync
    from app.core.agui_events import emit_quick_replies

    message_lower = message.lower().strip()

    # Detect checkout intent
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

    # Check if cart has items
    cart_data = get_cart_sync(session_id)
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

        return result
    except Exception as e:
        logger.error(
            "checkout_handler_failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        return f"❌ Error processing checkout: {str(e)}"


def is_checkout_message(message: str) -> bool:
    """
    Check if message is checkout-related.

    Returns:
        True if message is about checkout
    """
    message_lower = message.lower().strip()

    return any(word in message_lower for word in [
        "checkout", "check out", "place order", "complete order", "finish order"
    ])
