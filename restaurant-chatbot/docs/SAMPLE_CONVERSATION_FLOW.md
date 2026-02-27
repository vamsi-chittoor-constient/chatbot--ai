# Sample Conversation Flow - Event-Sourced Architecture
## Real-world example showing HOT/COLD storage in action

---

## Conversation Timeline

```
User: vamsi (customer_id: 4c85ba72-f59b-4287-bf91-e53f49ed0b9d)
Session: sess_abc123
Time: 2026-01-18 10:30:00
```

---

## 💬 **Turn 1: User browses menu**

### User Message
```
"show me the menu"
```

### LLM Processing (Intent Classification Only)
```
User input: "show me the menu"
↓
LLM classifies intent → Tool: search_menu()
↓
NO context passed to LLM (zero tokens!)
```

### Tool Execution: `search_menu()`

**1. Query menu (from preloader - in-memory, fast)**
```python
# Preloader cached menu (365 items, ~2MB RAM)
items = preloader.search(query="", meal_period="Breakfast")
# Returns: [{"id": "...", "name": "Idly", "price": 40}, ...]
```

**2. Log event to database**
```sql
INSERT INTO session_events (session_id, event_type, event_data)
VALUES (
    'sess_abc123',
    'menu_viewed',
    '{"query": "", "result_count": 50, "meal_period": "Breakfast"}'::jsonb
);
-- Write time: ~1ms (LOGGED table)
```

**3. Update session state**
```sql
INSERT INTO session_state (session_id, user_id, last_shown_menu)
VALUES (
    'sess_abc123',
    '4c85ba72-f59b-4287-bf91-e53f49ed0b9d',
    '[{"id": "item1", "name": "Idly", "position": 1}, ...]'::jsonb
)
ON CONFLICT (session_id) DO UPDATE SET
    last_shown_menu = EXCLUDED.last_shown_menu,
    last_activity_at = NOW();
-- Write time: ~1ms (UNLOGGED - HOT)
```

**4. Emit AGUI event (frontend callback)**
```python
emit_menu_data(session_id, items, meal_period)
# Frontend receives menu card event → displays visual menu
```

**5. Return final message (NO LLM!)**
```python
return "[MENU DISPLAYED] Here's our breakfast menu! What would you like?"
```

### Database State After Turn 1

**session_events:**
| event_id | session_id | event_type | event_data | timestamp |
|----------|-----------|-----------|-----------|-----------|
| uuid-1 | sess_abc123 | menu_viewed | {"query": "", "result_count": 50, ...} | 10:30:00 |

**session_state (UNLOGGED - HOT):**
| session_id | user_id | last_shown_menu | current_step | last_activity_at |
|-----------|---------|----------------|--------------|-----------------|
| sess_abc123 | 4c85ba72... | [{"id": "item1", ...}] | browsing | 10:30:00 |

**session_cart:** *(empty)*

---

## 💬 **Turn 2: User adds item**

### User Message
```
"add 2 idly"
```

### LLM Processing
```
User input: "add 2 idly"
↓
LLM classifies: Tool = add_to_cart, Params = {item: "idly", quantity: 2}
```

### Tool Execution: `add_to_cart("idly", 2)`

**1. Find item (preloader lookup)**
```python
found_item = preloader.find_item("idly")
# Returns: {"id": "item-123", "name": "Idly", "price": 40}
```

**2. Log event**
```sql
INSERT INTO session_events (session_id, event_type, event_data)
VALUES (
    'sess_abc123',
    'item_added',
    '{"item_id": "item-123", "item_name": "Idly", "quantity": 2, "price": 40}'::jsonb
);
-- Write time: ~1ms (LOGGED - audit trail)
```

**3. Update cart (HOT storage - UNLOGGED)**
```sql
INSERT INTO session_cart (session_id, item_id, item_name, quantity, price)
VALUES ('sess_abc123', 'item-123', 'Idly', 2, 40.00)
ON CONFLICT (session_id, item_id) DO UPDATE SET
    quantity = session_cart.quantity + EXCLUDED.quantity,
    updated_at = NOW(),
    is_active = TRUE;
-- Write time: ~1ms (UNLOGGED - 3-5x faster!)
```

**4. Update session state (last mentioned item)**
```sql
UPDATE session_state
SET
    last_mentioned_item_id = 'item-123',
    last_mentioned_item_name = 'Idly',
    current_step = 'ordering',
    last_activity_at = NOW()
WHERE session_id = 'sess_abc123';
-- Write time: ~1ms (UNLOGGED)
```

**5. Query cart for response**
```sql
SELECT * FROM get_session_cart('sess_abc123');
-- Returns: [{item_name: "Idly", quantity: 2, price: 40, total: 80}]
-- Query time: ~1ms
```

**6. Emit cart update (AGUI)**
```python
emit_cart_data(session_id, cart['items'], cart['total'])
# Frontend receives cart update → displays visual cart
```

**7. Return final message**
```python
return "Added 2x Idly to your cart! Anything else?"
```

### Database State After Turn 2

**session_events:**
| event_id | event_type | event_data | timestamp |
|----------|-----------|-----------|-----------|
| uuid-1 | menu_viewed | {...} | 10:30:00 |
| uuid-2 | **item_added** | **{"item_name": "Idly", "quantity": 2, ...}** | **10:30:15** |

**session_cart (HOT - UNLOGGED):**
| session_id | item_id | item_name | quantity | price | is_active | added_at |
|-----------|---------|-----------|----------|-------|-----------|----------|
| sess_abc123 | item-123 | **Idly** | **2** | **40.00** | **TRUE** | **10:30:15** |

**session_state (HOT - UNLOGGED):**
| session_id | last_mentioned_item_name | current_step | last_activity_at |
|-----------|-------------------------|--------------|-----------------|
| sess_abc123 | **Idly** | **ordering** | **10:30:15** |

---

## 💬 **Turn 3: User adds another item**

### User Message
```
"also add 1 masala dosa"
```

### Tool Execution: `add_to_cart("masala dosa", 1)`

**Database operations (same as Turn 2):**
```sql
-- 1. Log event
INSERT INTO session_events (...) VALUES (..., 'item_added', '{"item_name": "Masala Dosa", ...}');

-- 2. Add to cart
INSERT INTO session_cart (...) VALUES (..., 'item-456', 'Masala Dosa', 1, 80.00);

-- 3. Update state
UPDATE session_state SET last_mentioned_item_name = 'Masala Dosa', ...;

-- 4. Query cart
SELECT * FROM get_session_cart('sess_abc123');
-- Returns: [
--   {item_name: "Idly", quantity: 2, price: 40, total: 80},
--   {item_name: "Masala Dosa", quantity: 1, price: 80, total: 80}
-- ]
```

**Response:**
```
"Added 1x Masala Dosa! You have 2 items (₹160 total). Anything else?"
```

### Database State After Turn 3

**session_cart (HOT):**
| item_name | quantity | price | total | is_active |
|-----------|----------|-------|-------|-----------|
| Idly | 2 | 40 | 80 | TRUE |
| **Masala Dosa** | **1** | **80** | **80** | **TRUE** |

**Cart Total:** `₹160` *(calculated via SQL function)*

---

## 💬 **Turn 4: User wants to see cart**

### User Message
```
"view my cart"
```

### Tool Execution: `view_cart()`

**1. Query cart state (zero tokens - pure SQL!)**
```sql
-- No context passed to LLM!
-- Just query current state from database

SELECT * FROM get_session_cart('sess_abc123');
-- Returns current cart items
-- Query time: ~1ms

SELECT get_cart_total('sess_abc123');
-- Returns: 160.00
-- Query time: <1ms
```

**2. Emit cart card (AGUI)**
```python
emit_cart_data(session_id, cart_items, total)
# Frontend displays visual cart card
```

**3. Return formatted message**
```python
return "Your cart: 2x Idly (₹80), 1x Masala Dosa (₹80). Total: ₹160. Ready to checkout?"
```

**Key Point:** Cart state retrieved via SQL query, NOT from text context in LLM prompt!

---

## 💬 **Turn 5: User adds more of same item (pronoun resolution)**

### User Message
```
"add one more"
```

### LLM Processing
```
User input: "add one more"
Context needed: What item? → Query session_state
```

### Tool Execution: `add_to_cart("", 1)` with context query

**1. Query last mentioned item (SQL, not text!)**
```sql
SELECT last_mentioned_item_name
FROM session_state
WHERE session_id = 'sess_abc123';
-- Returns: "Masala Dosa"
-- Query time: <1ms
```

**2. Tool uses queried context**
```python
# Tool internally queries: "What was last mentioned?"
last_item = get_last_mentioned_item(session_id)
# Returns: {"item_name": "Masala Dosa"}

# Add 1 more of that item
add_to_cart("Masala Dosa", 1)
```

**3. Update cart (upsert existing item)**
```sql
UPDATE session_cart
SET quantity = quantity + 1, updated_at = NOW()
WHERE session_id = 'sess_abc123' AND item_id = 'item-456';
-- Masala Dosa quantity: 1 → 2
```

**Response:**
```
"Added 1x Masala Dosa! You now have 2x Masala Dosa. Total: ₹240."
```

### Database State After Turn 5

**session_cart:**
| item_name | quantity | price | total |
|-----------|----------|-------|-------|
| Idly | 2 | 40 | 80 |
| Masala Dosa | **2** | 80 | **160** |

**Cart Total:** `₹240`

---

## 💬 **Turn 6: Checkout (HOT → COLD Transition)**

### User Message
```
"checkout please"
```

### Tool Execution: `checkout("take_away")`

**This is where HOT → COLD transition happens!**

**1. Create checkout record (HOT)**
```sql
INSERT INTO session_checkout (session_id, order_type, started_at)
VALUES ('sess_abc123', 'take_away', NOW());
-- UNLOGGED table - fast write
```

**2. User confirms payment method**
```
"I'll pay cash"
```

**3. Call HOT → COLD transition function**
```sql
SELECT create_order_from_session(
    'sess_abc123',
    'take_away',
    'cash',
    '4c85ba72-f59b-4287-bf91-e53f49ed0b9d'
);
```

**Inside `create_order_from_session()` function:**

```sql
BEGIN TRANSACTION;

-- Step 1: Create order (COLD - LOGGED, permanent)
INSERT INTO orders (
    customer_id,
    order_type_id,
    order_source_id,
    total_amount,
    created_at
)
VALUES (
    '4c85ba72-f59b-4287-bf91-e53f49ed0b9d',
    (SELECT order_type_id FROM order_type_table WHERE order_type_name = 'take_away'),
    (SELECT order_source_id FROM order_source_type WHERE source_name = 'chatbot'),
    240.00,
    NOW()
)
RETURNING order_id;
-- Returns: order_id = 'order-789'

-- Step 2: Copy cart items to order_item (COLD - LOGGED)
INSERT INTO order_item (order_id, menu_item_id, quantity, unit_price, subtotal)
SELECT
    'order-789',
    sc.item_id,
    sc.quantity,
    sc.price,
    sc.quantity * sc.price
FROM session_cart sc
WHERE sc.session_id = 'sess_abc123' AND sc.is_active = TRUE;

-- Inserted rows:
-- ('order-789', 'item-123', 2, 40, 80)   -- Idly
-- ('order-789', 'item-456', 2, 80, 160)  -- Masala Dosa

-- Step 3: Mark session as completed (HOT)
UPDATE session_state
SET current_step = 'order_placed'
WHERE session_id = 'sess_abc123';

-- Step 4: Clear cart (soft delete - HOT)
UPDATE session_cart
SET is_active = FALSE
WHERE session_id = 'sess_abc123';

-- Step 5: Log order placed event (WARM - audit trail)
INSERT INTO session_events (session_id, event_type, event_data)
VALUES (
    'sess_abc123',
    'order_placed',
    '{"order_id": "order-789", "total": 240, "payment_method": "cash"}'::jsonb
);

COMMIT;
```

**Response:**
```
"Order placed successfully! Order #789 - Total: ₹240. Please pay cash when you pick up. Thank you!"
```

---

## 📊 **Final Database State**

### 🔥 HOT Tables (UNLOGGED - Temporary)

**session_cart:**
| item_name | is_active | Cart Status |
|-----------|-----------|-------------|
| Idly | **FALSE** | ✅ Cleared (soft deleted) |
| Masala Dosa | **FALSE** | ✅ Cleared (soft deleted) |

**session_state:**
| current_step | Status |
|--------------|--------|
| **order_placed** | ✅ Completed |

### 🧊 WARM Tables (LOGGED - Audit Trail)

**session_events (Complete history):**
| event_type | event_data | timestamp |
|-----------|-----------|-----------|
| menu_viewed | {"query": "", ...} | 10:30:00 |
| item_added | {"item_name": "Idly", "quantity": 2} | 10:30:15 |
| item_added | {"item_name": "Masala Dosa", "quantity": 1} | 10:30:30 |
| item_added | {"item_name": "Masala Dosa", "quantity": 1} | 10:30:45 |
| **order_placed** | **{"order_id": "order-789", "total": 240}** | **10:31:00** |

### ❄️ COLD Tables (LOGGED - Permanent)

**orders:**
| order_id | customer_id | total_amount | order_type | created_at |
|----------|-------------|--------------|-----------|-----------|
| **order-789** | 4c85ba72... | **240.00** | take_away | 10:31:00 |

**order_item:**
| order_id | menu_item_id | item_name | quantity | unit_price | subtotal |
|----------|--------------|-----------|----------|-----------|----------|
| order-789 | item-123 | Idly | 2 | 40 | 80 |
| order-789 | item-456 | Masala Dosa | 2 | 80 | 160 |

---

## 🔍 **Analytics Queries (Event Sourcing Power)**

### Conversion Funnel
```sql
SELECT
    COUNT(DISTINCT CASE WHEN event_type = 'menu_viewed' THEN session_id END) as viewed_menu,
    COUNT(DISTINCT CASE WHEN event_type = 'item_added' THEN session_id END) as added_items,
    COUNT(DISTINCT CASE WHEN event_type = 'order_placed' THEN session_id END) as placed_orders
FROM session_events
WHERE timestamp > NOW() - INTERVAL '1 day';

-- Results:
-- viewed_menu: 500
-- added_items: 320 (64% conversion)
-- placed_orders: 180 (36% conversion from view, 56% from add)
```

### Popular Items
```sql
SELECT
    event_data->>'item_name' as item_name,
    SUM((event_data->>'quantity')::int) as total_quantity
FROM session_events
WHERE event_type = 'item_added'
  AND timestamp > NOW() - INTERVAL '7 days'
GROUP BY event_data->>'item_name'
ORDER BY total_quantity DESC
LIMIT 10;
```

### Average Time to Order
```sql
SELECT
    AVG(order_time - view_time) as avg_time_to_order
FROM (
    SELECT
        session_id,
        MIN(CASE WHEN event_type = 'menu_viewed' THEN timestamp END) as view_time,
        MIN(CASE WHEN event_type = 'order_placed' THEN timestamp END) as order_time
    FROM session_events
    WHERE timestamp > NOW() - INTERVAL '1 day'
    GROUP BY session_id
    HAVING MIN(CASE WHEN event_type = 'order_placed' THEN timestamp END) IS NOT NULL
) t;

-- Result: ~3.5 minutes average
```

---

## ⚡ **Performance Summary**

| Operation | Old (Redis Text) | New (Event-Sourced SQL) | Improvement |
|-----------|------------------|------------------------|-------------|
| **Add to cart** | ~1ms + token cost | ~1ms (UNLOGGED) | Same speed, $0 tokens |
| **View cart** | ~1ms + 2K tokens | ~1ms SQL query | Same speed, $0 tokens |
| **Context retrieval** | 500 tokens/request | 0 tokens (SQL) | **100% token savings** |
| **LLM prompt size** | ~15K tokens | ~500 tokens | **97% reduction** |
| **Analytics** | Export to DB | Built-in SQL | **Instant queries** |
| **Audit trail** | None | Complete | **Full history** |

---

## 🧠 **Key Architectural Wins**

### 1. Zero Token Context
```python
# OLD approach (text-based)
context = f"Cart: {items}, Last: {last_item}, Menu: {menu_items}..."  # 2000 tokens!
llm.invoke(user_message + context)

# NEW approach (event-sourced)
tool_params = llm.invoke(user_message)  # Only ~100 tokens for intent
cart = query_sql("SELECT * FROM session_cart WHERE ...")  # 0 tokens!
```

### 2. Exact State Queries
```sql
-- No fuzzy matching, exact SQL queries
SELECT item_name, quantity FROM session_cart WHERE session_id = ? AND is_active = TRUE;
```

### 3. Event Sourcing
```sql
-- Complete audit trail
SELECT * FROM session_events WHERE session_id = 'sess_abc123' ORDER BY timestamp;
```

### 4. HOT → COLD Transition
```
Active Session (HOT/UNLOGGED) → Checkout → Permanent Order (COLD/LOGGED)
8KB temporary data → Durable order records
```

### 5. Crash Recovery
- **HOT lost** (cart, state) → User re-orders ✅ Acceptable
- **WARM preserved** (events) → Analytics intact ✅ Critical
- **COLD preserved** (orders, payments) → Revenue safe ✅ Critical

---

## 🎯 **Conclusion**

This architecture:
- ✅ **90% token reduction** (context via SQL, not text)
- ✅ **3-5x faster writes** (UNLOGGED tables)
- ✅ **Exact state** (SQL queries, not fuzzy text)
- ✅ **Complete audit trail** (event sourcing)
- ✅ **Analytics ready** (SQL queries on events)
- ✅ **Production grade** (HOT/COLD separation)

**Result:** Fast, cheap, accurate, auditable! 🚀
