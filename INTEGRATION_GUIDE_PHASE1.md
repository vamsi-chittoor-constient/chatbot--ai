# Phase 1 Tools Integration Guide

**Date:** 2025-12-21
**Tools to Add:** 15 high-priority tools
**Files Created:**
- `MISSING_CHATBOT_TOOLS_ANALYSIS.md` - Complete analysis of missing tools
- `restaurant-chatbot/app/features/food_ordering/new_tools_phase1.py` - Implementation of 15 tools
- `INTEGRATION_GUIDE_PHASE1.md` - This integration guide

---

## Quick Summary

### What Was Added

15 new chatbot tools across 5 categories:

1. **Customer Allergen Management (3 tools)**
   - `get_customer_allergens` - View customer's allergens
   - `add_customer_allergen` - Add allergen to profile
   - `remove_customer_allergen` - Remove allergen from profile

2. **Dietary Restrictions Management (2 tools)**
   - `get_dietary_restrictions` - View customer's dietary restrictions
   - `add_dietary_restriction` - Add dietary restriction (vegan, gluten-free, etc.)

3. **Customer Favorites (3 tools)**
   - `get_favorite_items` - View favorite menu items
   - `add_to_favorites` - Save item as favorite
   - `remove_from_favorites` - Remove item from favorites

4. **FAQ & Help System (4 tools)**
   - `search_faq` - Search FAQs by keyword
   - `get_faq_by_category` - Browse FAQs by category
   - `get_popular_faqs` - Show top FAQs
   - `get_help_categories` - List all FAQ categories

5. **Feedback & Reviews (3 tools)**
   - `submit_feedback` - Submit feedback/complaint/suggestion
   - `rate_last_order` - Rate most recent order
   - `get_my_feedback_history` - View past feedback

---

## Integration Steps

### Step 1: Verify Database Schema

All required tables should already exist (loaded from `03-app-tables.sql`). Verify key tables:

```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "\dt" | grep -E "(customer_allergens|dietary_restrictions|customer_favorite_items|faq|feedback)"
```

**Expected output:**
```
customer_allergens
customer_dietary_restrictions
customer_favorite_items
allergens
dietary_restrictions
faq
feedback
feedback_categories
feedback_types
feedback_statuses
```

### Step 2: Add Seed Data (Optional but Recommended)

For FAQ tools to work, you need FAQ data. Create seed data file:

**File:** `restaurant-chatbot/db/05-faq-seed-data.sql`

```sql
-- Insert sample FAQ categories and questions
INSERT INTO faq (question, answer, category, keywords, priority, is_active) VALUES
-- Delivery FAQs
('What are your delivery hours?', 'We deliver from 9 AM to 11 PM every day, including weekends and holidays.', 'delivery', ARRAY['delivery', 'hours', 'time'], 10, true),
('What is the delivery fee?', 'Delivery is FREE for orders above Rs.299. For orders below Rs.299, a delivery fee of Rs.40 applies.', 'delivery', ARRAY['delivery', 'fee', 'charge', 'cost'], 10, true),
('How long does delivery take?', 'Most deliveries arrive within 30-45 minutes. We''ll give you real-time updates on your order status.', 'delivery', ARRAY['delivery', 'time', 'how long', 'eta'], 9, true),

-- Payment FAQs
('What payment methods do you accept?', 'We accept credit/debit cards, UPI, net banking, and cash on delivery.', 'payment', ARRAY['payment', 'methods', 'card', 'upi', 'cod'], 10, true),
('Is online payment safe?', 'Yes! All online payments are processed through secure, PCI-compliant payment gateways with 256-bit encryption.', 'payment', ARRAY['payment', 'safe', 'security', 'secure'], 8, true),
('Can I pay with cash?', 'Yes, we accept cash on delivery for all orders.', 'payment', ARRAY['payment', 'cash', 'cod', 'cash on delivery'], 7, true),

-- Order FAQs
('How do I track my order?', 'After placing your order, you''ll receive a confirmation with order ID. Just ask me "what''s my order status" and I''ll check for you!', 'ordering', ARRAY['track', 'status', 'order'], 10, true),
('Can I cancel my order?', 'Yes, you can cancel within 5 minutes of placing the order. After that, please contact our support team.', 'ordering', ARRAY['cancel', 'cancellation'], 9, true),
('Can I modify my order after placing it?', 'Orders can be modified within 5 minutes of placement. After that, the kitchen may have already started preparing your food.', 'ordering', ARRAY['modify', 'change', 'edit', 'update'], 8, true),

-- Refund FAQs
('What is your refund policy?', 'If you''re not satisfied with your order, contact us within 24 hours. We offer full refunds for quality issues or incorrect orders.', 'refunds', ARRAY['refund', 'policy', 'money back'], 10, true),
('How long do refunds take?', 'Refunds are processed within 5-7 business days and will be credited to your original payment method.', 'refunds', ARRAY['refund', 'time', 'how long', 'processing'], 8, true),

-- Account FAQs
('How do I create an account?', 'Just start chatting with me! I''ll guide you through a quick phone verification to create your account.', 'account', ARRAY['account', 'register', 'sign up', 'create'], 9, true),
('I forgot my password. What should I do?', 'No worries! Just tell me "reset my password" and I''ll send you a verification code to reset it.', 'account', ARRAY['password', 'forgot', 'reset'], 8, true),

-- General FAQs
('Do you have dine-in or only delivery?', 'We offer both! You can order for delivery, takeaway, or dine-in at our restaurant.', 'general', ARRAY['dine in', 'takeaway', 'delivery'], 9, true),
('Are your ingredients fresh?', 'Absolutely! We source fresh ingredients daily and prepare everything in-house.', 'general', ARRAY['fresh', 'ingredients', 'quality'], 7, true),
('Do you cater to dietary restrictions?', 'Yes! We have vegetarian, vegan, and gluten-free options. Just tell me your dietary preferences and I''ll show you suitable items.', 'general', ARRAY['dietary', 'vegan', 'vegetarian', 'gluten-free', 'allergens'], 10, true);
```

Load the seed data:

```bash
docker exec -i a24-postgres psql -U admin -d restaurant_ai < restaurant-chatbot/db/05-faq-seed-data.sql
```

### Step 3: Integrate Tools into crew_agent.py

**Option A: Quick Integration (Recommended)**

Edit `restaurant-chatbot/app/features/food_ordering/crew_agent.py`:

1. Add import at the top of the file (around line 30):

```python
from app.features.food_ordering.new_tools_phase1 import get_all_phase1_tools
```

2. In the `create_crew()` function, find where tools are collected (around line 3100). Add Phase 1 tools:

```python
# Existing code creates tools:
tools = [
    search_menu,
    add_to_cart,
    view_cart,
    # ... existing 20 tools
]

# ADD THIS:
# Get customer_id from session context (you may need to pass this to create_crew)
customer_id = None  # TODO: Extract from session/auth context

# Add Phase 1 tools (15 new tools)
phase1_tools = get_all_phase1_tools(session_id, customer_id)
tools.extend(phase1_tools)

logger.info("crew_tools_loaded", total_tools=len(tools), session=session_id)
```

**Option B: Manual Integration**

If you prefer to add tools individually, copy tool factory functions from `new_tools_phase1.py` into `crew_agent.py` and call them explicitly.

### Step 4: Extract customer_id for Authenticated Tools

Many new tools require `customer_id`. You'll need to extract it from the session context.

**Find where `create_crew()` is called** (likely in `chat.py` or `conversation_handler.py`):

```python
# BEFORE (example):
crew = create_crew(session_id, user_message)

# AFTER:
customer_id = extract_customer_id_from_session(session_id)  # Implement this helper
crew = create_crew(session_id, user_message, customer_id=customer_id)
```

**Update `create_crew()` signature**:

```python
# In crew_agent.py
def create_crew(session_id: str, user_message: str, customer_id: Optional[str] = None):
    # ... existing code ...

    # Pass customer_id to Phase 1 tools
    phase1_tools = get_all_phase1_tools(session_id, customer_id)
```

**Helper function to extract customer_id** (add to appropriate module):

```python
def extract_customer_id_from_session(session_id: str) -> Optional[str]:
    """Extract customer_id from session data (Redis or database)."""
    try:
        from app.core.redis import get_redis_client
        import asyncio
        import json

        async def _get_customer_id():
            redis_client = await get_redis_client()
            session_key = f"session:{session_id}"
            session_data = await redis_client.get(session_key)
            if session_data:
                data = json.loads(session_data)
                return data.get('customer_id')
            return None

        # Run async function
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Create task and get result (if in async context)
            return None  # Fallback - implement proper async handling
        else:
            return asyncio.run(_get_customer_id())

    except Exception as e:
        logger.error("extract_customer_id_error", error=str(e))
        return None
```

### Step 5: Test the Integration

#### Test 1: Allergen Management

```bash
# Start chatbot if not running
docker-compose -f docker-compose.root.yml up chatbot-app -d

# Run test conversation
python test_single_chat.py
```

**Test messages:**
1. "I'm allergic to peanuts" → Should call `add_customer_allergen`
2. "What are my allergens?" → Should call `get_customer_allergens`
3. "Remove dairy allergy" → Should call `remove_customer_allergen`

#### Test 2: Dietary Restrictions

**Test messages:**
1. "I'm vegan" → Should call `add_dietary_restriction`
2. "Show my dietary restrictions" → Should call `get_dietary_restrictions`

#### Test 3: Favorites

**Test messages:**
1. "Add Margherita Pizza to my favorites" → Should call `add_to_favorites`
2. "Show my favorite items" → Should call `get_favorite_items`
3. "Remove burger from favorites" → Should call `remove_from_favorites`

#### Test 4: FAQ System

**Test messages:**
1. "What's your refund policy?" → Should call `search_faq`
2. "Show me delivery FAQs" → Should call `get_faq_by_category`
3. "What are popular questions?" → Should call `get_popular_faqs`

#### Test 5: Feedback

**Test messages:**
1. "I want to complain about cold food" → Should call `submit_feedback`
2. "Rate my last order 5 stars" → Should call `rate_last_order`
3. "Show my feedback history" → Should call `get_my_feedback_history`

### Step 6: Monitor Tool Usage

Add logging to track which new tools are being called:

```python
# In crew_agent.py, after tool execution
logger.info(
    "tool_called",
    tool_name=tool_name,
    is_phase1_tool=tool_name in [
        'get_customer_allergens', 'add_customer_allergen', 'remove_customer_allergen',
        'get_dietary_restrictions', 'add_dietary_restriction',
        'get_favorite_items', 'add_to_favorites', 'remove_from_favorites',
        'search_faq', 'get_faq_by_category', 'get_popular_faqs', 'get_help_categories',
        'submit_feedback', 'rate_last_order', 'get_my_feedback_history'
    ],
    session=session_id
)
```

---

## Verification Checklist

- [ ] Database tables verified (allergens, dietary_restrictions, customer_favorite_items, faq, feedback)
- [ ] FAQ seed data loaded
- [ ] `new_tools_phase1.py` imported in `crew_agent.py`
- [ ] Phase 1 tools added to tools list in `create_crew()`
- [ ] `customer_id` extraction implemented
- [ ] Chatbot container rebuilt with new code
- [ ] Test conversation 1 passed (allergens)
- [ ] Test conversation 2 passed (dietary)
- [ ] Test conversation 3 passed (favorites)
- [ ] Test conversation 4 passed (FAQ)
- [ ] Test conversation 5 passed (feedback)
- [ ] Tool usage logging added
- [ ] Production deployment planned

---

## Expected Impact

### Before Phase 1:
- 20 tools (basic ordering only)
- No personalization
- No FAQ/help system
- No customer feedback mechanism
- No allergen safety features

### After Phase 1:
- 35 tools (20 existing + 15 new)
- Customer profile management (allergens, dietary, favorites)
- Self-service FAQ system
- Feedback & review collection
- Enhanced customer safety (allergen warnings)
- Reduced support burden (FAQ automation)

---

## Next Phases

### Phase 2: Customer Engagement (9 tools)
- Advanced menu filtering (cuisine, tags, combos)
- Complete feedback responses
- **Estimated Implementation:** 2-3 days

### Phase 3: Full-Service Features (6 tools)
- Table reservations/bookings
- **Estimated Implementation:** 2-3 days

### Phase 4: Convenience Enhancements (3 tools)
- Order instructions
- Reorder functionality
- Item customizations
- **Estimated Implementation:** 1-2 days

---

## Troubleshooting

### Issue: Tools not being called

**Solution:**
1. Check tool descriptions are clear and match user intent
2. Verify tools are in the tools list passed to agent
3. Check OpenAI API key is valid (tool calling requires GPT-4)
4. Review agent logs for tool selection reasoning

### Issue: Database errors in tools

**Solution:**
1. Verify all tables exist: `docker exec a24-postgres psql -U admin -d restaurant_ai -c "\dt"`
2. Check foreign key constraints are satisfied
3. Ensure `customer_id` is valid UUID format
4. Check database connection pool settings

### Issue: customer_id is always None

**Solution:**
1. Verify authentication is working (check auth flow)
2. Ensure session data stores `customer_id`
3. Check `extract_customer_id_from_session()` implementation
4. Test with authenticated user (not anonymous)

### Issue: FAQ tools return "No FAQs found"

**Solution:**
1. Load FAQ seed data: `docker exec -i a24-postgres psql -U admin -d restaurant_ai < restaurant-chatbot/db/05-faq-seed-data.sql`
2. Verify data loaded: `docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT COUNT(*) FROM faq WHERE is_active = TRUE;"`
3. Expected: At least 15 FAQs

---

## Rollback Plan

If issues occur, quickly roll back:

1. **Remove Phase 1 tools from crew_agent.py:**
   ```python
   # Comment out or remove:
   # from app.features.food_ordering.new_tools_phase1 import get_all_phase1_tools
   # phase1_tools = get_all_phase1_tools(session_id, customer_id)
   # tools.extend(phase1_tools)
   ```

2. **Rebuild container:**
   ```bash
   docker-compose -f docker-compose.root.yml up chatbot-app -d --build
   ```

3. **Verify rollback:**
   - Chatbot should work with original 20 tools
   - No Phase 1 functionality available

---

## Support & Questions

For issues or questions:
1. Check [MISSING_CHATBOT_TOOLS_ANALYSIS.md](MISSING_CHATBOT_TOOLS_ANALYSIS.md) for tool specifications
2. Review [new_tools_phase1.py](restaurant-chatbot/app/features/food_ordering/new_tools_phase1.py) for implementation details
3. Check database schema: `restaurant-chatbot/db/03-app-tables.sql`

---

**Document Version:** 1.0
**Last Updated:** 2025-12-21
**Author:** Claude Sonnet 4.5
