"""
Analytics Tools
===============
Tools for satisfaction metrics, trends, and analytics.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from langchain_core.tools import tool


@tool
async def get_satisfaction_metrics(
    user_id: Optional[str] = None,
    days: int = 30,
    metric_type: str = "nps"
) -> Dict[str, Any]:
    """
    Get customer satisfaction metrics and analytics.

    Retrieves aggregate satisfaction data including NPS scores, ratings, and trends.
    Calculates Net Promoter Score (NPS) = % Promoters - % Detractors.

    Args:
        user_id: Optional user ID to get metrics for specific customer
        days: Number of days to look back (default 30)
        metric_type: Type of metric to retrieve (nps, csat, ces, overall_experience)

    Returns:
        Dict with satisfaction metrics including NPS breakdown and score
    """
    from sqlalchemy import select, and_, func
    from app.core.database import db_manager
    from app.shared.models import SatisfactionMetrics

    try:
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        async with db_manager.get_session() as session:
            # Build query
            query = select(SatisfactionMetrics).where(
                and_(
                    SatisfactionMetrics.metric_type == metric_type,
                    SatisfactionMetrics.created_at >= start_date,
                    SatisfactionMetrics.created_at <= end_date
                )
            )

            # Filter by user if specified
            if user_id:
                query = query.where(SatisfactionMetrics.user_id == user_id)

            # Execute query
            result = await session.execute(query)
            metrics = result.scalars().all()

            if not metrics:
                return {
                    "success": True,
                    "total_responses": 0,
                    "message": f"No {metric_type.upper()} data found for the last {days} days",
                    "metrics": {}
                }

            # Calculate statistics
            total_responses = len(metrics)
            scores = [float(m.score) for m in metrics]
            average_score = sum(scores) / total_responses if total_responses > 0 else 0

            # Calculate NPS-specific metrics
            if metric_type == "nps":
                promoters = sum(1 for score in scores if score >= 9)
                passives = sum(1 for score in scores if 7 <= score < 9)
                detractors = sum(1 for score in scores if score < 7)

                # Calculate percentages
                promoter_percentage = (promoters / total_responses * 100) if total_responses > 0 else 0
                passive_percentage = (passives / total_responses * 100) if total_responses > 0 else 0
                detractor_percentage = (detractors / total_responses * 100) if total_responses > 0 else 0

                # Net Promoter Score = % Promoters - % Detractors
                nps_score = promoter_percentage - detractor_percentage

                # Interpret NPS score
                if nps_score >= 70:
                    nps_interpretation = "Excellent"
                elif nps_score >= 50:
                    nps_interpretation = "Great"
                elif nps_score >= 30:
                    nps_interpretation = "Good"
                elif nps_score >= 0:
                    nps_interpretation = "Needs Improvement"
                else:
                    nps_interpretation = "Critical"

                metrics_data = {
                    "nps_score": round(nps_score, 2),
                    "interpretation": nps_interpretation,
                    "total_responses": total_responses,
                    "average_score": round(average_score, 2),
                    "breakdown": {
                        "promoters": {
                            "count": promoters,
                            "percentage": round(promoter_percentage, 2)
                        },
                        "passives": {
                            "count": passives,
                            "percentage": round(passive_percentage, 2)
                        },
                        "detractors": {
                            "count": detractors,
                            "percentage": round(detractor_percentage, 2)
                        }
                    },
                    "time_period": {
                        "days": days,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                }

                message = (
                    f"NPS Score: {round(nps_score, 1)} ({nps_interpretation}) | "
                    f"{total_responses} responses | "
                    f"{promoters} Promoters ({round(promoter_percentage, 1)}%), "
                    f"{passives} Passives ({round(passive_percentage, 1)}%), "
                    f"{detractors} Detractors ({round(detractor_percentage, 1)}%)"
                )

            else:
                # For other metric types (CSAT, CES, etc.)
                metrics_data = {
                    "metric_type": metric_type.upper(),
                    "total_responses": total_responses,
                    "average_score": round(average_score, 2),
                    "min_score": round(min(scores), 2),
                    "max_score": round(max(scores), 2),
                    "time_period": {
                        "days": days,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    }
                }

                message = (
                    f"{metric_type.upper()} Average: {round(average_score, 2)} | "
                    f"{total_responses} responses over {days} days"
                )

            return {
                "success": True,
                "metrics": metrics_data,
                "message": message
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to retrieve satisfaction metrics: {str(e)}",
            "metrics": {}
        }


@tool
async def calculate_nps_breakdown(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Calculate detailed NPS breakdown with promoters, passives, detractors.

    Args:
        start_date: Start date (ISO format)
        end_date: End date (ISO format)
        days: Number of days to look back (default: 30)

    Returns:
        Dict with NPS breakdown:
        - nps_score: Overall NPS (% Promoters - % Detractors)
        - promoters: Count and percentage
        - passives: Count and percentage
        - detractors: Count and percentage
        - total_responses: Total count
        - interpretation: Text interpretation of score
    """
    metrics_result = await get_satisfaction_metrics(
        metric_type="nps",
        start_date=start_date,
        end_date=end_date,
        days=days
    )

    if not metrics_result.get("success"):
        return metrics_result

    # Extract NPS scores from metrics
    nps_data = metrics_result.get("nps_data", {})

    promoters = nps_data.get("promoters", 0)
    passives = nps_data.get("passives", 0)
    detractors = nps_data.get("detractors", 0)
    total = promoters + passives + detractors

    if total == 0:
        return {
            "success": True,
            "nps_score": 0,
            "promoters": 0,
            "passives": 0,
            "detractors": 0,
            "total_responses": 0,
            "message": "No NPS responses in this period"
        }

    # Calculate percentages
    promoter_pct = (promoters / total) * 100
    passive_pct = (passives / total) * 100
    detractor_pct = (detractors / total) * 100

    # Calculate NPS score
    nps_score = promoter_pct - detractor_pct

    # Interpret score
    if nps_score >= 70:
        interpretation = "Excellent"
    elif nps_score >= 50:
        interpretation = "Great"
    elif nps_score >= 30:
        interpretation = "Good"
    elif nps_score >= 0:
        interpretation = "Needs Improvement"
    else:
        interpretation = "Critical"

    return {
        "success": True,
        "nps_score": round(nps_score, 1),
        "interpretation": interpretation,
        "promoters": {
            "count": promoters,
            "percentage": round(promoter_pct, 1)
        },
        "passives": {
            "count": passives,
            "percentage": round(passive_pct, 1)
        },
        "detractors": {
            "count": detractors,
            "percentage": round(detractor_pct, 1)
        },
        "total_responses": total,
        "period_days": days
    }


@tool
async def get_complaint_trends(
    category: Optional[str] = None,
    days: int = 30
) -> Dict[str, Any]:
    """
    Get complaint trends and statistics.

    Args:
        category: Filter by category (optional)
        days: Number of days to analyze (default: 30)

    Returns:
        Dict with complaint trends:
        - total_complaints: Total count
        - by_category: Breakdown by category
        - by_status: Breakdown by status
        - by_priority: Breakdown by priority
        - resolution_rate: Percentage resolved
        - avg_resolution_time: Average time to resolve
    """
    # This would query the complaints table
    # Placeholder implementation - would be replaced with actual database query

    return {
        "success": True,
        "total_complaints": 0,
        "by_category": {},
        "by_status": {},
        "by_priority": {},
        "resolution_rate": 0,
        "avg_resolution_time_hours": 0,
        "period_days": days,
        "message": "Complaint trends analysis (implementation pending)"
    }


@tool
async def compare_satisfaction_periods(
    current_days: int = 30,
    previous_days: int = 30
) -> Dict[str, Any]:
    """
    Compare satisfaction metrics between two time periods.

    Args:
        current_days: Days for current period (default: 30)
        previous_days: Days for previous period (default: 30)

    Returns:
        Dict with comparison:
        - current_period: Metrics for current period
        - previous_period: Metrics for previous period
        - changes: Delta between periods
        - trends: Up/down/stable for each metric
    """
    # Get current period
    current_result = await get_satisfaction_metrics(days=current_days)

    # Get previous period
    current_start = datetime.now() - timedelta(days=current_days)
    previous_start = current_start - timedelta(days=previous_days)
    previous_end = current_start

    previous_result = await get_satisfaction_metrics(
        start_date=previous_start.isoformat(),
        end_date=previous_end.isoformat()
    )

    return {
        "success": True,
        "current_period": current_result,
        "previous_period": previous_result,
        "changes": {},  # Would calculate deltas
        "trends": {},   # Would determine up/down/stable
        "message": "Period comparison (detailed implementation pending)"
    }


__all__ = [
    "get_satisfaction_metrics",
    "calculate_nps_breakdown",
    "get_complaint_trends",
    "compare_satisfaction_periods"
]
