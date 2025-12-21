# Agent-to-Agent Communication Architecture

**Complete Guide: Input/Output Tracking, Storage Locations, and Communication Patterns**

---

## Table of Contents

1. [Overview](#overview)
2. [All Agents - Functionality & Tools](#all-agents---functionality--tools)
3. [Communication Pattern 1: Routing-Based (Auth Handoff)](#communication-pattern-1-routing-based-auth-handoff)
4. [Communication Pattern 2: Delegation Protocol](#communication-pattern-2-delegation-protocol)
5. [Complete Flow Examples with Storage Tracking](#complete-flow-examples-with-storage-tracking)
6. [Data Storage Architecture](#data-storage-architecture)
7. [State Field Reference](#state-field-reference)
8. [Best Practices](#best-practices)

---

## Overview

The system has **TWO communication patterns** between agents:

1. **Routing-Based Communication** (Currently Active)
   - Uses `original_intent_agent` field
   - Graph-level routing via conditional edges
   - **Use case**: Authentication handoff during transactions

2. **Delegation Protocol** (Available, Ready to Use)
   - Uses `AgentCommunicator` class with delegation stack
   - Runtime routing with context passing
   - **Use case**: Complex multi-agent workflows

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AGENT COMMUNICATION SYSTEM                    │
└─────────────────────────────────────────────────────────────────┘

USER INPUT
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  ORCHESTRATION LAYER                                             │
│  ├─ auth_node                                                    │
│  ├─ perceive_node                                                │
│  ├─ task_manager_node                                            │
│  ├─ validation_node                                              │
│  └─ router_node  ←─────┐                                        │
└─────────────┬───────────│───────────────────────────────────────┘
              │           │
              ▼           │ (Communication happens here)
┌─────────────────────────┴───────────────────────────────────────┐
│  AGENT LAYER (8 Main Agents)                                     │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ food_ordering    │  │ booking_agent    │  │ user_agent    │ │
│  │ (sub-graph)      │  │ (autonomous)     │  │ (auth)        │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌───────────────┐ │
│  │ payment_agent    │  │ customer_sat     │  │ general       │ │
│  │ (autonomous)     │  │ (complaints)     │  │ queries       │ │
│  └──────────────────┘  └──────────────────┘  └───────────────┘ │
│                                                                   │
│  ┌──────────────────┐  ┌──────────────────┐                    │
│  │ support_agent    │  │ response_agent   │                    │
│  │                  │  │ (formatter)      │                    │
│  └──────────────────┘  └──────────────────┘                    │
└───────────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────────┐
│  DATABASE LAYER                                                  │
│  ├─ PostgreSQL (orders, bookings, users, menu)                  │
│  ├─ MongoDB (carts)                                              │
│  └─ Redis (inventory, rate limiting)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## All Agents - Functionality & Tools

### Agent 1: food_ordering_agent (Hierarchical Sub-Graph)

**Location**: `app/agents/food_ordering/node.py`

**Type**: Parent agent with 5 sub-agents

**Purpose**: Handle all food ordering operations from menu browsing to checkout

#### What It Does

```
┌─────────────────────────────────────────────────────────────────┐
│  FOOD ORDERING AGENT FLOW                                        │
└─────────────────────────────────────────────────────────────────┘

User Message: "I want butter chicken"
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Sub-Intent Classification (LLM)                         │
│  ─────────────────────────────────────────                       │
│  Input: user_message + FoodOrderingState                         │
│  LLM classifies into 1 of 5 sub-intents:                         │
│    • browse_menu                                                 │
│    • discover_items                                              │
│    • manage_cart                                                 │
│    • validate_order                                              │
│    • execute_checkout                                            │
│                                                                   │
│  Output: SubIntentClassification                                 │
│    sub_intent = "manage_cart"                                    │
│    entities = {"action": "add", "item_name": "butter chicken"}  │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Entity Validation                                       │
│  ─────────────────────────────────────                           │
│  Check if required entities present for sub-intent               │
│  If missing → Return clarification request                       │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Guardrail Checks                                        │
│  ─────────────────────────────────────────                       │
│  • SOFT GUIDES: Helpful redirects (empty cart → browse)          │
│  • HARD BLOCKS: Safety gates (locked cart, no validation)        │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Route to Sub-Agent (Deterministic)                      │
│  ─────────────────────────────────────────────                   │
│  {                                                                │
│    "browse_menu": menu_browsing_agent,                           │
│    "discover_items": menu_discovery_agent,                       │
│    "manage_cart": cart_management_agent,                         │
│    "validate_order": checkout_validator_agent,                   │
│    "execute_checkout": checkout_executor_agent                   │
│  }                                                                │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Execute Sub-Agent                                       │
│  ─────────────────────────────────────────                       │
│  cart_management_agent:                                          │
│    1. Fetch item from PostgreSQL                                 │
│    2. Check inventory in Redis                                   │
│    3. Reserve quantity in Redis                                  │
│    4. Add to cart in MongoDB                                     │
│    5. Return ActionResult                                        │
└────────────────────────┬────────────────────────────────────────┘
    ↓
ActionResult returned to parent graph
```

#### Sub-Agents

**1. menu_browsing_agent**
- **Purpose**: Browse menu structure
- **Operations**:
  - Show all categories
  - Show items in specific category
- **Database**: PostgreSQL (menu_items table)

**2. menu_discovery_agent**
- **Purpose**: Search and discover menu items
- **Operations**:
  - Search by name
  - Filter by category/dietary preferences
  - Get recommendations
- **Database**: PostgreSQL + Redis (caching)

**3. cart_management_agent**
- **Purpose**: Manage shopping cart
- **Operations**:
  - Add item to cart
  - Remove item from cart
  - Update item quantity
  - View cart contents
  - Clear cart
- **Database**: MongoDB (carts collection), Redis (inventory)

**4. checkout_validator_agent**
- **Purpose**: Validate cart before checkout
- **Operations**:
  - Validate cart items availability
  - Check inventory
  - Validate total amount
  - Set cart_validated flag
- **Database**: PostgreSQL, MongoDB, Redis

**5. checkout_executor_agent**
- **Purpose**: Execute the checkout process
- **Operations**:
  - Create order in PostgreSQL
  - Create order items
  - Generate payment link (Razorpay)
  - Clear cart in MongoDB
  - Confirm inventory in Redis
- **Database**: PostgreSQL, MongoDB, Redis

#### Input Fields

```python
# From state
state["messages"]              # Conversation history
state["task_entities"]         # Cart state, order details
state["user_id"]               # For authenticated operations
state["session_id"]            # For cart identification
state["device_id"]             # For anonymous cart tracking
```

#### Output Fields

```python
# ActionResult (structured data)
state["action_result"] = {
    "action": "item_added_to_cart",
    "success": True,
    "data": {
        "item_name": "Butter Chicken",
        "quantity": 1,
        "price": 350.00,
        "cart_items": [
            {"item_id": "123", "name": "Butter Chicken", "quantity": 1, "price": 350.00}
        ],
        "cart_subtotal": 350.00
    },
    "context": {"sub_intent": "manage_cart"}
}

# Updated task entities
state["task_entities"]["cart_items"] = [...]
state["task_entities"]["cart_subtotal"] = 350.00

# Execution metadata
state["agent_metadata"] = {
    "agent_name": "food_ordering_agent",
    "sub_agent": "cart_management",
    "execution_time_ms": 450,
    "database_queries": 3
}
```

#### Storage Locations

| Data | Storage | Purpose |
|------|---------|---------|
| Cart items | MongoDB `carts` collection | Session-based cart storage |
| Menu items | PostgreSQL `menu_items` table | Menu data |
| Inventory | Redis `inventory:item_id` | Real-time availability |
| Reservations | Redis `reservation:session:item` | Temporary holds (15 min TTL) |
| Orders | PostgreSQL `orders` table | Permanent order records |
| Order items | PostgreSQL `order_items` table | Order line items |

---

### Agent 2: booking_agent (Autonomous Sub-Graph)

**Location**: `app/agents/booking/node.py`

**Type**: Autonomous agent with internal reasoning loops

**Purpose**: Handle table reservations with complete multi-step flow

#### What It Does

```
┌─────────────────────────────────────────────────────────────────┐
│  BOOKING AGENT FLOW                                              │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Entity Collection (Multi-turn)                          │
│  ────────────────────────────────────                            │
│  Collect required booking details:                               │
│    • party_size (e.g., 2, 4, 6)                                  │
│    • date (e.g., "tomorrow", "2024-01-15")                       │
│    • time (e.g., "7pm", "19:00")                                 │
│    • special_requests (optional)                                 │
│                                                                   │
│  Storage: state["task_entities"]["booking_progress"]            │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Check Availability                                      │
│  ────────────────────────────────────────                        │
│  Tool: check_table_availability(date, time, party_size)          │
│                                                                   │
│  Database Query:                                                 │
│    SELECT * FROM tables                                          │
│    WHERE capacity >= :party_size                                 │
│    AND id NOT IN (                                               │
│      SELECT table_id FROM bookings                               │
│      WHERE date = :date AND time = :time                         │
│      AND status = 'confirmed'                                    │
│    )                                                              │
│                                                                   │
│  Returns: {available: bool, table_id: str, slots: [...]}        │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Authentication Check                                    │
│  ────────────────────────────────────────────                    │
│  if not state["is_authenticated"]:                               │
│      # Trigger authentication flow                               │
│      # (Routing-based communication)                             │
│      return route_to_user_agent()                                │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: User Confirmation                                       │
│  ────────────────────────────────────────────                    │
│  Ask: "Shall I confirm your booking for 2 people at 7pm?"       │
│  Wait for user confirmation                                      │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Create Booking                                          │
│  ────────────────────────────────────────────                    │
│  Tool: create_booking(user_id, date, time, party_size, ...)     │
│                                                                   │
│  Database Query:                                                 │
│    INSERT INTO bookings (                                        │
│      user_id, booking_number, date, time,                        │
│      party_size, table_id, status, confirmation_code            │
│    ) VALUES (                                                    │
│      'user_789', 'BOOK-20240115-001', '2024-01-15', '19:00',    │
│      2, 'T5', 'confirmed', 'ABC123'                             │
│    ) RETURNING id;                                               │
│                                                                   │
│  Returns: {booking_id: str, booking_number: str, ...}           │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Send SMS Confirmation                                   │
│  ────────────────────────────────────────────                    │
│  Tool: send_booking_confirmation_sms(phone, booking_details)     │
│                                                                   │
│  SMS Content:                                                    │
│    "Your table for 2 is confirmed on 2024-01-15 at 7pm.         │
│     Booking #BOOK-20240115-001. Confirmation code: ABC123"      │
│                                                                   │
│  Returns: {sms_sent: bool, message_id: str}                     │
└─────────────────────────────────────────────────────────────────┘
```

#### Tools (6 total)

**1. check_table_availability**
```python
@tool
async def check_table_availability(
    date: str,
    time: str,
    party_size: int
) -> Dict[str, Any]
```
**Returns**:
```python
{
    "available": True,
    "table_id": "T5",
    "table_number": 5,
    "capacity": 4,
    "available_slots": ["18:00", "18:30", "19:00", "19:30"]
}
```

**2. create_booking**
```python
@tool
async def create_booking(
    user_id: str,
    date: str,
    time: str,
    party_size: int,
    special_requests: Optional[str] = None
) -> Dict[str, Any]
```
**Returns**:
```python
{
    "success": True,
    "booking_id": "book_abc123",
    "booking_number": "BOOK-20240115-001",
    "confirmation_code": "ABC123",
    "table_id": "T5",
    "table_number": 5
}
```

**3. get_booking_details**
```python
@tool
async def get_booking_details(booking_id: str) -> Dict[str, Any]
```

**4. modify_booking**
```python
@tool
async def modify_booking(
    booking_id: str,
    new_date: Optional[str] = None,
    new_time: Optional[str] = None,
    new_party_size: Optional[int] = None
) -> Dict[str, Any]
```

**5. cancel_booking**
```python
@tool
async def cancel_booking(
    booking_id: str,
    reason: Optional[str] = None
) -> Dict[str, Any]
```

**6. send_booking_confirmation_sms**
```python
@tool
async def send_booking_confirmation_sms(
    phone: str,
    booking_details: Dict[str, Any]
) -> Dict[str, Any]
```

#### Input Fields

```python
state["messages"]                  # Conversation history
state["task_entities"]             # Booking details being collected
state["user_id"]                   # Required for booking
state["user_phone"]                # For SMS confirmation
state["is_authenticated"]          # Auth check
```

#### Output Fields

```python
state["action_result"] = {
    "action": "booking_confirmed",
    "success": True,
    "data": {
        "booking_id": "book_123",
        "booking_number": "BOOK-20240115-001",
        "date": "2024-01-15",
        "time": "19:00",
        "party_size": 2,
        "table_number": 5,
        "confirmation_code": "ABC123"
    }
}

state["task_entities"]["booking_progress"] = {
    "party_size": 2,
    "date": "2024-01-15",
    "time": "19:00",
    "availability_checked": True,
    "user_confirmed": True,
    "booking_created": True,
    "booking_id": "book_123",
    "sms_sent": True
}
```

#### Storage Locations

| Data | Storage | Purpose |
|------|---------|---------|
| Bookings | PostgreSQL `bookings` table | Permanent booking records |
| Tables | PostgreSQL `tables` table | Table availability data |
| Booking progress | `state["task_entities"]["booking_progress"]` | Multi-turn state tracking |

---

### Agent 3: user_agent (Authentication Agent)

**Location**: `app/agents/user/node.py`

**Type**: Autonomous agent (standalone or nested)

**Purpose**: Handle user authentication via OTP

#### What It Does

```
┌─────────────────────────────────────────────────────────────────┐
│  USER AGENT (AUTHENTICATION FLOW)                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Phone Number Collection                                 │
│  ────────────────────────────────────────                        │
│  Agent: "What's your mobile number?"                             │
│  User: "9876543210"                                              │
│                                                                   │
│  Storage: state["phone_number"] = "9876543210"                   │
│           state["authentication_step"] = "phone_collection"      │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Check User Exists                                       │
│  ────────────────────────────────────────                        │
│  Tool: check_user_exists(phone_number="9876543210")              │
│                                                                   │
│  Database Query:                                                 │
│    SELECT id, phone, full_name, email                            │
│    FROM users                                                    │
│    WHERE phone = '9876543210';                                   │
│                                                                   │
│  Returns: {exists: bool, user: {...}}                           │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Send OTP                                                │
│  ────────────────────────────────────────                        │
│  Tool: send_otp(phone_number="9876543210")                       │
│                                                                   │
│  Database Query:                                                 │
│    INSERT INTO otp_codes (                                       │
│      phone, code, expires_at, is_used                           │
│    ) VALUES (                                                    │
│      '9876543210', '123456',                                     │
│      NOW() + INTERVAL '5 minutes', false                        │
│    ) RETURNING id;                                               │
│                                                                   │
│  SMS API Call:                                                   │
│    Send SMS: "Your OTP is 123456. Valid for 5 minutes."         │
│                                                                   │
│  Storage: state["pending_otp_id"] = "otp_abc"                    │
│           state["authentication_step"] = "otp_sent"              │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Verify OTP                                              │
│  ────────────────────────────────────────                        │
│  User: "123456"                                                  │
│                                                                   │
│  Tool: verify_otp(otp_id="otp_abc", code="123456")              │
│                                                                   │
│  Database Query:                                                 │
│    SELECT * FROM otp_codes                                       │
│    WHERE id = 'otp_abc'                                          │
│    AND code = '123456'                                           │
│    AND expires_at > NOW()                                        │
│    AND is_used = false;                                          │
│                                                                   │
│  If valid:                                                       │
│    UPDATE otp_codes SET is_used = true WHERE id = 'otp_abc';    │
│                                                                   │
│  Returns: {valid: bool, user_id: str, user_data: {...}}         │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Generate Session Token                                  │
│  ────────────────────────────────────────────                    │
│  Tool: authenticate_user(phone_number="9876543210")              │
│                                                                   │
│  JWT Generation:                                                 │
│    session_token = jwt.encode({                                  │
│      "user_id": "user_789",                                      │
│      "phone": "9876543210",                                      │
│      "exp": now + 30 days                                        │
│    })                                                             │
│                                                                   │
│  Database Query:                                                 │
│    INSERT INTO user_devices (                                    │
│      user_id, device_id, session_token, last_seen               │
│    ) VALUES (                                                    │
│      'user_789', 'device_xyz', session_token, NOW()             │
│    );                                                             │
│                                                                   │
│  Returns: {                                                      │
│    authenticated: True,                                          │
│    user_id: "user_789",                                          │
│    session_token: "eyJhbGc...",                                  │
│    user_data: {...}                                              │
│  }                                                                │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Migrate Device Data (If Applicable)                     │
│  ────────────────────────────────────────────                    │
│  Tool: migrate_device_data_to_user(                              │
│      device_id="device_xyz",                                     │
│      user_id="user_789"                                          │
│  )                                                                │
│                                                                   │
│  MongoDB Query:                                                  │
│    db.carts.updateOne(                                           │
│      {session_id: "sess_abc123"},                                │
│      {$set: {user_id: "user_789"}}                               │
│    )                                                              │
│                                                                   │
│  Returns: {migrated_items: 2, cart_items: [...]}                │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 7: Update Global Auth State                                │
│  ────────────────────────────────────────                        │
│  state["is_authenticated"] = True                                │
│  state["auth_tier"] = 2                                          │
│  state["user_id"] = "user_789"                                   │
│  state["user_phone"] = "9876543210"                              │
│  state["user_name"] = "Jeswin Kumar"                             │
│  state["session_token"] = "eyJhbGc..."                           │
│  state["authentication_step"] = "completed"                      │
└─────────────────────────────────────────────────────────────────┘
```

#### Tools (8 total)

**1. check_user_exists**
```python
@tool
async def check_user_exists(phone_number: str) -> Dict[str, Any]
```

**2. send_otp**
```python
@tool
async def send_otp(phone_number: str) -> Dict[str, Any]
```

**3. verify_otp**
```python
@tool
async def verify_otp(otp_id: str, code: str) -> Dict[str, Any]
```

**4. create_user**
```python
@tool
async def create_user(
    phone_number: str,
    full_name: str,
    device_id: Optional[str] = None,
    email: Optional[str] = None
) -> Dict[str, Any]
```

**5. authenticate_user**
```python
@tool
async def authenticate_user(phone_number: str) -> Dict[str, Any]
```

**6. get_active_sessions**
```python
@tool
async def get_active_sessions(user_id: str) -> Dict[str, Any]
```

**7. revoke_session**
```python
@tool
async def revoke_session(user_id: str, device_id: str) -> Dict[str, Any]
```

**8. migrate_device_data_to_user**
```python
@tool
async def migrate_device_data_to_user(
    device_id: str,
    user_id: str
) -> Dict[str, Any]
```

#### Input Fields

```python
state["messages"]                  # User's phone/OTP messages
state["authentication_step"]       # Current auth step
state["pending_otp_id"]           # OTP ID for verification
state["phone_number"]              # Collected phone
state["device_id"]                 # Device fingerprint
state["original_intent_agent"]     # Agent that triggered auth
```

#### Output Fields (Global State Updates)

```python
# These affect ALL agents
state["is_authenticated"] = True
state["auth_tier"] = 2
state["user_id"] = "user_789"
state["user_phone"] = "9876543210"
state["user_name"] = "Jeswin Kumar"
state["session_token"] = "eyJhbGc..."
state["authentication_step"] = "completed"

# For routing back
state["original_intent_agent"] = None  # Cleared after auth
```

#### Storage Locations

| Data | Storage | Purpose |
|------|---------|---------|
| Users | PostgreSQL `users` table | User accounts |
| OTP codes | PostgreSQL `otp_codes` table | OTP verification |
| Sessions | PostgreSQL `user_devices` table | Device-user linking |
| Session tokens | JWT (30-day expiry) | Authentication |

---

### Agent 4: payment_agent (Autonomous Sub-Graph)

**Location**: `app/agents/payment/node.py`

**Purpose**: Handle payment processing via Razorpay

#### Tools (4 total)

**1. create_payment_link**
```python
@tool
async def create_payment_link(order_id: str) -> Dict[str, Any]
```
**Returns**:
```python
{
    "success": True,
    "payment_link": "https://rzp.io/i/abc123",
    "payment_id": "pay_xyz789",
    "amount": 412.99,
    "currency": "INR"
}
```

**2. check_payment_status**
```python
@tool
async def check_payment_status(payment_id: str) -> Dict[str, Any]
```

**3. verify_payment_signature**
```python
@tool
async def verify_payment_signature(
    order_id: str,
    payment_id: str,
    signature: str
) -> Dict[str, Any]
```

**4. get_order_amount**
```python
@tool
async def get_order_amount(order_id: str) -> Dict[str, Any]
```

---

### Agent 5: customer_satisfaction_agent

**Location**: `app/agents/customer_satisfaction/node.py`

**Purpose**: Handle complaints, feedback, and satisfaction surveys

#### Tools (3 total)

**1. create_complaint_ticket**
```python
@tool
async def create_complaint_ticket(
    user_id: str,
    complaint_text: str,
    category: str,
    severity: str
) -> Dict[str, Any]
```

**2. log_feedback**
```python
@tool
async def log_feedback(
    user_id: str,
    feedback_text: str,
    rating: int,
    order_id: Optional[str] = None
) -> Dict[str, Any]
```

**3. send_management_alert**
```python
@tool
async def send_management_alert(
    ticket_id: str,
    severity: str,
    complaint_summary: str
) -> Dict[str, Any]
```

---

### Agent 6: general_queries_agent

**Location**: `app/agents/general_queries/node.py`

**Purpose**: Answer FAQs and general questions about the restaurant

#### Tools (2 total)

**1. get_restaurant_info**
```python
@tool
async def get_restaurant_info(info_type: str) -> Dict[str, Any]
```

**2. search_faq**
```python
@tool
async def search_faq(question: str) -> Dict[str, Any]
```

---

### Agent 7: support_agent

**Location**: `app/agents/support/node.py`

**Purpose**: Handle technical support requests

#### Tools (2 total)

**1. create_support_ticket**
```python
@tool
async def create_support_ticket(
    user_id: str,
    issue_description: str,
    priority: str
) -> Dict[str, Any]
```

**2. escalate_to_human_support**
```python
@tool
async def escalate_to_human_support(
    ticket_id: str,
    reason: str
) -> Dict[str, Any]
```

---

### Agent 8: response_agent (Virtual Waiter Formatter)

**Location**: `app/agents/response/node.py`

**Type**: Formatting layer (NOT business logic)

**Purpose**: Format all agent responses with hospitality tone

#### What It Does

```
Input: ActionResult from specialist agent
  ↓
Format with LLM:
  - Add warm, casual tone
  - Add personalization (use customer name)
  - Add upselling suggestions
  - Apply restaurant personality
  ↓
Output: Friendly conversational text
```

#### Input Fields

```python
state["action_result"]     # Structured data from specialist agent
state["user_memory"]       # User preferences for personalization
state["task_entities"]     # Context for suggestions
state["user_name"]         # For personalization
```

#### Output Fields

```python
state["agent_response"] = "Formatted friendly text"
state["messages"] = [AIMessage(content="Formatted friendly text")]
```

---

## Communication Pattern 1: Routing-Based (Auth Handoff)

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  ROUTING-BASED COMMUNICATION (AUTH HANDOFF)                      │
└─────────────────────────────────────────────────────────────────┘

User wants transactional operation (checkout, booking)
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  ROUTER NODE                                                     │
│  ────────────────────                                            │
│  1. Maps intent to agent                                         │
│  2. Checks authentication requirement                            │
│  3. If auth required:                                            │
│     • selected_agent = "user_agent"                              │
│     • original_intent_agent = "food_ordering_agent" (SAVED)      │
│  4. Routes to user_agent                                         │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  USER AGENT (Authentication Flow)                                │
│  ────────────────────────────────────                            │
│  Multi-turn authentication:                                      │
│    Turn 1: Collect phone number                                  │
│    Turn 2: Send OTP                                              │
│    Turn 3: Verify OTP                                            │
│                                                                   │
│  Updates global state:                                           │
│    is_authenticated = True                                       │
│    user_id = "user_789"                                          │
│    user_phone = "9876543210"                                     │
│                                                                   │
│  CRITICAL: task_entities preserved throughout                    │
│    cart_items = [...]  ← NOT LOST                               │
│    cart_subtotal = 400.00  ← NOT LOST                           │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  ROUTE_AFTER_USER_AGENT (Conditional Edge)                       │
│  ────────────────────────────────────────────                    │
│  Checks: original_intent_agent field                             │
│                                                                   │
│  if original_intent_agent exists:                                │
│      route_to(original_intent_agent)  # Resume original agent    │
│  else:                                                            │
│      route_to(END)  # Standalone auth request                    │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  FOOD ORDERING AGENT (Resumed)                                   │
│  ────────────────────────────────────────────                    │
│  Now has:                                                        │
│    ✓ is_authenticated = True                                     │
│    ✓ user_id = "user_789"                                        │
│    ✓ cart_items = [...]  (preserved)                            │
│    ✓ cart_subtotal = 400.00  (preserved)                        │
│                                                                   │
│  Can proceed with checkout                                       │
└─────────────────────────────────────────────────────────────────┘
```

### State Fields Used

```python
# Set by router_node when auth required
state["selected_agent"] = "user_agent"
state["original_intent_agent"] = "food_ordering_agent"  # KEY FIELD

# Cleared by route_after_user_agent when auth complete
state["original_intent_agent"] = None
```

### Graph Configuration

**Location**: `app/orchestration/graph.py`

```python
# Conditional edge from user_agent
workflow.add_conditional_edges(
    "user_agent",
    route_after_user_agent,
    {
        "booking_agent": "booking_agent",
        "food_ordering_agent": "food_ordering_agent",
        "payment_agent": "payment_agent",
        # ... other agents
        END: "response_agent"  # Standalone auth
    }
)

# Routing function
def route_after_user_agent(state: AgentState) -> str:
    """Route back to original agent after auth."""
    original_agent = state.get("original_intent_agent")

    if original_agent:
        return original_agent  # Resume

    return END  # Standalone
```

### Data Preservation

```
BEFORE AUTH:
────────────
state["task_entities"] = {
    "cart_items": [
        {"name": "Butter Chicken", "quantity": 1, "price": 350.00},
        {"name": "Garlic Naan", "quantity": 1, "price": 50.00}
    ],
    "cart_subtotal": 400.00
}
state["original_intent_agent"] = "food_ordering_agent"

DURING AUTH (3 turns):
──────────────────────
# State preserved in checkpoint
state["task_entities"]["cart_items"] = [...]  ← STILL THERE
state["task_entities"]["cart_subtotal"] = 400.00  ← STILL THERE
state["original_intent_agent"] = "food_ordering_agent"  ← STILL THERE

# New auth data added
state["authentication_step"] = "otp_sent"
state["phone_number"] = "9876543210"
state["pending_otp_id"] = "otp_abc"

AFTER AUTH:
───────────
# Cart data preserved
state["task_entities"]["cart_items"] = [...]  ← STILL THERE

# Auth data added
state["is_authenticated"] = True
state["user_id"] = "user_789"
state["user_phone"] = "9876543210"

# Routing cleared
state["original_intent_agent"] = None
```

---

## Communication Pattern 2: Delegation Protocol

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  DELEGATION PROTOCOL (STACK-BASED)                               │
└─────────────────────────────────────────────────────────────────┘

Agent A needs functionality from Agent B
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  AGENT A: Initiate Delegation                                    │
│  ────────────────────────────────────                            │
│  from app.orchestration.agent_communication import              │
│      AgentCommunicator                                           │
│                                                                   │
│  delegation = AgentCommunicator.delegate(                        │
│      state=state,                                                │
│      from_agent="booking_agent",                                 │
│      to_agent="authentication_agent",                            │
│      task="authenticate_user_for_booking",                       │
│      context={                                                   │
│          "purpose": "booking_confirmation",                      │
│          "booking_details": {"party_size": 2, ...}               │
│      }                                                            │
│  )                                                                │
│                                                                   │
│  State updates:                                                  │
│    delegation_stack = ["booking_agent"]  ← PUSHED                │
│    delegation_context = {                                        │
│        "task": "authenticate_user_for_booking",                  │
│        "from_agent": "booking_agent",                            │
│        "to_agent": "authentication_agent",                       │
│        "purpose": "booking_confirmation",                        │
│        "booking_details": {...}                                  │
│    }                                                              │
│    current_delegator = "booking_agent"                           │
│    selected_agent = "authentication_agent"                       │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  AGENT B: Handle Delegated Task                                  │
│  ────────────────────────────────────────────                    │
│  # Check if this is a delegation                                 │
│  if AgentCommunicator.is_delegation(state):                      │
│      context = AgentCommunicator.get_delegation_context(state)   │
│      task = context.get("task")                                  │
│      purpose = context.get("purpose")                            │
│      booking_details = context.get("booking_details")            │
│                                                                   │
│      # Perform authentication                                    │
│      auth_result = perform_authentication(state)                 │
│                                                                   │
│      # Return result to delegator                                │
│      return_updates = AgentCommunicator.return_from_delegation(  │
│          state=state,                                            │
│          result={                                                │
│              "user_id": "user_789",                              │
│              "user_phone": "9876543210",                         │
│              "authenticated": True                               │
│          }                                                        │
│      )                                                            │
│                                                                   │
│      State updates:                                              │
│        delegation_stack = []  ← POPPED                           │
│        delegation_result = {                                     │
│            "user_id": "user_789",                                │
│            "user_phone": "9876543210",                           │
│            "authenticated": True                                 │
│        }                                                          │
│        delegation_context = {}  ← CLEARED                        │
│        selected_agent = "booking_agent"  ← ROUTE BACK            │
└────────────────────────┬────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────────────────────────┐
│  AGENT A: Receive Result                                         │
│  ────────────────────────────────────────────                    │
│  # Check for delegation result                                   │
│  delegation_result = state.get("delegation_result")              │
│                                                                   │
│  if delegation_result:                                           │
│      user_id = delegation_result.get("user_id")                  │
│      user_phone = delegation_result.get("user_phone")            │
│                                                                   │
│      # Use auth result to continue                               │
│      return create_booking(state, user_id)                       │
│                                                                   │
│      # Clear result (consumed)                                   │
│      state["delegation_result"] = None                           │
└─────────────────────────────────────────────────────────────────┘
```

### State Fields Used

```python
# Delegation tracking
state["delegation_stack"]: List[str]          # Stack of delegating agents
state["delegation_context"]: Dict[str, Any]   # Context passed to target
state["delegation_result"]: Optional[Dict]    # Result from target agent
state["current_delegator"]: Optional[str]     # Current delegator
```

### AgentCommunicator API

**Location**: `app/orchestration/agent_communication.py`

```python
class AgentCommunicator:
    """Helper class for inter-agent communication"""

    @staticmethod
    def delegate(
        state: AgentState,
        from_agent: str,
        to_agent: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare state for agent delegation.

        Returns state updates to merge.
        """

    @staticmethod
    def return_from_delegation(
        state: AgentState,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Return result to delegating agent.

        Returns state updates to merge.
        """

    @staticmethod
    def is_delegation(state: AgentState) -> bool:
        """Check if current execution is a delegation."""

    @staticmethod
    def get_delegation_context(state: AgentState) -> Dict[str, Any]:
        """Get delegation context for current execution."""

    @staticmethod
    def get_delegation_depth(state: AgentState) -> int:
        """Get current delegation depth (how many levels deep)."""

    @staticmethod
    def clear_delegation(state: AgentState) -> Dict[str, Any]:
        """Clear all delegation state (error recovery)."""
```

### Nested Delegation Example

```
Agent A → Agent B → Agent C

STEP 1: A delegates to B
────────────────────────
delegation_stack: ["agent_a"]
delegation_context: {from_agent: "agent_a", to_agent: "agent_b"}
current_delegator: "agent_a"

STEP 2: B delegates to C (nested)
──────────────────────────────────
delegation_stack: ["agent_a", "agent_b"]  ← STACKED
delegation_context: {from_agent: "agent_b", to_agent: "agent_c"}
current_delegator: "agent_b"

STEP 3: C completes, returns to B
───────────────────────────────────
delegation_stack: ["agent_a"]  ← Popped "agent_b"
delegation_result: {result from C}
current_delegator: "agent_a"
selected_agent: "agent_b"  ← Route back to B

STEP 4: B completes, returns to A
───────────────────────────────────
delegation_stack: []  ← Popped "agent_a"
delegation_result: {result from B}
current_delegator: None
selected_agent: "agent_a"  ← Route back to A

STEP 5: A receives result, continues
──────────────────────────────────────
delegation_result: {result from B}
No delegation active
```

### Convenience Functions

```python
# Delegate to authentication agent
from app.orchestration.agent_communication import delegate_to_auth

updates = delegate_to_auth(
    state=state,
    from_agent="booking_agent",
    purpose="booking_confirmation",
    booking_id="book_123"
)

# Delegate to user profile agent
from app.orchestration.agent_communication import delegate_to_user_profile

updates = delegate_to_user_profile(
    state=state,
    from_agent="order_agent",
    task="get_dietary_preferences",
    user_id=state.get("user_id")
)
```

---

## Complete Flow Examples with Storage Tracking

### Example 1: Checkout Flow with Auth Handoff

```
┌─────────────────────────────────────────────────────────────────┐
│  COMPLETE CHECKOUT FLOW WITH AUTHENTICATION                      │
└─────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════
TURN 1: User adds item to cart
═══════════════════════════════════════════════════════════════════

USER INPUT:
───────────
"I want butter chicken"

GRAPH EXECUTION:
────────────────
auth_node → perceive_node → task_manager_node → validation_node →
router_node → food_ordering_agent → response_agent → END

STORAGE AT EACH STEP:
─────────────────────

After perceive_node:
  state["current_intent"] = "order_request"
  state["extracted_entities"] = {"item_name": "butter chicken"}

After task_manager_node:
  state["task_entities"] = {
      "item_name": "butter chicken"
  }

After food_ordering_agent:
  # Sub-intent: manage_cart, action: add
  # Database writes:
  PostgreSQL:
    SELECT * FROM menu_items WHERE name ILIKE '%butter chicken%';
    → Returns: {item_id: "123", price: 350.00}

  Redis:
    HGET inventory:123 available_quantity
    → Returns: 50
    HINCRBY inventory:123 reserved_quantity 1
    SET reservation:sess_abc123:123 1 EX 900

  MongoDB:
    db.carts.updateOne(
      {session_id: "sess_abc123"},
      {$push: {items: {item_id: "123", name: "Butter Chicken", ...}},
       $inc: {subtotal: 350.00}},
      {upsert: true}
    )

  state["task_entities"] = {
      "cart_items": [
          {"item_id": "123", "name": "Butter Chicken", "quantity": 1, "price": 350.00}
      ],
      "cart_subtotal": 350.00
  }
  state["action_result"] = {
      "action": "item_added_to_cart",
      "success": True,
      "data": {...}
  }

After response_agent:
  state["agent_response"] = "Great choice! Added Butter Chicken to your cart (₹350)."
  state["messages"].append(AIMessage("Great choice!..."))

CHECKPOINT SAVED:
─────────────────
MemorySaver["sess_abc123"] = {
    "session_id": "sess_abc123",
    "messages": [
        HumanMessage("I want butter chicken"),
        AIMessage("Great choice! Added Butter Chicken...")
    ],
    "task_entities": {
        "cart_items": [...],
        "cart_subtotal": 350.00
    },
    "is_authenticated": False,
    "user_id": None
}

═══════════════════════════════════════════════════════════════════
TURN 2: User attempts checkout
═══════════════════════════════════════════════════════════════════

USER INPUT:
───────────
"Checkout"

STATE LOADED:
─────────────
From MemorySaver["sess_abc123"]:
  task_entities = {"cart_items": [...], "cart_subtotal": 350.00}
  is_authenticated = False
  user_id = None

GRAPH EXECUTION:
────────────────
auth_node → perceive_node → task_manager_node → validation_node →
router_node (AUTH REQUIRED!) → user_agent → END

STORAGE AT EACH STEP:
─────────────────────

After router_node:
  # Auth check logic:
  agent = "food_ordering_agent"
  cart_items = state["task_entities"]["cart_items"]  # Has items
  is_authenticated = False  # Not authenticated

  # AUTH REQUIRED!
  state["selected_agent"] = "user_agent"
  state["original_intent_agent"] = "food_ordering_agent"  ← KEY!

After user_agent:
  state["agent_response"] = "To complete your order, I'll need your phone number..."
  state["authentication_step"] = "phone_collection"

  # CRITICAL: Cart preserved
  state["task_entities"]["cart_items"] = [...]  ← STILL THERE
  state["original_intent_agent"] = "food_ordering_agent"  ← STILL SAVED

CHECKPOINT SAVED:
─────────────────
MemorySaver["sess_abc123"] = {
    "messages": [...],
    "task_entities": {
        "cart_items": [...],  ← PRESERVED
        "cart_subtotal": 350.00  ← PRESERVED
    },
    "authentication_step": "phone_collection",
    "original_intent_agent": "food_ordering_agent",  ← PRESERVED
    "is_authenticated": False
}

═══════════════════════════════════════════════════════════════════
TURN 3: User provides phone
═══════════════════════════════════════════════════════════════════

USER INPUT:
───────────
"9876543210"

STATE LOADED:
─────────────
From checkpoint:
  authentication_step = "phone_collection"
  task_entities = {"cart_items": [...], "cart_subtotal": 350.00}
  original_intent_agent = "food_ordering_agent"

GRAPH EXECUTION:
────────────────
auth_node → user_agent → END

STORAGE AT EACH STEP:
─────────────────────

In user_agent:
  # Tool call: check_user_exists
  Database query:
    SELECT * FROM users WHERE phone = '9876543210';
    → Returns: {user_id: "user_789", full_name: "Jeswin Kumar"}

  # Tool call: send_otp
  Database query:
    INSERT INTO otp_codes (phone, code, expires_at)
    VALUES ('9876543210', '123456', NOW() + INTERVAL '5 minutes')
    RETURNING id;
    → Returns: otp_id = "otp_abc"

  SMS sent: "Your OTP is 123456"

  state["authentication_step"] = "otp_sent"
  state["phone_number"] = "9876543210"
  state["pending_otp_id"] = "otp_abc"

  # Cart STILL preserved
  state["task_entities"]["cart_items"] = [...]  ← STILL THERE
  state["original_intent_agent"] = "food_ordering_agent"  ← STILL SAVED

CHECKPOINT SAVED:
─────────────────
MemorySaver["sess_abc123"] = {
    "authentication_step": "otp_sent",
    "phone_number": "9876543210",
    "pending_otp_id": "otp_abc",
    "task_entities": {
        "cart_items": [...],  ← STILL PRESERVED
        "cart_subtotal": 350.00
    },
    "original_intent_agent": "food_ordering_agent"  ← STILL PRESERVED
}

═══════════════════════════════════════════════════════════════════
TURN 4: User provides OTP
═══════════════════════════════════════════════════════════════════

USER INPUT:
───────────
"123456"

STATE LOADED:
─────────────
From checkpoint:
  authentication_step = "otp_sent"
  pending_otp_id = "otp_abc"
  task_entities = {"cart_items": [...]}
  original_intent_agent = "food_ordering_agent"

GRAPH EXECUTION:
────────────────
auth_node → user_agent → route_after_user_agent → food_ordering_agent →
response_agent → END

STORAGE AT EACH STEP:
─────────────────────

In user_agent:
  # Tool call: verify_otp
  Database query:
    SELECT * FROM otp_codes
    WHERE id = 'otp_abc' AND code = '123456'
    AND expires_at > NOW() AND is_used = false;
    → Valid!

    UPDATE otp_codes SET is_used = true WHERE id = 'otp_abc';

  # Tool call: authenticate_user
  session_token = jwt.encode({
      "user_id": "user_789",
      "phone": "9876543210",
      "exp": now + 30 days
  })

  Database query:
    INSERT INTO user_devices (user_id, device_id, session_token)
    VALUES ('user_789', 'device_xyz', session_token);

  # Tool call: migrate_device_data_to_user
  MongoDB query:
    db.carts.updateOne(
      {session_id: "sess_abc123"},
      {$set: {user_id: "user_789"}}
    )

  # GLOBAL AUTH STATE UPDATED
  state["is_authenticated"] = True
  state["auth_tier"] = 2
  state["user_id"] = "user_789"
  state["user_phone"] = "9876543210"
  state["user_name"] = "Jeswin Kumar"
  state["session_token"] = "eyJhbGc..."
  state["authentication_step"] = "completed"

  # Cart STILL preserved
  state["task_entities"]["cart_items"] = [...]  ← STILL THERE

After route_after_user_agent:
  original_agent = state["original_intent_agent"]  # "food_ordering_agent"
  → Route to "food_ordering_agent"

  state["original_intent_agent"] = None  ← CLEARED

In food_ordering_agent:
  # Sub-intent: execute_checkout
  # Now has user_id and cart_items!

  # Create order
  Database query:
    INSERT INTO orders (user_id, order_number, total_amount, status)
    VALUES ('user_789', 'ORD-20240115-001', 412.99, 'pending')
    RETURNING id;
    → order_id = "ord_abc456"

  # Create order items
  Database query:
    INSERT INTO order_items (order_id, menu_item_id, quantity, price)
    VALUES ('ord_abc456', '123', 1, 350.00);

  # Generate payment link
  Razorpay API:
    create_payment_link(amount=41299, order_id="ord_abc456")
    → payment_link = "https://rzp.io/i/payment123"

  # Clear cart
  MongoDB query:
    db.carts.deleteOne({session_id: "sess_abc123"})

  # Confirm inventory
  Redis:
    HINCRBY inventory:123 available_quantity -1
    HINCRBY inventory:123 reserved_quantity -1
    DEL reservation:sess_abc123:123

  state["action_result"] = {
      "action": "order_placed",
      "success": True,
      "data": {
          "order_id": "ord_abc456",
          "order_number": "ORD-20240115-001",
          "total_amount": 412.99,
          "payment_link": "https://rzp.io/i/payment123"
      }
  }
  state["task_entities"]["cart_items"] = []  ← CLEARED
  state["task_entities"]["order_id"] = "ord_abc456"

After response_agent:
  state["agent_response"] = "Awesome, Jeswin! Your order #ORD-20240115-001 is confirmed..."

FINAL CHECKPOINT:
─────────────────
MemorySaver["sess_abc123"] = {
    "is_authenticated": True,
    "user_id": "user_789",
    "user_phone": "9876543210",
    "session_token": "eyJhbGc...",
    "task_entities": {
        "cart_items": [],
        "cart_subtotal": 0.0,
        "order_id": "ord_abc456",
        "order_number": "ORD-20240115-001"
    },
    "action_result": {...},
    "agent_response": "Awesome, Jeswin!..."
}

RESPONSE TO USER:
─────────────────
"Awesome, Jeswin! Your order #ORD-20240115-001 is confirmed for ₹412.99. Here's your payment link: https://rzp.io/i/payment123. Looking forward to serving you!"
```

---

## Data Storage Architecture

### State Storage (Temporary)

```
┌─────────────────────────────────────────────────────────────────┐
│  STATE STORAGE (TEMPORARY - CONVERSATION LIFETIME)               │
└─────────────────────────────────────────────────────────────────┘

LOCATION: MemorySaver (in-memory)
KEY: session_id
LIFETIME: Server uptime (lost on restart)

STRUCTURE:
{
    "session_id": "sess_abc123",
    "messages": [...],                  # Full conversation history
    "task_entities": {...},             # Current task data
    "is_authenticated": bool,           # Auth status
    "user_id": str,                     # User identifier
    "cart_items": [...],                # Current cart
    "action_result": {...},             # Latest agent output
    "agent_response": str,              # Latest formatted response
    "original_intent_agent": str,       # For auth handoff
    "delegation_stack": [...],          # For delegation protocol
    // ... all AgentState fields
}
```

### Database Storage (Permanent)

```
┌─────────────────────────────────────────────────────────────────┐
│  POSTGRESQL (PERMANENT RECORDS)                                  │
└─────────────────────────────────────────────────────────────────┘

TABLES:

1. users
   ├─ id (PK)
   ├─ phone (unique)
   ├─ full_name
   ├─ email
   ├─ is_anonymous
   └─ created_at

2. orders
   ├─ id (PK)
   ├─ user_id (FK → users.id)
   ├─ order_number (unique)
   ├─ total_amount
   ├─ status (pending, confirmed, completed, cancelled)
   ├─ order_type (dine_in, takeout, delivery)
   └─ created_at

3. order_items
   ├─ id (PK)
   ├─ order_id (FK → orders.id)
   ├─ menu_item_id (FK → menu_items.id)
   ├─ quantity
   └─ price

4. bookings
   ├─ id (PK)
   ├─ user_id (FK → users.id)
   ├─ booking_number (unique)
   ├─ date
   ├─ time
   ├─ party_size
   ├─ table_id (FK → tables.id)
   ├─ status
   ├─ confirmation_code
   └─ created_at

5. otp_codes
   ├─ id (PK)
   ├─ phone
   ├─ code
   ├─ expires_at
   ├─ is_used
   └─ created_at

6. user_devices
   ├─ id (PK)
   ├─ user_id (FK → users.id)
   ├─ device_id
   ├─ session_token
   └─ last_seen

┌─────────────────────────────────────────────────────────────────┐
│  MONGODB (DOCUMENT STORAGE)                                      │
└─────────────────────────────────────────────────────────────────┘

COLLECTIONS:

1. carts
   {
       session_id: "sess_abc123",
       user_id: "user_789",  // Null for anonymous
       items: [
           {
               item_id: "123",
               name: "Butter Chicken",
               quantity: 1,
               price: 350.00,
               added_at: ISODate(...)
           }
       ],
       subtotal: 350.00,
       created_at: ISODate(...),
       updated_at: ISODate(...)
   }

┌─────────────────────────────────────────────────────────────────┐
│  REDIS (CACHING & RATE LIMITING)                                 │
└─────────────────────────────────────────────────────────────────┘

KEYS:

1. Inventory:
   inventory:123 → {available_quantity: 50, reserved_quantity: 2}

2. Reservations:
   reservation:sess_abc123:123 → 1 (TTL: 900 seconds)

3. Rate Limiting:
   otp_attempts:9876543210 → 3 (TTL: 3600 seconds)
```

---

## State Field Reference

### Communication-Specific Fields

```python
# Routing-Based Communication
state["original_intent_agent"]: Optional[str]
# - Set by: router_node when auth required
# - Used by: route_after_user_agent to resume original agent
# - Cleared: After routing back to original agent
# - Purpose: Enable auth handoff without losing context

# Delegation Protocol
state["delegation_stack"]: List[str]
# - Contains: Stack of delegating agents
# - Example: ["booking_agent", "auth_agent"]
# - Purpose: Track delegation chain for nested delegations

state["delegation_context"]: Dict[str, Any]
# - Contains: Task, from_agent, to_agent, custom context
# - Purpose: Pass information to delegated agent

state["delegation_result"]: Optional[Dict[str, Any]]
# - Contains: Result returned from delegated agent
# - Purpose: Receive data back from delegated agent
# - Note: Must be cleared after consuming

state["current_delegator"]: Optional[str]
# - Contains: Current delegating agent
# - Purpose: Know who initiated current delegation
```

### Agent Output Fields

```python
state["action_result"]: Optional[Dict[str, Any]]
# - Set by: All specialist agents
# - Read by: response_agent for formatting
# - Structure: {action, success, data, context}
# - Purpose: Structured output from business logic

state["agent_response"]: Optional[str]
# - Set by: response_agent (or agents that skip formatting)
# - Read by: HTTP handler for response to user
# - Purpose: Final formatted text response

state["agent_metadata"]: Dict[str, Any]
# - Set by: All agents
# - Contains: Execution details (time, queries, success)
# - Purpose: Analytics and debugging
```

### Authentication Fields

```python
state["is_authenticated"]: bool
# - Set by: user_agent after OTP verification
# - Affects: ALL agents (global state)
# - Purpose: Auth gate for transactional operations

state["user_id"]: Optional[str]
# - Set by: user_agent after authentication
# - Affects: ALL agents (used for database operations)
# - Purpose: User identification

state["authentication_step"]: Optional[str]
# - Set by: user_agent during auth flow
# - Values: "phone_collection", "otp_sent", "otp_verification", "completed"
# - Purpose: Resume auth flow across turns
```

### Task Management Fields

```python
state["task_entities"]: Dict[str, Any]
# - Set by: task_manager_node (merged from extracted_entities)
# - Updated by: Agents during execution
# - Purpose: Accumulate entities across multiple turns
# - CRITICAL: Preserved during auth handoff

state["active_task_type"]: Optional[TaskType]
# - Set by: task_manager_node
# - Purpose: Track current task being executed
```

---

## Best Practices

### For Routing-Based Communication

✅ **DO**:
1. Always check if `original_intent_agent` exists before routing back
2. Preserve `task_entities` during auth flow (don't clear cart!)
3. Clear `original_intent_agent` after routing back
4. Use for simple one-level auth handoffs

❌ **DON'T**:
1. Don't nest multiple routing-based handoffs (use delegation instead)
2. Don't modify task_entities during auth flow
3. Don't forget to set `original_intent_agent` when routing to auth
4. Don't use for complex multi-agent workflows

### For Delegation Protocol

✅ **DO**:
1. Always check `is_delegation()` at start of agent
2. Clear `delegation_result` after consuming
3. Check delegation depth to prevent infinite loops
4. Pass custom context when needed
5. Return structured results

❌ **DON'T**:
1. Don't forget to call `return_from_delegation()` when done
2. Don't leave delegation_result uncleard (will affect next call)
3. Don't exceed depth of 3 (performance + complexity)
4. Don't use for simple auth handoffs (use routing instead)

### For Data Storage

✅ **DO**:
1. Store cart in MongoDB (flexible schema)
2. Store orders in PostgreSQL (ACID transactions)
3. Use Redis for temporary data (inventory reservations, rate limiting)
4. Preserve critical data in `task_entities` during interruptions
5. Save checkpoints after each agent execution

❌ **DON'T**:
1. Don't store sensitive data in state (use database)
2. Don't assume state persists across server restarts (use PostgreSQL for permanent data)
3. Don't store large data in state (use references/IDs)
4. Don't forget to clear transient data after completion

---

## Summary

### Two Communication Patterns

| Feature | Routing-Based | Delegation Protocol |
|---------|--------------|---------------------|
| **Complexity** | Simple | More Complex |
| **Use Case** | Auth handoff | Complex workflows |
| **Nesting** | Single-level | Multi-level |
| **Context Passing** | No | Yes |
| **Result Handling** | No | Yes |
| **Currently Used** | ✅ Yes | ❌ Not yet |

### Key State Fields

- **`original_intent_agent`**: Resume agent after auth (routing-based)
- **`delegation_stack`**: Track delegation chain (delegation protocol)
- **`task_entities`**: Preserved across auth handoff (critical!)
- **`action_result`**: Structured output from agents
- **`agent_response`**: Final formatted text response

### Storage Locations

- **State**: MemorySaver (temporary, in-memory)
- **Permanent records**: PostgreSQL (users, orders, bookings)
- **Carts**: MongoDB (flexible schema)
- **Temporary data**: Redis (inventory, rate limiting)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-15
**Author**: AI Assistant (Claude Code)
**Status**: ✅ Complete
