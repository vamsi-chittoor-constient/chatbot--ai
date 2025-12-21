"""
Feedback Collector Agent
========================
Handles feedback and rating collection.

Responsibilities:
- Collect 1-5 star ratings
- Collect written feedback
- Auto-convert negative feedback to complaints
"""

from typing import Dict, Any
import structlog

from app.features.feedback.state import FeedbackState
from app.features.feedback.tools.feedback_tools import create_feedback
from app.features.feedback.tools.complaint_tools import create_complaint

logger = structlog.get_logger("agents.feedback_collector")


async def feedback_collector_agent(
    entities: Dict[str, Any],
    state: FeedbackState
) -> Dict[str, Any]:
    """
    Collect feedback and ratings from users.

    Args:
        entities: Extracted entities (rating, feedback_text, feedback_type)
        state: Current feedback state

    Returns:
        ActionResult dict for Response Agent
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Feedback collector executing",
        session_id=session_id,
        entities=entities
    )

    # Get data
    rating = entities.get("rating") or state.get("feedback_rating")
    feedback_text = entities.get("feedback_text") or state.get("feedback_text")
    feedback_type = entities.get("feedback_type", "general")
    user_id = state.get("user_id")
    order_id = entities.get("order_id") or state.get("order_id")
    booking_id = entities.get("booking_id") or state.get("booking_id")

    # Validate rating
    if not rating:
        return {
            "action": "missing_rating",
            "success": False,
            "data": {"message": "How would you rate your experience? (1-5 stars)"},
            "context": {}
        }

    if not (1 <= rating <= 5):
        return {
            "action": "invalid_rating",
            "success": False,
            "data": {"message": "Rating must be between 1 and 5 stars"},
            "context": {}
        }

    if not user_id:
        return {
            "action": "missing_user",
            "success": False,
            "data": {"message": "Please sign in to submit feedback"},
            "context": {}
        }

    # Create feedback
    result = await create_feedback(
        user_id=user_id,
        rating=rating,
        review_text=feedback_text,
        feedback_type=feedback_type,
        order_id=order_id,
        booking_id=booking_id
    )

    if not result.get("success"):
        return {
            "action": "feedback_failed",
            "success": False,
            "data": {"message": f"Failed to submit feedback: {result.get('message')}"},
            "context": {}
        }

    feedback_id = result.get("feedback_id")

    # Auto-convert negative feedback (1-2 stars) to complaint
    auto_complaint_created = False
    complaint_id = None

    if rating <= 2 and feedback_text:
        logger.info(
            "Auto-converting negative feedback to complaint",
            session_id=session_id,
            rating=rating
        )

        complaint_result = await create_complaint(
            user_id=user_id,
            description=feedback_text,
            category="other",  # Generic category for auto-complaints
            priority="high" if rating == 1 else "medium",
            order_id=order_id,
            booking_id=booking_id
        )

        if complaint_result.get("success"):
            auto_complaint_created = True
            complaint_id = complaint_result.get("complaint_id")

            logger.info(
                "Auto-complaint created",
                session_id=session_id,
                complaint_id=complaint_id
            )

    # Update FeedbackProgress
    if state.get("feedback_progress"):
        state["feedback_progress"].feedback_id = feedback_id
        state["feedback_progress"].feedback_submitted = True
        state["feedback_progress"].feedback_rating = rating

        if auto_complaint_created:
            state["feedback_progress"].complaint_id = complaint_id
            state["feedback_progress"].complaint_created = True

    return {
        "action": "feedback_submitted",
        "success": True,
        "data": {
            "feedback_id": feedback_id,
            "rating": rating,
            "feedback_type": feedback_type,
            "message": result.get("message"),
            "auto_complaint_created": auto_complaint_created,
            "complaint_id": complaint_id if auto_complaint_created else None
        },
        "context": {
            "feedback_id": feedback_id,
            "rating": rating,
            "auto_complaint_created": auto_complaint_created
        },
        # State updates
        "feedback_id": feedback_id,
        "feedback_rating": rating
    }


__all__ = ["feedback_collector_agent"]
