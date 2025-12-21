# Restaurant AI Architecture v30
## Multi-Agent Crew with Delegation

### High-Level Architecture

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        UI[Chat UI]
    end

    subgraph API["API Layer"]
        FastAPI[FastAPI Server]
        ChatRoute["/api/chat endpoint"]
    end

    subgraph Orchestration["Orchestration Layer - restaurant_crew.py"]
        RC[Restaurant Crew]

        subgraph Agents["Multi-Agent System"]
            FOA[Food Ordering Agent<br/>Kavya]
            BA[Booking Agent<br/>Booking Specialist]
        end

        DEL{{"Delegate work<br/>to coworker"}}
    end

    subgraph Tools["Tool Layer"]
        subgraph FoodTools["Food Ordering Tools (10)"]
            T1[search_menu]
            T2[add_to_cart]
            T3[view_cart]
            T4[remove_from_cart]
            T5[checkout]
            T6[cancel_order]
            T7[clear_cart]
            T8[update_quantity]
            T9[set_special_instructions]
            T10[get_item_details]
        end

        subgraph BookingTools["Booking Tools (5)"]
            B1[check_table_availability]
            B2[make_reservation]
            B3[get_my_bookings]
            B4[modify_reservation]
            B5[cancel_reservation]
        end
    end

    subgraph Data["Data Layer"]
        Redis[(Redis<br/>Cart & Sessions)]
        MongoDB[(MongoDB<br/>Orders & Analytics)]
        PostgreSQL[(PostgreSQL<br/>Menu & Tables)]
    end

    subgraph Context["Context Layer"]
        EG[Entity Graph<br/>Pronoun Resolution]
        SC[Semantic Context<br/>Conversation Memory]
    end

    UI --> FastAPI
    FastAPI --> ChatRoute
    ChatRoute --> RC
    RC --> FOA
    RC --> BA
    FOA <--> DEL
    BA <--> DEL
    FOA --> FoodTools
    BA --> BookingTools
    FoodTools --> Redis
    FoodTools --> MongoDB
    FoodTools --> PostgreSQL
    BookingTools --> Redis
    BookingTools --> PostgreSQL
    FOA --> EG
    EG --> SC
    SC --> Redis
```

---

### Agent Delegation Flow

```mermaid
sequenceDiagram
    participant U as User
    participant RC as Restaurant Crew
    participant FOA as Food Ordering Agent
    participant BA as Booking Agent
    participant Tools as Tools
    participant DB as Databases

    U->>RC: "I want a burger and book a table"
    RC->>FOA: Process request

    Note over FOA: Detects food + booking intent

    FOA->>Tools: search_menu("burger")
    Tools->>DB: Query PostgreSQL
    DB-->>Tools: Menu items
    Tools-->>FOA: "Classic Burger (Rs.350)..."

    FOA->>FOA: Ask quantity (no qty specified)
    FOA-->>U: "How many burgers would you like?"

    U->>FOA: "2 please, and book table for tomorrow"

    FOA->>Tools: add_to_cart("burger", 2)
    Tools->>DB: Update Redis cart
    Tools-->>FOA: "Added 2x Classic Burger"

    Note over FOA: Delegation Required for Booking

    FOA->>BA: Delegate: "Book table for tomorrow"
    BA->>Tools: check_table_availability("tomorrow")
    Tools->>DB: Query availability
    DB-->>Tools: Available tables
    Tools-->>BA: "Tables available..."
    BA->>Tools: make_reservation(...)
    Tools->>DB: Create booking in Redis
    Tools-->>BA: Confirmation code
    BA-->>FOA: "Reservation confirmed: ABC123"

    FOA-->>U: "Added 2 burgers! And your table is booked - Code: ABC123"
```

---

### Why This Architecture is Optimal

```mermaid
mindmap
  root((v30 Architecture))
    Thread Safety
      Factory Pattern
        Session ID Closure
        No Global State
        Concurrent Sessions OK

    Data Integrity
      Redis Single Source
        Cart State
        Session State
        Order History
      MongoDB Analytics
        Order Documents
        Testing Data

    Agent Intelligence
      GPT-4o Reasoning
        Context Understanding
        Intent Detection
        Natural Responses
      Multi-Agent Delegation
        Specialized Roles
        Clean Separation
        Scalable

    Conversation Quality
      Quantity Prompts
        "How many?"
        Multiple Items
      Checkout Flow
        Dine-in/Take-away
        Order Confirmation
      Context Memory
        Entity Graph
        Pronoun Resolution
```

---

### Tool Factory Pattern (Thread Safety)

```mermaid
flowchart LR
    subgraph "Session A"
        SA[session_id: "abc123"]
        TA[Tools with abc123 closure]
    end

    subgraph "Session B"
        SB[session_id: "xyz789"]
        TB[Tools with xyz789 closure]
    end

    subgraph "Factory Functions"
        F1[create_add_to_cart_tool]
        F2[create_checkout_tool]
        F3[create_view_cart_tool]
    end

    SA --> F1 --> TA
    SA --> F2 --> TA
    SA --> F3 --> TA

    SB --> F1 --> TB
    SB --> F2 --> TB
    SB --> F3 --> TB

    subgraph "Redis (Isolated)"
        RA[cart:abc123]
        RB[cart:xyz789]
    end

    TA --> RA
    TB --> RB
```

---

### Checkout Flow (v29+)

```mermaid
stateDiagram-v2
    [*] --> BrowsingMenu
    BrowsingMenu --> AddingItems: "I want X"
    AddingItems --> AskQuantity: No qty specified
    AskQuantity --> AddingItems: User provides qty
    AddingItems --> CartReady: Items in cart
    CartReady --> AskOrderType: "checkout" / "proceed"
    AskOrderType --> WaitingForType: "Dine-in or take away?"
    WaitingForType --> ProcessCheckout: User answers
    ProcessCheckout --> OrderPlaced: checkout(order_type)
    OrderPlaced --> [*]: Order confirmed

    CartReady --> AddingItems: "add more"
    CartReady --> RemovingItems: "remove X"
    RemovingItems --> CartReady: Item removed
```

---

### Evolution to v30

```mermaid
timeline
    title Architecture Evolution

    v26 : Single Agent
        : Basic tools (search, add, view, remove, checkout)
        : Added cancel_order tool

    v27 : Enhanced Tools
        : clear_cart tool
        : update_quantity tool
        : set_special_instructions tool
        : get_item_details tool

    v28 : Multi-Agent Delegation
        : Added Booking Agent
        : CrewAI delegation mechanism
        : "Delegate work to coworker" tool
        : Fixed "I've forwarded" issue

    v29 : Checkout Flow
        : Dine-in / Take-away prompt
        : order_type parameter
        : Typo handling (takw away)

    v30 : Natural Conversation
        : Ask quantity when not specified
        : Handle multiple items
        : Plural handling (burgers → burger)
        : WORKING VERSION
```

---

### Key Design Decisions

| Decision | Why It's Best | Alternative Rejected |
|----------|--------------|---------------------|
| **Multi-Agent with Delegation** | Clean separation of concerns, specialized agents | Single agent with all tools (harder to maintain) |
| **Factory Pattern for Tools** | Thread-safe, session isolation | Global tools (race conditions) |
| **Redis for Cart State** | Fast, single source of truth | In-memory (lost on restart) |
| **GPT-4o for Reasoning** | Better context understanding | GPT-3.5 (misses nuance) |
| **Entity Graph** | Pronoun resolution ("it", "the 2nd one") | No context (repetitive questions) |
| **Sequential Process** | Predictable flow with delegation | Hierarchical (over-complex) |
| **Quantity Prompts** | Natural conversation flow | Auto-assume 1 (not user-friendly) |
| **Checkout Flow** | Matches real restaurant UX | Direct checkout (missing info) |

---

### Data Flow Summary

```mermaid
flowchart LR
    subgraph Input
        MSG[User Message]
        CTX[Conversation History]
        SEM[Semantic Context]
    end

    subgraph Processing
        CREW[Restaurant Crew]
        AGENT[Active Agent]
        TOOL[Tool Execution]
    end

    subgraph Storage
        REDIS[Redis]
        MONGO[MongoDB]
        PG[PostgreSQL]
    end

    subgraph Output
        RESP[Natural Response]
        STATE[Updated State]
    end

    MSG --> CREW
    CTX --> CREW
    SEM --> CREW
    CREW --> AGENT
    AGENT --> TOOL
    TOOL <--> REDIS
    TOOL <--> MONGO
    TOOL <--> PG
    TOOL --> RESP
    TOOL --> STATE
    STATE --> REDIS
```

---

## AG-UI Protocol Integration (v31)

### Real-Time Streaming Architecture

```mermaid
sequenceDiagram
    participant UI as Frontend
    participant SSE as SSE Endpoint
    participant Emitter as AGUIEventEmitter
    participant Crew as Restaurant Crew
    participant Tools as Tools

    UI->>SSE: POST /api/v1/chat/stream
    SSE->>Emitter: Create emitter for session

    rect rgb(240, 248, 255)
        Note over SSE,Emitter: SSE Stream Open
        Emitter-->>UI: RUN_STARTED
        Emitter-->>UI: ACTIVITY_START (thinking)

        SSE->>Crew: Process message
        Crew->>Tools: Execute tool
        Emitter-->>UI: TOOL_CALL_START
        Emitter-->>UI: TOOL_CALL_ARGS
        Tools-->>Crew: Result
        Emitter-->>UI: TOOL_CALL_RESULT
        Emitter-->>UI: TOOL_CALL_END

        Crew-->>SSE: Response text
        Emitter-->>UI: TEXT_MESSAGE_START
        Emitter-->>UI: TEXT_MESSAGE_CONTENT (chunks)
        Emitter-->>UI: TEXT_MESSAGE_END
        Emitter-->>UI: RUN_FINISHED
    end
```

### AG-UI Event Types

| Event | Purpose | When Emitted |
|-------|---------|--------------|
| `RUN_STARTED` | Processing begins | Start of request |
| `ACTIVITY_START` | Show typing indicator | Thinking, searching |
| `ACTIVITY_END` | Hide indicator | Activity complete |
| `TOOL_CALL_START` | Tool execution begins | Before tool runs |
| `TOOL_CALL_ARGS` | Show tool arguments | With tool start |
| `TOOL_CALL_RESULT` | Tool output | After execution |
| `TOOL_CALL_END` | Tool complete | After result |
| `TEXT_MESSAGE_START` | Response begins | Before streaming |
| `TEXT_MESSAGE_CONTENT` | Text chunk | During streaming |
| `TEXT_MESSAGE_END` | Response complete | After all text |
| `RUN_FINISHED` | Processing done | End of request |
| `RUN_ERROR` | Error occurred | On failure |

### User Experience Enhancement

```
Before AG-UI:                    With AG-UI:
+------------------+             +------------------+
| [User sends msg] |             | [User sends msg] |
|                  |             |                  |
| [2-3 sec wait]   |             | "Thinking..."    |
|                  |             | "Searching menu" |
|                  |             | "Adding to cart" |
| [Full response]  |             | [Streamed text]  |
+------------------+             +------------------+
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/chat/stream` | POST | Process message with SSE streaming |
| `/api/v1/chat/stream/{session_id}` | GET | Connect to existing session stream |

### Frontend Integration Example

```javascript
// Connect to AG-UI stream
const response = await fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        message: "I want a burger",
        session_id: "session-123"
    })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const lines = decoder.decode(value).split('\n');
    for (const line of lines) {
        if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6));

            switch (event.type) {
                case 'ACTIVITY_START':
                    showTypingIndicator(event.message);
                    break;
                case 'TEXT_MESSAGE_CONTENT':
                    appendText(event.delta);
                    break;
                case 'RUN_FINISHED':
                    hideTypingIndicator();
                    break;
            }
        }
    }
}
```

---

## Quick Reference

**Tag:** `v30-working`

**Restore:** `git checkout v30-working`

**Key Files:**
- `app/orchestration/restaurant_crew.py` - Main orchestrator
- `app/features/food_ordering/crew_agent.py` - Food tools (10)
- `app/features/booking/crew_agent.py` - Booking tools (5) - PostgreSQL integrated
- `app/core/semantic_context.py` - Entity graph
- `app/core/redis.py` - Cart & session state
- `app/core/db_pool.py` - PostgreSQL connection pool
- `app/core/agui_events.py` - AG-UI event emitter
- `app/api/routes/stream.py` - SSE streaming endpoint
