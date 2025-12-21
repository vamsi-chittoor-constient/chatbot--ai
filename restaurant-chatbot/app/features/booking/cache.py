"""
Booking Feature Cache
====================

Feature-specific cache instance for booking operations.

Provides namespaced caching for:
- Availability data
- Booking data
- Table information
"""

from app.core.cache import get_feature_cache

# Booking cache instance
# All cache keys will be prefixed with "booking:"
booking_cache = get_feature_cache("booking")

# Convenience exports
__all__ = ["booking_cache"]
