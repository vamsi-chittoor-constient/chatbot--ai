# Agentic Graph Workflow Architecture

**Restaurant AI Assistant - LangGraph Orchestration System**

This document provides a comprehensive guide to the LangGraph-based orchestration system that powers the Virtual Waiter AI assistant.

---

## Table of Contents

1. [Overview](#overview)
2. [Complete Workflow Diagram](#complete-workflow-diagram)
3. [State Management](#state-management)
4. [Orchestration Nodes](#orchestration-nodes)
5. [Conditional Routing Logic](#conditional-routing-logic)
6. [Sub-Graph Architecture](#sub-graph-architecture)
7. [Database Integration Patterns](#database-integration-patterns)
8. [Checkpointing & State Persistence](#checkpointing--state-persistence)
9. [End-to-End Example](#end-to-end-example)
10. [Architectural Principles](#architectural-principles)

---

## Overview

### What is LangGraph?

LangGraph is a library for building stateful, multi-actor applications with LLMs. It extends LangChain's Expression Language with the ability to coordinate multiple chains (or actors) across multiple steps of computation in a cyclic manner.

### Our Architecture

The Virtual Waiter uses LangGraph to orchestrate:

- **8 Specialist Agents**: booking, payment, user, customer_satisfaction, support, general_queries, response, food_ordering
- **5 Food Ordering Sub-Agents**: menu_browsing, menu_discovery, cart_management, checkout_validator, checkout_executor
- **6 Orchestration Nodes**: auth, perceive, clarify, task_manager, validation, router
- **1 Formatting Layer**: response_agent (Virtual Waiter personality)

**Total**: 20+ nodes coordinated through a single StateGraph

---

## Complete Workflow Diagram

This is the exact current workflow as implemented in `app/orchestration/graph.py`:

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           USER MESSAGE INPUT                               │
│                      (HTTP POST /chat/message)                             │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │      START           │
                        │  (Graph Entry Point) │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │    AUTH NODE         │
                        │  Multi-Tier Identity │
                        │  Recognition         │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
            Auth Flow Active                 Authenticated
            (Waiting for OTP)              or Anonymous OK
                    │                             │
                    ▼                             ▼
            ┌──────────┐              ┌──────────────────────┐
            │   END    │              │   PERCEIVE NODE      │
            │(Wait for │              │ Intent Classification│
            │ input)   │              │ Entity Extraction    │
            └──────────┘              └──────────┬───────────┘
                                                 │
                                  ┌──────────────┴──────────────┐
                                  │                             │
                         Unclear Intent                  Clear Intent
                      (requires_clarification=True)   (requires_clarification=False)
                                  │                             │
                                  ▼                             ▼
                      ┌──────────────────────┐    ┌──────────────────────┐
                      │  CLARIFICATION NODE  │    │  TASK MANAGER NODE   │
                      │ Ask follow-up question│    │  Entity Enrichment   │
                      └──────────┬───────────┘    │  Task Context Setup  │
                                 │                └──────────┬───────────┘
                                 │                           │
                                 │                           ▼
                                 │              ┌──────────────────────┐
                                 │              │   VALIDATION NODE    │
                                 │              │  7 Validation Rules  │
                                 │              └──────────┬───────────┘
                                 │                         │
                                 │              ┌──────────┴──────────┐
                                 │              │                     │
                                 │         Validation              Validation
                                 │          Passed                  Failed
                                 │              │                     │
                                 │              ▼                     │
                                 │    ┌──────────────────┐           │
                                 │    │   ROUTER NODE    │           │
                                 │    │ Intent→Agent Map │           │
                                 │    │ Auth Check       │           │
                                 │    └────────┬─────────┘           │
                                 │             │                     │
                      ┌──────────┴─────────────┴─────────┬───────────┘
                      │                                   │
                      ▼                                   │
         ┌────────────────────────┐                      │
         │   AGENT ROUTING        │                      │
         │   (8 main agents)      │                      │
         └────────┬───────────────┘                      │
                  │                                       │
    ┌─────────────┼────────┬──────────┬─────────┬───────┼─────┬─────────┐
    │             │        │          │         │       │     │         │
    ▼             ▼        ▼          ▼         ▼       ▼     ▼         ▼
┌────────┐  ┌─────────┐ ┌────┐  ┌────────┐ ┌─────┐ ┌────┐ ┌────┐  ┌─────┐
│greeting│  │ food_   │ │book│  │booking_│ │pay  │ │user│ │cust│  │gen  │
│_agent  │  │ordering │ │ing │  │mgmt    │ │ment │ │_   │ │sat │  │queries
│        │  │_agent   │ │_   │  │_agent  │ │_    │ │agent│ │_   │  │_agent│
│        │  │ (SUB-   │ │agent│  │        │ │agent│ │    │ │agent│  │     │
│        │  │  GRAPH) │ │    │  │        │ │     │ │    │ │    │  │     │
└────┬───┘  └────┬────┘ └─┬──┘  └───┬────┘ └──┬──┘ └─┬──┘ └─┬──┘  └──┬──┘
     │           │         │         │         │      │      │        │
     │           │         │         │         │      │      │        │
     │           │    ┌────┴─────────┴─────────┴──────┴──────┴────────┘
     │           │    │
     │           │    │    ┌──────────────────────────────────────┐
     │           │    │    │  support_agent                       │
     │           │    │    └──────────────────┬───────────────────┘
     │           │    │                       │
     │           │    └───────────────────────┘
     │           │
     │    ┌──────┴───────────────────────────────────────────┐
     │    │                                                   │
     │    │  ┌──────────────────────────────────────────┐   │
     │    │  │   FOOD ORDERING SUB-GRAPH                │   │
     │    │  │   (Hierarchical Agent System)            │   │
     │    │  │                                           │   │
     │    │  │   Flow:                                   │   │
     │    │  │   1. Sub-Intent Classification (LLM)     │   │
     │    │  │   2. Entity Validation                   │   │
     │    │  │   3. Guardrail Checks                    │   │
     │    │  │   4. Route to Sub-Agent (deterministic)  │   │
     │    │  │                                           │   │
     │    │  │   Sub-Agents:                            │   │
     │    │  │   ┌──────────────┐  ┌──────────────┐   │   │
     │    │  │   │menu_browsing │  │menu_discovery│   │   │
     │    │  │   └──────────────┘  └──────────────┘   │   │
     │    │  │   ┌──────────────┐  ┌──────────────┐   │   │
     │    │  │   │cart_         │  │checkout_     │   │   │
     │    │  │   │management    │  │validator     │   │   │
     │    │  │   └──────────────┘  └──────────────┘   │   │
     │    │  │   ┌──────────────┐                     │   │
     │    │  │   │checkout_     │                     │   │
     │    │  │   │executor      │                     │   │
     │    │  │   └──────────────┘                     │   │
     │    │  │                                           │   │
     │    │  │   Returns: ActionResult                  │   │
     │    │  └───────────────────────────────────────────┘   │
     │    │                                                   │
     │    └───────────────────────────┬───────────────────────┘
     │                                │
     │                                │
     └────────────────┬───────────────┘
                      │
                      │ All agents return ActionResult
                      │ (structured data)
                      │
                      ▼
           ┌──────────────────────┐
           │   RESPONSE AGENT     │
           │   Virtual Waiter     │
           │   Formatting Layer   │
           │                      │
           │ - Hospitality tone   │
           │ - Upselling logic    │
           │ - Personalization    │
           └──────────┬───────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │        END           │
           │                      │
           │ Return formatted     │
           │ response to user     │
           └──────────────────────┘


LEGEND:
━━━━━  Main orchestration flow
──────  Agent execution flow
▼       Flow direction
┌─┐    Node/Component
```

---

## State Management

### AgentState Schema

The `AgentState` TypedDict is the single source of truth for all conversation data. It uses LangGraph's `add_messages` reducer for automatic message deduplication.

**Location**: `app/orchestration/state.py`

#### Core State Fields

```python
class AgentState(TypedDict, total=False):
    # Message History (with automatic deduplication)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Session Context
    session_id: str                    # Unique session identifier
    user_id: Optional[str]             # User ID (if authenticated)
    device_id: Optional[str]           # Device fingerprint
    session_token: Optional[str]       # 30-day long-lived token
    restaurant_id: Optional[str]       # Multi-tenant support

    # Authentication State (Centralized)
    is_authenticated: bool             # True if user_id exists
    auth_tier: int                     # 1=Anonymous, 2=Authenticated
    authentication_step: Optional[str] # Current auth step

    # User Identity
    user_phone: Optional[str]          # Phone number
    user_name: Optional[str]           # Full name
    user_email: Optional[str]          # Email address

    # Task Management
    active_task_type: Optional[TaskType]
    active_task_status: Optional[TaskStatus]
    task_entities: Dict[str, Any]      # Current task entities
    task_stack: List[TaskContext]      # Suspended tasks

    # Intent & Routing
    current_intent: Optional[str]      # Classified intent
    intent_confidence: float           # Confidence score
    selected_agent: Optional[str]      # Routed agent

    # Agent Results
    agent_response: Optional[str]      # Final response text
    agent_metadata: Dict[str, Any]     # Agent execution metadata
    action_result: Optional[Dict[str, Any]]  # ActionResult from agents

    # Control Flow
    requires_clarification: bool       # If true, route to clarify
    should_end: bool                   # If true, end conversation

    # Memory & Context
    user_memory: Dict[str, Any]        # Semantic memory
    conversation_summary: Optional[str] # Conversation summary
```

### State Persistence

State is persisted using **MemorySaver** checkpointing:

- **Scope**: Per-session (thread_id = session_id)
- **Lifetime**: During server uptime (lost on restart)
- **Method**: In-memory storage
- **Future**: Can migrate to PostgreSQL/Redis checkpointing when LangGraph fixes async compatibility

**Configuration**:
```python
config: RunnableConfig = {
    "configurable": {
        "thread_id": session_id  # Enables conversation continuity
    }
}

# Execute graph with checkpointing
final_state = await graph.ainvoke(initial_state, config)
```

### State Updates & Merging

LangGraph automatically merges state updates from nodes:

```python
# Node returns partial state update
return {
    "current_intent": "booking_request",
    "intent_confidence": 0.95,
    "extracted_entities": {"party_size": 2, "date": "2024-01-15"}
}

# LangGraph merges this with existing state
# Previous state values are preserved unless explicitly overwritten
```

**Key Features**:
- **Immutable Updates**: Original state never modified
- **Automatic Merging**: Dictionary updates are merged, not replaced
- **Message Deduplication**: `add_messages` reducer prevents duplicate messages
- **Type Safety**: TypedDict provides static type checking

---

## Orchestration Nodes

### 1. Auth Node

**Purpose**: Multi-tier identity recognition and authentication orchestration

**Location**: `app/orchestration/nodes/auth.py`

**Flow**:
```
Input: user_message, device_id, session_token
  ↓
Check Tier 1: Anonymous (device_id only)
Check Tier 2: Authenticated (session_token + user data)
  ↓
If authenticated → Proceed to perceive
If auth required → Start OTP flow
If OTP pending → Wait for OTP (return END)
```

**State Updates**:
```python
{
    "is_authenticated": bool,
    "auth_tier": 1 or 2,
    "user_id": str or None,
    "user_phone": str or None,
    "user_name": str or None,
    "authentication_step": "phone_collection" | "otp_sent" | "otp_verification"
}
```

**Routing**:
- `END` if waiting for OTP input (conversation paused)
- `perceive` if authenticated or anonymous OK

---

### 2. Perceive Node

**Purpose**: Intent classification and entity extraction using LLM

**Location**: `app/orchestration/nodes/perceive.py`

**Flow**:
```
Input: user_message, conversation history
  ↓
LLM Classification:
  - Intent (e.g., "booking_request", "order_request")
  - Entities (e.g., {"party_size": 2, "time": "19:00"})
  - Confidence score
  - Sentiment analysis
  ↓
Determine if clarification needed
```

**State Updates**:
```python
{
    "current_intent": str,
    "intent_confidence": float,
    "extracted_entities": Dict[str, Any],
    "user_sentiment": "positive" | "neutral" | "negative",
    "requires_clarification": bool
}
```

**Routing**:
- `clarify` if intent unclear (confidence < threshold)
- `task_manager` if intent clear

---

### 3. Clarification Node

**Purpose**: Ask follow-up questions when intent is unclear

**Location**: `app/orchestration/nodes/clarify.py`

**Flow**:
```
Input: unclear intent, partial entities
  ↓
Generate clarifying question:
  "Did you want to book a table or order food for pickup?"
  ↓
Route through response_agent for consistent tone
  ↓
END (wait for user's clarification)
```

**State Updates**:
```python
{
    "agent_response": "Clarifying question...",
    "requires_clarification": True
}
```

**Routing**:
- Always → `response_agent` → `END`

---

### 4. Task Manager Node

**Purpose**: Entity enrichment and task context setup

**Location**: `app/orchestration/nodes/task_manager.py`

**Flow**:
```
Input: intent, entities
  ↓
Merge with existing task_entities (multi-turn accumulation)
  ↓
Check if task should be resumed from stack
  ↓
Set active_task_type and active_task_status
```

**State Updates**:
```python
{
    "active_task_type": TaskType,
    "task_entities": {**previous_entities, **new_entities},
    "task_metadata": {"started_at": timestamp}
}
```

**Routing**:
- Always → `validation`

---

### 5. Validation Node

**Purpose**: Validate entities against 7 business rules before routing to agents

**Location**: `app/orchestration/nodes/validation.py`

**7 Validation Rules**:
1. **Required Fields**: Check if required entities present
2. **Phone Format**: Validate phone number (10 digits, starts with 6/7/8/9)
3. **Email Format**: Validate email structure
4. **Date/Time**: Check if date/time is valid and in future
5. **Party Size**: Ensure party_size is positive integer (1-50)
6. **Amount**: Validate monetary amounts are positive
7. **Business Hours**: Check if booking time within operating hours

**Flow**:
```
Input: intent, entities
  ↓
Apply validation rules
  ↓
If validation fails:
  - Set requires_clarification = True
  - Set validation_errors list
  - Route to response_agent (show error)
  ↓
If validation passes:
  - Route to router
```

**State Updates** (on failure):
```python
{
    "requires_clarification": True,
    "validation_errors": ["Phone number must be 10 digits"],
    "agent_response": "Error message..."
}
```

**Routing**:
- `response_agent` if validation failed
- `router` if validation passed

---

### 6. Router Node

**Purpose**: Map intent to specialist agent and check authentication requirements

**Location**: `app/orchestration/nodes/router.py`

**Intent-to-Agent Mapping**:
```python
{
    "greeting": "greeting_agent",
    "menu_inquiry": "food_ordering_agent",       # Sub-graph
    "order_request": "food_ordering_agent",      # Sub-graph
    "booking_request": "booking_agent",
    "payment_question": "payment_agent",
    "complaint": "customer_satisfaction_agent",
    "faq": "general_queries_agent",
    # ... etc
}
```

**Authentication Check**:
```python
# Agents requiring authentication:
transactional_agents = [
    "booking_agent",
    "order_agent",
    "food_ordering_agent",  # When cart has items
    "payment_agent"
]

if selected_agent in transactional_agents and not is_authenticated:
    # Route to user_agent first
    return {
        "selected_agent": "user_agent",
        "original_intent_agent": selected_agent  # Resume after auth
    }
```

**State Updates**:
```python
{
    "selected_agent": str,
    "original_intent_agent": str or None,  # If auth required
    "auth_required": bool
}
```

**Routing**:
- Dynamic routing based on `selected_agent` value
- If auth required → `user_agent` first, then back to original agent

---

## Conditional Routing Logic

### Route Functions

LangGraph uses **conditional edges** for dynamic routing. These are pure functions that examine state and return the next node name.

#### 1. `route_from_auth`

**Location**: `app/orchestration/nodes/auth.py`

```python
def route_from_auth(state: AgentState) -> Literal["perceive", END]:
    """
    Route after authentication node.

    Returns:
        - END: If waiting for OTP input (pause conversation)
        - "perceive": If authenticated or anonymous OK (continue)
    """
    auth_step = state.get("authentication_step")

    if auth_step in ["otp_sent", "otp_verification"]:
        return END  # Wait for user input

    return "perceive"  # Continue to intent classification
```

#### 2. `should_clarify`

**Location**: `app/orchestration/graph.py`

```python
def should_clarify(state: AgentState) -> Literal["clarify", "task_manager"]:
    """
    Determine if clarification needed after perception.

    Returns:
        - "clarify": If requires_clarification flag is True
        - "task_manager": If intent is clear
    """
    return "clarify" if state.get("requires_clarification") else "task_manager"
```

#### 3. `route_from_validation`

**Location**: `app/orchestration/graph.py`

```python
def route_from_validation(state: AgentState) -> Literal["router", "response_agent"]:
    """
    Route after validation gate.

    Returns:
        - "response_agent": If validation failed (show error)
        - "router": If validation passed (continue to agent)
    """
    return "response_agent" if state.get("requires_clarification") else "router"
```

#### 4. `route_to_agent`

**Location**: `app/orchestration/graph.py`

```python
def route_to_agent(state: AgentState) -> str:
    """
    Route to appropriate specialist agent.

    Returns:
        Agent name from selected_agent field, or "fallback" if missing
    """
    selected_agent = state.get("selected_agent")
    return selected_agent if selected_agent else "fallback"
```

#### 5. `route_after_user_agent`

**Location**: `app/orchestration/graph.py`

```python
def route_after_user_agent(state: AgentState) -> str:
    """
    Route after authentication completes.

    If original_intent_agent exists (auth was required for another agent),
    route back to that agent. Otherwise, end conversation.

    Returns:
        - Agent name: Resume original intent
        - END: No original intent (standalone auth)
    """
    original_agent = state.get("original_intent_agent")
    return original_agent if original_agent else END
```

### Edge Configuration

**Location**: `app/orchestration/graph.py` (create_restaurant_graph function)

```python
# Example: Conditional edge from perceive node
workflow.add_conditional_edges(
    "perceive",              # Source node
    should_clarify,          # Route function
    {                        # Destination mapping
        "clarify": "clarify",
        "task_manager": "task_manager"
    }
)
```

---

## Sub-Graph Architecture

### Food Ordering Sub-Graph

The `food_ordering_agent` is a **hierarchical agent system** that implements its own internal workflow.

**Location**: `app/agents/food_ordering/graph.py`

#### Sub-Graph Flow

```
User Message (from router)
  ↓
┌──────────────────────────────────────────────────────────┐
│  FOOD ORDERING SUB-GRAPH                                 │
│                                                           │
│  Step 1: Sub-Intent Classification (LLM)                 │
│  ────────────────────────────────────                    │
│  Input: user_message, FoodOrderingState                  │
│  LLM classifies into 1 of 5 sub-intents:                 │
│    - browse_menu                                         │
│    - discover_items                                      │
│    - manage_cart                                         │
│    - validate_order                                      │
│    - execute_checkout                                    │
│  Output: SubIntentClassification (Pydantic model)        │
│                                                           │
│  ↓                                                        │
│                                                           │
│  Step 2: Entity Validation                               │
│  ────────────────────────                                │
│  Check if required entities present for sub-intent       │
│  If missing → Return clarification_needed ActionResult   │
│                                                           │
│  ↓                                                        │
│                                                           │
│  Step 3: Guardrail Checks                                │
│  ────────────────────────                                │
│  Apply state-based guardrails:                           │
│    - SOFT GUIDES: Helpful redirects                      │
│      • Empty cart checkout → Suggest browsing            │
│    - HARD BLOCKS: Safety gates                           │
│      • Cannot modify locked cart                         │
│      • Cannot checkout without validation                │
│      • Cannot checkout without auth (if required)        │
│  If guardrail triggered → Return override ActionResult   │
│                                                           │
│  ↓                                                        │
│                                                           │
│  Step 4: Route to Sub-Agent (Deterministic)              │
│  ─────────────────────────────────────────               │
│  No LLM - pure dictionary lookup                         │
│  {                                                        │
│    "browse_menu": menu_browsing_agent,                   │
│    "discover_items": menu_discovery_agent,               │
│    "manage_cart": cart_management_agent,                 │
│    "validate_order": checkout_validator_agent,           │
│    "execute_checkout": checkout_executor_agent           │
│  }                                                        │
│                                                           │
│  ↓                                                        │
│                                                           │
│  Step 5: Execute Sub-Agent                               │
│  ─────────────────────────                               │
│  Each sub-agent:                                         │
│    1. Receives entities and state                        │
│    2. Performs database operations                       │
│    3. Returns ActionResult (structured data)             │
│                                                           │
│  ↓                                                        │
│                                                           │
│  Return ActionResult to Parent Graph                     │
│  ───────────────────────────────────                     │
│  {                                                        │
│    "action": "menu_categories_shown",                    │
│    "success": true,                                      │
│    "data": { "categories": [...] },                      │
│    "context": { "sub_intent": "browse_menu" }            │
│  }                                                        │
│                                                           │
└───────────────────────────────────────────────────────────┘
  ↓
Response Agent (formats ActionResult into friendly response)
```

#### Why Sub-Graph?

**Benefits**:
1. **Domain Isolation**: Food ordering logic encapsulated in one module
2. **Single LLM Call**: Only sub-intent classification uses LLM, rest is deterministic
3. **Specialized State**: FoodOrderingState extends AgentState with domain-specific fields
4. **Independent Development**: Food ordering team can work independently
5. **Reusability**: Sub-graph can be reused in other contexts (mobile app, voice)

**Trade-offs**:
- Additional complexity compared to single-level agents
- State synchronization between parent and sub-graph
- Debugging requires understanding two levels

#### Sub-Agent Examples

**Menu Browsing Agent**:
```python
async def menu_browsing_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    Browse menu structure (categories, items in category).

    Operations:
    - Show all categories
    - Show items in specific category

    Returns:
        ActionResult with menu data
    """
    category_name = entities.get("category_name")

    if category_name:
        # Fetch items in category from PostgreSQL
        items = await db.fetch_items_by_category(category_name)
        return {
            "action": "category_items_shown",
            "success": True,
            "data": {"items": items, "category": category_name},
            "context": {}
        }
    else:
        # Show all categories
        categories = await db.fetch_all_categories()
        return {
            "action": "menu_categories_shown",
            "success": True,
            "data": {"categories": categories},
            "context": {}
        }
```

**Cart Management Agent**:
```python
async def cart_management_agent(
    entities: Dict[str, Any],
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    Manage shopping cart operations.

    Operations:
    - add: Add item to cart
    - remove: Remove item from cart
    - update: Update item quantity
    - view: Show cart contents
    - clear: Empty cart

    Database: MongoDB (cart storage)

    Returns:
        ActionResult with cart data
    """
    action = entities.get("action")
    session_id = state.get("session_id")

    if action == "add":
        item_name = entities.get("item_name")
        quantity = entities.get("quantity", 1)

        # Fetch item from PostgreSQL
        item = await db.get_menu_item_by_name(item_name)

        # Add to cart in MongoDB
        cart = await mongo.add_to_cart(session_id, item, quantity)

        return {
            "action": "item_added_to_cart",
            "success": True,
            "data": {
                "cart_items": cart["items"],
                "cart_subtotal": cart["subtotal"],
                "item_added": item_name,
                "quantity": quantity
            },
            "context": {}
        }

    # ... other cart operations
```

---

## Database Integration Patterns

### Multi-Database Architecture

The system uses **3 databases** for different purposes:

1. **PostgreSQL** (Primary)
   - Menu items, orders, bookings, users
   - ACID transactions
   - Complex queries

2. **Redis** (Caching & Rate Limiting)
   - Inventory reservations (temporary holds)
   - Rate limiting (OTP attempts, daily limits)
   - Session management

3. **MongoDB** (Document Store)
   - Shopping cart storage (nested structure)
   - Flexible schema for cart items

### Database Operation Flow

#### Example: Adding Item to Cart

```
1. User: "Add butter chicken"
   ↓
2. Sub-Intent Classifier: "manage_cart" with action="add", item_name="butter chicken"
   ↓
3. Cart Management Agent:

   Step A: Fetch item from PostgreSQL
   ─────────────────────────────────
   SELECT id, name, price, category, description, image_url, is_available
   FROM menu_items
   WHERE name ILIKE '%butter chicken%'
   AND is_available = true
   LIMIT 1;

   Step B: Check inventory in Redis
   ────────────────────────────────
   HGET inventory:butter_chicken available_quantity
   → Returns: 50

   Step C: Reserve quantity in Redis
   ─────────────────────────────────
   HINCRBY inventory:butter_chicken reserved_quantity 1
   SET reservation:session_abc123:item_456 1 EX 900  (15-min TTL)

   Step D: Add to cart in MongoDB
   ──────────────────────────────
   db.carts.updateOne(
     { session_id: "abc123" },
     {
       $push: {
         items: {
           item_id: "456",
           name: "Butter Chicken",
           quantity: 1,
           price: 350.00,
           added_at: ISODate("2024-01-15T19:30:00Z")
         }
       },
       $inc: { subtotal: 350.00 }
     },
     { upsert: true }
   )

   Step E: Return ActionResult
   ───────────────────────────
   {
     "action": "item_added_to_cart",
     "success": true,
     "data": {
       "item_name": "Butter Chicken",
       "quantity": 1,
       "price": 350.00,
       "cart_items": [...],
       "cart_subtotal": 350.00
     }
   }
```

#### Example: Checkout (Multi-Database Transaction)

```
1. Checkout Executor Agent:

   Step A: Validate cart in MongoDB
   ────────────────────────────────
   cart = db.carts.findOne({ session_id: "abc123" })
   if not cart or len(cart["items"]) == 0:
     return error

   Step B: Begin PostgreSQL transaction
   ────────────────────────────────────
   BEGIN;

   -- Create order
   INSERT INTO orders (user_id, order_number, total_amount, status, order_type)
   VALUES ('user_789', 'ORD-20240115-001', 350.00, 'pending', 'dine_in')
   RETURNING id;

   -- Create order items
   INSERT INTO order_items (order_id, menu_item_id, quantity, price)
   SELECT '...', item_id, quantity, price FROM cart_items;

   COMMIT;

   Step C: Confirm inventory in Redis
   ──────────────────────────────────
   HINCRBY inventory:butter_chicken available_quantity -1
   HINCRBY inventory:butter_chicken reserved_quantity -1
   DEL reservation:session_abc123:item_456

   Step D: Clear cart in MongoDB
   ─────────────────────────────
   db.carts.deleteOne({ session_id: "abc123" })

   Step E: Return ActionResult with order details
```

### Database Service Layer

**Location**: `app/db_services/`

Each agent interacts with databases through service classes:

```python
# PostgreSQL Service
from app.db_services.menu_service import menu_service
items = await menu_service.get_items_by_category("appetizers")

# Redis Service
from app.db_services.redis_service import redis_service
await redis_service.reserve_inventory("item_123", quantity=2, session_id="abc")

# MongoDB Service
from app.db_services.cart_service import cart_service
cart = await cart_service.add_item(session_id="abc", item=item_data, quantity=1)
```

---

## Checkpointing & State Persistence

### How Checkpointing Works

LangGraph's checkpointing system saves state snapshots after each node execution, enabling:

1. **Conversation Continuity**: Resume conversations across HTTP requests
2. **Multi-Turn Flows**: Handle authentication, entity collection, etc.
3. **Error Recovery**: Rollback to previous checkpoint on failure
4. **State History**: Query past conversation states

### Current Implementation: MemorySaver

**Location**: `app/orchestration/graph.py` (get_or_create_checkpointer function)

```python
# Initialize checkpointer (singleton pattern)
checkpointer = MemorySaver()

# Compile graph with checkpointing
compiled_graph = workflow.compile(checkpointer=checkpointer)

# Execute with session-specific thread_id
config = {"configurable": {"thread_id": session_id}}
final_state = await compiled_graph.ainvoke(initial_state, config)
```

**Features**:
- ✅ Fast (in-memory)
- ✅ Reliable (no external dependencies)
- ✅ Async-compatible
- ❌ Lost on server restart (not persisted)
- ❌ Not suitable for multi-server deployment

### Future: PostgreSQL Checkpointing

**Blocked**: LangGraph v0.6.7 has sync/async API incompatibility
- `PostgresSaver` (sync) missing `aget_tuple()` needed by `ainvoke()`
- `AsyncPostgresSaver` (async) missing `get_tuple()` needed by `get_state()`

**When fixed**, migration will be straightforward:
```python
from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
from psycopg_pool import ConnectionPool

pool = ConnectionPool(conninfo=database_url, max_size=10)
checkpointer = PostgresSaver(pool)
checkpointer.setup()  # Creates checkpoints table

compiled_graph = workflow.compile(checkpointer=checkpointer)
```

**Benefits**:
- ✅ State persists across server restarts
- ✅ Works in multi-server deployments
- ✅ Can query historical conversations
- ✅ Supports time-travel debugging

### Checkpoint Schema

When PostgreSQL checkpointing is enabled, state is stored in:

**Table**: `checkpoints`
```sql
CREATE TABLE checkpoints (
    thread_id TEXT NOT NULL,       -- session_id
    checkpoint_ns TEXT NOT NULL DEFAULT '',
    checkpoint_id TEXT NOT NULL,   -- UUID for each checkpoint
    parent_checkpoint_id TEXT,     -- Links to previous checkpoint
    type TEXT,                     -- Node type
    checkpoint JSONB NOT NULL,     -- Full state snapshot
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
);
```

**State Retrieval**:
```python
# Get current state
state = graph.get_state(config)

# Get state history
history = list(graph.get_state_history(config))

# Time-travel to specific checkpoint
config_with_checkpoint = {
    "configurable": {
        "thread_id": session_id,
        "checkpoint_id": "previous-checkpoint-uuid"
    }
}
state_at_point = graph.get_state(config_with_checkpoint)
```

---

## End-to-End Example

### Example: User Orders Butter Chicken

**User Journey**: First-time user orders food via chat

#### Turn 1: Initial Greeting

**User**: "Hi"

**Graph Execution**:
```
START
  ↓
auth_node
  → Tier 1 (Anonymous): No session_token
  → auth_tier = 1, is_authenticated = False
  → Route: "perceive"
  ↓
perceive_node
  → LLM classifies: intent = "greeting", confidence = 0.98
  → requires_clarification = False
  → Route: "task_manager"
  ↓
task_manager_node
  → active_task_type = TaskType.GREETING
  → Route: "validation"
  ↓
validation_node
  → No entities to validate (greeting)
  → Route: "router"
  ↓
router_node
  → intent_agent_mapping["greeting"] = "greeting_agent"
  → selected_agent = "greeting_agent"
  → Route: "greeting_agent"
  ↓
greeting_agent_node
  → Generate friendly greeting
  → agent_response = "Hey there! 👋 Welcome to [Restaurant]! I'm here to help you with your order or answer any questions..."
  → Route: END (greeting_agent bypasses response_agent)
  ↓
END
```

**Response**: "Hey there! 👋 Welcome to [Restaurant]! I'm here to help you with your order or answer any questions..."

**State Checkpoint** (saved in MemorySaver):
```json
{
  "session_id": "sess_abc123",
  "messages": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hey there! 👋..."}
  ],
  "is_authenticated": false,
  "auth_tier": 1,
  "current_intent": "greeting",
  "selected_agent": "greeting_agent"
}
```

---

#### Turn 2: Order Request

**User**: "I want to order butter chicken"

**Graph Execution**:
```
START (load checkpoint for sess_abc123)
  ↓
auth_node
  → Load checkpoint: auth_tier = 1 (Anonymous)
  → No auth_step pending
  → Route: "perceive"
  ↓
perceive_node
  → LLM classifies:
      intent = "order_request"
      confidence = 0.93
      entities = {"item_name": "butter chicken"}
  → requires_clarification = False
  → Route: "task_manager"
  ↓
task_manager_node
  → active_task_type = TaskType.ORDER_REQUEST
  → task_entities = {"item_name": "butter chicken"}
  → Route: "validation"
  ↓
validation_node
  → Validate: item_name is string ✓
  → Route: "router"
  ↓
router_node
  → intent_agent_mapping["order_request"] = "food_ordering_agent"
  → selected_agent = "food_ordering_agent"
  → Auth check: Not required for browsing/adding to cart (Tier 1 OK)
  → Route: "food_ordering_agent"
  ↓
food_ordering_agent_node (SUB-GRAPH)
  ↓
  ┌─────────────────────────────────────────────────┐
  │ Food Ordering Sub-Graph                         │
  │                                                  │
  │ Step 1: Sub-Intent Classification                │
  │   → LLM input: "I want to order butter chicken" │
  │   → Classification:                              │
  │       sub_intent = "manage_cart"                 │
  │       entities = {"action": "add",               │
  │                   "item_name": "butter chicken"} │
  │   → confidence = 0.91                            │
  │                                                  │
  │ Step 2: Entity Validation                        │
  │   → Required: action ✓, item_name ✓             │
  │   → All required entities present                │
  │                                                  │
  │ Step 3: Guardrail Checks                         │
  │   → Cart locked? No ✓                            │
  │   → All guardrails passed                        │
  │                                                  │
  │ Step 4: Route to Sub-Agent                       │
  │   → route_to_agent("manage_cart")                │
  │   → agent = cart_management_agent                │
  │                                                  │
  │ Step 5: Execute Cart Management Agent            │
  │   ↓                                              │
  │   A) Fetch item from PostgreSQL                  │
  │      SELECT * FROM menu_items                    │
  │      WHERE name ILIKE '%butter chicken%'         │
  │      → item_id=123, price=350.00                 │
  │                                                  │
  │   B) Check inventory in Redis                    │
  │      HGET inventory:123 available_quantity       │
  │      → 50 available ✓                            │
  │                                                  │
  │   C) Reserve in Redis                            │
  │      HINCRBY inventory:123 reserved_quantity 1   │
  │      SET reservation:sess_abc123:123 1 EX 900    │
  │                                                  │
  │   D) Add to cart in MongoDB                      │
  │      db.carts.updateOne(                         │
  │        {session_id: "sess_abc123"},              │
  │        {$push: {items: {...}}, $inc: {...}}      │
  │      )                                           │
  │      → cart_items = [butter_chicken]             │
  │      → cart_subtotal = 350.00                    │
  │                                                  │
  │   E) Return ActionResult                         │
  │      {                                           │
  │        "action": "item_added_to_cart",           │
  │        "success": true,                          │
  │        "data": {                                 │
  │          "item_name": "Butter Chicken",          │
  │          "quantity": 1,                          │
  │          "price": 350.00,                        │
  │          "cart_items": [                         │
  │            {"name": "Butter Chicken",            │
  │             "quantity": 1,                       │
  │             "price": 350.00}                     │
  │          ],                                      │
  │          "cart_subtotal": 350.00                 │
  │        },                                        │
  │        "context": {                              │
  │          "sub_intent": "manage_cart"             │
  │        }                                         │
  │      }                                           │
  └──────────────────┬──────────────────────────────┘
                     │
  ↓
response_agent_node (Virtual Waiter)
  → Input: ActionResult from food_ordering_agent
  → LLM prompt:
      System: "You are a warm, casual virtual waiter..."
      User: "Format this action: item_added_to_cart
             Details: Butter Chicken added, 1x ₹350.00
             Cart total: ₹350.00"
  → LLM generates friendly response
  → agent_response = "Great choice! I've added Butter Chicken to your cart. That'll be ₹350 so far. Want to add anything else?"
  → Route: END
  ↓
END
```

**Response**: "Great choice! I've added Butter Chicken to your cart. That'll be ₹350 so far. Want to add anything else?"

**State Checkpoint** (updated):
```json
{
  "session_id": "sess_abc123",
  "messages": [
    {"role": "user", "content": "Hi"},
    {"role": "assistant", "content": "Hey there! 👋..."},
    {"role": "user", "content": "I want to order butter chicken"},
    {"role": "assistant", "content": "Great choice! I've added..."}
  ],
  "is_authenticated": false,
  "auth_tier": 1,
  "current_intent": "order_request",
  "selected_agent": "food_ordering_agent",
  "task_entities": {
    "cart_items": [{"name": "Butter Chicken", "quantity": 1, "price": 350.00}],
    "cart_subtotal": 350.00
  },
  "action_result": { /* ActionResult from food_ordering_agent */ }
}
```

---

#### Turn 3: Checkout Request

**User**: "Checkout please"

**Graph Execution**:
```
START (load checkpoint)
  ↓
auth_node
  → Load checkpoint: cart has items, auth_tier = 1 (Anonymous)
  → Auth required for checkout
  → Route: "perceive" (continue classification first)
  ↓
perceive_node
  → LLM classifies:
      intent = "order_request"
      confidence = 0.95
      context: "checkout" keyword
  → Route: "task_manager"
  ↓
task_manager_node
  → Merge entities with cart state
  → Route: "validation"
  ↓
validation_node
  → Validation passes
  → Route: "router"
  ↓
router_node
  → selected_agent = "food_ordering_agent"
  → Auth check: Cart has items → AUTHENTICATION REQUIRED
  → Route: "user_agent"
  ↓
user_agent_node (Authentication Flow)
  ↓
  A) Phone Collection
     → agent_response = "To complete your order, I'll need your phone number. What's your mobile number?"
     → authentication_step = "phone_collection"
     → Route: END (wait for phone number)
```

**Response**: "To complete your order, I'll need your phone number. What's your mobile number?"

**State Checkpoint**:
```json
{
  "session_id": "sess_abc123",
  "is_authenticated": false,
  "auth_tier": 1,
  "authentication_step": "phone_collection",
  "selected_agent": "user_agent",
  "original_intent_agent": "food_ordering_agent",  # Resume after auth
  "task_entities": {
    "cart_items": [...],
    "cart_subtotal": 350.00
  }
}
```

---

#### Turn 4: Phone Number Provided

**User**: "9876543210"

**Graph Execution**:
```
START (load checkpoint)
  ↓
auth_node
  → Load checkpoint: authentication_step = "phone_collection"
  → Phone number provided: "9876543210"
  → Validate phone format: ✓ (10 digits, starts with 9)

  A) Check if user exists
     SELECT id, phone, full_name FROM users
     WHERE phone = '9876543210';
     → User exists: user_id = "user_789", name = "Jeswin"

  B) Generate OTP
     INSERT INTO otp_codes (user_id, phone, code, expires_at)
     VALUES ('user_789', '9876543210', '123456', NOW() + INTERVAL '5 minutes')
     RETURNING id;
     → otp_id = "otp_abc"

  C) Send OTP via SMS
     SMS API: "Your OTP is 123456. Valid for 5 minutes."

  D) Update state
     → authentication_step = "otp_sent"
     → pending_otp_id = "otp_abc"
     → phone_number = "9876543210"
     → agent_response = "Great! I've sent a 6-digit code to 9876543210. Please enter it to continue."

  → Route: END (wait for OTP)
```

**Response**: "Great! I've sent a 6-digit code to 9876543210. Please enter it to continue."

**State Checkpoint**:
```json
{
  "session_id": "sess_abc123",
  "authentication_step": "otp_sent",
  "pending_otp_id": "otp_abc",
  "phone_number": "9876543210",
  "is_authenticated": false,
  "auth_tier": 1,
  "original_intent_agent": "food_ordering_agent"
}
```

---

#### Turn 5: OTP Verification

**User**: "123456"

**Graph Execution**:
```
START (load checkpoint)
  ↓
auth_node
  → Load checkpoint: authentication_step = "otp_sent"
  → OTP provided: "123456"

  A) Verify OTP
     SELECT * FROM otp_codes
     WHERE id = 'otp_abc'
     AND code = '123456'
     AND expires_at > NOW()
     AND is_used = false;
     → Match found ✓

  B) Mark OTP as used
     UPDATE otp_codes SET is_used = true WHERE id = 'otp_abc';

  C) Load user profile
     SELECT id, phone, full_name, email FROM users
     WHERE phone = '9876543210';
     → user_id = "user_789"
     → full_name = "Jeswin"
     → email = null

  D) Generate session token (30-day JWT)
     session_token = jwt.encode({
       "user_id": "user_789",
       "phone": "9876543210",
       "exp": now + 30 days
     })

  E) Link device
     INSERT INTO user_devices (user_id, device_id, session_token, last_seen)
     VALUES ('user_789', 'device_xyz', session_token, NOW());

  F) Update state
     → is_authenticated = true
     → auth_tier = 2
     → user_id = "user_789"
     → user_phone = "9876543210"
     → user_name = "Jeswin"
     → session_token = jwt_token
     → authentication_step = "completed"

  G) Resume original intent
     → original_intent_agent = "food_ordering_agent"
     → Route: "food_ordering_agent" (not END - resume order flow)
  ↓
food_ordering_agent_node (Resume Checkout)
  ↓
  Sub-Intent: "validate_order" (detected from context)
  ↓
  checkout_validator_agent
    A) Validate cart in MongoDB
       → cart has 1 item ✓

    B) Check inventory availability in Redis
       HGET inventory:123 available_quantity
       → 49 available (1 reserved by this session) ✓

    C) Validate total amount from PostgreSQL
       SELECT SUM(price * quantity) FROM cart_items...
       → Matches cart_subtotal ✓

    D) Set cart_validated flag

    E) Return ActionResult
       {
         "action": "cart_validated",
         "success": true,
         "data": {
           "cart_validated": true,
           "requires_order_type": true,
           "cart_summary": {
             "items": [{"name": "Butter Chicken", "quantity": 1, "price": 350.00}],
             "subtotal": 350.00,
             "tax": 62.99,
             "total": 412.99
           }
         }
       }
  ↓
response_agent_node
  → Format validation result
  → agent_response = "Perfect! Your order is ready. That'll be ₹412.99 total (including tax). Is this for dine-in or takeout?"
  → Route: END
```

**Response**: "Perfect! Your order is ready. That'll be ₹412.99 total (including tax). Is this for dine-in or takeout?"

**State Checkpoint** (fully authenticated):
```json
{
  "session_id": "sess_abc123",
  "is_authenticated": true,
  "auth_tier": 2,
  "user_id": "user_789",
  "user_phone": "9876543210",
  "user_name": "Jeswin",
  "session_token": "eyJhbGciOiJIUzI1NiIs...",
  "authentication_step": "completed",
  "task_entities": {
    "cart_items": [...],
    "cart_subtotal": 350.00,
    "cart_validated": true,
    "total_amount": 412.99
  }
}
```

---

#### Turn 6: Order Confirmation

**User**: "Dine-in please"

**Graph Execution**:
```
START (load checkpoint)
  ↓
auth_node
  → User authenticated (auth_tier = 2) ✓
  → Route: "perceive"
  ↓
perceive_node
  → LLM classifies:
      intent = "order_request"
      entities = {"order_type": "dine_in"}
  → Route: "task_manager"
  ↓
task_manager_node
  → Merge entities: task_entities["order_type"] = "dine_in"
  → Route: "validation"
  ↓
validation_node
  → Validation passes
  → Route: "router"
  ↓
router_node
  → selected_agent = "food_ordering_agent"
  → Route: "food_ordering_agent"
  ↓
food_ordering_agent_node
  ↓
  Sub-Intent: "execute_checkout"
  ↓
  checkout_executor_agent
    A) Validate preconditions
       → cart_validated = true ✓
       → is_authenticated = true ✓
       → order_type provided ✓

    B) Begin PostgreSQL transaction
       BEGIN;

       -- Create order
       INSERT INTO orders (
         user_id, order_number, total_amount,
         status, order_type, created_at
       )
       VALUES (
         'user_789', 'ORD-20240115-001', 412.99,
         'pending', 'dine_in', NOW()
       )
       RETURNING id;
       → order_id = "ord_456"

       -- Create order items
       INSERT INTO order_items (order_id, menu_item_id, quantity, price)
       VALUES ('ord_456', '123', 1, 350.00);

       COMMIT;

    C) Confirm inventory in Redis
       HINCRBY inventory:123 available_quantity -1
       HINCRBY inventory:123 reserved_quantity -1
       DEL reservation:sess_abc123:123

    D) Clear cart in MongoDB
       db.carts.deleteOne({session_id: "sess_abc123"})

    E) Generate payment link (Razorpay)
       payment_link = razorpay.create_payment_link({
         amount: 41299,  # In paise (₹412.99)
         order_id: "ord_456",
         customer: {
           name: "Jeswin",
           contact: "+919876543210"
         }
       })
       → payment_link_url = "https://rzp.io/i/abc123"

    F) Return ActionResult
       {
         "action": "order_placed",
         "success": true,
         "data": {
           "order_id": "ord_456",
           "order_number": "ORD-20240115-001",
           "total_amount": 412.99,
           "order_type": "dine_in",
           "payment_link": "https://rzp.io/i/abc123",
           "items": [
             {"name": "Butter Chicken", "quantity": 1, "price": 350.00}
           ]
         }
       }
  ↓
response_agent_node
  → Format order confirmation
  → agent_response = "Awesome! Your order #ORD-20240115-001 is confirmed for dine-in. Total: ₹412.99. Here's your payment link: https://rzp.io/i/abc123. Looking forward to serving you!"
  → Route: END
```

**Response**: "Awesome! Your order #ORD-20240115-001 is confirmed for dine-in. Total: ₹412.99. Here's your payment link: https://rzp.io/i/abc123. Looking forward to serving you!"

**Final State Checkpoint**:
```json
{
  "session_id": "sess_abc123",
  "is_authenticated": true,
  "auth_tier": 2,
  "user_id": "user_789",
  "session_token": "...",
  "current_intent": "order_request",
  "selected_agent": "food_ordering_agent",
  "task_entities": {
    "order_id": "ord_456",
    "order_number": "ORD-20240115-001",
    "total_amount": 412.99,
    "order_type": "dine_in",
    "cart_items": [],  # Cleared after checkout
    "cart_subtotal": 0
  },
  "agent_response": "Awesome! Your order #ORD-20240115-001..."
}
```

---

### What Just Happened?

**6 user messages → Complete order flow**:

1. ✅ Greeting handled by greeting_agent
2. ✅ Item added to cart by food_ordering_agent → cart_management sub-agent
3. ✅ Checkout triggered authentication flow
4. ✅ OTP sent and verified by user_agent
5. ✅ Order validated by checkout_validator sub-agent
6. ✅ Order placed by checkout_executor sub-agent

**Graph nodes executed**: 40+ node invocations across 6 turns

**Databases touched**:
- PostgreSQL: 8 queries (users, otp_codes, menu_items, orders, order_items)
- Redis: 6 operations (inventory checks, reservations)
- MongoDB: 3 operations (cart add, cart clear)

**State checkpoints saved**: 6 (one per turn)

---

## Architectural Principles

### 1. **Single Responsibility Principle**

Each node has one clear purpose:
- `auth_node`: Authentication only
- `perceive_node`: Intent classification only
- `validation_node`: Entity validation only
- `router_node`: Agent selection only

### 2. **Separation of Concerns**

**Orchestration Layer** (graph.py):
- Flow control
- Routing logic
- State management

**Agent Layer** (agents/):
- Business logic
- Database operations
- Domain expertise

**Formatting Layer** (response_agent):
- Response personality
- Upselling
- Tone consistency

### 3. **State Immutability**

State updates never mutate existing state:
```python
# ❌ WRONG - Mutating state
state["current_intent"] = "booking"

# ✅ CORRECT - Returning new state
return {"current_intent": "booking"}
```

LangGraph merges returned dict with existing state.

### 4. **Type Safety**

- TypedDict for state schema
- Pydantic models for ActionResult and entity schemas
- Literal types for routing functions
- mypy-compatible type hints

### 5. **Error Isolation**

Each node has try-except error handling:
```python
async def some_node(state: AgentState) -> Dict[str, Any]:
    try:
        result = await perform_operation()
        return {"agent_response": result}
    except Exception as e:
        logger.error("Operation failed", error=str(e))
        return {
            "error": str(e),
            "fallback_used": True,
            "agent_response": "I encountered an error..."
        }
```

Errors don't crash the entire graph.

### 6. **Database Transaction Safety**

- **Atomic Operations**: Use BEGIN/COMMIT for multi-table updates
- **Rollback on Failure**: Catch exceptions and ROLLBACK
- **Inventory Reservations**: Use Redis TTL for automatic cleanup
- **Idempotency**: Support retry-safe operations

Example from checkout_executor:
```python
async def execute_checkout():
    # Step 1: Reserve in Redis (with TTL)
    await redis.reserve_inventory(items, ttl=900)

    try:
        # Step 2: PostgreSQL transaction
        async with db.transaction():
            order = await db.create_order(...)
            await db.create_order_items(...)

        # Step 3: Confirm reservation (only if DB succeeded)
        await redis.confirm_reservation(items)

    except Exception as e:
        # Step 4: Rollback Redis reservation
        await redis.release_reservation(items)
        raise
```

### 7. **Observability**

Every node logs structured events:
```python
logger.info(
    "Node execution",
    session_id=session_id,
    node_name="perceive",
    intent=intent,
    confidence=confidence,
    duration_ms=duration
)
```

Logs are JSON-formatted (structlog) for easy parsing.

### 8. **Graceful Degradation**

- LLM failures → Fallback to keyword matching
- Database errors → Return cached data if available
- External API failures → Queue for retry

### 9. **Multi-Tenant Architecture**

State includes `restaurant_id` field for future multi-restaurant support:
```python
{
    "restaurant_id": "rest_123",
    "user_id": "user_789",
    ...
}
```

Database queries filter by `restaurant_id`:
```sql
SELECT * FROM menu_items
WHERE restaurant_id = 'rest_123'
AND is_available = true;
```

### 10. **Agent Autonomy**

Agents are **black boxes** to the orchestrator:
- Orchestrator provides intent + entities
- Agent decides how to fulfill
- Agent returns ActionResult
- Orchestrator never inspects agent internals

This enables independent agent development.

---

## Summary

The LangGraph orchestration system provides:

✅ **Stateful Conversations**: Checkpointing enables multi-turn flows
✅ **Modular Design**: 20+ nodes, each with single responsibility
✅ **Type Safety**: TypedDict + Pydantic for compile-time checks
✅ **Observability**: Structured logging at every step
✅ **Error Resilience**: Isolated error handling prevents cascading failures
✅ **Database Safety**: Transaction guarantees + automatic rollback
✅ **Scalability**: Sub-graphs enable domain specialization
✅ **Multi-Tier Auth**: Anonymous → Authenticated flow with seamless handoff
✅ **Response Consistency**: Virtual Waiter layer ensures brand voice

**Key Innovation**: Hierarchical agent architecture with sub-graphs (food_ordering) enables specialization while maintaining system cohesion.

---

**Document Version**: 1.0
**Last Updated**: 2024-01-15
**Author**: AI Assistant (Claude Code)
**Status**: ✅ Complete
