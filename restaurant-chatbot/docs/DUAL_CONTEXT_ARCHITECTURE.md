# Dual Context Architecture
## Semantic Graph RAG + Event-Sourced SQL

## Overview

The current architecture uses **TWO complementary context systems**:

1. **Semantic Graph (Redis)** - For conversational understanding
2. **Event-Sourced State (PostgreSQL)** - For transactional accuracy

This is intentional and beneficial!

---

## System 1: Semantic Graph RAG (Existing)

**Purpose:** Natural language understanding, pronoun resolution, conversational context

**Location:** `app/core/semantic_context.py`

**Storage:** Redis

**What it tracks:**
```python
{
    "last_mentioned_item": "Margherita Pizza",
    "last_shown_menu": ["Pizza", "Pasta", "Salad"],
    "entities": {
        "menu_items": ["Pizza"],
        "quantities": [2],
        "actions": ["add"]
    }
}
```

**Used by:**
- Task description in CrewAI (via `get_relevant_context()`)
- RAG filtering (only include relevant entities, not all)
- Old tools (not yet migrated to event-sourced)

**How it works:**
```
User: "add one more"
    ↓
semantic_context.get_relevant_context("add one more")
    ↓
Returns: "Last: Margherita Pizza" (pronoun "one" → Pizza)
    ↓
LLM knows: user wants to add 1x Margherita Pizza
```

**Cost:** ~50-100 tokens per request (RAG-filtered!)

---

## System 2: Event-Sourced SQL (New)

**Purpose:** Exact transactional state, zero-token queries

**Location:** `app/core/session_events.py`

**Storage:** PostgreSQL (UNLOGGED + LOGGED tables)

**What it tracks:**
```sql
session_cart:
  - item_id, item_name, quantity, price (current cart state)

session_state:
  - last_mentioned_item_id, last_mentioned_item_name (pronoun resolution)

session_events:
  - Complete audit trail (item_added, item_removed, etc.)
```

**Used by:**
- Event-sourced tools (search_menu, add_to_cart, view_cart, remove_from_cart)
- SQL queries for exact state (zero tokens!)

**How it works:**
```
Tool: view_cart()
    ↓
SQL: SELECT * FROM get_session_cart('session_123')
    ↓
Returns: [{item_name: "Pizza", quantity: 2, price: 300}]
    ↓
Formatter (gpt-4o-mini): "You've got 2 pizzas! ₹600 total."
```

**Cost:** 0 tokens for data retrieval + ~150 tokens for formatting = ~150 tokens total

---

## How They Work Together

### Example: "add one more pizza"

**Step 1: LLM Intent Recognition (uses Semantic Graph)**
```python
# restaurant_crew.py
semantic_context = graph.get_relevant_context("add one more pizza")
# Returns: "Last: Margherita Pizza"  (~50 tokens)

task = Task(
    description=f"User: add one more pizza\nContext: {semantic_context}",
    agent=food_ordering_agent
)
```

**LLM thinks:** "User said 'one more pizza', context says last was Margherita, so they want 1x Margherita Pizza"

**Step 2: LLM Calls Tool**
```
LLM: I'll call add_to_cart(item="Margherita Pizza", quantity=1)
```

**Step 3: Tool Execution (uses Event-Sourced SQL)**
```python
# tools_event_sourced.py
@tool("add_to_cart")
def add_to_cart(item: str, quantity: int):
    # Find item in preloader (fast in-memory lookup)
    found_item = preloader.find_item("Margherita Pizza")

    # Add to SQL cart (event-sourced, 0 tokens!)
    tracker = get_session_tracker(session_id)
    cart = await tracker.add_to_cart(
        item_id=found_item['id'],
        item_name=found_item['name'],
        quantity=1,
        price=found_item['price']
    )
    # SQL operations:
    # 1. INSERT INTO session_events (event_type='item_added', ...)
    # 2. INSERT INTO session_cart (item_name='Margherita Pizza', quantity=1, ...)
    # 3. UPDATE session_state SET last_mentioned_item_name='Margherita Pizza'

    # Format response (gpt-4o-mini, ~150 tokens)
    return format_item_added("Margherita Pizza", 1, cart['total'], cart['item_count'])
```

**Step 4: Response**
```
"Added 1 more Margherita Pizza! You now have 3 items (₹950 total). Anything else?"
```

---

## Division of Responsibilities

| Task | Semantic Graph | Event-Sourced SQL |
|------|---------------|------------------|
| **Pronoun resolution ("add one more")** | ✅ Provides context to LLM | ✅ Also tracks in session_state |
| **Intent understanding** | ✅ Entity extraction | ❌ Not needed |
| **Cart state queries** | ❌ Expensive (text in prompt) | ✅ Free (SQL query) |
| **Exact transaction log** | ❌ Not structured | ✅ Event sourcing |
| **Analytics** | ❌ Hard (Redis text) | ✅ Easy (SQL queries) |
| **Crash recovery** | ✅ Persisted in Redis | ⚠️ HOT tables lost (OK) |

---

## Token Comparison

### Old Approach (Full Semantic Graph)
```
Task prompt:
  - Instructions: 15K tokens
  - Semantic context (full): 1K tokens
  - Cart state (text): 500 tokens
  - Tools: 5K tokens
  - Total: ~21.5K tokens
```

### Current Approach (RAG Graph + Event SQL)
```
Task prompt:
  - Instructions: 500 tokens (reduced!)
  - Semantic context (RAG-filtered): 100 tokens
  - Cart state: 0 tokens (SQL query!)
  - Tools: 2K tokens
  - Total: ~2.6K tokens

Tool formatting (optional):
  - gpt-4o-mini: 150 tokens

Grand total: ~2.75K tokens
```

**Savings: 87% reduction** 🎉

---

## Why Keep Both?

**Q:** Why not use ONLY event-sourced SQL?

**A:** Because natural language understanding needs context!

**Example:**
```
User: "add pizza"
LLM: Which pizza? (needs to know we have 5 types)

User: "the margherita one"
LLM: Got it! (knows we're talking about pizzas)
```

The semantic graph provides:
- Entity disambiguation ("pizza" → which type?)
- Conversation flow tracking
- RAG for efficient context retrieval

The event-sourced SQL provides:
- Exact cart state (not fuzzy text)
- Zero-token queries
- Complete audit trail

**Together, they're powerful!**

---

## Migration Strategy

**Phase 1 (Current):** Hybrid system
- Semantic graph for LLM context (RAG-filtered)
- Event-sourced tools for core operations (add, view, remove)
- Old tools still use semantic graph

**Phase 2 (Future):** Migrate remaining tools
- Checkout → Event-sourced
- Order history → Event-sourced
- Keep semantic graph for conversational understanding

**Phase 3 (Optimization):** Reduce duplication
- Session_state.last_mentioned_item (SQL) can replace Redis tracking
- But keep semantic graph for entity extraction and RAG

---

## Architecture Diagram

```
┌─────────────────────────────────────────┐
│          User Message                    │
│       "add one more pizza"              │
└─────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│     Semantic Graph RAG (Redis)          │
│  get_relevant_context(user_message)     │
│  → "Last: Margherita Pizza"             │
│  Cost: ~50 tokens                       │
└─────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│          CrewAI + LLM                    │
│  Task: "User wants pizza, last was      │
│         Margherita"                      │
│  LLM: "I'll call add_to_cart"           │
│  Cost: ~2K tokens                       │
└─────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│    Tool: add_to_cart(item, qty)         │
│                                          │
│  1. Find item (preloader, in-memory)    │
│  2. SQL INSERT session_cart             │  Event-Sourced
│  3. SQL INSERT session_events           │  (PostgreSQL)
│  4. SQL UPDATE session_state            │
│  5. Format with gpt-4o-mini             │  Cost: 0 tokens (SQL)
│     Cost: ~150 tokens                   │       + 150 (format)
│                                          │       = 150 total
└─────────────────────────────────────────┘
           │
           ↓
┌─────────────────────────────────────────┐
│    Response to User                      │
│  "Added 1 Margherita Pizza! ₹950 total" │
└─────────────────────────────────────────┘

Total tokens: ~2.2K (vs 21.5K before = 90% reduction!)
```

---

## Summary

**Yes, semantic understanding via graph RAG is still there!**

- Semantic graph (Redis): Conversational context, pronoun resolution
- Event sourcing (SQL): Exact state, zero-token queries
- Both work together: Graph for LLM understanding, SQL for transactional accuracy

**This is better than using just one system:**
- Semantic graph alone: Expensive, fuzzy state
- SQL alone: Can't handle natural language ambiguity
- **Both together: Best of both worlds!** ✅
