"""
Feedback Models
===============

Database models for feedback feature, organized as one-file-per-table.

Models (6 tables):
- Complaint: Customer complaints and issue tracking
- Rating: Customer ratings and feedback
- Feedback: General feedback collection
- CustomerFeedbackDetails: Detailed feedback information
- SatisfactionMetrics: Customer satisfaction metrics (NPS, CSAT, etc.)
- ComplaintResolutionTemplate: Templates for complaint resolution
"""

from app.features.feedback.models.complaint import Complaint
from app.features.feedback.models.rating import Rating
from app.features.feedback.models.feedback import Feedback
from app.features.feedback.models.customer_feedback_details import CustomerFeedbackDetails
from app.features.feedback.models.satisfaction_metrics import SatisfactionMetrics
from app.features.feedback.models.complaint_resolution_template import ComplaintResolutionTemplate

__all__ = [
    "Complaint",
    "Rating",
    "Feedback",
    "CustomerFeedbackDetails",
    "SatisfactionMetrics",
    "ComplaintResolutionTemplate",
]
