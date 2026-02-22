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
WHATSAPP_API_VERSION = "v21.0"

# WhatsApp Flows
# FLOW_PROVISION_MODE: "auto" (default) = provision on startup, "manual" = use .env IDs only
WABA_ID = os.getenv("WABA_ID", "")
FLOW_PROVISION_MODE = os.getenv("FLOW_PROVISION_MODE", "auto").strip().lower()
FLOW_SELECT_ITEMS_ID = os.getenv("FLOW_SELECT_ITEMS_ID", "")
FLOW_SELECT_ITEMS_QTY_ID = os.getenv("FLOW_SELECT_ITEMS_QTY_ID", "")
FLOW_MANAGE_CART_ID = os.getenv("FLOW_MANAGE_CART_ID", "")

LOGGER.info("WhatsApp Bridge starting...")
LOGGER.info(f"Chatbot WebSocket base URL: {CHATBOT_WS_BASE_URL}")
LOGGER.info(f"Flow provision mode: {FLOW_PROVISION_MODE}")


@app.on_event("startup")
async def _auto_provision_flows():
    """Auto-provision WhatsApp Flows on server startup when FLOW_PROVISION_MODE=auto.
    Checks existing flows by name, creates missing ones, uploads JSON, publishes drafts.
    In manual mode, flow IDs must be set in .env.
    """
    global FLOW_SELECT_ITEMS_ID, FLOW_SELECT_ITEMS_QTY_ID, FLOW_MANAGE_CART_ID

    if FLOW_PROVISION_MODE != "auto":
        LOGGER.info("FLOW_PROVISION_MODE=manual — using .env flow IDs")
        return

    if not WABA_ID:
        LOGGER.info("WABA_ID not set — skipping flow auto-provision")
        return

    try:
        from manage_flows import auto_provision_flows
        LOGGER.info("Auto-provisioning WhatsApp Flows...")
        flow_ids = await asyncio.to_thread(auto_provision_flows)

        if "select_items" in flow_ids:
            FLOW_SELECT_ITEMS_ID = flow_ids["select_items"]
            LOGGER.info(f"Provisioned select_items: {FLOW_SELECT_ITEMS_ID}")
        if "select_items_qty" in flow_ids:
            FLOW_SELECT_ITEMS_QTY_ID = flow_ids["select_items_qty"]
            LOGGER.info(f"Provisioned select_items_qty: {FLOW_SELECT_ITEMS_QTY_ID}")
        if "manage_cart" in flow_ids:
            FLOW_MANAGE_CART_ID = flow_ids["manage_cart"]
            LOGGER.info(f"Provisioned manage_cart: {FLOW_MANAGE_CART_ID}")

        LOGGER.info("Flow auto-provision complete")
    except Exception as e:
        LOGGER.error(f"Flow auto-provision failed (non-fatal): {e}", exc_info=True)

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
# Active Flow contexts: phone -> {type, items/item_names, flow_token, ts}
# Used to correlate nfm_reply responses with the flow that triggered them
_active_flows: Dict[str, dict] = {}
_FLOW_CONTEXT_TTL = 1800  # 30 min


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
        # Intercept WhatsApp Flow responses (nfm_reply sentinel)
        if user_message.startswith("__FLOW_RESPONSE__"):
            response_json_str = user_message[len("__FLOW_RESPONSE__"):]
            try:
                response_data = json.loads(response_json_str)
            except json.JSONDecodeError:
                LOGGER.error(f"Failed to parse flow response for {phone}")
                await send_whatsapp_reply(phone, "Sorry, something went wrong. Please try again.")
                _start_bg_listener(phone)
                return
            await _handle_flow_response(phone, response_data)
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
    """Remove expired entries from the dedup map and stale flow contexts."""
    now = asyncio.get_event_loop().time()
    expired = [k for k, ts in _processed_msg_ids.items() if now - ts > _DEDUP_WINDOW]
    for k in expired:
        del _processed_msg_ids[k]
    # Clean up abandoned flow contexts (>30 min old)
    stale = [k for k, v in _active_flows.items() if now - v.get("ts", 0) > _FLOW_CONTEXT_TTL]
    for k in stale:
        del _active_flows[k]


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
        ws_connections.pop(phone, None)
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

        elif reply_type == "nfm_reply":
            # WhatsApp Flow completion — extract structured response
            nfm = interactive.get("nfm_reply", {})
            response_json_str = nfm.get("response_json", "{}")
            try:
                response_data = json.loads(response_json_str)
            except json.JSONDecodeError:
                LOGGER.warning(f"Invalid nfm_reply JSON: {response_json_str[:200]}")
                return None
            LOGGER.info(f"Flow response (nfm_reply): {json.dumps(response_data)[:200]}")
            # Return sentinel so _process_message routes to flow handler
            return f"__FLOW_RESPONSE__{json.dumps(response_data)}"

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


# ===================================================================
# WHATSAPP FLOWS — send flow messages & handle nfm_reply responses
# ===================================================================

async def send_whatsapp_flow_message(
    to_number: str,
    flow_id: str,
    flow_cta: str,
    body_text: str,
    screen_id: str,
    flow_data: dict,
    flow_token: str = None,
    header_text: str = None,
    footer_text: str = None,
) -> bool:
    """Send a WhatsApp Flow interactive message (navigate mode)."""
    import uuid as _uuid
    if flow_token is None:
        flow_token = str(_uuid.uuid4())

    interactive = {
        "type": "flow",
        "body": {"text": _truncate(body_text, 1024)},
        "action": {
            "name": "flow",
            "parameters": {
                "flow_message_version": "3",
                "flow_id": flow_id,
                "flow_cta": _truncate(flow_cta, 20),
                "flow_token": flow_token,
                "flow_action": "navigate",
                "flow_action_payload": {
                    "screen": screen_id,
                    "data": flow_data,
                },
            },
        },
    }
    if header_text:
        interactive["header"] = {"type": "text", "text": _truncate(header_text, 60)}
    if footer_text:
        interactive["footer"] = {"text": _truncate(footer_text, 60)}

    return await send_whatsapp_interactive(to_number, interactive)


async def _send_item_selection_flow(
    phone: str, category_name: str, items: list, meal: str = ""
) -> None:
    """Send Item Selection Flow with CheckboxGroup for a set of menu items."""
    import uuid as _uuid

    flow_items = []
    for item in items[:20]:  # CheckboxGroup max 20 items
        name = item.get("name", "Item")
        price = item.get("price", 0)
        flow_items.append({
            "id": name,
            "title": _truncate(f"{name} - \u20b9{price}", 30),
        })

    flow_data = {
        "screen_title": _truncate(category_name, 80),
        "items": flow_items,
    }

    meal_emoji = {"Breakfast": "\u2615", "Lunch": "\u2600\ufe0f", "Dinner": "\ud83c\udf19"}.get(meal, "\ud83c\udf7d\ufe0f")
    body = f"{meal_emoji} *{category_name}*\n{len(flow_items)} items available. Select to add:"

    flow_token = f"select_{phone}_{_uuid.uuid4().hex[:8]}"
    _active_flows[phone] = {
        "type": "select_items",
        "category": category_name,
        "items": {it["id"]: it for it in flow_items},
        "flow_token": flow_token,
        "ts": asyncio.get_event_loop().time(),
    }

    await send_whatsapp_flow_message(
        to_number=phone,
        flow_id=FLOW_SELECT_ITEMS_ID,
        flow_cta="Select Items",
        body_text=body,
        screen_id="SELECT_ITEMS",
        flow_data=flow_data,
        flow_token=flow_token,
    )
    LOGGER.info(f"Sent item selection flow ({len(flow_items)} items, {category_name}) to {phone}")


async def _send_item_selection_qty_flow(
    phone: str, category_name: str, items: list, meal: str = ""
) -> None:
    """Send Item Selection + Qty Flow: per-item TextInput (number) for quantity entry."""
    import uuid as _uuid

    flow_data: Dict[str, Any] = {
        "screen_title": _truncate(category_name, 80),
    }

    item_names: List[str] = []
    for idx in range(10):
        if idx < len(items):
            item = items[idx]
            name = item.get("name", "Item")
            price = item.get("price", 0)
            flow_data[f"item_{idx}_visible"] = True
            flow_data[f"item_{idx}_label"] = _truncate(f"{name} — \u20b9{price}", 80)
            item_names.append(name)
        else:
            flow_data[f"item_{idx}_visible"] = False
            flow_data[f"item_{idx}_label"] = "-"

    meal_emoji = {"Breakfast": "\u2615", "Lunch": "\u2600\ufe0f", "Dinner": "\ud83c\udf19"}.get(meal, "\ud83c\udf7d\ufe0f")
    body = f"{meal_emoji} *{category_name}*\n{len(item_names)} items. Enter qty to add:"

    flow_token = f"selqty_{phone}_{_uuid.uuid4().hex[:8]}"
    _active_flows[phone] = {
        "type": "select_items_qty",
        "category": category_name,
        "item_names": item_names,
        "flow_token": flow_token,
        "ts": asyncio.get_event_loop().time(),
    }

    await send_whatsapp_flow_message(
        to_number=phone,
        flow_id=FLOW_SELECT_ITEMS_QTY_ID,
        flow_cta="Select Items",
        body_text=body,
        screen_id="SELECT_ITEMS_QTY",
        flow_data=flow_data,
        flow_token=flow_token,
    )
    LOGGER.info(f"Sent item selection+qty flow ({len(item_names)} items, {category_name}) to {phone}")


async def _send_cart_management_flow(phone: str, items: list, total: float) -> None:
    """Send Cart Management Flow with per-item TextInput for quantity entry."""
    import uuid as _uuid

    flow_data: Dict[str, Any] = {
        "cart_summary": f"{len(items)} items \u2014 \u20b9{total:.0f}",
    }

    item_names: List[str] = []
    item_qtys: List[int] = []
    for idx in range(10):
        if idx < len(items):
            item = items[idx]
            name = item.get("name") or item.get("item_name", "Item")
            price = item.get("price", 0)
            qty = item.get("quantity", 1)
            flow_data[f"item_{idx}_visible"] = True
            flow_data[f"item_{idx}_label"] = _truncate(f"{name} \u2014 \u20b9{price} each (now: {qty})", 80)
            flow_data[f"item_{idx}_qty"] = qty
            item_names.append(name)
            item_qtys.append(qty)
        else:
            flow_data[f"item_{idx}_visible"] = False
            flow_data[f"item_{idx}_label"] = "-"
            flow_data[f"item_{idx}_qty"] = 0

    flow_token = f"cart_{phone}_{_uuid.uuid4().hex[:8]}"
    _active_flows[phone] = {
        "type": "manage_cart",
        "item_names": item_names,
        "item_qtys": item_qtys,
        "flow_token": flow_token,
        "ts": asyncio.get_event_loop().time(),
    }

    await send_whatsapp_flow_message(
        to_number=phone,
        flow_id=FLOW_MANAGE_CART_ID,
        flow_cta="Modify Cart",
        body_text="Tap to adjust quantities or remove items:",
        screen_id="MANAGE_CART",
        flow_data=flow_data,
        flow_token=flow_token,
    )
    LOGGER.info(f"Sent cart management flow ({len(items)} items) to {phone}")


async def _handle_flow_response(phone: str, response_data: dict) -> None:
    """Process a WhatsApp Flow nfm_reply: convert to form_response and send to chatbot."""
    flow_type = response_data.get("flow_type", "")
    flow_ctx = _active_flows.pop(phone, {})

    if flow_type == "select_items":
        selected_items = response_data.get("selected_items", [])
        if not selected_items:
            await send_whatsapp_reply(phone, "No items selected.")
            return

        items_payload = [{"name": name, "quantity": 1} for name in selected_items]
        form_response = {
            "type": "form_response",
            "form_type": "direct_add_to_cart",
            "data": {"items": items_payload},
        }
        LOGGER.info(f"Flow select_items -> direct_add_to_cart: {len(items_payload)} items for {phone}")
        await _send_form_response_to_chatbot(phone, form_response)

    elif flow_type == "manage_cart":
        item_names = flow_ctx.get("item_names", [])
        if not item_names:
            LOGGER.warning(f"No flow context for manage_cart from {phone}")
            await send_whatsapp_reply(phone, "Session expired. Please view your cart again.")
            return

        item_qtys = flow_ctx.get("item_qtys", [])
        updates = []
        removes = []
        for idx, name in enumerate(item_names):
            new_qty_str = response_data.get(f"qty_{idx}", "")
            if not new_qty_str:
                continue
            try:
                new_qty = int(new_qty_str)
            except (ValueError, TypeError):
                continue
            # Skip if quantity unchanged
            old_qty = item_qtys[idx] if idx < len(item_qtys) else 0
            if new_qty == old_qty:
                continue
            if new_qty <= 0:
                removes.append(name)
            else:
                updates.append({"item_name": name, "quantity": new_qty})

        # Process removes first, then updates
        for name in removes:
            fr = {
                "type": "form_response",
                "form_type": "direct_remove_from_cart",
                "data": {"item_name": name},
            }
            LOGGER.info(f"Flow manage_cart -> remove: {name} for {phone}")
            await _send_form_response_to_chatbot(phone, fr)

        for update in updates:
            fr = {
                "type": "form_response",
                "form_type": "direct_update_cart",
                "data": update,
            }
            LOGGER.info(f"Flow manage_cart -> update: {update['item_name']}={update['quantity']} for {phone}")
            await _send_form_response_to_chatbot(phone, fr)

        if not removes and not updates:
            await send_whatsapp_reply(phone, "Cart unchanged.")

    elif flow_type == "select_items_qty":
        item_names = flow_ctx.get("item_names", [])
        if not item_names:
            LOGGER.warning(f"No flow context for select_items_qty from {phone}")
            await send_whatsapp_reply(phone, "Session expired. Please try again.")
            return

        items_payload = []
        for idx, name in enumerate(item_names):
            qty_str = response_data.get(f"qty_{idx}", "")
            if not qty_str:
                continue
            try:
                qty = int(qty_str)
            except (ValueError, TypeError):
                continue
            if qty > 0:
                items_payload.append({"name": name, "quantity": qty})

        if not items_payload:
            await send_whatsapp_reply(phone, "No items selected. Enter a quantity to add items.")
            return

        form_response = {
            "type": "form_response",
            "form_type": "direct_add_to_cart",
            "data": {"items": items_payload},
        }
        LOGGER.info(f"Flow select_items_qty -> direct_add_to_cart: {len(items_payload)} items for {phone}")
        await _send_form_response_to_chatbot(phone, form_response)

    else:
        LOGGER.warning(f"Unknown flow_type in nfm_reply: {flow_type} for {phone}")
        await send_whatsapp_reply(phone, "Thanks for your selection!")


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
            text, any_sent = await _drain_and_collect_response(ws, phone, timeout=15)
            if text:
                await send_whatsapp_reply(phone, text)
            elif not any_sent:
                LOGGER.warning(f"No response after form_response for {phone}")

    except Exception as e:
        LOGGER.error(f"Error sending form_response for {phone}: {e}", exc_info=True)
        await send_whatsapp_reply(phone, "Sorry, something went wrong. Please try again.")


# ===================================================================
# AGUI EVENT → WHATSAPP CONVERTERS
# ===================================================================

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
    elif (FLOW_SELECT_ITEMS_QTY_ID or FLOW_SELECT_ITEMS_ID) and len(available) >= 4:
        # Use Flow for multi-select when there are enough available items
        if unavailable:
            note_lines = ["\ud83d\udd50 *Also available later:*"]
            for item in unavailable[:5]:
                name = item.get("name", "Item")
                meals = ", ".join(item.get("meal_types", ["later"])[:2])
                note_lines.append(f"  - {name} ({meals})")
            await send_whatsapp_reply(phone, "\n".join(note_lines))
        if FLOW_SELECT_ITEMS_QTY_ID and len(available) <= 10:
            await _send_item_selection_qty_flow(phone, f"Results: {query}", available, "")
        else:
            await _send_item_selection_flow(phone, f"Results: {query}", available, "")

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


# --- MENU_DATA ---
MENU_DIRECT_THRESHOLD = 100
MENU_CATEGORY_BUTTON_THRESHOLD = 9  # Max categories to show as inline buttons (3 per message)

async def _convert_menu_data(phone: str, agui: dict) -> None:
    """
    Convert menu to WhatsApp interactive messages.

    With Flows configured:
    - Single category or ≤20 items → Item Selection Flow (multi-select CheckboxGroup)
    - Multiple categories ≤9 → inline category buttons → user taps → Flow for that category
    - Multiple categories >9 → category list picker → user taps → Flow for that category

    Without Flows (graceful degradation):
    - Small menu (≤100 items): list message grouped by category
    - Large menu (>100 items): category picker list
    """
    items = agui.get("items", [])
    categories = agui.get("categories", [])
    if not items:
        return

    # Defensive: categories might arrive as string instead of list
    if isinstance(categories, str):
        categories = [c.strip() for c in categories.split(",") if c.strip()] if categories else []
    LOGGER.info(f"MENU_DATA: {len(items)} items, categories({type(categories).__name__})={categories!r}")

    # Group items by category
    by_category: Dict[str, list] = {}
    for item in items:
        cat = item.get("category", "Other")
        by_category.setdefault(cat, []).append(item)

    cat_order = categories if categories else list(by_category.keys())
    meal = agui.get("current_meal_period", "")
    meal_emoji = {"Breakfast": "\u2615", "Lunch": "\u2600\ufe0f", "Dinner": "\ud83c\udf19"}.get(meal, "\ud83c\udf7d\ufe0f")

    # ── Flow path: single category or small item set → Item Selection Flow ──
    _has_any_select_flow = FLOW_SELECT_ITEMS_QTY_ID or FLOW_SELECT_ITEMS_ID
    if _has_any_select_flow and (len(cat_order) == 1 or len(items) <= 20):
        cat_name = cat_order[0] if len(cat_order) == 1 else "Menu"
        if FLOW_SELECT_ITEMS_QTY_ID and len(items) <= 10:
            await _send_item_selection_qty_flow(phone, cat_name, items, meal)
        else:
            await _send_item_selection_flow(phone, cat_name, items, meal)
        return

    # ── Flow path: multiple categories → show categories as inline buttons ──
    if _has_any_select_flow and len(cat_order) <= MENU_CATEGORY_BUTTON_THRESHOLD:
        body = f"{meal_emoji} *Menu*"
        if meal:
            body += f" \u2014 {meal} Time"
        body += f"\n{len(items)} items across {len(cat_order)} categories.\nTap a category to browse:"
        await send_whatsapp_reply(phone, body)

        chunks = [cat_order[i:i + 3] for i in range(0, len(cat_order), 3)]
        for chunk in chunks:
            buttons = []
            for cat in chunk:
                count = len(by_category.get(cat, []))
                buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": _truncate(f"show {cat} menu", 256),
                        "title": _truncate(f"{cat} ({count})", 20),
                    },
                })
            await send_whatsapp_interactive(phone, {
                "type": "button",
                "body": {"text": "Pick a category:"},
                "action": {"buttons": buttons},
            })
        LOGGER.info(f"Sent category buttons ({len(cat_order)} categories) to {phone}")
        return

    # ── Fallback / no-Flow path ──
    if len(items) <= MENU_DIRECT_THRESHOLD:
        # Small menu: show all items grouped by category in one list
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
        LOGGER.info(f"Sent full menu ({len(items)} items, {len(sections)} sections) to {phone}")

    else:
        # Large menu: show categories as filter options
        rows = []
        for cat in cat_order[:10]:
            count = len(by_category.get(cat, []))
            rows.append({
                "id": _truncate(f"show {cat} menu", 200),
                "title": _truncate(cat, 24),
                "description": _truncate(f"{count} items", 72),
            })

        if not rows:
            return

        body = f"{meal_emoji} *Menu*"
        if meal:
            body += f" ({meal})"
        body += f"\n{len(items)} items across {len(cat_order)} categories."
        body += "\nPick a category to browse:"

        await send_whatsapp_interactive(phone, {
            "type": "list",
            "body": {"text": _truncate(body, 1024)},
            "action": {
                "button": "Choose Category",
                "sections": [{"title": "Categories", "rows": rows}],
            },
        })
        LOGGER.info(f"Sent category filter ({len(cat_order)} categories, {len(items)} total items) to {phone}")


# --- CART_DATA ---
async def _convert_cart_data(phone: str, agui: dict) -> None:
    """
    Convert cart to text summary + interactive management.

    - ≤3 items: per-item button cards (simple, intuitive)
    - >3 items + Flow: Cart Management Flow (qty dropdowns + remove)
    - >3 items, no Flow: simplified action buttons (fallback)
    """
    items = agui.get("items", [])
    total = agui.get("total", 0)
    packaging = agui.get("packaging_charge_per_item", 30)

    if not items:
        await send_whatsapp_reply(phone, "\ud83d\uded2 Your cart is empty.")
        return

    # Always send text summary first
    lines = ["\ud83d\uded2 *Your Cart*\n"]
    for i, item in enumerate(items, 1):
        name = item.get("name") or item.get("item_name", "Item")
        qty = item.get("quantity", 1)
        price = item.get("price", 0)
        lines.append(f"{i}. {name} \u00d7 {qty} \u2014 \u20b9{price * qty}")

    lines.append(f"\n\ud83d\udce6 Packaging: \u20b9{packaging} \u00d7 {len(items)} = \u20b9{packaging * len(items)}")
    lines.append(f"\ud83d\udcb0 *Total: \u20b9{total}*")
    await send_whatsapp_reply(phone, "\n".join(lines))

    if FLOW_MANAGE_CART_ID and len(items) <= 10:
        # Cart Management Flow (TextInput qty for all cart sizes)
        await _send_cart_management_flow(phone, items, total)
        buttons = [
            {"type": "reply", "reply": {"id": "add more items", "title": "Add More"}},
            {"type": "reply", "reply": {"id": "checkout", "title": "Checkout"}},
        ]
        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": "Or proceed directly:"},
            "action": {"buttons": buttons},
        })

    elif len(items) <= 3:
        # Fallback (no Flow): per-item button cards with +/- buttons
        for item in items:
            await _send_cart_item_buttons(phone, item)
        buttons = [
            {"type": "reply", "reply": {"id": "add more items", "title": "Add More Items"}},
            {"type": "reply", "reply": {"id": "checkout", "title": "Proceed to Checkout"}},
        ]
        await send_whatsapp_interactive(phone, {
            "type": "button",
            "body": {"text": "Ready to checkout?"},
            "action": {"buttons": buttons},
        })

    else:
        # Fallback (no Flow, >3 items): simplified action buttons
        buttons = [
            {"type": "reply", "reply": {"id": "modify_cart_items", "title": "Modify Items"}},
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
