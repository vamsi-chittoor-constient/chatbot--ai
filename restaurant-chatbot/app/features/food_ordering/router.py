"""
Router
======
Deterministic routing from sub-intent to agent.

No LLM needed - simple Python dict lookup.
"""

from typing import Callable, Dict
import structlog

from app.features.food_ordering.state import SubIntentClassification

logger = structlog.get_logger("food_ordering.router")


# Agent function type
AgentFunction = Callable


# Agent registry (populated by agents as they're imported)
_AGENT_REGISTRY: Dict[str, AgentFunction] = {}


def register_agent(sub_intent: str, agent_function: AgentFunction):
    """
    Register an agent for a specific sub-intent.

    Args:
        sub_intent: Sub-intent name
        agent_function: Async function that executes the agent
    """
    _AGENT_REGISTRY[sub_intent] = agent_function
    logger.info(f"Registered agent for sub-intent: {sub_intent}")


def route_to_agent(classification: SubIntentClassification) -> AgentFunction:
    """
    Route sub-intent to appropriate agent.

    Deterministic lookup - no LLM needed.

    Args:
        classification: Intent classification result

    Returns:
        Agent function to execute

    Raises:
        ValueError: If sub-intent has no registered agent
    """
    sub_intent = classification.sub_intent

    agent_function = _AGENT_REGISTRY.get(sub_intent)

    if not agent_function:
        available = list(_AGENT_REGISTRY.keys())
        raise ValueError(
            f"No agent registered for sub-intent '{sub_intent}'. "
            f"Available: {available}"
        )

    logger.info(
        "Routed to agent",
        sub_intent=sub_intent,
        confidence=classification.confidence
    )

    return agent_function


def get_agent_name(sub_intent: str) -> str:
    """
    Get human-readable agent name for sub-intent.

    Args:
        sub_intent: Sub-intent name

    Returns:
        Agent name for logging/display
    """
    names = {
        "browse_menu": "Menu Browsing Agent",
        "discover_items": "Menu Discovery Agent",
        "manage_cart": "Cart Management Agent",
        "validate_order": "Checkout Validator Agent",
        "execute_checkout": "Checkout Executor Agent"
    }

    return names.get(sub_intent, f"Unknown Agent ({sub_intent})")


__all__ = [
    "register_agent",
    "route_to_agent",
    "get_agent_name"
]
