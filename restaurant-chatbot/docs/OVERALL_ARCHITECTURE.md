# Restaurant AI Assistant - Complete Architecture Documentation

**Version:** 1.0
**Last Updated:** 2025-11-13
**Status:** Active Development

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Layers](#architecture-layers)
4. [Orchestration Engine (LangGraph)](#orchestration-engine-langgraph)
5. [Agent Architecture](#agent-architecture)
6. [Data Flow & State Management](#data-flow--state-management)
7. [Service Layer](#service-layer)
8. [Database Architecture](#database-architecture)
9. [Authentication & Identity](#authentication--identity)
10. [Error Handling & Validation](#error-handling--validation)
11. [Technology Stack](#technology-stack)
12. [Design Decisions](#design-decisions)
13. [Current Issues & Migration Path](#current-issues--migration-path)

---

## Executive Summary

This is a **conversation-driven, stateful, multi-agent AI system** for restaurant operations (ordering, booking, payments, support). Built on **LangGraph** for orchestration, **OpenAI GPT-4o** for intelligence, and **FastAPI** for API layer.

### Key Characteristics:
- **Conversational Interface**: Natural language via WebSocket
- **Multi-Agent**: Specialized agents for different tasks
- **Stateful**: Conversation memory with checkpointing
- **Hierarchical**: Parent agents coordinate sub-agents
- **Layered**: Clean separation of concerns (API → Orchestration → Agents → Services → Database)

### Current State:
- ✅ Food ordering flow: Fully modular (hierarchical agent)
- ⚠️ Table booking flow: Legacy monolithic (needs migration)
- ⚠️ Complaints flow: Legacy monolithic (needs migration)
- ✅ Validation gates: Recently added
- ✅ Service layer: Enforced (direct DB access removed)

---

## System Overview

### High-Level Architecture (6 Layers)

```
┌──────────────────────────────────────────────────────────┐
│                    LAYER 1: API                          │
│                 /app/api/routes/chat.py                  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  WebSocket Manager                                 │  │
│  │  - Connection management                           │  │
│  │  - Session tracking                                │  │
│  │  - Message routing                                 │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              LAYER 2: ORCHESTRATION                      │
│              /app/orchestration/graph.py                 │
│  ┌────────────────────────────────────────────────────┐  │
│  │  LangGraph Orchestrator                            │  │
│  │  - State management (AgentState)                   │  │
│  │  - Workflow graph (nodes + edges)                  │  │
│  │  - Checkpointing (MemorySaver)                     │  │
│  │  - Conditional routing                             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│           LAYER 3: ORCHESTRATION NODES                   │
│           /app/orchestration/nodes/                      │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Core Processing Nodes:                            │  │
│  │  • auth_node          - Authentication check       │  │
│  │  • perceive_node      - Intent classification      │  │
│  │  • clarification_node - Handle unclear intents     │  │
│  │  • task_manager_node  - Task structure creation    │  │
│  │  • validation_node    - Entity validation          │  │
│  │  • router_node        - Agent selection            │  │
│  │  • greeting_agent     - Welcome messages           │  │
│  │  • fallback_node      - Error handling             │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                LAYER 4: AGENTS                           │
│                /app/agents/                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Specialized AI Agents:                            │  │
│  │                                                    │  │
│  │  Core Flow Agents:                                 │  │
│  │  • food_ordering_agent (hierarchical ✅)           │  │
│  │  • booking_agent (monolithic ⚠️)                  │  │
│  │  • response_agent (Virtual Waiter)                 │  │
│  │                                                    │  │
│  │  Supporting Agents:                                │  │
│  │  • authentication_agent                            │  │
│  │  • payment_agent                                   │  │
│  │  • user_agent                                      │  │
│  │  • support_agent                                   │  │
│  │  • general_queries_agent                           │  │
│  │                                                    │  │
│  │  Legacy (to be deprecated):                        │  │
│  │  • menu_agent                                      │  │
│  │  • order_agent                                     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              LAYER 5: SERVICE LAYER                      │
│              /app/services/                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Business Logic Services:                          │  │
│  │  • user_data_manager     - User operations         │  │
│  │  • inventory_cache_srv   - Inventory + Redis       │  │
│  │  • identity_service      - Auth & tokens           │  │
│  │  • menu_service          - Menu operations         │  │
│  │  • cart_service          - Cart operations         │  │
│  │  • order_service         - Order processing        │  │
│  │  • booking_service       - Table bookings          │  │
│  │  • payment_service       - Payment processing      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│              LAYER 6: DATABASE                           │
│              /app/database/                              │
│  ┌────────────────────────────────────────────────────┐  │
│  │  PostgreSQL Database:                              │  │
│  │  • SQLAlchemy ORM (async)                          │  │
│  │  • Connection pooling                              │  │
│  │  • Models: User, Order, MenuItem, Booking, etc.    │  │
│  │                                                    │  │
│  │  Redis Cache:                                      │  │
│  │  • Inventory reservations                          │  │
│  │  • Session data                                    │  │
│  │  • Rate limiting                                   │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

---

## Architecture Layers

### Layer 1: API Layer

**Location:** `/app/api/routes/chat.py`

#### Purpose
- WebSocket connection management
- Message routing to orchestrator
- Session tracking
- Connection lifecycle management

#### Key Components

##### 1. WebSocketManager
```python
class WebSocketManager:
    active_connections: Dict[str, WebSocket]
    connection_metadata: Dict[str, Dict[str, Any]]

    async def connect(websocket, session_id)
    async def disconnect(session_id)
    async def send_message(session_id, message)
```

**Responsibilities:**
- Maintain active WebSocket connections
- Track connection metadata (user_id, start_time, messages_count)
- Handle connection/disconnection events
- Broadcast messages to clients

##### 2. WebSocket Endpoint
```python
@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    # 1. Accept connection
    await manager.connect(websocket, session_id)

    # 2. Message loop
    while True:
        data = await websocket.receive_json()

        # 3. Route to orchestrator
        response, metadata = await langgraph_orchestrator.process_message(...)

        # 4. Send response
        await manager.send_message(session_id, response)
```

#### Connection Lifecycle

```
Client Connect
    ↓
1. WebSocket handshake
    ↓
2. manager.connect() - Store connection
    ↓
3. Generate/validate session_id
    ↓
4. Enter message loop
    ↓
5. For each message:
   - Receive JSON
   - Extract user_message
   - Call orchestrator.process_message()
   - Send response back
    ↓
6. On disconnect:
   - manager.disconnect()
   - Clean up inventory (via service layer)
   - Log analytics
```

#### Recent Fix: Direct DB Access Removal

**BEFORE (Bad):**
```python
async def disconnect(self, session_id: str):
    # ❌ Direct database queries
    from app.database.models import Order, OrderItem
    async with get_db_session() as db:
        orders = await db.execute(select(Order).where(...))
        # ... 60 lines of DB operations
```

**AFTER (Good):**
```python
async def disconnect(self, session_id: str):
    # ✅ Use service layer
    from app.services.user_data_manager import get_user_data_manager
    user_manager = get_user_data_manager()

    async with get_db_session() as db:
        await user_manager.on_user_logout(user_id, db)
```

---

### Layer 2: Orchestration Layer

**Location:** `/app/orchestration/graph.py`

#### Purpose
- Coordinate conversation flow
- Manage state across turns
- Route to appropriate nodes
- Maintain conversation memory

#### Core Class: LangGraphOrchestrator

```python
class LangGraphOrchestrator:
    graph: CompiledStateGraph  # Compiled workflow

    async def process_message(
        user_message: str,
        session_id: str,
        user_id: Optional[str],
        device_id: Optional[str],
        session_token: Optional[str]
    ) -> tuple[str, Dict[str, Any]]
```

#### Workflow Graph Structure

```
START
  ↓
auth_node ─────────────────┐
  ↓ [authenticated]        │ [waiting for auth]
  │                        ↓
  │                       END
  ↓
perceive_node
  ↓
[Decision Point]
  ↓                    ↓
clarify_node      task_manager_node
  ↓                    ↓
  │              validation_node
  │                    ↓
  │              [Decision Point]
  │                ↓         ↓
  │           router_node   │
  │                ↓        │
  │           [Agents]      │
  │                ↓        │
  └────────→ response_agent ←┘
                 ↓
                END
```

#### State Management

**AgentState (TypedDict):**
```python
class AgentState(TypedDict):
    # Session Info
    session_id: str
    user_id: Optional[str]
    device_id: Optional[str]
    session_token: Optional[str]
    restaurant_id: Optional[str]

    # Conversation
    messages: Sequence[BaseMessage]
    conversation_summary: Optional[str]
    user_memory: Dict[str, Any]

    # Intent & Routing
    current_intent: Optional[str]
    intent_confidence: float
    selected_agent: Optional[str]
    requires_clarification: bool
    clarification_reason: Optional[str]

    # Task Management
    task_entities: Dict[str, Any]
    active_task_type: Optional[str]

    # Authentication
    is_authenticated: bool
    auth_tier: int  # 1=anonymous, 2=device, 3=phone, 4=full
    authentication_step: Optional[str]
    phone_number: Optional[str]
    pending_otp_id: Optional[str]
    otp_verified: bool

    # Food Ordering (specific state)
    cart_items: List[Dict[str, Any]]
    cart_validated: bool
    draft_order_id: Optional[str]
    order_type: Optional[str]

    # Validation
    validation_errors: List[str]

    # Response
    agent_response: str
    agent_metadata: Dict[str, Any]
```

#### Checkpointing

**MemorySaver** stores conversation state in memory:

```python
config = {"configurable": {"thread_id": session_id}}

# First message - create initial state
if not has_checkpoint:
    initial_state = create_initial_state(session_id, user_message, ...)

# Subsequent messages - load from checkpoint
else:
    initial_state = {"messages": [HumanMessage(content=user_message)]}

# Execute graph (state is automatically saved)
final_state = await graph.ainvoke(initial_state, config)
```

**Why MemorySaver?**
- In-memory (fast)
- Async compatible
- Simple to use
- Limitation: Lost on server restart (acceptable for current use case)

**Future:** Migrate to PostgreSQL checkpointing when LangGraph fixes sync/async API issues.

---

### Layer 3: Orchestration Nodes

**Location:** `/app/orchestration/nodes/`

These are the **processing units** in the LangGraph workflow. Each node performs a specific task and updates the state.

#### 1. auth_node

**File:** `nodes/auth.py`

**Purpose:** Check authentication status and determine if user can proceed.

**Flow:**
```python
async def auth_node(state: AgentState) -> Dict[str, Any]:
    # 1. Check if already authenticated
    if state.get("is_authenticated"):
        return {}  # Continue to perceive

    # 2. Check authentication step (in progress?)
    auth_step = state.get("authentication_step")
    if auth_step:
        return {}  # Continue auth flow

    # 3. Check if intent requires auth
    intent = state.get("current_intent")
    if intent in ["greeting", "menu_browse", ...]:
        return {}  # Allow anonymous access

    # 4. Require authentication
    return {
        "requires_authentication": True,
        "selected_agent": "authentication_agent"
    }
```

**Routing:**
```python
def route_from_auth(state: AgentState) -> Literal["perceive", END]:
    if state.get("requires_authentication"):
        return END  # Wait for auth completion
    return "perceive"  # Continue to intent detection
```

**Multi-Tier Authentication:**
- **Tier 1:** Anonymous (browse menu, view items)
- **Tier 2:** Device ID (cart persistence)
- **Tier 3:** Phone + OTP (place orders, bookings)
- **Tier 4:** Full profile (payment history, preferences)

---

#### 2. perceive_node

**File:** `nodes/perceive.py`

**Purpose:** Understand user intent and extract entities using GPT-4o.

**Flow:**
```python
async def perceive_node(state: AgentState) -> Dict[str, Any]:
    # 1. Get user message
    messages = state.get("messages", [])
    user_message = messages[-1].content

    # 2. Build context
    context = {
        "conversation_history": format_messages(messages),
        "user_memory": state.get("user_memory", {}),
        "cart_state": state.get("cart_items", []),
        "active_task": state.get("active_task_type")
    }

    # 3. Call LLM for intent classification
    intent_result = await classify_intent(user_message, context)

    # 4. Extract entities
    entities = extract_entities(user_message, intent_result)

    # 5. Determine if clarification needed
    requires_clarification = (
        intent_result.confidence < 0.7 or
        missing_required_entities(intent_result, entities)
    )

    return {
        "current_intent": intent_result.intent,
        "intent_confidence": intent_result.confidence,
        "task_entities": entities,
        "requires_clarification": requires_clarification
    }
```

**Intent Categories:**
- `greeting` - "Hi", "Hello"
- `order_request` - "I want to order", "Add butter chicken"
- `menu_browse` - "Show menu", "What's available?"
- `booking_request` - "Book a table"
- `payment_intent` - "Pay", "Complete order"
- `order_status` - "Where's my order?"
- `complaint` - "Food was cold"
- `general_query` - "What are your hours?"

**Entity Extraction Examples:**
```
User: "Book a table for 4 at 7pm tomorrow"
Entities: {
    "party_size": 4,
    "booking_time": "7pm",
    "booking_date": "2025-11-14"
}

User: "Add 2 butter chickens"
Entities: {
    "item_name": "butter chicken",
    "quantity": 2
}
```

---

#### 3. clarification_node

**File:** `nodes/clarify.py`

**Purpose:** Ask user for missing or unclear information.

**Triggers:**
- Intent confidence < 0.7
- Missing required entities
- Ambiguous request

**Example:**
```
User: "I want to book"
Missing: party_size, booking_time, booking_date

Clarification: "I'd be happy to help you book a table!
How many people, and what time works for you?"
```

---

#### 4. task_manager_node

**File:** `nodes/task_manager.py`

**Purpose:** Create task structure and select appropriate agent.

**Flow:**
```python
async def task_manager_node(state: AgentState) -> Dict[str, Any]:
    intent = state.get("current_intent")
    entities = state.get("task_entities", {})

    # Map intent to agent
    agent_mapping = {
        "order_request": "food_ordering_agent",
        "booking_request": "booking_agent",
        "payment_intent": "payment_agent",
        ...
    }

    selected_agent = agent_mapping.get(intent, "fallback")

    return {
        "selected_agent": selected_agent,
        "active_task_type": intent
    }
```

---

#### 5. validation_node (NEW!)

**File:** `nodes/validation.py`

**Purpose:** Validate entities before routing to agents.

**Validation Rules:**

| Entity | Rule | Example Error |
|--------|------|---------------|
| `phone_number` | 10 digits, starts with 6-9 | "Phone number must be 10 digits (e.g., 9876543210)" |
| `party_size` | 1-20 | "Party size cannot exceed 20 people" |
| `booking_time` | 10 AM - 11 PM, not past | "Restaurant opens at 10:00 AM" |
| `quantity` | 1-99 | "Quantity must be at least 1" |
| `item_id` | Format: mit000001 | "Invalid item ID format" |
| `order_type` | dine_in or takeout | "Order type must be either 'dine_in' or 'takeout'" |
| `rating` | 1-5 | "Rating must be between 1 and 5" |

**Flow:**
```python
async def validation_node(state: AgentState) -> Dict[str, Any]:
    entities = state.get("task_entities", {})

    # Run all validation rules
    all_valid, errors = validate_entities(entities)

    if all_valid:
        return {}  # Continue to router

    # Validation failed
    error_message = format_validation_errors(errors)

    return {
        "requires_clarification": True,
        "validation_errors": errors,
        "agent_response": error_message
    }
```

**Routing:**
```python
def route_from_validation(state: AgentState):
    if state.get("requires_clarification"):
        return "response_agent"  # Show error
    return "router"  # Continue to agent
```

**Impact:**
- **BEFORE:** Bad data reached agents → generic errors
- **AFTER:** Bad data caught early → clear error messages

---

#### 6. router_node

**File:** `nodes/router.py`

**Purpose:** Route to the selected agent.

**Simple routing logic:**
```python
async def router_node(state: AgentState) -> Dict[str, Any]:
    # Just returns empty dict - routing done by conditional edge
    return {}

def route_to_agent(state: AgentState) -> str:
    return state.get("selected_agent", "fallback")
```

---

#### 7. response_agent (Virtual Waiter)

**File:** `/app/agents/response/node.py`

**Purpose:** Format all agent responses with consistent personality and tone.

**Personality:**
- Casual & friendly (neighborhood restaurant vibe)
- Enthusiastic about food
- Brief and natural
- NO EMOJIS

**Action Templates:**
- `booking_created` - "Awesome! Got you all set for..."
- `item_added` - "Great choice! That's ₹149. Want to add..."
- `order_placed` - "Perfect! Your order should be ready in..."
- `error_occurred` - "Oh no! But I've got something even better..."
- **15 error templates** (database_error, inventory_error, etc.)

**Flow:**
```python
async def response_agent_node(state: AgentState) -> Dict[str, Any]:
    # 1. Get agent result
    agent_metadata = state.get("agent_metadata", {})
    action = agent_metadata.get("action")
    data = agent_metadata.get("data")

    # 2. Select template
    template = get_prompt_for_action(action)

    # 3. Format with personality
    response = await llm.ainvoke([
        SystemMessage(content=VIRTUAL_WAITER_SYSTEM_PROMPT),
        HumanMessage(content=template.format(details=data))
    ])

    return {"agent_response": response.content}
```

---

## Agent Architecture

### Agent Types

#### 1. Hierarchical Agents (Modern)

**Example:** `food_ordering_agent`

**Structure:**
```
food_ordering_agent (Parent)
    ↓
sub_intent_classifier
    ↓
    ├─→ menu_discovery (Sub-Agent 1)
    │     ├─ browse_categories_tool
    │     ├─ show_menu_tool
    │     └─ search_items_tool
    │
    ├─→ cart_management (Sub-Agent 2)
    │     ├─ add_to_cart_tool
    │     ├─ view_cart_tool
    │     ├─ update_quantity_tool
    │     └─ remove_item_tool
    │
    ├─→ order_finalization (Sub-Agent 3)
    │     ├─ validate_cart_tool
    │     ├─ create_draft_order_tool
    │     └─ place_order_tool
    │
    └─→ post_order (Sub-Agent 4)
          ├─ order_status_tool
          └─ modify_order_tool
```

**Benefits:**
- Modular (easy to maintain)
- Focused (each sub-agent has clear responsibility)
- Testable (test each sub-agent independently)
- Scalable (add new sub-agents easily)

**File Structure:**
```
/app/agents/food_ordering/
    node.py                    # Parent agent entry point
    sub_intent_classifier.py   # Routes to sub-agents

    agents/
        menu_discovery/
            react_agent.py     # Sub-agent logic
            tools.py           # Tools for this sub-agent
            prompts.py         # Prompts for this sub-agent

        cart_management/
            react_agent.py
            tools.py
            prompts.py

        order_finalization/
            react_agent.py
            tools.py
            prompts.py

        post_order/
            react_agent.py
            tools.py
            prompts.py
```

---

#### 2. Monolithic Agents (Legacy)

**Example:** `booking_agent`

**Structure:**
```
booking_agent
    ├─ 1,929 lines in single file
    ├─ All tools in one place
    ├─ Complex conditional logic
    └─ Hard to maintain
```

**Problems:**
- Too large (hard to understand)
- Mixed responsibilities
- Difficult to test
- Brittle (changes break multiple things)

**Migration Path:**
```
booking_agent (monolithic)
    ↓
booking_agent (hierarchical)
    ├─ table_availability
    ├─ booking_creation
    ├─ booking_modification
    └─ booking_cancellation
```

---

### Agent Components

Every agent has:

#### 1. Node Function (Entry Point)
```python
async def food_ordering_agent_node(state: AgentState) -> Dict[str, Any]:
    # Entry point called by orchestrator
    result = await food_ordering_agent.ainvoke(state)
    return {"agent_response": result.response}
```

#### 2. System Prompt
```python
FOOD_ORDERING_AGENT_PROMPT = """
You are a food ordering assistant.

Your responsibilities:
- Help users browse menu
- Manage cart (add/remove items)
- Validate orders
- Process orders

When user wants to add items, use the cart_management sub-agent.
When user wants to browse, use the menu_discovery sub-agent.
...
"""
```

#### 3. Tools
```python
@tool
async def add_to_cart_tool(
    item_id: str,
    quantity: int,
    user_id: str,
    session_id: str
) -> ToolResult:
    """Add item to user's cart"""
    cart_service = get_cart_service()
    result = await cart_service.add_item(...)

    return ToolResult(
        status="success",
        success=True,
        data={"cart_items": result}
    )
```

#### 4. Response Format (ActionResult)
```python
class ActionResult(TypedDict):
    action: str           # "item_added", "booking_created", etc.
    success: bool         # True if successful
    data: Dict[str, Any]  # Result data
    error: Optional[str]  # Error message if failed
```

---

### Sub-Intent Classification (Hierarchical Agents)

**File:** `/app/agents/food_ordering/sub_intent_classifier.py`

**Purpose:** Route user request to correct sub-agent within parent agent.

**Context-Aware Classification:**
```python
def classify_sub_intent(user_message: str, state: AgentState) -> str:
    # Build rich context
    cart_items = state.get("cart_items", [])
    draft_order_id = state.get("draft_order_id")

    context_parts = []

    if cart_items:
        context_parts.append(f"User has {len(cart_items)} items in cart")

    if draft_order_id:
        context_parts.append("Draft order exists")
        context_parts.append("IMPORTANT: 'Change order' likely means cart operations")

    # Call LLM with context
    result = llm.invoke([
        SystemMessage(content=SUB_INTENT_CLASSIFIER_PROMPT),
        HumanMessage(content=f"Context: {context}\nUser: {user_message}")
    ])

    return result.sub_intent  # "menu_discovery", "cart_management", etc.
```

**Sub-Intents:**
- `menu_discovery` - Browse menu, search items
- `cart_management` - Add/remove/view cart
- `order_finalization` - Validate, place order
- `post_order` - Order status, modifications

---

## Data Flow & State Management

### Complete User Journey: "Add butter chicken to cart"

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: User Input                                          │
│ User types: "Add butter chicken"                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: WebSocket Receives Message                          │
│ File: /app/api/routes/chat.py                              │
│                                                             │
│ data = await websocket.receive_json()                       │
│ user_message = data["message"]  # "Add butter chicken"      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: Orchestrator Entry                                  │
│ File: /app/orchestration/graph.py                          │
│                                                             │
│ response, metadata = await langgraph_orchestrator           │
│     .process_message(                                       │
│         user_message="Add butter chicken",                  │
│         session_id="abc123",                                │
│         user_id="usr456",                                   │
│         ...                                                 │
│     )                                                       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: Load Checkpoint                                     │
│                                                             │
│ config = {"configurable": {"thread_id": "abc123"}}          │
│ checkpoint = graph.get_state(config)                        │
│                                                             │
│ Previous state loaded:                                      │
│ - user_id: "usr456"                                         │
│ - is_authenticated: True                                    │
│ - cart_items: [{"item_id": "mit000123", "quantity": 1}]    │
│ - messages: [...previous conversation...]                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: Create Input State                                 │
│                                                             │
│ input_state = {                                             │
│     "messages": [HumanMessage("Add butter chicken")]        │
│ }                                                           │
│                                                             │
│ (Checkpoint has all other state - will merge automatically) │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 6: Graph Execution Starts                             │
│                                                             │
│ final_state = await graph.ainvoke(input_state, config)     │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ NODE 1: auth_node                                           │
│ File: /app/orchestration/nodes/auth.py                     │
│                                                             │
│ state.is_authenticated = True  ✓                            │
│ → Continue to perceive                                      │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ NODE 2: perceive_node                                       │
│ File: /app/orchestration/nodes/perceive.py                 │
│                                                             │
│ 1. Extract message: "Add butter chicken"                    │
│ 2. Build context:                                           │
│    - Conversation history: [...]                            │
│    - Cart: 1 item                                           │
│    - User memory: {dietary: [], preferences: []}           │
│                                                             │
│ 3. Call GPT-4o for intent:                                 │
│    Intent: "order_request"                                  │
│    Confidence: 0.95                                         │
│    Entities: {item_name: "butter chicken"}                  │
│                                                             │
│ 4. Update state:                                            │
│    current_intent = "order_request"                         │
│    task_entities = {"item_name": "butter chicken"}          │
│    requires_clarification = False  (high confidence)        │
│                                                             │
│ → Continue to task_manager                                  │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ NODE 3: task_manager_node                                   │
│ File: /app/orchestration/nodes/task_manager.py             │
│                                                             │
│ Intent: "order_request"                                     │
│ → Map to agent: "food_ordering_agent"                       │
│                                                             │
│ Update state:                                               │
│    selected_agent = "food_ordering_agent"                   │
│    active_task_type = "order_request"                       │
│                                                             │
│ → Continue to validation                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ NODE 4: validation_node                                     │
│ File: /app/orchestration/nodes/validation.py               │
│                                                             │
│ Entities to validate: {"item_name": "butter chicken"}       │
│                                                             │
│ Check validation rules:                                     │
│ - item_name: No validation rule (optional)                  │
│                                                             │
│ Result: ✓ All valid                                         │
│                                                             │
│ → Continue to router                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ NODE 5: router_node                                         │
│ File: /app/orchestration/nodes/router.py                   │
│                                                             │
│ selected_agent = "food_ordering_agent"                      │
│                                                             │
│ → Route to food_ordering_agent                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ AGENT: food_ordering_agent                                  │
│ File: /app/agents/food_ordering/node.py                    │
│                                                             │
│ PHASE 1: Sub-Intent Classification                          │
│ File: sub_intent_classifier.py                             │
│                                                             │
│ User message: "Add butter chicken"                          │
│ Context: Has items in cart, no draft order                  │
│                                                             │
│ GPT-4o-mini classification:                                 │
│ → sub_intent = "cart_management"                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SUB-AGENT: cart_management                                  │
│ File: /app/agents/food_ordering/agents/cart_management/    │
│                                                             │
│ PHASE 2: Agent Reasoning (ReAct Loop)                       │
│                                                             │
│ Agent thoughts:                                             │
│ "User wants to add butter chicken. I need to:               │
│  1. Search for this item in menu                            │
│  2. Add it to their cart"                                   │
│                                                             │
│ Action 1: search_menu_items                                 │
│   Input: {query: "butter chicken", user_id: "usr456"}       │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ TOOL: search_menu_items_tool                                │
│ File: menu_discovery/tools.py                              │
│                                                             │
│ 1. Call service layer:                                      │
│    menu_service = get_menu_service()                        │
│    results = await menu_service.search_items(               │
│        query="butter chicken",                              │
│        restaurant_id="rest001"                              │
│    )                                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SERVICE: menu_service                                       │
│ File: /app/services/menu_service.py                        │
│                                                             │
│ 1. Query database:                                          │
│    SELECT * FROM menu_items                                 │
│    WHERE name ILIKE '%butter chicken%'                      │
│    AND restaurant_id = 'rest001'                            │
│    AND is_available = true                                  │
│                                                             │
│ 2. Results:                                                 │
│    [                                                        │
│        {                                                    │
│            "item_id": "mit000456",                          │
│            "name": "Butter Chicken",                        │
│            "price": 320,                                    │
│            "category": "main_course",                       │
│            "description": "Creamy tomato curry..."          │
│        }                                                    │
│    ]                                                        │
│                                                             │
│ 3. Return to tool                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ TOOL RESULT: search_menu_items_tool                         │
│                                                             │
│ ToolResult(                                                 │
│     status="success",                                       │
│     success=True,                                           │
│     data={                                                  │
│         "items": [                                          │
│             {                                               │
│                 "item_id": "mit000456",                     │
│                 "name": "Butter Chicken",                   │
│                 "price": 320                                │
│             }                                               │
│         ]                                                   │
│     }                                                       │
│ )                                                           │
│                                                             │
│ → Return to agent                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SUB-AGENT: cart_management (continued)                      │
│                                                             │
│ Agent receives tool result:                                 │
│ "Found: Butter Chicken (mit000456) - ₹320"                  │
│                                                             │
│ Agent thoughts:                                             │
│ "Great! Found the item. Now add it to cart."                │
│                                                             │
│ Action 2: add_to_cart                                       │
│   Input: {                                                  │
│       item_id: "mit000456",                                 │
│       quantity: 1,                                          │
│       user_id: "usr456",                                    │
│       session_id: "abc123"                                  │
│   }                                                         │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ TOOL: add_to_cart_tool                                      │
│ File: cart_management/tools.py                             │
│                                                             │
│ 1. Call service layer:                                      │
│    cart_service = get_cart_service()                        │
│    result = await cart_service.add_item(                    │
│        user_id="usr456",                                    │
│        item_id="mit000456",                                 │
│        quantity=1                                           │
│    )                                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SERVICE: cart_service                                       │
│ File: /app/services/cart_service.py                        │
│                                                             │
│ 1. Check inventory:                                         │
│    inventory_service.check_availability("mit000456", 1)     │
│    → Available: Yes                                         │
│                                                             │
│ 2. Reserve inventory:                                       │
│    inventory_service.reserve_inventory(                     │
│        "mit000456", 1, "usr456"                             │
│    )                                                        │
│    → Redis: SET inv:mit000456:usr456 = 1                    │
│                                                             │
│ 3. Add to cart (in-memory for now):                         │
│    cart = get_user_cart("usr456")                           │
│    cart.add_item({                                          │
│        "item_id": "mit000456",                              │
│        "name": "Butter Chicken",                            │
│        "quantity": 1,                                       │
│        "price": 320                                         │
│    })                                                       │
│                                                             │
│ 4. Return updated cart:                                     │
│    [                                                        │
│        {"item_id": "mit000123", "quantity": 1},  # Old item│
│        {"item_id": "mit000456", "quantity": 1}   # New item│
│    ]                                                        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ TOOL RESULT: add_to_cart_tool                               │
│                                                             │
│ ToolResult(                                                 │
│     status="success",                                       │
│     success=True,                                           │
│     data={                                                  │
│         "cart_items": [                                     │
│             {"item_id": "mit000123", "quantity": 1},        │
│             {"item_id": "mit000456", "quantity": 1}         │
│         ],                                                  │
│         "cart_total": 470                                   │
│     }                                                       │
│ )                                                           │
│                                                             │
│ → Return to agent                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ SUB-AGENT: cart_management (final)                          │
│                                                             │
│ Agent receives tool result:                                 │
│ "Successfully added! Cart now has 2 items, total ₹470"      │
│                                                             │
│ Agent thoughts:                                             │
│ "Task complete. User's request fulfilled."                  │
│                                                             │
│ Agent returns ActionResult:                                 │
│ {                                                           │
│     "action": "item_added",                                 │
│     "success": True,                                        │
│     "data": {                                               │
│         "item_name": "Butter Chicken",                      │
│         "item_price": 320,                                  │
│         "quantity": 1,                                      │
│         "cart_total": 470                                   │
│     }                                                       │
│ }                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ AGENT: food_ordering_agent (exit)                           │
│                                                             │
│ Update orchestration state:                                 │
│ {                                                           │
│     "cart_items": [                                         │
│         {"item_id": "mit000123", "quantity": 1},            │
│         {"item_id": "mit000456", "quantity": 1}             │
│     ],                                                      │
│     "agent_metadata": {                                     │
│         "action": "item_added",                             │
│         "data": {...}                                       │
│     }                                                       │
│ }                                                           │
│                                                             │
│ → Continue to response_agent                                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ NODE: response_agent (Virtual Waiter)                       │
│ File: /app/agents/response/node.py                         │
│                                                             │
│ PHASE 1: Select Template                                    │
│ action = "item_added"                                       │
│ template = ACTION_PROMPTS["item_added"]                     │
│                                                             │
│ PHASE 2: Format Response                                    │
│ Call GPT-4o with:                                           │
│ - System: VIRTUAL_WAITER_SYSTEM_PROMPT                      │
│ - User: template.format(                                    │
│     details="Butter Chicken, ₹320, cart total ₹470"         │
│   )                                                         │
│                                                             │
│ GPT-4o generates:                                           │
│ "Great choice! Added Butter Chicken (₹320) to your cart.    │
│  Your total is now ₹470. Want to add anything else?"        │
│                                                             │
│ Update state:                                               │
│ {                                                           │
│     "agent_response": "Great choice! Added Butter..."       │
│ }                                                           │
│                                                             │
│ → END (graph execution complete)                            │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 7: Save Checkpoint                                     │
│                                                             │
│ MemorySaver automatically saves final state:                │
│ - cart_items: [2 items]                                     │
│ - messages: [...all messages including response...]        │
│ - agent_metadata: {...}                                     │
│                                                             │
│ Available for next turn!                                    │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 8: Extract Response                                    │
│ File: /app/orchestration/graph.py                          │
│                                                             │
│ response_text = final_state["agent_response"]               │
│                                                             │
│ metadata = {                                                │
│     "type": "success",                                      │
│     "intent": "order_request",                              │
│     "agent_used": "food_ordering_agent",                    │
│     "session_id": "abc123"                                  │
│ }                                                           │
│                                                             │
│ return response_text, metadata                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 9: Send to User                                        │
│ File: /app/api/routes/chat.py                              │
│                                                             │
│ await manager.send_message(                                 │
│     session_id="abc123",                                    │
│     message={                                               │
│         "type": "ai_message",                               │
│         "content": "Great choice! Added Butter Chicken..."  │
│     }                                                       │
│ )                                                           │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ STEP 10: User Receives Response                             │
│                                                             │
│ User sees in chat:                                          │
│ "Great choice! Added Butter Chicken (₹320) to your cart.    │
│  Your total is now ₹470. Want to add anything else?"        │
│                                                             │
│ ✓ Journey Complete!                                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Service Layer

**Location:** `/app/services/`

### Purpose
- Encapsulate business logic
- Abstract database operations
- Provide reusable components
- Manage external integrations

### Key Services

#### 1. user_data_manager
```python
class UserDataManager:
    async def on_user_logout(user_id: str, db_session):
        """Clean up user data on logout/disconnect"""
        # 1. Find pending orders
        # 2. Release inventory reservations
        # 3. Clear cache
        # 4. Clean up bookings
```

#### 2. inventory_cache_service
```python
class InventoryService:
    async def check_availability(item_id: str, quantity: int) -> bool
    async def reserve_inventory(item_id: str, quantity: int, user_id: str)
    async def release_inventory(item_id: str, quantity: int, user_id: str)
    async def commit_reservation(user_id: str)  # On order placement
```

**Redis Integration:**
```
Key: inv:reservation:{item_id}:{user_id}
Value: quantity
TTL: 15 minutes (auto-expires)
```

#### 3. cart_service
```python
class CartService:
    async def add_item(user_id, item_id, quantity)
    async def remove_item(user_id, item_id)
    async def update_quantity(user_id, item_id, quantity)
    async def get_cart(user_id)
    async def clear_cart(user_id)
    async def validate_cart(user_id)
```

#### 4. order_service
```python
class OrderService:
    async def create_draft_order(user_id, cart_items)
    async def place_order(draft_order_id)
    async def get_order_status(order_id)
    async def cancel_order(order_id)
```

---

## Database Architecture

**Location:** `/app/database/`

### Technology
- **PostgreSQL** - Main database
- **SQLAlchemy** - ORM (async)
- **Alembic** - Migrations

### Key Models

#### User
```python
class User(Base):
    __tablename__ = "users"

    id: str (PK)
    phone_number: str (unique)
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime
```

#### MenuItem
```python
class MenuItem(Base):
    __tablename__ = "menu_items"

    id: str (PK)
    restaurant_id: str (FK)
    name: str
    description: str
    price: Decimal
    category: str
    is_available: bool
    dietary_tags: JSON
```

#### Order
```python
class Order(Base):
    __tablename__ = "orders"

    id: str (PK)
    user_id: str (FK)
    restaurant_id: str (FK)
    order_type: str  # dine_in, takeout
    status: str  # pending, confirmed, preparing, ready, delivered, cancelled
    total_amount: Decimal
    created_at: datetime
```

#### OrderItem
```python
class OrderItem(Base):
    __tablename__ = "order_items"

    id: str (PK)
    order_id: str (FK)
    item_id: str (FK)
    quantity: int
    unit_price: Decimal
    subtotal: Decimal
```

---

## Authentication & Identity

**Location:** `/app/services/identity_service.py`

### Multi-Tier Identity

| Tier | Method | Capabilities | Use Case |
|------|--------|--------------|----------|
| 1 | Anonymous | Browse menu, view items | First-time visitor |
| 2 | Device ID | Persistent cart | Returning visitor |
| 3 | Phone + OTP | Place orders, bookings | Checkout |
| 4 | Full Profile | Payment history, preferences | Returning customer |

### Session Token
```
Format: JWT
Expiry: 30 days
Sliding Window: Renewed on each request
Storage: HTTP-only cookie
```

### OTP Flow
```
1. User provides phone number
2. System generates 6-digit OTP
3. Send via SMS (Twilio/similar)
4. User enters OTP
5. Verify OTP
6. Issue session token
```

---

## Error Handling & Validation

### Validation Gate (Layer 3)

**Location:** `/app/orchestration/nodes/validation.py`

**Prevents:**
- Invalid phone numbers reaching booking agent
- Negative quantities reaching cart
- Past dates reaching booking system
- Malformed item IDs reaching database

### Error Templates (Response Agent)

**Location:** `/app/agents/response/prompts.py`

**15 Error Types:**
1. database_error
2. inventory_error
3. service_unavailable
4. invalid_data_error
5. network_timeout
6. order_processing_error
7. payment_error
8. authentication_failed
9. item_not_found
10. cart_error
11. booking_error
12. rate_limit_error
13. agent_error
14. missing_required_field
15. generic_error

**Example:**
```
Error Type: invalid_data_error
Template: "Just need to double-check that phone number -
           it should be 10 digits like 9876543210. Can you try again?"
```

---

## Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| **API Framework** | FastAPI | Latest | WebSocket API |
| **Orchestration** | LangGraph | 0.2.x | Workflow management |
| **LLM** | OpenAI GPT-4o | Latest | Intent, reasoning |
| **LLM (sub-intents)** | GPT-4o-mini | Latest | Cost optimization |
| **Database** | PostgreSQL | 14+ | Primary data store |
| **ORM** | SQLAlchemy | 2.0+ (async) | Database abstraction |
| **Cache** | Redis | 7.x | Sessions, inventory |
| **Auth** | JWT | Latest | Session tokens |
| **Logging** | structlog | Latest | Structured logging |
| **Python** | 3.11+ | Latest | Runtime |

---

## Design Decisions

### 1. Why LangGraph?

**Problem:** Need to coordinate multiple agents with stateful conversations.

**Solution:** LangGraph provides:
- State management (AgentState)
- Conditional routing
- Conversation checkpointing
- Agent coordination

**Alternative Considered:** Custom orchestration
**Rejected Because:** Reinventing the wheel, harder to maintain

---

### 2. Why Hierarchical Agents?

**Problem:** Monolithic agents become unmaintainable (booking_agent = 1,929 lines).

**Solution:** Parent agent + specialized sub-agents

**Benefits:**
- Modular (easy to update one sub-agent)
- Testable (test each sub-agent independently)
- Scalable (add new sub-agents easily)
- Clear responsibilities

**Example:**
```
food_ordering_agent
    ├─ menu_discovery (focused on browsing)
    ├─ cart_management (focused on cart ops)
    ├─ order_finalization (focused on checkout)
    └─ post_order (focused on status/mods)
```

---

### 3. Why Service Layer?

**Problem:** API routes were directly querying database.

**Solution:** Add service layer between agents and database.

**Benefits:**
- Separation of concerns
- Reusable business logic
- Easier testing (mock services)
- Consistent error handling
- Transaction management

**Architecture:**
```
BEFORE: API → Database ❌
AFTER:  API → Service → Database ✅
```

---

### 4. Why Validation Gate?

**Problem:** Bad data reaching agents, causing downstream errors.

**Solution:** Add validation node between task_manager and router.

**Benefits:**
- Early error detection
- Clear error messages to user
- Prevents database corruption
- Easier debugging

**Flow:**
```
BEFORE: task_manager → router → agents ❌
AFTER:  task_manager → validation → [router or error] ✅
```

---

### 5. Why MemorySaver Instead of PostgreSQL Checkpointing?

**Problem:** LangGraph PostgresSaver has sync/async API incompatibility.

**Decision:** Use MemorySaver temporarily.

**Trade-offs:**
- ✅ Fast, simple, works reliably
- ❌ State lost on server restart
- ✅ Acceptable for current use case (session-based)

**Future:** Migrate to PostgreSQL when LangGraph fixes the issue.

---

### 6. Why Virtual Waiter (response_agent)?

**Problem:** Each agent had different tone/style.

**Solution:** All responses go through response_agent for consistent personality.

**Benefits:**
- Unified voice
- Easier to change tone (one place)
- Better UX
- Error messages feel natural

**Flow:**
```
All agents → response_agent → User
```

---

## Current Issues & Migration Path

### Issue 1: Monolithic Legacy Agents

**Affected Agents:**
- `booking_agent` (1,929 lines)
- `customer_satisfaction_agent` (complaints flow)

**Migration Plan:**

```
booking_agent (monolithic)
    ↓ Refactor into:
booking_agent (hierarchical)
    ├─ availability_checker
    ├─ booking_creator
    ├─ booking_modifier
    └─ booking_canceller
```

**Timeline:** After food ordering flow is fully tested

---

### Issue 2: Legacy menu_agent and order_agent

**Status:** Deprecated but still in codebase

**Action:** Remove after food_ordering_agent is stable

**Router Update:**
```python
# OLD mapping
"menu_browse": "menu_agent",  # Remove
"order_request": "order_agent",  # Remove

# NEW mapping
"menu_browse": "food_ordering_agent",
"order_request": "food_ordering_agent",
```

---

### Issue 3: Checkpointing Persistence

**Current:** MemorySaver (in-memory)
**Issue:** State lost on server restart
**Impact:** Users lose conversation context on deployment

**Future Solution:**
```python
# When LangGraph fixes async API:
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver(db_connection_pool)
graph = workflow.compile(checkpointer=checkpointer)
```

---

### Issue 4: No Production Deployment Features

**Missing:**
- Session persistence (PostgreSQL checkpointing)
- Advanced logging (structured + correlation IDs)
- Monitoring (Prometheus/Grafana)
- Rate limiting (per user)
- Load balancing
- Auto-scaling

**Priority:** After core flows are tested and stable

---

## Next Steps (After Testing)

### Phase 1: Complete Food Ordering Flow Testing
1. Test all sub-agents
2. Test error scenarios
3. Test validation gates
4. Verify service layer enforcement

### Phase 2: Migrate Table Booking
1. Design hierarchical booking_agent
2. Create sub-agents
3. Migrate tools
4. Test thoroughly

### Phase 3: Migrate Complaints Flow
1. Design hierarchical customer_satisfaction_agent
2. Create sub-agents
3. Migrate tools
4. Test thoroughly

### Phase 4: Production Readiness
1. PostgreSQL checkpointing
2. Advanced logging
3. Monitoring setup
4. Rate limiting
5. Load testing
6. Security audit

---

## Glossary

**AgentState:** TypedDict containing all conversation state (messages, entities, metadata)

**Checkpointing:** Saving conversation state between turns for continuity

**Hierarchical Agent:** Parent agent that coordinates specialized sub-agents

**LangGraph:** Framework for building stateful, multi-agent workflows

**MemorySaver:** In-memory checkpointing backend (fast, not persistent)

**Monolithic Agent:** Single large agent handling multiple responsibilities (legacy)

**Orchestration:** Coordination of multiple agents and workflow logic

**Service Layer:** Business logic layer between agents and database

**Sub-Intent:** Specific intent within a parent agent (e.g., "cart_management" within "food_ordering")

**Tool:** Function that an agent can call to perform actions

**ToolResult:** Standardized response format from tools

**Validation Gate:** Node that validates entities before routing to agents

**Virtual Waiter:** response_agent that formats all responses with consistent personality

---

## Document Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-13 | Initial comprehensive architecture documentation |

---

**END OF DOCUMENT**
