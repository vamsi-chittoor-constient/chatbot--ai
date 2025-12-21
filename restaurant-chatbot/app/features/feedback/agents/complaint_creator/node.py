"""
Complaint Creator Agent
=======================
Handles complaint submission with auto-categorization and priority assignment.

Responsibilities:
- Collect complaint details (category, description)
- Identify related order/booking
- Assign priority based on sentiment
- Create complaint in database
- Send confirmation (SMS + Email)
"""

from typing import Dict, Any
import structlog

from app.features.feedback.state import FeedbackState
from app.features.feedback.tools.complaint_tools import create_complaint, get_user_recent_orders
from app.tools.base.tool_base import ToolStatus

logger = structlog.get_logger("agents.complaint_creator")


async def complaint_creator_agent(
    entities: Dict[str, Any],
    state: FeedbackState
) -> Dict[str, Any]:
    """
    Create a new complaint from user input.

    Args:
        entities: Extracted entities (category, description, priority)
        state: Current feedback state

    Returns:
        ActionResult dict for Response Agent
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Complaint creator executing",
        session_id=session_id,
        entities=entities
    )

    # Get required data
    description = entities.get("description") or state.get("complaint_description")
    category = entities.get("category") or state.get("complaint_category")
    priority = entities.get("priority", "medium")
    order_id = entities.get("order_id") or state.get("order_id")
    booking_id = entities.get("booking_id") or state.get("booking_id")

    # Get user authentication
    user_id = state.get("user_id")
    phone = state.get("phone") or state.get("contact_phone")

    # Validate required fields
    if not description:
        logger.warning("Missing complaint description", session_id=session_id)
        return {
            "action": "missing_description",
            "success": False,
            "data": {
                "message": "Please describe the issue you'd like to report."
            },
            "context": {}
        }

    if not category:
        logger.warning("Missing complaint category", session_id=session_id)
        return {
            "action": "missing_category",
            "success": False,
            "data": {
                "message": "What type of issue is this? (food quality, service, cleanliness, wait time, billing, or other)"
            },
            "context": {}
        }

    if not user_id and not phone:
        logger.warning("Missing user identification", session_id=session_id)
        return {
            "action": "missing_contact",
            "success": False,
            "data": {
                "message": "Please provide your phone number so we can follow up on your complaint."
            },
            "context": {}
        }

    # If no order_id/booking_id, try to identify from recent orders
    if not order_id and not booking_id and (user_id or phone):
        try:
            recent_orders_result = await get_user_recent_orders(
                user_id=user_id,
                phone_number=phone,
                limit=5
            )

            if recent_orders_result.get("success"):
                recent_orders = recent_orders_result.get("orders", [])
                if recent_orders:
                    # Auto-link to most recent order
                    order_id = recent_orders[0].get("order_id")
                    logger.info(
                        "Auto-linked to recent order",
                        session_id=session_id,
                        order_id=order_id
                    )
        except Exception as e:
            logger.warning(
                "Failed to fetch recent orders",
                error=str(e)
            )

    # Create complaint
    result = await create_complaint(
        user_id=user_id or f"phone_{phone}",  # Use phone as fallback
        description=description,
        category=category,
        priority=priority,
        order_id=order_id,
        booking_id=booking_id,
        phone_number=phone
    )

    if not result.get("success"):
        logger.error(
            "Failed to create complaint",
            session_id=session_id,
            error=result.get("message")
        )
        return {
            "action": "complaint_creation_failed",
            "success": False,
            "data": {
                "message": f"Failed to create complaint: {result.get('message')}"
            },
            "context": {}
        }

    complaint_id = result.get("complaint_id")
    ticket_id = result.get("ticket_id")
    status = result.get("status")

    logger.info(
        "Complaint created successfully",
        session_id=session_id,
        complaint_id=complaint_id,
        ticket_id=ticket_id,
        priority=priority
    )

    # Update FeedbackProgress
    if state.get("feedback_progress"):
        state["feedback_progress"].complaint_id = complaint_id
        state["feedback_progress"].complaint_ticket_id = ticket_id
        state["feedback_progress"].complaint_created = True
        state["feedback_progress"].complaint_status = status
        state["feedback_progress"].confirmation_sent = True

    return {
        "action": "complaint_created",
        "success": True,
        "data": {
            "complaint_id": complaint_id,
            "ticket_id": ticket_id,
            "category": category,
            "priority": priority,
            "status": status,
            "message": result.get("message"),
            "confirmation_sent": True
        },
        "context": {
            "complaint_id": complaint_id,
            "ticket_id": ticket_id
        },
        # State updates
        "complaint_id": complaint_id,
        "complaint_ticket_id": ticket_id,
        "complaint_status": status
    }


__all__ = ["complaint_creator_agent"]
