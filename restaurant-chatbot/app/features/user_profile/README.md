# User Profile Feature

Modern user profile and preferences management system with specialized sub-agents.

## Overview

The user_profile feature handles:
- Dietary and cuisine preferences management
- Favorite menu items management
- Order and booking history viewing
- Quick reorder functionality

## Architecture

### Hierarchical Sub-Agent System

```
user_profile_node (Entry Point)
    ↓
sub_intent_classifier
    ↓
┌──────────────────────────────────────────┐
│         Sub-Agent Router                 │
├──────────────────────────────────────────┤
│  manage_preferences → preference_manager │
│  manage_favorites → favorites_manager    │
│  view_history → history_manager          │
└──────────────────────────────────────────┘
```

### Sub-Agents

| Sub-Agent | Responsibility | Sub-Intents |
|-----------|---------------|-------------|
| **preference_manager** | Manage dietary restrictions, cuisines, allergies, spice level | manage_preferences |
| **favorites_manager** | Add/remove/view favorite menu items | manage_favorites |
| **history_manager** | View order/booking history and reorder | view_history |

## Sub-Intent Classification

```python
class SubIntentClassification(BaseModel):
    sub_intent: Literal[
        "manage_preferences",
        "manage_favorites",
        "view_history"
    ]
    confidence: float
    entities: Dict[str, Any]
    missing_entities: List[str]
    reasoning: str
```

### Classification Examples

| User Message | Sub-Intent | Entities Extracted |
|--------------|------------|-------------------|
| "I'm vegetarian" | manage_preferences | dietary_restrictions: ["vegetarian"], action: "add" |
| "I'm allergic to peanuts" | manage_preferences | allergies: ["peanuts"], action: "add" |
| "I like Chinese food" | manage_preferences | favorite_cuisines: ["chinese"], action: "add" |
| "Add this to my favorites" | manage_favorites | action: "add" |
| "Show my order history" | view_history | history_type: "orders" |
| "Reorder my last order" | view_history | action: "reorder" |

## State Management

### ProfileProgress Tracker

```python
class ProfileProgress(BaseModel):
    # User identification
    user_id: Optional[str] = None
    phone: Optional[str] = None
    device_id: Optional[str] = None

    # Preferences
    dietary_restrictions: List[str] = []
    allergies: List[str] = []
    favorite_cuisines: List[str] = []
    spice_level: Optional[Literal["mild", "medium", "hot", "extra_hot"]] = None
    preferred_seating: Optional[Literal["indoor", "outdoor", "bar", "window"]] = None

    # Favorites management
    pending_favorite_item_id: Optional[str] = None
    pending_favorite_action: Optional[Literal["add", "remove"]] = None
    favorites_updated: bool = False

    # History viewing
    history_type: Optional[Literal["orders", "bookings", "browsing"]] = None
    reorder_from_order_id: Optional[str] = None
```

### Helper Methods

```python
# Check authentication
if profile_progress.is_authenticated():
    await get_user_preferences(...)

# Check dietary preferences
if profile_progress.has_dietary_preferences():
    summary = profile_progress.get_dietary_summary()

# Add/remove dietary items
profile_progress.add_dietary_restriction("vegetarian")
profile_progress.remove_allergy("peanuts")
profile_progress.add_favorite_cuisine("italian")
```

## Tools

### Preference Tools (`tools/preference_tools.py`)

```python
# Get current preferences
await get_user_preferences(user_id="user123")

# Update dietary restrictions
await update_dietary_restrictions(
    user_id="user123",
    dietary_restrictions=["vegetarian", "gluten-free"],
    action="set"  # set, add, remove
)

# Update allergies
await update_allergies(
    user_id="user123",
    allergies=["peanuts", "shellfish"],
    action="add"
)

# Update favorite cuisines
await update_favorite_cuisines(
    user_id="user123",
    favorite_cuisines=["italian", "chinese"],
    action="set"
)

# Update spice level
await update_spice_level(
    user_id="user123",
    spice_level="medium"
)

# Update preferred seating
await update_preferred_seating(
    user_id="user123",
    preferred_seating="outdoor"
)
```

### Favorite Tools (`tools/favorite_tools.py`)

```python
# Add to favorites
await add_to_favorites(
    user_id="user123",
    menu_item_id="item456",
    menu_item_name="Margherita Pizza"
)

# Remove from favorites
await remove_from_favorites(
    user_id="user123",
    menu_item_id="item456"
)

# Get user favorites
await get_user_favorites(
    user_id="user123",
    limit=20
)
```

### History Tools (`tools/history_tools.py`)

```python
# Get order history
await get_order_history(
    user_id="user123",
    limit=10
)

# Get booking history
await get_booking_history(
    user_id="user123",
    limit=10
)

# Get browsing history
await get_browsing_history(
    user_id="user123",
    limit=20
)

# Reorder from history
await reorder_from_history(
    order_id="order789",
    user_id="user123"
)
```

## Integration

### Orchestrator Routing

**Router Configuration** (`app/orchestration/nodes/router.py`):
```python
intent_agent_mapping = {
    "update_profile": "user_profile_agent",
    "manage_preferences": "user_profile_agent",
    "manage_favorites": "user_profile_agent",
    "view_history": "user_profile_agent",
    "reorder": "user_profile_agent",
    # ...
}
```

**Graph Configuration** (`app/orchestration/graph.py`):
```python
from app.features.user_profile import user_profile_node as user_profile_agent_node

workflow.add_node("user_profile_agent", user_profile_agent_node)
workflow.add_edge("user_profile_agent", "response_agent")
```

## Sub-Agent Details

### 1. Preference Manager

**File**: `agents/preference_manager/node.py`

**Responsibility**: Manage dietary and cuisine preferences

**Features**:
- Add/remove dietary restrictions
- Add/remove allergies
- Set favorite cuisines
- Configure spice level
- Set preferred seating
- View current preferences

**Example**:
```python
Input: "I'm vegetarian and allergic to peanuts"
Entities: {
    "dietary_restrictions": ["vegetarian"],
    "allergies": ["peanuts"],
    "action": "add"
}

Output: {
    "action": "preferences_updated",
    "success": True,
    "data": {
        "message": "Successfully updated: dietary restrictions, allergies.",
        "updated_fields": ["dietary restrictions", "allergies"]
    }
}
```

### 2. Favorites Manager

**File**: `agents/favorites_manager/node.py`

**Responsibility**: Manage favorite menu items

**Actions**:
- `add` - Add item to favorites
- `remove` - Remove item from favorites
- `view` - List all favorites

**Example**:
```python
Input: "Add Margherita Pizza to my favorites"
Entities: {
    "item_id": "item456",
    "item_name": "Margherita Pizza",
    "action": "add"
}

Output: {
    "action": "added_to_favorites",
    "success": True,
    "data": {
        "message": "Added 'Margherita Pizza' to your favorites!",
        "item_id": "item456"
    }
}
```

### 3. History Manager

**File**: `agents/history_manager/node.py`

**Responsibility**: View history and reorder

**Features**:
- View order history
- View booking history
- View browsing history
- Quick reorder from past orders

**History Types**:
- `orders` - Past food orders
- `bookings` - Past table reservations
- `browsing` - Recently viewed menu items

**Example**:
```python
Input: "Show my last 5 orders"
Entities: {
    "history_type": "orders",
    "limit": 5
}

Output: {
    "action": "orders_listed",
    "success": True,
    "data": {
        "message": "You have 5 past orders.",
        "orders": [...],
        "count": 5
    }
}
```

## Response Format

All agents return standardized responses:

```python
{
    "action": str,              # Action type identifier
    "success": bool,            # Operation success status
    "data": {                   # Response data
        "message": str,         # User-facing message
        # ... additional data
    },
    "context": {                # Metadata
        "sub_intent": str,      # Sub-intent classification
        "confidence": float,    # Classification confidence
        # ... additional context
    }
}
```

## Common Flows

### Preference Update Flow

```
1. User: "I'm vegetarian"
2. Sub-intent: manage_preferences
3. Entities: {dietary_restrictions: ["vegetarian"], action: "add"}
4. Agent: preference_manager
5. Actions:
   - Add vegetarian to dietary restrictions
   - Update user preferences in database
6. Response: "Successfully updated: dietary restrictions."
```

### Favorites Management Flow

```
1. User: "Add this pizza to my favorites"
2. Sub-intent: manage_favorites
3. Entities: {item_id: "item456", action: "add"}
4. Agent: favorites_manager
5. Actions:
   - Add item to user's favorites
   - Update favorites in database
6. Response: "Added 'Margherita Pizza' to your favorites!"
```

### Reorder Flow

```
1. User: "Reorder my last order"
2. Sub-intent: view_history
3. Entities: {action: "reorder"}
4. Agent: history_manager
5. Actions:
   - Get user's last order
   - Add items to current cart
6. Response: "Items from order #123 have been added to your cart!"
```

## Best Practices

1. **Require authentication** for all profile operations
2. **Cache preferences** for faster access
3. **Validate dietary restrictions** against menu items
4. **Show personalized recommendations** based on preferences
5. **Track browsing history** for better personalization
6. **Allow bulk updates** for efficiency
7. **Provide preference summaries** for easy review

## Personalization Features

- **Menu Filtering**: Filter menu based on dietary restrictions/allergies
- **Smart Recommendations**: Suggest items based on favorite cuisines
- **Quick Reorder**: One-click reorder from history
- **Favorites Shortcuts**: Quick access to favorite items
- **Spice Level Matching**: Show spice level indicators on menu

## Configuration

### Environment Variables

```bash
# Preferences
MAX_DIETARY_RESTRICTIONS=10
MAX_ALLERGIES=20
MAX_FAVORITE_CUISINES=5

# Favorites
MAX_FAVORITES_PER_USER=50

# History
ORDER_HISTORY_LIMIT=100
BOOKING_HISTORY_LIMIT=50
BROWSING_HISTORY_DAYS=90
```

## Migration Notes

### From Legacy user_profile_agent

The user_profile feature enhances the legacy `user_profile_agent`:

**Changes**:
- ✅ Split into 3 specialized sub-agents
- ✅ Added ProfileProgress tracker for state management
- ✅ Added sub-intent classification
- ✅ Improved preference management
- ✅ Added browsing history tracking
- ✅ Enhanced reorder functionality

## Troubleshooting

### Common Issues

**Issue**: Preferences not saving
**Solution**: Verify user is authenticated, check database connection

**Issue**: Favorites not showing
**Solution**: Check user_id is correct, verify database query

**Issue**: Reorder fails
**Solution**: Verify order_id exists, check items still available

**Issue**: History empty
**Solution**: Verify user has past orders/bookings, check query parameters

## Future Enhancements

- [ ] Meal planning and scheduling
- [ ] Nutritional goals tracking
- [ ] Calorie counting integration
- [ ] Recipe suggestions based on preferences
- [ ] Shared favorites (family/friends)
- [ ] Preference export/import
- [ ] AI-powered recommendations
- [ ] Social features (reviews, ratings sharing)

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [Pydantic Models](https://docs.pydantic.dev/)
- [Personalization Best Practices](https://www.nngroup.com/articles/personalization/)
- [Structlog](https://www.structlog.org/)
