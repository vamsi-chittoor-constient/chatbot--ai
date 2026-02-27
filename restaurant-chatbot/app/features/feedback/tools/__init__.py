"""
Feedback Tools
==============
Organized tools for feedback feature.

Tool Organization:
- complaint_tools: Complaint CRUD operations
- feedback_tools: Feedback and rating collection
- nps_tools: NPS/CSAT/CES survey tools
- analytics_tools: Metrics and analytics
"""

from app.features.feedback.tools.complaint_tools import (
    create_complaint,
    update_complaint_status,
    get_complaint_details,
    get_user_complaints,
    escalate_complaint
)

from app.features.feedback.tools.feedback_tools import (
    create_feedback,
    create_detailed_rating
)

from app.features.feedback.tools.nps_tools import (
    record_nps_score,
    record_csat_score,
    record_ces_score
)

from app.features.feedback.tools.analytics_tools import (
    get_satisfaction_metrics,
    calculate_nps_breakdown,
    get_complaint_trends,
    compare_satisfaction_periods
)

__all__ = [
    # Complaint tools
    "create_complaint",
    "update_complaint_status",
    "get_complaint_details",
    "get_user_complaints",
    "escalate_complaint",

    # Feedback tools
    "create_feedback",
    "create_detailed_rating",

    # NPS tools
    "record_nps_score",
    "record_csat_score",
    "record_ces_score",

    # Analytics tools
    "get_satisfaction_metrics",
    "calculate_nps_breakdown",
    "get_complaint_trends",
    "compare_satisfaction_periods"
]
