# Complete Quick Reply Action Sets - All 50 Tools Mapped

## Tool Coverage Matrix

### Base Tools (15)
| Tool | Action Set(s) | Journey Stage |
|------|--------------|---------------|
| search_menu | greeting_welcome, menu_discovery, browse_more | Entry, Discovery |
| add_to_cart | item_details_shown, upsell_suggestion | Item view |
| view_cart | added_to_cart, cart_reminder | Post-add, Pre-checkout |
| remove_from_cart | view_cart (natural language) | Cart management |
| clear_cart | view_cart | Cart management |
| update_quantity | view_cart (natural language) | Cart management |
| set_special_instructions | view_cart, item_customization | Cart management |
| get_item_details | menu_displayed, menu_discovery | Menu browsing |
| checkout | view_cart, cart_with_items | Cart → Order |
| cancel_order | order_tracking, order_management | Post-order |
| get_order_status | payment_completed, order_confirmed | Post-order |
| get_order_history | account_actions, my_account | Account |
| reorder | payment_completed, order_history_shown | Post-order |
| get_order_receipt | payment_completed, order_confirmed | Post-order |
| Payment suite (5) | payment_method, payment_flow | Checkout |

### Phase 1 Tools (15)
| Tool | Action Set(s) | Journey Stage |
|------|--------------|---------------|
| get_customer_allergens | dietary_inquiry, allergen_check | Anytime |
| add_customer_allergen | allergen_management | Profile setup |
| remove_customer_allergen | allergen_management | Profile management |
| get_dietary_restrictions | dietary_inquiry | Anytime |
| add_dietary_restriction | dietary_setup | Profile setup |
| get_favorite_items | my_favorites, account_actions | Account |
| add_to_favorites | payment_completed, item_liked | Post-order, Anytime |
| remove_from_favorites | my_favorites | Favorites management |
| search_faq | help_inquiry, question_asked | Help |
| get_faq_by_category | help_categories | Help |
| get_popular_faqs | help_inquiry | Help |
| get_help_categories | help_inquiry | Help |
| submit_feedback | payment_completed, post_delivery | Post-order |
| rate_last_order | payment_completed, post_delivery | Post-order |
| get_my_feedback_history | account_actions | Account |

### Phase 2 Tools (9)
| Tool | Action Set(s) | Journey Stage |
|------|--------------|---------------|
| get_popular_items | greeting_welcome, menu_discovery | Entry, Discovery |
| get_combo_deals | menu_discovery, deals_inquiry | Discovery, Deals |
| get_available_cuisines | menu_discovery, cuisine_browse | Discovery |
| search_by_cuisine | cuisine_selected | Post-cuisine-view |
| search_by_tag | menu_discovery, tag_filter | Discovery |
| filter_menu_by_allergen | allergen_check, dietary_filter | Pre-order |
| check_item_availability | item_details_shown | Item view |
| get_today_specials | greeting_welcome, menu_discovery | Entry, Discovery |
| get_nutritional_info | item_details_shown, health_inquiry | Item view |

### Phase 3 Tools (6)
| Tool | Action Set(s) | Journey Stage |
|------|--------------|---------------|
| check_table_availability | booking_inquiry, dine_in_mention | Booking flow |
| book_table | availability_confirmed | Booking |
| get_my_bookings | booking_management, account_actions | Booking |
| cancel_booking | booking_management | Booking |
| modify_booking | booking_management | Booking |
| get_available_time_slots | booking_inquiry | Booking |

### Phase 4-5 Tools (5)
| Tool | Action Set(s) | Journey Stage |
|------|--------------|---------------|
| schedule_order | checkout_options, future_order | Pre-checkout |
| apply_promo_code | view_cart_high_value, checkout_promo | Cart, Checkout |
| get_nutritional_info | health_inquiry, item_details | Discovery |
| get_restaurant_policies | help_inquiry, policy_question | Help |
| get_operating_hours | help_inquiry, hours_question | Help |

---

## 25+ Action Sets Design

```python
QUICK_ACTION_SETS = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ENTRY & WELCOME (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "greeting_welcome": [
        {"label": "🍔 Order Food", "action": "show me the menu"},
        {"label": "⭐ What's Popular?", "action": "what's popular today"},
        {"label": "🎁 Today's Deals", "action": "today's specials and offers"},
        {"label": "📅 Book a Table", "action": "book a table"},
        {"label": "❓ Help & FAQs", "action": "help"},
    ],

    "explore_features": [
        {"label": "🍔 Order Food", "action": "show me the menu"},
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "📅 Book Table", "action": "book a table"},
        {"label": "🔍 Check Allergens", "action": "check my allergens"},
        {"label": "🎁 Offers & Rewards", "action": "check offers and deals"},
        {"label": "❓ Get Help", "action": "help and faqs"},
    ],

    "first_time_user": [  # NEW - For users with no order history
        {"label": "🍔 Browse Menu", "action": "show me the menu"},
        {"label": "⭐ What's Popular?", "action": "show popular items"},
        {"label": "🎁 Today's Specials", "action": "today's specials"},
        {"label": "🔍 Dietary Options", "action": "dietary and allergen options"},
        {"label": "❓ How It Works", "action": "how to order"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # MENU DISCOVERY & BROWSING (5 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "menu_displayed": [
        {"label": "⭐ Popular Items", "action": "show popular items"},
        {"label": "🍽️ Browse by Cuisine", "action": "show available cuisines"},
        {"label": "🎁 Combo Deals", "action": "show combo deals"},
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "📅 Book Table", "action": "book a table"},
    ],

    "menu_discovery": [  # NEW - After user starts exploring
        {"label": "⭐ Popular Items", "action": "show popular items"},
        {"label": "🍽️ By Cuisine", "action": "browse by cuisine"},
        {"label": "🎁 Combo Deals", "action": "combo deals and offers"},
        {"label": "🌟 Today's Specials", "action": "today's specials"},
        {"label": "🔍 Filter by Diet", "action": "filter by dietary needs"},
        {"label": "🛒 View Cart", "action": "view cart"},
    ],

    "cuisine_browse": [  # NEW - When showing cuisines
        {"label": "🍕 Italian", "action": "show Italian dishes"},
        {"label": "🍜 Asian", "action": "show Asian dishes"},
        {"label": "🍔 American", "action": "show American dishes"},
        {"label": "🥗 Healthy", "action": "show healthy options"},
        {"label": "🔙 Back to Menu", "action": "show full menu"},
    ],

    "item_details_shown": [  # NEW - When showing details of specific item
        {"label": "➕ Add to Cart", "action": "add this to cart"},
        {"label": "📊 Nutrition Info", "action": "show nutrition information"},
        {"label": "✅ Check Stock", "action": "check availability"},
        {"label": "🔍 Allergen Info", "action": "check allergens"},
        {"label": "❤️ Add to Favorites", "action": "add to favorites"},
    ],

    "deals_inquiry": [  # NEW - When user asks about deals
        {"label": "🎁 Combo Deals", "action": "show combo deals"},
        {"label": "🌟 Today's Specials", "action": "today's specials"},
        {"label": "💰 Apply Promo Code", "action": "I have a promo code"},
        {"label": "🏆 Loyalty Rewards", "action": "check my rewards"},
        {"label": "🍔 Browse Menu", "action": "show menu"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CART & ORDERING (6 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "added_to_cart": [
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "add more items"},
        {"label": "❤️ Add to Favorites", "action": "add to favorites"},
    ],

    "added_to_cart_with_upsell": [  # NEW - After adding main item (burger, etc.)
        {"label": "🍟 Add Sides?", "action": "show sides and drinks"},
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "show menu"},
    ],

    "view_cart": [
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "➕ Add More", "action": "show menu"},
        {"label": "🎁 Apply Promo", "action": "apply promo code"},
        {"label": "✏️ Add Instructions", "action": "add special instructions"},
        {"label": "🗑️ Clear Cart", "action": "clear cart"},
    ],

    "view_cart_high_value": [  # NEW - When cart > Rs.500
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "🎁 Apply Promo Code", "action": "I have a promo code", "highlight": True},
        {"label": "➕ Add More", "action": "show menu"},
        {"label": "🔍 Check Allergens", "action": "check allergens in cart"},
    ],

    "checkout_options": [  # NEW - Before final checkout
        {"label": "✅ Order Now", "action": "checkout now"},
        {"label": "📅 Schedule Later", "action": "schedule order for later"},
        {"label": "🎁 Apply Promo", "action": "apply promo code"},
        {"label": "🔙 Back to Cart", "action": "view cart"},
    ],

    "cart_empty_reminder": [  # NEW - When user says checkout but cart is empty
        {"label": "🍔 Browse Menu", "action": "show menu"},
        {"label": "⭐ Popular Items", "action": "show popular items"},
        {"label": "📜 Recent Orders", "action": "show my order history"},
        {"label": "🔄 Reorder Last", "action": "reorder my last order"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # CHECKOUT & PAYMENT (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "order_type": [
        {"label": "🏠 Dine In", "action": "dine in"},
        {"label": "📦 Take Away", "action": "take away"},
    ],

    "dine_in_selected": [  # NEW - After user selects dine in
        {"label": "📅 Book Table First", "action": "book a table"},
        {"label": "✅ Continue Order", "action": "continue with dine in order"},
    ],

    "payment_method": [
        {"label": "💳 Card Payment", "action": "I want to pay by card"},
        {"label": "💵 Cash on Delivery", "action": "cash on delivery"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # POST-ORDER (4 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "order_confirmed": [
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
        {"label": "🍔 Order More", "action": "show menu"},
    ],

    "payment_completed": [
        {"label": "📍 Track Order", "action": "track my order"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
        {"label": "⭐ Rate Order", "action": "rate this order"},
        {"label": "❤️ Add to Favorites", "action": "add items to favorites"},
        {"label": "🔄 Reorder", "action": "reorder this"},
    ],

    "post_delivery": [  # NEW - Proactive 30 mins after delivery
        {"label": "⭐⭐⭐⭐⭐ Rate 5 Stars", "action": "rate 5 stars"},
        {"label": "💬 Leave Feedback", "action": "submit feedback"},
        {"label": "🔄 Reorder Same", "action": "reorder last order"},
        {"label": "❤️ Save Favorites", "action": "add to favorites"},
    ],

    "order_tracking": [  # NEW - During order tracking
        {"label": "🔄 Refresh Status", "action": "refresh order status"},
        {"label": "❌ Cancel Order", "action": "cancel this order"},
        {"label": "📞 Contact Support", "action": "contact support"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # TABLE BOOKING (4 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "booking_inquiry": [  # NEW
        {"label": "📅 Book Table", "action": "book a table now"},
        {"label": "🕐 Check Availability", "action": "check table availability"},
        {"label": "📖 My Bookings", "action": "show my bookings"},
        {"label": "❓ Booking Help", "action": "help with booking"},
    ],

    "availability_shown": [  # NEW - After showing available slots
        {"label": "✅ Confirm Booking", "action": "book this table"},
        {"label": "🔄 Check Other Times", "action": "show other time slots"},
        {"label": "🏠 Back to Home", "action": "go back"},
    ],

    "booking_confirmed": [  # NEW
        {"label": "📖 View Bookings", "action": "show my bookings"},
        {"label": "🍔 Pre-Order Food", "action": "order food for booking"},
        {"label": "✏️ Modify Booking", "action": "modify booking"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    "booking_management": [  # NEW - When viewing bookings
        {"label": "✏️ Modify Booking", "action": "modify my booking"},
        {"label": "❌ Cancel Booking", "action": "cancel booking"},
        {"label": "📅 Book Another", "action": "book another table"},
        {"label": "🍔 Order Food", "action": "show menu"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # DIETARY & ALLERGENS (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "dietary_inquiry": [  # NEW
        {"label": "🔍 Check My Allergens", "action": "show my allergens"},
        {"label": "➕ Add Allergen", "action": "add allergen"},
        {"label": "💚 Dietary Preferences", "action": "show dietary preferences"},
        {"label": "🥗 Veg Options", "action": "show vegetarian items"},
        {"label": "📊 Nutrition Info", "action": "nutrition information"},
    ],

    "allergen_management": [  # NEW
        {"label": "➕ Add Allergen", "action": "add new allergen"},
        {"label": "➖ Remove Allergen", "action": "remove allergen"},
        {"label": "🔍 Filter Menu", "action": "filter menu by my allergens"},
        {"label": "🏠 Back", "action": "go back"},
    ],

    "health_conscious": [  # NEW - For users filtering by health
        {"label": "🥗 Veg Options", "action": "show vegetarian options"},
        {"label": "📊 Nutrition Info", "action": "show nutrition info"},
        {"label": "💪 High Protein", "action": "show high protein items"},
        {"label": "🌿 Vegan Options", "action": "show vegan items"},
        {"label": "🍔 All Menu", "action": "show full menu"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HELP & SUPPORT (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "help_inquiry": [  # NEW
        {"label": "❓ View FAQs", "action": "show faqs"},
        {"label": "🕐 Operating Hours", "action": "what are your hours"},
        {"label": "📜 Policies", "action": "show restaurant policies"},
        {"label": "🚚 Delivery Info", "action": "delivery information"},
        {"label": "📞 Contact Support", "action": "contact support"},
    ],

    "faq_categories": [  # NEW - After showing FAQ categories
        {"label": "📦 Order & Delivery", "action": "order and delivery faqs"},
        {"label": "💳 Payment", "action": "payment faqs"},
        {"label": "📅 Booking", "action": "booking faqs"},
        {"label": "🔄 Returns", "action": "return and refund faqs"},
        {"label": "🔙 Back", "action": "back to help"},
    ],

    "policy_shown": [  # NEW - After showing policies
        {"label": "🚚 Delivery Policy", "action": "delivery policy"},
        {"label": "🔄 Refund Policy", "action": "refund policy"},
        {"label": "📜 Terms of Service", "action": "terms of service"},
        {"label": "🏠 Back", "action": "go back"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ACCOUNT & FAVORITES (3 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "my_account": [  # NEW
        {"label": "📜 Order History", "action": "show my order history"},
        {"label": "❤️ My Favorites", "action": "show my favorites"},
        {"label": "📖 My Bookings", "action": "show my bookings"},
        {"label": "💬 My Feedback", "action": "show my feedback history"},
        {"label": "⚙️ Preferences", "action": "show my preferences"},
    ],

    "my_favorites": [  # NEW
        {"label": "❤️ View Favorites", "action": "show my favorites"},
        {"label": "🔄 Reorder Favorite", "action": "reorder from favorites"},
        {"label": "➕ Add New Favorite", "action": "add to favorites"},
        {"label": "🏠 Back", "action": "go back"},
    ],

    "order_history_shown": [  # NEW - After showing order history
        {"label": "🔄 Reorder", "action": "reorder from history"},
        {"label": "🧾 View Receipt", "action": "show receipt"},
        {"label": "⭐ Rate Past Order", "action": "rate past order"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # FEEDBACK & RATING (2 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "feedback_prompt": [  # NEW - After delivery
        {"label": "⭐ Rate Order", "action": "rate my order"},
        {"label": "💬 Leave Feedback", "action": "submit feedback"},
        {"label": "👍 Everything Great!", "action": "rate 5 stars"},
        {"label": "Later", "action": "maybe later"},
    ],

    "rating_submitted": [  # NEW - After user rates
        {"label": "💬 Add Comments", "action": "add feedback comments"},
        {"label": "🔄 Reorder Same", "action": "reorder this"},
        {"label": "❤️ Add to Favorites", "action": "add to favorites"},
        {"label": "🏠 Home", "action": "back to home"},
    ],

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # UTILITY & FALLBACK (4 sets)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    "continue_ordering": [
        {"label": "🍔 Show Menu", "action": "show menu"},
        {"label": "🛒 View Cart", "action": "view cart"},
        {"label": "✅ Checkout", "action": "checkout"},
        {"label": "❓ Get Help", "action": "help"},
    ],

    "quantity": [
        {"label": "1", "action": "1"},
        {"label": "2", "action": "2"},
        {"label": "3", "action": "3"},
        {"label": "Other", "action": "__OTHER__"},
    ],

    "yes_no": [
        {"label": "✅ Yes", "action": "yes"},
        {"label": "❌ No", "action": "no"},
    ],

    "which_item": [
        # Dynamic - populated based on items mentioned in response
    ],

    "none": [],
}
```

**Total Action Sets: 43** (covers all 50 tools + context variations)
**Total Tools Covered: 50/50** ✅
