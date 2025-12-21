"""
Testing Middleware
==================

WARNING: TESTING MODULE - This file is part of the manual testing infrastructure
and can be removed when testing is complete.

This middleware intercepts messages for testing sessions and:
1. Streams real-time metadata events to WebSocket
2. Saves conversation data with metadata to MongoDB
3. Provides detailed orchestration flow information for testers
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from app.database.mongodb import get_mongodb_testing_manager

logger = logging.getLogger(__name__)


class TestingMiddleware:
    """
    Middleware to enhance testing sessions with metadata streaming and logging.

    This class wraps the normal message processing to add testing-specific features
    without modifying production code.
    """

    @staticmethod
    def is_testing_session(session_id: str) -> bool:
        """Check if a session is a testing session."""
        return session_id.startswith("test-")

    @staticmethod
    async def stream_metadata_event(
        websocket_manager: Any,
        session_id: str,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Stream a metadata event to the testing frontend via WebSocket.

        Args:
            websocket_manager: WebSocket manager instance
            session_id: Testing session ID
            event_type: Type of event (intent_detected, routing, agent_action, etc.)
            data: Event data to send
        """
        try:
            if session_id in websocket_manager.active_connections:
                websocket = websocket_manager.active_connections[session_id]

                # Send metadata event as raw JSON (not through ChatResponse model)
                import json
                event_payload = {
                    "type": event_type,
                    **data
                }
                await websocket.send_text(json.dumps(event_payload))
                logger.debug(f"Streamed {event_type} event to testing session {session_id}")
        except Exception as e:
            logger.error(f"Failed to stream metadata event: {str(e)}")

    @staticmethod
    async def process_and_log_testing_message(
        user_message: str,
        session_id: str,
        user_id: Optional[str],
        process_message_func,
        websocket_manager: Any
    ) -> tuple[str, Dict[str, Any]]:
        """
        Process a testing message with enhanced metadata streaming and logging.

        This wraps the standard message processing to add testing features:
        - Streams metadata events in real-time
        - Saves complete orchestration flow to MongoDB
        - Provides detailed timing information

        Args:
            user_message: The user's message
            session_id: Testing session ID
            user_id: Optional user ID (usually tester_id)
            process_message_func: The standard message processing function
            websocket_manager: WebSocket manager for streaming events

        Returns:
            Tuple of (response_text, metadata_dict)
        """
        message_id = f"msg-{uuid.uuid4()}"
        start_time = datetime.utcnow()

        try:
            # Initialize metadata structure for MongoDB
            message_metadata = {
                "message_id": message_id,
                "session_id": session_id,
                "tester_id": user_id,
                "timestamp": start_time.isoformat(),
                "user_input": {
                    "message": user_message,
                    "timestamp": start_time.isoformat()
                },
                "orchestration_flow": {}
            }

            # Process the message through normal flow
            ai_response, cycle_metadata = await process_message_func(
                user_message,
                session_id
            )

            # Calculate duration
            end_time = datetime.utcnow()
            total_duration_ms = int((end_time - start_time).total_seconds() * 1000)

            # Extract and structure metadata from cycle_metadata
            orchestration_flow = {}

            # 1. Intent Detection (from perceive node)
            if cycle_metadata.get("intent"):
                intent_data = {
                    "intent": cycle_metadata.get("intent"),
                    "confidence": cycle_metadata.get("confidence", 0.0),
                    "used_context": cycle_metadata.get("used_context", False),
                    "sentiment": cycle_metadata.get("sentiment"),
                    "requires_clarification": cycle_metadata.get("requires_clarification", False),
                    "duration_ms": cycle_metadata.get("perceive_duration_ms")
                }

                orchestration_flow["perceive"] = intent_data

                # Stream intent detection event
                await TestingMiddleware.stream_metadata_event(
                    websocket_manager,
                    session_id,
                    "intent_detected",
                    intent_data
                )

            # 2. Routing Decision (from router node)
            if cycle_metadata.get("agent_used"):
                routing_data = {
                    "selected_agent": cycle_metadata.get("agent_used"),
                    "routing_reason": cycle_metadata.get("routing_reason", f"Routed to {cycle_metadata.get('agent_used')} based on intent"),
                    "timestamp": datetime.utcnow().isoformat()
                }

                orchestration_flow["routing"] = routing_data

                # Stream routing event
                await TestingMiddleware.stream_metadata_event(
                    websocket_manager,
                    session_id,
                    "routing",
                    routing_data
                )

            # 3. Agent Execution (from agent nodes)
            agent_execution_data = {
                "agent_name": cycle_metadata.get("agent_used", "unknown"),
                "sub_intent": cycle_metadata.get("sub_intent"),
                "sub_intent_confidence": cycle_metadata.get("sub_intent_confidence"),
                "actions": cycle_metadata.get("actions", []),
                "reasoning": cycle_metadata.get("reasoning"),
                "duration_ms": cycle_metadata.get("agent_duration_ms")
            }

            orchestration_flow["agent_execution"] = agent_execution_data

            # Stream agent execution event
            await TestingMiddleware.stream_metadata_event(
                websocket_manager,
                session_id,
                "agent_action",
                agent_execution_data
            )

            # 4. Response
            response_data = {
                "message": ai_response,
                "timestamp": end_time.isoformat()
            }

            orchestration_flow["response"] = response_data

            # Update message metadata
            message_metadata["orchestration_flow"] = orchestration_flow
            message_metadata["total_duration_ms"] = total_duration_ms

            # Save to MongoDB
            mongo_manager = get_mongodb_testing_manager()
            await mongo_manager.save_message(message_metadata)

            logger.info(
                f"Testing message processed and logged: session={session_id}, message={message_id}, duration={total_duration_ms}ms"
            )

            # Add message_id to metadata for frontend
            enhanced_metadata = {
                **cycle_metadata,
                "message_id": message_id,
                "total_duration_ms": total_duration_ms,
                "testing_metadata": message_metadata
            }

            return ai_response, enhanced_metadata

        except Exception as e:
            logger.error(f"Error in testing middleware: {str(e)}", exc_info=True)
            # Still save error information to MongoDB
            error_metadata = {
                "message_id": message_id,
                "session_id": session_id,
                "tester_id": user_id,
                "timestamp": start_time.isoformat(),
                "user_input": {
                    "message": user_message,
                    "timestamp": start_time.isoformat()
                },
                "error": {
                    "message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            try:
                mongo_manager = get_mongodb_testing_manager()
                await mongo_manager.save_message(error_metadata)
            except Exception:
                pass

            # Re-raise to let the normal error handling take over
            raise


# Global instance
testing_middleware = TestingMiddleware()
