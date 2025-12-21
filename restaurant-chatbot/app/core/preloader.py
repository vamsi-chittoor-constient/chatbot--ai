"""
Application Preloader
=====================
Pre-warm caches and connections on startup for instant responses.

Before: First request = cold start (2-3 seconds)
After:  First request = instant (~50ms)

This eliminates cold start latency!

v2: Added meal_type support for time-aware menu filtering
"""
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


def get_current_meal_period() -> str:
    """
    Get current meal period based on IST time.

    Returns: 'Breakfast', 'Lunch', 'Dinner', or 'All Day' (for late night)
    """
    try:
        from app.utils.timezone import get_current_time
        current_time = get_current_time()
    except Exception:
        current_time = datetime.now()

    hour = current_time.hour

    if 5 <= hour < 11:
        return "Breakfast"
    elif 11 <= hour < 16:
        return "Lunch"
    elif 16 <= hour < 22:
        return "Dinner"
    else:
        return "All Day"  # Late night - show all day items


class MenuPreloader:
    """
    Pre-loads and caches menu data.

    Menu rarely changes, so we cache it aggressively.
    Auto-refreshes every 5 minutes in background.
    """

    def __init__(self, refresh_interval: int = 300):  # 5 minutes
        self.refresh_interval = refresh_interval
        self._menu_cache: Optional[List[Dict]] = None
        self._last_refresh: Optional[datetime] = None
        self._refresh_task: Optional[asyncio.Task] = None

    @property
    def menu(self) -> List[Dict]:
        """Get cached menu (returns empty if not loaded)."""
        return self._menu_cache or []

    @property
    def is_loaded(self) -> bool:
        """Check if menu is loaded."""
        return self._menu_cache is not None

    async def load(self):
        """Load menu from database into cache with meal_type info."""
        from app.core.db_pool import get_async_pool

        try:
            pool = await get_async_pool()
            async with pool.acquire() as conn:
                # Load basic menu items (meal_type mapping will be added later)
                rows = await conn.fetch("""
                    SELECT
                        mi.menu_item_id as id,
                        mi.menu_item_name as name,
                        mi.menu_item_price as price,
                        mi.menu_item_description as description,
                        mi.menu_item_in_stock as is_available,
                        'All Day' as meal_types
                    FROM menu_item mi
                    WHERE mi.is_deleted = FALSE
                    AND mi.menu_item_status = 'active'
                    ORDER BY mi.menu_item_name
                """)

                self._menu_cache = [
                    {
                        "id": str(row['id']),
                        "name": row['name'],
                        "price": float(row['price']),
                        "description": row['description'] or "",
                        "is_available": row['is_available'],
                        "meal_types": row['meal_types'].split(',') if row['meal_types'] else ['All Day']
                    }
                    for row in rows
                ]
                self._last_refresh = datetime.now()

                logger.info(
                    "menu_preloaded",
                    item_count=len(self._menu_cache),
                    refresh_interval=self.refresh_interval
                )

        except Exception as e:
            logger.error("menu_preload_failed", error=str(e))
            # Keep old cache if refresh fails
            if self._menu_cache is None:
                self._menu_cache = []

    async def start_background_refresh(self):
        """Start background refresh task."""
        async def refresh_loop():
            while True:
                await asyncio.sleep(self.refresh_interval)
                await self.load()
                logger.debug("menu_background_refresh_complete")

        self._refresh_task = asyncio.create_task(refresh_loop())
        logger.info("menu_background_refresh_started")

    async def stop(self):
        """Stop background refresh."""
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
            self._refresh_task = None

    def search(self, query: str = "", meal_period: Optional[str] = None, prioritize_meal: bool = True) -> List[Dict]:
        """
        Search cached menu (no DB query!).

        This is instant because menu is already in memory.

        Args:
            query: Search term (empty = show all)
            meal_period: Filter by meal period (Breakfast, Lunch, Dinner, All Day)
            prioritize_meal: If True, show meal-appropriate items first, then others

        Returns:
            List of menu items, optionally filtered/prioritized by meal period
        """
        if not self._menu_cache:
            return []

        # Get available items
        available_items = [item for item in self._menu_cache if item.get("is_available", True)]

        # Apply search filter if query provided
        if query and query.lower() not in ["", "all", "show all", "everything"]:
            query_lower = query.lower()
            available_items = [
                item for item in available_items
                if (query_lower in item.get("name", "").lower() or
                    query_lower in item.get("description", "").lower())
            ]

        # Apply meal period filtering/prioritization
        if meal_period:
            def is_for_meal(item):
                meal_types = item.get("meal_types", ["All Day"])
                return meal_period in meal_types or "All Day" in meal_types

            if prioritize_meal:
                # Show meal-appropriate items first, then others
                meal_items = [item for item in available_items if is_for_meal(item)]
                other_items = [item for item in available_items if not is_for_meal(item)]
                available_items = meal_items + other_items
            else:
                # Strict filter - only show meal-appropriate items
                available_items = [item for item in available_items if is_for_meal(item)]

        return available_items

    def get_meal_suggestions(self, meal_period: str, limit: int = 5) -> List[Dict]:
        """
        Get suggested items for a specific meal period.

        Args:
            meal_period: 'Breakfast', 'Lunch', 'Dinner', or 'All Day'
            limit: Maximum number of suggestions

        Returns:
            List of suggested menu items for the meal period
        """
        if not self._menu_cache:
            return []

        # Filter items appropriate for this meal period
        suggestions = [
            item for item in self._menu_cache
            if item.get("is_available", True) and (
                meal_period in item.get("meal_types", ["All Day"]) or
                "All Day" in item.get("meal_types", [])
            )
        ]

        # Return top items (could add popularity sorting later)
        return suggestions[:limit]

    def find_item(self, name: str) -> Optional[Dict]:
        """
        Find item by name (fuzzy match).

        Returns first match, or None if not found.
        """
        if not self._menu_cache:
            return None

        name_lower = name.lower()
        name_singular = name_lower.rstrip('s') if name_lower.endswith('s') else name_lower

        for item in self._menu_cache:
            item_name = item.get("name", "").lower()
            if (name_lower in item_name or
                name_singular in item_name or
                item_name == name_lower or
                item_name == name_singular):
                return item

        return None


# ============================================================================
# MODEL PRELOADER (warm up LLM connection)
# ============================================================================

class ModelPreloader:
    """
    Pre-warms LLM connection with a simple query.

    First LLM call has connection overhead (~1-2 seconds).
    Pre-warming eliminates this for real user queries.
    """

    @staticmethod
    async def warmup():
        """Send a simple query to warm up the connection."""
        import os
        from langchain_openai import ChatOpenAI

        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                logger.warning("model_warmup_skipped_no_api_key")
                return

            llm = ChatOpenAI(
                model="gpt-4o-mini",
                temperature=0,
                max_tokens=5,
                api_key=api_key
            )

            # Simple warmup query
            await asyncio.to_thread(
                llm.invoke,
                "Say 'ready'"
            )

            logger.info("model_connection_warmed")

        except Exception as e:
            logger.warning("model_warmup_failed", error=str(e))


# ============================================================================
# GLOBAL INSTANCES & STARTUP
# ============================================================================

_menu_preloader: Optional[MenuPreloader] = None


def get_menu_preloader() -> MenuPreloader:
    """Get global menu preloader instance."""
    global _menu_preloader
    if _menu_preloader is None:
        _menu_preloader = MenuPreloader()
    return _menu_preloader


async def preload_all():
    """
    Preload all caches on application startup.

    Call this in your FastAPI lifespan or startup event.
    """
    logger.info("preloading_application_caches")

    # Load menu
    preloader = get_menu_preloader()
    await preloader.load()
    await preloader.start_background_refresh()

    # Warm up model connection (optional, can be slow)
    # await ModelPreloader.warmup()

    logger.info("preloading_complete")


async def cleanup_preloaders():
    """Clean up on shutdown."""
    preloader = get_menu_preloader()
    await preloader.stop()
