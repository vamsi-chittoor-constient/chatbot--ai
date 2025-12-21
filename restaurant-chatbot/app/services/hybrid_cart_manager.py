"""
Hybrid Cart Manager
====================
Manages shopping cart with dual persistence:
1. Redis - Fast, temporary (active sessions)
2. PostgreSQL - Persistent, long-term (logged-in users)

Cart survives session refresh, app restart, and device switching.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import structlog

import redis.asyncio as redis
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert

from app.core.database import get_db_session
from app.core.config import config
from app.features.food_ordering.models.abandoned_cart import AbandonedCart
from app.utils.id_generator import generate_id

logger = structlog.get_logger("services.hybrid_cart")


class HybridCartManager:
    """
    Manages cart persistence across sessions and devices.

    Two-tier storage:
    - Redis: Fast access for active sessions (30min TTL)
    - PostgreSQL: Long-term storage for logged-in users
    """

    def __init__(self):
        # Redis connection for session cart
        self.redis_client = None
        self._redis_initialized = False

    async def _ensure_redis(self):
        """Lazy initialize Redis connection."""
        if not self._redis_initialized:
            try:
                self.redis_client = await redis.from_url(
                    config.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
                self._redis_initialized = True
                logger.info("Redis connection initialized for cart manager")
            except Exception as e:
                logger.error("Failed to connect to Redis", error=str(e))
                self.redis_client = None

    async def save_cart(
        self,
        session_id: str,
        cart_items: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        device_id: Optional[str] = None
    ):
        """
        Save cart to both Redis (fast) and PostgreSQL (persistent).

        Args:
            session_id: Current session ID
            cart_items: List of cart items
            user_id: User ID if authenticated
            device_id: Device fingerprint ID
        """
        try:
            # Calculate cart totals
            cart_total = sum(
                item.get('price', 0) * item.get('quantity', 1)
                for item in cart_items
            )

            # 1. Save to Redis (active session - 30 min TTL)
            await self._ensure_redis()
            if self.redis_client:
                try:
                    await self.redis_client.setex(
                        f"cart:{session_id}",
                        1800,  # 30 minutes
                        json.dumps({
                            'items': cart_items,
                            'total': cart_total,
                            'updated_at': datetime.now().isoformat()
                        })
                    )
                    logger.debug(
                        "Cart saved to Redis",
                        session_id=session_id,
                        items_count=len(cart_items)
                    )
                except Exception as e:
                    logger.warning("Redis save failed, continuing with PG only", error=str(e))

            # 2. Save to PostgreSQL (persistent - for logged-in or device-tracked users)
            if user_id or device_id:
                async with get_db_session() as db_session:
                    # Upsert to abandoned_cart table
                    stmt = insert(AbandonedCart).values(
                        abandoned_cart_id=generate_id("abandoned_cart"),
                        user_id=user_id,
                        device_id=device_id,
                        session_id=session_id,
                        cart_data={'items': cart_items},
                        cart_items_count=len(cart_items),
                        cart_total=str(cart_total),
                        recovery_status='active',
                        last_activity='cart_updated',
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    ).on_conflict_do_update(
                        index_elements=['session_id'],
                        set_={
                            'cart_data': {'items': cart_items},
                            'cart_items_count': len(cart_items),
                            'cart_total': str(cart_total),
                            'updated_at': datetime.now(),
                            'last_activity': 'cart_updated'
                        }
                    )

                    await db_session.execute(stmt)
                    await db_session.commit()

                    logger.info(
                        "Cart persisted to PostgreSQL",
                        session_id=session_id,
                        user_id=user_id,
                        device_id=device_id,
                        items_count=len(cart_items)
                    )

        except Exception as e:
            logger.error(
                "Failed to save cart",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            # Don't raise - cart save failure shouldn't break the flow

    async def get_cart(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get cart from Redis (fast) or PostgreSQL (fallback).

        Retrieval priority:
        1. Redis by session_id (fastest)
        2. PostgreSQL by user_id (logged-in user)
        3. PostgreSQL by device_id (recognized device)

        Args:
            session_id: Current session ID
            user_id: User ID if authenticated
            device_id: Device fingerprint ID

        Returns:
            List of cart items
        """
        try:
            # 1. Try Redis first (active session)
            await self._ensure_redis()
            if self.redis_client:
                try:
                    cart_json = await self.redis_client.get(f"cart:{session_id}")
                    if cart_json:
                        cart_data = json.loads(cart_json)
                        logger.debug(
                            "Cart retrieved from Redis",
                            session_id=session_id,
                            items_count=len(cart_data.get('items', []))
                        )
                        return cart_data.get('items', [])
                except Exception as e:
                    logger.warning("Redis get failed, falling back to PG", error=str(e))

            # 2. Try PostgreSQL (user or device)
            if user_id or device_id:
                async with get_db_session() as db_session:
                    # Query by user_id (highest priority for logged-in users)
                    if user_id:
                        query = select(AbandonedCart).where(
                            AbandonedCart.user_id == user_id,
                            AbandonedCart.is_deleted == False
                        ).order_by(AbandonedCart.updated_at.desc()).limit(1)
                    # Fallback to device_id (for recognized but not logged-in users)
                    elif device_id:
                        query = select(AbandonedCart).where(
                            AbandonedCart.device_id == device_id,
                            AbandonedCart.is_deleted == False
                        ).order_by(AbandonedCart.updated_at.desc()).limit(1)

                    result = await db_session.execute(query)
                    cart_record = result.scalar_one_or_none()

                    if cart_record and cart_record.cart_data:
                        cart_items = cart_record.cart_data.get('items', [])

                        # Restore to Redis for future fast access
                        if self.redis_client:
                            try:
                                await self.redis_client.setex(
                                    f"cart:{session_id}",
                                    1800,
                                    json.dumps({
                                        'items': cart_items,
                                        'updated_at': datetime.now().isoformat()
                                    })
                                )
                            except:
                                pass  # Redis restore is optional

                        logger.info(
                            "Cart recovered from PostgreSQL",
                            session_id=session_id,
                            user_id=user_id,
                            device_id=device_id,
                            items_count=len(cart_items)
                        )
                        return cart_items

            # No cart found
            logger.debug(
                "No cart found",
                session_id=session_id,
                user_id=user_id,
                device_id=device_id
            )
            return []

        except Exception as e:
            logger.error(
                "Failed to get cart",
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
            return []

    async def clear_cart(
        self,
        session_id: str,
        user_id: Optional[str] = None
    ):
        """
        Clear cart from both Redis and PostgreSQL.

        Args:
            session_id: Current session ID
            user_id: User ID if authenticated
        """
        try:
            # Clear from Redis
            await self._ensure_redis()
            if self.redis_client:
                try:
                    await self.redis_client.delete(f"cart:{session_id}")
                except:
                    pass

            # Clear from PostgreSQL
            if user_id:
                async with get_db_session() as db_session:
                    await db_session.execute(
                        update(AbandonedCart)
                        .where(AbandonedCart.user_id == user_id)
                        .values(
                            cart_data=None,
                            cart_items_count=0,
                            cart_total='0',
                            is_deleted=True,
                            updated_at=datetime.now()
                        )
                    )
                    await db_session.commit()

            logger.info(
                "Cart cleared",
                session_id=session_id,
                user_id=user_id
            )

        except Exception as e:
            logger.error(
                "Failed to clear cart",
                session_id=session_id,
                error=str(e)
            )

    async def mark_cart_as_ordered(
        self,
        session_id: str,
        user_id: Optional[str],
        order_id: str
    ):
        """
        Mark abandoned cart as recovered (converted to order).

        Args:
            session_id: Session ID
            user_id: User ID
            order_id: Created order ID
        """
        try:
            if user_id:
                async with get_db_session() as db_session:
                    await db_session.execute(
                        update(AbandonedCart)
                        .where(AbandonedCart.user_id == user_id)
                        .values(
                            recovery_status='recovered',
                            recovered_at=datetime.now(),
                            recovered_order_id=order_id,
                            updated_at=datetime.now()
                        )
                    )
                    await db_session.commit()

                logger.info(
                    "Cart marked as ordered",
                    session_id=session_id,
                    user_id=user_id,
                    order_id=order_id
                )

        except Exception as e:
            logger.error("Failed to mark cart as ordered", error=str(e))


# Global singleton
_cart_manager = None


def get_cart_manager() -> HybridCartManager:
    """Get global cart manager instance."""
    global _cart_manager
    if _cart_manager is None:
        _cart_manager = HybridCartManager()
    return _cart_manager


__all__ = ["HybridCartManager", "get_cart_manager"]
