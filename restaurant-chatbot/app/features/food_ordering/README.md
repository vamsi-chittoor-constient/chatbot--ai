# Food Ordering Feature

## Overview

Complete food ordering flow from menu browsing to order placement.

**Team Responsibilities:**
- Menu management (categories, items, search, recommendations)
- Cart operations (add/remove/update, inventory reservation)
- Order creation and management
- Checkout validation and execution

---

## Feature Structure

```
food_ordering/
├── README.md              # This file
├── __init__.py           # Package exports
├── graph.py              # Sub-agent orchestration
├── state.py              # FoodOrderingState definition
├── node.py               # State wrapper for main orchestrator
├── cache.py              # Feature cache instance
├── logger.py             # Feature logger instance
│
├── agents/               # Sub-agents (implement conversation logic)
│   ├── menu_browsing/        # Browse menu by category
│   ├── menu_discovery/       # Discover items (search, filter, recommend)
│   ├── cart_management/      # Cart operations (add/remove/update)
│   ├── checkout_validator/   # Validate cart before checkout
│   └── checkout_executor/    # Execute checkout and create order
│
├── tools/                # Food ordering tools
│   ├── __init__.py
│   ├── menu_tools.py         # Menu CRUD operations
│   ├── menu_ai_tools.py      # AI-powered menu tools
│   ├── cart_tools.py         # Cart management tools
│   ├── order_tools.py        # Order CRUD operations
│   └── order_ai_tools.py     # AI-powered order tools
│
├── services/             # Feature-specific services
│   ├── __init__.py
│   ├── menu_cache.py         # Menu caching service
│   └── inventory_sync.py     # Inventory synchronization
│
└── tests/                # Feature tests
    ├── test_graph.py
    ├── test_agents.py
    └── test_tools.py
```

---

## Database Models Used

From `app.shared.models`:
- **Menu**: `MenuCategory`, `MenuItem`
- **Cart**: Redis-based (ephemeral storage)
- **Order**: `Order`, `OrderItem`
- **User**: `User`, `UserPreferences`

---

## Sub-Agents

### 1. **menu_browsing**
**Purpose**: Browse menu by category, view specific categories/items

**Sub-intents**:
- `browse_menu` - Show menu structure
- `view_category` - Show items in specific category
- `view_item` - Show details of specific item

**Tools Used**:
- `GetMenuCategoryTool`
- `GetMenuItemTool`
- `ListMenuTool`

### 2. **menu_discovery**
**Purpose**: Discover items through search, filters, recommendations

**Sub-intents**:
- `discover_items` - Search/filter/recommend items
- `semantic_search` - Natural language search
- `dietary_filter` - Filter by dietary restrictions

**Tools Used**:
- `SemanticMenuSearchTool`
- `PersonalizedRecommendationTool`
- `SmartDietaryFilterTool`
- `PriceRangeMenuTool`
- `FindSimilarItemsTool`

### 3. **cart_management**
**Purpose**: Manage shopping cart operations

**Sub-intents**:
- `manage_cart` - Add/remove/update cart items
- `view_cart` - Show current cart
- `clear_cart` - Clear entire cart

**Tools Used**:
- `ViewCartTool`
- `AddToCartTool`
- `RemoveFromCartTool`
- `UpdateCartQuantityTool`
- `ClearCartTool`

**CRITICAL**: Cart operations must handle inventory reservation!

### 4. **checkout_validator**
**Purpose**: Validate cart and user data before checkout

**Validations**:
- Cart not empty
- All items still available
- User has required information (name, phone)
- Order type selected (dine_in/takeaway)

**Tools Used**:
- `ViewCartTool`
- `RealTimeAvailabilityTool`
- User validation tools

### 5. **checkout_executor**
**Purpose**: Execute checkout and create order

**Operations**:
- Create order in database
- Create payment link (via Payment Service API)
- Send confirmation (via Notification Service API)
- Clear cart

**Tools Used**:
- Order creation tools
- External service API calls

---

## State Management

### FoodOrderingState

```python
class FoodOrderingState(AgentState):
    """State for food ordering feature"""

    # Intent classification
    current_intent: str                    # "food_ordering"
    current_sub_intent: str                # Sub-intent within food ordering

    # Contexts (data accumulated during conversation)
    menu_context: dict                     # Menu browsing data
    cart_context: dict                     # Cart state
    order_context: dict                    # Order creation data

    # Metadata
    user_id: str
    session_id: str
    conversation_history: List[dict]
```

**State Flow Example**:
```
User: "Show me the menu"
→ current_sub_intent = "browse_menu"
→ menu_browsing agent processes
→ menu_context populated with menu data

User: "Add butter chicken to cart"
→ current_sub_intent = "manage_cart"
→ cart_management agent processes
→ cart_context updated with cart items

User: "Checkout"
→ current_sub_intent = "checkout"
→ checkout_validator validates
→ checkout_executor creates order
```

---

## Tools Documentation

### Menu Tools (`menu_tools.py`)

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| `CreateMenuCategoryTool` | Create menu category | name, description | Category data |
| `GetMenuCategoryTool` | Get categories | category_id (optional) | Category list |
| `CreateMenuItemTool` | Create menu item | name, category_id, price | Item data |
| `GetMenuItemTool` | Get menu items | Filters (category, price, dietary) | Item list |
| `UpdateMenuItemTool` | Update item | item_id, updates | Updated item |
| `ListMenuTool` | Get full menu | include_unavailable | Structured menu |

### Menu AI Tools (`menu_ai_tools.py`)

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `SemanticMenuSearchTool` | Natural language search | "something spicy and vegetarian" |
| `PersonalizedRecommendationTool` | User preference-based | "recommend something for me" |
| `SmartDietaryFilterTool` | Dietary filtering | "show vegan options" |
| `RealTimeAvailabilityTool` | Check availability | Before checkout |
| `FindSimilarItemsTool` | Similar items | Upselling, alternatives |
| `PriceRangeMenuTool` | Budget filtering | "items under ₹300" |
| `SmartUpsellingTool` | Upselling suggestions | After cart add |

### Cart Tools (`cart_tools.py`)

| Tool | Purpose | Storage | Important Notes |
|------|---------|---------|-----------------|
| `ViewCartTool` | View cart | Redis | Key: `cart:{session_id}` |
| `AddToCartTool` | Add item | Redis | **Reserves inventory!** |
| `RemoveFromCartTool` | Remove item | Redis | **Releases inventory!** |
| `UpdateCartQuantityTool` | Update quantity | Redis | Adjusts reservation |
| `ClearCartTool` | Clear cart | Redis | Releases all reservations |

**CRITICAL**: All cart operations interact with inventory cache to prevent overselling!

---

## Services

### Menu Cache Service (`menu_cache.py`)

Caches menu data in Redis to reduce database load.

**Cached Data**:
- Menu categories
- Menu items
- Full menu structure

**Cache Keys** (via `food_ordering_cache`):
- `menu:categories:all`
- `menu:categories:{category_id}`
- `menu:items:{item_id}`
- `menu:full`

**TTL**: 3600 seconds (1 hour)

### Inventory Sync Service (`inventory_sync.py`)

Manages inventory availability and reservations.

**Operations**:
- Check availability
- Reserve inventory (when adding to cart)
- Release reservations (when removing from cart)
- Sync with database

---

## Cache Usage

```python
from app.features.food_ordering.cache import food_ordering_cache

# Set cache
await food_ordering_cache.set(
    entity="menu",
    identifier="categories",
    value=menu_data,
    ttl=3600
)

# Get cache
menu_data = await food_ordering_cache.get(
    entity="menu",
    identifier="categories"
)

# Invalidate pattern
await food_ordering_cache.invalidate_pattern("menu:*")
```

---

## Logging

```python
from app.features.food_ordering.logger import food_ordering_logger

# Log with automatic feature tagging
food_ordering_logger.info(
    "Item added to cart",
    item_id="123",
    quantity=2,
    user_id="user-456"
)

# Logs: {"feature": "food_ordering", "message": "Item added to cart", ...}
```

---

## Integration with Shared Services

### Payment Service (Production Team)
```python
# Call payment service API
response = await payment_service_client.post(
    "/api/v1/payment/create-order",
    json={
        "order_id": order_id,
        "user_id": user_id,
        "amount": total_amount
    }
)
payment_link = response.json()["payment_link"]
```

### Notification Service (Production Team)
```python
# Send order confirmation SMS
response = await notification_service_client.post(
    "/api/v1/notifications/sms",
    json={
        "phone_number": user_phone,
        "message": f"Order {order_number} confirmed! Payment: {payment_link}"
    }
)
```

---

## Development Workflow

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your credentials
```

### 2. Working on Sub-Agents
```bash
# Edit sub-agent
vim app/features/food_ordering/agents/menu_browsing/node.py

# Run tests
pytest app/features/food_ordering/tests/test_agents.py -k menu_browsing
```

### 3. Adding New Tools
```python
# Create tool in tools/
# app/features/food_ordering/tools/my_new_tool.py

from app.shared.tools.base import ToolBase, ToolResult, ToolStatus

class MyNewTool(ToolBase):
    async def _execute_impl(self, **kwargs) -> ToolResult:
        # Implementation
        pass
```

### 4. Testing
```bash
# Run feature tests
pytest app/features/food_ordering/tests/

# Run specific test
pytest app/features/food_ordering/tests/test_cart.py -v
```

---

## Common Tasks

### Add New Menu Item
1. Use `CreateMenuItemTool`
2. Menu cache auto-invalidates
3. Item appears in menu queries

### Handle Out-of-Stock
1. `RealTimeAvailabilityTool` checks inventory
2. If unavailable, use `FindSimilarItemsTool` for alternatives
3. Suggest alternatives to user

### Process Checkout
1. `checkout_validator` validates cart
2. `checkout_executor` creates order
3. Call Payment Service API
4. Call Notification Service API
5. Clear cart

---

## Team Contacts

**Lead**: @food-ordering-lead
**Developers**: @dev1, @dev2
**Production Support**: @production-team

---

## Related Documentation

- [Agent State Documentation](../../../docs/AGENT_STATE.md)
- [Agent-to-SubAgent Data Transfer](../../../docs/AGENT_SUBAGENT_DATA_TRANSFER.md)
- [Deterministic Rules](../../../docs/DETERMINISTIC_RULES.md)
- [Tools Documentation](../../../docs/TOOLS.md)
