# User Journey Issues & Fixes Required

## 🔍 **Problems Identified from User Test**

### Issue #1: **Payment Flow Missing** ❌
**What Happened:**
```
User: "Checkout"
Bot: "Would you like to dine-in or take away?"
User: "Take Away"
Bot: "Order placed! ID: ORD-679BDB17" ← NO PAYMENT STEP!
```

**What SHOULD Happen:**
```
User: "Checkout"
Bot: "Would you like to dine-in or take away?"
User: "Take Away"
Bot: "Order created! Total: Rs.573. How would you like to pay?"
     [Quick Replies: "Card Payment" | "Cash on Delivery"]
User: "Card Payment"
Bot: "Please enter your card details..." (calls initiate_payment)
```

**Root Cause:**
- File: `crew_agent.py` line 1442
- Checkout tool places order and immediately marks as "confirmed"
- No call to `initiate_payment` tool
- Agent task description doesn't instruct payment workflow

---

### Issue #2: **Quick Replies Not Contextual** ❌
**Current:**
- After order placed: Shows "View Cart" and "What's Popular?"
- Not helpful - cart is already empty!

**Should Show:**
- After order placed: "Pay Now" | "Track Order" | "Order More"
- After adding to cart: "View Cart" | "Checkout" | "Add More"
- After payment: "Track Order" | "View Receipt" | "Rate Order"

---

### Issue #3: **Agent Not Following Full Workflow** ❌
We have 55 tools but the agent doesn't know the complete journey:

**Missing Instructions:**
1. After `checkout()` → MUST call `initiate_payment()`
2. After `initiate_payment()` → Wait for card details
3. After `submit_card_details()` → Call `verify_payment_otp()`
4. After payment → Offer "Track Order"

---

## 🛠️ **Fixes Required**

### **Fix 1: Update Agent Task Description**

**File:** `restaurant-chatbot/app/features/food_ordering/crew_agent.py`
**Line:** 3262-3268 (CRITICAL RULES section)

**Add:**
```python
**CRITICAL WORKFLOW - CHECKOUT TO PAYMENT:**
After calling checkout():
  1. Order is created but NOT paid yet
  2. YOU MUST immediately call initiate_payment() to start payment
  3. DO NOT tell customer "order confirmed" until payment is complete
  4. After initiate_payment(), guide customer to enter card details

Complete flow:
  checkout() → initiate_payment() → submit_card_details() → verify_payment_otp() → Done
```

---

### **Fix 2: Modify Checkout Tool Return Message**

**File:** `restaurant-chatbot/app/features/food_ordering/crew_agent.py`
**Line:** 1442

**Current:**
```python
return f"Order placed! ID: {order_display_id}. Items: {', '.join(order_items)}. Total: Rs.{total:.0f} ({order_type_display})"
```

**Change To:**
```python
return f"Order created! ID: {order_display_id}. Items: {', '.join(order_items)}. Total: Rs.{total:.0f} ({order_type_display}). IMPORTANT: Call initiate_payment() now to process payment before confirming order to customer."
```

---

### **Fix 3: Update Quick Replies Logic**

**File:** `restaurant-chatbot/app/core/agui_events.py` (or wherever quick replies are generated)

**Add Context-Aware Quick Replies:**

```python
def get_contextual_quick_replies(session_state: dict) -> list:
    """Generate quick replies based on current state"""

    # After adding to cart
    if session_state.get("cart_items") > 0 and not session_state.get("order_placed"):
        return [
            {"label": "View Cart", "action": "show my cart", "icon": "cart"},
            {"label": "Checkout", "action": "checkout", "icon": "checkout"},
            {"label": "Add More", "action": "show menu", "icon": "menu"}
        ]

    # After order placed (but not paid)
    if session_state.get("order_placed") and not session_state.get("payment_completed"):
        return [
            {"label": "Pay Now", "action": "pay for my order", "icon": "payment"},
            {"label": "Pay Cash", "action": "I'll pay cash on delivery", "icon": "cash"},
            {"label": "Cancel Order", "action": "cancel my order", "icon": "cancel"}
        ]

    # After payment completed
    if session_state.get("payment_completed"):
        return [
            {"label": "Track Order", "action": "track my order", "icon": "tracking"},
            {"label": "View Receipt", "action": "show receipt", "icon": "receipt"},
            {"label": "Order More", "action": "show menu", "icon": "menu"}
        ]

    # Default - browsing menu
    return [
        {"label": "View Menu", "action": "show me the menu", "icon": "menu"},
        {"label": "Popular Items", "action": "what's popular", "icon": "star"},
        {"label": "Special Offers", "action": "any deals today", "icon": "offers"}
    ]
```

---

### **Fix 4: Add Session State Tracking**

Track order/payment state in Redis:

```python
# After checkout
await set_session_state(session_id, {
    "order_placed": True,
    "order_id": order_display_id,
    "payment_completed": False,
    "order_type": order_type_clean
})

# After payment
await set_session_state(session_id, {
    "payment_completed": True,
    "payment_method": payment_method
})
```

---

## 📋 **Complete User Journey (How It Should Work)**

### **Journey 1: Card Payment**
```
1. User: "I want to order food"
   Bot: Shows menu
   Quick Replies: [Popular Items] [Offers] [Cuisines]

2. User clicks on items to add to cart
   Bot: "Added 2x Chicken Burger to cart"
   Quick Replies: [View Cart] [Checkout] [Add More]

3. User: "View Cart"
   Bot: Shows cart with total Rs.516
   Quick Replies: [Checkout] [Add More] [Clear Cart]

4. User: "Checkout"
   Bot: "Would you like dine-in or take-away?"
   Quick Replies: [Dine In] [Take Away]

5. User: "Take Away"
   Bot: "Order created! ID: ORD-ABC123, Total: Rs.516. How would you like to pay?"
   Quick Replies: [Card Payment] [Cash on Delivery]

6. User: "Card Payment"
   Bot: "Please enter your card details..."
   (Shows payment form or asks for details)

7. User enters card details
   Bot: "OTP sent to your registered mobile. Please enter OTP"
   Quick Replies: [Resend OTP]

8. User enters OTP
   Bot: "Payment successful! Your order is confirmed. Order ID: ORD-ABC123"
   Quick Replies: [Track Order] [View Receipt] [Order More]
```

### **Journey 2: Cash on Delivery**
```
...
5. User: "Take Away"
   Bot: "Order created! ID: ORD-ABC123, Total: Rs.516. How would you like to pay?"
   Quick Replies: [Card Payment] [Cash on Delivery]

6. User: "Cash on Delivery"
   Bot: "Order confirmed! Pay Rs.516 in cash when your order arrives. Order ID: ORD-ABC123"
   Quick Replies: [Track Order] [View Receipt] [Order More]
```

---

## 🎯 **Additional Improvements Needed**

### 1. **After Menu Display**
Current: Generic "What would you like?" response
Improve: "Browse our menu and tap items to add, or tell me what you're craving!"

### 2. **After Add to Cart**
Current: Just confirmation
Improve: Suggest related items
```
Bot: "Added 2x Chicken Burger (Rs.378).
     Would you like fries or a drink with that?
     - French Fries Rs.99
     - Coca Cola Rs.50"
Quick Replies: [Yes, add fries] [Just the burger] [View Cart]
```

### 3. **Order Tracking Proactive Updates**
After order placed, send status updates:
```
- "Your order is being prepared..."
- "Your order is ready for pickup!"
- "Your delivery driver is on the way!"
```

### 4. **Payment Failure Handling**
If payment fails:
```
Bot: "Payment failed. Would you like to:
     1. Try again with same card
     2. Use different card
     3. Pay cash on delivery"
Quick Replies: [Retry Payment] [Different Card] [Cash on Delivery]
```

---

## 🔧 **Implementation Priority**

### **Phase 1 (Critical - Fix Now):**
1. ✅ Add payment workflow to agent instructions
2. ✅ Modify checkout to prompt for payment
3. ✅ Add contextual quick replies

### **Phase 2 (High Priority):**
4. Add session state tracking
5. Implement upselling (fries/drinks after burger)
6. Add order status updates

### **Phase 3 (Nice to Have):**
7. Payment failure retry flow
8. Proactive notifications
9. Smart recommendations based on history

---

## 📊 **Testing Checklist After Fix**

- [ ] Order flow asks for payment method after checkout
- [ ] Card payment flow works (checkout → payment → OTP → success)
- [ ] Cash on delivery works (checkout → COD → confirmed)
- [ ] Quick replies change based on context
- [ ] Can't place order without payment (except COD)
- [ ] Payment tools are being called by agent
- [ ] Session state is tracked correctly

---

## 🚀 **Expected User Experience After Fix**

**Before:** 8 clicks, confusing flow, no payment
**After:** 5 clicks, guided journey, payment integrated

**User Satisfaction:**
- Clear next steps at each stage
- No confusion about what to do next
- Payment seamlessly integrated
- Can track order immediately after payment

---

**Files to Modify:**
1. `restaurant-chatbot/app/features/food_ordering/crew_agent.py` (agent task + checkout tool)
2. `restaurant-chatbot/app/core/agui_events.py` (quick replies logic)
3. `restaurant-chatbot/app/core/redis.py` (session state helpers)

---

**Estimated Fix Time:** 2-3 hours
**Impact:** High - Completes the core ordering journey
**Priority:** Critical - Without this, orders aren't actually paid!
