# Order API Documentation

## POST /api/orders/save

Submit a new order to the system. The order will be validated, stored in the database, and pushed to PetPooja.

### Endpoint
```
POST /api/orders/save
```

### Request Headers
```
Content-Type: application/json
```

### Request Body Schema

```json
{
  "restaurant_id": "uuid",                    // Required: Internal restaurant UUID
  "order_type": "string",                     // Required: "delivery" | "pickup" | "dine_in"
  "payment_type": "string",                   // Required: "cod" | "prepaid" | "card"
  "customer": {
    "name": "string",                         // Required
    "phone": "string",                        // Required
    "email": "string",                        // Optional
    "address": "string",                      // Required for delivery
    "latitude": "number",                     // Optional
    "longitude": "number"                     // Optional
  },
  "items": [
    {
      "menu_item_id": "uuid",                 // Required: From your menu_item table
      "quantity": "number",                   // Required
      "variation_id": "uuid",                 // Optional: If item has variations
      "price": "number",                      // Required: Base price
      "special_instructions": "string",       // Optional
      "addons": [                             // Optional
        {
          "addon_id": "uuid",                 // Required
          "addon_group_id": "uuid",           // Required
          "quantity": "number",               // Required
          "price": "number"                   // Required
        }
      ]
    }
  ],
  "charges": {
    "delivery_charges": "number",             // Default: 0
    "packing_charges": "number",              // Default: 0
    "service_charge": "number",               // Default: 0
    "platform_fee": "number",                 // Default: 0
    "convenience_fee": "number",              // Default: 0
    "tip_amount": "number"                    // Default: 0
  },
  "taxes": [                                  // Auto-calculated or provided
    {
      "tax_id": "uuid",                       // From your taxes table
      "tax_name": "string",
      "tax_percentage": "number",
      "tax_amount": "number"
    }
  ],
  "discounts": [                              // Optional
    {
      "discount_id": "uuid",                  // Optional: From your discount table
      "discount_code": "string",              // Optional
      "discount_amount": "number",            // Required
      "discount_type": "fixed" | "percentage" // Required
    }
  ],
  "delivery_info": {                          // Required if order_type = "delivery"
    "delivery_address_id": "uuid",            // Optional: If using saved address
    "enable_delivery": "boolean",             // Default: true
    "delivery_slot": "string",                // Optional: "YYYY-MM-DD HH:MM:SS"
    "delivery_otp": "string"                  // Optional
  },
  "dining_info": {                            // Required if order_type = "dine_in"
    "table_no": "number",
    "no_of_persons": "number"
  },
  "scheduling": {                             // Optional: For advance orders
    "is_advanced_order": "boolean",           // Default: false
    "preorder_date": "string",                // Format: "YYYY-MM-DD"
    "preorder_time": "string",                // Format: "HH:MM:SS"
    "is_urgent": "boolean",                   // Default: false
    "min_prep_time": "number"                 // Minutes, default: 20
  },
  "notes": {
    "special_instructions": "string",
    "kitchen_notes": "string",
    "delivery_notes": "string"
  },
  "callback_url": "string"                    // Optional: For order status updates
}
```

### Example Request

```json
{
  "restaurant_id": "550e8400-e29b-41d4-a716-446655440000",
  "order_type": "delivery",
  "payment_type": "cod",
  "customer": {
    "name": "John Doe",
    "phone": "9876543210",
    "email": "john@example.com",
    "address": "123 Main Street, Mumbai",
    "latitude": 19.0760,
    "longitude": 72.8777
  },
  "items": [
    {
      "menu_item_id": "660e8400-e29b-41d4-a716-446655440001",
      "quantity": 2,
      "price": 250.00,
      "special_instructions": "Extra spicy",
      "addons": [
        {
          "addon_id": "770e8400-e29b-41d4-a716-446655440002",
          "addon_group_id": "880e8400-e29b-41d4-a716-446655440003",
          "quantity": 1,
          "price": 20.00
        }
      ]
    },
    {
      "menu_item_id": "660e8400-e29b-41d4-a716-446655440004",
      "quantity": 1,
      "variation_id": "770e8400-e29b-41d4-a716-446655440005",
      "price": 150.00,
      "addons": []
    }
  ],
  "charges": {
    "delivery_charges": 40.00,
    "packing_charges": 10.00,
    "service_charge": 0,
    "platform_fee": 5.00,
    "convenience_fee": 0,
    "tip_amount": 20.00
  },
  "taxes": [
    {
      "tax_id": "990e8400-e29b-41d4-a716-446655440006",
      "tax_name": "CGST",
      "tax_percentage": 2.5,
      "tax_amount": 16.25
    },
    {
      "tax_id": "990e8400-e29b-41d4-a716-446655440007",
      "tax_name": "SGST",
      "tax_percentage": 2.5,
      "tax_amount": 16.25
    }
  ],
  "discounts": [
    {
      "discount_code": "FIRST50",
      "discount_amount": 50.00,
      "discount_type": "fixed"
    }
  ],
  "delivery_info": {
    "enable_delivery": true,
    "delivery_otp": "1234"
  },
  "scheduling": {
    "is_advanced_order": false,
    "is_urgent": false,
    "min_prep_time": 30
  },
  "notes": {
    "special_instructions": "Ring the bell twice",
    "kitchen_notes": "Customer prefers less oil",
    "delivery_notes": "Leave at the door"
  },
  "callback_url": "https://your-app.com/webhooks/order-status"
}
```

### Response

#### Success Response (200 OK)
```json
{
  "success": true,
  "message": "Order created and sent to PetPooja successfully",
  "data": {
    "order_id": "aa0e8400-e29b-41d4-a716-446655440008",
    "external_order_id": "A24-ORD-20250101-001",
    "petpooja_sync_status": "success",
    "total_amount": 657.50,
    "created_at": "2025-01-01T10:30:00Z"
  }
}
```

#### Error Response (400 Bad Request)
```json
{
  "success": false,
  "message": "Invalid order data",
  "errors": {
    "customer.phone": "Phone number is required",
    "items": "At least one item is required"
  }
}
```

### Order Flow

1. **Client → Our API**: Client sends order using our schema
2. **Validation**: We validate the order data
3. **Database Storage**: We store order in our normalized tables
4. **Transform**: We convert our schema to PetPooja format
5. **Push to PetPooja**: We call PetPooja's save_order API
6. **Response**: We return success/failure to client

### Notes

- All monetary values should be numbers with 2 decimal places
- UUIDs must be valid v4 UUIDs
- Phone numbers should be 10 digits (Indian format)
- The `restaurant_id` should be from your `restaurant_table`
- Menu item IDs should exist in your `menu_item` table
- Tax IDs should exist in your `taxes` table
