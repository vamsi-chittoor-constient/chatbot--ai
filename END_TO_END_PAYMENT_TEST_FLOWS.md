# End-to-End Payment Test Flows

## 🎯 Objective
Test 5 complete order flows from start to payment completion to verify the entire system works including Razorpay integration.

---

## 🚀 Pre-Test Setup

### 1. Apply Database Seed
```bash
psql -U admin -d restaurant_ai -f restaurant-chatbot/db/12-seed-payment-gateway-razorpay.sql
```

### 2. Rebuild and Restart Services
```bash
# Stop all services
docker-compose down

# Rebuild with new env vars
docker-compose build restaurant-chatbot

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f restaurant-chatbot
```

### 3. Verify Razorpay Credentials Loaded
```bash
# Check inside container
docker exec restaurant-chatbot printenv | grep RAZORPAY

# Should show:
# RAZORPAY_KEY_ID=rzp_test_dXwWkc7Rw3f52T
# RAZORPAY_KEY_SECRET=bs6Jk9HhctjKCBPN3IE4iPsF
```

---

## 🧪 Test Flow 1: Dine-In Order with Card Payment

**Customer Journey:**
```
User: "Hi, I'd like to order food"
Agent: [Greeting + menu offer]

User: "Show me the menu"
Agent: [Displays menu with categories]

User: "Add 2 Chicken Biryani"
Agent: [Adds to cart, shows cart total]

User: "Add 1 Paneer Tikka"
Agent: [Adds to cart, shows updated total]

User: "View my cart"
Agent: [Shows all items, quantities, and total amount]

User: "Checkout for dine-in"
Agent: [Creates order, confirms order number]

User: "I'll pay by card"
Agent: [Creates Razorpay payment link, sends SMS]
```

**Verification Steps:**
1. ✅ Cart created with correct items
2. ✅ Order created in database with status="confirmed", payment_status="pending"
3. ✅ Payment link generated (starts with `https://rzp.io/`)
4. ✅ SMS sent with payment link
5. ✅ Payment link opens in browser
6. ✅ Complete payment with test card: `4111 1111 1111 1111`
7. ✅ Razorpay redirects to callback URL
8. ✅ Order status updated to payment_status="paid"
9. ✅ Payment confirmation SMS sent
10. ✅ WebSocket notification received (if chat source)

**Expected Database State:**
```sql
-- Check order
SELECT order_number, status, payment_status, total_amount, order_type
FROM orders
WHERE order_number = '<ORDER_NUMBER>';
-- Expected: status='confirmed', payment_status='paid', order_type='dine_in'

-- Check payment_order
SELECT status, amount/100.0 as amount_rupees, payment_link_id
FROM payment_order
WHERE order_id = '<ORDER_ID>';
-- Expected: status='paid', amount matches order total

-- Check payment_transaction
SELECT payment_status, amount_paid/100.0 as paid_rupees, payment_method, card_last4
FROM payment_transaction
WHERE payment_order_id = '<PAYMENT_ORDER_ID>';
-- Expected: payment_status='captured', payment_method='card', card_last4='1111'
```

**Success Criteria:**
- ✅ Order placed successfully
- ✅ Payment link received
- ✅ Payment completed
- ✅ Order confirmed with payment_status='paid'
- ✅ Customer received confirmation SMS

---

## 🧪 Test Flow 2: Takeout Order with UPI Payment

**Customer Journey:**
```
User: "I want to order for takeout"
Agent: [Greeting]

User: "Show popular items"
Agent: [Shows popular dishes]

User: "Add 1 Butter Chicken and 2 Naan"
Agent: [Adds items to cart]

User: "Add 1 Mango Lassi"
Agent: [Adds drink to cart]

User: "Checkout for takeout"
Agent: [Creates order]

User: "Pay online"
Agent: [Creates payment link, sends SMS]
```

**Payment Method:** Choose UPI on Razorpay page

**Verification Steps:**
1. ✅ Order created with order_type="takeaway"
2. ✅ Payment link generated
3. ✅ Select UPI payment method
4. ✅ Complete UPI test payment
5. ✅ Payment recorded with payment_method='upi'
6. ✅ Order status updated

**Expected Database State:**
```sql
SELECT
    o.order_number,
    o.order_type,
    o.payment_status,
    pt.payment_method,
    pt.upi_vpa
FROM orders o
JOIN payment_order po ON po.order_id = o.id
JOIN payment_transaction pt ON pt.payment_order_id = po.id
WHERE o.order_number = '<ORDER_NUMBER>';
-- Expected: order_type='takeaway', payment_status='paid', payment_method='upi'
```

**Success Criteria:**
- ✅ Takeout order created
- ✅ UPI payment completed
- ✅ Payment method recorded correctly

---

## 🧪 Test Flow 3: Order with Payment Retry

**Customer Journey:**
```
User: "Order food for dine-in"
Agent: [Greeting]

User: "Add 1 Dal Makhani and 2 Roti"
Agent: [Adds to cart]

User: "Checkout"
Agent: [Creates order]

User: "Pay online"
Agent: [Creates payment link]
```

**Intentional Failure:**
1. Open payment link
2. Use **failure test card**: `4000 0000 0000 0002`
3. Payment should fail

**Retry Flow:**
```
User: "Payment failed, can I try again?"
Agent: [Generates new payment link with retry_count=1]
```

4. Open new payment link
5. Use **success test card**: `4111 1111 1111 1111`
6. Complete payment successfully

**Verification Steps:**
```sql
-- Check retry attempts
SELECT
    retry_count,
    status,
    payment_link_id,
    created_at
FROM payment_order
WHERE order_id = '<ORDER_ID>';
-- Expected: retry_count=1, status='paid'

-- Check all payment transactions (failed + successful)
SELECT
    payment_status,
    failure_reason,
    attempted_at
FROM payment_transaction
WHERE payment_order_id = '<PAYMENT_ORDER_ID>'
ORDER BY attempted_at;
-- Expected: 1 failed transaction, 1 successful transaction
```

**Success Criteria:**
- ✅ First payment fails gracefully
- ✅ Retry mechanism works (new link generated)
- ✅ Second payment succeeds
- ✅ retry_count incremented
- ✅ Both transactions recorded

---

## 🧪 Test Flow 4: Multiple Items Order with Netbanking

**Customer Journey:**
```
User: "Hi, show me lunch menu"
Agent: [Shows lunch menu with meal-time filtering]

User: "Add 1 Chicken Curry"
Agent: [Adds to cart]

User: "Add 1 Veg Pulao"
Agent: [Adds to cart]

User: "Add 2 Papad"
Agent: [Adds to cart]

User: "Add 1 Gulab Jamun"
Agent: [Adds dessert]

User: "What's my total?"
Agent: [Shows cart with total amount]

User: "Checkout for dine-in"
Agent: [Creates order]

User: "Pay with netbanking"
Agent: [Creates payment link]
```

**Payment Method:** Select Netbanking on Razorpay page

**Verification Steps:**
1. ✅ All 5 items added to cart
2. ✅ Total amount calculated correctly
3. ✅ Order items persisted to database
4. ✅ Payment link sent
5. ✅ Netbanking payment completed
6. ✅ Payment method='netbanking' recorded

**Expected Database State:**
```sql
-- Verify all order items
SELECT
    mi.name,
    oi.quantity,
    oi.unit_price,
    oi.total_price
FROM order_items oi
JOIN menu_items mi ON oi.menu_item_id = mi.id
WHERE oi.order_id = '<ORDER_ID>';
-- Expected: 4 rows (Chicken Curry, Veg Pulao, Papad x2, Gulab Jamun)

-- Verify payment
SELECT
    pt.payment_method,
    pt.amount_paid / 100.0 as amount_rupees,
    pt.bank_name
FROM payment_transaction pt
JOIN payment_order po ON pt.payment_order_id = po.id
WHERE po.order_id = '<ORDER_ID>';
-- Expected: payment_method='netbanking', amount matches order total
```

**Success Criteria:**
- ✅ Multiple items order
- ✅ Correct total calculation
- ✅ Netbanking payment successful
- ✅ All items recorded in database

---

## 🧪 Test Flow 5: Search-Based Order with Wallet Payment

**Customer Journey:**
```
User: "I want something spicy"
Agent: [Shows spicy dishes]

User: "Add 1 Chicken 65"
Agent: [Adds to cart]

User: "Search for drinks"
Agent: [Shows beverages]

User: "Add 2 Coke"
Agent: [Adds drinks to cart]

User: "Any desserts?"
Agent: [Shows desserts]

User: "Add 1 Ice Cream"
Agent: [Adds dessert]

User: "Proceed to checkout for takeout"
Agent: [Creates order]

User: "Pay with wallet"
Agent: [Creates payment link]
```

**Payment Method:** Select Wallet (Paytm/PhonePe) on Razorpay page

**Verification Steps:**
1. ✅ Search functionality works
2. ✅ Items from different categories added
3. ✅ Takeout order created
4. ✅ Payment link generated
5. ✅ Wallet payment completed
6. ✅ Payment method='wallet' recorded with wallet_provider

**Expected Database State:**
```sql
-- Verify search-based order
SELECT
    o.order_number,
    o.order_type,
    COUNT(oi.id) as item_count,
    o.total_amount / 100.0 as total_rupees
FROM orders o
JOIN order_items oi ON oi.order_id = o.id
WHERE o.order_number = '<ORDER_NUMBER>'
GROUP BY o.id;
-- Expected: order_type='takeaway', item_count=3 (spicy+drink+dessert)

-- Verify wallet payment
SELECT
    pt.payment_method,
    pt.wallet_provider,
    pt.payment_status
FROM payment_transaction pt
JOIN payment_order po ON pt.payment_order_id = po.id
WHERE po.order_id = '<ORDER_ID>';
-- Expected: payment_method='wallet', wallet_provider='paytm' or 'phonepe'
```

**Success Criteria:**
- ✅ Search functionality works
- ✅ Multi-category order
- ✅ Wallet payment successful
- ✅ Wallet provider recorded

---

## 📊 Post-Test Verification

### Overall Payment Statistics
```sql
-- Payment success rate
SELECT
    COUNT(*) as total_payments,
    SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as successful,
    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
    ROUND(100.0 * SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM payment_order
WHERE created_at > NOW() - INTERVAL '1 hour';
-- Expected: 4-5 successful payments (depending on retry test), ~80-100% success rate
```

### Payment Methods Distribution
```sql
SELECT
    payment_method,
    COUNT(*) as count,
    SUM(amount_paid) / 100.0 as total_amount_rupees
FROM payment_transaction
WHERE payment_status = 'captured'
AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY payment_method;
-- Expected: Mix of card, upi, netbanking, wallet
```

### Order Status Summary
```sql
SELECT
    o.order_type,
    o.payment_status,
    COUNT(*) as count
FROM orders o
WHERE o.created_at > NOW() - INTERVAL '1 hour'
GROUP BY o.order_type, o.payment_status;
-- Expected: All orders with payment_status='paid'
```

---

## ✅ Final Checklist

After completing all 5 flows:

- [ ] **Flow 1 (Dine-In + Card):** ✅ Payment completed
- [ ] **Flow 2 (Takeout + UPI):** ✅ Payment completed
- [ ] **Flow 3 (Retry):** ✅ Failure handled, retry successful
- [ ] **Flow 4 (Multi-item + Netbanking):** ✅ Payment completed
- [ ] **Flow 5 (Search + Wallet):** ✅ Payment completed

**Database Verification:**
- [ ] All payment_order records show status='paid'
- [ ] All payment_transaction records exist
- [ ] All orders show payment_status='paid'
- [ ] Payment methods recorded correctly (card, upi, netbanking, wallet)
- [ ] Retry count tracked correctly
- [ ] Order types correct (dine_in, takeaway)

**Integration Verification:**
- [ ] Razorpay payment links generated
- [ ] SMS notifications sent (Twilio)
- [ ] Callback URL handling works
- [ ] WebSocket notifications sent (if chat source)
- [ ] Circuit breaker doesn't block valid requests
- [ ] Logs show no errors

---

## 🐛 Common Issues & Solutions

### Issue: "Razorpay credentials missing"
```bash
# Check env vars loaded
docker exec restaurant-chatbot printenv | grep RAZORPAY

# If empty, rebuild:
docker-compose down
docker-compose build restaurant-chatbot
docker-compose up -d
```

### Issue: Payment link not generated
```bash
# Check payment_gateway table
docker exec postgres psql -U admin -d restaurant_ai -c "SELECT * FROM payment_gateway WHERE payment_gateway_code='razorpay';"

# If empty, run seed:
docker exec -i postgres psql -U admin -d restaurant_ai < restaurant-chatbot/db/12-seed-payment-gateway-razorpay.sql
```

### Issue: SMS not sent
```bash
# Check Twilio credentials
docker exec restaurant-chatbot printenv | grep TWILIO

# Verify phone number format: +91XXXXXXXXXX
```

### Issue: Callback not working
```bash
# Check callback URL
curl -X GET "http://localhost:8000/api/v1/payment/callback?source=external&razorpay_payment_link_status=paid"

# Should return 200 OK
```

---

## 📈 Expected Results

**All 5 flows should:**
1. ✅ Create order successfully
2. ✅ Generate Razorpay payment link
3. ✅ Send SMS with payment link
4. ✅ Open payment page on Razorpay
5. ✅ Accept test payment
6. ✅ Redirect to callback URL
7. ✅ Update order payment_status to 'paid'
8. ✅ Send payment confirmation SMS
9. ✅ Record transaction in database

**Total Test Time:** ~30-45 minutes for all 5 flows

**Success Rate:** 100% (all flows complete without errors)

---

## 🎉 Cleanup (Optional)

### Can Delete payment-service-main? YES! ✅

The payment-service-main folder was only used as reference to:
1. ✅ Extract Razorpay test credentials
2. ✅ Verify payment link generation pattern

**Both objectives complete!** You can safely delete it:

```bash
rm -rf payment-service-main/
```

Your current system is **far superior** with:
- 10+ payment tables vs 1 table
- Circuit breaker protection
- Retry logic
- SMS/WhatsApp notifications
- Comprehensive error handling
- Better security

**No need to keep payment-service-main anymore!**

---

## 📞 Support

If any flow fails, check:
1. Logs: `docker-compose logs restaurant-chatbot`
2. Database: Use queries above
3. Razorpay Dashboard: https://dashboard.razorpay.com/app/payments
4. Testing Guide: `RAZORPAY_PAYMENT_TESTING_GUIDE.md`

Happy testing! 🚀
