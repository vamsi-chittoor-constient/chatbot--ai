"""
User Session Cache Service
===========================
Multi-tier caching system for user-specific data:

1. Session Cache (Redis) - Active users, auto-expire on session end
2. Persistent Storage (PostgreSQL) - User preferences, history, favorites
3. Cache Restoration - Load user data from DB when user logs in

Architecture:
- Global cache (existing cache_service.py) - Shared data
- User session cache (this file) - Per-user temporary data
- Persistent storage (database) - Long-term user data
"""

import os
import json
from typing import Optional, Any, Dict, List
from datetime import timedelta
import structlog
import redis.asyncio as redis

logger = structlog.get_logger(__name__)


class UserSessionCacheService:
    """
    Manages user-specific session caches in Redis.

    Features:
    - Session-based caching (auto-expire on disconnect)
    - User context storage (cart, booking in progress)
    - Recent queries tracking
    - Cache restoration from persistent storage
    - Automatic cleanup on session end
    """

    def __init__(self):
        """Initialize Redis connection for user session caches"""
        self.enabled = os.getenv("ENABLE_USER_SESSION_CACHE", "true").lower() == "true"

        if not self.enabled:
            logger.info("user_session_cache_disabled")
            self.redis_client = None
            return

        # Redis configuration
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        self.redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        # Session TTL (default: 30 minutes of inactivity)
        self.session_ttl = int(os.getenv("USER_SESSION_TTL", "1800"))  # 30 minutes

        logger.info(
            "user_session_cache_initialized",
            enabled=self.enabled,
            session_ttl_seconds=self.session_ttl
        )

    def _get_session_key(self, user_id: str, key_type: str) -> str:
        """
        Generate Redis key for user session data.

        Args:
            user_id: User ID (e.g., usr000001)
            key_type: Type of data (cart, booking, queries, context)

        Returns:
            Redis key string
        """
        return f"user_session:{user_id}:{key_type}"

    # ========================================================================
    # SESSION MANAGEMENT
    # ========================================================================

    async def create_session(self, user_id: str, user_data: Optional[Dict] = None):
        """
        Create a new user session cache.

        Called when user logs in or starts a new session.
        Optionally loads user data from persistent storage.

        Args:
            user_id: User ID
            user_data: Optional user data to preload (preferences, history summary)
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            # Set session active marker
            session_key = self._get_session_key(user_id, "active")
            await self.redis_client.setex(
                session_key,
                self.session_ttl,
                "1"
            )

            # Preload user data if provided
            if user_data:
                context_key = self._get_session_key(user_id, "context")
                await self.redis_client.setex(
                    context_key,
                    self.session_ttl,
                    json.dumps(user_data)
                )

            logger.info(
                "user_session_created",
                user_id=user_id,
                ttl_seconds=self.session_ttl,
                preloaded_data=bool(user_data)
            )

        except Exception as e:
            logger.error(
                "user_session_create_error",
                user_id=user_id,
                error=str(e)
            )

    async def extend_session(self, user_id: str):
        """
        Extend session TTL (called on user activity).

        Args:
            user_id: User ID
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            # Extend all session keys for this user
            pattern = f"user_session:{user_id}:*"
            cursor = 0

            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)

                if keys:
                    for key in keys:
                        await self.redis_client.expire(key, self.session_ttl)

                if cursor == 0:
                    break

            logger.debug("user_session_extended", user_id=user_id)

        except Exception as e:
            logger.error(
                "user_session_extend_error",
                user_id=user_id,
                error=str(e)
            )

    async def destroy_session(self, user_id: str, save_to_persistent: bool = True):
        """
        Destroy user session cache.

        Called when user logs out or session expires.
        Optionally saves important data to persistent storage first.

        Args:
            user_id: User ID
            save_to_persistent: If True, save cart/booking to DB before destroying
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            # TODO: If save_to_persistent=True, save cart/booking to database
            # This would be done by calling database service here

            # Delete all session keys for this user
            pattern = f"user_session:{user_id}:*"
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
                "user_session_destroyed",
                user_id=user_id,
                deleted_keys=deleted_count,
                saved_to_persistent=save_to_persistent
            )

        except Exception as e:
            logger.error(
                "user_session_destroy_error",
                user_id=user_id,
                error=str(e)
            )

    # ========================================================================
    # CART MANAGEMENT (Session Cache)
    # ========================================================================

    async def get_cart(self, user_id: str) -> Optional[Dict]:
        """Get user's current cart from session cache."""
        if not self.enabled or not self.redis_client:
            return None

        try:
            cart_key = self._get_session_key(user_id, "cart")
            cart_data = await self.redis_client.get(cart_key)

            if cart_data:
                return json.loads(cart_data)

            return None

        except Exception as e:
            logger.error("get_cart_error", user_id=user_id, error=str(e))
            return None

    async def set_cart(self, user_id: str, cart_data: Dict):
        """Set user's current cart in session cache."""
        if not self.enabled or not self.redis_client:
            return

        try:
            cart_key = self._get_session_key(user_id, "cart")
            await self.redis_client.setex(
                cart_key,
                self.session_ttl,
                json.dumps(cart_data)
            )

            # Extend session on activity
            await self.extend_session(user_id)

        except Exception as e:
            logger.error("set_cart_error", user_id=user_id, error=str(e))

    # ========================================================================
    # BOOKING IN PROGRESS (Session Cache)
    # ========================================================================

    async def get_booking_in_progress(self, user_id: str) -> Optional[Dict]:
        """Get user's booking in progress from session cache."""
        if not self.enabled or not self.redis_client:
            return None

        try:
            booking_key = self._get_session_key(user_id, "booking")
            booking_data = await self.redis_client.get(booking_key)

            if booking_data:
                return json.loads(booking_data)

            return None

        except Exception as e:
            logger.error("get_booking_error", user_id=user_id, error=str(e))
            return None

    async def set_booking_in_progress(self, user_id: str, booking_data: Dict):
        """Set user's booking in progress in session cache."""
        if not self.enabled or not self.redis_client:
            return

        try:
            booking_key = self._get_session_key(user_id, "booking")
            await self.redis_client.setex(
                booking_key,
                self.session_ttl,
                json.dumps(booking_data)
            )

            await self.extend_session(user_id)

        except Exception as e:
            logger.error("set_booking_error", user_id=user_id, error=str(e))

    async def clear_booking_in_progress(self, user_id: str):
        """Clear booking in progress (after booking confirmed)."""
        if not self.enabled or not self.redis_client:
            return

        try:
            booking_key = self._get_session_key(user_id, "booking")
            await self.redis_client.delete(booking_key)

        except Exception as e:
            logger.error("clear_booking_error", user_id=user_id, error=str(e))

    # ========================================================================
    # RECENT QUERIES (Session Cache)
    # ========================================================================

    async def add_recent_query(self, user_id: str, query: str):
        """Add query to user's recent queries (last 10)."""
        if not self.enabled or not self.redis_client:
            return

        try:
            queries_key = self._get_session_key(user_id, "recent_queries")

            # Add to list (limited to 10 items)
            await self.redis_client.lpush(queries_key, query)
            await self.redis_client.ltrim(queries_key, 0, 9)  # Keep only last 10
            await self.redis_client.expire(queries_key, self.session_ttl)

            await self.extend_session(user_id)

        except Exception as e:
            logger.error("add_recent_query_error", user_id=user_id, error=str(e))

    async def get_recent_queries(self, user_id: str, limit: int = 10) -> List[str]:
        """Get user's recent queries."""
        if not self.enabled or not self.redis_client:
            return []

        try:
            queries_key = self._get_session_key(user_id, "recent_queries")
            queries = await self.redis_client.lrange(queries_key, 0, limit - 1)
            return queries

        except Exception as e:
            logger.error("get_recent_queries_error", user_id=user_id, error=str(e))
            return []

    # ========================================================================
    # USER CONTEXT (Session Cache)
    # ========================================================================

    async def get_context(self, user_id: str) -> Optional[Dict]:
        """
        Get user's session context.

        Contains:
        - User preferences (from persistent storage)
        - Current conversation state
        - Temporary filters
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            context_key = self._get_session_key(user_id, "context")
            context_data = await self.redis_client.get(context_key)

            if context_data:
                return json.loads(context_data)

            return None

        except Exception as e:
            logger.error("get_context_error", user_id=user_id, error=str(e))
            return None

    async def update_context(self, user_id: str, context_updates: Dict):
        """Update user's session context (merge with existing)."""
        if not self.enabled or not self.redis_client:
            return

        try:
            # Get existing context
            existing_context = await self.get_context(user_id) or {}

            # Merge updates
            existing_context.update(context_updates)

            # Save back
            context_key = self._get_session_key(user_id, "context")
            await self.redis_client.setex(
                context_key,
                self.session_ttl,
                json.dumps(existing_context)
            )

            await self.extend_session(user_id)

        except Exception as e:
            logger.error("update_context_error", user_id=user_id, error=str(e))

    # ========================================================================
    # STATISTICS
    # ========================================================================

    async def get_active_sessions_count(self) -> int:
        """Get count of currently active user sessions."""
        if not self.enabled or not self.redis_client:
            return 0

        try:
            pattern = "user_session:*:active"
            cursor = 0
            count = 0

            while True:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                count += len(keys)

                if cursor == 0:
                    break

            return count

        except Exception as e:
            logger.error("get_active_sessions_error", error=str(e))
            return 0

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("user_session_cache_service_closed")


# Global singleton instance
_user_cache_instance: Optional[UserSessionCacheService] = None


def get_user_cache_service() -> UserSessionCacheService:
    """
    Get or create the global user session cache service instance.

    Returns:
        Global user cache service singleton
    """
    global _user_cache_instance

    if _user_cache_instance is None:
        _user_cache_instance = UserSessionCacheService()

    return _user_cache_instance
