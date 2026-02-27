"""
Food Ordering Feature Cache
===========================

Feature-specific cache instance for food ordering operations.

Provides namespaced caching for:
- Menu data (categories, items)
- Cart data (session-based)
- Order data
- Inventory availability
"""

from app.core.cache import get_feature_cache

# Food ordering cache instance
# All cache keys will be prefixed with "food_ordering:"
food_ordering_cache = get_feature_cache("food_ordering")

# Convenience exports
__all__ = ["food_ordering_cache"]
