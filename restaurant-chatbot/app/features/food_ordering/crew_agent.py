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
_CREW_VERSION = 30  # v30: ALL PHASES COMPLETE - 55 total tools (20 base + 35 new)

# Concurrency configuration - custom ThreadPoolExecutor for handling concurrent users
import concurrent.futures
MAX_CONCURRENT_CREWS = 20  # Rate limit: max 20 concurrent crew executions
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(
    max_workers=50,  # Thread pool size: can handle up to 50 concurrent requests
    thread_name_prefix="crew_worker"
)
_CREW_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_CREWS)


def run_async(coro):
    """
    Run async coroutine from sync context (inside @tool functions).

    CrewAI's @tool decorator doesn't properly await async functions,
    so tools must be sync `def`. This helper bridges the gap by running
    async code from within sync tools.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run
        return asyncio.run(coro)

    # There's a running loop - run in thread to avoid blocking
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(asyncio.run, coro)
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
    return "I'm processing your request. Could you please try again?"


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


def _get_menu_from_preloader(query: str = "", use_meal_filter: bool = True) -> List[Dict]:
    """
    Get menu items from preloader cache (instant, no DB).

    Args:
        query: Search term
        use_meal_filter: If True, prioritize items for current meal period

    Returns:
        List of menu items, prioritized by current meal period
    """
    try:
        from app.core.preloader import get_menu_preloader, get_current_meal_period
        preloader = get_menu_preloader()

        if preloader.is_loaded:
            # Get current meal period for smart filtering
            meal_period = get_current_meal_period() if use_meal_filter else None
            return preloader.search(query, meal_period=meal_period)
    except Exception as e:
        logger.debug("preloader_not_available", error=str(e))
    return []


def _infer_category(item_name: str) -> str:
    """Infer category from item name for UI grouping."""
    name_lower = item_name.lower()

    if "pizza" in name_lower:
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

    # Get menu from preloader
    items = _get_menu_from_preloader(query)

    if not items:
        logger.warning("menu_preloader_empty", query=query)
        if query:
            return f"No items found matching '{query}'. Try browsing the full menu."
        return "Menu is loading. Please try again in a moment."

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
                if item_name.lower() in cart_item_names:
                    continue
                structured_items.append({
                    "name": item_name,
                    "price": item.get("price", 0),
                    "category": _infer_category(item_name),
                    "description": item.get("description", ""),
                    "item_id": str(item.get("id", "")),
                    "meal_types": item.get("meal_types", ["All Day"]),
                })

            if structured_items:
                emit_menu_data(session_id, structured_items, current_meal_period=current_meal)

            return f"[MENU CARD DISPLAYED - {len(structured_items)} items shown. Tell customer to browse the menu card!]"
        except Exception as e:
            logger.debug("menu_data_emit_failed", error=str(e))

    menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:15]]
    return f"Menu items: {', '.join(menu_items)}" + (f" (+{len(items)-15} more)" if len(items) > 15 else "")


def _add_to_cart_impl(item_name: str, quantity: int, session_id: str) -> str:
    """Sync implementation of add_to_cart for crew pool."""
    from app.core.agui_events import emit_tool_activity, emit_cart_update
    from app.core.redis import get_cart_sync, save_cart_sync
    from app.core.preloader import get_menu_preloader

    emit_tool_activity(session_id, "add_to_cart")

    # Find item
    preloader = get_menu_preloader()
    item = preloader.find_item(item_name) if preloader.is_loaded else None

    if not item:
        return f"Sorry, I couldn't find '{item_name}' on our menu. Try 'show menu' to see available items."

    # Get cart
    cart_data = get_cart_sync(session_id) or {"items": [], "total": 0}
    cart_items = cart_data.get("items", [])

    # Check if already in cart
    for cart_item in cart_items:
        if cart_item.get("name", "").lower() == item.get("name", "").lower():
            cart_item["quantity"] = cart_item.get("quantity", 1) + quantity
            break
    else:
        cart_items.append({
            "name": item.get("name"),
            "price": item.get("price"),
            "quantity": quantity,
            "item_id": str(item.get("id", "")),
        })

    # Calculate total
    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in cart_items)
    cart_data = {"items": cart_items, "total": total}

    # Save cart
    save_cart_sync(session_id, cart_data)

    # Emit cart update
    emit_cart_update(session_id, cart_items, total)

    return f"Added {quantity}x {item.get('name')} to cart. Total: Rs.{total}. Anything else?"


def _view_cart_impl(session_id: str) -> str:
    """Sync implementation of view_cart for crew pool."""
    from app.core.agui_events import emit_tool_activity, emit_cart_card
    from app.core.redis import get_cart_sync

    emit_tool_activity(session_id, "view_cart")

    cart_data = get_cart_sync(session_id)
    if not cart_data or not cart_data.get("items"):
        return "Your cart is empty. Would you like to see our menu?"

    items = cart_data.get("items", [])
    total = cart_data.get("total", 0)

    # Emit cart card
    emit_cart_card(session_id, items, total)

    cart_list = [f"{i.get('name')} x{i.get('quantity')} (Rs.{i.get('price') * i.get('quantity')})" for i in items]
    return f"[CART CARD DISPLAYED] Your cart: {', '.join(cart_list)}. Total: Rs.{total}. Ready to checkout?"


def _remove_from_cart_impl(item_name: str, session_id: str) -> str:
    """Sync implementation of remove_from_cart for crew pool."""
    from app.core.agui_events import emit_tool_activity, emit_cart_update
    from app.core.redis import get_cart_sync, save_cart_sync

    emit_tool_activity(session_id, "remove_from_cart")

    cart_data = get_cart_sync(session_id)
    if not cart_data or not cart_data.get("items"):
        return "Your cart is empty."

    items = cart_data.get("items", [])
    item_lower = item_name.lower()

    new_items = [i for i in items if i.get("name", "").lower() != item_lower]

    if len(new_items) == len(items):
        return f"'{item_name}' not found in your cart."

    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in new_items)
    cart_data = {"items": new_items, "total": total}
    save_cart_sync(session_id, cart_data)
    emit_cart_update(session_id, new_items, total)

    return f"Removed {item_name} from cart. Total: Rs.{total}."


def _checkout_impl(order_type: str, session_id: str) -> str:
    """Sync implementation of checkout for crew pool.

    Note: Guest checkout is allowed - no authentication required.
    Uses session_id as customer identifier for guest orders.
    """
    from app.core.agui_events import emit_tool_activity, emit_quick_replies, emit_order_data
    from app.core.redis import get_cart_sync, set_cart_sync
    import uuid
    from datetime import datetime

    emit_tool_activity(session_id, "checkout")

    cart_data = get_cart_sync(session_id)
    if not cart_data or not cart_data.get("items"):
        return "Your cart is empty. Add items before checkout."

    # Validate order_type
    order_type_lower = order_type.lower().strip() if order_type else ""
    is_dine_in = "dine" in order_type_lower or order_type_lower == "dine_in"
    is_take_away = "take" in order_type_lower or "away" in order_type_lower or order_type_lower == "take_away"

    if not order_type or (not is_dine_in and not is_take_away):
        emit_quick_replies(session_id, [
            {"label": "Dine In", "action": "dine in", "icon": "dineIn", "variant": "primary"},
            {"label": "Take Away", "action": "take away", "icon": "takeaway", "variant": "primary"},
        ])
        return "Would you like to dine in or take away?"

    order_type_clean = "take_away" if is_take_away else "dine_in"

    # Create order
    try:
        items = cart_data.get("items", [])
        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)

        # Generate order display ID
        order_display_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"

        # Persist to MongoDB (sync - works reliably)
        try:
            from pymongo import MongoClient
            import os

            mongo_url = os.getenv("MONGODB_CONNECTION_STRING", "mongodb://localhost:27017")
            mongo_db = os.getenv("MONGODB_DATABASE_NAME", "restaurant_ai_analytics")

            client = MongoClient(mongo_url, serverSelectionTimeoutMS=2000)
            db = client[mongo_db]

            order_items_data = []
            for item in items:
                order_items_data.append({
                    "name": item.get("name", "Item"),
                    "quantity": item.get("quantity", 1),
                    "price": item.get("price", 0),
                    "item_total": item.get("price", 0) * item.get("quantity", 1)
                })

            order_doc = {
                "order_id": order_display_id,
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
            logger.info("order_persisted_to_mongodb", session_id=session_id, order_id=order_display_id)

        except Exception as mongo_error:
            logger.warning("mongodb_order_persist_failed", error=str(mongo_error))

        # Clear cart after successful order (use empty cart)
        set_cart_sync(session_id, {"items": [], "total": 0})

        # Emit order data for UI
        emit_order_data(
            session_id=session_id,
            order_id=order_display_id,
            items=order_items_data if 'order_items_data' in dir() else items,
            total=total,
            status="confirmed",
            order_type=order_type_clean
        )

        order_type_display = "dine-in" if order_type_clean == "dine_in" else "take-away"
        return f"Order #{order_display_id} placed successfully for {order_type_display}! Total: Rs.{total}. Enjoy your meal!"

    except Exception as e:
        logger.error("checkout_failed", error=str(e), exc_info=True)
        return "Sorry, there was an issue placing your order. Please try again."


def _cancel_order_impl(session_id: str) -> str:
    """Sync implementation of cancel_order for crew pool."""
    from app.core.agui_events import emit_tool_activity
    emit_tool_activity(session_id, "cancel_order")
    return "Order cancellation requires an order ID. What order would you like to cancel?"


def _clear_cart_impl(session_id: str) -> str:
    """Sync implementation of clear_cart for crew pool."""
    from app.core.agui_events import emit_tool_activity, emit_cart_update
    from app.core.redis import clear_cart_sync

    emit_tool_activity(session_id, "clear_cart")
    clear_cart_sync(session_id)
    emit_cart_update(session_id, [], 0)
    return "Cart cleared. Would you like to see our menu?"


def _update_quantity_impl(item_name: str, quantity: int, session_id: str) -> str:
    """Sync implementation of update_quantity for crew pool."""
    from app.core.agui_events import emit_tool_activity, emit_cart_update
    from app.core.redis import get_cart_sync, save_cart_sync

    emit_tool_activity(session_id, "update_quantity")

    cart_data = get_cart_sync(session_id)
    if not cart_data or not cart_data.get("items"):
        return "Your cart is empty."

    items = cart_data.get("items", [])
    item_lower = item_name.lower()
    found = False

    for item in items:
        if item.get("name", "").lower() == item_lower:
            if quantity <= 0:
                items.remove(item)
            else:
                item["quantity"] = quantity
            found = True
            break

    if not found:
        return f"'{item_name}' not found in your cart."

    total = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)
    cart_data = {"items": items, "total": total}
    save_cart_sync(session_id, cart_data)
    emit_cart_update(session_id, items, total)

    return f"Updated {item_name} quantity to {quantity}. Total: Rs.{total}."


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


# ============================================================================
# QUICK REPLY AGENT - LLM-based intelligent quick action selection
# ============================================================================

# Available quick action sets that the agent can choose from
QUICK_ACTION_SETS = {
    "added_to_cart": [
        {"label": "View Cart", "action": "view cart", "icon": "cart", "variant": "primary"},
        {"label": "Checkout", "action": "checkout", "icon": "checkout", "variant": "success"},
        {"label": "Add More", "action": "show menu", "icon": "menu", "variant": "secondary"},
    ],
    "view_cart": [
        {"label": "Checkout", "action": "checkout", "icon": "checkout", "variant": "success"},
        {"label": "Add More", "action": "show menu", "icon": "menu", "variant": "primary"},
        {"label": "Clear Cart", "action": "clear cart", "icon": "cancel", "variant": "danger"},
    ],
    "order_type": [
        {"label": "Dine In", "action": "dine in", "icon": "dineIn", "variant": "primary"},
        {"label": "Take Away", "action": "take away", "icon": "takeaway", "variant": "primary"},
    ],
    "payment_method": [
        {"label": "Pay Online (UPI)", "action": "pay online", "icon": "upi", "variant": "success"},
        {"label": "Cash on Delivery", "action": "cash on delivery", "icon": "cash", "variant": "primary"},
    ],
    "quantity": [
        {"label": "1", "action": "1", "icon": "number", "variant": "primary"},
        {"label": "2", "action": "2", "icon": "number", "variant": "primary"},
        {"label": "3", "action": "3", "icon": "number", "variant": "primary"},
        {"label": "Other", "action": "__OTHER__", "icon": "edit", "variant": "secondary"},
    ],
    "continue_ordering": [
        {"label": "Show Menu", "action": "show menu", "icon": "menu", "variant": "primary"},
        {"label": "View Cart", "action": "view cart", "icon": "cart", "variant": "secondary"},
        {"label": "Checkout", "action": "checkout", "icon": "checkout", "variant": "success"},
    ],
    "yes_no": [
        {"label": "Yes", "action": "yes", "icon": "check", "variant": "success"},
        {"label": "No", "action": "no", "icon": "cancel", "variant": "secondary"},
    ],
    "order_confirmed": [
        {"label": "Track Order", "action": "track my order", "icon": "orders", "variant": "primary"},
        {"label": "Order More", "action": "show menu", "icon": "menu", "variant": "secondary"},
    ],
    "menu_displayed": [
        {"label": "View Cart", "action": "view cart", "icon": "cart", "variant": "secondary"},
        {"label": "What's Popular?", "action": "what's popular", "icon": "star", "variant": "primary"},
    ],
    "which_item": [
        # Dynamic - populated based on items mentioned in response
    ],
    "none": [],
}

QUICK_REPLY_AGENT_PROMPT = """You are a quick action selector for a restaurant chatbot. Given the assistant's response, select which quick action buttons to show the user.

Available action sets:
- added_to_cart: User just added item(s) to cart (response mentions "added to cart")
- view_cart: Showing cart contents (response shows what's in the cart)
- order_type: Asking dine-in or take-away (response asks about eating here or taking away)
- payment_method: Asking how to pay (response asks about payment method)
- quantity: Asking how many (response asks "how many" of something)
- continue_ordering: General "anything else?" or offering to continue (response asks if user wants more)
- yes_no: Simple yes/no question (response is a direct yes/no question)
- order_confirmed: Order was placed successfully (response confirms order with ID)
- menu_displayed: Menu was just shown (response says "menu is displayed" or "take a look at our menu" or "browse our menu")
- which_item: Asking which specific item from multiple options (response lists options like "BBQ Chicken Pizza, Margherita, or Pepperoni")
- none: No quick actions needed (greeting, informational response, etc.)

If "which_item" is selected, also extract the item options mentioned in the response.

Response to analyze:
"{response}"

Return JSON only:
{{"action_set": "<set_name>", "items": ["item1", "item2"] if which_item else null}}"""


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
                # Dynamic item selection buttons
                replies = []
                for item in items[:4]:  # Max 4 items
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
                return QUICK_ACTION_SETS[action_set]
            else:
                return []

        except json.JSONDecodeError as e:
            logger.warning("quick_reply_agent_json_error", error=str(e), content=content[:100])
            return []

    except Exception as e:
        logger.warning("quick_reply_agent_failed", error=str(e))
        # No fallback - if agent fails, just don't show quick replies
        return []


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
    def search_menu(query: str = "") -> str:
        """
        Search the restaurant menu for food items.

        Use this tool to show customers what's available to order.
        Call with empty string "" to show all menu items.
        Call with a search term to filter (e.g., "burger", "spicy", "vegetarian").

        Args:
            query: Search term to filter menu items. Use "" for all items.

        Returns:
            List of menu items with names and prices.
        """
        # Emit activity for frontend (async)
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "search_menu")

        # Try preloader first (instant - no DB query!)
        items = _get_menu_from_preloader(query)

        if not items:
            # Preloader should always have data, but log if empty
            logger.warning("menu_preloader_empty", query=query)
            # Return helpful message instead of DB fallback
            if query:
                return f"No items found matching '{query}'. Try browsing the full menu."
            return "Menu is loading. Please try again in a moment."

        logger.debug("menu_from_preloader", query=query, count=len(items))

        # Track displayed menu in entity graph (for "the 2nd one" resolution)
        try:
            from app.core.semantic_context import get_entity_graph
            graph = get_entity_graph(session_id)
            # Store item names in display order
            displayed_items = [item.get('name') for item in items[:15]]
            graph.set_displayed_menu(displayed_items)
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
                        "meal_types": item.get("meal_types", ["All Day"]),
                    })

                if structured_items:
                    emit_menu_data(session_id, structured_items, current_meal_period=current_meal)

                # Short response - MenuCard shows the details (DO NOT list items!)
                return f"[MENU CARD DISPLAYED - {len(structured_items)} items shown in visual menu. DO NOT list items - just tell customer to browse the menu card and let you know what they'd like!]"
            except Exception as e:
                logger.debug("menu_data_emit_failed", error=str(e))

        # Return item list for searches (no MenuCard shown)
        menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:15]]
        return f"Menu items: {', '.join(menu_items)}" + (f" (+{len(items)-15} more)" if len(items) > 15 else "")

    return search_menu


def create_add_to_cart_tool(session_id: str):
    """Factory to create add_to_cart tool with session context."""

    @tool("add_to_cart")
    def add_to_cart(item: str, quantity: int = 1) -> str:
        """
        Add a food item to the customer's cart.

        IMPORTANT: Only use this tool when the customer has specified BOTH the item AND quantity.
        - "I want 2 burgers" → Use tool with quantity=2
        - "add 3 cokes" → Use tool with quantity=3
        - "I want a burger" (no quantity) → DO NOT use tool, ask "How many would you like?" FIRST!
        - "add orange juice" (no quantity) → DO NOT use tool, ask "How many?" FIRST!

        The item name can be partial (fuzzy matched).

        Args:
            item: Name of the menu item to add (e.g., "Butter Chicken", "burger")
            quantity: Number of items to add - MUST be explicitly specified by customer!

        Returns:
            Confirmation message with item added.
        """
        # Emit activity for frontend (async - no thread overhead)
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "add_to_cart")

        from app.core.redis import get_cart_sync, set_cart_sync
        from app.core.preloader import get_menu_preloader

        try:
            item_name = item.strip()

            # Find the item (uses preloader - sync)
            preloader = get_menu_preloader()
            found_item = preloader.find_item(item_name) if preloader.is_loaded else None

            if not found_item:
                return f"Item '{item_name}' not found. Try searching the menu first."

            # Get current cart (sync Redis)
            cart_data = get_cart_sync(session_id) or {"items": [], "total": 0}
            items = cart_data.get('items', [])

            # Check if item already in cart
            existing_item = None
            for existing in items:
                if existing.get('item_id') == str(found_item.get('id', '')):
                    existing_item = existing
                    break

            if existing_item:
                existing_item['quantity'] += quantity
                final_quantity = existing_item['quantity']
            else:
                items.append({
                    'item_id': str(found_item.get('id', '')),
                    'name': found_item.get('name'),
                    'price': float(found_item.get('price', 0)),
                    'quantity': quantity,
                    'category': ''
                })
                final_quantity = quantity

            # Save cart (sync Redis)
            cart_data['items'] = items
            cart_data['updated_at'] = str(datetime.now())
            set_cart_sync(session_id, cart_data, ttl=3600)

            subtotal = sum(i['price'] * i['quantity'] for i in items)

            # Track last mentioned item (for pronoun resolution like "add more of it")
            try:
                from app.core.semantic_context import get_entity_graph
                graph = get_entity_graph(session_id)
                graph.update_last_mentioned(found_item['name'])
                logger.debug("entity_graph_item_tracked", session_id=session_id, item=found_item['name'])
            except Exception as e:
                logger.debug("entity_graph_update_failed", error=str(e))

            logger.info(
                "item_added_to_cart",
                session_id=session_id,
                item=found_item['name'],
                quantity=final_quantity,
                subtotal=subtotal
            )

            # Don't return cart total - force LLM to call view_cart for cart details
            return f"Added {quantity}x {found_item['name']} to cart."

        except Exception as e:
            logger.error("add_to_cart_error", error=str(e), session_id=session_id)
            return f"Error adding item: {str(e)}"

    return add_to_cart


def create_view_cart_tool(session_id: str):
    """Factory to create view_cart tool with session context."""

    @tool("view_cart")
    def view_cart(_nonce: str = "") -> str:
        """
        View the current contents of the customer's shopping cart.

        Use this to show what items have been added and the total price.

        Args:
            _nonce: Optional unique identifier (ignored, used for cache busting)

        Returns:
            List of cart items with quantities and total price.
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
    def remove_from_cart(item_name: str, quantity: int = 1) -> str:
        """
        Remove item(s) from the customer's cart.

        Use this when customer wants to remove something they added.
        Specify quantity to remove that many (default: 1).
        Use quantity=0 or "all" to remove all of that item.

        Args:
            item_name: Name of the item to remove from cart.
            quantity: How many to remove (default 1). Use 0 to remove all.

        Returns:
            Confirmation of what was removed and remaining cart total.
        """
        # Emit activity for frontend (sync)
        from app.core.agui_events import emit_tool_activity
        emit_tool_activity(session_id, "remove_from_cart")

        from app.core.redis import get_cart_sync, set_cart_sync

        try:
            item_name_clean = item_name.strip().lower()

            # Get cart (sync Redis)
            cart_data = get_cart_sync(session_id) or {"items": []}
            items = cart_data.get("items", [])

            if not items:
                return "Cart is already empty."

            # Find and update item
            updated_items = []
            removed_info = None
            for item in items:
                if item_name_clean in item.get("name", "").lower() and not removed_info:
                    current_qty = item.get("quantity", 1)

                    # quantity=0 means remove all
                    qty_to_remove = current_qty if quantity == 0 else min(quantity, current_qty)
                    new_qty = current_qty - qty_to_remove

                    removed_info = {
                        "name": item.get("name"),
                        "removed_qty": qty_to_remove,
                        "remaining_qty": new_qty
                    }

                    # Keep item if still has quantity
                    if new_qty > 0:
                        updated_items.append({**item, "quantity": new_qty})
                else:
                    updated_items.append(item)

            if not removed_info:
                return f"Item '{item_name}' not found in cart."

            # Save updated cart (sync Redis)
            cart_data['items'] = updated_items
            cart_data['updated_at'] = str(datetime.now())
            set_cart_sync(session_id, cart_data, ttl=3600)

            # Calculate new total
            new_total = sum(i['price'] * i['quantity'] for i in updated_items)

            logger.info(
                "item_removed_from_cart",
                session_id=session_id,
                item=removed_info['name'],
                removed_qty=removed_info['removed_qty'],
                remaining_qty=removed_info['remaining_qty']
            )

            if removed_info['remaining_qty'] > 0:
                return f"Removed {removed_info['removed_qty']}x {removed_info['name']} from cart. {removed_info['remaining_qty']} remaining. Cart total: Rs.{new_total:.0f}"
            else:
                return f"Removed {removed_info['name']} from cart. Cart total: Rs.{new_total:.0f}"

        except Exception as e:
            logger.error("remove_from_cart_error", error=str(e), session_id=session_id)
            return f"Remove error: {str(e)}"

    return remove_from_cart


def create_checkout_tool(session_id: str):
    """Factory to create checkout tool with session context."""

    @tool("checkout")
    def checkout(order_type: str = "") -> str:
        """
        Complete the order and place it.

        IMPORTANT: You MUST specify order_type explicitly. Do NOT call this with
        empty or default order_type. Ask the customer first if they want
        dine-in or take-away, then call with their choice.

        Args:
            order_type: REQUIRED - "dine_in" or "take_away". Must ask customer first!

        Returns:
            Order confirmation with order ID, total, and order type.
            If order_type not specified, returns error asking to specify.
        """
        # Use the sync implementation
        return _checkout_impl(order_type, session_id)

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

        # IMPORTANT: Validate order_type is explicitly specified
        order_type_lower = order_type.lower().strip() if order_type else ""
        is_dine_in = "dine" in order_type_lower or order_type_lower == "dine_in"
        is_take_away = "take" in order_type_lower or "away" in order_type_lower or order_type_lower == "take_away"

        if not order_type or (not is_dine_in and not is_take_away):
            # Emit quick replies for the user to choose (async)
            await emit_quick_replies_async(session_id, [
                {"label": "Dine In", "action": "dine in", "icon": "dineIn", "variant": "primary"},
                {"label": "Take Away", "action": "take away", "icon": "takeaway", "variant": "primary"},
            ])
            return "ORDER_TYPE_REQUIRED: Please ask the customer if they want to dine in or take away before completing checkout."

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
            return f"Order placed! ID: {order_display_id}. Items: {', '.join(order_items)}. Total: Rs.{total:.0f} ({order_type_display})"

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
    async def get_order_status(order_id: str = "") -> str:
        """
        Get the current status of an order.

        Use this when customer asks "where is my order" or "what's the status".
        Status can be: pending, confirmed, preparing, ready, completed, or cancelled.

        Args:
            order_id: Order ID to check (e.g., "ORD-ABC12345"). Leave empty for most recent.

        Returns:
            Current order status with details.
        """
        from app.core.redis import get_redis_client
        import json

        try:
            redis_client = get_redis_client()
            order_display_id = order_id.strip().upper() if order_id else None

            # If no order_id provided, get most recent from history (async Redis)
            if not order_display_id:
                history_key = f"order_history:{session_id}"
                recent_orders = await redis_client.lrange(history_key, 0, 0)
                if not recent_orders:
                    return "No recent orders found. Have you placed an order yet?"
                order_display_id = recent_orders[0].decode() if isinstance(recent_orders[0], bytes) else recent_orders[0]

            # Query PostgreSQL for order status (async with asyncpg)
            try:
                from app.core.db_pool import AsyncDBConnection

                async with AsyncDBConnection() as conn:
                    order_row = await conn.fetchrow("""
                        SELECT o.order_id, o.order_display_id, o.total_amount,
                               o.created_at, ost.order_status_code as status,
                               ost.order_status_name as status_name,
                               ott.order_type_name as order_type
                        FROM orders o
                        LEFT JOIN order_status_type ost ON o.order_status_type_id = ost.order_status_type_id
                        LEFT JOIN order_type_table ott ON o.order_type_id = ott.order_type_id
                        WHERE o.order_display_id = $1
                    """, order_display_id)

                    if order_row:
                        status = order_row['status_name'] or order_row['status']
                        order_type = order_row['order_type'] or 'Order'
                        total = float(order_row['total_amount'] or 0)

                        # Get order items
                        items = await conn.fetch("""
                            SELECT item_name, quantity, item_status
                            FROM order_item WHERE order_id = $1
                        """, order_row['order_id'])

                        items_str = ", ".join([f"{i['item_name']} x{i['quantity']}" for i in items])

                        # Status-specific messages
                        status_messages = {
                            'pending': "Your order is pending confirmation.",
                            'confirmed': "Your order has been confirmed and will be prepared shortly.",
                            'preparing': "Your order is being prepared in the kitchen!",
                            'ready': "Your order is ready for pickup/serving!",
                            'completed': "Your order has been completed. Enjoy!",
                            'cancelled': "This order was cancelled."
                        }
                        status_msg = status_messages.get(order_row['status'], f"Status: {status}")

                        return (
                            f"Order {order_display_id} ({order_type})\n"
                            f"Status: {status} - {status_msg}\n"
                            f"Items: {items_str}\n"
                            f"Total: Rs.{total:.0f}"
                        )

            except Exception as pg_error:
                logger.warning("postgresql_order_status_failed", error=str(pg_error))

            # Fallback to Redis (async)
            order_key = f"order:{session_id}:{order_display_id}"
            order_data = await redis_client.get(order_key)

            if order_data:
                order = json.loads(order_data)
                status = order.get("status", "unknown")
                items = order.get("items", [])
                items_str = ", ".join([f"{i['name']} x{i['quantity']}" for i in items])
                total = order.get("total", 0)

                return f"Order {order_display_id}: {status.title()}. Items: {items_str}. Total: Rs.{total:.0f}"

            return f"Order {order_display_id} not found."

        except Exception as e:
            logger.error("get_order_status_error", error=str(e), session_id=session_id)
            return f"Error checking order status: {str(e)}"

    return get_order_status


def create_get_order_history_tool(session_id: str):
    """Factory to create get_order_history tool with session context."""

    @tool("get_order_history")
    async def get_order_history(limit: int = 5) -> str:
        """
        Get the customer's recent order history.

        Use this when customer asks about past orders or wants to reorder.

        Args:
            limit: Maximum number of orders to return (default 5).

        Returns:
            List of recent orders with status and totals.
        """
        try:
            from app.core.db_pool import AsyncDBConnection

            async with AsyncDBConnection() as conn:
                orders = await conn.fetch("""
                    SELECT o.order_id, o.order_display_id, o.total_amount,
                           o.created_at, ost.order_status_code as status,
                           ott.order_type_name as order_type
                    FROM orders o
                    LEFT JOIN order_status_type ost ON o.order_status_type_id = ost.order_status_type_id
                    LEFT JOIN order_type_table ott ON o.order_type_id = ott.order_type_id
                    WHERE o.device_id = $1
                    ORDER BY o.created_at DESC
                    LIMIT $2
                """, session_id, limit)

                if not orders:
                    return "No order history found for this session."

                order_list = []
                for order in orders:
                    # Get items for each order
                    items = await conn.fetch("""
                        SELECT item_name, quantity FROM order_item WHERE order_id = $1 LIMIT 3
                    """, order['order_id'])
                    items_str = ", ".join([f"{i['item_name']}" for i in items])

                    created_at = order['created_at']
                    date_str = created_at.strftime('%b %d, %I:%M %p') if hasattr(created_at, 'strftime') else str(created_at)

                    order_list.append(
                        f"{order['order_display_id']}: {items_str} - Rs.{order['total_amount']:.0f} ({order['status']}) - {date_str}"
                    )

                return f"Your recent orders:\n" + "\n".join(order_list)

        except Exception as e:
            logger.error("get_order_history_error", error=str(e), session_id=session_id)
            return f"Error getting order history: {str(e)}"

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
    async def get_order_receipt(order_id: str = "") -> str:
        """
        Generate a detailed receipt for an order.

        Use this when customer asks for receipt, invoice, or bill.
        Returns a formatted receipt that can be downloaded.

        Args:
            order_id: Order ID to get receipt for. Leave empty for most recent.

        Returns:
            Formatted receipt with all order details.
        """
        from app.core.redis import get_redis_client
        from app.core.db_pool import AsyncDBConnection

        try:
            redis_client = get_redis_client()
            order_display_id = order_id.strip().upper() if order_id else None

            # If no order_id provided, get most recent (async Redis)
            if not order_display_id:
                history_key = f"order_history:{session_id}"
                recent_orders = await redis_client.lrange(history_key, 0, 0)
                if not recent_orders:
                    return "No recent orders found."
                order_display_id = recent_orders[0].decode() if isinstance(recent_orders[0], bytes) else recent_orders[0]

            # Get order from PostgreSQL (async with asyncpg)
            async with AsyncDBConnection() as conn:
                # Get order details
                order = await conn.fetchrow("""
                    SELECT o.order_id, o.order_display_id, o.total_amount,
                           o.created_at, ost.order_status_name as status,
                           ott.order_type_name as order_type,
                           rc.restaurant_name
                    FROM orders o
                    LEFT JOIN order_status_type ost ON o.order_status_type_id = ost.order_status_type_id
                    LEFT JOIN order_type_table ott ON o.order_type_id = ott.order_type_id
                    LEFT JOIN restaurant_config rc ON o.restaurant_id = rc.id
                    WHERE o.order_display_id = $1
                """, order_display_id)

                if not order:
                    return f"Order {order_display_id} not found."

                # Get order items
                items = await conn.fetch("""
                    SELECT item_name, quantity, unit_price, line_total,
                           cooking_instructions, spice_level
                    FROM order_item WHERE order_id = $1
                """, order['order_id'])

                # Get order totals
                totals = await conn.fetchrow("""
                    SELECT items_total, tax_total, discount_total, final_amount
                    FROM order_total WHERE order_id = $1
                """, order['order_id'])

            # Format receipt
            created_at = order['created_at']
            date_str = created_at.strftime('%B %d, %Y at %I:%M %p') if hasattr(created_at, 'strftime') else str(created_at)
            restaurant_name = order['restaurant_name'] or "Restaurant"

            receipt_lines = [
                "=" * 40,
                f"{restaurant_name}".center(40),
                "=" * 40,
                f"Order: {order_display_id}",
                f"Date: {date_str}",
                f"Type: {order['order_type'] or 'Dine In'}",
                f"Status: {order['status']}",
                "-" * 40,
                "ITEMS:",
            ]

            for item in items:
                qty = item['quantity']
                name = item['item_name']
                price = item['unit_price']
                total = item['line_total']
                receipt_lines.append(f"  {qty}x {name}")
                receipt_lines.append(f"     @ Rs.{price:.0f} = Rs.{total:.0f}")
                if item.get('cooking_instructions'):
                    receipt_lines.append(f"     Note: {item['cooking_instructions']}")

            receipt_lines.append("-" * 40)

            if totals:
                receipt_lines.append(f"Subtotal: Rs.{totals['items_total']:.0f}")
                if totals.get('tax_total'):
                    receipt_lines.append(f"Tax: Rs.{totals['tax_total']:.0f}")
                if totals.get('discount_total'):
                    receipt_lines.append(f"Discount: -Rs.{totals['discount_total']:.0f}")
                receipt_lines.append("-" * 40)
                receipt_lines.append(f"TOTAL: Rs.{totals['final_amount']:.0f}")
            else:
                receipt_lines.append(f"TOTAL: Rs.{order['total_amount']:.0f}")

            receipt_lines.extend([
                "=" * 40,
                "Thank you for your order!",
                "=" * 40,
            ])

            receipt_text = "\n".join(receipt_lines)

            logger.info(
                "receipt_generated",
                session_id=session_id,
                order_display_id=order_display_id
            )

            return receipt_text

        except Exception as e:
            logger.error("get_order_receipt_error", error=str(e), session_id=session_id)
            return f"Error generating receipt: {str(e)}"

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
        Update the quantity of an item already in the cart.

        Use this when customer wants to change quantity (e.g., "make it 3 burgers" or "change to 2").

        Args:
            item_name: Name of the item to update.
            new_quantity: New quantity to set (must be >= 1).

        Returns:
            Confirmation of updated quantity and new cart total.
        """
        # Emit activity for frontend (sync)
        from app.core.agui_events import emit_tool_activity, emit_cart_data
        emit_tool_activity(session_id, "update_quantity")

        from app.core.redis import get_cart_sync, set_cart_sync

        try:
            if new_quantity < 1:
                return "Quantity must be at least 1. Use remove_from_cart to remove items."

            item_name_clean = item_name.strip().lower()

            # Get cart (sync Redis)
            cart_data = get_cart_sync(session_id) or {"items": []}
            items = cart_data.get("items", [])

            if not items:
                return "Cart is empty. Nothing to update."

            # Find and update item
            updated = False
            for item in items:
                if item_name_clean in item.get("name", "").lower():
                    old_qty = item.get("quantity", 1)
                    item["quantity"] = new_quantity
                    updated = True

                    # Save cart (sync Redis)
                    cart_data['items'] = items
                    cart_data['updated_at'] = str(datetime.now())
                    set_cart_sync(session_id, cart_data, ttl=3600)

                    new_total = sum(i['price'] * i['quantity'] for i in items)

                    # Emit cart update
                    emit_cart_data(session_id, items, new_total)

                    logger.info(
                        "quantity_updated",
                        session_id=session_id,
                        item=item.get("name"),
                        old_qty=old_qty,
                        new_qty=new_quantity
                    )

                    return f"Updated {item.get('name')} to {new_quantity}. Cart total: Rs.{new_total:.0f}"

            if not updated:
                return f"Item '{item_name}' not found in cart."

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
            item_name_clean = item_name.strip().lower()

            # Get cart (sync Redis)
            cart_data = get_cart_sync(session_id) or {"items": []}
            items = cart_data.get("items", [])

            if not items:
                return "Cart is empty. Add items first before adding special instructions."

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
# PAYMENT TOOLS (Mock Payment Flow)
# ============================================================================

def create_initiate_payment_tool(session_id: str):
    """Factory to create initiate_payment tool with session context."""

    @tool("initiate_payment")
    async def initiate_payment(order_id: str = "") -> str:
        """
        Initiate payment for an order.

        Use this when customer is ready to pay. This creates a payment order
        and returns a payment form for card details entry.

        Args:
            order_id: Order ID to pay for (e.g., "ORD-ABC12345"). Leave empty for most recent.

        Returns:
            Payment initiation status with instructions.
        """
        from app.core.redis import get_redis_client
        from app.core.db_pool import AsyncDBConnection
        import json
        import uuid as uuid_module

        try:
            redis_client = get_redis_client()
            order_display_id = order_id.strip().upper() if order_id else None

            # If no order_id provided, get most recent unpaid order (async Redis)
            if not order_display_id:
                history_key = f"order_history:{session_id}"
                recent_orders = await redis_client.lrange(history_key, 0, 4)
                if not recent_orders:
                    return "No recent orders found. Please place an order first."

                # Find first unpaid order
                for order_key in recent_orders:
                    order_key_str = order_key.decode() if isinstance(order_key, bytes) else order_key
                    order_data_key = f"order:{session_id}:{order_key_str}"
                    order_data = await redis_client.get(order_data_key)
                    if order_data:
                        order = json.loads(order_data)
                        if order.get("status") == "confirmed" and order.get("payment_status") != "paid":
                            order_display_id = order_key_str
                            break

                if not order_display_id:
                    return "No unpaid orders found. All your orders have been paid."

            # Get order details from PostgreSQL (async with asyncpg)
            async with AsyncDBConnection() as conn:
                # Get order
                order_row = await conn.fetchrow("""
                    SELECT o.order_id, o.order_display_id, o.total_amount,
                           o.payment_status, o.payment_order_id
                    FROM orders o
                    WHERE o.order_display_id = $1
                """, order_display_id)

                if not order_row:
                    return f"Order {order_display_id} not found."

                if order_row.get('payment_status') == 'paid':
                    return f"Order {order_display_id} has already been paid."

                order_uuid = order_row['order_id']
                amount = float(order_row['total_amount'] or 0)

                # Check if payment order already exists
                if order_row.get('payment_order_id'):
                    existing = await conn.fetchrow("""
                        SELECT payment_order_id, pst.payment_status_code as status
                        FROM payment_order po
                        LEFT JOIN payment_status_type pst ON po.payment_status_type_id = pst.payment_status_type_id
                        WHERE payment_order_id = $1
                    """, order_row['payment_order_id'])
                    if existing and existing['status'] not in ('failed', 'cancelled'):
                        # Store payment info in Redis for form handling
                        payment_info = {
                            "payment_order_id": str(existing['payment_order_id']),
                            "order_id": str(order_uuid),
                            "order_display_id": order_display_id,
                            "amount": amount,
                            "status": "awaiting_card_details"
                        }
                        await redis_client.setex(
                            f"payment_pending:{session_id}",
                            1800,  # 30 min TTL
                            json.dumps(payment_info)
                        )
                        return (
                            f"Payment already initiated for order {order_display_id}.\n"
                            f"Amount: Rs.{amount:.0f}\n\n"
                            "Please enter your card details to complete the payment:\n"
                            "- Card Number (16 digits)\n"
                            "- Expiry (MM/YY)\n"
                            "- CVV (3-4 digits)\n"
                            "- Cardholder Name\n\n"
                            "(For testing, use any valid format - payment will be simulated)"
                        )

                # Get mock gateway ID
                gateway_row = await conn.fetchrow("""
                    SELECT payment_gateway_id FROM payment_gateway
                    WHERE gateway_code = 'mock_gateway' LIMIT 1
                """)
                gateway_id = gateway_row['payment_gateway_id'] if gateway_row else None

                # Get pending status ID
                status_row = await conn.fetchrow("""
                    SELECT payment_status_type_id FROM payment_status_type
                    WHERE payment_status_code = 'pending' LIMIT 1
                """)
                pending_status_id = status_row['payment_status_type_id'] if status_row else None

                # Create payment order
                payment_order_id = str(uuid_module.uuid4())
                gateway_order_id = f"pay_{uuid_module.uuid4().hex[:12]}"

                await conn.execute("""
                    INSERT INTO payment_order (
                        payment_order_id, order_id, payment_gateway_id,
                        gateway_order_id, amount, payment_status_type_id,
                        expires_at
                    ) VALUES (
                        $1::uuid, $2, $3, $4, $5, $6,
                        NOW() + INTERVAL '30 minutes'
                    )
                """, payment_order_id, order_uuid, gateway_id,
                    gateway_order_id, amount, pending_status_id)

                # Update order with payment_order_id
                await conn.execute("""
                    UPDATE orders SET
                        payment_order_id = $1::uuid,
                        payment_status = 'pending',
                        updated_at = NOW()
                    WHERE order_id = $2
                """, payment_order_id, order_uuid)

            # Store payment info in Redis for form handling (async)
            payment_info = {
                "payment_order_id": payment_order_id,
                "gateway_order_id": gateway_order_id,
                "order_id": str(order_uuid),
                "order_display_id": order_display_id,
                "amount": amount,
                "status": "awaiting_card_details"
            }
            await redis_client.setex(
                f"payment_pending:{session_id}",
                1800,  # 30 min TTL
                json.dumps(payment_info)
            )

            logger.info(
                "payment_initiated",
                session_id=session_id,
                order_display_id=order_display_id,
                payment_order_id=payment_order_id,
                amount=amount
            )

            return (
                f"Payment initiated for order {order_display_id}!\n"
                f"Amount: Rs.{amount:.0f}\n\n"
                "Please enter your card details to proceed:\n"
                "- Card Number (16 digits)\n"
                "- Expiry (MM/YY)\n"
                "- CVV (3-4 digits)\n"
                "- Cardholder Name\n\n"
                "You can type them in this format: '4111111111111111 12/25 123 John Doe'\n"
                "(For testing, use any valid format - payment will be simulated)"
            )

        except Exception as e:
            logger.error("initiate_payment_error", error=str(e), session_id=session_id)
            return f"Payment initiation failed: {str(e)}"

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

            # Validate OTP (mock - accepts 123456)
            otp_clean = otp.strip().replace(' ', '')
            if len(otp_clean) != 6 or not otp_clean.isdigit():
                return "Invalid OTP format. Please enter a 6-digit OTP."

            # Mock validation - 123456 always succeeds, others fail 50% of time
            if otp_clean == "123456":
                otp_valid = True
            else:
                otp_valid = random.random() > 0.5  # 50% success for random OTPs

            if not otp_valid:
                return "Invalid OTP. Please try again or request a new OTP.\n(Hint: Use 123456 for testing)"

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

            # Clear pending payment
            await redis_client.delete(f"payment_pending:{session_id}")

            logger.info(
                "payment_completed",
                session_id=session_id,
                order_display_id=payment_info['order_display_id'],
                amount=payment_info['amount'],
                transaction_id=payment_info['payment_transaction_id']
            )

            return (
                f"Payment successful!\n\n"
                f"Order: {payment_info['order_display_id']}\n"
                f"Amount Paid: Rs.{payment_info['amount']:.0f}\n"
                f"Card: {payment_info.get('card_network', 'Card')} ending in {payment_info.get('card_last4', '****')}\n\n"
                "Your order is confirmed and being prepared. Thank you!"
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
        max_tokens=256,  # Limit response length for speed
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
                base_tools=15,
                phase1_tools=len(phase1_tools),
                phase2_tools=len(phase2_tools),
                phase3_tools=len(phase3_tools),
                phase4_tools=len(phase4_tools),
                phase5_tools=len(phase5_tools),
                total_tools=15 + len(phase1_tools) + len(phase2_tools) + len(phase3_tools) + len(phase4_tools) + len(phase5_tools),
                customer_authenticated=customer_id is not None,
                session=session_id)

    # Collect all tools (20 base + 35 new = 55 total)
    base_tools = [
        search_tool, add_tool, view_tool, remove_tool, checkout_tool, cancel_tool,
        status_tool, history_tool, reorder_tool, receipt_tool,
        initiate_payment_tool, submit_card_tool, verify_otp_tool, payment_status_tool, cancel_payment_tool
    ]
    all_tools = base_tools + phase1_tools + phase2_tools + phase3_tools + phase4_tools + phase5_tools

    # Single efficient agent with CrewAI best practices
    agent = Agent(
        role="Kavya - Restaurant Assistant",
        goal="Help customers with food ordering, reservations, and all restaurant services",
        backstory="""You are Kavya, a friendly and knowledgeable restaurant assistant.

You help customers with:
- Menu browsing, ordering, and payment
- Dietary restrictions, allergens, and favorites
- Table reservations and bookings
- FAQs, feedback, and restaurant policies
- Advanced menu filtering by cuisine, tags, and preferences

Be warm, helpful, and efficient. Use tool outputs to provide accurate information.""",
        llm=llm,
        tools=all_tools,
        # Best practices from docs.crewai.com
        verbose=False,  # Reduce noise in production
        allow_delegation=False,
        respect_context_window=True,  # Handle long conversations gracefully
        cache=True,  # Cache tool results for repeated queries
        max_iter=10,  # Prevent infinite loops
        max_retry_limit=2,  # Error resilience
    )

    # Task with clear structure following LLM prompting best practices
    task = Task(
        description="""You are a friendly restaurant assistant.

## CONVERSATION HISTORY
{context}

## CURRENT MESSAGE
Customer: "{user_input}"

## BEFORE YOU RESPOND - CHECK THIS FIRST!

Look at the conversation history. Did you just offer the customer drinks/add-ons?
If yes AND customer says "yes"/"sure"/"ok"/"yeah":
→ YOU MUST ASK: "Which one would you like?" DO NOT add anything to cart yet!

Example of CORRECT behavior:
- You: "Would you like a drink or salad with that?"
- Customer: "yes"
- You: "Which one would you like - Coca Cola (Rs.50), Orange Juice (Rs.80), or a Caesar Salad (Rs.149)?"

Example of WRONG behavior (DO NOT DO THIS):
- You: "Would you like a drink or salad with that?"
- Customer: "yes"
- You: "I've added Coca Cola to your cart" ← WRONG! Customer didn't specify which item!

## OTHER RULES

1. When offering add-ons, always include specific items with prices
2. **IMPORTANT - ALWAYS ASK QUANTITY**: When customer mentions item(s) without quantity, ALWAYS ask "How many?" BEFORE adding to cart!
   - Customer: "add beef burger and chicken burger" → Ask: "How many Beef Burgers and how many Chicken Burgers?"
   - Customer: "I want pizza" → Ask: "How many pizzas would you like?"
   - Customer: "add 2 burgers" → OK to add directly (quantity specified)
3. Only ask "dine in or take away?" after customer has selected specific items

## YOUR AVAILABLE TOOLS (55 tools)

You have access to 55 tools to help customers. ALWAYS use the appropriate tool when customer asks a question or makes a request.

### Menu & Ordering
- search_menu("keyword") → search menu items (triggers visual menu card)
- add_to_cart(item="name", quantity=N) → add item to cart
- view_cart() → MUST call when user asks to see cart (triggers visual cart display!)
- update_quantity(item="name", quantity=N) → change quantity
- remove_from_cart("item") → remove item
- set_special_instructions(item="name", instructions="text") → add cooking notes
- clear_cart() → empty cart
- checkout() → place order
- cancel_order(order_id="") → cancel an order
- get_order_status(order_id="") → check order status
- get_order_history() → view past orders
- reorder_last_order() → repeat last order
- reorder_from_order_id(order_id="") → reorder specific order
- get_order_receipt(order_id="") → get receipt
- add_order_instructions(instruction_type="cooking/delivery", instruction_text="") → add special instructions
- customize_item_in_cart(item_name="", customization="") → customize cart item

### Advanced Menu Discovery
- search_by_cuisine(cuisine="Italian/Chinese/Indian") → filter menu by cuisine
- get_available_cuisines() → list all cuisines
- search_by_tag(tag="spicy/popular/new") → filter by tags
- get_popular_items() → show popular items
- get_combo_deals() → show combo packages
- get_meal_type_menu(meal_type="breakfast/lunch/dinner") → filter by meal time
- get_item_details(item_name="") → detailed item info

### Customer Profile & Safety
- get_customer_allergens() → view saved allergens
- add_customer_allergen(allergen="", severity="mild/moderate/severe") → save allergen
- remove_customer_allergen(allergen="") → remove allergen
- get_dietary_restrictions() → view dietary preferences
- add_dietary_restriction(restriction="vegan/vegetarian/gluten-free") → save dietary preference
- filter_menu_by_allergen(allergen="") → show allergen-safe items
- filter_menu_by_dietary_restriction(restriction="") → show diet-compatible items
- get_allergen_info_for_item(item_name="") → check item allergens
- get_favorite_items() → view saved favorites
- add_to_favorites(item_name="") → save to favorites
- remove_from_favorites(item_name="") → remove from favorites

### Table Reservations
- check_table_availability(date="YYYY-MM-DD", time="HH:MM", party_size=N) → check if tables available
- book_table(date="", time="", party_size=N, special_requests="", occasion="") → book table
- get_my_bookings() → view reservations
- cancel_booking(booking_id="") → cancel reservation
- modify_booking(booking_id="", new_date="", new_time="", new_party_size=N) → change reservation
- get_available_time_slots(date="YYYY-MM-DD", party_size=N) → show available times

### Help & Support
- search_faq(query="refund/delivery/payment") → search FAQs
- get_faq_by_category(category="delivery/payment/ordering") → FAQs by category
- get_popular_faqs() → show top FAQs
- get_help_categories() → list FAQ categories
- get_restaurant_policies(policy_type="refund/cancellation/privacy/all") → show policies
- get_operating_hours(date="") → show restaurant hours
- submit_feedback(feedback_type="complaint/suggestion/praise", feedback_text="", rating=N) → collect feedback
- rate_last_order(rating=N, review="") → rate order
- get_my_feedback_history() → view past feedback

### Payment
- initiate_payment(order_id="") → start payment
- submit_card_details(order_id="", card_number="", expiry="", cvv="") → submit card
- verify_payment_otp(order_id="", otp="") → verify OTP
- check_payment_status(order_id="") → check payment status
- cancel_payment(order_id="") → cancel payment

**CRITICAL RULES:**
1. When customer asks "what's on the menu?" / "show menu" / "what do you have?" → MUST call search_menu("")
2. When customer asks "show my cart" / "what's in my cart?" → MUST call view_cart()
3. When customer asks about policies/hours/FAQs → USE the appropriate tool, don't make up answers
4. When customer mentions allergens or dietary needs → USE the allergen/dietary tools
5. When customer wants to book a table → USE the booking tools
6. ALWAYS use tools to get accurate data - don't guess or make up information!

Be warm and helpful!""",
        expected_output="A friendly, natural language response confirming the action taken",
        agent=agent
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,  # Reduce noise in production
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
