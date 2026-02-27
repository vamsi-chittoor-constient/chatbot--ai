"""
General Queries Logger
=====================
Centralized structured logging for general_queries feature.
"""

import structlog

# Create feature-specific logger
logger = structlog.get_logger("general_queries")


def get_logger(component: str) -> structlog.BoundLogger:
    """
    Get a logger for a specific component.

    Args:
        component: Component name (e.g., "knowledge_agent", "restaurant_info_agent")

    Returns:
        Bound logger with component context
    """
    return logger.bind(component=component)


__all__ = ["logger", "get_logger"]
