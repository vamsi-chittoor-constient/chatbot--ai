"""
Favorites Manager Sub-Agent
===========================
Handles user's favorite menu items management.

Responsibilities:
- Add items to favorites
- Remove items from favorites
- View all favorite items
"""

from typing import Dict, Any
import structlog

from app.features.user_profile.state import ProfileState
from app.features.user_profile.tools import (
    add_to_favorites,
    remove_from_favorites,
    get_user_favorites
)

logger = structlog.get_logger("user_profile.agents.favorites_manager")


async def favorites_manager_agent(
    entities: Dict[str, Any],
    state: ProfileState
) -> Dict[str, Any]:
    """
    Favorites Manager sub-agent: Manage favorite menu items.

    Args:
        entities: Extracted entities (item_id, item_name, action)
        state: Current profile state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")

    logger.info(
        "Favorites manager agent executing",
        session_id=session_id,
        user_id=user_id,
        entities=entities
    )

    # Must be authenticated
    if not user_id:
        return {
            "action": "authentication_required",
            "success": False,
            "data": {
                "message": "You must be logged in to manage favorites."
            },
            "context": {
                "requires_auth": True
            }
        }

    # Extract entities
    action = entities.get("action", "view")  # add, remove, view
    item_id = entities.get("item_id") or entities.get("menu_item_id")
    item_name = entities.get("item_name") or entities.get("menu_item_name")
    limit = entities.get("limit", 20)

    # Action: View favorites
    if action == "view" or (action not in ["add", "remove"] and not item_id):
        logger.info("Viewing favorites", user_id=user_id)

        favorites_result = await get_user_favorites(user_id, limit=limit)

        if not favorites_result["success"]:
            return {
                "action": "favorites_fetch_failed",
                "success": False,
                "data": {
                    "message": favorites_result["message"]
                },
                "context": {}
            }

        favorites = favorites_result["data"]["favorites"]
        count = favorites_result["data"]["count"]

        return {
            "action": "favorites_listed",
            "success": True,
            "data": {
                "message": favorites_result["message"],
                "favorites": favorites,
                "count": count
            },
            "context": {
                "action_completed": "view"
            }
        }

    # Action: Add to favorites
    elif action == "add":
        logger.info("Adding to favorites", user_id=user_id, item_id=item_id)

        if not item_id:
            return {
                "action": "missing_item_id",
                "success": False,
                "data": {
                    "message": "Please specify which item to add to favorites."
                },
                "context": {
                    "required_field": "item_id"
                }
            }

        add_result = await add_to_favorites(user_id, item_id, item_name)

        if not add_result["success"]:
            return {
                "action": "add_to_favorites_failed",
                "success": False,
                "data": {
                    "message": add_result["message"]
                },
                "context": {}
            }

        return {
            "action": "added_to_favorites",
            "success": True,
            "data": {
                "message": add_result["message"],
                "item_id": item_id,
                "item_name": item_name
            },
            "context": {
                "action_completed": "add"
            }
        }

    # Action: Remove from favorites
    elif action == "remove":
        logger.info("Removing from favorites", user_id=user_id, item_id=item_id)

        if not item_id:
            return {
                "action": "missing_item_id",
                "success": False,
                "data": {
                    "message": "Please specify which item to remove from favorites."
                },
                "context": {
                    "required_field": "item_id"
                }
            }

        remove_result = await remove_from_favorites(user_id, item_id, item_name)

        if not remove_result["success"]:
            return {
                "action": "remove_from_favorites_failed",
                "success": False,
                "data": {
                    "message": remove_result["message"]
                },
                "context": {}
            }

        return {
            "action": "removed_from_favorites",
            "success": True,
            "data": {
                "message": remove_result["message"],
                "item_id": item_id,
                "item_name": item_name
            },
            "context": {
                "action_completed": "remove"
            }
        }

    # Unknown action
    else:
        return {
            "action": "unknown_action",
            "success": False,
            "data": {
                "message": f"Unknown favorites action: {action}"
            },
            "context": {}
        }


__all__ = ["favorites_manager_agent"]
