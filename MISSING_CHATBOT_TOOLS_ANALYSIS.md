# Missing Chatbot Tools Analysis

**Date:** 2025-12-21
**Current Tools:** 20 (focused on basic food ordering)
**Database Tables Analyzed:** 168 tables

## Executive Summary

The current chatbot implementation has **20 tools** focused exclusively on the core food ordering flow (menu browsing, cart management, ordering, payment). However, the database schema supports **many additional features** that don't have corresponding AI tools, limiting the chatbot to basic ordering functionality.

This document identifies **35+ missing tools** across 7 major feature categories that would transform the chatbot into a full-scale production system.

---

## Current Tool Coverage (20 Tools)

### Menu & Browsing (2 tools)
- `search_menu` - Basic menu search
- `get_item_details` - Item information

### Cart Management (5 tools)
- `add_to_cart` - Add items
- `remove_from_cart` - Remove items
- `view_cart` - View cart
- `update_cart_quantity` - Update quantities
- `clear_cart` - Clear cart

### Discounts & Pricing (3 tools)
- `apply_discount` - Apply discount codes
- `get_available_discounts` - List discounts
- `calculate_final_price` - Calculate totals

### Order Management (4 tools)
- `place_order` - Create order
- `get_order_status` - Check order status
- `get_order_history` - View past orders
- `cancel_order` - Cancel order

### Address Management (2 tools)
- `save_delivery_address` - Save address
- `get_saved_addresses` - Retrieve addresses

### Payment (3 tools)
- `initiate_payment` - Start payment
- `verify_payment` - Verify payment
- `get_payment_methods` - List payment methods

### Restaurant Info (1 tool)
- `get_restaurant_info` - Basic restaurant details

---

## Missing Tools Analysis

## Category 1: Customer Profile & Preferences (HIGH PRIORITY)

**Database Support:**
- `customer_allergens` - Customer allergen records with severity
- `customer_dietary_restrictions` - Dietary restrictions with notes
- `customer_favorite_items` - Saved favorite menu items
- `customer_preferences` - General customer preferences
- `allergens` - Master allergen list
- `dietary_restrictions` - Master dietary restriction types

**Missing Tools (7 tools):**

### 1.1 `get_customer_allergens`
**Purpose:** Retrieve customer's allergen information
**Use Case:** "What are my allergen restrictions?"
**Returns:** List of allergens with severity (mild/moderate/severe) and notes

### 1.2 `add_customer_allergen`
**Purpose:** Add allergen to customer profile
**Use Case:** "I'm allergic to peanuts"
**Parameters:** allergen_name, severity, notes

### 1.3 `get_customer_dietary_restrictions`
**Purpose:** Retrieve customer's dietary restrictions
**Use Case:** "What are my dietary restrictions?"
**Returns:** List of restrictions (vegetarian, vegan, gluten-free, etc.)

### 1.4 `add_dietary_restriction`
**Purpose:** Add dietary restriction to profile
**Use Case:** "I'm vegan" / "I'm gluten-free"
**Parameters:** restriction_type, severity, notes

### 1.5 `get_favorite_items`
**Purpose:** Retrieve customer's favorite menu items
**Use Case:** "Show me my favorites" / "Reorder my usual"
**Returns:** List of saved favorite items with details

### 1.6 `add_to_favorites`
**Purpose:** Save menu item as favorite
**Use Case:** "Add this pizza to my favorites"
**Parameters:** menu_item_id

### 1.7 `remove_from_favorites`
**Purpose:** Remove item from favorites
**Use Case:** "Remove this from my favorites"
**Parameters:** menu_item_id

**Impact:** Enables personalized recommendations and safety for customers with allergies

---

## Category 2: Advanced Menu Filtering & Discovery (HIGH PRIORITY)

**Database Support:**
- `cuisines` - Cuisine types (Italian, Chinese, Indian, etc.)
- `menu_item_cuisine_mapping` - Item-to-cuisine mapping
- `menu_item_tag` - Item tags (spicy, popular, chef's special)
- `menu_item_tag_mapping` - Tag associations
- `combo_item` - Combo deals
- `combo_item_components` - Combo item breakdown
- `meal_type` - Breakfast, lunch, dinner classifications

**Missing Tools (8 tools):**

### 2.1 `filter_menu_by_allergen`
**Purpose:** Show items safe for specific allergen
**Use Case:** "Show me all nut-free items" / "What can I eat if I'm allergic to dairy?"
**Parameters:** allergen_name (or use customer's saved allergens)
**Returns:** Menu items that don't contain specified allergen

### 2.2 `filter_menu_by_dietary_restriction`
**Purpose:** Filter menu by dietary needs
**Use Case:** "Show me vegan options" / "What's gluten-free?"
**Parameters:** restriction_type
**Returns:** Items matching dietary restriction

### 2.3 `search_by_cuisine`
**Purpose:** Browse menu by cuisine type
**Use Case:** "Show me Italian dishes" / "Do you have Chinese food?"
**Parameters:** cuisine_type
**Returns:** Items grouped by cuisine

### 2.4 `get_available_cuisines`
**Purpose:** List all available cuisines
**Use Case:** "What types of cuisine do you serve?"
**Returns:** List of cuisine types with item counts

### 2.5 `get_combo_deals`
**Purpose:** Show combo meal packages
**Use Case:** "What combo deals do you have?" / "Show me meal combos"
**Returns:** Combo deals with included items and pricing

### 2.6 `search_by_tag`
**Purpose:** Find items by tag (spicy, popular, new, etc.)
**Use Case:** "Show me spicy dishes" / "What's popular?" / "What's new?"
**Parameters:** tag_name
**Returns:** Tagged menu items

### 2.7 `get_meal_type_menu`
**Purpose:** Filter by meal time (breakfast, lunch, dinner)
**Use Case:** "What's for breakfast?" / "Show me dinner options"
**Parameters:** meal_type
**Returns:** Items available for specified meal period

### 2.8 `get_allergen_info_for_item`
**Purpose:** Check allergens in specific menu item
**Use Case:** "Does this burger contain nuts?" / "What allergens are in this salad?"
**Parameters:** menu_item_id
**Returns:** Complete allergen information for item

**Impact:** Dramatically improves menu discovery and ensures customer safety

---

## Category 3: FAQ & Help System (HIGH PRIORITY)

**Database Support:**
- `faq` - FAQ entries with categories and keywords
- `restaurant_faq` - Restaurant-specific FAQs
- `knowledge_base` - General knowledge articles

**Missing Tools (4 tools):**

### 3.1 `search_faq`
**Purpose:** Search frequently asked questions
**Use Case:** "How do I track my order?" / "What's your refund policy?"
**Parameters:** search_query
**Returns:** Matching FAQ entries with answers

### 3.2 `get_faq_by_category`
**Purpose:** Browse FAQs by category
**Use Case:** "Show me FAQs about delivery" / "Help with payment"
**Parameters:** category_name
**Returns:** FAQs in specified category

### 3.3 `get_popular_faqs`
**Purpose:** Show most commonly asked questions
**Use Case:** "What are common questions?"
**Returns:** Top priority FAQs

### 3.4 `search_help`
**Purpose:** Search knowledge base for help articles
**Use Case:** "How does loyalty program work?" / "Tell me about your app"
**Parameters:** search_query
**Returns:** Relevant help articles

**Impact:** Reduces support burden and provides instant answers

---

## Category 4: Feedback & Reviews (HIGH PRIORITY)

**Database Support:**
- `feedback` - Customer feedback with ratings and sentiment
- `feedback_categories` - Feedback categories (food quality, service, delivery)
- `feedback_types` - Complaint, suggestion, praise, etc.
- `feedback_statuses` - Submitted, acknowledged, resolved

**Missing Tools (5 tools):**

### 4.1 `submit_feedback`
**Purpose:** Submit general feedback or complaint
**Use Case:** "I want to report an issue" / "The food was cold"
**Parameters:** feedback_text, category, type (complaint/suggestion/praise), rating
**Returns:** Feedback submission confirmation with tracking ID

### 4.2 `rate_order`
**Purpose:** Rate a specific order
**Use Case:** "Rate my last order 5 stars" / "The delivery was slow - 2 stars"
**Parameters:** order_id, rating (1-5), review_text
**Returns:** Rating submission confirmation

### 4.3 `get_my_feedback_history`
**Purpose:** View past feedback submissions
**Use Case:** "Show my previous complaints" / "What feedback have I given?"
**Returns:** List of feedback with status (submitted, acknowledged, resolved)

### 4.4 `check_feedback_status`
**Purpose:** Check status of submitted feedback
**Use Case:** "What's the status of my complaint?" / "Has my issue been resolved?"
**Parameters:** feedback_id
**Returns:** Current status and any responses

### 4.5 `submit_order_review`
**Purpose:** Submit detailed review for order (separate from quick rating)
**Use Case:** "I want to write a review about my experience"
**Parameters:** order_id, rating, review_title, review_text, item_ratings
**Returns:** Review submission confirmation

**Impact:** Enables feedback loop and customer satisfaction tracking

---

## Category 5: Table Reservations/Bookings (MEDIUM PRIORITY)

**Database Support:**
- `table_booking_info` - Reservation details with status
- `table_info` - Table capacity and features
- `table_booking_occasion_info` - Special occasions (birthday, anniversary)
- `meal_slot_timing` - Available time slots

**Missing Tools (6 tools):**

### 5.1 `check_table_availability`
**Purpose:** Check if tables available for date/time/party size
**Use Case:** "Are you available for dinner tonight?" / "Can I book for 6 people tomorrow?"
**Parameters:** date, time, party_size
**Returns:** Available tables and time slots

### 5.2 `book_table`
**Purpose:** Create table reservation
**Use Case:** "Book a table for 4 people at 7 PM tonight"
**Parameters:** date, time, party_size, special_requests, occasion
**Returns:** Booking confirmation with booking ID

### 5.3 `get_my_bookings`
**Purpose:** View upcoming and past reservations
**Use Case:** "Show my reservations" / "When's my next booking?"
**Returns:** List of bookings with status

### 5.4 `cancel_booking`
**Purpose:** Cancel existing reservation
**Use Case:** "Cancel my reservation for tonight"
**Parameters:** booking_id, cancellation_reason
**Returns:** Cancellation confirmation

### 5.5 `modify_booking`
**Purpose:** Update reservation details
**Use Case:** "Change my booking from 4 people to 6" / "Move my reservation to 8 PM"
**Parameters:** booking_id, new_date, new_time, new_party_size
**Returns:** Modification confirmation

### 5.6 `get_available_time_slots`
**Purpose:** Show all available reservation times for a date
**Use Case:** "What times are available on Saturday?"
**Parameters:** date, party_size
**Returns:** List of available time slots

**Impact:** Enables full-service restaurant experience beyond delivery/takeout

---

## Category 6: Order Enhancements (MEDIUM PRIORITY)

**Database Support:**
- `order_instruction` - Special cooking/delivery instructions
- `order_note` - Order notes and comments
- `menu_item_variation` - Item variations (size, spice level)
- `menu_item_option` - Customization options

**Missing Tools (3 tools):**

### 6.1 `add_order_instructions`
**Purpose:** Add special instructions to order
**Use Case:** "Make it extra spicy" / "No onions please" / "Ring doorbell twice"
**Parameters:** instruction_type (cooking/delivery), instruction_text
**Returns:** Confirmation that instructions added

### 6.2 `reorder_previous_order`
**Purpose:** Quickly reorder exact previous order
**Use Case:** "Reorder my last order" / "I want the same as last time"
**Parameters:** order_id (or use most recent)
**Returns:** Cart populated with previous order items

### 6.3 `customize_item_options`
**Purpose:** Select item variations and customizations
**Use Case:** "Large pizza with extra cheese" / "Medium spice level"
**Parameters:** menu_item_id, variations {size: large, spice: medium}, options
**Returns:** Customized item details

**Impact:** Improves order accuracy and customer convenience

---

## Category 7: Restaurant Policies & Information (LOW PRIORITY)

**Database Support:**
- `restaurant_policy` - Policies (refund, cancellation, privacy)
- `branch_policy` - Branch-specific policies
- `restaurant_table` - Restaurant details

**Missing Tools (2 tools):**

### 7.1 `get_restaurant_policies`
**Purpose:** Retrieve restaurant policies
**Use Case:** "What's your refund policy?" / "What's your cancellation policy?"
**Parameters:** policy_type (refund, cancellation, privacy, delivery)
**Returns:** Policy details

### 7.2 `get_operating_hours`
**Purpose:** Show restaurant hours and holiday schedules
**Use Case:** "What time do you close?" / "Are you open on Christmas?"
**Parameters:** date (optional)
**Returns:** Operating hours, holiday schedules

**Impact:** Reduces customer service inquiries

---

## Implementation Priority Matrix

### Phase 1: Critical Safety & Personalization (HIGH PRIORITY)
**Estimated Tools:** 15 tools
**Timeline:** Implement first
**Business Impact:** High - Customer safety and personalization

1. Customer allergens management (3 tools)
2. Dietary restrictions management (2 tools)
3. Allergen menu filtering (2 tools)
4. Customer favorites (3 tools)
5. FAQ system (4 tools)
6. Basic feedback (1 tool: submit_feedback)

### Phase 2: Customer Engagement (HIGH PRIORITY)
**Estimated Tools:** 9 tools
**Timeline:** Implement second
**Business Impact:** High - Customer satisfaction and retention

1. Complete feedback system (4 remaining tools)
2. Advanced menu discovery (5 tools: cuisine, tags, combos, meal types)

### Phase 3: Full-Service Features (MEDIUM PRIORITY)
**Estimated Tools:** 6 tools
**Timeline:** Implement third
**Business Impact:** Medium - Expands service offerings

1. Table reservations (6 tools)

### Phase 4: Convenience Enhancements (MEDIUM PRIORITY)
**Estimated Tools:** 3 tools
**Timeline:** Implement fourth
**Business Impact:** Medium - Improves UX

1. Order enhancements (3 tools: instructions, reorder, customizations)

### Phase 5: Informational (LOW PRIORITY)
**Estimated Tools:** 2 tools
**Timeline:** Implement last
**Business Impact:** Low - Nice to have

1. Policies and hours (2 tools)

---

## Total Missing Tools Summary

| Category | Tools | Priority | Database Ready |
|----------|-------|----------|----------------|
| Customer Profile & Preferences | 7 | HIGH | ✅ Yes |
| Advanced Menu Filtering | 8 | HIGH | ✅ Yes |
| FAQ & Help | 4 | HIGH | ✅ Yes |
| Feedback & Reviews | 5 | HIGH | ✅ Yes |
| Table Reservations | 6 | MEDIUM | ✅ Yes |
| Order Enhancements | 3 | MEDIUM | ✅ Yes |
| Policies & Info | 2 | LOW | ✅ Yes |
| **TOTAL** | **35 tools** | - | ✅ All Ready |

---

## Technical Implementation Pattern

All new tools should follow the existing pattern in [crew_agent.py](restaurant-chatbot/app/features/food_ordering/crew_agent.py):

```python
from langchain.tools import tool
from typing import Optional

@tool("tool_name")
def tool_function(param1: str, param2: Optional[int] = None) -> str:
    """
    Clear description of what this tool does.

    Use this when the customer wants to [specific use case].

    Args:
        param1: Description
        param2: Description

    Returns:
        Description of return value
    """
    try:
        # Database query using SQLAlchemy
        result = execute_database_query(param1, param2)

        # Format response naturally
        return format_response(result)

    except Exception as e:
        logger.error(f"Error in tool_name: {str(e)}")
        return "Error message to customer"
```

---

## Recommended Next Steps

1. **Implement Phase 1 (15 tools)** - Critical safety features
2. **Test with real customer conversations** - Validate tool usage patterns
3. **Implement Phase 2 (9 tools)** - Customer engagement
4. **Monitor tool call analytics** - See which tools get used most
5. **Implement Phases 3-5 based on demand** - Data-driven prioritization

---

## Conclusion

The current chatbot has strong **ordering flow** functionality but is missing **35+ tools** across critical customer-facing features. The database schema is **100% ready** to support all missing tools.

**Key Insight:** The chatbot currently operates at ~35% of its potential capability based on available database schema. Implementing missing tools would transform it from a "basic food ordering bot" to a "full-service restaurant AI assistant."

**Immediate Action:** Implement Phase 1 (15 high-priority tools) to add critical allergen safety and personalization features.
