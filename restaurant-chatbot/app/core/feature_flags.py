"""
Feature Flags System
====================

Controls gradual rollout of new features with ZERO impact on existing functionality.

Design Principles:
- All features start DISABLED by default
- Enable via environment variables
- No code changes needed to enable/disable
- Instant rollback capability
- Zero performance impact when disabled

Usage:
    from app.core.feature_flags import Feature, FeatureFlags

    # Check if feature is enabled
    if FeatureFlags.is_enabled(Feature.PETPOOJA_ORDER_SYNC):
        await sync_order_to_petpooja(order)

    # Or use decorator
    @feature_flag(Feature.ADVANCED_TABLE_ASSIGNMENT)
    async def assign_best_table(...):
        # Only runs if feature enabled
        pass

Environment Variables:
    ENABLE_PETPOOJA_SYNC=true          # Enable PetPooja kitchen sync
    ENABLE_ADVANCED_TABLES=true        # Enable smart table assignment
    ENABLE_ORDER_TRACKING=true         # Enable order status tracking
    ENABLE_TABLE_COMBINATION=true      # Enable table combinations for large groups
    ENABLE_TABLE_FEATURES=true         # Enable table special features (window/garden)
    ENABLE_MIS_REPORTING=true          # Enable MIS reporting (future)
    ENABLE_STAFF_DASHBOARD=true        # Enable staff dashboard (future)
    ENABLE_COMPLAINTS_MODULE=true      # Enable complaints module (future)
"""

import os
from enum import Enum
from functools import wraps
from typing import Optional, Callable, Any
import structlog

logger = structlog.get_logger(__name__)


class Feature(Enum):
    """
    Feature flags enum

    Categories:
    - Food Ordering: Enhanced food ordering capabilities
    - Table Booking: Enhanced table booking capabilities
    - Future: Features planned for future activation
    """

    # ========================================================================
    # FOOD ORDERING FEATURES
    # ========================================================================

    PETPOOJA_ORDER_SYNC = "petpooja_order_sync"
    """
    Push orders to PetPooja kitchen system when created via chatbot

    Impact: When enabled, orders created through chatbot are automatically
    sent to PetPooja kitchen for preparation.

    Default: DISABLED
    Enable: export ENABLE_PETPOOJA_SYNC=true
    """

    ORDER_STATUS_TRACKING = "order_status_tracking"
    """
    Track order status through lifecycle (placed → preparing → ready → served)

    Impact: Enables real-time order status updates and notifications

    Default: DISABLED
    Enable: export ENABLE_ORDER_TRACKING=true
    """

    ADVANCED_ORDER_VALIDATION = "advanced_order_validation"
    """
    Advanced order validation (item availability, inventory checks)

    Impact: Additional validation before order placement

    Default: DISABLED
    Enable: export ENABLE_ADVANCED_VALIDATION=true
    """

    # ========================================================================
    # TABLE BOOKING FEATURES
    # ========================================================================

    ADVANCED_TABLE_ASSIGNMENT = "advanced_table_assignment"
    """
    Smart table assignment based on party size, preferences, and availability

    Impact: Uses intelligent algorithm to assign best table instead of
    simple first-available logic.

    Default: DISABLED
    Enable: export ENABLE_ADVANCED_TABLES=true
    """

    TABLE_COMBINATION = "table_combination"
    """
    Combine multiple tables for large groups

    Impact: Allows booking multiple adjacent tables for parties larger
    than single table capacity.

    Default: DISABLED
    Enable: export ENABLE_TABLE_COMBINATION=true
    """

    TABLE_SPECIAL_FEATURES = "table_special_features"
    """
    Support for table special features (window, garden, poolside, etc.)

    Impact: Allows customers to request specific table types

    Default: DISABLED
    Enable: export ENABLE_TABLE_FEATURES=true
    """

    # ========================================================================
    # FUTURE FEATURES (Always disabled for now)
    # ========================================================================

    MIS_REPORTING = "mis_reporting"
    """
    Management Information System reporting and analytics

    Impact: Provides order reports, booking analytics, revenue forecasting

    Default: DISABLED (not implemented yet)
    Enable: export ENABLE_MIS_REPORTING=true
    """

    STAFF_DASHBOARD = "staff_dashboard"
    """
    Staff management dashboard (FrontDesk, Manager, Housekeeping)

    Impact: Provides UI for restaurant staff operations

    Default: DISABLED (not implemented yet)
    Enable: export ENABLE_STAFF_DASHBOARD=true
    """

    COMPLAINTS_MODULE = "complaints_module"
    """
    Customer complaints and feedback management

    Impact: Enables complaint tracking and resolution workflow

    Default: DISABLED (not implemented yet)
    Enable: export ENABLE_COMPLAINTS_MODULE=true
    """


class FeatureFlags:
    """
    Feature flags manager

    Controls which features are active in the application.
    All features start DISABLED by default.
    """

    # Feature flag state (loaded from environment variables)
    _flags = {
        # Food Ordering - Default: DISABLED
        Feature.PETPOOJA_ORDER_SYNC: os.getenv("ENABLE_PETPOOJA_SYNC", "false").lower() == "true",
        Feature.ORDER_STATUS_TRACKING: os.getenv("ENABLE_ORDER_TRACKING", "false").lower() == "true",
        Feature.ADVANCED_ORDER_VALIDATION: os.getenv("ENABLE_ADVANCED_VALIDATION", "false").lower() == "true",

        # Table Booking - Default: DISABLED
        Feature.ADVANCED_TABLE_ASSIGNMENT: os.getenv("ENABLE_ADVANCED_TABLES", "false").lower() == "true",
        Feature.TABLE_COMBINATION: os.getenv("ENABLE_TABLE_COMBINATION", "false").lower() == "true",
        Feature.TABLE_SPECIAL_FEATURES: os.getenv("ENABLE_TABLE_FEATURES", "false").lower() == "true",

        # Future Features - ALWAYS DISABLED (not implemented yet)
        Feature.MIS_REPORTING: False,  # Not in env - always False
        Feature.STAFF_DASHBOARD: False,  # Not in env - always False
        Feature.COMPLAINTS_MODULE: False,  # Not in env - always False
    }

    @classmethod
    def is_enabled(cls, feature: Feature) -> bool:
        """
        Check if a feature is enabled

        Args:
            feature: Feature enum value

        Returns:
            True if feature is enabled, False otherwise

        Example:
            if FeatureFlags.is_enabled(Feature.PETPOOJA_ORDER_SYNC):
                await sync_order_to_petpooja(order)
        """
        enabled = cls._flags.get(feature, False)

        if enabled:
            logger.debug(
                "feature_flag_check",
                feature=feature.value,
                enabled=True
            )

        return enabled

    @classmethod
    def enable(cls, feature: Feature):
        """
        Enable a feature (runtime override, useful for testing)

        Args:
            feature: Feature to enable

        Example:
            FeatureFlags.enable(Feature.PETPOOJA_ORDER_SYNC)
        """
        cls._flags[feature] = True
        logger.info("feature_enabled", feature=feature.value)

    @classmethod
    def disable(cls, feature: Feature):
        """
        Disable a feature (runtime override, useful for testing)

        Args:
            feature: Feature to disable

        Example:
            FeatureFlags.disable(Feature.PETPOOJA_ORDER_SYNC)
        """
        cls._flags[feature] = False
        logger.info("feature_disabled", feature=feature.value)

    @classmethod
    def get_all_flags(cls) -> dict:
        """
        Get status of all feature flags

        Returns:
            Dictionary mapping feature names to enabled status

        Example:
            {
                "petpooja_order_sync": False,
                "advanced_table_assignment": False,
                ...
            }
        """
        return {
            feature.value: enabled
            for feature, enabled in cls._flags.items()
        }

    @classmethod
    def get_enabled_features(cls) -> list:
        """
        Get list of currently enabled features

        Returns:
            List of enabled feature names

        Example:
            ["petpooja_order_sync", "advanced_table_assignment"]
        """
        return [
            feature.value
            for feature, enabled in cls._flags.items()
            if enabled
        ]


def feature_flag(feature: Feature):
    """
    Decorator to conditionally execute function based on feature flag

    If feature is disabled, the function returns None without executing.
    If feature is enabled, the function executes normally.

    Args:
        feature: Feature flag to check

    Example:
        @feature_flag(Feature.PETPOOJA_ORDER_SYNC)
        async def sync_order_to_petpooja(order):
            # Only runs if PETPOOJA_ORDER_SYNC is enabled
            # Returns None if disabled
            await push_to_petpooja_api(order)

    Returns:
        Decorated function that checks feature flag before execution
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Optional[Any]:
            if not FeatureFlags.is_enabled(feature):
                # Feature disabled - skip execution
                logger.debug(
                    "feature_flag_skip",
                    feature=feature.value,
                    function=func.__name__,
                    reason="feature_disabled"
                )
                return None

            # Feature enabled - execute function
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Optional[Any]:
            if not FeatureFlags.is_enabled(feature):
                # Feature disabled - skip execution
                logger.debug(
                    "feature_flag_skip",
                    feature=feature.value,
                    function=func.__name__,
                    reason="feature_disabled"
                )
                return None

            # Feature enabled - execute function
            return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# LOGGING ON STARTUP
# ============================================================================

# Log feature flag status on module import (helps with debugging)
_enabled_features = FeatureFlags.get_enabled_features()

if _enabled_features:
    logger.info(
        "feature_flags_initialized",
        enabled_features=_enabled_features,
        total_enabled=len(_enabled_features)
    )
else:
    logger.info(
        "feature_flags_initialized",
        enabled_features=[],
        total_enabled=0,
        message="All features disabled (default state)"
    )


__all__ = [
    "Feature",
    "FeatureFlags",
    "feature_flag",
]
