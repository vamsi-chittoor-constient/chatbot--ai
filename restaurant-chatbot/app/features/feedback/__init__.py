"""
Feedback Feature
================
Modern feedback/complaints feature with sub-agent architecture.

Features:
- Complaint submission and tracking
- Feedback and rating collection
- NPS/CSAT/CES surveys
- Satisfaction analytics

NOTE: LangGraph implementation removed. System now uses Sticky Crew orchestrator.
Only schemas, models, and tools remain for potential future use.

Sub-Agents (REMOVED - using Sticky Crew):
- complaint_creator: Create complaints
- complaint_tracker: Track complaint status
- feedback_collector: Collect ratings and feedback
- nps_surveyor: NPS survey collection
- satisfaction_analyst: Metrics and analytics
"""

# LangGraph imports removed - using Sticky Crew orchestrator instead
# from app.features.feedback.node import feedback_node
# from app.features.feedback.state import FeedbackState, FeedbackProgress
# from app.features.feedback.graph import create_feedback_graph

__all__ = [
    # LangGraph components removed - using Sticky Crew
    # "feedback_node",
    # "FeedbackState",
    # "FeedbackProgress",
    # "create_feedback_graph"
]
