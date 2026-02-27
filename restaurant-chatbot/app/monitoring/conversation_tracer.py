"""
Conversation Tracer
===================
Captures and stores the entire conversation flow for analysis and debugging.
Tracks agents, state changes, tool calls, and decision paths.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)


class ConversationTracer:
    """
    Traces conversation flow through the system.
    Captures state changes, tool calls, and decision points.
    """

    def __init__(self, session_id: str, output_dir: str = "conversation_traces"):
        self.session_id = session_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self.trace_data = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "messages": [],
            "state_transitions": [],
            "agent_calls": [],
            "tool_calls": [],
            "errors": [],
            "metadata": {}
        }

        self.message_count = 0
        self.current_state = None

        logger.info("ConversationTracer initialized", session_id=session_id)

    def log_user_message(self, message: str, metadata: Optional[Dict] = None):
        """Log user input message"""
        self.message_count += 1

        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_number": self.message_count,
            "role": "user",
            "content": message,
            "metadata": metadata or {}
        }

        self.trace_data["messages"].append(entry)
        self._save_trace()

        logger.info("User message logged",
                   session_id=self.session_id,
                   message_number=self.message_count)

    def log_agent_response(self, agent_name: str, response: str, metadata: Optional[Dict] = None):
        """Log agent response"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_number": self.message_count,
            "role": "assistant",
            "agent": agent_name,
            "content": response,
            "metadata": metadata or {}
        }

        self.trace_data["messages"].append(entry)
        self._save_trace()

        logger.info("Agent response logged",
                   session_id=self.session_id,
                   agent=agent_name,
                   message_number=self.message_count)

    def log_state_transition(self, from_node: str, to_node: str, state_data: Optional[Dict] = None):
        """Log state graph node transition"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_number": self.message_count,
            "from_node": from_node,
            "to_node": to_node,
            "state_snapshot": state_data or {}
        }

        self.trace_data["state_transitions"].append(entry)
        self._save_trace()

        logger.debug("State transition logged",
                    session_id=self.session_id,
                    from_node=from_node,
                    to_node=to_node)

    def log_agent_call(self, agent_name: str, intent: str, confidence: float,
                      input_data: Optional[Dict] = None, output_data: Optional[Dict] = None):
        """Log agent invocation with intent and confidence"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_number": self.message_count,
            "agent": agent_name,
            "intent": intent,
            "confidence": confidence,
            "input": input_data or {},
            "output": output_data or {}
        }

        self.trace_data["agent_calls"].append(entry)
        self._save_trace()

        logger.info("Agent call logged",
                   session_id=self.session_id,
                   agent=agent_name,
                   intent=intent,
                   confidence=confidence)

    def log_tool_call(self, tool_name: str, parameters: Dict, result: Any):
        """Log tool invocation and result"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_number": self.message_count,
            "tool": tool_name,
            "parameters": parameters,
            "result": str(result)[:500],  # Truncate large results
            "success": True
        }

        self.trace_data["tool_calls"].append(entry)
        self._save_trace()

        logger.debug("Tool call logged",
                    session_id=self.session_id,
                    tool=tool_name)

    def log_error(self, error_type: str, error_message: str, context: Optional[Dict] = None):
        """Log errors during conversation flow"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "message_number": self.message_count,
            "error_type": error_type,
            "message": error_message,
            "context": context or {}
        }

        self.trace_data["errors"].append(entry)
        self._save_trace()

        logger.error("Error logged",
                    session_id=self.session_id,
                    error_type=error_type,
                    message=error_message)

    def update_metadata(self, key: str, value: Any):
        """Update trace metadata"""
        self.trace_data["metadata"][key] = value
        self._save_trace()

    def _save_trace(self):
        """Save trace data to JSON file"""
        try:
            # Update end time
            self.trace_data["end_time"] = datetime.now().isoformat()

            # Calculate duration
            start = datetime.fromisoformat(self.trace_data["start_time"])
            end = datetime.fromisoformat(self.trace_data["end_time"])
            self.trace_data["duration_seconds"] = (end - start).total_seconds()

            # Save to file
            filename = f"trace_{self.session_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.output_dir / filename

            with open(filepath, 'w') as f:
                json.dump(self.trace_data, f, indent=2)

            # Also save latest as separate file for real-time monitoring
            latest_filepath = self.output_dir / f"trace_{self.session_id}_latest.json"
            with open(latest_filepath, 'w') as f:
                json.dump(self.trace_data, f, indent=2)

        except Exception as e:
            logger.error("Failed to save trace",
                        session_id=self.session_id,
                        error=str(e))

    def get_summary(self) -> Dict[str, Any]:
        """Get conversation summary statistics"""
        return {
            "session_id": self.session_id,
            "total_messages": len(self.trace_data["messages"]),
            "user_messages": len([m for m in self.trace_data["messages"] if m["role"] == "user"]),
            "agent_responses": len([m for m in self.trace_data["messages"] if m["role"] == "assistant"]),
            "agents_used": list(set([a["agent"] for a in self.trace_data["agent_calls"]])),
            "state_transitions": len(self.trace_data["state_transitions"]),
            "tool_calls": len(self.trace_data["tool_calls"]),
            "errors": len(self.trace_data["errors"]),
            "duration_seconds": self.trace_data.get("duration_seconds", 0)
        }

    def finalize(self):
        """Finalize trace and save summary"""
        summary = self.get_summary()
        self.trace_data["summary"] = summary
        self._save_trace()

        logger.info("Conversation trace finalized",
                   session_id=self.session_id,
                   summary=summary)

        return summary


# Global tracer registry
_active_tracers: Dict[str, ConversationTracer] = {}


def get_tracer(session_id: str) -> ConversationTracer:
    """Get or create tracer for session"""
    if session_id not in _active_tracers:
        _active_tracers[session_id] = ConversationTracer(session_id)
    return _active_tracers[session_id]


def remove_tracer(session_id: str):
    """Remove tracer from registry"""
    if session_id in _active_tracers:
        tracer = _active_tracers[session_id]
        tracer.finalize()
        del _active_tracers[session_id]
