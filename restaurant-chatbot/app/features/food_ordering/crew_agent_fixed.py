"""
Fixed CrewAI Food Ordering Agent - Sync Tools Only
"""
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
from typing import Dict, Any, List, Optional
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)

def create_search_menu_tool(session_id: str):
    @tool("search_menu")
    def search_menu(query: Optional[str] = None) -> str:
        """Search the restaurant menu for food items."""
        from app.features.food_ordering.crew_agent import _search_menu_impl
        # Convert None to empty string for backward compatibility
        return _search_menu_impl(query or "", session_id)
    return search_menu

def create_add_to_cart_tool(session_id: str):
    @tool("add_to_cart")
    def add_to_cart(item: str, quantity: int = 1) -> str:
        """Add a food item to the customer's cart."""
        from app.features.food_ordering.crew_agent import _add_to_cart_impl
        return _add_to_cart_impl(item, quantity, session_id)
    return add_to_cart

def create_view_cart_tool(session_id: str):
    @tool("view_cart")
    def view_cart() -> str:
        """View the current contents of the customer's shopping cart."""
        from app.features.food_ordering.crew_agent import _view_cart_impl
        return _view_cart_impl(session_id)
    return view_cart

def create_checkout_tool(session_id: str):
    @tool("checkout")
    def checkout(order_type: Optional[str] = None) -> str:
        """Complete the order and place it."""
        from app.features.food_ordering.crew_agent import _checkout_impl
        return _checkout_impl(order_type or "", session_id)
    return checkout

def create_food_ordering_crew_fixed(session_id: str) -> Crew:
    """Create crew with sync tools only."""
    import os
    from langchain_openai import ChatOpenAI
    from app.ai_services.llm_manager import get_llm_manager

    llm_manager = get_llm_manager()
    api_key = llm_manager.get_next_api_key()
    os.environ["OPENAI_API_KEY"] = api_key

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=api_key,
        max_tokens=256,
    )

    # Sync tools only
    search_tool = create_search_menu_tool(session_id)
    add_tool = create_add_to_cart_tool(session_id)
    view_tool = create_view_cart_tool(session_id)
    checkout_tool = create_checkout_tool(session_id)

    agent = Agent(
        role="Restaurant Assistant",
        goal="Help customers order food",
        backstory="You help customers browse menu and place orders.",
        llm=llm,
        tools=[search_tool, add_tool, view_tool, checkout_tool],
        verbose=False,
        allow_delegation=False,
        max_iter=10,
    )

    task = Task(
        description="Customer: {user_input}\nContext: {context}\nHelp the customer with their request.",
        expected_output="A helpful response",
        agent=agent
    )

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False,
    )

async def test_sync_tools():
    """Test that sync tools work with akickoff()"""
    session_id = "test_session"
    crew = create_food_ordering_crew_fixed(session_id)
    
    inputs = {
        "user_input": "show me the menu",
        "context": "No previous context"
    }
    
    try:
        # This should work now with sync tools
        result = await crew.akickoff(inputs=inputs)
        print(f"✅ Success: {result}")
        return True
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_sync_tools())