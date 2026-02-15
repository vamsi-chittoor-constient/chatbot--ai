"""
AG-UI Event Emitter
===================
Implements AG-UI protocol for real-time streaming to frontend.

Events emitted:
- RunStarted/RunFinished: Lifecycle events
- TextMessageStart/Content/End: Streaming text responses
- ToolCallStart/Args/Result/End: Tool execution visibility
- StateSnapshot/StateDelta: State synchronization

Usage:
    emitter = AGUIEventEmitter(session_id)
    async for event in emitter.stream():
        yield f"data: {event}\\n\\n"
"""

import json
import uuid
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, AsyncGenerator, List
from dataclasses import dataclass, field, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


# ============================================================================
# VOICE MODE ISOLATION
# ============================================================================
# When voice mode is active for a session, events are routed to the voice
# WebSocket instead of the chat queue. This keeps the two systems isolated.

_VOICE_MODE_SESSIONS: Dict[str, Any] = {}  # session_id -> websocket
_RUN_FINISHED_SESSIONS: set = set()  # Sessions where run has finished - block late ACTIVITY_START


def set_voice_mode(session_id: str, websocket=None):
    """
    Enable or disable voice mode for a session.

    Args:
        session_id: The session ID
        websocket: The voice WebSocket connection (None to disable)
    """
    if websocket is not None:
        _VOICE_MODE_SESSIONS[session_id] = websocket
        logger.debug("voice_mode_enabled", session_id=session_id)
    else:
        _VOICE_MODE_SESSIONS.pop(session_id, None)
        logger.debug("voice_mode_disabled", session_id=session_id)


def is_voice_mode(session_id: str) -> bool:
    """Check if voice mode is active for a session."""
    return session_id in _VOICE_MODE_SESSIONS


def get_voice_websocket(session_id: str):
    """Get the voice WebSocket for a session (if in voice mode)."""
    return _VOICE_MODE_SESSIONS.get(session_id)


async def _emit_to_voice_websocket(session_id: str, event_type: str, data: Dict[str, Any]):
    """Send an event through the voice WebSocket."""
    ws = get_voice_websocket(session_id)
    if ws is None:
        return False

    try:
        import asyncio
        # Send as AGUI event through voice WebSocket
        asyncio.create_task(ws.send_json({
            "type": "agui_event",
            "agui": {
                "type": event_type,
                **data
            }
        }))
        return True
    except Exception as e:
        logger.debug("voice_websocket_emit_failed", session_id=session_id, error=str(e))
        return False


def _emit_to_voice_websocket_sync(session_id: str, event_type: str, data: Dict[str, Any]):
    """Send an event through the voice WebSocket (sync wrapper)."""
    ws = get_voice_websocket(session_id)
    if ws is None:
        return False

    try:
        import asyncio
        # Schedule the send on the event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(
                ws.send_json({
                    "type": "agui_event",
                    "agui": {
                        "type": event_type,
                        **data
                    }
                }),
                loop
            )
        return True
    except Exception as e:
        logger.debug("voice_websocket_emit_sync_failed", session_id=session_id, error=str(e))
        return False


class EventType(str, Enum):
    """AG-UI Event Types"""
    # Lifecycle
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    RUN_ERROR = "RUN_ERROR"
    STEP_STARTED = "STEP_STARTED"
    STEP_FINISHED = "STEP_FINISHED"

    # Text Messages
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"

    # Tool Calls
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS = "TOOL_CALL_ARGS"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_CALL_RESULT = "TOOL_CALL_RESULT"

    # State
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    STATE_DELTA = "STATE_DELTA"

    # Activity (for typing indicators)
    ACTIVITY_START = "ACTIVITY_START"
    ACTIVITY_END = "ACTIVITY_END"

    # Artifacts (for downloadable files like receipts)
    ARTIFACT = "ARTIFACT"

    # Interactive Forms (for payment, feedback, etc.)
    FORM_REQUEST = "FORM_REQUEST"
    FORM_SUBMITTED = "FORM_SUBMITTED"
    FORM_DISMISS = "FORM_DISMISS"

    # Rich Content (for visual cards)
    CART_DATA = "CART_DATA"
    ORDER_DATA = "ORDER_DATA"
    MENU_DATA = "MENU_DATA"
    SEARCH_RESULTS = "SEARCH_RESULTS"  # For search results with availability info
    QUICK_REPLIES = "QUICK_REPLIES"
    PAYMENT_LINK = "PAYMENT_LINK"
    PAYMENT_METHOD_SELECTION = "PAYMENT_METHOD_SELECTION"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    RECEIPT_LINK = "RECEIPT_LINK"


@dataclass
class AGUIEvent:
    """Base AG-UI Event"""
    type: EventType
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_json(self) -> str:
        data = asdict(self)
        data['type'] = self.type.value
        return json.dumps(data)


@dataclass
class RunStartedEvent(AGUIEvent):
    """Emitted when agent run begins"""
    type: EventType = EventType.RUN_STARTED
    run_id: str = ""
    thread_id: str = ""


@dataclass
class RunFinishedEvent(AGUIEvent):
    """Emitted when agent run completes"""
    type: EventType = EventType.RUN_FINISHED
    run_id: str = ""
    result: Optional[str] = None


@dataclass
class RunErrorEvent(AGUIEvent):
    """Emitted when agent run fails"""
    type: EventType = EventType.RUN_ERROR
    run_id: str = ""
    message: str = ""
    code: Optional[str] = None


@dataclass
class TextMessageStartEvent(AGUIEvent):
    """Emitted when assistant starts responding"""
    type: EventType = EventType.TEXT_MESSAGE_START
    message_id: str = ""
    role: str = "assistant"


@dataclass
class TextMessageContentEvent(AGUIEvent):
    """Emitted for each text chunk (streaming)"""
    type: EventType = EventType.TEXT_MESSAGE_CONTENT
    message_id: str = ""
    delta: str = ""


@dataclass
class TextMessageEndEvent(AGUIEvent):
    """Emitted when message is complete"""
    type: EventType = EventType.TEXT_MESSAGE_END
    message_id: str = ""


@dataclass
class ToolCallStartEvent(AGUIEvent):
    """Emitted when tool execution begins - uses friendly action name"""
    type: EventType = EventType.TOOL_CALL_START
    tool_call_id: str = ""
    action: str = ""  # User-friendly action name (NOT internal tool name)


@dataclass
class ToolCallArgsEvent(AGUIEvent):
    """Emitted with tool context - sanitized for user display"""
    type: EventType = EventType.TOOL_CALL_ARGS
    tool_call_id: str = ""
    context: str = ""  # User-friendly context (NOT raw args)


@dataclass
class ToolCallResultEvent(AGUIEvent):
    """Emitted with action result - sanitized for user display"""
    type: EventType = EventType.TOOL_CALL_RESULT
    tool_call_id: str = ""
    summary: str = ""  # User-friendly summary (NOT raw result)


@dataclass
class ToolCallEndEvent(AGUIEvent):
    """Emitted when action completes"""
    type: EventType = EventType.TOOL_CALL_END
    tool_call_id: str = ""


@dataclass
class ActivityStartEvent(AGUIEvent):
    """Emitted to show typing/thinking indicator"""
    type: EventType = EventType.ACTIVITY_START
    activity_type: str = "thinking"  # thinking, searching, adding, etc.
    message: str = ""


@dataclass
class ActivityEndEvent(AGUIEvent):
    """Emitted to hide activity indicator"""
    type: EventType = EventType.ACTIVITY_END


# Single source of truth for packaging charge - used by backend checkout and frontend CartCard
PACKAGING_CHARGE_PER_ITEM = 30


@dataclass
class CartDataEvent(AGUIEvent):
    """Emitted with cart data for rich UI display"""
    type: EventType = EventType.CART_DATA
    items: List[Dict[str, Any]] = field(default_factory=list)
    total: float = 0.0
    packaging_charge_per_item: int = PACKAGING_CHARGE_PER_ITEM


@dataclass
class OrderDataEvent(AGUIEvent):
    """Emitted with order data for rich UI display"""
    type: EventType = EventType.ORDER_DATA
    order_id: str = ""
    items: List[Dict[str, Any]] = field(default_factory=list)
    total: float = 0.0
    status: str = ""
    order_type: str = ""


@dataclass
class MenuDataEvent(AGUIEvent):
    """Emitted with menu data for rich UI display with categories"""
    type: EventType = EventType.MENU_DATA
    items: List[Dict[str, Any]] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    current_meal_period: str = ""  # Breakfast, Lunch, Dinner, or All Day
    show_meal_filters: bool = True  # Show breakfast/lunch/dinner tabs (False for filtered views)
    show_popular_tab: bool = False  # Popular items feature disabled


@dataclass
class SearchResultsEvent(AGUIEvent):
    """
    Emitted with search results showing items with availability info.

    Used when user searches for specific items (e.g., "parota").
    Shows all matching items with per-item availability status.
    """
    type: EventType = EventType.SEARCH_RESULTS
    query: str = ""  # What the user searched for
    items: List[Dict[str, Any]] = field(default_factory=list)  # Items with is_available_now, meal_types
    current_meal_period: str = ""  # Current meal period (Breakfast, Lunch, Dinner)
    available_count: int = 0  # How many items are available now
    unavailable_count: int = 0  # How many items are NOT available now


@dataclass
class QuickRepliesEvent(AGUIEvent):
    """
    Emitted with quick reply options for the user.

    Each reply has:
    - label: Display text for the button
    - action: The message to send when clicked
    - icon: Optional icon name (food, cart, checkout, etc.)
    - variant: Button style (primary, secondary, success, danger)
    """
    type: EventType = EventType.QUICK_REPLIES
    replies: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class PaymentLinkEvent(AGUIEvent):
    """
    Emitted with Razorpay payment link for online payment.

    Contains:
    - payment_link: Razorpay payment link URL
    - amount: Payment amount in rupees
    - expires_at: Payment link expiry timestamp
    """
    type: EventType = EventType.PAYMENT_LINK
    payment_link: str = ""
    amount: float = 0.0
    expires_at: str = ""


@dataclass
class PaymentMethodSelectionEvent(AGUIEvent):
    """
    Emitted with payment method selection options (card UI).

    Contains:
    - methods: List of payment methods with label, action, description
    - amount: Order total amount
    - order_id: Order display ID
    """
    type: EventType = EventType.PAYMENT_METHOD_SELECTION
    methods: List[Dict[str, str]] = field(default_factory=list)
    amount: float = 0.0
    order_id: str = ""


@dataclass
class PaymentSuccessEvent(AGUIEvent):
    """
    Emitted when payment is successfully completed.

    Contains:
    - order_id: Order display ID
    - order_number: Order invoice number
    - amount: Payment amount
    - payment_id: Razorpay payment ID
    - order_type: dine_in or takeaway
    - quick_replies: Next action buttons (View Receipt, Track Order, etc.)
    """
    type: EventType = EventType.PAYMENT_SUCCESS
    order_id: str = ""
    order_number: str = ""
    amount: float = 0.0
    payment_id: str = ""
    order_type: str = "takeaway"
    quick_replies: List[Dict[str, str]] = field(default_factory=list)


@dataclass
class ReceiptLinkEvent(AGUIEvent):
    """
    Emitted with a downloadable PDF receipt link.

    Contains:
    - order_number: Order display ID
    - amount: Total amount paid
    - download_url: URL to download the PDF receipt
    - items: List of order items with name, qty, price
    """
    type: EventType = EventType.RECEIPT_LINK
    order_number: str = ""
    amount: float = 0.0
    download_url: str = ""
    items: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class StateSnapshotEvent(AGUIEvent):
    """Emitted with full state"""
    type: EventType = EventType.STATE_SNAPSHOT
    state: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArtifactEvent(AGUIEvent):
    """
    Emitted when a downloadable artifact is available.

    Used for:
    - Order receipts
    - Booking confirmations
    - Any other downloadable content

    Frontend can render this as a download link or preview.
    """
    type: EventType = EventType.ARTIFACT
    artifact_id: str = ""
    artifact_type: str = "text"  # text, pdf, image
    filename: str = ""
    content: str = ""  # Base64 encoded for binary, plain text otherwise
    mime_type: str = "text/plain"
    title: str = ""  # User-friendly title
    description: str = ""  # Optional description


@dataclass
class FormRequestEvent(AGUIEvent):
    """
    Emitted when the agent needs user input via an interactive form.

    Used for:
    - Payment card entry forms
    - OTP verification
    - Feedback forms
    - Any structured input collection

    Frontend renders this as an interactive form in the chat.
    Form submission triggers FORM_SUBMITTED event back to server.
    """
    type: EventType = EventType.FORM_REQUEST
    form_id: str = ""
    form_type: str = ""  # payment_card, otp_verify, feedback, etc.
    title: str = ""
    description: str = ""
    fields: List[Dict[str, Any]] = field(default_factory=list)
    # Field format: {"name": "card_number", "type": "card", "label": "Card Number", "required": true}
    submit_label: str = "Submit"
    cancel_label: str = "Cancel"
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extra data like order_id, amount


@dataclass
class FormSubmittedEvent(AGUIEvent):
    """
    Emitted when user submits a form (received from frontend).

    This event is sent FROM the frontend TO the server.
    """
    type: EventType = EventType.FORM_SUBMITTED
    form_id: str = ""
    form_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)  # Form field values
    cancelled: bool = False


@dataclass
class FormDismissEvent(AGUIEvent):
    """
    Emitted to dismiss/hide forms of specified types.

    This event is sent FROM the server TO the frontend to remove
    forms from the UI (e.g., after successful authentication).
    """
    type: EventType = EventType.FORM_DISMISS
    form_types: List[str] = field(default_factory=list)


# Global event queues per session
_EVENT_QUEUES: Dict[str, asyncio.Queue] = {}
# Store event loops for thread-safe operations
_EVENT_LOOPS: Dict[str, asyncio.AbstractEventLoop] = {}

# ============================================================================
# THREAD-SAFE STAGING AREA FOR TOOL EVENTS
# ============================================================================
# Tool events (SEARCH_RESULTS, MENU_DATA) are emitted from sync contexts
# (CrewAI tools in thread pool). Instead of using call_soon_threadsafe which
# can race with RUN_FINISHED, we stage events here and flush them explicitly.
import threading
_PENDING_EVENTS: Dict[str, List["AGUIEvent"]] = {}  # session_id -> list of events
_PENDING_LOCK = threading.Lock()


def get_event_queue(session_id: str) -> asyncio.Queue:
    """Get or create event queue for session."""
    if session_id not in _EVENT_QUEUES:
        _EVENT_QUEUES[session_id] = asyncio.Queue()
        # Store the event loop that created this queue for thread-safe puts
        try:
            _EVENT_LOOPS[session_id] = asyncio.get_running_loop()
        except RuntimeError:
            pass  # No running loop - will be set later
    return _EVENT_QUEUES[session_id]


def clear_event_queue(session_id: str):
    """Clear event queue for session."""
    if session_id in _EVENT_QUEUES:
        del _EVENT_QUEUES[session_id]
    if session_id in _EVENT_LOOPS:
        del _EVENT_LOOPS[session_id]


def _put_event_threadsafe(session_id: str, event: "AGUIEvent"):
    """
    Thread-safe staging of events for later flush.

    Called from sync contexts (like CrewAI tools running in thread pool).
    Events are staged in _PENDING_EVENTS and flushed explicitly before RUN_FINISHED.
    This guarantees tool events (SEARCH_RESULTS, MENU_DATA) reach the queue
    before RUN_FINISHED, preventing race conditions.
    """
    with _PENDING_LOCK:
        if session_id not in _PENDING_EVENTS:
            _PENDING_EVENTS[session_id] = []
        _PENDING_EVENTS[session_id].append(event)
        # INFO level for visibility during testing
        logger.info("event_staged", session_id=session_id, event_type=event.type.value,
                    pending_count=len(_PENDING_EVENTS[session_id]))


def flush_pending_events(session_id: str) -> int:
    """
    Flush all pending tool events to the queue. MUST be called before RUN_FINISHED.

    This function is called from async context (process_with_agui_streaming)
    and synchronously moves all staged events into the asyncio.Queue.

    Returns:
        Number of events flushed
    """
    queue = get_event_queue(session_id)
    flushed_count = 0

    with _PENDING_LOCK:
        events = _PENDING_EVENTS.pop(session_id, [])

    for event in events:
        try:
            queue.put_nowait(event)
            flushed_count += 1
            logger.info("event_flushed", session_id=session_id, event_type=event.type.value)
        except Exception as e:
            logger.error("event_flush_failed", session_id=session_id, event_type=event.type.value, error=str(e))

    if flushed_count > 0:
        logger.info("events_flushed_total", session_id=session_id, count=flushed_count)
    else:
        logger.info("no_events_to_flush", session_id=session_id)

    return flushed_count


class AGUIEventEmitter:
    """
    AG-UI Event Emitter for streaming events to frontend.

    Usage:
        emitter = AGUIEventEmitter(session_id)

        # Emit events during processing
        emitter.emit_run_started()
        emitter.emit_tool_start("search_menu", {"query": "burger"})
        emitter.emit_tool_result("search_menu", "Found 5 items...")
        emitter.emit_text_chunk("How many ")
        emitter.emit_text_chunk("would you like?")
        emitter.emit_run_finished()
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.run_id = str(uuid.uuid4())[:8]
        self.current_message_id: Optional[str] = None
        self.current_tool_call_id: Optional[str] = None
        self.queue = get_event_queue(session_id)

    def _emit(self, event: AGUIEvent):
        """Put event in queue for streaming."""
        try:
            self.queue.put_nowait(event)
            logger.debug("agui_event_emitted",
                        session_id=self.session_id,
                        event_type=event.type.value)
        except Exception as e:
            logger.error("agui_emit_failed", error=str(e))

    def _emit_sync_safe(self, activity_type: str, message: str):
        """
        Thread-safe emit for use in sync contexts (like CrewAI executor).

        Can be called from sync code running in a thread pool executor.
        """
        try:
            event = ActivityStartEvent(
                activity_type=activity_type,
                message=message
            )
            self.queue.put_nowait(event)
            logger.debug("sync_event_emitted",
                        session_id=self.session_id,
                        activity_type=activity_type)
        except Exception as e:
            logger.error("sync_emit_failed", error=str(e))

    # =========================================================================
    # LIFECYCLE EVENTS
    # =========================================================================

    def emit_run_started(self):
        """Emit when agent processing begins."""
        _RUN_FINISHED_SESSIONS.discard(self.session_id)
        self._emit(RunStartedEvent(
            run_id=self.run_id,
            thread_id=self.session_id
        ))

    def emit_run_finished(self, result: Optional[str] = None):
        """Emit when agent processing completes."""
        # Mark session as finished - blocks any late ACTIVITY_START from tools
        _RUN_FINISHED_SESSIONS.add(self.session_id)

        # End any open message
        if self.current_message_id:
            self.emit_text_end()

        self._emit(RunFinishedEvent(
            run_id=self.run_id,
            result=result
        ))

    def emit_run_error(self, message: str, code: Optional[str] = None):
        """Emit when agent processing fails."""
        self._emit(RunErrorEvent(
            run_id=self.run_id,
            message=message,
            code=code
        ))

    # =========================================================================
    # TEXT MESSAGE EVENTS (Streaming Response)
    # =========================================================================

    def emit_text_start(self, role: str = "assistant"):
        """Start a new text message stream."""
        self.current_message_id = str(uuid.uuid4())[:8]
        self._emit(TextMessageStartEvent(
            message_id=self.current_message_id,
            role=role
        ))

    def emit_text_chunk(self, delta: str):
        """Emit a text chunk (for streaming)."""
        if not self.current_message_id:
            self.emit_text_start()

        self._emit(TextMessageContentEvent(
            message_id=self.current_message_id,
            delta=delta
        ))

    def emit_text_end(self):
        """End the current text message."""
        if self.current_message_id:
            self._emit(TextMessageEndEvent(
                message_id=self.current_message_id
            ))
            self.current_message_id = None

    def emit_full_text(self, text: str, chunk_size: int = 0):
        """
        Emit a complete text message.
        If chunk_size > 0, splits into chunks for streaming effect.
        """
        self.emit_text_start()

        if chunk_size > 0:
            # Stream in chunks
            words = text.split(' ')
            for i, word in enumerate(words):
                self.emit_text_chunk(word + (' ' if i < len(words) - 1 else ''))
        else:
            # Single chunk
            self.emit_text_chunk(text)

        self.emit_text_end()

    # =========================================================================
    # TOOL CALL EVENTS
    # =========================================================================

    def emit_tool_start(self, tool_name: str, args: Optional[Dict[str, Any]] = None):
        """
        Emit when a tool starts executing.

        IMPORTANT: Converts internal tool_name to user-friendly action.
        Never exposes internal tool names or raw arguments to frontend.
        """
        self.current_tool_call_id = str(uuid.uuid4())[:8]

        # Convert internal tool name to friendly action
        friendly_action = get_tool_activity_message(tool_name)

        self._emit(ToolCallStartEvent(
            tool_call_id=self.current_tool_call_id,
            action=friendly_action  # User-friendly, not internal name
        ))

        # Only emit sanitized context, not raw args
        if args:
            # Create user-friendly context from args
            context = _sanitize_args_for_display(tool_name, args)
            if context:
                self._emit(ToolCallArgsEvent(
                    tool_call_id=self.current_tool_call_id,
                    context=context
                ))

    def emit_tool_result(self, result: str):
        """
        Emit tool execution result.

        IMPORTANT: Sanitizes result to not expose internal details.
        """
        if self.current_tool_call_id:
            # Sanitize result for user display
            summary = _sanitize_result_for_display(result)
            self._emit(ToolCallResultEvent(
                tool_call_id=self.current_tool_call_id,
                summary=summary
            ))

    def emit_tool_end(self):
        """Emit when tool execution completes."""
        if self.current_tool_call_id:
            self._emit(ToolCallEndEvent(
                tool_call_id=self.current_tool_call_id
            ))
            self.current_tool_call_id = None

    # =========================================================================
    # ACTIVITY EVENTS (Typing Indicators)
    # =========================================================================

    def emit_activity(self, activity_type: str, message: str):
        """Emit activity indicator (e.g., 'thinking', 'searching')."""
        self._emit(ActivityStartEvent(
            activity_type=activity_type,
            message=message
        ))

    def emit_activity_end(self):
        """End activity indicator."""
        self._emit(ActivityEndEvent())

    # =========================================================================
    # STATE EVENTS
    # =========================================================================

    def emit_state_snapshot(self, state: Dict[str, Any]):
        """Emit full state snapshot."""
        self._emit(StateSnapshotEvent(state=state))

    # =========================================================================
    # RICH CONTENT EVENTS (Cards for Cart, Menu, Order) - IMMEDIATE
    # =========================================================================

    def emit_cart_data(self, items: List[Dict[str, Any]], total: float):
        """
        Emit cart data for rich UI display - IMMEDIATE (not scheduled).

        Use this in async contexts where timing matters.
        For sync contexts (CrewAI tools), use the global emit_cart_data() function.
        """
        self._emit(CartDataEvent(items=items, total=total))
        logger.debug("cart_data_emitted_immediate",
                    session_id=self.session_id, items_count=len(items), total=total)

    def emit_menu_data(self, items: List[Dict[str, Any]], categories: List[str] = None,
                       current_meal_period: str = "", show_meal_filters: bool = True):
        """
        Emit menu data for rich UI display - IMMEDIATE (not scheduled).

        Use this in async contexts where timing matters.
        For sync contexts (CrewAI tools), use the global emit_menu_data() function.
        """
        if categories is None:
            categories = list(set(item.get("category", "Other") for item in items))
            categories.sort()

        # Count recommended items to determine if Popular Items tab should be shown
        recommended_count = sum(1 for item in items if item.get("is_recommended", False))
        show_popular_tab = False  # Popular items feature disabled

        self._emit(MenuDataEvent(
            items=items,
            categories=categories,
            current_meal_period=current_meal_period,
            show_meal_filters=show_meal_filters,
            show_popular_tab=show_popular_tab
        ))
        logger.debug("menu_data_emitted_immediate",
                    session_id=self.session_id, items_count=len(items),
                    recommended_count=recommended_count, show_popular_tab=show_popular_tab)

    def emit_order_data(self, order_id: str, items: List[Dict[str, Any]],
                        total: float, status: str, order_type: str = ""):
        """
        Emit order data for rich UI display - IMMEDIATE (not scheduled).
        """
        self._emit(OrderDataEvent(
            order_id=order_id,
            items=items,
            total=total,
            status=status,
            order_type=order_type
        ))
        logger.debug("order_data_emitted_immediate",
                    session_id=self.session_id, order_id=order_id)

    def emit_quick_replies(self, replies: List[Dict[str, str]]):
        """
        Emit quick reply options - IMMEDIATE (not scheduled).

        This is the synchronous version that puts directly into the queue.
        Use this in async contexts where timing matters (before response streaming).

        For thread-safe use from sync contexts (like CrewAI tools), use the
        global emit_quick_replies() function instead.
        """
        if not replies:
            return

        self._emit(QuickRepliesEvent(replies=replies))
        logger.debug("quick_replies_emitted_immediate",
                    session_id=self.session_id, replies_count=len(replies))

    # =========================================================================
    # ARTIFACT EVENTS (Downloadable Files)
    # =========================================================================

    def emit_artifact(
        self,
        content: str,
        filename: str,
        title: str = "",
        description: str = "",
        artifact_type: str = "text",
        mime_type: str = "text/plain"
    ):
        """
        Emit a downloadable artifact (e.g., receipt, confirmation).

        Args:
            content: The artifact content (plain text or base64 for binary)
            filename: Suggested filename for download
            title: User-friendly title shown in UI
            description: Optional description
            artifact_type: Type of artifact (text, pdf, image)
            mime_type: MIME type for download
        """
        artifact_id = str(uuid.uuid4())[:8]

        self._emit(ArtifactEvent(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            filename=filename,
            content=content,
            mime_type=mime_type,
            title=title or filename,
            description=description
        ))

        logger.info(
            "artifact_emitted",
            session_id=self.session_id,
            artifact_id=artifact_id,
            filename=filename,
            content_length=len(content)
        )

    # =========================================================================
    # FORM REQUEST EVENTS (Interactive Forms in Chat)
    # =========================================================================

    def emit_payment_form(
        self,
        order_id: str,
        amount: float,
        order_display_id: str = ""
    ) -> str:
        """
        Emit a payment card entry form.

        Returns the form_id for tracking the submission.
        """
        form_id = str(uuid.uuid4())[:8]

        self._emit(FormRequestEvent(
            form_id=form_id,
            form_type="payment_card",
            title="Enter Payment Details",
            description=f"Complete payment of Rs.{amount:.0f} for order {order_display_id}",
            fields=[
                {"name": "card_number", "type": "card", "label": "Card Number", "required": True,
                 "placeholder": "1234 5678 9012 3456", "maxLength": 19},
                {"name": "expiry", "type": "text", "label": "Expiry (MM/YY)", "required": True,
                 "placeholder": "MM/YY", "maxLength": 5},
                {"name": "cvv", "type": "password", "label": "CVV", "required": True,
                 "placeholder": "***", "maxLength": 4},
                {"name": "card_holder", "type": "text", "label": "Cardholder Name", "required": True,
                 "placeholder": "Name on card"},
            ],
            submit_label="Pay Now",
            cancel_label="Cancel Payment",
            metadata={
                "order_id": order_id,
                "order_display_id": order_display_id,
                "amount": amount,
                "currency": "INR"
            }
        ))

        logger.info(
            "payment_form_emitted",
            session_id=self.session_id,
            form_id=form_id,
            order_id=order_id,
            amount=amount
        )

        return form_id

    def emit_otp_form(
        self,
        payment_transaction_id: str,
        masked_phone: str = "",
        order_display_id: str = ""
    ) -> str:
        """
        Emit an OTP verification form.

        Returns the form_id for tracking the submission.
        """
        form_id = str(uuid.uuid4())[:8]

        self._emit(FormRequestEvent(
            form_id=form_id,
            form_type="otp_verify",
            title="Verify OTP",
            description=f"Enter the OTP sent to {masked_phone or 'your registered mobile'}",
            fields=[
                {"name": "otp", "type": "otp", "label": "Enter 6-digit OTP", "required": True,
                 "placeholder": "______", "maxLength": 6, "minLength": 6},
            ],
            submit_label="Verify & Pay",
            cancel_label="Cancel",
            metadata={
                "payment_transaction_id": payment_transaction_id,
                "order_display_id": order_display_id,
                "hint": "For testing, use OTP: 123456"
            }
        ))

        logger.info(
            "otp_form_emitted",
            session_id=self.session_id,
            form_id=form_id,
            payment_transaction_id=payment_transaction_id
        )

        return form_id

    def emit_phone_auth_form(self, restaurant_name: str = "our restaurant") -> str:
        """
        Emit a phone number collection form for authentication.

        This is sent on connect when AUTH_REQUIRED=True and user is not authenticated.

        Returns the form_id for tracking the submission.
        """
        form_id = str(uuid.uuid4())[:8]

        self._emit(FormRequestEvent(
            form_id=form_id,
            form_type="phone_auth",
            title="Welcome!",
            description=f"Please enter your mobile number to continue to {restaurant_name}",
            fields=[
                {"name": "phone", "type": "tel", "label": "Mobile Number", "required": True,
                 "placeholder": "+91 XXXXX XXXXX", "maxLength": 15},
            ],
            submit_label="Continue",
            cancel_label="",  # No cancel option for auth
            metadata={
                "purpose": "authentication",
                "restaurant_name": restaurant_name
            }
        ))

        logger.info(
            "phone_auth_form_emitted",
            session_id=self.session_id,
            form_id=form_id
        )

        return form_id

    def emit_login_otp_form(self, phone_number: str) -> str:
        """
        Emit an OTP verification form for login/registration.

        This is sent after phone number is submitted for a new user.

        Returns the form_id for tracking the submission.
        """
        form_id = str(uuid.uuid4())[:8]

        # Mask phone number for display
        masked_phone = f"XXXXXX{phone_number[-4:]}" if len(phone_number) >= 4 else phone_number

        self._emit(FormRequestEvent(
            form_id=form_id,
            form_type="login_otp",
            title="Verify Your Number",
            description=f"Enter the OTP sent to {masked_phone}",
            fields=[
                {"name": "otp", "type": "otp", "label": "Enter 6-digit OTP", "required": True,
                 "placeholder": "______", "maxLength": 6, "minLength": 6},
            ],
            submit_label="Verify",
            cancel_label="Change Number",
            metadata={
                "phone_number": phone_number,
                "masked_phone": masked_phone,
                "hint": "For testing, use OTP: 123456",
                "session_id": self.session_id  # DEBUG: Track which session created this form
            }
        ))

        logger.info(
            "login_otp_form_emitted",
            session_id=self.session_id,
            form_id=form_id,
            masked_phone=masked_phone
        )

        return form_id

    def emit_name_collection_form(self, phone_number: str) -> str:
        """
        Emit a name collection form after OTP verification for new users.

        This is sent after OTP is verified to collect the user's name
        for personalization in future visits.

        Returns the form_id for tracking the submission.
        """
        form_id = str(uuid.uuid4())[:8]

        self._emit(FormRequestEvent(
            form_id=form_id,
            form_type="name_collection",
            title="Almost there!",
            description="What should we call you?",
            fields=[
                {"name": "name", "type": "text", "label": "Your Name", "required": True,
                 "placeholder": "Enter your name", "maxLength": 50, "minLength": 2},
            ],
            submit_label="Continue",
            cancel_label="Skip",
            metadata={
                "phone_number": phone_number,
                "hint": "This helps us personalize your experience"
            }
        ))

        logger.info(
            "name_collection_form_emitted",
            session_id=self.session_id,
            form_id=form_id
        )

        return form_id

    def emit_form_dismiss(self, form_types: List[str]) -> None:
        """
        Emit an event to dismiss/hide forms of specified types.

        This is used after authentication completes to hide the auth forms.
        """
        self._emit(FormDismissEvent(
            form_types=form_types
        ))

        logger.info(
            "form_dismiss_emitted",
            session_id=self.session_id,
            form_types=form_types
        )

    def emit_custom_form(
        self,
        form_type: str,
        title: str,
        description: str,
        fields: List[Dict[str, Any]],
        submit_label: str = "Submit",
        cancel_label: str = "Cancel",
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Emit a custom form for any structured input collection.

        Returns the form_id for tracking the submission.
        """
        form_id = str(uuid.uuid4())[:8]

        self._emit(FormRequestEvent(
            form_id=form_id,
            form_type=form_type,
            title=title,
            description=description,
            fields=fields,
            submit_label=submit_label,
            cancel_label=cancel_label,
            metadata=metadata or {}
        ))

        logger.info(
            "custom_form_emitted",
            session_id=self.session_id,
            form_id=form_id,
            form_type=form_type
        )

        return form_id


# ============================================================================
# STREAMING GENERATOR
# ============================================================================

async def stream_events(session_id: str, timeout: float = 60.0) -> AsyncGenerator[str, None]:
    """
    Async generator that yields SSE-formatted events.

    Usage in FastAPI:
        @app.get("/api/chat/stream/{session_id}")
        async def stream(session_id: str):
            return StreamingResponse(
                stream_events(session_id),
                media_type="text/event-stream"
            )
    """
    queue = get_event_queue(session_id)
    start_time = asyncio.get_event_loop().time()

    try:
        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > timeout:
                logger.debug("agui_stream_timeout", session_id=session_id)
                break

            try:
                # Wait for event with timeout
                event = await asyncio.wait_for(queue.get(), timeout=1.0)

                # Format as SSE
                yield f"data: {event.to_json()}\n\n"

                # Check if run finished
                if event.type in (EventType.RUN_FINISHED, EventType.RUN_ERROR):
                    break

            except asyncio.TimeoutError:
                # Send keepalive
                yield ": keepalive\n\n"
                continue

    except Exception as e:
        logger.error("agui_stream_error", session_id=session_id, error=str(e))
        error_event = RunErrorEvent(message=str(e))
        yield f"data: {error_event.to_json()}\n\n"
    finally:
        # Cleanup
        clear_event_queue(session_id)


# ============================================================================
# USER-FRIENDLY ACTIVITY MESSAGES
# ============================================================================
# IMPORTANT: These messages are shown to end users.
# Do NOT expose internal tool names, architecture, or technical details.

TOOL_ACTIVITY_MESSAGES = {
    # Food ordering - friendly messages
    "search_menu": "Looking through our menu...",
    "add_to_cart": "Adding that to your order...",
    "view_cart": "Checking your order...",
    "remove_from_cart": "Updating your order...",
    "checkout": "Finalizing your order...",
    "cancel_order": "Processing cancellation...",
    "clear_cart": "Clearing your order...",
    "update_quantity": "Updating your order...",
    "set_special_instructions": "Noting your preferences...",
    "get_item_details": "Getting more details...",

    # Order status and history
    "get_order_status": "Checking your order status...",
    "get_order_history": "Looking up your order history...",
    "reorder": "Adding items from your previous order...",
    "get_order_receipt": "Generating your receipt...",

    # Payment - friendly messages
    "initiate_payment": "Preparing payment...",
    "submit_card_details": "Processing your card...",
    "verify_payment_otp": "Verifying OTP...",
    "complete_payment": "Completing payment...",
    "check_payment_status": "Checking payment status...",
    "cancel_payment": "Cancelling payment...",

    # Booking - friendly messages
    "check_table_availability": "Checking table availability...",
    "make_reservation": "Booking your table...",
    "get_my_bookings": "Looking up your reservations...",
    "modify_reservation": "Updating your reservation...",
    "cancel_reservation": "Processing cancellation...",
}

# Generic fallback messages (no technical terms)
GENERIC_ACTIVITY_MESSAGES = [
    "Working on that...",
    "Just a moment...",
    "Processing...",
]


def get_tool_activity_message(tool_name: str) -> str:
    """
    Get user-friendly activity message for a tool.

    IMPORTANT: Never expose internal tool names to users.
    """
    return TOOL_ACTIVITY_MESSAGES.get(tool_name, "Working on that...")


# ============================================================================
# ASYNC EMIT FUNCTIONS (for async CrewAI tools - preferred, no thread overhead)
# ============================================================================

async def emit_tool_activity_async(session_id: str, tool_name: str):
    """
    Emit activity for a tool execution from async context.

    This is the preferred method for async CrewAI tools - no thread-safe
    overhead since we're in the same event loop.

    Args:
        session_id: The session ID
        tool_name: Internal tool name (will be converted to user-friendly message)
    """
    # Don't emit ACTIVITY_START after run has finished
    if session_id in _RUN_FINISHED_SESSIONS:
        return

    try:
        message = TOOL_ACTIVITY_MESSAGES.get(tool_name, "Working on that...")
        activity_type = _get_activity_type_for_tool(tool_name)

        event = ActivityStartEvent(
            activity_type=activity_type,
            message=message
        )

        # Direct queue put - no thread-safe overhead needed in async context
        queue = get_event_queue(session_id)
        await queue.put(event)

        logger.debug(
            "async_tool_activity_emitted",
            session_id=session_id,
            tool_name=tool_name,
            message=message
        )
    except Exception as e:
        logger.debug("async_tool_activity_emit_failed", error=str(e))


async def emit_activity_end_async(session_id: str):
    """
    Emit activity end to hide the loading indicator from async context.

    Call this at the end of each async tool to clear the hamburger animation.

    Args:
        session_id: The session ID
    """
    try:
        event = ActivityEndEvent()
        queue = get_event_queue(session_id)
        await queue.put(event)
        logger.debug("async_activity_end_emitted", session_id=session_id)
    except Exception as e:
        logger.debug("async_activity_end_emit_failed", error=str(e))


async def emit_cart_data_async(session_id: str, items: List[Dict[str, Any]], total: float):
    """
    Emit cart data for rich UI display from async context.

    Args:
        session_id: The session ID
        items: List of cart items with name, quantity, price
        total: Cart total amount
    """
    try:
        # Sanitize Decimal values to float for JSON serialization
        sanitized_items = _sanitize_cart_items(items)
        sanitized_total = _convert_decimal(total)

        event = CartDataEvent(items=sanitized_items, total=sanitized_total)
        queue = get_event_queue(session_id)
        await queue.put(event)

        logger.debug(
            "async_cart_data_emitted",
            session_id=session_id,
            items_count=len(items),
            total=total
        )
    except Exception as e:
        logger.debug("async_cart_data_emit_failed", error=str(e))


async def emit_menu_data_async(session_id: str, items: List[Dict[str, Any]],
                               categories: List[str] = None, current_meal_period: str = "", show_meal_filters: bool = True):
    """
    Emit menu data for rich UI display from async context.

    Args:
        session_id: The session ID
        items: List of menu items
        categories: List of categories
        current_meal_period: Current meal period
        show_meal_filters: Whether to show breakfast/lunch/dinner tabs (False for filtered views)
    """
    try:
        if categories is None:
            categories = list(set(item.get("category", "Other") for item in items))
            categories.sort()

        # Count recommended items to determine if Popular Items tab should be shown
        recommended_count = sum(1 for item in items if item.get("is_recommended", False))
        show_popular_tab = False  # Popular items feature disabled

        event = MenuDataEvent(
            items=items,
            categories=categories,
            current_meal_period=current_meal_period,
            show_meal_filters=show_meal_filters,
            show_popular_tab=show_popular_tab
        )
        queue = get_event_queue(session_id)
        await queue.put(event)

        logger.debug(
            "async_menu_data_emitted",
            session_id=session_id,
            items_count=len(items),
            recommended_count=recommended_count,
            show_popular_tab=show_popular_tab
        )
    except Exception as e:
        logger.debug("async_menu_data_emit_failed", error=str(e))


async def emit_order_data_async(session_id: str, order_id: str, items: List[Dict[str, Any]],
                                total: float, status: str, order_type: str = ""):
    """
    Emit order data for rich UI display from async context.

    Args:
        session_id: The session ID
        order_id: Order display ID
        items: List of order items
        total: Order total
        status: Order status
        order_type: dine_in or take_away
    """
    try:
        event = OrderDataEvent(
            order_id=order_id,
            items=items,
            total=total,
            status=status,
            order_type=order_type
        )
        queue = get_event_queue(session_id)
        await queue.put(event)

        logger.debug(
            "async_order_data_emitted",
            session_id=session_id,
            order_id=order_id
        )
    except Exception as e:
        logger.debug("async_order_data_emit_failed", error=str(e))


async def emit_quick_replies_async(session_id: str, replies: List[Dict[str, str]]):
    """
    Emit quick reply options from async context.

    Args:
        session_id: The session ID
        replies: List of reply objects with label, action, icon, variant
    """
    try:
        if not replies:
            return

        event = QuickRepliesEvent(replies=replies)
        queue = get_event_queue(session_id)
        await queue.put(event)

        logger.debug(
            "async_quick_replies_emitted",
            session_id=session_id,
            replies_count=len(replies)
        )
    except Exception as e:
        logger.debug("async_quick_replies_emit_failed", error=str(e))


# ============================================================================
# TOOL ACTIVITY WRAPPER - Auto-emit ACTIVITY_END
# ============================================================================

def with_activity_tracking(session_id: str, tool_name: str):
    """
    Decorator/context to automatically emit ACTIVITY_START and ACTIVITY_END.

    This ensures the hamburger animation always clears after tool execution,
    even if the tool throws an exception.

    Usage:
        @with_activity_tracking(session_id, "search_menu")
        def my_tool_logic():
            # ... tool code ...
            return result
    """
    from contextlib import contextmanager
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            emit_tool_activity(session_id, tool_name)
            try:
                return func(*args, **kwargs)
            finally:
                emit_activity_end(session_id)
        return wrapper
    return decorator


# ============================================================================
# SYNC EMIT FUNCTIONS (legacy - kept for backwards compatibility)
# ============================================================================

def emit_tool_activity(session_id: str, tool_name: str):
    """
    Emit activity for a tool execution from sync context (legacy).

    DEPRECATED: Use emit_tool_activity_async() in async tools instead.
    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        tool_name: Internal tool name (will be converted to user-friendly message)
    """
    # Don't emit ACTIVITY_START after run has finished
    if session_id in _RUN_FINISHED_SESSIONS:
        return

    message = TOOL_ACTIVITY_MESSAGES.get(tool_name, "Working on that...")
    activity_type = _get_activity_type_for_tool(tool_name)

    # Route to voice WebSocket if in voice mode
    if is_voice_mode(session_id):
        _emit_to_voice_websocket_sync(session_id, "ACTIVITY_START", {
            "activity_type": activity_type,
            "message": message
        })
        return

    try:
        event = ActivityStartEvent(
            activity_type=activity_type,
            message=message
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.debug(
            "tool_activity_emitted",
            session_id=session_id,
            tool_name=tool_name,
            message=message
        )
    except Exception as e:
        # Don't fail tool execution if activity emission fails
        logger.debug("tool_activity_emit_failed", error=str(e))


def emit_activity_end(session_id: str):
    """
    Emit activity end to hide the loading indicator.

    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.
    Call this at the end of each tool to clear the hamburger animation.

    Args:
        session_id: The session ID
    """
    # Route to voice WebSocket if in voice mode
    if is_voice_mode(session_id):
        _emit_to_voice_websocket_sync(session_id, "ACTIVITY_END", {})
        return

    try:
        event = ActivityEndEvent()
        _put_event_threadsafe(session_id, event)
        logger.debug("activity_end_emitted", session_id=session_id)
    except Exception as e:
        logger.debug("activity_end_emit_failed", error=str(e))


from contextlib import contextmanager

@contextmanager
def tool_activity(session_id: str, tool_name: str):
    """
    Context manager that automatically emits ACTIVITY_START and ACTIVITY_END.
    
    Usage:
        with tool_activity(session_id, "search_menu"):
            # tool logic here
            return result
    """
    emit_tool_activity(session_id, tool_name)
    try:
        yield
    finally:
        emit_activity_end(session_id)


def _convert_decimal(value):
    """Convert Decimal to float for JSON serialization."""
    from decimal import Decimal
    if isinstance(value, Decimal):
        return float(value)
    return value


def _sanitize_cart_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sanitize cart items by converting Decimal values to float and normalizing keys.

    The DB returns 'item_name' but the frontend CartCard expects 'name'.
    """
    sanitized = []
    for item in items:
        sanitized_item = {}
        for key, value in item.items():
            sanitized_item[key] = _convert_decimal(value)
        # Map item_name → name for frontend compatibility
        if "item_name" in sanitized_item and "name" not in sanitized_item:
            sanitized_item["name"] = sanitized_item["item_name"]
        sanitized.append(sanitized_item)
    return sanitized


def emit_cart_data(session_id: str, items: List[Dict[str, Any]], total: float):
    """
    Emit cart data for rich UI display from sync context.

    This is called when view_cart is executed to send structured cart data
    that the frontend can render as a visual card.
    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        items: List of cart items with name, quantity, price
        total: Cart total amount
    """
    # Sanitize Decimal values to float for JSON serialization
    sanitized_items = _sanitize_cart_items(items)
    sanitized_total = _convert_decimal(total)

    # Route to voice WebSocket if in voice mode
    if is_voice_mode(session_id):
        _emit_to_voice_websocket_sync(session_id, "CART_DATA", {
            "items": sanitized_items,
            "total": sanitized_total
        })
        return

    try:
        event = CartDataEvent(
            items=sanitized_items,
            total=sanitized_total
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.debug(
            "cart_data_emitted",
            session_id=session_id,
            items_count=len(items),
            total=total
        )
    except Exception as e:
        logger.debug("cart_data_emit_failed", error=str(e))


def emit_order_data(session_id: str, order_id: str, items: List[Dict[str, Any]],
                    total: float, status: str, order_type: str = ""):
    """
    Emit order data for rich UI display from sync context.

    This is called after checkout to send structured order data
    that the frontend can render as a visual card.
    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        order_id: Order display ID (e.g., ORD-ABC12345)
        items: List of order items
        total: Order total amount
        status: Order status (confirmed, preparing, ready, etc.)
        order_type: dine_in or take_away
    """
    # Sanitize Decimal values to float for JSON serialization
    sanitized_items = _sanitize_cart_items(items)
    sanitized_total = _convert_decimal(total)

    # Route to voice WebSocket if in voice mode
    if is_voice_mode(session_id):
        _emit_to_voice_websocket_sync(session_id, "ORDER_DATA", {
            "order_id": order_id,
            "items": sanitized_items,
            "total": sanitized_total,
            "status": status,
            "order_type": order_type
        })
        return

    try:
        event = OrderDataEvent(
            order_id=order_id,
            items=sanitized_items,
            total=sanitized_total,
            status=status,
            order_type=order_type
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.debug(
            "order_data_emitted",
            session_id=session_id,
            order_id=order_id,
            status=status
        )
    except Exception as e:
        logger.debug("order_data_emit_failed", error=str(e))


def emit_menu_data(session_id: str, items: List[Dict[str, Any]], categories: List[str] = None, current_meal_period: str = "", show_meal_filters: bool = True):
    """
    Emit menu data for rich UI display from sync context.

    This is called when show_menu is executed to send structured menu data
    that the frontend can render as a visual categorized menu card.
    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        items: List of menu items with name, price, category, meal_types
        categories: List of unique categories
        current_meal_period: Current meal period (Breakfast, Lunch, Dinner) for default tab
        show_meal_filters: Whether to show breakfast/lunch/dinner tabs (False for filtered views)
    """
    # Route to voice WebSocket if in voice mode
    if is_voice_mode(session_id):
        if categories is None:
            categories = list(set(item.get("category", "Other") for item in items))
            categories.sort()
        _emit_to_voice_websocket_sync(session_id, "MENU_DATA", {
            "items": items,
            "categories": categories,
            "current_meal_period": current_meal_period
        })
        return

    try:
        # Extract unique categories if not provided
        if categories is None:
            categories = list(set(item.get("category", "Other") for item in items))
            categories.sort()

        # Count recommended items to determine if Popular Items tab should be shown
        recommended_count = sum(1 for item in items if item.get("is_recommended", False))
        show_popular_tab = False  # Popular items feature disabled

        event = MenuDataEvent(
            items=items,
            categories=categories,
            current_meal_period=current_meal_period,
            show_meal_filters=show_meal_filters,
            show_popular_tab=show_popular_tab
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.debug(
            "menu_data_emitted",
            session_id=session_id,
            items_count=len(items),
            categories=categories,
            current_meal_period=current_meal_period,
            recommended_count=recommended_count,
            show_popular_tab=show_popular_tab
        )
    except Exception as e:
        logger.debug("menu_data_emit_failed", error=str(e))


def emit_search_results(
    session_id: str,
    query: str,
    items: List[Dict[str, Any]],
    current_meal_period: str,
    available_count: int,
    unavailable_count: int
):
    """
    Emit search results with per-item availability info.

    Used when user searches for specific items (e.g., "parota").
    Each item should have:
    - name, price, category, meal_types
    - is_available_now: bool (computed before calling)

    Args:
        session_id: The session ID
        query: What the user searched for
        items: List of items with availability info
        current_meal_period: Current meal period
        available_count: Number of items available now
        unavailable_count: Number of items NOT available now
    """
    # Route to voice WebSocket if in voice mode
    if is_voice_mode(session_id):
        _emit_to_voice_websocket_sync(session_id, "SEARCH_RESULTS", {
            "query": query,
            "items": items,
            "current_meal_period": current_meal_period,
            "available_count": available_count,
            "unavailable_count": unavailable_count
        })
        return

    try:
        event = SearchResultsEvent(
            query=query,
            items=items,
            current_meal_period=current_meal_period,
            available_count=available_count,
            unavailable_count=unavailable_count
        )

        _put_event_threadsafe(session_id, event)

        logger.debug(
            "search_results_emitted",
            session_id=session_id,
            query=query,
            items_count=len(items),
            available=available_count,
            unavailable=unavailable_count,
            meal_period=current_meal_period
        )
    except Exception as e:
        logger.debug("search_results_emit_failed", error=str(e))


def emit_quick_replies(session_id: str, replies: List[Dict[str, str]]):
    """
    Emit quick reply options for the user to click.

    This provides structured quick replies from the backend,
    eliminating the need for fragile regex-based detection in the frontend.
    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        replies: List of reply objects with label, action, icon, variant

    Example:
        emit_quick_replies(session_id, [
            {"label": "Coca Cola", "action": "Coca Cola", "icon": "food", "variant": "success"},
            {"label": "Orange Juice", "action": "Orange Juice", "icon": "food", "variant": "success"},
            {"label": "No thanks", "action": "no thanks", "icon": "no", "variant": "secondary"},
        ])
    """
    try:
        event = QuickRepliesEvent(replies=replies)

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.debug(
            "quick_replies_emitted",
            session_id=session_id,
            replies_count=len(replies)
        )
    except Exception as e:
        logger.debug("quick_replies_emit_failed", error=str(e))


def emit_payment_link(session_id: str, payment_link: str, amount: float, expires_at: str = ""):
    """
    Emit Razorpay payment link for online payment.

    This provides a secure payment link from Razorpay that supports
    multiple payment methods (cards, UPI, net banking, wallets, etc.)

    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        payment_link: Razorpay payment link URL
        amount: Payment amount in rupees
        expires_at: Payment link expiry timestamp (ISO format)

    Example:
        emit_payment_link(session_id, "https://rzp.io/l/abc123", 450.0, "2025-01-01T12:00:00Z")
    """
    try:
        event = PaymentLinkEvent(
            payment_link=payment_link,
            amount=amount,
            expires_at=expires_at
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.debug(
            "payment_link_emitted",
            session_id=session_id,
            amount=amount,
            link_length=len(payment_link)
        )
    except Exception as e:
        logger.error("payment_link_emit_failed", error=str(e), session_id=session_id)


def emit_payment_method_selection(session_id: str, methods: List[Dict[str, str]], amount: float, order_id: str = ""):
    """
    Emit payment method selection card for visual UI.

    This provides a card-based UI (similar to menu card) for users to select
    their preferred payment method visually instead of using quick reply buttons.

    Thread-safe: uses _put_event_threadsafe() for cross-thread queue operations.

    Args:
        session_id: The session ID
        methods: List of payment method objects with label, action, description
        amount: Order total amount
        order_id: Order display ID

    Example:
        emit_payment_method_selection(session_id, [
            {
                "label": "💳 Pay Online",
                "action": "pay_online",
                "description": "Secure payment via Razorpay (Card/UPI/NetBanking)"
            },
            {
                "label": "💵 Cash",
                "action": "pay_cash",
                "description": "Pay cash on delivery or at counter"
            },
            {
                "label": "💳 Card at Counter",
                "action": "pay_card_counter",
                "description": "Pay by card when you arrive"
            }
        ], 450.0, "ORD-ABC12345")
    """
    try:
        event = PaymentMethodSelectionEvent(
            methods=methods,
            amount=amount,
            order_id=order_id
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        # Set flag in Redis to prevent quick replies from overriding payment card
        # This flag is checked in _emit_response_quick_replies()
        from app.core.redis import get_sync_redis_client
        redis_client = get_sync_redis_client()
        redis_client.setex(f"payment_card_shown:{session_id}", 300, "1")  # 5 min TTL

        logger.info(
            "payment_method_selection_emitted",
            session_id=session_id,
            methods_count=len(methods),
            amount=amount,
            order_id=order_id
        )
    except Exception as e:
        logger.error("payment_method_selection_emit_failed", error=str(e), session_id=session_id)


def emit_payment_success(
    session_id: str,
    order_id: str,
    order_number: str,
    amount: float,
    payment_id: str,
    order_type: str = "takeaway",
    quick_replies: List[Dict[str, str]] = None
):
    """
    Emit payment success confirmation card with quick replies for next actions.

    Args:
        session_id: The session ID
        order_id: Order UUID
        order_number: Order invoice number (e.g., ORD-ABC123)
        amount: Payment amount
        payment_id: Razorpay payment ID
        order_type: dine_in or takeaway
        quick_replies: Next action buttons (View Receipt, Track Order, etc.)

    Example:
        emit_payment_success(
            session_id="sess_123",
            order_id="ab2a4a30-e7e5-42bb-b736-ab72c538c78a",
            order_number="ORD-EB85D444",
            amount=270.0,
            payment_id="pay_S0ZryXDgxz1p2z",
            order_type="takeaway",
            quick_replies=[
                {"label": "📄 View Receipt", "action": "view_receipt"},
                {"label": "📦 Track Order", "action": "track_order"},
                {"label": "🍽️ Order More", "action": "order_more"}
            ]
        )
    """
    try:
        if quick_replies is None:
            quick_replies = [
                {"label": "📄 View Receipt", "action": "view_receipt"},
                {"label": "📦 Track Order", "action": "track_order"},
                {"label": "🍽️ Order More", "action": "order_more"}
            ]

        event = PaymentSuccessEvent(
            order_id=order_id,
            order_number=order_number,
            amount=amount,
            payment_id=payment_id,
            order_type=order_type,
            quick_replies=quick_replies
        )

        # Use thread-safe put for cross-thread operation
        _put_event_threadsafe(session_id, event)

        logger.info(
            "payment_success_emitted",
            session_id=session_id,
            order_number=order_number,
            amount=amount,
            order_type=order_type
        )
    except Exception as e:
        logger.error("payment_success_emit_failed", error=str(e), session_id=session_id)


def emit_receipt_link(session_id: str, order_number: str, amount: float, download_url: str, items: List[Dict[str, Any]] = None):
    """Emit a receipt download card with PDF link and order summary."""
    try:
        event = ReceiptLinkEvent(
            order_number=order_number,
            amount=amount,
            download_url=download_url,
            items=items or []
        )
        _put_event_threadsafe(session_id, event)
        logger.info("receipt_link_emitted", session_id=session_id, order_number=order_number)
    except Exception as e:
        logger.error("receipt_link_emit_failed", error=str(e), session_id=session_id)


def _get_activity_type_for_tool(tool_name: str) -> str:
    """Map tool name to activity type for icon selection."""
    tool_activity_types = {
        "search_menu": "searching",
        "add_to_cart": "adding",
        "view_cart": "checking",
        "remove_from_cart": "updating",
        "checkout": "processing",
        "cancel_order": "processing",
        "clear_cart": "updating",
        "update_quantity": "updating",
        "set_special_instructions": "noting",
        "get_item_details": "searching",
        "check_table_availability": "checking",
        "make_reservation": "booking",
        "get_my_bookings": "checking",
        "cancel_reservation": "processing",
    }
    return tool_activity_types.get(tool_name, "processing")


def _sanitize_args_for_display(tool_name: str, args: Dict[str, Any]) -> str:
    """
    Convert raw tool arguments to user-friendly context.

    IMPORTANT: Never expose internal parameter names or technical details.

    Returns empty string if no user-friendly context is appropriate.
    """
    if not args:
        return ""

    # Only show minimal, user-relevant context
    if tool_name == "search_menu" and args.get("query"):
        query = args.get("query", "")
        if query and query.lower() not in ["", "all", "everything"]:
            return f'for "{query}"'
    elif tool_name == "add_to_cart" and args.get("item"):
        return ""  # Don't repeat what user just said
    elif tool_name in ["make_reservation", "check_table_availability"]:
        date = args.get("date", "")
        if date:
            return f"for {date}"

    # Default: don't expose args
    return ""


def _sanitize_result_for_display(result: str) -> str:
    """
    Sanitize tool result for user display.

    IMPORTANT: Never expose internal IDs, technical errors, or system details.

    Returns a brief, user-friendly summary.
    """
    if not result:
        return "Done"

    # Truncate to reasonable length
    result = result[:150]

    # Remove any technical markers
    technical_patterns = [
        "session_id",
        "item_id",
        "Error:",
        "Exception:",
        "Traceback",
        "_id",
        "ObjectId",
    ]

    for pattern in technical_patterns:
        if pattern.lower() in result.lower():
            return "Done"

    # If result looks user-friendly, use it
    if len(result) < 100 and not any(c in result for c in ['{', '}', '[', ']']):
        return result

    return "Done"
