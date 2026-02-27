"""
Async Tools Fix for CrewAI
==========================
Ensures proper async tool execution with akickoff()

The issue: CrewAI's async tool support is experimental and tools may not await properly.
The fix: Use sync wrappers that handle async operations correctly.
"""
import asyncio
import functools
from typing import Any, Callable
import structlog

logger = structlog.get_logger(__name__)


def async_to_sync_tool(async_func: Callable) -> Callable:
    """
    Convert async tool function to sync with proper event loop handling.
    
    This ensures async operations in tools work correctly with CrewAI's akickoff().
    """
    @functools.wraps(async_func)
    def sync_wrapper(*args, **kwargs):
        try:
            # Try to get current event loop
            loop = asyncio.get_running_loop()
            
            # If we're in an event loop, we need to run in a thread
            # to avoid "RuntimeError: cannot be called from a running event loop"
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, async_func(*args, **kwargs))
                return future.result()
                
        except RuntimeError:
            # No event loop running, we can use asyncio.run directly
            return asyncio.run(async_func(*args, **kwargs))
        except Exception as e:
            logger.error("async_tool_execution_failed", error=str(e), func=async_func.__name__)
            return f"Error: {str(e)}"
    
    return sync_wrapper


def ensure_sync_tools(tool_factory_func: Callable) -> Callable:
    """
    Decorator to ensure all tools returned by factory are sync-wrapped.
    
    Usage:
    @ensure_sync_tools
    def create_my_tool(session_id: str):
        @tool("my_tool")
        async def my_async_tool():
            # async operations here
            pass
        return my_async_tool
    """
    @functools.wraps(tool_factory_func)
    def wrapper(*args, **kwargs):
        tool = tool_factory_func(*args, **kwargs)
        
        # If the tool function is async, wrap it
        if asyncio.iscoroutinefunction(tool.func):
            tool.func = async_to_sync_tool(tool.func)
            logger.debug("wrapped_async_tool", tool_name=tool.name)
        
        return tool
    
    return wrapper


# Alternative: Direct sync implementations for critical tools
def create_sync_redis_operations():
    """
    Create sync Redis operations that work reliably with CrewAI.
    
    These bypass the async Redis client to avoid event loop issues.
    """
    import redis
    import json
    import os
    
    # Create sync Redis client
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    sync_redis = redis.from_url(redis_url, decode_responses=True)
    
    def get_cart_sync(session_id: str) -> dict:
        """Get cart data synchronously."""
        try:
            cart_key = f"cart:{session_id}"
            cart_data = sync_redis.get(cart_key)
            return json.loads(cart_data) if cart_data else {"items": [], "total": 0}
        except Exception as e:
            logger.warning("sync_redis_get_cart_failed", error=str(e))
            return {"items": [], "total": 0}
    
    def set_cart_sync(session_id: str, cart_data: dict) -> bool:
        """Set cart data synchronously."""
        try:
            cart_key = f"cart:{session_id}"
            sync_redis.setex(cart_key, 3600, json.dumps(cart_data))
            return True
        except Exception as e:
            logger.warning("sync_redis_set_cart_failed", error=str(e))
            return False
    
    def clear_cart_sync(session_id: str) -> bool:
        """Clear cart synchronously."""
        try:
            cart_key = f"cart:{session_id}"
            sync_redis.delete(cart_key)
            return True
        except Exception as e:
            logger.warning("sync_redis_clear_cart_failed", error=str(e))
            return False
    
    return get_cart_sync, set_cart_sync, clear_cart_sync


def create_sync_agui_events():
    """
    Create sync AGUI event emitters that work with CrewAI.
    
    These use thread-safe emission to avoid event loop conflicts.
    """
    def emit_tool_activity_sync(session_id: str, tool_name: str):
        """Emit tool activity synchronously."""
        try:
            from app.core.agui_events import emit_tool_activity
            emit_tool_activity(session_id, tool_name)
        except Exception as e:
            logger.debug("sync_emit_tool_activity_failed", error=str(e))
    
    def emit_cart_data_sync(session_id: str, items: list, total: float):
        """Emit cart data synchronously."""
        try:
            from app.core.agui_events import emit_cart_data
            emit_cart_data(session_id, items, total)
        except Exception as e:
            logger.debug("sync_emit_cart_data_failed", error=str(e))
    
    def emit_menu_data_sync(session_id: str, items: list, current_meal_period: str = None):
        """Emit menu data synchronously."""
        try:
            from app.core.agui_events import emit_menu_data
            emit_menu_data(session_id, items, current_meal_period=current_meal_period or "")
        except Exception as e:
            logger.debug("sync_emit_menu_data_failed", error=str(e))
    
    return emit_tool_activity_sync, emit_cart_data_sync, emit_menu_data_sync