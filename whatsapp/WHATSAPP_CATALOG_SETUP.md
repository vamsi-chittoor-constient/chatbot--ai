# WhatsApp Catalog Setup for A24 Food Ordering

## Overview
WhatsApp Commerce Catalog provides a native in-app experience for food ordering.
Customers browse the menu, add items to cart, and send orders — all within WhatsApp.

## Account Details
- **WABA ID:** 186831081184964
- **Phone Number ID:** 638297072702167
- **Business ID:** 368584742318268 (Constient Global Solutions Pvt Ltd)
- **Meta App ID:** 1554922978624080
- **Catalog ID:** 1585007629445142 (A24 Restaurant Menu)
- **System User:** assist24 (ID: 61576162946114)
- **API Version:** v25.0
- **Messaging Tier:** TIER_250 (250 business-initiated conversations/24h)

## Setup Steps Completed

### 1. Catalog Created (via Commerce Manager UI)
- URL: https://business.facebook.com/commerce/catalogs/1585007629445142/home/
- Type: Online products
- Name: A24 Restaurant Menu
- Business: Constient Global Solutions Pvt Ltd
- Event tracking: Connected (Constient pixel)

### 2. Catalog Linked to WhatsApp Phone Number
```bash
POST /v25.0/638297072702167/whatsapp_commerce_settings
{"catalog_id": "1585007629445142", "is_catalog_visible": true}
# Response: {"success": true}
# Verify: is_cart_enabled: true, is_catalog_visible: true, id: 869847242756485
```

### 3. Catalog Linked to WABA
- Phone number commerce settings alone was NOT enough
- Also needed: `POST /v25.0/186831081184964/product_catalogs` with `{"catalog_id": "1585007629445142"}`
- Response: `{"success": true}`
- Both links required for WhatsApp product messages to work
- Commerce settings ID (869847242756485) is different from catalog ID (1585007629445142)

### 4. Webhook Configuration
- Callback URL: https://noninflectionally-ultramicrochemical-reece.ngrok-free.dev/api/whatsapp/webhook
- Subscribed fields: `messages` (includes order messages)
- API version: v25.0 (upgraded from v19.0)

### 5. Menu Data Queried from Database
- 96 total menu items in DB, **67 with price > 0** (valid for catalog)
- No images available (`menu_item_image_url` is null for all items)
- No parent categories linked (`menu_category_name` is null)
- Sub-categories available: Beverages, Hot Coffees, Chicken Meal, Side Orders, Add Ons, Chicken, etc.
- Attributes: veg (346aafb1), non-veg (5b087580), egg (e6ee4807)
- Price range: ₹19 (Bun, Bisleri) to ₹319 (Chicken Fillet Nugget Snack)

**Working query:**
```sql
SELECT mi.menu_item_id, mi.menu_item_name, mi.menu_item_price,
       mi.menu_item_description, mi.menu_item_image_url,
       mi.menu_item_attribute_id, msc.sub_category_name
FROM menu_item mi
LEFT JOIN menu_sub_categories msc ON mi.menu_sub_category_id = msc.menu_sub_category_id
WHERE mi.is_deleted = false AND mi.menu_item_in_stock = true AND mi.menu_item_price > 0
ORDER BY msc.sub_category_name, mi.menu_item_name
```

**Join path:** menu_item.menu_sub_category_id → menu_sub_categories.menu_sub_category_id
                menu_sub_categories.category_id → menu_categories.menu_category_id (parent categories are null)

**Export command (run on server):**
```bash
sudo docker exec a24-chatbot-app python -c "
import asyncio, json
async def export():
    import asyncpg
    conn = await asyncpg.connect('postgresql://admin:admin123@postgres:5432/restaurant_ai')
    rows = await conn.fetch('''
        SELECT mi.menu_item_id, mi.menu_item_name, mi.menu_item_price,
               mi.menu_item_description, mi.menu_item_image_url, msc.sub_category_name
        FROM menu_item mi
        LEFT JOIN menu_sub_categories msc ON mi.menu_sub_category_id = msc.menu_sub_category_id
        WHERE mi.is_deleted = false AND mi.menu_item_in_stock = true AND mi.menu_item_price > 0
        ORDER BY msc.sub_category_name, mi.menu_item_name
    ''')
    items = []
    for r in rows:
        items.append({
            'id': str(r['menu_item_id']),
            'name': r['menu_item_name'],
            'price': int(float(r['menu_item_price']) * 100),
            'description': r['menu_item_description'] or r['menu_item_name'],
            'category': r['sub_category_name'] or 'Other',
        })
    print(json.dumps(items))
    await conn.close()
asyncio.run(export())
" > /tmp/menu_items.json
```

### 6. System User Token Regenerated
- Old token only had: `whatsapp_business_messaging`, `whatsapp_business_management`, `business_management`, `public_profile`
- **New token** includes all of above plus: `catalog_management`, `commerce_account_read_settings`, `commerce_account_manage_orders`, `commerce_account_read_orders`, `commerce_account_read_reports`, `whatsapp_business_manage_events`, `private_computation_access`
- Regenerated via: Business Settings → System Users → Generate New Token → App "Constient"
- Updated in: `whatsapp/.env` (both local and server)
- Token starts with: `EAAWGMbfLQlABQzRdEJ...`

### 7. System User Assigned to Catalog
- Initial upload attempt failed with `(#200) Permissions error`
- Root cause: system user "assist24" was not assigned to the catalog asset
- Fix: Business Settings → System Users → assist24 → Add Assets → Catalogs → A24 Restaurant Menu → Full control
- After assignment, catalog read (`GET /{catalog_id}`) and batch upload (`POST /{catalog_id}/batch`) both work

### 8. Menu Items Uploaded to Catalog (67 items)
- All 67 items with price > 0 uploaded via `POST /v25.0/1585007629445142/batch`
- `image_url` is **required** — used Wikipedia food placeholder:
  `https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/800px-Good_Food_Display_-_NCI_Visuals_Online.jpg`
- Batch upload: 20 items per request, 4 batches, all returned handles
- Product count confirmed via API: `product_count: 67`
- Verified in Commerce Manager UI: 67 products, all Active, In stock, with images and prices

**Batch upload format:**
```json
{
    "method": "CREATE",
    "retailer_id": "<menu_item_id>",
    "data": {
        "name": "<menu_item_name>",
        "price": 2850,
        "currency": "INR",
        "description": "<description>",
        "availability": "in stock",
        "category": "<sub_category_name>",
        "url": "https://constient.com",
        "image_url": "<placeholder_url>"
    }
}
```

### 9. Product Messages — Awaiting Meta Indexing
- Attempted: `catalog_message`, `product`, `product_list` — all return "Products not found in FB Catalog"
- Products show `visibility: "published"` but `review_status: ""` (empty/pending)
- Meta needs to review/index products for WhatsApp commerce (**takes a few hours to 24 hours**)
- Commerce Manager UI shows all products as Active with 0 WhatsApp issues
- **Status: WAITING** — will retry periodically

**Test command (run on server to check if indexed):**
```bash
sudo docker exec a24-whatsapp-bridge python -c "
import os, httpx, json
token = os.getenv('WA_TOKEN')
phone_id = os.getenv('PHONE_NUMBER_ID')
h = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
r = httpx.post(f'https://graph.facebook.com/v25.0/{phone_id}/messages', headers=h, json={
    'messaging_product': 'whatsapp',
    'to': '918431126627',
    'type': 'interactive',
    'interactive': {
        'type': 'catalog_message',
        'body': {'text': 'Browse our menu!'},
        'action': {'name': 'catalog_message', 'parameters': {'thumbnail_product_retailer_id': '6e692c6b-8834-40e1-8e1e-2b993c28fd69'}}
    }
}, timeout=30)
print(json.dumps(r.json(), indent=2))
"
```

### 10. Product Sets Created (Category Grouping)
- 8 categories created as Product Sets via `POST /{catalog_id}/product_sets`
- Categories and counts:
  - Side Orders: 13 items (set: 2062370404328886)
  - Seafood Meal: 6 items (set: 935694739395349)
  - Desserts: 4 items (set: 767449336200311)
  - Hot Coffees: 4 items (set: 1559731412413901)
  - Chicken Meal: 12 items (set: 1818094438861022)
  - Chicken: 4 items (set: 910233591986794)
  - Beverages: 16 items (set: 1363404188883075)
  - Add Ons: 8 items (set: 1257879979782899)
- Uses filter: `{"retailer_id": {"is_any": [<retailer_ids>]}}`

### 11. Catalog Message Types in Use
| Use Case | Message Type | Header | Max Items |
|----------|-------------|--------|-----------|
| Full menu browse | `catalog_message` | "View X's Catalog" (Meta-controlled) | All |
| Menu by category | `product_list` | "Browse Menu" (custom) | 30, 10 sections |
| Search results | `product_list` | "Results: query" (custom) | 30 |
| Similar items | `product_list` | "You might also like" (custom) | 30 |
| Single recommendation | `product` | Product name (auto) | 1 |

All message types use the same catalog (1585007629445142).

### 12. Catalog Order Handling
- Customer sends cart → webhook receives `message.type: "order"`
- Bridge looks up item names via chatbot menu API
- Sends `direct_add_to_cart` form_response to chatbot
- Chatbot adds items to cart, responds with cart update + AGUI events
- Checkout flow continues as normal (dine-in/takeaway → payment → receipt)

## Steps Remaining

### 10. Handle Order Webhooks
- When customer sends cart, webhook receives `message.type: "order"`
- Order payload contains: `product_items[]` with `{product_retailer_id, quantity, item_price}`
- Map `product_retailer_id` back to `menu_item_id`
- Feed into existing chatbot checkout flow (dine-in/takeaway → payment)

### 11. Send Catalog/Product Messages from Chatbot
- When user says "show menu" → send `catalog_message` (full catalog browse)
- When showing search results → send `product_list` with sections
- When recommending items → send `product` (single product card)
- Integrate into WhatsApp bridge AGUI event handlers

### 12. Catalog Sync Script
- Auto-sync menu changes from DB to catalog (availability, price, new items)
- `UPDATE` method for existing items, `CREATE` for new items
- Run on PetPooja sync events or on a schedule
- Availability updates are instant — no re-review needed

## Updating Products (Post-Indexing)
Once indexed, products can be updated unlimited times without re-review:
```json
{
    "method": "UPDATE",
    "retailer_id": "<menu_item_id>",
    "data": {
        "availability": "out of stock",
        "price": 3500
    }
}
```

## Database Schema

### menu_item table
Key columns:
- `menu_item_id` (UUID, PK) — use as `retailer_product_id` in catalog
- `menu_item_name` (text)
- `menu_item_price` (decimal)
- `menu_item_description` (text, some empty)
- `menu_item_image_url` (text, all null currently)
- `menu_item_in_stock` (boolean)
- `menu_item_status` (text: "active")
- `menu_item_attribute_id` (FK → menu_item_attribute: veg/non-veg/egg)
- `menu_item_packaging_charges` (decimal)
- `menu_sub_category_id` (FK → menu_sub_categories)
- `is_deleted` (boolean)
- `ext_petpooja_item_id` (text, PetPooja sync ID)

### menu_sub_categories table
- `menu_sub_category_id` (UUID, PK)
- `category_id` (FK → menu_categories.menu_category_id)
- `sub_category_name` (text)

### menu_categories table
- `menu_category_id` (UUID, PK)
- `menu_category_name` (text)

### menu_item_attribute table
- `menu_item_attribute_id` (UUID, PK)
- `menu_item_attribute_name` (text: "veg", "non-veg", "egg")

## Previous Approaches Tried

### WhatsApp Flows (Failed — TIER_250 restriction)
- All 4 flows (select_items, manage_cart, select_items_qty, booking) created as DRAFT
- JSON uploaded successfully with zero validation errors
- **Publish blocked:** "Blocked by Integrity" (error_subcode: 4233020)
- Root cause: Meta requires higher message quality/volume threshold
  - Current: 9 conversations in 30 days
  - UI shows: "Before you can publish this flow: Send high-quality messages"
- Tested with minimal flow JSON (TextBody + Footer) — same error
- Tested with v5.0 (invalid), v6.3, v7.3 — same publish error
- Tested via API (v21.0, v22.0, v25.0) and UI — same result
- Deleted all test flows after debugging
- **Conclusion:** Account-level restriction at TIER_250, not a code/JSON issue

### CTA Web Pages (Working but opens external browser)
- Menu browsing, cart management, search, checkout via web pages
- Works well but opens in Chrome (not in-app) because IAB requires TIER_1000+
- Users must manually return to WhatsApp after actions
- Currently deployed on release/v1.1-qa-fixes-petpooja-sync branch
- Quick reply ordering fix and receipt URL fix committed

### Interactive List Messages (Not yet tried)
- Native WhatsApp picker, no tier restrictions
- Limited to 10 items per section, no quantity input
- Could work for category browsing but not full menu

## Architecture (Catalog Approach)

```
Customer                WhatsApp            Bridge              Chatbot
   |                       |                  |                    |
   |--[Browse Catalog]---->|                  |                    |
   |<--[Native Menu UI]----|                  |                    |
   |--[Add to Cart]------->|                  |                    |
   |--[Send Cart]--------->|                  |                    |
   |                       |--[order webhook]>|                    |
   |                       |                  |--[cart items]----->|
   |                       |                  |<--[checkout flow]--|
   |<--[Dine-in/Takeaway?]-|<-----------------|                    |
   |--[Takeaway]---------->|----------------->|                    |
   |                       |                  |--[create order]--->|
   |<--[Payment link]------|<-----------------|<--[razorpay link]--|
   |--[Pay]--------------->|                  |                    |
   |<--[Confirmation]------|<-----------------|-<[receipt]---------|
```

## Notes
- Catalog does NOT require Flows publishing or tier restrictions
- Products can be synced programmatically via Commerce API
- Cart is native WhatsApp UI — best user experience
- Images improve conversion but placeholder works for now
- Currency must be INR for Indian phone numbers
- Products need initial Meta indexing (hours to 24h) but updates are instant after
- Branch: `feature/whatsapp-catalog-ordering`
