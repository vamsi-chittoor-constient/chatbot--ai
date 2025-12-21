"""
NPS Surveyor Agent
==================
Handles NPS (Net Promoter Score) survey collection.

Responsibilities:
- Collect NPS scores (0-10)
- Classify as Promoter/Passive/Detractor
- Record satisfaction metrics
"""

from typing import Dict, Any
import structlog

from app.features.feedback.state import FeedbackState
from app.features.feedback.tools.nps_tools import record_nps_score

logger = structlog.get_logger("agents.nps_surveyor")


async def nps_surveyor_agent(
    entities: Dict[str, Any],
    state: FeedbackState
) -> Dict[str, Any]:
    """
    Collect and record NPS scores.

    Args:
        entities: Extracted entities (nps_score, nps_reason)
        state: Current feedback state

    Returns:
        ActionResult dict for Response Agent
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "NPS surveyor executing",
        session_id=session_id,
        entities=entities
    )

    # Get data
    nps_score = entities.get("nps_score") or state.get("nps_score")
    nps_reason = entities.get("nps_reason") or state.get("nps_reason")
    user_id = state.get("user_id")
    order_id = entities.get("order_id") or state.get("order_id")
    booking_id = entities.get("booking_id") or state.get("booking_id")

    # Validate score
    if nps_score is None:
        return {
            "action": "missing_nps_score",
            "success": False,
            "data": {
                "message": "On a scale of 0-10, how likely are you to recommend us to a friend or colleague?"
            },
            "context": {}
        }

    if not (0 <= nps_score <= 10):
        return {
            "action": "invalid_nps_score",
            "success": False,
            "data": {"message": "NPS score must be between 0 and 10"},
            "context": {}
        }

    if not user_id:
        return {
            "action": "missing_user",
            "success": False,
            "data": {"message": "Please sign in to submit your score"},
            "context": {}
        }

    # Record NPS score
    result = await record_nps_score(
        user_id=user_id,
        nps_score=nps_score,
        reason=nps_reason,
        order_id=order_id,
        booking_id=booking_id,
        session_id=session_id
    )

    if not result.get("success"):
        return {
            "action": "nps_recording_failed",
            "success": False,
            "data": {"message": f"Failed to record NPS: {result.get('message')}"},
            "context": {}
        }

    metric_id = result.get("metric_id")
    category = result.get("category")
    category_description = result.get("category_description")

    logger.info(
        "NPS score recorded",
        session_id=session_id,
        nps_score=nps_score,
        category=category
    )

    # Update FeedbackProgress
    if state.get("feedback_progress"):
        state["feedback_progress"].nps_score = nps_score
        state["feedback_progress"].nps_category = category
        state["feedback_progress"].nps_recorded = True
        state["feedback_progress"].metric_id = metric_id

    return {
        "action": "nps_recorded",
        "success": True,
        "data": {
            "metric_id": metric_id,
            "nps_score": nps_score,
            "category": category,
            "category_description": category_description,
            "message": result.get("message"),
            "emoji": result.get("emoji")
        },
        "context": {
            "nps_score": nps_score,
            "nps_category": category
        },
        # State updates
        "nps_score": nps_score,
        "nps_category": category,
        "metric_id": metric_id
    }


__all__ = ["nps_surveyor_agent"]
