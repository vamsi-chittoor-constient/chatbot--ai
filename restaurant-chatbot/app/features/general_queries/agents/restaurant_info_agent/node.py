"""
Restaurant Info Agent
====================
Handles restaurant operational information queries.

Responsibilities:
- Fetch business hours
- Provide location and address
- Contact information (phone, email)
- Parking details
- Branch information
"""

from typing import Dict, Any
import structlog

from app.features.general_queries.state import GeneralQueriesState
from app.features.general_queries.tools import (
    get_restaurant_info,
    get_business_hours,
    get_location_info,
    get_contact_info,
    get_parking_info
)

logger = structlog.get_logger("general_queries.agents.restaurant_info")


async def restaurant_info_agent(
    entities: Dict[str, Any],
    state: GeneralQueriesState
) -> Dict[str, Any]:
    """
    Restaurant Info agent: Provide operational information.

    Args:
        entities: Extracted entities (info_type)
        state: Current queries state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    queries_progress = state.get("queries_progress")

    logger.info(
        "Restaurant info agent executing",
        session_id=session_id,
        entities=entities
    )

    # Extract entities
    info_type = entities.get("info_type", "general")

    # Route to appropriate info retrieval
    if info_type == "hours":
        logger.info("Getting business hours")

        hours_result = await get_business_hours()

        if not hours_result["success"]:
            return {
                "action": "hours_fetch_failed",
                "success": False,
                "data": {
                    "message": hours_result["message"]
                },
                "context": {}
            }

        hours = hours_result["data"]["hours"]

        # Update progress
        if queries_progress:
            queries_progress.info_type = "hours"
            queries_progress.restaurant_info = hours_result["data"]
            queries_progress.restaurant_info_fetched = True

        return {
            "action": "hours_retrieved",
            "success": True,
            "data": {
                "message": "Here are our business hours:",
                "hours": hours
            },
            "context": {
                "action_completed": "get_hours"
            }
        }

    elif info_type == "location":
        logger.info("Getting location info")

        location_result = await get_location_info()

        if not location_result["success"]:
            return {
                "action": "location_fetch_failed",
                "success": False,
                "data": {
                    "message": location_result["message"]
                },
                "context": {}
            }

        # Update progress
        if queries_progress:
            queries_progress.info_type = "location"
            queries_progress.restaurant_info = location_result["data"]
            queries_progress.restaurant_info_fetched = True

        return {
            "action": "location_retrieved",
            "success": True,
            "data": {
                "message": "Here's our location:",
                "address": location_result["data"].get("address"),
                "branch_name": location_result["data"].get("branch_name")
            },
            "context": {
                "action_completed": "get_location"
            }
        }

    elif info_type == "contact":
        logger.info("Getting contact info")

        contact_result = await get_contact_info()

        if not contact_result["success"]:
            return {
                "action": "contact_fetch_failed",
                "success": False,
                "data": {
                    "message": contact_result["message"]
                },
                "context": {}
            }

        # Update progress
        if queries_progress:
            queries_progress.info_type = "contact"
            queries_progress.restaurant_info = contact_result["data"]
            queries_progress.restaurant_info_fetched = True

        return {
            "action": "contact_retrieved",
            "success": True,
            "data": {
                "message": "Here's how to reach us:",
                "phone": contact_result["data"].get("phone"),
                "email": contact_result["data"].get("email")
            },
            "context": {
                "action_completed": "get_contact"
            }
        }

    elif info_type == "parking":
        logger.info("Getting parking info")

        parking_result = await get_parking_info()

        if not parking_result["success"]:
            return {
                "action": "parking_fetch_failed",
                "success": False,
                "data": {
                    "message": parking_result["message"]
                },
                "context": {}
            }

        # Update progress
        if queries_progress:
            queries_progress.info_type = "parking"
            queries_progress.restaurant_info = parking_result["data"]
            queries_progress.restaurant_info_fetched = True

        return {
            "action": "parking_retrieved",
            "success": True,
            "data": {
                "message": "Here's parking information:",
                "parking": parking_result["data"].get("parking")
            },
            "context": {
                "action_completed": "get_parking"
            }
        }

    else:  # general
        logger.info("Getting general restaurant info")

        info_result = await get_restaurant_info(info_type="general")

        if not info_result["success"]:
            return {
                "action": "info_fetch_failed",
                "success": False,
                "data": {
                    "message": info_result["message"]
                },
                "context": {}
            }

        # Update progress
        if queries_progress:
            queries_progress.info_type = "general"
            queries_progress.restaurant_info = info_result["data"]
            queries_progress.restaurant_info_fetched = True

        return {
            "action": "info_retrieved",
            "success": True,
            "data": {
                "message": "Here's our restaurant information:",
                "name": info_result["data"].get("name"),
                "address": info_result["data"].get("address"),
                "phone": info_result["data"].get("phone"),
                "email": info_result["data"].get("email"),
                "hours": info_result["data"].get("business_hours")
            },
            "context": {
                "action_completed": "get_general_info"
            }
        }


__all__ = ["restaurant_info_agent"]
