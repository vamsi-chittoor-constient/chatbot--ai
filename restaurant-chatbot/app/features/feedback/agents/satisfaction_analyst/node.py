"""
Satisfaction Analyst Agent
==========================
Handles satisfaction metrics and analytics reporting.

Responsibilities:
- Calculate NPS/CSAT/CES metrics
- Show trends over time
- Generate insights
"""

from typing import Dict, Any
import structlog

from app.features.feedback.state import FeedbackState
from app.features.feedback.tools.analytics_tools import (
    get_satisfaction_metrics,
    calculate_nps_breakdown,
    get_complaint_trends
)

logger = structlog.get_logger("agents.satisfaction_analyst")


async def satisfaction_analyst_agent(
    entities: Dict[str, Any],
    state: FeedbackState
) -> Dict[str, Any]:
    """
    Generate satisfaction metrics and analytics.

    Args:
        entities: Extracted entities (metric_type, time_period)
        state: Current feedback state

    Returns:
        ActionResult dict for Response Agent
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Satisfaction analyst executing",
        session_id=session_id,
        entities=entities
    )

    metric_type = entities.get("metric_type", "nps")  # nps, csat, ces, complaints
    days = entities.get("days", 30)

    # Route to appropriate analytics
    if metric_type == "nps":
        result = await calculate_nps_breakdown(days=days)
    elif metric_type == "complaints":
        result = await get_complaint_trends(days=days)
    else:
        result = await get_satisfaction_metrics(metric_type=metric_type, days=days)

    if not result.get("success"):
        return {
            "action": "analytics_failed",
            "success": False,
            "data": {"message": f"Failed to retrieve {metric_type} metrics"},
            "context": {}
        }

    logger.info(
        "Analytics retrieved",
        session_id=session_id,
        metric_type=metric_type
    )

    return {
        "action": "metrics_retrieved",
        "success": True,
        "data": {
            "metric_type": metric_type,
            "period_days": days,
            "metrics": result,
            "message": f"Here are your {metric_type.upper()} metrics for the last {days} days"
        },
        "context": {
            "metric_type": metric_type,
            "period_days": days
        }
    }


__all__ = ["satisfaction_analyst_agent"]
