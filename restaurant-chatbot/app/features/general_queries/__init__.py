"""
General Queries Feature
=======================
FAQ, policy, and restaurant information feature with sub-agent architecture.

Features:
- FAQ search with semantic matching
- Policy inquiries
- Restaurant operational information
- General assistance

NOTE: LangGraph implementation removed. System now uses Sticky Crew orchestrator.
Only schemas, models, and tools remain for potential future use.

Sub-Agents (REMOVED - using Sticky Crew):
- knowledge_agent: FAQ and policy knowledge base
- restaurant_info_agent: Hours, location, contact information
- general_assistant_agent: General questions and fallback
"""

# LangGraph imports removed - using Sticky Crew orchestrator instead
# from app.features.general_queries.node import general_queries_node
# from app.features.general_queries.state import GeneralQueriesState, GeneralQueriesProgress
# from app.features.general_queries.graph import create_general_queries_graph

__all__ = [
    # LangGraph components removed - using Sticky Crew
    # "general_queries_node",
    # "GeneralQueriesState",
    # "GeneralQueriesProgress",
    # "create_general_queries_graph"
]
