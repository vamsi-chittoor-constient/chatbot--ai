"""
Agent Handoff Service
======================
Manages smooth transitions between agents with context preservation.

Enables:
- Explicit agent-to-agent handoffs
- Context transfer with handoff reason
- Natural conversation flow
- Handoff tracking and analytics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from enum import Enum
import structlog

logger = structlog.get_logger("services.handof")


class HandoffReason(str, Enum):
    """Reasons for agent handoffs"""
    AUTHENTICATION_REQUIRED = "authentication_required"
    PAYMENT_NEEDED = "payment_needed"
    SPECIALIST_NEEDED = "specialist_needed"
    TASK_COMPLETE = "task_complete"
    USER_REQUEST = "user_request"
    CAPABILITY_LIMIT = "capability_limit"


class AgentHandoff:
    """Represents a handoff from one agent to another."""

    def __init__(
        self,
        from_agent: str,
        to_agent: str,
        reason: HandoffReason,
        context: Dict[str, Any],
        message_to_user: Optional[str] = None
    ):
        self.from_agent = from_agent
        self.to_agent = to_agent
        self.reason = reason
        self.context = context
        self.message_to_user = message_to_user
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert handoff to dict."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "reason": self.reason.value,
            "context": self.context,
            "message_to_user": self.message_to_user,
            "timestamp": self.timestamp
        }


class HandoffService:
    """Manages agent handoffs."""

    def __init__(self):
        self.handoff_history: Dict[str, List[AgentHandoff]] = {}

    def create_handoff(
        self,
        from_agent: str,
        to_agent: str,
        reason: HandoffReason,
        context: Dict[str, Any],
        session_id: str,
        message_to_user: Optional[str] = None
    ) -> AgentHandoff:
        """
        Create a handoff from one agent to another.

        Args:
            from_agent: Source agent name
            to_agent: Destination agent name
            reason: Reason for handoff
            context: Context to transfer (entities, intent, etc.)
            session_id: Session identifier
            message_to_user: Optional message to display during handoff

        Returns:
            AgentHandoff object
        """
        # Generate default message if not provided
        if not message_to_user:
            message_to_user = self._generate_handoff_message(
                from_agent, to_agent, reason
            )

        handoff = AgentHandoff(
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason,
            context=context,
            message_to_user=message_to_user
        )

        # Track handoff history
        if session_id not in self.handoff_history:
            self.handoff_history[session_id] = []

        self.handoff_history[session_id].append(handoff)

        logger.info(
            "Agent handoff created",
            session_id=session_id,
            from_agent=from_agent,
            to_agent=to_agent,
            reason=reason.value
        )

        return handoff

    def get_handoff_context(
        self,
        session_id: str,
        agent_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get context from last handoff to this agent.

        Args:
            session_id: Session identifier
            agent_name: Agent requesting context

        Returns:
            Handoff context if available
        """
        if session_id not in self.handoff_history:
            return None

        # Find last handoff TO this agent
        for handoff in reversed(self.handoff_history[session_id]):
            if handoff.to_agent == agent_name:
                return handoff.context

        return None

    def get_handoff_chain(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get complete handoff chain for a session.

        Returns:
            List of handoff dicts in chronological order
        """
        if session_id not in self.handoff_history:
            return []

        return [h.to_dict() for h in self.handoff_history[session_id]]

    def _generate_handoff_message(
        self,
        from_agent: str,
        to_agent: str,
        reason: HandoffReason
    ) -> str:
        """Generate natural handoff message."""

        agent_display_names = {
            "booking_agent": "reservation specialist",
            "food_ordering_agent": "food ordering specialist",
            "authentication_agent": "authentication specialist",
            "user_management_agent": "account specialist",
            "user_profile_agent": "profile specialist",
            "feedback_agent": "customer care specialist",
            "general_queries_agent": "information specialist"
        }

        from_name = agent_display_names.get(from_agent, from_agent)
        to_name = agent_display_names.get(to_agent, to_agent)

        messages = {
            HandoffReason.AUTHENTICATION_REQUIRED: f"Let me connect you with our {to_name} to help you log in or create an account.",
            HandoffReason.PAYMENT_NEEDED: f"I'll transfer you to our {to_name} to complete your payment securely.",
            HandoffReason.SPECIALIST_NEEDED: f"Let me connect you with our {to_name} who can better assist you with this.",
            HandoffReason.TASK_COMPLETE: f"Great! Let me connect you with our {to_name} for the next step.",
            HandoffReason.USER_REQUEST: f"Of course! Let me connect you with our {to_name}.",
            HandoffReason.CAPABILITY_LIMIT: f"For this request, I'll connect you with our {to_name} who specializes in this area."
        }

        return messages.get(
            reason,
            f"Let me transfer you to our {to_name}."
        )

    def clear_history(self, session_id: Optional[str] = None):
        """Clear handoff history."""
        if session_id:
            self.handoff_history.pop(session_id, None)
        else:
            self.handoff_history.clear()


# Global instance
handoff_service = HandoffService()
