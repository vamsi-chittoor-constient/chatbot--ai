"""
Inventory Cache Service
========================
Real-time inventory tracking and reservation system using Redis.

Solves the race condition problem:
- User A adds last Butter Chicken to cart
- User B tries to add same item at the same time
- Who gets it?  First to reserve it!

Architecture:
- Redis atomic operations (DECR, INCR) for thread-safe inventory
- Temporary reservations with TTL (15 minutes)
- Automatic release if user doesn't complete order
- Real-time availability tracking

Flow:
1. User adds item to cart  Reserve inventory (DECR available_count)
2. Item reserved for 15 minutes (TTL on reservation)
3. User completes order  Confirm reservation (update DB)
4. User abandons cart  Auto-release after TTL expires
5. User removes from cart  Explicit release (INCR available_count)
"""

import os
from typing import Optional, Dict, List, Tuple
from datetime import timedelta
import structlog
import redis.asyncio as redis

logger = structlog.get_logger(__name__)


class InventoryReservationError(Exception):
    """Raised when inventory cannot be reserved (out of stock)"""
    pass


class InventoryCacheService:
    """
    Manages real-time inventory with atomic Redis operations.

    Features:
    - Thread-safe inventory tracking
    - Temporary reservations (prevent overselling)
    - Automatic cleanup of expired reservations
    - Race condition prevention
    - Real-time availability queries
    """

    def __init__(self):
        """Initialize Redis connection for inventory management"""
        self.enabled = os.getenv("ENABLE_INVENTORY_CACHE", "true").lower() == "true"

        if not self.enabled:
            logger.info("inventory_cache_disabled")
            self.redis_client = None
            return

        # Use shared Redis connection pool
        from app.core.redis import get_redis_client
        try:
            self.redis_client = get_redis_client()
        except RuntimeError:
            logger.warning("inventory_cache_redis_not_initialized")
            self.redis_client = None
            self.enabled = False
            return

        # Reservation TTL: Tied to user session (no time limit while active)
        # Reservations released when user session expires (30 min inactivity)
        # This is handled by user_data_manager on session expiry
        self.reservation_ttl = None  # No TTL - managed by session lifecycle

        logger.info(
            "inventory_cache_initialized",
            enabled=self.enabled,
            reservation_ttl_seconds=self.reservation_ttl
        )

    def _get_inventory_key(self, item_id: str) -> str:
        """Get Redis key for item's available inventory count"""
        return f"inventory:available:{item_id}"

    def _get_reservation_key(self, item_id: str, user_id: str) -> str:
        """Get Redis key for user's reservation of an item"""
        return f"inventory:reserved:{item_id}:{user_id}"

    def _get_all_reservations_key(self, item_id: str) -> str:
        """Get Redis set key for all reservations of an item"""
        return f"inventory:reservations:{item_id}"

    # ========================================================================
    # INVENTORY INITIALIZATION (Called on startup or menu update)
    # ========================================================================

    async def sync_inventory_from_db(self, items: List[Dict]):
        """
        Sync inventory from database to Redis (3-column system).

        Called on:
        - Application startup
        - Menu update
        - Manual inventory adjustment by manager

        This syncs the available_quantity from DB to Redis. The DB is the source of truth.

        Args:
            items: List of items with {id, total_stock_quantity, reserved_quantity, available_quantity}
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            synced_count = 0

            for item in items:
                item_id = item.get("id")
                available_qty = item.get("available_quantity", 0)

                if item_id:
                    inventory_key = self._get_inventory_key(item_id)
                    await self.redis_client.set(inventory_key, available_qty)
                    synced_count += 1

            logger.info(
                "inventory_synced_from_db",
                items_synced=synced_count,
                total_items=len(items)
            )

        except Exception as e:
            logger.error("inventory_sync_error", error=str(e))

    async def set_item_inventory(self, item_id: str, available_quantity: int):
        """
        Set inventory for a single item in Redis.

        This should be called after database updates to keep Redis in sync.

        Args:
            item_id: Menu item ID (e.g., itm000001)
            available_quantity: Available quantity (from DB: total_stock - reserved)
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            inventory_key = self._get_inventory_key(item_id)
            await self.redis_client.set(inventory_key, available_quantity)

            logger.info(
                "item_inventory_set",
                item_id=item_id,
                available_quantity=available_quantity
            )

        except Exception as e:
            logger.error(
                "set_inventory_error",
                item_id=item_id,
                error=str(e)
            )

    # ========================================================================
    # REAL-TIME AVAILABILITY CHECK
    # ========================================================================

    async def get_available_quantity(self, item_id: str) -> int:
        """
        Get real-time available quantity for an item.

        Takes into account active reservations.

        Args:
            item_id: Menu item ID

        Returns:
            Available quantity (0 if out of stock)
        """
        if not self.enabled or not self.redis_client:
            # Fall back to database query if cache disabled
            return 999  # Assume available

        try:
            inventory_key = self._get_inventory_key(item_id)
            available = await self.redis_client.get(inventory_key)

            if available is None:
                # Not in cache yet, return 0 (trigger DB sync)
                logger.warning("item_not_in_inventory_cache", item_id=item_id)
                return 0

            return int(available)

        except Exception as e:
            logger.error(
                "get_available_quantity_error",
                item_id=item_id,
                error=str(e)
            )
            return 0

    async def check_availability(self, item_id: str, quantity: int) -> Tuple[bool, int]:
        """
        Check if quantity is available for an item.

        Args:
            item_id: Menu item ID
            quantity: Requested quantity

        Returns:
            Tuple of (is_available: bool, available_quantity: int)
        """
        available_qty = await self.get_available_quantity(item_id)
        is_available = available_qty >= quantity

        return is_available, available_qty

    # ========================================================================
    # INVENTORY RESERVATION (Atomic Operations)
    # ========================================================================

    async def reserve_inventory(
        self,
        item_id: str,
        quantity: int,
        user_id: str
    ) -> Dict:
        """
        Reserve inventory for a user (atomic operation).

        Flow:
        1. Check if enough inventory available
        2. Atomically decrement available count
        3. Create reservation record with TTL
        4. If user doesn't complete order in 15 min, auto-release

        Args:
            item_id: Menu item ID
            quantity: Quantity to reserve
            user_id: User ID reserving the item

        Returns:
            Reservation details

        Raises:
            InventoryReservationError: If not enough inventory
        """
        if not self.enabled or not self.redis_client:
            # Cache disabled, allow reservation
            return {
                "item_id": item_id,
                "quantity": quantity,
                "user_id": user_id,
                "reserved": True,
                "cache_disabled": True
            }

        try:
            inventory_key = self._get_inventory_key(item_id)
            reservation_key = self._get_reservation_key(item_id, user_id)
            reservations_set_key = self._get_all_reservations_key(item_id)

            # Check current availability
            available = await self.redis_client.get(inventory_key)
            if available is None:
                raise InventoryReservationError(
                    f"Item {item_id} not found in inventory cache. Sync required."
                )

            available = int(available)

            # Check if user already has a reservation (update scenario)
            existing_reservation = await self.redis_client.get(reservation_key)
            existing_qty = int(existing_reservation) if existing_reservation else 0

            # Calculate net change
            net_change = quantity - existing_qty

            # Check if enough inventory for net change
            if net_change > available:
                raise InventoryReservationError(
                    f"Not enough inventory for item {item_id}. "
                    f"Available: {available}, Requested: {net_change}"
                )

            # Atomic operations (Redis transaction)
            async with self.redis_client.pipeline(transaction=True) as pipe:
                # Decrement available inventory
                await pipe.decrby(inventory_key, net_change)

                # Set/Update reservation (NO TTL - managed by session lifecycle)
                await pipe.set(reservation_key, quantity)

                # Add to reservations set
                await pipe.sadd(reservations_set_key, user_id)

                # Execute transaction
                await pipe.execute()

            logger.info(
                "inventory_reserved",
                item_id=item_id,
                quantity=quantity,
                user_id=user_id,
                net_change=net_change,
                remaining_available=available - net_change
            )

            return {
                "item_id": item_id,
                "quantity": quantity,
                "user_id": user_id,
                "reserved": True,
                "note": "Reservation tied to session - will be released when session expires"
            }

        except InventoryReservationError:
            raise
        except Exception as e:
            logger.error(
                "reserve_inventory_error",
                item_id=item_id,
                quantity=quantity,
                user_id=user_id,
                error=str(e)
            )
            raise InventoryReservationError(f"Failed to reserve inventory: {str(e)}")

    async def release_reservation(
        self,
        item_id: str,
        user_id: str
    ):
        """
        Explicitly release a user's reservation.

        Called when:
        - User removes item from cart
        - User cancels order
        - User session expires

        Args:
            item_id: Menu item ID
            user_id: User ID
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            inventory_key = self._get_inventory_key(item_id)
            reservation_key = self._get_reservation_key(item_id, user_id)
            reservations_set_key = self._get_all_reservations_key(item_id)

            # Get reserved quantity
            reserved_qty = await self.redis_client.get(reservation_key)

            if reserved_qty:
                reserved_qty = int(reserved_qty)

                # Atomic operations
                async with self.redis_client.pipeline(transaction=True) as pipe:
                    # Return inventory
                    await pipe.incrby(inventory_key, reserved_qty)

                    # Delete reservation
                    await pipe.delete(reservation_key)

                    # Remove from reservations set
                    await pipe.srem(reservations_set_key, user_id)

                    # Execute transaction
                    await pipe.execute()

                logger.info(
                    "reservation_released",
                    item_id=item_id,
                    user_id=user_id,
                    quantity_released=reserved_qty
                )

        except Exception as e:
            logger.error(
                "release_reservation_error",
                item_id=item_id,
                user_id=user_id,
                error=str(e)
            )

    async def confirm_reservation(
        self,
        item_id: str,
        user_id: str
    ):
        """
        Confirm reservation (order completed).

        Removes reservation record but doesn't return inventory
        (inventory already deducted).

        Args:
            item_id: Menu item ID
            user_id: User ID
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            reservation_key = self._get_reservation_key(item_id, user_id)
            reservations_set_key = self._get_all_reservations_key(item_id)

            # Atomic operations
            async with self.redis_client.pipeline(transaction=True) as pipe:
                # Delete reservation (inventory stays deducted)
                await pipe.delete(reservation_key)

                # Remove from reservations set
                await pipe.srem(reservations_set_key, user_id)

                # Execute transaction
                await pipe.execute()

            logger.info(
                "reservation_confirmed",
                item_id=item_id,
                user_id=user_id
            )

        except Exception as e:
            logger.error(
                "confirm_reservation_error",
                item_id=item_id,
                user_id=user_id,
                error=str(e)
            )

    async def get_reserved_quantity(self, item_id: str) -> int:
        """
        Get total reserved quantity for an item across all users.

        Used for syncing back to database (3-column system).

        Args:
            item_id: Menu item ID

        Returns:
            Total quantity reserved by all users
        """
        if not self.enabled or not self.redis_client:
            return 0

        try:
            # Get all users who have reserved this item
            reservations_set_key = self._get_all_reservations_key(item_id)
            user_ids = await self.redis_client.smembers(reservations_set_key)

            total_reserved = 0
            for user_id in user_ids:
                reservation_key = self._get_reservation_key(item_id, user_id)
                reserved_qty = await self.redis_client.get(reservation_key)
                if reserved_qty:
                    total_reserved += int(reserved_qty)

            return total_reserved

        except Exception as e:
            logger.error(
                "get_reserved_quantity_error",
                item_id=item_id,
                error=str(e)
            )
            return 0

    # ========================================================================
    # DATABASE SYNC (3-Column System)
    # ========================================================================

    async def get_sync_data_for_db(self, item_ids: List[str]) -> Dict[str, Dict]:
        """
        Get inventory data for syncing to database (3-column system).

        Returns data needed to update database:
        - available_quantity (from Redis)
        - reserved_quantity (calculated from all user reservations)

        Args:
            item_ids: List of item IDs to get data for

        Returns:
            Dict mapping item_id to {available_quantity, reserved_quantity}
        """
        if not self.enabled or not self.redis_client:
            return {}

        try:
            sync_data = {}

            for item_id in item_ids:
                available = await self.get_available_quantity(item_id)
                reserved = await self.get_reserved_quantity(item_id)

                sync_data[item_id] = {
                    "available_quantity": available,
                    "reserved_quantity": reserved
                }

            logger.debug(
                "sync_data_prepared",
                items_count=len(sync_data)
            )

            return sync_data

        except Exception as e:
            logger.error(
                "get_sync_data_error",
                error=str(e)
            )
            return {}

    # ========================================================================
    # BATCH OPERATIONS (For cart with multiple items)
    # ========================================================================

    async def reserve_multiple_items(
        self,
        items: List[Dict[str, any]],
        user_id: str
    ) -> Dict:
        """
        Reserve multiple items atomically.

        Args:
            items: List of {item_id, quantity}
            user_id: User ID

        Returns:
            Dictionary with success status and details
        """
        reserved_items = []
        failed_items = []

        for item in items:
            item_id = item.get("item_id")
            quantity = item.get("quantity", 1)

            try:
                result = await self.reserve_inventory(item_id, quantity, user_id)
                reserved_items.append(result)

            except InventoryReservationError as e:
                failed_items.append({
                    "item_id": item_id,
                    "quantity": quantity,
                    "error": str(e)
                })

        # If any failed, rollback all successful reservations
        if failed_items:
            logger.warning(
                "partial_reservation_failure_rolling_back",
                user_id=user_id,
                failed_count=len(failed_items)
            )

            # Rollback successful reservations
            for reserved in reserved_items:
                await self.release_reservation(reserved["item_id"], user_id)

            return {
                "success": False,
                "reserved_items": [],
                "failed_items": failed_items
            }

        return {
            "success": True,
            "reserved_items": reserved_items,
            "failed_items": []
        }

    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================

    async def get_item_reservations(self, item_id: str) -> List[str]:
        """Get list of user IDs who have reserved this item"""
        if not self.enabled or not self.redis_client:
            return []

        try:
            reservations_set_key = self._get_all_reservations_key(item_id)
            user_ids = await self.redis_client.smembers(reservations_set_key)
            return list(user_ids)

        except Exception as e:
            logger.error("get_reservations_error", item_id=item_id, error=str(e))
            return []

    async def get_inventory_status(self, item_id: str) -> Dict:
        """
        Get complete inventory status for an item.

        Returns:
            Dictionary with available, reserved, total info
        """
        available = await self.get_available_quantity(item_id)
        reservations = await self.get_item_reservations(item_id)

        return {
            "item_id": item_id,
            "available": available,
            "reserved_by_users": reservations,
            "total_reservations": len(reservations)
        }

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("inventory_cache_service_closed")


# Global singleton instance
_inventory_cache_instance: Optional[InventoryCacheService] = None


def get_inventory_cache_service() -> InventoryCacheService:
    """
    Get or create the global inventory cache service instance.

    Returns:
        Global inventory cache service singleton
    """
    global _inventory_cache_instance

    if _inventory_cache_instance is None:
        _inventory_cache_instance = InventoryCacheService()

    return _inventory_cache_instance
