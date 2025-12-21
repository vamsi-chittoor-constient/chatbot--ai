"""
Knowledge Agent
===============
Handles FAQ and policy knowledge base queries.

Responsibilities:
- Search FAQs with semantic matching
- Get featured FAQs
- Filter FAQs by category
- Search policies by type
- Explain policy details
"""

from typing import Dict, Any
import structlog

from app.features.general_queries.state import GeneralQueriesState
from app.features.general_queries.tools import (
    search_faq,
    get_faq_by_id,
    get_featured_faqs,
    get_faqs_by_category,
    search_policies,
    get_policy_by_type
)

logger = structlog.get_logger("general_queries.agents.knowledge")


async def knowledge_agent(
    entities: Dict[str, Any],
    state: GeneralQueriesState
) -> Dict[str, Any]:
    """
    Knowledge agent: Handle FAQ and policy queries.

    Args:
        entities: Extracted entities (query, faq_category, policy_type)
        state: Current queries state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    queries_progress = state.get("queries_progress")

    logger.info(
        "Knowledge agent executing",
        session_id=session_id,
        entities=entities
    )

    # Extract entities
    query = entities.get("query") or queries_progress.query_text if queries_progress else None
    faq_category = entities.get("faq_category")
    policy_type = entities.get("policy_type")
    faq_id = entities.get("faq_id")

    # Priority 1: Get specific FAQ by ID
    if faq_id:
        logger.info("Getting FAQ by ID", faq_id=faq_id)

        faq_result = await get_faq_by_id(faq_id)

        if not faq_result["success"]:
            return {
                "action": "faq_not_found",
                "success": False,
                "data": {
                    "message": faq_result["message"]
                },
                "context": {}
            }

        return {
            "action": "faq_retrieved",
            "success": True,
            "data": {
                "message": "Here's the FAQ you requested:",
                "faq": faq_result["data"]["faq"]
            },
            "context": {
                "action_completed": "get_faq"
            }
        }

    # Priority 2: Search policies
    if policy_type:
        logger.info("Searching policies", policy_type=policy_type)

        policy_result = await get_policy_by_type(policy_type)

        if not policy_result["success"]:
            # Try generic search
            policy_result = await search_policies(policy_type=policy_type)

        if not policy_result["success"] or policy_result["data"]["count"] == 0:
            return {
                "action": "policy_not_found",
                "success": False,
                "data": {
                    "message": f"I couldn't find information about '{policy_type}' policy. Would you like to see all available policies?"
                },
                "context": {}
            }

        policies = policy_result["data"]["policies"]

        # Update progress
        if queries_progress:
            queries_progress.policy_type = policy_type
            queries_progress.policy_results = policies
            queries_progress.policy_retrieved = True

        return {
            "action": "policy_retrieved",
            "success": True,
            "data": {
                "message": f"Here's our {policy_type} policy:",
                "policies": policies,
                "count": len(policies)
            },
            "context": {
                "action_completed": "search_policy",
                "policy_type": policy_type
            }
        }

    # Priority 3: Search FAQs by category
    if faq_category and not query:
        logger.info("Getting FAQs by category", category=faq_category)

        category_result = await get_faqs_by_category(faq_category, limit=10)

        if not category_result["success"]:
            return {
                "action": "category_search_failed",
                "success": False,
                "data": {
                    "message": category_result["message"]
                },
                "context": {}
            }

        faqs = category_result["data"]["faqs"]

        # Update progress
        if queries_progress:
            queries_progress.faq_category_filter = faq_category
            queries_progress.faq_results = faqs
            queries_progress.faq_searched = True

        return {
            "action": "faqs_by_category",
            "success": True,
            "data": {
                "message": category_result["message"],
                "faqs": faqs,
                "count": len(faqs),
                "category": faq_category
            },
            "context": {
                "action_completed": "category_search"
            }
        }

    # Priority 4: Search FAQs with query
    if query:
        logger.info("Searching FAQs", query=query)

        faq_result = await search_faq(query, limit=5)

        if not faq_result["success"]:
            return {
                "action": "faq_search_failed",
                "success": False,
                "data": {
                    "message": faq_result["message"]
                },
                "context": {}
            }

        faqs = faq_result["data"]["faqs"]

        # Update progress
        if queries_progress:
            queries_progress.faq_search_query = query
            queries_progress.faq_results = faqs
            queries_progress.faq_searched = True

        if len(faqs) == 0:
            return {
                "action": "no_faqs_found",
                "success": True,
                "data": {
                    "message": "I couldn't find any FAQs matching your query. Would you like to see featured FAQs or contact support?"
                },
                "context": {
                    "no_results": True
                }
            }

        return {
            "action": "faqs_found",
            "success": True,
            "data": {
                "message": faq_result["message"],
                "faqs": faqs,
                "count": len(faqs),
                "query": query
            },
            "context": {
                "action_completed": "search_faq"
            }
        }

    # Default: Get featured FAQs
    logger.info("Getting featured FAQs")

    featured_result = await get_featured_faqs(limit=10)

    if not featured_result["success"]:
        return {
            "action": "featured_failed",
            "success": False,
            "data": {
                "message": featured_result["message"]
            },
            "context": {}
        }

    faqs = featured_result["data"]["faqs"]

    # Update progress
    if queries_progress:
        queries_progress.faq_results = faqs
        queries_progress.faq_searched = True

    return {
        "action": "featured_faqs",
        "success": True,
        "data": {
            "message": "Here are our most frequently asked questions:",
            "faqs": faqs,
            "count": len(faqs)
        },
        "context": {
            "action_completed": "featured_faqs"
        }
    }


__all__ = ["knowledge_agent"]
