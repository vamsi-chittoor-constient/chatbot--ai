# A24 Restaurant Data Pipeline - System Flow Documentation

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Data Flow](#data-flow)
4. [Restaurant Onboarding Flow](#restaurant-onboarding-flow)
5. [Menu Synchronization Flow](#menu-synchronization-flow)
6. [Order Placement Flow](#order-placement-flow)
7. [Webhook Processing Flow](#webhook-processing-flow)
8. [Authentication & Security](#authentication--security)
9. [Error Handling](#error-handling)
10. [Database Schema](#database-schema)

---

## System Overview

The A24 Restaurant Data Pipeline is a middleware service that integrates restaurant management systems with PetPooja POS. It handles:

- **Restaurant Management**: Onboarding restaurants and managing their PetPooja credentials
- **Menu Synchronization**: Fetching and syncing menu data from PetPooja
- **Order Management**: Placing orders to PetPooja POS and tracking their lifecycle
- **Webhook Handling**: Processing status updates from PetPooja
- **Data Persistence**: Storing all data in PostgreSQL database

### Key Components

```
┌─────────────────┐
│  Client Apps    │ (Mobile App, Web Dashboard, POS Systems)
└────────┬────────┘
         │ HTTPS
         │ Auth: Bearer Token
         ▼
┌─────────────────────────────────────────────────┐
│       A24 Restaurant Data Pipeline              │
│  ┌──────────────────────────────────────────┐  │
│  │         FastAPI Application              │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │  Routers (API Endpoints)           │  │  │
│  │  │  - Restaurant Router               │  │  │
│  │  │  - Menu Router                     │  │  │
│  │  │  - Order Router                    │  │  │
│  │  │  - Webhook Router                  │  │  │
│  │  └────────┬───────────────────────────┘  │  │
│  │           │                               │  │
│  │           ▼                               │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │  Service Layer                     │  │  │
│  │  │  - Order Service                   │  │  │
│  │  │  - Menu Sync Service               │  │  │
│  │  │  - Restaurant Service              │  │  │
│  │  └────────┬───────────────────────────┘  │  │
│  │           │                               │  │
│  │           ▼                               │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │  PetPooja Client                   │  │  │
│  │  │  - HTTP Client                     │  │  │
│  │  │  - AWS SigV4 Authentication        │  │  │
│  │  │  - Retry Logic                     │  │  │
│  │  └────────┬───────────────────────────┘  │  │
│  └───────────┼───────────────────────────────┘  │
│              │                                   │
│  ┌───────────┼───────────────────────────────┐  │
│  │           ▼                               │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │  PostgreSQL Database               │  │  │
│  │  │  - Restaurants                     │  │  │
│  │  │  - Menu Items                      │  │  │
│  │  │  - Orders                          │  │  │
│  │  │  - Sync Logs                       │  │  │
│  │  └────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┘
               │ HTTPS
               │ Auth: AWS SigV4 (Sandbox) or Standard (Production)
               ▼
┌─────────────────────────────────────────────────┐
│          PetPooja API                           │
│  - Save Order API                               │
│  - Get Restaurant Details                       │
│  - Push Menu API                                │
│  - Update Stock                                 │
└─────────────────────────────────────────────────┘
```

---

## Architecture

### Layered Architecture

#### 1. **Presentation Layer** (`app/routers/`)
- Handles HTTP requests and responses
- Input validation using Pydantic schemas
- Authentication and authorization
- Routes requests to service layer

#### 2. **Business Logic Layer** (`app/services/`)
- Order processing and conversion
- Menu synchronization logic
- Restaurant management
- Data transformation

#### 3. **Data Access Layer** (`app/models/`)
- SQLAlchemy ORM models
- Database operations
- Data persistence

#### 4. **Integration Layer** (`app/petpooja_client/`)
- External API communication
- HTTP client management
- Authentication handling
- Retry and error handling

#### 5. **Core Layer** (`app/core/`)
- Configuration management
- Database session handling
- Security utilities
- Logging setup

---

## Data Flow

### Complete Request-Response Cycle

```
1. Client Request
   │
   ├─> FastAPI receives request
   │   └─> Middleware processes (CORS, Auth, Rate Limiting)
   │
   ├─> Router validates request
   │   └─> Pydantic schemas validate data
   │
   ├─> Service layer processes business logic
   │   ├─> Transforms data
   │   ├─> Validates business rules
   │   └─> Calls PetPooja client if needed
   │
   ├─> PetPooja client makes external API call
   │   ├─> Signs request (AWS SigV4 for sandbox)
   │   ├─> Adds credentials
   │   ├─> Makes HTTP request
   │   └─> Handles retries on failure
   │
   ├─> Database operations
   │   ├─> Save data
   │   ├─> Update status
   │   └─> Log transaction
   │
   └─> Response sent back to client
       └─> JSON formatted response
```

---

## Restaurant Onboarding Flow

### Step-by-Step Process

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/restaurants/onboard
       │ {
       │   "restaurant_name": "Test Restaurant",
       │   "email": "test@example.com",
       │   "phone_no": "1234567890",
       │   "vendor_restaurant_id": "34467",
       │   "app_key": "xxx",
       │   "app_secret": "xxx",
       │   "access_token": "xxx",
       │   "sandbox_enabled": true
       │ }
       ▼
┌──────────────────────────┐
│  Restaurant Router       │
│  /api/restaurants/       │
└──────┬───────────────────┘
       │ 1. Validate input data
       │ 2. Check authentication
       ▼
┌──────────────────────────┐
│  Database Check          │
│  Check if restaurant     │
│  already exists          │
└──────┬───────────────────┘
       │ If exists → Return error
       │ If not exists → Continue
       ▼
┌──────────────────────────┐
│  Create Restaurant       │
│  1. Insert restaurant    │
│  2. Insert credentials   │
│  3. Commit transaction   │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Fetch from PetPooja     │
│  1. Call PetPooja API    │
│  2. Get restaurant data  │
│  3. Update local record  │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Sync Menu (Optional)    │
│  1. Fetch menu data      │
│  2. Store in database    │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│  Return Response         │
│  {                       │
│    "success": true,      │
│    "restaurant_id": "X", │
│    "message": "..."      │
│  }                       │
└──────────────────────────┘
```

### Database Changes

1. **restaurants** table: New record created
2. **restaurant_petpooja_credentials** table: Credentials stored
3. **restaurant_branches** table: Branches added
4. **petpooja_sync_logs** table: Sync event logged

---

## Menu Synchronization Flow

### Complete Menu Sync Process

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ POST /api/menu/{restaurant_id}/sync
       ▼
┌──────────────────────────────────────────┐
│  Menu Sync Service                       │
│  1. Validate restaurant exists           │
│  2. Get PetPooja credentials             │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Fetch Menu from PetPooja               │
│  GET /getrestaurantdetails              │
│  Response contains:                      │
│  - Categories                            │
│  - Items                                 │
│  - Variations                            │
│  - Addons                                │
│  - Taxes                                 │
│  - Discounts                             │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Transform Data                          │
│  Convert PetPooja format to internal     │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Database Transaction                    │
│  BEGIN TRANSACTION                       │
│  ├─> Delete old categories              │
│  ├─> Delete old items                   │
│  ├─> Insert new categories              │
│  ├─> Insert new items                   │
│  ├─> Insert variations                  │
│  ├─> Insert addons                      │
│  ├─> Insert taxes                       │
│  ├─> Log sync event                     │
│  └─> COMMIT                              │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Return Response                         │
│  {                                       │
│    "success": true,                      │
│    "categories_synced": 10,              │
│    "items_synced": 150,                  │
│    "sync_timestamp": "..."               │
│  }                                       │
└──────────────────────────────────────────┘
```

### Data Mapping

**PetPooja Format → Internal Format**

```
PetPooja Category
{
  "categoryID": "123",
  "categoryname": "Main Course",
  "categoryrank": "1"
}
↓
Internal Format
{
  "category_id": "123",
  "name": "Main Course",
  "rank": 1,
  "restaurant_id": "4878"
}
```

---

## Order Placement Flow

### Detailed Order Flow

```
┌─────────────┐
│   Client    │
│  (Your App) │
└──────┬──────┘
       │ POST /api/orders/place_order
       │ {
       │   "order_id": "A24_20251113113131",
       │   "restaurant_id": "4878",
       │   "customer": { ... },
       │   "items": [ ... ],
       │   "payment": { ... },
       │   "total_amount": 560.00
       │ }
       ▼
┌──────────────────────────────────────────┐
│  Step 1: Validate Request                │
│  - Check order_id is unique              │
│  - Validate customer data                │
│  - Validate items exist                  │
│  - Check required fields                 │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 2: Convert to PetPooja Format      │
│  Order Service converts:                 │
│  ┌────────────────────────────────────┐  │
│  │ Your Format → PetPooja Format      │  │
│  │                                    │  │
│  │ customer.name → name               │  │
│  │ order.order_type → H/P/D           │  │
│  │ payment.payment_method → COD/CARD  │  │
│  │ items[] → OrderItem structure      │  │
│  │ taxes[] → Tax structure            │  │
│  └────────────────────────────────────┘  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 3: Save to Database (Pending)      │
│  INSERT INTO orders VALUES (             │
│    order_id,                             │
│    restaurant_id,                        │
│    customer_name,                        │
│    ...                                   │
│    status='pending',                     │
│    synced_to_petpooja=false              │
│  )                                       │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 4: Build PetPooja Payload          │
│  {                                       │
│    "app_key": "xxx",                     │
│    "app_secret": "xxx",                  │
│    "access_token": "xxx",                │
│    "orderinfo": {                        │
│      "OrderInfo": {                      │
│        "Restaurant": { ... },            │
│        "Customer": { ... },              │
│        "Order": { ... },                 │
│        "OrderItem": { ... },             │
│        "Tax": { ... }                    │
│      }                                   │
│    }                                     │
│  }                                       │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 5: Submit to PetPooja              │
│  PetPooja Client:                        │
│  ┌────────────────────────────────────┐  │
│  │ If Sandbox:                        │  │
│  │   1. Sign with AWS SigV4           │  │
│  │   2. Add Authorization header      │  │
│  │                                    │  │
│  │ If Production:                     │  │
│  │   1. Add credentials to body       │  │
│  │   2. Standard authentication       │  │
│  └────────────────────────────────────┘  │
│  POST /save_order                        │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 6: Process PetPooja Response       │
│  Response: {                             │
│    "success": "1",                       │
│    "message": "Order saved successfully" │
│  }                                       │
│  ┌────────────────────────────────────┐  │
│  │ Extract petpooja_order_id (if any) │  │
│  │ Parse success status               │  │
│  │ Handle errors                      │  │
│  └────────────────────────────────────┘  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 7: Update Database                 │
│  UPDATE orders SET                       │
│    synced_to_petpooja = true,            │
│    synced_at = now(),                    │
│    petpooja_order_id = (if provided),    │
│    sync_response = { ... },              │
│    sync_attempts = 1                     │
│  WHERE order_id = 'A24_...'              │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Step 8: Return Response to Client       │
│  {                                       │
│    "success": true,                      │
│    "message": "Order placed",            │
│    "order_id": "A24_20251113113131",     │
│    "petpooja_order_id": null,            │
│    "order_status": "pending"             │
│  }                                       │
└──────────────────────────────────────────┘
```

### Order Status Lifecycle

```
┌─────────┐
│ Pending │ ← Order placed, waiting for PetPooja confirmation
└────┬────┘
     │ Webhook from PetPooja
     ▼
┌───────────┐
│ Confirmed │ ← Restaurant confirmed the order
└────┬──────┘
     │
     ▼
┌───────────┐
│ Preparing │ ← Restaurant is preparing the order
└────┬──────┘
     │
     ▼
┌────────┐
│ Ready  │ ← Order ready for pickup/delivery
└────┬───┘
     │
     ▼
┌────────────┐
│ Dispatched │ ← Order dispatched (delivery orders)
└────┬───────┘
     │
     ▼
┌───────────┐
│ Delivered │ ← Order successfully delivered
└───────────┘

Alternative flows:
┌───────────┐
│ Cancelled │ ← Order cancelled by customer/restaurant
└───────────┘

┌──────────┐
│ Rejected │ ← Order rejected by restaurant
└──────────┘
```

---

## Webhook Processing Flow

### Handling PetPooja Webhooks

```
┌─────────────────┐
│   PetPooja      │
│   Server        │
└────────┬────────┘
         │ POST /api/webhooks/petpooja/order-status
         │ {
         │   "orderID": "A24_20251113113131",
         │   "status": "accepted",
         │   "message": "Order accepted"
         │ }
         ▼
┌────────────────────────────────────────┐
│  Webhook Router                        │
│  1. Receive webhook                    │
│  2. Log raw payload                    │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Validate Signature (Optional)         │
│  Check X-Signature header              │
│  Verify HMAC signature                 │
└────────┬───────────────────────────────┘
         │ Valid ✓
         ▼
┌────────────────────────────────────────┐
│  Find Order in Database                │
│  SELECT * FROM orders                  │
│  WHERE order_id = 'A24_...'            │
└────────┬───────────────────────────────┘
         │ Found ✓
         ▼
┌────────────────────────────────────────┐
│  Update Order Status                   │
│  UPDATE orders SET                     │
│    status = 'accepted',                │
│    previous_status = 'pending',        │
│    status_updated_at = now(),          │
│    status_history = jsonb_append(...)  │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Store Webhook Log                     │
│  INSERT INTO webhook_logs VALUES (     │
│    order_id,                           │
│    webhook_type: 'order_status',       │
│    payload: { ... },                   │
│    processed_at: now()                 │
│  )                                     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Forward to Main Backend (Optional)    │
│  POST https://backend.domain.com/...   │
│  Notify main application of status     │
└────────┬───────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│  Return 200 OK to PetPooja            │
│  {                                     │
│    "success": true,                    │
│    "message": "Webhook processed"      │
│  }                                     │
└────────────────────────────────────────┘
```

### Webhook Types

1. **Order Status Update**
   - Endpoint: `/api/webhooks/petpooja/order-status`
   - Triggered when order status changes
   - Updates: order status, timestamps

2. **Delivery Status Update**
   - Endpoint: `/api/webhooks/petpooja/delivery-status`
   - Triggered when delivery status changes
   - Updates: delivery info, rider details

3. **Order Cancellation**
   - Endpoint: `/api/webhooks/petpooja/order-cancellation`
   - Triggered when order is cancelled
   - Updates: status, cancellation reason

4. **Menu Push**
   - Endpoint: `/api/webhooks/petpooja/pushmenu`
   - Triggered when menu is updated in PetPooja
   - Action: Sync menu data

---

## Authentication & Security

### Request Authentication

```
Client Request
│
├─> 1. Extract Authorization header
│   Bearer a24-backend-secure-token-2024
│
├─> 2. Verify token
│   if token == MAIN_BACKEND_API_TOKEN:
│     Allow request
│   else:
│     Return 401 Unauthorized
│
└─> 3. Process request
```

### PetPooja API Authentication

#### Sandbox (AWS SigV4)

```
1. Prepare request
   ├─> URL: https://...execute-api.ap-southeast-1.amazonaws.com/V1/save_order
   ├─> Method: POST
   ├─> Body: JSON payload
   └─> Headers: Content-Type: application/json

2. Create AWS signature
   ├─> Canonical request
   ├─> String to sign
   ├─> Calculate signature using AWS_SECRET_ACCESS_KEY
   └─> Add Authorization header with signature

3. Make request
   ├─> Send signed request
   └─> PetPooja validates signature
```

#### Production (Standard)

```
1. Prepare request
   ├─> URL: https://api-v2.petpooja.com/save_order
   ├─> Method: POST
   └─> Headers: Content-Type: application/json

2. Add credentials to body
   {
     "app_key": "xxx",
     "app_secret": "xxx",
     "access_token": "xxx",
     "orderinfo": { ... }
   }

3. Make request
   ├─> Send request with credentials in body
   └─> PetPooja validates credentials
```

### Security Layers

1. **Network Layer**
   - HTTPS/TLS encryption
   - Firewall rules
   - Rate limiting

2. **Application Layer**
   - Bearer token authentication
   - Input validation (Pydantic)
   - SQL injection prevention (ORM)
   - XSS prevention

3. **Data Layer**
   - Encrypted credentials in database
   - Database access controls
   - Audit logging

---

## Error Handling

### Error Flow

```
┌──────────────┐
│ Error Occurs │
└──────┬───────┘
       │
       ▼
┌──────────────────────────┐
│ Identify Error Type      │
│ - Validation Error       │
│ - API Error             │
│ - Database Error        │
│ - Network Error         │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Log Error Details        │
│ - Timestamp              │
│ - Error message         │
│ - Stack trace           │
│ - Context data          │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Handle Error             │
│ - Retry if transient     │
│ - Update status          │
│ - Notify user           │
└──────┬───────────────────┘
       │
       ▼
┌──────────────────────────┐
│ Return Error Response    │
│ {                        │
│   "success": false,      │
│   "error": "...",        │
│   "code": "ERR_001"      │
│ }                        │
└──────────────────────────┘
```

### Retry Logic

For transient errors (network timeout, 5xx errors):

```
Attempt 1
│ Wait 2 seconds
▼
Attempt 2
│ Wait 4 seconds
▼
Attempt 3
│ Wait 8 seconds
▼
Give up, return error
```

---

## Database Schema

### Core Tables

#### 1. **restaurants**
```
id (PK)
restaurant_name
email
phone_no
status
created_at
updated_at
```

#### 2. **restaurant_petpooja_credentials**
```
id (PK)
restaurant_id (FK)
vendor_restaurant_id
app_key
app_secret
access_token
sandbox_enabled
is_active
created_at
updated_at
```

#### 3. **orders**
```
id (PK)
order_id (unique)
petpooja_order_id
restaurant_id
customer_name
customer_phone
customer_email
order_type
subtotal
tax_amount
total_amount
status
synced_to_petpooja
synced_at
sync_response (JSONB)
order_items (JSONB)
created_at
updated_at
```

#### 4. **restaurants_menu_items**
```
id (PK)
restaurant_id (FK)
item_id
item_name
price
category_id
is_available
variations (JSONB)
addons (JSONB)
created_at
updated_at
```

#### 5. **petpooja_sync_logs**
```
id (PK)
restaurant_id (FK)
sync_type
status
response (JSONB)
synced_at
```

### Relationships

```
restaurants (1) ←→ (Many) restaurant_petpooja_credentials
restaurants (1) ←→ (Many) orders
restaurants (1) ←→ (Many) restaurants_menu_items
restaurants (1) ←→ (Many) petpooja_sync_logs
```

---

## Summary

The A24 Restaurant Data Pipeline provides a robust, scalable solution for integrating restaurant systems with PetPooja POS. Key features include:

✅ **Multi-restaurant Support**: Manage multiple restaurants with separate credentials
✅ **Automatic Synchronization**: Keep menu data in sync with PetPooja
✅ **Real-time Order Processing**: Place orders to PetPooja in real-time
✅ **Webhook Handling**: Process status updates from PetPooja
✅ **Error Recovery**: Automatic retries and comprehensive error handling
✅ **Audit Trail**: Complete logging of all operations
✅ **Security**: Multiple layers of authentication and authorization
✅ **Scalability**: Designed to handle high volumes of orders

For detailed API documentation, refer to `API_REFERENCE.md`.
