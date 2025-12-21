"""
Food Ordering Feature
====================

Complete food ordering flow from menu browsing to order placement.

This feature handles:
- Menu browsing and discovery
- Cart management with inventory reservation
- Order creation and checkout
- Integration with payment and notification services

Main Components:
- crew_agent.py: Sticky Crew agent (ACTIVE)
- graph.py: LangGraph sub-agent orchestration (REMOVED - not used)
- state.py: LangGraph feature state management (REMOVED - not used)
- agents/: LangGraph sub-agents (REMOVED - not used)
- tools/: Food ordering tools (USED by Sticky Crew)
- services/: Feature-specific services (USED by Sticky Crew)
- models/: Database models (USED by Sticky Crew)
- schemas/: Pydantic schemas (USED by Sticky Crew)

NOTE: System now uses Sticky Crew orchestrator (crew_agent.py).
LangGraph files (graph.py, state.py, node.py) are not imported to avoid errors.

OLD Usage (LangGraph):
    from app.features.food_ordering import food_ordering_graph
    from app.features.food_ordering.state import FoodOrderingState

NEW Usage (Sticky Crew):
    from app.features.food_ordering.crew_agent import create_food_ordering_crew
"""

# LangGraph imports removed - using Sticky Crew orchestrator instead
# from app.features.food_ordering.graph import food_ordering_agent
# from app.features.food_ordering.state import FoodOrderingState, OrderProgress
# from app.features.food_ordering.node import food_ordering_agent_node
# from app.features.food_ordering.cache import food_ordering_cache
# from app.features.food_ordering.logger import food_ordering_logger

__all__ = [
    # LangGraph components removed - using Sticky Crew
    # "food_ordering_agent",
    # "food_ordering_agent_node",
    # "FoodOrderingState",
    # "OrderProgress",
    # "food_ordering_cache",
    # "food_ordering_logger",
]
