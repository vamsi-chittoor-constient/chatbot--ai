# Quick Actions UX Redesign - Options & Recommendations

## Current Situation

**Problem:**
- 50+ tools available
- Only showing 2-4 quick replies at a time
- Users don't discover 80% of features
- No persistent way to access all capabilities

**Frontend Capability:**
- ✅ Uses `flex-wrap` - can handle unlimited buttons
- ✅ Buttons automatically wrap to multiple rows
- ✅ No technical limit on button count

---

## Option 1: Show All Actions (NOT RECOMMENDED)

### Design
Show 10-15 quick reply buttons for every response.

### Example
```
Bot: "Added chicken burger to cart!"
Quick Replies:
[View Cart] [Checkout] [Add More] [Show Menu] [Book Table]
[Track Order] [View FAQs] [Apply Promo] [Check Allergens]
[Today's Specials] [Order History] [Rate Order] [Get Help]
```

### Pros
- ✅ All features visible
- ✅ Maximum discoverability

### Cons
- ❌ **Decision paralysis** - too many choices
- ❌ **Overwhelming** - cognitive overload
- ❌ **Not contextual** - irrelevant options shown
- ❌ **Poor UX** - research shows 3-5 options is ideal
- ❌ **Mobile unfriendly** - takes up entire screen

### Verdict: **❌ DO NOT USE**
Research shows users perform worse with >7 options (Miller's Law)

---

## Option 2: Categorized Actions with Expansion

### Design
Show 3-4 contextual actions + 1 "More Actions..." button that expands.

### Example
```
Bot: "Added chicken burger to cart!"

Primary Actions (always visible):
[View Cart] [Checkout] [Add More]

[≡ More Actions...]  ← Tap to expand

When expanded:
┌─────────────────────────────┐
│ 🍽️ Order Actions            │
│  • Track My Orders           │
│  • Order History             │
│  • Reorder Last Order        │
│                              │
│ 🍴 Dining Options            │
│  • Book a Table              │
│  • View My Bookings          │
│                              │
│ ℹ️ Help & Info               │
│  • FAQs                      │
│  • Restaurant Policies       │
│  • Operating Hours           │
│                              │
│ 🎁 Deals & Promos            │
│  • Today's Specials          │
│  • Apply Promo Code          │
│  • Combo Deals               │
└─────────────────────────────┘
```

### Pros
- ✅ Clean by default (3-4 buttons)
- ✅ Full discovery on demand
- ✅ Organized by category
- ✅ Not overwhelming

### Cons
- ⚠️ Requires 2 clicks to access features
- ⚠️ Users might not notice "More Actions"
- ⚠️ Needs frontend component changes

### Verdict: **✅ GOOD - Best for comprehensive feature discovery**

---

## Option 3: Hybrid - Contextual + Persistent Menu Bar

### Design
- **Top area:** 3-4 contextual quick replies (changes with conversation)
- **Bottom bar:** Persistent menu (always visible)

### Example
```
Bot: "Added chicken burger to cart!"

Contextual (top):
[View Cart] [Checkout] [Add More]

────────────────────────────────────

Persistent Menu Bar (bottom - always visible):
[🏠 Menu] [🍽️ Orders] [📅 Book] [❓ Help]
```

When user taps [🏠 Menu]:
```
┌─────────────────────────────┐
│ Menu Options                 │
│  • Browse Full Menu          │
│  • Popular Items             │
│  • Today's Specials          │
│  • Combo Deals               │
│  • Search by Cuisine         │
└─────────────────────────────┘
```

### Pros
- ✅ Best of both worlds
- ✅ Contextual guidance (top)
- ✅ Feature discovery (bottom)
- ✅ Always accessible
- ✅ Like mobile apps users are familiar with

### Cons
- ⚠️ Requires significant frontend changes
- ⚠️ Takes vertical space

### Verdict: **✅ EXCELLENT - Best overall UX (requires frontend work)**

---

## Option 4: Smart Contextual with Proactive Suggestions (RECOMMENDED)

### Design
Show 4-6 quick replies that are **intelligent and contextual**.
Use LLM to determine not just category, but also **proactive feature discovery**.

### Logic
```python
Context: User just added item to cart
→ Show: [View Cart] [Checkout] [Add More]

Context: User is new (first order)
→ Show: [View Cart] [Checkout] [Add to Favorites ⭐] [Check Allergens 🔍]

Context: User has ordered 3+ times
→ Show: [View Cart] [Checkout] [Reorder Last Order 🔄]

Context: Cart total > Rs.500
→ Show: [View Cart] [Checkout] [Apply Promo Code 🎁]

Context: User said "dine in"
→ Show: [Dine In] [Book a Table 📅]

Context: After order placed
→ Show: [Track Order] [Rate Order ⭐] [View Receipt] [Add to Favorites]

Context: User asks question
→ Show: [View FAQs] [Restaurant Policies] [Operating Hours] [Contact Support]
```

### Implementation
Enhance the LLM prompt with **secondary suggestions**:

```python
QUICK_ACTION_SETS = {
    "added_to_cart": {
        "primary": [  # Always show (3 buttons)
            {"label": "View Cart", ...},
            {"label": "Checkout", ...},
            {"label": "Add More", ...}
        ],
        "secondary": [  # Show based on context (1-2 buttons)
            {"label": "Add to Favorites ⭐", ..., "condition": "new_user"},
            {"label": "Check Allergens", ..., "condition": "health_conscious"},
            {"label": "Apply Promo Code 🎁", ..., "condition": "cart_value > 500"},
        ]
    }
}
```

### Pros
- ✅ No frontend changes needed
- ✅ Clean (4-6 buttons total)
- ✅ Intelligent feature discovery
- ✅ Contextually relevant
- ✅ Proactive guidance

### Cons
- ⚠️ Need to track user state (cart value, order count, etc.)
- ⚠️ LLM needs more context

### Verdict: **✅ BEST - Quick win with high impact**

---

## Option 5: Feature Discovery Flow (Onboarding)

### Design
When user first connects, show a **feature discovery carousel**.

### Example
```
Bot: "Welcome! 👋 I'm Kavya, your restaurant assistant.
     Let me show you what I can help with..."

[Show carousel - swipe through 3 screens]

Screen 1:
┌─────────────────────────────┐
│ 🍔 Order Food                │
│ Browse menu, add to cart,    │
│ customize items, and order   │
│                              │
│         [Next →]             │
└─────────────────────────────┘

Screen 2:
┌─────────────────────────────┐
│ 📅 Book Tables               │
│ Reserve tables, check        │
│ availability, manage         │
│ bookings                     │
│                              │
│      [← Back] [Next →]       │
└─────────────────────────────┘

Screen 3:
┌─────────────────────────────┐
│ 💡 More Features             │
│ • Track orders               │
│ • Apply promo codes          │
│ • Check allergens            │
│ • Get help & FAQs            │
│                              │
│   [← Back] [Get Started!]    │
└─────────────────────────────┘
```

### Pros
- ✅ One-time education
- ✅ Sets expectations
- ✅ High feature awareness

### Cons
- ⚠️ Users skip onboarding
- ⚠️ Needs persistent menu to remind

### Verdict: **✅ GOOD - Use as complement to Option 4**

---

## Recommended Solution: Hybrid Approach

### Phase 1 (Quick Win - No Frontend Changes)
**Implement Option 4: Smart Contextual with Proactive Suggestions**

1. **Expand quick reply action sets to 15-20 scenarios**
2. **Add secondary suggestions based on context**
3. **Show 5-6 buttons per response** (not just 3)
4. **Make LLM smarter about feature discovery**

Example implementation:
```python
QUICK_ACTION_SETS = {
    "added_to_cart": [
        # Primary (always)
        {"label": "View Cart", ...},
        {"label": "Checkout", ...},
        {"label": "Add More", ...},
        # Discovery (contextual)
        {"label": "Add to Favorites ⭐", ..., "priority": 2},
        {"label": "Apply Promo 🎁", ..., "priority": 2},
    ],

    "order_confirmed": [
        {"label": "Track Order", ...},
        {"label": "View Receipt", ...},
        {"label": "Rate Order ⭐", ...},
        {"label": "Reorder Anytime", ...},
    ],

    "first_time_user": [  # NEW
        {"label": "Show Menu", ...},
        {"label": "What's Popular?", ...},
        {"label": "Book a Table 📅", ...},
        {"label": "View FAQs", ...},
        {"label": "Today's Specials", ...},
    ],

    "browsing_menu": [  # NEW
        {"label": "What's Popular?", ...},
        {"label": "View by Cuisine", ...},
        {"label": "Today's Specials", ...},
        {"label": "Combo Deals", ...},
        {"label": "View Cart", ...},
    ],

    "checkout_ready": [  # NEW
        {"label": "Checkout", ...},
        {"label": "Apply Promo Code 🎁", ...},
        {"label": "Add More", ...},
        {"label": "View Cart", ...},
    ],

    "question_asked": [  # NEW
        {"label": "View FAQs", ...},
        {"label": "Operating Hours", ...},
        {"label": "Policies", ...},
        {"label": "Show Menu", ...},
    ],

    "dietary_concern": [  # NEW - When user mentions allergies/diet
        {"label": "Check Allergens", ...},
        {"label": "Set Dietary Prefs", ...},
        {"label": "View Veg Options", ...},
        {"label": "Nutrition Info", ...},
    ],

    "post_delivery": [  # NEW - 30 mins after delivery
        {"label": "Rate Order ⭐", ...},
        {"label": "Submit Feedback", ...},
        {"label": "Reorder", ...},
        {"label": "View Receipt", ...},
    ],
}
```

### Phase 2 (Enhanced UX - Frontend Changes)
**Add Option 3: Persistent Menu Bar**

Add bottom navigation:
```jsx
<div className="persistent-menu">
  <button>🏠 Menu</button>
  <button>🍽️ Orders</button>
  <button>📅 Book</button>
  <button>❓ Help</button>
</div>
```

---

## Implementation Plan

### Week 1: Backend Enhancement (No Frontend Changes)
1. ✅ Expand `QUICK_ACTION_SETS` from 10 to 20+ scenarios
2. ✅ Add secondary/contextual suggestions
3. ✅ Enhance LLM prompt for better classification
4. ✅ Track user context (new user, cart value, order count)
5. ✅ Show 5-6 buttons instead of 3
6. ✅ Add emoji icons for visual hierarchy

### Week 2: Frontend Enhancement (Optional)
1. Add persistent bottom menu bar
2. Add "More Actions" expandable menu
3. Add onboarding carousel for first-time users
4. Track user dismissal of suggestions

---

## Testing Strategy

### A/B Test Setup
- **Control:** 3 buttons (current)
- **Variant A:** 5-6 smart contextual buttons
- **Variant B:** 5-6 buttons + persistent menu bar

### Metrics to Track
- Feature discovery rate (% of users who use non-ordering tools)
- Click-through rate on quick replies
- Time to complete order
- User satisfaction score
- Feature usage distribution

### Expected Results
- Feature discovery: 20% → 60%+
- Booking tool usage: <1% → 15%+
- FAQ usage: <1% → 20%+
- Allergen tool usage: 0% → 10%+

---

## Conclusion

**Best Approach:** Option 4 (Smart Contextual) for immediate implementation
- ✅ No frontend changes
- ✅ High impact
- ✅ Can implement in 1-2 days

**Future Enhancement:** Add Option 3 (Persistent Menu Bar)
- Requires frontend work
- Provides long-term discoverability
- Implement in Phase 2

**Key Principle:**
> "Guide, don't overwhelm. Show 5-6 smart suggestions, not 15 generic options."

---

Would you like me to implement Option 4 (Smart Contextual) now?
