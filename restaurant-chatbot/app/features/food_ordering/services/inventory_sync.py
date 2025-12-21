"""
Inventory Sync Service
=======================
Smart bidirectional sync between Redis (cache) and PostgreSQL (database).

Sync Strategy:
- Periodic: Every 5 minutes (full sync of all items)
- Event-based: On order completion (selective sync of ordered items)
- Event-based: On manager update (selective sync of updated items)
- Timer reset: Each event-based sync resets the 5-minute timer

Architecture:
- Redis  Database: Sync reserved_quantity and available_quantity
- Database  Redis: Sync after manager updates total_stock_quantity

Flow:
1. Order placed  Selective sync (only ordered items)
2. Manager updates stock  Selective sync (only updated items)
3. Timer reset on each event
4. Periodic full sync after 5 minutes of no events
"""

import asyncio
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.inventory_cache_service import get_inventory_cache_service
from app.features.food_ordering.models import MenuItem
from app.core.database import get_db_session

logger = structlog.get_logger(__name__)


class InventorySyncService:
    """
    Manages bidirectional sync between Redis cache and PostgreSQL database.

    Features:
    - Smart timer with reset on events
    - Selective sync for specific items (fast)
    - Full sync for all items (safety net)
    - Prevents redundant syncs
    """

    def __init__(self):
        """Initialize sync service"""
        self.inventory_cache = get_inventory_cache_service()

        # Sync interval: 5 minutes (300 seconds)
        self.sync_interval_seconds = 300

        # Timer management
        self._last_sync_time: Optional[datetime] = None
        self._sync_timer_task: Optional[asyncio.Task] = None
        self._running = False

        logger.info("inventory_sync_service_initialized")

    # ========================================================================
    # TIMER MANAGEMENT
    # ========================================================================

    def start_sync_timer(self):
        """
        Start the periodic sync timer.

        Should be called on application startup.
        """
        if self._sync_timer_task and not self._sync_timer_task.done():
            logger.warning("sync_timer_already_running")
            return

        self._running = True
        self._sync_timer_task = asyncio.create_task(self._sync_timer_loop())
        logger.info("sync_timer_started", interval_seconds=self.sync_interval_seconds)

    def stop_sync_timer(self):
        """Stop the periodic sync timer."""
        self._running = False
        if self._sync_timer_task:
            self._sync_timer_task.cancel()
        logger.info("sync_timer_stopped")

    def reset_sync_timer(self):
        """
        Reset the sync timer.

        Called after event-based syncs (order completion, manager update).
        """
        self._last_sync_time = datetime.now()
        logger.debug("sync_timer_reset", next_sync_in_seconds=self.sync_interval_seconds)

    async def _sync_timer_loop(self):
        """Background task that runs periodic full syncs."""
        logger.info("sync_timer_loop_started")

        try:
            while self._running:
                await asyncio.sleep(self.sync_interval_seconds)

                # Check if we need to sync
                if self._should_run_periodic_sync():
                    await self.sync_full()
                    self._last_sync_time = datetime.now()

        except asyncio.CancelledError:
            logger.info("sync_timer_loop_cancelled")
        except Exception as e:
            logger.error("sync_timer_loop_error", error=str(e), exc_info=True)

    def _should_run_periodic_sync(self) -> bool:
        """
        Check if periodic sync should run.

        Returns False if a recent event-based sync occurred (within interval).
        """
        if not self._last_sync_time:
            return True

        time_since_last_sync = datetime.now() - self._last_sync_time
        return time_since_last_sync.total_seconds() >= self.sync_interval_seconds

    # ========================================================================
    # FULL SYNC (All Items)
    # ========================================================================

    async def sync_full(self):
        """
        Full bidirectional sync of all items.

        Called:
        - Periodically (every 5 minutes with no events)
        - On application startup

        Syncs:
        - Redis  DB: reserved_quantity, available_quantity
        - DB  Redis: total_stock_quantity (if changed by manager)
        """
        logger.info("full_sync_started")

        try:
            async with get_db_session() as db_session:
                # Get all menu items from database
                result = await db_session.execute(
                    select(MenuItem).where(MenuItem.is_available == True)
                )
                all_items = result.scalars().all()

                item_ids = [item.id for item in all_items]

                # Get sync data from Redis
                sync_data = await self.inventory_cache.get_sync_data_for_db(item_ids)

                # Update database with Redis data
                updated_count = 0
                for item in all_items:
                    redis_data = sync_data.get(item.id)
                    if redis_data:
                        # Update reserved_quantity from Redis
                        item.reserved_quantity = redis_data["reserved_quantity"]

                        # Calculate and update available_quantity
                        # available = total_stock - reserved
                        new_available = item.total_stock_quantity - redis_data["reserved_quantity"]
                        item.available_quantity = max(0, new_available)

                        updated_count += 1

                await db_session.commit()

                logger.info(
                    "full_sync_completed",
                    total_items=len(all_items),
                    updated_count=updated_count
                )

                # Reset timer
                self.reset_sync_timer()

        except Exception as e:
            logger.error("full_sync_error", error=str(e), exc_info=True)

    # ========================================================================
    # SELECTIVE SYNC (Specific Items)
    # ========================================================================

    async def sync_items(self, item_ids: List[str], reason: str = "event"):
        """
        Selective sync of specific items only.

        Much faster than full sync. Called on:
        - Order completion (sync ordered items)
        - Manager update (sync updated items)

        Args:
            item_ids: List of item IDs to sync
            reason: Reason for sync (for logging)
        """
        if not item_ids:
            return

        logger.info(
            "selective_sync_started",
            item_count=len(item_ids),
            reason=reason
        )

        try:
            async with get_db_session() as db_session:
                # Get items from database
                result = await db_session.execute(
                    select(MenuItem).where(MenuItem.id.in_(item_ids))
                )
                items = result.scalars().all()

                # Get sync data from Redis
                sync_data = await self.inventory_cache.get_sync_data_for_db(item_ids)

                # Update database with Redis data
                for item in items:
                    redis_data = sync_data.get(item.id)
                    if redis_data:
                        # Update reserved_quantity from Redis
                        item.reserved_quantity = redis_data["reserved_quantity"]

                        # Calculate and update available_quantity
                        new_available = item.total_stock_quantity - redis_data["reserved_quantity"]
                        item.available_quantity = max(0, new_available)

                await db_session.commit()

                logger.info(
                    "selective_sync_completed",
                    item_count=len(items),
                    reason=reason
                )

                # Reset timer after event-based sync
                self.reset_sync_timer()

        except Exception as e:
            logger.error(
                "selective_sync_error",
                item_ids=item_ids,
                error=str(e),
                exc_info=True
            )

    # ========================================================================
    # ORDER COMPLETION SYNC
    # ========================================================================

    async def sync_after_order(self, order_items: List[Dict]):
        """
        Sync after order completion.

        Updates:
        - reserved_quantity (decreased, items left cart)
        - total_stock_quantity (decreased, items left kitchen)
        - available_quantity (recalculated)

        Args:
            order_items: List of {item_id, quantity} from completed order
        """
        if not order_items:
            return

        logger.info("order_completion_sync_started", items_count=len(order_items))

        try:
            async with get_db_session() as db_session:
                item_ids = [item["item_id"] for item in order_items]

                # Get items from database
                result = await db_session.execute(
                    select(MenuItem).where(MenuItem.id.in_(item_ids))
                )
                items = {item.id: item for item in result.scalars().all()}

                # Get current Redis state
                sync_data = await self.inventory_cache.get_sync_data_for_db(item_ids)

                # Update database
                for order_item in order_items:
                    item_id = order_item["item_id"]
                    quantity = order_item["quantity"]

                    db_item = items.get(item_id)
                    redis_data = sync_data.get(item_id)

                    if db_item and redis_data:
                        # Deduct from total_stock (item left kitchen)
                        db_item.total_stock_quantity = max(0, db_item.total_stock_quantity - quantity)

                        # Update reserved from Redis (should already be reduced)
                        db_item.reserved_quantity = redis_data["reserved_quantity"]

                        # Recalculate available
                        db_item.available_quantity = max(0, db_item.total_stock_quantity - db_item.reserved_quantity)

                        logger.debug(
                            "order_item_synced",
                            item_id=item_id,
                            quantity_sold=quantity,
                            new_total=db_item.total_stock_quantity,
                            new_available=db_item.available_quantity
                        )

                await db_session.commit()

                logger.info("order_completion_sync_completed")

                # Reset timer
                self.reset_sync_timer()

        except Exception as e:
            logger.error("order_sync_error", error=str(e), exc_info=True)

    # ========================================================================
    # MANAGER UPDATE SYNC
    # ========================================================================

    async def sync_after_manager_update(self, item_id: str, new_total_stock: int):
        """
        Sync after manager updates stock.

        Flow:
        1. Manager updates total_stock_quantity in DB
        2. Read reserved_quantity from Redis
        3. Calculate new available_quantity
        4. Update Redis with new available_quantity

        Args:
            item_id: Item ID that was updated
            new_total_stock: New total stock quantity set by manager
        """
        logger.info(
            "manager_update_sync_started",
            item_id=item_id,
            new_total_stock=new_total_stock
        )

        try:
            # Get current reserved quantity from Redis
            reserved_qty = await self.inventory_cache.get_reserved_quantity(item_id)

            # Calculate new available
            new_available = max(0, new_total_stock - reserved_qty)

            # Update Redis with new available quantity
            await self.inventory_cache.set_item_inventory(item_id, new_available)

            logger.info(
                "manager_update_sync_completed",
                item_id=item_id,
                total_stock=new_total_stock,
                reserved=reserved_qty,
                available=new_available
            )

            # Reset timer
            self.reset_sync_timer()

        except Exception as e:
            logger.error(
                "manager_update_sync_error",
                item_id=item_id,
                error=str(e),
                exc_info=True
            )

    # ========================================================================
    # STARTUP SYNC
    # ========================================================================

    async def sync_on_startup(self):
        """
        Initial sync on application startup.

        Loads all inventory from database to Redis.
        """
        logger.info("startup_sync_initiated")

        try:
            async with get_db_session() as db_session:
                # Get all active menu items
                result = await db_session.execute(
                    select(MenuItem).where(MenuItem.is_available == True)
                )
                items = result.scalars().all()

                # Prepare data for Redis
                items_data = [
                    {
                        "id": item.id,
                        "total_stock_quantity": item.total_stock_quantity,
                        "reserved_quantity": item.reserved_quantity,
                        "available_quantity": item.available_quantity
                    }
                    for item in items
                ]

                # Sync to Redis
                await self.inventory_cache.sync_inventory_from_db(items_data)

                logger.info(
                    "startup_sync_completed",
                    items_count=len(items_data)
                )

                # Set initial sync time
                self._last_sync_time = datetime.now()

        except Exception as e:
            logger.error("startup_sync_error", error=str(e), exc_info=True)


# Global singleton instance
_inventory_sync_instance: Optional[InventorySyncService] = None


def get_inventory_sync_service() -> InventorySyncService:
    """
    Get or create the global inventory sync service instance.

    Returns:
        Global inventory sync service singleton
    """
    global _inventory_sync_instance

    if _inventory_sync_instance is None:
        _inventory_sync_instance = InventorySyncService()

    return _inventory_sync_instance
