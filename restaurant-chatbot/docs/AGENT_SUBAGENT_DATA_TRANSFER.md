# AGENT TO SUB-AGENT DATA TRANSFER & VICE VERSA
**Complete Data Flow Architecture**

---

## TABLE OF CONTENTS

1. [Overview](#overview)
2. [Architecture Pattern: State Extension](#architecture-pattern)
3. [Complete Data Flow (End-to-End)](#complete-data-flow)
4. [State Conversion Mechanics](#state-conversion-mechanics)
5. [All 5 Sub-Agents (Tools, Inputs, Outputs)](#all-sub-agents)
6. [Complete Multi-Turn Example](#complete-example)
7. [Storage Tracking at Every Step](#storage-tracking)
8. [Return Flow (ActionResult Propagation)](#return-flow)
9. [Architecture Diagrams](#architecture-diagrams)
10. [Database Operations](#database-operations)

---

## 1. OVERVIEW {#overview}

### What is Agent-to-Sub-Agent Data Transfer?

**Parent Agent**: Food Ordering Agent (handles food domain)
**Sub-Agents**: 5 specialized agents for specific tasks
  - Menu Browsing
  - Menu Discovery
  - Cart Management
  - Checkout Validator
  - Checkout Executor

**Data Transfer Challenge**:
- Parent agent operates on **FoodOrderingState** (extended state)
- Orchestrator operates on **AgentState** (base state)
- Need to convert between them bidirectionally

**Flow Direction**:
```
Orchestrator (AgentState)
    ↓
Parent Agent (FoodOrderingState)
    ↓
Sub-Agent (FoodOrderingState + entities dict)
    ↓
Tools (Database queries)
    ↓
ActionResult (back to parent)
    ↓
Orchestrator (merged into AgentState)
```

---

## 2. ARCHITECTURE PATTERN: STATE EXTENSION {#architecture-pattern}

### The State Extension Pattern

The system uses **state inheritance** to add domain-specific fields:

```python
# Base State (used by orchestrator)
class AgentState(TypedDict, total=False):
    messages: Sequence[BaseMessage]
    session_id: str
    user_id: Optional[str]
    task_entities: Dict[str, Any]
    action_result: Optional[Dict[str, Any]]
    agent_response: Optional[str]
    # ... 50+ other fields

# Extended State (used by food ordering sub-graph)
class FoodOrderingState(AgentState, total=False):
    """Inherits ALL fields from AgentState + adds domain-specific"""

    # Sub-intent classification
    current_sub_intent: Optional[str]
    sub_intent_confidence: float

    # Cart state (MongoDB/Redis)
    cart_items: List[Dict[str, Any]]
    cart_subtotal: float
    cart_item_count: int
    cart_locked: bool
    cart_validated: bool

    # Order state (PostgreSQL)
    order_type: Optional[Literal["dine_in", "takeout"]]
    draft_order_id: Optional[str]
    order_number: Optional[str]

    # ReAct agent controls
    agent_mode: Optional[Literal["deterministic", "react", "parallel"]]
    react_agent_enabled: bool
    force_agent_mode: Optional[str]

    # Entity collection
    entity_collection_step: Optional[str]

    # ... 30+ domain-specific fields
```

**Key Insight**:
- FoodOrderingState **extends** AgentState (has all parent fields)
- Sub-agents receive **both** base fields + domain fields
- Conversion happens at the **node wrapper** level

---

## 3. COMPLETE DATA FLOW (END-TO-END) {#complete-data-flow}

### Step-by-Step Data Transfer

```
┌────────────────────────────────────────────────────────────────┐
│ STEP 1: User Message Arrives                                   │
│ Location: Main Orchestrator Graph                              │
└────────────────────────────────────────────────────────────────┘
  User: "Add 2 butter chicken to my cart"

  AgentState (in MemorySaver checkpoint):
  {
    "messages": [...],
    "session_id": "session_123",
    "user_id": "user_456",
    "current_intent": "food_ordering",
    "cart_items": [],  # Empty cart
    "cart_subtotal": 0.0,
    "agent_response": null
  }

┌────────────────────────────────────────────────────────────────┐
│ STEP 2: Intent Classifier Routes to Food Ordering              │
│ Location: app/orchestration/intent_classifier.py               │
└────────────────────────────────────────────────────────────────┘
  Intent Classification Result:
  {
    "intent": "food_ordering",
    "confidence": 0.95,
    "entities": {"item_name": "butter chicken", "quantity": 2}
  }

  Updated AgentState:
  {
    "current_intent": "food_ordering",
    "task_entities": {"item_name": "butter chicken", "quantity": 2}
  }

┌────────────────────────────────────────────────────────────────┐
│ STEP 3: Orchestrator Calls Food Ordering Node Wrapper          │
│ Location: app/agents/food_ordering/node.py                     │
│ Function: food_ordering_agent_node(state: AgentState)          │
└────────────────────────────────────────────────────────────────┘

  CODE:
  ```python
  async def food_ordering_agent_node(state: AgentState) -> Dict[str, Any]:
      """
      LangGraph node wrapper that:
      1. Converts AgentState → FoodOrderingState
      2. Calls food ordering sub-graph
      3. Returns ActionResult to orchestrator
      """

      # Extract latest user message
      messages = state.get("messages", [])
      latest_message = messages[-1].content if messages else ""

      # CONVERSION: AgentState → FoodOrderingState
      food_state = FoodOrderingState(
          # Copy ALL base fields from AgentState
          session_id=state.get("session_id"),
          user_id=state.get("user_id"),
          messages=messages,
          task_entities=state.get("task_entities", {}),

          # Copy food-specific fields (if they exist in AgentState)
          cart_items=state.get("cart_items", []),
          cart_subtotal=state.get("cart_subtotal", 0.0),
          cart_item_count=state.get("cart_item_count", 0),
          cart_validated=state.get("cart_validated", False),
          cart_locked=state.get("cart_locked", False),

          order_type=state.get("order_type"),
          draft_order_id=state.get("draft_order_id"),
          order_number=state.get("order_number"),

          current_sub_intent=state.get("current_sub_intent"),
          sub_intent_confidence=state.get("sub_intent_confidence", 0.0),

          # ReAct configuration
          agent_mode=state.get("agent_mode"),
          react_agent_enabled=state.get("react_agent_enabled", False)
      )

      # Call sub-graph with converted state
      result = await food_ordering_agent(latest_message, food_state)

      # Return ActionResult to orchestrator
      return {"action_result": result}
  ```

  CONVERTED FoodOrderingState (passed to parent agent):
  {
    # Base fields (from AgentState)
    "session_id": "session_123",
    "user_id": "user_456",
    "messages": [...],
    "task_entities": {"item_name": "butter chicken", "quantity": 2},

    # Domain-specific fields
    "cart_items": [],
    "cart_subtotal": 0.0,
    "cart_item_count": 0,
    "cart_validated": False,
    "order_type": null,
    "current_sub_intent": null
  }

┌────────────────────────────────────────────────────────────────┐
│ STEP 4: Parent Agent (Food Ordering) Processes Request         │
│ Location: app/agents/food_ordering/graph.py                    │
│ Function: food_ordering_agent()                                │
└────────────────────────────────────────────────────────────────┘

  Sub-Steps:

  4.1 - SUB-INTENT CLASSIFICATION (LLM Call)
  ─────────────────────────────────────────────────────
  Location: app/agents/food_ordering/sub_intent_classifier.py

  Input:
    - user_message: "Add 2 butter chicken to my cart"
    - state: FoodOrderingState (full context)

  LLM Prompt Context:
  ```
  Context:
  - Cart is EMPTY
  - User NOT authenticated
  - No order type set

  Message: "Add 2 butter chicken to my cart"

  Classify into: browse_menu, discover_items, manage_cart, validate_order, execute_checkout
  ```

  LLM Response (Structured Output):
  ```python
  SubIntentClassification(
      sub_intent="manage_cart",
      confidence=0.98,
      entities={
          "action": "add",
          "item_name": "butter chicken",
          "quantity": 2
      },
      missing_entities=[]
  )
  ```

  4.2 - ENTITY MERGING
  ─────────────────────────────────────────────────────
  Location: app/agents/food_ordering/entity_validator.py

  Merge entities from classification + state:
  ```python
  entities = {
      "action": "add",
      "item_name": "butter chicken",
      "quantity": 2,
      # No additional entities from state needed
  }
  ```

  4.3 - ENTITY VALIDATION
  ─────────────────────────────────────────────────────
  Check for required entities:

  Sub-Intent: manage_cart
  Action: add
  Required: ["action", "item_name", "quantity"]
  Provided: ["action", "item_name", "quantity"]

  Validation Result: ✓ PASS (all entities present)

  4.4 - GUARDRAIL CHECKS
  ─────────────────────────────────────────────────────
  Apply state-based guardrails:

  Check: Cart locked? → NO (cart_locked = False)
  Check: Empty cart checkout? → NO (sub_intent != validate_order)

  Guardrail Result: ✓ PASS (proceed to agent routing)

  4.5 - AGENT ROUTING (Deterministic)
  ─────────────────────────────────────────────────────
  Location: app/agents/food_ordering/router.py

  Routing Map:
  ```python
  {
      "browse_menu": menu_browsing_agent,
      "discover_items": menu_discovery_agent,
      "manage_cart": cart_management_agent,  # ← Selected
      "validate_order": checkout_validator_agent,
      "execute_checkout": checkout_executor_agent
  }
  ```

  Selected Agent: cart_management_agent

┌────────────────────────────────────────────────────────────────┐
│ STEP 5: Sub-Agent Execution (Cart Management)                  │
│ Location: app/agents/food_ordering/agents/cart_management/node.py │
│ Function: cart_management_agent(entities, state)               │
└────────────────────────────────────────────────────────────────┘

  Sub-Agent Receives:
  1. entities: Dict[str, Any] (extracted entities)
  2. state: FoodOrderingState (full state with all fields)

  Input Data:
  ```python
  entities = {
      "action": "add",
      "item_name": "butter chicken",
      "quantity": 2
  }

  state = FoodOrderingState(
      session_id="session_123",
      user_id="user_456",
      cart_items=[],  # Empty cart
      cart_subtotal=0.0,
      # ... all other state fields
  )
  ```

  Sub-Agent Logic:

  5.1 - ACTION ROUTING
  ─────────────────────────────────────────────────────
  ```python
  action = entities.get("action", "view")

  if action == "add":
      return await _handle_add_to_cart(entities, state, session_id)
  elif action == "remove":
      return await _handle_remove_from_cart(entities, state, session_id)
  elif action == "view":
      return await _handle_view_cart(entities, state, session_id)
  # ... other actions
  ```

  5.2 - TOOL EXECUTION (Add to Cart)
  ─────────────────────────────────────────────────────
  Location: app/tools/database/cart_tools.py
  Tool: AddToCartTool

  Tool receives:
  ```python
  {
      "session_id": "session_123",
      "item_name": "butter chicken",
      "quantity": 2
  }
  ```

  Tool executes:

  A) SEARCH FOR ITEM (Redis Menu Cache)
  ───────────────────────────────────────
  Query: Get item from menu cache
  Location: Redis
  Key: menu:item:butter_chicken

  Result:
  ```python
  {
      "item_id": "item_789",
      "name": "Butter Chicken",
      "price": 350.0,
      "category": "main_course",
      "is_available": True
  }
  ```

  B) CHECK INVENTORY (Redis Inventory Cache)
  ───────────────────────────────────────
  Query: Check if 2 units available
  Location: Redis
  Key: inventory:item_789

  Result:
  ```python
  {
      "item_id": "item_789",
      "available_quantity": 15,
      "reserved_quantity": 3,
      "stock_available": True
  }
  ```

  Availability: ✓ YES (15 available >= 2 requested)

  C) RESERVE INVENTORY
  ───────────────────────────────────────
  Redis Operation:
  - DECR inventory:item_789:available by 2
  - INCR inventory:item_789:reserved:session_123 by 2
  - SET with 15-minute TTL

  D) GET CURRENT CART (Redis)
  ───────────────────────────────────────
  Location: Redis
  Key: cart:session_123

  Current Value: NULL (empty cart)

  E) ADD ITEM TO CART (Redis)
  ───────────────────────────────────────
  Redis SET operation:
  Key: cart:session_123
  Value:
  ```json
  {
    "items": [
      {
        "item_id": "item_789",
        "name": "Butter Chicken",
        "price": 350.0,
        "quantity": 2,
        "subtotal": 700.0,
        "added_at": "2025-01-14T10:30:00Z"
      }
    ],
    "subtotal": 700.0,
    "item_count": 1,
    "updated_at": "2025-01-14T10:30:00Z"
  }
  ```
  TTL: 30 minutes

  Tool Result:
  ```python
  ToolResult(
      status=ToolStatus.SUCCESS,
      data={
          "cart_items": [
              {
                  "item_id": "item_789",
                  "name": "Butter Chicken",
                  "price": 350.0,
                  "quantity": 2,
                  "subtotal": 700.0
              }
          ],
          "cart_subtotal": 700.0,
          "item_count": 1,
          "message": "Added 2 x Butter Chicken to your cart"
      }
  )
  ```

┌────────────────────────────────────────────────────────────────┐
│ STEP 6: Sub-Agent Returns ActionResult                         │
│ Location: app/agents/food_ordering/agents/cart_management/node.py │
└────────────────────────────────────────────────────────────────┘

  Sub-Agent Constructs ActionResult:
  ```python
  return {
      "action": "item_added_to_cart",
      "success": True,
      "data": {
          "item_name": "Butter Chicken",
          "quantity": 2,
          "item_price": 350.0,
          "cart_items": [
              {
                  "item_id": "item_789",
                  "name": "Butter Chicken",
                  "price": 350.0,
                  "quantity": 2,
                  "subtotal": 700.0
              }
          ],
          "cart_subtotal": 700.0,
          "item_count": 1,
          "message": "Added 2 x Butter Chicken to your cart (₹700)"
      },
      "context": {
          "sub_intent": "manage_cart",
          "action": "add",
          "item_id": "item_789"
      },
      # STATE UPDATES (merged back into FoodOrderingState)
      "cart_items": [{"item_id": "item_789", "name": "Butter Chicken", ...}],
      "cart_subtotal": 700.0,
      "cart_item_count": 1
  }
  ```

┌────────────────────────────────────────────────────────────────┐
│ STEP 7: Parent Agent Receives ActionResult                     │
│ Location: app/agents/food_ordering/graph.py                    │
└────────────────────────────────────────────────────────────────┘

  Parent agent receives ActionResult from sub-agent and enhances it:

  ```python
  # Add classification metadata
  agent_result.setdefault("context", {})
  agent_result["context"]["sub_intent"] = "manage_cart"
  agent_result["context"]["confidence"] = 0.98

  return agent_result
  ```

  Final ActionResult from parent:
  ```python
  {
      "action": "item_added_to_cart",
      "success": True,
      "data": {
          "item_name": "Butter Chicken",
          "quantity": 2,
          "cart_items": [...],
          "cart_subtotal": 700.0,
          "item_count": 1,
          "message": "Added 2 x Butter Chicken to your cart (₹700)"
      },
      "context": {
          "sub_intent": "manage_cart",
          "confidence": 0.98,
          "action": "add",
          "item_id": "item_789"
      },
      "cart_items": [...],
      "cart_subtotal": 700.0,
      "cart_item_count": 1
  }
  ```

┌────────────────────────────────────────────────────────────────┐
│ STEP 8: Node Wrapper Returns to Orchestrator                   │
│ Location: app/agents/food_ordering/node.py                     │
└────────────────────────────────────────────────────────────────┘

  Node wrapper returns ActionResult to orchestrator:

  ```python
  return {
      "action_result": agent_result  # Full ActionResult dict
  }
  ```

┌────────────────────────────────────────────────────────────────┐
│ STEP 9: Orchestrator Merges ActionResult into AgentState       │
│ Location: app/orchestration/graph.py                           │
└────────────────────────────────────────────────────────────────┘

  Orchestrator receives:
  ```python
  {
      "action_result": {
          "action": "item_added_to_cart",
          "data": {...},
          "cart_items": [...],
          "cart_subtotal": 700.0,
          ...
      }
  }
  ```

  Orchestrator merges into AgentState:

  BEFORE:
  ```python
  AgentState(
      session_id="session_123",
      cart_items=[],
      cart_subtotal=0.0,
      action_result=None
  )
  ```

  AFTER:
  ```python
  AgentState(
      session_id="session_123",
      cart_items=[{"item_id": "item_789", "name": "Butter Chicken", ...}],
      cart_subtotal=700.0,
      cart_item_count=1,
      action_result={
          "action": "item_added_to_cart",
          "success": True,
          "data": {...}
      }
  )
  ```

  LangGraph's state reducer automatically merges fields from ActionResult
  into AgentState using the update pattern defined in StateGraph.

┌────────────────────────────────────────────────────────────────┐
│ STEP 10: Checkpoint Saved                                      │
│ Location: MemorySaver (in-memory persistence)                  │
└────────────────────────────────────────────────────────────────┘

  LangGraph saves checkpoint:

  Checkpoint Key: (thread_id="session_123", checkpoint_id="checkpoint_4")

  Saved State:
  ```python
  {
      "messages": [
          HumanMessage("Add 2 butter chicken to my cart"),
          # ... previous messages
      ],
      "session_id": "session_123",
      "user_id": "user_456",
      "current_intent": "food_ordering",
      "cart_items": [
          {
              "item_id": "item_789",
              "name": "Butter Chicken",
              "price": 350.0,
              "quantity": 2,
              "subtotal": 700.0
          }
      ],
      "cart_subtotal": 700.0,
      "cart_item_count": 1,
      "action_result": {
          "action": "item_added_to_cart",
          "success": True,
          "data": {...}
      },
      # ... all other state fields
  }
  ```

┌────────────────────────────────────────────────────────────────┐
│ STEP 11: Response Agent Formats Response                       │
│ Location: app/agents/response/node.py                          │
└────────────────────────────────────────────────────────────────┘

  Response Agent receives ActionResult and formats user-facing message:

  Input:
  ```python
  action_result = {
      "action": "item_added_to_cart",
      "success": True,
      "data": {
          "message": "Added 2 x Butter Chicken to your cart (₹700)",
          "cart_subtotal": 700.0,
          "item_count": 1
      }
  }
  ```

  Response Agent generates:
  ```
  ✓ Added 2 x Butter Chicken to your cart!

  Your cart now has 1 item (₹700)

  What else would you like to add?
  ```

  Stored in:
  - state["agent_response"] = formatted message
  - state["messages"].append(AIMessage(formatted message))

┌────────────────────────────────────────────────────────────────┐
│ STEP 12: Response Returned to User                             │
│ Location: API Response                                         │
└────────────────────────────────────────────────────────────────┘

  Final API Response:
  ```json
  {
    "session_id": "session_123",
    "response": "✓ Added 2 x Butter Chicken to your cart!\n\nYour cart now has 1 item (₹700)\n\nWhat else would you like to add?",
    "cart_summary": {
      "items": [
        {
          "item_id": "item_789",
          "name": "Butter Chicken",
          "quantity": 2,
          "subtotal": 700.0
        }
      ],
      "subtotal": 700.0,
      "item_count": 1
    },
    "success": true
  }
  ```
```

---

## 4. STATE CONVERSION MECHANICS {#state-conversion-mechanics}

### How AgentState Becomes FoodOrderingState

**Location**: `app/agents/food_ordering/node.py`

**Conversion Function**:

```python
async def food_ordering_agent_node(state: AgentState) -> Dict[str, Any]:
    """
    Node wrapper that converts AgentState → FoodOrderingState

    CRITICAL: This is the ONLY place where conversion happens
    """

    # Step 1: Extract latest user message
    messages = state.get("messages", [])
    latest_message = ""
    if messages:
        last_msg = messages[-1]
        latest_message = last_msg.content if hasattr(last_msg, 'content') else str(last_msg)

    # Step 2: Build FoodOrderingState (extended state)
    food_state = FoodOrderingState(
        # ═══════════════════════════════════════════════════════════
        # BASE FIELDS (inherited from AgentState)
        # ═══════════════════════════════════════════════════════════
        session_id=state.get("session_id"),
        user_id=state.get("user_id"),
        messages=messages,
        task_entities=state.get("task_entities", {}),
        current_intent=state.get("current_intent"),

        # ═══════════════════════════════════════════════════════════
        # FOOD ORDERING DOMAIN FIELDS
        # ═══════════════════════════════════════════════════════════

        # Cart state (from AgentState if present)
        cart_items=state.get("cart_items", []),
        cart_subtotal=state.get("cart_subtotal", 0.0),
        cart_item_count=state.get("cart_item_count", 0),
        cart_tax=state.get("cart_tax", 0.0),
        cart_total=state.get("cart_total", 0.0),
        cart_validated=state.get("cart_validated", False),
        cart_locked=state.get("cart_locked", False),

        # Order state
        order_type=state.get("order_type"),
        draft_order_id=state.get("draft_order_id"),
        order_number=state.get("order_number"),

        # Sub-intent tracking
        current_sub_intent=state.get("current_sub_intent"),
        sub_intent_confidence=state.get("sub_intent_confidence", 0.0),

        # Entity collection (multi-turn)
        entity_collection_step=state.get("entity_collection_step"),

        # ReAct configuration
        agent_mode=state.get("agent_mode"),
        react_agent_enabled=state.get("react_agent_enabled", False),
        force_agent_mode=state.get("force_agent_mode"),

        # User preferences
        dietary_restrictions=state.get("dietary_restrictions", []),
        spice_preference=state.get("spice_preference"),
        favorite_cuisines=state.get("favorite_cuisines", []),

        # Authentication state
        must_authenticate=state.get("must_authenticate", False),
        contact_phone=state.get("contact_phone"),
        device_id=state.get("device_id")
    )

    # Step 3: Call sub-graph with converted state
    result = await food_ordering_agent(latest_message, food_state)

    # Step 4: Return ActionResult to orchestrator
    # Any state updates in ActionResult will be merged into AgentState
    return {"action_result": result}
```

### Field Mapping Table

| AgentState Field | FoodOrderingState Field | Source | Notes |
|------------------|-------------------------|--------|-------|
| `session_id` | `session_id` | Copied | Required for all operations |
| `user_id` | `user_id` | Copied | May be None if not authenticated |
| `messages` | `messages` | Copied | Full conversation history |
| `task_entities` | `task_entities` | Copied | Extracted entities from intent classifier |
| `cart_items` | `cart_items` | Copied | Persisted across requests |
| `cart_subtotal` | `cart_subtotal` | Copied | Calculated field |
| `order_type` | `order_type` | Copied | dine_in or takeout |
| `draft_order_id` | `draft_order_id` | Copied | Set after checkout |
| `current_sub_intent` | `current_sub_intent` | Copied | browse_menu, discover_items, etc. |
| (none) | `cart_validated` | New | Food-specific field |
| (none) | `cart_locked` | New | Food-specific field |
| (none) | `agent_mode` | New | ReAct configuration |

**Key Points**:
1. **All AgentState fields are available** in FoodOrderingState (inheritance)
2. **Food-specific fields** are added on top
3. **Conversion is bidirectional**: ActionResult updates flow back to AgentState
4. **No data loss**: All state is preserved through conversion

---

## 5. ALL 5 SUB-AGENTS {#all-sub-agents}

### Sub-Agent 1: Menu Browsing Agent

**Location**: `app/agents/food_ordering/agents/menu_browsing/node.py`

**Purpose**: Navigate menu structure and categories

**Input Signature**:
```python
async def menu_browsing_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]
```

**Input Data**:
```python
entities = {
    "category_name": Optional[str]  # e.g., "appetizers", "main course"
}

state = FoodOrderingState(
    session_id="session_123",
    user_id="user_456",
    # ... all other state fields
)
```

**Tools Used**:
1. **GetMenuCategoryTool** - Get all menu categories
2. **ListMenuTool** - Get full menu with all items
3. **GetMenuItemTool** - Get items in specific category

**Database Operations**:
```sql
-- GetMenuCategoryTool (PostgreSQL)
SELECT category_id, name, description, display_order
FROM menu_categories
WHERE is_active = true
ORDER BY display_order;

-- GetMenuItemTool (PostgreSQL)
SELECT
    mi.item_id,
    mi.name,
    mi.description,
    mi.price,
    mi.category_id,
    mc.name as category_name
FROM menu_items mi
JOIN menu_categories mc ON mi.category_id = mc.category_id
WHERE mi.category_id = $1
  AND mi.is_available = true
ORDER BY mi.display_order;
```

**Output (ActionResult)**:
```python
{
    "action": "category_browsed",  # or "menu_displayed"
    "success": True,
    "data": {
        "category": {
            "category_id": "cat_123",
            "name": "Appetizers",
            "description": "Start your meal right"
        },
        "items": [
            {
                "item_id": "item_456",
                "name": "Samosa",
                "price": 80.0,
                "description": "Crispy pastry filled with spiced potatoes"
            },
            # ... more items
        ],
        "item_count": 8,
        "message": "Here are the items in Appetizers"
    },
    "context": {
        "current_category": "Appetizers",
        "browsing_mode": "category",
        "sub_intent": "browse_menu",
        "confidence": 0.95
    }
}
```

**When Used**:
- "Show me the menu"
- "What categories do you have?"
- "What's in appetizers?"
- "Browse main course"

---

### Sub-Agent 2: Menu Discovery Agent

**Location**: `app/agents/food_ordering/agents/menu_discovery/node.py`

**Purpose**: Intelligent menu search, filtering, and personalized recommendations

**Input Signature**:
```python
async def menu_discovery_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]
```

**Input Data**:
```python
entities = {
    "search_query": Optional[str],  # e.g., "spicy", "chicken"
    "dietary_restrictions": Optional[List[str]],  # ["vegetarian", "vegan"]
    "price_range": Optional[Dict[str, float]],  # {"min": 100, "max": 300}
    "category_name": Optional[str]  # Filter by category
}

state = FoodOrderingState(
    session_id="session_123",
    dietary_restrictions=["vegetarian"],  # User preferences from state
    spice_preference="medium",
    favorite_cuisines=["indian", "chinese"],
    # ... all other fields
)
```

**Tools Used**:
1. **SemanticMenuSearchTool** - AI-powered natural language search
2. **SmartDietaryFilterTool** - Filter by dietary requirements
3. **PriceRangeMenuTool** - Filter by price range
4. **PersonalizedRecommendationTool** - Generate recommendations
5. **FindSimilarItemsTool** - Find similar items

**Database Operations**:
```sql
-- SemanticMenuSearchTool (PostgreSQL + pgvector)
SELECT
    item_id,
    name,
    description,
    price,
    embedding <=> $1 as similarity
FROM menu_items
WHERE is_available = true
ORDER BY embedding <=> $1
LIMIT 10;

-- SmartDietaryFilterTool (PostgreSQL)
SELECT
    mi.item_id,
    mi.name,
    mi.price,
    mi.dietary_tags
FROM menu_items mi
WHERE mi.is_available = true
  AND mi.dietary_tags @> $1  -- Array contains dietary restrictions
ORDER BY mi.popularity_score DESC
LIMIT 20;

-- PriceRangeMenuTool (PostgreSQL)
SELECT item_id, name, price, description
FROM menu_items
WHERE is_available = true
  AND price BETWEEN $1 AND $2
ORDER BY price ASC
LIMIT 15;
```

**Output (ActionResult)**:
```python
{
    "action": "search_results",  # or "filtered_results", "recommendations"
    "success": True,
    "data": {
        "items": [
            {
                "item_id": "item_789",
                "name": "Butter Chicken",
                "price": 350.0,
                "description": "Tender chicken in creamy tomato gravy",
                "similarity_score": 0.87  # For semantic search
            },
            # ... more items
        ],
        "total_found": 5,
        "search_query": "creamy chicken",
        "message": "I found 5 items matching 'creamy chicken'"
    },
    "context": {
        "search_query": "creamy chicken",
        "results_count": 5,
        "sub_intent": "discover_items",
        "confidence": 0.92
    }
}
```

**When Used**:
- "Find something spicy"
- "Vegetarian options under ₹200"
- "Recommend something"
- "What's similar to butter chicken?"

---

### Sub-Agent 3: Cart Management Agent

**Location**: `app/agents/food_ordering/agents/cart_management/node.py`

**Purpose**: Add, remove, update, and view cart items

**Input Signature**:
```python
async def cart_management_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]
```

**Input Data**:
```python
entities = {
    "action": str,  # "add", "remove", "update", "view", "clear"
    "item_name": Optional[str],  # For add: "butter chicken"
    "item_id": Optional[str],  # For direct item reference
    "item_index": Optional[int],  # For remove: "remove item 2"
    "quantity": Optional[int]  # For add/update: 2
}

state = FoodOrderingState(
    session_id="session_123",
    cart_items=[...],  # Current cart state
    cart_subtotal=350.0,
    cart_locked=False,  # Can modify cart
    # ... all other fields
)
```

**Tools Used**:
1. **AddToCartTool** - Add item to cart
2. **RemoveFromCartTool** - Remove item from cart
3. **UpdateCartItemTool** - Update item quantity
4. **ViewCartTool** - View cart contents
5. **ClearCartTool** - Clear entire cart

**Database Operations**:
```python
# Redis Operations (cart stored in Redis)

# AddToCartTool
# 1. Get item from menu cache (Redis)
menu_cache.get("menu:item:item_789")
# Returns: {"item_id": "item_789", "name": "Butter Chicken", "price": 350.0}

# 2. Check inventory (Redis)
inventory_cache.check_availability("item_789", quantity=2)
# Redis: GET inventory:item_789
# Returns: {"available": 15, "reserved": 3}

# 3. Reserve inventory (Redis)
# DECR inventory:item_789:available by 2
# INCR inventory:item_789:reserved:session_123 by 2
# SET with 15-minute TTL

# 4. Update cart (Redis)
# SET cart:session_123 with TTL 30 minutes
redis.set("cart:session_123", {
    "items": [
        {
            "item_id": "item_789",
            "name": "Butter Chicken",
            "price": 350.0,
            "quantity": 2,
            "subtotal": 700.0
        }
    ],
    "subtotal": 700.0,
    "item_count": 1,
    "updated_at": "2025-01-14T10:30:00Z"
}, ttl=1800)
```

**Output (ActionResult)**:
```python
{
    "action": "item_added_to_cart",  # or "item_removed", "cart_updated", "cart_viewed"
    "success": True,
    "data": {
        "item_name": "Butter Chicken",
        "quantity": 2,
        "item_price": 350.0,
        "cart_items": [
            {
                "item_id": "item_789",
                "name": "Butter Chicken",
                "price": 350.0,
                "quantity": 2,
                "subtotal": 700.0
            }
        ],
        "cart_subtotal": 700.0,
        "item_count": 1,
        "message": "Added 2 x Butter Chicken to your cart (₹700)"
    },
    "context": {
        "sub_intent": "manage_cart",
        "action": "add",
        "item_id": "item_789"
    },
    # STATE UPDATES (merged back into state)
    "cart_items": [...],  # Updated cart
    "cart_subtotal": 700.0,
    "cart_item_count": 1
}
```

**When Used**:
- "Add 2 butter chicken"
- "Remove item 1"
- "Update quantity to 3"
- "Show my cart"
- "Clear cart"

---

### Sub-Agent 4: Checkout Validator Agent

**Location**: `app/agents/food_ordering/agents/checkout_validator/node.py`

**Purpose**: Validate cart before checkout (critical checkpoint)

**Input Signature**:
```python
async def checkout_validator_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]
```

**Input Data**:
```python
entities = {}  # No entities needed for validation

state = FoodOrderingState(
    session_id="session_123",
    cart_items=[...],  # Cart to validate
    cart_subtotal=700.0,
    cart_validated=False,  # Will be set to True if valid
    # ... all other fields
)
```

**Tools Used**:
1. **OrderValidationTool** - Validate cart (single tool)

**Database Operations**:
```python
# MongoDB + Redis Operations

# 1. Get cart from Redis
redis.get("cart:session_123")

# 2. Validate each item still available (Redis inventory cache)
for item in cart_items:
    inventory_cache.check_availability(item["item_id"], item["quantity"])

# 3. Check for minimum order amount (MongoDB config)
mongo.db.settings.find_one({"key": "min_order_amount"})
# Returns: {"value": 200}

# 4. Validate delivery/pickup time windows (MongoDB config)
mongo.db.settings.find_one({"key": "operating_hours"})

# 5. Calculate tax and total
# Tax rate from MongoDB: mongo.db.settings.find_one({"key": "tax_rate"})
```

**Output (ActionResult)**:
```python
{
    "action": "cart_validated",  # or "cart_validation_failed"
    "success": True,
    "data": {
        "valid": True,
        "message": "Your cart looks good! Ready to place your order?",
        "cart_summary": {
            "items": [...],
            "subtotal": 700.0,
            "tax": 126.0,  # 18% GST
            "total": 826.0
        }
    },
    "context": {
        "sub_intent": "validate_order",
        "confidence": 0.99
    },
    # STATE UPDATES
    "cart_validated": True,
    "validation_issues": [],
    "cart_tax": 126.0,
    "cart_total": 826.0
}

# If validation fails:
{
    "action": "cart_validation_failed",
    "success": False,
    "data": {
        "valid": False,
        "issues": [
            "Butter Chicken is no longer available",
            "Minimum order amount is ₹200"
        ],
        "message": "There are some issues with your cart: Butter Chicken is no longer available"
    },
    "context": {},
    # STATE UPDATES
    "cart_validated": False,
    "validation_issues": ["Butter Chicken is no longer available"]
}
```

**When Used**:
- "Checkout"
- "I'm ready to order"
- "Place my order"
- "Confirm order"

---

### Sub-Agent 5: Checkout Executor Agent

**Location**: `app/agents/food_ordering/agents/checkout_executor/node.py`

**Purpose**: Create draft order and initiate payment flow

**Input Signature**:
```python
async def checkout_executor_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]
```

**Input Data**:
```python
entities = {
    "order_type": str,  # REQUIRED: "dine_in" or "takeout"
    "special_instructions": Optional[str]  # "Extra spicy, no onions"
}

state = FoodOrderingState(
    session_id="session_123",
    user_id="user_456",
    cart_items=[...],
    cart_validated=True,  # MUST be validated first
    cart_subtotal=700.0,
    cart_tax=126.0,
    cart_total=826.0,
    contact_phone="+919876543210",  # From authentication
    # ... all other fields
)
```

**Tools Used**:
1. **CheckoutCartDraftTool** - Create draft order (single tool)

**Database Operations**:
```sql
-- PostgreSQL Operations

-- 1. Create draft order
INSERT INTO orders (
    order_number,
    user_id,
    session_id,
    order_type,
    status,
    subtotal,
    tax_amount,
    total_amount,
    contact_phone,
    device_id,
    special_instructions,
    created_at
) VALUES (
    'ORD-20250114-1234',
    'user_456',
    'session_123',
    'dine_in',
    'draft',  -- Status: draft (not confirmed yet)
    700.00,
    126.00,
    826.00,
    '+919876543210',
    'device_abc',
    'Extra spicy',
    NOW()
) RETURNING id, order_number;

-- 2. Insert order items
INSERT INTO order_items (
    order_id,
    item_id,
    item_name,
    quantity,
    unit_price,
    subtotal,
    special_instructions
) VALUES
    ($1, 'item_789', 'Butter Chicken', 2, 350.00, 700.00, NULL);

-- 3. Update order metadata
INSERT INTO order_metadata (
    order_id,
    key,
    value
) VALUES
    ($1, 'source', 'chatbot'),
    ($1, 'session_id', 'session_123'),
    ($1, 'cart_validated_at', NOW());
```

```python
# Redis Operations

# 1. Lock cart (prevent modifications during checkout)
redis.set("cart:session_123:locked", True, ttl=600)  # 10 minutes

# 2. Keep cart for reference (don't clear yet - payment may fail)
# Cart remains until payment success or timeout
```

**Output (ActionResult)**:
```python
{
    "action": "draft_order_created",
    "success": True,
    "data": {
        "order_id": "order_uuid_12345",
        "order_number": "ORD-20250114-1234",
        "order_type": "dine_in",
        "status": "draft",  # Not confirmed yet
        "items": [
            {
                "item_id": "item_789",
                "name": "Butter Chicken",
                "quantity": 2,
                "unit_price": 350.0,
                "subtotal": 700.0
            }
        ],
        "item_count": 1,
        "subtotal": 700.0,
        "tax_amount": 126.0,
        "total_amount": 826.0,
        "estimated_ready_time": "15-20 minutes",
        "message": "Your order #ORD-20250114-1234 has been created. Let's proceed with payment.",
        "next_step": "authentication"  # Signal to orchestrator
    },
    "context": {
        "draft_order_id": "order_uuid_12345",
        "order_number": "ORD-20250114-1234",
        "requires_payment": True,
        "sub_intent": "execute_checkout",
        "confidence": 0.99
    },
    # STATE UPDATES
    "draft_order_id": "order_uuid_12345",
    "order_number": "ORD-20250114-1234",
    "cart_locked": True,  # Cart is now locked
    "must_authenticate": True  # Trigger auth flow if not authenticated
}
```

**When Used**:
- After validation succeeds
- "Yes, place the order"
- "Confirm order for dine-in"
- "Checkout for takeout"

**Order Status Flow**:
```
draft → (authentication) → (payment) → confirmed → preparing → ready → completed
```

---

## 6. COMPLETE MULTI-TURN EXAMPLE {#complete-example}

Let's trace a complete 4-turn conversation with **full data tracking**:

### TURN 1: Show Menu

```
┌────────────────────────────────────────────────────────────────┐
│ USER MESSAGE: "Show me the menu"                               │
└────────────────────────────────────────────────────────────────┘

ORCHESTRATOR (AgentState):
─────────────────────────────────────────────────────────────────
{
  "messages": [HumanMessage("Show me the menu")],
  "session_id": "session_123",
  "user_id": null,
  "current_intent": "food_ordering",  # From intent classifier
  "cart_items": [],
  "cart_subtotal": 0.0
}

CONVERSION (AgentState → FoodOrderingState):
─────────────────────────────────────────────────────────────────
FoodOrderingState = {
  # Copied from AgentState
  "session_id": "session_123",
  "user_id": null,
  "messages": [...],
  "cart_items": [],
  "cart_subtotal": 0.0,

  # Food-specific (defaults)
  "cart_validated": False,
  "current_sub_intent": null,
  "order_type": null
}

PARENT AGENT (Food Ordering):
─────────────────────────────────────────────────────────────────
Step 1: Sub-Intent Classification (LLM)
  Input: "Show me the menu"
  Output: SubIntentClassification(
    sub_intent="browse_menu",
    confidence=0.97,
    entities={},  # No specific category
    missing_entities=[]
  )

Step 2: Route to Agent
  Selected: menu_browsing_agent

SUB-AGENT (Menu Browsing):
─────────────────────────────────────────────────────────────────
Receives:
  entities = {}
  state = FoodOrderingState(...)

Action: Show full menu (no category specified)

Tool: ListMenuTool
  Database Query (PostgreSQL):
  ```sql
  SELECT
      mc.category_id,
      mc.name as category_name,
      mc.description as category_description,
      json_agg(
          json_build_object(
              'item_id', mi.item_id,
              'name', mi.name,
              'price', mi.price,
              'description', mi.description
          )
          ORDER BY mi.display_order
      ) as items
  FROM menu_categories mc
  LEFT JOIN menu_items mi ON mc.category_id = mi.category_id
  WHERE mc.is_active = true
    AND mi.is_available = true
  GROUP BY mc.category_id, mc.name, mc.description
  ORDER BY mc.display_order;
  ```

  Result:
  ```python
  {
      "menu": [
          {
              "category_id": "cat_1",
              "category_name": "Appetizers",
              "items": [
                  {"item_id": "item_1", "name": "Samosa", "price": 80.0},
                  {"item_id": "item_2", "name": "Spring Roll", "price": 90.0}
              ]
          },
          {
              "category_id": "cat_2",
              "category_name": "Main Course",
              "items": [
                  {"item_id": "item_789", "name": "Butter Chicken", "price": 350.0},
                  {"item_id": "item_790", "name": "Paneer Tikka", "price": 280.0}
              ]
          }
      ],
      "total_categories": 2,
      "total_items": 4
  }
  ```

ActionResult Returned:
  ```python
  {
      "action": "menu_displayed",
      "success": True,
      "data": {
          "menu": [...],
          "total_categories": 2,
          "total_items": 4,
          "message": "Here's our menu with 2 categories and 4 items"
      },
      "context": {
          "categories": ["Appetizers", "Main Course"],
          "browsing_mode": "full_menu",
          "sub_intent": "browse_menu",
          "confidence": 0.97
      }
  }
  ```

ORCHESTRATOR (Merge into AgentState):
─────────────────────────────────────────────────────────────────
Updated AgentState:
{
  "messages": [
      HumanMessage("Show me the menu"),
      AIMessage("Here's our menu with 2 categories and 4 items...")
  ],
  "session_id": "session_123",
  "action_result": {
      "action": "menu_displayed",
      "data": {...}
  },
  "current_sub_intent": "browse_menu",  # Updated from ActionResult
  "agent_response": "Here's our menu with 2 categories and 4 items..."
}

CHECKPOINT SAVED (MemorySaver):
─────────────────────────────────────────────────────────────────
Key: (thread_id="session_123", checkpoint_id="chk_1")
Value: Full AgentState above

RESPONSE TO USER:
─────────────────────────────────────────────────────────────────
"Here's our menu:

**Appetizers**
1. Samosa - ₹80
2. Spring Roll - ₹90

**Main Course**
1. Butter Chicken - ₹350
2. Paneer Tikka - ₹280

What would you like to order?"
```

---

### TURN 2: Add to Cart

```
┌────────────────────────────────────────────────────────────────┐
│ USER MESSAGE: "Add 2 butter chicken"                           │
└────────────────────────────────────────────────────────────────┘

ORCHESTRATOR (AgentState - Loaded from checkpoint):
─────────────────────────────────────────────────────────────────
{
  "messages": [
      HumanMessage("Show me the menu"),
      AIMessage("Here's our menu..."),
      HumanMessage("Add 2 butter chicken")  # New message
  ],
  "session_id": "session_123",
  "user_id": null,
  "current_intent": "food_ordering",
  "cart_items": [],  # Still empty
  "cart_subtotal": 0.0,
  "current_sub_intent": "browse_menu"  # From previous turn
}

CONVERSION (AgentState → FoodOrderingState):
─────────────────────────────────────────────────────────────────
FoodOrderingState = {
  "session_id": "session_123",
  "messages": [...3 messages...],
  "cart_items": [],
  "cart_subtotal": 0.0,
  "current_sub_intent": "browse_menu"  # Previous sub-intent
}

PARENT AGENT (Food Ordering):
─────────────────────────────────────────────────────────────────
Step 1: Sub-Intent Classification (LLM)
  Input: "Add 2 butter chicken"
  Context:
    - Cart is EMPTY
    - User NOT authenticated
    - Previous sub-intent: browse_menu

  Output: SubIntentClassification(
    sub_intent="manage_cart",
    confidence=0.98,
    entities={
        "action": "add",
        "item_name": "butter chicken",
        "quantity": 2
    },
    missing_entities=[]
  )

Step 2: Entity Validation
  Required: ["action", "item_name", "quantity"]
  Provided: ["action", "item_name", "quantity"]
  Result: ✓ VALID

Step 3: Guardrails
  Check cart_locked: False → ✓ PASS

Step 4: Route to Agent
  Selected: cart_management_agent

SUB-AGENT (Cart Management):
─────────────────────────────────────────────────────────────────
Receives:
  entities = {
      "action": "add",
      "item_name": "butter chicken",
      "quantity": 2
  }
  state = FoodOrderingState(
      session_id="session_123",
      cart_items=[],
      cart_subtotal=0.0,
      ...
  )

Action: Add to cart

Tool: AddToCartTool

Database Operations:
─────────────────────────────────────────────────────────────────
1. SEARCH FOR ITEM (Redis Menu Cache)
   Operation: GET menu:item:butter_chicken
   Result: {
       "item_id": "item_789",
       "name": "Butter Chicken",
       "price": 350.0,
       "category_id": "cat_2",
       "is_available": True
   }

2. CHECK INVENTORY (Redis)
   Operation: GET inventory:item_789
   Result: {
       "item_id": "item_789",
       "available_quantity": 15,
       "reserved_quantity": 3,
       "total_stock": 20
   }

   Check: 15 available >= 2 requested → ✓ AVAILABLE

3. RESERVE INVENTORY (Redis)
   Operations:
   - DECR inventory:item_789:available by 2 (15 → 13)
   - INCR inventory:item_789:reserved:session_123 by 2 (0 → 2)
   - SETEX inventory:item_789:reserved:session_123 900 (15min TTL)

4. UPDATE CART (Redis)
   Operation: SET cart:session_123
   Value:
   ```json
   {
     "items": [
       {
         "item_id": "item_789",
         "name": "Butter Chicken",
         "price": 350.0,
         "quantity": 2,
         "subtotal": 700.0,
         "added_at": "2025-01-14T10:30:00Z"
       }
     ],
     "subtotal": 700.0,
     "item_count": 1,
     "updated_at": "2025-01-14T10:30:00Z"
   }
   ```
   TTL: 1800 seconds (30 minutes)

ActionResult Returned:
─────────────────────────────────────────────────────────────────
{
    "action": "item_added_to_cart",
    "success": True,
    "data": {
        "item_name": "Butter Chicken",
        "quantity": 2,
        "item_price": 350.0,
        "cart_items": [
            {
                "item_id": "item_789",
                "name": "Butter Chicken",
                "price": 350.0,
                "quantity": 2,
                "subtotal": 700.0
            }
        ],
        "cart_subtotal": 700.0,
        "item_count": 1,
        "message": "Added 2 x Butter Chicken to your cart (₹700)"
    },
    "context": {
        "sub_intent": "manage_cart",
        "action": "add",
        "item_id": "item_789",
        "confidence": 0.98
    },
    # STATE UPDATES (will be merged)
    "cart_items": [...],
    "cart_subtotal": 700.0,
    "cart_item_count": 1,
    "current_sub_intent": "manage_cart"
}

ORCHESTRATOR (Merge into AgentState):
─────────────────────────────────────────────────────────────────
Updated AgentState:
{
  "messages": [
      ...,
      HumanMessage("Add 2 butter chicken"),
      AIMessage("Added 2 x Butter Chicken to your cart...")
  ],
  "session_id": "session_123",
  "cart_items": [
      {
          "item_id": "item_789",
          "name": "Butter Chicken",
          "price": 350.0,
          "quantity": 2,
          "subtotal": 700.0
      }
  ],  # ← UPDATED
  "cart_subtotal": 700.0,  # ← UPDATED
  "cart_item_count": 1,  # ← UPDATED
  "current_sub_intent": "manage_cart",  # ← UPDATED
  "action_result": {...}
}

STORAGE LOCATIONS (After Turn 2):
─────────────────────────────────────────────────────────────────
1. MemorySaver Checkpoint (in-memory):
   - Full AgentState with conversation history

2. Redis (cart:session_123):
   - Cart items with reservations
   - TTL: 30 minutes

3. Redis (inventory:item_789:reserved:session_123):
   - Reserved quantity: 2
   - TTL: 15 minutes

4. Redis (menu:item:butter_chicken):
   - Menu item metadata
   - Permanent (refreshed from PostgreSQL)

RESPONSE TO USER:
─────────────────────────────────────────────────────────────────
"✓ Added 2 x Butter Chicken to your cart!

Your cart:
1. Butter Chicken (x2) - ₹700

Subtotal: ₹700

What else would you like to add?"
```

---

### TURN 3: Checkout

```
┌────────────────────────────────────────────────────────────────┐
│ USER MESSAGE: "I'm ready to checkout"                          │
└────────────────────────────────────────────────────────────────┘

ORCHESTRATOR (AgentState - Loaded from checkpoint):
─────────────────────────────────────────────────────────────────
{
  "messages": [...4 messages...],
  "session_id": "session_123",
  "user_id": null,
  "cart_items": [
      {"item_id": "item_789", "name": "Butter Chicken", "quantity": 2, "subtotal": 700.0}
  ],
  "cart_subtotal": 700.0,
  "cart_item_count": 1,
  "cart_validated": False,  # Not yet validated
  "current_sub_intent": "manage_cart"
}

CONVERSION (AgentState → FoodOrderingState):
─────────────────────────────────────────────────────────────────
FoodOrderingState = {
  "session_id": "session_123",
  "cart_items": [...],
  "cart_subtotal": 700.0,
  "cart_validated": False,
  "order_type": null
}

PARENT AGENT (Food Ordering):
─────────────────────────────────────────────────────────────────
Step 1: Sub-Intent Classification (LLM)
  Input: "I'm ready to checkout"
  Context:
    - Cart has 1 item (total: ₹700)
    - User NOT authenticated
    - IMPORTANT: User is FINISHING (not starting)

  Output: SubIntentClassification(
    sub_intent="validate_order",
    confidence=0.99,
    entities={},
    missing_entities=[]
  )

Step 2: Guardrails
  Check: Empty cart? → NO (has 1 item) → ✓ PASS

Step 3: Route to Agent
  Selected: checkout_validator_agent

SUB-AGENT (Checkout Validator):
─────────────────────────────────────────────────────────────────
Receives:
  entities = {}
  state = FoodOrderingState(
      session_id="session_123",
      cart_items=[...],
      cart_subtotal=700.0,
      cart_validated=False
  )

Tool: OrderValidationTool

Database Operations:
─────────────────────────────────────────────────────────────────
1. GET CART (Redis)
   Operation: GET cart:session_123
   Result: {
       "items": [
           {"item_id": "item_789", "name": "Butter Chicken", "quantity": 2, "subtotal": 700.0}
       ],
       "subtotal": 700.0
   }

2. VALIDATE ITEM AVAILABILITY (Redis)
   For each item:
   Operation: GET inventory:item_789
   Result: {"available_quantity": 13, "reserved_quantity": 5}

   Check: Item still available? → ✓ YES

3. GET CONFIG (MongoDB)
   Collection: settings
   Queries:
   - db.settings.find_one({"key": "min_order_amount"})
     Result: {"value": 200}
     Check: 700 >= 200 → ✓ PASS

   - db.settings.find_one({"key": "tax_rate"})
     Result: {"value": 0.18}  # 18% GST

   - db.settings.find_one({"key": "operating_hours"})
     Result: {"open": "09:00", "close": "22:00"}
     Current time: 10:30 → ✓ WITHIN HOURS

4. CALCULATE TAX & TOTAL
   Subtotal: 700.0
   Tax (18%): 126.0
   Total: 826.0

ActionResult Returned:
─────────────────────────────────────────────────────────────────
{
    "action": "cart_validated",
    "success": True,
    "data": {
        "valid": True,
        "message": "Your cart looks good! Ready to place your order?",
        "cart_summary": {
            "items": [
                {
                    "item_id": "item_789",
                    "name": "Butter Chicken",
                    "quantity": 2,
                    "subtotal": 700.0
                }
            ],
            "subtotal": 700.0,
            "tax": 126.0,
            "total": 826.0
        }
    },
    "context": {
        "sub_intent": "validate_order",
        "confidence": 0.99
    },
    # STATE UPDATES
    "cart_validated": True,  # ← CRITICAL UPDATE
    "validation_issues": [],
    "cart_tax": 126.0,
    "cart_total": 826.0,
    "current_sub_intent": "validate_order"
}

ORCHESTRATOR (Merge into AgentState):
─────────────────────────────────────────────────────────────────
Updated AgentState:
{
  "messages": [...],
  "cart_items": [...],
  "cart_subtotal": 700.0,
  "cart_tax": 126.0,  # ← NEW
  "cart_total": 826.0,  # ← NEW
  "cart_validated": True,  # ← CRITICAL (enables checkout)
  "validation_issues": [],
  "current_sub_intent": "validate_order"
}

STORAGE LOCATIONS (After Turn 3):
─────────────────────────────────────────────────────────────────
1. MemorySaver Checkpoint:
   - cart_validated = True
   - cart_tax = 126.0
   - cart_total = 826.0

2. Redis (cart:session_123):
   - Unchanged (still has items)

3. MongoDB (settings):
   - Config read (not modified)

RESPONSE TO USER:
─────────────────────────────────────────────────────────────────
"Your cart looks good! ✓

Cart Summary:
• Butter Chicken (x2) - ₹700

Subtotal: ₹700
Tax (18%): ₹126
Total: ₹826

Is this for dine-in or takeout?"
```

---

### TURN 4: Execute Checkout

```
┌────────────────────────────────────────────────────────────────┐
│ USER MESSAGE: "Dine-in please"                                 │
└────────────────────────────────────────────────────────────────┘

ORCHESTRATOR (AgentState - Loaded from checkpoint):
─────────────────────────────────────────────────────────────────
{
  "messages": [...],
  "session_id": "session_123",
  "user_id": null,
  "cart_items": [...],
  "cart_subtotal": 700.0,
  "cart_tax": 126.0,
  "cart_total": 826.0,
  "cart_validated": True,  # ← From previous turn
  "order_type": null
}

CONVERSION (AgentState → FoodOrderingState):
─────────────────────────────────────────────────────────────────
FoodOrderingState = {
  "session_id": "session_123",
  "cart_items": [...],
  "cart_validated": True,
  "cart_total": 826.0,
  "order_type": null
}

PARENT AGENT (Food Ordering):
─────────────────────────────────────────────────────────────────
Step 1: Sub-Intent Classification (LLM)
  Input: "Dine-in please"
  Context:
    - Cart has 1 item
    - Cart validated - ready for checkout
    - User NOT authenticated

  Output: SubIntentClassification(
    sub_intent="execute_checkout",
    confidence=0.98,
    entities={
        "order_type": "dine_in"
    },
    missing_entities=[]
  )

Step 2: Guardrails
  Check: cart_validated? → YES → ✓ PASS
  Check: must_authenticate? → NO (optional for dine-in) → ✓ PASS

Step 3: Route to Agent
  Selected: checkout_executor_agent

SUB-AGENT (Checkout Executor):
─────────────────────────────────────────────────────────────────
Receives:
  entities = {
      "order_type": "dine_in"
  }
  state = FoodOrderingState(
      session_id="session_123",
      user_id=null,
      cart_items=[...],
      cart_validated=True,
      cart_total=826.0
  )

Tool: CheckoutCartDraftTool

Database Operations:
─────────────────────────────────────────────────────────────────
POSTGRESQL:

1. INSERT ORDER (orders table)
   ```sql
   INSERT INTO orders (
       order_number,
       user_id,
       session_id,
       order_type,
       status,
       subtotal,
       tax_amount,
       total_amount,
       contact_phone,
       device_id,
       special_instructions,
       created_at,
       updated_at
   ) VALUES (
       'ORD-20250114-1234',  -- Generated order number
       NULL,  -- No user_id (guest)
       'session_123',
       'dine_in',
       'draft',  -- Status: DRAFT (not confirmed)
       700.00,
       126.00,
       826.00,
       NULL,  -- No phone yet
       NULL,
       NULL,
       NOW(),
       NOW()
   ) RETURNING id, order_number, created_at;
   ```

   Result:
   ```python
   {
       "id": "order_uuid_12345",
       "order_number": "ORD-20250114-1234",
       "created_at": "2025-01-14T10:35:00Z"
   }
   ```

2. INSERT ORDER ITEMS (order_items table)
   ```sql
   INSERT INTO order_items (
       order_id,
       item_id,
       item_name,
       quantity,
       unit_price,
       subtotal,
       category_name
   ) VALUES (
       'order_uuid_12345',
       'item_789',
       'Butter Chicken',
       2,
       350.00,
       700.00,
       'Main Course'
   );
   ```

3. INSERT ORDER METADATA (order_metadata table)
   ```sql
   INSERT INTO order_metadata (order_id, key, value)
   VALUES
       ('order_uuid_12345', 'source', 'chatbot'),
       ('order_uuid_12345', 'session_id', 'session_123'),
       ('order_uuid_12345', 'cart_validated_at', '2025-01-14T10:34:00Z'),
       ('order_uuid_12345', 'sub_intent', 'execute_checkout');
   ```

REDIS:

4. LOCK CART (prevent modifications)
   ```
   SET cart:session_123:locked true EX 600
   ```
   TTL: 10 minutes (until payment completes or times out)

5. KEEP CART (for payment reference)
   Cart remains in Redis:
   - cart:session_123 still exists
   - Will be cleared after payment success
   - Or released after timeout

ActionResult Returned:
─────────────────────────────────────────────────────────────────
{
    "action": "draft_order_created",
    "success": True,
    "data": {
        "order_id": "order_uuid_12345",
        "order_number": "ORD-20250114-1234",
        "order_type": "dine_in",
        "status": "draft",
        "items": [
            {
                "item_id": "item_789",
                "name": "Butter Chicken",
                "quantity": 2,
                "unit_price": 350.0,
                "subtotal": 700.0
            }
        ],
        "item_count": 1,
        "subtotal": 700.0,
        "tax_amount": 126.0,
        "total_amount": 826.0,
        "estimated_ready_time": "15-20 minutes",
        "message": "Your order #ORD-20250114-1234 has been created. Let's proceed with payment.",
        "next_step": "authentication"  # Signal to orchestrator
    },
    "context": {
        "draft_order_id": "order_uuid_12345",
        "order_number": "ORD-20250114-1234",
        "requires_payment": True,
        "sub_intent": "execute_checkout",
        "confidence": 0.98
    },
    # STATE UPDATES
    "draft_order_id": "order_uuid_12345",
    "order_number": "ORD-20250114-1234",
    "order_type": "dine_in",
    "cart_locked": True,
    "must_authenticate": True,  # Trigger auth flow
    "current_sub_intent": "execute_checkout"
}

ORCHESTRATOR (Merge into AgentState):
─────────────────────────────────────────────────────────────────
Updated AgentState:
{
  "messages": [...],
  "cart_items": [...],
  "cart_locked": True,  # ← Cart locked
  "draft_order_id": "order_uuid_12345",  # ← NEW
  "order_number": "ORD-20250114-1234",  # ← NEW
  "order_type": "dine_in",  # ← NEW
  "must_authenticate": True,  # ← Triggers auth flow next
  "current_sub_intent": "execute_checkout"
}

STORAGE LOCATIONS (After Turn 4):
─────────────────────────────────────────────────────────────────
1. MemorySaver Checkpoint:
   - Full AgentState with order details

2. PostgreSQL (orders table):
   - Draft order record (status='draft')

3. PostgreSQL (order_items table):
   - Order line items

4. PostgreSQL (order_metadata table):
   - Order metadata

5. Redis (cart:session_123):
   - Still exists (not cleared)
   - Locked: cart:session_123:locked = true

6. Redis (inventory:item_789:reserved:session_123):
   - Still reserved (will convert to order inventory after payment)

NEXT STEPS (Orchestrator routing):
─────────────────────────────────────────────────────────────────
1. Orchestrator sees action_result.data.next_step = "authentication"
2. Orchestrator sees state.must_authenticate = True
3. Routes to Authentication Agent
4. After auth: Routes to Payment Agent
5. After payment success: Webhook confirms order (status: draft → confirmed)

RESPONSE TO USER:
─────────────────────────────────────────────────────────────────
"✓ Order #ORD-20250114-1234 created!

Order Summary:
• Butter Chicken (x2) - ₹700

Subtotal: ₹700
Tax: ₹126
Total: ₹826

Type: Dine-in
Ready in: 15-20 minutes

To complete your order, I'll need your phone number for updates."
```

---

## 7. STORAGE TRACKING AT EVERY STEP {#storage-tracking}

### Complete Storage Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE TIER 1: IN-MEMORY                   │
│                    (LangGraph MemorySaver)                       │
└─────────────────────────────────────────────────────────────────┘
Location: Python process memory
Persistence: Session duration only
Purpose: Conversation state and checkpointing

Stored Data:
  - Full AgentState (all fields)
  - Message history (full conversation)
  - Checkpoint metadata
  - Thread/session mapping

Key-Value Format:
  Key: (thread_id="session_123", checkpoint_id="chk_4")
  Value: {AgentState dict}

Access Pattern:
  - Read: Every turn (load previous state)
  - Write: After every agent execution (save checkpoint)

┌─────────────────────────────────────────────────────────────────┐
│                      STORAGE TIER 2: REDIS                      │
│                    (Fast ephemeral storage)                      │
└─────────────────────────────────────────────────────────────────┘
Location: Redis server (in-memory database)
Persistence: TTL-based (minutes to hours)
Purpose: Cart, inventory, menu cache

CART STORAGE:
  Key: cart:{session_id}
  Value: {
      "items": [...],
      "subtotal": 700.0,
      "item_count": 1,
      "updated_at": "..."
  }
  TTL: 1800 seconds (30 minutes)

  Access:
  - Read: View cart, validate cart
  - Write: Add/remove/update items
  - Delete: After order confirmed

INVENTORY RESERVATIONS:
  Key: inventory:{item_id}:reserved:{session_id}
  Value: quantity (integer)
  TTL: 900 seconds (15 minutes)

  Access:
  - Read: Check reservation
  - Write: Reserve inventory
  - Delete: After order confirmed or timeout

MENU CACHE:
  Key: menu:item:{item_id}
  Value: {
      "item_id": "...",
      "name": "...",
      "price": 350.0,
      "is_available": true,
      ...
  }
  TTL: None (refreshed from PostgreSQL periodically)

  Access:
  - Read: Every item lookup (fast)
  - Write: On menu update from PostgreSQL

INVENTORY CACHE:
  Key: inventory:{item_id}
  Value: {
      "available_quantity": 15,
      "reserved_quantity": 3,
      "total_stock": 20
  }
  TTL: 60 seconds (1 minute)

  Access:
  - Read: Check availability
  - Write: Update on inventory change

CART LOCK:
  Key: cart:{session_id}:locked
  Value: true
  TTL: 600 seconds (10 minutes)

  Access:
  - Read: Check if cart locked
  - Write: Set during checkout
  - Delete: After payment complete/timeout

┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE TIER 3: POSTGRESQL                   │
│                 (Persistent relational database)                 │
└─────────────────────────────────────────────────────────────────┘
Location: PostgreSQL server (disk-based)
Persistence: Permanent
Purpose: Orders, menu, users, transactions

ORDERS TABLE:
  Schema:
    - id (UUID, primary key)
    - order_number (VARCHAR, unique)
    - user_id (UUID, nullable, FK to users)
    - session_id (VARCHAR)
    - order_type (ENUM: dine_in, takeout)
    - status (ENUM: draft, confirmed, preparing, ready, completed, cancelled)
    - subtotal (DECIMAL)
    - tax_amount (DECIMAL)
    - total_amount (DECIMAL)
    - created_at (TIMESTAMP)
    - updated_at (TIMESTAMP)
    - confirmed_at (TIMESTAMP, nullable)

  Access:
  - Write: Create draft order (checkout executor)
  - Update: Change status (payment webhook, kitchen)
  - Read: Order history, status checks

ORDER_ITEMS TABLE:
  Schema:
    - id (UUID, primary key)
    - order_id (UUID, FK to orders)
    - item_id (VARCHAR, FK to menu_items)
    - item_name (VARCHAR)
    - quantity (INTEGER)
    - unit_price (DECIMAL)
    - subtotal (DECIMAL)
    - special_instructions (TEXT, nullable)

  Access:
  - Write: Insert when order created
  - Read: Order details, kitchen display

MENU_ITEMS TABLE:
  Schema:
    - item_id (VARCHAR, primary key)
    - category_id (VARCHAR, FK to menu_categories)
    - name (VARCHAR)
    - description (TEXT)
    - price (DECIMAL)
    - is_available (BOOLEAN)
    - display_order (INTEGER)
    - embedding (VECTOR, for semantic search)

  Access:
  - Read: Menu browsing, search, discovery
  - Update: Admin menu changes

MENU_CATEGORIES TABLE:
  Schema:
    - category_id (VARCHAR, primary key)
    - name (VARCHAR)
    - description (TEXT)
    - is_active (BOOLEAN)
    - display_order (INTEGER)

  Access:
  - Read: Menu structure

┌─────────────────────────────────────────────────────────────────┐
│                     STORAGE TIER 4: MONGODB                     │
│                   (Document-based database)                      │
└─────────────────────────────────────────────────────────────────┘
Location: MongoDB server
Persistence: Permanent
Purpose: Configuration, analytics, flexible schemas

SETTINGS COLLECTION:
  Documents:
    {
      "_id": ObjectId("..."),
      "key": "min_order_amount",
      "value": 200,
      "updated_at": ISODate("...")
    }
    {
      "key": "tax_rate",
      "value": 0.18
    }
    {
      "key": "operating_hours",
      "value": {"open": "09:00", "close": "22:00"}
    }

  Access:
  - Read: Validation, business rules
  - Write: Admin configuration changes

ORDER_METADATA COLLECTION: (Alternative to PostgreSQL order_metadata)
  Documents:
    {
      "order_id": "order_uuid_12345",
      "source": "chatbot",
      "session_id": "session_123",
      "sub_intent": "execute_checkout",
      "cart_validated_at": ISODate("..."),
      "ip_address": "...",
      "user_agent": "..."
    }

  Access:
  - Write: Order creation (metadata enrichment)
  - Read: Analytics, debugging
```

### Data Flow Across Storage Tiers

```
USER MESSAGE: "Add 2 butter chicken"
│
├─→ TIER 1 (MemorySaver)
│   Read: Previous AgentState (session_123, checkpoint_3)
│   → Contains: messages, cart_items, session_id, etc.
│
├─→ PARENT AGENT PROCESSING
│   Sub-intent classification (in-memory)
│   Entity extraction (in-memory)
│   Routing (in-memory)
│
├─→ SUB-AGENT: Cart Management
│   │
│   ├─→ TIER 2 (Redis) - Menu Lookup
│   │   GET menu:item:butter_chicken
│   │   → Returns: {item_id, name, price, ...}
│   │
│   ├─→ TIER 2 (Redis) - Inventory Check
│   │   GET inventory:item_789
│   │   → Returns: {available: 15, reserved: 3}
│   │
│   ├─→ TIER 2 (Redis) - Reserve Inventory
│   │   DECR inventory:item_789:available
│   │   INCR inventory:item_789:reserved:session_123
│   │   SETEX ... (15min TTL)
│   │
│   └─→ TIER 2 (Redis) - Update Cart
│       SET cart:session_123 {...}
│       SETEX ... (30min TTL)
│
├─→ ACTIONRESULT RETURNED
│   {action: "item_added_to_cart", cart_items: [...], ...}
│
└─→ TIER 1 (MemorySaver) - Save Checkpoint
    Write: Updated AgentState (session_123, checkpoint_4)
    → Contains: updated cart_items, cart_subtotal, action_result
```

---

## 8. RETURN FLOW (ActionResult Propagation) {#return-flow}

### How ActionResult Flows Back

```
┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 5: Sub-Agent Creates ActionResult                         │
│ Location: app/agents/food_ordering/agents/cart_management/node.py│
└─────────────────────────────────────────────────────────────────┘

  ActionResult = {
      "action": "item_added_to_cart",
      "success": True,
      "data": {...},
      "context": {...},
      # STATE UPDATES (to be merged)
      "cart_items": [...],
      "cart_subtotal": 700.0,
      "cart_item_count": 1
  }

  Return: ActionResult dict

             ↓ ↓ ↓

┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 4: Parent Agent Receives ActionResult                     │
│ Location: app/agents/food_ordering/graph.py                     │
└─────────────────────────────────────────────────────────────────┘

  Parent agent enhances ActionResult:

  agent_result["context"]["sub_intent"] = "manage_cart"
  agent_result["context"]["confidence"] = 0.98

  Return: Enhanced ActionResult

             ↓ ↓ ↓

┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 3: Node Wrapper Returns to LangGraph                      │
│ Location: app/agents/food_ordering/node.py                      │
└─────────────────────────────────────────────────────────────────┘

  return {"action_result": agent_result}

  LangGraph receives: Dict[str, Any]

             ↓ ↓ ↓

┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 2: LangGraph State Reducer Merges Updates                 │
│ Location: LangGraph internal (state management)                 │
└─────────────────────────────────────────────────────────────────┘

  LangGraph automatically merges:

  BEFORE:
  AgentState = {
      "cart_items": [],
      "cart_subtotal": 0.0,
      "action_result": None
  }

  MERGE OPERATION (using TypedDict update):
  1. Take returned dict: {"action_result": {..., "cart_items": [...], ...}}
  2. Extract fields that match AgentState schema
  3. Update AgentState with new values

  AFTER:
  AgentState = {
      "cart_items": [...],  # ← Updated from ActionResult
      "cart_subtotal": 700.0,  # ← Updated from ActionResult
      "action_result": {...}  # ← Entire ActionResult stored
  }

             ↓ ↓ ↓

┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 1: Checkpoint Saved                                       │
│ Location: MemorySaver (in-memory persistence)                   │
└─────────────────────────────────────────────────────────────────┘

  LangGraph saves checkpoint:

  checkpoint = {
      "state": AgentState,  # Full updated state
      "metadata": {
          "thread_id": "session_123",
          "checkpoint_id": "chk_4",
          "timestamp": "2025-01-14T10:30:00Z"
      }
  }

  Stored in: MemorySaver[(thread_id, checkpoint_id)]

             ↓ ↓ ↓

┌─────────────────────────────────────────────────────────────────┐
│ LEVEL 0: Available for Next Turn                                │
│ Location: Next user message                                     │
└─────────────────────────────────────────────────────────────────┘

  Next turn loads checkpoint:

  state = checkpointer.get(thread_id="session_123")

  state.cart_items → [...] (persisted from previous turn)
  state.cart_subtotal → 700.0 (persisted)
  state.action_result → {...} (previous result)
```

### State Update Mechanism

**How state fields are merged**:

```python
# In LangGraph's state reducer (simplified)
def update_state(current_state: AgentState, updates: Dict[str, Any]) -> AgentState:
    """
    LangGraph's automatic state update mechanism
    """
    new_state = current_state.copy()

    # For each field in updates
    for field, value in updates.items():
        if field in AgentState.__annotations__:
            # Field exists in AgentState schema
            if field == "messages":
                # Special handling: append to messages
                new_state["messages"] = add_messages(
                    current_state.get("messages", []),
                    value
                )
            else:
                # Regular field: overwrite
                new_state[field] = value
        else:
            # Field not in schema: ignored (or add to extras)
            pass

    return new_state
```

**ActionResult Fields that Update AgentState**:

| ActionResult Field | AgentState Field | Update Type |
|--------------------|------------------|-------------|
| `action_result` (entire dict) | `action_result` | Overwrite |
| `cart_items` | `cart_items` | Overwrite |
| `cart_subtotal` | `cart_subtotal` | Overwrite |
| `cart_item_count` | `cart_item_count` | Overwrite |
| `cart_validated` | `cart_validated` | Overwrite |
| `cart_tax` | `cart_tax` | Overwrite |
| `cart_total` | `cart_total` | Overwrite |
| `draft_order_id` | `draft_order_id` | Overwrite |
| `order_number` | `order_number` | Overwrite |
| `order_type` | `order_type` | Overwrite |
| `current_sub_intent` | `current_sub_intent` | Overwrite |
| `must_authenticate` | `must_authenticate` | Overwrite |

---

## 9. ARCHITECTURE DIAGRAMS {#architecture-diagrams}

### Complete Agent-to-Sub-Agent Flow

```
┌────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR GRAPH                             │
│                        (AgentState)                                    │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ User: "Add 2 butter chicken"
                                    ↓
                        ┌───────────────────────┐
                        │ Intent Classifier     │
                        │ (LLM)                 │
                        └───────────────────────┘
                                    │
                                    │ intent="food_ordering"
                                    ↓
                        ┌───────────────────────┐
                        │ food_ordering_agent   │
                        │ _node (WRAPPER)       │
                        │                       │
                        │ CONVERTS:             │
                        │ AgentState →          │
                        │ FoodOrderingState     │
                        └───────────────────────┘
                                    │
                                    │ FoodOrderingState
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                      FOOD ORDERING SUB-GRAPH                           │
│                      (FoodOrderingState)                               │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
                        ┌───────────────────────┐
                        │ Sub-Intent Classifier │
                        │ (LLM)                 │
                        │                       │
                        │ Input:                │
                        │ - user_message        │
                        │ - FoodOrderingState   │
                        │                       │
                        │ Output:               │
                        │ - sub_intent          │
                        │ - entities            │
                        │ - confidence          │
                        └───────────────────────┘
                                    │
                                    │ sub_intent="manage_cart"
                                    │ entities={action: "add", ...}
                                    ↓
                        ┌───────────────────────┐
                        │ Entity Validator      │
                        │                       │
                        │ Check required fields │
                        │ Merge with state      │
                        └───────────────────────┘
                                    │
                                    │ entities validated ✓
                                    ↓
                        ┌───────────────────────┐
                        │ Guardrails            │
                        │                       │
                        │ - Cart locked?        │
                        │ - Empty cart checkout?│
                        │ - Auth required?      │
                        └───────────────────────┘
                                    │
                                    │ guardrails passed ✓
                                    ↓
                        ┌───────────────────────┐
                        │ Agent Router          │
                        │ (Deterministic)       │
                        │                       │
                        │ Route to:             │
                        │ cart_management_agent │
                        └───────────────────────┘
                                    │
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│                        SUB-AGENT LAYER                                 │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
          ┌─────────┴──────┐  ┌────┴──────┐  ┌────┴──────────┐
          │ Menu Browsing  │  │   Menu    │  │     Cart      │
          │     Agent      │  │ Discovery │  │  Management   │ ← Selected
          └────────────────┘  │   Agent   │  │     Agent     │
                              └───────────┘  └────┬──────────┘
                                                   │
                                                   │ entities + state
                                                   ↓
                                       ┌───────────────────────┐
                                       │ cart_management_agent │
                                       │                       │
                                       │ Input:                │
                                       │ - entities: {...}     │
                                       │ - state: FoodOrdering │
                                       │         State         │
                                       └───────────────────────┘
                                                   │
                                                   │ action="add"
                                                   ↓
                                       ┌───────────────────────┐
                                       │ _handle_add_to_cart   │
                                       └───────────────────────┘
                                                   │
                                                   ↓
┌────────────────────────────────────────────────────────────────────────┐
│                            TOOL LAYER                                  │
└────────────────────────────────────────────────────────────────────────┘
                                                   │
                                       ┌───────────┴───────────┐
                                       │  AddToCartTool        │
                                       │                       │
                                       │  1. Get item (Redis)  │
                                       │  2. Check inventory   │
                                       │  3. Reserve inventory │
                                       │  4. Update cart       │
                                       └───────────┬───────────┘
                                                   │
                                                   │ ToolResult
                                                   ↓
┌────────────────────────────────────────────────────────────────────────┐
│                         DATABASE LAYER                                 │
└────────────────────────────────────────────────────────────────────────┘
                    ┌──────────────┬──────────────┬──────────────┐
                    │              │              │              │
              ┌─────┴──────┐ ┌────┴──────┐ ┌─────┴──────┐ ┌────┴──────┐
              │   Redis    │ │PostgreSQL │ │  MongoDB   │ │MemorySaver│
              │            │ │           │ │            │ │           │
              │ - Cart     │ │ - Menu    │ │ - Config   │ │ - AgentState
              │ - Inventory│ │ - Orders  │ │ - Analytics│ │ - Checkpoints
              │ - Cache    │ │ - Users   │ │            │ │           │
              └────────────┘ └───────────┘ └────────────┘ └───────────┘
                    │              │              │              │
                    └──────────────┴──────────────┴──────────────┘
                                       │
                                       │ Data retrieved
                                       ↓

═════════════════════════════════════════════════════════════════════════
                           RETURN FLOW (BACK UP)
═════════════════════════════════════════════════════════════════════════

                            ┌───────────────┐
                            │ ActionResult  │
                            │               │
                            │ - action      │
                            │ - success     │
                            │ - data        │
                            │ - context     │
                            │ - state_updates│
                            └───────┬───────┘
                                    │
                                    │ Return from sub-agent
                                    ↓
                        ┌───────────────────────┐
                        │ Parent Agent          │
                        │ (food_ordering_agent) │
                        │                       │
                        │ Enhance ActionResult: │
                        │ - Add sub_intent      │
                        │ - Add confidence      │
                        └───────────┬───────────┘
                                    │
                                    │ Return to node wrapper
                                    ↓
                        ┌───────────────────────┐
                        │ Node Wrapper          │
                        │                       │
                        │ return {              │
                        │   "action_result": ...│
                        │ }                     │
                        └───────────┬───────────┘
                                    │
                                    │ Return to orchestrator
                                    ↓
                        ┌───────────────────────┐
                        │ LangGraph State       │
                        │ Reducer               │
                        │                       │
                        │ Merge ActionResult    │
                        │ into AgentState       │
                        └───────────┬───────────┘
                                    │
                                    │ Save checkpoint
                                    ↓
                        ┌───────────────────────┐
                        │ MemorySaver           │
                        │                       │
                        │ checkpoint_4 saved    │
                        └───────────┬───────────┘
                                    │
                                    │ Continue to response
                                    ↓
                        ┌───────────────────────┐
                        │ Response Agent        │
                        │                       │
                        │ Format user message   │
                        └───────────┬───────────┘
                                    │
                                    │ Final response
                                    ↓
                            ┌───────────────┐
                            │     USER      │
                            └───────────────┘
```

---

## 10. DATABASE OPERATIONS {#database-operations}

### Complete Database Query Reference

#### Cart Operations (Redis)

**Add to Cart**:
```python
# 1. Get menu item from cache
redis_key = f"menu:item:{item_name.lower().replace(' ', '_')}"
item_data = redis.get(redis_key)
# Returns: {"item_id": "item_789", "name": "Butter Chicken", "price": 350.0}

# 2. Check inventory
redis_key = f"inventory:{item_id}"
inventory_data = redis.get(redis_key)
# Returns: {"available": 15, "reserved": 3}

# 3. Reserve inventory
redis.decr(f"inventory:{item_id}:available", amount=quantity)
redis.incr(f"inventory:{item_id}:reserved:{session_id}", amount=quantity)
redis.expire(f"inventory:{item_id}:reserved:{session_id}", 900)  # 15min

# 4. Update cart
cart_data = {
    "items": [...],
    "subtotal": 700.0,
    "item_count": 1,
    "updated_at": datetime.utcnow().isoformat()
}
redis.setex(f"cart:{session_id}", 1800, json.dumps(cart_data))  # 30min TTL
```

#### Menu Operations (PostgreSQL)

**List Full Menu**:
```sql
SELECT
    mc.category_id,
    mc.name as category_name,
    mc.description as category_description,
    mc.display_order as category_order,
    json_agg(
        json_build_object(
            'item_id', mi.item_id,
            'name', mi.name,
            'price', mi.price,
            'description', mi.description,
            'is_available', mi.is_available,
            'dietary_tags', mi.dietary_tags,
            'spice_level', mi.spice_level
        )
        ORDER BY mi.display_order
    ) as items
FROM menu_categories mc
LEFT JOIN menu_items mi
    ON mc.category_id = mi.category_id
    AND mi.is_available = true
WHERE mc.is_active = true
GROUP BY mc.category_id, mc.name, mc.description, mc.display_order
ORDER BY mc.display_order;
```

**Semantic Search** (pgvector):
```sql
SELECT
    item_id,
    name,
    description,
    price,
    category_id,
    embedding <=> $1::vector as similarity_distance
FROM menu_items
WHERE is_available = true
ORDER BY embedding <=> $1::vector
LIMIT 10;
```

**Dietary Filter**:
```sql
SELECT
    mi.item_id,
    mi.name,
    mi.price,
    mi.description,
    mi.dietary_tags,
    mi.category_id,
    mc.name as category_name
FROM menu_items mi
JOIN menu_categories mc ON mi.category_id = mc.category_id
WHERE mi.is_available = true
  AND mi.dietary_tags @> $1::text[]  -- Array contains all required tags
ORDER BY mi.popularity_score DESC, mi.price ASC
LIMIT 20;
```
Parameters: `$1 = ['vegetarian', 'gluten-free']`

#### Order Operations (PostgreSQL)

**Create Draft Order**:
```sql
-- Insert order
INSERT INTO orders (
    order_number,
    user_id,
    session_id,
    order_type,
    status,
    subtotal,
    tax_amount,
    total_amount,
    contact_phone,
    device_id,
    special_instructions,
    created_at,
    updated_at
) VALUES (
    $1,  -- order_number (generated)
    $2,  -- user_id (nullable)
    $3,  -- session_id
    $4,  -- order_type ('dine_in' or 'takeout')
    'draft',  -- status
    $5,  -- subtotal
    $6,  -- tax_amount
    $7,  -- total_amount
    $8,  -- contact_phone
    $9,  -- device_id
    $10, -- special_instructions
    NOW(),
    NOW()
) RETURNING id, order_number, created_at;

-- Insert order items
INSERT INTO order_items (
    order_id,
    item_id,
    item_name,
    quantity,
    unit_price,
    subtotal,
    category_name,
    special_instructions
)
SELECT
    $1,  -- order_id from previous INSERT
    unnest($2::text[]),  -- item_ids
    unnest($3::text[]),  -- item_names
    unnest($4::int[]),   -- quantities
    unnest($5::decimal[]),  -- unit_prices
    unnest($6::decimal[]),  -- subtotals
    unnest($7::text[]),  -- category_names
    unnest($8::text[]);  -- special_instructions

-- Insert order metadata
INSERT INTO order_metadata (order_id, key, value)
VALUES
    ($1, 'source', 'chatbot'),
    ($1, 'session_id', $2),
    ($1, 'sub_intent', $3),
    ($1, 'cart_validated_at', $4);
```

**Validate Cart**:
```sql
-- Check minimum order amount
SELECT value::decimal as min_order_amount
FROM settings
WHERE key = 'min_order_amount';

-- Check item availability
SELECT
    mi.item_id,
    mi.name,
    mi.price,
    mi.is_available,
    COALESCE(inv.available_quantity, 0) as stock
FROM menu_items mi
LEFT JOIN inventory inv ON mi.item_id = inv.item_id
WHERE mi.item_id = ANY($1::text[])  -- Array of cart item IDs
FOR UPDATE;  -- Lock rows to prevent race conditions
```

#### Configuration Operations (MongoDB)

**Get Settings**:
```javascript
// Get tax rate
db.settings.findOne({"key": "tax_rate"})
// Returns: {_id: ObjectId(...), key: "tax_rate", value: 0.18}

// Get operating hours
db.settings.findOne({"key": "operating_hours"})
// Returns: {key: "operating_hours", value: {open: "09:00", close: "22:00"}}

// Get minimum order amount
db.settings.findOne({"key": "min_order_amount"})
// Returns: {key: "min_order_amount", value: 200}
```

**Store Order Metadata**:
```javascript
db.order_metadata.insertOne({
    order_id: "order_uuid_12345",
    session_id: "session_123",
    source: "chatbot",
    sub_intent: "execute_checkout",
    cart_validated_at: new Date("2025-01-14T10:34:00Z"),
    user_agent: "...",
    ip_address: "...",
    created_at: new Date()
})
```

---

## SUMMARY

This document provides a complete reference for agent-to-sub-agent data transfer in the restaurant AI system:

**Key Concepts**:
1. **State Extension Pattern**: FoodOrderingState extends AgentState
2. **Bidirectional Conversion**: Node wrapper converts states back and forth
3. **ActionResult Propagation**: Sub-agents return structured results that merge into parent state
4. **Storage Architecture**: 4-tier storage (MemorySaver, Redis, PostgreSQL, MongoDB)
5. **No Data Loss**: All state persists through conversions and checkpoints

**All 5 Sub-Agents**:
- Menu Browsing (navigate structure)
- Menu Discovery (search, filter, recommend)
- Cart Management (add, remove, update, view)
- Checkout Validator (validate cart)
- Checkout Executor (create draft order)

**Complete Example**:
- 4-turn conversation traced with full data flow
- Every database operation shown
- Storage tracking at every step
- State snapshots at each transition

This architecture enables scalable, maintainable sub-graphs with complete state visibility and control.
