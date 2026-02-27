"""
WebSocket Chat Endpoints
========================
Pure agentic AI chat interface for customer interactions
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
import structlog

from app.api.middleware.logging import log_chat_message, log_system_event

router = APIRouter()
logger = structlog.get_logger("api.chat")


def get_ist_timestamp() -> str:
    """Get current timestamp in IST"""
    try:
        from app.utils.timezone import get_current_time
        return get_current_time().isoformat()
    except Exception:
        # Fallback to UTC if timezone utils fail
        return datetime.now(timezone.utc).isoformat()


class ChatMessage(BaseModel):
    """Chat message structure"""
    message: str
    timestamp: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    device_id: Optional[str] = None  # Device fingerprint for multi-tier identity
    session_token: Optional[str] = None  # Long-lived session token (30-day)
    message_type: str = "user_message"  # user_message, ai_response, system_message


class ChatResponse(BaseModel):
    """Chat response structure"""
    message: str
    timestamp: str
    session_id: str
    message_type: str = "ai_response"
    metadata: Optional[Dict[str, Any]] = {}


async def translate_response(text: str, target_language: str) -> str:
    """
    Translate English response to target language (Hinglish/Tanglish).
    Only translates if response appears to be in English.

    Args:
        text: Response text (may be English or already translated)
        target_language: Target language (Hindi, Tamil, etc.)

    Returns:
        Translated text, or original if translation not needed/fails
    """
    if target_language == "English" or target_language not in ["Hindi", "Tamil"]:
        return text

    try:
        from openai import AsyncOpenAI
        import os

        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        if target_language == "Hindi":
            system_prompt = """Translate to casual Hinglish (Hindi-English mix in ROMAN script). Rules:
- If the text is ALREADY in Hinglish (Roman script Hindi-English mix), return it UNCHANGED
- Write like a young Indian texts friends — casual, short, natural. NOT formal/literary Hindi.
- ROMAN script ONLY — NO Devanagari (अ,ब,क). Write Hindi words phonetically: "chahiye", "dikha do", "karo"
- Use SIMPLE common Hindi words. Prefer "chahiye/chahte ho" over formal "chahenge", "karo" over "karenge", "dikha do" over "dikhana chahenge"
- Keep lots of English mixed in — "check karo", "add kar do", "menu dekh lo", "items available hain"
- Phonetic spelling for TTS: double vowels for long sounds (aa, ee, oo). Example: "aap", "nahi", "theek hai"
- Keep UNCHANGED: food names, numbers, prices (₹), order IDs (ORD-...), emojis, markdown (**bold**)
- Preserve ALL details (items, prices, totals) — do NOT shorten or drop information
- Output ONLY the translation, no explanations
Examples:
  English: "Would you like to dine in or take away?" → "Aap dine in chahte ho ya take away?"
  English: "Your cart has 2 items totaling ₹450" → "Aapke cart mein 2 items hain, total ₹450"
  English: "No items found for dosa" → "Dosa ke liye koi item nahi mila"
  BAD: "Kya aap kuch popular options dekhna chahenge" (too formal, TTS can't pronounce chahenge)
  GOOD: "Kya aap popular options check karna chahte ho?"  """
        else:  # Tamil
            system_prompt = """Translate to casual Tanglish (Tamil-English mix in ROMAN script). Rules:
- If the text is ALREADY in Tanglish (Roman script Tamil-English mix), return it UNCHANGED
- Write like a young South Indian texts friends — casual, short, natural. NOT formal/literary Tamil.
- ROMAN script ONLY — NO Tamil script (அ,ஆ,இ). Write Tamil words phonetically as they sound.
- Use SIMPLE common Tamil words mixed with English. Keep English technical/food words as-is.
- Phonetic spelling for TTS: spell as spoken. "irukku", "pannunga", "paarunga", "sollunga"
- Keep UNCHANGED: food names, numbers, prices (₹), order IDs (ORD-...), emojis, markdown (**bold**)
- Preserve ALL details (items, prices, totals) — do NOT shorten or drop information
- Output ONLY the translation, no explanations
Examples:
  English: "Would you like to dine in or take away?" → "Dine in ah illa take away ah?"
  English: "Your cart has 2 items totaling ₹450" → "Unga cart la 2 items irukku, total ₹450"
  English: "No items found for dosa" → "Dosa ku onnum kedaikala"  """

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=500
        )

        translated = response.choices[0].message.content.strip()
        logger.debug("chat_translation_applied",
                    original_len=len(text),
                    translated_len=len(translated),
                    language=target_language)
        return translated

    except Exception as e:
        logger.warning("chat_translation_failed", error=str(e), language=target_language)
        return text


class WebSocketManager:
    """
    Manages WebSocket connections for real-time chat
    Admin-ready: Tracks all active connections for monitoring
    """

    def __init__(self):
        # Store active connections: session_id -> WebSocket
        self.active_connections: Dict[str, WebSocket] = {}
        # Track connection metadata for admin analytics
        self.connection_metadata: Dict[str, Dict[str, Any]] = {}
        # Rate limiting: track message timestamps per session
        self.message_history: Dict[str, list] = {}  # session_id -> [timestamps]
        self.rate_limit_messages = 10  # Max messages per minute
        self.rate_limit_window = 60  # Time window in seconds

    async def connect(self, websocket: WebSocket, session_id: str, tester_id: str = None, restaurant: Dict[str, Any] = None):
        """Accept WebSocket connection and track it"""
        # CRITICAL: Disconnect existing connection for this session BEFORE accepting new one
        # This prevents duplicate welcome messages when server restarts and clients reconnect
        if session_id in self.active_connections:
            old_websocket = self.active_connections[session_id]
            try:
                await old_websocket.close(code=1000, reason="New connection for same session")
                logger.info(f"Closed old WebSocket connection for session: {session_id}")
            except Exception as e:
                logger.debug(f"Failed to close old WebSocket (already closed): {str(e)}")

        try:
            await websocket.accept()
            logger.info(f"WebSocket accepted for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to accept WebSocket for session {session_id}: {str(e)}")
            raise

        self.active_connections[session_id] = websocket

        # Preserve important state from previous connection (for reconnects)
        existing_metadata = self.connection_metadata.get(session_id, {})
        preserved_keys = [
            "welcome_sent", "auth_state", "user_id", "user_name", "phone_number",
            "auth_phone", "auth_form_id", "otp_form_id", "name_form_id", "welcome_msg"
        ]
        preserved_state = {k: existing_metadata[k] for k in preserved_keys if k in existing_metadata}

        metadata = {
            "connected_at": get_ist_timestamp(),
            "last_activity": datetime.now(timezone.utc),  # Track last activity for cleanup
            "client_info": {
                "host": websocket.client.host if websocket.client else "unknown",
                "port": websocket.client.port if websocket.client else "unknown"
            },
            "messages_sent": 0,
            "messages_received": 0,
            **preserved_state  # Restore preserved state from previous connection
        }

        # Log if this is a reconnect with preserved state
        if preserved_state:
            logger.info("websocket_reconnect_state_preserved", session_id=session_id, preserved_keys=list(preserved_state.keys()))

        # ============ MULTI-TENANT SUPPORT ============
        # Store restaurant info for multi-tenant operations
        if restaurant:
            metadata["restaurant_id"] = restaurant.get("restaurant_id")
            metadata["restaurant_name"] = restaurant.get("name")
            metadata["restaurant_data"] = restaurant  # Full restaurant config
        # ============ END MULTI-TENANT SUPPORT ============

        # ============ TESTING MODULE ============
        # Store tester_id for testing sessions
        if tester_id:
            metadata["tester_id"] = tester_id
        # ============ END TESTING MODULE ============

        self.connection_metadata[session_id] = metadata

        log_system_event(
            "websocket_connection_established",
            {
                "session_id": session_id,
                "client_host": websocket.client.host if websocket.client else "unknown",
                "restaurant_id": restaurant.get("restaurant_id") if restaurant else "unknown",
                "restaurant_name": restaurant.get("name") if restaurant else "unknown",
                "total_connections": len(self.active_connections)
            }
        )

    async def disconnect(self, session_id: str, websocket: WebSocket = None):
        """Remove WebSocket connection and log analytics.

        Args:
            session_id: Session to disconnect
            websocket: Optional WebSocket reference. If provided, only disconnect
                       if the stored WebSocket matches. This prevents a reconnecting
                       client's NEW connection from being removed by the OLD connection's
                       finally block cleanup.
        """
        if session_id in self.active_connections:
            # Guard: If a specific WebSocket was provided, only disconnect if it matches
            # the one currently stored. A newer connection may have replaced it.
            if websocket is not None and self.active_connections[session_id] is not websocket:
                logger.info(
                    "disconnect_skipped_newer_connection_exists",
                    session_id=session_id
                )
                return

            connection_info = self.connection_metadata.get(session_id, {})

            # ========================================================================
            # EVENT QUEUE CLEANUP - Prevent stale events from leaking
            # ========================================================================
            try:
                from app.core.agui_events import clear_event_queue
                clear_event_queue(session_id)
                logger.debug("event_queue_cleared", session_id=session_id)
            except Exception as e:
                logger.error("event_queue_clear_failed", session_id=session_id, error=str(e))

            # ========================================================================
            # INVENTORY CLEANUP ON DISCONNECT (Phase 3 Integration)
            # ========================================================================
            # Release inventory reservations if user was authenticated
            # FIXED: Use service layer instead of direct DB access
            try:
                user_id = connection_info.get("user_id")
                if user_id:
                    # User was authenticated - use service layer for cleanup
                    from app.services.user_data_manager import get_user_data_manager
                    from app.core.database import get_db_session

                    user_manager = get_user_data_manager()

                    # Use service method which internally handles inventory release
                    async with get_db_session() as db_session:
                        # Service method handles:
                        # 1. Releasing inventory from pending orders
                        # 2. Cache cleanup
                        # 3. Booking cleanup
                        await user_manager.on_user_logout(user_id, db_session)

                    logger.info(
                        "websocket_disconnect_cleanup_completed",
                        session_id=session_id,
                        user_id=user_id
                    )
            except Exception as e:
                logger.error(
                    "websocket_disconnect_inventory_cleanup_failed",
                    session_id=session_id,
                    error=str(e)
                )
            # ========================================================================

            # Log session analytics for admin dashboard
            log_system_event(
                "websocket_connection_closed",
                {
                    "session_id": session_id,
                    "duration_seconds": self._calculate_session_duration(session_id),
                    "messages_exchanged": connection_info.get("messages_sent", 0) + connection_info.get("messages_received", 0),
                    "total_connections": len(self.active_connections) - 1
                }
            )

            del self.active_connections[session_id]
            # DON'T delete connection_metadata on disconnect!
            # Keep it for reconnects so auth_state, user_id, etc. are preserved
            # Metadata will be overwritten/merged on next connect() call

    async def send_message(self, session_id: str, message: str, message_type: str = "ai_response"):
        """Send message to specific WebSocket connection"""
        await self.send_message_with_metadata(session_id, message, message_type, {})

    def _sanitize_metadata(self, metadata: Optional[dict]) -> dict:
        """Remove non-serializable objects from metadata (like BSON ObjectId)"""
        if not metadata:
            return {}

        import json
        try:
            # Try to serialize - if it works, return as-is
            json.dumps(metadata)
            return metadata
        except (TypeError, ValueError):
            # If serialization fails, convert problematic types
            def clean_value(obj):
                if obj is None:
                    return None
                elif isinstance(obj, (str, int, float, bool)):
                    return obj
                elif isinstance(obj, dict):
                    return {k: clean_value(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [clean_value(item) for item in obj]
                else:
                    # Convert any other type to string (handles ObjectId, datetime, etc.)
                    return str(obj)

            return clean_value(metadata)

    async def send_message_with_metadata(self, session_id: str, message: str, message_type: str = "ai_response", metadata: Optional[dict] = None) -> bool:
        """Send message with metadata to specific WebSocket connection.

        Returns True if sent successfully, False otherwise.
        IMPORTANT: Does NOT call disconnect() on send errors.
        Only the WebSocket endpoint's finally block should handle disconnection.
        This prevents transient send errors from permanently destroying the session.
        """
        if session_id not in self.active_connections:
            logger.debug(f"Cannot send message - session {session_id} not in active connections")
            return False

        websocket = self.active_connections[session_id]

        # Check if WebSocket is actually connected before attempting to send
        try:
            # Verify connection state
            if websocket.client_state.name != "CONNECTED":
                logger.warning(
                    f"WebSocket not connected for session {session_id}, state: {websocket.client_state.name}"
                )
                return False
        except AttributeError:
            # Fallback if client_state is not available
            pass

        # Sanitize metadata to remove non-serializable objects
        clean_metadata = self._sanitize_metadata(metadata)

        response = ChatResponse(
            message=message,
            timestamp=get_ist_timestamp(),
            session_id=session_id,
            message_type=message_type,
            metadata=clean_metadata
        )

        try:
            await websocket.send_text(response.model_dump_json())

            # Update analytics and activity time
            if session_id in self.connection_metadata:
                self.connection_metadata[session_id]["messages_sent"] += 1
                self.connection_metadata[session_id]["last_activity"] = datetime.now(timezone.utc)

            # Log for admin analytics
            log_chat_message(
                session_id=session_id,
                message_type=message_type,
                content=message,
                metadata={"sent_successfully": True, "debug_metadata": metadata}
            )
            return True

        except RuntimeError as e:
            if "WebSocket is not connected" in str(e):
                logger.warning(f"WebSocket send failed for session {session_id}: not connected")
            else:
                logger.warning(f"WebSocket runtime error for session {session_id}: {str(e)}")
            return False
        except Exception as e:
            logger.warning(f"Failed to send message to session {session_id}: {str(e)}")
            return False

    def _calculate_session_duration(self, session_id: str) -> float:
        """Calculate session duration for analytics"""
        if session_id in self.connection_metadata:
            connected_at = self.connection_metadata[session_id].get("connected_at")
            if connected_at:
                try:
                    from app.utils.timezone import get_current_time
                    current_time = get_current_time()
                    start_time = datetime.fromisoformat(connected_at.replace('Z', '+05:30'))
                    return (current_time - start_time).total_seconds()
                except Exception:
                    # Fallback to UTC calculation
                    start_time = datetime.fromisoformat(connected_at.replace('Z', '+00:00'))
                    return (datetime.now(timezone.utc) - start_time).total_seconds()
        return 0.0

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics for admin dashboard"""
        return {
            "total_active_connections": len(self.active_connections),
            "active_sessions": list(self.active_connections.keys()),
            "connection_metadata": self.connection_metadata
        }

    async def cleanup_inactive_sessions(self, inactive_timeout_minutes: int = 15):
        """
        Clean up inactive sessions (no activity for N minutes)
        For internal testing: removes sessions with no activity for 15+ minutes
        """
        now = datetime.now(timezone.utc)
        sessions_to_remove = []

        for session_id, metadata in self.connection_metadata.items():
            last_activity = metadata.get("last_activity")
            if last_activity:
                inactive_duration = (now - last_activity).total_seconds() / 60  # Convert to minutes

                if inactive_duration > inactive_timeout_minutes:
                    sessions_to_remove.append(session_id)
                    logger.info(
                        f"Cleaning up inactive session: {session_id} "
                        f"(inactive for {inactive_duration:.1f} minutes)"
                    )

        # Remove inactive sessions
        for session_id in sessions_to_remove:
            await self.disconnect(session_id)

        return {
            "sessions_cleaned": len(sessions_to_remove),
            "removed_sessions": sessions_to_remove
        }

    def check_rate_limit(self, session_id: str) -> tuple[bool, int]:
        """
        Check if session has exceeded rate limit
        Returns: (is_allowed, messages_remaining)
        """
        now = datetime.now(timezone.utc).timestamp()

        # Initialize message history for new sessions
        if session_id not in self.message_history:
            self.message_history[session_id] = []

        # Remove timestamps outside the time window
        self.message_history[session_id] = [
            ts for ts in self.message_history[session_id]
            if now - ts < self.rate_limit_window
        ]

        # Check if limit exceeded
        current_count = len(self.message_history[session_id])
        is_allowed = current_count < self.rate_limit_messages
        messages_remaining = max(0, self.rate_limit_messages - current_count)

        if is_allowed:
            # Add current timestamp
            self.message_history[session_id].append(now)

        return is_allowed, messages_remaining


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


async def manage_cart_ownership(session_id: str, user_id: str):
    """
    Ensure cart belongs to the authenticated user (SQL session_cart).
    If cart was owned by someone else -> CLEAR IT (data leakage risk).
    If cart was anonymous or owned by same user -> KEEP IT (resume).
    Always tag session_state with current user_id.
    """
    try:
        from app.core.database import get_db_session

        async with get_db_session() as db:
            # Check existing owner in session_state
            result = await db.execute(
                text("SELECT user_id FROM session_state WHERE session_id = :sid"),
                {"sid": session_id}
            )
            row = result.fetchone()
            existing_owner = str(row[0]) if row and row[0] else None

            if existing_owner and existing_owner != user_id:
                # CRITICAL: Different user -> clear cart to prevent data leakage
                logger.info(
                    "Clearing cart due to user switch",
                    session_id=session_id,
                    old_user=existing_owner,
                    new_user=user_id
                )
                await db.execute(
                    text("UPDATE session_cart SET is_active = FALSE, updated_at = NOW() WHERE session_id = :sid AND is_active = TRUE"),
                    {"sid": session_id}
                )

            # Upsert session_state with current user_id
            await db.execute(
                text("""
                    INSERT INTO session_state (session_id, user_id, last_activity_at)
                    VALUES (:sid, :uid::uuid, NOW())
                    ON CONFLICT (session_id) DO UPDATE
                    SET user_id = :uid::uuid, last_activity_at = NOW()
                """),
                {"sid": session_id, "uid": user_id}
            )
            await db.commit()

            if not existing_owner:
                logger.info("User claiming anonymous cart", session_id=session_id, user_id=user_id)

    except Exception as e:
        logger.error(f"Failed to manage cart ownership: {str(e)}")


@router.websocket("/chat/{session_id}")
async def chat_endpoint(
    websocket: WebSocket,
    session_id: str,
    api_key: str = None,
    tester_id: str = None,
    device_id: str = None,
    session_token: str = None
):
    """
    Main WebSocket chat endpoint for pure agentic AI interactions
    This is the ONLY customer-facing endpoint - everything goes through AI

    Query parameters:
    - api_key: Restaurant API key for multi-tenant authentication (REQUIRED)
    - tester_id: For testing sessions (ws://localhost:8000/api/v1/chat/test-session-123?tester_id=tester-001)
    - device_id: Device fingerprint for multi-tier identity recognition
    - session_token: Long-lived session token (30-day) for authenticated users
    """

    logger.info(
        f"New WebSocket connection attempt for session: {session_id}",
        has_api_key=bool(api_key),
        tester_id=tester_id,
        has_device_id=bool(device_id),
        has_session_token=bool(session_token)
    )

    # ========================================================================
    # MULTI-TENANT AUTHENTICATION (Phase 1 - Restaurant API Key)
    # ========================================================================
    # AUTHENTICATION DISABLED FOR TESTING - Accept all connections
    # Get actual restaurant from database for proper foreign key references
    from app.tools.database.restaurant_tools import GetRestaurantTool
    get_restaurant_tool = GetRestaurantTool()
    restaurant_result = await get_restaurant_tool.execute()

    if restaurant_result.status.value == "success" and restaurant_result.data:
        restaurant = {
            "restaurant_id": str(restaurant_result.data.get("id")),
            "name": restaurant_result.data.get("name", "Test Restaurant"),
            "api_key": api_key or "test_key",
            "status": "active"
        }
    else:
        # Fallback for testing without database
        restaurant = {
            "restaurant_id": "test_restaurant_001",
            "name": "Test Restaurant",
            "api_key": api_key or "test_key",
            "status": "active"
        }

    logger.info(
        "WebSocket connection accepted (auth bypassed for testing)",
        session_id=session_id,
        restaurant_id=restaurant["restaurant_id"],
        tester_id=tester_id
    )
    # ========================================================================

    # Connect to WebSocket (with tester_id for testing sessions)
    await websocket_manager.connect(websocket, session_id, tester_id, restaurant)

    try:
        # Initialize session with existing services
        from app.services.session_manager import SessionManager
        session_manager = SessionManager()

        # Get or create session (SessionManager methods are async)
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            # Create new session - use authenticated restaurant_id as tenant_id
            # IMPORTANT: Pass session_id to use WebSocket session ID for conversation tracking
            tenant_id = restaurant["restaurant_id"]
            session_data = await session_manager.create_session(
                tenant_id=tenant_id,
                user_id=None,  # Will be set after authentication
                phone_number=None,
                email=None,
                session_id=session_id  # Use WebSocket session ID for conversation retrieval
            )
            logger.info(
                f"Created new session: {session_id}",
                tenant_id=tenant_id,
                restaurant_name=restaurant["name"]
            )

        # ========================================================================
        # UPFRONT PHONE AUTHENTICATION FLOW
        # ========================================================================
        # Check if authentication is required and user is not already authenticated
        from app.core.config import config
        from app.core.agui_events import AGUIEventEmitter

        auth_emitter = AGUIEventEmitter(session_id)
        is_authenticated = False
        authenticated_user_name = None
        authenticated_user_id = None
        authenticated_phone = None

        # Check if session was already authenticated (reconnection scenario)
        if session_data and session_data.is_authenticated and session_data.user_id:
            is_authenticated = True
            authenticated_user_id = session_data.user_id
            authenticated_user_name = session_data.metadata.get("user_name") if session_data.metadata else None
            authenticated_phone = session_data.phone_number
            logger.info(
                "User already authenticated via session data (reconnection)",
                session_id=session_id,
                user_id=authenticated_user_id,
                user_name=authenticated_user_name
            )
            # Manage cart ownership on reconnection
            await manage_cart_ownership(session_id, authenticated_user_id)

        # Check if user already authenticated via session_token
        elif session_token:
            try:
                from app.services.identity_service import identity_service
                recognition_result = await identity_service.recognize_user(
                    device_id=device_id,
                    session_token=session_token
                )
                if recognition_result.get("tier") == 3 and recognition_result.get("user_name"):
                    is_authenticated = True
                    authenticated_user_name = recognition_result.get("user_name")
                    authenticated_user_id = recognition_result.get("user_id")
                    logger.info(
                        "User already authenticated via session_token",
                        session_id=session_id,
                        user_name=authenticated_user_name
                    )
                    
                    # Manage Cart Ownership (Auto-Login)
                    await manage_cart_ownership(session_id, authenticated_user_id)

            except Exception as e:
                logger.warning(f"Session token validation failed: {str(e)}")

        # ========================================================================
        # WHATSAPP SESSION AUTO-AUTH (bypass phone/OTP form flow)
        # ========================================================================
        # WhatsApp sessions use session_id prefix "wa-" followed by phone number.
        # These users are already phone-verified by Meta — skip form auth entirely.
        elif session_id.startswith("wa-"):
            wa_phone_raw = session_id[3:]  # Strip "wa-" prefix to get phone number
            # Normalize: WhatsApp sends "919876543210", we store "+919876543210"
            if not wa_phone_raw.startswith("+"):
                wa_phone_raw = "+" + wa_phone_raw

            logger.info(
                "WhatsApp session detected, auto-authenticating",
                session_id=session_id,
                phone=wa_phone_raw[:6] + "****"
            )

            try:
                from app.features.user_management.tools.otp_tools import check_user_exists, create_user

                user_check = await check_user_exists(phone_number=wa_phone_raw)

                if user_check.get("success") and user_check.get("data", {}).get("exists"):
                    # Existing user
                    user_data = user_check["data"]["user"]
                    is_authenticated = True
                    authenticated_user_name = user_data.get("full_name") or user_data.get("name") or "WhatsApp User"
                    authenticated_user_id = str(user_data.get("user_id") or user_data.get("id"))
                    authenticated_phone = wa_phone_raw
                else:
                    # New user — auto-register (phone already verified by Meta)
                    create_result = await create_user(
                        phone_number=wa_phone_raw,
                        full_name="WhatsApp User"
                    )
                    if create_result.get("success"):
                        user_data = create_result["data"]["user"]
                        is_authenticated = True
                        authenticated_user_name = user_data.get("full_name") or "WhatsApp User"
                        authenticated_user_id = str(user_data.get("user_id") or user_data.get("id"))
                        authenticated_phone = wa_phone_raw
                    else:
                        # Fallback: let them through as guest
                        is_authenticated = True
                        authenticated_user_name = "WhatsApp User"
                        authenticated_user_id = None
                        authenticated_phone = wa_phone_raw

                # Update connection metadata
                if session_id in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[session_id]["user_id"] = authenticated_user_id
                    websocket_manager.connection_metadata[session_id]["user_name"] = authenticated_user_name
                    websocket_manager.connection_metadata[session_id]["phone_number"] = authenticated_phone
                    websocket_manager.connection_metadata[session_id]["auth_state"] = "authenticated"
                    websocket_manager.connection_metadata[session_id]["source"] = "whatsapp"

                # Manage cart ownership
                if authenticated_user_id:
                    await manage_cart_ownership(session_id, authenticated_user_id)

                # Update session in Redis
                await session_manager.update_session(
                    session_id,
                    is_authenticated=True,
                    user_id=authenticated_user_id,
                    phone_number=authenticated_phone,
                    metadata={"user_name": authenticated_user_name, "source": "whatsapp"}
                )

                logger.info(
                    "WhatsApp user auto-authenticated",
                    session_id=session_id,
                    user_id=authenticated_user_id,
                    user_name=authenticated_user_name
                )

            except Exception as e:
                logger.error(f"WhatsApp auto-auth failed: {str(e)}", exc_info=True)
                # Still let them through as guest
                is_authenticated = True
                authenticated_user_name = "WhatsApp User"
                authenticated_user_id = None
                authenticated_phone = session_id[3:]
        # ========================================================================

        # If not authenticated and AUTH_REQUIRED, start phone auth flow
        if not is_authenticated and config.AUTH_REQUIRED:
            # Check if auth is already in progress or completed for this session
            existing_auth_state = websocket_manager.connection_metadata.get(session_id, {}).get("auth_state")

            # If already authenticated via preserved metadata, skip auth flow entirely
            # BUT only trust it if we have a valid user_id (prevents stale auth after hard refresh)
            preserved_user_id = websocket_manager.connection_metadata.get(session_id, {}).get("user_id")
            preserved_user_name = websocket_manager.connection_metadata.get(session_id, {}).get("user_name")

            if existing_auth_state == "authenticated" and preserved_user_id:
                # Valid preserved auth - skip form entirely
                logger.info(
                    "User already authenticated via preserved metadata, skipping auth flow",
                    session_id=session_id,
                    user_id=preserved_user_id
                )
                is_authenticated = True
                authenticated_user_id = preserved_user_id
                authenticated_user_name = preserved_user_name
                # Skip the form emission entirely - no elif/else needed
            elif existing_auth_state == "authenticated" and not preserved_user_id:
                # Stale auth state without user_id - clear it and show form
                logger.warning(
                    "Stale auth state found without user_id, clearing and showing form",
                    session_id=session_id
                )
                if session_id in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[session_id]["auth_state"] = "awaiting_phone"

                # Emit phone auth form request
                auth_form_id = auth_emitter.emit_phone_auth_form(restaurant["name"])
                if session_id in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[session_id]["auth_form_id"] = auth_form_id
                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
            elif existing_auth_state and existing_auth_state not in (None,):
                # Auth in progress on reconnect - RE-EMIT the form since frontend lost it
                logger.info(
                    "Auth in progress on reconnect, re-emitting form",
                    session_id=session_id,
                    auth_state=existing_auth_state
                )

                if existing_auth_state == "awaiting_phone":
                    auth_form_id = auth_emitter.emit_phone_auth_form(restaurant["name"])
                    if session_id in websocket_manager.connection_metadata:
                        websocket_manager.connection_metadata[session_id]["auth_form_id"] = auth_form_id
                    await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                elif existing_auth_state == "awaiting_otp":
                    auth_phone = websocket_manager.connection_metadata.get(session_id, {}).get("auth_phone")
                    if auth_phone:
                        otp_form_id = auth_emitter.emit_login_otp_form(auth_phone)
                        if session_id in websocket_manager.connection_metadata:
                            websocket_manager.connection_metadata[session_id]["otp_form_id"] = otp_form_id
                        await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                elif existing_auth_state == "awaiting_name":
                    auth_phone = websocket_manager.connection_metadata.get(session_id, {}).get("auth_phone")
                    if auth_phone:
                        name_form_id = auth_emitter.emit_name_collection_form(auth_phone)
                        if session_id in websocket_manager.connection_metadata:
                            websocket_manager.connection_metadata[session_id]["name_form_id"] = name_form_id
                        await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
            else:
                logger.info(
                    "Starting phone authentication flow",
                    session_id=session_id,
                    metadata_exists=session_id in websocket_manager.connection_metadata
                )
                print(f"[DEBUG] Starting phone auth flow for session: {session_id}")

                try:
                    # Set auth state BEFORE emitting form (prevents duplicate on reconnect)
                    if session_id in websocket_manager.connection_metadata:
                        websocket_manager.connection_metadata[session_id]["auth_state"] = "awaiting_phone"

                    # Emit phone auth form request
                    auth_form_id = auth_emitter.emit_phone_auth_form(restaurant["name"])
                    logger.info("Phone auth form emitted", session_id=session_id, form_id=auth_form_id)
                    print(f"[DEBUG] Phone auth form emitted for session: {session_id}, form_id: {auth_form_id}")

                    # Store form ID in connection metadata
                    if session_id in websocket_manager.connection_metadata:
                        websocket_manager.connection_metadata[session_id]["auth_form_id"] = auth_form_id

                    # Forward the form request to WebSocket
                    print(f"[DEBUG] About to stream form events for session: {session_id}")
                    await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                    logger.info("Form events streamed to WebSocket", session_id=session_id)
                    print(f"[DEBUG] Form events streamed to WebSocket for session: {session_id}")
                except Exception as e:
                    logger.error("Error in auth flow", session_id=session_id, error=str(e), exc_info=True)

            # Wait for phone auth form response
            logger.info(
                "Entering auth response loop",
                session_id=session_id,
                is_authenticated=is_authenticated,
                existing_auth_state=existing_auth_state
            )
            print(f"[DEBUG] Entering auth loop - is_authenticated: {is_authenticated}, existing_auth_state: {existing_auth_state}")
            while not is_authenticated:
                try:
                    raw_message = await websocket.receive_text()
                    print(f"[DEBUG] Auth loop received raw message: {raw_message[:200]}")
                    logger.info("auth_loop_message_received", session_id=session_id, message_preview=raw_message[:100])
                    message_data = json.loads(raw_message)

                    # Check if this is a form_response
                    if message_data.get("type") == "form_response":
                        form_type = message_data.get("form_type")
                        form_data = message_data.get("data", {})

                        if form_type == "phone_auth":
                            # Phone number submitted
                            print(f"[DEBUG] phone_auth form received, form_data: {form_data}")
                            phone_number = form_data.get("phone", "").strip()
                            if not phone_number:
                                print(f"[DEBUG] phone_number is empty, skipping")
                                continue

                            # Normalize phone number
                            phone_number = phone_number.replace(" ", "").replace("-", "")
                            if not phone_number.startswith("+"):
                                phone_number = "+91" + phone_number.lstrip("0")

                            logger.info(
                                "Phone number received",
                                session_id=session_id,
                                phone=phone_number[:6] + "****"
                            )

                            # Check if user exists
                            from app.features.user_management.tools.otp_tools import check_user_exists, send_otp
                            print(f"[DEBUG] Checking if user exists for phone: {phone_number[:6]}****")
                            user_check = await check_user_exists(phone_number=phone_number)
                            print(f"[DEBUG] check_user_exists result: {user_check}")

                            if user_check.get("success") and user_check.get("data", {}).get("exists"):
                                # Existing user - authenticate directly without OTP
                                print(f"[DEBUG] Existing user found, authenticating directly")
                                user_data = user_check["data"]["user"]
                                is_authenticated = True
                                authenticated_user_name = user_data.get("full_name") or user_data.get("name")
                                authenticated_user_id = str(user_data.get("user_id") or user_data.get("id"))
                                authenticated_phone = phone_number

                                logger.info(
                                    "Existing user recognized",
                                    session_id=session_id,
                                    user_name=authenticated_user_name
                                )
                                print(f"[DEBUG] Existing user: {authenticated_user_name} (ID: {authenticated_user_id})")

                                # Update connection metadata
                                if session_id in websocket_manager.connection_metadata:
                                    websocket_manager.connection_metadata[session_id]["user_id"] = authenticated_user_id
                                    websocket_manager.connection_metadata[session_id]["user_name"] = authenticated_user_name
                                    websocket_manager.connection_metadata[session_id]["phone_number"] = authenticated_phone
                                    websocket_manager.connection_metadata[session_id]["auth_state"] = "authenticated"

                                # Dismiss auth forms
                                print(f"[DEBUG] Dismissing auth forms and streaming to WebSocket")
                                auth_emitter.emit_form_dismiss(["phone_auth", "login_otp"])
                                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                                print(f"[DEBUG] Auth forms dismissed, auth complete")

                                # Manage Cart Ownership (Existing User Login)
                                await manage_cart_ownership(session_id, authenticated_user_id)

                                # Update session data in Redis for reconnection support
                                await session_manager.update_session(
                                    session_id,
                                    is_authenticated=True,
                                    user_id=authenticated_user_id,
                                    phone_number=authenticated_phone,
                                    metadata={"user_name": authenticated_user_name}
                                )

                            else:
                                # New user - send OTP for verification
                                print(f"[DEBUG] New user detected, sending OTP to {phone_number[:6]}****")
                                otp_result = await send_otp(phone_number=phone_number, purpose="registration")
                                print(f"[DEBUG] send_otp result: {otp_result}")

                                if otp_result.get("success"):
                                    # Emit both events FIRST, then stream once (fixes race condition)
                                    print(f"[DEBUG] OTP sent successfully, showing OTP form")
                                    auth_emitter.emit_form_dismiss(["phone_auth"])
                                    otp_form_id = auth_emitter.emit_login_otp_form(phone_number)

                                    # Update auth state
                                    if session_id in websocket_manager.connection_metadata:
                                        websocket_manager.connection_metadata[session_id]["auth_state"] = "awaiting_otp"
                                        websocket_manager.connection_metadata[session_id]["auth_phone"] = phone_number
                                        websocket_manager.connection_metadata[session_id]["otp_form_id"] = otp_form_id

                                    # Stream ALL events at once (dismiss + OTP form)
                                    await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                                    print(f"[DEBUG] OTP form streamed to WebSocket")
                                else:
                                    print(f"[DEBUG] Failed to send OTP: {otp_result.get('message')}")
                                    logger.error(f"Failed to send OTP: {otp_result.get('message')}")

                        elif form_type == "login_otp":
                            # Check if user cancelled (wants to change number)
                            if form_data.get("cancelled") or message_data.get("cancelled"):
                                logger.info("User cancelled OTP, returning to phone form", session_id=session_id)
                                # Emit both events FIRST, then stream once (fixes race condition)
                                auth_emitter.emit_form_dismiss(["login_otp"])
                                auth_form_id = auth_emitter.emit_phone_auth_form(restaurant["name"])
                                if session_id in websocket_manager.connection_metadata:
                                    websocket_manager.connection_metadata[session_id]["auth_state"] = "awaiting_phone"
                                    websocket_manager.connection_metadata[session_id].pop("auth_phone", None)
                                # Stream ALL events at once (dismiss + phone form)
                                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                                continue

                            # OTP submitted
                            otp_code = form_data.get("otp", "").strip()
                            auth_phone = websocket_manager.connection_metadata.get(session_id, {}).get("auth_phone")

                            if not otp_code or not auth_phone:
                                continue

                            # Verify OTP
                            from app.features.user_management.tools.otp_tools import verify_otp, create_user
                            otp_result = await verify_otp(
                                phone_number=auth_phone,
                                otp_code=otp_code,
                                purpose="registration"
                            )

                            if otp_result.get("success") and otp_result.get("data", {}).get("verified"):
                                # OTP verified - ask for user's name before creating account
                                logger.info(
                                    "OTP verified, collecting user name",
                                    session_id=session_id,
                                    phone=auth_phone[:6] + "****"
                                )

                                # Emit both events FIRST, then stream once (fixes race condition)
                                auth_emitter.emit_form_dismiss(["login_otp"])
                                name_form_id = auth_emitter.emit_name_collection_form(auth_phone)

                                # Update auth state
                                if session_id in websocket_manager.connection_metadata:
                                    websocket_manager.connection_metadata[session_id]["auth_state"] = "awaiting_name"
                                    websocket_manager.connection_metadata[session_id]["name_form_id"] = name_form_id

                                # Stream ALL events at once (dismiss + name form)
                                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)
                            else:
                                # Invalid OTP - send error message
                                await websocket_manager.send_message(
                                    session_id=session_id,
                                    message="Invalid OTP. Please try again.",
                                    message_type="system_message"
                                )

                        elif form_type == "name_collection":
                            # Name submitted (or skipped)
                            auth_phone = websocket_manager.connection_metadata.get(session_id, {}).get("auth_phone")
                            if not auth_phone:
                                continue

                            # Get name from form data, use "Guest" if skipped/empty
                            user_name = form_data.get("name", "").strip()
                            if not user_name or message_data.get("cancelled"):
                                user_name = "Guest"

                            logger.info(
                                "Name collected, creating user account",
                                session_id=session_id,
                                user_name=user_name
                            )

                            # Create user account with the provided name
                            from app.features.user_management.tools.otp_tools import create_user
                            create_result = await create_user(
                                phone_number=auth_phone,
                                full_name=user_name
                            )

                            if create_result.get("success"):
                                user_data = create_result["data"]["user"]
                                is_authenticated = True
                                authenticated_user_name = user_data.get("full_name") or user_name
                                authenticated_user_id = str(user_data.get("user_id") or user_data.get("id"))
                                authenticated_phone = auth_phone

                                logger.info(
                                    "New user created and authenticated",
                                    session_id=session_id,
                                    user_id=authenticated_user_id,
                                    user_name=authenticated_user_name
                                )

                                # Update connection metadata
                                if session_id in websocket_manager.connection_metadata:
                                    websocket_manager.connection_metadata[session_id]["user_id"] = authenticated_user_id
                                    websocket_manager.connection_metadata[session_id]["user_name"] = authenticated_user_name
                                    websocket_manager.connection_metadata[session_id]["phone_number"] = authenticated_phone
                                    websocket_manager.connection_metadata[session_id]["auth_state"] = "authenticated"

                                # Dismiss all auth forms
                                auth_emitter.emit_form_dismiss(["phone_auth", "login_otp", "name_collection"])
                                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)

                                # Manage Cart Ownership (New User Creation)
                                await manage_cart_ownership(session_id, authenticated_user_id)

                                # Update session data in Redis for reconnection support
                                await session_manager.update_session(
                                    session_id,
                                    is_authenticated=True,
                                    user_id=authenticated_user_id,
                                    phone_number=authenticated_phone,
                                    metadata={"user_name": authenticated_user_name}
                                )

                            else:
                                logger.error(f"Failed to create user: {create_result.get('message')}")
                                # Fall back to Guest account
                                is_authenticated = True
                                authenticated_user_name = "Guest"
                                authenticated_phone = auth_phone
                                auth_emitter.emit_form_dismiss(["phone_auth", "login_otp", "name_collection"])
                                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)

                except WebSocketDisconnect:
                    logger.info(f"WebSocket disconnected during auth for session: {session_id}")
                    await websocket_manager.disconnect(session_id, websocket)
                    return
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error in auth flow: {error_msg}")
                    # Check if this is a WebSocket disconnection error
                    if "WebSocket is not connected" in error_msg or "disconnect" in error_msg.lower():
                        logger.info(f"WebSocket disconnected, exiting auth flow for session: {session_id}")
                        await websocket_manager.disconnect(session_id, websocket)
                        return
                    continue
        # ========================================================================

        # ========================================================================
        # AI-POWERED WELCOME MESSAGE - Multi-Tier Identity Recognition
        # ========================================================================
        # Generate personalized welcome based on user recognition tier:
        # - Tier 1 (Anonymous): Generic welcome with service overview
        # - Tier 2 (Device): Welcome back message
        # - Tier 3 (Authenticated): Fully personalized with name, favorites, history

        # Check if welcome was already sent for this session (prevent duplicates on reconnect)
        welcome_already_sent = websocket_manager.connection_metadata.get(session_id, {}).get("welcome_sent", False)
        preserved_welcome_msg = websocket_manager.connection_metadata.get(session_id, {}).get("welcome_msg")

        if welcome_already_sent and preserved_welcome_msg:
            # Re-send the preserved welcome message on reconnect
            logger.info("welcome_resent_on_reconnect", session_id=session_id, message_length=len(preserved_welcome_msg))
            await websocket_manager.send_message(
                session_id=session_id,
                message=preserved_welcome_msg,
                message_type="ai_response"
            )
        elif welcome_already_sent:
            logger.info("welcome_skipped_already_sent", session_id=session_id)
        else:
            # Mark welcome as sent BEFORE sending to prevent race conditions
            if session_id in websocket_manager.connection_metadata:
                websocket_manager.connection_metadata[session_id]["welcome_sent"] = True

            try:
                from app.services.identity_service import identity_service
                from app.ai_services.welcome_service import welcome_service
                from app.utils.welcome import get_time_based_greeting, get_restaurant_name

                # If already authenticated via phone auth flow, use that info
                if is_authenticated and authenticated_user_name:
                    tier = 3
                    user_name = authenticated_user_name
                    personalization = {}
                else:
                    # Recognize user using multi-tier identity system
                    recognition_result = await identity_service.recognize_user(
                        device_id=device_id,
                        session_token=session_token
                    )

                    tier = recognition_result.get("tier", 1)
                    user_name = recognition_result.get("user_name")
                    personalization = recognition_result.get("personalization", {})

                logger.info(
                    "User recognized for welcome",
                    session_id=session_id,
                    tier=tier,
                    user_name=user_name,
                    has_user_name=bool(user_name),
                    has_device_id=bool(device_id),
                    has_session_token=bool(session_token)
                )

                # Get restaurant name from authenticated restaurant and time-based greeting
                restaurant_name = restaurant["name"]
                time_greeting = get_time_based_greeting()

                # Emit starting activity for welcome generation
                # This masks the LLM latency with a "Setting up..." status
                from app.core.agui_events import AGUIEventEmitter
                welcome_emitter = AGUIEventEmitter(session_id)
                welcome_emitter.emit_activity("thinking", "Setting up your personal waiter...")
                await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=1.0)

                # Check for existing cart items (from PostgreSQL session_cart)
                has_cart_items = False
                try:
                    from app.core.session_events import get_sync_session_tracker
                    tracker = get_sync_session_tracker(session_id)
                    cart_data = tracker.get_cart_summary()
                    has_cart_items = bool(cart_data.get("items"))
                    if has_cart_items:
                        logger.info("welcome_generating_with_cart_items", session_id=session_id)
                except Exception as e:
                    logger.warning(f"Failed to check cart for welcome: {str(e)}")

                try:
                    # Generate AI-powered welcome message
                    welcome_msg = await welcome_service.generate_welcome(
                        tier=tier,
                        restaurant_name=restaurant_name,
                        time_greeting=time_greeting,
                        user_name=user_name,
                        personalization=personalization,
                        has_cart_items=has_cart_items
                    )
                finally:
                    # Clear the activity status
                    welcome_emitter.emit_activity_end()
                    await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=1.0)

                await websocket_manager.send_message(
                    session_id=session_id,
                    message=welcome_msg,
                    message_type="ai_response"
                )

                # Store welcome message for adding to conversation history
                if session_id in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[session_id]["welcome_msg"] = welcome_msg

                logger.info(
                    "AI-powered welcome sent",
                    session_id=session_id,
                    tier=tier,
                    message_length=len(welcome_msg)
                )

            except Exception as e:
                # Fallback welcome message if AI generation fails
                logger.error(f"Failed to generate AI welcome for session {session_id}: {str(e)}")

                # Use authenticated name if available
                if is_authenticated and authenticated_user_name:
                    fallback_msg = (
                        f"Hello {authenticated_user_name}! Welcome back to our restaurant. I'm your AI assistant, "
                        "and I can help you browse our menu, place a takeaway order, make a reservation, "
                        "or answer any questions. What would you like to do?"
                    )
                else:
                    fallback_msg = (
                        "Hello! Welcome to our restaurant. I'm your AI assistant, and I can help you "
                        "browse our menu, place a takeaway order, make a reservation, "
                        "or answer any questions about our restaurant. What would you like to do?"
                    )
                await websocket_manager.send_message(
                    session_id=session_id,
                    message=fallback_msg,
                    message_type="ai_response"
                )

                # Store fallback welcome message for adding to conversation history
                if session_id in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[session_id]["welcome_msg"] = fallback_msg

                logger.warning(f"Used fallback welcome message for session {session_id}")
        # ========================================================================

        # ========================================================================
        # PENDING PAYMENT DELIVERY ON RECONNECT
        # ========================================================================
        # When user clicks Razorpay payment link, the browser navigates away,
        # killing the WebSocket. The payment callback stores success in Redis
        # but the WebSocket notification is lost. On reconnect, check Redis
        # for a completed payment and deliver the PaymentSuccessEvent.
        try:
            from app.services.payment_state_service import get_payment_state, set_payment_state

            payment_state = get_payment_state(session_id)
            # Skip for WhatsApp sessions — WA bridge bg listener already
            # handles payment delivery; re-sending causes duplicates.
            is_wa_session = session_id.startswith("wa-")
            if (
                not is_wa_session
                and payment_state.get("step") == "payment_success"
                and payment_state.get("completed")
                and not payment_state.get("ws_delivered")
            ):
                from app.core.agui_events import PaymentSuccessEvent
                import json as _json

                event = PaymentSuccessEvent(
                    order_id=payment_state.get("order_id", ""),
                    order_number=payment_state.get("order_number", ""),
                    amount=payment_state.get("amount", 0),
                    payment_id=payment_state.get("payment_id", ""),
                    order_type=payment_state.get("order_type", "takeaway"),
                    quick_replies=[
                        {"label": "\U0001f4c4 View Receipt", "action": "view_receipt"},
                        {"label": "\U0001f37d\ufe0f Order More", "action": "order_more"}
                    ]
                )

                event_data = _json.loads(event.to_json())
                sent = await websocket_manager.send_message_with_metadata(
                    session_id=session_id,
                    message="",
                    message_type="agui_event",
                    metadata={
                        "agui": event_data,
                        "target_session": session_id
                    }
                )

                if sent:
                    payment_state["ws_delivered"] = True
                    set_payment_state(session_id, payment_state)
                    logger.info(
                        "pending_payment_delivered_on_reconnect",
                        session_id=session_id,
                        order_id=payment_state.get("order_id")
                    )
        except Exception as e:
            logger.warning("pending_payment_check_failed", session_id=session_id, error=str(e))
        # ========================================================================

        # Main message loop
        while True:
            # Receive message from client
            try:
                raw_message = await websocket.receive_text()

                # Parse message
                device_id = None
                session_token = None
                language = "English"  # Default language
                try:
                    message_data = json.loads(raw_message)
                    # Support both "message" and "content" keys for backwards compatibility
                    user_message = message_data.get("message") or message_data.get("content") or raw_message
                    device_id = message_data.get("device_id")
                    session_token = message_data.get("session_token")

                    # Extract language preference for response
                    language = message_data.get("language", "English")

                    # DEBUG: Log language received from frontend
                    logger.info("chat_language_received", session_id=session_id, language=language, raw_message_keys=list(message_data.keys()) if isinstance(message_data, dict) else "not_dict")

                    # Add language instruction to user message for Hinglish/Tanglish responses
                    if language == "Hindi":
                        user_message = f"[RESPOND IN HINGLISH - Write Hindi words in ROMAN/ENGLISH script only (NO Devanagari like अ,ब,क). Keep food names, prices in English. Example: 'Aapka order mein 2 Masala Dosa add kar diya hai, total ₹250 ho gaya'] {user_message}"
                    elif language == "Tamil":
                        user_message = f"[RESPOND IN TANGLISH - Write Tamil words in ROMAN/ENGLISH script only (NO Tamil script like அ,ப,க). Keep food names, prices in English. Example: 'Ungal order-la 2 Masala Dosa add panniten, total ₹250 aagum'] {user_message}"
                except json.JSONDecodeError:
                    # Handle plain text messages
                    user_message = raw_message
                    language = "English"

                # ========================================================================
                # DIRECT ADD-TO-CART HANDLER (bypasses LLM for UI card interactions)
                # ========================================================================
                if isinstance(message_data, dict) and message_data.get("type") == "form_response":
                    form_type = message_data.get("form_type")
                    form_data = message_data.get("data", {})

                    # Skip auth form responses that arrive in main loop
                    # (e.g. from frontend form submitted after reconnect)
                    if form_type in ("phone_auth", "login_otp", "name_collection"):
                        logger.info(
                            "auth_form_response_in_main_loop_skipped",
                            session_id=session_id,
                            form_type=form_type
                        )
                        continue  # Skip - auth already handled

                    if form_type == "direct_add_to_cart":
                        # Direct add-to-cart from UI cards - bypass LLM entirely
                        items = form_data.get("items", [])
                        if items:
                            from app.features.food_ordering.tools_event_sourced import create_event_sourced_tools

                            # Get user_id from connection metadata
                            customer_id = None
                            if session_id in websocket_manager.connection_metadata:
                                customer_id = websocket_manager.connection_metadata[session_id].get("user_id")

                            # Create tools for this session
                            tools = create_event_sourced_tools(session_id, customer_id)
                            batch_add_tool = tools[1]  # batch_add_to_cart

                            # Format items as "item:qty, item:qty" for batch tool
                            pairs = []
                            for item in items:
                                item_name = item.get("name", "")
                                quantity = item.get("quantity", 1)
                                if item_name and quantity > 0:
                                    pairs.append(f"{item_name}:{quantity}")

                            if pairs:
                                try:
                                    result = batch_add_tool.run(items_with_quantities=", ".join(pairs))
                                except Exception as e:
                                    logger.error("direct_add_to_cart_failed", error=str(e))
                                    result = "Failed to add items to cart"
                            else:
                                result = "No items added"

                            # Flush staged events to queue, then stream to WebSocket
                            from app.core.agui_events import flush_pending_events
                            flush_pending_events(session_id)
                            await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=2.0)

                            # Send the final response (with translation if needed)
                            if language != "English":
                                result = await translate_response(result, language)
                            await websocket_manager.send_message_with_metadata(
                                session_id=session_id,
                                message=result,
                                message_type="ai_response",
                                metadata={"direct_action": "add_to_cart"}
                            )
                            continue  # Skip normal message processing

                    if form_type == "direct_update_cart":
                        # Direct quantity update from CartCard +/- buttons
                        # Uses SQL session_cart (same store as AI agent tools)
                        item_name = form_data.get("item_name", "")
                        new_quantity = int(form_data.get("quantity", 1))
                        if item_name and new_quantity > 0:
                            from app.core.db_pool import SyncDBConnection
                            from app.core.agui_events import emit_cart_data

                            with SyncDBConnection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(
                                        """UPDATE session_cart
                                           SET quantity = %s, updated_at = NOW()
                                           WHERE session_id = %s AND LOWER(item_name) = LOWER(%s) AND is_active = TRUE""",
                                        (new_quantity, session_id, item_name)
                                    )
                                    conn.commit()

                                    # Get updated cart
                                    cur.execute("SELECT * FROM get_session_cart(%s)", (session_id,))
                                    columns = [desc[0] for desc in cur.description] if cur.description else []
                                    items_list = [dict(zip(columns, row)) for row in cur.fetchall()]

                                    cur.execute("SELECT get_cart_total(%s)", (session_id,))
                                    total_row = cur.fetchone()
                                    new_total = float(total_row[0]) if total_row and total_row[0] else 0.0

                            emit_cart_data(session_id, items_list, new_total)
                            from app.core.agui_events import flush_pending_events
                            flush_pending_events(session_id)
                            await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=1.0)
                            continue

                    if form_type == "direct_remove_from_cart":
                        # Direct item removal from CartCard delete button
                        # Uses SQL session_cart (same store as AI agent tools)
                        item_name = form_data.get("item_name", "")
                        if item_name:
                            from app.core.db_pool import SyncDBConnection
                            from app.core.agui_events import emit_cart_data

                            with SyncDBConnection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute(
                                        """UPDATE session_cart
                                           SET is_active = FALSE, updated_at = NOW()
                                           WHERE session_id = %s AND LOWER(item_name) = LOWER(%s) AND is_active = TRUE""",
                                        (session_id, item_name)
                                    )
                                    conn.commit()

                                    # Get updated cart
                                    cur.execute("SELECT * FROM get_session_cart(%s)", (session_id,))
                                    columns = [desc[0] for desc in cur.description] if cur.description else []
                                    items_list = [dict(zip(columns, row)) for row in cur.fetchall()]

                                    cur.execute("SELECT get_cart_total(%s)", (session_id,))
                                    total_row = cur.fetchone()
                                    new_total = float(total_row[0]) if total_row and total_row[0] else 0.0

                            emit_cart_data(session_id, items_list, new_total)
                            from app.core.agui_events import flush_pending_events
                            flush_pending_events(session_id)
                            await stream_agui_events_to_websocket(session_id, websocket_manager, timeout=1.0)
                            continue
                # ========================================================================

                # Check rate limit before processing
                is_allowed, messages_remaining = websocket_manager.check_rate_limit(session_id)

                if not is_allowed:
                    # Rate limit exceeded - send warning message
                    await websocket_manager.send_message(
                        session_id=session_id,
                        message=f"WARNING: You're sending messages too quickly. Please wait a moment before sending another message. (Limit: {websocket_manager.rate_limit_messages} messages per minute)",
                        message_type="system_message"
                    )
                    logger.warning(f"Rate limit exceeded for session {session_id}")
                    continue

                # Update analytics and activity time
                if session_id in websocket_manager.connection_metadata:
                    websocket_manager.connection_metadata[session_id]["messages_received"] += 1
                    websocket_manager.connection_metadata[session_id]["last_activity"] = datetime.now(timezone.utc)

                # Log user message for admin analytics
                log_chat_message(
                    session_id=session_id,
                    message_type="user_message",
                    content=user_message,
                    metadata={"received_successfully": True, "messages_remaining": messages_remaining}
                )

                logger.info(f"Received message from session {session_id}: {len(user_message)} characters (remaining: {messages_remaining})")

                # Send "processing" indicator to keep connection alive during AI processing
                try:
                    await websocket_manager.send_message(
                        session_id=session_id,
                        message="typing",
                        message_type="typing_indicator"
                    )
                except Exception as e:
                    logger.warning(f"Failed to send typing indicator: {str(e)}")

                # ========================================================================
                # PENDING PAYMENT HANDLER — intercept ALL messages during pending payment
                # ========================================================================
                # When there's a pending payment:
                # - Cancel text ("cancel payment") → clear payment state, show cart, continue
                # - Payment text ("pay now", "complete payment") → re-show Razorpay link
                # - Any other message → remind about pending payment with link + cancel quick replies
                try:
                    from app.services.payment_state_service import get_payment_state as _gps, PaymentStep as _PStep
                    _pstate = _gps(session_id)
                    if (_pstate.get("step") == _PStep.AWAITING_PAYMENT.value
                            and _pstate.get("order_id")):
                        _pay_order_id = _pstate["order_id"]
                        _pay_amount = _pstate.get("amount", 0)
                        _pay_link = _pstate.get("payment_link", "")
                        _msg_lower = user_message.lower().strip()

                        # Check for cancel intent
                        _cancel_phrases = [
                            "cancel", "cancel payment", "cancel order",
                            "cancel my order", "don't want", "dont want",
                            "never mind", "nevermind", "yes cancel",
                            "yes, cancel",
                        ]
                        _is_cancel = any(p in _msg_lower for p in _cancel_phrases)

                        if _is_cancel:
                            # Clear payment state and let user continue
                            from app.services.payment_state_service import clear_payment_state
                            clear_payment_state(session_id)
                            await websocket_manager.send_message_with_metadata(
                                session_id=session_id,
                                message=(
                                    f"Payment for order **{_pay_order_id}** has been cancelled.\n\n"
                                    f"Your cart items are still saved. What would you like to do?"
                                ),
                                message_type="ai_response",
                                metadata={"direct_action": "payment_cancelled"}
                            )
                            # Show helpful quick replies after cancellation
                            import json as _json
                            from app.core.agui_events import QuickRepliesEvent
                            _cancel_qr = QuickRepliesEvent(replies=[
                                {"label": "🛒 View Cart", "action": "view cart"},
                                {"label": "🍔 Show Menu", "action": "show menu"},
                                {"label": "✅ Checkout", "action": "checkout"},
                            ])
                            await websocket_manager.send_message_with_metadata(
                                session_id=session_id,
                                message="",
                                message_type="agui_event",
                                metadata={"agui": _json.loads(_cancel_qr.to_json())}
                            )
                            logger.info("payment_cancelled_by_user", session_id=session_id, order_id=_pay_order_id)
                            continue

                        # Check for "complete payment" / "pay now" → re-show Razorpay link
                        _complete_phrases = ["complete payment", "no, complete", "no complete", "finish payment", "pay now", "pay online"]
                        _is_complete = any(p in _msg_lower for p in _complete_phrases)
                        if _is_complete:
                            await websocket_manager.send_message_with_metadata(
                                session_id=session_id,
                                message=(
                                    f"Your payment link for order **{_pay_order_id}** (₹{_pay_amount:.0f}):\n\n"
                                    f"👉 [Pay Now with Razorpay]({_pay_link})\n\n"
                                    f"Click the link above to complete your payment."
                                ),
                                message_type="ai_response",
                                metadata={"direct_action": "payment_pending_redirect"}
                            )
                            logger.info("payment_pending_redirect", session_id=session_id, order_id=_pay_order_id)
                            continue

                        # Any other message → remind about pending payment with Razorpay link
                        await websocket_manager.send_message_with_metadata(
                            session_id=session_id,
                            message=(
                                f"You have a pending payment for order **{_pay_order_id}** (₹{_pay_amount:.0f}).\n\n"
                                f"👉 [Pay Now with Razorpay]({_pay_link})\n\n"
                                f"Would you like to cancel it instead?"
                            ),
                            message_type="ai_response",
                            metadata={"direct_action": "payment_pending_confirm_cancel"}
                        )
                        # Show quick reply buttons for cancel / complete payment
                        import json as _json
                        from app.core.agui_events import QuickRepliesEvent
                        _confirm_qr = QuickRepliesEvent(replies=[
                            {"label": "Yes, cancel payment", "action": "yes cancel"},
                            {"label": "No, complete payment", "action": "complete payment"},
                        ])
                        await websocket_manager.send_message_with_metadata(
                            session_id=session_id,
                            message="",
                            message_type="agui_event",
                            metadata={"agui": _json.loads(_confirm_qr.to_json())}
                        )
                        logger.info("payment_pending_cancel_prompt", session_id=session_id, order_id=_pay_order_id)
                        continue
                except Exception as _ptf_err:
                    logger.warning("payment_pending_handler_error", error=str(_ptf_err))
                # ========================================================================

                # Clear stale events from previous processing cycles so they
                # don't leak into the new response stream.
                try:
                    from app.core.agui_events import clear_event_queue
                    clear_event_queue(session_id)
                except Exception:
                    pass

                # ============ TESTING MODULE - Metadata Streaming ============
                # WARNING: This section can be removed when manual testing is complete
                # Check if this is a testing session and use enhanced processing
                if session_id.startswith("test-"):
                    from app.api.routes.testing_middleware import testing_middleware

                    # Get tester_id from connection metadata
                    tester_id = None
                    welcome_msg_from_metadata = None
                    if session_id in websocket_manager.connection_metadata:
                        tester_id = websocket_manager.connection_metadata[session_id].get("tester_id")
                        welcome_msg_from_metadata = websocket_manager.connection_metadata[session_id].get("welcome_msg")

                    # Process with testing middleware (streams metadata + saves to MongoDB)
                    # Capture language in closure for translation
                    lang = language
                    ai_response, cycle_metadata = await testing_middleware.process_and_log_testing_message(
                        user_message=user_message,
                        session_id=session_id,
                        user_id=tester_id,
                        process_message_func=lambda msg, sid: process_message_with_ai(msg, sid, device_id, session_token, welcome_msg_from_metadata, lang),
                        websocket_manager=websocket_manager
                    )

                    # Clear welcome message after first use
                    if welcome_msg_from_metadata and session_id in websocket_manager.connection_metadata:
                        websocket_manager.connection_metadata[session_id].pop("welcome_msg", None)
                else:
                    # Normal production processing
                    # Get welcome message from connection metadata (only for first message)
                    welcome_msg_from_metadata = None
                    if session_id in websocket_manager.connection_metadata:
                        welcome_msg_from_metadata = websocket_manager.connection_metadata[session_id].get("welcome_msg")

                    ai_response, cycle_metadata = await process_message_with_ai(
                        user_message,
                        session_id,
                        device_id,
                        session_token,
                        welcome_msg_from_metadata,
                        language=language  # Pass language for translation before AGUI streaming
                    )

                    # Clear welcome message after first use
                    if welcome_msg_from_metadata and session_id in websocket_manager.connection_metadata:
                        websocket_manager.connection_metadata[session_id].pop("welcome_msg", None)
                # ============ END TESTING MODULE ============

                # ========================================================================
                # UPDATE CONNECTION METADATA WITH USER_ID (Phase 3 Integration)
                # ========================================================================
                # Store user_id in connection metadata for inventory cleanup on disconnect
                if cycle_metadata and "user_id" in cycle_metadata:
                    user_id_from_state = cycle_metadata.get("user_id")
                    if user_id_from_state and session_id in websocket_manager.connection_metadata:
                        # Update connection metadata with user_id
                        websocket_manager.connection_metadata[session_id]["user_id"] = user_id_from_state
                        logger.debug(
                            "websocket_connection_user_authenticated",
                            session_id=session_id,
                            user_id=user_id_from_state
                        )
                # ========================================================================

                # NOTE: Response is already streamed via AGUI (TEXT_MESSAGE events) with translation
                # Do NOT send again via send_message_with_metadata to avoid duplicate messages
                logger.info(
                    "ASSISTANT RESPONSE (session: %s...)\n%s",
                    session_id[:12] if session_id else "unknown",
                    ai_response[:100] + "..." if len(ai_response) > 100 else ai_response
                )

                # Get or create conversation and save messages for context
                try:
                    conn_metadata = websocket_manager.connection_metadata.get(session_id, {})
                    tenant_id = conn_metadata.get("restaurant_id", "unknown")

                    # Try to get existing conversation from session
                    conversation = None
                    session_for_conv = await session_manager.get_session(session_id)
                    if session_for_conv and session_for_conv.metadata:
                        active_conv_id = session_for_conv.metadata.get('active_conversation')
                        if active_conv_id:
                            conversation = await session_manager.get_conversation(active_conv_id)

                    # Create new conversation only if none exists
                    if not conversation:
                        conversation = await session_manager.create_conversation(
                            session_id=session_id,
                            tenant_id=tenant_id,
                            user_id=session_data.user_id if session_data else None
                        )
                        logger.debug(f"Created new conversation {conversation.conversation_id} for session {session_id}")

                    # Add the user message to conversation
                    await session_manager.add_message(
                        conversation_id=conversation.conversation_id,
                        role="user",
                        content=user_message,
                        detected_intent="general_inquiry",
                        intent_confidence=0.8
                    )

                    # Add AI response to conversation
                    await session_manager.add_message(
                        conversation_id=conversation.conversation_id,
                        role="assistant",
                        content=ai_response
                    )

                except Exception as e:
                    logger.warning(f"Failed to save conversation for session {session_id}: {str(e)}")

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for session: {session_id}")
                break
            except RuntimeError as e:
                # Handle WebSocket already closed errors
                if "WebSocket is not connected" in str(e) or "accept" in str(e):
                    logger.info(f"WebSocket closed during processing for session: {session_id}")
                    break
                logger.error(f"Runtime error for session {session_id}: {str(e)}")
            except Exception as e:
                error_msg = str(e)
                # Don't try to send messages if WebSocket is disconnected
                if "WebSocket is not connected" in error_msg or "accept" in error_msg:
                    logger.info(f"WebSocket closed for session: {session_id}")
                    break

                logger.error(f"Error processing message for session {session_id}: {error_msg}")
                # Only send error message if session is still connected
                if session_id in websocket_manager.active_connections:
                    try:
                        await websocket_manager.send_message(
                            session_id=session_id,
                            message="I apologize, but I encountered an error. Please try again.",
                            message_type="system_message"
                        )
                    except Exception:
                        # If sending fails, connection is dead - exit loop
                        break

    except Exception as e:
        logger.error(f"WebSocket connection error for session {session_id}: {str(e)}")

    finally:
        # Clean up connection (pass websocket to prevent removing a newer connection)
        await websocket_manager.disconnect(session_id, websocket)
        logger.info(f"WebSocket connection closed for session: {session_id}")


async def stream_agui_events_to_websocket(
    session_id: str,
    websocket_mgr: WebSocketManager,
    timeout: float = 30.0
):
    """
    Background task to stream AG-UI events from the queue to WebSocket.

    This runs concurrently with message processing and forwards all AG-UI
    events (ACTIVITY_START, TOOL_CALL_START, etc.) to the frontend via WebSocket.
    """
    from app.core.agui_events import get_event_queue
    import asyncio

    queue = get_event_queue(session_id)
    start_time = asyncio.get_event_loop().time()

    try:
        while True:
            # Check if session is still connected
            if session_id not in websocket_mgr.active_connections:
                logger.debug("agui_stream_stopped_disconnected", session_id=session_id)
                break

            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.debug("agui_stream_timeout", session_id=session_id)
                break

            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=0.5)

                # Check again before sending (connection could have closed)
                if session_id not in websocket_mgr.active_connections:
                    break

                # Convert event to JSON and send via WebSocket
                event_json = event.to_json()
                event_data = json.loads(event_json)

                # Send as special message type for AG-UI events
                # Include session_id in metadata for frontend validation
                await websocket_mgr.send_message_with_metadata(
                    session_id=session_id,
                    message="",  # Empty message - data is in metadata
                    message_type="agui_event",
                    metadata={
                        "agui": event_data,
                        "target_session": session_id  # Explicit session target for debugging
                    }
                )

                # Log FORM_REQUEST events at INFO level for debugging session isolation
                if event_data.get("type") == "FORM_REQUEST":
                    logger.info(
                        "FORM_EVENT_SENT",
                        target_session=session_id,
                        form_type=event_data.get("form_type"),
                        form_metadata=event_data.get("metadata", {})
                    )
                else:
                    logger.debug(
                        "agui_event_forwarded",
                        session_id=session_id,
                        event_type=event_data.get("type")
                    )

                # Stop on terminal events
                if event_data.get("type") in ["RUN_FINISHED", "RUN_ERROR"]:
                    break

            except asyncio.TimeoutError:
                # No event available, continue checking
                continue

    except asyncio.CancelledError:
        # Task was cancelled, exit gracefully
        logger.debug("agui_stream_cancelled", session_id=session_id)
    except Exception as e:
        # Don't log WebSocket disconnection as error
        if "WebSocket is not connected" not in str(e) and "accept" not in str(e):
            logger.error("agui_stream_error", session_id=session_id, error=str(e))


async def process_message_with_ai(
    message: str,
    session_id: str,
    device_id: Optional[str] = None,
    session_token: Optional[str] = None,
    welcome_msg: Optional[str] = None,
    language: str = "English"
) -> tuple[str, dict]:
    """
    Process user message with Unified Restaurant Crew + AG-UI Streaming.

    AG-UI STREAMING:
    - Real-time events sent to frontend via WebSocket
    - Activity indicators (thinking, searching, adding)
    - Tool call visibility
    - Streaming text response

    Performance: ~2-3 seconds per message
    """
    import asyncio

    try:
        # Import AG-UI streaming version
        from app.orchestration.restaurant_crew import process_with_agui_streaming
        from app.core.agui_events import AGUIEventEmitter
        from app.services.session_manager import SessionManager

        logger.info(
            "Using Restaurant Crew with AG-UI streaming",
            session_id=session_id,
            language=language  # DEBUG: Trace language through call chain
        )

        # Create session manager for conversation history
        session_manager = SessionManager()

        # Create AG-UI emitter for this session
        emitter = AGUIEventEmitter(session_id)

        # Start background task to forward AG-UI events to WebSocket
        agui_task = asyncio.create_task(
            stream_agui_events_to_websocket(session_id, websocket_manager, timeout=60.0)
        )

        # Build conversation history from Redis session storage
        # Only include recent messages (last 30 minutes) to prevent stale context
        conversation_history = []
        try:
            from datetime import datetime, timezone, timedelta
            context_window = timedelta(minutes=30)  # Only use messages from last 30 mins
            now = datetime.now(timezone.utc)

            # Retrieve conversation from Redis for context
            session_data = await session_manager.get_session(session_id)
            if session_data and session_data.metadata and session_data.metadata.get('active_conversation'):
                conversation_id = session_data.metadata['active_conversation']
                conversation = await session_manager.get_conversation(conversation_id)
                if conversation and conversation.messages:
                    # Filter to recent messages only, then take last 6
                    recent_messages = []
                    for msg in conversation.messages:
                        msg_time = msg.get('timestamp')
                        if msg_time:
                            try:
                                if isinstance(msg_time, str):
                                    msg_dt = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                                else:
                                    msg_dt = msg_time
                                if now - msg_dt < context_window:
                                    recent_messages.append(msg)
                            except:
                                pass  # Skip messages with invalid timestamps
                        else:
                            recent_messages.append(msg)  # Include if no timestamp

                    # Format last N messages for LLM context (last 6 messages = 3 exchanges)
                    for msg in recent_messages[-6:]:
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                        if role == 'user':
                            conversation_history.append(f"User: {content}")
                        elif role == 'assistant':
                            conversation_history.append(f"Assistant: {content}")
                    logger.debug(
                        "conversation_history_loaded",
                        session_id=session_id,
                        message_count=len(conversation_history),
                        context_window_minutes=30
                    )
        except Exception as e:
            logger.warning(f"Failed to load conversation history: {str(e)}")
            conversation_history = []

        # =====================================================================
        # AI AGENT PROCESSING
        # Agent handles all messages including payment method selection.
        # No interceptor — agent calls tools (select_payment_method,
        # initiate_payment, etc.) which trigger deterministic workflows.
        # =====================================================================
        if True:
            try:
                # Process message with AG-UI streaming
                # Pass user_id from authenticated session (available after OTP verification at session start)
                authenticated_user_id = session_data.user_id if session_data and session_data.is_authenticated else None
                # Read source from connection metadata (set once at connection time)
                _conn_meta = websocket_manager.connection_metadata.get(session_id, {})
                _source = _conn_meta.get("source", "web")

                ai_response, cycle_metadata = await process_with_agui_streaming(
                    user_message=message,
                    session_id=session_id,
                    conversation_history=conversation_history,
                    emitter=emitter,
                    user_id=authenticated_user_id,
                    welcome_msg=welcome_msg,
                    language=language,
                    source=_source
                )
            finally:
                # Wait for event stream to finish naturally (flush queue)
                # This ensures "View Cart" events are sent before closing connection
                if not agui_task.done():
                    try:
                        # Give it time to flush remaining events (e.g. 2.0 seconds)
                        # The stream task should finish when RUN_FINISHED is seen
                        await asyncio.wait_for(agui_task, timeout=2.0)
                    except (asyncio.TimeoutError, asyncio.CancelledError):
                        # If it's still running after timeout, force close
                        if not agui_task.done():
                            agui_task.cancel()
                            try:
                                await agui_task
                            except asyncio.CancelledError:
                                pass
                    except Exception as e:
                        logger.warning(f"Error waiting for event stream: {str(e)}")

        # SECURITY: Sanitize crew response before sending to frontend
        from app.core.response_sanitizer import sanitize_response
        ai_response = sanitize_response(ai_response)

        # Log cycle metadata for analytics
        logger.info(
            "Restaurant Crew completed",
            session_id=session_id,
            cycle_type=cycle_metadata.get("type"),
            orchestrator=cycle_metadata.get("orchestrator")
        )

        return ai_response, cycle_metadata

    except Exception as e:
        # Fallback error handling with simple response
        logger.error(
            "Restaurant crew failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )

        # SECURITY: Convert technical error to user-friendly message
        from app.core.response_sanitizer import sanitize_error
        fallback_response = sanitize_error(e)

        return fallback_response, {
            "type": "fallback",
            "intent": "system_error",
            "confidence": 0.0,
            "agent_used": "system_fallback",
            "orchestrator": "error_fallback"
        }


@router.get("/chat/stats")
async def get_chat_stats():
    """
    Get WebSocket connection statistics
    Admin-ready: Provides real-time connection analytics
    """
    try:
        stats = websocket_manager.get_connection_stats()

        log_system_event(
            "chat_stats_requested",
            {"active_connections": stats["total_active_connections"]}
        )

        return {
            "success": True,
            "message": "Chat statistics retrieved",
            "data": stats,
            "timestamp": get_ist_timestamp()
        }

    except Exception as e:
        logger.error(f"Failed to get chat stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve chat statistics",
                "error": str(e)
            }
        )


@router.get("/monitor/status")
async def get_monitoring_status():
    """
    Get comprehensive system monitoring status for concurrent testing
    Includes: active sessions, DB pool, resource usage
    """
    try:
        # Get WebSocket stats
        ws_stats = websocket_manager.get_connection_stats()

        # Get database pool stats
        from app.core.database import db_manager

        db_stats = {}
        if db_manager.engine:
            pool = db_manager.engine.pool
            db_stats = {
                "pool_size": pool.size(),
                "checked_out_connections": pool.checkedout(),
                "overflow_connections": pool.overflow(),
                "total_available": pool.size() - pool.checkedout()
            }

        # Calculate session activity
        active_count = 0
        idle_count = 0
        now = datetime.now(timezone.utc)

        for session_id, metadata in ws_stats["connection_metadata"].items():
            last_activity = metadata.get("last_activity")
            if last_activity:
                idle_minutes = (now - last_activity).total_seconds() / 60
                if idle_minutes < 5:  # Active if activity within 5 minutes
                    active_count += 1
                else:
                    idle_count += 1

        return {
            "success": True,
            "timestamp": get_ist_timestamp(),
            "system_status": {
                "websocket": {
                    "total_connections": ws_stats["total_active_connections"],
                    "active_sessions": active_count,
                    "idle_sessions": idle_count,
                    "session_ids": ws_stats["active_sessions"]
                },
                "database": db_stats,
                "health": "healthy" if db_stats.get("total_available", 0) > 5 else "degraded"
            }
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to retrieve monitoring status",
                "error": str(e)
            }
        )
