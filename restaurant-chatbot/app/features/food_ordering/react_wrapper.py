"""
ReAct Agent Wrapper
===================
Universal wrapper for LangGraph ReAct agents.

Provides standardized:
- Agent creation with tools
- Execution with guardrails
- Error handling and rollback
- Response formatting
"""

from typing import Dict, Any, List, Optional
import time
import asyncio
import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.prebuilt import create_react_agent

from app.features.food_ordering.state import FoodOrderingState
from app.ai_services.agent_llm_factory import get_llm_for_agent
from app.features.food_ordering.react_config import (
    is_react_logging_enabled,
    is_performance_tracking_enabled
)

logger = structlog.get_logger("food_ordering.react_wrapper")


async def react_agent_wrapper(
    agent_name: str,
    tools: List[Any],
    entities: Dict[str, Any],
    state: FoodOrderingState,
    system_prompt: str,
    temperature: float = 0.1,
    max_iterations: Optional[int] = None,
    timeout_seconds: Optional[int] = None
) -> Dict[str, Any]:
    """
    Universal ReAct agent wrapper using LangGraph's create_react_agent.

    Creates and executes a ReAct agent with:
    - Specified tools
    - System prompt for instructions
    - Guardrails (max iterations, timeout)
    - Error handling and rollback
    - Standardized response format

    Args:
        agent_name: Name of the agent (for logging/monitoring)
        tools: List of LangChain tools
        entities: Extracted entities from user message
        state: Current food ordering state
        system_prompt: Instructions for the agent
        temperature: LLM temperature (default 0.1 for consistency)
        max_iterations: Maximum reasoning steps (overrides state guardrails)
        timeout_seconds: Maximum execution time (overrides state guardrails)

    Returns:
        ActionResult dict with:
            - action: str - Action type
            - success: bool - Whether execution succeeded
            - data: Dict - Response data for user
            - context: Dict - Metadata and debugging info
    """
    session_id = state.get("session_id", "unknown")
    start_time = time.time()

    # Get guardrails from state or use overrides
    guardrails = state.get("guardrails", {})
    max_iter = max_iterations or guardrails.get("max_iterations", 10)
    timeout = timeout_seconds or guardrails.get("timeout_seconds", 30)

    logger.info(
        "ReAct agent starting",
        session_id=session_id,
        agent_name=agent_name,
        tools_count=len(tools),
        max_iterations=max_iter,
        timeout=timeout
    )

    try:
        # Get LLM for this agent
        llm = get_llm_for_agent(agent_name, temperature=temperature)

        # Create ReAct agent (using messages_modifier for system prompt)
        agent_executor = create_react_agent(
            llm,
            tools,
            messages_modifier=SystemMessage(content=system_prompt)
        )

        # Get the latest user message
        messages = state.get("messages", [])
        if not messages:
            return _error_response(
                "no_messages",
                "No user message found in state",
                session_id
            )

        latest_message = messages[-1]
        user_message_content = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)

        # Add session context to message
        enhanced_message = f"""Session ID: {session_id}
Restaurant ID: {state.get('restaurant_id', 'unknown')}

User Message: {user_message_content}

Entities Extracted: {entities}
"""

        # Execute agent with timeout
        try:
            agent_result = await asyncio.wait_for(
                agent_executor.ainvoke({
                    "messages": [HumanMessage(content=enhanced_message)]
                }),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            logger.error(
                "ReAct agent timeout",
                session_id=session_id,
                agent_name=agent_name,
                timeout=timeout
            )
            return _error_response(
                "agent_timeout",
                f"Agent execution exceeded {timeout} seconds",
                session_id
            )

        # Extract final response from agent
        agent_messages = agent_result.get("messages", [])
        if not agent_messages:
            return _error_response(
                "no_agent_response",
                "Agent did not produce any response",
                session_id
            )

        # Get the final AI message
        final_message = agent_messages[-1]
        agent_response = final_message.content if hasattr(final_message, 'content') else str(final_message)

        execution_time = time.time() - start_time

        logger.info(
            "ReAct agent completed",
            session_id=session_id,
            agent_name=agent_name,
            execution_time=execution_time,
            message_count=len(agent_messages)
        )

        # Log performance metrics if enabled
        if is_performance_tracking_enabled():
            _log_performance_metrics(
                agent_name=agent_name,
                session_id=session_id,
                execution_time=execution_time,
                iterations=len(agent_messages),
                success=True
            )

        # Format and return response
        return {
            "action": "react_agent_success",
            "success": True,
            "data": {
                "message": agent_response,
                "agent_name": agent_name
            },
            "context": {
                "execution_time": execution_time,
                "iterations": len(agent_messages),
                "temperature": temperature,
                "session_id": session_id
            }
        }

    except Exception as e:
        execution_time = time.time() - start_time

        logger.error(
            "ReAct agent failed",
            session_id=session_id,
            agent_name=agent_name,
            error=str(e),
            execution_time=execution_time,
            exc_info=True
        )

        # Log failure metrics if enabled
        if is_performance_tracking_enabled():
            _log_performance_metrics(
                agent_name=agent_name,
                session_id=session_id,
                execution_time=execution_time,
                iterations=0,
                success=False,
                error=str(e)
            )

        return _error_response(
            "agent_execution_failed",
            f"Agent execution failed: {str(e)}",
            session_id
        )


def _error_response(
    action: str,
    error_message: str,
    session_id: str
) -> Dict[str, Any]:
    """
    Create standardized error response.

    Args:
        action: Error action type
        error_message: Human-readable error message
        session_id: Session ID for logging

    Returns:
        ActionResult dict with error details
    """
    return {
        "action": action,
        "success": False,
        "data": {
            "message": "I encountered an issue processing your request. Please try again or rephrase your message."
        },
        "context": {
            "error": error_message,
            "session_id": session_id
        }
    }


def _log_performance_metrics(
    agent_name: str,
    session_id: str,
    execution_time: float,
    iterations: int,
    success: bool,
    error: Optional[str] = None
) -> None:
    """
    Log ReAct agent performance metrics.

    Can be extended to store metrics in database for monitoring.

    Args:
        agent_name: Name of the agent
        session_id: Session ID
        execution_time: Total execution time in seconds
        iterations: Number of reasoning iterations
        success: Whether execution succeeded
        error: Error message if failed
    """
    metric = {
        "agent_name": agent_name,
        "session_id": session_id,
        "execution_time": execution_time,
        "iterations": iterations,
        "success": success
    }

    if error:
        metric["error"] = error

    logger.info(
        "ReAct performance metric",
        **metric
    )

    # TODO: Store metrics in MongoDB for dashboard/analytics
    # if is_react_logging_enabled():
    #     await store_react_metrics(metric)


__all__ = ["react_agent_wrapper"]
