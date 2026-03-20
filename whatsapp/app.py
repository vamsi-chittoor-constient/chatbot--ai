from fastapi import FastAPI, Request, Query, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
import asyncio
import websockets
import json
import os
from typing import Dict, Optional
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
WHATSAPP_API_VERSION = "v21.0"

# WhatsApp Catalog
WABA_ID = os.getenv("WABA_ID", "")
CATALOG_ID = os.getenv("CATALOG_ID", "1585007629445142")

# Menu page CTA URL (set to your public domain/ngrok URL)
MENU_PAGE_BASE_URL = os.getenv("MENU_PAGE_BASE_URL", "")
CHATBOT_API_BASE_URL = os.getenv("CHATBOT_API_BASE_URL", "http://chatbot-app:8000")

LOGGER.info("WhatsApp Bridge starting...")
LOGGER.info(f"Chatbot WebSocket base URL: {CHATBOT_WS_BASE_URL}")
LOGGER.info(f"Catalog ID: {CATALOG_ID or '(not set)'}")
LOGGER.info(f"Menu page base URL: {MENU_PAGE_BASE_URL or '(not set)'}")

# === Global persistent WebSocket connections (per user) ===
ws_connections: Dict[str, websockets.WebSocketClientProtocol] = {}
ws_lock = asyncio.Lock()
# Per-user locks to prevent concurrent recv() on the same WebSocket
_user_locks: Dict[str, asyncio.Lock] = {}
# Dedup: track processed WhatsApp message IDs to reject Meta retries
_processed_msg_ids: Dict[str, float] = {}   # msg_id → monotonic timestamp
_DEDUP_WINDOW = 300  # seconds (5 min)
# Background listeners for server-pushed events (e.g. PAYMENT_SUCCESS after Razorpay)
_bg_listeners: Dict[str, asyncio.Task] = {}
# Active contexts: phone -> {type, order_id, ts} (e.g. order_type_selection)
_active_contexts: Dict[str, dict] = {}


def _cleanup_user(phone: str):
    """Remove all per-user state when WebSocket closes."""
    ws_connections.pop(phone, None)
    _user_locks.pop(phone, None)
    _active_contexts.pop(phone, None)


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
        return PlainTextResponse(content=challenge)
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

                    # --- Handle catalog order (cart sent by customer) ---
                    if message_type == "order":
                        order_data = message.get("order", {})
                        product_items = order_data.get("product_items", [])
                        catalog_id = order_data.get("catalog_id", "")
                        LOGGER.info(f"Catalog order from {from_number}: {len(product_items)} items, catalog={catalog_id}")
                        asyncio.create_task(
                            _process_catalog_order(from_number, product_items, msg_id)
                        )
                        continue

                    # Extract user message based on message type
                    user_message = _extract_user_message(message, message_type)

                    if user_message is None:
                        LOGGER.warning(f"Unsupported message type: {message_type} from {from_number}")
                        if message_type in ("image", "audio", "video", "sticker", "document", "location", "contacts"):
                            asyncio.create_task(
                                send_whatsapp_reply(
                                    from_number,
                                    "I can only handle text and button messages right now. "
                                    "Please type your request instead! 😊"
                                )
                            )
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


async def _process_catalog_order(phone: str, product_items: list, msg_id: str):
    """Handle a catalog order (cart sent by customer from WhatsApp catalog).

    Converts catalog product_items to a chatbot-compatible direct_add_to_cart.
    Each product_item has: product_retailer_id, quantity, item_price, currency.
    The retailer_id = our menu_item_id (UUID).

    Steps:
    1. Look up item names from chatbot menu cache via internal API
    2. Send as direct_add_to_cart form_response (bypasses LLM, adds directly)
    3. Chatbot responds with cart update + AGUI events
    """
    try:
        if not product_items:
            await send_whatsapp_reply(phone, "Your cart appears to be empty. Please add items and try again.")
            return

        LOGGER.info(f"Catalog order from {phone}: {len(product_items)} items")

        # Look up item names from chatbot's menu API
        item_names = {}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{CHATBOT_API_BASE_URL}/api/v1/config/restaurant")
                if resp.status_code == 200:
                    menu_items = resp.json().get("menu", {}).get("items", [])
                    for mi in menu_items:
                        mid = mi.get("id", "")
                        if mid:
                            item_names[mid] = mi.get("name", "")
        except Exception as e:
            LOGGER.warning(f"Failed to fetch menu for name lookup: {e}")

        # Build items list with names for direct_add_to_cart
        cart_items = []
        summary_parts = []
        for pi in product_items:
            retailer_id = pi.get("product_retailer_id", "")
            qty = pi.get("quantity", 1)
            price_str = pi.get("item_price", "0")
            name = item_names.get(retailer_id, "")

            if name:
                cart_items.append({"name": name, "quantity": qty})
                summary_parts.append(f"{qty}x {name}")
            else:
                # Fallback: use retailer_id as identifier
                cart_items.append({"name": retailer_id, "quantity": qty})
                summary_parts.append(f"{qty}x item")
                LOGGER.warning(f"No name found for retailer_id {retailer_id}")

        if not cart_items:
            await send_whatsapp_reply(phone, "Could not process your order. Please try again.")
            return

        LOGGER.info(f"Catalog order resolved: {', '.join(summary_parts)} for {phone}")

        # Send as direct_add_to_cart — chatbot handles this without LLM
        form_response = {
            "type": "form_response",
            "form_type": "direct_add_to_cart",
            "data": {"items": cart_items}
        }
        await _send_form_response_to_chatbot(phone, form_response)

    except Exception as e:
        LOGGER.error(f"Error processing catalog order for {phone}: {e}", exc_info=True)
        await send_whatsapp_reply(phone, "Sorry, something went wrong processing your order. Please try again.")

    _start_bg_listener(phone)


async def _process_message(phone: str, user_message: str, msg_id: str):
    """Background task: forward message to chatbot, send response to WhatsApp."""
    try:
        # Intercept order type selection button replies
        if user_message in ("order_type_takeaway", "order_type_dinein"):
            flow_ctx = _active_contexts.pop(phone, {})
            order_id = flow_ctx.get("order_id", "")
            order_type = "take_away" if user_message == "order_type_takeaway" else "dine_in"
            form_response = {
                "type": "form_response",
                "form_type": "order_type_selection",
                "data": {"order_type": order_type, "order_id": order_id},
            }
            LOGGER.info(f"Order type selected: {order_type} (order={order_id}) for {phone}")
            await _send_form_response_to_chatbot(phone, form_response)
            _start_bg_listener(phone)
            return

        assistant_reply = await get_chatbot_reply(phone, user_message)

        if assistant_reply is not None:
            LOGGER.info(f"Sending response to WhatsApp: {assistant_reply[:50]}...")
            await send_whatsapp_reply(phone, assistant_reply)
        else:
            LOGGER.info(f"Response for {phone} handled via AGUI events")

    except Exception as e:
        LOGGER.error(f"Error processing message {msg_id} for {phone}: {e}", exc_info=True)
        await send_whatsapp_reply(phone, "Sorry, something went wrong. Please try again.")

    # Start background listener for server-pushed events (e.g. PAYMENT_SUCCESS)
    _start_bg_listener(phone)


def _cleanup_dedup():
    """Remove expired entries from the dedup map."""
    now = asyncio.get_event_loop().time()
    expired = [k for k, ts in _processed_msg_ids.items() if now - ts > _DEDUP_WINDOW]
    for k in expired:
        del _processed_msg_ids[k]


# ===================================================================
# BACKGROUND WEBSOCKET LISTENER (server-pushed events)
# ===================================================================
# After each request cycle, a background task listens on the WebSocket
# for events pushed by the server outside of a user message (e.g.
# PAYMENT_SUCCESS after Razorpay callback, receipts, notifications).
# The listener is cancelled when the next user message arrives.
# ===================================================================

async def _cancel_bg_listener(phone: str):
    """Cancel background listener before active message processing."""
    task = _bg_listeners.pop(phone, None)
    if task and not task.done():
        task.cancel()
        try:
            await task
        except (asyncio.CancelledError, Exception):
            pass


def _start_bg_listener(phone: str):
    """Start background listener for server-pushed events after response cycle."""
    old = _bg_listeners.pop(phone, None)
    if old and not old.done():
        old.cancel()
    _bg_listeners[phone] = asyncio.create_task(_bg_listen(phone))
    LOGGER.debug(f"Started background WS listener for {phone}")


async def _bg_listen(phone: str):
    """
    Background listener for server-pushed WebSocket events.
    Handles events like PAYMENT_SUCCESS that arrive outside user-initiated
    request cycles. Acquires the per-user lock briefly for each recv() so
    that an incoming user message (which cancels this task) can take over.

    QUICK_REPLIES are buffered (last-wins) and flushed on RUN_FINISHED,
    same as the main drain, to prevent duplicate quick reply messages.
    """
    user_lock = _user_locks.get(phone)
    if not user_lock:
        return

    text_chunks: list = []
    last_quick_replies = None  # Buffer QUICK_REPLIES, flush on RUN_FINISHED

    try:
        while True:
            async with user_lock:
                ws = ws_connections.get(phone)
                if not ws or not ws.open:
                    return

                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=5)
                except asyncio.TimeoutError:
                    continue

                LOGGER.debug(f"BG listener received for {phone}: {raw[:200]}...")

                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                msg_type = data.get("message_type", "")

                if msg_type == "agui_event":
                    agui_data = data.get("metadata", {}).get("agui", {})
                    agui_type = agui_data.get("type", "")

                    # Text streaming (in case server pushes text outside a request)
                    if agui_type == "TEXT_MESSAGE_CONTENT":
                        delta = agui_data.get("delta", "")
                        if delta:
                            text_chunks.append(delta)
                    elif agui_type == "TEXT_MESSAGE_END":
                        if text_chunks:
                            text = "".join(text_chunks).strip()
                            if text:
                                await send_whatsapp_reply(phone, text)
                            text_chunks.clear()
                    elif agui_type in ("RUN_FINISHED", "RUN_ERROR"):
                        # Flush any remaining text
                        if text_chunks:
                            text = "".join(text_chunks).strip()
                            if text:
                                await send_whatsapp_reply(phone, text)
                            text_chunks.clear()
                        # Flush buffered QUICK_REPLIES (only the last one)
                        if last_quick_replies:
                            await _convert_quick_replies(phone, last_quick_replies)
                            last_quick_replies = None

                    # QUICK_REPLIES: buffer, don't send (same dedup as main drain)
                    elif agui_type == "QUICK_REPLIES":
                        last_quick_replies = agui_data
                        LOGGER.debug(f"BG listener buffered QUICK_REPLIES for {phone}")

                    # Skip lifecycle noise
                    elif agui_type in (
                        "TEXT_MESSAGE_START", "RUN_STARTED",
                        "ACTIVITY_START", "ACTIVITY_END",
                        "TOOL_CALL_START", "TOOL_CALL_ARGS",
                        "TOOL_CALL_END", "TOOL_CALL_RESULT",
                        "STATE_SNAPSHOT", "STATE_DELTA",
                        "STEP_STARTED", "STEP_FINISHED",
                    ):
                        continue
                    else:
                        # Interactive push events: PAYMENT_SUCCESS, SEARCH_RESULTS, etc.
                        await _handle_agui_event(phone, agui_data)

                elif msg_type == "ai_response" and data.get("message"):
                    await send_whatsapp_reply(phone, data["message"])

                # Skip typing_indicator, system_message, etc.

    except asyncio.CancelledError:
        LOGGER.debug(f"Background listener cancelled for {phone}")
    except websockets.exceptions.ConnectionClosed:
        LOGGER.debug(f"Background listener: WS closed for {phone}")
        _cleanup_user(phone)
    except Exception as e:
        LOGGER.error(f"Background listener error for {phone}: {e}", exc_info=True)


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


_GREETING_WORDS = frozenset({
    "hi", "hey", "hello", "hii", "hiii", "yo", "sup",
    "namaste", "hola", "heya", "hiya", "howdy",
})


def _is_simple_greeting(text: str) -> bool:
    """Check if message is a simple greeting with no follow-up intent."""
    return text.strip().lower().rstrip("!.,? ") in _GREETING_WORDS


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

    # Cancel background listener (it holds user_lock intermittently)
    await _cancel_bg_listener(phone)

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
                        _cleanup_user(phone)
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
            # suppress_quick_replies=True prevents stale init quick replies leaking to user
            if is_new_connection:
                welcome_text, _, _ = await _drain_and_collect_response(
                    websocket, phone, timeout=15, suppress_quick_replies=True
                )
                if welcome_text:
                    LOGGER.info(f"Welcome message for {phone}: {welcome_text[:80]}...")
                    await send_whatsapp_reply(phone, welcome_text)

                # If the user's message is just a greeting ("Hi", "Hey", etc.)
                # skip forwarding it — the welcome already greeted them.
                # Avoids a redundant second greeting appearing in the chat.
                if _is_simple_greeting(user_message):
                    LOGGER.info(f"Skipping greeting '{user_message}' for {phone} (welcome already sent)")
                    return None

            # Purge stale events sitting in the WebSocket buffer from previous
            # request cycles (e.g. receipt/quick-replies the bg listener didn't read).
            if not is_new_connection:
                purged = 0
                while True:
                    try:
                        stale = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        purged += 1
                        LOGGER.debug(f"Purged stale WS message for {phone}: {stale[:120]}...")
                    except asyncio.TimeoutError:
                        break
                if purged:
                    LOGGER.info(f"Purged {purged} stale WS message(s) for {phone}")

            # Send user message to chatbot
            payload = {
                "message": user_message,
                "source": "whatsapp"
            }
            await websocket.send(json.dumps(payload))
            LOGGER.info(f"Sent to chatbot from {phone}: {user_message[:50]}...")

            # Collect response (text via AGUI streaming + interactive cards sent directly)
            text, any_sent, pending_qr = await _drain_and_collect_response(websocket, phone, timeout=45)

            # Send text FIRST, then quick replies — ensures correct ordering
            if text:
                await send_whatsapp_reply(phone, text)
                any_sent = True
            if pending_qr:
                await _convert_quick_replies(phone, pending_qr)
                LOGGER.info(f"Sent final QUICK_REPLIES to {phone}")
                any_sent = True

            if any_sent:
                return None  # Everything already sent in correct order
            else:
                return "Sorry, I couldn't get a response. Please try again."

    except asyncio.TimeoutError:
        LOGGER.error(f"Timeout waiting for response for {phone}")
        _cleanup_user(phone)
        return "Sorry, the assistant is taking too long to respond. Please try again."

    except websockets.exceptions.ConnectionClosed:
        LOGGER.error(f"WebSocket connection closed for {phone}")
        _cleanup_user(phone)
        return "Sorry, the connection was lost. Please try again."

    except Exception as e:
        LOGGER.error(f"Error communicating with chatbot for {phone}: {e}", exc_info=True)
        _cleanup_user(phone)
        return "Sorry, the assistant is currently unavailable. Please try again later."


async def _drain_and_collect_response(
    websocket: websockets.WebSocketClientProtocol,
    phone: str,
    timeout: float = 45,
    suppress_quick_replies: bool = False,
) -> tuple:
    """
    Read messages from the chatbot WebSocket and collect response.

    The chatbot streams responses via AGUI events:
    - TEXT_MESSAGE_CONTENT: text chunks (delta) — these ARE the AI text response
    - SEARCH_RESULTS, QUICK_REPLIES, etc.: interactive cards — sent to WhatsApp immediately
    - RUN_FINISHED: signals end of a processing stage (chatbot may have multiple stages)
    - ai_response: only for welcome messages and direct actions (legacy path)

    QUICK_REPLIES are buffered (last-wins) to deduplicate tool + orchestrator emissions.
    On RUN_FINISHED we don't break immediately — we shorten the deadline by 3s to allow
    follow-up processing stages (e.g. greeting stage + actual response stage).

    Returns:
        (text, any_sent) where:
        - text: remaining text to send as reply (or None if already sent)
        - any_sent: True if any messages were already sent to WhatsApp during processing
    """
    text_chunks = []       # TEXT_MESSAGE_CONTENT deltas (joined at TEXT_MESSAGE_END)
    direct_parts = []      # ai_response / system_message text (legacy path)
    any_sent = False       # Whether we already sent messages to WhatsApp
    last_quick_replies = None  # Buffer: only send the LAST QUICK_REPLIES (web UI replaces them)
    seen_content = False   # True once we see real content from THIS response (text/cards)
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
                seen_content = True
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
                    seen_content = True
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
                    seen_content = True
                    continue

                # Text stream start: just a marker, skip
                elif agui_type == "TEXT_MESSAGE_START":
                    seen_content = True
                    continue

                # RUN_FINISHED: chatbot may have follow-up processing stages.
                # Don't break — shorten the deadline so we wait briefly for more.
                elif agui_type == "RUN_FINISHED":
                    follow_up = asyncio.get_event_loop().time() + 3.0
                    deadline = min(deadline, follow_up)
                    LOGGER.debug(f"RUN_FINISHED for {phone}, waiting up to 3s for follow-up")
                    continue

                elif agui_type == "RUN_ERROR":
                    LOGGER.debug(f"RUN_ERROR for {phone}, stopping")
                    break

                # QUICK_REPLIES: buffer instead of sending (web UI replaces them;
                # tools emit one, then orchestrator emits another — only last matters)
                # Only accept quick replies AFTER we've seen real content from this
                # response — any arriving before are stale from the previous turn.
                elif agui_type == "QUICK_REPLIES":
                    if seen_content:
                        last_quick_replies = agui_data
                        LOGGER.debug(f"Buffered QUICK_REPLIES for {phone} (will send last one)")
                    else:
                        LOGGER.info(f"Discarded stale QUICK_REPLIES for {phone} (no content seen yet)")
                    continue

                # Other interactive events: convert and send to WhatsApp
                else:
                    sent = await _handle_agui_event(phone, agui_data)
                    if sent:
                        any_sent = True
                        seen_content = True
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

    # Build final text from any remaining pieces
    remaining_text = None
    if direct_parts:
        remaining_text = "\n\n".join(direct_parts)
    elif text_chunks:
        # TEXT_MESSAGE_END never arrived — flush remaining chunks
        text = "".join(text_chunks).strip()
        if text:
            remaining_text = text

    # Return buffered quick replies so caller can send AFTER text
    # (sending inside drain causes quick replies to appear before the text message)
    pending_qr = None
    if last_quick_replies and not suppress_quick_replies:
        pending_qr = last_quick_replies
    elif last_quick_replies and suppress_quick_replies:
        LOGGER.info(f"Suppressed welcome QUICK_REPLIES for {phone} (session init)")

    return (remaining_text, any_sent, pending_qr)


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
    elif event_type == "BOOKING_CONFIRMATION":
        await _convert_booking_confirmation(phone, agui)
        return True
    elif event_type == "ORDER_TYPE_SELECTION":
        await _convert_order_type_selection(phone, agui)
        return True
    elif event_type == "BOOKING_INTAKE_FORM":
        await _convert_booking_intake_form(phone, agui)
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



async def _send_form_response_to_chatbot(phone: str, form_response: dict) -> None:
    """Send a form_response to the chatbot via the existing WebSocket connection."""
    await _cancel_bg_listener(phone)

    if phone not in _user_locks:
        _user_locks[phone] = asyncio.Lock()

    try:
        async with _user_locks[phone]:
            ws = ws_connections.get(phone)
            if not ws or not ws.open:
                LOGGER.warning(f"No active WebSocket for {phone}, cannot send form_response")
                await send_whatsapp_reply(phone, "Session expired. Please send a message to restart.")
                return

            # Purge stale events
            purged = 0
            while True:
                try:
                    await asyncio.wait_for(ws.recv(), timeout=0.1)
                    purged += 1
                except asyncio.TimeoutError:
                    break
            if purged:
                LOGGER.debug(f"Purged {purged} stale WS messages before form_response for {phone}")

            # Send form_response JSON to chatbot
            await ws.send(json.dumps(form_response))
            LOGGER.info(f"Sent form_response to chatbot for {phone}: {form_response['form_type']}")

            # Drain response — chatbot emits CART_DATA and/or ai_response
            text, any_sent, pending_qr = await _drain_and_collect_response(ws, phone, timeout=15)
            if text:
                await send_whatsapp_reply(phone, text)
            if pending_qr:
                await _convert_quick_replies(phone, pending_qr)
            elif not any_sent and not text:
                LOGGER.warning(f"No response after form_response for {phone}")

    except Exception as e:
        LOGGER.error(f"Error sending form_response for {phone}: {e}", exc_info=True)
        await send_whatsapp_reply(phone, "Sorry, something went wrong. Please try again.")


# ===================================================================
# AGUI EVENT → WHATSAPP CONVERTERS
# ===================================================================

# --- SEARCH_RESULTS ---
async def _convert_search_results(phone: str, agui: dict) -> None:
    """Convert search results to CTA web page or reply buttons/list with availability indicators."""
    items = agui.get("items", [])
    if not items:
        return

    query = agui.get("query", "search")
    available = [i for i in items if i.get("is_available_now", True)]
    unavailable = [i for i in items if not i.get("is_available_now", True)]

    # ── 1. Catalog product_list: native product cards with add-to-cart ──
    if CATALOG_ID and available:
        try:
            product_items = [{"product_retailer_id": item.get("id", "")} for item in available[:30] if item.get("id")]
            if product_items:
                await send_whatsapp_interactive(phone, {
                    "type": "product_list",
                    "header": {"type": "text", "text": f"Results: {query}"},
                    "body": {"text": f"{len(available)} items found. Tap to view details and add to cart."},
                    "action": {
                        "catalog_id": CATALOG_ID,
                        "sections": [{"title": _truncate(f"Results for {query}", 24), "product_items": product_items[:30]}]
                    }
                })
                LOGGER.info(f"Sent product_list search results ({len(product_items)} items) to {phone}")
                return
        except Exception as e:
            LOGGER.warning(f"product_list failed for search, falling back: {e}")

    # ── 2. CTA URL fallback: full search results with add-to-cart ──
    search_body = f"\ud83d\udd0d *{len(items)} results for \"{query}\"*"
    if available:
        search_body += f"\n\u2705 {len(available)} available now"
    if unavailable:
        search_body += f"\n\ud83d\udd50 {len(unavailable)} available later"
    search_body += "\n\nTap below to view results and add to cart:"
    search_data = {"query": query, "items": items, "current_meal_period": agui.get("current_meal_period", "")}
    if await _send_cta_page(phone, "search", search_body, "View Results", search_data):
        return

    # ── Fallback: buttons/list ──
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
                    "description": _truncate(f"\u20b9{price} \u2022 {category}", 72),
                })
            sections.append({"title": f"\u2705 Available Now ({len(available)})", "rows": rows})

        if unavailable and len(sections) == 0:
            rows = []
            for item in unavailable[:10]:
                name = item.get("name", "Item")
                price = item.get("price", 0)
                meal_types = item.get("meal_types", [])
                meal_str = ", ".join(meal_types[:2]) if meal_types else "later"
                rows.append({
                    "id": _truncate(f"notify {name}", 200),
                    "title": _truncate(name, 24),
                    "description": _truncate(f"\u20b9{price} \u2022 {meal_str}", 72),
                })
            sections.append({"title": f"\ud83d\udd50 Available Later ({len(unavailable)})", "rows": rows})

        if sections:
            await send_whatsapp_interactive(phone, {
                "type": "list",
                "body": {"text": _truncate(f"\ud83d\udd0d Found {len(items)} items for *{query}*. Tap to add:", 1024)},
                "action": {
                    "button": "View Items",
                    "sections": sections,
                },
            })
    LOGGER.info(f"Sent search results ({len(items)} items, {len(available)} available) to {phone}")


# --- CTA URL Helper ---

async def _send_cta_page(phone: str, page_type: str, body_text: str, cta_label: str, data: dict = None) -> bool:
    """
    Generate a token, store page data in Redis, and send a CTA URL button.
    Returns True if sent successfully, False to fall back to non-CTA path.
    """
    if not MENU_PAGE_BASE_URL:
        return False
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{CHATBOT_API_BASE_URL}/api/v1/wa/token",
                json={"phone": phone, "page_type": page_type, "data": data or {}},
            )
            if resp.status_code != 200:
                LOGGER.warning(f"Failed to get {page_type} token: {resp.status_code}")
                return False
            token = resp.json().get("token", "")
            page_url = f"{MENU_PAGE_BASE_URL}/menu/{token}"

            await send_whatsapp_interactive(phone, {
                "type": "cta_url",
                "body": {"text": body_text},
                "action": {
                    "name": "cta_url",
                    "parameters": {
                        "display_text": _truncate(cta_label, 20),
                        "url": page_url,
                    },
                },
            })
            LOGGER.info(f"Sent {page_type} CTA URL to {phone}")
            return True
    except Exception as e:
        LOGGER.warning(f"CTA URL failed for {page_type}, falling back: {e}")
        return False


# --- MENU_DATA ---

async def _send_catalog_message(phone: str, body_text: str, thumbnail_retailer_id: str = "") -> bool:
    """Send a WhatsApp catalog_message. Returns True on success, False to fall back."""
    if not CATALOG_ID:
        return False
    try:
        # Pick a thumbnail product — use provided or first available
        thumb_id = thumbnail_retailer_id or ""
        payload = {
            "type": "catalog_message",
            "body": {"text": body_text},
            "action": {
                "name": "catalog_message",
                "parameters": {}
            }
        }
        if thumb_id:
            payload["action"]["parameters"]["thumbnail_product_retailer_id"] = thumb_id
        await send_whatsapp_interactive(phone, payload)
        LOGGER.info(f"Sent catalog_message to {phone}")
        return True
    except Exception as e:
        LOGGER.warning(f"catalog_message failed for {phone}, falling back: {e}")
        return False


async def _convert_menu_data(phone: str, agui: dict) -> None:
    """
    Convert menu to WhatsApp catalog message, CTA web page, or interactive list.
    Priority: Catalog > CTA > List
    """
    items = agui.get("items", [])
    categories = agui.get("categories", [])
    if not items:
        return

    # Defensive: categories might arrive as string instead of list
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",") if c.strip()] if categories else []
    LOGGER.info(f"MENU_DATA: {len(items)} items, categories({type(categories).__name__})={categories!r}")

    meal = agui.get("current_meal_period", "")
    meal_emoji = {"Breakfast": "\u2615", "Lunch": "\u2600\ufe0f", "Dinner": "\ud83c\udf19"}.get(meal, "\ud83c\udf7d\ufe0f")

    # ── 1. WhatsApp Catalog: native in-app menu browsing + cart ──
    catalog_body = f"{meal_emoji} *Menu*"
    if meal:
        catalog_body += f" \u2014 {meal} Time"
    catalog_body += f"\n{len(items)} items available"
    catalog_body += "\n\nBrowse our menu, add items to cart, and send your order!"
    # Use first item's ID as thumbnail
    first_item_id = items[0].get("id", "") if items else ""
    if await _send_catalog_message(phone, catalog_body, first_item_id):
        return

    # ── 2. CTA URL fallback: open mobile menu page in browser ──
    body = f"{meal_emoji} *Menu*"
    if meal:
        body += f" \u2014 {meal} Time"
    body += f"\n{len(items)} items available"
    body += "\n\nTap below to browse, select items & quantities:"
    if await _send_cta_page(phone, "menu", body, "Browse Full Menu"):
        return

    # ── Fallback: interactive list grouped by category (when MENU_PAGE_BASE_URL is not set) ──

    # Group items by category
    by_category: Dict[str, list] = {}
    for item in items:
        cat = item.get("category", "Other")
        by_category.setdefault(cat, []).append(item)

    cat_order = categories if categories else list(by_category.keys())
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
                "description": _truncate(f"\u20b9{price}", 72),
            })
        if rows:
            sections.append({"title": _truncate(cat, 24), "rows": rows})

    if not sections:
        return

    body = f"{meal_emoji} *Menu*"
    if meal:
        body += f" \u2014 {meal} Time"
    body += f"\n{len(items)} items available now. Tap to add:"

    await send_whatsapp_interactive(phone, {
        "type": "list",
        "body": {"text": _truncate(body, 1024)},
        "action": {"button": "Browse Menu", "sections": sections[:10]},
    })
    LOGGER.info(f"Sent full menu list ({len(items)} items, {len(sections)} sections) to {phone}")


# --- CART_DATA ---
async def _convert_cart_data(phone: str, agui: dict) -> None:
    """
    Convert cart to CTA web page or text summary + action buttons.
    """
    items = agui.get("items", [])
    total = agui.get("total", 0)
    packaging = agui.get("packaging_charge_per_item", 30)

    if not items:
        await send_whatsapp_reply(phone, "\ud83d\uded2 Your cart is empty.")
        return

    # ── CTA URL path: full cart management in web page ──
    cart_body = f"\ud83d\uded2 *Your Cart* \u2014 {len(items)} items, \u20b9{total}\n\nTap below to edit quantities, remove items, or checkout:"
    cart_data = {"items": items, "total": total, "packaging_charge_per_item": packaging}
    if await _send_cta_page(phone, "cart", cart_body, "Manage Cart", cart_data):
        return

    # ── Fallback: text summary + buttons ──
    lines = ["\ud83d\uded2 *Your Cart*\n"]
    for i, item in enumerate(items, 1):
        name = item.get("name") or item.get("item_name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        lines.append(f"{i}. {name} \u00d7 {qty} \u2014 \u20b9{price * qty}")

    lines.append(f"\n\ud83d\udce6 Packaging: \u20b9{packaging} \u00d7 {len(items)} = \u20b9{packaging * len(items)}")
    lines.append(f"\ud83d\udcb0 *Total: \u20b9{total}*")
    await send_whatsapp_reply(phone, "\n".join(lines))

    buttons = [
        {"type": "reply", "reply": {"id": "add more items", "title": "Add More"}},
        {"type": "reply", "reply": {"id": "checkout", "title": "Checkout"}},
    ]
    await send_whatsapp_interactive(phone, {
        "type": "button",
        "body": {"text": "What would you like to do?"},
        "action": {"buttons": buttons},
    })

    LOGGER.info(f"Sent cart ({len(items)} items, \u20b9{total}) to {phone}")


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
    """Convert quick replies to inline reply buttons, splitting >3 into multiple messages."""
    replies = agui.get("replies", [])
    if not replies:
        return

    if len(replies) > 10:
        # Safety valve: >10 options use list to avoid message spam
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
    else:
        # Split into chunks of 3 — each chunk becomes an inline button message
        chunks = [replies[i:i + 3] for i in range(0, len(replies), 3)]
        for chunk_idx, chunk in enumerate(chunks):
            buttons = []
            for r in chunk:
                buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": _truncate(r.get("action", r.get("label", "")), 256),
                        "title": _truncate(r.get("label", "Option"), 20)
                    }
                })
            body_text = "Choose an option:" if chunk_idx == 0 else "More options:"
            await send_whatsapp_interactive(phone, {
                "type": "button",
                "body": {"text": body_text},
                "action": {"buttons": buttons}
            })
    LOGGER.info(f"Sent quick replies ({len(replies)} options) to {phone}")


# --- ORDER_DATA ---
async def _convert_order_data(phone: str, agui: dict) -> None:
    """Convert order data to a CTA web page or formatted text message."""
    order_id = agui.get("order_id", "")
    items = agui.get("items", [])
    total = agui.get("total", 0)
    status = agui.get("status", "")
    order_type = agui.get("order_type", "")

    # ── CTA URL path: visual order card ──
    order_body = f"\ud83d\udccb *Order #{order_id}*"
    if status:
        order_body += f" \u2014 {status.title()}"
    order_body += f"\n{len(items)} items \u2022 \u20b9{total}"
    order_body += "\n\nTap below to view full order details:"
    order_data = {"order_id": order_id, "items": items, "total": total, "status": status, "order_type": order_type}
    if await _send_cta_page(phone, "order", order_body, "View Order", order_data):
        return

    # ── Fallback: text message ──
    lines = ["\ud83d\udccb *Order Details*\n"]
    if order_id:
        lines.append(f"\ud83c\udd94 Order: {order_id}")
    if status:
        lines.append(f"\ud83d\udcca Status: {status.title()}")
    if order_type:
        lines.append(f"\ud83d\udce6 Type: {order_type.replace('_', ' ').title()}")
    lines.append("")
    for i, item in enumerate(items, 1):
        name = item.get("name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        lines.append(f"{i}. {name} \u00d7 {qty} \u2014 \u20b9{price * qty}")
    lines.append(f"\n\ud83d\udcb0 *Total: \u20b9{total}*")

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

    # Fix relative URLs — prepend public base URL
    if download_url.startswith("/"):
        base = MENU_PAGE_BASE_URL or CHATBOT_API_BASE_URL
        download_url = f"{base.rstrip('/')}{download_url}"

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


# --- BOOKING_CONFIRMATION ---
async def _convert_booking_confirmation(phone: str, agui: dict) -> None:
    """Convert booking confirmation to text summary + quick action buttons."""
    code = agui.get("confirmation_code", "")
    guest = agui.get("guest_name", "Guest")
    party = agui.get("party_size", 0)
    date_str = agui.get("booking_date", "")
    time_str = agui.get("booking_time", "")
    table = agui.get("table_number", "")
    location = agui.get("table_location", "")

    text = "*Table Reservation Confirmed!*\n\n"
    text += f"Confirmation Code: *{code}*\n"
    text += f"Guest: {guest}\n"
    text += f"Party Size: {party} guests\n"
    text += f"Date: {date_str}\n"
    text += f"Time: {time_str}\n"
    text += f"Table: {table}"
    if location:
        text += f" ({location})"

    quick_replies = agui.get("quick_replies", [])
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

    LOGGER.info(f"Sent booking confirmation ({code}) to {phone}")


# --- ORDER_TYPE_SELECTION ---
async def _convert_order_type_selection(phone: str, agui: dict) -> None:
    """Convert order type selection to Dine-in / Takeaway buttons."""
    order_id = agui.get("order_id", "")
    subtotal = agui.get("subtotal", 0)
    item_count = agui.get("item_count", 0)
    summary = agui.get("items_summary", "")

    body = f"🛒 *Order Ready!*\n"
    if summary:
        body += f"{summary}\n"
    body += f"Subtotal: ₹{subtotal:.0f} ({item_count} items)\n\n"
    body += "How would you like your order?"

    # Store order_id so button response can include it
    _active_contexts[phone] = {
        "type": "order_type_selection",
        "order_id": order_id,
        "ts": asyncio.get_event_loop().time(),
    }

    buttons = [
        {"type": "reply", "reply": {"id": "order_type_takeaway", "title": "🥡 Takeaway"}},
        {"type": "reply", "reply": {"id": "order_type_dinein", "title": "🍽️ Dine In"}},
    ]
    await send_whatsapp_interactive(phone, {
        "type": "button",
        "body": {"text": _truncate(body, 1024)},
        "action": {"buttons": buttons}
    })
    LOGGER.info(f"Sent order type selection (order={order_id}) to {phone}")


# --- BOOKING_INTAKE_FORM ---
async def _convert_booking_intake_form(phone: str, agui: dict) -> None:
    """
    Convert booking intake form to WhatsApp Flow (if available) or text prompts.

    The AGUI event contains:
      - availability: {date_str: {slots: {time_label: {available, max_party, tables_free}}}}
      - party_sizes: [1, 2, 3, ...]
      - max_party_size: int
    """
    availability = agui.get("availability", {})
    party_sizes = agui.get("party_sizes", list(range(1, 9)))
    max_party = agui.get("max_party_size", 8)

    # Text prompt — user types booking details
    dates_preview = []
    for date_str, date_info in sorted(availability.items())[:5]:
        slots = date_info.get("slots", {})
        available_count = sum(1 for s in slots.values() if s.get("available", False))
        if available_count > 0:
            try:
                from datetime import datetime as _dt
                d = _dt.strptime(date_str, "%Y-%m-%d")
                display = d.strftime("%a, %b %d")
            except Exception:
                display = date_str
            dates_preview.append(f"  • {display} — {available_count} slots")

    text = "📅 *Book a Table*\n\n"
    if dates_preview:
        text += "Available dates:\n" + "\n".join(dates_preview) + "\n\n"
    text += (
        f"Party sizes: 1-{max_party} guests\n\n"
        "Please reply with your booking details, e.g.:\n"
        '*"Book a table for 4 on March 20 at 7 PM"*'
    )
    await send_whatsapp_reply(phone, text)
    LOGGER.info(f"Sent booking text prompt ({len(dates_preview)} dates) to {phone}")
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
@app.post("/internal/add-to-cart")
async def internal_add_to_cart(request: Request):
    """Legacy: add-to-cart endpoint. Redirects to unified wa-action."""
    body = await request.json()
    body["action"] = "add_to_cart"
    body["items"] = body.get("items", [])
    # Forward to unified handler
    from starlette.requests import Request as StarletteRequest
    return await internal_wa_action_handler(body)


@app.post("/internal/wa-action")
async def internal_wa_action(request: Request):
    """Unified internal endpoint for all WhatsApp web page actions."""
    body = await request.json()
    return await internal_wa_action_handler(body)


async def internal_wa_action_handler(body: dict):
    """
    Handle all actions from WhatsApp web pages:
    - add_to_cart: Add items to cart via form_response
    - update_cart: Update quantities / remove items
    - checkout: Trigger checkout flow
    - add_more: Send "show menu" to reopen menu
    - message: Send arbitrary text message to chatbot
    """
    try:
        phone = body.get("phone", "")
        action = body.get("action", "")

        if not phone:
            return JSONResponse(status_code=400, content={"error": "phone required"})

        LOGGER.info(f"Internal wa-action for {phone}: {action}")

        # Helper: ensure WS connection exists
        async def _ensure_session_and_send(message: str):
            ws = ws_connections.get(phone)
            if not ws or not ws.open:
                reply = await get_chatbot_reply(phone, message)
                if reply:
                    await send_whatsapp_reply(phone, reply)
                _start_bg_listener(phone)
                return {"success": True, "method": "new_session"}
            return None

        # Helper: send form_response through existing WS
        async def _send_form(form_type: str, data: dict):
            form_response = {"type": "form_response", "form_type": form_type, "data": data}
            ws = ws_connections.get(phone)
            if not ws or not ws.open:
                # Fallback: send as text
                return await _ensure_session_and_send(str(data))
            await _send_form_response_to_chatbot(phone, form_response)
            _start_bg_listener(phone)
            return {"success": True, "method": "form_response"}

        if action == "add_to_cart":
            items = body.get("items", [])
            if not items:
                return JSONResponse(status_code=400, content={"error": "items required"})
            items_payload = [{"name": it["name"], "quantity": it.get("quantity", 1)} for it in items]
            item_summary = ", ".join(f"{it.get('quantity', 1)}x {it['name']}" for it in items)
            LOGGER.info(f"Add to cart for {phone}: {item_summary}")

            fallback = await _ensure_session_and_send(f"add to cart: {item_summary}")
            if fallback:
                return fallback
            return await _send_form("direct_add_to_cart", {"items": items_payload})

        elif action == "update_cart":
            updates = body.get("updates", [])
            removes = body.get("removes", [])
            # Process removes
            for name in removes:
                await _send_form("direct_remove_from_cart", {"item_name": name})
            # Process quantity updates
            for upd in updates:
                await _send_form("direct_update_cart", {
                    "item_name": upd.get("item_name", ""),
                    "quantity": upd.get("quantity", 1),
                })
            return {"success": True}

        elif action == "checkout":
            fallback = await _ensure_session_and_send("I want to checkout")
            if fallback:
                return fallback
            # Send checkout as a regular message
            reply = await get_chatbot_reply(phone, "checkout")
            if reply:
                await send_whatsapp_reply(phone, reply)
            _start_bg_listener(phone)
            return {"success": True}

        elif action == "add_more":
            fallback = await _ensure_session_and_send("show menu")
            if fallback:
                return fallback
            reply = await get_chatbot_reply(phone, "show menu")
            if reply:
                await send_whatsapp_reply(phone, reply)
            _start_bg_listener(phone)
            return {"success": True}

        elif action == "message":
            message = body.get("message", "")
            if not message:
                return JSONResponse(status_code=400, content={"error": "message required"})
            reply = await get_chatbot_reply(phone, message)
            if reply:
                await send_whatsapp_reply(phone, reply)
            _start_bg_listener(phone)
            return {"success": True}

        else:
            return JSONResponse(status_code=400, content={"error": f"Unknown action: {action}"})

    except Exception as e:
        LOGGER.error(f"Internal wa-action error: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


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
    """Application shutdown - cancel listeners and close all WebSocket connections"""
    LOGGER.info("Shutting down WhatsApp Bridge...")

    # Cancel all background listeners
    for phone in list(_bg_listeners):
        await _cancel_bg_listener(phone)

    LOGGER.info(f"Closing {len(ws_connections)} active WebSocket connections...")
    for phone, ws in list(ws_connections.items()):
        try:
            await ws.close()
            LOGGER.info(f"Closed WebSocket for {phone}")
        except Exception as e:
            LOGGER.error(f"Error closing WebSocket for {phone}: {e}")

    ws_connections.clear()
    LOGGER.info("Shutdown complete")
