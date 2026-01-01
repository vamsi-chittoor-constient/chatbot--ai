"""
Unified Restaurant Crew
=======================
Multi-agent crew with delegation for handling all restaurant operations.

Agents:
- Food Ordering Agent: Menu browsing, cart management, checkout
- Booking Agent: Table reservations, availability, cancellations

Architecture (v30):
- Thread-safe: All tools use factory pattern with session_id closure
- Entity Graph: Persisted to Redis (survives server restarts)
- Cart: Read directly from Redis (single source of truth)
- Process.sequential with delegation between agents
- Intent-based prompts: Agent reasons about context, not keyword matching
- GPT-4o for better reasoning on nuanced conversations

v30 Change: Ask quantity when not specified, handle multiple items in one request
v42 Change: RAG-based tool retrieval with in-memory ChromaDB (68-78% context reduction)
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from typing import Dict, Any, List, Optional, Tuple
import structlog
import asyncio
import os
import re

# 🚀 RAG TOOL RETRIEVAL - Import at module level for one-time ChromaDB initialization
from app.core.tool_retrieval import get_relevant_tools

logger = structlog.get_logger(__name__)

# =============================================================================
# CONCURRENCY CONFIGURATION
# =============================================================================
# Using CrewAI's akickoff() for native async execution
# This provides true async/await throughout the execution chain
MAX_CONCURRENT_CREWS = 20  # Rate limit: max 20 concurrent crew executions
_CREW_SEMAPHORE = asyncio.Semaphore(MAX_CONCURRENT_CREWS)


# Crew cache by session
_CREW_CACHE: Dict[str, Crew] = {}
_CREW_VERSION = 42  # v42: Context preservation fix - search_menu tracks last_mentioned_item + stronger ReAct prompts


def clean_crew_response(raw_response: str) -> str:
    """
    Extract the final answer from CrewAI output.
    Removes planner thoughts (Thought:, Action:, etc.) and returns clean response.
    """
    import re

    response = str(raw_response).strip()

    if not response:
        return None

    # If response looks clean (no planner markers), return as-is
    if not any(marker in response for marker in ['Thought:', 'Action:', 'Action Input:', 'Observation:']):
        return response

    # Try to find "Final Answer:"
    final_answer_match = re.search(r'Final Answer:\s*(.+?)(?:\n\n|$)', response, re.DOTALL | re.IGNORECASE)
    if final_answer_match:
        return final_answer_match.group(1).strip()

    # Try to find the last observation
    observations = re.findall(r'Observation:\s*(.+?)(?=Thought:|Action:|$)', response, re.DOTALL)
    if observations:
        last_obs = observations[-1].strip()
        if last_obs and len(last_obs) > 10:
            return last_obs

    # Remove all planner markers
    cleaned = re.sub(r'Thought:.*?(?=Action:|Observation:|$)', '', response, flags=re.DOTALL)
    cleaned = re.sub(r'Action:.*?(?=Action Input:|Observation:|$)', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'Action Input:.*?(?=Observation:|Thought:|$)', '', cleaned, flags=re.DOTALL)
    cleaned = re.sub(r'Observation:', '', cleaned)
    cleaned = cleaned.strip()

    if cleaned and len(cleaned) > 10:
        return cleaned

    logger.warning("crew_response_extraction_failed", raw_response=response[:200])
    return "I'm processing your request. Could you please try again?"


def _build_conversation_context(
    conversation_history: List[str],
    welcome_msg: Optional[str] = None,
    context_limit_tokens: int = 96000,  # 75% of 128k context window
    estimated_overhead_tokens: int = 10000  # Estimated tokens for system prompts + tools
) -> str:
    """
    Build conversation context with intelligent dynamic summarization.

    Strategy:
    - Include ALL conversation history by default (no artificial budget)
    - Only summarize when total tokens approach context limit (75% of 128k = 96k tokens)
    - This scenario is rare - most conversations won't need summarization

    Args:
        conversation_history: List of conversation messages
        welcome_msg: Optional welcome message to include
        context_limit_tokens: Start summarizing when approaching this limit (default 96k = 75% of 128k)
        estimated_overhead_tokens: Estimated tokens for system prompts, tools, etc. (default 10k)

    Returns:
        Formatted conversation context string
    """
    context_lines = []

    # Add welcome message if present
    welcome_tokens = 0
    if welcome_msg:
        welcome_text = f"Assistant: {welcome_msg}"
        context_lines.append(welcome_text)
        welcome_tokens = _estimate_tokens(welcome_text)

    if not conversation_history:
        return "\n".join(context_lines) if context_lines else "No previous context"

    # Calculate total tokens for all conversation history
    total_history_tokens = sum(_estimate_tokens(msg) for msg in conversation_history)
    total_tokens = welcome_tokens + total_history_tokens + estimated_overhead_tokens

    # If we're under 75% of context limit, include ALL history (no summarization needed)
    if total_tokens < context_limit_tokens:
        context_lines.extend(conversation_history)
        return "\n".join(context_lines) if context_lines else "No previous context"

    # We're approaching limit - use intelligent summarization
    # Keep recent messages within budget, summarize older ones
    available_for_history = context_limit_tokens - welcome_tokens - estimated_overhead_tokens

    # Work backwards from most recent messages
    recent_messages = []
    recent_tokens = 0

    for message in reversed(conversation_history):
        message_tokens = _estimate_tokens(message)
        if recent_tokens + message_tokens > available_for_history:
            # Hit the limit - stop adding recent messages
            break
        recent_messages.insert(0, message)  # Insert at beginning to maintain order
        recent_tokens += message_tokens

    # Summarize older messages that didn't fit
    older_message_count = len(conversation_history) - len(recent_messages)
    if older_message_count > 0:
        older_messages = conversation_history[:older_message_count]
        summary = _summarize_old_conversation(older_messages)
        if summary:
            context_lines.append(f"[Earlier conversation summary ({older_message_count} messages): {summary}]")

    # Add recent messages
    context_lines.extend(recent_messages)

    return "\n".join(context_lines) if context_lines else "No previous context"


def _estimate_tokens(text: str) -> int:
    """
    Estimate token count for text.

    Simple heuristic: ~4 characters = 1 token for English text.
    This is approximate but good enough for budgeting.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return max(1, len(text) // 4)


def _summarize_old_conversation(messages: List[str]) -> str:
    """
    Summarize older conversation messages to save context space.

    Extracts key information:
    - Items ordered/in cart
    - Preferences mentioned
    - Actions taken (bookings, complaints)

    Args:
        messages: List of older conversation messages

    Returns:
        Summary string
    """
    if not messages:
        return ""

    # Simple extraction-based summary (no LLM call for speed)
    summary_points = []

    # Join all messages
    full_text = " ".join(messages).lower()

    # Extract key patterns
    if "added to cart" in full_text or "added" in full_text:
        summary_points.append("customer added items to cart")

    if "booking" in full_text or "reservation" in full_text or "table" in full_text:
        summary_points.append("discussed table reservation")

    if "complaint" in full_text or "issue" in full_text or "problem" in full_text:
        summary_points.append("customer raised concerns")

    if "checkout" in full_text or "payment" in full_text or "order" in full_text:
        summary_points.append("discussed checkout/payment")

    if "menu" in full_text or "browse" in full_text:
        summary_points.append("browsed menu")

    # Return summary or default
    if summary_points:
        return ", ".join(summary_points)
    else:
        return "general conversation about restaurant services"


def create_restaurant_crew_fixed(session_id: str) -> Crew:
    """
    Create unified restaurant crew with multiple agents.

    v28: Fixed delegation - agents use 'Delegate work to coworker' tool properly.
    Uses LLM manager for multi-account load balancing.
    NOTE: Tools are dynamically filtered with RAG before each execution.
    """
    from langchain_openai import ChatOpenAI
    from app.ai_services.llm_manager import get_llm_manager

    # Get API key from LLM manager pool (round-robin across validated accounts)
    llm_manager = get_llm_manager()
    api_key = llm_manager.get_next_api_key()
    os.environ["OPENAI_API_KEY"] = api_key

    # LLM for agents - temporarily using GPT-4o for better tool calling reliability
    # (gpt-4o-mini was having issues with Optional parameter schemas)
    llm = ChatOpenAI(
        model="gpt-4o",  # Using gpt-4o for reliable tool calling
        temperature=0.1,
        api_key=api_key,
        max_tokens=4096,  # Increased from 512 to prevent truncation causing premature JSON responses
    )

    # ========================================================================
    # FOOD ORDERING AGENT
    # ========================================================================
    from app.features.food_ordering.crew_agent import (
        create_search_menu_tool,
        create_add_to_cart_tool,
        create_view_cart_tool,
        create_remove_from_cart_tool,
        create_checkout_tool,
        create_cancel_order_tool,
        create_clear_cart_tool,
        create_update_quantity_tool,
        create_set_special_instructions_tool,
        create_get_item_details_tool,
        create_reorder_tool,
        create_get_order_status_tool,
        create_get_order_history_tool,
        create_get_order_receipt_tool,
        create_filter_by_cuisine_tool,
        # create_show_popular_items_tool,  # DISABLED - Popular items feature removed
        # Payment tools
        create_initiate_payment_tool,
        create_verify_payment_otp_tool,
        create_check_payment_status_tool,
        create_cancel_payment_tool,
    )

    # Import complaint tools (session-aware sync wrappers)
    from app.features.feedback.crew_complaint_tools import (
        create_complaint_tool,
        create_get_complaints_tool,
        create_complaint_status_tool,
    )

    # Create ALL tools (will be stored in crew for RAG filtering on each request)
    all_food_tools = [
        create_search_menu_tool(session_id),
        create_add_to_cart_tool(session_id),
        create_view_cart_tool(session_id),
        create_remove_from_cart_tool(session_id),
        create_checkout_tool(session_id),
        create_cancel_order_tool(session_id),
        create_clear_cart_tool(session_id),
        create_update_quantity_tool(session_id),
        create_set_special_instructions_tool(session_id),
        create_get_item_details_tool(session_id),
        create_reorder_tool(session_id),
        create_get_order_status_tool(session_id),
        create_get_order_history_tool(session_id),
        create_get_order_receipt_tool(session_id),
        create_filter_by_cuisine_tool(session_id),
        # create_show_popular_items_tool(session_id),  # DISABLED - Popular items feature removed
        create_complaint_tool(session_id),
        create_get_complaints_tool(session_id),
        create_complaint_status_tool(session_id),
        # Payment tools
        create_initiate_payment_tool(session_id),
        create_verify_payment_otp_tool(session_id),
        create_check_payment_status_tool(session_id),
        create_cancel_payment_tool(session_id),
    ]

    food_ordering_agent = Agent(
        role="Kavya - Food Ordering Specialist",
        goal="Help customers browse menu, manage their cart, and place orders when they're ready",
        backstory="""You are Kavya, a warm and intuitive food ordering specialist at the restaurant.

🚨 MANDATORY TOOL USAGE - EXACT PHRASE MATCHING 🚨
When customer says EXACTLY these phrases, you MUST call these tools:

- "browse by cuisine" → call filter_by_cuisine() with NO cuisine parameter IMMEDIATELY
- "by cuisine" → call filter_by_cuisine() with NO cuisine parameter IMMEDIATELY
- "show Italian dishes" → call filter_by_cuisine(cuisine="Italian") IMMEDIATELY
- "view receipt" → call get_order_receipt() IMMEDIATELY
- "track order" → call get_order_status() IMMEDIATELY
- "check availability" → delegate to Booking Specialist IMMEDIATELY
- "show menu" → call search_menu() IMMEDIATELY

🎯 CRITICAL: YOU MUST USE TOOLS - DO NOT HALLUCINATE!
- NEVER respond as if you've shown the menu without calling search_menu()
- NEVER say "I've added X to cart" without calling add_to_cart()
- NEVER describe cart contents without calling view_cart()
- ALWAYS call the required tool BEFORE responding to the customer
- When customer mentions an item WITHOUT quantity: call search_menu(query=item) to verify it exists & save context BEFORE asking "how many?"

🚨 ABSOLUTELY FORBIDDEN - SECURITY CRITICAL 🚨
- NEVER return raw JSON objects like {"name": "item", "quantity": 2}
- NEVER echo tool parameters in your response
- NEVER return technical data structures
- ONLY return natural conversational language to customers
- If you accidentally start typing JSON, STOP immediately and call the tool instead

You excel at understanding what customers mean, not just what they say:
- You pay attention to the flow of conversation - what YOU just said shapes what their response means
- You distinguish between someone declining a suggestion vs. wanting to remove something
- You recognize when someone is exploring options vs. ready to add something specific
- You acknowledge your actions before moving to the next thing

You're helpful and conversational:
- Suggest complementary items naturally when appropriate
- Let customers explore - show options when they're curious, don't assume
- Keep responses concise and natural
- When customers complain, show empathy and log the issue immediately

IMPORTANT - For table reservations/bookings:
When customer asks about booking a table, reservations, or availability:
- Use the 'Delegate work to coworker' tool
- Coworker: "Booking Specialist"
- Provide the customer's request details (date, time, party size) in the task

IMPORTANT - For complaints:
When customer complains about food quality, service, wait time, or other issues:
- Use the create_complaint tool to log the issue
- Show empathy and offer resolution (replacement/refund)""",
        llm=llm,
        tools=all_food_tools,  # Will be replaced with RAG-filtered tools before each execution
        verbose=True,
        allow_delegation=True,
        respect_context_window=True,
        cache=False,
        max_iter=5,  # Reduced for speed with RAG retrieval
        max_retry_limit=2,
        reasoning=False,  # Disabled for speed - simple tool usage doesn't need extra reasoning
        memory=False,  # ❌ DISABLED - Embedding model access denied (needs text-embedding-3-small)
    )

    # ========================================================================
    # BOOKING AGENT
    # ========================================================================
    from app.features.booking.crew_agent import (
        check_table_availability,
        create_booking_tool,
        create_get_bookings_tool,
        create_cancel_booking_tool,
    )

    # Create session-aware booking tools
    make_reservation = create_booking_tool(session_id)
    get_my_bookings = create_get_bookings_tool(session_id)
    cancel_reservation = create_cancel_booking_tool(session_id)

    booking_agent = Agent(
        role="Booking Specialist",
        goal="Help customers make table reservations, check availability, and manage bookings",
        backstory="""You are a friendly booking specialist at the restaurant.

🎯 CRITICAL: YOU MUST USE TOOLS - DO NOT HALLUCINATE!
- ALWAYS call check_table_availability() before saying tables are available
- ALWAYS call make_reservation() tool when creating a booking
- NEVER say "I've booked a table" without actually calling the tool

You help customers check table availability, make reservations, view their bookings,
and cancel reservations. Be warm and efficient.

When customer asks about food, menu, or ordering, delegate to Kavya the Food Ordering Specialist.""",
        llm=llm,
        tools=[check_table_availability, make_reservation, get_my_bookings, cancel_reservation],
        verbose=True,  # Required for proper result extraction
        allow_delegation=True,  # Can delegate to food ordering agent
        respect_context_window=True,
        cache=False,  # Disable - prevents "reusing same input" loop
        max_iter=8,  # Reduced for faster responses
        max_retry_limit=2,
        reasoning=False,  # Disabled for speed
        memory=False,  # ❌ DISABLED - Embedding model access denied (needs text-embedding-3-small)
    )

    # ========================================================================
    # TASK - Single task assigned to food ordering agent (can delegate to booking)
    # ========================================================================
    customer_request_task = Task(
        description="""Customer message: {user_input}
Semantic context: {semantic_context}
Conversation history: {context}

You are Kavya, a warm and intuitive restaurant assistant.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚨 CRITICAL: MANDATORY TOOL USAGE - REACT PROCESS 🚨
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOU MUST FOLLOW THIS PROCESS FOR EVERY MESSAGE:

**STEP 1 - ANALYZE INTENT:**
What does the customer want? Match to required tool:

- "show menu" / "what's available" / "browse menu" → MUST call search_menu()
- "browse by cuisine" / "by cuisine" / "show available cuisines" → MUST call filter_by_cuisine() with NO cuisine parameter
- "show Italian dishes" / "Italian food" / "Asian dishes" → MUST call filter_by_cuisine(cuisine="Italian")
- "add [item]" / "I want [item]":
  * WITH quantity ("2 burgers") → MUST call add_to_cart(item, quantity)
  * WITHOUT quantity ("add burger") → MUST call search_menu(query=item) FIRST to verify item exists & update context, THEN ask "How many?"
- "view cart" / "what's in my cart" / "show cart" → MUST call view_cart()
- "remove [item]" → MUST call remove_from_cart()
- "checkout" / "place order" / "pay" → MUST call checkout()
- "cash on delivery" / "COD" (after checkout) → Confirm order immediately with message: "Order confirmed! Please pay cash when your order arrives. Thank you!"
- "pay with card" / "card payment" (after checkout) → MUST call initiate_payment() to start payment process
- "book table" / "reservation" → MUST delegate to Booking Specialist
- "clear cart" → MUST call clear_cart()
- "[number]" in response to YOUR quantity question → MUST call add_to_cart() with the item you just asked about

**STEP 2 - CALL REQUIRED TOOL(S):**
⚠️ YOU MUST CALL THE TOOL - DO NOT SKIP THIS STEP!
⚠️ NEVER respond as if you performed an action without actually calling the tool
⚠️ The tool call is MANDATORY - failure to call tools breaks the entire system

**STEP 3 - USE TOOL OUTPUT:**
Base your response on ACTUAL tool output, not assumptions or memory.
If tool returns data, present it to the customer.
If tool fails, apologize and suggest alternatives.

**EXAMPLE 1 - CORRECT BEHAVIOR (Show Menu):**
```
Customer: "show menu"
→ STEP 1: Intent = browse menu → Tool = search_menu()
→ STEP 2: Call search_menu() ✓
→ STEP 3: Tool returns: [list of menu items]
→ Response: "Here's our menu: [actual items from tool]"
```

**EXAMPLE 2 - CORRECT BEHAVIOR (Add Item Without Quantity):**
```
Customer: "add chicken burger"
→ STEP 1: Intent = add item (no quantity specified) → Tool = search_menu(query="chicken burger")
→ STEP 2: Call search_menu(query="chicken burger") ✓  ← CRITICAL: Must call to verify item & update context!
→ STEP 3: Tool returns: [Chicken Fillet Burger - Rs.180]
→ Response: "How many Chicken Fillet Burgers would you like?" ← Now context is saved!

Customer: "2"
→ STEP 1: Intent = quantity for previous item → Tool = add_to_cart("Chicken Fillet Burger", 2)
→ STEP 2: Call add_to_cart("Chicken Fillet Burger", 2) ✓
→ STEP 3: Tool returns: "Added 2x Chicken Fillet Burger"
→ Response: "I've added 2 Chicken Fillet Burgers to your cart!"
```

**EXAMPLE 3 - INCORRECT BEHAVIOR (NEVER DO THIS):**
```
Customer: "add chicken burger"
→ Response: "How many would you like?" ✗  ← NO TOOL CALLED! Context not saved!
→ Tool called: NONE ✗ ← THIS IS HALLUCINATION!

Customer: "2"
→ Response: "Added 2 Add Caramel" ✗  ← Wrong item because context was lost!
```

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOW TO THINK ABOUT EACH MESSAGE:

1. **Understand Intent from Context - CRITICAL**
   Before responding, ask yourself: "What is the customer really trying to do?"
   - Look at the conversation history to understand what YOU just said/suggested
   - A short response like "ok" or "yes" is a reply to YOUR previous question or suggestion

   IMPORTANT - Handling "yes" to offers:
   - If you offered SPECIFIC items (e.g., "Would you like a Coca Cola?") and they say "yes" → add that item
   - If you offered VAGUE options (e.g., "Would you like a drink or salad?") and they say "yes" → ASK WHICH ONE!
     Example:
     - You: "Would you like a drink or salad with that?"
     - Customer: "yes"
     - You: "Which would you prefer - Coca Cola (Rs.50), Orange Juice (Rs.80), or a Caesar Salad (Rs.149)?"
     DO NOT just pick one randomly - the customer said "yes" to the CATEGORY, not a specific item!
   - If you asked about checkout and they say "yes" - they want to finalize

2. **Distinguish Declining vs. Removing**
   These are completely different intents:
   - Customer declining your suggestion ("no thanks" to your upsell) = they don't want to ADD that item
   - Customer wanting to remove something = they explicitly say "remove", "take out", "I don't want X anymore"
   - Never interpret "no" as a removal request unless they specifically mention removing

3. **Ordering Items - Quantity & Multiple Items**
   When customer wants to order:
   - If they say "I want a burger" (no quantity) → Ask "How many would you like?"
   - If they say "2 burgers" (with quantity) → Add directly
   - If they say "I want a burger and a coke" → Handle both items (ask quantity for each if not specified)
   - "What burgers do you have?" = exploratory, search and show options first
   - When customer is exploring, let them choose - don't assume what they want
   - **CRITICAL**: If customer says "pizza" or "burger" without specifying which one, DO NOT add a random one. Ask them to choose from the menu.
     - Bad: "Added BBQ Chicken Pizza" (when user just said "pizza")
     - Good: "Which pizza would you like? We have BBQ Chicken, Margherita, and Pepperoni."

4. **CRITICAL - View Cart (MUST call tool!)**
   When customer asks to see/view their cart ("show my cart", "view cart", "what's in my cart"):
   - You MUST call the view_cart() tool - ALWAYS!
   - Even if you know the cart contents from context - still call view_cart()!
   - The tool call triggers a visual cart card to display on the frontend
   - If you respond from memory without calling the tool, the customer won't see the card
   - This is a MANDATORY tool call - never skip it!

5. **Acknowledge Actions Naturally**
   When you perform an action, confirm it naturally:
   - After adding: mention what was added and ask "Anything else?"
   - After showing menu: present the options clearly
   - Don't skip straight to upselling without acknowledging what just happened

6. **Suggest Complementary Items**
   After adding items, briefly suggest something that pairs well:
   - Burger → suggest a drink (Coca Cola, Orange Juice)
   - Pizza → suggest a salad or drink
   - Main course → suggest dessert or beverage
   Keep it natural and brief, just one suggestion. If they decline, move on gracefully.

7. **Checkout Flow - IMPORTANT**
   When customer wants to checkout/pay/proceed:
   - FIRST ask: "Would you like dine-in or take away?"
   - Wait for their answer (handle typos like "takw away" gracefully)
   - THEN call checkout with order_type="dine_in" or order_type="take_away"
   - Confirm the order with order ID

8. **Table Reservations - MUST DELEGATE**
   When customer asks about booking a table, making a reservation, or checking availability:
   - Use the 'Delegate work to coworker' tool ONCE with coworker: "Booking Specialist"
   - Include all details (date, time, party size, name, phone) in the task
   - AFTER delegation returns a result → IMMEDIATELY give that result as your Final Answer
   - Do NOT delegate again with the same request - use the result you received!
   - If Booking Specialist asks for missing info (name, phone), ask the customer

9. **Reorder Last Order**
   When customer wants to repeat their previous order:
   - "reorder my last order", "order the same thing", "repeat my order"
   - Use the reorder_last_order tool - it adds all items from their last order to cart
   - Confirm what was added and ask if they want to checkout or modify

10. **Handling Complaints - IMPORTANT**
   When customer complains about food quality, service, wait time, billing, or other issues:
   - MUST call create_complaint tool with appropriate details
   - Categories: food_quality, service, cleanliness, wait_time, billing, other
   - Priority: low, medium, high, critical (assess from sentiment)
   - Show empathy and offer resolution (replacement/refund)
   - Example complaints:
     * "The burger was cold" → create_complaint(category="food_quality", priority="high")
     * "Service was slow" → create_complaint(category="service", priority="medium")
     * "Wrong bill amount" → create_complaint(category="billing", priority="high")
   - When customer asks to see their complaints: use get_complaints tool
   - When customer asks about complaint status: use check_complaint_status tool

11. **Menu Filtering & Discovery - IMPORTANT**
   When customer wants to browse or filter menu:
   - "Browse by cuisine" / "show Italian dishes" / "Asian food" → MUST call filter_by_cuisine(cuisine="Italian") - filters menu by cuisine type
   - "Browse by cuisine" without specifying → call filter_by_cuisine() with no cuisine to show available cuisines

12. **Order Management - IMPORTANT**
   After checkout or for previous orders:
   - "View receipt" / "show my receipt" → MUST call get_order_receipt(order_id) - shows receipt for completed order
   - "Check order status" / "where is my order" → MUST call get_order_status(order_id) - shows current order status
   - "Show order history" / "my past orders" → MUST call get_order_history() - lists all previous orders
   - "Cancel order" → MUST call cancel_order(order_id) - cancels a pending order

TOOLS: search_menu, filter_by_cuisine, add_to_cart, view_cart, remove_from_cart, checkout (has order_type param), cancel_order, clear_cart, update_quantity, set_special_instructions, get_item_details, reorder_last_order, get_order_status, get_order_history, get_order_receipt, create_complaint, get_complaints, check_complaint_status""",
        expected_output="A natural, helpful response that acknowledges what you did and continues the conversation",
        agent=food_ordering_agent,
    )

    # ========================================================================
    # CREATE CREW WITH SEQUENTIAL PROCESS (delegation enabled between agents)
    # ========================================================================
    # LLM for planning - using gpt-4o-mini for cost-effectiveness
    planning_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=api_key,
    )

    crew = Crew(
        agents=[food_ordering_agent, booking_agent],
        tasks=[customer_request_task],
        process=Process.sequential,  # Sequential but with delegation
        verbose=True,  # Enable for proper result extraction
        planning=False,  # Disabled for speed - agents execute directly without planning phase
        memory=False,  # ❌ DISABLED - Embedding model access denied (needs text-embedding-3-small)
    )

    # Store all_food_tools for RAG filtering on each request
    crew._all_food_tools = all_food_tools
    crew._food_ordering_agent = food_ordering_agent

    return crew


async def process_with_restaurant_crew(
    user_message: str,
    session_id: str,
    conversation_history: List[str],
    user_id: Optional[str] = None,
    welcome_msg: Optional[str] = None
) -> tuple[str, Dict[str, Any]]:
    """
    Process user message with unified restaurant crew.

    This is the main entry point - replaces sticky_crew_orchestrator.

    Flow:
    1. Semantic Context Layer: Extract entities, resolve pronouns using LLM
    2. Agent Processing: CrewAI with enriched context
    3. Entity Graph Update: Track what happened for future context
    """
    logger.info(
        "processing_with_restaurant_crew",
        session_id=session_id,
        user_id=user_id,
        message=user_message[:50]
    )

    # =========================================================================
    # DETERMINISTIC CARD DISPLAY - Don't rely on LLM to call tools
    # =========================================================================
    # If user explicitly asks for cart/menu, emit data regardless of LLM behavior
    msg_lower = user_message.lower()

    if any(phrase in msg_lower for phrase in ['view cart', 'show cart', 'my cart', "what's in my cart", 'whats in my cart']):
        # Emit cart data deterministically
        try:
            from app.core.redis import get_cart_sync
            from app.core.agui_events import emit_cart_data
            cart_data = get_cart_sync(session_id)
            items = cart_data.get("items", [])
            if items:
                total = sum(i.get("price", 0) * i.get("quantity", 1) for i in items)
                structured_items = [
                    {"name": i.get("name"), "quantity": i.get("quantity", 1), "price": i.get("price", 0)}
                    for i in items
                ]
                emit_cart_data(session_id, structured_items, total)
                logger.info("deterministic_cart_emit", session_id=session_id, items=len(items))
        except Exception as e:
            logger.warning("deterministic_cart_emit_failed", error=str(e))

    # NOTE: Menu deterministic emit removed - search_menu tool handles this

    # =========================================================================
    # ENTITY GRAPH CONTEXT - Deterministic tracking from tool outputs
    # =========================================================================
    # v20: All tools use factory pattern with session_id closure (thread-safe)
    # Entity graph persisted to Redis, cart read from Redis (single source of truth)

    from app.core.semantic_context import get_entity_graph

    # Get entity graph context (populated by previous tool calls, persisted in Redis)
    graph = get_entity_graph(session_id)
    semantic_context = graph.get_context_summary()

    if semantic_context:
        logger.debug(
            "entity_graph_context",
            session_id=session_id,
            context=semantic_context[:100]
        )

    # =========================================================================
    # AGENT PROCESSING
    # =========================================================================
    # Get or create crew (cached per session)
    global _CREW_CACHE, _CREW_VERSION
    cache_key = f"{session_id}:v{_CREW_VERSION}"

    if cache_key not in _CREW_CACHE:
        logger.info("creating_restaurant_crew", session_id=session_id, version=_CREW_VERSION)
        _CREW_CACHE[cache_key] = create_restaurant_crew_fixed(session_id)
    else:
        logger.debug("reusing_cached_crew", session_id=session_id)

    crew = _CREW_CACHE[cache_key]

    # 🚀 RAG-BASED TOOL RETRIEVAL - Dynamically filter tools per request
    # Convert tools list to dict for RAG
    all_tools_dict = {tool.name: tool for tool in crew._all_food_tools}
    relevant_tools = get_relevant_tools(user_message, all_tools_dict, max_tools=6)

    # Update food ordering agent's tools dynamically (cached crew, fresh tools!)
    crew._food_ordering_agent.tools = relevant_tools

    logger.info(
        "rag_tool_retrieval",
        session_id=session_id,
        total_tools=len(all_tools_dict),
        relevant_tools=len(relevant_tools),
        reduction=f"{int((1-len(relevant_tools)/len(all_tools_dict))*100)}%",
        tool_names=[t.name for t in relevant_tools]
    )

    # Build context from conversation history with intelligent dynamic summarization
    # Includes ALL history by default, only summarizes when approaching 75% of 128k context (rare scenario)
    context = _build_conversation_context(
        conversation_history=conversation_history,
        welcome_msg=welcome_msg
        # Uses defaults: 96k token limit (75% of 128k), 10k estimated overhead
    )

    # Prepare inputs - include entity graph context for pronoun/positional resolution
    inputs = {
        "user_input": user_message,
        "semantic_context": semantic_context if semantic_context else "No tracked context yet",
        "context": context
    }

    try:
        # Use akickoff() for native async execution
        # Semaphore rate-limits concurrent crews to MAX_CONCURRENT_CREWS
        async with _CREW_SEMAPHORE:
            result = await crew.akickoff(inputs=inputs)

        # Process result - extract clean response
        response = None

        # Try result.raw first (usually contains clean output)
        if hasattr(result, 'raw') and result.raw:
            raw = str(result.raw).strip()
            # If raw output looks clean (no planner markers), check for incomplete
            if not any(marker in raw for marker in ['Thought:', 'Action:', 'Action Input:']):
                cleaned = clean_crew_response(raw)
                if cleaned is not None:
                    response = cleaned
            else:
                # Has planner markers, clean it up
                cleaned = clean_crew_response(raw)
                if cleaned is not None:
                    response = cleaned

        # Fallback to str(result)
        if response is None:
            cleaned = clean_crew_response(str(result).strip())
            if cleaned is not None:
                response = cleaned

        # All cleaning failed - return a helpful message
        if response is None:
            logger.warning("all_response_cleaning_failed")
            response = "I apologize, I had trouble processing that request. Could you please try again?"

        logger.info(
            "restaurant_crew_complete",
            session_id=session_id,
            response_length=len(response)
        )

        metadata = {
            "type": "success",
            "orchestrator": "restaurant_crew",
            "session_id": session_id,
            "user_id": user_id,
        }

        return response, metadata

    except Exception as e:
        logger.error(
            "restaurant_crew_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )

        fallback_response = (
            "I'm here to help! I can assist you with:\n"
            "- Browsing our menu and placing orders\n"
            "- Making table reservations\n"
            "- Viewing or cancelling bookings\n\n"
            "What would you like to do?"
        )

        metadata = {
            "type": "fallback",
            "orchestrator": "restaurant_crew_fallback",
            "error": str(e),
            "session_id": session_id,
        }

        return fallback_response, metadata


def reset_session(session_id: str):
    """Reset crew cache and entity graph for a session."""
    global _CREW_CACHE

    # Clear crew cache
    keys_to_remove = [k for k in _CREW_CACHE if k.startswith(f"{session_id}:")]
    for key in keys_to_remove:
        del _CREW_CACHE[key]

    # Clear entity graph
    try:
        from app.core.semantic_context import clear_entity_graph
        clear_entity_graph(session_id)
    except Exception as e:
        logger.debug("entity_graph_clear_failed", error=str(e))

    logger.info("session_crew_reset", session_id=session_id)


# ============================================================================
# AG-UI STREAMING SUPPORT
# ============================================================================

async def process_with_agui_streaming(
    user_message: str,
    session_id: str,
    conversation_history: List[str],
    emitter: "AGUIEventEmitter",
    user_id: Optional[str] = None,
    welcome_msg: Optional[str] = None,
    device_id: Optional[str] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Process user message with AG-UI event streaming.

    This is the streaming-enabled version of process_with_restaurant_crew.
    Emits real-time events for frontend visibility into agent processing.

    Events emitted:
    - RUN_STARTED: Processing begins
    - ACTIVITY_START/END: Thinking, searching, adding indicators
    - TOOL_CALL_START/ARGS/RESULT/END: Tool execution visibility
    - TEXT_MESSAGE_START/CONTENT/END: Streaming response
    - RUN_FINISHED/RUN_ERROR: Processing complete

    Args:
        user_message: The user's message
        session_id: Session identifier
        conversation_history: Previous conversation
        emitter: AGUIEventEmitter instance for streaming events
        user_id: Optional user identifier
        welcome_msg: Optional welcome message for context

    Returns:
        Tuple of (response_text, metadata)
    """
    from app.core.agui_events import get_tool_activity_message

    logger.info(
        "processing_with_agui_streaming",
        session_id=session_id,
        user_id=user_id,
        message=user_message[:50]
    )

    # Set session context so tools can access user_id via get_current_user_id()
    from app.services.crew_pool import set_session_context
    set_session_context(session_id, user_id)

    # Emit run started
    emitter.emit_run_started()

    # =========================================================================
    # DETERMINISTIC CARD DISPLAY - Emit right after RUN_STARTED
    # =========================================================================
    # v37: Must be in process_with_agui_streaming to ensure correct timing
    # (previously was in process_with_restaurant_crew which is not used by chat endpoint)
    msg_lower = user_message.lower()

    # NOTE: Both Menu and Cart deterministic emits removed - tools in crew_agent.py already emit:
    # - search_menu tool emits MENU_DATA (was causing duplicate MenuCards)
    # - view_cart tool emits CART_DATA at crew_agent.py:682 (was causing duplicate CartCards)

    try:
        # =========================================================================
        # ACTIVITY FLOW - Each new activity replaces the previous (no ACTIVITY_END between)
        # =========================================================================

        # Phase 1: Starting
        emitter.emit_activity("thinking", "Let me help you with that...")

        # Load context
        from app.core.semantic_context import get_entity_graph
        graph = get_entity_graph(session_id)
        semantic_context = graph.get_context_summary()

        # Phase 2: If returning user with context
        if semantic_context:
            emitter.emit_activity("checking", "Checking your preferences...")
            logger.debug("entity_graph_context", session_id=session_id, context=semantic_context[:100])

        # Get or create crew
        global _CREW_CACHE, _CREW_VERSION
        cache_key = f"{session_id}:v{_CREW_VERSION}"

        if cache_key not in _CREW_CACHE:
            emitter.emit_activity("thinking", "Setting things up...")
            logger.info("creating_restaurant_crew", session_id=session_id, version=_CREW_VERSION)
            _CREW_CACHE[cache_key] = create_restaurant_crew_fixed(session_id)

        crew = _CREW_CACHE[cache_key]

        # 🚀 RAG-BASED TOOL RETRIEVAL - Dynamically filter tools per request
        # Convert tools list to dict for RAG
        all_tools_dict = {tool.name: tool for tool in crew._all_food_tools}
        relevant_tools = get_relevant_tools(user_message, all_tools_dict, max_tools=6)

        # Update food ordering agent's tools dynamically (cached crew, fresh tools!)
        crew._food_ordering_agent.tools = relevant_tools

        logger.info(
            "rag_tool_retrieval",
            session_id=session_id,
            total_tools=len(all_tools_dict),
            relevant_tools=len(relevant_tools),
            reduction=f"{int((1-len(relevant_tools)/len(all_tools_dict))*100)}%",
            tool_names=[t.name for t in relevant_tools]
        )

        # Build context with intelligent dynamic summarization
        context = _build_conversation_context(
            conversation_history=conversation_history,
            welcome_msg=welcome_msg
            # Uses defaults: 96k token limit (75% of 128k), 10k estimated overhead
        )

        inputs = {
            "user_input": user_message,
            "semantic_context": semantic_context if semantic_context else "No tracked context yet",
            "context": context
        }

        # Phase 3: Processing - this is where the real work happens
        emitter.emit_activity("processing", "Processing your request...")

        # Use akickoff() for native async execution
        async with _CREW_SEMAPHORE:
            result = await crew.akickoff(inputs=inputs)

        # Process result - extract clean response
        response = None

        if hasattr(result, 'raw') and result.raw:
            raw = str(result.raw).strip()
            if not any(marker in raw for marker in ['Thought:', 'Action:', 'Action Input:']):
                cleaned = clean_crew_response(raw)
                if cleaned is not None:
                    response = cleaned
            else:
                cleaned = clean_crew_response(raw)
                if cleaned is not None:
                    response = cleaned

        if response is None:
            cleaned = clean_crew_response(str(result).strip())
            if cleaned is not None:
                response = cleaned

        if response is None:
            logger.warning("all_response_cleaning_failed")
            response = "I apologize, I had trouble processing that request. Could you please try again?"

        emitter.emit_activity_end()

        # Stream response
        logger.info("restaurant_crew_complete", session_id=session_id, response_length=len(response))

        # Stream the response word by word
        emitter.emit_full_text(response, chunk_size=1)

        # Get quick replies AFTER streaming response (so they appear below the message)
        # Uses GPT-4o-mini to classify response and determine appropriate buttons
        # IMPORTANT: Use emitter.emit_quick_replies() for immediate/synchronous emission
        # (not the global emit_quick_replies() which uses call_soon_threadsafe and can race)
        try:
            from app.features.food_ordering.crew_agent import get_response_quick_replies
            quick_replies = get_response_quick_replies(response)
            if quick_replies:
                emitter.emit_quick_replies(quick_replies)
                logger.debug("quick_replies_emitted_direct", session_id=session_id, count=len(quick_replies))
        except Exception as e:
            logger.debug("quick_reply_emit_failed", error=str(e))
            # Fallback will be used by frontend

        # Ensure activity indicator is cleared before finishing
        # (redundant safety - already called at line 758, but ensures it's sent after streaming)
        emitter.emit_activity_end()

        # Emit run finished
        emitter.emit_run_finished(response)

        metadata = {
            "type": "success",
            "orchestrator": "restaurant_crew_streaming",
            "session_id": session_id,
            "user_id": user_id,
        }

        return response, metadata

    except Exception as e:
        logger.error(
            "agui_streaming_error",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )

        emitter.emit_activity_end()
        emitter.emit_run_error(str(e))

        fallback_response = (
            "I'm here to help! I can assist you with:\n"
            "- Browsing our menu and placing orders\n"
            "- Making table reservations\n"
            "- Viewing or cancelling bookings\n\n"
            "What would you like to do?"
        )

        metadata = {
            "type": "fallback",
            "orchestrator": "restaurant_crew_streaming_fallback",
            "error": str(e),
            "session_id": session_id,
        }

        return fallback_response, metadata
