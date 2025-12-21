"""
ReAct Agent Configuration
==========================
Manages ReAct feature flags and A/B testing configuration.

Reads environment variables to determine:
- Whether ReAct mode is enabled globally and per-agent
- A/B testing percentages for gradual rollout
- Guardrails and safety limits
"""

import os
import random
from typing import Dict, Any
import structlog
from pathlib import Path

# Load .env file to ensure environment variables are available
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass

from app.features.food_ordering.state import FoodOrderingState

logger = structlog.get_logger("food_ordering.react_config")


def get_react_config_for_agent(
    agent_name: str,
    state: FoodOrderingState
) -> Dict[str, Any]:
    """
    Get ReAct configuration for a specific agent.

    Determines if ReAct mode should be enabled based on:
    1. Global feature flag (REACT_GLOBAL_ENABLED)
    2. Agent-specific feature flag (REACT_{AGENT}_ENABLED)
    3. A/B testing percentage (REACT_AB_TEST_PERCENTAGE)
    4. User/session overrides

    Args:
        agent_name: Name of the agent (e.g., "cart_management", "menu_browsing")
        state: Current food ordering state

    Returns:
        Dict with:
            - react_enabled: bool - Whether ReAct should be used
            - agent_mode: str - "react" or "deterministic"
            - guardrails: Dict - Safety limits (max_iterations, timeout)
    """
    session_id = state.get("session_id", "unknown")

    # Check for forced mode override in state
    force_mode = state.get("force_agent_mode")
    if force_mode:
        logger.info(
            "Agent mode forced via state",
            session_id=session_id,
            agent_name=agent_name,
            forced_mode=force_mode
        )
        return {
            "react_enabled": force_mode == "react",
            "agent_mode": force_mode,
            "guardrails": _get_default_guardrails(agent_name)
        }

    # TEMPORARY OVERRIDE: Force deterministic mode until .env loading is fixed
    logger.info(
        "ReAct TEMPORARILY DISABLED (hardcoded override)",
        session_id=session_id,
        agent_name=agent_name
    )
    return {
        "react_enabled": False,
        "agent_mode": "deterministic",
        "guardrails": _get_default_guardrails(agent_name)
    }

    # 1. Check global ReAct flag (TEMPORARILY DISABLED - see override above)
    # global_enabled_str = os.getenv("REACT_GLOBAL_ENABLED", "false")
    # logger.debug(
    #     "Reading REACT_GLOBAL_ENABLED from environment",
    #     session_id=session_id,
    #     raw_value=global_enabled_str
    # )
    # global_enabled = global_enabled_str.lower() == "true"
    # if not global_enabled:
    #     logger.info(
    #         "ReAct disabled globally",
    #         session_id=session_id,
    #         agent_name=agent_name,
    #         global_enabled_raw=global_enabled_str
    #     )
    #     return {
    #         "react_enabled": False,
    #         "agent_mode": "deterministic",
    #         "guardrails": _get_default_guardrails(agent_name)
    #     }

    # 2. Check agent-specific flag
    agent_env_name = f"REACT_{agent_name.upper()}_ENABLED"
    agent_enabled = os.getenv(agent_env_name, "true").lower() == "true"
    if not agent_enabled:
        logger.debug(
            "ReAct disabled for agent",
            session_id=session_id,
            agent_name=agent_name,
            env_var=agent_env_name
        )
        return {
            "react_enabled": False,
            "agent_mode": "deterministic",
            "guardrails": _get_default_guardrails(agent_name)
        }

    # 3. A/B testing - route percentage of traffic to ReAct
    ab_test_percentage = int(os.getenv("REACT_AB_TEST_PERCENTAGE", "0"))

    # Use session_id hash for consistent routing (same session always gets same mode)
    session_hash = hash(session_id) % 100
    use_react = session_hash < ab_test_percentage

    if use_react:
        logger.info(
            "ReAct enabled via A/B test",
            session_id=session_id,
            agent_name=agent_name,
            ab_percentage=ab_test_percentage,
            session_hash=session_hash
        )
        return {
            "react_enabled": True,
            "agent_mode": "react",
            "guardrails": _get_default_guardrails(agent_name)
        }
    else:
        logger.info(
            "Deterministic mode via A/B test",
            session_id=session_id,
            agent_name=agent_name,
            ab_percentage=ab_test_percentage,
            session_hash=session_hash
        )
        return {
            "react_enabled": False,
            "agent_mode": "deterministic",
            "guardrails": _get_default_guardrails(agent_name)
        }


def _get_default_guardrails(agent_name: str) -> Dict[str, Any]:
    """
    Get default guardrails for an agent.

    Guardrails prevent runaway execution and ensure safety.

    Args:
        agent_name: Name of the agent

    Returns:
        Dict with guardrail settings
    """
    # Agent-specific guardrail overrides
    agent_guardrails = {
        "menu_browsing": {
            "max_iterations": 5,
            "timeout_seconds": 15
        },
        "menu_discovery": {
            "max_iterations": 8,
            "timeout_seconds": 20
        },
        "cart_management": {
            "max_iterations": 10,
            "timeout_seconds": 25
        },
        "checkout_validator": {
            "max_iterations": 6,
            "timeout_seconds": 15
        },
        "checkout_executor": {
            "max_iterations": 8,
            "timeout_seconds": 30
        }
    }

    # Get agent-specific or use defaults
    guardrails = agent_guardrails.get(agent_name, {
        "max_iterations": 10,
        "timeout_seconds": 20
    })

    # Add common guardrails
    guardrails.update({
        "max_tool_failures": 3,
        "enable_rollback": True,
        "log_reasoning": True
    })

    return guardrails


def is_react_logging_enabled() -> bool:
    """Check if ReAct interaction logging to MongoDB is enabled."""
    return os.getenv("REACT_MONGODB_LOGGING_ENABLED", "false").lower() == "true"


def is_finetuning_data_enabled() -> bool:
    """Check if ReAct interaction should be saved for finetuning."""
    return os.getenv("REACT_FINETUNING_DATA_ENABLED", "false").lower() == "true"


def is_performance_tracking_enabled() -> bool:
    """Check if ReAct performance metrics should be tracked."""
    return os.getenv("REACT_PERFORMANCE_TRACKING_ENABLED", "false").lower() == "true"


__all__ = [
    "get_react_config_for_agent",
    "is_react_logging_enabled",
    "is_finetuning_data_enabled",
    "is_performance_tracking_enabled"
]
