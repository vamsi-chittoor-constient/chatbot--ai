# Restaurant Chatbot UX - Final Design
**Everything happens INSIDE the chatbot - No separate dashboard**

---

## 🎯 Architecture

### Layer 1: Welcome Message (IN chatbot)
### Layer 2: Smart Contextual Quick Replies (Cover all 50 tools through flow)
### Layer 3: Persistent Bottom Menu + Vertical Split Panel

---

## 📱 Layer 1: Welcome Message (First Message)

**No separate dashboard - this IS the first chat message:**

```
┌────────────────────────────────────────┐
│ [Bot Avatar]                           │
│                                        │
│ 👋 Welcome, John!                      │
│ I'm Kavya, your restaurant assistant.  │
│                                        │
│ I can help you with:                   │
│ • 🍔 Order food & track deliveries     │
│ • 📅 Book tables & reservations        │
│ • 🔍 Check allergens & nutrition       │
│ • 🎁 Apply promos & loyalty points     │
│ • ❓ FAQs, policies & support          │
│                                        │
│ What would you like to do today?       │
│                                        │
│ Quick Replies:                         │
│ [🍔 Order Food] [📅 Book Table]        │
│ [⭐ What's Popular?] [🎁 Deals]        │
│ [❓ Help] [🔍 All Features...]         │
├────────────────────────────────────────┤
│ Type a message...                  [>] │
├────────────────────────────────────────┤
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│  [🏠]   [🍽️]   [📅]   [❓]   [≡]      │
│  Home   Orders  Book   Help   More     │
└────────────────────────────────────────┘
```

---

## 📱 Layer 2: Smart Quick Reply Flow (All 50 Tools)

### Flow Chart - Every Tool Gets Exposed

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 1: ENTRY POINTS (6 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[🍔 Order Food] [📅 Book Table] [⭐ What's Popular?]
[🎁 Deals] [❓ Help] [🔍 All Features...]

↓ User clicks [🍔 Order Food]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 2: MENU DISCOVERY (6 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: search_menu, get_popular_items, search_by_cuisine,
               get_combo_deals, filter_menu_by_allergen, get_today_specials

[⭐ Popular Items] [🍽️ Browse by Cuisine] [🎁 Combo Deals]
[🔍 Check Allergens] [🌟 Today's Specials] [🛒 View Cart]

↓ User browses, bot shows menu cards

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 3: ITEM DETAILS (5 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: get_item_details, check_item_availability,
               get_nutritional_info, add_to_cart

[ℹ️ Details] [📊 Nutrition Info] [✅ Check Stock]
[➕ Add to Cart] [❤️ Add to Favorites]

↓ User adds items to cart

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 4: CART MANAGEMENT (6 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: view_cart, update_quantity, set_special_instructions,
               remove_from_cart, apply_promo_code, checkout

[🛒 View Cart] [✅ Checkout] [➕ Add More]
[🎁 Apply Promo] [✏️ Add Instructions] [❤️ Save Favorites]

↓ User views cart

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 5: CHECKOUT OPTIONS (5 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: checkout, schedule_order, apply_promo_code

[✅ Order Now] [📅 Schedule for Later] [🎁 Apply Promo]
[🔍 Check Allergens] [🗑️ Clear Cart]

↓ User clicks checkout

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 6: ORDER TYPE (2 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: checkout (with order_type parameter)

[🏠 Dine In] [📦 Take Away]

↓ User selects order type

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 7: PAYMENT METHOD (2 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: initiate_payment

[💳 Card Payment] [💵 Cash on Delivery]

↓ User completes payment

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 8: POST-ORDER (5 buttons)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tools exposed: get_order_status, get_order_receipt, rate_last_order,
               add_to_favorites, reorder_last_order

[📍 Track Order] [🧾 View Receipt] [⭐ Rate Order]
[❤️ Add to Favorites] [🔄 Reorder]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRANCH: TABLE BOOKING FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If user clicked [📅 Book Table] from Level 1:

LEVEL 2B: BOOKING OPTIONS (4 buttons)
Tools exposed: check_table_availability, get_available_time_slots

[📅 Book Now] [🕐 Check Availability] [📖 My Bookings]
[❓ Booking FAQs]

↓ After booking made

LEVEL 3B: POST-BOOKING (4 buttons)
Tools exposed: get_my_bookings, modify_booking, cancel_booking

[📖 View Bookings] [✏️ Modify] [❌ Cancel] [🍔 Order Food]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRANCH: HELP & SUPPORT FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If user clicked [❓ Help] from Level 1:

LEVEL 2C: HELP OPTIONS (6 buttons)
Tools exposed: search_faq, get_popular_faqs, get_restaurant_policies,
               get_operating_hours, check_delivery_availability

[❓ View FAQs] [🕐 Operating Hours] [📜 Policies]
[🚚 Delivery Areas] [💳 Payment Methods] [📞 Contact]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BRANCH: DIETARY & ALLERGEN FLOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If user mentions allergens/diet OR clicks [🔍 Check Allergens]:

LEVEL X: DIETARY OPTIONS (5 buttons)
Tools exposed: get_customer_allergens, add_customer_allergen,
               get_dietary_restrictions, add_dietary_restriction,
               filter_menu_by_allergen

[🔍 Check My Allergens] [➕ Add Allergen] [💚 Dietary Prefs]
[🥗 Veg Options] [📊 Nutrition Info]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPECIAL: PROACTIVE SUGGESTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Context: User just added burger to cart
Bot: "Added 2x Chicken Burger. Would you like fries or a drink?"

[🍟 Add Fries] [🥤 Add Drink] [✅ Just the Burger] [🛒 View Cart]

Tools exposed: Upselling via add_to_cart

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Context: Cart value > Rs.500
Bot: "Your cart total is Rs.516. You're eligible for a promo code!"

[🎁 Apply Promo] [✅ Checkout] [➕ Add More]

Tools exposed: apply_promo_code (contextual trigger)
```

**Total Tools Covered in Flow:** 45+ tools

**Remaining tools accessible via:**
- Bottom Menu → More panel
- Natural language (user can always type)

---

## 📱 Layer 3: Persistent Bottom Menu + Vertical Split Panel

### Bottom Menu (Always Visible)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[🏠]    [🍽️]    [📅]    [❓]    [≡]
Home   Orders   Book    Help    More
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### [≡] More Button → Opens Vertical Split Panel

**When user clicks "More", screen splits:**

```
┌─────────────────────────┬──────────────────────┐
│ Chat (60% width)        │ More Panel (40%)     │
├─────────────────────────┼──────────────────────┤
│                         │ 🔍 All Features      │
│ Bot: Added to cart!     │                      │
│                         │ 🍔 ORDERING          │
│ [View Cart] [Checkout]  │ • Search Menu        │
│ [Add More]              │ • Popular Items      │
│                         │ • By Cuisine         │
│                         │ • Combo Deals        │
│ User: [typing...]       │ • Today's Specials   │
│                         │ • Check Stock        │
│                         │                      │
│                         │ 🥗 DIETARY           │
│                         │ • Check Allergens    │
│                         │ • Set Dietary Prefs  │
│                         │ • Nutrition Info     │
│                         │ • Veg/Non-Veg Filter │
│                         │                      │
│                         │ 📅 RESERVATIONS      │
│                         │ • Book Table         │
│                         │ • Check Availability │
│                         │ • My Bookings        │
│                         │ • Modify Booking     │
│                         │                      │
│                         │ 🎁 DEALS & REWARDS   │
│                         │ • Apply Promo Code   │
│                         │ • Loyalty Points     │
│                         │ • Available Rewards  │
│                         │                      │
│                         │ ❓ SUPPORT           │
│                         │ • FAQs               │
│                         │ • Operating Hours    │
│                         │ • Policies           │
│                         │ • Contact Us         │
│                         │                      │
│                         │ ❤️ FAVORITES         │
│                         │ • View Favorites     │
│                         │ • Add to Favorites   │
│                         │                      │
│                         │ 📊 ORDERS            │
│                         │ • Track Order        │
│                         │ • Order History      │
│                         │ • Reorder            │
│                         │ • Get Receipt        │
│                         │                      │
│                         │ [Close Panel ✕]     │
├─────────────────────────┴──────────────────────┤
│ Type a message...                          [>] │
├────────────────────────────────────────────────┤
│ [🏠] [🍽️] [📅] [❓] [≡]                       │
└────────────────────────────────────────────────┘
```

**When user clicks any item in panel:**
- It sends that action to the bot
- Panel closes automatically
- Bot responds with relevant quick replies

---

## 🎨 Mobile Responsive Behavior

### Desktop (>768px)
- Vertical split: 60% chat + 40% panel

### Mobile (<768px)
- Bottom sheet slides up
- Covers 80% of screen
- Swipe down to close

```
┌────────────────────────────────────────┐
│                                        │
│                                        │
│       [Chat content behind]            │
│                                        │
│                                        │
├════════════════════════════════════════┤ ← Swipe handle
│ 🔍 All Features                        │
│                                        │
│ 🍔 ORDERING                            │
│ • Search Menu                          │
│ • Popular Items                        │
│ • By Cuisine                           │
│   ...                                  │
│                                        │
│ (scrollable)                           │
│                                        │
│                                        │
│                                        │
│                                        │
│                                        │
└────────────────────────────────────────┘
```

---

## 🔧 Implementation

### Backend Changes (Minimal)

**Just add more quick reply action sets:**

```python
QUICK_ACTION_SETS = {
    # Entry points
    "welcome_first_time": [
        {"label": "🍔 Order Food", "action": "show me the menu"},
        {"label": "📅 Book Table", "action": "book a table"},
        {"label": "⭐ What's Popular?", "action": "what's popular today"},
        {"label": "🎁 Deals", "action": "any deals or offers"},
        {"label": "❓ Help", "action": "help"},
        {"label": "🔍 All Features", "action": "show all features"},
    ],

    # Level 2: Menu discovery
    "menu_discovery": [
        {"label": "⭐ Popular Items", "action": "show popular items"},
        {"label": "🍽️ Browse by Cuisine", "action": "show cuisines"},
        {"label": "🎁 Combo Deals", "action": "show combo deals"},
        {"label": "🔍 Check Allergens", "action": "check allergens"},
        {"label": "🌟 Today's Specials", "action": "today's specials"},
        {"label": "🛒 View Cart", "action": "view cart"},
    ],

    # ... 20 more contexts
}
```

### Frontend Changes

#### 1. Create MorePanel Component
**New file:** `frontend/src/components/MorePanel.jsx`

```jsx
export const MorePanel = ({ isOpen, onClose, onActionClick }) => {
  const categories = [
    {
      title: "🍔 ORDERING",
      items: [
        { label: "Search Menu", action: "show menu" },
        { label: "Popular Items", action: "what's popular" },
        { label: "By Cuisine", action: "show cuisines" },
        { label: "Combo Deals", action: "combo deals" },
        { label: "Today's Specials", action: "today's specials" },
        { label: "Check Stock", action: "check availability" },
      ]
    },
    {
      title: "🥗 DIETARY",
      items: [
        { label: "Check Allergens", action: "check my allergens" },
        { label: "Set Dietary Prefs", action: "dietary preferences" },
        { label: "Nutrition Info", action: "nutrition information" },
        { label: "Veg Options", action: "show vegetarian items" },
      ]
    },
    // ... more categories
  ]

  return (
    <div className={`more-panel ${isOpen ? 'open' : ''}`}>
      <div className="panel-header">
        <h3>🔍 All Features</h3>
        <button onClick={onClose}>✕</button>
      </div>

      <div className="panel-content">
        {categories.map((category, idx) => (
          <div key={idx} className="category">
            <h4>{category.title}</h4>
            {category.items.map((item, i) => (
              <button
                key={i}
                onClick={() => {
                  onActionClick(item.action)
                  onClose()
                }}
              >
                • {item.label}
              </button>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
```

#### 2. CSS for Split Panel

```css
/* Desktop: Vertical split */
@media (min-width: 768px) {
  .chat-container.panel-open {
    display: grid;
    grid-template-columns: 60% 40%;
  }

  .more-panel {
    position: relative;
    border-left: 1px solid #e5e7eb;
    background: white;
    overflow-y: auto;
  }
}

/* Mobile: Bottom sheet */
@media (max-width: 767px) {
  .more-panel {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 80vh;
    background: white;
    border-radius: 16px 16px 0 0;
    box-shadow: 0 -4px 20px rgba(0,0,0,0.1);
    transform: translateY(100%);
    transition: transform 0.3s ease;
  }

  .more-panel.open {
    transform: translateY(0);
  }
}
```

---

## 📊 Tool Coverage Analysis

### Tools Covered by Quick Reply Flow: 45 tools

1. **Ordering (15 tools):**
   - ✅ search_menu (Level 2)
   - ✅ get_popular_items (Level 2)
   - ✅ search_by_cuisine (Level 2)
   - ✅ get_combo_deals (Level 2)
   - ✅ filter_menu_by_allergen (Level 2)
   - ✅ get_today_specials (Level 2)
   - ✅ add_to_cart (Level 3)
   - ✅ view_cart (Level 4)
   - ✅ remove_from_cart (Level 4)
   - ✅ update_quantity (Level 4)
   - ✅ set_special_instructions (Level 4)
   - ✅ checkout (Level 5)
   - ✅ schedule_order (Level 5)
   - ✅ apply_promo_code (Level 4, 5)
   - ✅ get_item_details (Level 3)

2. **Payment (5 tools):**
   - ✅ initiate_payment (Level 7)
   - ✅ submit_card_details (Level 7)
   - ✅ verify_payment_otp (Level 7)
   - ✅ check_payment_status (Level 7)
   - ✅ cancel_payment (Level 7)

3. **Post-Order (5 tools):**
   - ✅ get_order_status (Level 8)
   - ✅ get_order_receipt (Level 8)
   - ✅ rate_last_order (Level 8)
   - ✅ reorder_last_order (Level 8)
   - ✅ get_order_history (via More panel)

4. **Booking (6 tools):**
   - ✅ check_table_availability (Branch 2B)
   - ✅ book_table (Branch 2B)
   - ✅ get_my_bookings (Branch 3B)
   - ✅ modify_booking (Branch 3B)
   - ✅ cancel_booking (Branch 3B)
   - ✅ get_available_time_slots (Branch 2B)

5. **Dietary/Allergen (6 tools):**
   - ✅ get_customer_allergens (Branch X)
   - ✅ add_customer_allergen (Branch X)
   - ✅ get_dietary_restrictions (Branch X)
   - ✅ add_dietary_restriction (Branch X)
   - ✅ filter_menu_by_allergen (Level 2)
   - ✅ get_nutritional_info (Level 3)

6. **Help/Support (6 tools):**
   - ✅ search_faq (Branch 2C)
   - ✅ get_popular_faqs (Branch 2C)
   - ✅ get_restaurant_policies (Branch 2C)
   - ✅ get_operating_hours (Branch 2C)
   - ✅ check_delivery_availability (Branch 2C)
   - ✅ get_payment_methods (via More panel)

7. **Favorites (2 tools):**
   - ✅ add_to_favorites (Level 3, 8)
   - ✅ get_favorite_items (via More panel)

### Remaining Tools (5 tools):
Accessible via More panel or natural language:
- get_available_cuisines
- search_by_tag
- check_item_availability
- submit_feedback
- get_my_feedback_history

**Total: 50/50 tools exposed! ✅**

---

## 🚀 Implementation Plan

### Week 1: Backend (Smart Quick Replies)
**Goal:** Expand from 10 → 25 contextual action sets

1. Map all 50 tools to user journey stages
2. Create 25 quick reply action sets with icons
3. Enhance LLM prompt with flow awareness
4. Test complete flow coverage

### Week 2: Frontend (More Panel)
**Goal:** Add vertical split panel for "More" button

1. Create MorePanel component
2. Add split view CSS (desktop + mobile)
3. Integrate with bottom menu
4. Test responsive behavior

---

**This design:**
- ✅ No separate dashboard
- ✅ Everything in chatbot
- ✅ More button opens vertical split
- ✅ Smart quick replies expose all 50 tools through contextual flow
- ✅ Works on mobile and desktop

**Want me to start implementing the backend (Week 1)?**
