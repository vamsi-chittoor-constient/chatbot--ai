"""
History Manager Sub-Agent
=========================
Handles order/booking history and reorder functionality.

Responsibilities:
- View order history
- View booking/reservation history
- View browsing history
- Reorder from past orders
"""

from typing import Dict, Any
import structlog

from app.features.user_profile.state import ProfileState
from app.features.user_profile.tools import (
    get_order_history,
    get_booking_history,
    get_browsing_history,
    reorder_from_history
)

logger = structlog.get_logger("user_profile.agents.history_manager")


async def history_manager_agent(
    entities: Dict[str, Any],
    state: ProfileState
) -> Dict[str, Any]:
    """
    History Manager sub-agent: View history and reorder.

    Args:
        entities: Extracted entities (history_type, limit, order_id)
        state: Current profile state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")
    phone = state.get("phone")

    logger.info(
        "History manager agent executing",
        session_id=session_id,
        user_id=user_id,
        entities=entities
    )

    # Extract entities
    history_type = entities.get("history_type", "orders")  # orders, bookings, browsing
    limit = entities.get("limit", 10)
    order_id = entities.get("order_id")
    action = entities.get("action", "view")  # view, reorder

    # Check authentication for certain operations
    if history_type == "browsing" and not user_id:
        return {
            "action": "authentication_required",
            "success": False,
            "data": {
                "message": "You must be logged in to view browsing history."
            },
            "context": {
                "requires_auth": True
            }
        }

    # For orders and bookings, allow phone-based lookup
    if not user_id and not phone:
        return {
            "action": "authentication_required",
            "success": False,
            "data": {
                "message": "You must be logged in or provide your phone number to view history."
            },
            "context": {
                "requires_auth": True
            }
        }

    # Action: Reorder
    if action == "reorder" or order_id:
        logger.info("Reordering from history", user_id=user_id, order_id=order_id)

        if not order_id:
            return {
                "action": "missing_order_id",
                "success": False,
                "data": {
                    "message": "Please specify which order to reorder."
                },
                "context": {
                    "required_field": "order_id"
                }
            }

        reorder_result = await reorder_from_history(order_id, user_id, phone)

        if not reorder_result["success"]:
            return {
                "action": "reorder_failed",
                "success": False,
                "data": {
                    "message": reorder_result["message"]
                },
                "context": {}
            }

        return {
            "action": "reorder_successful",
            "success": True,
            "data": {
                "message": reorder_result["message"],
                "order_id": order_id
            },
            "context": {
                "action_completed": "reorder"
            }
        }

    # Action: View order history
    if history_type == "orders":
        logger.info("Viewing order history", user_id=user_id, phone=phone)

        orders_result = await get_order_history(user_id, phone, limit)

        if not orders_result["success"]:
            return {
                "action": "orders_fetch_failed",
                "success": False,
                "data": {
                    "message": orders_result["message"]
                },
                "context": {}
            }

        orders = orders_result["data"]["orders"]
        count = orders_result["data"]["count"]

        return {
            "action": "orders_listed",
            "success": True,
            "data": {
                "message": orders_result["message"],
                "orders": orders,
                "count": count
            },
            "context": {
                "action_completed": "view",
                "history_type": "orders"
            }
        }

    # Action: View booking history
    elif history_type == "bookings":
        logger.info("Viewing booking history", user_id=user_id, phone=phone)

        bookings_result = await get_booking_history(user_id, phone, limit)

        if not bookings_result["success"]:
            return {
                "action": "bookings_fetch_failed",
                "success": False,
                "data": {
                    "message": bookings_result["message"]
                },
                "context": {}
            }

        bookings = bookings_result["data"]["bookings"]
        count = bookings_result["data"]["count"]

        return {
            "action": "bookings_listed",
            "success": True,
            "data": {
                "message": bookings_result["message"],
                "bookings": bookings,
                "count": count
            },
            "context": {
                "action_completed": "view",
                "history_type": "bookings"
            }
        }

    # Action: View browsing history
    elif history_type == "browsing":
        logger.info("Viewing browsing history", user_id=user_id)

        browsing_result = await get_browsing_history(user_id, limit)

        if not browsing_result["success"]:
            return {
                "action": "browsing_fetch_failed",
                "success": False,
                "data": {
                    "message": browsing_result["message"]
                },
                "context": {}
            }

        browsing_history = browsing_result["data"]["browsing_history"]
        count = browsing_result["data"]["count"]

        return {
            "action": "browsing_listed",
            "success": True,
            "data": {
                "message": browsing_result["message"],
                "browsing_history": browsing_history,
                "count": count
            },
            "context": {
                "action_completed": "view",
                "history_type": "browsing"
            }
        }

    # Unknown history type
    else:
        return {
            "action": "unknown_history_type",
            "success": False,
            "data": {
                "message": f"Unknown history type: {history_type}"
            },
            "context": {}
        }


__all__ = ["history_manager_agent"]
