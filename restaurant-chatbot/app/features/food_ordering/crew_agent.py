"""
CrewAI Food Ordering Agent
==========================
Production-ready food ordering agent following CrewAI best practices.

Architecture:
- Single agent with tools for menu, cart, order, and payment operations
- Tools use @tool decorator for auto-generated Pydantic schemas
- Core tools (cart/menu) are ASYNC - native CrewAI async support (no thread pool overhead)
- Order/payment tools remain sync (PostgreSQL via psycopg2, no AGUI emissions)
- Session-aware tools via factory pattern with closures

Best Practices Applied (from docs.crewai.com):
- respect_context_window=True for handling long conversations
- cache=True for repetitive tool usage
- max_iter limit to prevent infinite loops
- Proper error handling in all tools
- Clear tool descriptions for effective agent utilization

Performance Note:
- Async cart/menu tools eliminate ~10-20ms thread pool overhead per call
- AGUI event emissions use direct queue.put() instead of call_soon_threadsafe()
- Cart Redis operations use async client (no GIL contention)
- Order/payment tools use sync PostgreSQL (asyncpg migration would add complexity)
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from typing import Dict, Any, List, Optional
import structlog
import asyncio
import re
from datetime import datetime

# Phase 1 tools: Customer profile, FAQ, feedback
from app.features.food_ordering.new_tools_phase1 import get_all_phase1_tools
# Phase 2 tools: Advanced menu filtering
from app.features.food_ordering.new_tools_phase2 import get_all_phase2_tools
# Phase 3 tools: Table reservations
from app.features.food_ordering.new_tools_phase3 import get_all_phase3_tools
# Phase 4 & 5 tools: Order enhancements, policies & info
from app.features.food_ordering.new_tools_phase4_5 import get_all_phase4_tools, get_all_phase5_tools

logger = structlog.get_logger(__name__)

# Cache crews by session to avoid recreating them every message
_CREW_CACHE = {}
_CREW_VERSION = 30

# Concurrency configuration - custom ThreadPoolExecutor for handling concurrent users
import concurrent.futures
MAX_CONCURRENT_CREWS = 20  # Rate limit: max 20 concurrent crew executions
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=50,  # Thread pool size: can handle up to 50 concurrent requests
    thread_name_prefix="crew_worker"
)
_CREW_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_CREWS)


# Reference to the main event loop, set before crew kickoff.
# Used by run_async() to schedule coroutines on the main loop instead of
# creating a new loop (which causes "Future attached to a different loop"
# errors when async resources like HTTP clients are tied to the main loop).
_MAIN_LOOP = None


def run_async(coro):
    """
    Run async coroutine from sync context (inside @tool functions).

    CrewAI's @tool decorator doesn't properly await async functions,
    so tools must be sync `def`. This helper bridges the gap by running
    async code from within sync tools.

    Routes through _MAIN_LOOP to share DB/HTTP connections. Uses
    nest_asyncio when called from the main event loop thread so that
    asyncpg connections (bound to _MAIN_LOOP) work without deadlock.
    """
    if _MAIN_LOOP is None or not _MAIN_LOOP.is_running():
        return asyncio.run(coro)

    # Check if we're being called FROM the main event loop thread.
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if current_loop is _MAIN_LOOP:
        # ON the main loop — use nest_asyncio for re-entrant execution.
        # This keeps the coro on _MAIN_LOOP so asyncpg connections work.
        import nest_asyncio
        nest_asyncio.apply(_MAIN_LOOP)
        return _MAIN_LOOP.run_until_complete(coro)

    # Worker thread (with or without its own loop) — schedule on _MAIN_LOOP.
    future = asyncio.run_coroutine_threadsafe(coro, _MAIN_LOOP)
    return future.result(timeout=30)


def clean_crew_response(raw_response: str) -> str:
    """
    Extract the final answer from CrewAI output.

    CrewAI sometimes returns the planner's internal thoughts:
    "Thought: I need to show the menu\nAction: search_menu\nAction Input: {}\n..."

    We need to extract just the final human-readable answer.
    """
    import re

    response = str(raw_response).strip()

    # If response looks clean (no planner output), return as-is
    if not any(marker in response for marker in ['Thought:', 'Action:', 'Action Input:', 'Observation:']):
        return response

    # Try to find "Final Answer:" - this is what we want
    final_answer_match = re.search(r'Final Answer:\s*(.+?)(?:\n\n|$)', response, re.DOTALL | re.IGNORECASE)
    if final_answer_match:
        return final_answer_match.group(1).strip()

    # Try to find the last observation (tool output) - often the useful part
    observations = re.findall(r'Observation:\s*(.+?)(?=Thought:|Action:|$)', response, re.DOTALL)
    if observations:
        # Return the last observation, cleaned up
        last_obs = observations[-1].strip()
        if last_obs and len(last_obs) > 10:  # Make sure it's substantive
            return last_obs

    # Look for content after the last "Action Input:" that isn't another action
    parts = re.split(r'(?:Thought:|Action:|Action Input:|Observation:)', response)
    if parts:
        # Get the last substantive part
        for part in reversed(parts):
            cleaned = part.strip()
            if cleaned and len(cleaned) > 20 and not cleaned.startswith('{'):
                return cleaned

    # Fallback: Remove all planner markers and return what's left
    cleaned = re.sub(r'Thought:.*?(?=Action:|Observation:|$)', '', response, flags=re.DOTALL)
    cleaned = re.sub(r'Action:.*?(?=Action Input:|Observation:|$)', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'Action Input:.*?(?=Observation:|Thought:|$)', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'Observation:', '', cleaned)
    cleaned = cleaned.strip()

    if cleaned and len(cleaned) > 10:
        return cleaned

    # Last resort - return a helpful message
    logger.warning("crew_response_extraction_failed", raw_response=response[:200])
    return "I didn't quite catch that. Could you say that again? You can ask me about the menu, place an order, or make a reservation."


# ============================================================================
# SYNCHRONOUS HELPER FUNCTIONS
# All database and Redis operations are sync - no async hacks!
# ============================================================================

def _get_all_menu_items() -> List[Dict]:
    """
    Get all menu items from preloader cache (for deterministic menu emit).
    Returns all items without filtering by meal period.
    """
    return _get_menu_from_preloader(query="", use_meal_filter=False)


def _get_menu_from_preloader(query: str = "", use_meal_filter: bool = True, strict_filter: bool = False) -> List[Dict]:
    """
    Get menu items from preloader cache (instant, no DB).

    Args:
        query: Search term
        use_meal_filter: If True, filter by current meal period
        strict_filter: If True, ONLY show items for current meal (not other meals)

    Returns:
        List of menu items, filtered by current meal period
    """
    try:
        from app.core.preloader import get_menu_preloader, get_current_meal_period
        preloader = get_menu_preloader()

        if preloader.is_loaded:
            # Get current meal period for smart filtering
            meal_period = get_current_meal_period() if use_meal_filter else None
            # Disable strict filtering since most items don't have meal types assigned yet
            # When meal data is populated, re-enable: use_strict = strict_filter or (not query)
            use_strict = strict_filter
            return preloader.search(query, meal_period=meal_period, strict_meal_filter=use_strict)
    except Exception as e:
        logger.debug("preloader_not_available", error=str(e))
    return []


def _infer_category(item_name: str) -> str:
    """Infer category from item name for UI grouping."""
    name_lower = item_name.lower()

    # South Indian breakfast items
    if any(s in name_lower for s in ["dosa", "dosai", "idli", "vada", "upma", "pongal", "uttapam"]):
        return "South Indian Breakfast"
    elif "pizza" in name_lower:
        return "Pizza"
    elif "burger" in name_lower:
        return "Burgers"
    elif "salad" in name_lower:
        return "Salads"
    elif any(p in name_lower for p in ["pasta", "spaghetti", "carbonara", "bolognese", "fettuccine", "penne"]):
        return "Pasta"
    elif any(d in name_lower for d in ["cola", "juice", "water", "coffee", "tea", "soda", "lemonade", "shake"]):
        return "Beverages"
    elif any(d in name_lower for d in ["cake", "ice cream", "brownie", "pudding", "mousse", "dessert"]):
        return "Desserts"
    elif any(a in name_lower for a in ["fries", "wings", "nachos", "soup", "bread", "appetizer"]):
        return "Appetizers"
    else:
        return "Main Course"


# ============================================================================
# SYNC IMPLEMENTATION FUNCTIONS FOR CREW POOL
# These are called by the pooled crew's dynamic tools
# ============================================================================

def _search_menu_impl(query: str, session_id: str) -> str:
    """Sync implementation of search_menu for crew pool."""
    from app.core.agui_events import emit_tool_activity, emit_menu_data
    from app.core.redis import get_cart_sync
    from app.core.preloader import get_current_meal_period

    # Emit activity
    emit_tool_activity(session_id, "search_menu")

    # Get current meal period
    current_meal = get_current_meal_period()

    # Get menu from preloader (without meal filtering for searches, so we can provide context)
    items = _get_menu_from_preloader(query, use_meal_filter=False) if query else _get_menu_from_preloader(query)

    if not items:
        logger.warning("menu_preloader_empty", query=query)
        if query:
            return f"No items found matching '{query}'. Try browsing the full menu."
        return "Menu is loading. Please try again in a moment."

    # Check if search results are available in current meal period (when there's a query)
    if query:
        # Separate items by meal availability
        available_now = [item for item in items if current_meal in item.get("meal_types", [])]
        available_other_times = [item for item in items if current_meal not in item.get("meal_types", []) and item.get("meal_types")]

        # If found items but none available in current meal period
        if not available_now and available_other_times:
            # Get the meal periods when these items ARE available
            other_meals = set()
            for item in available_other_times:
                other_meals.update(item.get("meal_types", []))

            meal_times = {
                "Breakfast": "6 AM - 11 AM",
                "Lunch": "11 AM - 4 PM",
                "Dinner": "4 PM - 10 PM"
            }

            availability_text = ", ".join([f"{meal} ({meal_times.get(meal, '')})" for meal in sorted(other_meals)])
            item_names = ", ".join([item.get("name") for item in available_other_times[:3]])

            # Get suggestions for current meal
            current_meal_items = _get_menu_from_preloader("", use_meal_filter=True, strict_filter=True)
            suggestions = [item.get("name") for item in current_meal_items[:5]]
            suggestion_text = ", ".join(suggestions) if suggestions else "our current menu"

            return (f"I found {len(available_other_times)} items matching '{query}' ({item_names}), "
                    f"but they're only available during {availability_text}. "
                    f"It's currently {current_meal} time. "
                    f"Would you like to see our {current_meal.lower()} items instead? "
                    f"We have {suggestion_text} available right now!")

        # If some items ARE available now, emit them
        if available_now:
            try:
                cart_data = get_cart_sync(session_id)
                cart_items = cart_data.get("items", []) if cart_data else []
                cart_item_names = {item.get("name", "").lower() for item in cart_items}

                structured_items = []
                for item in available_now:
                    item_name = item.get("name", "")
                    item_price = item.get("price", 0)
                    # Skip items already in cart or with price 0
                    if item_name.lower() in cart_item_names or item_price <= 0:
                        continue
                    structured_items.append({
                        "name": item_name,
                        "price": item_price,
                        "category": _infer_category(item_name),
                        "description": item.get("description", ""),
                        "item_id": str(item.get("id", "")),
                        "meal_types": item.get("meal_types") or ["All Day"],
                    })

                if structured_items:
                    emit_menu_data(session_id, structured_items, current_meal_period=current_meal)

                # Also mention if there are items available at other times
                if available_other_times:
                    other_meals = set()
                    for item in available_other_times:
                        other_meals.update(item.get("meal_types", []))
                    availability_text = ", ".join(sorted(other_meals))

                    return (f"[MENU CARD DISPLAYED - {len(structured_items)} items available now] "
                            f"Found {len(available_now)} items available now. "
                            f"Note: {len(available_other_times)} more items are available during {availability_text}.")

                return f"[MENU CARD DISPLAYED - {len(structured_items)} items shown]"
            except Exception as e:
                logger.debug("search_menu_emit_failed", error=str(e))

    logger.debug("menu_from_preloader", query=query, count=len(items))

    # Track displayed menu
    try:
        from app.core.semantic_context import get_entity_graph
        graph = get_entity_graph(session_id)
        displayed_items = [item.get('name') for item in items[:15]]
        graph.set_displayed_menu(displayed_items)
    except Exception as e:
        logger.debug("entity_graph_update_failed", error=str(e))

    # Emit menu data for full menu requests
    if not query:
        try:
            current_meal = get_current_meal_period()
            cart_data = get_cart_sync(session_id)
            cart_items = cart_data.get("items", []) if cart_data else []
            cart_item_names = {item.get("name", "").lower() for item in cart_items}

            structured_items = []
            for item in items:
                item_name = item.get("name", "")
                item_price = item.get("price", 0)
                # Skip items already in cart or with price 0
                if item_name.lower() in cart_item_names or item_price <= 0:
                    continue
                structured_items.append({
                    "name": item_name,
                    "price": item_price,
                    "category": _infer_category(item_name),
                    "description": item.get("description", ""),
                    "item_id": str(item.get("id", "")),
                    "meal_types": item.get("meal_types", ["All Day"]),
                })

            if structured_items:
                emit_menu_data(session_id, structured_items, current_meal_period=current_meal)

            return f"Menu card displayed with {len(structured_items)} items available."
        except Exception as e:
            logger.debug("menu_data_emit_failed", error=str(e))

    menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:15]]
    return f"Menu items: {', '.join(menu_items)}" + (f" (+{len(items)-15} more)" if len(items) > 15 else "")




def _checkout_impl(order_type: str, session_id: str) -> str:
    """Sync implementation of checkout for crew pool.

    Note: Guest checkout is allowed - no authentication required.
    Uses session_id as customer identifier for guest orders.

    DETERMINISTIC FLOW: After checkout, payment workflow is automatically triggered.
    """
    from app.core.agui_events import emit_tool_activity, emit_quick_replies, emit_order_data
    from app.core.session_events import get_sync_session_tracker
    import uuid
    from datetime import datetime

    emit_tool_activity(session_id, "checkout")

    # Read cart from PostgreSQL session_cart (event-sourced)
    tracker = get_sync_session_tracker(session_id)
    cart_data = tracker.get_cart_summary()
    if not cart_data or not cart_data.get("items"):
        return "[EMPTY CART] Your cart is looking a bit empty! 😊 Let me help you add some delicious items before we proceed to checkout. What would you like to order?"

    # Always takeaway - no dine-in option
    order_type_clean = "take_away"

    # Prepare order and trigger payment workflow
    try:
        # Normalize cart items: PostgreSQL returns item_name/item_id,
        # downstream code expects name/id
        raw_items = cart_data.get("items", [])
        items = []
        for item in raw_items:
            normalized = dict(item)
            if "item_name" in normalized and "name" not in normalized:
                normalized["name"] = normalized["item_name"]
            if "item_id" in normalized and "id" not in normalized:
                normalized["id"] = str(normalized["item_id"])
            # Convert Decimal to float for JSON serialization
            if "price" in normalized:
                normalized["price"] = float(normalized["price"])
            if "total" in normalized:
                normalized["total"] = float(normalized["total"])
            items.append(normalized)
        subtotal = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)

        # Packaging charge per item - single source of truth in agui_events
        from app.core.agui_events import PACKAGING_CHARGE_PER_ITEM
        total_quantity = sum(i.get("quantity", 1) for i in items)
        packaging_charges = total_quantity * PACKAGING_CHARGE_PER_ITEM
        total = subtotal + packaging_charges

        # Generate order display ID
        order_display_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Store order as pending_payment in Redis (temporary)
        from app.core.redis import get_sync_redis_client
        import json
        redis_client = get_sync_redis_client()
        pending_order_key = f"pending_order:{session_id}"
        pending_order = {
            "order_id": order_display_id,
            "session_id": session_id,
            "items": items,
            "subtotal": subtotal,
            "packaging_charges": packaging_charges,
            "total": total,
            "order_type": order_type_clean,
            "status": "pending_payment",
            "created_at": datetime.now().isoformat()
        }
        redis_client.setex(pending_order_key, 3600, json.dumps(pending_order))  # Expire in 1 hour

        # Save to order history so receipt tool can find this order later
        history_key = f"order_history:{session_id}"
        redis_client.lpush(history_key, order_display_id)
        redis_client.expire(history_key, 86400 * 7)  # 7 days

        logger.info("pending_order_created", session_id=session_id, order_id=order_display_id)

        # Clear session_cart in PostgreSQL so cart shows empty after checkout
        from app.core.db_pool import SyncDBConnection
        try:
            with SyncDBConnection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE session_cart SET is_active = FALSE, updated_at = NOW() WHERE session_id = %s AND is_active = TRUE",
                        (session_id,)
                    )
                    conn.commit()
        except Exception as clear_err:
            logger.warning("cart_clear_after_checkout_failed", error=str(clear_err))

        # =====================================================================
        # PAYMENT WORKFLOW — Store info for after-crew trigger
        # =====================================================================
        # Don't call init_payment_workflow() here (worker thread).
        # Store payment info in Redis so the after-crew block in
        # restaurant_crew.py can call run_payment_workflow() on the
        # main async loop where DB/HTTP connections work correctly.
        payment_info = {
            "order_display_id": order_display_id,
            "total": total,
            "session_id": session_id,
        }
        redis_client.setex(
            f"checkout_payment_info:{session_id}",
            3600,
            json.dumps(payment_info)
        )

        logger.info(
            "checkout_payment_info_stored",
            session_id=session_id,
            order_id=order_display_id,
            amount=total
        )

        # Return confirmation — run_payment_workflow() will show the
        # payment card after the crew finishes (on the main thread).
        items_summary = ", ".join([f"{i.get('name')} x{i.get('quantity', 1)}" for i in items[:3]])
        if len(items) > 3:
            items_summary += f" and {len(items) - 3} more"

        return (
            f"[CHECKOUT COMPLETE] Order {order_display_id} created. "
            f"Items: {items_summary}. "
            f"Subtotal: Rs.{subtotal:.0f}, Packaging: Rs.{packaging_charges:.0f}, "
            f"Total: Rs.{total:.0f} (Take-away). "
            f"Online payment via Razorpay has been automatically initiated. "
            f"The payment link is now displayed to the customer. "
            f"Let them know their order is placed and they can complete payment using the link shown."
        )

    except Exception as e:
        logger.error("checkout_failed", error=str(e), exc_info=True)
        return "Sorry, there was an issue placing your order. Please try again."


def _cancel_order_impl(session_id: str) -> str:
    """Sync implementation of cancel_order for crew pool."""
    from app.core.agui_events import emit_tool_activity
    emit_tool_activity(session_id, "cancel_order")
    return "Order cancellation requires an order ID. What order would you like to cancel?"




def _get_item_details_impl(item_name: str, session_id: str) -> str:
    """Sync implementation of get_item_details for crew pool."""
    from app.core.agui_events import emit_tool_activity
    from app.core.preloader import get_menu_preloader

    emit_tool_activity(session_id, "get_item_details")

    preloader = get_menu_preloader()
    item = preloader.find_item(item_name) if preloader.is_loaded else None

    if not item:
        return f"Sorry, couldn't find '{item_name}'. Try 'show menu' to see available items."

    return f"{item.get('name')}: Rs.{item.get('price')}. {item.get('description', 'A delicious choice!')}"


def _reorder_impl(session_id: str) -> str:
    """Sync implementation of reorder for crew pool."""
    from app.core.agui_events import emit_tool_activity
    emit_tool_activity(session_id, "reorder")
    return "To reorder, I need your previous order ID. What order would you like to reorder?"


def _set_special_instructions_impl(item_name: str, instructions: str, session_id: str) -> str:
    """Sync implementation of set_special_instructions for crew pool."""
    from app.core.agui_events import emit_tool_activity
    from app.core.redis import get_cart_sync, save_cart_sync

    emit_tool_activity(session_id, "set_special_instructions")

    cart_data = get_cart_sync(session_id)
    if not cart_data or not cart_data.get("items"):
        return "Your cart is empty. Add items first."

    items = cart_data.get("items", [])
    item_lower = item_name.lower()

    for item in items:
        if item.get("name", "").lower() == item_lower:
            item["special_instructions"] = instructions
            save_cart_sync(session_id, cart_data)
            return f"Added instructions for {item.get('name')}: '{instructions}'"

    return f"'{item_name}' not found in your cart."


def _get_order_receipt_impl(order_id: str, session_id: str) -> str:
    """Sync implementation of get_order_receipt for crew pool.

    Reads receipt data from Redis payment_state (which has full item details)
    rather than PostgreSQL (which doesn't store item_name/quantity).
    """
    from app.core.agui_events import emit_tool_activity, emit_receipt_link
    from datetime import datetime

    emit_tool_activity(session_id, "get_order_receipt")

    try:
        # Get payment state from Redis — has full order details including items
        from app.services.payment_state_service import get_payment_state
        payment_state = get_payment_state(session_id)

        if not payment_state.get("order_id"):
            return "No recent orders found. Please place an order first."

        if payment_state.get("step") not in ["payment_success", "cash_selected"]:
            return "Payment hasn't been completed yet. Please complete payment first."

        # Extract receipt data from payment_state
        order_number = payment_state.get("order_number") or payment_state.get("order_id", "N/A")
        amount = float(payment_state.get("amount", 0))
        payment_id = payment_state.get("payment_id", "")
        items = payment_state.get("items", [])
        order_type_raw = payment_state.get("order_type", "")
        order_type = "Take Away" if "take" in order_type_raw.lower() else "Dine In" if order_type_raw else ""
        subtotal = float(payment_state.get("subtotal", 0))
        packaging = float(payment_state.get("packaging_charges", 0))

        completed_at = payment_state.get("completed_at", "")
        if completed_at:
            try:
                dt = datetime.fromisoformat(completed_at)
                date_str = dt.strftime('%B %d, %Y at %I:%M %p')
            except (ValueError, TypeError):
                date_str = completed_at
        else:
            date_str = datetime.now().strftime('%B %d, %Y at %I:%M %p')

        # Emit receipt card with PDF download link via AGUI
        import os
        base_url = os.getenv("FRONTEND_URL", "").rstrip("/")
        download_url = f"{base_url}/api/v1/payment/receipt/pdf?session_id={session_id}"
        receipt_items = []
        for item in items:
            name = item.get("name") or item.get("item_name", "Item")
            qty = int(item.get("quantity", 1))
            price = float(item.get("price", 0))
            receipt_items.append({"name": name, "quantity": qty, "price": price})

        emit_receipt_link(
            session_id=session_id,
            order_number=order_number,
            amount=amount,
            download_url=download_url,
            items=receipt_items
        )

        # Return text for the LLM (tag stripped by post-processing, rest may be echoed)
        return (
            f"[RECEIPT DISPLAYED] Here's your receipt for order {order_number}! "
            f"You can download the PDF using the button below."
        )

    except Exception as e:
        logger.error("get_order_receipt_failed", error=str(e), exc_info=True)
        return f"Error retrieving receipt: {str(e)}"


def _get_order_status_impl(order_id: str, session_id: str) -> str:
    """Sync implementation of get_order_status for crew pool."""
    from app.core.agui_events import emit_tool_activity
    from app.core.redis import get_sync_redis_client
    from app.core.db_pool import SyncDBConnection

    emit_tool_activity(session_id, "get_order_status")

    try:
        redis_client = get_sync_redis_client()
        order_display_id = order_id.strip().upper() if order_id else None

        # If no order_id provided, get most recent
        if not order_display_id:
            history_key = f"order_history:{session_id}"
            recent_orders = redis_client.lrange(history_key, 0, 0)
            if not recent_orders:
                return "No recent orders found."
            order_display_id = recent_orders[0].decode() if isinstance(recent_orders[0], bytes) else recent_orders[0]

        # Get order status from PostgreSQL
        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT o.order_invoice_number, ost.order_status_name,
                           ott.order_type_name, o.created_at, o.total_amount
                    FROM orders o
                    LEFT JOIN order_status_type ost ON o.order_status_type_id = ost.order_status_type_id
                    LEFT JOIN order_type_table ott ON o.order_type_id = ott.order_type_id
                    WHERE o.order_invoice_number = %s
                """, (order_display_id,))
                order = cur.fetchone()

        if not order:
            return f"Order {order_display_id} not found."

        display_id, status, order_type, created_at, total = order
        date_str = created_at.strftime('%I:%M %p') if hasattr(created_at, 'strftime') else str(created_at)

        return f"Order {display_id} ({order_type}) - Status: {status}\nPlaced at: {date_str}\nTotal: Rs.{total}"

    except Exception as e:
        logger.error("get_order_status_failed", error=str(e))
        return f"Error checking order status: {str(e)}"


def _get_order_history_impl(session_id: str) -> str:
    """Sync implementation of get_order_history for crew pool."""
    from app.core.agui_events import emit_tool_activity
    from app.core.redis import get_sync_redis_client
    from app.core.db_pool import SyncDBConnection

    emit_tool_activity(session_id, "get_order_history")

    try:
        redis_client = get_sync_redis_client()
        history_key = f"order_history:{session_id}"
        order_ids = redis_client.lrange(history_key, 0, 9)  # Last 10 orders

        if not order_ids:
            return "You haven't placed any orders yet."

        # Get orders from PostgreSQL
        with SyncDBConnection() as conn:
            with conn.cursor() as cur:
                placeholders = ','.join(['%s'] * len(order_ids))
                cur.execute(f"""
                    SELECT o.order_invoice_number, ost.order_status_name,
                           ott.order_type_name, o.created_at, o.total_amount
                    FROM orders o
                    LEFT JOIN order_status_type ost ON o.order_status_type_id = ost.order_status_type_id
                    LEFT JOIN order_type_table ott ON o.order_type_id = ott.order_type_id
                    WHERE o.order_invoice_number IN ({placeholders})
                    ORDER BY o.created_at DESC
                """, tuple(oid.decode() if isinstance(oid, bytes) else oid for oid in order_ids))
                orders = cur.fetchall()

        if not orders:
            return "No orders found in history."

        history_lines = ["Your Recent Orders:"]
        for display_id, status, order_type, created_at, total in orders:
            date_str = created_at.strftime('%b %d, %I:%M %p') if hasattr(created_at, 'strftime') else str(created_at)
            history_lines.append(f"  {display_id} - {status} ({order_type}) - Rs.{total} - {date_str}")

        return "\n".join(history_lines)

    except Exception as e:
        logger.error("get_order_history_failed", error=str(e))
        return f"Error retrieving order history: {str(e)}"


# ============================================================================
# QUICK REPLY AGENT - LLM-based intelligent quick action selection
# ============================================================================

# Available quick action sets that the agent can choose from
# Comprehensive 43 action sets covering all 50+ tools through contextual flow
QUICK_ACTION_SETS = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENTRY & WELCOME (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "greeting_welcome": [
        {"label": "🍔 Order Food", "action": "show me the menu"},
        {"label": "🛒 View Cart", "action": "view my cart"},
        {"label": "🎁 Today's Deals", "action": "today's specials and offers"},
        {"label": "📅 Book a Table", "action": "book a table"},
        {"label": "❓ Help & FAQs", "action": "help"},
    ],

    "explore_features": [
        {"label": "🍔 Order Food", "action": "show me the menu"},
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "📅 Book Table", "action": "book a table"},
        {"label": "🔍 Check Allergens", "action": "check my allergens"},
        {"label": "🎁 Offers & Rewards", "action": "check offers and deals"},
        {"label": "❓ Get Help", "action": "help and faqs"},
    ],

    "first_time_user": [
        {"label": "🍔 Browse Menu", "action": "show me the menu"},
        {"label": "🔍 Search Items", "action": "search for items"},
        {"label": "🎁 Today's Specials", "action": "today's specials"},
        {"label": "🔍 Dietary Options", "action": "dietary and allergen options"},
        {"label": "❓ How It Works", "action": "how to order"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MENU DISCOVERY & BROWSING (5 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "menu_displayed": [
        {"label": "🔍 Search Items", "action": "search for specific items"},
        {"label": "🎁 Today's Specials", "action": "today's specials"},
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "📅 Book Table", "action": "book a table"},
    ],

    "menu_discovery": [
        {"label": "🔍 Search Items", "action": "search for items"},
        {"label": "🎁 Today's Specials", "action": "today's specials"},
        {"label": "🛒 View Cart", "action": "view cart"},
    ],

    "cuisine_browse": [
        {"label": "🔍 Search Items", "action": "search for items"},
        {"label": "🔙 Back to Menu", "action": "show full menu"},
        {"label": "🛒 View Cart", "action": "view cart"},
    ],

    "item_details_shown": [
        {"label": "➕ Add to Cart", "action": "add this to cart"},
        {"label": "🛒 View Cart", "action": "view cart"},
    ],

    "deals_inquiry": [
        {"label": "🍔 Browse Menu", "action": "show menu"},
        {"label": "🛒 View Cart", "action": "view cart"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CART & ORDERING (6 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "added_to_cart": [
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "add more items"},
        {"label": "❤️ Add to Favorites", "action": "add to favorites"},
    ],

    "added_to_cart_with_upsell": [
        {"label": "🍟 Add Sides?", "action": "show sides and drinks"},
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "show menu"},
    ],

    "view_cart": [
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "show menu"},
        {"label": "✏️ Add Instructions", "action": "add special instructions"},
        {"label": "🗑️ Clear Cart", "action": "clear cart"},
    ],

    "view_cart_high_value": [
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "show menu"},
        {"label": "✏️ Add Instructions", "action": "add special instructions"},
    ],

    "checkout_options": [
        {"label": "✅ Order Now", "action": "checkout now"},
        {"label": "🔙 Back to Cart", "action": "view cart"},
    ],

    "cart_empty_reminder": [
        {"label": "🍔 Browse Menu", "action": "show menu"},
        {"label": "📜 Recent Orders", "action": "show my order history"},
        {"label": "🔄 Reorder Last", "action": "reorder my last order"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CHECKOUT & PAYMENT (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "order_type": [
        {"label": "📦 Take Away", "action": "take away"},
    ],

    "payment_method": [
        {"label": "💳 Pay Online", "action": "pay_online"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # POST-ORDER (4 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "order_confirmed": [
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
        {"label": "🍔 Order More", "action": "show menu"},
    ],

    "payment_completed": [
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
        {"label": "⭐ Rate Order", "action": "rate this order"},
        {"label": "❤️ Add to Favorites", "action": "add items to favorites"},
        {"label": "🔄 Reorder", "action": "reorder this"},
    ],

    "post_delivery": [
        {"label": "⭐⭐⭐⭐⭐ Rate 5 Stars", "action": "rate 5 stars"},
        {"label": "💬 Leave Feedback", "action": "submit feedback"},
        {"label": "🔄 Reorder Same", "action": "reorder last order"},
        {"label": "❤️ Save Favorites", "action": "add to favorites"},
    ],

    "order_tracking": [
        {"label": "🔄 Refresh Status", "action": "refresh order status"},
        {"label": "❌ Cancel Order", "action": "cancel this order"},
        {"label": "📞 Contact Support", "action": "contact support"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
    ],

    "receipt_shown": [
        {"label": "🍔 Order More", "action": "show menu"},
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "⭐ Rate Order", "action": "rate this order"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TABLE BOOKING (4 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "booking_inquiry": [
        {"label": "📅 Book Table", "action": "book a table now"},
        {"label": "🕐 Check Availability", "action": "check table availability"},
        {"label": "📖 My Bookings", "action": "show my bookings"},
        {"label": "❓ Booking Help", "action": "help with booking"},
    ],

    "availability_shown": [
        {"label": "✅ Confirm Booking", "action": "book this table"},
        {"label": "🔄 Check Other Times", "action": "show other time slots"},
        {"label": "🏠 Back to Home", "action": "go back"},
    ],

    "booking_confirmed": [
        {"label": "📖 View Bookings", "action": "show my bookings"},
        {"label": "🍔 Pre-Order Food", "action": "order food for booking"},
        {"label": "✏️ Modify Booking", "action": "modify booking"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    "booking_management": [
        {"label": "✏️ Modify Booking", "action": "modify my booking"},
        {"label": "❌ Cancel Booking", "action": "cancel booking"},
        {"label": "📅 Book Another", "action": "book another table"},
        {"label": "🍔 Order Food", "action": "show menu"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DIETARY & ALLERGENS (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "dietary_inquiry": [
        {"label": "🔍 Check My Allergens", "action": "show my allergens"},
        {"label": "➕ Add Allergen", "action": "add allergen"},
        {"label": "💚 Dietary Preferences", "action": "show dietary preferences"},
        {"label": "🥗 Veg Options", "action": "show vegetarian items"},
        {"label": "📊 Nutrition Info", "action": "nutrition information"},
    ],

    "allergen_management": [
        {"label": "➕ Add Allergen", "action": "add new allergen"},
        {"label": "➖ Remove Allergen", "action": "remove allergen"},
        {"label": "🔍 Filter Menu", "action": "filter menu by my allergens"},
        {"label": "🏠 Back", "action": "go back"},
    ],

    "health_conscious": [
        {"label": "🥗 Veg Options", "action": "show vegetarian options"},
        {"label": "📊 Nutrition Info", "action": "show nutrition info"},
        {"label": "💪 High Protein", "action": "show high protein items"},
        {"label": "🌿 Vegan Options", "action": "show vegan items"},
        {"label": "🍔 All Menu", "action": "show full menu"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HELP & SUPPORT (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "help_inquiry": [
        {"label": "❓ View FAQs", "action": "show faqs"},
        {"label": "🕐 Operating Hours", "action": "what are your hours"},
        {"label": "📜 Policies", "action": "show restaurant policies"},
        {"label": "🚚 Delivery Info", "action": "delivery information"},
        {"label": "📞 Contact Support", "action": "contact support"},
    ],

    "faq_categories": [
        {"label": "📦 Order & Delivery", "action": "order and delivery faqs"},
        {"label": "💳 Payment", "action": "payment faqs"},
        {"label": "📅 Booking", "action": "booking faqs"},
        {"label": "🔄 Returns", "action": "return and refund faqs"},
        {"label": "🔙 Back", "action": "back to help"},
    ],

    "policy_shown": [
        {"label": "🚚 Delivery Policy", "action": "delivery policy"},
        {"label": "🔄 Refund Policy", "action": "refund policy"},
        {"label": "📜 Terms of Service", "action": "terms of service"},
        {"label": "🏠 Back", "action": "go back"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ACCOUNT & FAVORITES (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "my_account": [
        {"label": "📜 Order History", "action": "show my order history"},
        {"label": "❤️ My Favorites", "action": "show my favorites"},
        {"label": "📖 My Bookings", "action": "show my bookings"},
        {"label": "💬 My Feedback", "action": "show my feedback history"},
        {"label": "⚙️ Preferences", "action": "show my preferences"},
    ],

    "my_favorites": [
        {"label": "❤️ View Favorites", "action": "show my favorites"},
        {"label": "🔄 Reorder Favorite", "action": "reorder from favorites"},
        {"label": "➕ Add New Favorite", "action": "add to favorites"},
        {"label": "🏠 Back", "action": "go back"},
    ],

    "order_history_shown": [
        {"label": "🔄 Reorder", "action": "reorder from history"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
        {"label": "⭐ Rate Past Order", "action": "rate past order"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEEDBACK & RATING (2 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "feedback_prompt": [
        {"label": "⭐ Rate Order", "action": "rate my order"},
        {"label": "💬 Leave Feedback", "action": "submit feedback"},
        {"label": "👍 Everything Great!", "action": "rate 5 stars"},
        {"label": "Later", "action": "maybe later"},
    ],

    "rating_submitted": [
        {"label": "💬 Add Comments", "action": "add feedback comments"},
        {"label": "🔄 Reorder Same", "action": "reorder this"},
        {"label": "❤️ Add to Favorites", "action": "add to favorites"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILITY & FALLBACK (4 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "continue_ordering": [
        {"label": "🍔 Show Menu", "action": "show menu"},
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "❓ Get Help", "action": "help"},
    ],

    "quantity": [
        {"label": "1", "action": "1"},
        {"label": "2", "action": "2"},
        {"label": "3", "action": "3"},
        {"label": "Other", "action": "__OTHER__"},
    ],

    "yes_no": [
        {"label": "✅ Yes", "action": "yes"},
        {"label": "❌ No", "action": "no"},
    ],

    "which_item": [
        # Dynamic - populated based on items mentioned in response
    ],

    "none": [],
}

# Default fallback quick replies - shown when classifier fails or returns empty
DEFAULT_QUICK_REPLIES = [
    {"label": "🍔 Show Menu", "action": "show menu"},
    {"label": "🛒 View Cart", "action": "view cart"},
    {"label": "✅ Checkout", "action": "checkout"},
    {"label": "❓ Help", "action": "help"},
]

QUICK_REPLY_AGENT_PROMPT = """You are a quick action selector for a restaurant chatbot. Your job is to proactively guide users through the ordering journey by showing contextual action buttons.

🎯 CORE PRINCIPLE: Be the user's driver! Users don't know what the chatbot can do - show them the way at every step.

📋 Available Action Sets (43 total):

━━━ ENTRY & WELCOME ━━━
- greeting_welcome: User greets (hi/hello/hey) or response welcomes user → Show main features (Order, View Cart, Deals, Book Table, Help)
- explore_features: User asks "what can you do" or capabilities → Show all major features (Order, Track, Book, Allergens, Offers, Help)
- first_time_user: New user with no history → Show onboarding options (Browse Menu, Search, Specials, Dietary, How It Works)

━━━ MENU DISCOVERY ━━━
- menu_displayed: Menu shown (response says "here's our menu" or lists menu items) → Guide exploration (Search, Specials, Cart, Book Table)
- menu_discovery: User exploring menu → Show discovery options (Search, Specials, Cart)
- cuisine_browse: Response shows cuisines or user asks about cuisine types → Show Continental cuisine option (only available cuisine)
- item_details_shown: Showing details of specific item → Action buttons (Add to Cart, Nutrition, Check Stock, Allergens, Favorites)
- deals_inquiry: User asks about deals/offers/specials → Show promo options (Combos, Specials, Promo Code, Loyalty Rewards)

━━━ CART & ORDERING ━━━
- added_to_cart: Item added to cart (response: "added X to cart") → Next steps (View Cart, Checkout, Add More, Add to Favorites)
- added_to_cart_with_upsell: Added main dish (burger/pizza/etc) → Suggest upsells (Add Sides?, View Cart, Checkout, Add More)
- view_cart: Showing cart contents → Cart actions (Checkout, Add More, Apply Promo, Add Instructions, Clear Cart)
- view_cart_high_value: Cart shown with total > Rs.500 → Highlight promo (Checkout, Apply Promo Code★, Add More, Check Allergens)
- checkout_options: Before final checkout → Final options (Order Now, Schedule Later, Apply Promo, Back to Cart)
- cart_empty_reminder: User tries checkout but cart empty → Redirect (Browse Menu, Search Items, Recent Orders, Reorder Last)

━━━ CHECKOUT & PAYMENT ━━━
- order_type: Order type confirmed → Takeaway (Take Away)
- payment_method: Asking payment method (response: "how would you like to pay") → Payment options (Pay Online)

━━━ POST-ORDER ━━━
- order_confirmed: Order placed (response has "Order ID" but NO payment yet) → Post-order (Track Order, View Receipt, Order More)
- payment_completed: Payment successful (response: "payment successful" or "paid") → Full post-order (Track, Receipt, Rate, Favorites, Reorder)
- post_delivery: 30+ mins after delivery → Feedback prompt (Rate 5 Stars, Leave Feedback, Reorder Same, Save Favorites)
- order_tracking: User tracking order → Tracking actions (Refresh Status, Cancel Order, Contact Support, View Receipt)
- receipt_shown: Receipt displayed (response: "receipt" or "RECEIPT DISPLAYED" or "download") → Post-receipt (Order More, Track, Rate, Home)

━━━ TABLE BOOKING ━━━
- booking_inquiry: User asks about booking or wants to book → Booking options (Book Table, Check Availability, My Bookings, Help)
- availability_shown: Response shows available time slots → Booking action (Confirm Booking, Check Other Times, Back)
- booking_confirmed: Booking confirmed (response: "booking confirmed") → Post-booking (View Bookings, Pre-Order Food, Modify, Home)
- booking_management: Showing user's bookings → Manage bookings (Modify, Cancel, Book Another, Order Food)

━━━ DIETARY & ALLERGENS ━━━
- dietary_inquiry: User mentions diet/allergens/health concerns → Dietary options (Check Allergens, Add Allergen, Dietary Prefs, Veg, Nutrition)
- allergen_management: Managing allergen preferences → Allergen actions (Add, Remove, Filter Menu, Back)
- health_conscious: User filtering by health/diet → Health options (Veg, Nutrition Info, High Protein, Vegan, All Menu)

━━━ HELP & SUPPORT ━━━
- help_inquiry: User asks for help or has questions → Help options (FAQs, Operating Hours, Policies, Delivery Info, Contact Support)
- faq_categories: Showing FAQ categories → FAQ topics (Order & Delivery, Payment, Booking, Returns, Back)
- policy_shown: Showing policies → Policy types (Delivery Policy, Refund Policy, Terms, Back)

━━━ ACCOUNT & FAVORITES ━━━
- my_account: User asks about account/profile → Account options (Order History, Favorites, Bookings, Feedback, Preferences)
- my_favorites: Showing favorites → Favorites actions (View, Reorder Favorite, Add New, Back)
- order_history_shown: Showing past orders → History actions (Reorder, View Receipt, Rate Past Order, Home)

━━━ FEEDBACK & RATING ━━━
- feedback_prompt: After delivery, prompting feedback → Feedback options (Rate Order, Leave Feedback, Everything Great!, Later)
- rating_submitted: User just rated order → Follow-up (Add Comments, Reorder Same, Add to Favorites, Home)

━━━ UTILITY & FALLBACK ━━━
- continue_ordering: General "anything else?" or continue prompt → General options (Show Menu, View Cart, Checkout, Get Help)
- quantity: Asking "how many" → Number buttons (1, 2, 3, Other)
- yes_no: Simple yes/no question → Binary choice (Yes, No)
- none: ONLY for purely informational responses with NO next action (rare - default to helpful actions!)

🎯 CRITICAL DECISION RULES:
1. Payment question → ALWAYS "payment_method"
2. Welcome/greeting → "greeting_welcome"
3. Menu shown → "menu_displayed"
4. Item added → "added_to_cart" OR "added_to_cart_with_upsell" (if burger/pizza/main dish)
5. Cart shown + total > Rs.500 → "view_cart_high_value" (highlight promo!)
6. Cart shown + total < Rs.500 → "view_cart"
7. User asks capabilities → "explore_features"
8. Payment successful → "payment_completed" (NOT order_confirmed)
9. Order placed but NOT paid → "order_confirmed"
10. Receipt shown/displayed → "receipt_shown" (NOT view_cart!)

🚗 GUIDE PRINCIPLE:
- Default to showing helpful actions rather than "none"
- Think: "What would the user logically want to do next?"
- Proactively expose features users don't know exist
- Use context to show 5-6 relevant buttons per response

11. Search results displayed (response lists menu items with prices) → "menu_displayed"
12. AI asking "which one" / disambiguating between items → "menu_displayed"

Response to analyze:
"{response}"

Return JSON only:
{{"action_set": "<set_name>"}}"""


def get_response_quick_replies(response: str) -> List[Dict[str, str]]:
    """
    Use a small LLM agent to intelligently determine which quick reply buttons to show.

    This replaces fragile rule-based detection with contextual understanding.
    Uses GPT-4o-mini for speed and cost efficiency.

    Returns:
        List of reply dicts, or empty list if none applicable.
    """
    import json

    try:
        from langchain_openai import ChatOpenAI
        from app.ai_services.llm_manager import get_llm_manager

        # Get API key from LLM manager pool (round-robin across validated accounts)
        llm_manager = get_llm_manager()
        api_key = llm_manager.get_next_api_key()

        # Use GPT-4o-mini for speed (fastest, cheapest, good enough for classification)
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
            max_tokens=100,
            api_key=api_key,
        )

        # Get the agent's decision
        prompt = QUICK_REPLY_AGENT_PROMPT.format(response=response[:500])  # Limit response length
        result = llm.invoke(prompt)

        # Parse the JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            content = result.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            decision = json.loads(content)
            action_set = decision.get("action_set", "none")
            items = decision.get("items")

            logger.debug("quick_reply_agent_decision",
                        action_set=action_set,
                        items=items)

            # Get the replies for the selected action set
            if action_set == "which_item" and items:
                # Reject placeholder/generic names (GPT-4o-mini sometimes copies template)
                PLACEHOLDER_PATTERN = re.compile(r'^item\s*\d+$', re.IGNORECASE)
                real_items = [i for i in items if not PLACEHOLDER_PATTERN.match(i.strip())]
                if not real_items:
                    logger.warning("which_item_placeholder_names", raw_items=items)
                    # Fall back to menu_displayed instead of showing "item1, item2"
                    return QUICK_ACTION_SETS.get("menu_displayed", DEFAULT_QUICK_REPLIES)

                # Dynamic item selection buttons
                replies = []
                for item in real_items[:4]:  # Max 4 items
                    replies.append({
                        "label": item,
                        "action": item,
                        "icon": "food",
                        "variant": "success"
                    })
                replies.append({
                    "label": "Something else",
                    "action": "__OTHER__",
                    "icon": "edit",
                    "variant": "secondary"
                })
                return replies
            elif action_set in QUICK_ACTION_SETS:
                replies = QUICK_ACTION_SETS[action_set]
                # If the selected set is empty (e.g. "none"), use default fallback
                return replies if replies else DEFAULT_QUICK_REPLIES
            else:
                logger.warning("quick_reply_agent_unknown_set", action_set=action_set)
                return DEFAULT_QUICK_REPLIES

        except json.JSONDecodeError as e:
            logger.warning("quick_reply_agent_json_error", error=str(e), content=content[:100])
            return DEFAULT_QUICK_REPLIES

    except Exception as e:
        logger.warning("quick_reply_agent_failed", error=str(e))
        return DEFAULT_QUICK_REPLIES


def _emit_response_quick_replies(session_id: str, response: str):
    """
    DEPRECATED: Use get_response_quick_replies() and emit via emitter directly.

    This function uses thread-safe emission which can cause race conditions
    with streaming. Prefer using get_response_quick_replies() + emitter.emit_quick_replies().
    """
    from app.core.agui_events import emit_quick_replies

    replies = get_response_quick_replies(response)
    if replies:
        emit_quick_replies(session_id, replies)
        logger.debug("quick_replies_emitted_legacy", session_id=session_id, count=len(replies))


async def _get_menu_from_db(query: str = "") -> List[Dict]:
    """Fallback: fetch menu from database using async connection pool."""
    try:
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as conn:
            rows = await conn.fetch("""
                SELECT
                    menu_item_id as id,
                    menu_item_name as name,
                    menu_item_price as price,
                    menu_item_description as description,
                    menu_item_in_stock as is_available
                FROM menu_item
                WHERE is_deleted = FALSE
                AND menu_item_status = 'active'
                ORDER BY menu_item_name
            """)

        items = [
            {
                "id": str(row['id']),
                "name": row['name'],
                "price": float(row['price']),
                "description": row['description'] or "",
                "is_available": row['is_available']
            }
            for row in rows
        ]

        # Filter if query provided
        if query and query.lower() not in ["", "all", "show all", "everything"]:
            query_lower = query.lower()
            items = [
                item for item in items
                if query_lower in item.get("name", "").lower()
                or query_lower in item.get("description", "").lower()
            ]

        return [item for item in items if item.get("is_available", True)]

    except Exception as e:
        logger.error("db_menu_fetch_failed", error=str(e))
        return []


async def _find_item_by_name(item_name: str) -> Optional[Dict]:
    """Find menu item by name (fuzzy match). Tries preloader first, then DB."""
    search_term = item_name.lower().strip()
    search_term_singular = search_term.rstrip('s') if search_term.endswith('s') else search_term

    # Try preloader first (instant)
    try:
        from app.core.preloader import get_menu_preloader
        preloader = get_menu_preloader()

        if preloader.is_loaded:
            found = preloader.find_item(item_name)
            if found:
                logger.debug("item_found_in_preloader", item=item_name)
                return found
    except Exception as e:
        logger.debug("preloader_item_lookup_failed", error=str(e))

    # Fallback to DB (async)
    try:
        from app.core.db_pool import AsyncDBConnection

        async with AsyncDBConnection() as conn:
            row = await conn.fetchrow("""
                SELECT menu_item_id as id, menu_item_name as name, menu_item_price as price
                FROM menu_item
                WHERE is_deleted = FALSE
                AND menu_item_status = 'active'
                AND (
                    LOWER(menu_item_name) LIKE $1
                    OR LOWER(menu_item_name) LIKE $2
                    OR LOWER(menu_item_name) = $3
                    OR LOWER(menu_item_name) = $4
                )
                LIMIT 1
            """, f"%{search_term}%", f"%{search_term_singular}%", search_term, search_term_singular)

            if row:
                return {
                    "id": str(row['id']),
                    "name": row['name'],
                    "price": float(row['price'])
                }

    except Exception as e:
        logger.error("db_item_lookup_failed", error=str(e))

    return None


# ============================================================================
# TOOL FUNCTIONS WITH @tool DECORATOR
# All tools are ASYNC - native CrewAI async support (no thread pool overhead)
# All tools use FACTORY PATTERN for session handling
# ============================================================================


def create_search_menu_tool(session_id: str):
    """Factory to create search_menu tool with session context."""

    @tool("search_menu")
    def search_menu(query: Optional[str] = None) -> str:
        """
        Search the restaurant menu for food items.

        Use this tool to show customers what's available to order.
        Displays a menu card UI with matching items.

        Args:
            query: Search term to filter menu items (e.g., "burger", "spicy", "chicken").
                   Use None or "" to show full menu.

        Returns:
            Confirmation message that menu card was displayed with item count.

        Examples:
            - search_menu("") → Full menu card displayed
            - search_menu("burger") → All burger items in menu card
            - search_menu("spicy") → All items containing "spicy"
            - search_menu("vegetarian") → Vegetarian items only
            - search_menu("pizza") → All pizza varieties
        """
        # Convert None to empty string for backward compatibility
        query = query or ""

        # Emit activity for frontend (async)
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "search_menu")

        # Get current meal period for time-aware filtering
        from app.core.preloader import get_current_meal_period
        current_meal = get_current_meal_period()

        # Try preloader first (instant - no DB query!)
        # For searches, get ALL items without pre-filtering to enable contextual messages
        items = _get_menu_from_preloader(query, use_meal_filter=False) if query else _get_menu_from_preloader(query)

        # DEBUG: Log what preloader returned
        logger.info(f"preloader_search_result", query=query, items_count=len(items) if items else 0,
                   items_type=type(items), current_meal=current_meal)
        if items:
            logger.info(f"preloader_first_item", first_item=items[0] if items else None)

        if not items:
            # Preloader should always have data, but log if empty
            logger.warning("menu_preloader_empty", query=query, items_type=type(items), items_value=items)
            # Return helpful message instead of DB fallback
            if query:
                # Try to find similar items and show as MENU CARD
                from app.core.preloader import get_menu_preloader
                preloader = get_menu_preloader()
                all_items = preloader.menu if preloader.is_loaded else []

                # Find items that might be similar (contain any word from query)
                query_words = query.lower().split()
                logger.info(f"searching_for_similar_items", query=query, query_words=query_words, total_items_to_search=len(all_items))
                similar_items = []
                for menu_item in all_items:  # Check all items
                    item_name = menu_item.get('name', '').lower()
                    if any(word in item_name for word in query_words if len(word) > 2):
                        similar_items.append(menu_item)
                    if len(similar_items) >= 10:  # Limit to 10 suggestions
                        break
                logger.info(f"similar_items_found", query=query, count=len(similar_items))

                if similar_items:
                    # CRITICAL: Emit MENU_DATA card with similar items (user journey!)
                    try:
                        from app.core.agui_events import emit_menu_data
                        from app.core.redis import get_cart_sync
                        from app.core.preloader import get_current_meal_period

                        current_meal = get_current_meal_period()
                        cart_data = get_cart_sync(session_id)
                        cart_items = cart_data.get("items", []) if cart_data else []
                        cart_item_names = {item.get("name", "").lower() for item in cart_items}

                        # Build structured similar items for menu card
                        structured_similar = []
                        for item in similar_items:
                            item_name = item.get("name", "")
                            if item_name.lower() not in cart_item_names:
                                structured_similar.append({
                                    "name": item_name,
                                    "price": item.get("price", 0),
                                    "category": _infer_category(item_name),
                                    "description": item.get("description", ""),
                                    "item_id": str(item.get("id", "")),
                                    "meal_types": item.get("meal_types") or ["All Day"],
                                })

                        if structured_similar:
                            emit_menu_data(session_id, structured_similar, current_meal_period=current_meal)
                            logger.info(f"similar_items_menu_emitted", query=query, count=len(structured_similar))
                            return f"Menu card showing {len(structured_similar)} similar items to '{query}'."
                        else:
                            # All similar items already in cart
                            return (f"We don't have '{query}' available. The similar items I found are already in your cart. "
                                   f"Would you like to browse other categories?")
                    except Exception as e:
                        logger.error(f"similar_items_menu_emit_failed", error=str(e))
                        # Fallback to text
                        suggestions = [f"{item.get('name')} (Rs.{item.get('price')})" for item in similar_items[:5]]
                        return (f"We don't have '{query}' available. However, we have these similar items: "
                               f"{', '.join(suggestions)}. Which one would you like?")
                else:
                    # No similar items found - suggest alternative categories
                    # Define category fallback hierarchy based on common user intents
                    category_alternatives = {
                        "pizza": ["Burgers", "Sandwiches", "Main Course"],
                        "pasta": ["Main Course", "Burgers"],
                        "salad": ["Appetizers", "Main Course"],
                        "soup": ["Appetizers", "Main Course"],
                        "dessert": ["Beverages", "Main Course"],
                        "breakfast": ["Main Course", "Appetizers"],
                    }

                    # Try to find alternative category based on query
                    suggested_category = None
                    for keyword, alternatives in category_alternatives.items():
                        if keyword in query.lower():
                            suggested_category = alternatives[0] if alternatives else None
                            break

                    # If no specific mapping, default to Burgers (most popular)
                    if not suggested_category:
                        suggested_category = "Burgers"

                    # Get items from suggested category
                    category_items = [item for item in all_items
                                    if _infer_category(item.get('name', '')) == suggested_category][:8]

                    if not category_items:
                        # Try "Main Course" as final fallback
                        category_items = [item for item in all_items
                                        if _infer_category(item.get('name', '')) == "Main Course"][:8]
                        suggested_category = "Main Course"

                    if category_items:
                        # Emit MENU_DATA with alternative category items
                        try:
                            from app.core.agui_events import emit_menu_data
                            from app.core.redis import get_cart_sync
                            from app.core.preloader import get_current_meal_period

                            current_meal = get_current_meal_period()
                            cart_data = get_cart_sync(session_id)
                            cart_items = cart_data.get("items", []) if cart_data else []
                            cart_item_names = {item.get("name", "").lower() for item in cart_items}

                            structured_alternatives = []
                            for item in category_items:
                                item_name = item.get("name", "")
                                if item_name.lower() not in cart_item_names:
                                    structured_alternatives.append({
                                        "name": item_name,
                                        "price": item.get("price", 0),
                                        "category": _infer_category(item_name),
                                        "description": item.get("description", ""),
                                        "item_id": str(item.get("id", "")),
                                        "meal_types": item.get("meal_types") or ["All Day"],
                                    })

                            if structured_alternatives:
                                emit_menu_data(session_id, structured_alternatives, current_meal_period=current_meal)
                                logger.info(f"alternative_category_menu_emitted", query=query,
                                          category=suggested_category, count=len(structured_alternatives))
                                return (f"[ALTERNATIVE CATEGORY MENU DISPLAYED] We don't have '{query}' available. "
                                       f"How about trying our {suggested_category}? I've shown some options in the menu card. "
                                       f"If you'd prefer something else, just let me know or I can show you the full menu!")
                        except Exception as e:
                            logger.error(f"alternative_category_emit_failed", error=str(e))

                    # Final fallback if everything fails - emit current meal menu
                    try:
                        current_meal_items = _get_menu_from_preloader("", use_meal_filter=True, strict_filter=True)
                        if current_meal_items:
                            from app.core.redis import get_cart_sync
                            cart_data = get_cart_sync(session_id)
                            cart_items = cart_data.get("items", []) if cart_data else []
                            cart_item_names = {item.get("name", "").lower() for item in cart_items}

                            structured_menu = []
                            for item in current_meal_items:
                                item_name = item.get("name", "")
                                if item_name.lower() not in cart_item_names:
                                    structured_menu.append({
                                        "name": item_name,
                                        "price": item.get("price", 0),
                                        "category": _infer_category(item_name),
                                        "description": item.get("description", ""),
                                        "item_id": str(item.get("id", "")),
                                        "meal_types": item.get("meal_types") or ["All Day"],
                                    })

                            if structured_menu:
                                emit_menu_data(session_id, structured_menu, current_meal_period=current_meal)
                                return (f"We don't have '{query}' available at the moment. "
                                       f"I've shown you our current menu - please browse and let me know what you'd like!")
                    except Exception as e:
                        logger.error(f"final_fallback_menu_emit_failed", error=str(e))

                    return (f"We don't have '{query}' available at the moment. "
                           f"Would you like me to show you what's on the menu?")
            return "Menu is loading. Please try again in a moment."

        # **MEAL-TIME CONTEXT AWARENESS** - Check if search results are available during current meal period
        if query:
            # Separate items by meal availability
            available_now = [item for item in items if current_meal in item.get("meal_types", [])]
            available_other_times = [item for item in items if current_meal not in item.get("meal_types", []) and item.get("meal_types")]

            logger.info(f"meal_time_check", query=query, current_meal=current_meal,
                       available_now=len(available_now), available_other_times=len(available_other_times))

            # If found items but NONE available in current meal period
            if not available_now and available_other_times:
                logger.info(f"returning_meal_context_message", query=query, unavailable_count=len(available_other_times))
                # Get the meal periods when these items ARE available
                other_meals = set()
                for item in available_other_times:
                    other_meals.update(item.get("meal_types", []))

                meal_times = {
                    "Breakfast": "6 AM - 11 AM",
                    "Lunch": "11 AM - 4 PM",
                    "Dinner": "4 PM - 10 PM"
                }

                availability_text = ", ".join([f"{meal} ({meal_times.get(meal, '')})" for meal in sorted(other_meals)])
                item_names = ", ".join([item.get("name") for item in available_other_times[:3]])

                # Get full current meal menu and emit MENU_DATA card
                current_meal_items = _get_menu_from_preloader("", use_meal_filter=True, strict_filter=True)

                # Emit full lunch/dinner menu card so user can browse
                try:
                    from app.core.agui_events import emit_menu_data
                    from app.core.redis import get_cart_sync

                    cart_data = get_cart_sync(session_id)
                    cart_items = cart_data.get("items", []) if cart_data else []
                    cart_item_names = {item.get("name", "").lower() for item in cart_items}

                    # Build structured menu items (exclude items already in cart)
                    structured_menu = []
                    for item in current_meal_items:
                        item_name = item.get("name", "")
                        if item_name.lower() not in cart_item_names:
                            structured_menu.append({
                                "name": item_name,
                                "price": item.get("price", 0),
                                "category": _infer_category(item_name),
                                "description": item.get("description", ""),
                                "item_id": str(item.get("id", "")),
                                "meal_types": item.get("meal_types") or ["All Day"],
                            })

                    if structured_menu:
                        emit_menu_data(session_id, structured_menu, current_meal_period=current_meal)
                        logger.info(f"current_meal_menu_emitted", meal=current_meal, count=len(structured_menu))

                        contextual_message = (f"I found {len(available_other_times)} items matching '{query}' ({item_names}), "
                                f"but they're only available during {availability_text}. "
                                f"It's currently {current_meal} time. "
                                f"I've displayed our full {current_meal.lower()} menu for you to browse! "
                                f"Please check the menu card and let me know what you'd like to order.")
                    else:
                        # All items in cart
                        contextual_message = (f"I found {len(available_other_times)} items matching '{query}' ({item_names}), "
                                f"but they're only available during {availability_text}. "
                                f"It's currently {current_meal} time. "
                                f"All our {current_meal.lower()} items are already in your cart!")
                except Exception as e:
                    logger.error(f"menu_emit_failed", error=str(e))
                    # Fallback to text-only suggestions
                    suggestions = [item.get("name") for item in current_meal_items[:5]]
                    suggestion_text = ", ".join(suggestions) if suggestions else "our current menu"
                    contextual_message = (f"I found {len(available_other_times)} items matching '{query}' ({item_names}), "
                            f"but they're only available during {availability_text}. "
                            f"It's currently {current_meal} time. "
                            f"Would you like to see our {current_meal.lower()} items instead? "
                            f"We have {suggestion_text} available right now!")

                logger.info(f"tool_returning_message", message=contextual_message[:200])
                return contextual_message

            # Filter items to only show what's available NOW (for menu emit)
            if available_now:
                items = available_now  # Replace items list with only currently available items

        logger.debug("menu_from_preloader", query=query, count=len(items))

        # Track displayed menu in entity graph (for "the 2nd one" resolution)
        try:
            from app.core.semantic_context import get_entity_graph
            graph = get_entity_graph(session_id)
            # Store item names in display order
            displayed_items = [item.get('name') for item in items[:15]]
            graph.set_displayed_menu(displayed_items)

            # CRITICAL: If this is a specific item search (not full menu), track as last_mentioned_item
            # This preserves context for multi-turn conversations like "add burger" → "how many?" → "2"
            if query and items:  # Non-empty query with results
                first_item_name = items[0].get('name')
                if first_item_name:
                    graph.update_last_mentioned(first_item_name)
                    logger.debug("entity_graph_item_tracked", session_id=session_id, item=first_item_name)

            logger.debug("entity_graph_menu_tracked", session_id=session_id, count=len(displayed_items))
        except Exception as e:
            logger.debug("entity_graph_update_failed", error=str(e))

        # Emit structured menu data for rich UI card - ONLY for full menu requests
        # Don't show MenuCard for item searches like "pizza" - just return text
        if not query:  # Empty query = full menu request
            try:
                from app.core.agui_events import emit_menu_data
                from app.core.redis import get_cart_sync
                from app.core.preloader import get_current_meal_period

                # Get current meal period for frontend
                current_meal = get_current_meal_period()

                # Get current cart items to filter them out (sync Redis)
                cart_data = get_cart_sync(session_id)
                cart_items = cart_data.get("items", []) if cart_data else []
                cart_item_names = {item.get("name", "").lower() for item in cart_items}

                # Send ALL items (frontend handles pagination) with meal_types
                structured_items = []
                for item in items:  # Send all items, not just 15
                    item_name = item.get("name", "")
                    # Skip items already in cart
                    if item_name.lower() in cart_item_names:
                        continue
                    structured_items.append({
                        "name": item_name,
                        "price": item.get("price", 0),
                        "category": _infer_category(item_name),
                        "description": item.get("description", ""),
                        "item_id": str(item.get("id", "")),
                        "meal_types": item.get("meal_types") or ["All Day"],
                    })

                if structured_items:
                    emit_menu_data(session_id, structured_items, current_meal_period=current_meal)

                # Menu card displayed - provide data, let LLM decide next action based on user intent
                return f"Menu card displayed with {len(structured_items)} items available for ordering."
            except Exception as e:
                logger.debug("menu_data_emit_failed", error=str(e))

        # Handle search results - if multiple items (ambiguous), show filtered menu
        if query and len(items) > 1:
            # Multiple matches - show filtered menu for clarification
            logger.info(f"ambiguous_query_detected", query=query, matches=len(items))
            try:
                from app.core.agui_events import emit_menu_data
                from app.core.redis import get_cart_sync
                from app.core.preloader import get_current_meal_period

                current_meal = get_current_meal_period()
                cart_data = get_cart_sync(session_id)
                cart_items = cart_data.get("items", []) if cart_data else []
                cart_item_names = {item.get("name", "").lower() for item in cart_items}

                # Build filtered menu items
                structured_items = []
                for item in items[:15]:  # Limit to top 15 matches
                    item_name = item.get("name", "")
                    if item_name.lower() not in cart_item_names:
                        structured_items.append({
                            "name": item_name,
                            "price": item.get("price", 0),
                            "category": _infer_category(item_name),
                            "description": item.get("description", ""),
                            "item_id": str(item.get("id", "")),
                            "meal_types": item.get("meal_types") or ["All Day"],
                        })

                logger.info(f"filtered_menu_built", total_matches=len(items), structured_count=len(structured_items))

                if structured_items:
                    logger.info(f"emitting_filtered_menu", session_id=session_id, count=len(structured_items))
                    emit_menu_data(session_id, structured_items, current_meal_period=current_meal)
                    logger.info(f"filtered_menu_emitted_successfully", count=len(structured_items))
                    return f"Menu card showing {len(items)} items matching '{query}'."
                else:
                    # All items already in cart
                    logger.info(f"filtered_items_all_in_cart", query=query)
                    menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:5]]
                    return f"I found these items matching '{query}': {', '.join(menu_items)}. Which one would you like?"
            except Exception as e:
                logger.error(f"filtered_menu_emit_failed", error=str(e), query=query)
                # Fallback to text list
                menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:5]]
                return f"I found these items matching '{query}': {', '.join(menu_items)}. Which one would you like?"

        # Single item match or no query - return simple text
        if query and len(items) == 1:
            # Exact match - single item found
            item = items[0]
            return f"We have {item.get('name')} available for Rs.{item.get('price')}."

        # Fallback for edge cases
        menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:15]]
        return f"Menu items: {', '.join(menu_items)}" + (f" (+{len(items)-15} more)" if len(items) > 15 else "")

    return search_menu


def create_add_to_cart_tool(session_id: str):
    """Factory to create add_to_cart tool with session context."""

    @tool("add_to_cart")
    def add_to_cart(items: str) -> str:
        """
        Add one or more food items to the customer's cart in a SINGLE call.

        IMPORTANT: Quantity is REQUIRED for every item. Do NOT call this tool
        unless the customer has explicitly stated the quantity for each item.
        If the customer says "add biryani" without a number, ASK them
        "How many would you like?" first. NEVER assume quantity is 1.

        Args:
            items: JSON array of items to add. Each object has "item" (name) and "quantity" (number).
                Single item:  [{"item": "Butter Chicken", "quantity": 2}]
                Multiple:     [{"item": "Burger", "quantity": 2}, {"item": "Coke", "quantity": 1}]

        Returns:
            Confirmation of all items added to cart with updated total.

        Examples:
            - "Add 2 burgers" → add_to_cart('[{"item": "burger", "quantity": 2}]')
            - "I want 1 Butter Chicken and 2 Naan" → add_to_cart('[{"item": "Butter Chicken", "quantity": 1}, {"item": "Naan", "quantity": 2}]')
            - "Add biryani" → Do NOT call. Ask: "How many would you like?"
        """
        import json as _json

        from app.core.agui_events import emit_tool_activity, emit_cart_data
        emit_tool_activity(session_id, "add_to_cart")

        from app.core.redis import get_cart_sync, set_cart_sync
        from app.core.preloader import get_menu_preloader

        try:
            # Parse items JSON
            try:
                items_list = _json.loads(items)
                if isinstance(items_list, dict):
                    items_list = [items_list]
            except (_json.JSONDecodeError, TypeError):
                return f"Invalid items format. Use JSON array: [{'{'}\"item\": \"name\", \"quantity\": N{'}'}]"

            if not items_list:
                return "No items specified."

            preloader = get_menu_preloader()
            cart_data = get_cart_sync(session_id) or {"items": [], "total": 0}
            cart_items = cart_data.get('items', [])

            added = []
            not_found = []

            for entry in items_list:
                item_name = str(entry.get("item", "")).strip()
                quantity = int(entry.get("quantity", 0))

                if not item_name:
                    continue

                if quantity <= 0:
                    return f"[INVALID QUANTITY] Quantity for '{item_name}' must be positive."
                if quantity > 50:
                    return f"[INVALID QUANTITY] Maximum 50 per item. '{item_name}' has quantity {quantity}."

                found_item = preloader.find_item(item_name) if preloader.is_loaded else None
                if not found_item:
                    not_found.append(item_name)
                    continue

                # Check if already in cart
                existing = None
                for ci in cart_items:
                    if ci.get('item_id') == str(found_item.get('id', '')):
                        existing = ci
                        break

                if existing:
                    existing['quantity'] += quantity
                else:
                    cart_items.append({
                        'item_id': str(found_item.get('id', '')),
                        'name': found_item.get('name'),
                        'price': float(found_item.get('price', 0)),
                        'quantity': quantity,
                        'category': ''
                    })

                added.append(f"{quantity}x {found_item.get('name')}")

                # Track last mentioned item
                try:
                    from app.core.semantic_context import get_entity_graph
                    graph = get_entity_graph(session_id)
                    graph.update_last_mentioned(found_item['name'])
                except Exception:
                    pass

            if not added and not_found:
                return f"Items not found: {', '.join(not_found)}. Try searching the menu first."

            # Save cart
            cart_data['items'] = cart_items
            cart_data['updated_at'] = str(datetime.now())
            set_cart_sync(session_id, cart_data, ttl=3600)

            subtotal = sum(i['price'] * i['quantity'] for i in cart_items)

            # Emit ONE cart card with all items
            emit_cart_data(session_id, cart_items, subtotal)

            logger.info(
                "items_added_to_cart",
                session_id=session_id,
                added=added,
                not_found=not_found,
                subtotal=subtotal
            )

            result = f"Added to cart: {', '.join(added)}."
            if not_found:
                result += f" Not found: {', '.join(not_found)}."
            return result

        except Exception as e:
            logger.error("add_to_cart_error", error=str(e), session_id=session_id)
            return f"Error adding items: {str(e)}"

    return add_to_cart


def create_view_cart_tool(session_id: str):
    """Factory to create view_cart tool with session context."""

    @tool("view_cart")
    def view_cart() -> str:
        """
        View the current contents of the customer's shopping cart.

        Displays all items currently in cart with quantities, individual prices,
        and total order amount. Emits cart UI for visual display.

        Returns:
            Detailed cart summary with items, quantities, prices, and total.

        Examples:
            - view_cart() → Shows cart with all items and total
            - Common use: After adding items, before checkout
            - Common use: When customer asks "what's in my cart?"
            - Common use: When customer asks "how much is my total?"
        """
        # Emit activity for frontend (async - no thread overhead)
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        emit_tool_activity(session_id, "view_cart")

        from app.core.redis import get_cart_sync

        try:
            cart_data = get_cart_sync(session_id) or {"items": []}
            items = cart_data.get("items", [])

            if not items:
                return "Cart is empty."

            # Build cart summary
            cart_items = []
            total = 0
            structured_items = []
            for item in items:
                name = item.get("name", "Item")
                qty = item.get("quantity", 1)
                price = item.get("price", 0)
                total += price * qty
                cart_items.append(f"{name} x{qty}")
                # Build structured items for rich UI
                structured_items.append({
                    "name": name,
                    "quantity": qty,
                    "price": price,
                    "item_id": item.get("item_id", ""),
                    "special_instructions": item.get("special_instructions", "")
                })

            # Emit structured cart data for rich UI display (async)
            emit_cart_data(session_id, structured_items, total)

            return f"Cart: {', '.join(cart_items)}. Total: Rs.{total:.0f}"

        except Exception as e:
            logger.error("view_cart_error", error=str(e), session_id=session_id)
            return f"Cart error: {str(e)}"

    return view_cart


def create_remove_from_cart_tool(session_id: str):
    """Factory to create remove_from_cart tool with session context."""

    @tool("remove_from_cart")
    def remove_from_cart(items: str) -> str:
        """
        Remove one or more items from the customer's cart in a SINGLE call.

        Args:
            items: JSON array of items to remove. Each object has "item" (name) and optionally "quantity" (number, default: remove all).
                Single:   [{"item": "burger"}]                    — removes all burgers
                Multiple: [{"item": "burger"}, {"item": "coke"}]  — removes both
                Partial:  [{"item": "burger", "quantity": 1}]     — removes 1 burger

        Returns:
            Confirmation of removed items and updated cart total.

        Examples:
            - "remove the burger" → remove_from_cart('[{"item": "burger"}]')
            - "delete 2 cokes and the pizza" → remove_from_cart('[{"item": "coke", "quantity": 2}, {"item": "pizza"}]')
        """
        import json as _json

        from app.core.agui_events import emit_tool_activity, emit_cart_data
        emit_tool_activity(session_id, "remove_from_cart")

        from app.core.redis import get_cart_sync, set_cart_sync

        try:
            # Parse items JSON
            try:
                items_list = _json.loads(items)
                if isinstance(items_list, dict):
                    items_list = [items_list]
            except (_json.JSONDecodeError, TypeError):
                return f"Invalid items format. Use JSON array: [{'{'}\"item\": \"name\"{'}'}]"

            cart_data = get_cart_sync(session_id) or {"items": []}
            cart_items = cart_data.get("items", [])

            if not cart_items:
                return "Cart is already empty."

            removed = []
            not_found = []

            for entry in items_list:
                item_name = str(entry.get("item", "")).strip().lower()
                qty_to_remove = entry.get("quantity", 0)  # 0 = remove all

                if not item_name:
                    continue

                found = False
                new_cart = []
                for ci in cart_items:
                    if item_name in ci.get("name", "").lower() and not found:
                        found = True
                        current_qty = ci.get("quantity", 1)
                        actual_remove = current_qty if qty_to_remove == 0 else min(qty_to_remove, current_qty)
                        new_qty = current_qty - actual_remove
                        removed.append(f"{actual_remove}x {ci.get('name')}")
                        if new_qty > 0:
                            new_cart.append({**ci, "quantity": new_qty})
                    else:
                        new_cart.append(ci)
                cart_items = new_cart

                if not found:
                    not_found.append(item_name)

            # Save updated cart
            cart_data['items'] = cart_items
            cart_data['updated_at'] = str(datetime.now())
            set_cart_sync(session_id, cart_data, ttl=3600)

            new_total = sum(i['price'] * i['quantity'] for i in cart_items)

            # Emit updated cart card
            emit_cart_data(session_id, cart_items, new_total)

            logger.info(
                "items_removed_from_cart",
                session_id=session_id,
                removed=removed,
                not_found=not_found
            )

            result = f"Removed: {', '.join(removed)}." if removed else ""
            if not_found:
                result += f" Not found: {', '.join(not_found)}."
            if cart_items:
                result += f" Cart total: Rs.{new_total:.0f}"
            else:
                result += " Cart is now empty."
            return result.strip()

        except Exception as e:
            logger.error("remove_from_cart_error", error=str(e), session_id=session_id)
            return f"Remove error: {str(e)}"

    return remove_from_cart


def create_checkout_tool(session_id: str):
    """Factory to create checkout tool with session context."""

    @tool("checkout")
    def checkout(order_type: Optional[str] = None) -> str:
        """
        Complete the order and initiate payment workflow.

        Creates order in database, initiates payment workflow (online/cash/card at counter),
        and returns order confirmation. Cart is cleared after successful checkout.

        Args:
            order_type: Order type - "dine_in" or "take_away" (extracted from customer message)

        Returns:
            Order confirmation with order ID, total amount, and payment workflow status.

        Examples:
            - checkout("dine_in") → Creates dine-in order and starts payment
            - checkout("take_away") → Creates takeaway order and starts payment
            - checkout() → If order type missing, will be handled by checkout handler

        Common triggers:
            - Customer: "checkout" / "place order" / "proceed to checkout"
            - Customer: "checkout for dine in" → checkout("dine_in")
            - Customer: "checkout for takeaway" → checkout("take_away")
        """
        # Use the sync implementation
        return _checkout_impl(order_type or "", session_id)

    return checkout


def _create_checkout_tool_async_DISABLED(session_id: str):
    """DISABLED - Async checkout tool that doesn't work with CrewAI.
    CrewAI doesn't properly await async tools even with akickoff().
    Use create_checkout_tool instead which uses sync _checkout_impl.
    """

    @tool("checkout_async_disabled")
    async def checkout_disabled(order_type: str = "") -> str:
        """DISABLED async checkout - do not use"""
        # Emit activity for frontend (async - no thread overhead)
        from app.core.agui_events import emit_tool_activity_async, emit_quick_replies_async
        await emit_tool_activity_async(session_id, "checkout")

        # Always takeaway - no dine-in option
        order_type = "take_away"

        from app.core.redis import get_cart, set_cart
        import uuid

        try:
            # Get cart (async Redis)
            cart_data = await get_cart(session_id)
            items = cart_data.get("items", [])

            if not items:
                return "Cart is empty. Cannot checkout."

            # Build order summary
            order_items = []
            order_items_data = []
            total = 0
            for item in items:
                name = item.get("name", "Item")
                qty = item.get("quantity", 1)
                price = item.get("price", 0)
                item_total = price * qty
                total += item_total
                order_items.append(f"{name} x{qty}")
                order_items_data.append({
                    "name": name,
                    "quantity": qty,
                    "price": price,
                    "item_total": item_total
                })

            # Generate order display ID
            order_display_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

            # Use already validated order_type
            order_type_clean = "take_away" if is_take_away else "dine_in"

            # ============================================================
            # PERSIST ORDER TO POSTGRESQL (A24 schema - primary storage)
            # ============================================================
            postgres_order_id = None
            try:
                from app.core.db_pool import AsyncDBConnection

                async with AsyncDBConnection() as conn:
                    # Get restaurant_id
                    restaurant_row = await conn.fetchrow("SELECT id FROM restaurant_config LIMIT 1")
                    restaurant_id = restaurant_row['id'] if restaurant_row else None

                    # Get order_type_id
                    type_row = await conn.fetchrow(
                        "SELECT order_type_id FROM order_type_table WHERE order_type_code = $1",
                        order_type_clean
                    )
                    order_type_id = type_row['order_type_id'] if type_row else None

                    # Get order_status_type_id (confirmed)
                    status_row = await conn.fetchrow(
                        "SELECT order_status_type_id FROM order_status_type WHERE order_status_code = 'confirmed'"
                    )
                    order_status_id = status_row['order_status_type_id'] if status_row else None

                    # Get order_source_type_id (chat_agent)
                    source_row = await conn.fetchrow(
                        "SELECT order_source_type_id FROM order_source_type WHERE order_source_type_code = 'chat_agent'"
                    )
                    order_source_id = source_row['order_source_type_id'] if source_row else None

                    # Use transaction for inserts
                    async with conn.transaction():
                        # Insert into orders table
                        result = await conn.fetchrow("""
                            INSERT INTO orders (
                                restaurant_id, order_type_id, order_status_type_id, order_source_type_id,
                                device_id, order_display_id, total_amount
                            ) VALUES (
                                $1, $2, $3, $4, $5, $6, $7
                            ) RETURNING order_id
                        """, restaurant_id, order_type_id, order_status_id, order_source_id,
                            session_id, order_display_id, total)
                        postgres_order_id = result['order_id']

                        # Insert order items
                        for item in items:
                            item_name = item.get("name", "Item")
                            item_qty = item.get("quantity", 1)
                            item_price = item.get("price", 0)
                            item_total = item_price * item_qty
                            menu_item_id = item.get("id")

                            await conn.execute("""
                                INSERT INTO order_item (
                                    order_id, menu_item_id, item_name, quantity, unit_price,
                                    base_price, line_total, item_status
                                ) VALUES (
                                    $1, $2::uuid, $3, $4, $5, $6, $7, 'confirmed'
                                )
                            """, postgres_order_id, menu_item_id, item_name, item_qty,
                                item_price, item_price, item_total)

                        # Insert order total
                        await conn.execute("""
                            INSERT INTO order_total (
                                order_id, items_total, subtotal, final_amount
                            ) VALUES (
                                $1, $2, $3, $4
                            )
                        """, postgres_order_id, total, total, total)

                logger.info(
                    "order_persisted_to_postgresql",
                    session_id=session_id,
                    order_id=str(postgres_order_id),
                    order_display_id=order_display_id
                )

            except Exception as pg_error:
                logger.error(
                    "postgresql_order_persist_failed",
                    error=str(pg_error),
                    order_display_id=order_display_id
                )

            # ============================================================
            # PERSIST ORDER TO MONGODB (backup for analytics)
            # ============================================================
            try:
                from pymongo import MongoClient
                import os

                mongo_url = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
                mongo_db = os.getenv("MONGODB_DATABASE_NAME", "restaurant_ai_analytics")

                client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
                db = client[mongo_db]

                order_doc = {
                    "order_id": order_display_id,
                    "postgres_order_id": str(postgres_order_id) if postgres_order_id else None,
                    "session_id": session_id,
                    "items": order_items_data,
                    "total": total,
                    "order_type": order_type_clean,
                    "status": "confirmed",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }

                db.orders.insert_one(order_doc)
                client.close()

                logger.info(
                    "order_persisted_to_mongodb",
                    session_id=session_id,
                    order_id=order_display_id
                )

            except Exception as mongo_error:
                # Log but don't fail checkout if MongoDB is unavailable
                logger.warning(
                    "mongodb_order_persist_failed",
                    error=str(mongo_error),
                    order_display_id=order_display_id
                )

            # ============================================================
            # PERSIST ORDER TO REDIS (for quick access and session state)
            # ============================================================
            try:
                from app.core.redis import get_redis_client
                import json

                redis_client = await get_redis_client()
                order_key = f"order:{session_id}:{order_display_id}"
                await redis_client.setex(
                    order_key,
                    86400,  # 24 hours TTL
                    json.dumps({
                        "order_id": order_display_id,
                        "postgres_order_id": str(postgres_order_id) if postgres_order_id else None,
                        "items": order_items_data,
                        "total": total,
                        "order_type": order_type_clean,
                        "status": "confirmed",
                        "created_at": datetime.now().isoformat()
                    })
                )

                # Also save to order history for session
                history_key = f"order_history:{session_id}"
                await redis_client.lpush(history_key, order_display_id)
                await redis_client.expire(history_key, 86400 * 7)  # 7 days

            except Exception as redis_error:
                logger.warning(
                    "redis_order_persist_failed",
                    error=str(redis_error),
                    order_display_id=order_display_id
                )

            # Clear the cart after successful order (async Redis)
            await set_cart(session_id, {"items": [], "updated_at": str(datetime.now())}, ttl=3600)

            # Emit order data for rich UI display (Order Confirmation Card - async)
            try:
                from app.core.agui_events import emit_order_data_async
                await emit_order_data_async(
                    session_id=session_id,
                    order_id=order_display_id,
                    items=order_items_data,
                    total=total,
                    status="confirmed",
                    order_type=order_type_clean
                )
            except Exception as e:
                logger.debug("emit_order_data_failed", error=str(e))

            logger.info(
                "order_placed",
                session_id=session_id,
                order_display_id=order_display_id,
                postgres_order_id=str(postgres_order_id) if postgres_order_id else None,
                total=total,
                items=len(items)
            )

            order_type_display = "Take Away" if order_type_clean == "take_away" else "Dine In"
            return f"Order created! ID: {order_display_id}. Items: {', '.join(order_items)}. Total: Rs.{total:.0f} ({order_type_display}). IMPORTANT: Order is created but not yet paid. You MUST now ask customer: 'How would you like to pay?' and offer options: 'Card Payment' or 'Cash on Delivery'. If they choose card, call initiate_payment(order_id='{order_display_id}')"

        except Exception as e:
            logger.error("checkout_error", error=str(e), session_id=session_id)
            return f"Checkout error: {str(e)}"

    return checkout


def create_cancel_order_tool(session_id: str):
    """Factory to create cancel_order tool with session context."""

    @tool("cancel_order")
    async def cancel_order(order_id: str = "") -> str:
        """
        Cancel a placed order.

        Use this when customer wants to cancel an order they already placed.
        If no order_id provided, cancels the most recent order for this session.

        Args:
            order_id: Order ID to cancel (e.g., "ORD-ABC12345"). Leave empty for most recent.

        Returns:
            Confirmation of cancellation or error message.
        """
        # Emit activity for frontend (async - no thread overhead)
        from app.core.agui_events import emit_tool_activity_async
        await emit_tool_activity_async(session_id, "cancel_order")

        from app.core.redis import get_redis_client
        import json

        try:
            redis_client = await get_redis_client()
            order_display_id = order_id.strip().upper() if order_id else None

            # If no order_id provided, get most recent from history
            if not order_display_id:
                history_key = f"order_history:{session_id}"
                recent_orders = await redis_client.lrange(history_key, 0, 0)
                if not recent_orders:
                    return "No recent orders found to cancel."
                order_display_id = recent_orders[0].decode() if isinstance(recent_orders[0], bytes) else recent_orders[0]

            # ============================================================
            # CANCEL IN POSTGRESQL (A24 schema - primary storage)
            # ============================================================
            order_info = None
            postgres_cancelled = False
            try:
                from app.core.db_pool import AsyncDBConnection

                async with AsyncDBConnection() as conn:
                    # Find order by display_id
                    order_row = await conn.fetchrow("""
                        SELECT o.order_id, o.order_display_id, o.total_amount,
                               ost.order_status_code as status
                        FROM orders o
                        LEFT JOIN order_status_type ost ON o.order_status_type_id = ost.order_status_type_id
                        WHERE o.order_display_id = $1 AND o.device_id = $2
                    """, order_display_id, session_id)

                    if order_row:
                        if order_row['status'] == 'cancelled':
                            return f"Order {order_display_id} was already cancelled."

                        # Get order items for response
                        items = await conn.fetch("""
                            SELECT item_name, quantity FROM order_item
                            WHERE order_id = $1 AND (is_deleted = FALSE OR is_deleted IS NULL)
                        """, order_row['order_id'])
                        order_info = {
                            "order_id": str(order_row['order_id']),
                            "total": float(order_row['total_amount'] or 0),
                            "items": [{"name": i['item_name'], "quantity": i['quantity']} for i in items]
                        }

                        # Get cancelled status id
                        cancelled_status = await conn.fetchrow(
                            "SELECT order_status_type_id FROM order_status_type WHERE order_status_code = 'cancelled'"
                        )
                        cancelled_status_id = cancelled_status['order_status_type_id'] if cancelled_status else None

                        # Use transaction for updates
                        async with conn.transaction():
                            # Update order status to cancelled
                            await conn.execute("""
                                UPDATE orders
                                SET order_status_type_id = $1,
                                    cancelled_at = NOW(),
                                    cancellation_reason = 'Cancelled by customer via chat',
                                    updated_at = NOW()
                                WHERE order_id = $2
                            """, cancelled_status_id, order_row['order_id'])

                            # Update order items
                            await conn.execute("""
                                UPDATE order_item
                                SET item_status = 'cancelled',
                                    cancelled_at = NOW(),
                                    cancellation_reason = 'Order cancelled',
                                    updated_at = NOW()
                                WHERE order_id = $1
                            """, order_row['order_id'])

                        postgres_cancelled = True

                        logger.info(
                            "order_cancelled_postgresql",
                            session_id=session_id,
                            order_display_id=order_display_id,
                            postgres_order_id=str(order_row['order_id'])
                        )

            except Exception as pg_error:
                logger.error(
                    "postgresql_cancel_failed",
                    error=str(pg_error),
                    order_display_id=order_display_id
                )

            # ============================================================
            # UPDATE IN REDIS (cache consistency)
            # ============================================================
            try:
                order_key = f"order:{session_id}:{order_display_id}"
                order_data = await redis_client.get(order_key)

                if order_data:
                    order = json.loads(order_data)
                    if not order_info:
                        order_info = {
                            "total": order.get("total", 0),
                            "items": order.get("items", [])
                        }
                    order["status"] = "cancelled"
                    order["cancelled_at"] = datetime.now().isoformat()
                    await redis_client.setex(order_key, 86400, json.dumps(order))
                elif not postgres_cancelled:
                    return f"Order {order_display_id} not found. It may have already been cancelled or doesn't exist."

            except Exception as redis_error:
                logger.warning(
                    "redis_cancel_update_failed",
                    error=str(redis_error),
                    order_display_id=order_display_id
                )

            # ============================================================
            # UPDATE IN MONGODB (analytics backup)
            # ============================================================
            try:
                from pymongo import MongoClient
                import os

                mongo_url = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
                mongo_db = os.getenv("MONGODB_DATABASE_NAME", "restaurant_ai_analytics")

                client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
                db = client[mongo_db]
                db.orders.update_one(
                    {"order_id": order_display_id},
                    {"$set": {"status": "cancelled", "cancelled_at": datetime.now().isoformat()}}
                )
                client.close()
            except Exception:
                pass  # MongoDB update is optional

            logger.info(
                "order_cancelled",
                session_id=session_id,
                order_display_id=order_display_id
            )

            if order_info:
                items_str = ", ".join([f"{i['name']} x{i['quantity']}" for i in order_info.get("items", [])])
                return f"Order {order_display_id} has been cancelled. (Was: {items_str}, Rs.{order_info.get('total', 0):.0f})"
            else:
                return f"Order {order_display_id} has been cancelled."

        except Exception as e:
            logger.error("cancel_order_error", error=str(e), session_id=session_id)
            return f"Cancel error: {str(e)}"

    return cancel_order


def create_get_order_status_tool(session_id: str):
    """Factory to create get_order_status tool with session context."""

    @tool("get_order_status")
    def get_order_status(order_id: str = "") -> str:
        """
        Get the current status and progress of an order.

        Retrieves real-time order status including preparation stage, estimated time,
        and any special notes. If no order_id provided, checks most recent order.

        Args:
            order_id: Order ID to check (e.g., "ORD-ABC12345", leave empty for most recent)

        Returns:
            Order status (pending/confirmed/preparing/ready/completed/cancelled) with details.

        Examples:
            - get_order_status("ORD-123") → Status of specific order
            - get_order_status() → Status of customer's most recent order

        Common triggers:
            - Customer: "where is my order?" → get_order_status()
            - Customer: "what's the status?" → get_order_status()
            - Customer: "is my food ready?" → get_order_status()
        """
        return _get_order_status_impl(order_id, session_id)

    return get_order_status


def create_get_order_history_tool(session_id: str):
    """Factory to create get_order_history tool with session context."""

    @tool("get_order_history")
    def get_order_history() -> str:
        """
        Get the customer's recent order history.

        Use this when customer asks about past orders or wants to reorder.

        Returns:
            List of recent orders with status and totals.
        """
        return _get_order_history_impl(session_id)

    return get_order_history


def create_reorder_by_id_tool(session_id: str):
    """Factory to create reorder tool with session context."""

    @tool("reorder")
    async def reorder(order_id: str) -> str:
        """
        Reorder items from a previous order.

        Use this when customer wants to order the same items again.
        Adds all items from the specified order to the current cart.

        Args:
            order_id: Order ID to reorder from (e.g., "ORD-ABC12345").

        Returns:
            Confirmation of items added to cart.
        """
        from app.core.redis import get_cart, set_cart
        from app.core.db_pool import AsyncDBConnection

        try:
            order_display_id = order_id.strip().upper()

            # Get order from PostgreSQL (async with asyncpg)
            async with AsyncDBConnection() as conn:
                # Verify order belongs to this session
                order_row = await conn.fetchrow("""
                    SELECT o.order_id FROM orders o
                    WHERE o.order_display_id = $1 AND o.device_id = $2
                """, order_display_id, session_id)

                if not order_row:
                    return f"Order {order_display_id} not found or doesn't belong to your session."

                # Get order items
                items = await conn.fetch("""
                    SELECT oi.menu_item_id, oi.item_name, oi.quantity, oi.unit_price
                    FROM order_item oi
                    WHERE oi.order_id = $1 AND oi.item_status != 'cancelled'
                """, order_row['order_id'])

                if not items:
                    return f"No items found in order {order_display_id}."

            # Add items to cart (async Redis)
            cart_data = await get_cart(session_id)
            cart_items = cart_data.get('items', [])

            added_items = []
            for item in items:
                cart_items.append({
                    'item_id': str(item['menu_item_id']) if item['menu_item_id'] else '',
                    'name': item['item_name'],
                    'price': float(item['unit_price']),
                    'quantity': item['quantity'],
                    'category': ''
                })
                added_items.append(f"{item['item_name']} x{item['quantity']}")

            cart_data['items'] = cart_items
            cart_data['updated_at'] = str(datetime.now())
            await set_cart(session_id, cart_data, ttl=3600)

            subtotal = sum(i['price'] * i['quantity'] for i in cart_items)

            logger.info(
                "reorder_completed",
                session_id=session_id,
                from_order=order_display_id,
                items_added=len(items)
            )

            return f"Added from order {order_display_id}: {', '.join(added_items)}. Cart total: Rs.{subtotal:.0f}. Ready to checkout?"

        except Exception as e:
            logger.error("reorder_error", error=str(e), session_id=session_id)
            return f"Error reordering: {str(e)}"

    return reorder


def create_get_order_receipt_tool(session_id: str):
    """Factory to create get_order_receipt tool with session context."""

    @tool("get_order_receipt")
    def get_order_receipt(order_id: str = "") -> str:
        """
        Generate detailed receipt/invoice for an order.

        Creates formatted receipt with itemized list, prices, taxes, discounts,
        and payment details. Can be downloaded or printed.

        Args:
            order_id: Order ID for receipt (e.g., "ORD-123", leave empty for most recent)

        Returns:
            Formatted receipt with complete order breakdown and totals.

        Examples:
            - get_order_receipt("ORD-123") → Receipt for specific order
            - get_order_receipt() → Receipt for most recent order

        Common triggers:
            - Customer: "can I get a receipt?" → get_order_receipt()
            - Customer: "show me the bill" → get_order_receipt()
            - Customer: "invoice please" → get_order_receipt()
        """
        return _get_order_receipt_impl(order_id, session_id)

    return get_order_receipt


def create_clear_cart_tool(session_id: str):
    """Factory to create clear_cart tool with session context."""

    @tool("clear_cart")
    def clear_cart(_nonce: str = "") -> str:
        """
        Clear all items from the customer's cart.

        Use this when customer wants to start over or empty their cart completely.

        Args:
            _nonce: Optional unique identifier (ignored, used for cache busting)

        Returns:
            Confirmation that cart was cleared.
        """
        # Emit activity for frontend (sync)
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        emit_tool_activity(session_id, "clear_cart")

        from app.core.redis import set_cart_sync

        try:
            # Clear the cart (sync Redis)
            set_cart_sync(session_id, {"items": [], "updated_at": str(datetime.now())}, ttl=3600)

            # Emit empty cart to frontend
            emit_cart_data(session_id, [], 0)

            logger.info("cart_cleared", session_id=session_id)
            return "Cart cleared. You can start fresh!"

        except Exception as e:
            logger.error("clear_cart_error", error=str(e), session_id=session_id)
            return f"Error clearing cart: {str(e)}"

    return clear_cart


def create_update_quantity_tool(session_id: str):
    """Factory to create update_quantity tool with session context."""

    @tool("update_quantity")
    def update_quantity(item_name: str, new_quantity: int) -> str:
        """
        Update the quantity of an existing item in the cart.

        Modifies the quantity of an item already in cart without removing and re-adding.
        Automatically recalculates cart total.

        Args:
            item_name: Name of the item to update (e.g., "burger", "Butter Chicken")
            new_quantity: New quantity to set (must be positive integer >= 1)

        Returns:
            Confirmation of updated quantity with item name and new cart total.

        Examples:
            - update_quantity("burger", 3) → Changes burger quantity to 3
            - update_quantity("Butter Chicken", 2) → Changes Butter Chicken to 2
            - update_quantity("coke", 5) → Changes Coke quantity to 5

        Common triggers:
            - Customer: "change quantity to 3" → update_quantity(item, 3)
            - Customer: "make it 5 burgers" → update_quantity("burger", 5)
            - Customer: "update to 2" → update_quantity(item, 2)
        """
        # Emit activity for frontend (sync)
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        emit_tool_activity(session_id, "update_quantity")

        from app.core.db_pool import SyncDBConnection

        try:
            # VALIDATION: Quantity must be positive and reasonable
            if new_quantity <= 0:
                return f"[INVALID QUANTITY] I can't update to {new_quantity} items. Quantity must be at least 1. Use 'remove from cart' to remove items."

            if new_quantity > 50:
                return f"[INVALID QUANTITY] That's a lot! Our maximum order quantity per item is 50. If you need more, please contact us directly."

            item_name_clean = item_name.strip()

            with SyncDBConnection() as conn:
                with conn.cursor() as cur:
                    # Update quantity in SQL session_cart (same store as event-sourced tools)
                    cur.execute(
                        """UPDATE session_cart
                           SET quantity = %s, updated_at = NOW()
                           WHERE session_id = %s AND LOWER(item_name) = LOWER(%s) AND is_active = TRUE""",
                        (new_quantity, session_id, item_name_clean)
                    )
                    rows_updated = cur.rowcount
                    conn.commit()

                    if rows_updated == 0:
                        return f"Item '{item_name}' not found in cart."

                    # Get updated cart
                    cur.execute("SELECT * FROM get_session_cart(%s)", (session_id,))
                    columns = [desc[0] for desc in cur.description] if cur.description else []
                    items = [dict(zip(columns, row)) for row in cur.fetchall()]

                    cur.execute("SELECT get_cart_total(%s)", (session_id,))
                    total_row = cur.fetchone()
                    new_total = float(total_row[0]) if total_row and total_row[0] else 0.0

            # Emit updated cart card
            emit_cart_data(session_id, items, new_total)

            logger.info(
                "quantity_updated",
                session_id=session_id,
                item=item_name_clean,
                new_qty=new_quantity
            )

            return f"Updated {item_name} to {new_quantity}. Cart total: Rs.{new_total:.0f}"

        except Exception as e:
            logger.error("update_quantity_error", error=str(e), session_id=session_id)
            return f"Update error: {str(e)}"

    return update_quantity


def create_set_special_instructions_tool(session_id: str):
    """Factory to create set_special_instructions tool with session context."""

    @tool("set_special_instructions")
    def set_special_instructions(item_name: str, instructions: str) -> str:
        """
        Add special instructions for a cart item.

        Use for customizations like "no onions", "extra spicy", "allergic to nuts", etc.

        Args:
            item_name: Name of the item to add instructions to.
            instructions: Special instructions (e.g., "no onions", "extra cheese").

        Returns:
            Confirmation that instructions were added.
        """
        # Emit activity for frontend (sync)
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "set_special_instructions")

        from app.core.redis import get_cart_sync, set_cart_sync

        try:
            # VALIDATION: Instructions length
            instructions_clean = instructions.strip()
            if not instructions_clean:
                return "[INVALID INSTRUCTIONS] Please provide specific instructions (e.g., 'no onions', 'extra spicy')."

            if len(instructions_clean) > 200:
                return "[INVALID INSTRUCTIONS] Instructions are too long (max 200 characters). Please keep them brief and specific."

            item_name_clean = item_name.strip().lower()

            # Get cart (sync Redis)
            cart_data = get_cart_sync(session_id) or {"items": []}
            items = cart_data.get("items", [])

            if not items:
                return "[EMPTY CART] Your cart is empty. Please add items first before adding special instructions."

            # Find and update item
            for item in items:
                if item_name_clean in item.get("name", "").lower():
                    item["special_instructions"] = instructions

                    # Save cart (sync Redis)
                    cart_data['items'] = items
                    cart_data['updated_at'] = str(datetime.now())
                    set_cart_sync(session_id, cart_data, ttl=3600)

                    logger.info(
                        "special_instructions_set",
                        session_id=session_id,
                        item=item.get("name"),
                        instructions=instructions
                    )

                    return f"Added instructions for {item.get('name')}: \"{instructions}\""

            return f"Item '{item_name}' not found in cart. Add it first."

        except Exception as e:
            logger.error("set_special_instructions_error", error=str(e), session_id=session_id)
            return f"Error: {str(e)}"

    return set_special_instructions


def create_get_item_details_tool(session_id: str):
    """Factory to create get_item_details tool with session context."""

    @tool("get_item_details")
    def get_item_details(item_name: str) -> str:
        """
        Get detailed information about a menu item.

        Use when customer asks about ingredients, allergens, or wants more info.

        Args:
            item_name: Name of the menu item to get details for.

        Returns:
            Item details including description, ingredients, and allergen info.
        """
        # Emit activity for frontend (sync)
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "get_item_details")

        try:
            # Try to get from preloader first
            item = None
            try:
                from app.core.preloader import get_preloaded_data
                menu_data = get_preloaded_data()
                menu_items = menu_data.get("menu_items", [])

                item_name_clean = item_name.strip().lower()
                for menu_item in menu_items:
                    if item_name_clean in menu_item.get("name", "").lower():
                        item = menu_item
                        break
            except Exception:
                pass

            # Fallback to DB if not found in preloader
            if not item:
                item = _find_menu_item_in_db(item_name)

            if not item:
                return f"Item '{item_name}' not found on the menu."

            # Build details response
            details = [f"**{item.get('name')}** - Rs.{item.get('price', 0)}"]

            if item.get('description'):
                details.append(f"Description: {item.get('description')}")

            if item.get('ingredients'):
                details.append(f"Ingredients: {item.get('ingredients')}")

            if item.get('allergens'):
                details.append(f"⚠️ Allergens: {item.get('allergens')}")

            if item.get('is_vegetarian'):
                details.append("🥬 Vegetarian")

            if item.get('is_vegan'):
                details.append("🌱 Vegan")

            if item.get('spice_level'):
                spice = "🌶️" * item.get('spice_level', 0)
                details.append(f"Spice level: {spice}")

            if item.get('calories'):
                details.append(f"Calories: {item.get('calories')} kcal")

            return "\n".join(details)

        except Exception as e:
            logger.error("get_item_details_error", error=str(e), session_id=session_id)
            return f"Error getting details: {str(e)}"

    return get_item_details


# ============================================================================
# REORDER TOOL - Quick reorder from last order
# ============================================================================

def create_reorder_tool(session_id: str):
    """Factory to create reorder tool with session context."""

    @tool("reorder_last_order")
    async def reorder_last_order() -> str:
        """
        Reorder items from the customer's last order.

        Use when customer says things like:
        - "reorder my last order"
        - "order the same thing again"
        - "repeat my previous order"

        This finds their most recent order and adds all items to the current cart.

        Returns:
            Confirmation of items added to cart or message if no previous orders.
        """
        # Emit activity for frontend (async - no thread overhead)
        from app.core.agui_events import emit_tool_activity_async, emit_cart_data_async
        await emit_tool_activity_async(session_id, "reorder_last_order")

        from app.core.redis import get_redis_client, get_cart, set_cart
        import json

        try:
            # Order history operations use async Redis client
            redis_client = await get_redis_client()

            # Get order history for this session
            history_key = f"order_history:{session_id}"
            recent_orders = await redis_client.lrange(history_key, 0, 0)  # Get most recent

            if not recent_orders:
                return "You don't have any previous orders yet. Would you like to browse our menu?"

            # Get the last order details
            last_order_id = recent_orders[0].decode() if isinstance(recent_orders[0], bytes) else recent_orders[0]
            order_key = f"order:{session_id}:{last_order_id}"
            order_data = await redis_client.get(order_key)

            if not order_data:
                return "I couldn't find your last order details. Would you like to browse our menu instead?"

            order = json.loads(order_data)
            order_items = order.get("items", [])

            if not order_items:
                return "Your last order didn't have any items. Would you like to browse our menu?"

            # Get current cart (async Redis)
            cart_data = await get_cart(session_id)
            current_items = cart_data.get("items", [])

            # Add items from last order to current cart
            added_items = []
            for item in order_items:
                # Check if item is already in cart
                existing = next((i for i in current_items if i.get("name", "").lower() == item.get("name", "").lower()), None)
                if existing:
                    existing["quantity"] += item.get("quantity", 1)
                else:
                    current_items.append({
                        "name": item.get("name"),
                        "quantity": item.get("quantity", 1),
                        "price": item.get("price", 0),
                        "item_id": item.get("item_id")
                    })
                added_items.append(f"{item.get('quantity', 1)}x {item.get('name')}")

            # Calculate new total
            total = sum(i.get("price", 0) * i.get("quantity", 1) for i in current_items)

            # Save updated cart (async Redis)
            cart_data["items"] = current_items
            cart_data["total"] = total
            await set_cart(session_id, cart_data)

            # Emit cart data for rich UI (async)
            await emit_cart_data_async(session_id, current_items, total)

            items_list = ", ".join(added_items)
            return f"I've added your previous order to the cart: {items_list}. Total: Rs.{total}. Ready to checkout, or would you like to add anything else?"

        except Exception as e:
            logger.error("reorder_error", error=str(e), session_id=session_id)
            return f"Sorry, I couldn't reorder your last order. Would you like to browse the menu instead?"

    return reorder_last_order


# ============================================================================
# MENU FILTERING TOOLS (Cuisine & Popular Items)
# ============================================================================

def create_filter_by_cuisine_tool(session_id: str):
    """Factory to create filter_by_cuisine tool with session context."""

    @tool("filter_by_cuisine")
    def filter_by_cuisine(cuisine: Optional[str] = None) -> str:
        """
        Filter menu items by cuisine type.

        Use this when customer asks for specific cuisine like:
        - "show Italian dishes"
        - "browse by cuisine"
        - "what Asian food do you have"

        Args:
            cuisine: Cuisine type to filter by (e.g., "Italian", "Asian", "Indian", "American").
                    Leave empty to show all available cuisines.

        Returns:
            List of menu items from that cuisine or available cuisine types.
        """
        from app.core.agui_events import emit_tool_activity, emit_menu_data
        from app.core.preloader import get_menu_preloader, get_current_meal_period
        from app.core.redis import get_cart_sync

        emit_tool_activity(session_id, "filter_by_cuisine")

        try:
            # If no cuisine specified, show available cuisines
            if not cuisine:
                preloader = get_menu_preloader()
                if not preloader.is_loaded:
                    return "Menu is loading. Please try again in a moment."

                # Get all unique cuisines from the menu
                all_cuisines = set()
                for item in preloader.menu:
                    item_cuisines = item.get("cuisines", [])
                    if isinstance(item_cuisines, list):
                        all_cuisines.update(item_cuisines)

                if not all_cuisines:
                    return "We have a variety of cuisines available. Would you like to see the full menu?"

                cuisines_list = ", ".join(sorted(all_cuisines))
                return f"We have the following cuisines available: {cuisines_list}. Which cuisine would you like to explore?"

            # Filter menu by specified cuisine
            cuisine_lower = cuisine.lower().strip()

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

            # Get mapped cuisine names or use original
            target_cuisines = cuisine_mapping.get(cuisine_lower, [cuisine])

            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading. Please try again in a moment."

            # Filter items by cuisine (check if any target cuisine matches)
            filtered_items = []
            for item in preloader.menu:
                item_cuisines = item.get("cuisines", [])
                if isinstance(item_cuisines, list):
                    # Check if any of the target cuisines match any of the item's cuisines
                    for target_cuisine in target_cuisines:
                        if any(target_cuisine.lower() in c.lower() or c.lower() in target_cuisine.lower() for c in item_cuisines):
                            filtered_items.append(item)
                            break  # Don't add the same item twice

            if not filtered_items:
                return f"We don't have {cuisine} dishes currently available. Would you like to try another cuisine or see our full menu?"

            # Get current cart to mark items already in cart
            cart_data = get_cart_sync(session_id)
            cart_items = cart_data.get("items", []) if cart_data else []
            cart_item_names = {item.get("name", "").lower() for item in cart_items}

            # Build structured menu data
            current_meal = get_current_meal_period()
            structured_items = []
            for item in filtered_items[:20]:  # Limit to 20 items
                item_name = item.get("name", "")
                if item_name.lower() not in cart_item_names:
                    structured_items.append({
                        "name": item_name,
                        "price": item.get("price", 0),
                        "category": _infer_category(item_name),
                        "description": item.get("description", ""),
                        "item_id": str(item.get("id", "")),
                        "meal_types": item.get("meal_types") or ["All Day"],
                    })

            # Emit menu card with filtered items (no meal period tabs for filtered view)
            if structured_items:
                emit_menu_data(session_id, structured_items, current_meal_period=current_meal, show_meal_filters=False)
                return f"[MENU CARD DISPLAYED] Here are our {cuisine} dishes! I've shown {len(structured_items)} items. Which one would you like to try?"
            else:
                return f"All {cuisine} items are already in your cart! Would you like to browse other cuisines?"

        except Exception as e:
            logger.error("filter_by_cuisine_error", error=str(e), session_id=session_id)
            return f"Sorry, I had trouble filtering by {cuisine}. Would you like to see the full menu instead?"

    return filter_by_cuisine


def create_show_popular_items_tool(session_id: str):
    """Factory to create show_popular_items tool with session context."""

    @tool("show_popular_items")
    def show_popular_items() -> str:
        """
        Show popular/recommended menu items.

        Use this when customer asks for:
        - "show popular items"
        - "what's recommended"
        - "best sellers"
        - "what's good here"

        Returns:
            List of popular/recommended menu items.
        """
        from app.core.agui_events import emit_tool_activity, emit_menu_data
        from app.core.preloader import get_menu_preloader, get_current_meal_period
        from app.core.redis import get_cart_sync

        emit_tool_activity(session_id, "show_popular_items")

        try:
            preloader = get_menu_preloader()
            if not preloader.is_loaded:
                return "Menu is loading. Please try again in a moment."

            # Filter for recommended items or highest ranked items
            popular_items = []
            for item in preloader.menu:
                is_recommended = item.get("is_recommended", False)
                rank = item.get("rank", 0)
                if is_recommended or rank > 0:
                    popular_items.append(item)

            # Sort by rank (highest first)
            popular_items.sort(key=lambda x: x.get("rank", 0), reverse=True)

            # If no recommended items, show top items by default
            if not popular_items:
                popular_items = preloader.menu[:10]  # Top 10 items

            # Get current cart
            cart_data = get_cart_sync(session_id)
            cart_items = cart_data.get("items", []) if cart_data else []
            cart_item_names = {item.get("name", "").lower() for item in cart_items}

            # Build structured menu data
            current_meal = get_current_meal_period()
            structured_items = []
            for item in popular_items[:15]:  # Limit to 15 items
                item_name = item.get("name", "")
                if item_name.lower() not in cart_item_names:
                    structured_items.append({
                        "name": item_name,
                        "price": item.get("price", 0),
                        "category": _infer_category(item_name),
                        "description": item.get("description", ""),
                        "item_id": str(item.get("id", "")),
                        "meal_types": item.get("meal_types") or ["All Day"],
                    })

            # Emit menu card with popular items (no meal period tabs for filtered view)
            if structured_items:
                emit_menu_data(session_id, structured_items, current_meal_period=current_meal, show_meal_filters=False)
                return f"[MENU CARD DISPLAYED] Here are our popular items! I've shown {len(structured_items)} customer favorites. What would you like to try?"
            else:
                return "All our popular items are already in your cart! Would you like to explore other menu options?"

        except Exception as e:
            logger.error("show_popular_items_error", error=str(e), session_id=session_id)
            return "Sorry, I had trouble loading popular items. Would you like to see the full menu instead?"

    return show_popular_items


# ============================================================================
# PAYMENT TOOLS (Mock Payment Flow)
# ============================================================================

def create_initiate_payment_tool(session_id: str):
    """Factory to create initiate_payment tool with session context."""

    @tool("initiate_payment")
    def initiate_payment(order_id: str = "") -> str:
        """
        Initiate Razorpay payment for an order.

        Use this when customer chooses card payment. This creates a secure
        Razorpay payment link that the customer can use to complete payment.

        Args:
            order_id: Order ID to pay for (e.g., "ORD-ABC12345"). Leave empty for most recent.

        Returns:
            Payment link or error message.
        """
        async def _async_initiate_payment():
                from app.core.redis import get_sync_redis_client
                from app.core.agui_events import emit_payment_link
                from app.tools.external_apis.razorpay_tools import razorpay_payment_tool
                import json
                import os

                try:
                    # Check if Razorpay is configured
                    razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "")
                    if not razorpay_key_id or razorpay_key_id.startswith("your_") or razorpay_key_id == "rzp_test_XXXXXXXXXXXXX":
                        return (
                            "Payment gateway is not configured. Please contact restaurant support.\n\n"
                            "For admins: Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET in .env file.\n"
                            "Get test keys from: https://dashboard.razorpay.com/app/keys (Test Mode ON)"
                        )

                    redis_client = get_sync_redis_client()

                    # Get pending order from Redis (created during checkout)
                    pending_order_key = f"pending_order:{session_id}"
                    pending_order_data = redis_client.get(pending_order_key)

                    if not pending_order_data:
                        return "No pending order found. Please complete checkout first."

                    pending_order = json.loads(pending_order_data)
                    order_display_id = pending_order.get("order_id")
                    total_amount = float(pending_order.get("total", 0))

                    if total_amount <= 0:
                        return "Invalid order amount. Please contact support."

                    # Get customer info from session (for Razorpay customer details)
                    # Default to guest customer if no customer info
                    customer_name = "Guest Customer"
                    customer_email = f"guest_{session_id[:8]}@restaurant.com"
                    customer_phone = "9999999999"  # Razorpay requires phone

                    # Try to get actual customer info if available
                    try:
                        customer_key = f"session:{session_id}:customer"
                        customer_data = redis_client.get(customer_key)
                        if customer_data:
                            customer = json.loads(customer_data)
                            customer_name = customer.get("name", customer_name)
                            customer_email = customer.get("email", customer_email)
                            customer_phone = customer.get("phone", customer_phone)
                    except:
                        pass  # Use defaults

                    # Save pending order to database before payment
                    # (Razorpay tool requires database UUID, not Redis order reference)
                    from app.core.db_pool import get_async_db_pool

                    try:
                        pool = await get_async_db_pool()
                        async with pool.acquire() as conn:
                            # Get lookup table UUIDs
                            order_type_id = await conn.fetchval(
                                "SELECT order_type_id FROM order_type_table WHERE order_type_code = $1",
                                pending_order.get("order_type", "take_away")
                            )
                            order_status_id = await conn.fetchval(
                                "SELECT order_status_type_id FROM order_status_type WHERE order_status_code = $1",
                                "pending"
                            )
                            order_source_id = await conn.fetchval(
                                "SELECT order_source_type_id FROM order_source_type WHERE order_source_type_code = $1",
                                "chat_agent"
                            )

                            # Insert order record
                            db_order_id = await conn.fetchval(
                                """
                                INSERT INTO orders (
                                    restaurant_id,
                                    order_type_id,
                                    order_status_type_id,
                                    order_source_type_id,
                                    order_external_reference_id,
                                    order_display_id,
                                    total_amount,
                                    device_id
                                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                                RETURNING order_id
                                """,
                                pending_order.get("restaurant_id"),
                                order_type_id,
                                order_status_id,
                                order_source_id,
                                order_display_id,  # External reference
                                order_display_id,  # Display ID
                                total_amount,
                                session_id  # Device ID
                            )

                            # Insert order items
                            items = pending_order.get("items", [])
                            for item in items:
                                await conn.execute(
                                    """
                                    INSERT INTO order_item (
                                        order_id,
                                        item_name,
                                        quantity,
                                        unit_price,
                                        line_total
                                    ) VALUES ($1, $2, $3, $4, $5)
                                    """,
                                    db_order_id,
                                    item.get("name"),
                                    item.get("quantity", 1),
                                    item.get("price", 0),
                                    item.get("quantity", 1) * item.get("price", 0)
                                )

                            logger.info(
                                "pending_order_saved_to_database",
                                session_id=session_id,
                                order_display_id=order_display_id,
                                db_order_id=str(db_order_id)
                            )

                    except Exception as e:
                        logger.error(f"Failed to save pending order to database: {e}", exc_info=True)
                        return f"Failed to prepare order for payment: {str(e)}. Please try again."

                    # Create Razorpay payment link using razorpay_payment_tool
                    payment_result = await razorpay_payment_tool._execute_impl(
                        operation="create_order",
                        order_id=db_order_id,
                        user_id="guest",  # For guest checkout
                        payment_source="chat",
                        session_id=session_id,
                        notes={
                            "order_display_id": order_display_id,
                            "session_id": session_id,
                            "customer_name": customer_name
                        }
                    )

                    if payment_result.status.value == "success":
                        payment_link = payment_result.data.get("payment_link")
                        expires_at = payment_result.data.get("expires_at")

                        # Emit payment link to frontend
                        try:
                            emit_payment_link(session_id, payment_link, total_amount, expires_at)
                        except Exception as e:
                            logger.warning(f"Failed to emit payment link event: {e}")

                        # Update pending order in Redis with payment info
                        pending_order["payment_link"] = payment_link
                        pending_order["payment_initiated"] = True
                        redis_client.setex(pending_order_key, 3600, json.dumps(pending_order))

                        logger.info(
                            "razorpay_payment_initiated",
                            session_id=session_id,
                            order_id=order_display_id,
                            payment_link=payment_link[:50]
                        )

                        return (
                            f"Payment link generated for order {order_display_id}!\n"
                            f"Amount: Rs.{total_amount:.0f}\n\n"
                            f"Click here to pay securely: {payment_link}\n\n"
                            f"Link valid for 15 minutes.\n"
                            f"After payment, return here for order confirmation."
                        )
                    else:
                        error_msg = payment_result.data.get("error", "Unknown error")
                        logger.error(f"Razorpay payment creation failed: {error_msg}")
                        return f"Payment initiation failed: {error_msg}"

                except Exception as e:
                    logger.error("initiate_payment_error", error=str(e), session_id=session_id, exc_info=True)
                    return f"Payment initiation failed: {str(e)}. Please try again or contact support."

        return run_async(_async_initiate_payment())

    return initiate_payment


def create_submit_card_details_tool(session_id: str):
    """Factory to create submit_card_details tool with session context."""

    @tool("submit_card_details")
    async def submit_card_details(card_number: str, expiry: str, cvv: str, cardholder_name: str) -> str:
        """
        Submit card details for payment.

        Use this when customer provides their card details.
        After validation, an OTP will be sent for verification.

        Args:
            card_number: 16-digit card number (spaces will be removed)
            expiry: Card expiry in MM/YY format
            cvv: 3-4 digit CVV
            cardholder_name: Name on card

        Returns:
            Result of card submission and OTP status.
        """
        from app.core.redis import get_redis_client
        from app.core.db_pool import AsyncDBConnection
        import json
        import re
        import uuid as uuid_module

        try:
            redis_client = get_redis_client()

            # Get pending payment info (async Redis)
            payment_info_raw = await redis_client.get(f"payment_pending:{session_id}")
            if not payment_info_raw:
                return "No pending payment found. Please initiate payment first using 'pay for order'."

            payment_info = json.loads(payment_info_raw)

            # Validate card details (basic validation for mock)
            card_clean = re.sub(r'\D', '', card_number)
            if len(card_clean) < 13 or len(card_clean) > 19:
                return "Invalid card number. Please enter a valid 13-19 digit card number."

            expiry_match = re.match(r'^(\d{2})/(\d{2})$', expiry.strip())
            if not expiry_match:
                return "Invalid expiry format. Please use MM/YY format (e.g., 12/25)."

            cvv_clean = re.sub(r'\D', '', cvv)
            if len(cvv_clean) < 3 or len(cvv_clean) > 4:
                return "Invalid CVV. Please enter a 3-4 digit CVV."

            if len(cardholder_name.strip()) < 2:
                return "Please enter the cardholder name."

            # Determine card network (mock)
            card_network = "Unknown"
            if card_clean.startswith('4'):
                card_network = "Visa"
            elif card_clean.startswith(('51', '52', '53', '54', '55')):
                card_network = "Mastercard"
            elif card_clean.startswith(('34', '37')):
                card_network = "Amex"
            elif card_clean.startswith('6'):
                card_network = "RuPay"

            # Create payment transaction in PostgreSQL (async with asyncpg)
            async with AsyncDBConnection() as conn:
                # Get card payment method ID
                method_row = await conn.fetchrow("""
                    SELECT order_payment_method_id FROM order_payment_method
                    WHERE order_payment_method_code = 'card' LIMIT 1
                """)
                card_method_id = method_row['order_payment_method_id'] if method_row else None

                # Get awaiting_otp status ID
                status_row = await conn.fetchrow("""
                    SELECT payment_status_type_id FROM payment_status_type
                    WHERE payment_status_code = 'awaiting_otp' LIMIT 1
                """)
                awaiting_otp_status_id = status_row['payment_status_type_id'] if status_row else None

                # Get gateway ID
                gateway_row = await conn.fetchrow("""
                    SELECT payment_gateway_id FROM payment_gateway
                    WHERE gateway_code = 'mock_gateway' LIMIT 1
                """)
                gateway_id = gateway_row['payment_gateway_id'] if gateway_row else None

                # Create transaction
                transaction_id = str(uuid_module.uuid4())
                gateway_payment_id = f"txn_{uuid_module.uuid4().hex[:12]}"

                await conn.execute("""
                    INSERT INTO payment_transaction (
                        payment_transaction_id, payment_order_id, order_id,
                        payment_gateway_id, gateway_payment_id,
                        order_payment_method_id, payment_method_details,
                        transaction_amount, amount_due, transaction_currency,
                        payment_status_type_id, card_network, card_last4,
                        otp_sent_at, attempted_at
                    ) VALUES (
                        $1::uuid, $2::uuid, $3::uuid,
                        $4, $5,
                        $6, $7,
                        $8, $9, 'INR',
                        $10, $11, $12,
                        NOW(), NOW()
                    )
                """, transaction_id, payment_info['payment_order_id'], payment_info['order_id'],
                    gateway_id, gateway_payment_id, card_method_id,
                    json.dumps({
                        "card_network": card_network,
                        "card_last4": card_clean[-4:],
                        "expiry": expiry.strip(),
                        "cardholder": cardholder_name.strip()
                    }),
                    payment_info['amount'], payment_info['amount'],
                    awaiting_otp_status_id, card_network, card_clean[-4:])

                # Update payment order status
                await conn.execute("""
                    UPDATE payment_order SET
                        payment_status_type_id = $1,
                        attempts = attempts + 1,
                        updated_at = NOW()
                    WHERE payment_order_id = $2::uuid
                """, awaiting_otp_status_id, payment_info['payment_order_id'])

            # Update Redis with transaction info (async)
            payment_info['payment_transaction_id'] = transaction_id
            payment_info['card_last4'] = card_clean[-4:]
            payment_info['card_network'] = card_network
            payment_info['status'] = 'awaiting_otp'
            await redis_client.setex(
                f"payment_pending:{session_id}",
                1800,
                json.dumps(payment_info)
            )

            logger.info(
                "card_details_submitted",
                session_id=session_id,
                transaction_id=transaction_id,
                card_network=card_network,
                card_last4=card_clean[-4:]
            )

            # Mock: OTP always sent successfully
            masked_phone = "XXXXXX7890"  # Mock masked phone

            return (
                f"Card ending in {card_clean[-4:]} ({card_network}) accepted.\n"
                f"An OTP has been sent to {masked_phone}.\n\n"
                "Please enter the 6-digit OTP to complete payment.\n"
                "(For testing, use OTP: 123456)"
            )

        except Exception as e:
            logger.error("submit_card_details_error", error=str(e), session_id=session_id)
            return f"Card submission failed: {str(e)}"

    return submit_card_details


def create_verify_payment_otp_tool(session_id: str):
    """Factory to create verify_payment_otp tool with session context."""

    @tool("verify_payment_otp")
    async def verify_payment_otp(otp: str) -> str:
        """
        Verify OTP for payment.

        Use this when customer provides the OTP for payment verification.
        In sandbox/test mode, OTP "123456" always succeeds.

        Args:
            otp: 6-digit OTP received on phone

        Returns:
            Payment completion status.
        """
        from app.core.redis import get_redis_client
        from app.core.db_pool import AsyncDBConnection
        import json
        import random

        try:
            redis_client = get_redis_client()

            # Get pending payment info (async Redis)
            payment_info_raw = await redis_client.get(f"payment_pending:{session_id}")
            if not payment_info_raw:
                return "No pending payment found. Please initiate payment first."

            payment_info = json.loads(payment_info_raw)

            if payment_info.get('status') != 'awaiting_otp':
                return "Payment is not awaiting OTP verification. Current status: " + payment_info.get('status', 'unknown')

            # Validate OTP
            import os
            test_mode = os.getenv("PAYMENT_TEST_MODE", "true").lower() == "true"

            otp_clean = otp.strip().replace(' ', '')
            if len(otp_clean) != 6 or not otp_clean.isdigit():
                return "Invalid OTP format. Please enter a 6-digit OTP."

            if test_mode:
                # Test mode - 123456 always succeeds, others fail 50% of time
                if otp_clean == "123456":
                    otp_valid = True
                else:
                    otp_valid = random.random() > 0.5  # 50% success for random OTPs

                if not otp_valid:
                    return "Invalid OTP. Please try again or request a new OTP.\n(Hint: Use 123456 for testing)"
            else:
                # Real payment mode - verify OTP with payment gateway
                # TODO: Integrate with real payment gateway OTP verification
                return "Real payment gateway integration not yet implemented. Please set PAYMENT_TEST_MODE=true in .env file."

            # Update transaction in PostgreSQL (async with asyncpg)
            async with AsyncDBConnection() as conn:
                # Get captured status ID
                status_row = await conn.fetchrow("""
                    SELECT payment_status_type_id FROM payment_status_type
                    WHERE payment_status_code = 'captured' LIMIT 1
                """)
                captured_status_id = status_row['payment_status_type_id'] if status_row else None

                # Get confirmed order status ID
                order_status_row = await conn.fetchrow("""
                    SELECT order_status_type_id FROM order_status_type
                    WHERE order_status_code = 'confirmed' LIMIT 1
                """)
                confirmed_status_id = order_status_row['order_status_type_id'] if order_status_row else None

                # Update transaction
                await conn.execute("""
                    UPDATE payment_transaction SET
                        otp_verified = TRUE,
                        otp_verified_at = NOW(),
                        payment_status_type_id = $1,
                        amount_paid = transaction_amount,
                        amount_due = 0,
                        authorized_at = NOW(),
                        captured_at = NOW(),
                        updated_at = NOW()
                    WHERE payment_transaction_id = $2::uuid
                """, captured_status_id, payment_info['payment_transaction_id'])

                # Update payment order
                await conn.execute("""
                    UPDATE payment_order SET
                        payment_status_type_id = $1,
                        updated_at = NOW()
                    WHERE payment_order_id = $2::uuid
                """, captured_status_id, payment_info['payment_order_id'])

                # Update order payment status
                await conn.execute("""
                    UPDATE orders SET
                        payment_status = 'paid',
                        order_status_type_id = $1,
                        updated_at = NOW()
                    WHERE order_id = $2::uuid
                """, confirmed_status_id, payment_info['order_id'])

                # Create order_payment record
                method_row = await conn.fetchrow("""
                    SELECT order_payment_method_id FROM order_payment_method
                    WHERE order_payment_method_code = 'card' LIMIT 1
                """)
                card_method_id = method_row['order_payment_method_id'] if method_row else None

                await conn.execute("""
                    INSERT INTO order_payment (
                        payment_order_id, primary_transaction_id, order_id,
                        order_payment_method_id, paid_amount,
                        order_payment_status, order_payment_transaction_reference
                    ) VALUES (
                        $1::uuid, $2::uuid, $3::uuid,
                        $4, $5,
                        'completed', $6
                    )
                """, payment_info['payment_order_id'], payment_info['payment_transaction_id'],
                    payment_info['order_id'], card_method_id, payment_info['amount'],
                    payment_info.get('gateway_order_id', ''))

            # Update order in Redis (async)
            order_key = f"order:{session_id}:{payment_info['order_display_id']}"
            order_data_raw = await redis_client.get(order_key)
            if order_data_raw:
                order_data = json.loads(order_data_raw)
                order_data['payment_status'] = 'paid'
                order_data['payment_transaction_id'] = payment_info['payment_transaction_id']
                await redis_client.setex(order_key, 86400, json.dumps(order_data))

            # Save confirmed order to MongoDB for persistence
            try:
                from pymongo import MongoClient
                import os
                from datetime import datetime

                mongo_url = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://mongodb:27017")
                mongo_db = os.getenv("MONGODB_DATABASE_NAME", "restaurant_ai_analytics")

                client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
                db = client[mongo_db]

                # Get pending order from Redis
                pending_order_key = f"pending_order:{session_id}"
                pending_order_raw = await redis_client.get(pending_order_key)

                if pending_order_raw:
                    pending_order = json.loads(pending_order_raw)
                    order_items_data = []
                    for item in pending_order.get('items', []):
                        order_items_data.append({
                            "name": item.get("name", "Item"),
                            "quantity": item.get("quantity", 1),
                            "price": item.get("price", 0),
                            "item_total": item.get("price", 0) * item.get("quantity", 1)
                        })

                    order_doc = {
                        "order_id": payment_info['order_display_id'],
                        "session_id": session_id,
                        "items": order_items_data,
                        "total": payment_info['amount'],
                        "order_type": pending_order.get('order_type', 'take_away'),
                        "status": "confirmed",
                        "payment_status": "paid",
                        "payment_method": "card",
                        "payment_transaction_id": payment_info['payment_transaction_id'],
                        "card_network": payment_info.get('card_network'),
                        "card_last4": payment_info.get('card_last4'),
                        "created_at": pending_order.get('created_at', datetime.now().isoformat()),
                        "paid_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }

                    db.orders.insert_one(order_doc)
                    logger.info("order_persisted_to_mongodb", session_id=session_id, order_id=payment_info['order_display_id'])

                    # Clear pending order and cart
                    await redis_client.delete(pending_order_key)
                    from app.core.redis import set_cart_sync
                    set_cart_sync(session_id, {"items": [], "total": 0})

                client.close()
            except Exception as mongo_error:
                logger.warning("mongodb_order_persist_failed", error=str(mongo_error))

            # Clear pending payment
            await redis_client.delete(f"payment_pending:{session_id}")

            logger.info(
                "payment_completed",
                session_id=session_id,
                order_display_id=payment_info['order_display_id'],
                amount=payment_info['amount'],
                transaction_id=payment_info['payment_transaction_id']
            )

            # Emit order confirmation with receipt data
            from app.core.agui_events import emit_order_data
            if pending_order_raw:
                pending_order = json.loads(pending_order_raw)
                emit_order_data(
                    session_id=session_id,
                    order_id=payment_info['order_display_id'],
                    items=pending_order.get('items', []),
                    total=payment_info['amount'],
                    status="confirmed",
                    order_type=pending_order.get('order_type', 'take_away')
                )

            return (
                f"✅ Payment successful!\n\n"
                f"📋 Order: {payment_info['order_display_id']}\n"
                f"💰 Amount Paid: Rs.{payment_info['amount']:.0f}\n"
                f"💳 Card: {payment_info.get('card_network', 'Card')} ending in {payment_info.get('card_last4', '****')}\n\n"
                f"Your order is confirmed and being prepared!\n"
                f"You can view your receipt by saying 'show receipt for {payment_info['order_display_id']}'\n\n"
                "Thank you for your order! 🎉"
            )

        except Exception as e:
            logger.error("verify_payment_otp_error", error=str(e), session_id=session_id)
            return f"OTP verification failed: {str(e)}"

    return verify_payment_otp


def create_check_payment_status_tool(session_id: str):
    """Factory to create check_payment_status tool with session context."""

    @tool("check_payment_status")
    async def check_payment_status(order_id: str = "") -> str:
        """
        Check payment status for an order.

        Use this when customer asks about payment status.

        Args:
            order_id: Order ID to check payment for. Leave empty for most recent.

        Returns:
            Payment status details.
        """
        from app.core.redis import get_redis_client
        import json

        try:
            redis_client = await get_redis_client()
            order_display_id = order_id.strip().upper() if order_id else None

            # Get from pending payment first
            if not order_display_id:
                payment_info_raw = await redis_client.get(f"payment_pending:{session_id}")
                if payment_info_raw:
                    payment_info = json.loads(payment_info_raw)
                    order_display_id = payment_info.get('order_display_id')

            # If still no order_id, get most recent
            if not order_display_id:
                history_key = f"order_history:{session_id}"
                recent_orders = await redis_client.lrange(history_key, 0, 0)
                if recent_orders:
                    order_display_id = recent_orders[0].decode() if isinstance(recent_orders[0], bytes) else recent_orders[0]

            if not order_display_id:
                return "No orders found. Please place an order first."

            # Get from PostgreSQL
            from app.core.db_pool import AsyncDBConnection

            async with AsyncDBConnection() as conn:
                result = await conn.fetchrow("""
                    SELECT o.order_display_id, o.total_amount, o.payment_status,
                           po.gateway_order_id, pst.payment_status_name as po_status,
                           pt.card_network, pt.card_last4, pt.amount_paid,
                           pt.captured_at, pst2.payment_status_name as txn_status
                    FROM orders o
                    LEFT JOIN payment_order po ON o.payment_order_id = po.payment_order_id
                    LEFT JOIN payment_status_type pst ON po.payment_status_type_id = pst.payment_status_type_id
                    LEFT JOIN payment_transaction pt ON po.payment_order_id = pt.payment_order_id
                    LEFT JOIN payment_status_type pst2 ON pt.payment_status_type_id = pst2.payment_status_type_id
                    WHERE o.order_display_id = $1
                    ORDER BY pt.created_at DESC
                    LIMIT 1
                """, order_display_id)

                if not result:
                    return f"Order {order_display_id} not found."

                payment_status = result.get('payment_status', 'pending')

                if payment_status == 'paid':
                    card_info = ""
                    if result.get('card_network') and result.get('card_last4'):
                        card_info = f"\nCard: {result['card_network']} ending in {result['card_last4']}"
                    return (
                        f"Order {order_display_id} - PAID\n"
                        f"Amount: Rs.{result['amount_paid'] or result['total_amount']:.0f}{card_info}\n"
                        f"Transaction Status: {result.get('txn_status', 'Captured')}"
                    )
                elif payment_status == 'pending':
                    # Check if there's a pending payment in process
                    pending_raw = await redis_client.get(f"payment_pending:{session_id}")
                    if pending_raw:
                        pending = json.loads(pending_raw)
                        if pending.get('order_display_id') == order_display_id:
                            status = pending.get('status', 'pending')
                            if status == 'awaiting_otp':
                                return (
                                    f"Order {order_display_id} - AWAITING OTP\n"
                                    f"Amount: Rs.{pending['amount']:.0f}\n"
                                    "Please enter the OTP sent to your phone to complete payment.\n"
                                    "(For testing, use OTP: 123456)"
                                )
                            elif status == 'awaiting_card_details':
                                return (
                                    f"Order {order_display_id} - AWAITING CARD DETAILS\n"
                                    f"Amount: Rs.{pending['amount']:.0f}\n"
                                    "Please provide your card details to proceed with payment."
                                )

                    return (
                        f"Order {order_display_id} - PAYMENT PENDING\n"
                        f"Amount: Rs.{result['total_amount']:.0f}\n"
                        "Say 'pay for order' to initiate payment."
                    )
                else:
                    return (
                        f"Order {order_display_id} - {payment_status.upper()}\n"
                        f"Amount: Rs.{result['total_amount']:.0f}"
                    )

        except Exception as e:
            logger.error("check_payment_status_error", error=str(e), session_id=session_id)
            return f"Error checking payment status: {str(e)}"

    return check_payment_status


def create_cancel_payment_tool(session_id: str):
    """Factory to create cancel_payment tool with session context."""

    @tool("cancel_payment")
    async def cancel_payment() -> str:
        """
        Cancel an in-progress payment.

        Use this when customer wants to cancel the payment they started.
        The order will remain but payment will be marked as cancelled.

        Returns:
            Confirmation of payment cancellation.
        """
        from app.core.redis import get_redis_client
        import json

        try:
            redis_client = await get_redis_client()

            # Get pending payment info
            payment_info_raw = await redis_client.get(f"payment_pending:{session_id}")
            if not payment_info_raw:
                return "No pending payment to cancel."

            payment_info = json.loads(payment_info_raw)

            # Update in PostgreSQL
            from app.core.db_pool import AsyncDBConnection

            async with AsyncDBConnection() as conn:
                # Get cancelled status ID
                status_row = await conn.fetchrow("""
                    SELECT payment_status_type_id FROM payment_status_type
                    WHERE payment_status_code = 'cancelled' LIMIT 1
                """)
                cancelled_status_id = status_row['payment_status_type_id'] if status_row else None

                # Use transaction for multiple updates
                async with conn.transaction():
                    # Update payment order
                    await conn.execute("""
                        UPDATE payment_order SET
                            payment_status_type_id = $1,
                            updated_at = NOW()
                        WHERE payment_order_id = $2::uuid
                    """, cancelled_status_id, payment_info['payment_order_id'])

                    # Update transaction if exists
                    if payment_info.get('payment_transaction_id'):
                        await conn.execute("""
                            UPDATE payment_transaction SET
                                payment_status_type_id = $1,
                                failure_reason = 'Cancelled by user',
                                updated_at = NOW()
                            WHERE payment_transaction_id = $2::uuid
                        """, cancelled_status_id, payment_info['payment_transaction_id'])

                    # Reset order payment status
                    await conn.execute("""
                        UPDATE orders SET
                            payment_status = 'cancelled',
                            updated_at = NOW()
                        WHERE order_id = $1::uuid
                    """, payment_info['order_id'])

            # Clear pending payment from Redis
            await redis_client.delete(f"payment_pending:{session_id}")

            logger.info(
                "payment_cancelled",
                session_id=session_id,
                order_display_id=payment_info['order_display_id'],
                payment_order_id=payment_info['payment_order_id']
            )

            return (
                f"Payment cancelled for order {payment_info['order_display_id']}.\n"
                "You can initiate payment again when ready by saying 'pay for order'."
            )

        except Exception as e:
            logger.error("cancel_payment_error", error=str(e), session_id=session_id)
            return f"Error cancelling payment: {str(e)}"

    return cancel_payment


def create_select_payment_method_tool(session_id: str):
    """Factory to create select_payment_method tool with session context."""

    @tool("select_payment_method")
    def select_payment_method(method: str) -> str:
        """
        Select a payment method for the current order after checkout.

        NOTE: Payment is automatically initiated as online (Razorpay) after checkout.
        This tool is only needed if the automatic payment flow didn't trigger.

        Args:
            method: Payment method. Only "online" is supported (Razorpay — Card/UPI/NetBanking).

        Returns:
            Payment confirmation or payment link details.

        Common triggers:
            - "pay online" / "online payment" / "UPI" / "card" / "pay" → select_payment_method("online")
        """
        async def _async_select():
            from app.services.payment_state_service import get_payment_state, PaymentStep
            from app.workflows.payment_workflow import run_payment_workflow
            from app.core.agui_events import emit_tool_activity

            emit_tool_activity(session_id, "select_payment_method")

            # Normalize method name
            # Only online payment (Razorpay) is supported
            method_map = {
                "online": "online",
                "pay_online": "online",
                "upi": "online",
                "razorpay": "online",
                "card": "online",
                "pay": "online",
            }
            normalized = method_map.get(method.lower().strip(), method.lower().strip())

            # Get current payment state
            payment_state = get_payment_state(session_id)
            order_id = payment_state.get("order_id")
            amount = payment_state.get("amount", 0)

            if not order_id:
                return "No pending order found. Please checkout first before selecting a payment method."

            logger.info(
                "select_payment_method_tool",
                session_id=session_id,
                method=normalized,
                order_id=order_id,
                amount=amount
            )

            try:
                # Run payment workflow with selected method
                final_state = await run_payment_workflow(
                    session_id=session_id,
                    order_id=order_id,
                    amount=amount,
                    initial_method=normalized,
                    items=payment_state.get("items"),
                    order_type=payment_state.get("order_type"),
                    subtotal=payment_state.get("subtotal"),
                    packaging_charges=payment_state.get("packaging_charges")
                )

                step = final_state.get("step", "")

                if step == PaymentStep.CASH_SELECTED.value:
                    return (
                        f"[PAYMENT CONFIRMED] Cash payment confirmed for order {order_id}. "
                        f"Amount: Rs.{amount:.0f}. Customer will pay at counter/delivery. "
                        f"Order is confirmed!"
                    )
                elif step == PaymentStep.AWAITING_PAYMENT.value:
                    link = final_state.get("payment_link", "")
                    return (
                        f"[PAYMENT LINK SENT] Online payment link generated for order {order_id}. "
                        f"Amount: Rs.{amount:.0f}. Payment link has been displayed to the customer. "
                        f"They can complete payment via the link. Order will be confirmed after payment."
                    )
                elif step == PaymentStep.PAYMENT_FAILED.value:
                    error = final_state.get("error", "Unknown error")
                    return f"Payment setup failed: {error}. Please try again."
                else:
                    return f"Payment method '{normalized}' selected for order {order_id}."

            except Exception as e:
                logger.error("select_payment_method_error", error=str(e), session_id=session_id)
                return f"Error processing payment: {str(e)}. Please try again."

        return run_async(_async_select())

    return select_payment_method


# ============================================================================
# CREW CREATION
# ============================================================================

def create_food_ordering_crew(session_id: str, customer_id: Optional[str] = None) -> Crew:
    """
    Optimized single-agent crew using @tool decorated functions.

    Tools have auto-generated schemas from function signatures and docstrings.
    LLM reads these to understand:
    - What each tool does (from docstring)
    - Parameter names and types (from function signature)
    - How to call each tool correctly

    Args:
        session_id: Current chat session ID
        customer_id: Current customer ID (None if not authenticated)
    """
    import os
    from langchain_openai import ChatOpenAI
    from app.ai_services.llm_manager import get_llm_manager

    # Get API key from LLM manager pool (round-robin across validated accounts)
    llm_manager = get_llm_manager()
    api_key = llm_manager.get_next_api_key()
    os.environ["OPENAI_API_KEY"] = api_key

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,  # Lower = faster, more deterministic
        api_key=api_key,
        max_tokens=2048,  # CRITICAL FIX: Increased to accommodate 55 tool schemas and responses
    )

    # Tools - using factory functions for session-aware tools
    search_tool = create_search_menu_tool(session_id)
    add_tool = create_add_to_cart_tool(session_id)
    view_tool = create_view_cart_tool(session_id)
    remove_tool = create_remove_from_cart_tool(session_id)
    checkout_tool = create_checkout_tool(session_id)
    cancel_tool = create_cancel_order_tool(session_id)
    # Order status and history tools
    status_tool = create_get_order_status_tool(session_id)
    history_tool = create_get_order_history_tool(session_id)
    reorder_tool = create_reorder_tool(session_id)
    receipt_tool = create_get_order_receipt_tool(session_id)

    # Payment tools
    initiate_payment_tool = create_initiate_payment_tool(session_id)
    submit_card_tool = create_submit_card_details_tool(session_id)
    verify_otp_tool = create_verify_payment_otp_tool(session_id)
    payment_status_tool = create_check_payment_status_tool(session_id)
    cancel_payment_tool = create_cancel_payment_tool(session_id)
    select_payment_tool = create_select_payment_method_tool(session_id)

    # Phase 1 tools: Customer profile, FAQ, feedback (15 new tools)
    phase1_tools = get_all_phase1_tools(session_id, customer_id)

    # Phase 2 tools: Advanced menu filtering (9 new tools)
    phase2_tools = get_all_phase2_tools(session_id, customer_id)

    # Phase 3 tools: Table reservations (6 new tools)
    phase3_tools = get_all_phase3_tools(session_id, customer_id)

    # Phase 4 tools: Order enhancements (3 new tools)
    phase4_tools = get_all_phase4_tools(session_id, customer_id)

    # Phase 5 tools: Policies & info (2 new tools)
    phase5_tools = get_all_phase5_tools(session_id)

    logger.info("crew_tools_loaded",
                base_tools=16,
                phase1_tools=len(phase1_tools),
                phase2_tools=len(phase2_tools),
                phase3_tools=len(phase3_tools),
                phase4_tools=len(phase4_tools),
                phase5_tools=len(phase5_tools),
                total_tools=16 + len(phase1_tools) + len(phase2_tools) + len(phase3_tools) + len(phase4_tools) + len(phase5_tools),
                customer_authenticated=customer_id is not None,
                session=session_id)

    # Collect all tools (16 base + phase tools)
    base_tools = [
        search_tool, add_tool, view_tool, remove_tool, checkout_tool, cancel_tool,
        status_tool, history_tool, reorder_tool, receipt_tool,
        initiate_payment_tool, submit_card_tool, verify_otp_tool, payment_status_tool, cancel_payment_tool,
        select_payment_tool
    ]
    all_tools = base_tools + phase1_tools + phase2_tools + phase3_tools + phase4_tools + phase5_tools

    # Single efficient agent with CrewAI best practices
    agent = Agent(
        role="Kavya - Senior Restaurant Concierge",
        goal="Deliver exceptional dining experiences through personalized, accurate, and efficient service",
        backstory="""You are Kavya, a highly experienced senior restaurant concierge with over 10 years in premium dining establishments. You're known for your warm personality, exceptional attention to detail, and natural ability to gracefully handle any dining request.

Your strengths:
- Reading customer intent and adapting your service style accordingly
- Providing accurate information using real-time data from your comprehensive toolset
- Naturally clarifying ambiguities without making customers feel interrogated
- Balancing efficiency with genuine warmth and friendliness

You understand that great service means knowing when to guide patiently (with browsing customers) and when to expedite smoothly (with customers who have clear intent). You excel at handling dietary needs, preferences, reservations, and special occasions with care.

You rely on your tools to ensure every recommendation, price, cart detail, and order status is accurate - you never guess when you can look up the exact answer. Your conversational style is natural and adaptive, not robotic or scripted.""",
        llm=llm,
        tools=all_tools,
        # Best practices from docs.crewai.com
        verbose=False,  # Disabled for performance (reduces 10s to ~2s per request)
        allow_delegation=False,
        respect_context_window=True,  # Handle long conversations gracefully
        cache=True,  # Cache tool results for repeated queries
        max_iter=10,  # Prevent infinite loops
        max_retry_limit=2,  # Error resilience
    )

    # Task with pattern-based guidance following 2025 industry best practices
    task = Task(
        description="""Help the customer with their dining request.

## CONVERSATION CONTEXT
{context}

## SEMANTIC CONTEXT
{semantic_context}

## CUSTOMER MESSAGE
"{user_input}"

## SERVICE PATTERNS

**Order Accuracy (CRITICAL):**
NEVER call add_to_cart without an explicit quantity from the customer. If they say "add biryani" or "I want pizza" without a number, you MUST ask "How many would you like?" BEFORE calling add_to_cart. Do NOT assume quantity is 1.
When adding multiple items, add them ALL in ONE add_to_cart call using a JSON array:
Example: "2 burgers and 1 coke" → add_to_cart('[{"item": "burger", "quantity": 2}, {"item": "coke", "quantity": 1}]')
Example: "I want pizza" → Ask "How many?" first, then add_to_cart('[{"item": "pizza", "quantity": N}]')

**Ambiguity Resolution:**
When confirmations are unclear (like "yes" after offering multiple options), ask which specific option the customer prefers.
Example: You offered "Coke or Juice?" → Customer: "yes" → You: "Which drink would you prefer?"

**Tool Usage:**
Use your comprehensive toolset for real-time accurate data - menu items, prices, cart contents, order status, policies, allergen info, reservations. Trust tool outputs and incorporate them naturally in your responses.

**Adaptive Service:**
Read the customer's intent and adapt your approach:
- Browsing customers → Guide patiently, offer recommendations
- Customers with clear intent → Expedite efficiently
- Ambiguous requests → Clarify naturally without interrogation
- Special dietary needs → Use allergen/dietary tools proactively

**Upselling (Natural Suggestions):**
After adding items to cart, suggest complementary items naturally:
- Main course added → "Would you like to add a drink or side with that?"
- Only drinks in cart → "How about a snack to go with your drink?"
- Cart total > ₹500 → "Great order! Want to add a dessert to round it off?"
Keep suggestions brief, natural, and non-pushy. Only suggest once per add-to-cart, not repeatedly.

**Checkout & Payment Flow:**
When customer says "checkout" / "place order" → call checkout tool. This creates the order and shows payment options.
After checkout, you MUST ask: "How would you like to pay? You can pay online, cash, or card at counter."
When the customer chooses a payment method → call select_payment_method with their choice:
- "pay online" / "online" / "UPI" / "card" → select_payment_method("online")
- "cash" / "pay cash" → select_payment_method("cash")
- "card at counter" → select_payment_method("card_at_counter")
If customer says "cancel checkout" or "cancel order" → call cancel_payment or cancel_order.
NEVER guess or assume the payment method - always ask the customer.

**Language:**
If the customer message starts with [RESPOND IN HINGLISH...], respond in casual Hinglish (Roman script ONLY, NO Devanagari). Use simple words: "chahiye", "karo", "dekh lo" — NOT formal "chahenge", "karenge", "dekhenge". Mix English freely. Example: "Aapke cart mein 2 Masala Dosa add ho gaye, total ₹250. Aur kuch chahiye?"
If the customer message starts with [RESPOND IN TANGLISH...], respond in casual Tanglish (Roman script ONLY, NO Tamil script). Example: "Unga cart la 2 Masala Dosa add aaiduchu, total ₹250. Vera enna venum?"
Keep food names, prices, order IDs in English always.

Respond warmly and naturally!""",
        expected_output="A friendly, natural language response confirming the action taken",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,  # Disabled for performance
    )

    return crew


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def process_with_crew(
    user_message: str,
    session_id: str,
    conversation_history: List[str],
    user_id: Optional[str] = None
) -> str:
    """
    Process user message using CrewAI agent.

    This is the main entry point that replaces the intent classifier.
    Tools are fully synchronous - no async hacks needed.
    """
    logger.info(
        "processing_with_crew",
        session_id=session_id,
        user_id=user_id,
        message=user_message[:50]
    )

    # Get or create crew (CACHED per session+user for speed)
    # Include user_id in cache key so crew is recreated when user logs in/out
    global _CREW_CACHE, _CREW_VERSION
    cache_key = f"{session_id}:u{user_id or 'anon'}:v{_CREW_VERSION}"

    if cache_key not in _CREW_CACHE:
        logger.info("creating_crew",
                   session_id=session_id,
                   user_id=user_id,
                   version=_CREW_VERSION,
                   authenticated=user_id is not None)
        _CREW_CACHE[cache_key] = create_food_ordering_crew(session_id, customer_id=user_id)
    else:
        logger.debug("reusing_cached_crew", session_id=session_id, user_id=user_id)

    crew = _CREW_CACHE[cache_key]

    # Build compact context (only last 3 messages)
    context_lines = conversation_history[-3:] if conversation_history else []
    context = "\n".join(context_lines) if context_lines else "No previous context"

    # Run the crew
    inputs = {
        "user_input": user_message,
        "context": context
    }

    try:
        # Rate limiting: wait for semaphore slot (max 20 concurrent)
        async with _CREW_SEMAPHORE:
            logger.debug(
                "crew_semaphore_acquired",
                session_id=session_id,
                available_slots=_CREW_SEMAPHORE._value
            )

            # Run CrewAI in a thread to not block the async event loop
            # Use custom executor with 50 workers instead of default (6 workers)
            loop = asyncio.get_running_loop()

            def run_crew_sync():
                result = crew.kickoff(inputs=inputs)
                raw_response = str(result)
                return clean_crew_response(raw_response)

            response = await loop.run_in_executor(_EXECUTOR, run_crew_sync)

        logger.info(
            "crew_processing_complete",
            session_id=session_id,
            response_length=len(response)
        )

        # Emit quick replies based on response content
        _emit_response_quick_replies(session_id, response)

        return response

    except Exception as e:
        logger.error(
            "crew_processing_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )
        return "I'm sorry, I encountered an error processing your request. Could you try again?"
