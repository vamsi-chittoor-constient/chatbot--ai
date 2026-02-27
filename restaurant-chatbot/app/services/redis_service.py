"""
Redis service for caching and pub/sub messaging.

This service provides:
1. General-purpose caching (menu items, availability, user preferences)
2. Real-time pub/sub for order status, table availability updates
3. Rate limiting support
4. Performance optimized connection pooling

NOTE: Session and conversation state management is handled by PostgreSQL.
      This service focuses on short-lived caching and real-time messaging only.
"""

import redis.asyncio as redis
import json
import pickle
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta, timezone
import asyncio
import logging
from dataclasses import asdict, is_dataclass
import os
from contextlib import asynccontextmanager

from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration settings"""

    def __init__(self):
        self.host = os.getenv('REDIS_HOST', 'localhost')
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD')
        self.decode_responses = True
        self.socket_timeout = 5
        self.socket_connect_timeout = 5
        self.retry_on_timeout = True
        self.health_check_interval = 30


class RedisService:
    """
    Redis service for the Restaurant AI Assistant.

    Features:
    - General-purpose caching with TTL
    - Real-time pub/sub messaging
    - Connection pooling
    - JSON and pickle serialization

    Conversation state is handled by PostgreSQL.
    This service focuses on:
    - Short-lived data caching (menu items, availability)
    - Real-time pub/sub (order updates, table availability)
    - Rate limiting
    - Performance optimization
    """

    def __init__(self, config: Optional[RedisConfig] = None):
        self.config = config or RedisConfig()
        self._redis_client: Optional[redis.Redis] = None
        self._pubsub_client: Optional[redis.Redis] = None
        self._subscribers: Dict[str, List[Callable]] = {}
        self._running_subscribers = set()

        # Use shared Redis client from RedisManager instead of creating own pool
        try:
            self._redis_client = get_redis_client()
            self._pubsub_client = get_redis_client()
            logger.info("RedisService initialized using shared RedisManager connection pool")
        except RuntimeError as e:
            logger.warning(f"Could not get shared Redis client: {e}. Service will initialize on first use.")
            # Client will be initialized lazily when first used

    def _serialize_value(self, value: Any, use_pickle: bool = False) -> Union[str, bytes]:
        """Serialize Python objects for Redis storage"""
        if value is None:
            return ""

        if use_pickle:
            return pickle.dumps(value)

        # Handle dataclasses
        if is_dataclass(value) and not isinstance(value, type):
            value = asdict(value)

        # JSON serialization
        try:
            return json.dumps(value, default=str, ensure_ascii=False)
        except (TypeError, ValueError) as e:
            logger.warning(f"JSON serialization failed, falling back to pickle: {e}")
            return pickle.dumps(value)

    def _deserialize_value(self, value: Union[str, bytes], use_pickle: bool = False) -> Any:
        """Deserialize Redis values back to Python objects"""
        if not value:
            return None

        if use_pickle or isinstance(value, bytes):
            try:
                # Ensure we have bytes for pickle.loads
                if isinstance(value, str):
                    value_bytes = value.encode('utf-8')
                else:
                    value_bytes = value
                return pickle.loads(value_bytes)
            except (pickle.PickleError, TypeError, UnicodeEncodeError):
                pass

        # JSON deserialization
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    # ==================== CORE CACHING METHODS ====================

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, use_pickle: bool = False) -> bool:
        """
        Set a value in Redis with optional TTL

        Args:
            key: Redis key
            value: Value to store (will be JSON serialized)
            ttl: Time to live in seconds
            use_pickle: Use pickle instead of JSON for complex objects

        Returns:
            bool: True if successful
        """
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            serialized_value = self._serialize_value(value, use_pickle)

            if ttl:
                result = await self._redis_client.setex(key, ttl, serialized_value)
                return bool(result)
            else:
                result = await self._redis_client.set(key, serialized_value)
                return bool(result)
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis SET failed for key {key}: {e}")
            return False

    async def get(self, key: str, use_pickle: bool = False) -> Any:
        """
        Get a value from Redis

        Args:
            key: Redis key
            use_pickle: Use pickle for deserialization

        Returns:
            Deserialized value or None
        """
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return None

        try:
            value = await self._redis_client.get(key)
            if value is None:
                return None
            return self._deserialize_value(str(value) if not isinstance(value, bytes) else value, use_pickle)
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis GET failed for key {key}: {e}")
            return None

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys from Redis"""
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return 0

        try:
            result = await self._redis_client.delete(*keys)
            return int(result) if result is not None else 0
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis DELETE failed for keys {keys}: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            result = await self._redis_client.exists(key)
            return int(result) > 0 if result is not None else False
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis EXISTS failed for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for an existing key"""
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return False

        try:
            result = await self._redis_client.expire(key, ttl)
            return bool(result)
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis EXPIRE failed for key {key}: {e}")
            return False

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching a pattern"""
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return []

        try:
            result = await self._redis_client.keys(pattern)
            return list(result) if result is not None else []
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis KEYS failed for pattern {pattern}: {e}")
            return []

    async def incr(self, key: str, amount: int = 1) -> int:
        """
        Increment a key's value (useful for rate limiting, counters)

        Args:
            key: Redis key
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return 0

        try:
            result = await self._redis_client.incrby(key, amount)
            return int(result) if result is not None else 0
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis INCR failed for key {key}: {e}")
            return 0

    # ==================== REAL-TIME PUB/SUB ====================

    async def publish(self, channel: str, message: Any) -> int:
        """
        Publish a message to a Redis channel

        Args:
            channel: Channel name
            message: Message to publish (will be JSON serialized)

        Returns:
            Number of subscribers that received the message
        """
        if not self._redis_client:
            logger.error("Redis client not initialized")
            return 0

        try:
            serialized_message = self._serialize_value({
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "channel": channel
            })
            result = await self._redis_client.publish(channel, serialized_message)
            return int(result) if result is not None else 0
        except (redis.RedisError, Exception) as e:
            logger.error(f"Redis PUBLISH failed for channel {channel}: {e}")
            return 0

    def subscribe(self, channel: str, callback: Callable[[str, Any], None]) -> bool:
        """
        Subscribe to a Redis channel with a callback function

        Args:
            channel: Channel to subscribe to
            callback: Function to call when message received (channel, message)

        Returns:
            bool: True if subscription started successfully
        """
        try:
            if channel not in self._subscribers:
                self._subscribers[channel] = []

            self._subscribers[channel].append(callback)

            # Start subscriber if not already running
            if channel not in self._running_subscribers:
                asyncio.create_task(self._run_subscriber(channel))
                self._running_subscribers.add(channel)

            logger.info(f"Subscribed to Redis channel: {channel}")
            return True
        except Exception as e:
            logger.error(f"Failed to subscribe to channel {channel}: {e}")
            return False

    async def _run_subscriber(self, channel: str):
        """Run subscriber for a channel (internal method)"""
        if not self._pubsub_client:
            logger.error("Redis pubsub client not initialized")
            return

        pubsub = self._pubsub_client.pubsub()
        try:
            pubsub.subscribe(channel)

            while channel in self._running_subscribers:
                message = pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        # Deserialize message
                        data = self._deserialize_value(message['data'])
                        msg_content = data.get('message') if isinstance(data, dict) else data

                        # Call all callbacks for this channel
                        for callback in self._subscribers.get(channel, []):
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(channel, msg_content)
                                else:
                                    callback(channel, msg_content)
                            except Exception as e:
                                logger.error(f"Callback error for channel {channel}: {e}")

                    except Exception as e:
                        logger.error(f"Message processing error for channel {channel}: {e}")

                await asyncio.sleep(0.1)  # Small delay to prevent CPU spinning

        except Exception as e:
            logger.error(f"Subscriber error for channel {channel}: {e}")
        finally:
            pubsub.close()
            self._running_subscribers.discard(channel)

    def unsubscribe(self, channel: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from a channel

        Args:
            channel: Channel to unsubscribe from
            callback: Specific callback to remove (if None, removes all)
        """
        if channel in self._subscribers:
            if callback:
                self._subscribers[channel] = [
                    cb for cb in self._subscribers[channel] if cb != callback
                ]
            else:
                self._subscribers[channel] = []

            # Stop subscriber if no more callbacks
            if not self._subscribers[channel]:
                self._running_subscribers.discard(channel)
                logger.info(f"Unsubscribed from Redis channel: {channel}")

    # ==================== BUSINESS-SPECIFIC CACHING ====================

    async def cache_menu_items(self, menu_items: List[Dict], ttl: int = 3600) -> bool:
        """
        Cache menu items (frequently accessed data)

        Args:
            menu_items: List of menu item dictionaries
            ttl: Cache TTL in seconds (default 1 hour)
        """
        return await self.set("cache:menu_items", menu_items, ttl)

    async def get_cached_menu_items(self) -> Optional[List[Dict]]:
        """Get cached menu items"""
        return await self.get("cache:menu_items")

    async def cache_table_availability(self, restaurant_id: str, date: str, availability: Dict, ttl: int = 300) -> bool:
        """
        Cache table availability for a specific date

        Args:
            restaurant_id: Restaurant identifier
            date: Date string (YYYY-MM-DD)
            availability: Availability data
            ttl: Cache TTL in seconds (default 5 minutes)
        """
        key = f"cache:availability:{restaurant_id}:{date}"
        return await self.set(key, availability, ttl)

    async def get_cached_table_availability(self, restaurant_id: str, date: str) -> Optional[Dict]:
        """Get cached table availability"""
        key = f"cache:availability:{restaurant_id}:{date}"
        return await self.get(key)

    async def cache_user_preferences(self, user_id: str, preferences: Dict, ttl: int = 86400) -> bool:
        """
        Cache user preferences

        Args:
            user_id: User identifier
            preferences: User preferences dictionary
            ttl: Cache TTL in seconds (default 24 hours)
        """
        return await self.set(f"cache:user_prefs:{user_id}", preferences, ttl)

    async def get_cached_user_preferences(self, user_id: str) -> Optional[Dict]:
        """Get cached user preferences"""
        return await self.get(f"cache:user_prefs:{user_id}")

    async def cache_faq_search_results(self, query_hash: str, results: List[Dict], ttl: int = 1800) -> bool:
        """
        Cache FAQ search results

        Args:
            query_hash: Hash of the search query
            results: Search results
            ttl: Cache TTL in seconds (default 30 minutes)
        """
        return await self.set(f"cache:faq:{query_hash}", results, ttl)

    async def get_cached_faq_results(self, query_hash: str) -> Optional[List[Dict]]:
        """Get cached FAQ search results"""
        return await self.get(f"cache:faq:{query_hash}")

    # ==================== REAL-TIME UPDATES ====================

    async def publish_order_update(self, order_id: str, status: str, details: Optional[Dict] = None) -> int:
        """
        Publish order status update to real-time channel

        Args:
            order_id: Order identifier
            status: New order status
            details: Additional order details

        Returns:
            Number of subscribers notified
        """
        message = {
            "order_id": order_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return await self.publish(f"order_updates:{order_id}", message)

    async def publish_table_update(self, table_id: str, available: bool, details: Optional[Dict] = None) -> int:
        """
        Publish table availability update to real-time channel

        Args:
            table_id: Table identifier
            available: Whether table is available
            details: Additional table details

        Returns:
            Number of subscribers notified
        """
        message = {
            "table_id": table_id,
            "available": available,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return await self.publish("table_updates", message)

    async def publish_booking_update(self, booking_id: str, status: str, details: Optional[Dict] = None) -> int:
        """
        Publish booking status update to real-time channel

        Args:
            booking_id: Booking identifier
            status: New booking status
            details: Additional booking details

        Returns:
            Number of subscribers notified
        """
        message = {
            "booking_id": booking_id,
            "status": status,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return await self.publish(f"booking_updates:{booking_id}", message)

    # ==================== RATE LIMITING ====================

    async def check_rate_limit(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if rate limit is exceeded

        Args:
            key: Rate limit key (e.g., user_id, ip_address)
            max_requests: Maximum requests allowed
            window_seconds: Time window in seconds

        Returns:
            bool: True if under limit, False if exceeded
        """
        rate_key = f"rate_limit:{key}"

        try:
            current = await self.incr(rate_key)

            # Set expiry on first request
            if current == 1:
                await self.expire(rate_key, window_seconds)

            return current <= max_requests
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow on error

    # ==================== UTILITY METHODS ====================

    async def health_check(self) -> Dict[str, Any]:
        """Perform Redis health check"""
        if not self._redis_client:
            return {
                "status": "unhealthy",
                "error": "Redis client not initialized",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        try:
            start_time = datetime.now(timezone.utc)

            # Ping test
            ping_result = await self._redis_client.ping()

            # Set/get test
            test_key = f"health_check:{datetime.now(timezone.utc).timestamp()}"
            await self._redis_client.set(test_key, "test", ex=60)
            get_result = await self._redis_client.get(test_key)
            await self._redis_client.delete(test_key)

            response_time = (datetime.now(timezone.utc) - start_time).total_seconds()

            return {
                "status": "healthy",
                "ping": ping_result,
                "set_get_test": get_result == "test",
                "response_time_seconds": response_time,
                "active_subscribers": len(self._running_subscribers),
                "using_shared_pool": True  # Now using RedisManager's shared pool
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def close(self):
        """Close Redis connections and cleanup"""
        try:
            # Stop all subscribers
            self._running_subscribers.clear()
            self._subscribers.clear()

            # Note: We don't close the shared Redis client from RedisManager
            # The RedisManager handles connection lifecycle
            logger.info("RedisService cleanup complete (shared connections managed by RedisManager)")
        except Exception as e:
            logger.error(f"Error during RedisService cleanup: {e}")


# ==================== SINGLETON INSTANCE ====================

# Global Redis service instance
_redis_service_instance = None

def get_redis_service() -> RedisService:
    """Get singleton Redis service instance"""
    global _redis_service_instance
    if _redis_service_instance is None:
        _redis_service_instance = RedisService()
    return _redis_service_instance


# ==================== CONTEXT MANAGER ====================

@asynccontextmanager
async def redis_service():
    """Context manager for Redis service"""
    service = get_redis_service()
    try:
        yield service
    finally:
        # Don't close the global instance
        pass


if __name__ == "__main__":

    async def test_redis_service():
        """Test the Redis service functionality"""
        print("Testing Redis Service...")

        # Initialize service
        redis_svc = RedisService()

        # Test health check
        health = redis_svc.health_check()
        print(f"Health check: {health}")

        # Test basic caching
        redis_svc.set("test_key", {"message": "Hello Redis!"}, ttl=300)
        result = redis_svc.get("test_key")
        print(f"Cache test: {result}")

        # Test menu caching
        redis_svc.cache_menu_items([{"id": "1", "name": "Pizza"}])
        menu = redis_svc.get_cached_menu_items()
        print(f"Menu cache test: {menu}")

        # Test rate limiting
        is_allowed = redis_svc.check_rate_limit("test_user", max_requests=5, window_seconds=60)
        print(f"Rate limit test: {is_allowed}")

        # Test pub/sub
        def message_handler(channel, message):
            print(f"Received on {channel}: {message}")

        redis_svc.subscribe("test_channel", message_handler)
        await asyncio.sleep(1)  # Let subscriber start

        sent_count = redis_svc.publish("test_channel", {"test": "pub/sub working"})
        print(f"Published to {sent_count} subscribers")

        await asyncio.sleep(2)  # Let message process

        # Cleanup
        redis_svc.delete("test_key")
        redis_svc.close()

        print("Redis service test completed!")

    # Run test
    asyncio.run(test_redis_service())
