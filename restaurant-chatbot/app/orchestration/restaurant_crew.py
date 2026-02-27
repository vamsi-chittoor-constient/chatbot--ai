"""
Restaurant Crew
================
Single-agent crew for handling all restaurant operations.

Agent:
- Restaurant Assistant (Kavya): Menu browsing, cart management, checkout,
  table reservations, complaints, payments

Architecture:
- Thread-safe: All tools use factory pattern with session_id closure
- Entity Graph: Persisted to Redis (survives server restarts)
- Cart: Read directly from Redis (single source of truth)
- Intent-based prompts: Agent reasons about context, not keyword matching
- GPT-4o for better reasoning on nuanced conversations
- Dynamic tool selection (context-aware)
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from typing import Dict, Any, List, Optional, Tuple
import structlog
import asyncio
import os
import re

# Tool retrieval - import at module level for initialization
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
_CREW_VERSION = 42


async def _translate_response(text: str, target_language: str) -> str:
    """
    Translate English response to target language (Hinglish/Tanglish).
    Skips translation if text already contains target language characters.

    Args:
        text: Response text (may be English or already translated)
        target_language: Target language (Hindi, Tamil)

    Returns:
        Translated text, or original if translation not needed/fails
    """
    import re

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if target_language == "Hindi":
            system_prompt = """Translate to casual Hinglish (Hindi-English mix in ROMAN script). Rules:
- If the text is ALREADY in Hinglish (Roman script Hindi-English mix), return it UNCHANGED
- Write like a young Indian texts friends — casual, short, natural. NOT formal/literary Hindi.
- ROMAN script ONLY — NO Devanagari (अ,ब,क). Write Hindi words phonetically: "chahiye", "dikha do", "karo"
- Use SIMPLE common Hindi words. Prefer "chahiye/chahte ho" over formal "chahenge", "karo" over "karenge", "dikha do" over "dikhana chahenge"
- Keep lots of English mixed in — "check karo", "add kar do", "menu dekh lo", "items available hain"
- Phonetic spelling for TTS: double vowels for long sounds (aa, ee, oo). Example: "aap", "nahi", "theek hai"
- Keep UNCHANGED: food names, numbers, prices (₹), order IDs (ORD-...), emojis, markdown (**bold**)
- Preserve ALL details (items, prices, totals) — do NOT shorten or drop information
- Output ONLY the translation, no explanations
Examples:
  English: "Would you like to dine in or take away?" → "Aap dine in chahte ho ya take away?"
  English: "Your cart has 2 items totaling ₹450" → "Aapke cart mein 2 items hain, total ₹450"
  BAD: "Kya aap kuch popular options dekhna chahenge" (too formal)
  GOOD: "Kya aap popular options check karna chahte ho?"  """
        elif target_language == "Tamil":
            system_prompt = """Translate to casual Tanglish (Tamil-English mix in ROMAN script). Rules:
- If the text is ALREADY in Tanglish (Roman script Tamil-English mix), return it UNCHANGED
- Write like a young South Indian texts friends — casual, short, natural. NOT formal/literary Tamil.
- ROMAN script ONLY — NO Tamil script (அ,ஆ,இ). Write Tamil words phonetically as they sound.
- Use SIMPLE common Tamil words mixed with English. Keep English technical/food words as-is.
- Phonetic spelling for TTS: spell as spoken. "irukku", "pannunga", "paarunga", "sollunga"
- Keep UNCHANGED: food names, numbers, prices (₹), order IDs (ORD-...), emojis, markdown (**bold**)
- Preserve ALL details (items, prices, totals) — do NOT shorten or drop information
- Output ONLY the translation, no explanations
Examples:
  English: "Would you like to dine in or take away?" → "Dine in ah illa take away ah?"
  English: "Your cart has 2 items totaling ₹450" → "Unga cart la 2 items irukku, total ₹450"  """
        else:
            return text

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=500
        )

        translated = response.choices[0].message.content.strip()
        logger.debug("crew_translation_applied",
                    original_len=len(text),
                    translated_len=len(translated),
                    language=target_language)
        return translated

    except Exception as e:
        logger.warning("crew_translation_failed", error=str(e), language=target_language)
        return text


def extract_unrealized_tool_call(raw_response: str) -> dict | None:
    """
    Detect when CrewAI's LLM output a tool call in its final answer text
    instead of actually executing it.

    Returns:
        Dict with 'action' and 'input' keys, or None if no unrealized call found.
    """
    import re
    import json

    response = str(raw_response).strip()
    # Strip triple backtick wrappers
    response = re.sub(r'^```\s*', '', response)
    response = re.sub(r'\s*```?\s*$', '', response)

    # Only applies when there's Action + Action Input but no Observation
    if 'Action:' not in response or 'Action Input:' not in response:
        return None
    if 'Observation:' in response:
        return None  # Tool was executed — normal flow

    action_match = re.search(r'Action:\s*(.+?)(?:\n|$)', response)
    input_match = re.search(r'Action Input:\s*(.+?)(?:\n|$)', response, re.DOTALL)

    if not action_match or not input_match:
        return None

    action_name = action_match.group(1).strip()
    action_input_raw = input_match.group(1).strip()

    # Parse JSON input
    try:
        action_input = json.loads(action_input_raw)
    except json.JSONDecodeError:
        # Try to extract JSON from the string (may have trailing backticks)
        json_match = re.search(r'\{.*\}', action_input_raw, re.DOTALL)
        if json_match:
            try:
                action_input = json.loads(json_match.group())
            except json.JSONDecodeError:
                return None
        else:
            return None

    logger.info(
        "unrealized_tool_call_detected",
        action=action_name,
        input=action_input
    )
    return {"action": action_name, "input": action_input}


def execute_unrealized_tool_call(tool_call: dict, tools: list) -> str | None:
    """
    Execute an unrealized tool call using the tools list from the crew.

    Args:
        tool_call: Dict with 'action' (tool name) and 'input' (dict of args)
        tools: List of CrewAI tool instances

    Returns:
        Tool result string, or None if tool not found
    """
    action_name = tool_call["action"]
    action_input = tool_call["input"]

    # Find matching tool by name
    matching_tool = None
    for t in tools:
        tool_name = getattr(t, 'name', '') or ''
        if tool_name == action_name:
            matching_tool = t
            break

    if not matching_tool:
        logger.warning("unrealized_tool_not_found", action=action_name)
        return None

    try:
        # Run tool in a THREAD so that run_async() inside tools sees no running
        # event loop and properly schedules on _MAIN_LOOP. Without this, calling
        # tool.run() from the main loop thread causes run_async() to create a new
        # loop, breaking DB connections tied to the main loop.
        import concurrent.futures

        def _run_tool():
            if hasattr(matching_tool, 'run'):
                if isinstance(action_input, dict):
                    return matching_tool.run(**action_input)
                else:
                    return matching_tool.run(action_input)
            elif callable(matching_tool):
                if isinstance(action_input, dict):
                    return matching_tool(**action_input)
                else:
                    return matching_tool(action_input)
            else:
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_tool)
            # Increase timeout to 60s for slow operations like payment API calls
            result = future.result(timeout=60)

        if result is None:
            logger.warning("unrealized_tool_not_callable", action=action_name)
            return None

        logger.info(
            "unrealized_tool_call_executed",
            action=action_name,
            result_len=len(str(result))
        )
        return str(result)

    except Exception as e:
        logger.error(
            "unrealized_tool_call_failed",
            action=action_name,
            error=str(e),
            exc_info=True
        )
        return None


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
    return "I didn't quite catch that. Could you say that again? You can ask me about the menu, place an order, or make a reservation."


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
    Accurately count tokens using OpenAI's tiktoken tokenizer.

    Uses the official tokenizer for gpt-4o to ensure accurate token counting.
    This prevents underestimation that could lead to context limit errors.

    Args:
        text: Text to count tokens for

    Returns:
        Exact token count for gpt-4o model
    """
    import tiktoken

    try:
        # Use tiktoken for accurate token counting
        encoding = tiktoken.encoding_for_model("gpt-4o")
        return len(encoding.encode(text))
    except Exception as e:
        # Fallback to heuristic if tiktoken fails
        logger.warning(f"tiktoken failed, using heuristic: {str(e)}")
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


def create_restaurant_crew_fixed(session_id: str, customer_id: Optional[str] = None, source: str = "web") -> Crew:
    """
    Create restaurant crew with a single agent handling all operations.

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
    # FOOD ORDERING AGENT - Event-Sourced Tools
    # ========================================================================
    # Import event-sourced tools (SQL-based state, zero token context)
    from app.features.food_ordering.tools_event_sourced import create_event_sourced_tools

    # Import remaining legacy tools (not yet migrated to event-sourced pattern)
    from app.features.food_ordering.crew_agent import (
        create_checkout_tool,
        create_cancel_order_tool,
        create_update_quantity_tool,
        create_set_special_instructions_tool,
        create_get_item_details_tool,
        create_reorder_tool,
        create_get_order_status_tool,
        create_get_order_history_tool,
        create_get_order_receipt_tool,
        create_filter_by_cuisine_tool,
        # Payment tools
        create_initiate_payment_tool,
        create_verify_payment_otp_tool,
        create_check_payment_status_tool,
        create_cancel_payment_tool,
        create_select_payment_method_tool,
    )

    # Import complaint tools (session-aware sync wrappers)
    from app.features.feedback.crew_complaint_tools import (
        create_complaint_tool,
        create_get_complaints_tool,
        create_complaint_status_tool,
    )

    # Create event-sourced tools (search_menu, add_to_cart, view_cart, remove_from_cart)
    event_sourced_tools = create_event_sourced_tools(session_id, customer_id)

    # Create ALL tools (event-sourced + legacy tools)
    all_food_tools = [
        *event_sourced_tools,  # Event-sourced: search_menu, add_to_cart, view_cart, remove_from_cart
        # Legacy tools (not yet migrated):
        create_checkout_tool(session_id),
        create_cancel_order_tool(session_id),
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
        create_select_payment_method_tool(session_id),
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
- "show menu" → call search_menu() IMMEDIATELY

🎯 CRITICAL: YOU MUST USE TOOLS - DO NOT HALLUCINATE!
- NEVER respond as if you've shown the menu without calling search_menu()
- NEVER say "I've added X to cart" without calling add_to_cart()
- NEVER describe cart contents without calling view_cart()
- ALWAYS call the required tool BEFORE responding to the customer

🛒 ADDING TO CART vs SEARCHING:
- "add two beeda" / "add 2 beeda" / "I'll take two beeda" → call add_to_cart("beeda", 2) DIRECTLY
- "one beeda please" / "I'll have a beeda" → call add_to_cart("beeda", 1) DIRECTLY
- "add beeda to cart" / "order beeda" / "get me beeda" (NO quantity mentioned) → ASK "How many would you like?" BEFORE adding
- Any request with "add" + item + EXPLICIT quantity → use add_to_cart() DIRECTLY
- "do you have beeda?" / "what is beeda?" / "show me beeda" → call search_menu(query="beeda") to show options
- IMPORTANT: If the customer does NOT specify a quantity, ASK them how many they want before calling add_to_cart()

🚨 PRESERVE EXACT ITEM NAMES - DO NOT CORRECT SPELLINGS 🚨
When calling add_to_cart(), batch_add_to_cart(), or search_menu(), use the EXACT item name the customer typed.
Do NOT "correct" or re-spell food names. The tools have fuzzy matching built in.
- Customer says "aloo parota" → pass "aloo parota", NOT "aloo paratha"
- Customer says "dosai" → pass "dosai", NOT "dosa"
- Customer says "biriyani" → pass "biriyani", NOT "biryani"

🚨 BATCH RULE - MULTIPLE ITEMS IN ONE MESSAGE:
When the customer mentions 2+ DIFFERENT items in one message, ALWAYS use batch_add_to_cart() instead of calling add_to_cart() multiple times.
- "add two ghee masala dosa and ghee onion dosa" → batch_add_to_cart("ghee masala dosa:2, ghee onion dosa:1")
- "I want 1 margherita pizza, 2 cokes, and garlic bread" → batch_add_to_cart("margherita pizza:1, coke:2, garlic bread:1")
- NEVER call add_to_cart() twice in one turn - use batch_add_to_cart() instead

🚨 BATCH REMOVE RULE - REMOVING MULTIPLE ITEMS:
When the customer asks to remove 2+ items, use correct_order() with empty add_items instead of calling remove_from_cart() multiple times.
- "remove burger and coke" → correct_order(remove_items="burger, coke", add_items="")
- "delete pizza and garlic bread from cart" → correct_order(remove_items="pizza, garlic bread", add_items="")
- NEVER call remove_from_cart() twice in one turn - use correct_order() instead

🚨 CLEAR CART RULE:
- "clear cart", "clear my cart", "empty cart", "empty my cart", "empty everything", "remove everything", "start over" → call clear_cart() IMMEDIATELY. Do NOT call view_cart() for these. Do NOT ask for confirmation.
- For CORRECTIONS ("no, I meant...", "that's wrong"), use correct_order() instead — never clear_cart() for corrections.
- For quantity changes: use update_quantity("item name", correct_quantity)

📝 OUTPUT FORMAT:
- Return friendly, natural language responses (not JSON or technical data)
- If a tool returns a message, share it conversationally with the customer

⚠️ CRITICAL - NEVER REFUSE RESTAURANT REQUESTS:
- You are a restaurant assistant. ALL requests about food, cart, orders, payment are VALID.
- NEVER say "I cannot comply", "I'm unable to", or refuse any restaurant-related request.
- "show my cart" → call view_cart and share the result
- "pay online" / "payment" → payment is handled automatically after checkout (Razorpay online only)
- "checkout" / "I want to checkout" / "place order" / "proceed to payment" → call checkout() IMMEDIATELY. Do NOT ask "would you like to continue?" or ask for confirmation. Just call the tool. Payment link is shown automatically after checkout.
- When in doubt, USE THE APPROPRIATE TOOL and relay its result to the customer.

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

IMPORTANT - For complaints:
When customer complains about food quality, service, wait time, or other issues:
- Use the create_complaint tool to log the issue
- Show empathy and offer resolution (replacement/refund)""",
        llm=llm,
        tools=all_food_tools,  # Will be replaced with RAG-filtered tools before each execution
        verbose=True,
        allow_delegation=False,
        respect_context_window=True,
        cache=False,
        max_iter=15,  # Needs enough iterations for tool call + observation + final answer
        max_retry_limit=1,
        reasoning=False,  # Disabled for speed
        memory=False,  # Disabled - uses Redis for state
    )

    # ========================================================================
    # TASK - Single task assigned to the restaurant agent
    # ========================================================================
    # --- Task description: web (unchanged from original) ---
    _WEB_TASK = """User: {user_input}
Context: {semantic_context}
History: {context}

RULES:
- Always use tools. Return tool output as-is.
- LANGUAGE: If the user message starts with [RESPOND IN HINGLISH...], respond in casual Hinglish (Roman script ONLY, NO Devanagari). Use simple words like "chahiye", "karo", "dekh lo" — NOT formal "chahenge", "karenge", "dekhenge". Mix English freely: "cart mein add ho gaya", "menu check karo". Example: "Aapke cart mein 2 Masala Dosa add ho gaye, total ₹250. Aur kuch chahiye?"
- LANGUAGE: If the user message starts with [RESPOND IN TANGLISH...], respond in casual Tanglish (Roman script ONLY, NO Tamil script). Example: "Unga cart la 2 Masala Dosa add aaiduchu, total ₹250. Vera enna venum?"
- Keep food names, prices, order IDs in English always."""

    # --- Task description: WhatsApp ---
    _WHATSAPP_TASK = """User: {user_input}
Context: {semantic_context}
History: {context}

RULES:
- Always use tools. Return tool output as-is.
- Keep responses concise (under 300 words). Use *bold* for emphasis.
- Use emojis for structure (🍽️ 🛒 ✅ 💳). Format lists with emojis or numbers, not bullets.
- Don't reference UI cards, buttons, or visual elements — the user is on WhatsApp.
- For large menus, guide the user to pick a category first (e.g. "Starters, Curries, Biryani...") instead of listing everything.
- LANGUAGE: If the user message starts with [RESPOND IN HINGLISH...], respond in casual Hinglish (Roman script ONLY, NO Devanagari). Mix English freely.
- LANGUAGE: If the user message starts with [RESPOND IN TANGLISH...], respond in casual Tanglish (Roman script ONLY, NO Tamil script).
- Keep food names, prices, order IDs in English always."""

    customer_request_task = Task(
        description=_WHATSAPP_TASK if source == "whatsapp" else _WEB_TASK,
        expected_output="Tool output (human-friendly message from tool)",
        agent=food_ordering_agent,
    )

    # ========================================================================
    # CREATE CREW - Single agent, no delegation
    # ========================================================================
    crew = Crew(
        agents=[food_ordering_agent],
        tasks=[customer_request_task],
        process=Process.sequential,
        verbose=True,  # Enable for proper result extraction
        planning=False,  # Disabled for speed - agent executes directly without planning phase
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

    This is the main entry point for processing user messages.

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
        # Emit cart data deterministically (from PostgreSQL session_cart)
        try:
            from app.core.session_events import get_sync_session_tracker
            from app.core.agui_events import emit_cart_data
            tracker = get_sync_session_tracker(session_id)
            cart_data = tracker.get_cart_summary()
            items = cart_data.get("items", [])
            if items:
                emit_cart_data(session_id, items, cart_data.get("total", 0))
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

    # RAG-based context retrieval - only get relevant entities for this query
    graph = get_entity_graph(session_id)
    semantic_context = graph.get_relevant_context(user_message)

    logger.debug(
        "rag_context_retrieved",
        session_id=session_id,
        context=semantic_context,
        query=user_message[:50]
    )

    # =========================================================================
    # AGENT PROCESSING
    # =========================================================================
    # Get or create crew (cached per session — non-streaming path is web-only)
    global _CREW_CACHE, _CREW_VERSION
    cache_key = f"{session_id}:v{_CREW_VERSION}"

    if cache_key not in _CREW_CACHE:
        logger.info("creating_restaurant_crew", session_id=session_id, version=_CREW_VERSION)
        _CREW_CACHE[cache_key] = create_restaurant_crew_fixed(session_id, customer_id=user_id, source="web")
    else:
        logger.debug("reusing_cached_crew", session_id=session_id)

    crew = _CREW_CACHE[cache_key]

    # 🚀 RAG-BASED TOOL RETRIEVAL - Dynamically filter tools per request
    # Convert tools list to dict for RAG
    all_tools_dict = {tool.name: tool for tool in crew._all_food_tools}

    # MULTI-TURN CONTEXT RESOLUTION FOR RAG:
    # Short/ambiguous messages like "Yes please", "do that", "ok" need context
    # from the last assistant turn to resolve intent for tool retrieval.
    # History can be strings ("Assistant: ...") or dicts ({"role": "assistant", "content": "..."})
    rag_query = user_message
    if len(user_message.split()) <= 4 and conversation_history:
        last_assistant_msg = ""
        for turn in reversed(conversation_history):
            if isinstance(turn, dict):
                if turn.get("role", "") == "assistant":
                    last_assistant_msg = turn.get("content", "")[:150]
                    break
            elif isinstance(turn, str) and turn.startswith("Assistant:"):
                last_assistant_msg = turn[len("Assistant:"):].strip()[:150]
                break
        if last_assistant_msg:
            rag_query = f"{last_assistant_msg} | User: {user_message}"
            logger.info("rag_query_enriched", original=user_message, enriched_query=rag_query[:100])

    # TRANSLATION LAYER FOR RAG:
    # If query is non-English (or we want to be safe), translate it to English for better retrieval
    # Tools are indexed in English, so searching in Hindi/Tamil yields poor results.
    # We use a lightweight LLM call to translate ONLY the search query.
    if any(ord(c) > 127 for c in rag_query):
        try:
            from app.ai_services.openai_service import OpenAIService
            openai_service = OpenAIService()
            rag_query = await openai_service.translate_query(rag_query, "English")
            logger.info("rag_query_translated", original=user_message, translated=rag_query)
        except Exception as e:
            logger.warning("rag_translation_failed", error=str(e))

    relevant_tools = get_relevant_tools(rag_query, all_tools_dict, max_tools=6)

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
        # Store main event loop so run_async() in tools can schedule coroutines
        # on it instead of creating a new loop (prevents "Future attached to
        # a different loop" errors with HTTP clients/DB connections).
        from app.features.food_ordering import crew_agent as _crew_agent_mod
        _crew_agent_mod._MAIN_LOOP = asyncio.get_running_loop()

        # Use akickoff() for native async execution
        # Semaphore rate-limits concurrent crews to MAX_CONCURRENT_CREWS
        async with _CREW_SEMAPHORE:
            result = await crew.akickoff(inputs=inputs)

        # Process result - extract clean response
        response = None

        # First: check for unrealized tool calls (LLM output Action/Input but tool wasn't executed)
        raw_for_tool_check = str(result.raw).strip() if hasattr(result, 'raw') and result.raw else str(result).strip()
        unrealized = extract_unrealized_tool_call(raw_for_tool_check)
        if unrealized:
            tool_result = execute_unrealized_tool_call(unrealized, crew._all_food_tools)
            if tool_result:
                response = tool_result

        # Try result.raw first (usually contains clean output)
        if response is None and hasattr(result, 'raw') and result.raw:
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
    device_id: Optional[str] = None,
    language: str = "English",
    voice_mode: bool = False,
    source: str = "web"
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
        language: Response language (English, Hindi, Tamil) for translation

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

    # NOTE: Menu deterministic emit removed - search_menu tool handles it
    # NOTE: Cart deterministic emit removed - view_cart tool handles it

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

        # Get or create crew (cached per session+source — web and whatsapp use different prompts)
        global _CREW_CACHE, _CREW_VERSION
        cache_key = f"{session_id}:v{_CREW_VERSION}"

        if cache_key not in _CREW_CACHE:
            emitter.emit_activity("thinking", "Setting things up...")
            logger.info("creating_restaurant_crew", session_id=session_id, version=_CREW_VERSION, source=source)
            _CREW_CACHE[cache_key] = create_restaurant_crew_fixed(session_id, customer_id=user_id, source=source)

        crew = _CREW_CACHE[cache_key]

        # 🚀 RAG-BASED TOOL RETRIEVAL - Dynamically filter tools per request
        # Convert tools list to dict for RAG
        all_tools_dict = {tool.name: tool for tool in crew._all_food_tools}

        # MULTI-TURN CONTEXT RESOLUTION FOR RAG:
        # Short/ambiguous messages like "Yes please", "do that", "ok" need context
        # from the last assistant turn to resolve intent for tool retrieval.
        # History can be strings ("Assistant: ...") or dicts ({"role": "assistant", "content": "..."})
        rag_query = user_message
        if len(user_message.split()) <= 4 and conversation_history:
            last_assistant_msg = ""
            for turn in reversed(conversation_history):
                if isinstance(turn, dict):
                    if turn.get("role", "") == "assistant":
                        last_assistant_msg = turn.get("content", "")[:150]
                        break
                elif isinstance(turn, str) and turn.startswith("Assistant:"):
                    last_assistant_msg = turn[len("Assistant:"):].strip()[:150]
                    break
            if last_assistant_msg:
                rag_query = f"{last_assistant_msg} | User: {user_message}"
                logger.info("rag_query_enriched", original=user_message, enriched_query=rag_query[:100])

        # TRANSLATION LAYER: Translate non-English input to English for crew + RAG.
        # Only fires when input contains non-ASCII chars (native script like Devanagari/Tamil).
        # Voice mode with Romanization produces ASCII Hinglish ("do caramel add karo")
        # which GPT-4 understands natively — translating it mangles intent
        # ("add karo" → "add-ons"). Chat mode typed in native script needs translation.
        english_input = user_message
        if language != "English" and language in ["Hindi", "Tamil"] and any(ord(c) > 127 for c in user_message):
            try:
                from openai import AsyncOpenAI
                _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                _resp = await _client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Translate to English. Keep food names, numbers, prices unchanged. Output ONLY the translation."},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.1,
                    max_tokens=200
                )
                english_input = _resp.choices[0].message.content.strip()
                logger.info("crew_input_translated", original=user_message, english=english_input)
            except Exception as e:
                logger.warning("crew_input_translation_failed", error=str(e))
                english_input = user_message

        # Use enriched query for RAG, but original english_input for crew task
        rag_input = rag_query if rag_query != user_message else english_input
        relevant_tools = get_relevant_tools(rag_input, all_tools_dict, max_tools=6)

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
            "user_input": english_input,  # English for reliable tool calling
            "semantic_context": semantic_context if semantic_context else "No tracked context yet",
            "context": context
        }

        # Phase 3: Processing - this is where the real work happens
        emitter.emit_activity("processing", "Processing your request...")

        # Store main event loop for run_async() in tools
        from app.features.food_ordering import crew_agent as _crew_agent_mod
        _crew_agent_mod._MAIN_LOOP = asyncio.get_running_loop()

        # Use akickoff() for native async execution
        async with _CREW_SEMAPHORE:
            result = await crew.akickoff(inputs=inputs)

        # Process result - extract clean response
        response = None

        # First: check for unrealized tool calls (LLM output Action/Input but tool wasn't executed)
        raw_for_tool_check = str(result.raw).strip() if hasattr(result, 'raw') and result.raw else str(result).strip()
        unrealized = extract_unrealized_tool_call(raw_for_tool_check)
        if unrealized:
            tool_result = execute_unrealized_tool_call(unrealized, crew._all_food_tools)
            if tool_result:
                response = tool_result

        if response is None and hasattr(result, 'raw') and result.raw:
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

        # Translate crew response if needed.
        # In VOICE mode: skip — translate_for_tts() in voice.py handles response translation.
        # In CHAT mode: translate here (crew responds in English, user expects Hinglish/Tanglish).
        logger.info("crew_language_check", session_id=session_id, language=language, voice_mode=voice_mode, will_translate=(language != "English" and language in ["Hindi", "Tamil"] and not voice_mode), response_preview=response[:50] if response else "")
        if language != "English" and language in ["Hindi", "Tamil"] and not voice_mode:
            logger.info("crew_translating_response", session_id=session_id, language=language)
            response = await _translate_response(response, language)
            logger.info("crew_translation_done", session_id=session_id, translated_preview=response[:50] if response else "")

        # Stream response
        logger.info("restaurant_crew_complete", session_id=session_id, response_length=len(response))

        # Strip internal context markers before streaming to the user.
        # These brackets are LLM-agent metadata, not user-facing text.
        response = re.sub(
            r'\[(?:SEARCH RESULTS DISPLAYED|MENU CARD DISPLAYED|MENU DISPLAYED'
            r'|CART CARD DISPLAYED|EMPTY CART|ALTERNATIVE CATEGORY MENU DISPLAYED'
            r'|INVALID QUANTITY|INVALID INSTRUCTIONS'
            r'|CHECKOUT COMPLETE|PAYMENT CONFIRMED|PAYMENT LINK SENT'
            r'|RECEIPT DISPLAYED)[^\]]*\]\s*',
            '', response
        ).strip()

        # Strip leaked language directive prefixes (e.g. [RESPOND IN HINGLISH ...])
        # These are injected into user messages for the LLM but must never appear in output.
        response = re.sub(
            r'\[RESPOND IN (?:HINGLISH|TANGLISH)[^\]]*\]\s*',
            '', response, flags=re.IGNORECASE
        ).strip()

        # Sanitize response to catch any remaining prompt leaks, JSON, errors
        from app.core.response_sanitizer import sanitize_response as _sanitize
        response = _sanitize(response)

        # Stream the response word by word
        emitter.emit_full_text(response, chunk_size=1)

        # Classify quick replies NOW (while GPT-4o-mini processes, we can flush events)
        # But EMIT them later — after all tool/payment events are flushed —
        # so they don't get stripped by CART_DATA/PAYMENT_LINK/RECEIPT_LINK reducers.
        quick_replies_to_emit = None
        try:
            from app.features.food_ordering.crew_agent import get_response_quick_replies, DEFAULT_QUICK_REPLIES
            quick_replies_to_emit = get_response_quick_replies(response)
            if not quick_replies_to_emit:
                quick_replies_to_emit = DEFAULT_QUICK_REPLIES
        except Exception as e:
            logger.warning("quick_reply_classify_failed", error=str(e))
            quick_replies_to_emit = [
                {"label": "🍔 Show Menu", "action": "show menu"},
                {"label": "🛒 View Cart", "action": "view cart"},
                {"label": "✅ Checkout", "action": "checkout"},
                {"label": "❓ Help", "action": "help"},
            ]

        # Ensure activity indicator is cleared before finishing
        # (redundant safety - already called at line 758, but ensures it's sent after streaming)
        emitter.emit_activity_end()

        # CRITICAL: Flush all pending tool events BEFORE quick replies and RUN_FINISHED.
        # Tool events (SEARCH_RESULTS, MENU_DATA, RECEIPT_LINK) are emitted from sync
        # contexts (thread pool) and staged in _PENDING_EVENTS. Flushing them first
        # ensures they arrive on the frontend BEFORE quick replies, so the reducer
        # doesn't strip quick_replies when processing data events.
        from app.core.agui_events import flush_pending_events
        flushed = flush_pending_events(session_id)
        if flushed > 0:
            logger.debug("tool_events_flushed_before_run_finished", session_id=session_id, count=flushed)

        # =====================================================================
        # PAYMENT WORKFLOW TRIGGER — runs AFTER crew finishes on main thread
        # =====================================================================
        # The checkout tool stores payment info in Redis. After the crew
        # completes, we trigger run_payment_workflow() here (on the main
        # async loop) so that DB/HTTP connections work correctly and
        # payment events are staged before RUN_FINISHED.
        try:
            from app.core.redis import get_sync_redis_client
            import json as _json
            _redis = get_sync_redis_client()
            _pinfo_key = f"checkout_payment_info:{session_id}"
            _pinfo_data = _redis.get(_pinfo_key)
            if _pinfo_data:
                _pinfo = _json.loads(_pinfo_data)
                _redis.delete(_pinfo_key)
                # Read pending order items for receipt generation
                _items = None
                _order_type = None
                _subtotal = None
                _packaging = None
                _pending_key = f"pending_order:{session_id}"
                _pending_data = _redis.get(_pending_key)
                if _pending_data:
                    _pending = _json.loads(_pending_data)
                    _items = _pending.get("items")
                    _order_type = _pending.get("order_type")
                    _subtotal = _pending.get("subtotal")
                    _packaging = _pending.get("packaging_charges")
                from app.workflows.payment_workflow import run_payment_workflow
                await run_payment_workflow(
                    session_id, _pinfo["order_display_id"], _pinfo["total"],
                    initial_method="online",
                    items=_items, order_type=_order_type,
                    subtotal=_subtotal, packaging_charges=_packaging
                )
                # Flush payment events so they're queued before quick replies
                flushed_payment = flush_pending_events(session_id)
                if flushed_payment > 0:
                    logger.debug("payment_events_flushed", session_id=session_id, count=flushed_payment)
        except Exception as _pe:
            logger.warning("payment_workflow_trigger_failed", error=str(_pe), session_id=session_id)

        # NOW emit quick replies — AFTER all tool/payment events are flushed.
        # This guarantees quick replies are the last message before RUN_FINISHED
        # and won't be stripped by data event reducers (CART_DATA, PAYMENT_LINK, etc.).
        if quick_replies_to_emit:
            try:
                emitter.emit_quick_replies(quick_replies_to_emit)
                logger.debug("quick_replies_emitted_last", session_id=session_id, count=len(quick_replies_to_emit))
            except Exception:
                pass

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

        # Flush any pending tool events before error
        from app.core.agui_events import flush_pending_events
        flush_pending_events(session_id)

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
