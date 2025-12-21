"""
Complaint Tracker Agent
=======================
Handles complaint status tracking and updates.

Responsibilities:
- View complaint status
- Update complaint progress
- Track resolution
"""

from typing import Dict, Any
import structlog

from app.features.feedback.state import FeedbackState
from app.features.feedback.tools.complaint_tools import (
    get_complaint_details,
    get_user_complaints,
    update_complaint_status
)

logger = structlog.get_logger("agents.complaint_tracker")


async def complaint_tracker_agent(
    entities: Dict[str, Any],
    state: FeedbackState
) -> Dict[str, Any]:
    """
    Track and manage existing complaints.

    Args:
        entities: Extracted entities (complaint_id, status, resolution)
        state: Current feedback state

    Returns:
        ActionResult dict for Response Agent
    """
    session_id = state.get("session_id", "unknown")
    action = entities.get("action", "view")  # view or update

    logger.info(
        "Complaint tracker executing",
        session_id=session_id,
        action=action
    )

    complaint_id = entities.get("complaint_id") or state.get("complaint_id")
    user_id = state.get("user_id")

    # If no complaint_id, list user's complaints
    if not complaint_id and user_id:
        result = await get_user_complaints(
            user_id=user_id,
            limit=10
        )

        if not result.get("success"):
            return {
                "action": "list_failed",
                "success": False,
                "data": {"message": "Failed to retrieve complaints"},
                "context": {}
            }

        complaints = result.get("complaints", [])

        return {
            "action": "complaints_listed",
            "success": True,
            "data": {
                "complaints": complaints,
                "count": len(complaints),
                "message": f"You have {len(complaints)} complaint(s) on record"
            },
            "context": {"complaints_count": len(complaints)}
        }

    # Get specific complaint details
    if complaint_id and action == "view":
        result = await get_complaint_details(complaint_id=complaint_id)

        if not result.get("success"):
            return {
                "action": "complaint_not_found",
                "success": False,
                "data": {"message": f"Complaint {complaint_id} not found"},
                "context": {}
            }

        complaint = result.get("complaint")

        # Update FeedbackProgress
        if state.get("feedback_progress"):
            state["feedback_progress"].complaint_tracked = True

        return {
            "action": "complaint_details",
            "success": True,
            "data": {
                "complaint": complaint,
                "message": "Here are your complaint details"
            },
            "context": {"complaint_id": complaint_id}
        }

    # Update complaint status
    if complaint_id and action == "update":
        new_status = entities.get("status")
        resolution = entities.get("resolution")

        result = await update_complaint_status(
            complaint_id=complaint_id,
            status=new_status,
            resolution=resolution
        )

        if not result.get("success"):
            return {
                "action": "update_failed",
                "success": False,
                "data": {"message": "Failed to update complaint"},
                "context": {}
            }

        return {
            "action": "complaint_updated",
            "success": True,
            "data": {
                "complaint_id": complaint_id,
                "status": new_status,
                "message": result.get("message")
            },
            "context": {"complaint_id": complaint_id}
        }

    return {
        "action": "insufficient_info",
        "success": False,
        "data": {"message": "Please provide a complaint ID to track"},
        "context": {}
    }


__all__ = ["complaint_tracker_agent"]
