"""
MCP-Based Food Ordering Agent
==============================
Simplified agent using direct MCP tool calls instead of ReAct reasoning.
Eliminates hallucinations and ensures reliable database operations.
"""

from typing import Dict, Any
import structlog
from langchain_core.messages import HumanMessage, AIMessage

from app.features.food_ordering.state import FoodOrderingState
from app.mcp_server import get_mcp_tools
from langgraph.prebuilt import create_react_agent
from app.ai_services.agent_llm_factory import get_llm_for_agent

logger = structlog.get_logger("food_ordering.mcp_agent")


async def mcp_food_ordering_agent(state: FoodOrderingState) -> Dict[str, Any]:
    """
    Food ordering agent using MCP tools for reliable operations.

    Args:
        state: Current food ordering state

    Returns:
        Updated state with agent response
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")
    sub_intent = state.get("current_sub_intent", "unknown")

    logger.info(
        "MCP food ordering agent started",
        session_id=session_id,
        sub_intent=sub_intent
    )

    try:
        # Get all MCP tools
        mcp_tools = get_mcp_tools()

        # Get LLM
        llm = get_llm_for_agent("food_ordering_mcp", temperature=0.1)

        # Create agent with MCP tools
        agent = create_react_agent(llm, mcp_tools)

        # Get user message
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": [AIMessage(content="I didn't receive your message. Could you try again?")],
                "should_end": True
            }

        latest_message = messages[-1]
        user_content = latest_message.content if hasattr(latest_message, 'content') else str(latest_message)

        # Add context to message
        enhanced_message = f"""Session ID: {session_id}
User ID: {user_id or 'anonymous'}
Sub-intent: {sub_intent}
Restaurant ID: {state.get('restaurant_id', 'rest_001')}

User message: {user_content}

Available tools:
- browse_menu: Browse menu categories
- search_menu: Semantic search for items
- get_menu_item: Get specific item details
- add_to_cart: Add items to cart
- view_cart: View current cart
- update_cart_item: Update item quantity
- clear_cart: Empty the cart

Instructions:
1. For menu requests: Use browse_menu or search_menu
2. For item queries: Use get_menu_item
3. For adding items: Use add_to_cart (requires item_name, quantity, session_id)
4. For cart operations: Use view_cart, update_cart_item, or clear_cart
5. ALWAYS pass session_id to cart operations
6. Present results in a friendly, conversational way
"""

        # Invoke agent
        result = await agent.ainvoke({
            "messages": [HumanMessage(content=enhanced_message)]
        })

        # Extract AI response
        agent_messages = result.get("messages", [])
        if not agent_messages:
            return {
                "messages": [AIMessage(content="I encountered an issue. Please try again.")],
                "should_end": True
            }

        # Get final AI message
        final_message = agent_messages[-1]
        response_content = final_message.content if hasattr(final_message, 'content') else str(final_message)

        logger.info(
            "MCP agent completed",
            session_id=session_id,
            response_length=len(response_content)
        )

        return {
            "messages": [AIMessage(content=response_content)],
            "should_end": True
        }

    except Exception as e:
        logger.error(
            "MCP food ordering agent failed",
            session_id=session_id,
            error=str(e),
            exc_info=True
        )

        return {
            "messages": [AIMessage(content="I apologize, but I encountered an error. Please try again.")],
            "should_end": True,
            "error": str(e)
        }
