"""
Booking Feature Logger
=====================

Feature-specific logger instance for booking operations.

All logs will be tagged with feature="booking"
"""

from app.core.logging_config import get_feature_logger

# Booking logger instance
# All logs will include {"feature": "booking"}
booking_logger = get_feature_logger("booking")

# Convenience exports
__all__ = ["booking_logger"]
