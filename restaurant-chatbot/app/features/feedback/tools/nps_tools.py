"""
NPS Tools
=========
Tools for NPS (Net Promoter Score) survey collection and tracking.
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool

from app.tools.database.satisfaction_tools import CreateSatisfactionMetricTool
from app.tools.base.tool_base import ToolStatus


@tool
async def record_nps_score(
    user_id: str,
    nps_score: int,
    reason: Optional[str] = None,
    order_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record Net Promoter Score (NPS) from customer.

    NPS Classification:
    - 9-10: Promoters (Loyal enthusiasts)
    - 7-8: Passives (Satisfied but unenthusiastic)
    - 0-6: Detractors (Unhappy customers)

    Args:
        user_id: Customer's user ID
        nps_score: Score from 0 to 10
        reason: Optional reason for the score
        order_id: Optional order ID
        booking_id: Optional booking ID
        session_id: Optional session ID

    Returns:
        Dict with metric_id, category, and personalized message
    """
    # Validate score
    if not (0 <= nps_score <= 10):
        return {
            "success": False,
            "message": "NPS score must be between 0 and 10"
        }

    # Classify NPS category
    if nps_score >= 9:
        category = "promoter"
        category_description = "Promoter - Loyal enthusiast"
        emoji = "🌟"
        message = "You're a Promoter! Thank you for being a valued customer who loves our service."
    elif nps_score >= 7:
        category = "passive"
        category_description = "Passive - Satisfied customer"
        emoji = "😊"
        message = "You're a Passive. We'd love to exceed your expectations next time!"
    else:
        category = "detractor"
        category_description = "Detractor - Needs attention"
        emoji = "😟"
        message = "We're sorry to hear that. Your feedback helps us improve. We'll work hard to earn your recommendation."

    metric_tool = CreateSatisfactionMetricTool()

    result = await metric_tool.execute(
        user_id=user_id,
        metric_type="nps",
        score=nps_score,
        max_score=10,
        interaction_type="order" if order_id else "booking" if booking_id else "general",
        reference_id=order_id or booking_id,
        reference_type="order" if order_id else "booking" if booking_id else None,
        session_id=session_id,
        category=category,
        additional_data={"reason": reason, "category_description": category_description} if reason else {"category_description": category_description}
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to record NPS score"
        }

    return {
        "success": True,
        "metric_id": result.data.get("metric_id"),
        "nps_score": nps_score,
        "category": category,
        "category_description": category_description,
        "emoji": emoji,
        "message": message,
        "reason": reason
    }


@tool
async def record_csat_score(
    user_id: str,
    csat_score: int,
    max_score: int = 5,
    interaction_type: str = "general",
    order_id: Optional[str] = None,
    booking_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record Customer Satisfaction (CSAT) score.

    Typically 1-5 scale (but configurable).

    Args:
        user_id: Customer's user ID
        csat_score: Satisfaction score
        max_score: Maximum score (default: 5)
        interaction_type: Type of interaction (order, booking, support, general)
        order_id: Optional order ID
        booking_id: Optional booking ID

    Returns:
        Dict with metric_id and confirmation
    """
    if not (1 <= csat_score <= max_score):
        return {
            "success": False,
            "message": f"CSAT score must be between 1 and {max_score}"
        }

    metric_tool = CreateSatisfactionMetricTool()

    result = await metric_tool.execute(
        user_id=user_id,
        metric_type="csat",
        score=csat_score,
        max_score=max_score,
        interaction_type=interaction_type,
        reference_id=order_id or booking_id,
        reference_type="order" if order_id else "booking" if booking_id else None
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to record CSAT score"
        }

    satisfaction_level = "Very Satisfied" if csat_score >= max_score * 0.8 else \
                        "Satisfied" if csat_score >= max_score * 0.6 else \
                        "Neutral" if csat_score >= max_score * 0.4 else \
                        "Dissatisfied"

    return {
        "success": True,
        "metric_id": result.data.get("metric_id"),
        "csat_score": csat_score,
        "max_score": max_score,
        "satisfaction_level": satisfaction_level,
        "message": f"Thank you! Your satisfaction score: {csat_score}/{max_score} ({satisfaction_level})"
    }


@tool
async def record_ces_score(
    user_id: str,
    ces_score: int,
    max_score: int = 7,
    interaction_type: str = "general",
    order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Record Customer Effort Score (CES).

    Measures ease of experience (typically 1-7 scale).
    Lower scores = less effort = better experience

    Args:
        user_id: Customer's user ID
        ces_score: Effort score (1=very easy, 7=very difficult)
        max_score: Maximum score (default: 7)
        interaction_type: Type of interaction
        order_id: Optional order ID

    Returns:
        Dict with metric_id and confirmation
    """
    if not (1 <= ces_score <= max_score):
        return {
            "success": False,
            "message": f"CES score must be between 1 and {max_score}"
        }

    metric_tool = CreateSatisfactionMetricTool()

    result = await metric_tool.execute(
        user_id=user_id,
        metric_type="ces",
        score=ces_score,
        max_score=max_score,
        interaction_type=interaction_type,
        reference_id=order_id,
        reference_type="order" if order_id else None
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to record CES score"
        }

    # Lower CES = better (less effort required)
    effort_level = "Very Easy" if ces_score <= 2 else \
                   "Easy" if ces_score <= 4 else \
                   "Moderate" if ces_score <= 5 else \
                   "Difficult"

    return {
        "success": True,
        "metric_id": result.data.get("metric_id"),
        "ces_score": ces_score,
        "max_score": max_score,
        "effort_level": effort_level,
        "message": f"Thank you! Your effort score: {ces_score}/{max_score} ({effort_level})"
    }


__all__ = [
    "record_nps_score",
    "record_csat_score",
    "record_ces_score"
]
