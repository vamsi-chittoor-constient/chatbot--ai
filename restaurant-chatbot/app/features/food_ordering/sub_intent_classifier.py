"""
Sub-Intent Classifier
=====================
LLM-based intent classification and entity extraction for food ordering.

Uses structured output with Pydantic models for type-safe, deterministic parsing.
"""

from typing import Dict, Any
import structlog

from langchain_core.messages import SystemMessage, HumanMessage

from app.features.food_ordering.state import SubIntentClassification, EntitySchema, FoodOrderingState
from app.ai_services.agent_llm_factory import ManagedChatOpenAI
from app.core.config import config

logger = structlog.get_logger("food_ordering.sub_intent_classifier")


async def classify_sub_intent(
    user_message: str,
    state: FoodOrderingState
) -> SubIntentClassification:
    """
    Classify user's sub-intent and extract entities.

    Uses LLM with structured output to classify into one of 5 sub-intents
    and extract relevant entities in a single call.

    Args:
        user_message: User's current message
        state: Current food ordering state (for context)

    Returns:
        SubIntentClassification with intent, entities, and missing fields
    """
    session_id = state.get("session_id", "unknown")

    logger.info(
        "Classifying sub-intent",
        session_id=session_id,
        message=user_message[:50]
    )

    # Build context from state
    context_parts = []

    # === LOAD STATE FROM EXTERNAL STORAGE (PRIMARY SOURCE) ===
    # CRITICAL: Load pending_entities and entity_collection_step from entity_graph_service
    # This is the source of truth - primary storage
    entity_collection_step = None
    pending_entities = {}
    current_sub_intent = None

    user_id = state.get("user_id")
    if user_id:
        try:
            from app.core.entity_graph_service import get_entity_graph_service
            graph_service = get_entity_graph_service()
            active_intent = graph_service.get_active_intent(user_id, session_id)

            if active_intent:
                # Load from external storage (PRIMARY SOURCE)
                current_sub_intent = active_intent.get("sub_intent")
                pending_entities = active_intent.get("entities", {})
                entity_collection_step = active_intent.get("entity_collection_step")

                logger.info(
                    "Loaded state from external storage",
                    session_id=session_id,
                    current_sub_intent=current_sub_intent,
                    entity_collection_step=entity_collection_step,
                    pending_entities=pending_entities
                )
        except Exception as e:
            logger.warning("Failed to load from external storage, falling back to state", error=str(e))

    # Fallback to state ONLY if external storage returned nothing
    if not entity_collection_step and not current_sub_intent:
        entity_collection_step = state.get("entity_collection_step")
        pending_entities = state.get("pending_entities", {})
        current_sub_intent = state.get("current_sub_intent")

        logger.debug(
            "Fallback to state",
            session_id=session_id,
            entity_collection_step=entity_collection_step,
            current_sub_intent=current_sub_intent
        )

    # === ENTITY COLLECTION CONTEXT (HIGHEST PRIORITY) ===
    # If we're in the middle of collecting an entity, this is THE MOST IMPORTANT context
    if entity_collection_step:
        context_parts.append("╔═══ ACTIVE ENTITY COLLECTION ═══╗")
        context_parts.append(f"COLLECTING: {entity_collection_step}")
        context_parts.append(f"CURRENT INTENT: {current_sub_intent}")
        context_parts.append(f"CRITICAL: User is responding to our question about {entity_collection_step}")
        context_parts.append(f"CRITICAL: Continue the {current_sub_intent} flow, do NOT start a new intent!")

        # Include pending entities for context
        if pending_entities:
            pending_str = ", ".join([f"{k}={v}" for k, v in pending_entities.items()])
            context_parts.append(f"Already collected: {pending_str}")

            # Special handling for quantity collection
            if entity_collection_step == "quantity" and pending_entities.get("item_name"):
                context_parts.append(f"⚠️ WAITING FOR QUANTITY for item: {pending_entities.get('item_name')}")
                context_parts.append("If user says a number or 'i need X', classify as manage_cart with action=add and quantity=X")

        context_parts.append("╚═════════════════════════════════╝")
        context_parts.append("")  # Blank line for separation

    # === CONVERSATION CONTEXT ===
    # 1. Conversation Summary (Long-term context)
    conversation_summary = state.get("conversation_summary")
    if conversation_summary:
        context_parts.append("=== CONVERSATION SUMMARY ===")
        context_parts.append(conversation_summary)
        context_parts.append("="*30)
        context_parts.append("")

    # 2. Recent Message History (Immediate context)
    # Get last 10 messages to understand the flow and user intent
    messages = state.get("messages", [])
    if messages:
        # Get last 10 messages (excluding current user message if it's already appended)
        # Note: The current message might already be in state["messages"]
        recent_msgs = messages[-11:-1] if len(messages) >= 11 else messages[:-1]
        
        if recent_msgs:
            history_str = ""
            for msg in recent_msgs:
                role = "User" if isinstance(msg, HumanMessage) else "Bot"
                content = msg.content
                history_str += f"{role}: {content}\n"
            
            context_parts.append("=== RECENT HISTORY ===")
            context_parts.append(history_str.strip())
            context_parts.append("="*30)
            context_parts.append("")

    # 3. Last displayed items (CRITICAL for "selection by repetition")
    last_displayed_items = state.get("last_displayed_items", [])
    if last_displayed_items:
        # Show top 5 items to give LLM context on what user is seeing
        item_names = [f"{i.get('name')} (₹{i.get('price', 'N/A')})" for i in last_displayed_items[:5]]
        context_parts.append(f"User sees these items: {', '.join(item_names)}")
        context_parts.append("NOTE: If user repeats one of these names WITHOUT saying 'I want' or 'Order', it is AMBIGUOUS. Classify as manage_cart with action='ambiguous_select'.")
        context_parts.append("")
    
    # Cart context
    cart_items = state.get("cart_items", [])
    cart_validated = state.get("cart_validated", False)
    if cart_items:
        cart_subtotal = state.get("cart_subtotal", 0.0)
        context_parts.append(f"Cart has {len(cart_items)} items (total: ₹{cart_subtotal})")
        if cart_validated:
            context_parts.append("Cart validated - ready for checkout")
    else:
        context_parts.append("Cart is EMPTY")

    # Existing order context (for "change order" disambiguation)
    draft_order_id = state.get("draft_order_id")
    if draft_order_id:
        context_parts.append(f"Draft order exists: {draft_order_id}")
        context_parts.append("IMPORTANT: 'Change order' likely means cart operations (manage_cart)")

    # Auth context
    if state.get("user_id"):
        context_parts.append(f"User authenticated: {state.get('user_name', 'Guest')}")
    else:
        context_parts.append("User NOT authenticated")

    # Order type context
    order_type = state.get("order_type")
    if order_type:
        context_parts.append(f"Order type: {order_type}")

    context = "\n".join(context_parts) if context_parts else "No context"

    # System prompt for classification
    system_prompt = """You are a food ordering intent classifier.

Your task: Classify the user's message into ONE of 5 sub-intents and extract entities.

## Sub-Intents:

1. **browse_menu** - Navigate menu structure (categories, full menu)
   Examples: "show menu", "what categories do you have", "what's in appetizers"
   Entities: category_name (optional)

2. **discover_items** - ONLY for explicit searching/filtering with browse keywords
   Use this ONLY when user has explicit browse/search keywords.

   **MUST have one of these keywords to be discover_items:**
   - "show me", "what is", "search", "find", "tell me about", "what's available"
   - "recommend", "suggest", "options", "available"

   Search/Filter Examples: "show me vegetarian options", "what's available for dinner", "search for spicy food"
   Info/Query Examples: "what is butter chicken", "tell me about biryani", "what dishes do you have"
   Recommendation Examples: "recommend something", "what do you suggest", "what's good", "surprise me"
   Filter Examples: "items under ₹300", "show veg items", "find non-veg starters"

   **NOT discover_items:**
   - Just an item name like "veg roll", "biryani", "naan" → This is manage_cart (ordering)
   - "veg roll please", "biryani for me" → This is manage_cart (ordering)

   Entities: search_query, dietary_restrictions, price_range, meal_timing

3. **manage_cart** - Add/remove/update cart items OR ORDERING items by name

   CRITICAL: If user says ANY item name (with or without ordering keywords), this is manage_cart with action="add"

   **MANDATORY RULES FOR ORDERING:**
   1. ALWAYS include "action": "add" in entities for ordering
   2. DO NOT default quantity to 1 - ONLY include quantity if user explicitly says a number
   3. If user doesn't specify quantity → add "quantity" to missing_entities

   **Item Name WITHOUT Quantity (missing_entities: ["quantity"]):**
   - "veg roll" → entities: {"action": "add", "item_name": "veg roll"}, missing_entities: ["quantity"]
   - "ghee rice" → entities: {"action": "add", "item_name": "ghee rice"}, missing_entities: ["quantity"]
   - "biryani" → entities: {"action": "add", "item_name": "biryani"}, missing_entities: ["quantity"]
   - "I want butter chicken" → entities: {"action": "add", "item_name": "butter chicken"}, missing_entities: ["quantity"]
   - "give me gobi manchurian" → entities: {"action": "add", "item_name": "gobi manchurian"}, missing_entities: ["quantity"]

   **Item Name WITH Quantity (missing_entities: []):**
   - "2 veg rolls" → entities: {"action": "add", "item_name": "veg roll", "quantity": 2}, missing_entities: []
   - "I need 3 biryani" → entities: {"action": "add", "item_name": "biryani", "quantity": 3}, missing_entities: []
   - "get me 2 naan" → entities: {"action": "add", "item_name": "naan", "quantity": 2}, missing_entities: []

   **Quantity Response (when collecting quantity):**
   - "2" → entities: {"action": "add", "quantity": 2}, missing_entities: []
   - "yes 3" → entities: {"action": "add", "quantity": 3}, missing_entities: []
   - "i need 1" → entities: {"action": "add", "quantity": 1}, missing_entities: []

   **Cart Management Examples:**
   - "add butter chicken" → entities: {"action": "add", "item_name": "butter chicken"}, missing_entities: ["quantity"]
   - "remove item 2" → entities: {"action": "remove", "item_index": 2}, missing_entities: []
   - "change quantity to 3" → entities: {"action": "update", "quantity": 3}, missing_entities: []
   - "show cart", "view cart" → entities: {"action": "view"}, missing_entities: []
   - "clear cart" → entities: {"action": "clear"}, missing_entities: []

   **Item Selection by Ordinals (CRITICAL - Extract item_index):**
   - "add first one" → entities: {"action": "add", "item_index": 1}, missing_entities: ["quantity"]
   - "the first one" → entities: {"action": "add", "item_index": 1}, missing_entities: ["quantity"]
   - "add the second one" → entities: {"action": "add", "item_index": 2}, missing_entities: ["quantity"]
   - "I want the third one" → entities: {"action": "add", "item_index": 3}, missing_entities: ["quantity"]
   - "remove the first one" → entities: {"action": "remove", "item_index": 1}, missing_entities: []
   - "add item 1" → entities: {"action": "add", "item_index": 1}, missing_entities: ["quantity"]
   - "add item number 2" → entities: {"action": "add", "item_index": 2}, missing_entities: ["quantity"]

   **Multi-item Examples:**
   - "I'll take 3 no:2 and 5 no:3" → items_to_add list
   - "add 2 item 1 and 3 item 5" → items_to_add list

   **Key ordering indicators:** "order", "want", "need", "give me", "get me", "I'll have", "I'll take", OR just an item name

   Sub-actions: add, remove, update, view, clear
   Entities: action (REQUIRED), item_name or item_index, quantity (ONLY if user specifies)
   Special: For multiple items, use items_to_add list (see below)

4. **validate_order** - Validate cart before checkout (ONLY when user explicitly signals readiness)
   Examples: "checkout", "I'm ready to order", "place my order", "confirm my order"
   NOT THIS: "I want to order food" (that's discovery/browse - they're STARTING, not finishing)
   CRITICAL: User must explicitly signal they are DONE selecting and ready to checkout
   Context matters with the word "order":
   - "I want to ORDER food" = starting the process → discover_items
   - "Ready to ORDER" = finishing the process → validate_order
   Entities: None (system triggers validation)

5. **execute_checkout** - Execute checkout after validation
   Examples: "yes, place it" (after validation), "confirm order"
   Entities: order_type (dine_in or takeout) - REQUIRED

## Entity Extraction Rules:

- **item_name**: Dish name (e.g., "butter chicken", "naan")
- **quantity**: Number (default: 1 if not specified)
- **category_name**: Menu category (e.g., "appetizers", "main course")
- **dietary_restrictions**: List ["vegetarian", "vegan", "gluten-free"]
- **search_query**: Free text search term
- **price_range**: {"min": 0, "max": 500} or just {"max": 300}
- **order_type**: "dine_in" or "takeout" (REQUIRED for execute_checkout)
- **action**: For manage_cart - "add", "remove", "update", "view", "clear", "ambiguous_select"
- **item_index**: For cart operations like "remove item 2" (1-indexed)
  - Also extract from ordinal patterns: "first one" = 1, "second one" = 2, "third one" = 3, etc.
  - "the first one", "add first one", "I want the second one" → extract item_index
- **items_to_add**: For MULTIPLE items in one message (list of dicts)

### Multiple Item Pattern (IMPORTANT):

When user specifies MULTIPLE items with quantities by index number:

**Patterns to recognize:**
- "3 no:2 and 5 no:3" = 3 of item #2, 5 of item #3
- "2 item 1 and 3 item 5" = 2 of item #1, 3 of item #5
- "I'll take item 2, item 3, and 4 of item 5"
- "add 3x item 2 and 2x item 4"

**Extract as items_to_add list:**
```json
{
  "action": "add",
  "items_to_add": [
    {"item_index": 2, "quantity": 3},
    {"item_index": 3, "quantity": 5}
  ]
}
```

**Key indicators:**
- Multiple numbers mentioned with "and" or commas
- Pattern: [quantity] [no:|item|of|x] [number]
- Numbers after "no:", "item", or quantity indicators

**Do NOT use items_to_add for single items** - use item_index and quantity instead

## Missing Entities:

If an intent REQUIRES an entity but it's not in the message or context:
- Add to "missing_entities" list
- System will ask user for it

Example:
  Message: "checkout"
  Intent: execute_checkout
  Missing: ["order_type"]  System asks: "Dine-in or takeout?"

## Context Awareness:

Use the provided context to:
- Know what's in cart (empty vs has items)
- Know if cart is validated (validated = ready for checkout)
- Know if draft order exists ("change order" = manage_cart, not new order)
- Know if user is authenticated
- Know if we're collecting a specific entity (multi-turn)

## CRITICAL: Entity Collection Response Handling

**When context shows "COLLECTING ENTITY: quantity" and "WAITING FOR QUANTITY":**

The user is responding to "How many would you like?" - ANY number response should be classified as:
- Sub-intent: manage_cart
- Action: add
- Quantity: <the number they said>
- item_name is NOT needed (already in pending_entities)

**Examples when collecting quantity:**
- "1" → manage_cart, action=add, quantity=1
- "2" → manage_cart, action=add, quantity=2
- "i need 3" → manage_cart, action=add, quantity=3
- "yes 2" → manage_cart, action=add, quantity=2
- "make it 5" → manage_cart, action=add, quantity=5
- "just one" → manage_cart, action=add, quantity=1
- "two please" → manage_cart, action=add, quantity=2

**DO NOT classify these as discover_items when collecting quantity!**

**Edge Case Disambiguation:**
1. "change my order" with draft_order → manage_cart (modify current cart)
2. "I want to order" (no item name) with empty cart → discover_items (generic starting)
3. "I want to order [ITEM NAME]" → manage_cart action=add (specific item)
4. "ready to order" with items in cart → validate_order (finishing)
5. "add another" with items in cart → manage_cart (adding more)
6. "show me biryani" → discover_items (has "show me" = browsing)
7. "I want biryani" or "give me biryani" → manage_cart action=add (ordering)
8. Just a number like "3" or "yes 3" after seeing menu → manage_cart action=add (quantity confirmation)
9. "veg roll" (just item name, no keywords) → manage_cart action=add (item selection)
10. "biryani please" → manage_cart action=add (polite item selection)
11. "the paneer tikka" → manage_cart action=add (item selection with article)

**ORDERING vs BROWSING - Key Distinction:**
- BROWSING (discover_items): MUST have browse keywords like "show me", "what is", "search", "find", "tell me about"
- ORDERING (manage_cart): Everything else with an item name, including:
  - Just item name: "veg roll", "biryani" → manage_cart (action=add)
  - With ordering words: "I want X", "give me X", "I need X" → manage_cart (action=add)
  - Polite form: "veg roll please", "biryani for me" → manage_cart (action=add)

**DEFAULT RULE:** If user says something that looks like a food item name and there are NO browse keywords, treat it as manage_cart (action=add)

## Output Format:

Return VALID JSON following this schema:
{
  "sub_intent": "browse_menu" | "discover_items" | "manage_cart" | "validate_order" | "execute_checkout",
  "confidence": 0.95,
  "entities": {
    "item_name": "butter chicken",
    "quantity": 2
  },
  "missing_entities": ["order_type"],
  "reasoning": "User wants to add item to cart, mentioned butter chicken and quantity 2"
}

CRITICAL: Return ONLY valid JSON, no markdown, no explanation."""

    user_prompt = f"""Context:
{context}

User Message: "{user_message}"

Classify intent and extract entities:"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        # Create ManagedChatOpenAI with full failover support
        llm = ManagedChatOpenAI(
            model=config.INTENT_CLASSIFICATION_MODEL,
            temperature=0.1,  # Low temp for classification
            agent_name="sub_intent_classifier"
        )

        # Use structured output with Pydantic model (eliminates JSON parsing errors)
        # This uses ManagedChatOpenAI with automatic round-robin and failover
        structured_llm = llm.with_structured_output(
            SubIntentClassification,
            method="function_calling"
        )

        # Invoke with type-safe structured response and full failover
        classification: SubIntentClassification = await structured_llm.ainvoke_structured(messages)

        logger.info(
            "Sub-intent classified (structured output)",
            session_id=session_id,
            sub_intent=classification.sub_intent,
            confidence=classification.confidence,
            entities=classification.entities,
            missing=classification.missing_entities
        )

        return classification

    except Exception as e:
        logger.error(
            "Sub-intent classification failed",
            error=str(e),
            session_id=session_id,
            exc_info=True
        )

        # Fallback: Try to infer from keywords
        return _fallback_classification(user_message, state)


def _fallback_classification(
    user_message: str,
    state: FoodOrderingState
) -> SubIntentClassification:
    """
    Fallback classification using keyword matching.

    Used when LLM fails to return valid JSON.
    """
    message_lower = user_message.lower()

    # PRIORITY 1: Check if we're collecting a specific entity (multi-turn)
    entity_collection_step = state.get("entity_collection_step")
    pending_entities = state.get("pending_entities", {})

    if entity_collection_step == "quantity":
        # User is responding to "How many would you like?"
        # Try to extract number from message
        import re
        number_words = {
            "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
            "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
        }

        # Try numeric extraction first
        numbers = re.findall(r'\d+', user_message)
        if numbers:
            quantity = int(numbers[0])
            return SubIntentClassification(
                sub_intent="manage_cart",
                confidence=0.9,
                entities={"action": "add", "quantity": quantity},
                missing_entities=[],
                reasoning=f"Fallback: Quantity response detected ({quantity}) during entity collection"
            )

        # Try word-based numbers
        for word, num in number_words.items():
            if word in message_lower:
                return SubIntentClassification(
                    sub_intent="manage_cart",
                    confidence=0.9,
                    entities={"action": "add", "quantity": num},
                    missing_entities=[],
                    reasoning=f"Fallback: Quantity word '{word}' detected during entity collection"
                )

    # Checkout keywords
    if any(word in message_lower for word in ["checkout", "place order", "ready to order"]):
        cart_validated = state.get("cart_validated", False)
        order_type = state.get("order_type")
        if cart_validated:
            return SubIntentClassification(
                sub_intent="execute_checkout",
                confidence=0.7,
                entities={},
                missing_entities=["order_type"] if not order_type else [],
                reasoning="Fallback: Checkout keywords detected"
            )
        else:
            return SubIntentClassification(
                sub_intent="validate_order",
                confidence=0.7,
                entities={},
                missing_entities=[],
                reasoning="Fallback: First checkout mention - validate first"
            )

    # Ordering intent keywords (I want X, give me X, I need X, order X)
    ordering_patterns = ["i want", "i need", "give me", "get me", "i'll have", "i'll take", "order"]
    if any(pattern in message_lower for pattern in ordering_patterns):
        # Check if there's an item name (not just "I want to order" generically)
        generic_phrases = ["i want to order food", "i want to order", "order food", "order something"]
        if not any(phrase in message_lower for phrase in generic_phrases):
            # Extract potential item name (words after ordering keyword)
            return SubIntentClassification(
                sub_intent="manage_cart",
                confidence=0.7,
                entities={"action": "add"},
                missing_entities=["item_name"] if len(user_message.split()) <= 3 else [],
                reasoning="Fallback: Ordering intent detected (want/need/give me)"
            )

    # Cart management keywords
    if any(word in message_lower for word in ["add", "remove", "delete", "update", "change", "cart"]):
        action = "add" if "add" in message_lower else \
                 "remove" if any(w in message_lower for w in ["remove", "delete"]) else \
                 "update" if any(w in message_lower for w in ["update", "change"]) else \
                 "view" if "cart" in message_lower else "add"

        return SubIntentClassification(
            sub_intent="manage_cart",
            confidence=0.6,
            entities={"action": action},
            missing_entities=["item_name"] if action == "add" else [],
            reasoning="Fallback: Cart action keywords detected"
        )

    # Browse keywords
    if any(word in message_lower for word in ["menu", "categories", "show", "list"]):
        return SubIntentClassification(
            sub_intent="browse_menu",
            confidence=0.6,
            entities={},
            missing_entities=[],
            reasoning="Fallback: Browse keywords detected"
        )

    # Discovery keywords (MUST have explicit search/filter keywords)
    discovery_keywords = ["vegetarian", "vegan", "search", "find", "spicy", "what is", "tell me", "show me", "available", "options"]
    if any(word in message_lower for word in discovery_keywords):
        return SubIntentClassification(
            sub_intent="discover_items",
            confidence=0.6,
            entities={"search_query": user_message},
            missing_entities=[],
            reasoning="Fallback: Discovery keywords detected"
        )

    # DEFAULT: Treat as item name selection (ordering intent)
    # If message is 1-4 words and no browse keywords, assume it's an item name
    word_count = len(user_message.split())
    if 1 <= word_count <= 5:
        # Clean up common polite words to get item name
        item_name = message_lower.replace("please", "").replace("thanks", "").replace("the", "").strip()
        return SubIntentClassification(
            sub_intent="manage_cart",
            confidence=0.6,
            entities={"action": "add", "item_name": item_name},
            missing_entities=["quantity"],  # Always ask for quantity when just item name
            reasoning="Fallback: Short message without browse keywords, treating as item selection"
        )

    # Very long message with no keywords - default to browse
    return SubIntentClassification(
        sub_intent="browse_menu",
        confidence=0.4,
        entities={},
        missing_entities=[],
        reasoning="Fallback: No clear intent, defaulting to browse"
    )


__all__ = ["classify_sub_intent"]
