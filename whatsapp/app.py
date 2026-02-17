from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse
import httpx
import asyncio
import websockets
import json
import os
from typing import Dict, Optional, List, Any
from logger_wrapper import LOGGER
from dotenv import load_dotenv

load_dotenv(override=True)

app = FastAPI(
    title="WhatsApp Bridge",
    description="Bridge service between WhatsApp Business API and Restaurant Assistant",
    version="2.0.0"
)

# === Config ===
VERIFY_TOKEN = os.getenv("WEBHOOK_VERIFY_TOKEN")
ACCESS_TOKEN = os.getenv("WA_TOKEN")
WHATSAPP_PHONE_ID = os.getenv("PHONE_NUMBER_ID")
CHATBOT_WS_BASE_URL = os.getenv("CHATBOT_WS_BASE_URL", "ws://chatbot-app:8000/api/v1/chat")
WHATSAPP_API_VERSION = "v19.0"

LOGGER.info("WhatsApp Bridge starting...")
LOGGER.info(f"Chatbot WebSocket base URL: {CHATBOT_WS_BASE_URL}")

# === Global persistent WebSocket connections (per user) ===
ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
ws_lock = asyncio.Lock()
# Per-user locks to prevent concurrent recv() on the same WebSocket
_user_locks: Dict[str, asyncio.Lock] = {}
# Dedup: track processed WhatsApp message IDs to reject Meta retries
_processed_msg_ids: Dict[str, float] = {}   # msg_id → monotonic timestamp
_DEDUP_WINDOW = 300  # seconds (5 min)


# ===================================================================
# WEBHOOK VERIFICATION ENDPOINT (GET)
# ===================================================================
@app.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
):
    """
    Webhook verification endpoint for Meta WhatsApp Business API.
    Meta calls this to verify your webhook URL during setup.
    """
    LOGGER.info(f"Webhook verification request: mode={mode}, token_match={token == VERIFY_TOKEN}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        LOGGER.info("Webhook verified successfully")
        return int(challenge)
    else:
        LOGGER.warning(f"Webhook verification failed: mode={mode}")
        raise HTTPException(status_code=403, detail="Verification failed")


# ===================================================================
# WEBHOOK MESSAGE RECEIVER ENDPOINT (POST)
# ===================================================================
@app.post("/webhook")
async def receive_message(request: Request):
    """
    Receive incoming WhatsApp messages from Meta webhook.
    Returns 200 immediately to Meta, then processes the message in the background.
    This prevents Meta from retrying the webhook when AI response takes >20s.
    """
    try:
        data = await request.json()
        LOGGER.debug(f"Webhook payload received: {json.dumps(data, indent=2)}")

        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                if messages:
                    message = messages[0]
                    msg_id = message.get("id", "")
                    from_number = message.get("from")
                    message_type = message.get("type")
                    user_name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "User")

                    # --- Dedup: reject retries of already-processed messages ---
                    if msg_id and msg_id in _processed_msg_ids:
                        LOGGER.warning(f"Duplicate webhook for msg {msg_id} from {from_number}, skipping")
                        return JSONResponse(content={"status": "ok"}, status_code=200)
                    if msg_id:
                        _processed_msg_ids[msg_id] = asyncio.get_event_loop().time()
                        _cleanup_dedup()

                    # Extract user message based on message type
                    user_message = _extract_user_message(message, message_type)

                    if user_message is None:
                        LOGGER.warning(f"Unsupported message type: {message_type}")
                        continue

                    LOGGER.info(f"Message from {from_number} ({user_name}): {user_message[:50]}...")

                    # Process in background — return 200 to Meta immediately
                    asyncio.create_task(
                        _process_message(from_number, user_message, msg_id)
                    )

    except Exception as e:
        LOGGER.error(f"Error processing webhook: {e}", exc_info=True)

    # Always return 200 immediately to Meta (prevents timeout retries)
    return JSONResponse(content={"status": "ok"}, status_code=200)


async def _process_message(phone: str, user_message: str, msg_id: str):
    """Background task: forward message to chatbot, send response to WhatsApp."""
    try:
        assistant_reply = await get_chatbot_reply(phone, user_message)

        if assistant_reply is not None:
            LOGGER.info(f"Sending response to WhatsApp: {assistant_reply[:50]}...")
            await send_whatsapp_reply(phone, assistant_reply)
        else:
            LOGGER.info(f"Response for {phone} handled via AGUI events")

    except Exception as e:
        LOGGER.error(f"Error processing message {msg_id} for {phone}: {e}", exc_info=True)
        await send_whatsapp_reply(phone, "Sorry, something went wrong. Please try again.")


def _cleanup_dedup():
    """Remove expired entries from the dedup map (older than _DEDUP_WINDOW)."""
    now = asyncio.get_event_loop().time()
    expired = [k for k, ts in _processed_msg_ids.items() if now - ts > _DEDUP_WINDOW]
    for k in expired:
        del _processed_msg_ids[k]


def _extract_user_message(message: dict, message_type: str) -> Optional[str]:
    """
    Extract user-facing message text from any supported WhatsApp message type.
    Returns None for unsupported types.
    """
    if message_type == "text":
        return message.get("text", {}).get("body", "")

    elif message_type == "interactive":
        interactive = message.get("interactive", {})
        reply_type = interactive.get("type")

        if reply_type == "button_reply":
            # User tapped a reply button — use the button ID as the action
            button_id = interactive.get("button_reply", {}).get("id", "")
            button_title = interactive.get("button_reply", {}).get("title", "")
            LOGGER.info(f"Button reply: id={button_id}, title={button_title}")
            return button_id or button_title

        elif reply_type == "list_reply":
            # User selected from a list — use the row ID as the action
            row_id = interactive.get("list_reply", {}).get("id", "")
            row_title = interactive.get("list_reply", {}).get("title", "")
            LOGGER.info(f"List reply: id={row_id}, title={row_title}")
            return row_id or row_title

    return None


# ===================================================================
# WEBSOCKET MESSAGE HANDLER
# ===================================================================
async def get_chatbot_reply(phone: str, user_message: str) -> Optional[str]:
    """
    Send message to main app via WebSocket and wait for response.
    Creates persistent WebSocket connection per user (phone number as session ID).

    Returns:
        str: text message to send to WhatsApp
        None: response was already sent via AGUI events (interactive messages / streamed text)

    The chatbot streams responses via AGUI events:
    - TEXT_MESSAGE_CONTENT: text chunks streamed directly to WhatsApp
    - SEARCH_RESULTS, QUICK_REPLIES, etc.: converted to WhatsApp interactive messages
    - ai_response: only for welcome messages and direct actions (legacy)
    - RUN_FINISHED: signals response is complete
    """
    is_new_connection = False

    # Per-user lock to prevent concurrent recv() on the same WebSocket
    if phone not in _user_locks:
        _user_locks[phone] = asyncio.Lock()
    user_lock = _user_locks[phone]

    try:
        # Per-user lock covers BOTH connection management AND message exchange
        async with user_lock:
            # Lock for connection management
            async with ws_lock:
                # Check if connection exists and is open
                if phone in ws_connections:
                    ws = ws_connections[phone]
                    if not ws.open:
                        LOGGER.warning(f"WebSocket for {phone} is closed, reconnecting...")
                        del ws_connections[phone]
                    else:
                        LOGGER.debug(f"Reusing existing WebSocket for {phone}")

                # Create new connection if needed
                if phone not in ws_connections:
                    # Session ID uses "wa-" prefix so chatbot skips auth forms
                    session_id = f"wa-{phone}"
                    ws_url = f"{CHATBOT_WS_BASE_URL}/{session_id}"
                    LOGGER.info(f"Creating new WebSocket connection for {phone} -> {ws_url}")

                    ws_connections[phone] = await asyncio.wait_for(
                        websockets.connect(ws_url),
                        timeout=30
                    )
                    LOGGER.info(f"WebSocket connected for {phone}")
                    is_new_connection = True

            websocket = ws_connections[phone]

            # On new connection, drain welcome/init messages from chatbot
            if is_new_connection:
                welcome_text, _ = await _drain_and_collect_response(websocket, phone, timeout=15)
                if welcome_text:
                    LOGGER.info(f"Welcome message for {phone}: {welcome_text[:80]}...")
                    await send_whatsapp_reply(phone, welcome_text)

            # Send user message to chatbot
            payload = {
                "message": user_message,
                "source": "whatsapp"
            }
            await websocket.send(json.dumps(payload))
            LOGGER.info(f"Sent to chatbot from {phone}: {user_message[:50]}...")

            # Collect response (text via AGUI streaming + interactive cards sent directly)
            text, any_sent = await _drain_and_collect_response(websocket, phone, timeout=45)

            if text:
                return text  # Caller will send this as WhatsApp text message
            elif any_sent:
                return None  # Response already handled via AGUI (interactive messages / streamed text)
            else:
                return "Sorry, I couldn't get a response. Please try again."

    except asyncio.TimeoutError:
        LOGGER.error(f"Timeout waiting for response for {phone}")
        if phone in ws_connections:
            del ws_connections[phone]
        return "Sorry, the assistant is taking too long to respond. Please try again."

    except websockets.exceptions.ConnectionClosed:
        LOGGER.error(f"WebSocket connection closed for {phone}")
        if phone in ws_connections:
            del ws_connections[phone]
        return "Sorry, the connection was lost. Please try again."

    except Exception as e:
        LOGGER.error(f"Error communicating with chatbot for {phone}: {e}", exc_info=True)
        if phone in ws_connections:
            del ws_connections[phone]
        return "Sorry, the assistant is currently unavailable. Please try again later."


async def _drain_and_collect_response(
    websocket: websockets.WebSocketClientProtocol,
    phone: str,
    timeout: float = 45
) -> tuple:
    """
    Read messages from the chatbot WebSocket and collect response.

    The chatbot streams responses via AGUI events:
    - TEXT_MESSAGE_CONTENT: text chunks (delta) — these ARE the AI text response
    - SEARCH_RESULTS, QUICK_REPLIES, etc.: interactive cards — sent to WhatsApp immediately
    - RUN_FINISHED: signals end of response
    - ai_response: only for welcome messages and direct actions (legacy path)

    Returns:
        (text, any_sent) where:
        - text: remaining text to send as reply (or None if already sent)
        - any_sent: True if any messages were already sent to WhatsApp during processing
    """
    text_chunks = []       # TEXT_MESSAGE_CONTENT deltas (joined at TEXT_MESSAGE_END)
    direct_parts = []      # ai_response / system_message text (legacy path)
    any_sent = False       # Whether we already sent messages to WhatsApp
    last_quick_replies = None  # Buffer: only send the LAST QUICK_REPLIES (web UI replaces them)
    deadline = asyncio.get_event_loop().time() + timeout

    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            break

        try:
            raw = await asyncio.wait_for(
                websocket.recv(),
                timeout=min(remaining, 10)
            )
        except asyncio.TimeoutError:
            # No more messages — break if we already sent/collected something
            if direct_parts or text_chunks or any_sent:
                break
            continue

        LOGGER.debug(f"Raw WS message for {phone}: {raw[:200]}...")

        try:
            data = json.loads(raw)
            msg_type = data.get("message_type", "")
            message_text = data.get("message", "")

            # --- Legacy ai_response (welcome messages, direct actions like add-to-cart) ---
            if msg_type == "ai_response" and message_text:
                direct_parts.append(message_text)
                # Drain trailing AGUI events (QUICK_REPLIES often follow direct actions)
                trailing_sent = await _drain_trailing_events(websocket, phone)
                any_sent = any_sent or trailing_sent
                break

            # --- AGUI events (primary response path) ---
            elif msg_type == "agui_event":
                agui_data = data.get("metadata", {}).get("agui", {})
                agui_type = agui_data.get("type", "")

                # Text streaming: collect delta chunks
                if agui_type == "TEXT_MESSAGE_CONTENT":
                    delta = agui_data.get("delta", "")
                    if delta:
                        text_chunks.append(delta)
                    continue

                # Text stream ended: flush accumulated text to WhatsApp immediately
                # (so text appears BEFORE interactive cards that follow)
                elif agui_type == "TEXT_MESSAGE_END":
                    if text_chunks:
                        text = "".join(text_chunks).strip()
                        if text:
                            await send_whatsapp_reply(phone, text)
                            any_sent = True
                            LOGGER.info(f"Sent streamed text to {phone}: {text[:80]}...")
                        text_chunks.clear()
                    continue

                # Text stream start: just a marker, skip
                elif agui_type == "TEXT_MESSAGE_START":
                    continue

                # Completion signals — stop collecting
                elif agui_type in ("RUN_FINISHED", "RUN_ERROR"):
                    LOGGER.debug(f"Received {agui_type} for {phone}, response complete")
                    break

                # QUICK_REPLIES: buffer instead of sending (web UI replaces them;
                # tools emit one, then orchestrator emits another — only last matters)
                elif agui_type == "QUICK_REPLIES":
                    last_quick_replies = agui_data
                    LOGGER.debug(f"Buffered QUICK_REPLIES for {phone} (will send last one)")
                    continue

                # Other interactive events: convert and send to WhatsApp
                else:
                    sent = await _handle_agui_event(phone, agui_data)
                    if sent:
                        any_sent = True
                    continue

            elif msg_type == "typing_indicator":
                continue

            elif msg_type == "system_message" and message_text:
                direct_parts.append(message_text)
                continue

            elif message_text:
                direct_parts.append(message_text)

        except json.JSONDecodeError:
            if raw.strip():
                direct_parts.append(raw.strip())
                break

    # Flush the last buffered QUICK_REPLIES (deduplicates tool + orchestrator emissions)
    if last_quick_replies:
        await _convert_quick_replies(phone, last_quick_replies)
        any_sent = True
        LOGGER.info(f"Sent final QUICK_REPLIES to {phone}")

    # Build final text from any remaining pieces
    remaining_text = None
    if direct_parts:
        remaining_text = "\n\n".join(direct_parts)
    elif text_chunks:
        # TEXT_MESSAGE_END never arrived — flush remaining chunks
        text = "".join(text_chunks).strip()
        if text:
            remaining_text = text

    return (remaining_text, any_sent)


async def _drain_trailing_events(
    websocket: websockets.WebSocketClientProtocol,
    phone: str,
    window: float = 5.0
) -> bool:
    """
    After receiving an ai_response, drain any trailing AGUI events
    (e.g. SEARCH_RESULTS card, QUICK_REPLIES) that arrive shortly after.
    Stops on RUN_FINISHED or timeout.

    Returns True if any messages were sent to WhatsApp.
    """
    any_sent = False
    last_quick_replies = None
    deadline = asyncio.get_event_loop().time() + window
    while True:
        remaining = deadline - asyncio.get_event_loop().time()
        if remaining <= 0:
            break
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=min(remaining, 2.0))
            data = json.loads(raw)
            msg_type = data.get("message_type", "")

            if msg_type == "agui_event":
                agui_data = data.get("metadata", {}).get("agui", {})
                agui_type = agui_data.get("type", "")

                # Stop on completion signals
                if agui_type in ("RUN_FINISHED", "RUN_ERROR"):
                    break

                # Buffer QUICK_REPLIES — only send last one
                if agui_type == "QUICK_REPLIES":
                    last_quick_replies = agui_data
                    continue

                sent = await _handle_agui_event(phone, agui_data)
                if sent:
                    any_sent = True

            elif msg_type == "ai_response" and data.get("message"):
                await send_whatsapp_reply(phone, data["message"])
                any_sent = True
            # Skip typing_indicator, system_message, etc.
        except (asyncio.TimeoutError, json.JSONDecodeError, Exception):
            break

    # Flush last buffered QUICK_REPLIES
    if last_quick_replies:
        await _convert_quick_replies(phone, last_quick_replies)
        any_sent = True

    return any_sent


# ===================================================================
# AGUI → WHATSAPP INTERACTIVE CONVERSION
# ===================================================================

async def _handle_agui_event(phone: str, agui: dict) -> bool:
    """
    Route AGUI events to the appropriate WhatsApp interactive converter.
    Skips events with no WhatsApp equivalent (lifecycle, activity, forms, etc.).

    Returns True if a WhatsApp message was sent, False if skipped.
    Note: TEXT_MESSAGE_* and RUN_FINISHED/RUN_ERROR are handled by the caller.
    """
    event_type = agui.get("type", "")

    # Interactive events that send WhatsApp messages
    if event_type == "SEARCH_RESULTS":
        await _convert_search_results(phone, agui)
        return True
    elif event_type == "MENU_DATA":
        await _convert_menu_data(phone, agui)
        return True
    elif event_type == "CART_DATA":
        await _convert_cart_data(phone, agui)
        return True
    elif event_type == "PAYMENT_METHOD_SELECTION":
        await _convert_payment_methods(phone, agui)
        return True
    elif event_type == "PAYMENT_LINK":
        await _convert_payment_link(phone, agui)
        return True
    elif event_type == "PAYMENT_SUCCESS":
        await _convert_payment_success(phone, agui)
        return True
    elif event_type == "QUICK_REPLIES":
        # Handled by caller (buffered to deduplicate — tools + orchestrator both emit)
        LOGGER.debug(f"QUICK_REPLIES passed to _handle_agui_event for {phone} (should be buffered by caller)")
        await _convert_quick_replies(phone, agui)
        return True
    elif event_type == "ORDER_DATA":
        await _convert_order_data(phone, agui)
        return True
    elif event_type == "RECEIPT_LINK":
        await _convert_receipt_link(phone, agui)
        return True

    # Lifecycle events — skip silently (TEXT_MESSAGE_* handled by caller)
    elif event_type in (
        "RUN_STARTED",
        "ACTIVITY_START", "ACTIVITY_END",
        "TEXT_MESSAGE_START", "TEXT_MESSAGE_CONTENT", "TEXT_MESSAGE_END",
        "TOOL_CALL_START", "TOOL_CALL_ARGS", "TOOL_CALL_END", "TOOL_CALL_RESULT",
        "STATE_SNAPSHOT", "STATE_DELTA",
        "FORM_REQUEST", "FORM_SUBMITTED", "FORM_DISMISS",
        "STEP_STARTED", "STEP_FINISHED", "ARTIFACT",
    ):
        LOGGER.debug(f"Skipping AGUI event {event_type} for {phone} (no WA equivalent)")
        return False
    else:
        LOGGER.warning(f"Unknown AGUI event type: {event_type} for {phone}")
        return False


def _truncate(text: str, max_len: int) -> str:
    """Truncate text to max_len, appending '...' if truncated."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# --- SEARCH_RESULTS ---
async def _convert_search_results(phone: str, agui: dict) -> None:
    """Convert search results to reply buttons (≤3) or list message (>3) with availability indicators."""
    items = agui.get("items", [])
    if not items:
        return

    query = agui.get("query", "search")
    available = [i for i in items if i.get("is_available_now", True)]
    unavailable = [i for i in items if not i.get("is_available_now", True)]

    if len(items) <= 3:
        # Reply buttons — one per available item only
        buttons = []
        body = f"🔍 Results for *{query}*:\n"
        for item in items[:3]:
            name = item.get("name", "Item")
            price = item.get("price", 0)
            is_avail = item.get("is_available_now", True)
            meal_types = item.get("meal_types", [])
            
            if is_avail:
                body += f"\n✅ {name} — ₹{price}"
                buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": _truncate(f"add {name} to cart", 256),
                        "title": _truncate(name, 20)
                    }
                })
            else:
                meal_str = ", ".join(meal_types) if meal_types else "later"
                body += f"\n🕐 {name} — ₹{price} ({meal_str})"

        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": _truncate(body, 1024)},
            "action": {"buttons": buttons}
        })
    else:
        # List message with sections for available/unavailable
        sections = []
        if available:
            rows = []
            for item in available[:10]:
                name = item.get("name", "Item")
                price = item.get("price", 0)
                category = item.get("category", "")
                rows.append({
                    "id": _truncate(f"add {name} to cart", 200),
                    "title": _truncate(name, 24),
                    "description": _truncate(f"₹{price} • {category}", 72)
                })
            sections.append({"title": f"✅ Available Now ({len(available)})", "rows": rows})
        
        if unavailable and len(sections) == 0:  # Only show unavailable if no available items
            rows = []
            for item in unavailable[:10]:
                name = item.get("name", "Item")
                price = item.get("price", 0)
                meal_types = item.get("meal_types", [])
                meal_str = ", ".join(meal_types[:2]) if meal_types else "later"
                rows.append({
                    "id": _truncate(f"notify {name}", 200),
                    "title": _truncate(name, 24),
                    "description": _truncate(f"₹{price} • {meal_str}", 72)
                })
            sections.append({"title": f"🕐 Available Later ({len(unavailable)})", "rows": rows})

        if sections:
            await send_whatsapp_interactive(phone, {
                "type": "list",
                "body": {"text": _truncate(f"🔍 Found {len(items)} items for *{query}*. Tap to add:", 1024)},
                "action": {
                    "button": "View Items",
                    "sections": sections
                }
            })
    LOGGER.info(f"Sent search results ({len(items)} items, {len(available)} available) to {phone}")


# --- MENU_DATA ---
# Threshold: if menu fits in one list message (≤10 categories, ≤10 items each), show items directly.
# Otherwise, show category list and let user drill down.
MENU_DIRECT_THRESHOLD = 100  # max items to show directly (10 sections × 10 rows)

async def _convert_menu_data(phone: str, agui: dict) -> None:
    """
    Convert menu to WhatsApp list message with meal period indicator.
    - Small menu (≤100 items): show items grouped by category in one list
    - Large menu (>100 items): show categories as a list, user taps to filter
    """
    items = agui.get("items", [])
    categories = agui.get("categories", [])
    if not items:
        return

    # Group items by category
    by_category: Dict[str, list] = {}
    for item in items:
        cat = item.get("category", "Other")
        by_category.setdefault(cat, []).append(item)

    cat_order = categories or list(by_category.keys())
    meal = agui.get("current_meal_period", "")
    
    # Meal period emoji
    meal_emoji = {"Breakfast": "☕", "Lunch": "☀️", "Dinner": "🌙"}.get(meal, "🍽️")

    if len(items) <= MENU_DIRECT_THRESHOLD:
        # --- Small menu: show all items grouped by category ---
        sections = []
        for cat in cat_order:
            if cat not in by_category:
                continue
            rows = []
            for item in by_category[cat][:10]:
                name = item.get("name", "Item")
                price = item.get("price", 0)
                rows.append({
                    "id": _truncate(f"add {name} to cart", 200),
                    "title": _truncate(name, 24),
                    "description": _truncate(f"₹{price}", 72)
                })
            if rows:
                sections.append({"title": _truncate(cat, 24), "rows": rows})

        if not sections:
            return

        body = f"{meal_emoji} *Menu*"
        if meal:
            body += f" — {meal} Time"
        body += f"\n{len(items)} items available now. Tap to add:"

        await send_whatsapp_interactive(phone, {
            "type": "list",
            "body": {"text": _truncate(body, 1024)},
            "action": {"button": "Browse Menu", "sections": sections[:10]}
        })
        LOGGER.info(f"Sent full menu ({len(items)} items, {len(sections)} sections) to {phone}")

    else:
        # --- Large menu: show categories as filter options ---
        rows = []
        for cat in cat_order[:10]:  # Max 10 rows
            count = len(by_category.get(cat, []))
            rows.append({
                "id": _truncate(f"show {cat} menu", 200),
                "title": _truncate(cat, 24),
                "description": _truncate(f"{count} items", 72)
            })

        if not rows:
            return

        body = "🍽️ *Menu*"
        if meal:
            body += f" ({meal})"
        body += f"\n{len(items)} items across {len(cat_order)} categories."
        body += "\nPick a category to browse:"

        await send_whatsapp_interactive(phone, {
            "type": "list",
            "body": {"text": _truncate(body, 1024)},
            "action": {
                "button": "Choose Category",
                "sections": [{"title": "Categories", "rows": rows}]
            }
        })
        LOGGER.info(f"Sent category filter ({len(cat_order)} categories, {len(items)} total items) to {phone}")


# --- CART_DATA ---
async def _convert_cart_data(phone: str, agui: dict) -> None:
    """Convert cart to text summary + per-item action buttons (for small carts) or list (for large carts)."""
    items = agui.get("items", [])
    total = agui.get("total", 0)
    packaging = agui.get("packaging_charge_per_item", 30)

    if not items:
        await send_whatsapp_reply(phone, "🛒 Your cart is empty.")
        return

    # Send cart summary
    lines = ["🛒 *Your Cart*\n"]
    for i, item in enumerate(items, 1):
        name = item.get("name") or item.get("item_name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        lines.append(f"{i}. {name} × {qty} — ₹{price * qty}")

    lines.append(f"\n📦 Packaging: ₹{packaging} × {len(items)} = ₹{packaging * len(items)}")
    lines.append(f"💰 *Total: ₹{total}*")
    await send_whatsapp_reply(phone, "\n".join(lines))
    
    # Strategy: For small carts (≤3 items), send per-item buttons. For larger carts, use list.
    if len(items) <= 3:
        # Send individual item cards with +/- buttons
        for item in items:
            await _send_cart_item_buttons(phone, item)
        
        # Then send checkout button
        buttons = [
            {"type": "reply", "reply": {"id": "add more items", "title": "Add More Items"}},
            {"type": "reply", "reply": {"id": "checkout", "title": "Proceed to Checkout"}}
        ]
        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": "Ready to checkout?"},
            "action": {"buttons": buttons}
        })
    else:
        # For large carts, use list-based modification
        buttons = [
            {"type": "reply", "reply": {"id": "modify_cart_items", "title": "Modify Items"}},
            {"type": "reply", "reply": {"id": "add more items", "title": "Add More"}},
            {"type": "reply", "reply": {"id": "checkout", "title": "Checkout"}}
        ]
        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": "What would you like to do?"},
            "action": {"buttons": buttons}
        })
    
    LOGGER.info(f"Sent cart ({len(items)} items, ₹{total}) to {phone}")


async def _send_cart_item_buttons(phone: str, item: dict) -> None:
    """Send a button card for a single cart item with +1, -1, Remove actions."""
    name = item.get("name") or item.get("item_name", "Item")
    qty = item.get("quantity", 1)
    price = item.get("price", 0)
    
    buttons = [
        {"type": "reply", "reply": {"id": _truncate(f"increase {name}", 256), "title": "➕ Add One"}},
        {"type": "reply", "reply": {"id": _truncate(f"decrease {name}", 256), "title": "➖ Remove One"}},
        {"type": "reply", "reply": {"id": _truncate(f"remove {name}", 256), "title": "🗑️ Delete"}}
    ]
    
    body = f"*{name}*\nQuantity: {qty}\nPrice: ₹{price} each\nSubtotal: ₹{price * qty}"
    
    await send_whatsapp_interactive(phone, {
        "type": "button",
        "body": {"text": _truncate(body, 1024)},
        "action": {"buttons": buttons}
    })


# --- PAYMENT_METHOD_SELECTION ---
async def _convert_payment_methods(phone: str, agui: dict) -> None:
    """Convert payment method selection to reply buttons."""
    methods = agui.get("methods", [])
    amount = agui.get("amount", 0)

    if not methods:
        return

    buttons = []
    for method in methods[:3]:  # Max 3 reply buttons
        buttons.append({
            "type": "reply",
            "reply": {
                "id": _truncate(method.get("action", ""), 256),
                "title": _truncate(method.get("label", "Pay"), 20)
            }
        })

    body = f"💳 *Choose payment method*\nOrder total: ₹{amount}"
    for method in methods:
        desc = method.get("description", "")
        if desc:
            body += f"\n• {method.get('label', '')}: {desc}"

    await send_whatsapp_interactive(phone, {
        "type": "button",
        "body": {"text": _truncate(body, 1024)},
        "action": {"buttons": buttons}
    })
    LOGGER.info(f"Sent payment methods ({len(methods)} options) to {phone}")


# --- PAYMENT_LINK ---
async def _convert_payment_link(phone: str, agui: dict) -> None:
    """Convert payment link to a CTA URL button."""
    link = agui.get("payment_link", "")
    amount = agui.get("amount", 0)

    if not link:
        return

    await send_whatsapp_interactive(phone, {
        "type": "cta_url",
        "body": {"text": f"💳 Complete your payment of *₹{amount}*\n\nTap the button below to pay securely via Razorpay:"},
        "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": "Pay Now",
                "url": link
            }
        }
    })
    LOGGER.info(f"Sent payment link (₹{amount}) to {phone}")


# --- PAYMENT_SUCCESS ---
async def _convert_payment_success(phone: str, agui: dict) -> None:
    """Convert payment success to text + quick action buttons."""
    order_number = agui.get("order_number", "")
    amount = agui.get("amount", 0)
    order_type = agui.get("order_type", "")
    quick_replies = agui.get("quick_replies", [])

    text = f"✅ *Payment Successful!*\n\n"
    text += f"🧾 Order: *{order_number}*\n"
    text += f"💰 Amount: ₹{amount}\n"
    if order_type:
        text += f"📦 Type: {order_type.replace('_', ' ').title()}"

    if quick_replies and len(quick_replies) <= 3:
        buttons = []
        for qr in quick_replies[:3]:
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": _truncate(qr.get("action", ""), 256),
                    "title": _truncate(qr.get("label", ""), 20)
                }
            })
        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": _truncate(text, 1024)},
            "action": {"buttons": buttons}
        })
    else:
        await send_whatsapp_reply(phone, text)

    LOGGER.info(f"Sent payment success ({order_number}, ₹{amount}) to {phone}")


# --- QUICK_REPLIES ---
async def _convert_quick_replies(phone: str, agui: dict) -> None:
    """Convert quick replies to reply buttons (≤3) or list message (>3)."""
    replies = agui.get("replies", [])
    if not replies:
        return

    if len(replies) <= 3:
        buttons = []
        for r in replies[:3]:
            buttons.append({
                "type": "reply",
                "reply": {
                    "id": _truncate(r.get("action", r.get("label", "")), 256),
                    "title": _truncate(r.get("label", "Option"), 20)
                }
            })
        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": "Choose an option:"},
            "action": {"buttons": buttons}
        })
    else:
        rows = []
        for r in replies[:10]:
            rows.append({
                "id": _truncate(r.get("action", r.get("label", "")), 200),
                "title": _truncate(r.get("label", "Option"), 24),
                "description": ""
            })
        await send_whatsapp_interactive(phone, {
            "type": "list",
            "body": {"text": "Choose an option:"},
            "action": {
                "button": "View Options",
                "sections": [{"title": "Options", "rows": rows}]
            }
        })
    LOGGER.info(f"Sent quick replies ({len(replies)} options) to {phone}")


# --- ORDER_DATA ---
async def _convert_order_data(phone: str, agui: dict) -> None:
    """Convert order data to a formatted text message."""
    order_id = agui.get("order_id", "")
    items = agui.get("items", [])
    total = agui.get("total", 0)
    status = agui.get("status", "")
    order_type = agui.get("order_type", "")

    lines = ["📋 *Order Details*\n"]
    if order_id:
        lines.append(f"🆔 Order: {order_id}")
    if status:
        lines.append(f"📊 Status: {status.title()}")
    if order_type:
        lines.append(f"📦 Type: {order_type.replace('_', ' ').title()}")
    lines.append("")
    for i, item in enumerate(items, 1):
        name = item.get("name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        lines.append(f"{i}. {name} × {qty} — ₹{price * qty}")
    lines.append(f"\n💰 *Total: ₹{total}*")

    await send_whatsapp_reply(phone, "\n".join(lines))
    LOGGER.info(f"Sent order data ({order_id}) to {phone}")


# --- RECEIPT_LINK ---
async def _convert_receipt_link(phone: str, agui: dict) -> None:
    """Convert receipt link to a CTA URL button for PDF download."""
    order_number = agui.get("order_number", "")
    amount = agui.get("amount", 0)
    download_url = agui.get("download_url", "")
    items = agui.get("items", [])

    if not download_url:
        return

    # Build receipt summary text
    text = f"🧾 *Receipt — {order_number}*\n"
    if items:
        for item in items[:5]:
            name = item.get("name", "Item")
            qty = item.get("quantity", 1)
            price = item.get("price", 0)
            text += f"\n• {name} × {qty} — ₹{price * qty}"
        if len(items) > 5:
            text += f"\n  ... and {len(items) - 5} more items"
        text += "\n"
    text += f"\n💰 *Total: ₹{amount}*"
    text += "\n\nTap below to download your receipt:"

    await send_whatsapp_interactive(phone, {
        "type": "cta_url",
        "body": {"text": _truncate(text, 1024)},
        "action": {
            "name": "cta_url",
            "parameters": {
                "display_text": "Download Receipt",
                "url": download_url
            }
        }
    })
    LOGGER.info(f"Sent receipt link ({order_number}, ₹{amount}) to {phone}")


# ===================================================================
# WHATSAPP MESSAGE SENDERS
# ===================================================================
async def send_whatsapp_reply(to_number: str, message: str) -> bool:
    """
    Send text message to WhatsApp user via WhatsApp Business Cloud API.
    """
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Truncate if message too long (WhatsApp limit is 4096 chars)
    MAX_MESSAGE_LENGTH = 4096
    if len(message) > MAX_MESSAGE_LENGTH:
        LOGGER.warning(f"Message too long ({len(message)} chars), truncating to {MAX_MESSAGE_LENGTH}")
        message = message[:MAX_MESSAGE_LENGTH - 3] + "..."

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": True,
            "body": message
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            data = resp.json()

            if resp.status_code == 200:
                message_id = data.get("messages", [{}])[0].get("id", "unknown")
                LOGGER.info(f"WhatsApp message sent to {to_number} (msg_id: {message_id})")
                return True
            else:
                error = data.get("error", {})
                error_message = error.get("message", "Unknown error")
                LOGGER.error(f"Failed to send WhatsApp message to {to_number}: {error_message}")
                return False

    except httpx.TimeoutException:
        LOGGER.error(f"Timeout sending WhatsApp message to {to_number}")
        return False
    except Exception as e:
        LOGGER.error(f"Error sending WhatsApp message to {to_number}: {e}", exc_info=True)
        return False


async def send_whatsapp_interactive(to_number: str, interactive: dict) -> bool:
    """
    Send an interactive message (buttons, list, CTA URL) to WhatsApp user.

    WhatsApp interactive types:
    - "button": up to 3 reply buttons
    - "list": expandable list with sections and rows
    - "cta_url": call-to-action URL button
    """
    url = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "interactive",
        "interactive": interactive
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            data = resp.json()

            if resp.status_code == 200:
                message_id = data.get("messages", [{}])[0].get("id", "unknown")
                LOGGER.info(f"WhatsApp interactive sent to {to_number} (msg_id: {message_id})")
                return True
            else:
                error = data.get("error", {})
                error_code = error.get("code", 0)
                error_message = error.get("message", "Unknown error")
                LOGGER.error(
                    f"Failed to send interactive to {to_number}: [{error_code}] {error_message}"
                )
                # Fallback: send body text as plain message
                body_text = interactive.get("body", {}).get("text", "")
                if body_text:
                    LOGGER.info(f"Falling back to plain text for {to_number}")
                    return await send_whatsapp_reply(to_number, body_text)
                return False

    except httpx.TimeoutException:
        LOGGER.error(f"Timeout sending interactive to {to_number}")
        return False
    except Exception as e:
        LOGGER.error(f"Error sending interactive to {to_number}: {e}", exc_info=True)
        return False


# ===================================================================
# HEALTH CHECK & ADMIN ENDPOINTS
# ===================================================================
@app.get("/health")
async def health_check():
    """Health check endpoint to monitor service status"""
    return {
        "status": "ok",
        "service": "WhatsApp Bridge",
        "active_connections": len(ws_connections),
        "connected_phones": list(ws_connections.keys())
    }

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "WhatsApp Bridge",
        "status": "running",
        "version": "2.0.0",
        "endpoints": {
            "webhook_verify": "GET /webhook",
            "webhook_receive": "POST /webhook",
            "health": "GET /health"
        }
    }


# ===================================================================
# STARTUP & SHUTDOWN EVENTS
# ===================================================================
@app.on_event("startup")
async def startup_event():
    """Application startup"""
    LOGGER.info("WhatsApp Bridge started successfully")
    LOGGER.info(f"Chatbot WebSocket base URL: {CHATBOT_WS_BASE_URL}")
    LOGGER.info("WebSocket connections will be created on-demand per user")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown - close all WebSocket connections"""
    LOGGER.info("Shutting down WhatsApp Bridge...")
    LOGGER.info(f"Closing {len(ws_connections)} active WebSocket connections...")

    for phone, ws in list(ws_connections.items()):
        try:
            await ws.close()
            LOGGER.info(f"Closed WebSocket for {phone}")
        except Exception as e:
            LOGGER.error(f"Error closing WebSocket for {phone}: {e}")

    ws_connections.clear()
    LOGGER.info("Shutdown complete")
