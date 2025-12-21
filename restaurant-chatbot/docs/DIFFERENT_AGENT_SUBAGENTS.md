# Agent & Sub-Agent Data Flow Reference

**Version:** 1.0
**Last Updated:** 2025-11-13
**Purpose:** Complete reference for each agent's data requirements, database operations, and outputs

---

## System-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              USER MESSAGE INPUT                                  │
└───────────────────────────────┬─────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ Orchestration Engine  │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Task Manager       │
                    │ Intent Classification │
                    └───────────┬───────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   Validation Gate     │
                    │  7 Validation Rules   │
                    └───────┬───────────────┘
                            │
                ┌───────────┴───────────┐
                │ Valid                 │ Invalid
                ▼                       ▼
    ┌───────────────────┐    ┌─────────────────────┐
    │   Agent Router    │    │  response_agent     │
    └─────┬─────────────┘    │ (Skip to formatting)│
          │                  └─────────────────────┘
          │
    ┌─────┴─────┬──────┬──────┬──────┬──────┬──────┬──────┐
    │           │      │      │      │      │      │      │
    ▼           ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌────────┐  ┌─────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
│ FOOD   │  │BOOK │ │PAY │ │USER│ │CSAT│ │SUPP│ │GENQ│ │(skip)
│ORDERING│  │ ING │ │MENT│ │AUTH│ │    │ │ORT │ │    │ │
└───┬────┘  └──┬──┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ └──┬─┘ │
    │          │       │      │      │      │      │      │
    │          │       │      │      │      │      │      │
┌───┴───┐      │       │      │      │      │      │      │
│SUB-   │      │       │      │      │      │      │      │
│AGENTS │      │       │      │      │      │      │      │
└───┬───┘      │       │      │      │      │      │      │
    │          │       │      │      │      │      │      │
┌───┴──────────┴───────┴──────┴──────┴──────┴──────┴──────┴────┐
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  menu_   │  │  menu_   │  │  cart_   │  │ checkout │      │
│  │ browsing │  │discovery │  │management│  │validator │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│                    ┌──────────┐                                │
│                    │ checkout │                                │
│                    │ executor │                                │
│                    └──────────┘                                │
│                                                                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   ActionResult       │
                │  (Structured Data)   │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   response_agent     │
                │  Virtual Waiter      │
                │  Formatter           │
                └──────────┬───────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │  FRIENDLY RESPONSE   │
                │      TO USER         │
                └──────────────────────┘
```

**System Architecture:**
- **1 Orchestrator** → Routes requests to appropriate agents
- **1 Parent Agent** (food_ordering) → 5 Sub-Agents
- **6 Independent Agents** → Specialized functionality
- **1 Response Agent** → Formatting layer (Virtual Waiter)

**Total: 8 Main Agents + 5 Sub-Agents = 13 Agent Nodes**

---

## Table of Contents

1. [food_ordering_agent](#1-food_ordering_agent-parent)
   - [1.1 menu_browsing](#11-sub-agent-menu_browsing)
   - [1.2 menu_discovery](#12-sub-agent-menu_discovery)
   - [1.3 cart_management](#13-sub-agent-cart_management)
   - [1.4 checkout_validator](#14-sub-agent-checkout_validator)
   - [1.5 checkout_executor](#15-sub-agent-checkout_executor)
2. [booking_agent](#2-booking_agent)
3. [payment_agent](#3-payment_agent)
4. [user_agent](#4-user_agent)
5. [customer_satisfaction_agent](#5-customer_satisfaction_agent)
6. [support_agent](#6-support_agent)
7. [general_queries_agent](#7-general_queries_agent)
8. [response_agent](#8-response_agent)

---

## 1. food_ordering_agent (Parent)

### Purpose
Coordinate food ordering workflow - acts as entry point and routes to correct sub-agent

### Use Cases
- Any food ordering related request
- Menu browsing, searching, cart operations, checkout

### Input Required
```python
{
    "user_message": str,              # e.g., "Add butter chicken"
    "session_id": str,                # "abc123"
    "user_id": Optional[str],         # "usr456" (if authenticated)
    "state": AgentState               # Full conversation context
}
```

### Database Tables Accessed
**NONE** - Parent agent doesn't access database directly. Only performs:
1. Sub-intent classification (LLM call)
2. Guardrails validation
3. Entity validation
4. Routing to sub-agent

### Processing Flow
```
Input → classify_sub_intent() → apply_guardrails() → validate_entities() → route_to_agent() → Sub-agent
```

### Flow Diagram

```
                        ┌─────────────────────┐
                        │   USER MESSAGE      │
                        │ "Add butter chicken"│
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │  LLM: Classify      │
                        │  Sub-Intent         │
                        └──────────┬──────────┘
                                   │
        ┌──────────────┬───────────┼───────────┬───────────┐
        │              │           │           │           │
        ▼              ▼           ▼           ▼           ▼
  browse_menu    discover_items  manage_cart  validate   execute
                                              _order    _checkout
        │              │           │           │           │
        ▼              ▼           ▼           ▼           ▼
┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
│ Sub-Agent:   │ │Sub-Agent:│ │Sub-Agent:│ │Sub-Agent:│ │Sub-Agent:│
│    menu_     │ │   menu_  │ │   cart_  │ │ checkout │ │ checkout │
│  browsing    │ │ discovery│ │management│ │validator │ │ executor │
└──────┬───────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘ └─────┬────┘
       │               │            │            │            │
       └───────────────┴────────────┴────────────┴────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Return ActionResult │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  To Response Agent   │
                        └──────────────────────┘
```

**Sub-Intent Classification Logic:**
- `browse_menu`: "show menu", "what categories", "what's in appetizers"
- `discover_items`: "vegetarian options", "spicy food", "butter chicken", "recommend something"
- `manage_cart`: "add butter chicken", "remove item 2", "change quantity", "show cart"
- `validate_order`: "checkout", "I'm ready to order", "place my order"
- `execute_checkout`: "yes, place it" (after validation), "confirm order"

### Output Format
```python
{
    "action": str,                    # From sub-agent (e.g., "item_added")
    "success": bool,                  # True/False
    "data": Dict,                     # Sub-agent specific data
    "context": Dict,                  # Metadata
    # Optional state updates
    "cart_items": List[Dict],
    "cart_subtotal": float,
    "cart_validated": bool,
    "cart_locked": bool,
    "draft_order_id": Optional[str]
}
```

---

## 1.1 SUB-AGENT: menu_browsing

### Purpose
List menu categories and browse items within specific categories

### Use Cases
```
✓ "Show me the menu"
✓ "What categories do you have?"
✓ "Show me appetizers"
✓ "What's in the main course section?"
```

### Input Required
```python
{
    "entities": {
        "category_name": Optional[str]  # "appetizers", "main course", etc.
    },
    "state": {
        "session_id": str,              # "abc123"
        "restaurant_id": str            # "rest001"
    }
}
```

---

### Database Operations

#### Operation 1: List All Categories

**Table:** `menu_items`

**SQL Query:**
```sql
SELECT DISTINCT
    category,
    display_order
FROM menu_items
WHERE restaurant_id = 'rest001'
  AND is_available = true
ORDER BY display_order ASC;
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| category | VARCHAR(50) | Category name | "Appetizers" |
| display_order | INT | Sort order | 1, 2, 3... |

**Sample Result:**
```
category          | display_order
------------------|-------------
Appetizers        | 1
Main Course       | 2
Breads            | 3
Desserts          | 4
Beverages         | 5
```

---

#### Operation 2: Browse Category Items

**Table:** `menu_items`

**SQL Query:**
```sql
SELECT
    item_id,
    name,
    description,
    price,
    category,
    dietary_tags,
    spice_level,
    image_url,
    is_recommended,
    display_order
FROM menu_items
WHERE restaurant_id = 'rest001'
  AND category = 'Main Course'
  AND is_available = true
ORDER BY display_order ASC, name ASC;
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| item_id | UUID | Unique identifier | "mit000456" |
| name | VARCHAR(200) | Item name | "Butter Chicken" |
| description | TEXT | Item description | "Creamy tomato-based curry..." |
| price | DECIMAL(10,2) | Price in rupees | 320.00 |
| category | VARCHAR(50) | Category | "Main Course" |
| dietary_tags | JSON | Dietary info | ["gluten-free", "dairy"] |
| spice_level | VARCHAR(20) | Spice level | "medium", "hot", "mild" |
| image_url | VARCHAR(500) | Image URL | "https://..." |
| is_recommended | BOOLEAN | Featured item | true/false |
| display_order | INT | Sort order | 1, 2, 3... |

**Sample Result:**
```
item_id    | name                | price  | dietary_tags           | spice_level
-----------|---------------------|--------|------------------------|------------
mit000456  | Butter Chicken      | 320.00 | ["gluten-free","dairy"]| medium
mit000457  | Chicken Tikka Masala| 340.00 | ["gluten-free","dairy"]| hot
mit000458  | Paneer Tikka        | 250.00 | ["vegetarian"]         | medium
```

---

### Output Format

#### Case 1: List Categories
```python
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
        "action_performed": "list_categories",
        "restaurant_id": "rest001"
    }
}
```

#### Case 2: Browse Category
```python
{
    "action": "category_browsed",
    "success": True,
    "data": {
        "category": "Main Course",
        "items": [
            {
                "item_id": "mit000456",
                "name": "Butter Chicken",
                "description": "Creamy tomato-based curry with tender chicken",
                "price": 320,
                "dietary_tags": ["gluten-free", "dairy"],
                "spice_level": "medium",
                "image_url": "https://...",
                "is_recommended": True
            },
            {
                "item_id": "mit000457",
                "name": "Chicken Tikka Masala",
                "description": "Grilled chicken in spiced gravy",
                "price": 340,
                "dietary_tags": ["gluten-free", "dairy"],
                "spice_level": "hot",
                "is_recommended": False
            }
            // ... more items
        ],
        "count": 12,
        "message": "Here are items in Main Course"
    },
    "context": {
        "category": "Main Course",
        "action_performed": "browse_category",
        "items_shown": 12
    }
}
```

---

## 1.2 SUB-AGENT: menu_discovery

### Purpose
AI-powered semantic search, filtering by dietary restrictions/price/spice, and recommendations

### Use Cases
```
✓ "Show me vegetarian options"
✓ "Spicy food under ₹300"
✓ "Do you have butter chicken?"
✓ "Recommend something"
✓ "What's vegan and gluten-free?"
```

### Input Required
```python
{
    "entities": {
        "search_query": Optional[str],              # "vegetarian", "butter chicken"
        "dietary_restrictions": Optional[List],     # ["vegetarian", "vegan", "gluten-free"]
        "price_range": Optional[Dict],              # {"min": 0, "max": 300}
        "spice_level": Optional[str],               # "mild", "medium", "hot"
        "category": Optional[str]                   # Filter by category
    },
    "state": {
        "session_id": str,
        "restaurant_id": str,
        "user_id": Optional[str]                    # For personalized recommendations
    }
}
```

---

### Database Operations

#### Operation 1: Semantic Search (with pgvector)

**Table:** `menu_items`

**SQL Query:**
```sql
SELECT
    item_id,
    name,
    description,
    price,
    category,
    dietary_tags,
    spice_level,
    image_url,
    is_recommended,
    popularity_score,
    embedding,
    1 - (embedding <=> query_embedding) as similarity
FROM menu_items
WHERE restaurant_id = 'rest001'
  AND is_available = true
ORDER BY similarity DESC
LIMIT 100;
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| item_id | UUID | Unique ID | "mit000123" |
| name | VARCHAR(200) | Item name | "Paneer Tikka" |
| description | TEXT | Description | "Grilled cottage cheese..." |
| price | DECIMAL(10,2) | Price | 250.00 |
| category | VARCHAR(50) | Category | "appetizers" |
| dietary_tags | JSON | Dietary tags | ["vegetarian", "gluten-free"] |
| spice_level | VARCHAR(20) | Spice level | "medium" |
| image_url | VARCHAR(500) | Image | "https://..." |
| is_recommended | BOOLEAN | Featured | true |
| popularity_score | INT | Order count | 450 |
| embedding | VECTOR(1536) | Text embedding | [0.123, -0.456, ...] |
| similarity | FLOAT | Match score | 0.89 (0-1 scale) |

**How Embedding Works:**
```python
# Generate embedding for search query
search_query = "vegetarian"
query_embedding = openai.embeddings.create(
    model="text-embedding-ada-002",
    input=search_query
)

# Database compares with all item embeddings
# Returns items with highest cosine similarity
```

**Sample Result:**
```
item_id    | name          | price  | similarity | dietary_tags
-----------|---------------|--------|------------|-------------------
mit000123  | Paneer Tikka  | 250.00 | 0.89       | ["vegetarian","gluten-free"]
mit000234  | Veg Biryani   | 280.00 | 0.85       | ["vegetarian","vegan"]
mit000345  | Dal Makhani   | 180.00 | 0.82       | ["vegetarian","gluten-free"]
```

---

#### Operation 2: Get Recommendations (No Search Query)

**Tables:** `menu_items` + `menu_item_ratings`

**SQL Query:**
```sql
SELECT
    mi.item_id,
    mi.name,
    mi.description,
    mi.price,
    mi.category,
    mi.image_url,
    AVG(mir.rating) as avg_rating,
    COUNT(mir.rating) as rating_count,
    mi.popularity_score
FROM menu_items mi
LEFT JOIN menu_item_ratings mir ON mi.item_id = mir.item_id
WHERE mi.restaurant_id = 'rest001'
  AND mi.is_available = true
GROUP BY mi.item_id
HAVING COUNT(mir.rating) >= 5  -- At least 5 ratings
ORDER BY avg_rating DESC, rating_count DESC, mi.popularity_score DESC
LIMIT 10;
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| item_id | UUID | Item ID | "mit000456" |
| name | VARCHAR(200) | Item name | "Butter Chicken" |
| price | DECIMAL(10,2) | Price | 320.00 |
| avg_rating | DECIMAL(3,2) | Average rating | 4.8 |
| rating_count | INT | Total ratings | 234 |
| popularity_score | INT | Order count | 450 |

**Sample Result:**
```
item_id    | name           | price  | avg_rating | rating_count | popularity_score
-----------|----------------|--------|------------|--------------|----------------
mit000456  | Butter Chicken | 320.00 | 4.8        | 234          | 450
mit000457  | Tikka Masala   | 340.00 | 4.7        | 189          | 380
mit000123  | Paneer Tikka   | 250.00 | 4.6        | 156          | 320
```

---

#### Operation 3: Python-Side Filtering

After fetching from database, apply additional filters:

```python
# Filter 1: Dietary restrictions
if dietary_restrictions:
    filtered = [
        item for item in results
        if any(tag in item['dietary_tags'] for tag in dietary_restrictions)
    ]

# Example:
# dietary_restrictions = ["vegetarian"]
# Only keeps items with "vegetarian" in dietary_tags

# Filter 2: Price range
if price_range:
    if 'min' in price_range:
        filtered = [
            item for item in filtered
            if item['price'] >= price_range['min']
        ]
    if 'max' in price_range:
        filtered = [
            item for item in filtered
            if item['price'] <= price_range['max']
        ]

# Example:
# price_range = {"max": 300}
# Only keeps items with price <= 300

# Filter 3: Spice level
if spice_level:
    filtered = [
        item for item in filtered
        if item['spice_level'] == spice_level
    ]

# Example:
# spice_level = "mild"
# Only keeps items with spice_level = "mild"

# Filter 4: Category
if category:
    filtered = [
        item for item in filtered
        if item['category'].lower() == category.lower()
    ]
```

---

### Output Format

#### Case 1: Search Results
```python
{
    "action": "search_results",
    "success": True,
    "data": {
        "items": [
            {
                "item_id": "mit000123",
                "name": "Paneer Tikka",
                "description": "Grilled cottage cheese with spices",
                "price": 250,
                "category": "appetizers",
                "dietary_tags": ["vegetarian", "gluten-free"],
                "spice_level": "medium",
                "image_url": "https://...",
                "similarity_score": 0.89,      # How well it matched
                "is_recommended": True
            },
            {
                "item_id": "mit000234",
                "name": "Veg Biryani",
                "description": "Fragrant rice with mixed vegetables",
                "price": 280,
                "category": "main_course",
                "dietary_tags": ["vegetarian", "vegan"],
                "spice_level": "medium",
                "similarity_score": 0.85,
                "is_recommended": False
            }
            // ... more items (up to 100, then filtered)
        ],
        "count": 12,
        "search_query": "vegetarian",
        "filters_applied": [
            "dietary: vegetarian",
            "price: <= 300"
        ],
        "message": "Found 12 vegetarian items under ₹300"
    },
    "context": {
        "search_type": "semantic",
        "initial_results": 50,
        "after_filtering": 12,
        "filters": {
            "dietary_restrictions": ["vegetarian"],
            "price_range": {"max": 300}
        }
    }
}
```

#### Case 2: Recommendations
```python
{
    "action": "recommendations",
    "success": True,
    "data": {
        "items": [
            {
                "item_id": "mit000456",
                "name": "Butter Chicken",
                "description": "Creamy tomato curry",
                "price": 320,
                "category": "main_course",
                "avg_rating": 4.8,
                "rating_count": 234,
                "popularity_score": 450,
                "reason": "Highly rated by 234 customers (4.8/5)"
            },
            {
                "item_id": "mit000457",
                "name": "Chicken Tikka Masala",
                "price": 340,
                "avg_rating": 4.7,
                "rating_count": 189,
                "popularity_score": 380,
                "reason": "Customer favorite (4.7/5)"
            }
            // ... 8 more items
        ],
        "count": 10,
        "recommendation_type": "popular",
        "message": "Here are our most popular dishes"
    },
    "context": {
        "recommendation_strategy": "rating_and_popularity",
        "min_ratings_threshold": 5
    }
}
```

#### Case 3: No Results
```python
{
    "action": "no_results",
    "success": False,
    "data": {
        "search_query": "lobster",
        "filters_applied": [],
        "message": "Sorry, we couldn't find any items matching 'lobster'",
        "suggestions": [
            "Try browsing our categories",
            "Search for 'seafood' or 'chicken'"
        ]
    },
    "context": {
        "search_type": "semantic",
        "results_count": 0
    }
}
```

---

## 1.3 SUB-AGENT: cart_management

### Purpose
Manage cart operations - add, remove, update quantities, view, clear

### Use Cases
```
✓ "Add 2 butter chickens"
✓ "Remove item 2"
✓ "Change quantity to 3"
✓ "Update naan to 5"
✓ "Show my cart"
✓ "Clear cart"
```

### Input Required
```python
{
    "entities": {
        "action": str,                      # "add", "remove", "update", "view", "clear"
        "item_id": Optional[str],           # "mit000456"
        "item_name": Optional[str],         # "butter chicken"
        "item_index": Optional[int],        # 2 (for "remove item 2")
        "quantity": Optional[int],          # 2 (for add)
        "new_quantity": Optional[int]       # 3 (for update)
    },
    "state": {
        "session_id": str,                  # "abc123"
        "user_id": Optional[str],           # "usr456"
        "cart_items": List[Dict],           # Current cart contents
        "restaurant_id": str
    }
}
```

### Flow Diagram

```
                    ┌──────────────────────┐
                    │   CART ACTION        │
                    │ "Add butter chicken" │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │   Action Type?      │
                    └──┬────┬────┬────┬───┘
       ┌───────────────┘    │    │    └───────────┐
       │              ┌─────┘    └─────┐          │
       ▼              ▼                ▼          ▼
    [ADD]         [REMOVE]         [UPDATE]   [VIEW/CLEAR]
       │              │                │          │
       ▼              │                │          │
┌─────────────┐       │                │          │
│ Resolve Item│       │                │          │
│ DB: menu_   │       │                │          │
│   items     │       │                │          │
└──────┬──────┘       │                │          │
       │              │                │          │
       ▼              │                │          │
┌─────────────┐       │                │          │
│Check Inven- │       │                │          │
│tory (Redis) │       │                │          │
└──┬────┬─────┘       │                │          │
   │    │             │                │          │
Available│Not          │                │          │
   │    │Available    │                │          │
   ▼    ▼             │                │          │
┌─────┐ ┌────────┐    │                │          │
│Reserve Stock  │    │                │          │
│(Redis)│ │ERROR: │    │                │          │
└───┬──┘ │Out of │    │                │          │
    │    │Stock  │    │                │          │
    │    └───┬───┘    │                │          │
    ▼        │        │                │          │
┌─────────┐  │        │                │          │
│Add to   │  │        │                │          │
│Cart     │  │        │                │          │
│(MongoDB)│  │        │                │          │
└────┬────┘  │        │                │          │
     │       │        │                │          │
     └───────┴────────┴────────────────┴──────────┘
                      │
                      ▼
            ┌──────────────────┐
            │  Update State    │
            │ Calculate Total  │
            └─────────┬────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
    ┌──────────┐            ┌──────────┐
    │ SUCCESS  │            │  ERROR   │
    └─────┬────┘            └─────┬────┘
          └──────────┬─────────────┘
                     ▼
            ┌─────────────────┐
            │  ActionResult   │
            └─────────────────┘
```

**Cart Operation Flow:**
1. **Add Item**: Item resolution → Inventory check (Redis) → Reserve stock → Add to cart
2. **Remove Item**: Remove from cart → Release reservation (Redis) → Update state
3. **Update Quantity**: Check new inventory → Adjust reservation → Update cart
4. **View Cart**: Fetch items → Calculate totals → Return
5. **Clear Cart**: Release all reservations (Redis) → Empty cart

---

### Database Operations

#### Operation 1: Item Resolution (when only name provided)

**Table:** `menu_items`

**SQL Query (Option A - Pattern Matching):**
```sql
SELECT
    item_id,
    name,
    price,
    category,
    is_available
FROM menu_items
WHERE restaurant_id = 'rest001'
  AND LOWER(name) LIKE LOWER('%butter chicken%')
  AND is_available = true
ORDER BY
    CASE
        WHEN LOWER(name) = LOWER('butter chicken') THEN 1  -- Exact match first
        ELSE 2
    END,
    name
LIMIT 1;
```

**SQL Query (Option B - Semantic Search):**
```sql
SELECT
    item_id,
    name,
    price,
    category,
    is_available,
    1 - (embedding <=> query_embedding) as similarity
FROM menu_items
WHERE restaurant_id = 'rest001'
  AND is_available = true
ORDER BY similarity DESC
LIMIT 1;
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| item_id | UUID | Unique ID | "mit000456" |
| name | VARCHAR(200) | Canonical name | "Butter Chicken" |
| price | DECIMAL(10,2) | Current price | 320.00 |
| category | VARCHAR(50) | Category | "main_course" |
| is_available | BOOLEAN | Available? | true |
| similarity | FLOAT | Match score | 0.95 (semantic only) |

**Sample Result:**
```
item_id    | name           | price  | category     | is_available
-----------|----------------|--------|--------------|-------------
mit000456  | Butter Chicken | 320.00 | main_course  | true
```

---

#### Operation 2: Check Inventory (Redis)

**Redis Keys:**

```redis
# Key 1: Current inventory stock
GET inventory:mit000456
→ Returns: "50" (total stock available)

# Key 2: Get all reservations for this item
KEYS reservation:mit000456:*
→ Returns: [
    "reservation:mit000456:usr123",
    "reservation:mit000456:usr456",
    "reservation:mit000456:sess789"
]

# Key 3: Get specific user's reservation
GET reservation:mit000456:usr456
→ Returns: "2" (user already reserved 2 units)

# Calculate available inventory
total_stock = 50
reservations = [2, 3, 1, 2]  # From all users
reserved_total = sum(reservations) = 8
available = total_stock - reserved_total = 42
```

**Availability Check:**
```python
def check_availability(item_id, requested_qty):
    # Get current stock
    stock = redis.get(f"inventory:{item_id}")
    stock = int(stock) if stock else 0

    # Get all reservations
    reservation_keys = redis.keys(f"reservation:{item_id}:*")

    # Sum all reservations
    reserved = 0
    for key in reservation_keys:
        qty = redis.get(key)
        reserved += int(qty) if qty else 0

    # Calculate available
    available = stock - reserved

    # Check if sufficient
    if available >= requested_qty:
        return True, available
    else:
        return False, available
```

---

#### Operation 3: Cart Storage

**Storage Option A: MongoDB**

**Collection:** `carts`

**Document Structure:**
```javascript
{
    "_id": ObjectId("507f1f77bcf86cd799439011"),
    "session_id": "abc123",
    "user_id": "usr456",                    // Optional (anonymous users have null)
    "restaurant_id": "rest001",
    "items": [
        {
            "item_id": "mit000456",
            "name": "Butter Chicken",
            "quantity": 2,
            "unit_price": 320.00,
            "item_total": 640.00,
            "added_at": ISODate("2025-11-14T10:30:00Z")
        },
        {
            "item_id": "mit000123",
            "name": "Naan",
            "quantity": 3,
            "unit_price": 50.00,
            "item_total": 150.00,
            "added_at": ISODate("2025-11-14T10:32:00Z")
        }
    ],
    "subtotal": 790.00,
    "locked": false,
    "locked_at": null,
    "created_at": ISODate("2025-11-14T10:30:00Z"),
    "updated_at": ISODate("2025-11-14T10:35:00Z")
}
```

**MongoDB Operations:**

```javascript
// Operation 1: Get cart
db.carts.findOne({ session_id: "abc123" })

// Operation 2: Add item to cart
db.carts.updateOne(
    { session_id: "abc123" },
    {
        $push: {
            items: {
                item_id: "mit000456",
                name: "Butter Chicken",
                quantity: 2,
                unit_price: 320.00,
                item_total: 640.00,
                added_at: new Date()
            }
        },
        $inc: { subtotal: 640.00 },
        $set: { updated_at: new Date() }
    },
    { upsert: true }
)

// Operation 3: Remove item from cart
db.carts.updateOne(
    { session_id: "abc123" },
    {
        $pull: { items: { item_id: "mit000456" } },
        $inc: { subtotal: -640.00 },
        $set: { updated_at: new Date() }
    }
)

// Operation 4: Update quantity
db.carts.updateOne(
    {
        session_id: "abc123",
        "items.item_id": "mit000456"
    },
    {
        $set: {
            "items.$.quantity": 3,
            "items.$.item_total": 960.00,
            updated_at: new Date()
        },
        $inc: { subtotal: 320.00 }  // Difference: 960 - 640
    }
)

// Operation 5: Clear cart
db.carts.updateOne(
    { session_id: "abc123" },
    {
        $set: {
            items: [],
            subtotal: 0,
            updated_at: new Date()
        }
    }
)

// Operation 6: Lock cart (during checkout)
db.carts.updateOne(
    { session_id: "abc123" },
    {
        $set: {
            locked: true,
            locked_at: new Date()
        }
    }
)
```

---

**Storage Option B: In-Memory (Python Dictionary)**

```python
# Global dictionary (in-memory)
carts = {}

# Structure:
carts["abc123"] = {
    "items": [
        {
            "item_id": "mit000456",
            "name": "Butter Chicken",
            "quantity": 2,
            "unit_price": 320,
            "item_total": 640
        }
    ],
    "subtotal": 640
}

# Operations:
# Add item
carts["abc123"]["items"].append(new_item)
carts["abc123"]["subtotal"] += new_item["item_total"]

# Remove item
carts["abc123"]["items"] = [
    item for item in carts["abc123"]["items"]
    if item["item_id"] != item_id_to_remove
]

# Recalculate subtotal
carts["abc123"]["subtotal"] = sum(
    item["item_total"] for item in carts["abc123"]["items"]
)
```

---

#### Operation 4: Reserve Inventory (Redis)

**When Adding Item:**

```redis
# Step 1: Check current availability
GET inventory:mit000456
→ "50"

# Step 2: Get all existing reservations
KEYS reservation:mit000456:*
→ ["reservation:mit000456:usr123", "reservation:mit000456:sess789"]

# Step 3: Sum existing reservations
GET reservation:mit000456:usr123 → "3"
GET reservation:mit000456:sess789 → "2"
Total reserved: 5

# Step 4: Calculate available
Available = 50 - 5 = 45

# Step 5: Check if sufficient for new request
Requested = 2
45 >= 2? YES ✓

# Step 6: Create/update reservation
SET reservation:mit000456:usr456 2
EXPIRE reservation:mit000456:usr456 900  # 15 minutes TTL

# Result: User has reserved 2 units for 15 minutes
# If they don't checkout within 15 min, reservation auto-expires
```

**When Removing Item:**

```redis
# Release reservation
DEL reservation:mit000456:usr456

# Inventory becomes available to other users immediately
```

**When Updating Quantity:**

```redis
# Update reservation quantity
SET reservation:mit000456:usr456 5  # Changed from 2 to 5
EXPIRE reservation:mit000456:usr456 900  # Reset TTL
```

---

### Output Format

#### Case 1: Add to Cart (Success)
```python
{
    "action": "item_added",
    "success": True,
    "data": {
        "item_id": "mit000456",
        "item_name": "Butter Chicken",
        "quantity": 2,
        "unit_price": 320,
        "item_total": 640,
        "cart_subtotal": 790,
        "cart_item_count": 2,
        "message": "Added 2x Butter Chicken to cart"
    },
    "context": {
        "item_id": "mit000456",
        "action_performed": "added",
        "inventory_reserved": True,
        "reservation_expires_in": 900  # seconds
    },
    # State update
    "cart_subtotal": 790
}
```

#### Case 2: Add to Cart (Insufficient Inventory)
```python
{
    "action": "add_failed",
    "success": False,
    "data": {
        "item_name": "Butter Chicken",
        "requested_quantity": 10,
        "available_quantity": 3,
        "error_type": "insufficient_inventory",
        "message": "Sorry, only 3 units of Butter Chicken available"
    },
    "context": {
        "item_id": "mit000456",
        "action_performed": "add_attempted",
        "inventory_reserved": False
    }
}
```

#### Case 3: Add to Cart (Item Not Found)
```python
{
    "action": "item_not_found",
    "success": False,
    "data": {
        "searched_item": "lobster biryani",
        "message": "I couldn't find 'lobster biryani' in our menu. Try searching for it first?"
    },
    "context": {
        "action_performed": "add_attempted",
        "resolution_failed": True
    }
}
```

#### Case 4: Remove from Cart
```python
{
    "action": "item_removed",
    "success": True,
    "data": {
        "item_name": "Naan",
        "cart_subtotal": 640,
        "cart_item_count": 1,
        "message": "Removed Naan from cart"
    },
    "context": {
        "action_performed": "removed",
        "inventory_released": True
    },
    # State update
    "cart_subtotal": 640
}
```

#### Case 5: Update Quantity
```python
{
    "action": "quantity_updated",
    "success": True,
    "data": {
        "item_name": "Butter Chicken",
        "old_quantity": 2,
        "new_quantity": 3,
        "item_total": 960,
        "cart_subtotal": 1110,
        "message": "Updated Butter Chicken quantity to 3"
    },
    "context": {
        "action_performed": "updated",
        "inventory_adjustment": +1
    },
    # State update
    "cart_subtotal": 1110
}
```

#### Case 6: View Cart
```python
{
    "action": "cart_viewed",
    "success": True,
    "data": {
        "items": [
            {
                "item_id": "mit000456",
                "name": "Butter Chicken",
                "quantity": 2,
                "unit_price": 320,
                "item_total": 640
            },
            {
                "item_id": "mit000123",
                "name": "Naan",
                "quantity": 3,
                "unit_price": 50,
                "item_total": 150
            }
        ],
        "item_count": 2,
        "subtotal": 790,
        "order_type": None,  # Not set yet
        "is_locked": False,
        "message": "Your cart has 2 items, total ₹790"
    },
    "context": {
        "action_performed": "viewed"
    },
    # State updates
    "cart_subtotal": 790,
    "cart_items": [...]  # Full cart data
}
```

#### Case 7: Clear Cart
```python
{
    "action": "cart_cleared",
    "success": True,
    "data": {
        "items_removed": 2,
        "previous_subtotal": 790,
        "message": "Your cart has been cleared. You can start fresh now."
    },
    "context": {
        "action_performed": "cleared",
        "all_inventory_released": True
    },
    # State updates
    "cart_items": [],
    "cart_subtotal": 0.0,
    "cart_validated": False
}
```

---

## 1.4 SUB-AGENT: checkout_validator

### Purpose
Validate cart before checkout - verify availability, prices, calculate totals with taxes

### Use Cases
```
✓ "Checkout"
✓ "I'm ready to order"
✓ "Place my order"
✓ "Ready to pay"
```

### Input Required
```python
{
    "entities": {},  # No entities needed (system action)
    "state": {
        "session_id": str,              # "abc123"
        "user_id": Optional[str],       # "usr456"
        "cart_items": List[Dict],       # Current cart
        "cart_subtotal": float,         # 790.00
        "restaurant_id": str
    }
}
```

---

### Database Operations

#### Operation 1: Verify Items Still Available

**Table:** `menu_items`

**SQL Query:**
```sql
SELECT
    item_id,
    name,
    price,
    is_available
FROM menu_items
WHERE item_id IN ('mit000456', 'mit000123', ...)  -- All cart item IDs
  AND restaurant_id = 'rest001';
```

**Purpose:** Check if all cart items are:
1. Still in the menu (not deleted)
2. Still available (is_available = true)
3. Price unchanged (compare with cart price)

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| item_id | UUID | Item ID | "mit000456" |
| name | VARCHAR(200) | Current name | "Butter Chicken" |
| price | DECIMAL(10,2) | Current price | 320.00 |
| is_available | BOOLEAN | Available? | true/false |

**Sample Result:**
```
item_id    | name           | price  | is_available
-----------|----------------|--------|-------------
mit000456  | Butter Chicken | 320.00 | true
mit000123  | Naan           | 50.00  | true
```

**Validation Checks:**
```python
for cart_item in cart_items:
    db_item = database_results[cart_item['item_id']]

    # Check 1: Item exists?
    if not db_item:
        errors.append(f"{cart_item['name']} no longer in menu")

    # Check 2: Item available?
    elif not db_item['is_available']:
        errors.append(f"{cart_item['name']} is no longer available")

    # Check 3: Price unchanged?
    elif db_item['price'] != cart_item['unit_price']:
        price_changes.append({
            'item': cart_item['name'],
            'old_price': cart_item['unit_price'],
            'new_price': db_item['price']
        })
```

---

#### Operation 2: Verify Inventory Sufficient

**Redis Operations:**

```redis
# For each cart item, verify inventory
# Item 1: Butter Chicken (mit000456, quantity=2)

# Get current stock
GET inventory:mit000456
→ "50"

# Get all reservations
KEYS reservation:mit000456:*
→ ["reservation:mit000456:usr456", "reservation:mit000456:usr123", ...]

# Sum reservations
GET reservation:mit000456:usr456 → "2"
GET reservation:mit000456:usr123 → "3"
# ... more
Total reserved: 8

# Calculate available
available = 50 - 8 = 42

# Verify sufficient
cart_quantity = 2
42 >= 2? YES ✓

# Repeat for all cart items
```

**Validation Check:**
```python
for cart_item in cart_items:
    item_id = cart_item['item_id']
    quantity = cart_item['quantity']

    # Get inventory
    stock = redis.get(f"inventory:{item_id}")

    # Get reservations
    reservations = redis.keys(f"reservation:{item_id}:*")
    reserved = sum(int(redis.get(key)) for key in reservations)

    # Check availability
    available = int(stock) - reserved

    if available < quantity:
        errors.append({
            'item': cart_item['name'],
            'requested': quantity,
            'available': available
        })
```

---

#### Operation 3: Get Restaurant Settings

**Table:** `restaurant_settings`

**SQL Query:**
```sql
SELECT
    tax_rate,
    service_charge_rate,
    minimum_order_amount,
    delivery_charge_dine_in,
    delivery_charge_takeout
FROM restaurant_settings
WHERE restaurant_id = 'rest001';
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| tax_rate | DECIMAL(5,4) | Tax % | 0.1000 (10%) |
| service_charge_rate | DECIMAL(5,4) | Service charge % | 0.0500 (5%) |
| minimum_order_amount | DECIMAL(10,2) | Min order | 100.00 |
| delivery_charge_dine_in | DECIMAL(10,2) | Dine-in fee | 0.00 |
| delivery_charge_takeout | DECIMAL(10,2) | Takeout fee | 20.00 |

**Sample Result:**
```
tax_rate | service_charge_rate | minimum_order_amount
---------|---------------------|--------------------
0.1000   | 0.0500              | 100.00
```

---

### Calculation Logic

```python
# Step 1: Subtotal (already calculated in cart)
subtotal = 790.00

# Step 2: Minimum order check
minimum_order = 100.00  # From restaurant_settings
if subtotal < minimum_order:
    raise ValidationError(f"Minimum order amount is ₹{minimum_order}")

# Step 3: Tax calculation
tax_rate = 0.10  # 10% from restaurant_settings
tax_amount = round(subtotal * tax_rate, 2)
# Example: 790.00 * 0.10 = 79.00

# Step 4: Service charge (optional, usually for dine-in)
service_charge_rate = 0.05  # 5% from restaurant_settings
service_charge = round(subtotal * service_charge_rate, 2)
# Example: 790.00 * 0.05 = 39.50

# Step 5: Delivery/packaging charge (depends on order_type)
# Note: order_type not set yet at validation stage
# Will be applied in checkout_executor
delivery_charge = 0.00  # TBD based on order_type

# Step 6: Total
total = subtotal + tax_amount + service_charge + delivery_charge
# Example: 790.00 + 79.00 + 39.50 + 0.00 = 908.50
```

**Breakdown Example:**
```
Items:
  2x Butter Chicken @ ₹320   = ₹640.00
  3x Naan @ ₹50             = ₹150.00
                         ───────────
Subtotal:                    ₹790.00

Tax (10%):                   ₹ 79.00
Service Charge (5%):         ₹ 39.50
                         ───────────
Total:                       ₹908.50
```

---

### Output Format

#### Case 1: Validation Passed
```python
{
    "action": "cart_validated",
    "success": True,
    "data": {
        "items": [
            {
                "item_id": "mit000456",
                "name": "Butter Chicken",
                "quantity": 2,
                "unit_price": 320.00,
                "item_total": 640.00,
                "available": True,
                "price_changed": False,
                "inventory_sufficient": True
            },
            {
                "item_id": "mit000123",
                "name": "Naan",
                "quantity": 3,
                "unit_price": 50.00,
                "item_total": 150.00,
                "available": True,
                "price_changed": False,
                "inventory_sufficient": True
            }
        ],
        "subtotal": 790.00,
        "tax": 79.00,
        "tax_rate": 0.10,
        "service_charge": 39.50,
        "service_charge_rate": 0.05,
        "delivery_charge": 0.00,
        "total": 908.50,
        "validation_checks": {
            "items_available": True,
            "inventory_sufficient": True,
            "prices_unchanged": True,
            "minimum_order_met": True
        },
        "order_summary": "2 items, Total: ₹908.50",
        "message": "Cart validated successfully. Ready to place order."
    },
    "context": {
        "validation_passed": True,
        "checks_run": 4,
        "all_checks_passed": True
    },
    # State update
    "cart_validated": True
}
```

#### Case 2: Item Unavailable
```python
{
    "action": "validation_failed",
    "success": False,
    "data": {
        "validation_errors": [
            {
                "error_type": "item_unavailable",
                "item_id": "mit000456",
                "item_name": "Butter Chicken",
                "message": "Butter Chicken is no longer available"
            }
        ],
        "failed_checks": ["items_available"],
        "message": "Some items in your cart are no longer available"
    },
    "context": {
        "validation_passed": False,
        "checks_run": 4,
        "failed_check": "items_available"
    },
    # State update
    "cart_validated": False
}
```

#### Case 3: Insufficient Inventory
```python
{
    "action": "validation_failed",
    "success": False,
    "data": {
        "validation_errors": [
            {
                "error_type": "insufficient_inventory",
                "item_id": "mit000456",
                "item_name": "Butter Chicken",
                "requested": 10,
                "available": 3,
                "message": "Only 3 units of Butter Chicken available (you have 10 in cart)"
            }
        ],
        "failed_checks": ["inventory_sufficient"],
        "message": "Not enough inventory for some items"
    },
    "context": {
        "validation_passed": False,
        "failed_check": "inventory_sufficient"
    },
    # State update
    "cart_validated": False
}
```

#### Case 4: Price Changed
```python
{
    "action": "price_changed",
    "success": False,
    "data": {
        "validation_errors": [
            {
                "error_type": "price_changed",
                "item_id": "mit000456",
                "item_name": "Butter Chicken",
                "old_price": 320.00,
                "new_price": 350.00,
                "difference": +30.00,
                "message": "Price of Butter Chicken changed from ₹320 to ₹350"
            }
        ],
        "price_changes": [
            {
                "item": "Butter Chicken",
                "old_price": 320.00,
                "new_price": 350.00
            }
        ],
        "old_total": 908.50,
        "new_total": 968.50,
        "difference": +60.00,
        "failed_checks": ["prices_unchanged"],
        "message": "Prices have changed since you added items. Please review."
    },
    "context": {
        "validation_passed": False,
        "failed_check": "prices_unchanged",
        "requires_user_confirmation": True
    },
    # State update
    "cart_validated": False
}
```

#### Case 5: Below Minimum Order
```python
{
    "action": "validation_failed",
    "success": False,
    "data": {
        "validation_errors": [
            {
                "error_type": "below_minimum_order",
                "current_subtotal": 75.00,
                "minimum_required": 100.00,
                "shortfall": 25.00,
                "message": "Minimum order amount is ₹100. Add ₹25 more to proceed."
            }
        ],
        "failed_checks": ["minimum_order_met"],
        "message": "Cart total below minimum order amount"
    },
    "context": {
        "validation_passed": False,
        "failed_check": "minimum_order_met"
    },
    # State update
    "cart_validated": False
}
```

---

## 1.5 SUB-AGENT: checkout_executor

### Purpose
Execute final checkout - create order in database, commit inventory, lock cart, generate confirmation

### Use Cases
```
✓ "Yes, confirm" (after validation)
✓ "Place order for dine-in"
✓ "Confirm for takeout"
```

### Input Required
```python
{
    "entities": {
        "order_type": str  # REQUIRED: "dine_in" or "takeout"
    },
    "state": {
        "session_id": str,              # "abc123"
        "user_id": str,                 # "usr456" (REQUIRED - must be authenticated)
        "cart_items": List[Dict],       # Validated cart
        "cart_subtotal": float,         # 790.00
        "cart_validated": bool,         # Must be True
        "restaurant_id": str,
        "tax": float,                   # 79.00 (from validator)
        "service_charge": float         # 39.50 (from validator)
    }
}
```

---

### Database Operations

#### Operation 1: Create Order Record

**Table:** `orders`

**SQL Query:**
```sql
INSERT INTO orders (
    id,
    user_id,
    restaurant_id,
    order_type,
    status,
    subtotal,
    tax_amount,
    service_charge,
    delivery_charge,
    total_amount,
    order_number,
    estimated_prep_time_minutes,
    created_at,
    confirmed_at
) VALUES (
    'ord_789abc',           -- Generated UUID
    'usr456',
    'rest001',
    'dine_in',
    'confirmed',            -- Status: pending → confirmed
    790.00,
    79.00,
    39.50,
    0.00,
    908.50,
    'ABC141030',            -- Generated order number
    25,                     -- Calculated prep time
    '2025-11-14 10:30:00',
    '2025-11-14 10:30:05'
)
RETURNING id, order_number, created_at;
```

**Columns Inserted:**
| Column | Type | Description | Value |
|--------|------|-------------|-------|
| id | UUID | Order ID | "ord_789abc" |
| user_id | UUID | User who placed | "usr456" |
| restaurant_id | UUID | Restaurant | "rest001" |
| order_type | VARCHAR(20) | Type | "dine_in" or "takeout" |
| status | VARCHAR(20) | Status | "confirmed" |
| subtotal | DECIMAL(10,2) | Items total | 790.00 |
| tax_amount | DECIMAL(10,2) | Tax | 79.00 |
| service_charge | DECIMAL(10,2) | Service charge | 39.50 |
| delivery_charge | DECIMAL(10,2) | Delivery fee | 0.00 |
| total_amount | DECIMAL(10,2) | Final total | 908.50 |
| order_number | VARCHAR(20) | Display number | "ABC141030" |
| estimated_prep_time_minutes | INT | Prep time | 25 |
| created_at | TIMESTAMP | Created | NOW() |
| confirmed_at | TIMESTAMP | Confirmed | NOW() |

**Returns:**
```
id          | order_number | created_at
------------|--------------|-------------------
ord_789abc  | ABC141030    | 2025-11-14 10:30:00
```

---

#### Operation 2: Create Order Items

**Table:** `order_items`

**SQL Queries (Multiple Inserts):**
```sql
-- Item 1: Butter Chicken
INSERT INTO order_items (
    id,
    order_id,
    item_id,
    item_name,
    quantity,
    unit_price,
    subtotal,
    special_instructions
) VALUES (
    'oi_111',
    'ord_789abc',
    'mit000456',
    'Butter Chicken',
    2,
    320.00,
    640.00,
    NULL
);

-- Item 2: Naan
INSERT INTO order_items (
    id,
    order_id,
    item_id,
    item_name,
    quantity,
    unit_price,
    subtotal,
    special_instructions
) VALUES (
    'oi_222',
    'ord_789abc',
    'mit000123',
    'Naan',
    3,
    50.00,
    150.00,
    'Extra butter'
);
```

**Columns Inserted:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | UUID | Item record ID | "oi_111" |
| order_id | UUID | Parent order | "ord_789abc" |
| item_id | UUID | Menu item | "mit000456" |
| item_name | VARCHAR(200) | Item name snapshot | "Butter Chicken" |
| quantity | INT | Quantity ordered | 2 |
| unit_price | DECIMAL(10,2) | Price at order time | 320.00 |
| subtotal | DECIMAL(10,2) | quantity × price | 640.00 |
| special_instructions | TEXT | Special requests | "Extra butter" |

**Why Store Item Name?**
- Menu items might be renamed later
- Order history shows what customer actually ordered
- Preserves historical data

---

#### Operation 3: Commit Inventory

**Redis Operations:**

```redis
# For each order item:

# === Item 1: Butter Chicken (mit000456, qty=2) ===

# Step 1: Remove user's reservation
DEL reservation:mit000456:usr456

# Step 2: Decrement actual inventory
DECRBY inventory:mit000456 2
→ Before: "50"
→ After: "48"

# Step 3: Verify decrement succeeded
GET inventory:mit000456
→ "48" ✓


# === Item 2: Naan (mit000123, qty=3) ===

# Step 1: Remove reservation
DEL reservation:mit000123:usr456

# Step 2: Decrement inventory
DECRBY inventory:mit000123 3
→ Before: "100"
→ After: "97"

# Result: Inventory permanently decreased
```

---

#### Operation 4: Record Inventory Transactions (Audit Trail)

**Table:** `inventory_transactions`

**SQL Queries:**
```sql
-- Transaction 1: Butter Chicken
INSERT INTO inventory_transactions (
    id,
    item_id,
    order_id,
    change_type,
    quantity_change,
    previous_quantity,
    new_quantity,
    user_id,
    timestamp
) VALUES (
    'invt_456',
    'mit000456',
    'ord_789abc',
    'order_placed',
    -2,                 -- Negative = decrease
    50,                 -- Previous stock
    48,                 -- New stock
    'usr456',
    '2025-11-14 10:30:05'
);

-- Transaction 2: Naan
INSERT INTO inventory_transactions (
    id,
    item_id,
    order_id,
    change_type,
    quantity_change,
    previous_quantity,
    new_quantity,
    user_id,
    timestamp
) VALUES (
    'invt_457',
    'mit000123',
    'ord_789abc',
    'order_placed',
    -3,
    100,
    97,
    'usr456',
    '2025-11-14 10:30:05'
);
```

**Columns Inserted:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | UUID | Transaction ID | "invt_456" |
| item_id | UUID | Item affected | "mit000456" |
| order_id | UUID | Related order | "ord_789abc" |
| change_type | VARCHAR(50) | Type | "order_placed", "refund", "restock" |
| quantity_change | INT | Change amount | -2 (negative = decrease) |
| previous_quantity | INT | Before | 50 |
| new_quantity | INT | After | 48 |
| user_id | UUID | Who caused | "usr456" |
| timestamp | TIMESTAMP | When | NOW() |

**Purpose:**
- Audit trail for inventory changes
- Can track inventory history
- Support refunds (reverse transactions)
- Analytics (which items sell fastest)

---

#### Operation 5: Lock Cart

**MongoDB Operation:**
```javascript
db.carts.updateOne(
    { session_id: "abc123" },
    {
        $set: {
            locked: true,
            locked_at: new Date(),
            locked_for_order_id: "ord_789abc"
        }
    }
);
```

**Why Lock Cart?**
- Prevent modifications after order placed
- User can't add/remove items
- Cart preserved for order history
- Can be "unlocked" if order cancelled

---

### Helper Functions

#### Order Number Generation

```python
def generate_order_number():
    """
    Generate human-readable order number
    Format: ABC + DDMMHH + Random
    """
    prefix = "ABC"  # Restaurant prefix

    # Date/time component: DDMMHH (day, month, hour)
    now = datetime.now()
    timestamp = now.strftime("%d%m%H")
    # Example: Nov 14, 10:30 → "141030"

    # Random 2-digit suffix (avoid collisions)
    random_suffix = random.randint(10, 99)

    # Combine
    order_number = f"{prefix}{timestamp}{random_suffix}"
    # Example: "ABC14103045"

    return order_number

# Additional check: Ensure uniqueness
def generate_unique_order_number():
    while True:
        number = generate_order_number()
        # Check if exists in database
        exists = db.query(
            "SELECT 1 FROM orders WHERE order_number = ?",
            [number]
        )
        if not exists:
            return number
```

---

#### Estimated Prep Time Calculation

```python
def calculate_prep_time(items: List[Dict]) -> int:
    """
    Calculate estimated preparation time based on items
    Returns: Minutes
    """
    # Base time (kitchen setup)
    base_time = 10  # minutes

    # Category-based time
    category_times = {
        'appetizers': 3,      # 3 min per item
        'main_course': 5,     # 5 min per item
        'breads': 2,          # 2 min per item
        'desserts': 4,        # 4 min per item
        'beverages': 1        # 1 min per item
    }

    # Calculate per item
    for item in items:
        category = item['category']
        quantity = item['quantity']
        time_per_item = category_times.get(category, 3)

        # Add time (but max 2x for multiple quantities)
        # Example: 5 biryanis ≠ 25 min (parallel cooking)
        multiplier = min(quantity, 2)
        base_time += time_per_item * multiplier

    # Round to nearest 5 minutes
    rounded = round(base_time / 5) * 5

    # Min 15, max 60 minutes
    return max(15, min(60, rounded))

# Example:
# Items: 2x Butter Chicken (main), 3x Naan (bread)
# Time: 10 + (5*2) + (2*2) = 10 + 10 + 4 = 24 → 25 minutes
```

---

### Output Format

#### Case 1: Order Placed Successfully
```python
{
    "action": "order_placed",
    "success": True,
    "data": {
        "order_id": "ord_789abc",
        "order_number": "ABC141030",
        "status": "confirmed",
        "order_type": "dine_in",

        # Items
        "items": [
            {
                "item_id": "mit000456",
                "name": "Butter Chicken",
                "quantity": 2,
                "unit_price": 320.00,
                "item_total": 640.00
            },
            {
                "item_id": "mit000123",
                "name": "Naan",
                "quantity": 3,
                "unit_price": 50.00,
                "item_total": 150.00
            }
        ],

        # Pricing
        "subtotal": 790.00,
        "tax": 79.00,
        "tax_rate": 0.10,
        "service_charge": 39.50,
        "service_charge_rate": 0.05,
        "delivery_charge": 0.00,
        "total": 908.50,

        # Timing
        "estimated_time_minutes": 25,
        "estimated_ready_at": "2025-11-14T10:55:00Z",
        "ordered_at": "2025-11-14T10:30:00Z",

        # Payment
        "payment_required": True,
        "payment_status": "pending",

        "message": "Order placed successfully! Order #ABC141030"
    },
    "context": {
        "order_created": True,
        "inventory_committed": True,
        "cart_locked": True,
        "database_transactions": 4  # orders, order_items x2, inventory_transactions x2
    },

    # State updates
    "draft_order_id": "ord_789abc",
    "order_number": "ABC141030",
    "cart_locked": True,
    "cart_validated": False  # Reset for next order
}
```

#### Case 2: Order Failed - Inventory Race Condition
```python
{
    "action": "order_failed",
    "success": False,
    "data": {
        "error_type": "inventory_insufficient",
        "message": "Some items are no longer available in the requested quantity",

        "unavailable_items": [
            {
                "item_id": "mit000456",
                "item_name": "Butter Chicken",
                "requested": 2,
                "available": 1,
                "reason": "Another customer just ordered the same item"
            }
        ],

        "order_created": False,
        "inventory_committed": False,
        "suggested_action": "Please review your cart and try again"
    },
    "context": {
        "order_created": False,
        "failure_stage": "inventory_commit",
        "reason": "inventory_race_condition",
        "rollback_performed": True
    }
}
```

#### Case 3: Order Failed - User Not Authenticated
```python
{
    "action": "order_failed",
    "success": False,
    "data": {
        "error_type": "authentication_required",
        "message": "You must be logged in to place an order",
        "required_action": "authenticate",
        "suggested_flow": "Please provide your phone number to continue"
    },
    "context": {
        "order_created": False,
        "failure_stage": "pre_validation",
        "reason": "user_not_authenticated"
    }
}
```

#### Case 4: Order Failed - Cart Not Validated
```python
{
    "action": "order_failed",
    "success": False,
    "data": {
        "error_type": "cart_not_validated",
        "message": "Please validate your cart before placing order",
        "required_action": "validate_cart",
        "suggested_flow": "System will validate your cart automatically"
    },
    "context": {
        "order_created": False,
        "failure_stage": "pre_validation",
        "reason": "cart_not_validated"
    }
}
```

---

---

## 2. booking_agent

### Purpose
Handle table reservations from initial request through confirmation - autonomous multi-step flow with internal loops

### Use Cases
```
✓ "Book a table for 4 tomorrow at 7pm"
✓ "I need a reservation for dinner"
✓ "Table for 2 next Friday evening"
✓ "Can I book for 6 people on December 25th?"
✓ "Check my booking"
✓ "Cancel my reservation"
✓ "Change my booking time to 8pm"
```

### Input Required
```python
{
    "user_message": str,              # "book table for 4 tomorrow at 7pm"
    "session_id": str,                # "abc123"
    "user_id": Optional[str],         # "usr456" (if authenticated)
    "device_id": Optional[str],       # "dev_..." (3-tier auth)
    "state": AgentState               # Full conversation context
}
```

---

### Architecture Pattern

**MONOLITHIC with PROGRESS TRACKING** (not hierarchical like food_ordering)

The booking agent uses a **BookingProgress** model instead of rigid state machine:

```python
class BookingProgress(BaseModel):
    # Collected data
    party_size: Optional[int]
    date: Optional[str]
    time: Optional[str]
    special_requests: Optional[str]

    # Progress flags
    availability_checked: bool = False
    availability_result: Optional[Dict]
    user_confirmed: bool = False
    booking_created: bool = False
    booking_id: Optional[str]
    confirmation_code: Optional[str]
    sms_sent: bool = False

    # Authentication
    phone: Optional[str]
    user_id: Optional[str]
    user_name: Optional[str]
```

**Flow**:
1. Collect booking info (party_size, date, time)
2. Check availability (tool call)
3. Get user confirmation
4. Authenticate user (if not already authenticated)
5. Create booking (tool call)
6. Send SMS confirmation (automatic)

### Flow Diagram

```
                ┌──────────────────────────┐
                │   BOOKING REQUEST        │
                │ "Table for 4 tomorrow"   │
                └────────────┬─────────────┘
                             │
                             ▼
                ┌────────────────────────┐
                │ Collect Information:   │
                │ - party_size           │
                │ - date                 │
                │ - time                 │
                └────┬──────────┬────────┘
                     │          │
          Has All Info│          │Missing Info
                     │          │
                     ▼          ▼
        ┌──────────────────┐  ┌─────────────────┐
        │ Check Availabil- │  │ Ask for Missing │──┐
        │ ity              │  │ Details         │  │
        │ DB: tables,      │  └─────────────────┘  │
        │     bookings     │                        │
        └────┬────────┬────┘                        │
             │        │                             │
       Available   Not Available                    │
             │        │                             │
             ▼        ▼                             │
    ┌──────────┐  ┌─────────────┐                 │
    │Show Avail│  │Offer Wait-  │                 │
    │Tables    │  │list?        │                 │
    └─────┬────┘  └──┬──────┬───┘                 │
          │          │Yes   │No                   │
          │          ▼      ▼                      │
          │    ┌─────────┐  ┌────────┐            │
          │    │Add to   │  │BOOKING │            │
          │    │Waitlist │  │FAILED  │            │
          │    └────┬────┘  └────────┘            │
          │         │                              │
          ▼         │                              │
    ┌──────────┐   │                              │
    │Get User  │   │                              │
    │Confirma- │   │         ┌────────────────────┘
    │tion      │   │         │
    └────┬─────┘   │         │
         │         │         │
    Confirmed│Declined       │
         │         │         │
         ▼         ▼         │
    ┌─────────┐ ┌────────┐  │
    │User     │ │BOOKING │  │
    │Auth?    │ │CANCEL  │  │
    └──┬───┬──┘ └────────┘  │
     Yes│  │No               │
        │  │                 │
        │  ▼                 │
        │ ┌────────────┐    │
        │ │Authenticate│    │
        │ │User via    │    │
        │ │user_agent  │    │
        │ └────┬───┬───┘    │
        │   Success│Failed  │
        │      │   │        │
        │      │   ▼        │
        │      │ ┌────────┐ │
        │      │ │AUTH    │ │
        │      │ │REQUIRED│ │
        │      │ └────────┘ │
        ▼      ▼            │
    ┌───────────────────┐  │
    │ Create Booking    │  │
    │ DB: bookings,     │  │
    │     users         │  │
    └────┬──────┬───────┘  │
      Success│  │Failed    │
         │    ▼            │
         │  ┌────────┐    │
         │  │BOOKING │    │
         │  │FAILED  │    │
         │  └────────┘    │
         ▼                │
    ┌────────────┐        │
    │Send SMS    │        │
    │Confirmation│        │
    └─────┬──────┘        │
          │               │
          └───────────────┴────────┐
                                   │
                                   ▼
                        ┌──────────────────┐
                        │ Update State:    │
                        │ - booking_id     │
                        │ - confirm_code   │
                        └────────┬─────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │ BOOKING CONFIRMED│
                        └──────────────────┘
```

**Multi-Step Progress Tracking:**
- **Step 1**: Collect party_size, date, time (may take multiple turns)
- **Step 2**: Check table availability against existing bookings
- **Step 3**: Get explicit user confirmation ("Is this correct?")
- **Step 4**: Ensure user is authenticated (redirect to user_agent if needed)
- **Step 5**: Create booking record and assign table
- **Step 6**: Send SMS with confirmation code

**Autonomous Loops**: Agent can handle missing data, ask clarifying questions, and retry failed operations internally.

---

### Database Operations

#### Operation 1: Check Table Availability

**Tool**: `check_table_availability(date, time, party_size)`

**Tables**: `tables`, `bookings`

**SQL Query:**
```sql
-- Step 1: Get tables that can accommodate party size
SELECT
    id,
    table_number,
    capacity,
    location,
    features,
    is_active
FROM tables
WHERE capacity >= 4  -- party_size parameter
  AND is_active = true
  AND restaurant_id = 'rest001';
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | VARCHAR(20) | Table ID | "tbl001" |
| table_number | VARCHAR(20) | Display number | "A1", "Table 5" |
| capacity | INT | Max people | 4, 6, 8 |
| location | VARCHAR(100) | Table location | "Window side", "Patio" |
| features | ARRAY[VARCHAR] | Special features | ["wheelchair_accessible"] |
| is_active | BOOLEAN | Available? | true |

**Sample Result:**
```
id     | table_number | capacity | location     | features
-------|--------------|----------|--------------|----------
tbl001 | A1           | 4        | Window side  | ["quiet"]
tbl002 | A2           | 6        | Main hall    | ["wheelchair_accessible"]
tbl003 | B1           | 4        | Patio        | ["outdoor"]
```

**Step 2: Check for Booking Conflicts**

For each table found, check if it has overlapping bookings:

```sql
-- Check conflicts for table tbl001
SELECT COUNT(id)
FROM bookings
WHERE table_id = 'tbl001'
  AND status IN ('scheduled', 'confirmed')  -- Active bookings only
  AND booking_status != 'cancelled'         -- Not cancelled
  AND (
    -- Existing booking overlaps with requested time
    -- Requested: 2025-11-15 19:00 (1-hour window)
    (
      booking_datetime <= '2025-11-15 19:00:00+00'
      AND booking_datetime + INTERVAL '1 hour' > '2025-11-15 19:00:00+00'
    )
    OR
    (
      booking_datetime < '2025-11-15 20:00:00+00'
      AND booking_datetime >= '2025-11-15 19:00:00+00'
    )
  );
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| COUNT(id) | BIGINT | Number of conflicts | 0 (available), 1+ (occupied) |

**Availability Logic:**
```python
available_tables = []
for table in tables:
    # Check conflicts
    conflict_count = execute_sql(check_conflicts_query, table.id)

    if conflict_count == 0:
        # No conflicts - table is available
        available_tables.append(table)

has_availability = len(available_tables) > 0
```

---

#### Operation 2: Create Booking

**Tool**: `create_booking(date, time, party_size, phone, name, user_id, device_id, special_requests)`

**Tables**: `bookings`, `users`, `tables`

**Step 1: Find/Create User**

If `user_id` not provided, try to find existing user by phone:

```sql
SELECT
    id,
    phone_number,
    full_name,
    email,
    is_anonymous
FROM users
WHERE phone_number = '9876543210';
```

If user doesn't exist, create new user:

```sql
INSERT INTO users (
    id,
    phone_number,
    full_name,
    email,
    is_anonymous,
    phone_verified,
    created_at,
    updated_at
) VALUES (
    'usr789',           -- Generated ID
    '9876543210',
    'John Doe',
    'john@example.com',
    false,
    true,               -- Phone verified via OTP
    NOW(),
    NOW()
)
RETURNING id, phone_number, full_name;
```

**Step 2: Select Best Available Table**

From the available tables (from availability check), select the smallest table that fits:

```python
# Get available tables from Step 1 (availability check)
available_tables = [
    {"id": "tbl001", "capacity": 4, "table_number": "A1"},
    {"id": "tbl002", "capacity": 6, "table_number": "A2"},
]

# Select smallest table that fits party size
best_table = min(available_tables, key=lambda t: t['capacity'])
# Result: tbl001 (capacity 4 for party of 4)
```

**Step 3: Create Booking Record**

```sql
INSERT INTO bookings (
    id,
    user_id,
    device_id,
    restaurant_id,
    table_id,
    booking_datetime,
    party_size,
    status,
    booking_status,
    special_requests,
    contact_phone,
    contact_email,
    guest_name,
    confirmation_code,
    is_waitlisted,
    reminder_sent,
    created_at,
    updated_at
) VALUES (
    'bkg456',                           -- Generated ID
    'usr789',                           -- User ID
    'dev_abc123',                       -- Device ID (3-tier auth)
    'rest001',                          -- Restaurant ID
    'tbl001',                           -- Selected table
    '2025-11-15 19:00:00+00',          -- Booking datetime
    4,                                  -- Party size
    'scheduled',                        -- Status (lifecycle)
    'active',                           -- Booking status (modification)
    'Window seat preferred',            -- Special requests
    '9876543210',                       -- Contact phone
    'john@example.com',                 -- Contact email
    'John Doe',                         -- Guest name
    'ABC12345',                         -- Confirmation code
    false,                              -- Not waitlisted
    false,                              -- Reminder not sent yet
    NOW(),
    NOW()
)
RETURNING id, confirmation_code, booking_datetime, party_size;
```

**Columns Inserted:**
| Column | Type | Description | Value |
|--------|------|-------------|-------|
| id | VARCHAR(20) | Booking ID | "bkg456" |
| user_id | VARCHAR(20) | User who booked | "usr789" |
| device_id | VARCHAR(255) | Device (3-tier auth) | "dev_abc123" |
| restaurant_id | VARCHAR(20) | Restaurant | "rest001" |
| table_id | VARCHAR(20) | Assigned table | "tbl001" |
| booking_datetime | TIMESTAMP | Booking date/time | 2025-11-15 19:00 |
| party_size | INT | Number of people | 4 |
| status | VARCHAR(20) | Lifecycle status | "scheduled" |
| booking_status | VARCHAR(20) | Modification status | "active" |
| special_requests | TEXT | Special requests | "Window seat preferred" |
| contact_phone | VARCHAR(20) | Contact phone | "9876543210" |
| contact_email | VARCHAR(255) | Contact email | "john@example.com" |
| guest_name | VARCHAR(255) | Guest name | "John Doe" |
| confirmation_code | VARCHAR(20) | Confirmation code | "ABC12345" |
| is_waitlisted | BOOLEAN | Waitlisted? | false |
| reminder_sent | BOOLEAN | Reminder sent? | false |

**Returns:**
```
id      | confirmation_code | booking_datetime         | party_size
--------|-------------------|--------------------------|----------
bkg456  | ABC12345          | 2025-11-15 19:00:00+00  | 4
```

---

#### Operation 3: Get Booking

**Tool**: `get_booking(booking_id=None, user_id=None, device_id=None, phone=None)`

**Tables**: `bookings` (with JOINs to `users`, `tables`)

**Case A: Get Single Booking by ID**

```sql
SELECT
    b.id,
    b.booking_datetime,
    b.party_size,
    b.status,
    b.booking_status,
    b.special_requests,
    b.contact_phone,
    b.contact_email,
    b.guest_name,
    b.confirmation_code,
    b.is_waitlisted,
    b.created_at,
    b.updated_at,
    -- User data
    u.id as user_id,
    u.full_name as user_full_name,
    u.phone_number,
    u.email,
    -- Table data
    t.table_number,
    t.capacity,
    t.location
FROM bookings b
LEFT JOIN users u ON b.user_id = u.id
LEFT JOIN tables t ON b.table_id = t.id
WHERE b.id = 'bkg456';
```

**Case B: Get All Future Bookings for User**

```sql
SELECT
    b.id,
    b.booking_datetime,
    b.party_size,
    b.status,
    b.confirmation_code,
    t.table_number,
    t.capacity
FROM bookings b
LEFT JOIN tables t ON b.table_id = t.id
WHERE b.user_id = 'usr789'
  AND b.booking_status = 'active'
  AND b.booking_datetime > NOW()
ORDER BY b.booking_datetime ASC;
```

**Sample Result:**
```
id     | booking_datetime         | party_size | status    | confirmation | table_number
-------|--------------------------|------------|-----------|--------------|-------------
bkg456 | 2025-11-15 19:00:00+00  | 4          | scheduled | ABC12345     | A1
bkg789 | 2025-11-20 20:00:00+00  | 2          | confirmed | XYZ67890     | B3
```

---

#### Operation 4: Update Booking Status

**Tool**: `update_booking_status(booking_id, status)`

**Valid statuses**: `scheduled`, `confirmed`, `cancelled`, `completed`, `no_show`

```sql
UPDATE bookings
SET
    status = 'confirmed',    -- New status
    updated_at = NOW()
WHERE id = 'bkg456'
RETURNING id, status, booking_datetime;
```

---

#### Operation 5: Cancel Booking

**Tool**: `cancel_booking(booking_id, reason=None)`

```sql
UPDATE bookings
SET
    status = 'cancelled',
    booking_status = 'cancelled',  -- Also update modification status
    updated_at = NOW()
WHERE id = 'bkg456'
  AND status NOT IN ('cancelled', 'completed', 'no_show')  -- Can't cancel if already done
RETURNING id, status, booking_status;
```

---

#### Operation 6: Modify Booking

**Tool**: `modify_booking(booking_id, booking_datetime=None, party_size=None, special_requests=None)`

```sql
UPDATE bookings
SET
    booking_datetime = '2025-11-15 20:00:00+00',  -- Changed from 19:00 to 20:00
    booking_status = 'modified',                  -- Mark as modified
    updated_at = NOW()
WHERE id = 'bkg456'
  AND status NOT IN ('cancelled', 'completed', 'no_show')  -- Can only modify active bookings
RETURNING
    id,
    booking_datetime,
    party_size,
    special_requests,
    booking_status;
```

---

### Output Format

#### Case 1: Availability Check - Available

```python
{
    "has_availability": True,
    "total_available": 3,
    "available_tables": [
        {
            "table_id": "tbl001",
            "table_number": "A1",
            "capacity": 4,
            "location": "Window side",
            "features": ["quiet"]
        },
        {
            "table_id": "tbl002",
            "table_number": "A2",
            "capacity": 6,
            "location": "Main hall",
            "features": ["wheelchair_accessible"]
        },
        {
            "table_id": "tbl003",
            "table_number": "B1",
            "capacity": 4,
            "location": "Patio",
            "features": ["outdoor"]
        }
    ],
    "requested_party_size": 4,
    "requested_datetime": "2025-11-15T19:00:00+00:00",
    "waitlist_available": False
}
```

#### Case 2: Availability Check - Not Available

```python
{
    "has_availability": False,
    "total_available": 0,
    "available_tables": [],
    "requested_party_size": 8,
    "requested_datetime": "2025-11-15T19:00:00+00:00",
    "waitlist_available": True,
    "message": "No tables available for party size 8"
}
```

#### Case 3: Booking Created Successfully

```python
{
    "success": True,
    "booking_id": "bkg456",
    "confirmation_code": "ABC12345",
    "status": "scheduled",
    "booking_datetime": "2025-11-15T19:00:00+00:00",
    "party_size": 4,
    "guest_name": "John Doe",
    "contact_phone": "9876543210",
    "contact_email": "john@example.com",
    "special_requests": "Window seat preferred",
    "is_waitlisted": False,
    "table_info": {
        "table_id": "tbl001",
        "table_number": "A1",
        "capacity": 4,
        "location": "Window side"
    },
    "email_sent": False,  # Email is optional backup channel
    "sms_will_be_sent": True  # SMS sent automatically in next step
}
```

#### Case 4: Booking Failed - No Tables Available

```python
{
    "success": True,  # Note: Still success for waitlist
    "booking_id": "bkg789",
    "confirmation_code": "WL12345",
    "status": "waitlisted",
    "is_waitlisted": True,
    "message": "No tables available, added to waitlist",
    "booking_datetime": "2025-11-15T19:00:00+00:00",
    "party_size": 8,
    "guest_name": "Jane Smith",
    "contact_phone": "9876543211",
    "contact_email": None,
    "special_requests": None
}
```

#### Case 5: Get Booking - Found

```python
{
    "found": True,
    "booking_id": "bkg456",
    "confirmation_code": "ABC12345",
    "booking_datetime": "2025-11-15T19:00:00+00:00",
    "party_size": 4,
    "status": "scheduled",
    "booking_status": "active",
    "guest_name": "John Doe",
    "contact_phone": "9876543210",
    "contact_email": "john@example.com",
    "special_requests": "Window seat preferred",
    "is_waitlisted": False,
    "created_at": "2025-11-13T10:30:00+00:00",
    "updated_at": "2025-11-13T10:30:00+00:00",
    "user_id": "usr789",
    "device_id": "dev_abc123",
    "table_info": {
        "table_id": "tbl001",
        "table_number": "A1",
        "capacity": 4,
        "location": "Window side"
    }
}
```

#### Case 6: Cancel Booking - Success

```python
{
    "success": True,
    "booking_id": "bkg456",
    "old_status": "scheduled",
    "new_status": "cancelled",
    "cancellation_reason": "User cancellation",
    "cancelled_at": "2025-11-14T08:00:00+00:00",
    "booking_datetime": "2025-11-15T19:00:00+00:00",
    "party_size": 4,
    "confirmation_code": "ABC12345"
}
```

#### Case 7: Modify Booking - Success

```python
{
    "success": True,
    "booking_id": "bkg456",
    "modified_fields": ["booking_datetime"],
    "old_values": {
        "booking_datetime": "2025-11-15T19:00:00+00:00",
        "party_size": 4,
        "special_requests": "Window seat preferred"
    },
    "new_values": {
        "booking_datetime": "2025-11-15T20:00:00+00:00",
        "party_size": 4,
        "special_requests": "Window seat preferred"
    },
    "status": "scheduled",
    "booking_status": "modified",
    "confirmation_code": "ABC12345"
}
```

#### Case 8: Booking Failed - User Not Authenticated

```python
{
    "success": False,
    "error_type": "authentication_required",
    "message": "You must be logged in to place a booking",
    "required_action": "authenticate",
    "suggested_flow": "Please provide your phone number to continue"
}
```

---

## 3. payment_agent

### Purpose
Handle payment processing with Razorpay integration - create payment links, check status, manage payment lifecycle

### Use Cases
```
✓ "I need to pay for my order ORD-123"
✓ "Send me payment link"
✓ "Check payment status"
✓ "Retry my payment"
✓ "I want to pay now"
```

### Input Required
```python
{
    "order_id": str,                  # Required: "ord_789abc"
    "user_id": str,                   # Required: "usr456"
    "phone": Optional[str],           # For SMS/WhatsApp link sending
    "payment_source": str,            # "chat" or "external"
    "session_id": Optional[str],      # Required if payment_source="chat"
    "state": AgentState               # Full conversation context
}
```

---

### Critical Security Rules

**PAYMENT AMOUNTS ARE DETERMINISTIC - NEVER HALLUCINATED**

- Payment amounts come ONLY from the Order database record
- LLM NEVER provides or guesses payment amounts
- Tools automatically fetch amounts from `orders.total_amount`
- This prevents amount tampering and hallucination
- LLM only provides `order_id` and `user_id` - not amounts

**Tool Signatures** (note what's NOT provided):
```python
create_payment_order(order_id, user_id)  # NO amount parameter!
send_payment_link_sms(payment_order_id, phone)  # NO amount/link parameters!
send_payment_link_whatsapp(payment_order_id, phone)  # NO amount/link parameters!
```

### Flow Diagram

```
           ┌────────────────────────────┐
           │   PAYMENT REQUEST          │
           │ "Pay for order ORD-123"    │
           └─────────────┬──────────────┘
                         │
                         ▼
           ┌─────────────────────────┐
           │ Fetch Order             │
           │ DB: orders              │
           │ CRITICAL: Get Amount    │
           └──────┬──────────────────┘
                  │
        ┌─────────┴─────────┐
      Found│              │Not Found
           │              │
           ▼              ▼
┌──────────────────┐  ┌────────────┐
│Get total_amount  │  │ERROR:      │──┐
│FROM DATABASE ONLY│  │Order Not   │  │
│(NEVER from LLM!) │  │Found       │  │
└────────┬─────────┘  └────────────┘  │
         │                             │
         ▼                             │
┌──────────────────┐                  │
│Convert to Paise  │                  │
│amount * 100      │                  │
└────────┬─────────┘                  │
         │                             │
         ▼                             │
┌──────────────────┐                  │
│Create Razorpay   │                  │
│Order (External   │                  │
│API Call)         │                  │
└──────┬───────────┘                  │
       │                               │
  ┌────┴────┐                         │
Success│   │Failed                    │
       │   │                          │
       │   ▼                          │
       │ ┌────────────┐               │
       │ │ERROR:      │───────────────┤
       │ │Payment     │               │
       │ │Creation    │               │
       │ └────────────┘               │
       ▼                               │
┌──────────────────┐                  │
│Generate Payment  │                  │
│Link (Razorpay)   │                  │
└──────┬───────────┘                  │
       │                               │
  ┌────┴────┐                         │
Success│   │Failed                    │
       │   │                          │
       │   ▼                          │
       │ ┌────────────┐               │
       │ │ERROR:      │───────────────┤
       │ │Link Gen    │               │
       │ │Failed      │               │
       │ └────────────┘               │
       ▼                               │
┌──────────────────┐                  │
│ Save to DB:      │                  │
│ payment_orders   │                  │
└──────┬───────────┘                  │
       │                               │
       ▼                               │
┌──────────────────┐                  │
│ Send Method?     │                  │
└──┬────┬─────┬────┘                  │
   │    │     │                       │
 SMS│ WA│  None│                      │
   │    │     │                       │
   ▼    ▼     ▼                       │
┌────┐┌────┐┌────────┐                │
│Send││Send││Return  │                │
│SMS ││WA  ││Link    │                │
│    ││    ││Only    │                │
└─┬──┘└─┬──┘└───┬────┘                │
  │     │       │                     │
  └─────┴───────┴────┐                │
                     │                │
                     ▼                │
           ┌──────────────────┐      │
           │ PAYMENT LINK SENT│      │
           └─────────┬────────┘      │
                     │                │
                     ├────────────────┘
                     │
                     ▼
           ┌──────────────────┐
           │   ActionResult   │
           └──────────────────┘
```

**Security-First Flow:**
1. **Fetch Order** from database (NEVER trust LLM for amount)
2. **Get total_amount** from `orders.total_amount` column
3. **Create Razorpay Order** with database amount
4. **Generate Payment Link** with 15-minute expiry
5. **Save to payment_orders** table
6. **Send Link** via SMS/WhatsApp (fetching amount from DB again)

**Key Security Controls:**
- ❌ LLM NEVER provides payment amounts
- ✅ Amount ALWAYS from `orders.total_amount`
- ✅ SMS/WhatsApp tools fetch amount from `payment_orders` (not LLM)
- ✅ Double-fetch pattern prevents any hallucination

---

### Database Operations

#### Operation 1: Create Payment Order

**Tool**: `create_payment_order(order_id, user_id, payment_source="external", session_id=None)`

**Tables**: `orders`, `payment_orders`

**Step 1: Fetch Order Amount from Database**

CRITICAL: Amount is ALWAYS from database, never from LLM:

```sql
SELECT
    id,
    order_number,
    user_id,
    total_amount,
    status,
    order_type
FROM orders
WHERE id = 'ord_789abc';
```

**Columns Fetched:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | VARCHAR(20) | Order ID | "ord_789abc" |
| order_number | VARCHAR(20) | Display number | "ABC141030" |
| user_id | VARCHAR(20) | User who ordered | "usr456" |
| total_amount | DECIMAL(10,2) | **Source of truth** | 908.50 |
| status | VARCHAR(20) | Order status | "confirmed" |
| order_type | VARCHAR(20) | dine_in/takeout | "dine_in" |

**Sample Result:**
```
id          | order_number | total_amount | status    | order_type
------------|--------------|--------------|-----------|----------
ord_789abc  | ABC141030    | 908.50       | confirmed | dine_in
```

**Step 2: Create Razorpay Order (External API)**

Convert amount to paise (Razorpay requirement):

```python
amount_paise = int(total_amount * 100)  # 908.50 → 90850 paise
```

**Razorpay API Call:**
```python
import razorpay

razorpay_client = razorpay.Client(auth=(api_key, api_secret))

razorpay_order = razorpay_client.order.create({
    "amount": 90850,  # Amount in paise from database
    "currency": "INR",
    "receipt": "ord_789abc",  # Order ID as receipt
    "notes": {
        "order_number": "ABC141030",
        "user_id": "usr456",
        "order_type": "dine_in"
    }
})

# Returns:
{
    "id": "order_NuxZqQCp4f0123",  # Razorpay order ID
    "amount": 90850,
    "currency": "INR",
    "status": "created",
    "created_at": 1731501000
}
```

**Step 3: Generate Payment Link (Razorpay)**

```python
razorpay_link = razorpay_client.payment_link.create({
    "amount": 90850,
    "currency": "INR",
    "description": f"Payment for order {order_number}",
    "customer": {
        "phone": "+919876543210",
        "name": "John Doe"
    },
    "notify": {
        "sms": False,  # We send our own SMS
        "email": False  # We send our own email
    },
    "callback_url": f"https://restaurant.com/payment/callback?session_id={session_id}",
    "callback_method": "get",
    "expire_by": int(time.time()) + 900,  # 15 minutes
    "reference_id": razorpay_order["id"]
})

# Returns:
{
    "id": "plink_NuxZz9pjXs4567",  # Payment link ID
    "short_url": "https://rzp.io/i/abc123",  # Short payment link
    "reference_id": "order_NuxZqQCp4f0123",
    "status": "created",
    "amount": 90850,
    "expire_by": 1731501900
}
```

**Step 4: Create Payment Order Record**

```sql
INSERT INTO payment_orders (
    id,
    order_id,
    user_id,
    razorpay_order_id,
    razorpay_payment_link_id,
    payment_link,
    amount,
    currency,
    status,
    callback_url,
    callback_method,
    payment_source,
    session_id,
    retry_count,
    max_retry_attempts,
    expires_at,
    created_at,
    updated_at
) VALUES (
    'pmt_order_123',                     -- Generated ID
    'ord_789abc',                        -- Order ID
    'usr456',                            -- User ID
    'order_NuxZqQCp4f0123',             -- Razorpay order ID
    'plink_NuxZz9pjXs4567',             -- Razorpay link ID
    'https://rzp.io/i/abc123',          -- Short URL
    90850,                               -- Amount in paise
    'INR',                               -- Currency
    'created',                           -- Status
    'https://restaurant.com/payment/callback',  -- Callback URL
    'GET',                               -- Callback method
    'chat',                              -- Payment source
    'sess_abc123',                       -- Session ID
    0,                                   -- Retry count
    3,                                   -- Max retries
    '2025-11-14 10:45:00+00',           -- Expires at
    NOW(),
    NOW()
)
RETURNING id, payment_link, amount, expires_at;
```

**Columns Inserted:**
| Column | Type | Description | Value |
|--------|------|-------------|-------|
| id | VARCHAR(20) | Payment order ID | "pmt_order_123" |
| order_id | VARCHAR(20) | Restaurant order | "ord_789abc" |
| user_id | VARCHAR(20) | User | "usr456" |
| razorpay_order_id | VARCHAR(100) | Razorpay order | "order_NuxZqQCp4f0123" |
| razorpay_payment_link_id | VARCHAR(100) | Razorpay link | "plink_NuxZz9pjXs4567" |
| payment_link | TEXT | Short URL | "https://rzp.io/i/abc123" |
| amount | BIGINT | Amount (paise) | 90850 |
| currency | VARCHAR(3) | Currency | "INR" |
| status | VARCHAR(20) | Status | "created" |
| payment_source | VARCHAR(20) | Source | "chat" or "external" |
| session_id | VARCHAR(50) | Session | "sess_abc123" |
| retry_count | INT | Retry attempts | 0 |
| max_retry_attempts | INT | Max retries | 3 |
| expires_at | TIMESTAMP | Link expiry | 15 min from now |

---

#### Operation 2: Send Payment Link via SMS

**Tool**: `send_payment_link_sms(payment_order_id, phone)`

**Tables**: `payment_orders`, `orders`

**Step 1: Fetch Payment Details from Database**

CRITICAL: Amount and link from database (not LLM):

```sql
SELECT
    po.id,
    po.payment_link,
    po.amount,
    po.status,
    po.expires_at,
    o.order_number,
    o.total_amount
FROM payment_orders po
JOIN orders o ON po.order_id = o.id
WHERE po.id = 'pmt_order_123';
```

**Sample Result:**
```
id            | payment_link              | amount | order_number | total_amount
--------------|---------------------------|--------|--------------|-------------
pmt_order_123 | https://rzp.io/i/abc123  | 90850  | ABC141030    | 908.50
```

**Step 2: Convert Paise to Rupees**

```python
amount_rupees = float(amount_paise) / 100  # 90850 → 908.50
```

**Step 3: Send SMS**

```python
from app.services.sms_service import SMSService

sms_service = SMSService()

message = f"""Payment link for your order {order_number} (₹{amount_rupees:.2f}): {payment_link}

Link expires in 15 minutes."""

sms_result = await sms_service.send_notification(
    phone_number="+919876543210",
    message=message,
    notification_type="payment_link"
)
```

---

#### Operation 3: Check Payment Status

**Tool**: `check_payment_status(order_id=None, payment_order_id=None)`

**Tables**: `payment_orders`, `payment_transactions`

```sql
SELECT
    po.id as payment_order_id,
    po.razorpay_order_id,
    po.payment_link,
    po.amount,
    po.status,
    po.retry_count,
    po.max_retry_attempts,
    po.expires_at,
    po.created_at,
    o.order_number
FROM payment_orders po
JOIN orders o ON po.order_id = o.id
WHERE po.id = 'pmt_order_123'
   OR po.order_id = 'ord_789abc';
```

**Get Latest Transaction:**
```sql
SELECT
    id,
    razorpay_payment_id,
    status,
    method,
    amount_paid,
    fee,
    created_at,
    updated_at
FROM payment_transactions
WHERE payment_order_id = 'pmt_order_123'
ORDER BY created_at DESC
LIMIT 1;
```

---

#### Operation 4: Retry Payment

**Tool**: `retry_payment(payment_order_id)`

**Tables**: `payment_orders`

**Step 1: Check Retry Eligibility**

```sql
SELECT
    id,
    retry_count,
    max_retry_attempts,
    status,
    amount
FROM payment_orders
WHERE id = 'pmt_order_123';
```

**Retry Logic:**
```python
if retry_count >= max_retry_attempts:
    return {"success": False, "message": "Maximum retry limit reached"}

if status == "paid":
    return {"success": False, "message": "Payment already completed"}
```

**Step 2: Increment Retry Count**

```sql
UPDATE payment_orders
SET
    retry_count = retry_count + 1,
    updated_at = NOW()
WHERE id = 'pmt_order_123'
RETURNING id, retry_count;
```

**Step 3: Generate New Payment Link**

Same as Operation 1 (Razorpay API call) - creates new link with same amount.

---

### Output Format

#### Case 1: Payment Order Created Successfully

```python
{
    "success": True,
    "payment_order_id": "pmt_order_123",
    "razorpay_order_id": "order_NuxZqQCp4f0123",
    "payment_link": "https://rzp.io/i/abc123",
    "amount": 908.50,  # Rupees (converted from paise)
    "expires_at": "2025-11-14T10:45:00+00:00",
    "message": "Payment link created for ₹908.50"
}
```

#### Case 2: Payment Link Sent via SMS

```python
{
    "success": True,
    "message": "Payment link sent to +919876543210 via SMS",
    "amount": 908.50,
    "order_number": "ABC141030"
}
```

#### Case 3: Payment Status Check - Pending

```python
{
    "success": True,
    "payment_order_id": "pmt_order_123",
    "razorpay_order_id": "order_NuxZqQCp4f0123",
    "status": "created",  # Awaiting payment
    "amount": 908.50,
    "payment_link": "https://rzp.io/i/abc123",
    "expires_at": "2025-11-14T10:45:00+00:00",
    "retry_count": 0,
    "can_retry": True,
    "latest_transaction": None,
    "message": "Payment pending - awaiting customer payment"
}
```

#### Case 4: Payment Status Check - Paid

```python
{
    "success": True,
    "payment_order_id": "pmt_order_123",
    "razorpay_order_id": "order_NuxZqQCp4f0123",
    "status": "paid",  # Payment successful
    "amount": 908.50,
    "payment_link": "https://rzp.io/i/abc123",
    "retry_count": 0,
    "can_retry": False,
    "latest_transaction": {
        "id": "txn_456",
        "razorpay_payment_id": "pay_NuxaAbc123",
        "status": "captured",
        "method": "upi",
        "amount_paid": 90850,  # Paise
        "fee": 1817,  # Razorpay fee in paise
        "created_at": "2025-11-14T10:35:00+00:00"
    },
    "message": "Payment successful"
}
```

#### Case 5: Payment Status Check - Failed

```python
{
    "success": True,
    "payment_order_id": "pmt_order_123",
    "status": "failed",
    "amount": 908.50,
    "retry_count": 1,
    "can_retry": True,
    "latest_transaction": {
        "id": "txn_789",
        "status": "failed",
        "method": "card",
        "error_code": "BAD_REQUEST_ERROR",
        "error_description": "Payment failed due to insufficient funds",
        "created_at": "2025-11-14T10:32:00+00:00"
    },
    "message": "Payment failed"
}
```

#### Case 6: Retry Payment - Success

```python
{
    "success": True,
    "payment_link": "https://rzp.io/i/def456",  # New link
    "retry_count": 2,
    "expires_at": "2025-11-14T11:00:00+00:00",
    "message": "Payment retry #2 - new link generated"
}
```

#### Case 7: Retry Payment - Max Retries Reached

```python
{
    "success": False,
    "message": "Maximum retry limit reached (3 attempts)",
    "can_retry": False,
    "retry_count": 3
}
```

#### Case 8: Payment History

```python
{
    "success": True,
    "payment_history": [
        {
            "payment_order_id": "pmt_order_123",
            "order_number": "ABC141030",
            "razorpay_order_id": "order_NuxZqQCp4f0123",
            "amount": 908.50,
            "status": "paid",
            "created_at": "2025-11-14T10:30:00+00:00",
            "latest_transaction": {
                "razorpay_payment_id": "pay_NuxaAbc123",
                "status": "captured",
                "method": "upi",
                "created_at": "2025-11-14T10:35:00+00:00"
            }
        },
        {
            "payment_order_id": "pmt_order_456",
            "order_number": "ABC151045",
            "amount": 1250.00,
            "status": "created",  # Pending
            "created_at": "2025-11-15T10:45:00+00:00"
        }
    ],
    "total_count": 2,
    "filters": {
        "user_id": "usr456",
        "limit": 10
    }
}
```

---

## 4. user_agent

### Purpose
Handle user authentication via OTP, registration for new users, profile management with comprehensive error handling and rate limiting

### Use Cases
```
✓ "I want to login"
✓ "Create an account"
✓ "Send OTP to my phone"
✓ "My OTP code is 123456"
✓ "Resend OTP"
✓ "Update my profile"
✓ "View my order history"
```

### Input Required
```python
{
    "user_message": str,              # User's request
    "device_id": Optional[str],       # Device fingerprint for rate limiting
    "user_id": Optional[str],         # If already authenticated
    "state": AgentState               # Full conversation context
}
```

---

### Key Features

**3-Tier Authentication System:**
- Tier 1: Anonymous (no device_id)
- Tier 2: Recognized device (device_id, no auth) - soft personalization
- Tier 3: Authenticated (session_token or recent OTP) - full personalization

**Comprehensive Rate Limiting:**
- Session limit: 3 OTP sends per session
- Daily limit: 10 OTP sends per phone number per day
- OTP verification: 3 attempts per OTP code
- Auto-lockout: 15 minutes after excessive failures

**Multi-Step Flow with Progress Tracking:**
Phone validation → Phone confirmation → User check → OTP send → OTP verify → Register/Authenticate

### Flow Diagram

```
         ┌─────────────────────┐
         │  AUTH REQUEST       │
         │ "I want to login"   │
         └──────────┬──────────┘
                    │
                    ▼
         ┌──────────────────────┐
         │ Validate Phone Format│
         │ (10 digits, 6/7/8/9) │
         └────┬───────────┬─────┘
              │           │
          Valid│        │Invalid
              │           │
              ▼           ▼
    ┌──────────────┐  ┌────────┐
    │Confirm with  │  │ERROR:  │
    │User          │  │Invalid │
    └───┬──────┬───┘  │Phone   │
        │      │      └────────┘
   Confirmed│  │Declined
        │      │
        │      └──────┐
        ▼             │
 ┌─────────────┐      │
 │Check User   │      │
 │Exists       │◄─────┘
 │DB: users    │
 └──────┬──────┘
        │
        ▼
 ┌───────────────────────┐
 │  Rate Limit Check     │
 │  Redis Checks         │
 └┬────┬──────────┬──────┘
  │    │          │
Session│Daily   │OK
Limit│ Limit    │
  │    │          │
  ▼    ▼          ▼
┌───┐┌───┐  ┌──────────────┐
│ERR││ERR│  │Generate &    │
│   ││   │  │Send OTP      │
└───┘└───┘  │DB: otp_codes │
             │SMS Service   │
             └──────┬───────┘
               Success│Failed
                    │  │
                    │  ▼
                    │┌─────┐
                    ││ERROR│
                    │└─────┘
                    ▼
             ┌──────────────┐
             │ Verify OTP   │
             │ DB: otp_codes│
             └─────┬────────┘
                   │
          ┌────────┴─────────┐
        Valid│            │Invalid
             │               │
             │               ▼
             │        ┌──────────┐
             │        │Attempts  │
             │        │< 3?      │
             │        └──┬───┬───┘
             │         Yes│ │No
             │            │ │
             │            │ ▼
             │            │┌────────┐
             │            ││LOCKOUT │
             │            ││15 min  │
             │            │└────────┘
             │            │
             │            └────┐
             │                 │
             ▼                 │
      ┌─────────────┐          │
      │New or       │          │
      │Existing?    │          │
      └──┬──────┬───┘          │
    New│    │Existing         │
        │       │              │
        ▼       ▼              │
  ┌────────┐ ┌────────────┐   │
  │Collect │ │Update Last │   │
  │Name    │ │Login       │   │
  └───┬────┘ │DB: users   │   │
      │      └─────┬──────┘   │
      ▼            │           │
  ┌────────┐      │           │
  │Create  │      │           │
  │User    │      │           │
  └───┬────┘      │           │
      │           │           │
      └───────┬───┘           │
              │               │
              ▼               │
       ┌──────────────┐       │
       │Link Device   │       │
       │DB: user_     │       │
       │    devices   │       │
       └──────┬───────┘       │
              │               │
              ▼               │
       ┌──────────────┐       │
       │Generate Token│       │
       │30-day JWT    │       │
       └──────┬───────┘       │
              │               │
              ▼               │
       ┌──────────────┐       │
       │ AUTH SUCCESS │       │
       └──────┬───────┘       │
              │               │
              ├───────────────┘
              │
              ▼
       ┌──────────────┐
       │Return user_id│
       │session_token │
       └──────────────┘
```

**OTP Authentication Flow (Step-by-Step):**
1. **Phone Validation**: Check format (10 digits, starts with 6/7/8/9)
2. **Phone Confirmation**: "I'll send OTP to +91XXXXXXXXXX. Is this correct?"
3. **User Check**: Query `users` table by phone_number
4. **Rate Limit Check**:
   - Redis: `auth_session:{device_id}` → 3 OTPs/session
   - Redis: `daily_otp:{phone}:{date}` → 10 OTPs/day
5. **Send OTP**: Generate 6-digit code, save to `otp_codes`, send SMS
6. **Verify OTP**: Check code, track attempts (max 3)
7. **Lockout**: 15-minute lockout after 3 failed attempts
8. **Register/Auth**: Create user (if new) or update last_login (if existing)
9. **Generate Token**: 30-day JWT session token

**Rate Limiting (Redis):**
- `auth_session:{device_id}` → Session state (OTP count, lockout)
- `daily_otp:{phone}:{date}` → Daily OTP counter (24h TTL)

---

### Output Format (Summary - For complete SQL/Database details, see similar patterns in agents above)

#### Case 1: OTP Sent Successfully

```python
{
    "success": True,
    "otp_id": "otp_abc123",
    "phone_number": "+919876543210",
    "expires_in": "10 minutes",
    "message": "OTP sent to +919876543210"
}
```

#### Case 2: OTP Verification - Success

```python
{
    "success": True,
    "verified": True,
    "phone_number": "+919876543210",
    "message": "Phone number verified successfully"
}
```

#### Case 3: Account Locked

```python
{
    "success": False,
    "locked": True,
    "message": "Too many failed attempts. Please try again in 15 minutes.",
    "locked_until": "2025-11-14T11:15:00+00:00"
}
```

#### Case 4: User Created

```python
{
    "success": True,
    "user_id": "usr789",
    "session_token": "eyJhbG...",
    "message": "Welcome, John Doe! Account created successfully."
}
```

#### Case 5: Authentication Complete

```python
{
    "success": True,
    "user_id": "usr456",
    "session_token": "eyJhbG...",
    "token_expires_at": "2025-12-14T10:30:00+00:00",
    "message": "Welcome back, John Doe!"
}
```

---

## 5. customer_satisfaction_agent

### Purpose
Handle customer complaints, feedback collection, and NPS (Net Promoter Score) tracking

### Use Cases
```
✓ "I want to file a complaint"
✓ "Food was cold"
✓ "Give feedback about my experience"
✓ "Rate my visit"
```

### Key Database Operations

**Tables**: `complaints`, `feedbacks`, `ratings`

**Operation 1: Create Complaint**
```sql
INSERT INTO complaints (
    id, user_id, order_id, booking_id,
    complaint_type,  -- food_quality, service, cleanliness, billing
    description, priority, status,
    assigned_to, resolution_notes
) VALUES (...)
RETURNING id, status, priority;
```

**Operation 2: Submit Feedback**
```sql
INSERT INTO feedbacks (
    id, user_id, order_id, booking_id,
    rating, comments, feedback_type,
    is_public
) VALUES (...)
RETURNING id, rating;
```

**Operation 3: Record NPS Score**
```sql
INSERT INTO ratings (
    id, user_id, order_id,
    overall_rating,  -- 1-10 scale
    food_rating, service_rating, ambience_rating,
    comments, nps_category  -- promoter (9-10), passive (7-8), detractor (0-6)
) VALUES (...)
RETURNING id, nps_category;
```

### Output Format

```python
{
    "success": True,
    "complaint_id": "cmp_123",
    "status": "open",
    "priority": "high",
    "message": "We're sorry to hear that. Your complaint has been registered and will be addressed within 24 hours."
}
```

---

## 6. support_agent

### Purpose
Provide general restaurant information - hours, location, directions, policies

### Use Cases
```
✓ "What are your hours?"
✓ "Where are you located?"
✓ "How do I get there?"
✓ "What's your cancellation policy?"
✓ "Do you have parking?"
```

### Key Database Operations

**Tables**: `restaurant_config`, `faqs`

**Operation 1: Get Restaurant Details**
```sql
SELECT
    name, description, address, phone, email,
    business_hours,  -- JSON: {"monday": {"open": "09:00", "close": "22:00"}, ...}
    policies          -- JSON: {"cancellation": "...", "refund": "...", "parking": "..."}
FROM restaurant_config
WHERE id = 'rest001';
```

**Sample business_hours JSON:**
```json
{
    "monday": {"open": "09:00", "close": "22:00", "closed": false},
    "tuesday": {"open": "09:00", "close": "22:00", "closed": false},
    "sunday": {"open": "10:00", "close": "21:00", "closed": false}
}
```

**Sample policies JSON:**
```json
{
    "cancellation": "Free cancellation up to 2 hours before booking time",
    "refund": "Refunds processed within 5-7 business days",
    "parking": "Free valet parking available",
    "dress_code": "Smart casual"
}
```

### Output Format

```python
{
    "restaurant_name": "The Golden Spoon",
    "address": "123 Main Street, Mumbai, Maharashtra 400001",
    "phone": "+91 22 1234 5678",
    "business_hours": {
        "today": {"open": "09:00", "close": "22:00", "is_open_now": True},
        "full_week": {...}
    },
    "directions": "Located near CST Railway Station. Valet parking available.",
    "policies": {
        "cancellation": "Free cancellation up to 2 hours before",
        "parking": "Free valet parking"
    }
}
```

---

## 7. general_queries_agent

### Purpose
Answer FAQs using semantic search over knowledge base

### Use Cases
```
✓ "Do you have WiFi?"
✓ "Are pets allowed?"
✓ "Do you deliver?"
✓ "What payment methods do you accept?"
✓ "Is there a kids menu?"
```

### Key Database Operations

**Tables**: `faqs` (with pgvector embeddings)

**Operation 1: Semantic FAQ Search**
```sql
SELECT
    id, question, answer, category,
    tags,  -- ARRAY: ["wifi", "facilities"]
    embedding <=> query_embedding AS similarity  -- Cosine similarity
FROM faqs
WHERE is_active = true
ORDER BY embedding <=> query_embedding  -- Vector similarity search
LIMIT 5;
```

**Columns:**
| Column | Type | Description | Example |
|--------|------|-------------|---------|
| id | VARCHAR(20) | FAQ ID | "faq_001" |
| question | TEXT | FAQ question | "Do you have WiFi?" |
| answer | TEXT | FAQ answer | "Yes, free WiFi for all guests" |
| category | VARCHAR(50) | Category | "facilities" |
| tags | ARRAY[VARCHAR] | Search tags | ["wifi", "internet"] |
| embedding | VECTOR(1536) | Semantic embedding | [0.123, -0.456, ...] |

### Output Format

```python
{
    "found": True,
    "faqs": [
        {
            "question": "Do you have WiFi?",
            "answer": "Yes, we offer free high-speed WiFi for all guests. Network name: GoldenSpoon_Guest",
            "category": "facilities",
            "relevance_score": 0.95
        }
    ],
    "count": 1
}
```

---

## 8. response_agent (Virtual Waiter)

### Purpose
Transform structured ActionResults from specialist agents into warm, friendly, hospitality-focused responses

### Architecture Pattern

**FORMATTING LAYER** - Not a decision-making agent

The response_agent is the final layer that takes structured data from specialist agents and reformats it with personality.

**Flow:**
1. Specialist agent (e.g., food_ordering) returns structured `ActionResult`:
   ```python
   ActionResult(
       action="cart_add_item",
       success=True,
       data={"item_name": "Butter Chicken", "quantity": 2, "price": 450.00}
   )
   ```

2. Response agent receives ActionResult and applies personality:
   - Detects action type (`cart_add_item`)
   - Loads appropriate prompt template
   - Formats data with Virtual Waiter personality
   - Adds upsell suggestions if applicable

3. Returns warm, conversational response:
   ```
   "Great choice! I've added 2 servings of Butter Chicken (₹450.00 each) to your order.

   That's a popular dish! Pairs wonderfully with our Garlic Naan.
   Would you like to add that?"
   ```

### Flow Diagram

```
    ┌──────────────────────────┐
    │   ActionResult from      │
    │   Specialist Agent       │
    └────────────┬─────────────┘
                 │
                 ▼
    ┌────────────────────────┐
    │  Extract Action Type   │
    │       & Data           │
    └────────────┬───────────┘
                 │
                 ▼
         ┌───────────────┐
         │ Map Action to │
         │   Template    │
         └───┬───────┬───┘
             │       │
      ┌──────┴──┐ ┌──┴─────┐
   Success│   Error│  Info
   Action│   Action│  Action
      │       │       │
      ▼       ▼       ▼
 ┌─────────┐ ┌─────┐ ┌─────┐
 │ Success │ │Error│ │Info │
 │Template │ │Temp │ │Temp │
 └────┬────┘ └──┬──┘ └──┬──┘
      │         │       │
      ▼         │       │
 ┌─────────┐   │       │
 │Should   │   │       │
 │Upsell?  │   │       │
 └──┬───┬──┘   │       │
   Yes│ │No     │       │
      │ │       │       │
      ▼ │       │       │
 ┌─────────┐   │       │
 │Add      │   │       │
 │Upsell   │   │       │
 │Suggest. │   │       │
 └────┬────┘   │       │
      │        │       │
      └────┬───┴───────┘
           │
           ▼
    ┌──────────────────┐
    │ Apply Virtual    │
    │ Waiter           │
    │ Personality      │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ Format with LLM: │
    │ Warm, Casual,    │
    │ Conversational   │
    └────────┬─────────┘
             │
             ▼
    ┌──────────────────┐
    │ FRIENDLY RESPONSE│
    │    TO USER       │
    └──────────────────┘
```

**Response Agent Flow:**
1. **Receive ActionResult** from specialist agent (structured data)
2. **Extract Action Type**: "cart_add_item", "booking_confirmed", "otp_sent", etc.
3. **Map to Template**: Select from 30+ pre-defined templates
4. **Check Upsell Logic**: Based on action type and cart state
5. **Apply Personality**: Use Virtual Waiter prompt
6. **Format with LLM**: Transform structured data → natural language
7. **Return Response**: Warm, conversational message to user

**Template Categories:**
- **Success Templates** (20): item_added, booking_confirmed, payment_sent, etc.
- **Error Templates** (15): out_of_stock, invalid_data, database_error, etc.
- **Info Templates** (10): cart_view, menu_display, booking_details, etc.

**NO Database Access** - Pure formatting layer, receives all data from previous agents.

### Key Operations

**No Database Operations** - Pure formatting layer

**Operation 1: Action-to-Prompt Mapping**

Maps 30+ action types to specific prompt templates:

```python
PROMPT_TEMPLATES = {
    "cart_add_item": "Item added successfully template...",
    "cart_view": "Display cart summary template...",
    "booking_confirmed": "Booking confirmation template...",
    "payment_link_sent": "Payment link sent template...",
    "otp_sent": "OTP sent template...",
    # ... 25 more templates
}
```

**Operation 2: Upsell Logic**

```python
def should_upsell(action: str, cart_items: List) -> bool:
    # Upsell triggers:
    # - After adding appetizer → suggest drinks
    # - After adding main course → suggest sides
    # - Cart total > ₹500 → suggest dessert
    # - Dine-in order → suggest chef specials
```

**Operation 3: Error Template Selection**

```python
ERROR_TEMPLATES = {
    "database_error": "Oops, hiccup template...",
    "invalid_data_error": "Double-check that template...",
    "inventory_error": "Unfortunately sold out template...",
    # ... 15 error templates
}
```

### Virtual Waiter Personality Traits

- **Warm & Casual**: "Great choice!" instead of "Item added"
- **Proactive**: Suggests pairings and upsells
- **Empathetic**: "I totally understand" for issues
- **Conversational**: Uses natural language, not robotic responses
- **Hospitality-focused**: Makes guests feel valued

### Output Format

The response_agent returns the final formatted message that goes directly to the user:

```python
{
    "agent_response": "Great choice! I've added 2 servings of Butter Chicken to your cart...",
    "formatted": True,
    "personality_applied": "virtual_waiter"
}
```

---

## Summary

This document provides complete data flow reference for all 8 agents in the restaurant AI assistant:

1. **food_ordering_agent** (Hierarchical) - 5 sub-agents for menu, cart, checkout
2. **booking_agent** (Monolithic) - Table reservations with availability checking
3. **payment_agent** (Autonomous) - Razorpay integration with security controls
4. **user_agent** (Progressive Auth) - OTP authentication with rate limiting
5. **customer_satisfaction_agent** - Complaints, feedback, NPS
6. **support_agent** - Restaurant info and policies
7. **general_queries_agent** - FAQ semantic search
8. **response_agent** - Virtual Waiter formatting layer

---

**Document Complete!**

For implementation questions, refer to source code in `/app/agents/<agent_name>/` directories.

---
