# Quick Test Commands - Menu Sync Debug

Copy and paste these commands to quickly test the menu sync debug logging.

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Watch logs in real-time
docker compose -f docker-compose.root.yml logs petpooja-app -f

# 2. (In another terminal) Restart to trigger sync
docker compose -f docker-compose.root.yml restart petpooja-app

# 3. Watch for warnings (after 10 seconds)
# Press Ctrl+C on the logs window and run:
docker compose -f docker-compose.root.yml logs petpooja-app | grep "empty/zero price"
```

---

## 📊 Database Quick Checks

### Count zero-price items:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT COUNT(*) FROM menu_item WHERE is_deleted = FALSE AND menu_item_price = 0;"
```

### List zero-price items:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT menu_item_name, menu_item_price, ext_petpooja_item_id FROM menu_item WHERE is_deleted = FALSE AND menu_item_price = 0 ORDER BY menu_item_name LIMIT 10;"
```

### Check recently updated items:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT menu_item_name, menu_item_price, updated_at FROM menu_item WHERE is_deleted = FALSE AND updated_at > NOW() - INTERVAL '10 minutes' ORDER BY updated_at DESC LIMIT 10;"
```

---

## 🔍 Log Analysis Commands

### Show only warnings:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app | grep -i "WARNING.*price"
```

### Show recent logs (last 2 minutes):
```bash
docker compose -f docker-compose.root.yml logs petpooja-app --since 2m
```

### Count warnings:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app | grep -c "empty/zero price"
```

### Extract item names from warnings:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app | grep "empty/zero price" | sed -n "s/.*Item '\([^']*\)'.*/\1/p"
```

---

## 🛠️ Service Management

### Check all services:
```bash
docker compose -f docker-compose.root.yml ps
```

### Restart only PetPooja:
```bash
docker compose -f docker-compose.root.yml restart petpooja-app
```

### Restart both services:
```bash
docker compose -f docker-compose.root.yml restart petpooja-app chatbot-app
```

### Rebuild and restart:
```bash
docker compose -f docker-compose.root.yml build petpooja-app
docker compose -f docker-compose.root.yml up -d petpooja-app
```

---

## 🧪 Automated Test

### Run the test script:
```bash
python test_menu_sync_debug.py
```

### Expected output:
```
==================================================
  MENU SYNC DEBUG TEST
==================================================

✅ petpooja-app: Running
✅ chatbot-app: Running
✅ postgres: Running

Current zero-price items: 29

Found 29 debug warnings:
  ⚠️  A24-chicken                              → Price: None
  ⚠️  Americano                                → Price: ''
  ...

✅ Debug logging is working!
```

---

## 📈 Full Diagnostic

### Run all checks at once:
```bash
echo "=== Services ===" && \
docker compose -f docker-compose.root.yml ps && \
echo "" && \
echo "=== Zero-Price Count ===" && \
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT COUNT(*) FROM menu_item WHERE is_deleted = FALSE AND menu_item_price = 0;" -t && \
echo "" && \
echo "=== Recent Warnings ===" && \
docker compose -f docker-compose.root.yml logs petpooja-app --since 5m | grep "empty/zero price" | head -5
```

---

## 🎯 Specific Item Lookup

### Check specific item by name:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT menu_item_name, menu_item_price, menu_item_allow_variation, ext_petpooja_item_id FROM menu_item WHERE menu_item_name LIKE '%Americano%' AND is_deleted = FALSE;"
```

### Check specific item by PetPooja ID:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT menu_item_name, menu_item_price, menu_item_status, updated_at FROM menu_item WHERE ext_petpooja_item_id = 10584283;"
```

---

## 🔄 Force Re-Sync

### Clear cache and restart (full re-sync):
```bash
# Note: This doesn't delete data, just triggers fresh sync
docker compose -f docker-compose.root.yml restart petpooja-app chatbot-app
```

### Delete specific items to force re-creation:
```bash
# CAUTION: Only use for testing
docker exec a24-postgres psql -U admin -d restaurant_ai -c "DELETE FROM menu_item WHERE ext_petpooja_item_id IN (10584283, 10587463);"

# Then restart to re-sync
docker compose -f docker-compose.root.yml restart petpooja-app
```

---

## 📝 Save Logs to File

### Save all logs:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app > petpooja_logs_$(date +%Y%m%d_%H%M%S).txt
```

### Save only warnings:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app | grep "empty/zero price" > price_warnings_$(date +%Y%m%d_%H%M%S).txt
```

---

## 🎨 Pretty Output

### Formatted zero-price items:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
SELECT
  ROW_NUMBER() OVER (ORDER BY menu_item_name) as \"#\",
  menu_item_name as \"Item Name\",
  'Rs.' || menu_item_price as \"Price\",
  ext_petpooja_item_id as \"PetPooja ID\"
FROM menu_item
WHERE is_deleted = FALSE
  AND menu_item_price = 0
ORDER BY menu_item_name;
"
```

---

## ⚡ One-Liner Tests

### Test 1: Quick health check
```bash
curl -s http://localhost:8001/health && echo " ✅ PetPooja OK" || echo " ❌ PetPooja Down"
```

### Test 2: Check if sync happened recently
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT CASE WHEN MAX(updated_at) > NOW() - INTERVAL '10 minutes' THEN '✅ Recent sync' ELSE '⚠️  No recent sync' END FROM menu_item;" -t
```

### Test 3: Zero-price percentage
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT ROUND(COUNT(*) FILTER (WHERE menu_item_price = 0) * 100.0 / COUNT(*), 1) || '% zero-price' FROM menu_item WHERE is_deleted = FALSE;" -t
```

---

## 🆘 Troubleshooting Commands

### Check if PostgreSQL is accessible:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "SELECT version();"
```

### Check PetPooja service health:
```bash
curl http://localhost:8001/health
```

### View PetPooja environment:
```bash
docker compose -f docker-compose.root.yml exec petpooja-app env | grep PETPOOJA
```

### Check for errors in logs:
```bash
docker compose -f docker-compose.root.yml logs petpooja-app | grep -i error | tail -20
```

---

## 📊 Export Report

### Generate CSV of zero-price items:
```bash
docker exec a24-postgres psql -U admin -d restaurant_ai -c "
COPY (
  SELECT
    menu_item_name,
    menu_item_price,
    ext_petpooja_item_id,
    menu_item_status,
    updated_at
  FROM menu_item
  WHERE is_deleted = FALSE AND menu_item_price = 0
  ORDER BY menu_item_name
) TO STDOUT WITH CSV HEADER;
" > zero_price_items.csv

echo "✅ Exported to zero_price_items.csv"
```

---

**Quick Reference Card**
- 📋 Full Guide: MENU_SYNC_DEBUG_GUIDE.md
- 🤖 Auto Test: python test_menu_sync_debug.py
- 📖 Documentation: CHATBOT_CAPABILITIES_GUIDE.md
