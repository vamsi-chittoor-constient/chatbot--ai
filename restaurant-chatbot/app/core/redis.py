"""
Redis Connection Management
===========================

Centralized Redis connection pooling for caching and ephemeral data.

Features:
- Production-ready connection pooling (async AND sync)
- Feature-aware key namespacing
- Automatic connection health checks
- Connection timeout handling
"""

import redis.asyncio as async_redis
import redis as sync_redis
from typing import Optional, Any, Dict
import os
import json

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class RedisManager:
    """
    Centralized Redis connection manager with production-ready pooling.

    All features use this shared connection pool for caching operations.
    Provides both async and sync clients.
    """

    def __init__(self):
        self.pool: Optional[async_redis.ConnectionPool] = None
        self.client: Optional[async_redis.Redis] = None
        self.sync_pool: Optional[sync_redis.ConnectionPool] = None
        self.sync_client: Optional[sync_redis.Redis] = None
        self._initialized = False

    def init_redis(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 50,
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        decode_responses: bool = True
    ):
        """
        Initialize Redis with connection pooling (async AND sync).

        Args:
            redis_url: Redis connection string (from env if not provided)
            max_connections: Maximum connections in pool
            socket_timeout: Socket operation timeout in seconds
            socket_connect_timeout: Socket connection timeout in seconds
            decode_responses: Automatically decode responses to strings
        """
        if self._initialized:
            logger.warning("Redis already initialized")
            return

        # Get Redis URL from environment if not provided
        if not redis_url:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

        logger.info(
            "Initializing Redis connection pools",
            max_connections=max_connections,
            socket_timeout=socket_timeout
        )

        # Create ASYNC connection pool
        self.pool = async_redis.ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=decode_responses,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            socket_keepalive=True,
            health_check_interval=30  # Check connection health every 30s
        )

        # Create ASYNC Redis client
        self.client = async_redis.Redis(connection_pool=self.pool)

        # Create SYNC connection pool (for CrewAI tools running in threads)
        self.sync_pool = sync_redis.ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            decode_responses=decode_responses,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
        )

        # Create SYNC Redis client
        self.sync_client = sync_redis.Redis(connection_pool=self.sync_pool)

        self._initialized = True
        logger.info("Redis connection pools initialized (async + sync)")

    def get_client(self) -> async_redis.Redis:
        """
        Get ASYNC Redis client from the pool.

        Returns:
            async_redis.Redis: Async Redis client instance

        Raises:
            RuntimeError: If Redis not initialized
        """
        if not self._initialized or not self.client:
            raise RuntimeError(
                "Redis not initialized. Call init_redis() first."
            )
        return self.client

    def get_sync_client(self) -> sync_redis.Redis:
        """
        Get SYNC Redis client from the pool.

        Use this for synchronous code (e.g., CrewAI tools).

        Returns:
            sync_redis.Redis: Sync Redis client instance

        Raises:
            RuntimeError: If Redis not initialized
        """
        if not self._initialized or not self.sync_client:
            raise RuntimeError(
                "Redis not initialized. Call init_redis() first."
            )
        return self.sync_client

    async def ping(self) -> bool:
        """
        Test Redis connection (async).

        Returns:
            bool: True if connection is healthy
        """
        if not self.client:
            return False

        try:
            return await self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False

    def ping_sync(self) -> bool:
        """
        Test Redis connection (sync).

        Returns:
            bool: True if connection is healthy
        """
        if not self.sync_client:
            return False

        try:
            return self.sync_client.ping()
        except Exception as e:
            logger.error(f"Redis sync ping failed: {str(e)}")
            return False

    async def close(self):
        """Close Redis connections and cleanup"""
        if self.client:
            logger.info("Closing async Redis connections")
            await self.client.close()

        if self.pool:
            await self.pool.disconnect()

        if self.sync_client:
            logger.info("Closing sync Redis connections")
            self.sync_client.close()

        if self.sync_pool:
            self.sync_pool.disconnect()

        self._initialized = False
        logger.info("All Redis connections closed")


# Global Redis manager instance
redis_manager = RedisManager()


# Convenience function for getting ASYNC Redis client
def get_redis_client() -> async_redis.Redis:
    """
    Convenience function to get ASYNC Redis client.

    Usage:
        from app.core.redis import get_redis_client

        redis_client = get_redis_client()
        await redis_client.set('key', 'value')
    """
    return redis_manager.get_client()


# Convenience function for getting SYNC Redis client
def get_sync_redis_client() -> sync_redis.Redis:
    """
    Convenience function to get SYNC Redis client.

    Use this for synchronous code (e.g., CrewAI tools running in threads).

    Usage:
        from app.core.redis import get_sync_redis_client

        redis_client = get_sync_redis_client()
        redis_client.set('key', 'value')  # No await needed
    """
    return redis_manager.get_sync_client()


# ============================================================================
# ASYNC CART OPERATIONS (for async CrewAI tools - preferred)
# ============================================================================

async def get_cart(session_id: str) -> Dict[str, Any]:
    """
    Get cart data asynchronously.

    Args:
        session_id: Session ID

    Returns:
        Cart data dict or empty dict if no cart
    """
    client = get_redis_client()
    cart_key = f"cart:{session_id}"
    cart_data = await client.get(cart_key)

    if cart_data:
        return json.loads(cart_data)
    return {"items": []}


async def set_cart(session_id: str, cart_data: Dict[str, Any], ttl: int = 3600):
    """
    Set cart data asynchronously.

    Args:
        session_id: Session ID
        cart_data: Cart data dict
        ttl: Time to live in seconds (default 1 hour)
    """
    client = get_redis_client()
    cart_key = f"cart:{session_id}"
    await client.setex(cart_key, ttl, json.dumps(cart_data))


# ============================================================================
# SYNC CART OPERATIONS (legacy - kept for backwards compatibility)
# ============================================================================

def get_cart_sync(session_id: str) -> Dict[str, Any]:
    """
    Get cart data synchronously.

    Args:
        session_id: Session ID

    Returns:
        Cart data dict or empty dict if no cart
    """
    client = get_sync_redis_client()
    cart_key = f"cart:{session_id}"
    cart_data = client.get(cart_key)

    if cart_data:
        return json.loads(cart_data)
    return {"items": []}


def set_cart_sync(session_id: str, cart_data: Dict[str, Any], ttl: int = 3600):
    """
    Set cart data synchronously.

    Args:
        session_id: Session ID
        cart_data: Cart data dict
        ttl: Time to live in seconds (default 1 hour)
    """
    client = get_sync_redis_client()
    cart_key = f"cart:{session_id}"
    client.setex(cart_key, ttl, json.dumps(cart_data))
