# Agent Architecture - Complete Functionality Guide

**Version:** 1.0
**Last Updated:** 2025-11-13
**Purpose:** Comprehensive reference for all agent functionality, flows, and architecture patterns

---

## Table of Contents

1. [Agent Inventory](#agent-inventory)
2. [Architecture Patterns](#architecture-patterns)
3. [Agent Details](#agent-details)
   - [1. food_ordering_agent](#1-food_ordering_agent-hierarchical)
   - [2. booking_agent](#2-booking_agent-monolithic)
   - [3. payment_agent](#3-payment_agent)
   - [4. user_agent](#4-user_agent)
   - [5. customer_satisfaction_agent](#5-customer_satisfaction_agent)
   - [6. support_agent](#6-support_agent)
   - [7. general_queries_agent](#7-general_queries_agent)
   - [8. response_agent](#8-response_agent-virtual-waiter)
4. [Comparison Tables](#comparison-tables)

---

## Agent Inventory

### Active Agents (8)

| Agent | Type | Status | Lines of Code | Complexity |
|-------|------|--------|---------------|------------|
| food_ordering_agent | Hierarchical | ✅ Modern | ~2000 (split across 5 sub-agents) | Medium |
| booking_agent | Monolithic | ⚠️ Legacy | 1,929 | High |
| payment_agent | Monolithic | ⚠️ Legacy | ~400 | Low |
| user_agent | Monolithic | ⚠️ Legacy | ~600 | Medium |
| customer_satisfaction_agent | Monolithic | ⚠️ Legacy | ~500 | Medium |
| support_agent | Monolithic | ⚠️ Legacy | ~300 | Low |
| general_queries_agent | Monolithic | ⚠️ Legacy | ~300 | Low |
| response_agent | Special | ✅ Modern | ~400 | Low |

### Deprecated Agents (2)

| Agent | Replaced By | Status |
|-------|-------------|--------|
| menu_agent | food_ordering_agent → menu_browsing/discovery | ❌ To be removed |
| order_agent | food_ordering_agent → cart_management/checkout | ❌ To be removed |

---

## Architecture Patterns

### Pattern A: Hierarchical (Modern)

**Example:** food_ordering_agent

```
Parent Agent (Coordinator)
    ↓
LLM-based Sub-Intent Classification
    ↓
Router (Registry-based)
    ↓
5 Specialized Sub-Agents
    ├─ browse_menu (menu_browsing)
    ├─ discover_items (menu_discovery)
    ├─ manage_cart (cart_management)
    ├─ validate_order (checkout_validator)
    └─ execute_checkout (checkout_executor)
```

**Benefits:**
- ✅ Modular (easy to maintain/test)
- ✅ Focused (single responsibility per sub-agent)
- ✅ Scalable (add new sub-agents easily)
- ✅ Clear separation of concerns
- ✅ Independent testing

**File Structure:**
```
/app/agents/food_ordering/
    node.py                    # Parent agent entry
    sub_intent_classifier.py   # LLM-based routing
    router.py                  # Agent registry
    graph.py                   # Guardrails & validation

    agents/
        menu_browsing/
            node.py            # Sub-agent logic
            tools.py           # Specific tools

        cart_management/
            node.py
            tools.py
            react_agent.py     # Optional: ReAct mode
```

---

### Pattern B: Monolithic (Legacy)

**Example:** booking_agent

```
Single Agent (1,929 lines)
    ├─ All logic in one file
    ├─ Mixed responsibilities
    ├─ Complex conditional routing
    └─ Hard to maintain/test
```

**Problems:**
- ❌ Hard to maintain (find specific logic)
- ❌ Mixed concerns (booking + modification + cancellation)
- ❌ Difficult to test (test entire agent)
- ❌ Brittle (changes break multiple things)
- ❌ Code duplication

**File Structure:**
```
/app/agents/booking/
    node.py        # 1,929 lines (everything!)
    tools.py       # 940 lines (all tools)
```

---

### Pattern C: Special (Response Agent)

**Example:** response_agent (Virtual Waiter)

```
All Agents
    ↓
Return ActionResult
    ↓
Response Agent
    ├─ Select template based on action
    ├─ Apply personality/tone
    ├─ Format with GPT-4o
    └─ Return user-facing message
```

**Purpose:** Unified voice across all interactions

---

## Agent Details

---

## 1. food_ordering_agent (Hierarchical)

### Overview

**What It Does:**
Complete food ordering workflow from menu browsing to order placement.

**Why It Exists:**
Replace legacy menu_agent + order_agent with modular, maintainable system.

**Type:** Hierarchical (5 sub-agents)

**Location:** `/app/agents/food_ordering/`

---

### Architecture

```
ENTRY POINT: food_ordering_agent_node(state: AgentState)
    ↓
STEP 1: Sub-Intent Classification
    └─ classify_sub_intent(user_message, state)
       ├─ Call GPT-4o-mini with context
       └─ Returns: SubIntentClassification
           {
               sub_intent: "manage_cart",
               entities: {action: "add", item_name: "butter chicken"},
               confidence: 0.95,
               missing_entities: []
           }
    ↓
STEP 2: State Guardrails
    └─ apply_state_guardrails(classification, state)
       ├─ Soft Guides (helpful redirects)
       │   └─ Empty cart + checkout → suggest browse
       └─ Hard Blocks (safety gates)
           └─ Cart locked + modify → prevent
    ↓
STEP 3: Entity Validation
    └─ validate_entities(entities)
       ├─ Check required fields present
       └─ If missing → trigger multi-turn collection
    ↓
STEP 4: Router
    └─ route_to_agent(sub_intent)
       ├─ Registry lookup
       └─ Execute sub-agent function
    ↓
STEP 5: Sub-Agent Execution
    └─ [Depends on sub_intent]
    ↓
STEP 6: Return ActionResult
    └─ {action, success, data, context, state_updates}
```

---

### Sub-Intent Classification

**File:** `/app/agents/food_ordering/sub_intent_classifier.py`

**5 Sub-Intents:**

| Sub-Intent | Description | Examples | Entities |
|------------|-------------|----------|----------|
| `browse_menu` | Navigate menu structure | "show menu", "what categories" | category_name |
| `discover_items` | Search/filter/recommendations | "vegetarian", "butter chicken", "recommend" | search_query, dietary_restrictions, price_range |
| `manage_cart` | Cart CRUD operations | "add butter chicken", "remove item 2" | action, item_name, quantity, item_index |
| `validate_order` | Pre-checkout validation | "checkout", "ready to order" | None (system) |
| `execute_checkout` | Execute order placement | "yes confirm" (after validation) | order_type (required) |

**Context Building:**

```python
# Context from state
context_parts = []

# Cart context
if cart_items:
    context_parts.append(f"Cart has {len(cart_items)} items (total: ₹{cart_subtotal})")
    if cart_validated:
        context_parts.append("Cart validated - ready for checkout")
else:
    context_parts.append("Cart is EMPTY")

# Draft order context (for disambiguation)
if draft_order_id:
    context_parts.append(f"Draft order exists: {draft_order_id}")
    context_parts.append("IMPORTANT: 'Change order' likely means cart operations")

# Auth context
if user_id:
    context_parts.append(f"User authenticated: {user_name}")
else:
    context_parts.append("User NOT authenticated")

# Entity collection context (multi-turn)
if entity_collection_step:
    context_parts.append(f"Collecting entity: {entity_collection_step}")
```

**Edge Case Disambiguation:**
- "change my order" + draft_order_id → `manage_cart` (modify current cart)
- "I want to order" + empty cart → `discover_items` (starting)
- "ready to order" + items in cart → `validate_order` (finishing)
- "add another" + items in cart → `manage_cart` (adding more)

---

### Sub-Agent 1: menu_browsing

**File:** `/app/agents/food_ordering/agents/menu_browsing/node.py`

**Functionality:**
- List all menu categories
- Browse items in specific category

**Tools:**
- `ListMenuCategoriesTool()` → Get all categories
- `BrowseCategoryTool(category_name)` → Get items in category

**Flow Example:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Show me the menu"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORCHESTRATOR ROUTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
perceive_node → Intent: "order_request"
task_manager_node → selected_agent: "food_ordering_agent"
validation_node → PASS (no entities to validate)
router_node → Route to food_ordering_agent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - STEP 1: Classification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
classify_sub_intent("Show me the menu", state)
    ↓
GPT-4o-mini Call:
    System: [Sub-intent classifier prompt]
    User: Context: Cart is EMPTY
          User authenticated: John

          User Message: "Show me the menu"
    ↓
Response:
{
    "sub_intent": "browse_menu",
    "entities": {},
    "confidence": 0.98,
    "missing_entities": [],
    "reasoning": "User wants to see full menu structure"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - STEP 2: Guardrails
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
apply_state_guardrails(classification, state)
    ↓
Check: Cart locked? NO
Check: Cart empty for checkout? N/A (not checkout)
    ↓
Result: PROCEED (no guardrail triggered)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - STEP 3: Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
validate_entities({})
    ↓
No entities to validate
    ↓
Result: VALID

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - STEP 4: Router
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
route_to_agent("browse_menu")
    ↓
Agent Registry Lookup:
    _agent_registry["browse_menu"] → menu_browsing_agent
    ↓
Execute: menu_browsing_agent(entities={}, state)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: menu_browsing
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
menu_browsing_agent(entities, state)
    ↓
Decision: No category specified → List all categories
    ↓
Tool Call: ListMenuCategoriesTool()

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL EXECUTION: ListMenuCategoriesTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute:
    ↓
Database Query:
    SELECT DISTINCT category
    FROM menu_items
    WHERE restaurant_id = 'rest001'
    AND is_available = true
    ORDER BY display_order
    ↓
Results:
    ["Appetizers", "Main Course", "Breads", "Desserts", "Beverages"]
    ↓
Return ToolResult:
{
    "status": "SUCCESS",
    "success": True,
    "data": {
        "categories": [
            "Appetizers",
            "Main Course",
            "Breads",
            "Desserts",
            "Beverages"
        ]
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: menu_browsing (Return)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Receive ToolResult
    ↓
Format ActionResult:
{
    "action": "categories_listed",
    "success": True,
    "data": {
        "categories": [
            "Appetizers",
            "Main Course",
            "Breads",
            "Desserts",
            "Beverages"
        ],
        "count": 5,
        "message": "Here are our menu categories"
    },
    "context": {
        "action_performed": "list_categories"
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACK TO ORCHESTRATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Update State:
    state["agent_metadata"] = {
        "action": "categories_listed",
        "data": {...}
    }
    ↓
Route to: response_agent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE AGENT (Virtual Waiter)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
action = "categories_listed"
template = ACTION_PROMPTS["categories_listed"]
    ↓
Template says: "Output the pre-formatted list exactly as provided"
    ↓
GPT-4o Call:
    System: VIRTUAL_WAITER_SYSTEM_PROMPT (casual, friendly)
    User: [categories data]
    ↓
Response:
"Here's our menu for today!

**Appetizers**
**Main Course**
**Breads**
**Desserts**
**Beverages**

What are you in the mood for?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER SEES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Here's our menu for today!

**Appetizers**
**Main Course**
**Breads**
**Desserts**
**Beverages**

What are you in the mood for?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Sub-Agent 2: menu_discovery

**File:** `/app/agents/food_ordering/agents/menu_discovery/node.py`

**Functionality:**
- Semantic search for dishes (AI-powered)
- Filter by dietary restrictions
- Filter by price range
- Get recommendations

**Tools:**
- `SemanticMenuSearchTool(search_query, filters)` → Vector search + filters
- `GetMenuItemDetailsTool(item_id)` → Get full item details

**Flow Example - Filtered Search:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Show me vegetarian options under ₹300"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - Classification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sub-Intent: "discover_items"
Entities:
{
    "dietary_restrictions": ["vegetarian"],
    "price_range": {"max": 300}
}
Confidence: 0.92

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: menu_discovery
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
menu_discovery_agent(entities, state)
    ↓
Extract:
    dietary_restrictions = ["vegetarian"]
    price_range = {"max": 300}
    ↓
Tool Call: SemanticMenuSearchTool(
    search_query="vegetarian",
    filters={
        "dietary_restrictions": ["vegetarian"],
        "price_range": {"max": 300}
    }
)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: SemanticMenuSearchTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Vector Search
    ↓
Generate embedding for "vegetarian"
    ↓
Database (PostgreSQL with pgvector):
    SELECT
        item_id,
        name,
        description,
        price,
        dietary_tags,
        1 - (embedding <=> query_embedding) as similarity
    FROM menu_items
    WHERE restaurant_id = 'rest001'
    AND is_available = true
    ORDER BY similarity DESC
    LIMIT 100
    ↓
Initial Results: [50 items with "vegetarian" similarity]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Apply Filters (Python)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Filter 1: dietary_restrictions = ["vegetarian"]
    ↓
for item in results:
    if "vegetarian" in item.dietary_tags:
        filtered_results.append(item)
    ↓
Results after filter 1: [35 items]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Filter 2: price_range = {"max": 300}
    ↓
for item in filtered_results:
    if item.price <= 300:
        final_results.append(item)
    ↓
Final Results: [12 items]
    [
        {
            "item_id": "mit000123",
            "name": "Paneer Tikka",
            "price": 250,
            "description": "Grilled cottage cheese with spices",
            "dietary_tags": ["vegetarian"]
        },
        {
            "item_id": "mit000234",
            "name": "Veg Biryani",
            "price": 280,
            "description": "Fragrant rice with mixed vegetables",
            "dietary_tags": ["vegetarian", "spicy"]
        },
        ... 10 more items
    ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ToolResult
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
    "status": "SUCCESS",
    "success": True,
    "data": {
        "items": [...12 items...],
        "count": 12,
        "filters_applied": ["vegetarian", "price <= 300"]
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: menu_discovery (Return)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ActionResult:
{
    "action": "search_results",
    "success": True,
    "data": {
        "items": [...12 items...],
        "count": 12,
        "search_query": "vegetarian",
        "filters": ["vegetarian", "under ₹300"]
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE AGENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GPT-4o Response:
"Looking for vegetarian options? Here's what we have under ₹300:

1. **Paneer Tikka** - ₹250
   Grilled cottage cheese with spices

2. **Veg Biryani** - ₹280
   Fragrant rice with mixed vegetables

... [10 more items]

The Paneer Tikka is really popular! Want to add something to your cart?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Sub-Agent 3: cart_management

**File:** `/app/agents/food_ordering/agents/cart_management/node.py`

**Functionality:**
- Add items to cart (with item resolution)
- Remove items from cart (by name or index)
- Update quantities
- View cart
- Clear cart

**Execution Modes:**
1. **Deterministic Mode** (default) - Predefined action routing
2. **ReAct Mode** (optional) - AI reasoning with tools

**Tools:**
- `AddToCartTool(session_id, item_id, quantity)`
- `RemoveFromCartTool(session_id, item_id)`
- `UpdateCartQuantityTool(session_id, item_id, new_quantity)`
- `ViewCartTool(session_id)`
- `ClearCartTool(session_id)`

**Flow Example - Add Item:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Add 2 butter chickens to my cart"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - Classification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sub-Intent: "manage_cart"
Entities:
{
    "action": "add",
    "item_name": "butter chicken",
    "quantity": 2
}
Confidence: 0.96

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: cart_management
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
cart_management_agent(entities, state)
    ↓
Mode Check:
    agent_mode = "deterministic"
    react_enabled = False
    ↓
Route to: _deterministic_cart_management()
    ↓
Action: "add"
    ↓
Route to: _handle_add_to_cart(entities, state)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FUNCTION: _handle_add_to_cart
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extract:
    item_id = None  (not provided)
    item_name = "butter chicken"
    quantity = 2
    ↓
Step 1: Resolve item_name → item_id
    ↓
    if not item_id and item_name:
        # Need to look up item_id from name
        search_tool = SemanticMenuSearchTool()
        result = await search_tool.execute(
            search_query="butter chicken",
            limit=1,
            include_unavailable=False
        )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: SemanticMenuSearchTool (Item Resolution)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Search: "butter chicken"
    ↓
Vector Search (exact match highly ranked)
    ↓
Result:
{
    "items": [
        {
            "item_id": "mit000456",
            "name": "Butter Chicken",
            "price": 320,
            "description": "Creamy tomato-based curry with tender chicken"
        }
    ]
}
    ↓
Extract:
    item_id = "mit000456"
    item_name = "Butter Chicken"  (canonical name)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACK TO: _handle_add_to_cart
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
item_id = "mit000456" ✓
    ↓
Step 2: Add to cart
    ↓
add_tool = AddToCartTool()
result = await add_tool.execute(
    session_id="abc123",
    item_id="mit000456",
    quantity=2
)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: AddToCartTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute:
    session_id = "abc123"
    item_id = "mit000456"
    quantity = 2
    ↓
Call Service Layer:
    cart_service = get_cart_service()
    result = await cart_service.add_item(
        session_id="abc123",
        item_id="mit000456",
        quantity=2
    )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICE: CartService.add_item()
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Get item details
    ↓
Database:
    SELECT * FROM menu_items
    WHERE item_id = 'mit000456'
    ↓
Result:
    {
        "item_id": "mit000456",
        "name": "Butter Chicken",
        "price": 320,
        "category": "main_course"
    }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Check inventory availability
    ↓
inventory_service = get_inventory_service()
available = await inventory_service.check_availability(
    item_id="mit000456",
    quantity=2
)
    ↓
Redis Check:
    GET inventory:mit000456
    → Current stock: 50

    GET reservation:mit000456:*  (all user reservations)
    → Reserved: 8

    Available = 50 - 8 = 42
    Requested = 2

    42 >= 2 ✓ AVAILABLE

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Reserve inventory
    ↓
await inventory_service.reserve_inventory(
    item_id="mit000456",
    quantity=2,
    user_id="usr456"  (or session_id if anonymous)
)
    ↓
Redis:
    SET reservation:mit000456:usr456 = 2
    EXPIRE reservation:mit000456:usr456 900  (15 minutes)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Add to cart (in-memory or MongoDB)
    ↓
cart = await cart_store.get_cart(session_id="abc123")
    ↓
Existing cart:
    [
        {
            "item_id": "mit000123",
            "name": "Naan",
            "quantity": 3,
            "unit_price": 50,
            "item_total": 150
        }
    ]
    ↓
Check if item already in cart:
    item "mit000456" NOT found
    ↓
Add new item:
    cart.items.append({
        "item_id": "mit000456",
        "name": "Butter Chicken",
        "quantity": 2,
        "unit_price": 320,
        "item_total": 640  (320 * 2)
    })
    ↓
Recalculate totals:
    cart_subtotal = 150 + 640 = 790
    cart_item_count = 2

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 5: Save cart
    ↓
await cart_store.save_cart(session_id="abc123", cart)
    ↓
MongoDB (or in-memory):
    db.carts.updateOne(
        {session_id: "abc123"},
        {
            $set: {
                items: [...],
                subtotal: 790,
                updated_at: now()
            }
        },
        {upsert: true}
    )

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SERVICE: Return Result
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return:
{
    "item_name": "Butter Chicken",
    "quantity": 2,
    "item_total": 640,
    "cart_subtotal": 790,
    "cart_item_count": 2,
    "message": "Added 2x Butter Chicken to cart"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: AddToCartTool (Return)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ToolResult:
{
    "status": "SUCCESS",
    "success": True,
    "data": {
        "item_name": "Butter Chicken",
        "quantity": 2,
        "item_total": 640,
        "cart_subtotal": 790,
        "cart_item_count": 2,
        "message": "Added 2x Butter Chicken to cart"
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: cart_management (Return ActionResult)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ActionResult:
{
    "action": "item_added",
    "success": True,
    "data": {
        "item_name": "Butter Chicken",
        "quantity": 2,
        "item_total": 640,
        "cart_subtotal": 790,
        "cart_item_count": 2,
        "message": "Added 2x Butter Chicken to cart"
    },
    "context": {
        "item_id": "mit000456",
        "action_performed": "added"
    },
    // State updates
    "cart_subtotal": 790
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORCHESTRATOR: Update State
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
state["cart_subtotal"] = 790
state["agent_metadata"] = {...}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE AGENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Action: "item_added"
Template: ACTION_PROMPTS["item_added"]
    ↓
GPT-4o with Virtual Waiter personality:
"Great choice! Added 2x Butter Chicken (₹640) to your cart.
Your total is now ₹790.

Want to add some garlic naan or a drink to go with it?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER SEES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Great choice! Added 2x Butter Chicken (₹640) to your cart.
Your total is now ₹790.

Want to add some garlic naan or a drink to go with it?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Flow Example - Remove by Index:**

```
User: "Remove item 2"
    ↓
Sub-Intent: "manage_cart"
Entities: {action: "remove", item_index: 2}
    ↓
cart_management_agent → _handle_remove_from_cart()
    ↓
Step 1: Resolve item_index → item_id
    cart_items = state.cart_items  // [item1, item2, item3]
    index = 2 - 1 = 1  (convert to 0-indexed)
    item_id = cart_items[1].item_id  // "mit000456"
    ↓
Step 2: Remove from cart
    RemoveFromCartTool(session_id, "mit000456")
    ↓
Service:
    - Release inventory reservation (Redis)
    - Remove from cart
    - Recalculate totals
    ↓
ActionResult: {action: "item_removed", ...}
```

---

### Sub-Agent 4: checkout_validator

**File:** `/app/agents/food_ordering/agents/checkout_validator/node.py`

**Functionality:**
- Validate cart before checkout
- Check all items still available
- Verify inventory sufficient
- Show order summary
- Set `cart_validated = True`

**Tools:**
- `ValidateCartTool(session_id)`
- `CheckInventoryAvailabilityTool(item_id, quantity)`

**Flow Example:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "I'm ready to checkout"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - Classification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sub-Intent: "validate_order"
Entities: {}
Confidence: 0.94
Reasoning: "User explicitly signals readiness to checkout"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - Guardrails
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Check: Cart empty?
    cart_item_count = 2
    NO → Continue
    ↓
(If YES, would return empty_cart_redirect)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: checkout_validator
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
checkout_validator_agent(entities, state)
    ↓
Tool Call: ValidateCartTool(session_id="abc123")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: ValidateCartTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute:
    ↓
Service: cart_service.validate_cart(session_id)
    ↓
Step 1: Get cart
    cart = await cart_store.get_cart("abc123")
    items = [
        {item_id: "mit000123", name: "Naan", quantity: 3, price: 50},
        {item_id: "mit000456", name: "Butter Chicken", quantity: 2, price: 320}
    ]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Validate each item
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For item "mit000123" (Naan x3):
    ↓
    Check 1: Still available?
        Database: SELECT is_available FROM menu_items WHERE item_id = 'mit000123'
        → Result: TRUE ✓
    ↓
    Check 2: Inventory sufficient?
        inventory_service.check_availability("mit000123", 3)
        → Redis: Available = 100, Reserved = 15, Free = 85
        → 85 >= 3 ✓ SUFFICIENT
    ↓
    Check 3: Price changed?
        Database price: 50
        Cart price: 50
        → SAME ✓

For item "mit000456" (Butter Chicken x2):
    ↓
    Check 1: Still available? ✓
    Check 2: Inventory sufficient? ✓
    Check 3: Price same? ✓

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Calculate final totals
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Subtotal:
    Naan: 3 x 50 = 150
    Butter Chicken: 2 x 320 = 640
    ───────────────────────
    Subtotal: 790
    ↓
Taxes (10%):
    Tax: 790 * 0.10 = 79
    ↓
Total:
    Total: 790 + 79 = 869

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Generate order summary
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Summary:
"Order Summary:
- 3x Naan @ ₹50 = ₹150
- 2x Butter Chicken @ ₹320 = ₹640

Subtotal: ₹790
Tax (10%): ₹79
──────────────
Total: ₹869"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: Return ToolResult
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
    "status": "SUCCESS",
    "success": True,
    "data": {
        "items": [
            {
                "item_id": "mit000123",
                "name": "Naan",
                "quantity": 3,
                "unit_price": 50,
                "item_total": 150
            },
            {
                "item_id": "mit000456",
                "name": "Butter Chicken",
                "quantity": 2,
                "unit_price": 320,
                "item_total": 640
            }
        ],
        "subtotal": 790,
        "tax": 79,
        "total": 869,
        "order_summary": "Order Summary: ...",
        "validation_passed": True
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: checkout_validator (Return)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ActionResult:
{
    "action": "cart_validated",
    "success": True,
    "data": {
        "items": [...],
        "subtotal": 790,
        "tax": 79,
        "total": 869,
        "order_summary": "..."
    },
    // State updates
    "cart_validated": True
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE AGENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Perfect! Here's your order summary:

**Order Summary:**
- 3x Naan @ ₹50 = ₹150
- 2x Butter Chicken @ ₹320 = ₹640

Subtotal: ₹790
Tax (10%): ₹79
──────────────
**Total: ₹869**

Ready to place your order? Just say 'confirm' and let me know if it's for dine-in or takeout!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Sub-Agent 5: checkout_executor

**File:** `/app/agents/food_ordering/agents/checkout_executor/node.py`

**Functionality:**
- Create draft order in database
- Create order items records
- Commit inventory reservations
- Lock cart
- Update order status to confirmed
- Generate order confirmation

**Tools:**
- `CreateDraftOrderTool(session_id, order_type)`
- `CommitInventoryTool(session_id, draft_order_id)`
- `PlaceOrderTool(draft_order_id)`

**Flow Example:**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
USER INPUT (After validation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Yes, confirm it. Dine-in please."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - Classification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sub-Intent: "execute_checkout"
Entities: {order_type: "dine_in"}
Confidence: 0.97

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOOD ORDERING AGENT - Guardrails
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Check: Cart validated?
    cart_validated = True ✓
    Continue
    ↓
(If NO, would return validation_required)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: checkout_executor
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
checkout_executor_agent(entities, state)
    ↓
Extract:
    order_type = "dine_in"
    session_id = "abc123"
    user_id = "usr456"
    ↓
Tool Call: CreateDraftOrderTool(
    session_id="abc123",
    order_type="dine_in"
)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: CreateDraftOrderTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute:
    ↓
Service: order_service.create_draft_order(session_id, order_type)
    ↓
Step 1: Get cart
    cart = await cart_store.get_cart("abc123")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Create order record
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database Transaction BEGIN:
    ↓
INSERT INTO orders:
    INSERT INTO orders (
        id,
        user_id,
        restaurant_id,
        order_type,
        status,
        subtotal,
        tax_amount,
        total_amount,
        created_at
    ) VALUES (
        'ord_789abc',      -- Generated UUID
        'usr456',
        'rest001',
        'dine_in',
        'pending',         -- Initial status
        790.00,
        79.00,
        869.00,
        '2025-11-14 10:30:00'
    )
    RETURNING id;
    ↓
Result: order_id = "ord_789abc"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Create order items
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
For each cart item:
    ↓
INSERT INTO order_items (Item 1):
    INSERT INTO order_items (
        id,
        order_id,
        item_id,
        quantity,
        unit_price,
        subtotal
    ) VALUES (
        'oi_111',
        'ord_789abc',
        'mit000123',       -- Naan
        3,
        50.00,
        150.00
    );

INSERT INTO order_items (Item 2):
    INSERT INTO order_items (
        id,
        order_id,
        item_id,
        quantity,
        unit_price,
        subtotal
    ) VALUES (
        'oi_222',
        'ord_789abc',
        'mit000456',       -- Butter Chicken
        2,
        320.00,
        640.00
    );

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Generate order number
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
order_number = generate_order_number()
    → "ABC" + timestamp_short + random
    → "ABC141030" (Nov 14, 10:30)
    ↓
UPDATE orders
SET order_number = 'ABC141030'
WHERE id = 'ord_789abc';

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Database Transaction COMMIT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return:
{
    "order_id": "ord_789abc",
    "order_number": "ABC141030"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACK TO: checkout_executor_agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
draft_order_id = "ord_789abc"
    ↓
Tool Call: CommitInventoryTool(
    session_id="abc123",
    draft_order_id="ord_789abc"
)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: CommitInventoryTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute:
    ↓
Service: inventory_service.commit_reservations(session_id)
    ↓
For each cart item:

Item 1: Naan (mit000123, quantity=3)
    ↓
    Redis:
        # Remove reservation
        DEL reservation:mit000123:usr456

        # Decrement inventory
        DECRBY inventory:mit000123 3
        → New stock: 100 → 97
    ↓
    Database (audit trail):
        INSERT INTO inventory_transactions (
            item_id,
            order_id,
            change_type,
            quantity_change,
            timestamp
        ) VALUES (
            'mit000123',
            'ord_789abc',
            'order_placed',
            -3,
            now()
        );

Item 2: Butter Chicken (mit000456, quantity=2)
    ↓
    Redis:
        DEL reservation:mit000456:usr456
        DECRBY inventory:mit000456 2
        → New stock: 50 → 48

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACK TO: checkout_executor_agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
inventory_committed = True
    ↓
Tool Call: PlaceOrderTool(draft_order_id="ord_789abc")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOOL: PlaceOrderTool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute:
    ↓
Service: order_service.place_order(order_id)
    ↓
Step 1: Update order status
    UPDATE orders
    SET status = 'confirmed',
        confirmed_at = now()
    WHERE id = 'ord_789abc';
    ↓
Step 2: Lock cart
    cart_store.lock_cart(session_id="abc123")
    → cart.locked = True
    ↓
Step 3: Calculate estimated time
    estimated_time = calculate_prep_time(items)
    → 25 minutes (based on item complexity)
    ↓
Return:
{
    "order_id": "ord_789abc",
    "order_number": "ABC141030",
    "status": "confirmed",
    "estimated_time_minutes": 25,
    "total": 869
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUB-AGENT: checkout_executor (Return ActionResult)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ActionResult:
{
    "action": "order_placed",
    "success": True,
    "data": {
        "order_id": "ord_789abc",
        "order_number": "ABC141030",
        "total": 869,
        "estimated_time": "25 minutes",
        "order_type": "dine_in",
        "items": [
            {"name": "Naan", "quantity": 3},
            {"name": "Butter Chicken", "quantity": 2}
        ]
    },
    // State updates
    "draft_order_id": "ord_789abc",
    "cart_locked": True,
    "cart_validated": False  // Reset for next order
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RESPONSE AGENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"Perfect! Your order is confirmed! 🎉

**Order Number:** ABC141030
**Total:** ₹869
**Estimated Time:** 25 minutes
**Type:** Dine-in

Your order:
- 3x Naan
- 2x Butter Chicken

We'll have it ready for you soon. Anything else I can help with?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### State Management (food_ordering_agent)

**File:** `/app/agents/food_ordering/state.py`

```python
class FoodOrderingState(TypedDict):
    # Session
    session_id: str
    user_id: Optional[str]

    # Cart
    cart_items: List[Dict[str, Any]]
    cart_subtotal: float
    cart_validated: bool
    cart_locked: bool

    # Order
    draft_order_id: Optional[str]
    order_type: Optional[str]  # "dine_in" or "takeout"

    # Execution mode
    agent_mode: str  # "deterministic" or "react"
    react_agent_enabled: bool

    # Entity collection (multi-turn)
    entity_collection_step: Optional[str]
    collected_entities: Dict[str, Any]
```

**State Updates by Sub-Agent:**

| Sub-Agent | Updates |
|-----------|---------|
| menu_browsing | None (read-only) |
| menu_discovery | None (read-only) |
| cart_management | `cart_items`, `cart_subtotal` |
| checkout_validator | `cart_validated = True` |
| checkout_executor | `draft_order_id`, `cart_locked`, `cart_validated = False` |

---

## 2. booking_agent (Monolithic)

### Overview

**What It Does:**
Table booking workflow - check availability, create booking, manage bookings.

**Why It Exists:**
Handle restaurant table reservations with date/time/party size.

**Type:** Monolithic (1,929 lines)

**Location:** `/app/agents/booking/node.py`

**Status:** ⚠️ Legacy - Needs migration to hierarchical

---

### Architecture

```
ENTRY POINT: booking_agent_node(state: AgentState)
    ↓
INTERNAL SUBGRAPH (LangGraph loop)
    ├─ Node 1: reasoning_node
    │   ├─ Extract entities (BookingEntities)
    │   ├─ Track progress (BookingProgress)
    │   ├─ Decide next action
    │   └─ Call tools or respond to user
    │
    ├─ Node 2: tools_node (if tools called)
    │   └─ Execute booking tools
    │
    └─ Loop until booking_created = True
```

**Key Difference:** Single monolithic agent with internal state machine vs. hierarchical with sub-agents.

---

### Booking Progress Tracker

```python
class BookingProgress(BaseModel):
    # Required fields
    party_size: Optional[int] = None
    date: Optional[str] = None
    time: Optional[str] = None
    special_requests: Optional[str] = None

    # Progress flags
    availability_checked: bool = False
    availability_result: Optional[Dict] = None
    user_confirmed: bool = False
    booking_created: bool = False
    booking_id: Optional[str] = None
    confirmation_code: Optional[str] = None
    sms_sent: bool = False

    # Auth tracking
    phone: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None

    def is_ready_to_check_availability(self) -> bool:
        return all([self.party_size, self.date, self.time])

    def is_complete(self) -> bool:
        return self.booking_created and self.booking_id is not None
```

---

### Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `CheckAvailabilityTool` | Check table availability | party_size, date, time |
| `CreateBookingTool` | Create booking in DB | party_size, date, time, user_id/phone |
| `SendBookingConfirmationTool` | Send SMS | phone, booking_details |
| `GetUserBookingsTool` | Retrieve bookings | user_id or phone |
| `CancelBookingTool` | Cancel booking | booking_id |
| `ModifyBookingTool` | Modify booking | booking_id, updates |

---

### Flow Example - Complete Booking

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TURN 1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "I want to book a table for 4"

booking_agent_node() starts
    ↓
Internal Subgraph Loop Iteration #1:
    ↓
reasoning_node:
    ├─ Extract entities (GPT-4o with structured output):
    │   BookingEntities:
    │       party_size: 4
    │       date: None
    │       time: None
    │       phone_number: None
    │       user_name: None
    │
    ├─ Update progress:
    │   BookingProgress:
    │       party_size: 4 ✓
    │       date: None ✗
    │       time: None ✗
    │       is_ready_to_check_availability(): False
    │
    ├─ Decision: Need more info (date & time)
    │
    └─ Generate response (no tool call):
        "Great! When would you like to come?
         Please tell me the date and time."

should_continue_booking(state):
    last_message has tool_calls? NO
    → Return "end"

Subgraph exits, returns to orchestrator

Response: "Great! When would you like to come?
           Please tell me the date and time."

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TURN 2
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Tomorrow at 7pm"

booking_agent_node() starts (same subgraph, new conversation turn)
    ↓
Internal Subgraph Loop Iteration #1:
    ↓
reasoning_node:
    ├─ Context: BookingProgress from previous turn
    │   party_size: 4 (already collected)
    │
    ├─ Extract entities:
    │   BookingEntities:
    │       party_size: 4 (from context)
    │       date: "tomorrow"
    │       time: "7pm"
    │
    ├─ Update progress:
    │   BookingProgress:
    │       party_size: 4 ✓
    │       date: "2025-11-15" (parsed)
    │       time: "19:00" (parsed)
    │       is_ready_to_check_availability(): True ✓
    │
    ├─ Decision: All info collected, check availability
    │
    └─ Call Tool: CheckAvailabilityTool
        tool_call = {
            "name": "check_availability",
            "args": {
                "party_size": 4,
                "date": "2025-11-15",
                "time": "19:00"
            }
        }

should_continue_booking(state):
    last_message has tool_calls? YES
    → Return "continue"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Internal Subgraph Loop Iteration #2:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tools_node:
    ↓
Execute: CheckAvailabilityTool(
    party_size=4,
    date="2025-11-15",
    time="19:00"
)
    ↓
Database Query:
    SELECT
        t.table_id,
        t.capacity,
        b.booking_id
    FROM tables t
    LEFT JOIN bookings b ON (
        b.table_id = t.table_id
        AND b.booking_date = '2025-11-15'
        AND b.booking_time = '19:00'
        AND b.status != 'cancelled'
    )
    WHERE t.restaurant_id = 'rest001'
    AND t.capacity >= 4
    AND b.booking_id IS NULL  -- Not booked
    ORDER BY t.capacity ASC  -- Smallest suitable table
    LIMIT 1
    ↓
Result:
    {
        "table_id": "tbl003",
        "capacity": 4,
        "available": True
    }
    ↓
Return ToolMessage:
{
    "name": "check_availability",
    "content": {
        "available": True,
        "table_id": "tbl003",
        "capacity": 4,
        "date": "2025-11-15",
        "time": "19:00"
    }
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Internal Subgraph Loop Iteration #3:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
reasoning_node (after tool execution):
    ├─ Update progress:
    │   BookingProgress:
    │       availability_checked: True ✓
    │       availability_result: {available: True, table_id: "tbl003"}
    │
    ├─ Decision: Show availability, ask for confirmation
    │
    └─ Generate response (no tool call):
        "Perfect! We have a table for 4 available tomorrow
         (Nov 15) at 7pm. Should I confirm this booking for you?"

should_continue_booking(state):
    tool_calls? NO
    → Return "end"

Subgraph exits

Response: "Perfect! We have a table for 4 available tomorrow
           (Nov 15) at 7pm. Should I confirm this booking for you?"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TURN 3
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
User: "Yes, please"

booking_agent_node() starts
    ↓
reasoning_node:
    ├─ Context: BookingProgress
    │   availability_checked: True
    │   availability_result: {available: True}
    │
    ├─ Extract: user_confirmed = True
    │
    ├─ Check: User authenticated?
    │   is_authenticated = True
    │   user_id = "usr456"
    │   phone_number = "9876543210"
    │
    ├─ Decision: Create booking
    │
    └─ Call Tool: CreateBookingTool
        tool_call = {
            "name": "create_booking",
            "args": {
                "user_id": "usr456",
                "party_size": 4,
                "date": "2025-11-15",
                "time": "19:00",
                "table_id": "tbl003"
            }
        }

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tools_node:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute: CreateBookingTool(...)
    ↓
Database Transaction:
    BEGIN;

    # Generate confirmation code
    confirmation_code = "BK" + random_digits(4)
    → "BK7392"

    # Insert booking
    INSERT INTO bookings (
        id,
        user_id,
        restaurant_id,
        table_id,
        party_size,
        booking_date,
        booking_time,
        status,
        confirmation_code,
        created_at
    ) VALUES (
        'bk_123abc',
        'usr456',
        'rest001',
        'tbl003',
        4,
        '2025-11-15',
        '19:00:00',
        'confirmed',
        'BK7392',
        now()
    )
    RETURNING id, confirmation_code;

    COMMIT;
    ↓
Result:
{
    "booking_id": "bk_123abc",
    "confirmation_code": "BK7392",
    "status": "confirmed"
}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
reasoning_node (after tool):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ├─ Update progress:
    │   BookingProgress:
    │       booking_created: True ✓
    │       booking_id: "bk_123abc"
    │       confirmation_code: "BK7392"
    │       is_complete(): True ✓
    │
    ├─ Decision: (Optional) Send SMS confirmation
    │
    └─ Call Tool: SendBookingConfirmationTool
        (Optional - may skip in some flows)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
tools_node:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Execute: SendBookingConfirmationTool(
    phone="9876543210",
    booking_details={...}
)
    ↓
SMS Service (Twilio/etc.):
    Send SMS to 9876543210:
    "Booking confirmed! Table for 4 on Nov 15 at 7pm.
     Confirmation code: BK7392"
    ↓
Result: {sent: True}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
reasoning_node (final):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ├─ Update progress:
    │   sms_sent: True ✓
    │
    ├─ Decision: Complete! No more actions
    │
    └─ Generate response:
        "All set! Your table for 4 is confirmed for tomorrow
         (Nov 15) at 7pm. Your confirmation code is BK7392.
         I've sent you an SMS with the details. See you then!"

should_continue_booking(state):
    tool_calls? NO
    → Return "end"

Subgraph exits permanently (booking complete)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACK TO ORCHESTRATOR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Update state:
    agent_response = "All set! Your table..."

Route to: response_agent (Virtual Waiter)

Response Agent (minimal transformation):
    "All set! Your table for 4 is confirmed for tomorrow
     at 7pm. Confirmation code: BK7392.
     I've texted you the details. Can't wait to see you!"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Problems with Monolithic Approach

1. **Hard to Find Logic:**
   - Availability check logic buried in 1,929 lines
   - Modification logic mixed with creation logic
   - Cancellation flow intertwined

2. **Difficult to Test:**
   - Must test entire 1,929-line agent
   - Can't test "check availability" in isolation
   - Hard to mock specific scenarios

3. **Mixed Responsibilities:**
   - Booking creation
   - Booking modification
   - Booking cancellation
   - Availability checking
   - SMS sending
   - All in one agent!

4. **Brittle:**
   - Change one part, risk breaking another
   - Progress tracker couples all flows

---

### Migration Plan (Not Yet Done)

**Target:** Hierarchical booking_agent

```
booking_agent (parent)
    ↓
sub_intent_classifier
    ↓
    ├─ availability_checker (check availability)
    ├─ booking_creator (create new booking)
    ├─ booking_manager (view/modify/cancel)
    └─ waitlist_manager (if no availability)
```

**Benefits:**
- Each sub-agent < 300 lines
- Clear responsibilities
- Easy to test
- Easy to extend (add waitlist feature)

---

## 3. payment_agent

### Overview

**What It Does:**
Process payments via Razorpay integration.

**Why It Exists:**
Handle payment workflow after order/booking creation.

**Type:** Monolithic

**Location:** `/app/agents/payment/node.py`

---

### Architecture

```
ENTRY POINT: payment_agent_node(state)
    ↓
INTERNAL SUBGRAPH (LangGraph loop)
    ├─ reasoning_node
    │   └─ Understand payment intent, call tools
    │
    ├─ tools_node
    │   └─ Execute Razorpay integration
    │
    └─ Loop until payment link created
```

---

### Tools

| Tool | Purpose |
|------|---------|
| `CreatePaymentLinkTool` | Generate Razorpay payment link |
| `CheckPaymentStatusTool` | Check if payment completed |
| `ProcessRefundTool` | Initiate refund |
| `GetPaymentHistoryTool` | User's payment history |

---

### Flow Example

```
User: "Pay for my order"
    ↓
reasoning_node:
    Context: draft_order_id = "ord789"
    Decision: Create payment link
    Tool: CreatePaymentLinkTool(order_id, amount=869)
    ↓
Razorpay API:
    POST /payment_links
    {
        amount: 86900,  // Paise
        currency: "INR",
        description: "Order ABC141030",
        customer: {phone: "9876543210"}
    }
    ↓
Response:
    {
        payment_link_id: "plink_xyz",
        short_url: "rzp.io/l/abc123"
    }
    ↓
Database:
    UPDATE orders
    SET payment_link_id = "plink_xyz"
    WHERE order_id = "ord789"
    ↓
Response: "Here's your payment link: rzp.io/l/abc123 (₹869)"

---

(User pays via Razorpay)

---

Webhook: payment.success
    ↓
Backend:
    UPDATE orders
    SET payment_status = "paid",
        payment_id = "pay_xyz",
        status = "confirmed"
    WHERE payment_link_id = "plink_xyz"
    ↓
Notify user (WebSocket/SMS)
```

---

## 4. user_agent

### Overview

**What It Does:**
Authentication, registration, profile management.

**Why It Exists:**
Manage user identity - phone + OTP flow.

**Type:** Monolithic

**Location:** `/app/agents/user/node.py`

---

### User Auth Progress Tracker

```python
class UserAuthProgress(BaseModel):
    # Phone
    phone_number: Optional[str]
    phone_validated: bool
    phone_confirmed: bool

    # User check
    user_checked: bool
    user_exists: bool
    user_id: Optional[str]

    # OTP
    otp_sent: bool
    otp_code: Optional[str]
    otp_verified: bool

    # Registration (new users)
    full_name: Optional[str]
    name_collected: bool
    account_created: bool

    # Complete
    authenticated: bool
    session_token: Optional[str]

    # Error handling
    otp_verification_attempts: int  # Max 3
    otp_send_count: int  # Max 3
    locked_until: Optional[str]
```

---

### Tools

| Tool | Purpose |
|------|---------|
| `ValidatePhoneNumberTool` | Validate phone format |
| `CheckUserExistsTool` | Check if user registered |
| `SendOTPTool` | Send OTP via SMS |
| `VerifyOTPTool` | Verify user-entered OTP |
| `CreateUserAccountTool` | Register new user |
| `IssueSessionTokenTool` | Generate JWT |

---

### Flow Example - Existing User

```
TURN 1:
User: "I need to login"
    ↓
Response: "What's your phone number?"

TURN 2:
User: "9876543210"
    ↓
Tool: ValidatePhoneNumberTool("9876543210")
    → Valid ✓
    ↓
Tool: CheckUserExistsTool("9876543210")
    ↓
Database:
    SELECT * FROM users WHERE phone = "9876543210"
    ↓
Result: {exists: True, user_id: "usr456", name: "John"}
    ↓
Tool: SendOTPTool("9876543210")
    ↓
OTP Service:
    code = "123456"
    Redis: SET otp:9876543210 = "123456" EX 300
    SMS: "Your OTP is 123456"
    ↓
Response: "I've sent you an OTP. Please enter it."

TURN 3:
User: "123456"
    ↓
Tool: VerifyOTPTool("9876543210", "123456")
    ↓
Redis:
    GET otp:9876543210
    Compare: "123456" == "123456" ✓
    DEL otp:9876543210
    ↓
Tool: IssueSessionTokenTool("usr456")
    ↓
JWT:
    payload = {user_id: "usr456", phone: "9876543210"}
    token = sign(payload, secret)
    expiry = 30 days
    ↓
Update State:
    is_authenticated = True
    user_id = "usr456"
    session_token = "jwt_token"
    ↓
Response: "You're logged in! Welcome back, John."
```

### Flow Example - New User

```
(After CheckUserExistsTool returns exists: False)

Response: "Looks like you're new! What's your name?"

User: "Jane Doe"
    ↓
Tool: SendOTPTool("9876543210")
    (Same OTP flow)
    ↓
After OTP verified:
    ↓
Tool: CreateUserAccountTool(
    phone="9876543210",
    full_name="Jane Doe"
)
    ↓
Database:
    INSERT INTO users (phone, full_name)
    VALUES ("9876543210", "Jane Doe")
    RETURNING user_id
    ↓
Result: {user_id: "usr789"}
    ↓
Tool: IssueSessionTokenTool("usr789")
    ↓
Response: "Account created! Welcome, Jane."
```

### Error Handling

```
Wrong OTP (3 attempts):
    otp_verification_attempts = 1
    Response: "That OTP didn't match. Try again (2 attempts left)."

    otp_verification_attempts = 2
    Response: "Not quite. One more try!"

    otp_verification_attempts = 3
    locked_until = now() + 15 minutes
    Response: "Too many failed attempts. Try again in 15 minutes."
```

---

## 5. customer_satisfaction_agent

### Overview

**What It Does:**
Handle complaints, feedback, NPS tracking.

**Why It Exists:**
Manage customer issues and sentiment post-order/booking.

**Type:** Monolithic

**Location:** `/app/agents/customer_satisfaction/node.py`

---

### Tools

| Tool | Purpose |
|------|---------|
| `RecordComplaintTool` | Store complaint in DB |
| `RecordFeedbackTool` | Store positive/neutral feedback |
| `RecordNPSTool` | Track Net Promoter Score |
| `GetComplaintStatusTool` | Check resolution status |
| `UpdateComplaintStatusTool` | Mark resolved/escalated |

---

### Flow Example - Complaint

```
User: "My food was cold"
    ↓
reasoning_node:
    Intent: complaint
    Category: food_quality
    ↓
Response: "I'm sorry to hear that! Which order was this?"

User: "Order ABC123"
    ↓
Tool: RecordComplaintTool(
    user_id="usr456",
    order_id="ABC123",
    category="food_quality",
    description="Food was cold",
    severity="medium"
)
    ↓
Database:
    INSERT INTO complaints (
        user_id,
        order_id,
        category,
        description,
        severity,
        status: "open"
    )
    ↓
Result: {complaint_id: "cmp789"}
    ↓
Response: "I've recorded your complaint (ref: CMP789).
           We'll look into this. Can I offer you a 20%
           discount on your next order as an apology?"
```

### Flow Example - Positive Feedback

```
User: "The food was amazing!"
    ↓
Tool: RecordFeedbackTool(
    user_id="usr456",
    type="positive",
    comment="The food was amazing!",
    sentiment_score=0.95
)
    ↓
Database:
    INSERT INTO feedback (type, comment, sentiment_score)
    ↓
Response: "Thank you so much! We're thrilled you enjoyed it!"
```

### Flow Example - NPS

```
(After order completion - proactive)

Response: "On a scale of 0-10, how likely are you to
           recommend us to a friend?"

User: "9"
    ↓
Tool: RecordNPSTool(
    user_id="usr456",
    score=9,
    order_id="ABC123"
)
    ↓
Database:
    INSERT INTO nps_scores (user_id, score, order_id)
    ↓
Response: "Thanks for the feedback!"
```

---

## 6. support_agent

### Overview

**What It Does:**
General support - hours, location, policies.

**Why It Exists:**
Answer non-transactional queries about restaurant.

**Type:** Monolithic

**Location:** `/app/agents/support/node.py`

---

### Tools

| Tool | Purpose |
|------|---------|
| `GetRestaurantInfoTool` | Hours, location, contact |
| `GetPoliciesTool` | Cancellation, refund policies |
| `GetFAQsTool` | Common questions |

---

### Flow Example

```
User: "What are your hours?"
    ↓
Tool: GetRestaurantInfoTool(query="hours")
    ↓
Database/Config:
    {
        hours: "10 AM - 11 PM (Mon-Sun)",
        location: "123 Main St",
        phone: "1234567890"
    }
    ↓
Response: "We're open 10 AM to 11 PM every day!"
```

---

## 7. general_queries_agent

### Overview

**What It Does:**
FAQs, policies (structured Q&A).

**Why It Exists:**
Handle common questions with structured responses.

**Type:** Monolithic

**Location:** `/app/agents/general_queries/node.py`

---

### Tools

Similar to support_agent but more FAQ-focused.

---

### Flow Example

```
User: "Do you deliver?"
    ↓
Tool: GetFAQsTool(query="delivery")
    ↓
FAQ Database:
    SELECT answer FROM faqs WHERE keywords LIKE '%delivery%'
    ↓
Result: "We offer dine-in and takeout. Delivery coming soon!"
    ↓
Response: "Currently we offer dine-in and takeout.
           Delivery service is coming soon!"
```

---

## 8. response_agent (Virtual Waiter)

### Overview

**What It Does:**
Format ALL agent responses with consistent personality.

**Why It Exists:**
Ensure unified voice across all interactions.

**Type:** Special (formatting layer)

**Location:** `/app/agents/response/`

---

### Architecture

```
All Agents
    ↓
Return ActionResult: {action, success, data}
    ↓
Response Agent
    ├─ Extract action type
    ├─ Select template from ACTION_PROMPTS
    ├─ Apply Virtual Waiter personality
    ├─ Format with GPT-4o
    └─ Return user-facing message
```

---

### Personality

**System Prompt:**
- Casual & warm (neighborhood restaurant vibe)
- Enthusiastic about food
- Brief and natural (2-3 sentences)
- NO EMOJIS
- Answer direct questions first, then upsell

---

### Templates (Examples)

**Success Actions:**
```
"item_added":
    "Great choice! Added Butter Chicken (₹320) to your cart.
     Want to add anything else?"

"booking_created":
    "Awesome! Got you all set for 4 people this Saturday at 7pm.
     Can't wait to see you!"

"order_placed":
    "Perfect! Your order should be ready in about 25 minutes.
     You're gonna love it!"
```

**Error Actions:**
```
"database_error":
    "Oops, our system hiccupped for a sec.
     Give me a moment to try that again?"

"inventory_error":
    "Oh no! We just ran out of that one. But I can show you
     similar options that are just as good - want to take a look?"

"invalid_data_error":
    "Just need to double-check that phone number -
     it should be 10 digits like 9876543210. Can you try again?"
```

---

### Flow

```
INPUT: ActionResult from food_ordering_agent
{
    action: "item_added",
    data: {item_name: "Butter Chicken", price: 320, ...}
}
    ↓
Step 1: Select Template
    template = ACTION_PROMPTS["item_added"]
    ↓
Step 2: Format Data
    details = format_data(data)
    → "Butter Chicken, ₹320, cart total ₹790"
    ↓
Step 3: Call GPT-4o
    System: VIRTUAL_WAITER_SYSTEM_PROMPT
    User: template.format(details=details)
    ↓
Step 4: Get Response
    GPT-4o: "Great choice! Added Butter Chicken (₹320) to your cart.
             Your total is now ₹790. Want to add some garlic naan?"
    ↓
OUTPUT: User sees natural, friendly message
```

---

## Comparison Tables

### Agent Responsibilities Summary

| Agent | Primary Function | Key Operations | Typical Output |
|-------|-----------------|----------------|----------------|
| **food_ordering** | Complete food ordering | Browse, search, cart, checkout | Order confirmation |
| **booking** | Table reservations | Availability, create, modify | Booking confirmation |
| **payment** | Payment processing | Generate link, verify | Payment URL |
| **user** | Authentication | Phone + OTP, registration | Session token |
| **customer_satisfaction** | Complaints & feedback | Record, track, resolve | Ticket ID |
| **support** | General help | Hours, policies, info | Informational |
| **general_queries** | FAQs | Structured Q&A | FAQ answer |
| **response** | Response formatting | Apply personality | User-friendly message |

---

### Tool Inventory by Agent

| Agent | Tool Count | Key Tools |
|-------|------------|-----------|
| food_ordering | 15+ | SemanticMenuSearch, AddToCart, ValidateCart, PlaceOrder |
| booking | 6 | CheckAvailability, CreateBooking, SendConfirmation |
| payment | 4 | CreatePaymentLink, CheckPaymentStatus, ProcessRefund |
| user | 6 | ValidatePhone, CheckUserExists, SendOTP, VerifyOTP |
| customer_satisfaction | 5 | RecordComplaint, RecordFeedback, RecordNPS |
| support | 3 | GetRestaurantInfo, GetPolicies, GetFAQs |
| general_queries | 2 | GetFAQs, SearchFAQs |
| response | 0 | (Formatting only, no tools) |

---

### State Updates by Agent

| Agent | State Fields Updated |
|-------|---------------------|
| food_ordering | `cart_items`, `cart_subtotal`, `cart_validated`, `cart_locked`, `draft_order_id` |
| booking | `booking_id`, `booking_confirmed` |
| payment | `payment_link`, `payment_status` |
| user | `is_authenticated`, `user_id`, `session_token`, `phone_number` |
| customer_satisfaction | None (records to DB only) |
| support | None (read-only) |
| general_queries | None (read-only) |
| response | `agent_response` |

---

### Hierarchical vs Monolithic

| Aspect | Hierarchical (food_ordering) | Monolithic (booking) |
|--------|------------------------------|----------------------|
| **File Size** | ~2000 lines (split across 5 sub-agents) | 1,929 lines (single file) |
| **Maintainability** | ✅ Easy (change one sub-agent) | ❌ Hard (find logic in large file) |
| **Testing** | ✅ Test each sub-agent independently | ❌ Must test entire agent |
| **Responsibilities** | ✅ Clear (one per sub-agent) | ❌ Mixed (all in one) |
| **Scalability** | ✅ Add new sub-agent easily | ❌ Add more conditions (spaghetti) |
| **Routing** | ✅ LLM-based classification | ❌ Manual if/else |
| **Code Duplication** | ✅ Minimal | ❌ High |
| **Onboarding** | ✅ Easy to understand flow | ❌ Overwhelming |

---

## Migration Roadmap

### Completed Migrations
- ✅ **food_ordering_agent** - Fully hierarchical with 5 sub-agents

### Pending Migrations

#### Priority 1: booking_agent
```
Current: 1,929 lines monolithic
Target: Hierarchical with 4 sub-agents
    ├─ availability_checker
    ├─ booking_creator
    ├─ booking_manager (modify/cancel)
    └─ waitlist_manager
```

#### Priority 2: customer_satisfaction_agent
```
Current: ~500 lines monolithic
Target: Hierarchical with 3 sub-agents
    ├─ complaint_handler
    ├─ feedback_collector
    └─ nps_tracker
```

#### Priority 3: Others
- payment_agent (low priority - simple enough)
- user_agent (low priority - simple enough)
- support/general_queries (can remain simple)

---

## Key Takeaways

1. **food_ordering_agent** shows the modern pattern - use this as template

2. **booking_agent** shows the legacy pattern - avoid this

3. **response_agent** is special - all responses go through it for unified voice

4. Hierarchical > Monolithic for complex workflows

5. Each sub-agent should be < 300 lines and have ONE clear responsibility

6. Use LLM-based classification for sub-intent routing

7. State guardrails prevent bad flows (empty cart checkout, etc.)

8. Entity validation happens at orchestration level (before agents)

9. All agents return ActionResult format for consistency

10. Tools should be stateless - state management at agent level

---

**END OF DOCUMENT**
