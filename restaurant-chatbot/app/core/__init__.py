"""
Core Infrastructure Package
===========================

Centralized infrastructure services for all features.

Modules:
- database: Database connection pooling and session management
- redis: Redis connection pooling
- cache: Feature-aware caching service
- logging_config: Structured logging with feature tagging
- metrics: Prometheus metrics for monitoring
- errors: Feature-aware error handling
- config: Application configuration
"""

from app.core.database import db_manager, get_db_session
from app.core.redis import redis_manager, get_redis_client
from app.core.cache import CacheService, get_feature_cache
from app.core.logging_config import FeatureLogger, get_feature_logger, setup_logging
from app.core.errors import (
    FeatureError,
    FoodOrderingError,
    BookingError,
    FeedbackError,
    UserAuthError,
    UserProfileError,
    GeneralQueryError,
    ErrorCodes
)
from app.core.config import settings, get_settings

__all__ = [
    # Database
    "db_manager",
    "get_db_session",

    # Redis
    "redis_manager",
    "get_redis_client",

    # Cache
    "CacheService",
    "get_feature_cache",

    # Logging
    "FeatureLogger",
    "get_feature_logger",
    "setup_logging",

    # Errors
    "FeatureError",
    "FoodOrderingError",
    "BookingError",
    "FeedbackError",
    "UserAuthError",
    "UserProfileError",
    "GeneralQueryError",
    "ErrorCodes",

    # Config
    "settings",
    "get_settings",
]
