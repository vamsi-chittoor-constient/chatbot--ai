"""
User Management Cache
====================
Centralized caching for authentication and identity data.
"""

from typing import Optional, Any
import json
from datetime import timedelta

from app.core.cache import CacheService as CacheManager

# Initialize cache manager
cache_manager = CacheManager()


async def get_from_cache(key: str) -> Optional[Any]:
    """
    Get value from cache.

    Args:
        key: Cache key

    Returns:
        Cached value or None if not found
    """
    cached = await cache_manager.get(key)
    if cached:
        try:
            return json.loads(cached)
        except (json.JSONDecodeError, TypeError):
            return cached
    return None


async def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    """
    Set value in cache with TTL.

    Args:
        key: Cache key
        value: Value to cache
        ttl: Time-to-live in seconds (default 5 minutes)
    """
    try:
        serialized = json.dumps(value) if not isinstance(value, str) else value
        await cache_manager.set(key, serialized, ttl=timedelta(seconds=ttl))
    except (TypeError, ValueError):
        # Fallback for non-serializable objects
        await cache_manager.set(key, str(value), ttl=timedelta(seconds=ttl))


async def delete_from_cache(key: str) -> None:
    """
    Delete value from cache.

    Args:
        key: Cache key
    """
    await cache_manager.delete(key)


async def clear_user_cache(user_id: str) -> None:
    """
    Clear all cached data for a specific user.

    Args:
        user_id: User identifier
    """
    keys_to_clear = [
        f"user:{user_id}",
        f"sessions:{user_id}",
        f"identity:{user_id}",
        f"auth_status:{user_id}"
    ]
    for key in keys_to_clear:
        await delete_from_cache(key)


__all__ = [
    "get_from_cache",
    "set_cache",
    "delete_from_cache",
    "clear_user_cache"
]
