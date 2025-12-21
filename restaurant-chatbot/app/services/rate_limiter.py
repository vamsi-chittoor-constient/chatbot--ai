"""
Rate Limiting Service for Multi-Tenant API
Provides configurable rate limiting per restaurant API key
"""
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import structlog

from app.services.cache_service import CacheService

logger = structlog.get_logger(__name__)


class RateLimiter:
    """
    Redis-based rate limiter for API requests.

    Features:
    - Sliding window rate limiting
    - Per-restaurant limits
    - Configurable windows (minute, hour, day)
    - Graceful degradation if Redis unavailable
    """

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache = cache_service or CacheService()

        self.default_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        }

        self.custom_limits: Dict[str, Dict[str, int]] = {}

    def set_custom_limits(self, restaurant_id: str, limits: Dict[str, int]):
        """
        Set custom rate limits for a specific restaurant.

        Args:
            restaurant_id: Restaurant ID
            limits: Dict with keys: requests_per_minute, requests_per_hour, requests_per_day
        """
        self.custom_limits[restaurant_id] = limits
        logger.info(
            "custom_rate_limits_set",
            restaurant_id=restaurant_id,
            limits=limits
        )

    def get_limits(self, restaurant_id: str) -> Dict[str, int]:
        """Get rate limits for restaurant (custom or default)"""
        return self.custom_limits.get(restaurant_id, self.default_limits)

    async def check_rate_limit(
        self,
        restaurant_id: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limits.

        Args:
            restaurant_id: Restaurant ID
            endpoint: Specific endpoint (optional, for endpoint-specific limits)

        Returns:
            dict: {
                "allowed": bool,
                "limit": int,
                "remaining": int,
                "reset_at": datetime,
                "retry_after": int (seconds)
            }
        """
        try:
            limits = self.get_limits(restaurant_id)

            minute_key = f"rate_limit:{restaurant_id}:minute:{int(time.time() // 60)}"
            hour_key = f"rate_limit:{restaurant_id}:hour:{int(time.time() // 3600)}"
            day_key = f"rate_limit:{restaurant_id}:day:{int(time.time() // 86400)}"

            if not self.cache.redis_client:
                logger.warning("rate_limiter_redis_unavailable_allowing_request")
                return {
                    "allowed": True,
                    "limit": limits["requests_per_minute"],
                    "remaining": limits["requests_per_minute"],
                    "reset_at": datetime.now() + timedelta(minutes=1),
                    "retry_after": 0
                }

            minute_count = await self.cache.redis_client.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0

            hour_count = await self.cache.redis_client.get(hour_key)
            hour_count = int(hour_count) if hour_count else 0

            day_count = await self.cache.redis_client.get(day_key)
            day_count = int(day_count) if day_count else 0

            if minute_count >= limits["requests_per_minute"]:
                logger.warning(
                    "rate_limit_exceeded_minute",
                    restaurant_id=restaurant_id,
                    count=minute_count,
                    limit=limits["requests_per_minute"]
                )
                return {
                    "allowed": False,
                    "limit": limits["requests_per_minute"],
                    "remaining": 0,
                    "reset_at": datetime.now() + timedelta(seconds=60 - (int(time.time()) % 60)),
                    "retry_after": 60 - (int(time.time()) % 60)
                }

            if hour_count >= limits["requests_per_hour"]:
                logger.warning(
                    "rate_limit_exceeded_hour",
                    restaurant_id=restaurant_id,
                    count=hour_count,
                    limit=limits["requests_per_hour"]
                )
                return {
                    "allowed": False,
                    "limit": limits["requests_per_hour"],
                    "remaining": 0,
                    "reset_at": datetime.now() + timedelta(seconds=3600 - (int(time.time()) % 3600)),
                    "retry_after": 3600 - (int(time.time()) % 3600)
                }

            if day_count >= limits["requests_per_day"]:
                logger.warning(
                    "rate_limit_exceeded_day",
                    restaurant_id=restaurant_id,
                    count=day_count,
                    limit=limits["requests_per_day"]
                )
                return {
                    "allowed": False,
                    "limit": limits["requests_per_day"],
                    "remaining": 0,
                    "reset_at": datetime.now() + timedelta(seconds=86400 - (int(time.time()) % 86400)),
                    "retry_after": 86400 - (int(time.time()) % 86400)
                }

            await self.cache.redis_client.incr(minute_key)
            await self.cache.redis_client.expire(minute_key, 60)

            await self.cache.redis_client.incr(hour_key)
            await self.cache.redis_client.expire(hour_key, 3600)

            await self.cache.redis_client.incr(day_key)
            await self.cache.redis_client.expire(day_key, 86400)

            return {
                "allowed": True,
                "limit": limits["requests_per_minute"],
                "remaining": limits["requests_per_minute"] - minute_count - 1,
                "reset_at": datetime.now() + timedelta(seconds=60 - (int(time.time()) % 60)),
                "retry_after": 0
            }

        except Exception as e:
            logger.error("rate_limit_check_error", error=str(e))
            return {
                "allowed": True,
                "limit": self.default_limits["requests_per_minute"],
                "remaining": self.default_limits["requests_per_minute"],
                "reset_at": datetime.now() + timedelta(minutes=1),
                "retry_after": 0
            }

    async def reset_limits(self, restaurant_id: str):
        """
        Reset rate limits for a restaurant (admin function).

        Args:
            restaurant_id: Restaurant ID
        """
        try:
            if not self.cache.redis_client:
                return

            minute_pattern = f"rate_limit:{restaurant_id}:minute:*"
            hour_pattern = f"rate_limit:{restaurant_id}:hour:*"
            day_pattern = f"rate_limit:{restaurant_id}:day:*"

            for pattern in [minute_pattern, hour_pattern, day_pattern]:
                cursor = 0
                while True:
                    cursor, keys = await self.cache.redis_client.scan(
                        cursor=cursor,
                        match=pattern,
                        count=100
                    )
                    if keys:
                        await self.cache.redis_client.delete(*keys)
                    if cursor == 0:
                        break

            logger.info("rate_limits_reset", restaurant_id=restaurant_id)

        except Exception as e:
            logger.error("rate_limit_reset_error", error=str(e))


_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create singleton rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
