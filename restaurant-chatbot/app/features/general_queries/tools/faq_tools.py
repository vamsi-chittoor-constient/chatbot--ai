"""
FAQ Tools
=========
Tools for FAQ search and management.
"""

from typing import Dict, Any, Optional, List
import structlog

from app.tools.database.queries_tools import SearchFAQTool, GetFAQTool, GetFeaturedFAQsTool
from app.core.database import get_db_session as get_db

logger = structlog.get_logger("general_queries.tools.faq")


async def search_faq(
    query: str,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Search FAQs using semantic search.

    Args:
        query: Search query
        limit: Maximum number of results

    Returns:
        Dict with success status and FAQ results
    """
    try:
        logger.info("Searching FAQs", query=query, limit=limit)

        async with get_db() as db:
            search_tool = SearchFAQTool()
            result = await search_tool._arun(query=query, limit=limit, db=db)

            # Parse result
            if "error" in result.lower() or "not found" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {
                        "faqs": [],
                        "count": 0
                    }
                }

            # Assume result is list of FAQs or formatted string
            faqs = result if isinstance(result, list) else []
            count = len(faqs)

            if count == 0:
                message = "No FAQs found matching your query."
            elif count == 1:
                message = "Found 1 relevant FAQ."
            else:
                message = f"Found {count} relevant FAQs."

            return {
                "success": True,
                "message": message,
                "data": {
                    "faqs": faqs,
                    "count": count,
                    "query": query
                }
            }

    except Exception as e:
        logger.error("FAQ search failed", error=str(e), query=query)

        return {
            "success": False,
            "message": f"FAQ search failed: {str(e)}",
            "data": {
                "faqs": [],
                "count": 0
            }
        }


async def get_faq_by_id(
    faq_id: str
) -> Dict[str, Any]:
    """
    Get specific FAQ by ID.

    Args:
        faq_id: FAQ identifier

    Returns:
        Dict with success status and FAQ data
    """
    try:
        logger.info("Getting FAQ by ID", faq_id=faq_id)

        async with get_db() as db:
            faq_tool = GetFAQTool()
            result = await faq_tool._arun(faq_id=faq_id, db=db)

            if "not found" in result.lower() or "error" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            return {
                "success": True,
                "message": "FAQ retrieved successfully",
                "data": {
                    "faq": result
                }
            }

    except Exception as e:
        logger.error("Get FAQ by ID failed", error=str(e), faq_id=faq_id)

        return {
            "success": False,
            "message": f"Failed to retrieve FAQ: {str(e)}",
            "data": {}
        }


async def get_featured_faqs(
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get featured/popular FAQs.

    Args:
        limit: Maximum number of FAQs

    Returns:
        Dict with success status and featured FAQs
    """
    try:
        logger.info("Getting featured FAQs", limit=limit)

        async with get_db() as db:
            featured_tool = GetFeaturedFAQsTool()
            result = await featured_tool._arun(limit=limit, db=db)

            if "error" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {
                        "faqs": [],
                        "count": 0
                    }
                }

            faqs = result if isinstance(result, list) else []
            count = len(faqs)

            return {
                "success": True,
                "message": f"Found {count} featured FAQ(s)",
                "data": {
                    "faqs": faqs,
                    "count": count
                }
            }

    except Exception as e:
        logger.error("Get featured FAQs failed", error=str(e))

        return {
            "success": False,
            "message": f"Failed to retrieve featured FAQs: {str(e)}",
            "data": {
                "faqs": [],
                "count": 0
            }
        }


async def get_faqs_by_category(
    category: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get FAQs filtered by category.

    Args:
        category: FAQ category (menu, orders, payments, reservations, etc.)
        limit: Maximum number of FAQs

    Returns:
        Dict with success status and category FAQs
    """
    try:
        logger.info("Getting FAQs by category", category=category, limit=limit)

        async with get_db() as db:
            # Use search with category filter
            search_tool = SearchFAQTool()
            result = await search_tool._arun(
                query=category,
                limit=limit,
                db=db
            )

            if "error" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {
                        "faqs": [],
                        "count": 0
                    }
                }

            faqs = result if isinstance(result, list) else []
            count = len(faqs)

            return {
                "success": True,
                "message": f"Found {count} FAQ(s) in category '{category}'",
                "data": {
                    "faqs": faqs,
                    "count": count,
                    "category": category
                }
            }

    except Exception as e:
        logger.error("Get FAQs by category failed", error=str(e), category=category)

        return {
            "success": False,
            "message": f"Failed to retrieve FAQs: {str(e)}",
            "data": {
                "faqs": [],
                "count": 0
            }
        }


__all__ = [
    "search_faq",
    "get_faq_by_id",
    "get_featured_faqs",
    "get_faqs_by_category"
]
