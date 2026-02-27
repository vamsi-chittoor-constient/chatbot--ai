"""
Food Ordering Feature Logger
============================

Feature-specific logger instance for food ordering operations.

All logs will be tagged with feature="food_ordering"
"""

from app.core.logging_config import get_feature_logger

# Food ordering logger instance
# All logs will include {"feature": "food_ordering"}
food_ordering_logger = get_feature_logger("food_ordering")

# Convenience exports
__all__ = ["food_ordering_logger"]
