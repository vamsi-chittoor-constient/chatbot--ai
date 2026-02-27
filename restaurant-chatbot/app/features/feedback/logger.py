"""
Feedback Feature Logger
=======================
Isolated logger instance for feedback feature.

Provides structured logging with feature context for:
- Complaint submissions
- Feedback collection
- NPS surveys
- Analytics queries
"""

import structlog

# Feature-scoped logger
feedback_logger = structlog.get_logger("features.feedback")

__all__ = ["feedback_logger"]
