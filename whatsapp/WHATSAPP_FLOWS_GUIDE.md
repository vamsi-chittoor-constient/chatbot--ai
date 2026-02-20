# WhatsApp Flows & UX Upgrade — Implementation Guide

## Overview

This document covers the WhatsApp UX upgrade implemented for the A24 restaurant ordering platform. Three key problems were solved:

| Problem | Solution |
|---------|----------|
| Menu was single-select (list popup) | **WhatsApp Flows** — native multi-select CheckboxGroup |
| Quick replies >3 showed as popup | **Split button messages** — chunks of 3 inline buttons |
| Cart editing was messy with per-item buttons | **Cart Management Flow** — per-item quantity dropdowns |

---

## Architecture

```
User taps "View Menu" in WhatsApp
  → Chatbot emits MENU_DATA (items, categories, prices)
  → WhatsApp Bridge builds Flow data payload
  → Sends interactive message (type: "flow") to Meta API
  → WhatsApp app opens native Flow form
  → User selects items / adjusts quantities
  → Flow returns nfm_reply via webhook
  → Bridge converts to form_response
  → Sends to chatbot WebSocket (bypasses LLM)
  → Chatbot updates cart directly
```

**Key design decision:** We use **Navigate mode** (not Data Exchange), which means:
- No encryption required
- Data is passed at send time via `flow_action_payload`
- Flow JSON uses `${data.xxx}` bindings to display dynamic content
- No endpoint/server needed for the Flow itself

---

## Files Modified/Created

| File | Action | Purpose |
|------|--------|---------|
| `whatsapp/app.py` | Modified | Core bridge — Flow sending, nfm_reply handling, quick reply split |
| `whatsapp/flows/select_items_flow.json` | Created | Item Selection Flow template (CheckboxGroup) |
| `whatsapp/flows/manage_cart_flow.json` | Created | Cart Management Flow template (Dropdowns) |
| `whatsapp/manage_flows.py` | Created | CLI to create/publish/manage Flows via Meta Graph API |
| `whatsapp/.env.example` | Modified | Added WABA_ID, FLOW_SELECT_ITEMS_ID, FLOW_MANAGE_CART_ID |
| `whatsapp/test_whatsapp_bridge.py` | Modified | 37 tests covering all new functionality |

**No changes to chatbot** — existing `form_response` handlers at `chat.py:1338-1463` already support `direct_add_to_cart`, `direct_update_cart`, `direct_remove_from_cart`.

---

## Feature Details

### 1. Quick Reply Split (4-10 options)

**Before:** >3 quick replies → popup list message (bad UX)
**After:** Split into multiple inline button messages (chunks of 3)

```
5 quick replies → 2 messages:
  Message 1: [Option A] [Option B] [Option C]
  Message 2: [Option D] [Option E]
```

- 1-3 options → single button message (unchanged)
- 4-10 options → split into chunks of 3, multiple button messages
- 11+ options → list fallback (WhatsApp limit)

**Code:** `_convert_quick_replies()` in `app.py`

### 2. Item Selection Flow (Menu Ordering)

**Before:** List message with radio buttons (single-select, max 10 items)
**After:** Native WhatsApp Flow with CheckboxGroup (multi-select, up to 20 items)

**Flow JSON:** `flows/select_items_flow.json` (version 6.0)
- Screen: `SELECT_ITEMS`
- Component: `CheckboxGroup` bound to `${data.items}`
- Returns: `{selected_items: ["Item A", "Item B"], flow_type: "select_items"}`
- All selected items are added to cart with quantity 1

**Menu routing logic:**
- Single category OR ≤20 items + Flow ID configured → **Item Selection Flow**
- Multiple categories, ≤9 → **Inline category buttons** (chunks of 3)
- Multiple categories, >9 → List-based category picker (fallback)
- No Flow ID configured → Original list behavior (graceful degradation)

**Code:** `_convert_menu_data()`, `_send_item_selection_flow()` in `app.py`

### 3. Cart Management Flow

**Before:** >3 cart items → simplified text + action buttons (no per-item control)
**After:** Native WhatsApp Flow with per-item quantity dropdowns

**Flow JSON:** `flows/manage_cart_flow.json` (version 6.0)
- Screen: `MANAGE_CART`
- 10 item slots, each with TextSubheading + Dropdown (visible/hidden dynamically)
- Dropdown options: Remove (0), 1, 2, 3, ..., 10
- Returns: `{qty_0: "3", qty_1: "0", ..., flow_type: "manage_cart"}`
- qty=0 → removes item, qty>0 → updates quantity

**Cart routing logic:**
- ≤3 items → Per-item button cards (unchanged, clean for small carts)
- 4-10 items + Flow ID configured → **Cart Management Flow** + Add More / Checkout buttons
- >10 items or no Flow ID → Simplified action buttons (fallback)

**Code:** `_convert_cart_data()`, `_send_cart_management_flow()` in `app.py`

### 4. nfm_reply Webhook Handler

When a user submits a Flow, WhatsApp sends an `nfm_reply` message type. The bridge:
1. Detects `nfm_reply` in `_extract_user_message()` → returns `__FLOW_RESPONSE__` sentinel
2. `_process_message()` intercepts the sentinel → calls `_handle_flow_response()`
3. Routes by `flow_type`:
   - `select_items` → sends `direct_add_to_cart` form_response to chatbot
   - `manage_cart` → sends `direct_update_cart` / `direct_remove_from_cart` to chatbot

### 5. Upselling via Flow

When the chatbot suggests upsell items (e.g., "Add sides?"), it emits `MENU_DATA` with a small item set. The same `_send_item_selection_flow()` handles this automatically — no separate upsell code needed.

Search results with ≥4 available items also use the Flow for multi-select.

---

## Environment Variables

```env
# Required for Flows
WABA_ID="your-whatsapp-business-account-id"
FLOW_SELECT_ITEMS_ID="flow-id-from-manage_flows.py"
FLOW_MANAGE_CART_ID="flow-id-from-manage_flows.py"

# Existing
WA_TOKEN="your-meta-access-token"
PHONE_NUMBER_ID="your-phone-number-id"
WEBHOOK_VERIFY_TOKEN="your-webhook-verify-token"
CHATBOT_WS_BASE_URL="ws://chatbot-app:8000/api/v1/chat"
```

**Graceful degradation:** If `FLOW_SELECT_ITEMS_ID` or `FLOW_MANAGE_CART_ID` are empty, all features fall back to the original list/button behavior.

---

## Flow Management CLI

```bash
# Create flows + upload JSON (returns Flow IDs for .env)
python manage_flows.py create

# Check flow status and validation errors
python manage_flows.py status

# List all flows on your WABA
python manage_flows.py list

# Publish flows (IRREVERSIBLE - only after verifying no errors)
python manage_flows.py publish
```

**Important:** Publishing is irreversible. Once published, Flow JSON cannot be modified — you must create a new flow (new ID). Always check `status` first.

**Note:** Publishing requires a verified Meta Business Account. Draft flows can still be tested with your own phone number.

---

## Flow Data is Dynamic

The Flow JSON templates are static (published once), but the **data is dynamic**:

- **Menu items & prices** come from the chatbot's MENU_DATA event (synced from PetPooja)
- **Cart contents** come from the chatbot's CART_DATA event
- Data is passed at send time via `flow_action_payload.data`

When PetPooja syncs new items/prices, the next Flow opened will show the latest data automatically.

---

## Testing

```bash
cd whatsapp
python -m pytest test_whatsapp_bridge.py -v
```

37 tests cover:
- Quick reply split: 4→2 msgs, 10→4 msgs, 11+→list fallback
- Menu: single category→Flow, multi-category→buttons, large→list
- Cart: small→per-item buttons, large→Cart Flow
- Search: large results→Flow
- nfm_reply extraction and parsing
- Flow response handling (select_items, manage_cart)
- Graceful degradation (no Flow IDs → original behavior)

---

## Constraints & Limits

| Constraint | Limit |
|-----------|-------|
| Flow CheckboxGroup items | 1-20 per screen |
| Flow Dropdown options | 1-200 |
| Cart Flow item slots | 10 max (falls back for >10) |
| Button message buttons | 3 max per message |
| Flow CTA text | 20 chars, no emoji |
| Components per screen | 50 max (cart flow uses ~32) |
| Active flow context TTL | 30 minutes (auto-cleaned) |

---

## Troubleshooting

**"Integrity requirements not met" on publish:**
Your Meta Business Account needs to be verified. Go to Business Manager → Security Center → complete verification.

**"INVALID_FLOW_JSON_VERSION":**
Flow JSON version 5.0 and below are expired. Use version `6.0` or later.

**Flows not appearing in WhatsApp:**
- Check flow status: `python manage_flows.py status`
- Ensure Flow IDs are in `.env`
- Draft flows only work with your test phone number
- Published flows work with all users

**Token expired:**
Temporary tokens expire every ~24 hours. Generate a new one at developers.facebook.com → WhatsApp → API Setup. For production, use a System User permanent token.
