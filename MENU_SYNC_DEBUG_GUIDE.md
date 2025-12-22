# Menu Sync Debug Testing Guide
**Testing Debug Logging for Zero/Null Price Items**

---

## 📋 Overview

This guide helps you test the debug logging added to track items with zero or null prices from PetPooja API.

**What We're Testing:**
- Menu sync from PetPooja API
- Debug warnings for items with empty/zero/null prices
- Price data quality from source

**Expected Output:**
```
WARNING: Item 'A24-chicken' (ID: 10587463) has empty/zero price: None
WARNING: Item 'Americano' (ID: 10584283) has empty/zero price: ''
```

---

## 🚀 Method 1: Automatic Sync (Recommended)

The menu sync happens automatically when the chatbot service starts.

### **Step 1: Monitor PetPooja Logs**

Open a terminal and start watching the PetPooja service logs:

```bash
docker compose -f docker-compose.root.yml logs petpooja-app -f
```

### **Step 2: Restart PetPooja Service**

In another terminal, restart the service to trigger sync:

```bash
docker compose -f docker-compose.root.yml restart petpooja-app
```

### **Step 3: Watch for Debug Output**

Look for log entries like:

```
WARNING: Item 'Chicken Drumsticks' (ID: 10584215) has empty/zero price: ''
WARNING: NEW Item 'Cappuccino' (ID: 10584283) has empty/zero price: 0
```

**What to Look For:**
- ✅ `WARNING` entries for items with zero prices
- ✅ Item names and PetPooja IDs
- ✅ Raw price values: `None`, `''`, `'0'`, or `0`
- ✅ Both "UPDATE" and "NEW" item paths

---

## 🔧 Method 2: Manual Sync via API

Trigger sync manually via the PetPooja service API.

### **Step 1: Check if PetPooja Service is Running**

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{"status": "healthy"}
```

### **Step 2: Find the Sync Endpoint**

```bash
curl http://localhost:8001/docs
```

Open in browser: **http://localhost:8001/docs**

Look for endpoints like:
- `POST /api/v1/store-menu`
- `POST /api/v1/petpooja-sync`

### **Step 3: Monitor Logs While Syncing**

Terminal 1 - Watch logs:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app -f
```

Terminal 2 - Trigger sync (if endpoint available):
```bash
curl -X POST http://localhost:8001/api/v1/petpooja-sync \
  -H "Content-Type: application/json" \
  -d '{
    "restaurant_id": "your-restaurant-id",
    "app_key": "your-app-key",
    "app_secret": "your-app-secret",
    "access_token": "your-token",
    "sandbox_enabled": true
  }'
```

---

## 📊 Method 3: Database-Driven Test

Check current state and trigger sync.

### **Step 1: Check Current Zero-Price Items**

```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
SELECT
  menu_item_name,
  menu_item_price,
  ext_petpooja_item_id,
  updated_at
FROM menu_item
WHERE is_deleted = FALSE
  AND menu_item_price = 0
ORDER BY menu_item_name;
"
```

**Expected Output:**
```
          menu_item_name           | menu_item_price | ext_petpooja_item_id |       updated_at
-----------------------------------+-----------------+----------------------+------------------------
 A24-chicken                       |            0.00 |             10587463 | 2025-12-22 10:00:00+00
 Americano                         |            0.00 |             10584283 | 2025-12-22 10:00:00+00
 Cappuccino                        |            0.00 |             10584285 | 2025-12-22 10:00:00+00
...
(29 rows)
```

### **Step 2: Clear Menu Cache (Optional)**

Force a fresh sync:

```bash
# Delete existing menu items
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
DELETE FROM menu_item WHERE ext_petpooja_item_id IN (10587463, 10584283);
"
```

### **Step 3: Restart Services to Re-Sync**

```bash
docker compose -f docker-compose.root.yml restart petpooja-app
docker compose -f docker-compose.root.yml restart chatbot-app
```

### **Step 4: Check Logs**

```bash
docker compose -f docker-compose.root.yml logs petpooja-app | grep -i "empty/zero price"
```

### **Step 5: Verify Database Update**

```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
SELECT
  menu_item_name,
  menu_item_price,
  updated_at
FROM menu_item
WHERE ext_petpooja_item_id IN (10587463, 10584283)
ORDER BY updated_at DESC;
"
```

---

## 🧪 Method 4: Live Frontend Test

Test how the frontend displays zero-price items.

### **Step 1: Open Chatbot Frontend**

```
http://localhost:8000/
```

### **Step 2: Search for Zero-Price Items**

Type in the chat:
```
"Show me the menu"
```

Or specifically:
```
"Do you have Americano?"
"Show me A24-chicken"
"What about Cappuccino?"
```

### **Step 3: Observe Behavior**

**Current Behavior:**
- Items appear in the list
- Price shows: Rs.0

**Expected After Fix:**
- Price shows: "Market Price" or "Call for Price"
- OR item is hidden from menu

### **Step 4: Check Browser Console**

Open DevTools (F12) → Console tab

Look for any errors or warnings related to pricing.

---

## 📈 Method 5: Complete End-to-End Test

Full workflow test from API to frontend.

### **Test Script:**

Create `test_menu_sync_debug.sh`:

```bash
#!/bin/bash

echo "=========================================="
echo "Menu Sync Debug Test"
echo "=========================================="
echo ""

# 1. Check services
echo "1. Checking services..."
docker compose -f docker-compose.root.yml ps

echo ""
echo "2. Current zero-price items count..."
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
SELECT COUNT(*) as zero_price_count
FROM menu_item
WHERE is_deleted = FALSE AND menu_item_price = 0;
" -t

echo ""
echo "3. Restarting PetPooja service to trigger sync..."
docker compose -f docker-compose.root.yml restart petpooja-app

echo ""
echo "4. Waiting 10 seconds for sync to complete..."
sleep 10

echo ""
echo "5. Checking logs for debug warnings..."
docker compose -f docker-compose.root.yml logs petpooja-app --since 30s | grep -i "empty/zero price"

echo ""
echo "6. Checking updated items..."
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
SELECT
  menu_item_name,
  menu_item_price,
  TO_CHAR(updated_at, 'HH24:MI:SS') as update_time
FROM menu_item
WHERE is_deleted = FALSE
  AND menu_item_price = 0
  AND updated_at > NOW() - INTERVAL '5 minutes'
ORDER BY updated_at DESC
LIMIT 10;
"

echo ""
echo "=========================================="
echo "Test Complete!"
echo "=========================================="
```

### **Run the Test:**

```bash
chmod +x test_menu_sync_debug.sh
./test_menu_sync_debug.sh
```

---

## 🔍 What to Look For

### **✅ Success Indicators:**

1. **Log Warnings Appear:**
   ```
   WARNING: Item 'A24-chicken' (ID: 10587463) has empty/zero price: None
   ```

2. **Consistent Count:**
   - Before sync: 29 zero-price items
   - After sync: Still 29 (if PetPooja still sends Rs.0)
   - Logs show all 29 warnings

3. **Raw Value Captured:**
   - Logs show: `None`, `''`, `'0'`, or `0`
   - This tells us exactly what PetPooja is sending

### **❌ Issues to Watch For:**

1. **No Warnings:**
   - Means sync didn't run or items weren't updated
   - Check if PetPooja service is running

2. **Different Count:**
   - Zero-price count changed unexpectedly
   - May indicate data corruption or sync issues

3. **Error Messages:**
   - Database connection errors
   - PetPooja API authentication failures

---

## 📝 Expected Results

### **Scenario 1: PetPooja Sends Actual Zero Prices**

**Logs:**
```
WARNING: Item 'A24-chicken' (ID: 10587463) has empty/zero price: '0'
WARNING: Item 'Americano' (ID: 10584283) has empty/zero price: '0'
```

**Conclusion:** Restaurant needs to update prices in PetPooja dashboard

---

### **Scenario 2: PetPooja Sends Null/Empty**

**Logs:**
```
WARNING: Item 'A24-chicken' (ID: 10587463) has empty/zero price: None
WARNING: Item 'Americano' (ID: 10584283) has empty/zero price: ''
```

**Conclusion:** PetPooja API issue or incomplete data setup

---

### **Scenario 3: Items Should Have Variations**

**Logs:**
```
WARNING: Item 'Albaik International Chicken Meal' (ID: 10584214) has empty/zero price: None
```

**Database Check:**
```sql
SELECT
  mi.menu_item_name,
  mi.menu_item_allow_variation,
  COUNT(mv.menu_item_variation_id) as variation_count
FROM menu_item mi
LEFT JOIN menu_item_variation mv ON mi.menu_item_id = mv.menu_item_id
WHERE mi.ext_petpooja_item_id = 10584214
GROUP BY mi.menu_item_id;
```

**Result:**
```
menu_item_name                     | allow_variation | variation_count
-----------------------------------|-----------------|----------------
Albaik International Chicken Meal  | t               | 0
```

**Conclusion:** Item configured for variations but none exist - incomplete setup

---

## 🛠️ Troubleshooting

### **Problem: No Logs Appearing**

**Solution:**
```bash
# Check if logs are enabled
docker compose -f docker-compose.root.yml exec petpooja-app env | grep LOG

# Rebuild with logs enabled
docker compose -f docker-compose.root.yml build petpooja-app
docker compose -f docker-compose.root.yml up -d petpooja-app
```

### **Problem: Sync Not Triggering**

**Solution:**
```bash
# Check PetPooja service health
curl http://localhost:8001/health

# Check for errors
docker compose -f docker-compose.root.yml logs petpooja-app | tail -50

# Manual restart
docker compose -f docker-compose.root.yml restart petpooja-app
```

### **Problem: Can't Connect to Database**

**Solution:**
```bash
# Check PostgreSQL is running
docker compose -f docker-compose.root.yml ps postgres

# Test connection
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT 1;"
```

---

## 📊 Sample Test Report

After running tests, create a report:

```
MENU SYNC DEBUG TEST REPORT
Date: 2025-12-22
Tester: [Your Name]

RESULTS:
✅ Zero-price items detected: 29
✅ Debug warnings logged: 29
✅ Raw price values captured:
   - None: 12 items
   - '': 10 items
   - '0': 7 items

ITEMS REQUIRING ATTENTION:
1. A24-chicken (ID: 10587463) - Price: None
2. Americano (ID: 10584283) - Price: ''
3. Cappuccino (ID: 10584285) - Price: '0'
... (list all 29)

RECOMMENDATION:
□ Contact restaurant to update prices in PetPooja
□ Implement frontend "Market Price" display
□ Hide zero-price items from menu
```

---

## ✅ Quick Test Checklist

- [ ] Services running (chatbot, petpooja, postgres)
- [ ] Baseline count of zero-price items recorded
- [ ] Logs monitored in separate terminal
- [ ] PetPooja service restarted
- [ ] Debug warnings appear in logs
- [ ] Raw price values captured (None/''/0)
- [ ] Database updated_at timestamps recent
- [ ] Frontend displays items correctly
- [ ] Results documented

---

## 🎯 Next Steps After Testing

Based on test results, choose:

1. **If logs show PetPooja sends `0`:**
   → Ask restaurant to update prices

2. **If logs show `None` or `''`:**
   → Contact PetPooja support about API data quality

3. **If some items should have variations:**
   → Restaurant needs to configure variations in PetPooja

4. **Immediate frontend fix:**
   → Implement "Market Price" display for Rs.0 items

---

**Test Duration:** ~5-10 minutes
**Required Access:** Docker, PostgreSQL, Browser
**Skill Level:** Intermediate

---

**Happy Testing! 🧪**
