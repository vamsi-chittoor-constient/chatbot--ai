"""
Policy Tools
============
Tools for restaurant policy search and retrieval.
"""

from typing import Dict, Any, Optional
import structlog

from app.tools.database.queries_tools import SearchRestaurantPolicyTool
from app.core.database import get_db_session as get_db

logger = structlog.get_logger("general_queries.tools.policy")


# Hardcoded policy templates (fallback if database empty)
POLICY_TEMPLATES = {
    "cancellation": {
        "title": "Cancellation Policy",
        "description": "You may cancel your reservation up to 2 hours before your booking time without penalty. Cancellations made less than 2 hours before will incur a $25 cancellation fee."
    },
    "refund": {
        "title": "Refund Policy",
        "description": "Full refunds are available for cancellations made 24+ hours in advance. Partial refunds (50%) for 2-24 hours notice. No refunds for same-day cancellations or no-shows."
    },
    "reservation": {
        "title": "Reservation Policy",
        "description": "Reservations can be made up to 30 days in advance. We hold your table for 15 minutes past your reservation time. Please call if running late."
    },
    "dietary": {
        "title": "Dietary Accommodations",
        "description": "We accommodate vegetarian, vegan, and gluten-free diets. Please inform your server of any dietary restrictions when ordering."
    },
    "allergen": {
        "title": "Allergen Policy",
        "description": "Please inform staff of any allergies. While we take precautions, we cannot guarantee allergen-free meals due to shared kitchen equipment."
    },
    "group_booking": {
        "title": "Group Booking Policy",
        "description": "For parties of 8+, please contact us directly. A deposit may be required. Group menus available upon request."
    },
    "payment": {
        "title": "Payment Policy",
        "description": "We accept all major credit cards, debit cards, and cash. Split payments are available. We do not accept checks."
    },
    "privacy": {
        "title": "Privacy Policy",
        "description": "We protect your personal information and only use it for reservations and communication. We never share your data with third parties."
    }
}


async def search_policies(
    policy_type: Optional[str] = None,
    query: Optional[str] = None
) -> Dict[str, Any]:
    """
    Search restaurant policies.

    Args:
        policy_type: Type of policy (cancellation, refund, etc.)
        query: Search query text

    Returns:
        Dict with success status and policy results
    """
    try:
        logger.info("Searching policies", policy_type=policy_type, query=query)

        # Try database first
        async with get_db() as db:
            search_tool = SearchRestaurantPolicyTool()

            # Use policy_type or query
            search_term = policy_type or query or "general"

            result = await search_tool._arun(
                policy_type=search_term,
                db=db
            )

            # Check if database returned results
            if result and not ("error" in str(result).lower() or "not found" in str(result).lower()):
                policies = result if isinstance(result, list) else [result]

                return {
                    "success": True,
                    "message": f"Found {len(policies)} policy/policies",
                    "data": {
                        "policies": policies,
                        "count": len(policies),
                        "source": "database"
                    }
                }

        # Fallback to templates
        if policy_type and policy_type in POLICY_TEMPLATES:
            policy = POLICY_TEMPLATES[policy_type]

            return {
                "success": True,
                "message": f"{policy['title']} retrieved",
                "data": {
                    "policies": [policy],
                    "count": 1,
                    "source": "template"
                }
            }

        # No specific policy found, return all templates
        all_policies = list(POLICY_TEMPLATES.values())

        return {
            "success": True,
            "message": f"Found {len(all_policies)} policies",
            "data": {
                "policies": all_policies,
                "count": len(all_policies),
                "source": "template"
            }
        }

    except Exception as e:
        logger.error("Policy search failed", error=str(e), policy_type=policy_type)

        return {
            "success": False,
            "message": f"Policy search failed: {str(e)}",
            "data": {
                "policies": [],
                "count": 0
            }
        }


async def get_policy_by_type(
    policy_type: str
) -> Dict[str, Any]:
    """
    Get specific policy by type.

    Args:
        policy_type: Type of policy

    Returns:
        Dict with success status and policy data
    """
    try:
        logger.info("Getting policy by type", policy_type=policy_type)

        # Search for specific policy
        result = await search_policies(policy_type=policy_type)

        if result["success"] and result["data"]["count"] > 0:
            policy = result["data"]["policies"][0]

            return {
                "success": True,
                "message": f"Policy '{policy_type}' retrieved",
                "data": {
                    "policy": policy,
                    "policy_type": policy_type
                }
            }

        return {
            "success": False,
            "message": f"Policy '{policy_type}' not found",
            "data": {}
        }

    except Exception as e:
        logger.error("Get policy by type failed", error=str(e), policy_type=policy_type)

        return {
            "success": False,
            "message": f"Failed to retrieve policy: {str(e)}",
            "data": {}
        }


async def get_all_policies() -> Dict[str, Any]:
    """
    Get all available policies.

    Returns:
        Dict with success status and all policies
    """
    try:
        logger.info("Getting all policies")

        # Try database first
        async with get_db() as db:
            search_tool = SearchRestaurantPolicyTool()
            result = await search_tool._arun(policy_type="all", db=db)

            if result and isinstance(result, list) and len(result) > 0:
                return {
                    "success": True,
                    "message": f"Found {len(result)} policies",
                    "data": {
                        "policies": result,
                        "count": len(result),
                        "source": "database"
                    }
                }

        # Fallback to templates
        all_policies = list(POLICY_TEMPLATES.values())

        return {
            "success": True,
            "message": f"Found {len(all_policies)} policies",
            "data": {
                "policies": all_policies,
                "count": len(all_policies),
                "source": "template"
            }
        }

    except Exception as e:
        logger.error("Get all policies failed", error=str(e))

        return {
            "success": False,
            "message": f"Failed to retrieve policies: {str(e)}",
            "data": {
                "policies": [],
                "count": 0
            }
        }


__all__ = [
    "search_policies",
    "get_policy_by_type",
    "get_all_policies"
]
