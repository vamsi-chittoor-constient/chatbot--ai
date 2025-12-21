"""
State Helpers
=============
Helper functions for initializing and managing FoodOrderingState.

Provides utilities for:
- State initialization with defaults
- State transitions
- Flow stage management
- State updates (TypedDict-compatible)
"""

from typing import Dict, Any
from app.features.food_ordering.state import FoodOrderingState


def update_state(state: FoodOrderingState, updates: Dict[str, Any]) -> None:
    """
    Update TypedDict state with new values.

    TypedDict doesn't support .update() method in type system,
    so we manually update each field.

    Args:
        state: State to update (modified in place)
        updates: Dict of updates to apply
    """
    for key, value in updates.items():
        state[key] = value  # type: ignore


def initialize_food_ordering_state(base_state: Dict[str, Any]) -> FoodOrderingState:
    """
    Initialize FoodOrderingState with safe defaults.

    Args:
        base_state: Base AgentState to extend

    Returns:
        FoodOrderingState with defaults initialized
    """
    food_state = {**base_state}

    # Set defaults for new fields if not present
    defaults = {
        # Flow control
        "flow_stage": "classification",
        "agent_mode": "deterministic",  # Start with deterministic, can switch to react
        "react_agent_enabled": False,   # Feature flag - disabled by default

        # Guardrails: Tool control
        "allowed_tools": [],            # Empty = all allowed
        "forbidden_tools": [],
        "required_action": None,

        # Guardrails: Safety limits
        "max_tool_calls": 10,           # Prevent infinite loops
        "tool_call_count": 0,
        "agent_iterations": 0,

        # Guardrails: Validation gates
        "must_validate_cart": True,     # Always validate before checkout
        "must_authenticate": True,      # Always auth before payment
        "confirmation_required": False,
        "cart_locked": False,

        # Rollback
        "previous_state_snapshot": None,
        "can_rollback": False,

        # Monitoring
        "last_tool_calls": [],
        "last_agent_reasoning": None,
        "guardrail_violations": [],
        "agent_error_count": 0,

        # Cart state
        "cart_items": [],
        "cart_subtotal": 0.0,
        "cart_item_count": 0,
        "cart_validated": False,
        "validation_issues": [],

        # Entity tracking
        "extracted_entities": {},
        "missing_entities": [],
        "entity_collection_step": None,

        # Order state
        "order_type": None,
        "draft_order_id": None,
        "draft_order_number": None,
        "draft_order_total": None,
        "checkout_confirmed": False,
        "payment_link_sent": False,
    }

    # Apply defaults only if key doesn't exist
    for key, default_value in defaults.items():
        if key not in food_state:
            food_state[key] = default_value

    return food_state


def transition_flow_stage(
    state: FoodOrderingState,
    new_stage: str
) -> Dict[str, Any]:
    """
    Transition to a new flow stage with appropriate state updates.

    Args:
        state: Current state
        new_stage: Target flow stage

    Returns:
        State updates dict
    """
    updates = {"flow_stage": new_stage}

    # Stage-specific updates
    if new_stage == "tool_execution":
        # Reset tool call count when entering execution
        updates["tool_call_count"] = 0

    elif new_stage == "validation":
        # Lock cart during validation
        updates["cart_locked"] = True

    elif new_stage == "confirmation":
        # Require explicit confirmation
        updates["confirmation_required"] = True

    elif new_stage == "classification":
        # Reset for new turn
        updates["tool_call_count"] = 0
        updates["last_tool_calls"] = []
        updates["guardrail_violations"] = []

    return updates


def enable_react_mode(state: FoodOrderingState) -> Dict[str, Any]:
    """
    Enable ReAct agent mode with appropriate guardrails.

    Args:
        state: Current state

    Returns:
        State updates to enable ReAct mode
    """
    return {
        "react_agent_enabled": True,
        "agent_mode": "react",
        "max_tool_calls": 5,  # Stricter limit for ReAct
        "flow_stage": "tool_execution",
    }


def disable_react_mode(state: FoodOrderingState) -> Dict[str, Any]:
    """
    Disable ReAct agent mode and revert to deterministic.

    Args:
        state: Current state

    Returns:
        State updates to disable ReAct mode
    """
    return {
        "react_agent_enabled": False,
        "agent_mode": "deterministic",
    }


def set_guardrails(
    allowed_tools: list = None,
    forbidden_tools: list = None,
    max_tool_calls: int = None,
    must_validate_cart: bool = None,
    cart_locked: bool = None
) -> Dict[str, Any]:
    """
    Set specific guardrail constraints.

    Args:
        allowed_tools: Whitelist of allowed tools
        forbidden_tools: Blacklist of forbidden tools
        max_tool_calls: Maximum tool calls per turn
        must_validate_cart: Whether cart validation is required
        cart_locked: Whether cart is locked

    Returns:
        State updates dict
    """
    updates = {}

    if allowed_tools is not None:
        updates["allowed_tools"] = allowed_tools

    if forbidden_tools is not None:
        updates["forbidden_tools"] = forbidden_tools

    if max_tool_calls is not None:
        updates["max_tool_calls"] = max_tool_calls

    if must_validate_cart is not None:
        updates["must_validate_cart"] = must_validate_cart

    if cart_locked is not None:
        updates["cart_locked"] = cart_locked

    return updates


def reset_error_state(state: FoodOrderingState) -> Dict[str, Any]:
    """
    Reset error-related state fields.

    Used after successful recovery from errors.

    Args:
        state: Current state

    Returns:
        State updates to reset errors
    """
    return {
        "agent_error_count": 0,
        "guardrail_violations": [],
        "can_rollback": False,
        "previous_state_snapshot": None,
    }


def create_rollback_updates(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create state updates to rollback to previous snapshot.

    Args:
        snapshot: Previous state snapshot

    Returns:
        State updates to restore snapshot
    """
    if not snapshot:
        return {}

    return {
        **snapshot,
        "can_rollback": False,
        "previous_state_snapshot": None,
    }


def configure_react_for_agent(
    agent_name: str,
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    Configure state for ReAct agent execution.

    Applies agent-specific configuration including:
    - Feature flags
    - Guardrails
    - Monitoring settings

    Args:
        agent_name: Name of the agent to configure
        state: Current state

    Returns:
        State updates dict with ReAct configuration
    """
    from app.features.food_ordering.react_config import get_react_config_for_agent

    config = get_react_config_for_agent(agent_name, state)

    updates = {
        "react_agent_enabled": config["react_enabled"],
        "agent_mode": config["agent_mode"],
        **config["guardrails"]
    }

    return updates


__all__ = [
    "update_state",
    "initialize_food_ordering_state",
    "transition_flow_stage",
    "enable_react_mode",
    "disable_react_mode",
    "set_guardrails",
    "reset_error_state",
    "create_rollback_updates",
    "configure_react_for_agent",
]
