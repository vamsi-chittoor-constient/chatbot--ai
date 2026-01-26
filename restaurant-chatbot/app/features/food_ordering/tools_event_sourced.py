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
import re

logger = structlog.get_logger(__name__)


# ============================================================================
# ORDINAL RESOLUTION - Resolve "option 1", "first one", etc.
# ============================================================================

def resolve_ordinal_reference(item_text: str, tracker) -> Optional[str]:
    """
    Resolve ordinal references like "option 1", "first", "#2" to actual item names.

    Uses the last MENU_VIEWED event from session_events to map ordinals to items.

    Args:
        item_text: User input like "option 1", "amla juice option 1", "first one"
        tracker: SyncSessionEventTracker instance

    Returns:
        Resolved item name if ordinal found, None otherwise
    """
    text = item_text.lower().strip()

    # Patterns to detect ordinal references
    ordinal_patterns = [
        # "option 1", "option 2" - most common
        (r'option\s*(\d+)', lambda m: int(m.group(1))),
        # "#1", "#2"
        (r'#\s*(\d+)', lambda m: int(m.group(1))),
        # "number 1", "number 2"
        (r'number\s*(\d+)', lambda m: int(m.group(1))),
        # "1st", "2nd", "3rd", "4th"
        (r'(\d+)(?:st|nd|rd|th)\b', lambda m: int(m.group(1))),
        # Plain numbers at end: "amla juice 1"
        (r'\b(\d+)$', lambda m: int(m.group(1))),
        # Word ordinals
        (r'\b(first|1st)\b', lambda m: 1),
        (r'\b(second|2nd)\b', lambda m: 2),
        (r'\b(third|3rd)\b', lambda m: 3),
        (r'\b(fourth|4th)\b', lambda m: 4),
        (r'\b(fifth|5th)\b', lambda m: 5),
    ]

    ordinal_index = None
    for pattern, extractor in ordinal_patterns:
        match = re.search(pattern, text)
        if match:
            ordinal_index = extractor(match)
            break

    if ordinal_index is None:
        return None

    # Get last search results from event store
    last_items = tracker.get_last_search_results()
    if not last_items:
        logger.debug("ordinal_resolution_no_items", text=item_text)
        return None

    # Convert to 0-based index
    idx = ordinal_index - 1
    if 0 <= idx < len(last_items):
        resolved_name = last_items[idx]['name']
        logger.info(
            "ordinal_resolved",
            original=item_text,
            ordinal=ordinal_index,
            resolved_name=resolved_name
        )
        return resolved_name

    logger.debug("ordinal_out_of_range", text=item_text, ordinal=ordinal_index, items_count=len(last_items))
    return None


# ============================================================================
# TOOL FACTORY - Create session-scoped tools
# ============================================================================

def create_event_sourced_tools(session_id: str, customer_id: Optional[str] = None):
    """
    Factory to create event-sourced food ordering tools with session context.

    Tools are stateless - all state comes from SQL queries.
    Tools return final human-friendly messages (no LLM reformatting needed).
    Ordinal references ("option 1") are resolved via event store queries.
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
        from app.core.agui_events import emit_tool_activity, emit_cart_data, emit_quick_replies
        from app.core.preloader import get_menu_preloader
        from app.core.session_events import get_sync_session_tracker

        # Emit activity indicator for frontend
        emit_tool_activity(session_id, "add_to_cart")

        try:
            # Validate quantity
            if quantity <= 0:
                return "I need a positive quantity. How many would you like?"

            if quantity > 50:
                return "That's a lot! Maximum 50 per item. Contact us for bulk orders."

            # Use sync tracker (thread-safe for CrewAI)
            tracker = get_sync_session_tracker(session_id, UUID(customer_id) if customer_id else None)

            # Try to resolve ordinal reference first ("option 1", "first one", etc.)
            resolved_item_name = resolve_ordinal_reference(item, tracker)
            item_to_find = resolved_item_name if resolved_item_name else item.strip()

            # Find item in menu (preloader - sync, fast)
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading, please try again in a moment."

            found_item = preloader.find_item(item_to_find)
            if not found_item:
                return f"I couldn't find '{item}' on our menu. Try searching first?"

            item_id = UUID(found_item['id'])
            item_name = found_item['name']
            price = float(found_item['price'])

            # Add to cart (logs event + updates state) - tracker already created above
            cart = tracker.add_to_cart(
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

            # Emit quick replies for cart actions
            emit_quick_replies(session_id, [
                {"label": "🛒 View Cart", "action": "view cart"},
                {"label": "✅ Checkout", "action": "checkout"},
                {"label": "➕ Add More", "action": "add more items"},
            ])

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
        from app.core.agui_events import emit_tool_activity, emit_cart_data, emit_quick_replies
        from app.core.session_events import get_sync_session_tracker

        emit_tool_activity(session_id, "view_cart")

        try:
            # Use sync tracker (thread-safe for CrewAI)
            tracker = get_sync_session_tracker(session_id, UUID(customer_id) if customer_id else None)
            cart = tracker.get_cart_summary()

            # Emit cart card to frontend
            emit_cart_data(session_id, cart['items'], cart['total'])

            # Emit quick replies based on cart state
            if cart.get('items'):
                emit_quick_replies(session_id, [
                    {"label": "✅ Checkout", "action": "checkout"},
                    {"label": "➕ Add More", "action": "add more items"},
                    {"label": "🗑️ Remove Item", "action": "remove item"},
                ])
            else:
                emit_quick_replies(session_id, [
                    {"label": "📋 View Menu", "action": "show menu"},
                    {"label": "🔍 Search", "action": "search menu"},
                ])

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
        from app.core.agui_events import emit_tool_activity, emit_cart_data, emit_quick_replies
        from app.core.preloader import get_menu_preloader
        from app.core.session_events import get_sync_session_tracker

        emit_tool_activity(session_id, "remove_from_cart")

        try:
            # Find item
            preloader = get_menu_preloader()
            found_item = preloader.find_item(item.strip())

            if not found_item:
                return f"I couldn't find '{item}' in your cart."

            item_id = UUID(found_item['id'])

            # Use sync tracker (thread-safe for CrewAI)
            tracker = get_sync_session_tracker(session_id, UUID(customer_id) if customer_id else None)
            cart = tracker.remove_from_cart(item_id)

            if not cart.get('success', False):
                return f"'{item}' is not in your cart."

            # Emit updated cart
            emit_cart_data(session_id, cart['items'], cart['total'])

            # Emit quick replies based on remaining cart
            if cart.get('items'):
                emit_quick_replies(session_id, [
                    {"label": "🛒 View Cart", "action": "view cart"},
                    {"label": "✅ Checkout", "action": "checkout"},
                    {"label": "➕ Add More", "action": "add more items"},
                ])
            else:
                emit_quick_replies(session_id, [
                    {"label": "📋 View Menu", "action": "show menu"},
                    {"label": "🔍 Search", "action": "search menu"},
                ])

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
        from app.core.agui_events import emit_tool_activity, emit_menu_data, emit_search_results, emit_quick_replies
        from app.core.preloader import get_menu_preloader, get_current_meal_period
        from app.core.session_events import get_sync_session_tracker, EventType

        emit_tool_activity(session_id, "search_menu")

        try:
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading, please try again in a moment."

            # Get current meal period for filtering
            meal_period = get_current_meal_period()

            # Differentiate between browsing and searching:
            # - Browsing (empty/generic query): use MenuCard with meal filters
            # - Searching (specific query): use SearchResultsCard with availability info
            is_browsing = not query or query.lower() in ["", "all", "show all", "everything", "menu", "show menu"]

            if is_browsing:
                # Browsing: strict filter to current meal period, use MenuCard
                items = preloader.search(query, meal_period=meal_period, strict_meal_filter=True)
                if not items:
                    return f"No items available for {meal_period} right now. Try a different search?"

                # Log event with items for ordinal resolution ("option 1", "first one")
                tracker = get_sync_session_tracker(session_id, UUID(customer_id) if customer_id else None)
                # Store minimal item data for resolution
                items_for_event = [{'id': i['id'], 'name': i['name'], 'price': i.get('price', 0)} for i in items[:20]]
                tracker.log_event(EventType.MENU_VIEWED, {
                    'query': query,
                    'result_count': len(items),
                    'meal_period': meal_period,
                    'items': items_for_event  # For resolving "option 1", "second one", etc.
                })

                # Emit menu card to frontend
                emit_menu_data(session_id, items[:50], meal_period)

                # Emit quick replies for menu browsing
                emit_quick_replies(session_id, [
                    {"label": "🛒 View Cart", "action": "view cart"},
                    {"label": "🔍 Search Item", "action": "search for an item"},
                ])

                # Return formatted menu results
                from app.core.llm_formatter import format_menu_results
                return format_menu_results(items, query)

            else:
                # Searching: find ALL matching items, use SearchResultsCard
                all_matching_items = preloader.search(query, meal_period=None)

                if not all_matching_items:
                    return f"No items found for '{query}'. Try a different search?"

                # Check availability for each item
                def check_available(item):
                    meal_types = item.get("meal_types", [])
                    if isinstance(meal_types, str):
                        meal_types = [mt.strip() for mt in meal_types.split(",")]
                    return meal_period in meal_types or "All Day" in meal_types

                # Add is_available_now field to each item
                items_with_availability = []
                available_count = 0
                unavailable_count = 0

                for item in all_matching_items[:20]:  # Limit to 20 items
                    is_avail = check_available(item)
                    item_copy = dict(item)
                    item_copy["is_available_now"] = is_avail
                    items_with_availability.append(item_copy)
                    if is_avail:
                        available_count += 1
                    else:
                        unavailable_count += 1

                # Sort: available items first
                items_with_availability.sort(key=lambda x: (not x["is_available_now"], x["name"]))

                # Log event with items for ordinal resolution ("option 1", "first one")
                tracker = get_sync_session_tracker(session_id, UUID(customer_id) if customer_id else None)
                # Store minimal item data for resolution (only available items for ordering)
                items_for_event = [
                    {'id': i['id'], 'name': i['name'], 'price': i.get('price', 0)}
                    for i in items_with_availability if i.get('is_available_now', True)
                ]
                tracker.log_event(EventType.MENU_VIEWED, {
                    'query': query,
                    'result_count': len(items_with_availability),
                    'meal_period': meal_period,
                    'available_count': available_count,
                    'unavailable_count': unavailable_count,
                    'items': items_for_event  # For resolving "option 1", "second one", etc.
                })

                # Emit SearchResultsCard
                emit_search_results(
                    session_id=session_id,
                    query=query,
                    items=items_with_availability,
                    current_meal_period=meal_period,
                    available_count=available_count,
                    unavailable_count=unavailable_count
                )

                # Emit quick replies for search results
                emit_quick_replies(session_id, [
                    {"label": "🛒 View Cart", "action": "view cart"},
                    {"label": "✅ Checkout", "action": "checkout"},
                    {"label": "🔍 Search More", "action": "search for another item"},
                ])

                # Build response message with upselling
                # Human-friendly meal period name
                period_display = meal_period if meal_period != "All Day" else "late night"

                if available_count > 0 and unavailable_count > 0:
                    return f"I found {len(items_with_availability)} '{query}' options! {available_count} available now, {unavailable_count} at other times. Which one would you like?"
                elif available_count > 0:
                    if available_count == 1:
                        return f"I found {items_with_availability[0]['name']}! Would you like to add it to your cart?"
                    return f"I found {available_count} '{query}' options available now. Which one would you like?"
                else:
                    # No items available now - ALSO show menu card with available items (upselling)
                    available_items = preloader.search("", meal_period=meal_period, strict_meal_filter=True)

                    if available_items:
                        # Emit SECOND card: MenuCard with currently available items
                        emit_menu_data(session_id, available_items[:30], meal_period)

                    # Get meal periods from first unavailable item for better messaging
                    first_item_meals = items_with_availability[0].get("meal_types", []) if items_with_availability else []
                    if isinstance(first_item_meals, str):
                        first_item_meals = [m.strip() for m in first_item_meals.split(",")]
                    available_times = " & ".join([m for m in first_item_meals if m != "All Day"]) or "other times"

                    # Build response that drives action
                    if available_items:
                        return f"I found {unavailable_count} '{query}' options - they're available during {available_times}. Meanwhile, here's what's available now - want to explore?"
                    else:
                        return f"I found {unavailable_count} '{query}' options, but they're only available during {available_times}. Check the card above to see when you can order them."

        except Exception as e:
            logger.error("search_menu_failed", error=str(e), session_id=session_id)
            return "Sorry, I couldn't load the menu. Please try again."

    @tool("batch_add_to_cart")
    def batch_add_to_cart(items_with_quantities: str) -> str:
        """
        Add MULTIPLE different items to cart in one call. Emits a single cart update.

        Use this when customer orders 2+ DIFFERENT items in one message.
        Format: "item1:qty1, item2:qty2, ..."

        Args:
            items_with_quantities: Comma-separated "item:quantity" pairs.
                Examples:
                - "ghee masala dosa:2, ghee onion dosa:1"
                - "margherita pizza:1, coke:2, garlic bread:1"

        Returns:
            Final message confirming all items added.
        """
        from app.core.agui_events import emit_tool_activity, emit_cart_data, emit_quick_replies
        from app.core.preloader import get_menu_preloader
        from app.core.session_events import get_sync_session_tracker

        emit_tool_activity(session_id, "add_to_cart")

        try:
            tracker = get_sync_session_tracker(session_id, UUID(customer_id) if customer_id else None)
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading, please try again in a moment."

            # Parse "item:qty, item:qty, ..." format
            pairs = [p.strip() for p in items_with_quantities.split(",") if p.strip()]
            added_items = []
            failed_items = []
            cart = None

            for pair in pairs:
                # Support "item:qty" or just "item" (default qty=1)
                if ":" in pair:
                    item_name_raw, qty_str = pair.rsplit(":", 1)
                    try:
                        quantity = int(qty_str.strip())
                    except ValueError:
                        quantity = 1
                        item_name_raw = pair  # treat the whole thing as item name
                else:
                    item_name_raw = pair
                    quantity = 1

                item_name_raw = item_name_raw.strip()
                if quantity <= 0:
                    quantity = 1
                if quantity > 50:
                    quantity = 50

                # Resolve ordinal references
                resolved = resolve_ordinal_reference(item_name_raw, tracker)
                item_to_find = resolved if resolved else item_name_raw

                found_item = preloader.find_item(item_to_find)
                if not found_item:
                    failed_items.append(item_name_raw)
                    continue

                item_id = UUID(found_item['id'])
                name = found_item['name']
                price = float(found_item['price'])

                cart = tracker.add_to_cart(
                    item_id=item_id,
                    item_name=name,
                    quantity=quantity,
                    price=price
                )
                added_items.append(f"{quantity}x {name}")

            if not added_items:
                return f"I couldn't find these items on our menu: {', '.join(failed_items)}. Try searching first?"

            # Emit ONE cart update after all items added
            if cart:
                emit_cart_data(session_id, cart['items'], cart['total'])

            # Emit quick replies for cart actions
            emit_quick_replies(session_id, [
                {"label": "🛒 View Cart", "action": "view cart"},
                {"label": "✅ Checkout", "action": "checkout"},
                {"label": "➕ Add More", "action": "add more items"},
            ])

            # Build response
            summary = ", ".join(added_items)
            msg = f"Added {summary} to your cart!"
            if cart:
                msg += f" Cart total: ₹{cart['total']:.0f} ({cart['item_count']} items)."
            if failed_items:
                msg += f"\nCouldn't find: {', '.join(failed_items)}."
            msg += " Anything else?"
            return msg

        except Exception as e:
            logger.error("batch_add_to_cart_failed", error=str(e), session_id=session_id)
            return "Sorry, I couldn't add those items. Please try again."

    # Return all tools
    return [
        add_to_cart,
        batch_add_to_cart,
        view_cart,
        remove_from_cart,
        search_menu,
    ]
