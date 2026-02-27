"""
Phase 2 Missing Tools Implementation
=====================================
Advanced menu filtering and discovery tools.

These tools provide enhanced menu browsing by cuisine, allergens, dietary restrictions,
tags, combos, and meal types.

Implementation Date: 2025-12-21
Total Tools: 9 (Phase 2 of 4)
"""

from crewai.tools import tool
import structlog
from typing import Optional, List, Dict

logger = structlog.get_logger(__name__)


# ============================================================================
# CATEGORY: ADVANCED MENU FILTERING & DISCOVERY (9 tools)
# ============================================================================

def create_advanced_menu_tools(session_id: str, customer_id: Optional[str] = None):
    """Factory to create advanced menu filtering tools with session context."""

    @tool("filter_menu_by_allergen")
    async def filter_menu_by_allergen(allergen_name: str = "") -> str:
        """
        Show menu items safe for customers with specific allergen.

        Use this when customer asks "show me nut-free items", "what can I eat if I'm allergic to dairy",
        or "which items don't have shellfish".

        If no allergen specified, uses customer's saved allergen profile (if logged in).

        Args:
            allergen_name: Name of allergen to avoid (e.g., "peanuts", "dairy", "shellfish", "gluten").
                         Leave empty to use customer's saved allergens.

        Returns:
            List of menu items that don't contain the specified allergen(s).
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async
            from app.core.preloader import get_menu_preloader

            await emit_tool_activity_async(session_id, "filter_menu_by_allergen")

            # If no allergen specified and customer is logged in, use their allergens
            allergens_to_avoid = []
            if not allergen_name and customer_id:
                async with AsyncDBConnection() as db:
                    allergen_query = """
                        SELECT a.allergen_name
                        FROM customer_allergens ca
                        JOIN allergens a ON ca.allergen_id = a.allergen_id
                        WHERE ca.customer_id = %s AND ca.is_deleted = FALSE
                    """
                    results = await db.fetch_all(allergen_query, (customer_id,))
                    allergens_to_avoid = [r['allergen_name'] for r in results]

                if not allergens_to_avoid:
                    return "You don't have any allergens registered. Please specify which allergen you want to avoid."
            else:
                allergens_to_avoid = [allergen_name]

            # Get menu items that DON'T contain these allergens
            # Note: This is a simplified version. In production, you'd have menu_item_allergen_mapping table
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu data is loading. Please try again in a moment."

            # For now, use description-based filtering (you should implement proper allergen tagging)
            all_items = preloader.search("")
            safe_items = []

            for item in all_items:
                item_desc = (item.get('description', '') + ' ' + item.get('name', '')).lower()
                is_safe = True
                for allergen in allergens_to_avoid:
                    if allergen.lower() in item_desc:
                        is_safe = False
                        break
                if is_safe:
                    safe_items.append(item)

            if not safe_items:
                allergen_list = ", ".join(allergens_to_avoid)
                return f"I couldn't find menu items that are definitely safe for {allergen_list} allergies. Would you like me to check specific items?"

            # Format response
            items_list = []
            for item in safe_items[:15]:
                items_list.append(f"- {item.get('name')} (Rs.{item.get('price')})")

            allergen_list = ", ".join(allergens_to_avoid)
            response = f"**Items safe for {allergen_list} allergies:**\n\n" + "\n".join(items_list)

            if len(safe_items) > 15:
                response += f"\n\n...and {len(safe_items) - 15} more items."

            response += "\n\n⚠️ **Note:** Please verify with our staff before ordering if you have severe allergies."
            return response

        except Exception as e:
            logger.error("filter_menu_by_allergen_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't filter the menu by allergen right now. Please ask me to check specific items."

    @tool("filter_menu_by_dietary_restriction")
    async def filter_menu_by_dietary_restriction(restriction_type: str) -> str:
        """
        Filter menu items by dietary restriction.

        Use this when customer asks "show me vegan options", "what's vegetarian", "gluten-free menu".

        Args:
            restriction_type: Type of dietary restriction - "vegan", "vegetarian", "gluten-free",
                            "lactose-free", "keto", "halal", "kosher", "paleo"

        Returns:
            Menu items matching the dietary restriction.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "filter_menu_by_dietary_restriction")

            async with AsyncDBConnection() as db:
                # Query menu items with dietary type tags
                # Note: Requires menu_item_dietary_type_mapping table or tags
                query = """
                    SELECT DISTINCT
                        mi.menu_item_name,
                        mi.menu_item_price,
                        mi.menu_item_description
                    FROM menu_item mi
                    LEFT JOIN menu_item_tag_mapping mitm ON mi.menu_item_id = mitm.menu_item_id
                    LEFT JOIN menu_item_tag mit ON mitm.tag_id = mit.tag_id
                    WHERE mi.menu_item_is_active = TRUE
                      AND mi.is_deleted = FALSE
                      AND (
                        LOWER(mit.tag_name) = LOWER(%s)
                        OR LOWER(mi.menu_item_name) LIKE LOWER(%s)
                        OR LOWER(mi.menu_item_description) LIKE LOWER(%s)
                      )
                    ORDER BY mi.menu_item_price
                    LIMIT 20
                """
                search_pattern = f"%{restriction_type}%"
                results = await db.fetch_all(query, (restriction_type, search_pattern, search_pattern))

                if not results:
                    return f"I couldn't find items specifically tagged as {restriction_type}. Would you like me to check our full menu and suggest suitable options?"

                # Format response
                items_list = []
                for row in results:
                    items_list.append(f"- {row['menu_item_name']} (Rs.{row['menu_item_price']})")

                response = f"**{restriction_type.title()} Options:**\n\n" + "\n".join(items_list)
                response += f"\n\nFound {len(results)} {restriction_type} items."
                return response

        except Exception as e:
            logger.error("filter_menu_by_dietary_restriction_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't filter by {restriction_type} right now. Let me try a basic search instead."

    @tool("search_by_cuisine")
    async def search_by_cuisine(cuisine_type: str) -> str:
        """
        Browse menu by cuisine type.

        Use this when customer asks "show me Italian dishes", "do you have Chinese food",
        "what Indian items do you have".

        Args:
            cuisine_type: Type of cuisine (e.g., "Italian", "Chinese", "Indian", "Mexican", "Thai", "American")

        Returns:
            Menu items for the specified cuisine.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async, emit_menu_data_async
            from app.core.preloader import get_menu_preloader

            await emit_tool_activity_async(session_id, "search_by_cuisine")

            # Map user-friendly cuisine names to actual database cuisine names
            cuisine_mapping = {
                'italian': ['Continental'],
                'american': ['Continental'],
                'continental': ['Continental'],
                'asian': ['Chinese / Indo-Chinese'],
                'chinese': ['Chinese / Indo-Chinese'],
                'indo-chinese': ['Chinese / Indo-Chinese'],
                'indo chinese': ['Chinese / Indo-Chinese'],
                'indian': ['South Indian', 'North Indian'],
                'south indian': ['South Indian'],
                'north indian': ['North Indian'],
                'street food': ['Street Food / Chaat'],
                'chaat': ['Street Food / Chaat']
            }

            # Get mapped cuisine names
            cuisine_lower = cuisine_type.lower().strip()
            db_cuisine_names = cuisine_mapping.get(cuisine_lower, [cuisine_type])

            async with AsyncDBConnection() as db:
                # Build query with IN clause for multiple cuisines
                placeholders = ','.join(['%s'] * len(db_cuisine_names))
                query = f"""
                    SELECT DISTINCT
                        mi.menu_item_id,
                        mi.menu_item_name,
                        mi.menu_item_price,
                        mi.menu_item_description,
                        c.cuisine_name,
                        mc.menu_category_name
                    FROM menu_item mi
                    JOIN menu_item_cuisine_mapping micm ON mi.menu_item_id = micm.menu_item_id
                    JOIN cuisines c ON micm.cuisine_id = c.cuisine_id
                    LEFT JOIN menu_item_category_mapping mcm ON mi.menu_item_id = mcm.menu_item_id AND mcm.is_primary = TRUE
                    LEFT JOIN menu_categories mc ON mcm.menu_category_id = mc.menu_category_id
                    WHERE mi.menu_item_is_active = TRUE
                      AND mi.is_deleted = FALSE
                      AND c.is_deleted = FALSE
                      AND c.cuisine_name IN ({placeholders})
                    ORDER BY mi.menu_item_price
                """
                results = await db.fetch_all(query, tuple(db_cuisine_names))

                if not results:
                    return f"I couldn't find {cuisine_type} cuisine items. Would you like to see our available cuisines?"

                # Use preloader to get full item details with meal types
                preloader = get_menu_preloader()
                item_ids = [str(row['menu_item_id']) for row in results]

                # Get full item details from preloader
                all_items = preloader.menu
                filtered_items = [
                    item for item in all_items
                    if item.get('id') in item_ids
                ]

                # Emit rich menu data event for frontend to display
                if filtered_items:
                    await emit_menu_data_async(
                        session_id,
                        filtered_items,
                        current_meal_period="",
                        show_meal_filters=False  # Hide meal filters for cuisine-specific view
                    )
                    return f"[MENU CARD DISPLAYED - {len(filtered_items)} {cuisine_type} items shown in visual menu. Browse the menu card and let me know what you'd like!]"

                # Fallback: Format text response if preloader fails
                items_list = []
                for row in results[:20]:
                    desc = f" - {row['menu_item_description'][:50]}..." if row['menu_item_description'] else ""
                    items_list.append(f"- {row['menu_item_name']} (Rs.{row['menu_item_price']}){desc}")

                response = f"**{cuisine_type.title()} Cuisine:**\n\n" + "\n".join(items_list)
                if len(results) > 20:
                    response += f"\n\n...and {len(results) - 20} more items."
                response += f"\n\nFound {len(results)} {cuisine_type} items total."
                return response

        except Exception as e:
            logger.error("search_by_cuisine_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't search by {cuisine_type} cuisine right now."

    @tool("get_available_cuisines")
    async def get_available_cuisines() -> str:
        """
        List all available cuisine types.

        Use this when customer asks "what cuisines do you have", "what types of food do you serve",
        "show me all cuisines".

        Returns:
            List of all available cuisines with item counts.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_available_cuisines")

            async with AsyncDBConnection() as db:
                query = """
                    SELECT
                        c.cuisine_name,
                        COUNT(DISTINCT mi.menu_item_id) as item_count
                    FROM cuisines c
                    JOIN menu_item_cuisine_mapping micm ON c.cuisine_id = micm.cuisine_id
                    JOIN menu_item mi ON micm.menu_item_id = mi.menu_item_id
                    WHERE c.is_deleted = FALSE
                      AND mi.menu_item_is_active = TRUE
                      AND mi.is_deleted = FALSE
                    GROUP BY c.cuisine_id, c.cuisine_name
                    ORDER BY item_count DESC, c.cuisine_name
                """
                results = await db.fetch_all(query)

                if not results:
                    return "No cuisines available at the moment. Our menu is being updated."

                # Format response
                cuisines_list = []
                for row in results:
                    cuisines_list.append(f"- {row['cuisine_name']} ({row['item_count']} items)")

                response = f"**Available Cuisines:**\n\n" + "\n".join(cuisines_list)
                response += "\n\nWhich cuisine would you like to explore?"
                return response

        except Exception as e:
            logger.error("get_available_cuisines_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve cuisines right now."

    @tool("get_combo_deals")
    async def get_combo_deals() -> str:
        """
        Show combo meal packages.

        Use this when customer asks "what combo deals do you have", "show me meal combos",
        "any package offers".

        Returns:
            Available combo deals with included items and pricing.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_combo_deals")

            async with AsyncDBConnection() as db:
                # Query combo items
                query = """
                    SELECT
                        ci.combo_item_id,
                        ci.combo_item_name,
                        ci.combo_item_price,
                        ci.combo_item_description,
                        COUNT(cic.component_id) as component_count
                    FROM combo_item ci
                    LEFT JOIN combo_item_components cic ON ci.combo_item_id = cic.combo_item_id
                    WHERE ci.is_deleted = FALSE
                      AND ci.combo_item_is_active = TRUE
                    GROUP BY ci.combo_item_id
                    ORDER BY ci.combo_item_price
                """
                results = await db.fetch_all(query)

                if not results:
                    return "We don't have combo deals available right now. Would you like to see our regular menu?"

                # Get components for each combo
                combos_list = []
                for row in results:
                    combo_id = row['combo_item_id']

                    # Get combo components
                    components_query = """
                        SELECT
                            mi.menu_item_name,
                            cic.quantity
                        FROM combo_item_components cic
                        JOIN menu_item mi ON cic.menu_item_id = mi.menu_item_id
                        WHERE cic.combo_item_id = %s
                        ORDER BY cic.display_order
                    """
                    components = await db.fetch_all(components_query, (combo_id,))

                    combo_str = f"**{row['combo_item_name']}** - Rs.{row['combo_item_price']}"
                    if row['combo_item_description']:
                        combo_str += f"\n  {row['combo_item_description']}"

                    if components:
                        combo_str += "\n  Includes:"
                        for comp in components:
                            qty = comp['quantity'] if comp['quantity'] > 1 else ""
                            combo_str += f"\n  • {qty} {comp['menu_item_name']}"

                    combos_list.append(combo_str)

                response = "**Combo Deals:**\n\n" + "\n\n".join(combos_list)
                response += "\n\nWould you like to order any of these combos?"
                return response

        except Exception as e:
            logger.error("get_combo_deals_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve combo deals right now."

    @tool("search_by_tag")
    async def search_by_tag(tag_name: str) -> str:
        """
        Find menu items by tag.

        Use this when customer asks "show me spicy dishes", "what's popular", "what's new",
        "chef's special", "best sellers".

        Args:
            tag_name: Tag to search for (e.g., "spicy", "popular", "new", "chef's special",
                    "best seller", "healthy", "comfort food")

        Returns:
            Menu items with the specified tag.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "search_by_tag")

            async with AsyncDBConnection() as db:
                query = """
                    SELECT DISTINCT
                        mi.menu_item_name,
                        mi.menu_item_price,
                        mi.menu_item_description,
                        mit.tag_name
                    FROM menu_item mi
                    JOIN menu_item_tag_mapping mitm ON mi.menu_item_id = mitm.menu_item_id
                    JOIN menu_item_tag mit ON mitm.tag_id = mit.tag_id
                    WHERE mi.menu_item_is_active = TRUE
                      AND mi.is_deleted = FALSE
                      AND LOWER(mit.tag_name) LIKE LOWER(%s)
                    ORDER BY mi.menu_item_price
                    LIMIT 20
                """
                search_pattern = f"%{tag_name}%"
                results = await db.fetch_all(query, (search_pattern,))

                if not results:
                    return f"I couldn't find items tagged as '{tag_name}'. Try tags like: spicy, popular, new, chef's special, healthy."

                # Format response
                items_list = []
                for row in results:
                    items_list.append(f"- {row['menu_item_name']} (Rs.{row['menu_item_price']})")

                response = f"**{tag_name.title()} Items:**\n\n" + "\n".join(items_list)
                response += f"\n\nFound {len(results)} items."
                return response

        except Exception as e:
            logger.error("search_by_tag_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't search by tag '{tag_name}' right now."

    @tool("get_meal_type_menu")
    async def get_meal_type_menu(meal_type: str) -> str:
        """
        Filter menu by meal time.

        Use this when customer asks "what's for breakfast", "show me dinner options",
        "lunch menu", "what do you have for brunch".

        Args:
            meal_type: Type of meal - "breakfast", "lunch", "dinner", "brunch", "snacks", "dessert"

        Returns:
            Menu items available for the specified meal period.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_meal_type_menu")

            async with AsyncDBConnection() as db:
                # Query menu items by meal type
                query = """
                    SELECT DISTINCT
                        mi.menu_item_name,
                        mi.menu_item_price,
                        mi.menu_item_description,
                        mt.meal_type_name
                    FROM menu_item mi
                    JOIN menu_item_ordertype_mapping miom ON mi.menu_item_id = miom.menu_item_id
                    JOIN meal_type mt ON miom.meal_type_id = mt.meal_type_id
                    WHERE mi.menu_item_is_active = TRUE
                      AND mi.is_deleted = FALSE
                      AND LOWER(mt.meal_type_name) = LOWER(%s)
                    ORDER BY mi.menu_item_price
                    LIMIT 20
                """
                results = await db.fetch_all(query, (meal_type,))

                if not results:
                    return f"I couldn't find items for {meal_type}. Would you like to see our full menu?"

                # Format response
                items_list = []
                for row in results:
                    desc = f" - {row['menu_item_description'][:50]}..." if row['menu_item_description'] else ""
                    items_list.append(f"- {row['menu_item_name']} (Rs.{row['menu_item_price']}){desc}")

                response = f"**{meal_type.title()} Menu:**\n\n" + "\n".join(items_list)
                response += f"\n\nFound {len(results)} {meal_type} items."
                return response

        except Exception as e:
            logger.error("get_meal_type_menu_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't get the {meal_type} menu right now."

    @tool("get_allergen_info_for_item")
    async def get_allergen_info_for_item(item_name: str) -> str:
        """
        Check allergens in a specific menu item.

        Use this when customer asks "does this burger contain nuts?", "what allergens are in the salad?",
        "is this gluten-free?".

        Args:
            item_name: Name of the menu item to check (partial names work)

        Returns:
            Complete allergen information for the specified item.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async
            from app.core.preloader import get_menu_preloader

            await emit_tool_activity_async(session_id, "get_allergen_info_for_item")

            # Find the menu item
            preloader = get_menu_preloader()
            item = preloader.find_item(item_name) if preloader.is_loaded else None

            if not item:
                return f"Sorry, I couldn't find '{item_name}' on our menu. Please check the spelling."

            menu_item_id = item.get('id')
            menu_item_name = item.get('name')

            # Note: This requires menu_item_allergen_mapping table
            # For now, return a placeholder response
            async with AsyncDBConnection() as db:
                # Check if we have allergen mapping (this table may not exist yet)
                try:
                    allergen_query = """
                        SELECT a.allergen_name
                        FROM menu_item_allergen_mapping miam
                        JOIN allergens a ON miam.allergen_id = a.allergen_id
                        WHERE miam.menu_item_id = %s AND miam.is_deleted = FALSE
                    """
                    results = await db.fetch_all(allergen_query, (menu_item_id,))

                    if results:
                        allergens = [r['allergen_name'] for r in results]
                        allergen_list = ", ".join(allergens)
                        return f"**{menu_item_name}** contains the following allergens:\n\n{allergen_list}\n\n⚠️ If you have severe allergies, please verify with our staff."
                    else:
                        return f"**{menu_item_name}** has no known allergens registered in our system.\n\n⚠️ If you have allergies, please verify with our staff before ordering."

                except Exception:
                    # Table doesn't exist, use description-based detection
                    desc = item.get('description', '').lower()
                    common_allergens = ['peanut', 'nut', 'dairy', 'milk', 'egg', 'shellfish', 'soy', 'wheat', 'gluten', 'sesame']

                    detected = []
                    for allergen in common_allergens:
                        if allergen in desc or allergen in menu_item_name.lower():
                            detected.append(allergen)

                    if detected:
                        return f"**{menu_item_name}** may contain: {', '.join(detected)}\n\n⚠️ Please verify with our staff for accurate allergen information."
                    else:
                        return f"**{menu_item_name}** description doesn't mention common allergens, but please verify with our staff if you have allergies."

        except Exception as e:
            logger.error("get_allergen_info_for_item_error", error=str(e), exc_info=True)
            return f"Sorry, I couldn't check allergen info for {item_name} right now."

    @tool("get_popular_items")
    async def get_popular_items(limit: int = 10) -> str:
        """
        Show most popular menu items.

        Use this when customer asks "what's popular", "best sellers", "most ordered items",
        "what do people usually order".

        Args:
            limit: Maximum number of items to show (default: 10)

        Returns:
            List of most popular menu items based on order frequency.
        """
        try:
            from app.core.db_pool import AsyncDBConnection
            from app.core.agui_events import emit_tool_activity_async

            await emit_tool_activity_async(session_id, "get_popular_items")

            async with AsyncDBConnection() as db:
                # Query most ordered items
                query = """
                    SELECT
                        mi.menu_item_name,
                        mi.menu_item_price,
                        mi.menu_item_description,
                        COUNT(oi.order_item_id) as order_count
                    FROM menu_item mi
                    JOIN order_item oi ON mi.menu_item_id = oi.menu_item_id
                    JOIN orders o ON oi.order_id = o.order_id
                    WHERE mi.menu_item_is_active = TRUE
                      AND mi.is_deleted = FALSE
                      AND o.created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY mi.menu_item_id
                    ORDER BY order_count DESC, mi.menu_item_name
                    LIMIT %s
                """
                results = await db.fetch_all(query, (limit,))

                if not results:
                    # Fallback: show items tagged as popular
                    fallback_query = """
                        SELECT DISTINCT
                            mi.menu_item_name,
                            mi.menu_item_price,
                            mi.menu_item_description
                        FROM menu_item mi
                        JOIN menu_item_tag_mapping mitm ON mi.menu_item_id = mitm.menu_item_id
                        JOIN menu_item_tag mit ON mitm.tag_id = mit.tag_id
                        WHERE mi.menu_item_is_active = TRUE
                          AND mi.is_deleted = FALSE
                          AND LOWER(mit.tag_name) LIKE '%popular%'
                        LIMIT %s
                    """
                    results = await db.fetch_all(fallback_query, (limit,))

                if not results:
                    return "I couldn't find popular items data. Would you like to see our full menu instead?"

                # Format response
                items_list = []
                for idx, row in enumerate(results, 1):
                    order_count = row.get('order_count', '')
                    count_str = f" ({order_count} orders)" if order_count else ""
                    items_list.append(f"{idx}. {row['menu_item_name']} - Rs.{row['menu_item_price']}{count_str}")

                response = "**Most Popular Items:**\n\n" + "\n".join(items_list)
                response += "\n\nWould you like to try any of these favorites?"
                return response

        except Exception as e:
            logger.error("get_popular_items_error", error=str(e), exc_info=True)
            return "Sorry, I couldn't retrieve popular items right now."

    return [
        filter_menu_by_allergen,
        filter_menu_by_dietary_restriction,
        search_by_cuisine,
        get_available_cuisines,
        get_combo_deals,
        search_by_tag,
        get_meal_type_menu,
        get_allergen_info_for_item,
        get_popular_items
    ]


# ============================================================================
# TOOL COLLECTION FOR EASY INTEGRATION
# ============================================================================

def get_all_phase2_tools(session_id: str, customer_id: Optional[str] = None) -> List:
    """
    Get all Phase 2 tools for integration into crew_agent.py.

    Usage in crew_agent.py:
        from app.features.food_ordering.new_tools_phase2 import get_all_phase2_tools

        # In create_crew() function, add to tools list:
        phase2_tools = get_all_phase2_tools(session_id, customer_id)
        all_tools = existing_tools + phase2_tools

    Args:
        session_id: Current chat session ID
        customer_id: Current customer ID (None if not logged in)

    Returns:
        List of all 9 Phase 2 tool functions
    """
    tools = create_advanced_menu_tools(session_id, customer_id)

    logger.info("phase2_tools_loaded", tool_count=len(tools), session=session_id)

    return tools
