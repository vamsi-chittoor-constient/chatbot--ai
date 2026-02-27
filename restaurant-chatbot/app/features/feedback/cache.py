"""
Feedback Feature Cache
======================
Isolated cache instance for feedback feature.

Provides feature-scoped caching for:
- Complaint templates
- User complaint history
- NPS metrics
- Satisfaction trends
"""

from app.utils.cache import Cache

# Feature-scoped cache instance
feedback_cache = Cache(prefix="feedback")

__all__ = ["feedback_cache"]
