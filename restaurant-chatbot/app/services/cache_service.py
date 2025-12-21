"""
Response Cache Service
=====================
Redis-based caching for common LLM responses to reduce API calls.

Caching Strategy:
- Menu queries: 1 hour TTL
- Restaurant info: 24 hours TTL
- FAQ responses: 24 hours TTL
- Business hours: 24 hours TTL
- Default: 30 minutes TTL
"""

import os
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
import structlog

from app.core.redis import get_redis_client

logger = structlog.get_logger(__name__)


class ResponseCacheService:
    """
    Manages response caching using Redis.

    Features:
    - Automatic cache key generation from query
    - TTL-based expiration
    - Categorized caching (menu, restaurant_info, faq, etc.)
    - Cache hit/miss metrics
    """

    def __init__(self):
        """Initialize Redis connection and cache configuration"""
        self.enabled = os.getenv("ENABLE_RESPONSE_CACHING", "true").lower() == "true"

        if not self.enabled:
            logger.info("response_caching_disabled")
            self.redis_client = None
            return

        # Use shared Redis connection pool
        try:
            self.redis_client = get_redis_client()
        except RuntimeError:
            logger.warning("response_cache_redis_not_initialized")
            self.redis_client = None
            self.enabled = False
            return

        # TTL configuration (in seconds)
        self.ttl_config = {
            "menu": int(os.getenv("CACHE_TTL_MENU", "3600")),              # 1 hour
            "restaurant_info": int(os.getenv("CACHE_TTL_RESTAURANT_INFO", "86400")),  # 24 hours
            "faq": int(os.getenv("CACHE_TTL_FAQ", "86400")),               # 24 hours
            "business_hours": int(os.getenv("CACHE_TTL_BUSINESS_HOURS", "86400")),   # 24 hours
            "default": int(os.getenv("CACHE_TTL_DEFAULT", "1800"))         # 30 minutes
        }

        # Metrics
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(
            "response_cache_initialized",
            enabled=self.enabled,
            ttl_config=self.ttl_config,
            using_shared_pool=True
        )

    def _generate_cache_key(
        self,
        query: str,
        category: str = "default",
        user_id: Optional[str] = None
    ) -> str:
        """
        Generate a unique cache key from query and context.

        Args:
            query: The user query or agent input
            category: Cache category (menu, faq, etc.)
            user_id: Optional user ID for personalized caching

        Returns:
            Cache key string
        """
        # Normalize query (lowercase, strip whitespace)
        normalized_query = query.lower().strip()

        # Create hash of query for consistent key
        query_hash = hashlib.md5(normalized_query.encode()).hexdigest()[:12]

        # Build cache key
        if user_id:
            cache_key = f"cache:{category}:{user_id}:{query_hash}"
        else:
            cache_key = f"cache:{category}:global:{query_hash}"

        return cache_key

    def _detect_category(self, query: str, intent: Optional[str] = None) -> str:
        """
        Detect cache category from query or intent.

        Args:
            query: The user query
            intent: Optional detected intent

        Returns:
            Category string (menu, restaurant_info, faq, etc.)
        """
        query_lower = query.lower()

        # Menu-related queries
        menu_keywords = ["menu", "food", "dish", "items", "appetizer", "dessert", "drink", "beverage"]
        if any(keyword in query_lower for keyword in menu_keywords):
            return "menu"

        # Restaurant info queries
        info_keywords = ["restaurant", "address", "location", "phone", "email", "contact"]
        if any(keyword in query_lower for keyword in info_keywords):
            return "restaurant_info"

        # Business hours queries
        hours_keywords = ["hours", "open", "close", "timing", "schedule"]
        if any(keyword in query_lower for keyword in hours_keywords):
            return "business_hours"

        # FAQ queries
        faq_keywords = ["policy", "rule", "allowed", "dress code", "parking", "reservation"]
        if any(keyword in query_lower for keyword in faq_keywords):
            return "faq"

        # Use intent if provided
        if intent:
            if intent in ["menu_inquiry", "view_menu"]:
                return "menu"
            elif intent in ["restaurant_info", "contact_info"]:
                return "restaurant_info"
            elif intent in ["business_hours"]:
                return "business_hours"
            elif intent in ["faq", "policies"]:
                return "faq"

        return "default"

    async def get_cached_response(
        self,
        query: str,
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        intent: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.

        Args:
            query: The user query
            category: Optional category override
            user_id: Optional user ID
            intent: Optional detected intent

        Returns:
            Cached response dict or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            # Detect category if not provided
            if category is None:
                category = self._detect_category(query, intent)

            # Generate cache key
            cache_key = self._generate_cache_key(query, category, user_id)

            # Try to get from cache
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                self.cache_hits += 1
                response = json.loads(cached_data)

                logger.info(
                    "cache_hit",
                    category=category,
                    cache_key=cache_key,
                    query_preview=query[:50],
                    total_hits=self.cache_hits
                )

                return response
            else:
                self.cache_misses += 1

                logger.debug(
                    "cache_miss",
                    category=category,
                    cache_key=cache_key,
                    query_preview=query[:50],
                    total_misses=self.cache_misses
                )

                return None

        except Exception as e:
            logger.error(
                "cache_get_error",
                error=str(e),
                error_type=type(e).__name__
            )
            return None

    async def set_cached_response(
        self,
        query: str,
        response: Dict[str, Any],
        category: Optional[str] = None,
        user_id: Optional[str] = None,
        intent: Optional[str] = None,
        ttl_override: Optional[int] = None
    ):
        """
        Cache a response.

        Args:
            query: The user query
            response: The response to cache
            category: Optional category override
            user_id: Optional user ID
            intent: Optional detected intent
            ttl_override: Optional TTL override (seconds)
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            # Detect category if not provided
            if category is None:
                category = self._detect_category(query, intent)

            # Generate cache key
            cache_key = self._generate_cache_key(query, category, user_id)

            # Get TTL
            ttl = ttl_override if ttl_override else self.ttl_config.get(category, self.ttl_config["default"])

            # Serialize response
            cached_data = json.dumps(response)

            # Set in cache with TTL
            await self.redis_client.setex(cache_key, ttl, cached_data)

            logger.info(
                "cache_set",
                category=category,
                cache_key=cache_key,
                ttl=ttl,
                query_preview=query[:50]
            )

        except Exception as e:
            logger.error(
                "cache_set_error",
                error=str(e),
                error_type=type(e).__name__
            )

    async def invalidate_category(self, category: str):
        """
        Invalidate all cached responses in a category.

        Args:
            category: Category to invalidate (menu, restaurant_info, etc.)
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            # Find all keys matching pattern
            pattern = f"cache:{category}:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)

                if keys:
                    await self.redis_client.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(
                "cache_invalidated",
                category=category,
                deleted_keys=deleted_count
            )

        except Exception as e:
            logger.error(
                "cache_invalidation_error",
                category=category,
                error=str(e),
                error_type=type(e).__name__
            )

    async def clear_all_cache(self):
        """Clear all cached responses"""
        if not self.enabled or not self.redis_client:
            return

        try:
            # Find all cache keys
            pattern = "cache:*"
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)

                if keys:
                    await self.redis_client.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            logger.info(
                "all_cache_cleared",
                deleted_keys=deleted_count
            )

        except Exception as e:
            logger.error(
                "cache_clear_error",
                error=str(e),
                error_type=type(e).__name__
            )

    # Generic key-value cache methods for general-purpose caching
    async def get(self, key: str) -> Optional[str]:
        """
        Get a value from cache by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error("cache_get_error", key=key, error=str(e))
            return None

    async def set(self, key: str, value: str, ttl: Optional[timedelta] = None):
        """
        Set a value in cache with optional TTL.

        Args:
            key: Cache key
            value: Value to cache (must be string)
            ttl: Optional time-to-live (timedelta)
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            if ttl:
                # Convert timedelta to seconds
                ttl_seconds = int(ttl.total_seconds())
                await self.redis_client.setex(key, ttl_seconds, value)
            else:
                await self.redis_client.set(key, value)
        except Exception as e:
            logger.error("cache_set_error", key=key, error=str(e))

    async def delete(self, key: str):
        """
        Delete a key from cache.

        Args:
            key: Cache key to delete
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            await self.redis_client.delete(key)
        except Exception as e:
            logger.error("cache_delete_error", key=key, error=str(e))

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "enabled": self.enabled,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate_percent": round(hit_rate, 2),
            "ttl_config": self.ttl_config
        }

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("cache_service_closed")


# Global singleton instance
_cache_service_instance: Optional[ResponseCacheService] = None


def get_cache_service() -> ResponseCacheService:
    """
    Get or create the global cache service instance.

    Returns:
        Global cache service singleton
    """
    global _cache_service_instance

    if _cache_service_instance is None:
        _cache_service_instance = ResponseCacheService()

    return _cache_service_instance
