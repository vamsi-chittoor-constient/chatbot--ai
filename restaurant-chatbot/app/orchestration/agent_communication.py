"""
Agent Communication Protocol
=============================
Helper utilities for inter-agent communication in LangGraph.

This module provides a clean protocol for agents to delegate tasks to other agents
and receive results back, without hardcoding the delegation logic.

Pattern: Nested Subgraph with Explicit Delegation Tracking

Example:
    booking_agent needs authentication 
        Uses AgentCommunicator.delegate() to prepare state 
            Routes to nested authentication_subgraph 
                Auth completes and returns via AgentCommunicator.return_from_delegation() 
                    booking_agent receives result and continues
"""

from typing import Dict, Any, Optional, List
import structlog
from app.orchestration.state import AgentState

logger = structlog.get_logger("orchestration.agent_communication")


class AgentCommunicator:
    """
    Helper class for inter-agent communication in LangGraph.

    Provides methods for:
    - Delegating tasks to other agents (delegate)
    - Returning results from delegated agents (return_from_delegation)
    - Checking if current execution is a delegation (is_delegation)
    - Getting delegation context (get_delegation_context)
    """

    @staticmethod
    def delegate(
        state: AgentState,
        from_agent: str,
        to_agent: str,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare state for agent delegation.

        This method sets up the delegation protocol fields in state so that:
        1. The target agent knows it's being delegated to
        2. The target agent has context about what to do
        3. We can track the delegation chain for debugging

        Args:
            state: Current agent state
            from_agent: Name of agent initiating delegation (e.g., "booking_agent")
            to_agent: Name of target agent to delegate to (e.g., "authentication_agent")
            task: Description of task to delegate (e.g., "authenticate_user_for_booking")
            context: Optional context dict to pass to target agent

        Returns:
            Dict with updated delegation fields to merge into state

        Example:
            >>> state = {...}
            >>> updates = AgentCommunicator.delegate(
            ...     state=state,
            ...     from_agent="booking_agent",
            ...     to_agent="authentication_agent",
            ...     task="authenticate_user",
            ...     context={
            ...         "purpose": "booking_confirmation",
            ...         "phone": "+1234567890",
            ...         "booking_details": {...}
            ...     }
            ... )
            >>> new_state = {**state, **updates}
        """
        delegation_stack = list(state.get("delegation_stack", []))
        delegation_stack.append(from_agent)

        delegation_context = {
            "task": task,
            "from_agent": from_agent,
            "to_agent": to_agent,
            **(context or {})
        }

        logger.info(
            "agent_delegation_initiated",
            from_agent=from_agent,
            to_agent=to_agent,
            task=task,
            delegation_depth=len(delegation_stack),
            session_id=state.get("session_id")
        )

        return {
            "delegation_stack": delegation_stack,
            "delegation_context": delegation_context,
            "current_delegator": from_agent,
            "delegation_result": None  # Clear any previous result
        }

    @staticmethod
    def return_from_delegation(
        state: AgentState,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Return result to delegating agent.

        This method prepares the state for returning to the agent that
        initiated the delegation, including the result data.

        Args:
            state: Current agent state
            result: Result dict to return to delegating agent

        Returns:
            Dict with updated delegation fields to merge into state

        Example:
            >>> # In authentication_agent after completing auth
            >>> state = {...}
            >>> updates = AgentCommunicator.return_from_delegation(
            ...     state=state,
            ...     result={
            ...         "user_id": "usr000123",
            ...         "user_phone": "+1234567890",
            ...         "user_name": "John Doe",
            ...         "authenticated": True
            ...     }
            ... )
            >>> new_state = {**state, **updates}
        """
        delegation_stack = list(state.get("delegation_stack", []))
        delegation_context = state.get("delegation_context", {})

        # Pop current agent from stack
        returning_to = None
        if delegation_stack:
            current_delegator = delegation_stack.pop()
            returning_to = delegation_stack[-1] if delegation_stack else None
        else:
            current_delegator = state.get("current_delegator")

        from_agent = delegation_context.get("to_agent", "unknown")
        to_agent = delegation_context.get("from_agent", "unknown")

        logger.info(
            "agent_delegation_completed",
            from_agent=from_agent,
            to_agent=to_agent,
            returning_to=returning_to,
            delegation_depth=len(delegation_stack),
            result_keys=list(result.keys()),
            session_id=state.get("session_id")
        )

        return {
            "delegation_stack": delegation_stack,
            "delegation_result": result,
            "current_delegator": returning_to,
            "delegation_context": {}  # Clear context after return
        }

    @staticmethod
    def is_delegation(state: AgentState) -> bool:
        """
        Check if current agent execution is a delegation.

        Args:
            state: Current agent state

        Returns:
            True if this is a delegated execution, False if standalone

        Example:
            >>> if AgentCommunicator.is_delegation(state):
            ...     # Handle as delegated task
            ...     result = perform_delegated_task(state)
            ...     return AgentCommunicator.return_from_delegation(state, result)
            ... else:
            ...     # Handle as standalone request
            ...     return perform_standalone_task(state)
        """
        delegation_context = state.get("delegation_context", {})
        return bool(delegation_context.get("from_agent"))

    @staticmethod
    def get_delegation_context(state: AgentState) -> Dict[str, Any]:
        """
        Get the delegation context for current execution.

        Args:
            state: Current agent state

        Returns:
            Delegation context dict (empty if not a delegation)

        Example:
            >>> context = AgentCommunicator.get_delegation_context(state)
            >>> task = context.get("task")  # What task was delegated
            >>> from_agent = context.get("from_agent")  # Who delegated
            >>> purpose = context.get("purpose")  # Custom context field
        """
        return state.get("delegation_context", {})

    @staticmethod
    def get_delegation_depth(state: AgentState) -> int:
        """
        Get current delegation depth (how many agents deep).

        Args:
            state: Current agent state

        Returns:
            Delegation depth (0 = not delegated, 1 = first level, 2 = nested, etc.)

        Example:
            >>> depth = AgentCommunicator.get_delegation_depth(state)
            >>> if depth > 2:
            ...     logger.warning("Deep delegation detected", depth=depth)
        """
        delegation_stack = state.get("delegation_stack", [])
        return len(delegation_stack)

    @staticmethod
    def clear_delegation(state: AgentState) -> Dict[str, Any]:
        """
        Clear all delegation state (useful for error recovery).

        Args:
            state: Current agent state

        Returns:
            Dict with cleared delegation fields

        Example:
            >>> try:
            ...     result = perform_delegation(state)
            ... except Exception as e:
            ...     logger.error("Delegation failed", error=str(e))
            ...     return AgentCommunicator.clear_delegation(state)
        """
        logger.warning(
            "delegation_cleared",
            session_id=state.get("session_id"),
            delegation_stack=state.get("delegation_stack"),
            reason="explicit_clear"
        )

        return {
            "delegation_stack": [],
            "delegation_context": {},
            "delegation_result": None,
            "current_delegator": None
        }


# Convenience functions for common delegation patterns

def delegate_to_auth(
    state: AgentState,
    from_agent: str,
    purpose: str,
    **extra_context
) -> Dict[str, Any]:
    """
    Convenience function for delegating to authentication_agent.

    Args:
        state: Current agent state
        from_agent: Name of agent delegating (e.g., "booking_agent")
        purpose: Purpose of authentication (e.g., "booking_confirmation")
        **extra_context: Additional context to pass to auth agent

    Returns:
        State updates for delegation

    Example:
        >>> updates = delegate_to_auth(
        ...     state=state,
        ...     from_agent="booking_agent",
        ...     purpose="booking_confirmation",
        ...     booking_details={"party_size": 4, "date": "2025-01-15"}
        ... )
        >>> new_state = {**state, **updates}
    """
    return AgentCommunicator.delegate(
        state=state,
        from_agent=from_agent,
        to_agent="authentication_agent",
        task="authenticate_user",
        context={
            "purpose": purpose,
            **extra_context
        }
    )


def delegate_to_user_profile(
    state: AgentState,
    from_agent: str,
    task: str,
    **extra_context
) -> Dict[str, Any]:
    """
    Convenience function for delegating to user_profile_agent.

    Args:
        state: Current agent state
        from_agent: Name of agent delegating
        task: What profile task to perform
        **extra_context: Additional context

    Returns:
        State updates for delegation

    Example:
        >>> updates = delegate_to_user_profile(
        ...     state=state,
        ...     from_agent="order_agent",
        ...     task="get_dietary_preferences",
        ...     user_id=state.get("user_id")
        ... )
    """
    return AgentCommunicator.delegate(
        state=state,
        from_agent=from_agent,
        to_agent="user_profile_agent",
        task=task,
        context=extra_context
    )
