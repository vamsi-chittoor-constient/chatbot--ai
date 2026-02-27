"""
Menu Cache Service
===================
Caches full menu item data in Redis for fast access without database queries.

Architecture:
- Redis key: menu:item:{item_id}
- Stores: id, name, price, category, description, dietary info
- Loaded on startup, synced on menu updates
- Used by cart tools to avoid database queries

Flow:
1. Startup → Load all menu items from DB to Redis
2. Cart operations → Get item data from Redis (no DB query)
3. Menu update → Refresh specific items in Redis
"""

import os
from typing import Optional, Dict, List
from datetime import datetime
import structlog
import json

from app.features.food_ordering.models import MenuItem, MenuCategory, MenuItemCategoryMapping, MenuItemAvailabilitySchedule
from app.core.database import get_db_session
from app.core.redis import get_redis_client
from sqlalchemy import select
from sqlalchemy.orm import selectinload

logger = structlog.get_logger(__name__)


class MenuCacheService:
    """
    Manages Redis cache of full menu item data.

    Features:
    - Fast lookups without database queries
    - Automatic sync on startup
    - Selective refresh on menu updates
    - JSON storage for rich data
    """

    def __init__(self):
        """Initialize Redis connection for menu caching"""
        self.enabled = os.getenv("ENABLE_MENU_CACHE", "true").lower() == "true"

        if not self.enabled:
            logger.info("menu_cache_disabled")
            self.redis_client = None
            return

        # Use shared Redis connection pool
        try:
            self.redis_client = get_redis_client()
        except RuntimeError:
            logger.warning("menu_cache_redis_not_initialized")
            self.redis_client = None
            self.enabled = False
            return

        # Cache TTL: None (indefinite, manually refreshed)
        # Menu data doesn't expire - it's updated on menu changes
        self.cache_ttl = None

        logger.info("menu_cache_initialized", enabled=self.enabled, using_shared_pool=True)

    def _get_menu_item_key(self, item_id: str) -> str:
        """Get Redis key for menu item"""
        return f"menu:item:{item_id}"

    def _get_all_menu_items_key(self) -> str:
        """Get Redis key for set of all menu item IDs"""
        return "menu:items:all"

    def _get_category_key(self, category_id: str) -> str:
        """Get Redis key for category"""
        return f"menu:category:{category_id}"

    def _get_all_categories_key(self) -> str:
        """Get Redis key for set of all category IDs"""
        return "menu:categories:all"

    def _get_category_items_key(self, category_id: str) -> str:
        """Get Redis key for set of item IDs in a category"""
        return f"menu:category:{category_id}:items"

    # ========================================================================
    # LOAD MENU DATA FROM DATABASE
    # ========================================================================

    async def load_menu_from_db(self):
        """
        Load all menu items and categories from database to Redis.

        Called on:
        - Application startup
        - Full menu refresh

        Caches:
        - Items: id, name, price, category_id, category_name (denormalized)
        - Categories: id, name, description, display_order
        - Category-to-items mappings for efficient filtering
        """
        if not self.enabled or not self.redis_client:
            logger.warning("menu_cache_disabled_skipping_load")
            return

        logger.info("menu_cache_load_started")

        try:
            async with get_db_session() as db_session:
                # Load all categories first
                categories_result = await db_session.execute(
                    select(MenuCategory).order_by(MenuCategory.menu_category_rank)
                )
                categories = categories_result.scalars().all()

                # Create category lookup map
                category_map = {str(cat.menu_category_id): cat for cat in categories}

                # Get all active menu items with their category mappings and availability schedules
                items_result = await db_session.execute(
                    select(MenuItem)
                    .options(
                        selectinload(MenuItem.category_mappings),
                        selectinload(MenuItem.availability_schedules).selectinload(MenuItemAvailabilitySchedule.meal_type)
                    )
                    .where(MenuItem.menu_item_in_stock == True)
                    .where(MenuItem.is_deleted == False)
                )
                items = items_result.scalars().all()

                # Cache everything using pipeline
                cached_items = 0
                cached_categories = 0
                item_ids = []
                category_ids = []
                category_items_map = {}  # category_id -> list of item_ids

                async with self.redis_client.pipeline(transaction=False) as pipe:
                    # Cache categories
                    for category in categories:
                        cat_id = str(category.menu_category_id)
                        category_key = self._get_category_key(cat_id)
                        category_ids.append(cat_id)

                        category_data = {
                            "id": cat_id,
                            "name": category.menu_category_name,
                            "description": category.menu_category_description or "",
                            "display_order": category.menu_category_rank,
                            "cached_at": datetime.now().isoformat()
                        }

                        await pipe.set(category_key, json.dumps(category_data))
                        cached_categories += 1

                        # Initialize category items list
                        category_items_map[cat_id] = []

                    # Cache items with denormalized category_name
                    for item in items:
                        item_id = str(item.menu_item_id)
                        item_key = self._get_menu_item_key(item_id)
                        item_ids.append(item_id)

                        # Get category from mapping table
                        category_name = "Unknown"
                        category_id = None
                        if item.category_mappings:
                            first_mapping = item.category_mappings[0]
                            category_id = str(first_mapping.menu_category_id)
                            if category_id in category_map:
                                category_name = category_map[category_id].menu_category_name

                        # Derive availability_time from availability_schedules + meal_type
                        meal_timings = []
                        if item.availability_schedules:
                            for schedule in item.availability_schedules:
                                if schedule.meal_type and not schedule.is_deleted:
                                    meal_name = schedule.meal_type.meal_type_name.lower()
                                    if meal_name not in meal_timings:
                                        meal_timings.append(meal_name)
                        # None = no restrictions (always available), "all_day" = explicit all day
                        availability_time = ",".join(meal_timings) if meal_timings else None

                        item_data = {
                            "id": item_id,
                            "name": item.menu_item_name,
                            "price": float(item.menu_item_price),
                            "category_id": category_id,
                            "category_name": category_name,
                            "description": item.menu_item_description or "",
                            "is_available": item.menu_item_in_stock,
                            "is_popular": item.menu_item_is_recommended or False,
                            "spice_level": item.menu_item_spice_level or "",
                            "calories": item.menu_item_calories or 0,
                            "prep_time_minutes": item.menu_item_minimum_preparation_time or 0,
                            "availability_time": availability_time,
                            "cached_at": datetime.now().isoformat()
                        }

                        await pipe.set(item_key, json.dumps(item_data))
                        cached_items += 1

                        # Add item to category mapping
                        if category_id and category_id in category_items_map:
                            category_items_map[category_id].append(item_id)

                    # Store set of all item IDs
                    await pipe.delete(self._get_all_menu_items_key())
                    if item_ids:
                        await pipe.sadd(self._get_all_menu_items_key(), *item_ids)

                    # Store set of all category IDs
                    await pipe.delete(self._get_all_categories_key())
                    if category_ids:
                        await pipe.sadd(self._get_all_categories_key(), *category_ids)

                    # Store category-to-items mappings
                    for cat_id, item_id_list in category_items_map.items():
                        category_items_key = self._get_category_items_key(cat_id)
                        await pipe.delete(category_items_key)
                        if item_id_list:
                            await pipe.sadd(category_items_key, *item_id_list)

                    # Execute pipeline
                    await pipe.execute()

                logger.info(
                    "menu_cache_load_completed",
                    items_cached=cached_items,
                    categories_cached=cached_categories,
                    total_items=len(items),
                    total_categories=len(categories)
                )

        except Exception as e:
            logger.error("menu_cache_load_error", error=str(e), exc_info=True)

    async def refresh_item(self, item_id: str):
        """
        Refresh a single menu item in cache.

        Called when:
        - Item updated by manager
        - Item added/removed from menu

        Args:
            item_id: Menu item ID to refresh
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            async with get_db_session() as db_session:
                # Get item from database with category mappings and availability schedules
                result = await db_session.execute(
                    select(MenuItem)
                    .options(
                        selectinload(MenuItem.category_mappings),
                        selectinload(MenuItem.availability_schedules).selectinload(MenuItemAvailabilitySchedule.meal_type)
                    )
                    .where(MenuItem.menu_item_id == item_id)
                )
                item = result.scalar_one_or_none()

                if not item:
                    # Item deleted - remove from cache
                    await self.remove_item(item_id)
                    logger.info("menu_item_removed_from_cache", item_id=item_id)
                    return

                # Get category name from mapping
                category_name = "Unknown"
                category_id = None
                if item.category_mappings:
                    first_mapping = item.category_mappings[0]
                    category_id = str(first_mapping.menu_category_id)

                    # Fetch category name
                    cat_result = await db_session.execute(
                        select(MenuCategory).where(MenuCategory.menu_category_id == first_mapping.menu_category_id)
                    )
                    category = cat_result.scalar_one_or_none()
                    if category:
                        category_name = category.menu_category_name

                # Derive availability_time from availability_schedules + meal_type
                meal_timings = []
                if item.availability_schedules:
                    for schedule in item.availability_schedules:
                        if schedule.meal_type and not schedule.is_deleted:
                            meal_name = schedule.meal_type.meal_type_name.lower()
                            if meal_name not in meal_timings:
                                meal_timings.append(meal_name)
                availability_time = ",".join(meal_timings) if meal_timings else None

                # Update cache
                item_key = self._get_menu_item_key(str(item.menu_item_id))

                item_data = {
                    "id": str(item.menu_item_id),
                    "name": item.menu_item_name,
                    "price": float(item.menu_item_price),
                    "category_id": category_id,
                    "category_name": category_name,
                    "description": item.menu_item_description or "",
                    "is_available": item.menu_item_in_stock,
                    "is_popular": item.menu_item_is_recommended or False,
                    "spice_level": item.menu_item_spice_level or "",
                    "calories": item.menu_item_calories or 0,
                    "prep_time_minutes": item.menu_item_minimum_preparation_time or 0,
                    "availability_time": availability_time,
                    "cached_at": datetime.now().isoformat()
                }

                async with self.redis_client.pipeline(transaction=False) as pipe:
                    # Update item cache
                    await pipe.set(item_key, json.dumps(item_data))

                    # Add to all items set
                    await pipe.sadd(self._get_all_menu_items_key(), str(item.menu_item_id))

                    # Add to category items set
                    if category_id:
                        await pipe.sadd(self._get_category_items_key(category_id), str(item.menu_item_id))

                    await pipe.execute()

                logger.info("menu_item_refreshed", item_id=item_id, item_name=item.menu_item_name)

        except Exception as e:
            logger.error(
                "menu_item_refresh_error",
                item_id=item_id,
                error=str(e),
                exc_info=True
            )

    async def remove_item(self, item_id: str):
        """
        Remove an item from cache.

        Args:
            item_id: Item ID to remove
        """
        if not self.enabled or not self.redis_client:
            return

        try:
            item_key = self._get_menu_item_key(item_id)

            async with self.redis_client.pipeline(transaction=False) as pipe:
                await pipe.delete(item_key)
                await pipe.srem(self._get_all_menu_items_key(), item_id)
                await pipe.execute()

            logger.info("menu_item_removed", item_id=item_id)

        except Exception as e:
            logger.error("menu_item_remove_error", item_id=item_id, error=str(e))

    # ========================================================================
    # GET MENU DATA FROM CACHE
    # ========================================================================

    async def get_item(self, item_id: str) -> Optional[Dict]:
        """
        Get menu item data from cache.

        Args:
            item_id: Menu item ID

        Returns:
            Dict with item data or None if not found
        """
        if not self.enabled or not self.redis_client:
            # Fall back to database query if cache disabled
            return await self._get_item_from_db(item_id)

        try:
            item_key = self._get_menu_item_key(item_id)
            item_json = await self.redis_client.get(item_key)

            if not item_json:
                # Cache miss - try loading from database
                logger.warning("menu_cache_miss", item_id=item_id)
                await self.refresh_item(item_id)

                # Try again
                item_json = await self.redis_client.get(item_key)
                if not item_json:
                    return None

            return json.loads(item_json)

        except Exception as e:
            logger.error(
                "menu_item_get_error",
                item_id=item_id,
                error=str(e)
            )
            # Fall back to database
            return await self._get_item_from_db(item_id)

    async def _get_item_from_db(self, item_id: str) -> Optional[Dict]:
        """
        Fallback: Get item from database if cache unavailable.

        Args:
            item_id: Menu item ID

        Returns:
            Dict with item data or None
        """
        try:
            async with get_db_session() as db_session:
                result = await db_session.execute(
                    select(MenuItem)
                    .options(selectinload(MenuItem.category_mappings))
                    .where(MenuItem.menu_item_id == item_id)
                )
                item = result.scalar_one_or_none()

                if not item:
                    return None

                # Get category from mapping
                category_id = None
                if item.category_mappings:
                    category_id = str(item.category_mappings[0].menu_category_id)

                return {
                    "id": str(item.menu_item_id),
                    "name": item.menu_item_name,
                    "price": float(item.menu_item_price),
                    "category_id": category_id,
                    "description": item.menu_item_description or "",
                    "is_available": item.menu_item_in_stock,
                    "is_popular": item.menu_item_is_recommended or False,
                    "spice_level": item.menu_item_spice_level or "",
                    "calories": item.menu_item_calories or 0
                }

        except Exception as e:
            logger.error("database_fallback_error", item_id=item_id, error=str(e))
            return None

    async def get_all_item_ids(self) -> List[str]:
        """
        Get list of all menu item IDs in cache.

        Returns:
            List of item IDs
        """
        if not self.enabled or not self.redis_client:
            return []

        try:
            all_items_key = self._get_all_menu_items_key()
            item_ids = await self.redis_client.smembers(all_items_key)
            return list(item_ids)

        except Exception as e:
            logger.error("get_all_item_ids_error", error=str(e))
            return []

    async def get_category(self, category_id: str) -> Optional[Dict]:
        """
        Get category data from cache.

        Args:
            category_id: Category ID

        Returns:
            Dict with category data or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            category_key = self._get_category_key(category_id)
            category_json = await self.redis_client.get(category_key)

            if not category_json:
                logger.warning("category_cache_miss", category_id=category_id)
                return None

            return json.loads(category_json)

        except Exception as e:
            logger.error("category_get_error", category_id=category_id, error=str(e))
            return None

    async def get_all_categories(self) -> List[Dict]:
        """
        Get all categories from cache, sorted by display_order.

        Returns:
            List of category dicts
        """
        if not self.enabled or not self.redis_client:
            return []

        try:
            # Get all category IDs
            all_categories_key = self._get_all_categories_key()
            category_ids = await self.redis_client.smembers(all_categories_key)

            if not category_ids:
                return []

            # Fetch all category data
            categories = []
            async with self.redis_client.pipeline(transaction=False) as pipe:
                for category_id in category_ids:
                    await pipe.get(self._get_category_key(category_id))

                results = await pipe.execute()

            for category_json in results:
                if category_json:
                    categories.append(json.loads(category_json))

            # Sort by display_order
            categories.sort(key=lambda c: c.get("display_order", 0))

            return categories

        except Exception as e:
            logger.error("get_all_categories_error", error=str(e))
            return []

    async def get_items_by_category(self, category_id: str) -> List[Dict]:
        """
        Get all items in a category from cache.

        Args:
            category_id: Category ID

        Returns:
            List of item dicts
        """
        if not self.enabled or not self.redis_client:
            return []

        try:
            # Get item IDs in this category
            category_items_key = self._get_category_items_key(category_id)
            item_ids = await self.redis_client.smembers(category_items_key)

            if not item_ids:
                return []

            # Fetch all item data
            items = []
            async with self.redis_client.pipeline(transaction=False) as pipe:
                for item_id in item_ids:
                    await pipe.get(self._get_menu_item_key(item_id))

                results = await pipe.execute()

            for item_json in results:
                if item_json:
                    items.append(json.loads(item_json))

            return items

        except Exception as e:
            logger.error("get_items_by_category_error", category_id=category_id, error=str(e))
            return []

    async def get_all_items(self) -> List[Dict]:
        """
        Get all menu items from cache.

        Returns:
            List of item dicts
        """
        if not self.enabled or not self.redis_client:
            return []

        try:
            item_ids = await self.get_all_item_ids()

            if not item_ids:
                return []

            # Fetch all item data
            items = []
            async with self.redis_client.pipeline(transaction=False) as pipe:
                for item_id in item_ids:
                    await pipe.get(self._get_menu_item_key(item_id))

                results = await pipe.execute()

            for item_json in results:
                if item_json:
                    items.append(json.loads(item_json))

            return items

        except Exception as e:
            logger.error("get_all_items_error", error=str(e))
            return []

    # ========================================================================
    # STATISTICS & MONITORING
    # ========================================================================

    async def get_cache_stats(self) -> Dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}

        try:
            item_ids = await self.get_all_item_ids()

            return {
                "enabled": True,
                "total_items_cached": len(item_ids),
                "cache_keys_used": len(item_ids) + 1  # items + all_items_set
            }

        except Exception as e:
            logger.error("cache_stats_error", error=str(e))
            return {"enabled": True, "error": str(e)}

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("menu_cache_service_closed")


# Global singleton instance
_menu_cache_instance: Optional[MenuCacheService] = None


def get_menu_cache_service() -> MenuCacheService:
    """
    Get or create the global menu cache service instance.

    Returns:
        Global menu cache service singleton
    """
    global _menu_cache_instance

    if _menu_cache_instance is None:
        _menu_cache_instance = MenuCacheService()

    return _menu_cache_instance
