"""
Crew Pool Service
=================
Pre-warmed pool of CrewAI instances for instant response times.

Architecture:
- Shared LLM singleton (reuse OpenAI connection)
- Pool of pre-created Crew instances
- Dynamic session binding at request time
- Crews returned to pool after use

This eliminates first-message latency by:
1. Pre-warming LLM connection at startup
2. Pre-creating N crew instances
3. Binding session_id dynamically (not at creation)
"""

import os
import asyncio
import threading
from contextvars import ContextVar
from typing import Dict, Any, Optional, List, Tuple
from queue import Queue, Empty
from dataclasses import dataclass
from contextlib import contextmanager
import structlog

logger = structlog.get_logger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

POOL_SIZE = 20  # Number of pre-warmed crews (matches MAX_CONCURRENT_CREWS)
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0.1
LLM_MAX_TOKENS = 512

# =============================================================================
# LLM FACTORY - Round-robin at CREW level (each crew gets different API key)
# =============================================================================

_LLM_LOCK = threading.Lock()


def get_llm_for_crew(crew_index: int):
    """
    Get LLM instance for a specific crew using round-robin API key assignment.

    - Crew 0 → Account 1
    - Crew 1 → Account 2
    - ...
    - Crew 17 → Account 18
    - Crew 18 → Account 1 (wraps around)

    Each session that gets this crew will use this API key for all its requests.
    """
    from langchain_openai import ChatOpenAI
    from app.ai_services.llm_manager import get_llm_manager

    llm_manager = get_llm_manager()
    num_accounts = llm_manager.get_account_count()

    # Round-robin: crew_index % num_accounts
    account_index = crew_index % num_accounts
    account = llm_manager.accounts[account_index]

    llm = ChatOpenAI(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        api_key=account.api_key,
        max_tokens=LLM_MAX_TOKENS,
    )

    logger.info(
        "llm_assigned_to_crew",
        crew_index=crew_index,
        account_number=account.account_number,
        total_accounts=num_accounts
    )

    return llm, account.account_number


def get_shared_llm():
    """Backward compatibility - returns LLM for crew 0."""
    llm, _ = get_llm_for_crew(0)
    return llm


async def prewarm_llm():
    """
    Pre-warm LLM connections with dummy calls to each account.
    Called at application startup.
    """
    logger.info("prewarming_llm_connections")

    try:
        from langchain_openai import ChatOpenAI
        from app.ai_services.llm_manager import get_llm_manager

        llm_manager = get_llm_manager()
        num_accounts = llm_manager.get_account_count()

        loop = asyncio.get_running_loop()

        # Warm up each account
        for account in llm_manager.accounts:
            llm = ChatOpenAI(
                model=LLM_MODEL,
                api_key=account.api_key,
                max_tokens=10,
            )
            await loop.run_in_executor(None, lambda l=llm: l.invoke("OK"))
            logger.info("llm_prewarm_complete", account_number=account.account_number)

        logger.info("all_llm_prewarm_complete", accounts_warmed=num_accounts)
        return True
    except Exception as e:
        logger.error("llm_prewarm_failed", error=str(e))
        return False


# =============================================================================
# DYNAMIC SESSION BINDING (Coroutine-safe using ContextVar)
# =============================================================================

@dataclass
class SessionContext:
    """Context that gets bound to tools at request time."""
    session_id: str
    user_id: Optional[str] = None


# ContextVar for coroutine-safe session context
# Unlike threading.local(), ContextVar is properly isolated per-coroutine
_session_context: ContextVar[Optional[SessionContext]] = ContextVar('session_context', default=None)


def set_session_context(session_id: str, user_id: Optional[str] = None):
    """Set session context for current coroutine/task."""
    _session_context.set(SessionContext(session_id=session_id, user_id=user_id))


def get_session_context() -> Optional[SessionContext]:
    """Get session context for current coroutine/task."""
    return _session_context.get()


def clear_session_context():
    """Clear session context for current coroutine/task."""
    _session_context.set(None)


def get_current_session_id() -> str:
    """Get current session_id from coroutine-local context."""
    ctx = get_session_context()
    if ctx is None:
        raise RuntimeError("No session context set. Call set_session_context() first.")
    return ctx.session_id


def get_current_user_id() -> Optional[str]:
    """Get current user_id from coroutine-local context."""
    ctx = get_session_context()
    if ctx is None:
        return None
    return ctx.user_id


# =============================================================================
# ASYNC ORDER CREATION
# =============================================================================

async def create_order_async(
    user_id: str,
    session_id: str,
    items: List[Dict[str, Any]],
    total: float,
    order_type: str = "dine_in"
) -> str:
    """
    Create order using async database connection.
    Returns the order number (invoice-style).

    Note: Uses the actual database schema with order_id, order_invoice_number, etc.
    Foreign keys (order_type_id, order_status_type_id) are left NULL since lookup
    tables may not be populated.
    """
    import uuid
    import random
    from datetime import datetime
    from app.core.database import get_db_session
    from sqlalchemy import text

    order_id = str(uuid.uuid4())
    # Generate a simple order number (bigint compatible)
    order_number = int(datetime.now().strftime('%Y%m%d%H%M%S')) + random.randint(1, 999)
    # Human-readable invoice number
    invoice_number = f"INV-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"

    logger.info("create_order_async_start", order_id=order_id, session_id=session_id, invoice_number=invoice_number)

    try:
        async with get_db_session() as session:
            logger.info("create_order_async_got_session", order_id=order_id)
            # Insert order using actual schema
            # Note: order_type_id, order_status_type_id left NULL (FK tables empty)
            await session.execute(
                text("""
                    INSERT INTO orders (
                        order_id, order_number, order_invoice_number,
                        order_external_reference_id, created_at
                    ) VALUES (
                        :order_id, :order_number, :invoice_number,
                        :session_id, NOW()
                    )
                """),
                {
                    "order_id": order_id,
                    "order_number": order_number,
                    "invoice_number": invoice_number,
                    "session_id": session_id,
                }
            )
            logger.info("create_order_async_executed", order_id=order_id)
            await session.commit()
            logger.info("create_order_async_committed", order_id=order_id)
    except Exception as e:
        logger.error("create_order_async_error", order_id=order_id, error=str(e), error_type=type(e).__name__, exc_info=True)
        raise

    logger.info("order_created_async", order_id=order_id, invoice_number=invoice_number, total=total)
    return invoice_number


# =============================================================================
# DYNAMIC TOOL FACTORIES
# =============================================================================

def create_dynamic_tools():
    """
    Create ASYNC tools that dynamically get session_id from ContextVar.
    These tools use native async for all I/O operations.
    Use with crew.akickoff() for proper async execution.
    """
    from crewai.tools import tool
    from app.core.redis import get_cart, save_cart, clear_cart as clear_cart_redis
    from app.core.agui_events import (
        emit_tool_activity_async, emit_menu_data_async,
        emit_cart_data_async
    )
    from app.core.preloader import get_menu_preloader, get_current_meal_period
    from app.core.semantic_context import get_entity_graph
    from app.features.food_ordering.crew_agent import (
        _get_menu_from_preloader, _infer_category
    )

    @tool("search_menu")
    async def search_menu(query: str = "") -> str:
        """Search menu items by name, category, or dietary preference. Use empty string for full menu."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "search_menu")

        items = _get_menu_from_preloader(query)
        if not items:
            if query:
                return f"No items found matching '{query}'. Try browsing the full menu."
            return "Menu is loading. Please try again."

        # Track displayed menu
        try:
            graph = get_entity_graph(session_id)
            graph.set_displayed_menu([item.get('name') for item in items[:15]])
        except Exception:
            pass

        # Emit menu card for full menu
        if not query:
            try:
                current_meal = get_current_meal_period()
                cart_data = await get_cart(session_id)
                cart_items = cart_data.get("items", []) if cart_data else []
                cart_item_names = {i.get("name", "").lower() for i in cart_items}

                structured_items = [
                    {
                        "name": item.get("name", ""),
                        "price": item.get("price", 0),
                        "category": _infer_category(item.get("name", "")),
                        "description": item.get("description", ""),
                        "item_id": str(item.get("id", "")),
                        "meal_types": item.get("meal_types", ["All Day"]),
                    }
                    for item in items
                    if item.get("name", "").lower() not in cart_item_names
                ]

                if structured_items:
                    await emit_menu_data_async(session_id, structured_items, current_meal_period=current_meal)

                return f"[MENU CARD DISPLAYED - {len(structured_items)} items. Tell customer to browse!]"
            except Exception:
                pass

        menu_items = [f"{item.get('name')} (Rs.{item.get('price')})" for item in items[:15]]
        return f"Menu: {', '.join(menu_items)}" + (f" (+{len(items)-15} more)" if len(items) > 15 else "")

    @tool("add_to_cart")
    async def add_to_cart(item_name: str, quantity: int = 1) -> str:
        """Add an item to the cart."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "add_to_cart")

        preloader = get_menu_preloader()
        item = preloader.find_item(item_name) if preloader.is_loaded else None

        if not item:
            return f"Sorry, couldn't find '{item_name}'. Try 'show menu' to see available items."

        cart_data = await get_cart(session_id) or {"items": [], "total": 0}
        cart_items = cart_data.get("items", [])

        # Update existing or add new
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

        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in cart_items)
        await save_cart(session_id, {"items": cart_items, "total": total})
        await emit_cart_data_async(session_id, cart_items, total)

        return f"Added {quantity}x {item.get('name')} to cart. Total: Rs.{total}. Anything else?"

    @tool("view_cart")
    async def view_cart(_nonce: str = "") -> str:
        """View current cart contents."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "view_cart")

        cart_data = await get_cart(session_id)
        if not cart_data or not cart_data.get("items"):
            return "Your cart is empty. Would you like to see our menu?"

        items = cart_data.get("items", [])
        total = cart_data.get("total", 0)
        await emit_cart_data_async(session_id, items, total)

        cart_list = [f"{i.get('name')} x{i.get('quantity')}" for i in items]
        return f"[CART DISPLAYED] {', '.join(cart_list)}. Total: Rs.{total}. Ready to checkout?"

    @tool("remove_from_cart")
    async def remove_from_cart(item_name: str) -> str:
        """Remove an item from the cart."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "remove_from_cart")

        cart_data = await get_cart(session_id)
        if not cart_data or not cart_data.get("items"):
            return "Your cart is empty."

        items = cart_data.get("items", [])
        new_items = [i for i in items if i.get("name", "").lower() != item_name.lower()]

        if len(new_items) == len(items):
            return f"'{item_name}' not found in cart."

        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in new_items)
        await save_cart(session_id, {"items": new_items, "total": total})
        await emit_cart_data_async(session_id, new_items, total)

        return f"Removed {item_name}. Total: Rs.{total}."

    @tool("checkout")
    async def checkout(order_type: str = "dine_in") -> str:
        """Checkout and place the order. order_type: 'dine_in' or 'take_away'"""
        session_id = get_current_session_id()
        user_id = get_current_user_id()
        logger.info("checkout_started", session_id=session_id, user_id=user_id, order_type=order_type)
        await emit_tool_activity_async(session_id, "checkout")

        cart_data = await get_cart(session_id)
        logger.info("checkout_cart_data", session_id=session_id, cart_data=cart_data)
        if not cart_data or not cart_data.get("items"):
            return "Your cart is empty. Add items before checkout."

        # Use session_id as fallback if no user_id (guest checkout)
        effective_user_id = user_id or session_id

        try:
            items = cart_data.get("items", [])
            # Calculate total from items if not in cart_data
            total = cart_data.get("total", 0)
            if total == 0 and items:
                total = sum(item.get("price", 0) * item.get("quantity", 1) for item in items)

            logger.info("checkout_creating_order", session_id=session_id, total=total, item_count=len(items))

            # Create order using async database
            order_id = await create_order_async(
                user_id=effective_user_id,
                session_id=session_id,
                items=items,
                total=total,
                order_type=order_type or "dine_in"
            )

            logger.info("checkout_order_created", session_id=session_id, order_id=order_id)
            await clear_cart_redis(session_id)
            return f"Order #{order_id} placed! Total: Rs.{total}. Enjoy your meal!"
        except Exception as e:
            logger.error("checkout_failed", session_id=session_id, error=str(e), error_type=type(e).__name__, exc_info=True)
            return "Sorry, there was an issue placing your order. Please try again."

    @tool("clear_cart")
    async def clear_cart(_nonce: str = "") -> str:
        """Clear all items from the cart."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "clear_cart")
        await clear_cart_redis(session_id)
        await emit_cart_data_async(session_id, [], 0)
        return "Cart cleared. Would you like to see our menu?"

    @tool("update_quantity")
    async def update_quantity(item_name: str, quantity: int) -> str:
        """Update quantity of an item in cart."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "update_quantity")

        cart_data = await get_cart(session_id)
        if not cart_data or not cart_data.get("items"):
            return "Your cart is empty."

        items = cart_data.get("items", [])
        found = False

        for item in items:
            if item.get("name", "").lower() == item_name.lower():
                if quantity <= 0:
                    items.remove(item)
                else:
                    item["quantity"] = quantity
                found = True
                break

        if not found:
            return f"'{item_name}' not found in cart."

        total = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)
        await save_cart(session_id, {"items": items, "total": total})
        await emit_cart_data_async(session_id, items, total)

        return f"Updated {item_name} to {quantity}. Total: Rs.{total}."

    @tool("get_item_details")
    async def get_item_details(item_name: str) -> str:
        """Get details of a menu item."""
        session_id = get_current_session_id()
        await emit_tool_activity_async(session_id, "get_item_details")

        preloader = get_menu_preloader()
        item = preloader.find_item(item_name) if preloader.is_loaded else None

        if not item:
            return f"Sorry, couldn't find '{item_name}'."

        return f"{item.get('name')}: Rs.{item.get('price')}. {item.get('description', 'A delicious choice!')}"

    return {
        'search_menu': search_menu,
        'add_to_cart': add_to_cart,
        'view_cart': view_cart,
        'remove_from_cart': remove_from_cart,
        'checkout': checkout,
        'clear_cart': clear_cart,
        'update_quantity': update_quantity,
        'get_item_details': get_item_details,
    }


def create_dynamic_booking_tools():
    """Create booking tools with dynamic session binding."""
    from crewai.tools import tool

    @tool
    def check_table_availability(date: str, time: str, party_size: int) -> str:
        """Check table availability for a reservation."""
        from app.features.booking.crew_agent import check_table_availability as _check
        return _check.run(date=date, time=time, party_size=party_size)

    return {
        'check_table_availability': check_table_availability,
    }


# =============================================================================
# CREW POOL
# =============================================================================

class CrewPool:
    """
    Pool of pre-warmed CrewAI instances.

    Usage:
        pool = CrewPool(size=20)
        await pool.initialize()

        # Get a crew for a session
        with pool.get_crew() as crew:
            set_session_context(session_id)
            result = crew.kickoff(inputs)
    """

    def __init__(self, size: int = POOL_SIZE):
        self.size = size
        self._pool: Queue = Queue(maxsize=size)
        self._initialized = False
        self._lock = threading.Lock()
        self._stats = {
            'created': 0,
            'checkouts': 0,
            'returns': 0,
            'active': 0,
        }

    async def initialize(self):
        """Initialize pool with pre-created crews."""
        if self._initialized:
            return

        with self._lock:
            if self._initialized:
                return

            logger.info("initializing_crew_pool", size=self.size)

            # Pre-warm LLM first
            await prewarm_llm()

            # Create crews in thread pool (CrewAI is sync)
            loop = asyncio.get_running_loop()

            for i in range(self.size):
                # Pass crew index for round-robin API key assignment
                crew = await loop.run_in_executor(None, lambda idx=i: self._create_pooled_crew(idx))
                self._pool.put(crew)
                self._stats['created'] += 1

                if (i + 1) % 5 == 0:
                    logger.info("crew_pool_progress", created=i + 1, total=self.size)

            self._initialized = True
            logger.info("crew_pool_initialized", size=self.size)

    def _create_pooled_crew(self, crew_index: int = 0):
        """Create a single pooled crew with dynamic tools and dedicated API key."""
        from crewai import Agent, Task, Crew, Process

        # Each crew gets its own LLM with different API key (round-robin)
        llm, account_num = get_llm_for_crew(crew_index)
        logger.info("creating_pooled_crew", crew_index=crew_index, account_number=account_num)

        # Create dynamic tools (session-id from ContextVar)
        food_tools = create_dynamic_tools()

        # Food Ordering Agent
        food_ordering_agent = Agent(
            role="Kavya - Food Ordering Specialist",
            goal="Help customers browse menu, manage their cart, and place orders",
            backstory="""You are Kavya, a warm food ordering specialist at the restaurant.
You understand what customers mean, not just what they say.""",
            llm=llm,
            tools=list(food_tools.values()),
            verbose=True,
            allow_delegation=False,
            respect_context_window=True,
            cache=False,
            max_iter=15,
            max_retry_limit=2,
        )

        # Task
        customer_task = Task(
            description="""Customer message: {user_input}
Context: {semantic_context}
History: {context}

Handle the customer's request appropriately.
- For food orders: search menu, add to cart, checkout
- Always confirm actions and ask "Anything else?"
- Ask for quantity if not specified
- Ask which specific item if multiple matches""",
            expected_output="Natural, helpful response",
            agent=food_ordering_agent,
        )

        crew = Crew(
            agents=[food_ordering_agent],
            tasks=[customer_task],
            process=Process.sequential,
            verbose=True,
        )

        return crew

    @contextmanager
    def get_crew(self):
        """
        Get a crew from pool (context manager).

        Usage:
            with pool.get_crew() as crew:
                result = crew.kickoff(inputs)
        """
        crew = None
        try:
            # Try to get from pool (non-blocking)
            try:
                crew = self._pool.get_nowait()
                self._stats['checkouts'] += 1
                self._stats['active'] += 1
            except Empty:
                # Pool exhausted - create a new one with round-robin API key
                logger.warning("crew_pool_exhausted", creating_new=True)
                crew = self._create_pooled_crew(self._stats['created'])
                self._stats['created'] += 1
                self._stats['active'] += 1

            yield crew

        finally:
            # Return crew to pool
            if crew is not None:
                self._stats['active'] -= 1
                self._stats['returns'] += 1

                try:
                    self._pool.put_nowait(crew)
                except:
                    # Pool full - discard
                    pass

            # Clear session context
            clear_session_context()

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        return {
            **self._stats,
            'pool_size': self._pool.qsize(),
            'max_size': self.size,
        }


# =============================================================================
# GLOBAL POOL INSTANCE
# =============================================================================

_crew_pool: Optional[CrewPool] = None


def get_crew_pool() -> CrewPool:
    """Get or create global crew pool."""
    global _crew_pool

    if _crew_pool is None:
        _crew_pool = CrewPool(size=POOL_SIZE)

    return _crew_pool


async def initialize_crew_pool():
    """Initialize global crew pool (call at app startup)."""
    pool = get_crew_pool()
    await pool.initialize()
    return pool


# =============================================================================
# PROCESSING FUNCTION WITH POOL
# =============================================================================

async def process_with_pooled_crew(
    user_message: str,
    session_id: str,
    conversation_history: List[str],
    user_id: Optional[str] = None,
) -> tuple[str, Dict[str, Any]]:
    """
    Process message using pooled crew with native async tools.

    Uses akickoff() for proper async tool execution - no thread pool overhead.
    This is a drop-in replacement for process_with_restaurant_crew.
    """
    from app.orchestration.restaurant_crew import clean_crew_response
    from app.core.semantic_context import get_entity_graph

    logger.info("processing_with_pooled_crew", session_id=session_id)

    pool = get_crew_pool()

    # Ensure pool is initialized
    if not pool._initialized:
        await pool.initialize()

    # Set session context for async tools (ContextVar propagates to async tasks)
    set_session_context(session_id, user_id)

    # Get entity context
    graph = get_entity_graph(session_id)
    semantic_context = graph.get_context_summary()

    # Build conversation context
    context_lines = conversation_history[-8:] if conversation_history else []
    context = "\n".join(context_lines) if context_lines else "No previous context"

    inputs = {
        "user_input": user_message,
        "semantic_context": semantic_context or "No tracked context yet",
        "context": context,
    }

    try:
        # Get crew from pool and use akickoff() for native async execution
        with pool.get_crew() as crew:
            result = await crew.akickoff(inputs=inputs)

            # Clean response
            if hasattr(result, 'raw') and result.raw:
                cleaned = clean_crew_response(str(result.raw))
                if cleaned:
                    response = cleaned
                else:
                    response = clean_crew_response(str(result)) or "I had trouble processing that. Could you try again?"
            else:
                response = clean_crew_response(str(result)) or "I had trouble processing that. Could you try again?"

        logger.info("pooled_crew_complete", session_id=session_id, pool_stats=pool.get_stats())

        return response, {
            "type": "success",
            "orchestrator": "crew_pool",
            "session_id": session_id,
            "pool_stats": pool.get_stats(),
        }

    except Exception as e:
        logger.error("pooled_crew_error", session_id=session_id, error=str(e))

        return (
            "I'm here to help! What would you like to do?",
            {"type": "error", "error": str(e)}
        )
