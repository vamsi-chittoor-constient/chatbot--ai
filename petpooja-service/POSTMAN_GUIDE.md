# Postman Collection Guide

## 📦 Files Included

1. **A24_PetPooja_Integration.postman_collection.json** - Complete API collection
2. **A24_PetPooja_Environment.postman_environment.json** - Environment variables

## 🚀 Quick Start

### Step 1: Import Collection

1. Open Postman
2. Click **Import** button
3. Select `A24_PetPooja_Integration.postman_collection.json`
4. Click **Import**

### Step 2: Import Environment

1. Click **Import** button again
2. Select `A24_PetPooja_Environment.postman_environment.json`
3. Click **Import**
4. Select "A24 PetPooja - Local" from environment dropdown (top right)

### Step 3: Update Environment Variables

Click the eye icon (👁️) next to environment dropdown and update:

| Variable | Description | Example |
|----------|-------------|---------|
| `base_url` | Your API URL | `http://localhost:8001` |
| `restaurant_id` | PetPooja Restaurant ID | `czw6b9ykas` |
| `callback_url` | Public webhook URL | `https://abc123.ngrok-free.app` |

## 📁 Collection Structure

```
A24 PetPooja Integration API
│
├── General
│   ├── Health Check
│   └── Root
│
├── Menu Operations
│   └── Fetch Menu
│
├── Order Operations
│   ├── Save Order
│   └── Cancel Order
│
└── Webhooks (Called by PetPooja)
    ├── Order Status Callback
    ├── Order Status - Cancelled
    ├── Order Status - Dispatched
    ├── Get Store Status (POST)
    ├── Get Store Status (GET)
    ├── Update Store Status - Close (POST)
    ├── Update Store Status - Open (POST)
    ├── Stock Update - Items Out of Stock
    ├── Stock Update - Addons Available
    └── Test Webhook
```

## 🔧 Testing Guide

### 1. Health Check

**Request:** `GET /health`

Test if API is running:
```bash
GET http://localhost:8001/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-18T...",
  "services": {
    "database": {
      "status": "healthy"
    },
    "petpooja": {
      "status": "configured"
    }
  }
}
```

### 2. Fetch Menu

**Request:** `POST /api/menu/fetch?restaurant_id=czw6b9ykas`

Fetches complete menu from PetPooja.

**Expected Response:**
```json
{
  "success": true,
  "message": "Menu fetched successfully",
  "data": {
    "items": [...],
    "item_categories": [...],
    "addon_groups": [...]
  }
}
```

### 3. Save Order

**Request:** `POST /api/orders/save`

Submit order to PetPooja POS. The order will appear as "Pending" on the POS.

**Important Fields:**
- `orderID`: Unique order ID (auto-generated with timestamp)
- `callback_url`: Your webhook URL for status updates
- `customer.details.phone`: Customer phone number
- `order_item.details`: Array of items with prices and taxes

**Expected Response:**
```json
{
  "success": true,
  "message": "Order saved successfully",
  "order_id": "ORD-1234567890"
}
```

### 4. Cancel Order

**Request:** `POST /api/orders/cancel`

Cancel a pending order. Only works before restaurant accepts it.

**Required Fields:**
- `restID`: Restaurant ID
- `clientorderID`: Your order ID
- `cancelReason`: Reason for cancellation
- `status`: "-1" (cancel code)

**Expected Response:**
```json
{
  "success": true,
  "message": "Order cancelled successfully",
  "order_id": "ORD-1234567890"
}
```

### 5. Webhooks

These endpoints are called BY PetPooja, but you can test them manually:

#### Order Status Callback

**Webhook:** `POST /api/webhooks/petpooja/order-callback`

PetPooja calls this when order status changes.

**Status Codes:**
- `-1`: Cancelled by restaurant
- `1`, `2`, `3`: Accepted by restaurant
- `4`: Dispatched (for self-delivery)
- `5`: Food ready for pickup
- `10`: Delivered

**Test Accepted Order:**
```json
{
  "restID": "czw6b9ykas",
  "orderID": "ORD-1234567890",
  "status": "1",
  "minimum_prep_time": "20"
}
```

**Test Dispatched Order:**
```json
{
  "restID": "czw6b9ykas",
  "orderID": "ORD-1234567890",
  "status": "4",
  "rider_name": "Rajesh Kumar",
  "rider_phone_number": "+91-9876543210"
}
```

#### Store Status Webhooks

**Get Store Status:** Check if restaurant is open

```
POST /api/webhooks/petpooja/store-status
{
  "restID": "czw6b9ykas"
}
```

**Response:**
```json
{
  "status": "success",
  "store_status": "1",  // 1=Open, 0=Closed
  "http_code": 200,
  "message": "Store is open"
}
```

**Update Store Status:** Merchant turns store on/off

```
POST /api/webhooks/petpooja/update-store-status
{
  "restID": "czw6b9ykas",
  "store_status": "0",  // Closing
  "turn_on_time": "2025-11-19 18:00:00",
  "reason": "Lunch break"
}
```

#### Stock Update Webhook

**Mark Items Out of Stock:**

```json
{
  "restID": "czw6b9ykas",
  "inStock": false,
  "type": "item",
  "itemID": {
    "0": "12345",
    "1": "12346"
  },
  "autoTurnOnTime": "custom",
  "customTurnOnTime": "2025-11-19T18:00:00"
}
```

**Auto Turn-On Options:**
- `""` (empty): Manual turn-on only
- `"endofday"`: Auto turn-on at midnight
- `"custom"`: Turn on at specific time

## 🔗 Webhook URLs for PetPooja Dashboard

Configure these URLs in your PetPooja dashboard:

### For Local Testing (using ngrok)

1. Start ngrok: `ngrok http 8001`
2. Get your ngrok URL: `https://abc123.ngrok-free.app`
3. Configure in PetPooja:

| Webhook | URL |
|---------|-----|
| Order Callback | `https://abc123.ngrok-free.app/api/webhooks/petpooja/order-callback` |
| Store Status | `https://abc123.ngrok-free.app/api/webhooks/petpooja/store-status` |
| Update Store Status | `https://abc123.ngrok-free.app/api/webhooks/petpooja/update-store-status` |
| Stock Update | `https://abc123.ngrok-free.app/api/webhooks/petpooja/stock-update` |

### For Production

Replace ngrok URL with your production domain:
```
https://api.yourdomain.com/api/webhooks/petpooja/...
```

## 📝 Environment Variables Reference

| Variable | Description | Where to Get It |
|----------|-------------|----------------|
| `base_url` | Your API server URL | Local: `http://localhost:8001`<br>Production: Your domain |
| `restaurant_id` | PetPooja Restaurant ID | From PetPooja dashboard or `.env` file |
| `callback_url` | Public webhook URL | ngrok URL (local) or production domain |

## 🎯 Common Use Cases

### Testing Order Flow

1. **Save Order** → Creates order on PetPooja POS
2. Wait for webhook → PetPooja calls **Order Status Callback** when accepted
3. Monitor status changes → Track through Accepted → Food Ready → Dispatched → Delivered

### Testing Stock Updates

1. Mark item as out of stock → **Stock Update** webhook
2. Item becomes unavailable in menu
3. Auto turn-on at scheduled time (or manual)

### Testing Store Status

1. Merchant closes store → **Update Store Status** (store_status: "0")
2. Check status → **Get Store Status** (returns "0")
3. Merchant opens store → **Update Store Status** (store_status: "1")

## ⚡ Quick Test Sequence

Run these in order to test complete flow:

1. ✅ **Health Check** - Verify API is running
2. ✅ **Fetch Menu** - Get menu from PetPooja
3. ✅ **Save Order** - Submit test order
4. ✅ **Order Status Callback** - Simulate acceptance
5. ✅ **Get Store Status** - Check if open
6. ✅ **Stock Update** - Mark item out of stock

## 🐛 Troubleshooting

### Issue: "Connection refused"
- Check if API server is running: `python main.py`
- Verify port is correct: Default is `8001`

### Issue: "Restaurant not found"
- Update `restaurant_id` variable
- Check PetPooja credentials in `.env`

### Issue: Webhooks not working locally
- Use ngrok: `ngrok http 8001`
- Update `callback_url` variable with ngrok URL
- Configure webhook URLs in PetPooja dashboard

### Issue: "Invalid JSON response"
- Check PetPooja credentials are correct
- Verify sandbox mode is enabled if testing
- Check logs: `logs/petpooja_microservice.log`

## 📚 Additional Resources

- **API Documentation:** `/docs` (Swagger UI)
- **Alternative Docs:** `/redoc` (ReDoc)
- **Logs:** `logs/petpooja_microservice.log`
- **Environment:** `.env` file

## 🎉 Success Indicators

When everything works correctly:

1. ✅ Health check returns "healthy"
2. ✅ Menu fetch returns items and categories
3. ✅ Order save returns success with order_id
4. ✅ Webhooks return 200 OK
5. ✅ Logs show successful API calls

Happy Testing! 🚀
