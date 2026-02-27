# A24 Restaurant Data Pipeline - API Reference

## Table of Contents

1. [Base URL & Authentication](#base-url--authentication)
2. [General Endpoints](#general-endpoints)
3. [Restaurant Endpoints](#restaurant-endpoints)
4. [Menu Endpoints](#menu-endpoints)
5. [Order Endpoints](#order-endpoints)
6. [Webhook Endpoints](#webhook-endpoints)
7. [Response Codes](#response-codes)
8. [Error Handling](#error-handling)

---

## Base URL & Authentication

### Base URL

**Sandbox:**
```
http://localhost:8001
```

**Production:**
```
https://api.yourdomain.com
```

### Authentication

All endpoints (except webhooks and health check) require authentication using Bearer token.

**Header:**
```http
Authorization: Bearer a24-backend-secure-token-2024
```

**Example:**
```bash
curl -X GET http://localhost:8001/api/restaurants \
  -H "Authorization: Bearer a24-backend-secure-token-2024"
```

---

## General Endpoints

### 1. Root - API Info

Get API information and version.

**Endpoint:** `GET /`

**Authentication:** Not required

**Response:**
```json
{
  "app_name": "A24 Restaurant Data Pipeline",
  "version": "1.0.0",
  "status": "running"
}
```

---

### 2. Health Check

Check API health and database connectivity.

**Endpoint:** `GET /health`

**Authentication:** Not required

**Response:**
```json
{
  "status": "healthy",
  "database": "connected",
  "petpooja_credentials": "configured",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Service healthy
- `503 Service Unavailable` - Service unhealthy

---

## Restaurant Endpoints

### 1. Add Restaurant

Add a new restaurant with PetPooja credentials.

**Endpoint:** `POST /api/restaurants/add`

**Request Body:**
```json
{
  "restaurant_name": "Test Restaurant",
  "email": "test@example.com",
  "phone_no": "1234567890",
  "petpooja_credentials": {
    "vendor_restaurant_id": "34467",
    "app_key": "your_app_key",
    "app_secret": "your_app_secret",
    "access_token": "your_access_token",
    "sandbox_enabled": true
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Restaurant added successfully",
  "restaurant_id": "1",
  "data": {
    "id": 1,
    "restaurant_name": "Test Restaurant",
    "email": "test@example.com",
    "phone_no": "1234567890",
    "status": "active",
    "created_at": "2025-11-14T10:00:00Z"
  }
}
```

**Status Codes:**
- `201 Created` - Restaurant created successfully
- `400 Bad Request` - Invalid input data
- `409 Conflict` - Restaurant already exists
- `401 Unauthorized` - Invalid or missing authentication

---

### 2. List Restaurants

Get list of restaurants with optional filters.

**Endpoint:** `GET /api/restaurants`

**Query Parameters:**
- `status` (optional): Filter by status (active/inactive)
- `limit` (optional): Number of records (default: 100, max: 100)
- `offset` (optional): Offset for pagination (default: 0)

**Example:**
```
GET /api/restaurants?status=active&limit=50&offset=0
```

**Response:**
```json
{
  "restaurants": [
    {
      "id": 1,
      "restaurant_name": "Test Restaurant",
      "email": "test@example.com",
      "phone_no": "1234567890",
      "status": "active",
      "petpooja_restaurant_id": "34467",
      "created_at": "2025-11-14T10:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid authentication

---

### 3. Get Restaurant Details

Get detailed information about a specific restaurant.

**Endpoint:** `GET /api/restaurants/{restaurant_id}`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Response:**
```json
{
  "id": 1,
  "restaurant_name": "Test Restaurant",
  "email": "test@example.com",
  "phone_no": "1234567890",
  "status": "active",
  "petpooja_credentials": {
    "vendor_restaurant_id": "34467",
    "sandbox_enabled": true,
    "is_active": true
  },
  "branches": [],
  "created_at": "2025-11-14T10:00:00Z",
  "updated_at": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `401 Unauthorized` - Invalid authentication

---

### 4. Update Restaurant Credentials

Update PetPooja credentials for a restaurant.

**Endpoint:** `PUT /api/restaurants/{restaurant_id}/credentials`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Request Body:**
```json
{
  "vendor_restaurant_id": "34467",
  "app_key": "new_app_key",
  "app_secret": "new_app_secret",
  "access_token": "new_access_token",
  "sandbox_enabled": false,
  "is_active": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Credentials updated successfully",
  "restaurant_id": "1"
}
```

**Status Codes:**
- `200 OK` - Updated successfully
- `404 Not Found` - Restaurant not found
- `400 Bad Request` - Invalid input data
- `401 Unauthorized` - Invalid authentication

---

### 5. Delete Restaurant

Delete a restaurant and all associated data.

**Endpoint:** `DELETE /api/restaurants/{restaurant_id}`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Response:**
```json
{
  "success": true,
  "message": "Restaurant deleted successfully",
  "restaurant_id": "1"
}
```

**Status Codes:**
- `200 OK` - Deleted successfully
- `404 Not Found` - Restaurant not found
- `401 Unauthorized` - Invalid authentication

---

### 6. Onboard Restaurant

Complete restaurant onboarding (add + sync).

**Endpoint:** `POST /api/restaurants/onboard`

**Request Body:**
```json
{
  "restaurant_name": "Test Restaurant",
  "email": "test@example.com",
  "phone_no": "1234567890",
  "vendor_restaurant_id": "34467",
  "app_key": "your_app_key",
  "app_secret": "your_app_secret",
  "access_token": "your_access_token",
  "sandbox_enabled": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Restaurant onboarded successfully",
  "restaurant_id": "1",
  "restaurant_details_synced": true,
  "menu_synced": true,
  "branches_synced": 1,
  "items_synced": 150
}
```

**Status Codes:**
- `201 Created` - Onboarded successfully
- `400 Bad Request` - Invalid input data
- `409 Conflict` - Restaurant already exists
- `401 Unauthorized` - Invalid authentication

---

### 7. Fetch Restaurant Details from PetPooja

Fetch and update restaurant details from PetPooja API.

**Endpoint:** `POST /api/restaurants/{restaurant_id}/fetch-details`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Response:**
```json
{
  "success": true,
  "message": "Restaurant details fetched successfully",
  "restaurant_id": "4878",
  "restaurant_name": "Test Restaurant",
  "branches": 1,
  "updated_at": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `500 Internal Server Error` - PetPooja API error
- `401 Unauthorized` - Invalid authentication

---

### 8. Sync All (Restaurant + Menu)

Sync both restaurant details and menu data.

**Endpoint:** `POST /api/restaurants/{restaurant_id}/sync-all`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Response:**
```json
{
  "success": true,
  "message": "Sync completed successfully",
  "restaurant_synced": true,
  "menu_synced": true,
  "categories_synced": 10,
  "items_synced": 150,
  "sync_timestamp": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `500 Internal Server Error` - Sync error
- `401 Unauthorized` - Invalid authentication

---

### 9. Get Restaurant Status

Get restaurant operational status from PetPooja.

**Endpoint:** `GET /api/restaurants/status?restID={restaurant_id}`

**Query Parameters:**
- `restID` (required): Restaurant ID

**Response:**
```json
{
  "success": true,
  "restID": "4878",
  "status": "open",
  "message": "Restaurant is open"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `401 Unauthorized` - Invalid authentication

---

### 10. Update Restaurant Status

Update restaurant operational status.

**Endpoint:** `POST /api/restaurants/update-status`

**Request Body:**
```json
{
  "restID": "4878",
  "status": "open"
}
```

**Valid Status Values:**
- `open` - Restaurant is open
- `closed` - Restaurant is closed

**Response:**
```json
{
  "success": true,
  "message": "Restaurant status updated",
  "restID": "4878",
  "status": "open"
}
```

**Status Codes:**
- `200 OK` - Updated successfully
- `400 Bad Request` - Invalid status value
- `404 Not Found` - Restaurant not found
- `401 Unauthorized` - Invalid authentication

---

## Menu Endpoints

### 1. Get Menu Items

Get menu items for a restaurant.

**Endpoint:** `GET /api/menu/{restaurant_id}/items`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Query Parameters:**
- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records (default: 100, max: 500)

**Example:**
```
GET /api/menu/4878/items?skip=0&limit=100
```

**Response:**
```json
{
  "restaurant_id": "4878",
  "items": [
    {
      "id": 1,
      "item_id": "7765862",
      "item_name": "Garlic Bread",
      "price": 140.00,
      "category_id": "123",
      "category_name": "Starters",
      "is_available": true,
      "variations": [],
      "addons": []
    }
  ],
  "total": 150,
  "skip": 0,
  "limit": 100
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `401 Unauthorized` - Invalid authentication

---

### 2. Sync Menu from PetPooja

Sync menu data from PetPooja API.

**Endpoint:** `POST /api/menu/{restaurant_id}/sync`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Response:**
```json
{
  "success": true,
  "message": "Menu synced successfully",
  "restaurant_id": "4878",
  "categories_synced": 10,
  "items_synced": 150,
  "variations_synced": 50,
  "addons_synced": 30,
  "taxes_synced": 4,
  "sync_timestamp": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `500 Internal Server Error` - Sync error
- `401 Unauthorized` - Invalid authentication

---

### 3. Get Menu Categories

Get menu categories for a restaurant.

**Endpoint:** `GET /api/menu/{restaurant_id}/categories`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID

**Response:**
```json
{
  "restaurant_id": "4878",
  "categories": [
    {
      "category_id": "123",
      "name": "Starters",
      "rank": 1,
      "item_count": 15
    },
    {
      "category_id": "124",
      "name": "Main Course",
      "rank": 2,
      "item_count": 50
    }
  ],
  "total": 10
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Restaurant not found
- `401 Unauthorized` - Invalid authentication

---

### 4. Update Item Availability

Update menu item availability status.

**Endpoint:** `PUT /api/menu/{restaurant_id}/items/{item_id}/availability`

**Path Parameters:**
- `restaurant_id` (required): Restaurant ID
- `item_id` (required): Item ID

**Request Body:**
```json
{
  "is_available": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Item availability updated",
  "item_id": "7765862",
  "is_available": false
}
```

**Status Codes:**
- `200 OK` - Updated successfully
- `404 Not Found` - Item or restaurant not found
- `401 Unauthorized` - Invalid authentication

---

### 5. Get Sync Logs

Get menu synchronization history.

**Endpoint:** `GET /api/menu/sync-logs`

**Query Parameters:**
- `restaurant_id` (optional): Filter by restaurant
- `limit` (optional): Number of records (default: 50)

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "restaurant_id": "4878",
      "sync_type": "menu",
      "status": "success",
      "items_synced": 150,
      "synced_at": "2025-11-14T10:00:00Z"
    }
  ],
  "total": 10
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid authentication

---

### 6. Disable Menu Item

Disable a menu item in PetPooja.

**Endpoint:** `POST /api/menu/item/disable`

**Request Body:**
```json
{
  "restID": "4878",
  "itemID": "7765862"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Item disabled successfully",
  "restID": "4878",
  "itemID": "7765862"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `500 Internal Server Error` - PetPooja API error
- `401 Unauthorized` - Invalid authentication

---

### 7. Enable Menu Item

Enable a menu item in PetPooja.

**Endpoint:** `POST /api/menu/item/enable`

**Request Body:**
```json
{
  "restID": "4878",
  "itemID": "7765862"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Item enabled successfully",
  "restID": "4878",
  "itemID": "7765862"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid input
- `500 Internal Server Error` - PetPooja API error
- `401 Unauthorized` - Invalid authentication

---

## Order Endpoints

### 1. Place Order

Place a new order to PetPooja POS.

**Endpoint:** `POST /api/orders/place_order`

**Request Body:**
```json
{
  "order_id": "A24_20251113113131",
  "restaurant_id": "4878",
  "mapping_code": "czw6b9ykas",
  "restaurant_name": "Test Restaurant",
  "customer": {
    "name": "John Doe",
    "phone": "9999999999",
    "email": "john@example.com",
    "address": "123 Main St, City",
    "latitude": "12.9716",
    "longitude": "77.5946"
  },
  "order": {
    "order_id": "A24_20251113113131",
    "order_type": "delivery",
    "order_date_time": "2025-11-14T10:00:00"
  },
  "payment": {
    "payment_method": "cod",
    "delivery_charge": 50.0,
    "delivery_tax_percentage": 5.0,
    "packing_charge": 20.0,
    "packing_tax_percentage": 5.0,
    "service_charge": 0.0
  },
  "items": [
    {
      "item_id": "7765862",
      "item_name": "Garlic Bread",
      "item_price": 140.0,
      "final_price": 126.0,
      "item_quantity": 1,
      "item_discount": "14 [F]",
      "variation_id": "89058",
      "variation_name": "3 Pieces",
      "gst_liability": "vendor",
      "tax_inclusive": true,
      "special_instructions": "Extra crispy",
      "item_tax": [
        {
          "tax_id": "11213",
          "tax_name": "CGST",
          "tax_percentage": 2.5,
          "tax_amount": 3.15
        }
      ],
      "addons": []
    }
  ],
  "taxes": [
    {
      "id": "11213",
      "title": "CGST",
      "tax_rate": 2.5,
      "tax_amount": 5.9,
      "restaurant_liable_amt": 0.0
    }
  ],
  "discounts": [
    {
      "discount_type": "fixed",
      "discount_value": 45.0
    }
  ],
  "tax_total": 65.52,
  "total_amount": 560.0,
  "urgent_order": false,
  "urgent_time": 20,
  "otp_for_pickup": "9876",
  "order_instructions": "Handle with care"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Order placed successfully to PetPooja",
  "order_id": "A24_20251113113131",
  "petpooja_order_id": null,
  "order_status": "pending"
}
```

**Status Codes:**
- `200 OK` - Order placed successfully
- `400 Bad Request` - Invalid order data
- `500 Internal Server Error` - PetPooja API error
- `401 Unauthorized` - Invalid authentication

---

### 2. Get Order by ID

Get details of a specific order.

**Endpoint:** `GET /api/orders/{order_id}`

**Path Parameters:**
- `order_id` (required): Order ID

**Response:**
```json
{
  "order_id": "A24_20251113113131",
  "petpooja_order_id": null,
  "restaurant_id": "4878",
  "branch_id": "1",
  "customer": {
    "name": "John Doe",
    "phone": "9999999999",
    "email": "john@example.com",
    "address": "123 Main St, City"
  },
  "status": "pending",
  "payment_status": "pending",
  "payment_method": "cod",
  "order_type": "delivery",
  "subtotal": 495.0,
  "tax_amount": 65.52,
  "discount_amount": 45.0,
  "delivery_charge": 50.0,
  "total_amount": 560.0,
  "order_items": [...],
  "synced_to_petpooja": true,
  "synced_at": "2025-11-14T10:00:00Z",
  "created_at": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Order not found
- `401 Unauthorized` - Invalid authentication

---

### 3. List Orders

Get list of orders with optional filters.

**Endpoint:** `GET /api/orders`

**Query Parameters:**
- `restaurant_id` (optional): Filter by restaurant
- `branch_id` (optional): Filter by branch
- `status` (optional): Filter by status
- `payment_status` (optional): Filter by payment status
- `synced_only` (optional): Filter synced orders only (true/false)
- `limit` (optional): Number of records (default: 50, max: 100)
- `offset` (optional): Offset for pagination (default: 0)

**Example:**
```
GET /api/orders?restaurant_id=4878&status=pending&limit=50
```

**Response:**
```json
{
  "orders": [
    {
      "order_id": "A24_20251113113131",
      "petpooja_order_id": null,
      "restaurant_id": "4878",
      "customer_name": "John Doe",
      "status": "pending",
      "payment_status": "pending",
      "total_amount": 560.0,
      "synced_to_petpooja": true,
      "created_at": "2025-11-14T10:00:00Z"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

**Status Codes:**
- `200 OK` - Success
- `401 Unauthorized` - Invalid authentication

---

### 4. Update Order Status

Update order status manually.

**Endpoint:** `PUT /api/orders/{order_id}/status`

**Path Parameters:**
- `order_id` (required): Order ID

**Request Body:**
```json
{
  "status": "confirmed",
  "note": "Order confirmed by restaurant"
}
```

**Valid Status Values:**
- `pending` - Order placed, awaiting confirmation
- `confirmed` - Restaurant confirmed
- `preparing` - Being prepared
- `ready` - Ready for pickup/delivery
- `dispatched` - Out for delivery
- `delivered` - Successfully delivered
- `cancelled` - Order cancelled
- `rejected` - Order rejected by restaurant

**Response:**
```json
{
  "success": true,
  "message": "Order status updated successfully",
  "order_id": "A24_20251113113131",
  "previous_status": "pending",
  "new_status": "confirmed"
}
```

**Status Codes:**
- `200 OK` - Updated successfully
- `404 Not Found` - Order not found
- `400 Bad Request` - Invalid status value
- `401 Unauthorized` - Invalid authentication

---

### 5. Retry Failed Order

Retry syncing a failed order to PetPooja.

**Endpoint:** `POST /api/orders/{order_id}/retry`

**Path Parameters:**
- `order_id` (required): Order ID

**Response:**
```json
{
  "success": true,
  "message": "Order synced successfully",
  "order_id": "A24_20251113113131",
  "petpooja_order_id": null
}
```

**Status Codes:**
- `200 OK` - Synced successfully
- `404 Not Found` - Order not found
- `400 Bad Request` - Order already synced
- `500 Internal Server Error` - Sync failed
- `401 Unauthorized` - Invalid authentication

---

## Webhook Endpoints

Webhook endpoints are called by PetPooja to send status updates. These endpoints do **not** require Bearer token authentication.

### 1. Order Status Update

Receive order status updates from PetPooja.

**Endpoint:** `POST /api/webhooks/petpooja/order-status`

**Authentication:** Not required (or optional signature verification)

**Request Body:**
```json
{
  "orderID": "A24_20251113113131",
  "petpooja_order_id": "PP123456",
  "status": "accepted",
  "status_code": 2,
  "message": "Order accepted by restaurant",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Webhook processed successfully"
}
```

**Status Codes:**
- `200 OK` - Webhook processed
- `400 Bad Request` - Invalid payload
- `404 Not Found` - Order not found

---

### 2. Delivery Status Update

Receive delivery status updates from PetPooja.

**Endpoint:** `POST /api/webhooks/petpooja/delivery-status`

**Request Body:**
```json
{
  "orderID": "A24_20251113113131",
  "rider_name": "John Rider",
  "rider_phone": "9876543210",
  "status": "dispatched",
  "status_code": 4,
  "message": "Order dispatched with rider",
  "timestamp": "2025-11-14T10:30:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Delivery status updated"
}
```

**Status Codes:**
- `200 OK` - Webhook processed
- `400 Bad Request` - Invalid payload
- `404 Not Found` - Order not found

---

### 3. Order Cancellation

Receive order cancellation notifications from PetPooja.

**Endpoint:** `POST /api/webhooks/petpooja/order-cancellation`

**Request Body:**
```json
{
  "orderID": "A24_20251113113131",
  "petpooja_order_id": "PP123456",
  "cancellation_reason": "Out of stock",
  "cancelled_by": "restaurant",
  "timestamp": "2025-11-14T10:15:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Order cancellation processed"
}
```

**Status Codes:**
- `200 OK` - Webhook processed
- `400 Bad Request` - Invalid payload
- `404 Not Found` - Order not found

---

### 4. Menu Push Webhook

Receive menu updates from PetPooja.

**Endpoint:** `POST /api/webhooks/petpooja/pushmenu`

**Request Body:**
```json
{
  "restID": "4878",
  "data": {
    "restaurant": {...},
    "categories": [...],
    "items": [...]
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Menu data received and processed"
}
```

**Status Codes:**
- `200 OK` - Webhook processed
- `400 Bad Request` - Invalid payload

---

### 5. Test Webhook

Test webhook connectivity.

**Endpoint:** `GET /api/webhooks/petpooja/test`

**Authentication:** Not required

**Response:**
```json
{
  "success": true,
  "message": "Webhook endpoint is working",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

**Status Codes:**
- `200 OK` - Webhook working

---

## Response Codes

### Success Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully

### Client Error Codes

- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Missing or invalid authentication
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource already exists
- `422 Unprocessable Entity` - Validation error

### Server Error Codes

- `500 Internal Server Error` - Server error
- `502 Bad Gateway` - Upstream service error
- `503 Service Unavailable` - Service temporarily unavailable
- `504 Gateway Timeout` - Upstream service timeout

---

## Error Handling

### Error Response Format

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "error_code": "ERR_001",
  "timestamp": "2025-11-14T10:00:00Z"
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `ERR_001` | Invalid authentication token |
| `ERR_002` | Resource not found |
| `ERR_003` | Validation error |
| `ERR_004` | PetPooja API error |
| `ERR_005` | Database error |
| `ERR_006` | External service error |

### Example Error Responses

**401 Unauthorized:**
```json
{
  "detail": "Invalid or missing authentication token"
}
```

**400 Bad Request:**
```json
{
  "detail": "Validation error: order_id is required"
}
```

**404 Not Found:**
```json
{
  "detail": "Restaurant with ID 9999 not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error occurred. Please try again later."
}
```

---

## Rate Limiting

All endpoints are subject to rate limiting:

**Limits:**
- Sandbox: 100 requests per minute
- Production: 60 requests per minute

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1699977600
```

**Rate Limit Exceeded Response:**
```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

**Status Code:** `429 Too Many Requests`

---

## Postman Collection

Import the Postman collection for easy API testing:

**File:** `A24_PetPooja_API.postman_collection.json`

**Steps:**
1. Open Postman
2. Click Import
3. Select the collection file
4. Update environment variables:
   - `base_url`: Your API base URL
   - `MAIN_BACKEND_API_TOKEN`: Your authentication token
   - `restaurant_id`: Your restaurant ID

---

## Support

For API support:
- Email: support@a24.com
- Documentation: `documents/SYSTEM_FLOW.md`
- Sandbox Setup: `documents/SANDBOX_SETUP.md`
- Production Setup: `documents/PRODUCTION_SETUP.md`
