"""
AG-UI SSE Streaming Endpoint
============================
Server-Sent Events endpoint for AG-UI protocol streaming.

Provides real-time visibility into agent processing:
- Activity indicators (typing, searching, adding)
- Tool execution progress
- Streaming text responses
- State updates
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import structlog
import asyncio

from app.core.agui_events import (
    AGUIEventEmitter,
    stream_events,
    get_event_queue,
    clear_event_queue,
    get_tool_activity_message
)

router = APIRouter()
logger = structlog.get_logger(__name__)


class StreamChatRequest(BaseModel):
    """Request body for stream chat endpoint"""
    message: str
    session_id: str
    user_id: Optional[str] = None
    device_id: Optional[str] = None
    conversation_history: list[str] = []


@router.post("/chat/stream")
async def stream_chat(request: StreamChatRequest):
    """
    Process chat message with AG-UI streaming.

    Returns SSE stream with real-time events:
    - RUN_STARTED: Processing begins
    - ACTIVITY_START/END: Typing indicators
    - TOOL_CALL_START/ARGS/RESULT/END: Tool execution
    - TEXT_MESSAGE_START/CONTENT/END: Response streaming
    - RUN_FINISHED: Processing complete

    Usage:
        const eventSource = new EventSource('/api/v1/chat/stream');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            switch(data.type) {
                case 'ACTIVITY_START':
                    showTypingIndicator(data.message);
                    break;
                case 'TEXT_MESSAGE_CONTENT':
                    appendText(data.delta);
                    break;
                // ... handle other event types
            }
        };
    """
    session_id = request.session_id

    logger.info(
        "stream_chat_request",
        session_id=session_id,
        message_length=len(request.message)
    )

    # Create emitter for this session
    emitter = AGUIEventEmitter(session_id)

    async def generate_stream():
        """Generator that processes message and yields SSE events."""
        try:
            # NOTE: Don't emit RUN_STARTED here - it's handled by:
            # 1. Auth flow (if AUTH_REQUIRED) - emits its own events
            # 2. process_with_agui_streaming - emits RUN_STARTED after auth

            # Start background processing
            process_task = asyncio.create_task(
                process_message_with_streaming(
                    message=request.message,
                    session_id=session_id,
                    user_id=request.user_id,
                    device_id=request.device_id,
                    conversation_history=request.conversation_history,
                    emitter=emitter
                )
            )

            # Stream events while processing
            async for event_str in stream_events(session_id, timeout=120.0):
                yield event_str

            # Wait for processing to complete (should already be done)
            await process_task

        except Exception as e:
            logger.error("stream_chat_error", session_id=session_id, error=str(e))
            emitter.emit_run_error(str(e))
            # Yield error event
            async for event_str in stream_events(session_id, timeout=5.0):
                yield event_str
        finally:
            clear_event_queue(session_id)

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.get("/chat/stream/{session_id}")
async def stream_events_endpoint(session_id: str):
    """
    SSE endpoint for connecting to existing session stream.

    Use this when processing is initiated elsewhere (e.g., WebSocket)
    and you want to receive AG-UI events via SSE.
    """
    logger.info("stream_events_connect", session_id=session_id)

    return StreamingResponse(
        stream_events(session_id, timeout=120.0),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def process_message_with_streaming(
    message: str,
    session_id: str,
    user_id: Optional[str],
    device_id: Optional[str],
    conversation_history: list[str],
    emitter: AGUIEventEmitter
) -> tuple[str, Dict[str, Any]]:
    """
    Process message with Restaurant Crew while emitting AG-UI events.

    This wraps the standard processing to add real-time streaming.
    Uses the process_with_agui_streaming function from restaurant_crew.
    """
    try:
        from app.orchestration.restaurant_crew import process_with_agui_streaming

        # Delegate to the AG-UI enabled processing function
        return await process_with_agui_streaming(
            user_message=message,
            session_id=session_id,
            conversation_history=conversation_history,
            emitter=emitter,
            user_id=user_id,
            welcome_msg=None,
            device_id=device_id
        )

    except Exception as e:
        logger.error("streaming_process_error", error=str(e), exc_info=True)
        emitter.emit_activity_end()
        emitter.emit_run_error(str(e))
        raise


# ============================================================================
# AGUI-ENABLED TOOL WRAPPERS
# ============================================================================

def create_agui_tool_wrapper(tool_func, tool_name: str, emitter: AGUIEventEmitter):
    """
    Wrap a tool function to emit AG-UI events.

    Usage:
        wrapped_search = create_agui_tool_wrapper(search_menu, "search_menu", emitter)
        result = wrapped_search(query="burger")
    """
    def wrapper(*args, **kwargs):
        # Emit tool start
        emitter.emit_tool_start(tool_name, kwargs)
        emitter.emit_activity(
            "searching" if "search" in tool_name else "adding",
            get_tool_activity_message(tool_name)
        )

        try:
            # Execute tool
            result = tool_func(*args, **kwargs)

            # Emit result
            emitter.emit_tool_result(str(result))
            emitter.emit_tool_end()
            emitter.emit_activity_end()

            return result

        except Exception as e:
            emitter.emit_tool_result(f"Error: {str(e)}")
            emitter.emit_tool_end()
            emitter.emit_activity_end()
            raise

    return wrapper
