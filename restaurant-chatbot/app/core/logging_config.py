"""
Feature-Aware Logging Configuration
===================================

Structured logging with feature tagging for better observability.

Features:
- Feature-specific log tagging
- Structured logging with context
- JSON output for production
- Component-level logging
"""

import logging
import structlog
from typing import Any, Dict, Optional
import sys

# Logging utilities now defined in this module (migrated from app.utils.logger)
import time
from functools import wraps


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get structlog logger instance for specific module.

    Args:
        name (str): Logger name (usually __name__)

    Returns:
        structlog.BoundLogger: Structlog logger instance
    """
    return structlog.get_logger(name)


def get_performance_logger():
    """
    Get performance logger (for backward compatibility).

    Returns:
        None: Structlog handles performance logging directly
    """
    return None


def log_async_performance(func):
    """
    Decorator to automatically log async function performance.

    Args:
        func: Async function to decorate

    Returns:
        Wrapped async function with performance logging
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        logger = get_logger(func.__module__)

        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                "Performance metric",
                metric_type="execution_time",
                function=func_name,
                execution_time_seconds=round(execution_time, 4),
                args_count=len(args) if args else 0,
                kwargs_count=len(kwargs) if kwargs else 0
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Async function {func_name} failed after {execution_time:.4f}s",
                function=func_name,
                execution_time_seconds=round(execution_time, 4),
                error=str(e),
                exc_info=True
            )
            raise

    return wrapper


def log_performance(func):
    """
    Decorator to automatically log function performance.

    Args:
        func: Function to decorate

    Returns:
        Wrapped function with performance logging
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        func_name = f"{func.__module__}.{func.__name__}"
        logger = get_logger(func.__module__)

        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            logger.info(
                "Performance metric",
                metric_type="execution_time",
                function=func_name,
                execution_time_seconds=round(execution_time, 4),
                args_count=len(args) if args else 0,
                kwargs_count=len(kwargs) if kwargs else 0
            )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Function {func_name} failed after {execution_time:.4f}s",
                function=func_name,
                execution_time_seconds=round(execution_time, 4),
                error=str(e),
                exc_info=True
            )
            raise

    return wrapper


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/restaurant_ai.log",
    console_output: bool = True,
    force_colors: Optional[bool] = None,
    json_logs: bool = False
):
    """
    Setup structured logging for the application.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (for backward compatibility, currently unused)
        console_output: Enable console output (for backward compatibility, currently unused)
        force_colors: Force colors on/off (for backward compatibility, currently unused)
        json_logs: Output logs as JSON (recommended for production)
    """
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if json_logs
            else structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper())
    )


class FeatureLogger:
    """
    Feature-aware structured logger with automatic context injection.

    Automatically tags all logs with feature and component information.
    """

    def __init__(self, feature_name: str, component: Optional[str] = None):
        """
        Initialize feature logger.

        Args:
            feature_name: Name of the feature (e.g., 'food_ordering', 'booking')
            component: Optional component name (e.g., 'cart_management', 'checkout')
        """
        self.feature_name = feature_name
        self.component = component
        self.logger = structlog.get_logger()

    def _add_context(self, **kwargs) -> Dict[str, Any]:
        """Add feature and component context to log"""
        context = {
            "feature": self.feature_name,
            **kwargs
        }
        if self.component:
            context["component"] = self.component
        return context

    def debug(self, message: str, **kwargs):
        """Log debug message with feature context"""
        self.logger.debug(message, **self._add_context(**kwargs))

    def info(self, message: str, **kwargs):
        """Log info message with feature context"""
        self.logger.info(message, **self._add_context(**kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message with feature context"""
        self.logger.warning(message, **self._add_context(**kwargs))

    def error(self, message: str, **kwargs):
        """Log error message with feature context"""
        self.logger.error(message, **self._add_context(**kwargs))

    def exception(self, message: str, **kwargs):
        """Log exception with traceback and feature context"""
        self.logger.exception(message, **self._add_context(**kwargs))

    def critical(self, message: str, **kwargs):
        """Log critical message with feature context"""
        self.logger.critical(message, **self._add_context(**kwargs))


def get_feature_logger(feature_name: str, component: Optional[str] = None) -> FeatureLogger:
    """
    Get feature-specific logger.

    Usage:
        from app.core.logging_config import get_feature_logger

        logger = get_feature_logger('food_ordering', 'cart_management')
        logger.info("Item added to cart", item_id="123", quantity=2)

        # Logs: {"feature": "food_ordering", "component": "cart_management",
        #        "message": "Item added to cart", "item_id": "123", "quantity": 2}
    """
    return FeatureLogger(feature_name, component)
