"""
Restaurant Cache Service
========================
Consolidated restaurant configuration caching service combining:
- Multi-tenant caching by API key and restaurant ID
- Fast single-restaurant lookups for simple use cases
- Redis-backed with 24-hour TTL
- Database fallback on cache miss
- Manual refresh on config updates

Features:
- Load all restaurant configs on startup
- Get restaurant by API key (multi-tenant support)
- Get restaurant by ID
- Simple single-restaurant caching for backward compatibility
- 24-hour TTL with automatic refresh
- Fallback to database on cache miss
"""

import json
import structlog
from typing import Dict, Any, Optional
from datetime import timedelta

from app.services.cache_service import ResponseCacheService
from app.core.database import get_db_session
from app.shared.models import Restaurant
from app.tools.database.restaurant_tools import GetRestaurantTool
from sqlalchemy import select

logger = structlog.get_logger(__name__)

# ===== Multi-Tenant Cache Class =====

class RestaurantCache:
    """
    Manages restaurant configuration in Redis cache for multi-tenant scenarios.

    Cache Strategy:
    - Key format: restaurant:{api_key} or restaurant_id:{id}
    - Value: JSON with all restaurant data
    - TTL: 24 hours (auto-refresh daily)
    - Fallback: DB query on cache miss + populate cache

    Use Cases:
    - Multi-tenant applications where each request has an API key
    - Looking up restaurants by ID or API key
    - Automatic cache population on miss
    """

    def __init__(self, cache_service: Optional[ResponseCacheService] = None):
        """Initialize with cache service"""
        self.cache_service = cache_service or ResponseCacheService()
        self.cache_ttl = timedelta(hours=24)  # 24-hour TTL
        self.key_prefix = "restaurant:"
        self.id_key_prefix = "restaurant_id:"

    async def load_all_restaurants(self) -> Dict[str, Any]:
        """
        Load all restaurant configurations into Redis cache.
        Called on application startup.

        Returns:
            Dict with load statistics
        """
        logger.info("restaurant_config_cache_load_started")

        try:
            async with get_db_session() as session:
                # Query all restaurant configs
                query = select(Restaurant)
                result = await session.execute(query)
                restaurants = result.scalars().all()

                loaded_count = 0
                failed_count = 0

                for restaurant in restaurants:
                    try:
                        # Build cache data
                        cache_data = {
                            "restaurant_id": str(restaurant.id),
                            "name": restaurant.name,
                            "description": restaurant.description,
                            "address": restaurant.address,
                            "phone": restaurant.phone,
                            "email": restaurant.email,
                            "settings": restaurant.settings or {},
                            "opening_time": restaurant.opening_time.isoformat() if restaurant.opening_time else None,
                            "closing_time": restaurant.closing_time.isoformat() if restaurant.closing_time else None,
                            "is_open": restaurant.is_open,
                            "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
                            "updated_at": restaurant.updated_at.isoformat() if restaurant.updated_at else None
                        }

                        # Store in Redis with 24-hour TTL (cache by restaurant ID)
                        id_cache_key = f"{self.id_key_prefix}{restaurant.id}"
                        await self.cache_service.set(
                            key=id_cache_key,
                            value=json.dumps(cache_data),
                            ttl=self.cache_ttl
                        )

                        loaded_count += 1

                        logger.info(
                            "restaurant_config_cached",
                            restaurant_id=restaurant.id,
                            restaurant_name=restaurant.name
                        )

                    except Exception as e:
                        failed_count += 1
                        logger.error(
                            "restaurant_config_cache_failed",
                            restaurant_id=restaurant.id,
                            error=str(e)
                        )

                logger.info(
                    "restaurant_config_cache_load_completed",
                    total_restaurants=len(restaurants),
                    loaded=loaded_count,
                    failed=failed_count
                )

                return {
                    "success": True,
                    "total_restaurants": len(restaurants),
                    "loaded": loaded_count,
                    "failed": failed_count
                }

        except Exception as e:
            logger.error("restaurant_config_cache_load_error", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "loaded": 0
            }

    async def get_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: API key authentication removed from schema.
        Use get_by_id() instead.

        The api_key field was removed in migration 13. Restaurant auth is now
        handled differently (single restaurant, no multi-tenant api_key auth).
        """
        logger.warning(
            "get_by_api_key_deprecated",
            message="API key authentication is deprecated. Use get_by_id() instead."
        )
        raise NotImplementedError(
            "API key authentication removed. Restaurant.api_key field no longer exists. "
            "Use get_by_id() instead."
        )

    async def get_by_id(self, restaurant_id: str) -> Optional[Dict[str, Any]]:
        """
        Get restaurant configuration by restaurant ID.

        Flow:
        1. Check Redis cache
        2. If cache miss, query database
        3. Populate cache for next request
        4. Return restaurant data

        Args:
            restaurant_id: Restaurant ID

        Returns:
            Restaurant configuration dict or None if not found
        """
        cache_key = f"{self.id_key_prefix}{restaurant_id}"

        try:
            # Try to get from cache first
            cached_data = await self.cache_service.get(cache_key)

            if cached_data:
                logger.debug(
                    "restaurant_config_cache_hit_by_id",
                    restaurant_id=restaurant_id
                )
                return json.loads(cached_data)

            # Cache miss - query database
            logger.info(
                "restaurant_config_cache_miss_by_id",
                restaurant_id=restaurant_id
            )

            async with get_db_session() as session:
                query = select(Restaurant).where(Restaurant.id == restaurant_id)
                result = await session.execute(query)
                restaurant = result.scalar_one_or_none()

                if not restaurant:
                    logger.warning(
                        "restaurant_config_not_found_by_id",
                        restaurant_id=restaurant_id
                    )
                    return None

                # Build cache data
                cache_data = {
                    "restaurant_id": str(restaurant.id),
                    "name": restaurant.name,
                    "description": restaurant.description,
                    "address": restaurant.address,
                    "phone": restaurant.phone,
                    "email": restaurant.email,
                    "settings": restaurant.settings or {},
                    "opening_time": restaurant.opening_time.isoformat() if restaurant.opening_time else None,
                    "closing_time": restaurant.closing_time.isoformat() if restaurant.closing_time else None,
                    "is_open": restaurant.is_open,
                    "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
                    "updated_at": restaurant.updated_at.isoformat() if restaurant.updated_at else None
                }

                # Populate cache for next request (cache by ID)
                await self.cache_service.set(
                    key=cache_key,
                    value=json.dumps(cache_data),
                    ttl=self.cache_ttl
                )

                logger.info(
                    "restaurant_config_cached_from_db_by_id",
                    restaurant_id=restaurant.id,
                    restaurant_name=restaurant.name
                )

                return cache_data

        except Exception as e:
            logger.error(
                "restaurant_config_fetch_error_by_id",
                restaurant_id=restaurant_id,
                error=str(e)
            )
            return None

    async def refresh_restaurant(self, restaurant_id: str) -> bool:
        """
        Manually refresh a specific restaurant's cache.
        Called when restaurant config is updated.

        Args:
            restaurant_id: Restaurant ID

        Returns:
            True if successful, False otherwise
        """
        try:
            async with get_db_session() as session:
                query = select(Restaurant).where(Restaurant.id == restaurant_id)
                result = await session.execute(query)
                restaurant = result.scalar_one_or_none()

                if not restaurant:
                    logger.warning("restaurant_config_refresh_not_found", restaurant_id=restaurant_id)
                    return False

                # Build cache data
                cache_data = {
                    "restaurant_id": str(restaurant.id),
                    "name": restaurant.name,
                    "description": restaurant.description,
                    "address": restaurant.address,
                    "phone": restaurant.phone,
                    "email": restaurant.email,
                    "settings": restaurant.settings or {},
                    "opening_time": restaurant.opening_time.isoformat() if restaurant.opening_time else None,
                    "closing_time": restaurant.closing_time.isoformat() if restaurant.closing_time else None,
                    "is_open": restaurant.is_open,
                    "created_at": restaurant.created_at.isoformat() if restaurant.created_at else None,
                    "updated_at": restaurant.updated_at.isoformat() if restaurant.updated_at else None
                }

                # Update cache by ID
                id_cache_key = f"{self.id_key_prefix}{restaurant.id}"
                await self.cache_service.set(
                    key=id_cache_key,
                    value=json.dumps(cache_data),
                    ttl=self.cache_ttl
                )

                logger.info(
                    "restaurant_config_refreshed",
                    restaurant_id=restaurant.id,
                    restaurant_name=restaurant.name
                )

                return True

        except Exception as e:
            logger.error("restaurant_config_refresh_error", restaurant_id=restaurant_id, error=str(e))
            return False

    async def invalidate_restaurant(self, restaurant_id: str) -> bool:
        """
        Remove restaurant from cache.

        Args:
            restaurant_id: Restaurant ID

        Returns:
            True if successful
        """
        try:
            cache_key = f"{self.id_key_prefix}{restaurant_id}"
            await self.cache_service.delete(cache_key)

            logger.info("restaurant_config_invalidated", restaurant_id=restaurant_id)
            return True

        except Exception as e:
            logger.error("restaurant_config_invalidation_error", restaurant_id=restaurant_id, error=str(e))
            return False


# ===== Simple Function-Based Interface (Backward Compatibility) =====
# These functions provide a simple interface for single-restaurant scenarios
# They use RedisService directly for simpler use cases

from app.services.redis_service import get_redis_service

# Redis keys for simple single-restaurant caching
RESTAURANT_CONFIG_KEY = "cache:restaurant:config"
RESTAURANT_PHONE_KEY = "cache:restaurant:phone"

# Cache TTL - 24 hours (restaurant info rarely changes)
CACHE_TTL = 86400


async def load_restaurant_config_to_redis() -> bool:
    """
    Load restaurant configuration from database into Redis cache.

    Simple interface for single-restaurant applications.
    For multi-tenant, use RestaurantCache.load_all_restaurants() instead.

    This should be called on application startup to pre-populate
    the cache with restaurant information.

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info("Loading restaurant config into Redis cache...")

        # Fetch restaurant config from database
        restaurant_tool = GetRestaurantTool()
        result = await restaurant_tool.execute()

        if result.status.value != "success" or not result.data:
            logger.error("Failed to fetch restaurant config from database")
            return False

        restaurant_data = result.data
        redis = get_redis_service()

        # Cache full restaurant config
        success = await redis.set(
            RESTAURANT_CONFIG_KEY,
            restaurant_data,
            ttl=CACHE_TTL
        )

        if not success:
            logger.error("Failed to cache restaurant config in Redis")
            return False

        # Cache restaurant phone separately for quick access
        restaurant_phone = restaurant_data.get("phone")
        if restaurant_phone:
            phone_success = await redis.set(
                RESTAURANT_PHONE_KEY,
                restaurant_phone,
                ttl=CACHE_TTL
            )

            if phone_success:
                logger.info(
                    "Restaurant config loaded into Redis",
                    restaurant_name=restaurant_data.get("name"),
                    has_phone=bool(restaurant_phone),
                    cache_ttl_seconds=CACHE_TTL
                )
            else:
                logger.warning("Failed to cache restaurant phone separately")
        else:
            logger.warning("No restaurant phone found in database")

        return True

    except Exception as e:
        logger.error(
            "Failed to load restaurant config to Redis",
            error=str(e),
            exc_info=True
        )
        return False


async def get_cached_restaurant_config() -> Optional[Dict[str, Any]]:
    """
    Get cached restaurant configuration from Redis.

    Simple interface for single-restaurant applications.
    For multi-tenant, use RestaurantCache.get_by_api_key() instead.

    Returns:
        Dict with restaurant config or None if not cached
    """
    try:
        redis = get_redis_service()
        config = await redis.get(RESTAURANT_CONFIG_KEY)

        if config:
            logger.debug("Restaurant config retrieved from Redis cache")
            return config
        else:
            logger.warning("Restaurant config not found in Redis cache")
            return None

    except Exception as e:
        logger.error(
            "Failed to get restaurant config from Redis",
            error=str(e)
        )
        return None


async def get_cached_restaurant_phone() -> Optional[str]:
    """
    Get cached restaurant phone from Redis.

    This is a fast lookup optimized for phone validation checks.

    Returns:
        Restaurant phone number or None if not cached
    """
    try:
        redis = get_redis_service()
        phone = await redis.get(RESTAURANT_PHONE_KEY)

        if phone:
            logger.debug("Restaurant phone retrieved from Redis cache", phone=phone)
            return str(phone)
        else:
            logger.warning("Restaurant phone not found in Redis cache")
            return None

    except Exception as e:
        logger.error(
            "Failed to get restaurant phone from Redis",
            error=str(e)
        )
        return None


async def refresh_restaurant_cache() -> bool:
    """
    Manually refresh restaurant cache from database.

    Useful when restaurant information is updated.

    Returns:
        bool: True if refresh successful
    """
    logger.info("Manually refreshing restaurant cache...")
    return await load_restaurant_config_to_redis()


async def clear_restaurant_cache():
    """
    Clear restaurant cache from Redis.

    Useful for testing or when forcing a reload.
    """
    try:
        redis = get_redis_service()
        deleted = await redis.delete(RESTAURANT_CONFIG_KEY, RESTAURANT_PHONE_KEY)

        logger.info(
            "Restaurant cache cleared",
            keys_deleted=deleted
        )

    except Exception as e:
        logger.error(
            "Failed to clear restaurant cache",
            error=str(e)
        )


# ===== Global Singleton for Multi-Tenant Cache =====

_restaurant_config_cache: Optional[RestaurantCache] = None


def get_restaurant_config_cache() -> RestaurantCache:
    """Get or create restaurant config cache singleton"""
    global _restaurant_config_cache
    if _restaurant_config_cache is None:
        _restaurant_config_cache = RestaurantCache()
    return _restaurant_config_cache


# ===== Convenience Aliases =====
# Provides backward compatibility with old import names

async def get_restaurant_by_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get restaurant by API key"""
    cache = get_restaurant_config_cache()
    return await cache.get_by_api_key(api_key)


async def get_restaurant_by_id(restaurant_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get restaurant by ID"""
    cache = get_restaurant_config_cache()
    return await cache.get_by_id(restaurant_id)
