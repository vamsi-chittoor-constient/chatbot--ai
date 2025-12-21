# DETERMINISTIC RULES DOCUMENTATION
**Complete Guide to Rule-Based Logic in the Restaurant AI System**

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Deterministic vs AI-Powered Decision Making](#deterministic-vs-ai)
3. [Intent Routing Rules](#intent-routing)
4. [Sub-Intent Routing Rules](#sub-intent-routing)
5. [Guardrail System (2-Tier)](#guardrails)
6. [Entity Validation Rules](#entity-validation)
7. [Action Routing Rules (Sub-Agent Level)](#action-routing)
8. [Business Logic Rules](#business-rules)
9. [State Transition Rules](#state-transitions)
10. [Priority-Based Tool Selection](#priority-selection)
11. [Complete Rule Execution Flow](#execution-flow)
12. [Rule Configuration & Customization](#configuration)

---

## 1. OVERVIEW {#overview}

### What are Deterministic Rules?

**Deterministic Rules** are predefined, non-AI decision-making logic that produces **consistent, predictable outputs** for the same inputs. Unlike LLM-based decisions (which may vary), deterministic rules guarantee the same result every time.

### Why Use Deterministic Rules?

**Benefits**:
1. **Predictability** - Same input → Same output (every time)
2. **Performance** - No LLM calls = faster execution (milliseconds vs seconds)
3. **Cost Efficiency** - No API costs for rule-based logic
4. **Debuggability** - Easy to trace and understand decisions
5. **Safety** - Critical business logic can't be bypassed by creative prompts
6. **Compliance** - Ensures regulatory requirements are always enforced

**Use Cases in Restaurant AI**:
- Routing requests to the correct agent
- Enforcing business rules (min order amount, operating hours)
- Validating cart state before checkout
- Preventing invalid operations (modifying locked cart)
- Priority-based tool selection

---

## 2. DETERMINISTIC VS AI-POWERED DECISION MAKING {#deterministic-vs-ai}

### Hybrid Architecture

The system uses **both** deterministic rules and AI-powered decisions:

```
┌─────────────────────────────────────────────────────────────┐
│                    DECISION LAYER MAP                        │
└─────────────────────────────────────────────────────────────┘

LEVEL 1: Intent Classification
├─ AI-POWERED (LLM)
│  Input: User message
│  Output: food_ordering, table_booking, general_inquiry
│  Why: Natural language understanding required
│
└─ Example: "I want butter chicken" → food_ordering

LEVEL 2: Agent Routing
├─ DETERMINISTIC (Rules)
│  Input: Intent string
│  Output: Agent function
│  Why: Simple mapping, no ambiguity
│
└─ Example: food_ordering → food_ordering_agent

LEVEL 3: Sub-Intent Classification
├─ AI-POWERED (LLM)
│  Input: User message + state context
│  Output: browse_menu, discover_items, manage_cart, etc.
│  Why: Context-aware understanding needed
│
└─ Example: "Add butter chicken" → manage_cart

LEVEL 4: Sub-Agent Routing
├─ DETERMINISTIC (Rules)
│  Input: Sub-intent string
│  Output: Sub-agent function
│  Why: Simple mapping, no ambiguity
│
└─ Example: manage_cart → cart_management_agent

LEVEL 5: Guardrails
├─ DETERMINISTIC (Rules)
│  Input: Sub-intent + state fields
│  Output: allow/block/redirect
│  Why: Safety-critical, must be consistent
│
└─ Example: cart_locked=true + action=add → BLOCK

LEVEL 6: Entity Validation
├─ DETERMINISTIC (Rules)
│  Input: Entities + sub-intent
│  Output: valid/missing fields
│  Why: Required field checking is rule-based
│
└─ Example: execute_checkout requires order_type

LEVEL 7: Action Routing (within sub-agent)
├─ DETERMINISTIC (Rules)
│  Input: Action string
│  Output: Handler function
│  Why: Simple mapping
│
└─ Example: action=add → _handle_add_to_cart

LEVEL 8: Tool Selection
├─ DETERMINISTIC (Priority Rules) OR AI-POWERED (ReAct)
│  Input: Entities + context
│  Output: Tool to execute
│  Why: Can be rule-based OR intelligent
│
└─ Example: search_query present → SemanticMenuSearchTool
```

### Decision Matrix

| Decision Type | Method | Speed | Cost | Consistency | Use When |
|---------------|--------|-------|------|-------------|----------|
| **Intent Classification** | LLM | Slow (1-2s) | High | Variable | Natural language understanding needed |
| **Agent Routing** | Rules | Fast (<1ms) | None | 100% | Simple string mapping |
| **Sub-Intent Classification** | LLM | Slow (1-2s) | High | Variable | Context-aware understanding needed |
| **Sub-Agent Routing** | Rules | Fast (<1ms) | None | 100% | Simple string mapping |
| **Guardrails** | Rules | Fast (<1ms) | None | 100% | Safety-critical checks |
| **Entity Validation** | Rules | Fast (<1ms) | None | 100% | Required field validation |
| **Action Routing** | Rules | Fast (<1ms) | None | 100% | Simple function dispatch |
| **Tool Selection** | Rules OR LLM | Fast/Slow | None/High | 100%/Variable | Depends on mode |

---

## 3. INTENT ROUTING RULES {#intent-routing}

### Main Intent Router

**Location**: `app/orchestration/graph.py`

**Purpose**: Route to top-level domain agents based on intent

**Rule Type**: Simple string-to-function mapping

**Routing Table**:

```python
INTENT_ROUTING_TABLE = {
    "food_ordering": food_ordering_agent_node,
    "table_booking": table_booking_agent_node,
    "general_inquiry": general_inquiry_agent_node,
    "authentication": authentication_agent_node,
    "payment": payment_agent_node,
    "order_status": order_status_agent_node,
    "fallback": fallback_agent_node
}
```

**Execution Logic**:

```python
def route_to_agent(state: AgentState) -> str:
    """
    DETERMINISTIC: Route based on current_intent field

    No LLM involved - pure rule-based routing
    """
    current_intent = state.get("current_intent", "fallback")

    # Rule 1: If intent is in routing table, return it
    if current_intent in INTENT_ROUTING_TABLE:
        return current_intent

    # Rule 2: Otherwise, route to fallback
    return "fallback"
```

**Examples**:

```
Input: current_intent = "food_ordering"
Output: "food_ordering"
Agent: food_ordering_agent_node
─────────────────────────────────────────
Input: current_intent = "table_booking"
Output: "table_booking"
Agent: table_booking_agent_node
─────────────────────────────────────────
Input: current_intent = "unknown_intent"
Output: "fallback"
Agent: fallback_agent_node
```

**Performance**: <1ms (dictionary lookup)

---

## 4. SUB-INTENT ROUTING RULES {#sub-intent-routing}

### Food Ordering Sub-Intent Router

**Location**: `app/agents/food_ordering/router.py`

**Purpose**: Route to specialized sub-agents within food ordering domain

**Rule Type**: Registry pattern with string-to-function mapping

**Routing Registry**:

```python
# Global registry (populated at module initialization)
_AGENT_REGISTRY: Dict[str, Callable] = {}

def register_agent(sub_intent: str, agent_function: Callable):
    """
    Register a sub-agent for a specific sub-intent

    DETERMINISTIC: Simple dictionary insertion
    """
    _AGENT_REGISTRY[sub_intent] = agent_function
    logger.info(f"Registered agent: {sub_intent} -> {agent_function.__name__}")

# Registration happens on module import
register_agent("browse_menu", menu_browsing_agent)
register_agent("discover_items", menu_discovery_agent)
register_agent("manage_cart", cart_management_agent)
register_agent("validate_order", checkout_validator_agent)
register_agent("execute_checkout", checkout_executor_agent)
```

**Routing Logic**:

```python
def route_to_agent(classification: SubIntentClassification) -> Callable:
    """
    DETERMINISTIC: Route based on sub_intent string

    No LLM involved - pure rule-based routing
    """
    sub_intent = classification.sub_intent

    # Rule 1: Look up in registry
    if sub_intent in _AGENT_REGISTRY:
        agent_function = _AGENT_REGISTRY[sub_intent]
        logger.info(f"Routing to: {agent_function.__name__}")
        return agent_function

    # Rule 2: If not found, raise error
    raise ValueError(f"No agent registered for sub-intent: {sub_intent}")
```

**Complete Routing Table**:

| Sub-Intent | Agent Function | Purpose |
|------------|----------------|---------|
| `browse_menu` | `menu_browsing_agent` | Navigate menu structure |
| `discover_items` | `menu_discovery_agent` | Search, filter, recommend |
| `manage_cart` | `cart_management_agent` | Add, remove, update cart |
| `validate_order` | `checkout_validator_agent` | Validate cart before checkout |
| `execute_checkout` | `checkout_executor_agent` | Create draft order |

**Examples**:

```
Input: sub_intent = "browse_menu"
Output: menu_browsing_agent
─────────────────────────────────────────
Input: sub_intent = "manage_cart"
Output: cart_management_agent
─────────────────────────────────────────
Input: sub_intent = "invalid_intent"
Output: ValueError raised
```

**Performance**: <1ms (dictionary lookup)

---

## 5. GUARDRAIL SYSTEM (2-TIER) {#guardrails}

### Overview

**Location**: `app/agents/food_ordering/graph.py` → `apply_state_guardrails()`

**Purpose**: State-based safety gates to prevent invalid operations

**Architecture**: 2-tier system

```
┌─────────────────────────────────────────────────────────────┐
│                    GUARDRAIL TIERS                           │
└─────────────────────────────────────────────────────────────┘

TIER 1: SOFT GUIDES (Helpful Redirects)
├─ Purpose: User experience optimization
├─ Behavior: Redirect to better flow
├─ Action: Return helpful suggestion (success=True)
├─ Example: Empty cart checkout → Suggest browsing
└─ User Impact: Helpful nudge, not blocking

TIER 2: HARD BLOCKS (Safety Gates)
├─ Purpose: Prevent invalid/unsafe operations
├─ Behavior: Block operation completely
├─ Action: Return error (success=False)
├─ Example: Modify locked cart → BLOCKED
└─ User Impact: Cannot proceed
```

### Tier 1: Soft Guides

**Rule Set**:

```python
def apply_soft_guides(
    sub_intent: str,
    state: FoodOrderingState
) -> Optional[Dict[str, Any]]:
    """
    TIER 1: Helpful redirects (not strict blocks)
    """

    # RULE SG-1: Empty Cart Checkout
    # ─────────────────────────────────────────────────────
    # Condition: User tries to checkout with empty cart
    # Action: Suggest browsing menu
    # Severity: SOFT (suggestion, not block)

    if sub_intent == "validate_order":
        cart_items = state.get("cart_items", [])
        cart_item_count = len(cart_items)

        if cart_item_count == 0:
            logger.info("Soft guide: Empty cart checkout → browse menu")
            return {
                "action": "empty_cart_redirect",
                "success": True,  # ← Not an error
                "data": {
                    "message": "Your cart is empty! Would you like to browse our menu?",
                    "suggestion": "browse_menu",
                    "cart_item_count": 0
                },
                "context": {
                    "guardrail_type": "soft_guide",
                    "original_intent": "validate_order",
                    "redirect_reason": "empty_cart"
                }
            }

    # No soft guides triggered
    return None
```

**Soft Guide Rules**:

| Rule ID | Condition | Action | User Experience |
|---------|-----------|--------|-----------------|
| **SG-1** | `validate_order` + empty cart | Suggest browse_menu | "Your cart is empty! Would you like to browse our menu?" |
| **SG-2** | First-time user + no preferences | Suggest preference collection | "Let me learn your preferences to give better recommendations" |
| **SG-3** | High cart value + no authentication | Suggest login for rewards | "Sign in to earn points on this order!" |

### Tier 2: Hard Blocks

**Rule Set**:

```python
def apply_hard_blocks(
    sub_intent: str,
    state: FoodOrderingState
) -> Optional[Dict[str, Any]]:
    """
    TIER 2: Safety gates (strict enforcement)
    """

    # RULE HB-1: Locked Cart Modification
    # ─────────────────────────────────────────────────────
    # Condition: Cart is locked AND user tries to modify it
    # Action: BLOCK operation
    # Severity: HARD (cannot proceed)

    if sub_intent == "manage_cart":
        cart_locked = state.get("cart_locked", False)
        action = entities.get("action")

        # Block all modification actions on locked cart
        if cart_locked and action in ["add", "remove", "update", "clear"]:
            logger.warning(
                "Hard block: Cart modification blocked (cart locked)",
                action=action
            )
            return {
                "action": "cart_locked",
                "success": False,  # ← This is an error
                "data": {
                    "message": "Your cart is locked for checkout. Please complete your order or cancel to make changes.",
                    "cart_locked": True
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "modify_locked_cart",
                    "attempted_action": action
                },
                "guardrail_violations": [f"Attempted to {action} on locked cart"]
            }

    # RULE HB-2: Checkout Without Validation
    # ─────────────────────────────────────────────────────
    # Condition: User tries to checkout without validating cart
    # Action: BLOCK operation
    # Severity: HARD (must validate first)

    if sub_intent == "execute_checkout":
        cart_validated = state.get("cart_validated", False)

        if not cart_validated:
            logger.warning("Hard block: Checkout blocked (cart not validated)")
            return {
                "action": "validation_required",
                "success": False,
                "data": {
                    "message": "Let me validate your cart first before we complete your order.",
                    "requires_validation": True
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "checkout_without_validation"
                },
                "guardrail_violations": ["Attempted checkout without validation"]
            }

    # RULE HB-3: Checkout Without Authentication (if required)
    # ─────────────────────────────────────────────────────
    # Condition: must_authenticate=True AND user_id=None
    # Action: BLOCK operation
    # Severity: HARD (must authenticate first)

    if sub_intent == "execute_checkout":
        must_authenticate = state.get("must_authenticate", False)
        user_authenticated = state.get("user_id") is not None

        if must_authenticate and not user_authenticated:
            logger.warning("Hard block: Checkout blocked (authentication required)")
            return {
                "action": "authentication_required",
                "success": False,
                "data": {
                    "message": "I'll need your phone number to complete your order.",
                    "requires_auth": True
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "checkout_without_auth"
                },
                "guardrail_violations": ["Attempted checkout without authentication"]
            }

    # No hard blocks triggered
    return None
```

**Hard Block Rules**:

| Rule ID | Condition | Violation | User Experience |
|---------|-----------|-----------|-----------------|
| **HB-1** | `manage_cart` + `cart_locked=True` + modify action | Modify locked cart | "Your cart is locked for checkout. Please complete your order or cancel to make changes." |
| **HB-2** | `execute_checkout` + `cart_validated=False` | Checkout without validation | "Let me validate your cart first before we complete your order." |
| **HB-3** | `execute_checkout` + `must_authenticate=True` + `user_id=None` | Checkout without auth | "I'll need your phone number to complete your order." |
| **HB-4** | `manage_cart` + `cart_item_count > 50` | Exceed max cart size | "You've reached the maximum of 50 items per order." |
| **HB-5** | Any operation + `restaurant_closed=True` | Operation during closed hours | "We're currently closed. Our hours are 9 AM - 10 PM." |

### Execution Order

```python
def apply_state_guardrails(
    classification: SubIntentClassification,
    state: FoodOrderingState,
    session_id: str
) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    Apply guardrails in order: Soft Guides → Hard Blocks

    Returns:
        (should_proceed, override_result)
        - If should_proceed=True: Continue to agent routing
        - If should_proceed=False: Return override_result to user
    """

    # Step 1: Check soft guides first
    soft_guide_result = apply_soft_guides(classification.sub_intent, state)
    if soft_guide_result:
        return False, soft_guide_result

    # Step 2: Check hard blocks
    hard_block_result = apply_hard_blocks(classification.sub_intent, state)
    if hard_block_result:
        return False, hard_block_result

    # Step 3: All guardrails passed
    logger.debug("Guardrails passed", sub_intent=classification.sub_intent)
    return True, None
```

**Examples**:

```
Example 1: Empty Cart Checkout (Soft Guide)
────────────────────────────────────────────
State:
  cart_items: []
  cart_item_count: 0

Sub-Intent: validate_order

Guardrail: SG-1 triggered
Result: Redirect to browse_menu
Response: "Your cart is empty! Would you like to browse our menu?"
Success: True (helpful suggestion)

─────────────────────────────────────────────

Example 2: Modify Locked Cart (Hard Block)
────────────────────────────────────────────
State:
  cart_locked: True
  cart_items: [...]

Sub-Intent: manage_cart
Entities: {"action": "add"}

Guardrail: HB-1 triggered
Result: BLOCKED
Response: "Your cart is locked for checkout. Please complete your order or cancel to make changes."
Success: False (error)

─────────────────────────────────────────────

Example 3: Valid Operation (No Guardrail)
────────────────────────────────────────────
State:
  cart_items: [...]
  cart_locked: False

Sub-Intent: manage_cart
Entities: {"action": "add"}

Guardrail: None triggered
Result: Proceed to agent
Success: Agent executes normally
```

**Performance**: <1ms (simple conditional checks)

---

## 6. ENTITY VALIDATION RULES {#entity-validation}

### Overview

**Location**: `app/agents/food_ordering/entity_validator.py`

**Purpose**: Validate that all required entities are present for each sub-intent

**Rule Type**: Required field mapping + conditional validation

### Entity Requirements by Sub-Intent

**Rule Set**:

```python
# REQUIRED ENTITY RULES
# ────────────────────────────────────────────────────────────

ENTITY_REQUIREMENTS = {
    "browse_menu": {
        "required": [],  # No required entities
        "optional": ["category_name"]
    },

    "discover_items": {
        "required": [],  # At least ONE of optional OR none for recommendations
        "optional": ["search_query", "dietary_restrictions", "price_range"],
        "validation": "at_least_one_or_none"  # Special rule
    },

    "manage_cart": {
        "required": ["action"],  # Always need action
        "optional": ["item_name", "item_id", "item_index", "quantity"],
        "conditional": {
            # If action=add, need item_name AND quantity
            "add": ["item_name", "quantity"],
            # If action=remove, need item_index OR item_id
            "remove": ["item_index|item_id"],  # Either/or
            # If action=update, need item_index AND quantity
            "update": ["item_index", "quantity"],
            # If action=view, no additional fields
            "view": [],
            # If action=clear, no additional fields
            "clear": []
        }
    },

    "validate_order": {
        "required": [],  # Validation uses state, not entities
        "optional": []
    },

    "execute_checkout": {
        "required": ["order_type"],  # Must specify dine_in or takeout
        "optional": ["special_instructions"]
    }
}
```

### Validation Logic

```python
def validate_entities(
    classification: SubIntentClassification,
    state: FoodOrderingState
) -> tuple[bool, List[str], Optional[str]]:
    """
    DETERMINISTIC: Validate entities based on sub-intent rules

    Returns:
        (is_valid, missing_entities, clarification_question)
    """
    sub_intent = classification.sub_intent
    entities = classification.entities

    # Get requirements for this sub-intent
    requirements = ENTITY_REQUIREMENTS.get(sub_intent, {})
    required = requirements.get("required", [])
    conditional = requirements.get("conditional", {})

    # Rule 1: Check required fields
    missing = []
    for field in required:
        if field not in entities or entities[field] is None:
            missing.append(field)

    # Rule 2: Check conditional fields (based on action)
    if conditional and "action" in entities:
        action = entities["action"]
        action_required = conditional.get(action, [])

        for field in action_required:
            # Handle either/or fields (e.g., "item_index|item_id")
            if "|" in field:
                options = field.split("|")
                # Check if at least one option is present
                if not any(opt in entities and entities[opt] is not None for opt in options):
                    missing.append(f"({' or '.join(options)})")
            else:
                # Regular field check
                if field not in entities or entities[field] is None:
                    missing.append(field)

    # Rule 3: If missing fields, generate clarification question
    if missing:
        question = generate_clarification_question(sub_intent, missing, state)
        return False, missing, question

    # All entities valid
    return True, [], None
```

### Clarification Questions

**Rule Set**:

```python
CLARIFICATION_TEMPLATES = {
    "order_type": "Is this for dine-in or takeout?",
    "item_name": "Which item would you like to add?",
    "quantity": "How many would you like?",
    "item_index": "Which item number would you like to remove?",
    "category_name": "Which category would you like to browse?",
    "search_query": "What would you like to search for?",
    "(item_index or item_id)": "Which item would you like to remove?"
}

def generate_clarification_question(
    sub_intent: str,
    missing_entities: List[str],
    state: FoodOrderingState
) -> str:
    """
    DETERMINISTIC: Generate clarification question based on missing entities
    """
    # Rule: Use first missing entity to generate question
    first_missing = missing_entities[0]

    # Look up template
    question = CLARIFICATION_TEMPLATES.get(
        first_missing,
        f"Could you provide {first_missing}?"
    )

    return question
```

### Examples

```
Example 1: Valid Entities
──────────────────────────────────────────────
Sub-Intent: manage_cart
Entities: {"action": "add", "item_name": "butter chicken", "quantity": 2}

Validation:
  Required: ["action"] ✓ Present
  Conditional (action=add): ["item_name", "quantity"] ✓ Both present

Result: VALID
Missing: []
Question: None

─────────────────────────────────────────────

Example 2: Missing Quantity
──────────────────────────────────────────────
Sub-Intent: manage_cart
Entities: {"action": "add", "item_name": "butter chicken"}

Validation:
  Required: ["action"] ✓ Present
  Conditional (action=add): ["item_name", "quantity"]
    - item_name ✓ Present
    - quantity ✗ MISSING

Result: INVALID
Missing: ["quantity"]
Question: "How many would you like?"

─────────────────────────────────────────────

Example 3: Missing Order Type
──────────────────────────────────────────────
Sub-Intent: execute_checkout
Entities: {}

Validation:
  Required: ["order_type"] ✗ MISSING

Result: INVALID
Missing: ["order_type"]
Question: "Is this for dine-in or takeout?"

─────────────────────────────────────────────

Example 4: Either/Or Field
──────────────────────────────────────────────
Sub-Intent: manage_cart
Entities: {"action": "remove", "item_index": 2}

Validation:
  Required: ["action"] ✓ Present
  Conditional (action=remove): ["item_index|item_id"]
    - At least one present ✓ (item_index=2)

Result: VALID
Missing: []
Question: None
```

**Performance**: <1ms (dictionary lookups + list iteration)

---

## 7. ACTION ROUTING RULES (SUB-AGENT LEVEL) {#action-routing}

### Overview

Sub-agents perform **internal action routing** based on entity values (deterministic dispatch).

### Cart Management Agent Actions

**Location**: `app/agents/food_ordering/agents/cart_management/node.py`

**Rule Set**:

```python
def cart_management_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    DETERMINISTIC: Route to action handler based on 'action' entity
    """
    action = entities.get("action", "view")  # Default to view

    # ACTION ROUTING TABLE
    # ─────────────────────────────────────────────────────

    if action == "add":
        # Rule: Add item to cart
        return await _handle_add_to_cart(entities, state, session_id)

    elif action == "remove":
        # Rule: Remove item from cart
        return await _handle_remove_from_cart(entities, state, session_id)

    elif action == "update":
        # Rule: Update item quantity
        return await _handle_update_cart_item(entities, state, session_id)

    elif action == "view":
        # Rule: View cart contents
        return await _handle_view_cart(entities, state, session_id)

    elif action == "clear":
        # Rule: Clear entire cart
        return await _handle_clear_cart(entities, state, session_id)

    else:
        # Rule: Unknown action → fallback to view
        logger.warning(f"Unknown action: {action}, falling back to view")
        return await _handle_view_cart(entities, state, session_id)
```

**Routing Table**:

| Action | Handler Function | Tool Used | Purpose |
|--------|------------------|-----------|---------|
| `add` | `_handle_add_to_cart` | `AddToCartTool` | Add item to cart |
| `remove` | `_handle_remove_from_cart` | `RemoveFromCartTool` | Remove item from cart |
| `update` | `_handle_update_cart_item` | `UpdateCartItemTool` | Update item quantity |
| `view` | `_handle_view_cart` | `ViewCartTool` | View cart contents |
| `clear` | `_handle_clear_cart` | `ClearCartTool` | Clear entire cart |
| (unknown) | `_handle_view_cart` | `ViewCartTool` | Fallback to view |

### Menu Browsing Agent Actions

**Location**: `app/agents/food_ordering/agents/menu_browsing/node.py`

**Rule Set**:

```python
def _deterministic_menu_browsing(
    entities: Dict[str, Any],
    state: FoodOrderingState,
    session_id: str,
    category_name: Optional[str]
) -> Dict[str, Any]:
    """
    DETERMINISTIC: Route based on presence of category_name
    """

    # RULE 1: If category_name provided → Browse specific category
    if category_name:
        return await _browse_category(category_name, session_id)

    # RULE 2: No category_name → Show full menu
    else:
        return await _show_full_menu(session_id)
```

**Routing Table**:

| Condition | Handler Function | Tool Used | Result |
|-----------|------------------|-----------|--------|
| `category_name` present | `_browse_category` | `GetMenuItemTool` | Items in category |
| `category_name` absent | `_show_full_menu` | `ListMenuTool` | Full menu structure |

### Menu Discovery Agent (Priority-Based)

**Location**: `app/agents/food_ordering/agents/menu_discovery/node.py`

**Rule Set**:

```python
def _deterministic_menu_discovery(
    entities: Dict[str, Any],
    state: FoodOrderingState,
    session_id: str
) -> Dict[str, Any]:
    """
    DETERMINISTIC: Priority-based tool selection

    Priority Order:
    1. Natural language search (most specific)
    2. Dietary filtering
    3. Price range filtering
    4. Personalized recommendations (fallback)
    """

    search_query = entities.get("search_query")
    dietary_restrictions = entities.get("dietary_restrictions")
    price_range = entities.get("price_range")

    # PRIORITY 1: Natural language search
    if search_query:
        return await _semantic_search(search_query, session_id)

    # PRIORITY 2: Dietary filtering
    if dietary_restrictions:
        return await _dietary_filter(dietary_restrictions, session_id, price_range)

    # PRIORITY 3: Price range filtering
    if price_range:
        return await _price_filter(price_range, session_id)

    # PRIORITY 4: Personalized recommendations (fallback)
    return await _personalized_recommendations(state, session_id)
```

**Priority Table**:

| Priority | Condition | Handler | Tool | Use Case |
|----------|-----------|---------|------|----------|
| **1** | `search_query` present | `_semantic_search` | `SemanticMenuSearchTool` | "something spicy", "chicken curry" |
| **2** | `dietary_restrictions` present | `_dietary_filter` | `SmartDietaryFilterTool` | "vegetarian", "gluten-free" |
| **3** | `price_range` present | `_price_filter` | `PriceRangeMenuTool` | "under ₹300", "between 200 and 400" |
| **4** | No entities (fallback) | `_personalized_recommendations` | `PersonalizedRecommendationTool` | "recommend something", "what's good" |

**Examples**:

```
Example 1: Natural Language Search
───────────────────────────────────────────
Entities: {"search_query": "spicy chicken"}

Priority Check:
  1. search_query present? YES → Use semantic search

Handler: _semantic_search
Tool: SemanticMenuSearchTool
Result: Items matching "spicy chicken"

─────────────────────────────────────────

Example 2: Dietary Filter
───────────────────────────────────────────
Entities: {"dietary_restrictions": ["vegetarian"]}

Priority Check:
  1. search_query present? NO
  2. dietary_restrictions present? YES → Use dietary filter

Handler: _dietary_filter
Tool: SmartDietaryFilterTool
Result: Vegetarian items

─────────────────────────────────────────

Example 3: Multiple Entities (Priority Wins)
───────────────────────────────────────────
Entities: {
    "search_query": "chicken",
    "dietary_restrictions": ["vegetarian"],
    "price_range": {"max": 300}
}

Priority Check:
  1. search_query present? YES → Use semantic search

Handler: _semantic_search (Priority 1 wins)
Tool: SemanticMenuSearchTool
Result: Items matching "chicken"

Note: dietary_restrictions and price_range ignored (lower priority)

─────────────────────────────────────────

Example 4: Fallback to Recommendations
───────────────────────────────────────────
Entities: {}

Priority Check:
  1. search_query present? NO
  2. dietary_restrictions present? NO
  3. price_range present? NO
  4. Fallback → Recommendations

Handler: _personalized_recommendations
Tool: PersonalizedRecommendationTool
Result: Personalized recommendations based on state
```

---

## 8. BUSINESS LOGIC RULES {#business-rules}

### Overview

**Location**: Various validation tools and agents

**Purpose**: Enforce restaurant business rules

### Configuration-Driven Rules

**Storage**: MongoDB `settings` collection

```javascript
// Business Rules Configuration
db.settings.find()

{
  "key": "min_order_amount",
  "value": 200,
  "description": "Minimum order amount in rupees",
  "updated_at": ISODate("2025-01-10")
}

{
  "key": "max_cart_items",
  "value": 50,
  "description": "Maximum items allowed in cart",
  "updated_at": ISODate("2025-01-10")
}

{
  "key": "tax_rate",
  "value": 0.18,
  "description": "GST tax rate (18%)",
  "updated_at": ISODate("2025-01-10")
}

{
  "key": "operating_hours",
  "value": {
    "open": "09:00",
    "close": "22:00",
    "timezone": "Asia/Kolkata"
  },
  "description": "Restaurant operating hours",
  "updated_at": ISODate("2025-01-10")
}

{
  "key": "max_item_quantity",
  "value": 10,
  "description": "Maximum quantity per item",
  "updated_at": ISODate("2025-01-10")
}

{
  "key": "cart_expiry_minutes",
  "value": 30,
  "description": "Cart TTL in minutes",
  "updated_at": ISODate("2025-01-10")
}

{
  "key": "inventory_reservation_minutes",
  "value": 15,
  "description": "Inventory reservation TTL",
  "updated_at": ISODate("2025-01-10")
}
```

### Rule Enforcement

**Location**: `app/tools/database/order_ai_tools.py` → `OrderValidationTool`

```python
async def _execute_impl(self, **kwargs) -> ToolResult:
    """
    DETERMINISTIC: Apply business rules to cart
    """
    session_id = kwargs["session_id"]

    # Get cart from Redis
    cart_data = redis.get(f"cart:{session_id}")

    issues = []

    # RULE BR-1: Minimum Order Amount
    # ─────────────────────────────────────────────────────
    min_order_config = mongo.db.settings.find_one({"key": "min_order_amount"})
    min_order_amount = min_order_config.get("value", 200)

    cart_subtotal = cart_data.get("subtotal", 0)

    if cart_subtotal < min_order_amount:
        issues.append(f"Minimum order amount is ₹{min_order_amount}. Current: ₹{cart_subtotal}")

    # RULE BR-2: Operating Hours
    # ─────────────────────────────────────────────────────
    hours_config = mongo.db.settings.find_one({"key": "operating_hours"})
    operating_hours = hours_config.get("value", {})

    current_time = datetime.now(timezone(operating_hours.get("timezone", "UTC")))
    open_time = datetime.strptime(operating_hours.get("open", "00:00"), "%H:%M").time()
    close_time = datetime.strptime(operating_hours.get("close", "23:59"), "%H:%M").time()

    if not (open_time <= current_time.time() <= close_time):
        issues.append(f"We're currently closed. Our hours are {operating_hours['open']} - {operating_hours['close']}")

    # RULE BR-3: Item Availability
    # ─────────────────────────────────────────────────────
    for item in cart_data.get("items", []):
        item_id = item["item_id"]
        quantity = item["quantity"]

        # Check inventory
        inventory = redis.get(f"inventory:{item_id}")
        available = inventory.get("available_quantity", 0)

        if available < quantity:
            issues.append(f"{item['name']} is out of stock (requested: {quantity}, available: {available})")

    # RULE BR-4: Tax Calculation
    # ─────────────────────────────────────────────────────
    tax_config = mongo.db.settings.find_one({"key": "tax_rate"})
    tax_rate = tax_config.get("value", 0.18)

    tax_amount = cart_subtotal * tax_rate
    total_amount = cart_subtotal + tax_amount

    # Return validation result
    if issues:
        return ToolResult(
            status=ToolStatus.FAILURE,
            data={
                "valid": False,
                "issues": issues
            }
        )

    return ToolResult(
        status=ToolStatus.SUCCESS,
        data={
            "valid": True,
            "cart_summary": {
                "subtotal": cart_subtotal,
                "tax": tax_amount,
                "total": total_amount
            }
        }
    )
```

### Business Rule Table

| Rule ID | Name | Configuration | Enforcement Point | Violation Action |
|---------|------|---------------|-------------------|------------------|
| **BR-1** | Minimum Order Amount | `min_order_amount=200` | Cart Validation | BLOCK checkout |
| **BR-2** | Operating Hours | `operating_hours={open:"09:00", close:"22:00"}` | Cart Validation | BLOCK checkout |
| **BR-3** | Item Availability | (Redis inventory) | Add to Cart, Validation | BLOCK if unavailable |
| **BR-4** | Tax Calculation | `tax_rate=0.18` | Cart Validation | Auto-calculate |
| **BR-5** | Max Cart Items | `max_cart_items=50` | Add to Cart | BLOCK if exceeded |
| **BR-6** | Max Item Quantity | `max_item_quantity=10` | Add to Cart | BLOCK if exceeded |
| **BR-7** | Cart Expiry | `cart_expiry_minutes=30` | Redis TTL | Auto-expire cart |
| **BR-8** | Inventory Reservation | `inventory_reservation_minutes=15` | Redis TTL | Auto-release |

---

## 9. STATE TRANSITION RULES {#state-transitions}

### Overview

**Purpose**: Define valid state transitions (what changes are allowed when)

### Cart State Machine

```
┌─────────────────────────────────────────────────────────────┐
│                  CART STATE MACHINE                          │
└─────────────────────────────────────────────────────────────┘

STATE: EMPTY
├─ cart_items: []
├─ cart_locked: false
├─ cart_validated: false
└─ ALLOWED TRANSITIONS:
    ├─ add → ACTIVE
    └─ (all other operations ignored)

STATE: ACTIVE
├─ cart_items: [...]
├─ cart_locked: false
├─ cart_validated: false
└─ ALLOWED TRANSITIONS:
    ├─ add → ACTIVE (add more items)
    ├─ remove → ACTIVE or EMPTY
    ├─ update → ACTIVE
    ├─ clear → EMPTY
    └─ validate → VALIDATED

STATE: VALIDATED
├─ cart_items: [...]
├─ cart_locked: false
├─ cart_validated: true
└─ ALLOWED TRANSITIONS:
    ├─ add → ACTIVE (invalidates cart)
    ├─ remove → ACTIVE (invalidates cart)
    ├─ update → ACTIVE (invalidates cart)
    ├─ execute_checkout → LOCKED
    └─ clear → EMPTY

STATE: LOCKED
├─ cart_items: [...]
├─ cart_locked: true
├─ cart_validated: true
└─ ALLOWED TRANSITIONS:
    ├─ view → LOCKED (read-only)
    ├─ payment_success → COMPLETED
    ├─ payment_failure → VALIDATED (unlock)
    └─ timeout → VALIDATED (unlock)

STATE: COMPLETED
├─ cart_items: []
├─ cart_locked: false
├─ cart_validated: false
└─ ALLOWED TRANSITIONS:
    └─ (cart cleared, start over)
```

### Transition Rules

**Rule Set**:

```python
# STATE TRANSITION VALIDATION
# ────────────────────────────────────────────────────────────

def validate_cart_transition(
    current_state: FoodOrderingState,
    action: str
) -> tuple[bool, Optional[str]]:
    """
    DETERMINISTIC: Validate if cart transition is allowed

    Returns:
        (is_allowed, rejection_reason)
    """
    cart_items = current_state.get("cart_items", [])
    cart_locked = current_state.get("cart_locked", False)
    cart_validated = current_state.get("cart_validated", False)

    # Determine current state
    if len(cart_items) == 0:
        current = "EMPTY"
    elif cart_locked:
        current = "LOCKED"
    elif cart_validated:
        current = "VALIDATED"
    else:
        current = "ACTIVE"

    # TRANSITION RULES
    # ────────────────────────────────────────────────────────

    # RULE ST-1: LOCKED cart cannot be modified
    if current == "LOCKED" and action in ["add", "remove", "update", "clear"]:
        return False, "Cart is locked for checkout"

    # RULE ST-2: EMPTY cart can only be added to
    if current == "EMPTY" and action in ["remove", "update", "validate"]:
        return False, f"Cannot {action} on empty cart"

    # RULE ST-3: Any modification invalidates validation
    if current == "VALIDATED" and action in ["add", "remove", "update", "clear"]:
        # Allowed, but will reset cart_validated to False
        return True, None

    # RULE ST-4: Cannot checkout without validation
    if action == "execute_checkout" and not cart_validated:
        return False, "Cart must be validated before checkout"

    # All other transitions allowed
    return True, None
```

### State Update Rules

```python
def apply_cart_state_updates(
    action: str,
    current_state: FoodOrderingState,
    action_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    DETERMINISTIC: Apply state updates based on action
    """
    updates = {}

    # RULE SU-1: Modification actions invalidate validation
    if action in ["add", "remove", "update", "clear"]:
        updates["cart_validated"] = False
        updates["validation_issues"] = []

    # RULE SU-2: Clear action resets cart state
    if action == "clear":
        updates["cart_items"] = []
        updates["cart_subtotal"] = 0.0
        updates["cart_item_count"] = 0
        updates["cart_validated"] = False
        updates["cart_locked"] = False

    # RULE SU-3: Execute checkout locks cart
    if action == "execute_checkout":
        updates["cart_locked"] = True

    # RULE SU-4: Payment failure unlocks cart
    if action == "payment_failed":
        updates["cart_locked"] = False

    # RULE SU-5: Payment success clears cart
    if action == "payment_success":
        updates["cart_items"] = []
        updates["cart_subtotal"] = 0.0
        updates["cart_item_count"] = 0
        updates["cart_validated"] = False
        updates["cart_locked"] = False

    return updates
```

---

## 10. PRIORITY-BASED TOOL SELECTION {#priority-selection}

### Overview

Some sub-agents use **priority-based tool selection** instead of AI-powered selection.

### Menu Discovery Priority Rules

**Already covered in Section 7**, but summarized here:

**Priority Order**:
1. **Semantic Search** (if `search_query` present) - Most specific
2. **Dietary Filter** (if `dietary_restrictions` present)
3. **Price Range Filter** (if `price_range` present)
4. **Personalized Recommendations** (fallback)

**Rule**: First matching condition wins, lower priorities ignored

---

## 11. COMPLETE RULE EXECUTION FLOW {#execution-flow}

### End-to-End Rule Application

```
USER MESSAGE: "Add butter chicken to cart"
│
├─→ LEVEL 1: Intent Classification (AI-POWERED)
│   Input: "Add butter chicken to cart"
│   Output: intent = "food_ordering"
│
├─→ LEVEL 2: Intent Routing (RULE: Intent Router)
│   Input: intent = "food_ordering"
│   Rule: INTENT_ROUTING_TABLE lookup
│   Output: food_ordering_agent_node
│
├─→ LEVEL 3: Sub-Intent Classification (AI-POWERED)
│   Input: "Add butter chicken to cart" + FoodOrderingState
│   Output: sub_intent = "manage_cart", entities = {action:"add", item_name:"butter chicken"}
│
├─→ LEVEL 4: Entity Validation (RULE: Entity Requirements)
│   Input: sub_intent="manage_cart", entities={action:"add", item_name:"butter chicken"}
│   Rule: Check required fields for manage_cart + action=add
│   Required: ["action", "item_name", "quantity"]
│   Missing: ["quantity"]
│   Output: INVALID → Ask "How many would you like?"
│
│   [USER RESPONDS: "2"]
│
│   Updated entities: {action:"add", item_name:"butter chicken", quantity:2}
│   Revalidate: ALL REQUIRED PRESENT ✓
│   Output: VALID
│
├─→ LEVEL 5: Guardrail Check (RULE: State Guardrails)
│   Input: sub_intent="manage_cart", state={cart_locked:false, ...}
│
│   Check Soft Guides:
│     SG-1: Empty cart checkout? NO (sub_intent != validate_order)
│     Result: No soft guide triggered
│
│   Check Hard Blocks:
│     HB-1: Locked cart modification? NO (cart_locked=false)
│     Result: No hard block triggered
│
│   Output: PASS (proceed to routing)
│
├─→ LEVEL 6: Sub-Agent Routing (RULE: Sub-Intent Router)
│   Input: sub_intent = "manage_cart"
│   Rule: _AGENT_REGISTRY lookup
│   Output: cart_management_agent
│
├─→ LEVEL 7: Action Routing (RULE: Action Dispatcher)
│   Input: action = "add"
│   Rule: Action routing table
│   Output: _handle_add_to_cart
│
├─→ LEVEL 8: Tool Execution (RULE: Single Tool)
│   Tool: AddToCartTool
│
│   Business Rules Applied:
│     BR-3: Item availability check ✓
│     BR-5: Max cart items check ✓
│     BR-6: Max item quantity check ✓
│
│   Operations:
│     1. Get item from cache (Redis)
│     2. Check inventory (Redis)
│     3. Reserve inventory (Redis)
│     4. Update cart (Redis)
│
│   Output: ToolResult(success=True, cart_updated)
│
├─→ LEVEL 9: State Transition (RULE: State Updates)
│   Input: action="add", current_state={cart_validated:false}
│
│   Rule SU-1: Modification invalidates validation
│   Updates: {cart_validated: false}
│
│   Output: Updated state with new cart items
│
└─→ LEVEL 10: Response Generation (AI-POWERED)
    Input: ActionResult + state
    Output: "Added 2 x Butter Chicken to your cart (₹700)"
```

### Rule Application Summary

| Level | Component | Decision Type | Performance | Cost |
|-------|-----------|---------------|-------------|------|
| 1 | Intent Classification | AI | 1-2s | High |
| 2 | Intent Routing | **RULE** | <1ms | None |
| 3 | Sub-Intent Classification | AI | 1-2s | High |
| 4 | Entity Validation | **RULE** | <1ms | None |
| 5 | Guardrail Check | **RULE** | <1ms | None |
| 6 | Sub-Agent Routing | **RULE** | <1ms | None |
| 7 | Action Routing | **RULE** | <1ms | None |
| 8 | Tool Execution | **RULE** | 10-50ms | None |
| 9 | State Transition | **RULE** | <1ms | None |
| 10 | Response Generation | AI | 1-2s | High |

**Total AI Calls**: 3 (Intent, Sub-Intent, Response)
**Total Rule Evaluations**: 7
**Total Time**: ~3-6 seconds
**Rule Execution Time**: <10ms (negligible)

---

## 12. RULE CONFIGURATION & CUSTOMIZATION {#configuration}

### Where Rules Are Defined

**Rule Location Map**:

| Rule Type | File Location | Format |
|-----------|---------------|--------|
| Intent Routing | `app/orchestration/graph.py` | Python dict |
| Sub-Intent Routing | `app/agents/food_ordering/router.py` | Python registry |
| Guardrails | `app/agents/food_ordering/graph.py` | Python functions |
| Entity Requirements | `app/agents/food_ordering/entity_validator.py` | Python dict |
| Action Routing | `app/agents/food_ordering/agents/*/node.py` | Python if/elif |
| Business Rules | MongoDB `settings` collection | JSON documents |
| State Transitions | `app/agents/food_ordering/state_helpers.py` | Python functions |

### Modifying Rules

**Example 1: Add New Sub-Agent**

```python
# File: app/agents/food_ordering/router.py

# Step 1: Create new sub-agent file
# app/agents/food_ordering/agents/loyalty_program/node.py
async def loyalty_program_agent(entities, state):
    # Implementation
    pass

# Step 2: Register in router
from app.agents.food_ordering.agents.loyalty_program.node import loyalty_program_agent

register_agent("check_loyalty", loyalty_program_agent)

# Step 3: Add entity requirements
# File: app/agents/food_ordering/entity_validator.py
ENTITY_REQUIREMENTS["check_loyalty"] = {
    "required": [],
    "optional": ["phone_number"]
}

# Done! Now "check_loyalty" sub-intent routes correctly
```

**Example 2: Add New Guardrail**

```python
# File: app/agents/food_ordering/graph.py

def apply_state_guardrails(...):
    # ... existing guardrails ...

    # NEW GUARDRAIL: Maximum order value
    if sub_intent == "execute_checkout":
        cart_total = state.get("cart_total", 0.0)
        max_order_value = 5000.0  # ₹5000 limit

        if cart_total > max_order_value:
            logger.warning("Hard block: Order exceeds maximum value")
            return False, {
                "action": "order_too_large",
                "success": False,
                "data": {
                    "message": f"Maximum order value is ₹{max_order_value}. Please reduce your cart.",
                    "max_order_value": max_order_value,
                    "current_total": cart_total
                },
                "context": {
                    "guardrail_type": "hard_block",
                    "violation": "exceed_max_order_value"
                }
            }
```

**Example 3: Change Business Rule**

```javascript
// MongoDB: Change minimum order amount

db.settings.updateOne(
    {"key": "min_order_amount"},
    {$set: {"value": 300}}  // Change from ₹200 to ₹300
)

// Takes effect immediately (next validation will use new value)
```

**Example 4: Add Action to Cart Management**

```python
# File: app/agents/food_ordering/agents/cart_management/node.py

async def cart_management_agent(entities, state):
    action = entities.get("action", "view")

    # ... existing actions ...

    elif action == "save_for_later":
        # NEW ACTION
        return await _handle_save_for_later(entities, state, session_id)
```

---

## SUMMARY

### Key Deterministic Rule Types

1. **Routing Rules** - Map strings to functions (intent → agent, sub-intent → sub-agent, action → handler)
2. **Guardrails** - State-based safety gates (2-tier: soft guides + hard blocks)
3. **Entity Validation** - Required field checking with conditional requirements
4. **Action Routing** - Internal sub-agent dispatch based on entity values
5. **Business Rules** - Configuration-driven validation (min order, hours, tax, etc.)
6. **State Transitions** - Valid state change enforcement (cart state machine)
7. **Priority Selection** - Ordered tool selection based on entity presence

### Performance Benefits

- **Fast Execution**: All rules execute in <10ms total
- **Zero Cost**: No LLM API calls
- **100% Consistency**: Same input → Same output
- **Easy Debugging**: Clear decision paths

### Customization Points

- Add new agents: Register in router
- Add new guardrails: Add to `apply_state_guardrails()`
- Change business rules: Update MongoDB settings
- Modify validation: Update `ENTITY_REQUIREMENTS`
- Add actions: Update action routing in sub-agents

### Best Practices

1. **Use Rules for Safety**: Critical business logic should be deterministic
2. **Use AI for Understanding**: Natural language → structured data
3. **Combine Both**: Hybrid architecture maximizes benefits
4. **Make Rules Configurable**: Use database config for business rules
5. **Log Rule Decisions**: Always log which rule triggered and why

This deterministic rule system ensures the restaurant AI is **fast, predictable, safe, and cost-efficient** while still leveraging AI for natural language understanding.
