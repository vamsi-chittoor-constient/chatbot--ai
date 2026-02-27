Payload Structure Analysis

  ISSUES FOUND in Current Implementation:

  | Field          | Correct Value                      | Current Issue                              |
  |----------------|------------------------------------|--------------------------------------------|
  | advanced_order | "N" or "Y" (string)                | Sending 0 or 1 (integer)                   |
  | udid           | Root level                         | Inside orderinfo                           |
  | device_type    | Root level                         | Inside orderinfo                           |
  | OrderItem.id   | PetPooja item ID (e.g., "ITEM001") | Sending ext_petpooja_item_id or empty      |
  | variation_id   | PetPooja variation ID              | Sending ext_petpooja_variation_id or empty |
  | addon.group_id | Integer (1001)                     | Sending string                             |
  | mapping_code   | NOT needed in Restaurant.details   | Being sent                                 |

  ---
  Field Source Mapping

  From Database:

  ├── app_key, app_secret, access_token  → integration_credentials_table
  ├── restID                             → branch_info_table.ext_petpooja_restaurant_id
  ├── Restaurant
  │   ├── res_name                       → branch_info_table.branch_name
  │   ├── address                        → branch_location_table
  │   └── contact_information            → branch_contact_table
  ├── Customer
  │   ├── name                           → customer_profile_table
  │   ├── phone                          → customer_contact_table (type=phone)
  │   ├── email                          → customer_contact_table (type=email)
  │   ├── address                        → customer_address_table
  │   ├── latitude                       → customer_address_table.customer_latitude
  │   └── longitude                      → customer_address_table.customer_longitude
  ├── Order
  │   ├── orderID                        → orders.order_external_reference_id
  │   ├── delivery_charges               → order_charges_table (type=delivery)
  │   ├── packing_charges                → order_charges_table (type=packing)
  │   ├── service_charge                 → order_charges_table (type=service)
  │   ├── discount_total                 → order_total_table.discount_total
  │   ├── tax_total                      → order_total_table.tax_total
  │   ├── total                          → order_total_table.final_amount
  │   ├── description                    → order_instruction_table.special_instructions
  │   ├── table_no                       → order_dining_info_table.table_no
  │   ├── no_of_persons                  → order_dining_info_table.no_of_persons
  │   ├── preorder_date                  → order_scheduling_table.preorder_date
  │   ├── preorder_time                  → order_scheduling_table.preorder_time
  │   └── otp                            → order_delivery_info_table.delivery_otp
  ├── OrderItem[]
  │   ├── id                             → menu_item_table.ext_petpooja_item_id ⚠️
  │   ├── name                           → menu_item_table.menu_item_name
  │   ├── price                          → order_item_table.base_price
  │   ├── quantity                       → order_item_table.quantity (or 1 per row)
  │   ├── variation_id                   → menu_item_variation.ext_petpooja_variation_id ⚠️
  │   ├── variation_name                 → menu_item_variation.menu_item_variation_name
  │   └── description                    → order_item_table.cooking_instructions
  ├── Tax[]                              → order_tax_line_table
  └── Discount[]                         → order_discount_table

  Static/Hardcoded:

  ├── order_type                         → Mapped: "delivery"→"H", "pickup"→"P", "dine_in"→"D"
  ├── payment_type                       → Mapped: "cod"→"COD", "prepaid"→"PAID"
  ├── dc_tax_percentage                  → "0" (or calculate)
  ├── dc_tax_amount                      → "0" (or calculate)
  ├── dc_gst_details                     → [] (or build structure)
  ├── pc_tax_percentage                  → "0" (or calculate)
  ├── pc_tax_amount                      → "0" (or calculate)
  ├── pc_gst_details                     → [] (or build structure)
  ├── sc_tax_amount                      → "0"
  ├── discount_type                      → "F" (Fixed)
  ├── enable_delivery                    → 1 for delivery, 0 otherwise
  ├── min_prep_time                      → 20-25 (default)
  ├── urgent_order                       → false
  ├── urgent_time                        → 0 or 30
  ├── callback_url                       → Your webhook URL
  ├── collect_cash                       → "0" for prepaid, total for COD
  ├── ondc_bap                           → "" (empty)
  ├── tax_inclusive                      → true
  ├── gst_liability                      → "restaurant" or "vendor"
  ├── udid                               → Device identifier
  └── device_type                        → "Web"





log payload this is success :
2025-12-16 12:48:54,634 - app.petpooja_client.order_client - INFO - === FULL PETPOOJA REQUEST PAYLOAD ===
2025-12-16 12:48:54,634 - app.petpooja_client.order_client - INFO - URL: https://47pfzh5sf2.execute-api.ap-southeast-1.amazonaws.com/V1/save_order
2025-12-16 12:48:54,635 - app.petpooja_client.order_client - INFO - Headers: {'Content-Type': 'application/json'}
2025-12-16 12:48:54,635 - app.petpooja_client.order_client - INFO - FULL Payload (with creds): {
  "app_key": "3b9pon1v6jgdhar7fxkmi8c0t54yewsz",
  "app_secret": "e6ce04ec5ce5f9e166f42c486d12c23c06c3af2b",
  "access_token": "7520a7d6cebbe30362b2bc0feca78c2d430a589f",
  "orderinfo": {
    "OrderInfo": {
      "Restaurant": {
        "details": {
          "res_name": "Aswins sweets[34467]",
          "address": "",
          "contact_information": "",
          "restID": "czw6b9ykas"
        }
      },
      "Customer": {
        "details": {
          "name": "Customer",
          "phone": "+916380767664",
          "email": "NOT SET",
          "address": "",
          "latitude": "",
          "longitude": ""
        }
      },
      "Order": {
        "details": {
          "orderID": "ORD-PGDRXHAK",
          "preorder_date": "2025-12-16",
          "preorder_time": "07:48:54",
          "advanced_order": "N",
          "order_type": "H",
          "ondc_bap": "",
          "payment_type": "COD",
          "delivery_charges": "0.00",
          "dc_tax_percentage": "0",
          "dc_tax_amount": "0",
          "dc_gst_details": [],
          "packing_charges": "0.00",
          "pc_tax_percentage": "0",
          "pc_tax_amount": "0",
          "pc_gst_details": [],
          "service_charge": "0.00",
          "sc_tax_amount": "0",
          "discount_total": "0.00",
          "discount_type": "F",
          "tax_total": "0.00",
          "total": "147.00",
          "description": "",
          "created_on": "2025-12-16 07:18:54",
          "enable_delivery": 1,
          "callback_url": "",
          "urgent_order": false,
          "urgent_time": 30,
          "table_no": "",
          "no_of_persons": "0",
          "min_prep_time": 20,
          "collect_cash": "147.00",
          "otp": ""
        }
      },
      "OrderItem": {
        "details": [
          {
            "id": "10584293",
            "name": "Add Caramel",
            "price": "49.00",
            "final_price": "49.00",
            "quantity": "1",
            "tax_inclusive": true,
            "gst_liability": "vendor",
            "item_tax": [],
            "item_discount": "",
            "variation_id": "",
            "variation_name": "",
            "description": "",
            "AddonItem": {
              "details": []
            }
          }
        ]
      },
      "Tax": {
        "details": []
      },
      "Discount": {
        "details": []
      }
    }
  },
  "udid": "a24-pipeline",
  "device_type": "Web"
}