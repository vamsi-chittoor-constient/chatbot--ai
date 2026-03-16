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
import os
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import structlog

from app.core.db_pool import get_async_pool

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
        self._has_recommendation_tags: bool = False

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
        try:
            pool = await get_async_pool()
            async with pool.acquire() as conn:
                # Load menu items with meal types, cuisines, and categories
                rows = await conn.fetch("""
                    SELECT
                        mi.menu_item_id as id,
                        mi.menu_item_name as name,
                        mi.menu_item_price as price,
                        mi.menu_item_description as description,
                        mi.menu_item_in_stock as is_available,
                        mi.menu_item_is_recommended as is_recommended,
                        mi.recommendation_tags as recommendation_tags,
                        ARRAY_AGG(DISTINCT mt.meal_type_name)
                            FILTER (WHERE mt.meal_type_name IS NOT NULL) as meal_types,
                        msc.sub_category_name as category
                    FROM menu_item mi
                    LEFT JOIN menu_item_availability_schedule mas
                        ON mi.menu_item_id = mas.menu_item_id
                        AND mas.is_deleted = FALSE
                        AND mas.is_available = TRUE
                    LEFT JOIN meal_type mt
                        ON mas.meal_type_id = mt.meal_type_id
                        AND mt.is_deleted = FALSE
                    LEFT JOIN menu_sub_categories msc
                        ON mi.menu_sub_category_id = msc.menu_sub_category_id
                        AND msc.is_deleted = FALSE
                    WHERE mi.is_deleted = FALSE
                    AND mi.menu_item_status = 'active'
                    GROUP BY mi.menu_item_id, mi.menu_item_name, mi.menu_item_price,
                             mi.menu_item_description, mi.menu_item_in_stock,
                             mi.menu_item_is_recommended, msc.sub_category_name
                    ORDER BY mi.menu_item_is_recommended DESC, mi.menu_item_name
                """)

                _ALL_MEAL_PERIODS = {"Breakfast", "Lunch", "Dinner", "All Day"}

                self._menu_cache = []
                for row in rows:
                    meal_types = list(row['meal_types']) if row['meal_types'] else []
                    # Normalize: items with "All Day" or no tags get all meal periods
                    # so they pass any meal period filter without special-casing
                    if not meal_types or "All Day" in meal_types:
                        meal_types = list(_ALL_MEAL_PERIODS)

                    # Parse recommendation_tags from JSONB (comes as list or None)
                    _raw_tags = row['recommendation_tags']
                    _rec_tags = _raw_tags if isinstance(_raw_tags, list) else []

                    self._menu_cache.append({
                        "id": str(row['id']),
                        "name": row['name'],
                        "price": float(row['price']),
                        "description": row['description'] or "",
                        "is_available": row['is_available'],
                        "is_recommended": row['is_recommended'],
                        "meal_types": meal_types,
                        "category": row['category'] or "Other",
                        "recommendation_tags": _rec_tags,
                    })
                self._last_refresh = datetime.now()

                logger.info(
                    "menu_preloaded",
                    item_count=len(self._menu_cache),
                    refresh_interval=self.refresh_interval
                )

                # Auto-index into ChromaDB for semantic search
                await self._sync_vector_db()

                # Tag untagged items via LLM recommendation engine
                await self._tag_untagged_items()

        except Exception as e:
            logger.error("menu_preload_failed", error=str(e))
            # Keep old cache if refresh fails
            if self._menu_cache is None:
                self._menu_cache = []

    async def _sync_vector_db(self):
        """Index menu items into ChromaDB if out of sync."""
        try:
            from app.ai_services.vector_db_service import get_vector_db_service
            vdb = get_vector_db_service()

            # Skip if counts match (menu hasn't changed)
            if vdb.menu_collection.count() == len(self._menu_cache):
                return

            # Clear and re-index
            vdb.clear_collection()
            items_for_index = [
                {
                    "id": item["id"],
                    "name": item["name"],
                    "description": item.get("description", ""),
                    "category": item.get("category", "Other"),
                    "price": item.get("price", 0),
                }
                for item in self._menu_cache
                if item.get("price", 0) > 0
            ]
            if items_for_index:
                await vdb.bulk_index_menu_items(items_for_index)
                logger.info("vector_db_synced", item_count=len(items_for_index))
        except Exception as e:
            # Non-critical — semantic search degrades to category fallback
            logger.debug("vector_db_sync_skipped", error=str(e))

    async def _tag_untagged_items(self):
        """Run LLM tagger on any menu items missing recommendation_tags."""
        try:
            from app.services.menu_tagger import tag_untagged_items
            self._menu_cache = await tag_untagged_items(self._menu_cache)
            self._has_recommendation_tags = any(
                item.get("recommendation_tags") for item in (self._menu_cache or [])
            )
        except Exception as e:
            # Non-critical — recommendation falls back to food group engine
            logger.debug("menu_tagger_skipped", error=str(e))

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

    def search(self, query: str = "", meal_period: Optional[str] = None, prioritize_meal: bool = True, strict_meal_filter: bool = False) -> List[Dict]:
        """
        Search cached menu (no DB query!).

        This is instant because menu is already in memory.

        Args:
            query: Search term (empty = show all)
            meal_period: Filter by meal period (Breakfast, Lunch, Dinner, All Day)
            prioritize_meal: If True, show meal-appropriate items first, then others
            strict_meal_filter: If True, ONLY show meal-appropriate items (ignores prioritize_meal)

        Returns:
            List of menu items, optionally filtered/prioritized by meal period
        """
        if not self._menu_cache:
            return []

        # Get available items with valid prices (exclude zero-price items)
        available_items = [
            item for item in self._menu_cache
            if item.get("is_available", True) and item.get("price", 0) > 0
        ]

        # Apply search filter if query provided
        if query and query.lower() not in ["", "all", "show all", "everything"]:
            query_lower = query.lower()

            # Expand drink-related search terms to include common synonyms
            drink_keywords = ["drink", "drinks", "beverage", "beverages", "cold drink", "cool drink"]
            is_drink_search = any(keyword in query_lower for keyword in drink_keywords)

            # Stage 1: Substring match (fast, precise)
            matched_items = [
                item for item in available_items
                if (query_lower in item.get("name", "").lower() or
                    query_lower in item.get("description", "").lower() or
                    query_lower in item.get("subcategory", "").lower() or
                    (is_drink_search and item.get("subcategory", "").lower() == "beverages"))
            ]

            # Stage 1.5: Word-level substring match (handles multi-word queries like "fresh juice")
            if not matched_items:
                query_words = [w for w in query_lower.split() if len(w) > 2]
                if query_words:
                    matched_items = [
                        item for item in available_items
                        if all(
                            any(word in item.get(field, "").lower()
                                for field in ("name", "description", "subcategory"))
                            for word in query_words
                        )
                    ]

            # Stage 2: Fuzzy match fallback for spelling variations
            # (e.g. "paratha" vs "parota", "biriyani" vs "biryani")
            if not matched_items and len(query_lower) >= 4:
                matched_items = [
                    item for item in available_items
                    if SequenceMatcher(None, query_lower, item.get("name", "").lower()).ratio() >= 0.80
                ]
                if matched_items:
                    logger.info("search_fuzzy_fallback", query=query, matches=len(matched_items))

            available_items = matched_items

        # Apply meal period filtering/prioritization
        if meal_period:
            if strict_meal_filter:
                # Strict filter - show items for current meal period + "All Day" items
                def is_for_meal_strict(item):
                    meal_types = item.get("meal_types", [])
                    return meal_period in meal_types or "All Day" in meal_types

                available_items = [item for item in available_items if is_for_meal_strict(item)]
            elif prioritize_meal:
                # Show meal-appropriate items first, then others (for search results)
                # In this mode, "All Day" items ARE included
                def is_for_meal(item):
                    meal_types = item.get("meal_types", ["All Day"])
                    return meal_period in meal_types or "All Day" in meal_types

                meal_items = [item for item in available_items if is_for_meal(item)]
                other_items = [item for item in available_items if not is_for_meal(item)]
                available_items = meal_items + other_items

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

        # Filter items appropriate for this meal period (exclude zero-price items)
        suggestions = [
            item for item in self._menu_cache
            if item.get("is_available", True) and
               item.get("price", 0) > 0 and (
                meal_period in item.get("meal_types", ["All Day"]) or
                "All Day" in item.get("meal_types", [])
            )
        ]

        # Return top items (could add popularity sorting later)
        return suggestions[:limit]

    def find_item(self, name: str, with_confidence: bool = False):
        """
        Find item by name with multi-stage matching.

        Stage 1: Exact/substring match (fast, precise) — confidence 1.0
        Stage 2: Fuzzy match via SequenceMatcher (handles spelling variations
                 like parota/paratha, biryani/biriyani, dosa/dosai)

        Args:
            name: Item name to search for
            with_confidence: If True, returns (item, confidence) tuple

        Returns:
            If with_confidence=False: best match dict, or None
            If with_confidence=True: (item, confidence) tuple, or (None, 0.0)
        """
        if not self._menu_cache:
            return (None, 0.0) if with_confidence else None

        name_lower = name.lower().strip()
        name_singular = name_lower.rstrip('s') if name_lower.endswith('s') else name_lower

        # Stage 1a: Exact match (highest priority)
        for item in self._menu_cache:
            if item.get("price", 0) <= 0:
                continue
            item_name = item.get("name", "").lower()
            if item_name == name_lower or item_name == name_singular:
                return (item, 1.0) if with_confidence else item

        # Stage 1b: Substring match — prefer the longest (most specific) match
        # Without this, "amla juice" (substring of "aswins amla juice") would
        # incorrectly match before the exact "Aswins Amla Juice" item.
        best_substring = None
        best_len = 0
        for item in self._menu_cache:
            if item.get("price", 0) <= 0:
                continue
            item_name = item.get("name", "").lower()
            if (name_lower in item_name or
                name_singular in item_name or
                item_name in name_lower):
                if len(item_name) > best_len:
                    best_len = len(item_name)
                    best_substring = item
        if best_substring:
            return (best_substring, 1.0) if with_confidence else best_substring

        # Stage 2: Fuzzy match (handles LLM "correcting" spellings)
        # e.g. "aloo paratha" matches "Aloo Parota", "biriyani" matches "Biryani"
        best_match = None
        best_ratio = 0.0

        for item in self._menu_cache:
            if item.get("price", 0) <= 0:
                continue

            item_name = item.get("name", "").lower()
            ratio = SequenceMatcher(None, name_lower, item_name).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = item

        # Require at least 85% similarity for single-item lookup
        # (catches spelling variations like idli/idly, paneer/panir
        #  but rejects false positives like "fresh juice" → "french fries")
        if best_ratio >= 0.85 and best_match:
            logger.info(
                "find_item_fuzzy_match",
                query=name,
                matched=best_match.get("name"),
                similarity=f"{best_ratio:.2f}"
            )
            return (best_match, best_ratio) if with_confidence else best_match

        return (None, 0.0) if with_confidence else None

    def get_similar_items(self, query: str, limit: int = 10, exclude_ids: Optional[set] = None) -> tuple[List[Dict], str]:
        """
        Find individually similar menu items using semantic search.

        Returns actual items that are semantically close to the query,
        not an entire category dump.

        Args:
            query: The search term that had no direct matches
            limit: Max items to return
            exclude_ids: Item IDs to exclude (e.g. items already in cart)

        Returns:
            (items, label) — list of similar items and a display label
        """
        if not self._menu_cache:
            return [], ""

        exclude_ids = exclude_ids or set()

        # Build ID→item lookup from cache for fast matching
        item_by_id = {
            item["id"]: item
            for item in self._menu_cache
            if item.get("price", 0) > 0 and item.get("is_available", True)
        }

        # Step 1: Semantic search via VectorDB (item-level results)
        try:
            from app.ai_services.vector_db_service import get_vector_db_service
            vdb = get_vector_db_service()

            if vdb.menu_collection.count() > 0:
                results = vdb.menu_collection.query(
                    query_texts=[query],
                    n_results=min(limit + len(exclude_ids), 20),
                    include=["metadatas", "distances"]
                )

                if results and results['ids'] and results['ids'][0]:
                    # Log top 3 scores for debugging
                    top_scores = [
                        (results['metadatas'][0][i].get('name', ''), round(1 - float(results['distances'][0][i]) / 2, 3))
                        for i in range(min(3, len(results['ids'][0])))
                    ]
                    logger.info("semantic_search_scores", query=query, top_scores=top_scores)

                    similar = []
                    for idx, item_id in enumerate(results['ids'][0]):
                        if item_id in exclude_ids:
                            continue

                        distance = float(results['distances'][0][idx])
                        similarity = 1 - (distance / 2)

                        # Only include genuinely similar items (>0.85)
                        # 0.85 in rescaled space = cosine_similarity > 0.7
                        if similarity < 0.85:
                            break  # distances are sorted, rest will be worse

                        # Look up full item data from preloader cache
                        cached_item = item_by_id.get(item_id)
                        if cached_item:
                            similar.append(cached_item)

                        if len(similar) >= limit:
                            break

                    if similar:
                        label = "similar items"
                        logger.info(
                            "similar_items_semantic",
                            query=query,
                            count=len(similar),
                            items=[i["name"] for i in similar[:5]],
                        )
                        return similar, label
                    else:
                        top_sim = 1 - (float(results['distances'][0][0]) / 2)
                        logger.info("similar_items_too_weak", query=query, top_similarity=round(top_sim, 3), top_item=results['metadatas'][0][0].get('name', ''))
        except Exception as e:
            logger.debug("semantic_similar_items_fallback", error=str(e))

        # Step 2: Fallback — match query against category names
        query_lower = query.lower().strip()
        for item in self._menu_cache:
            if item.get("price", 0) <= 0 or not item.get("is_available", True):
                continue
            cat = item.get("category", "Other")
            if query_lower in cat.lower() or cat.lower() in query_lower:
                cat_items = [
                    i for i in self._menu_cache
                    if i.get("category") == cat
                    and i.get("price", 0) > 0
                    and i.get("is_available", True)
                    and i["id"] not in exclude_ids
                ]
                return cat_items[:limit], cat

        # Step 3: LLM-based recommendation engine (tag overlap)
        # Each menu item has pre-computed recommendation_tags from the LLM tagger.
        # Score items by how many tags they share with query-matching items.
        if self._has_recommendation_tags:
            # Find items whose tags match the query words
            query_words = set(query_lower.replace("-", "_").replace(" ", "_").split("_"))
            query_words.update(query_lower.split())  # also keep original words
            # Add full underscore-joined form (e.g. "ice cream" => "ice_cream" tag match)
            query_words.add(query_lower.replace(" ", "_").replace("-", "_"))
            query_words = {w for w in query_words if len(w) > 2}

            # Collect tags from items that directly match the query (name/desc substring)
            seed_tags: set = set()
            for item in self._menu_cache:
                item_tags = item.get("recommendation_tags", [])
                if not item_tags:
                    continue
                item_name = item.get("name", "").lower()
                # If the query appears in item name or vice versa, use its tags as seed
                if query_lower in item_name or item_name in query_lower:
                    seed_tags.update(item_tags)
                else:
                    # Also check if any query word matches a tag directly
                    tag_set = set(item_tags)
                    if query_words & tag_set:
                        seed_tags.update(item_tags)

            # If no seed from name match, use query words directly as tags
            if not seed_tags:
                seed_tags = query_words

            if seed_tags:
                scored = []
                for item in self._menu_cache:
                    if (item.get("price", 0) <= 0 or not item.get("is_available", True)
                            or item["id"] in exclude_ids):
                        continue
                    item_tags = set(item.get("recommendation_tags", []))
                    if not item_tags:
                        continue
                    # Score = number of shared tags with seed
                    overlap = len(seed_tags & item_tags)
                    if overlap > 0:
                        scored.append((overlap, item))

                if scored:
                    scored.sort(key=lambda x: x[0], reverse=True)
                    result = [item for _, item in scored[:limit]]
                    logger.info(
                        "similar_items_tag_engine",
                        query=query,
                        seed_tags=list(seed_tags)[:10],
                        count=len(result),
                        items=[i["name"] for i in result[:5]],
                    )
                    return result, "similar items"

        # Step 3b: Fallback — hardcoded food group engine (used when tags not yet generated)
        _FOOD_GROUPS = {
            "fast_food": {
                "keywords": ["burger", "pizza", "sandwich", "wrap", "roll", "hotdog", "sub", "shawarma", "frankie"],
                "related": ["snacks", "appetizers"],
            },
            "snacks": {
                "keywords": ["fries", "nachos", "wings", "nuggets", "fingers", "tikka", "kebab", "cutlet", "pakoda", "pakora", "bajji", "bonda", "side orders", "add ons"],
                "related": ["fast_food", "appetizers"],
            },
            "appetizers": {
                "keywords": ["soup", "starter", "appetizer", "salad", "manchurian", "gobi", "paneer tikka", "spring roll"],
                "related": ["snacks"],
            },
            "rice_dishes": {
                "keywords": ["biryani", "biriyani", "pulao", "fried rice", "rice", "khichdi", "jeera rice"],
                "related": ["north_indian"],
            },
            "south_indian": {
                "keywords": ["dosa", "dosai", "idli", "idly", "vada", "vadai", "upma", "pongal", "uttapam", "appam", "puttu", "parota", "paratha", "kothu"],
                "related": ["breakfast"],
            },
            "north_indian": {
                "keywords": ["naan", "nan", "roti", "chapati", "kulcha", "paratha", "paneer", "dal", "curry", "butter chicken", "tandoori", "tikka masala", "chicken", "chicken meal"],
                "related": ["rice_dishes"],
            },
            "chinese": {
                "keywords": ["noodles", "chowmein", "hakka", "manchurian", "schezwan", "fried rice", "momos", "dim sum", "spring roll", "chilli"],
                "related": ["fast_food"],
            },
            "beverages": {
                "keywords": ["juice", "shake", "smoothie", "lassi", "coffee", "tea", "chai", "soda", "lemonade", "mojito", "cooler", "drink", "water", "cola", "beverages", "hot coffees"],
                "related": ["desserts"],
            },
            "desserts": {
                "keywords": ["ice cream", "cake", "brownie", "pudding", "gulab jamun", "rasgulla", "halwa", "kheer", "payasam", "kulfi", "sweet", "mousse", "pastry", "desserts"],
                "related": ["beverages"],
            },
            "breakfast": {
                "keywords": ["omelette", "egg", "toast", "cereal", "pancake", "waffle", "poha", "upma", "sandwich"],
                "related": ["south_indian"],
            },
            "seafood": {
                "keywords": ["fish", "prawn", "shrimp", "crab", "lobster", "squid", "calamari", "seafood", "seafood meal"],
                "related": ["north_indian", "chinese"],
            },
        }

        matched_groups = set()
        for group_key, group_data in _FOOD_GROUPS.items():
            for kw in group_data["keywords"]:
                if kw in query_lower or query_lower in kw:
                    matched_groups.add(group_key)
                    break

        if matched_groups:
            all_groups = set(matched_groups)
            for g in matched_groups:
                all_groups.update(_FOOD_GROUPS[g].get("related", []))

            all_keywords = set()
            for g in all_groups:
                if g in _FOOD_GROUPS:
                    all_keywords.update(_FOOD_GROUPS[g]["keywords"])

            scored = []
            for item in self._menu_cache:
                if (item.get("price", 0) <= 0 or not item.get("is_available", True)
                        or item["id"] in exclude_ids):
                    continue
                item_name = item.get("name", "").lower()
                item_desc = item.get("description", "").lower()
                item_cat = item.get("category", "").lower()
                item_text = f"{item_name} {item_desc} {item_cat}"

                score = 0.0
                for kw in all_keywords:
                    if kw in item_text:
                        is_primary = any(kw in _FOOD_GROUPS.get(g, {}).get("keywords", []) for g in matched_groups)
                        score += 2.0 if is_primary else 1.0

                query_words = [w for w in query_lower.split() if len(w) > 2]
                item_words = [w for w in item_name.split() if len(w) > 2]
                for qw in query_words:
                    for iw in item_words:
                        ratio = SequenceMatcher(None, qw, iw).ratio()
                        if ratio >= 0.60:
                            score += ratio

                if score > 0:
                    scored.append((score, item))

            if scored:
                scored.sort(key=lambda x: x[0], reverse=True)
                result = [item for _, item in scored[:limit]]
                group_labels = [g.replace("_", " ").title() for g in matched_groups]
                label = f"similar to {', '.join(group_labels)}"
                logger.info("similar_items_food_group", query=query, groups=list(matched_groups),
                           count=len(result), items=[i["name"] for i in result[:5]])
                return result, label

        # Step 4: No food group match — try pure fuzzy for unlisted food terms
        query_words = [w for w in query_lower.split() if len(w) > 2]
        if query_words:
            scored_items = []
            for item in self._menu_cache:
                if (item.get("price", 0) <= 0 or not item.get("is_available", True)
                        or item["id"] in exclude_ids):
                    continue
                item_name = item.get("name", "").lower()
                item_words = [w for w in item_name.split() if len(w) > 2]
                score = 0.0
                for qw in query_words:
                    for iw in item_words:
                        ratio = SequenceMatcher(None, qw, iw).ratio()
                        if ratio >= 0.60:
                            score += ratio
                if score > 0.5:
                    scored_items.append((score, item))
            if scored_items:
                scored_items.sort(key=lambda x: x[0], reverse=True)
                result = [item for _, item in scored_items[:limit]]
                logger.info("similar_items_fuzzy", query=query, count=len(result))
                return result, "similar items"

        # Step 5: No matches — suggest popular/recommended alternatives
        alternatives = [
            item for item in self._menu_cache
            if item.get("price", 0) > 0
            and item.get("is_available", True)
            and item.get("is_recommended", False)
            and item["id"] not in exclude_ids
        ]
        # If not enough recommended items, pad with other available items
        if len(alternatives) < limit:
            alt_ids = {a["id"] for a in alternatives}
            for item in self._menu_cache:
                if (item.get("price", 0) > 0
                    and item.get("is_available", True)
                    and item["id"] not in exclude_ids
                    and item["id"] not in alt_ids):
                    alternatives.append(item)
                    if len(alternatives) >= limit:
                        break

        if alternatives:
            logger.info("similar_items_alternatives", query=query, count=len(alternatives[:limit]))
            return alternatives[:limit], "popular alternatives"

        return [], ""

    def get_category_items(self, category: str, limit: int = 10, exclude_ids: Optional[set] = None) -> List[Dict]:
        """Get available items from a specific category."""
        if not self._menu_cache:
            return []
        exclude_ids = exclude_ids or set()
        return [
            i for i in self._menu_cache
            if i.get("category") == category
            and i.get("price", 0) > 0
            and i.get("is_available", True)
            and i["id"] not in exclude_ids
        ][:limit]


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
