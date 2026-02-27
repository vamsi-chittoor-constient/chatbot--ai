"""
LLM with Caching Wrapper
=========================
Combines LLM Manager (multi-provider fallback) with Response Caching.
Provides a simple interface for agents to use.
"""

from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, AIMessage
import structlog

from app.ai_services.llm_manager import get_llm_manager
from app.services.cache_service import get_cache_service

logger = structlog.get_logger(__name__)


async def invoke_llm_with_cache(
    messages: List[BaseMessage],
    cache_enabled: bool = True,
    cache_category: Optional[str] = None,
    user_id: Optional[str] = None,
    intent: Optional[str] = None,
    **kwargs
) -> AIMessage:
    """
    Invoke LLM with automatic caching and multi-provider fallback.

    Workflow:
    1. Check cache for existing response
    2. If cache hit, return cached response
    3. If cache miss, invoke LLM Manager (with auto-fallback)
    4. Cache the response for future use
    5. Return response

    Args:
        messages: List of messages to send to LLM
        cache_enabled: Enable caching for this request (default: True)
        cache_category: Cache category (menu, faq, etc.) - auto-detected if None
        user_id: Optional user ID for personalized caching
        intent: Optional intent for better category detection
        **kwargs: Additional arguments for LLM

    Returns:
        AIMessage response from LLM

    Example:
        ```python
        from app.ai_services.llm_with_cache import invoke_llm_with_cache
        from langchain_core.messages import HumanMessage, SystemMessage

        messages = [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Show me the menu")
        ]

        response = await invoke_llm_with_cache(
            messages,
            cache_category="menu",
            user_id="usr000001"
        )
        ```
    """
    cache_service = get_cache_service()
    llm_manager = get_llm_manager()

    # Extract query from messages for cache key
    query = ""
    for msg in reversed(messages):
        if hasattr(msg, 'content') and msg.content:
            query = msg.content
            break

    # Try to get from cache first
    if cache_enabled and query:
        cached_response = await cache_service.get_cached_response(
            query=query,
            category=cache_category,
            user_id=user_id,
            intent=intent
        )

        if cached_response:
            # Cache hit - return cached response
            logger.info(
                "returning_cached_response",
                query_preview=query[:50],
                cache_category=cache_category or "auto-detected"
            )

            return AIMessage(
                content=cached_response.get("content", ""),
                additional_kwargs=cached_response.get("additional_kwargs", {})
            )

    # Cache miss - invoke LLM with auto-fallback
    logger.debug(
        "cache_miss_invoking_llm",
        query_preview=query[:50] if query else "N/A"
    )

    response = await llm_manager.ainvoke(messages, **kwargs)

    # Cache the response
    if cache_enabled and query and isinstance(response, AIMessage):
        await cache_service.set_cached_response(
            query=query,
            response={
                "content": response.content,
                "additional_kwargs": response.additional_kwargs if hasattr(response, 'additional_kwargs') else {}
            },
            category=cache_category,
            user_id=user_id,
            intent=intent
        )

    return response


async def get_llm_for_agent(agent_name: str) -> Any:
    """
    Get an LLM instance for an agent that supports bind_tools().

    This is for agents that need to bind tools to the LLM.
    The returned LLM uses the manager internally.

    Args:
        agent_name: Name of the agent

    Returns:
        LLM instance with bind_tools() support

    Note:
        For now, returns the primary LLM from the manager.
        In the future, could return a wrapper that supports bind_tools()
        while using the manager's fallback logic.
    """
    from langchain_openai import ChatOpenAI
    from app.core.config import config

    llm_manager = get_llm_manager()

    # Return a simple ChatOpenAI instance using the first account's API key
    # For proper load balancing, use invoke_llm_with_cache instead
    if not llm_manager.accounts:
        raise Exception("No LLM accounts configured")

    first_account = llm_manager.accounts[0]

    return ChatOpenAI(
        model=config.AGENT_MODEL,  # gpt-4o-mini
        api_key=first_account.api_key,
        temperature=0.3
    )


async def get_llm_usage_stats() -> Dict[str, Any]:
    """
    Get LLM usage statistics across all providers.

    Returns:
        Dictionary with usage stats and cache metrics
    """
    llm_manager = get_llm_manager()
    cache_service = get_cache_service()

    llm_stats = llm_manager.get_all_usage_stats()
    cache_stats = cache_service.get_cache_stats()

    return {
        "llm_providers": llm_stats,
        "cache": cache_stats
    }
