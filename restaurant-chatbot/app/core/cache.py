"""
Feature-Aware Cache Service
===========================

Namespaced caching service to prevent key collisions between features.

Features:
- Automatic key namespacing by feature
- JSON serialization/deserialization
- Pattern-based invalidation
- TTL management
"""

import json
from typing import Any, Optional, List
import redis.asyncio as redis

from app.core.redis import get_redis_client
from app.core.logging_config import get_logger


class CacheService:
    """
    Feature-aware Redis cache service with automatic key namespacing.

    Each feature gets its own namespace to prevent key collisions.

    Key Format: {feature}:{entity}:{identifier}
    Examples:
        - food_ordering:menu:categories:all
        - food_ordering:cart:session_abc123
        - booking:availability:2024-01-15
    """

    def __init__(self, feature_name: str):
        """
        Initialize cache service for a specific feature.

        Args:
            feature_name: Name of the feature (e.g., 'food_ordering', 'booking')
        """
        self.feature_name = feature_name
        self.redis_client: Optional[redis.Redis] = None
        self._logger = get_logger(f"{__name__}.{feature_name}")

    def _get_client(self) -> redis.Redis:
        """Get Redis client lazily"""
        if not self.redis_client:
            self.redis_client = get_redis_client()
        return self.redis_client

    def _build_key(self, entity: str, identifier: str) -> str:
        """
        Build namespaced cache key.

        Args:
            entity: Entity type (e.g., 'menu', 'cart', 'booking')
            identifier: Unique identifier (e.g., 'session_id', 'item_id')

        Returns:
            str: Namespaced key
        """
        return f"{self.feature_name}:{entity}:{identifier}"

    async def get(self, entity: str, identifier: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            entity: Entity type
            identifier: Unique identifier

        Returns:
            Cached value (deserialized from JSON) or None if not found
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            value = await client.get(key)
            if value:
                # Deserialize JSON
                return json.loads(value)

            return None

        except Exception as e:
            self._logger.error(
                f"Cache get error for {entity}:{identifier}",
                error=str(e)
            )
            return None

    async def set(
        self,
        entity: str,
        identifier: str,
        value: Any,
        ttl: int = 3600
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            entity: Entity type
            identifier: Unique identifier
            value: Value to cache (will be JSON serialized)
            ttl: Time-to-live in seconds (default: 1 hour)

        Returns:
            bool: True if successful
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            # Serialize to JSON
            serialized = json.dumps(value, default=str)

            # Set with TTL
            await client.setex(key, ttl, serialized)

            self._logger.debug(
                f"Cache set: {entity}:{identifier}",
                ttl=ttl
            )
            return True

        except Exception as e:
            self._logger.error(
                f"Cache set error for {entity}:{identifier}",
                error=str(e)
            )
            return False

    async def delete(self, entity: str, identifier: str) -> bool:
        """
        Delete value from cache.

        Args:
            entity: Entity type
            identifier: Unique identifier

        Returns:
            bool: True if key existed and was deleted
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            result = await client.delete(key)

            self._logger.debug(f"Cache delete: {entity}:{identifier}")
            return result > 0

        except Exception as e:
            self._logger.error(
                f"Cache delete error for {entity}:{identifier}",
                error=str(e)
            )
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., 'menu:*' to clear all menu cache)

        Returns:
            int: Number of keys deleted
        """
        try:
            client = self._get_client()
            full_pattern = f"{self.feature_name}:{pattern}"

            # Find matching keys
            keys = []
            async for key in client.scan_iter(match=full_pattern):
                keys.append(key)

            if not keys:
                return 0

            # Delete all matching keys
            deleted = await client.delete(*keys)

            self._logger.info(
                f"Cache invalidated pattern: {pattern}",
                deleted_count=deleted
            )
            return deleted

        except Exception as e:
            self._logger.error(
                f"Cache invalidate pattern error for {pattern}",
                error=str(e)
            )
            return 0

    async def exists(self, entity: str, identifier: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            entity: Entity type
            identifier: Unique identifier

        Returns:
            bool: True if key exists
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            return await client.exists(key) > 0

        except Exception as e:
            self._logger.error(
                f"Cache exists error for {entity}:{identifier}",
                error=str(e)
            )
            return False

    async def get_ttl(self, entity: str, identifier: str) -> Optional[int]:
        """
        Get remaining TTL for a key.

        Args:
            entity: Entity type
            identifier: Unique identifier

        Returns:
            int: Remaining TTL in seconds, or None if key doesn't exist
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            ttl = await client.ttl(key)

            # TTL returns -2 if key doesn't exist, -1 if no expiry
            if ttl == -2:
                return None
            elif ttl == -1:
                return None  # Key exists but has no expiry
            else:
                return ttl

        except Exception as e:
            self._logger.error(
                f"Cache get_ttl error for {entity}:{identifier}",
                error=str(e)
            )
            return None

    async def increment(
        self,
        entity: str,
        identifier: str,
        amount: int = 1
    ) -> Optional[int]:
        """
        Increment a counter in cache.

        Args:
            entity: Entity type
            identifier: Unique identifier
            amount: Amount to increment by

        Returns:
            int: New value after increment, or None on error
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            new_value = await client.incrby(key, amount)
            return new_value

        except Exception as e:
            self._logger.error(
                f"Cache increment error for {entity}:{identifier}",
                error=str(e)
            )
            return None

    async def decrement(
        self,
        entity: str,
        identifier: str,
        amount: int = 1
    ) -> Optional[int]:
        """
        Decrement a counter in cache.

        Args:
            entity: Entity type
            identifier: Unique identifier
            amount: Amount to decrement by

        Returns:
            int: New value after decrement, or None on error
        """
        try:
            client = self._get_client()
            key = self._build_key(entity, identifier)

            new_value = await client.decrby(key, amount)
            return new_value

        except Exception as e:
            self._logger.error(
                f"Cache decrement error for {entity}:{identifier}",
                error=str(e)
            )
            return None


# Feature-specific cache instances
def get_feature_cache(feature_name: str) -> CacheService:
    """
    Get cache service for a specific feature.

    Usage:
        from app.core.cache import get_feature_cache

        cache = get_feature_cache('food_ordering')
        await cache.set('menu', 'categories', data, ttl=3600)
    """
    return CacheService(feature_name)
