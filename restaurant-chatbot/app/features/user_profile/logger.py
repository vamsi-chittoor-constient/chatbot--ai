"""
User Profile Logger
==================
Centralized structured logging for user_profile feature.
"""

import structlog

# Create feature-specific logger
logger = structlog.get_logger("user_profile")


def get_logger(component: str) -> structlog.BoundLogger:
    """
    Get a logger for a specific component.

    Args:
        component: Component name (e.g., "preference_manager", "favorites_manager")

    Returns:
        Bound logger with component context
    """
    return logger.bind(component=component)


__all__ = ["logger", "get_logger"]
