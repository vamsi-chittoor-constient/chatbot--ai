"""
Event-Sourced Food Ordering Tools
===================================
New architecture: Tools use SQL state queries and return final human messages.

Key Changes from Old Approach:
1. State Management: SQL queries instead of text context
2. Event Logging: All actions logged as discrete events
3. Final Output: Tools return human-friendly messages (no LLM post-processing)
4. Zero Token Cost: Context retrieved via SQL, not passed in prompts
5. Callbacks: Tools emit frontend events directly (AGUI)

Architecture:
- LLM's job: User text → Tool name + params (intent classification only)
- Tool's job: Execute action + Log event + Query state + Return final message
- No iterations: Tool output IS the final response
"""

from crewai.tools import tool
from typing import Optional
from uuid import UUID
import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# TOOL FACTORY - Create session-scoped tools
# ============================================================================

def create_event_sourced_tools(session_id: str, customer_id: Optional[str] = None):
    """
    Factory to create event-sourced food ordering tools with session context.

    Tools are stateless - all state comes from SQL queries.
    Tools return final human-friendly messages (no LLM reformatting needed).
    """

    @tool("add_to_cart")
    def add_to_cart(item: str, quantity: int = 1) -> str:
        """
        Add item to cart. Returns final confirmation message.

        Args:
            item: Menu item name (fuzzy matched)
            quantity: Number to add (1-50)

        Process:
        1. Find item in menu (preloader)
        2. Log event to session_events
        3. Update session_cart (SQL)
        4. Update session_state (last mentioned)
        5. Emit cart update event (AGUI callback)
        6. Return human-friendly confirmation

        Returns:
            Final message: "Added 2x Margherita Pizza! Anything else?"
        """
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        from app.core.preloader import get_menu_preloader
        from app.core.session_events import get_session_tracker
        from app.core.db_pool import AsyncDBConnection
        import asyncio

        # Emit activity indicator for frontend
        emit_tool_activity(session_id, "add_to_cart")

        try:
            # Validate quantity
            if quantity <= 0:
                return "I need a positive quantity. How many would you like?"

            if quantity > 50:
                return "That's a lot! Maximum 50 per item. Contact us for bulk orders."

            # Find item in menu (preloader - sync, fast)
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading, please try again in a moment."

            found_item = preloader.find_item(item.strip())
            if not found_item:
                return f"I couldn't find '{item}' on our menu. Try searching first?"

            item_id = UUID(found_item['id'])
            item_name = found_item['name']
            price = float(found_item['price'])

            # Event-sourced update (async)
            async def update_cart():
                tracker = get_session_tracker(session_id, UUID(customer_id) if customer_id else None)

                # Add to cart (logs event + updates state)
                cart = await tracker.add_to_cart(
                    item_id=item_id,
                    item_name=item_name,
                    quantity=quantity,
                    price=price
                )

                # Emit cart update to frontend (AGUI callback)
                emit_cart_data(
                    session_id,
                    cart['items'],
                    cart['total']
                )

                return cart

            # Run async operation synchronously (tool context)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cart = loop.run_until_complete(update_cart())
            loop.close()

            # Return final human message with LLM formatting
            from app.core.llm_formatter import format_item_added

            return format_item_added(
                item_name=item_name,
                quantity=quantity,
                cart_total=cart['total'],
                item_count=cart['item_count']
            )

        except Exception as e:
            logger.error("add_to_cart_failed", error=str(e), session_id=session_id)
            return "Sorry, I couldn't add that to your cart. Please try again."

    @tool("view_cart")
    def view_cart() -> str:
        """
        View current cart contents.

        Process:
        1. Query session_cart table (SQL)
        2. Format items as human-readable list
        3. Emit cart card to frontend (AGUI callback)
        4. Return summary message

        Returns:
            Final message: "Your cart: 2x Margherita (₹400), 1x Coke (₹50). Total: ₹450"
        """
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        from app.core.session_events import get_session_tracker
        import asyncio

        emit_tool_activity(session_id, "view_cart")

        try:
            async def get_cart():
                tracker = get_session_tracker(session_id, UUID(customer_id) if customer_id else None)
                cart = await tracker.get_cart_summary()

                # Emit cart card to frontend
                emit_cart_data(session_id, cart['items'], cart['total'])

                return cart

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cart = loop.run_until_complete(get_cart())
            loop.close()

            # Return formatted cart view with LLM
            from app.core.llm_formatter import format_cart_view

            return format_cart_view(cart)

        except Exception as e:
            logger.error("view_cart_failed", error=str(e), session_id=session_id)
            return "Sorry, I couldn't retrieve your cart. Please try again."

    @tool("remove_from_cart")
    def remove_from_cart(item: str) -> str:
        """
        Remove item from cart.

        Process:
        1. Find item in current cart (SQL query)
        2. Log removal event
        3. Soft delete from session_cart
        4. Emit updated cart (AGUI)
        5. Return confirmation

        Returns:
            Final message: "Removed Margherita Pizza from your cart."
        """
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        from app.core.preloader import get_menu_preloader
        from app.core.session_events import get_session_tracker
        import asyncio

        emit_tool_activity(session_id, "remove_from_cart")

        try:
            # Find item
            preloader = get_menu_preloader()
            found_item = preloader.find_item(item.strip())

            if not found_item:
                return f"I couldn't find '{item}' in your cart."

            item_id = UUID(found_item['id'])

            async def remove():
                tracker = get_session_tracker(session_id, UUID(customer_id) if customer_id else None)
                cart = await tracker.remove_from_cart(item_id)

                if not cart.get('success', False):
                    return None

                # Emit updated cart
                emit_cart_data(session_id, cart['items'], cart['total'])
                return cart

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            cart = loop.run_until_complete(remove())
            loop.close()

            if not cart:
                return f"'{item}' is not in your cart."

            # Return formatted removal confirmation with LLM
            from app.core.llm_formatter import format_item_removed

            return format_item_removed(
                item_name=found_item['name'],
                remaining_items=len(cart['items'])
            )

        except Exception as e:
            logger.error("remove_from_cart_failed", error=str(e), session_id=session_id)
            return "Sorry, I couldn't remove that item. Please try again."

    @tool("search_menu")
    def search_menu(query: str = "") -> str:
        """
        Search menu and show matching items.

        Process:
        1. Query menu (preloader - fast, in-memory)
        2. Log menu_viewed event
        3. Update session_state (last shown menu)
        4. Emit menu card (AGUI callback)
        5. Return summary message

        Returns:
            Final message: "[MENU DISPLAYED] Browse the menu and let me know what you'd like!"
        """
        from app.core.agui_events import emit_tool_activity, emit_menu_data
        from app.core.preloader import get_menu_preloader, get_current_meal_period
        from app.core.session_events import get_session_tracker, EventType
        import asyncio

        emit_tool_activity(session_id, "search_menu")

        try:
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading, please try again in a moment."

            # Get current meal period for filtering
            meal_period = get_current_meal_period()

            # Search menu (in-memory, fast)
            items = preloader.search(query, meal_period=meal_period, strict_meal_filter=False)

            if not items:
                return f"No items found for '{query}'. Try a different search?"

            # Log event
            async def log_and_update():
                tracker = get_session_tracker(session_id, UUID(customer_id) if customer_id else None)
                await tracker.log_event(EventType.MENU_VIEWED, {
                    'query': query,
                    'result_count': len(items),
                    'meal_period': meal_period
                })

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(log_and_update())
            loop.close()

            # Emit menu card to frontend
            emit_menu_data(session_id, items[:50], meal_period)

            # Return formatted menu results with LLM
            from app.core.llm_formatter import format_menu_results

            formatted_msg = format_menu_results(items, query, meal_period)
            return f"[MENU DISPLAYED] {formatted_msg}"

        except Exception as e:
            logger.error("search_menu_failed", error=str(e), session_id=session_id)
            return "Sorry, I couldn't load the menu. Please try again."

    # Return all tools
    return [
        add_to_cart,
        view_cart,
        remove_from_cart,
        search_menu,
    ]
