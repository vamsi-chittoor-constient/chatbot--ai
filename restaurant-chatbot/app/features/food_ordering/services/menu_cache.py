"""
Menu Cache Service
===================
Selective Redis caching for multi-tenant menu data.

**Multi-Tenant Strategy:**
- Cache ONLY lightweight data (hierarchy)
- Query MenuItemEnrichedView directly for item details
- ~3KB per tenant = 3MB for 1000 tenants (sustainable)

**What we cache:**
- Menu hierarchy (Section → Category → SubCategory)
- Popular item IDs

**What we DON'T cache:**
- Full menu item details (query from view instead)
- Search results (compute on demand)

Architecture:
- Redis keys: tenant:{restaurant_id}:menu:hierarchy
- TTL: 24 hours, refresh on access
- Loaded on first request (lazy loading)
"""

import os
from typing import Optional, Dict, List, Any
from datetime import datetime
from uuid import UUID
import structlog
import redis.asyncio as redis
import json

from app.features.food_ordering.models import (
    MenuSection, MenuCategory, MenuSubCategory,
    MenuItemEnrichedView
)
from app.core.database import get_db_session
from sqlalchemy import select, func

logger = structlog.get_logger(__name__)


class MenuCacheService:
    """
    Manages selective Redis cache of menu hierarchy for multi-tenant.

    Features:
    - Lightweight caching (hierarchy only)
    - Multi-tenant safe (restaurant_id scoping)
    - Lazy loading (cache on first request)
    - 24-hour TTL with auto-refresh
    """

    def __init__(self):
        """Initialize Redis connection for menu caching"""
        self.enabled = os.getenv("ENABLE_MENU_CACHE", "true").lower() == "true"

        if not self.enabled:
            logger.info("menu_cache_disabled")
            self.redis_client = None
            return

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

        self.redis_client = redis.from_url(
            redis_url,
            encoding="utf-8",
            decode_responses=True
        )

        # Cache TTL: 24 hours
        self.cache_ttl = 86400  # 24 * 60 * 60

        logger.info("menu_cache_initialized", enabled=self.enabled, strategy="selective")

    def _get_hierarchy_key(self, restaurant_id: UUID) -> str:
        """Get Redis key for menu hierarchy"""
        return f"tenant:{restaurant_id}:menu:hierarchy"

    def _get_popular_items_key(self, restaurant_id: UUID) -> str:
        """Get Redis key for popular items list"""
        return f"tenant:{restaurant_id}:menu:popular_ids"

    async def get_hierarchy(self, restaurant_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get cached menu hierarchy for restaurant.

        Returns:
            Hierarchy dict or None if not cached
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._get_hierarchy_key(restaurant_id)
            cached = await self.redis_client.get(key)

            if cached:
                logger.debug("hierarchy_cache_hit", restaurant_id=str(restaurant_id))
                return json.loads(cached)

            logger.debug("hierarchy_cache_miss", restaurant_id=str(restaurant_id))
            return None

        except Exception as e:
            logger.error("hierarchy_cache_get_error", error=str(e), restaurant_id=str(restaurant_id))
            return None

    async def set_hierarchy(self, restaurant_id: UUID, hierarchy: Dict[str, Any]) -> bool:
        """
        Cache menu hierarchy for restaurant.

        Args:
            restaurant_id: Restaurant UUID
            hierarchy: Hierarchy dict to cache

        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._get_hierarchy_key(restaurant_id)
            await self.redis_client.setex(
                key,
                self.cache_ttl,
                json.dumps(hierarchy)
            )

            logger.info("hierarchy_cached", restaurant_id=str(restaurant_id))
            return True

        except Exception as e:
            logger.error("hierarchy_cache_set_error", error=str(e), restaurant_id=str(restaurant_id))
            return False

    async def load_hierarchy_from_db(self, restaurant_id: UUID) -> Dict[str, Any]:
        """
        Load menu hierarchy from database and cache it.

        Returns:
            Hierarchy dict (Section → Categories → SubCategories with counts)
        """
        async with get_db_session() as session:
            # Get all sections for restaurant
            sections_stmt = (
                select(MenuSection)
                .where(MenuSection.restaurant_id == restaurant_id)
                .where(MenuSection.is_deleted == False)
                .order_by(MenuSection.menu_section_rank)
            )
            sections_result = await session.execute(sections_stmt)
            sections = sections_result.scalars().all()

            hierarchy = []

            # Get all categories (not filtered by section since FK doesn't exist in current schema)
            categories_stmt = (
                select(MenuCategory)
                .where(MenuCategory.restaurant_id == restaurant_id)
                .where(MenuCategory.is_deleted == False)
                .order_by(MenuCategory.menu_category_rank)
            )
            categories_result = await session.execute(categories_stmt)
            all_categories = categories_result.scalars().all()

            for section in sections:

                section_data = {
                    "id": str(section.menu_section_id),
                    "name": section.menu_section_name,
                    "description": section.menu_section_description,
                    "categories": []
                }

                for category in all_categories:
                    # Get subcategories for this category
                    subcategories_stmt = (
                        select(MenuSubCategory)
                        .where(MenuSubCategory.category_id == category.menu_category_id)
                        .where(MenuSubCategory.is_deleted == False)
                        .order_by(MenuSubCategory.sub_category_rank)
                    )
                    subcategories_result = await session.execute(subcategories_stmt)
                    subcategories = subcategories_result.scalars().all()

                    # Count items in category
                    category_count_stmt = (
                        select(func.count(MenuItemEnrichedView.menu_item_id))
                        .where(MenuItemEnrichedView.restaurant_id == restaurant_id)
                        .where(MenuItemEnrichedView.categories.contains([category.menu_category_name]))
                        .where(MenuItemEnrichedView.is_deleted == False)
                    )
                    category_count_result = await session.execute(category_count_stmt)
                    category_count = category_count_result.scalar() or 0

                    category_data = {
                        "id": str(category.menu_category_id),
                        "name": category.menu_category_name,
                        "description": category.menu_category_description,
                        "item_count": category_count,
                        "subcategories": []
                    }

                    for subcategory in subcategories:
                        # Count items in subcategory
                        subcat_count_stmt = (
                            select(func.count(MenuItemEnrichedView.menu_item_id))
                            .where(MenuItemEnrichedView.restaurant_id == restaurant_id)
                            .where(MenuItemEnrichedView.subcategories.contains([subcategory.sub_category_name]))
                            .where(MenuItemEnrichedView.is_deleted == False)
                        )
                        subcat_count_result = await session.execute(subcat_count_stmt)
                        subcat_count = subcat_count_result.scalar() or 0

                        subcategory_data = {
                            "id": str(subcategory.menu_sub_category_id),
                            "name": subcategory.sub_category_name,
                            "description": subcategory.sub_category_description,
                            "item_count": subcat_count
                        }

                        category_data["subcategories"].append(subcategory_data)

                    section_data["categories"].append(category_data)

                hierarchy.append(section_data)

            # Cache the hierarchy
            await self.set_hierarchy(restaurant_id, {"sections": hierarchy})

            logger.info("hierarchy_loaded_from_db", restaurant_id=str(restaurant_id), sections=len(hierarchy))

            return {"sections": hierarchy}

    async def get_or_load_hierarchy(self, restaurant_id: UUID) -> Dict[str, Any]:
        """
        Get hierarchy from cache or load from DB.

        This is the main method to call for getting hierarchy.

        Returns:
            Hierarchy dict
        """
        # Try cache first
        cached = await self.get_hierarchy(restaurant_id)
        if cached:
            return cached

        # Cache miss - load from DB
        return await self.load_hierarchy_from_db(restaurant_id)

    async def invalidate_hierarchy(self, restaurant_id: UUID) -> bool:
        """
        Invalidate cached hierarchy for restaurant.

        Call this when menu structure changes (category/section updates).

        Returns:
            True if invalidated successfully
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._get_hierarchy_key(restaurant_id)
            await self.redis_client.delete(key)

            logger.info("hierarchy_cache_invalidated", restaurant_id=str(restaurant_id))
            return True

        except Exception as e:
            logger.error("hierarchy_cache_invalidate_error", error=str(e), restaurant_id=str(restaurant_id))
            return False

    async def get_popular_items(self, restaurant_id: UUID) -> Optional[List[str]]:
        """
        Get cached list of popular item IDs.

        Returns:
            List of item IDs or None if not cached
        """
        if not self.enabled or not self.redis_client:
            return None

        try:
            key = self._get_popular_items_key(restaurant_id)
            cached = await self.redis_client.get(key)

            if cached:
                logger.debug("popular_items_cache_hit", restaurant_id=str(restaurant_id))
                return json.loads(cached)

            logger.debug("popular_items_cache_miss", restaurant_id=str(restaurant_id))
            return None

        except Exception as e:
            logger.error("popular_items_cache_get_error", error=str(e), restaurant_id=str(restaurant_id))
            return None

    async def set_popular_items(self, restaurant_id: UUID, item_ids: List[str]) -> bool:
        """
        Cache list of popular item IDs.

        Args:
            restaurant_id: Restaurant UUID
            item_ids: List of popular item IDs

        Returns:
            True if cached successfully
        """
        if not self.enabled or not self.redis_client:
            return False

        try:
            key = self._get_popular_items_key(restaurant_id)
            await self.redis_client.setex(
                key,
                self.cache_ttl,
                json.dumps(item_ids)
            )

            logger.info("popular_items_cached", restaurant_id=str(restaurant_id), count=len(item_ids))
            return True

        except Exception as e:
            logger.error("popular_items_cache_set_error", error=str(e), restaurant_id=str(restaurant_id))
            return False

    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("menu_cache_closed")


# Singleton instance
_menu_cache_service = None


def get_menu_cache_service() -> MenuCacheService:
    """Get or create menu cache service singleton"""
    global _menu_cache_service
    if _menu_cache_service is None:
        _menu_cache_service = MenuCacheService()
    return _menu_cache_service
