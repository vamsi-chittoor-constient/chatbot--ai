"""
Preference Management Tools
===========================
Tools for managing user dietary and cuisine preferences.
"""

from typing import Dict, Any, Optional, List
import structlog

from app.tools.database.user_tools import UpdateUserPreferencesTool, GetUserTool
from app.core.database import get_db_session as get_db

logger = structlog.get_logger("user_profile.tools.preferences")


async def get_user_preferences(
    user_id: str
) -> Dict[str, Any]:
    """
    Get user's current preferences.

    Args:
        user_id: User identifier

    Returns:
        Dict with success status and preferences data
    """
    try:
        logger.info("Getting user preferences", user_id=user_id)

        async with get_db() as db:
            user_tool = GetUserTool()
            result = await user_tool._arun(user_id=user_id, db=db)

            if "not found" in result.lower():
                return {
                    "success": False,
                    "message": "User not found",
                    "data": {}
                }

            # Extract preferences from user data
            # In production, this would parse the actual user preferences
            return {
                "success": True,
                "message": "Preferences retrieved",
                "data": {
                    "preferences": result.get("preferences", {})
                }
            }

    except Exception as e:
        logger.error("Failed to get preferences", error=str(e), user_id=user_id)

        return {
            "success": False,
            "message": f"Failed to retrieve preferences: {str(e)}",
            "data": {}
        }


async def update_dietary_restrictions(
    user_id: str,
    dietary_restrictions: List[str],
    action: str = "set"  # set, add, remove
) -> Dict[str, Any]:
    """
    Update user's dietary restrictions.

    Args:
        user_id: User identifier
        dietary_restrictions: List of dietary restrictions
        action: set (replace all), add (append), or remove

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info(
            "Updating dietary restrictions",
            user_id=user_id,
            restrictions=dietary_restrictions,
            action=action
        )

        async with get_db() as db:
            prefs_tool = UpdateUserPreferencesTool()
            result = await prefs_tool._arun(
                user_id=user_id,
                dietary_restrictions=dietary_restrictions,
                action=action,
                db=db
            )

            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            return {
                "success": True,
                "message": f"Dietary restrictions {action}",
                "data": {
                    "dietary_restrictions": dietary_restrictions,
                    "action": action
                }
            }

    except Exception as e:
        logger.error("Failed to update dietary restrictions", error=str(e), user_id=user_id)

        return {
            "success": False,
            "message": f"Failed to update dietary restrictions: {str(e)}",
            "data": {}
        }


async def update_allergies(
    user_id: str,
    allergies: List[str],
    action: str = "set"  # set, add, remove
) -> Dict[str, Any]:
    """
    Update user's allergies.

    Args:
        user_id: User identifier
        allergies: List of allergies
        action: set (replace all), add (append), or remove

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info(
            "Updating allergies",
            user_id=user_id,
            allergies=allergies,
            action=action
        )

        async with get_db() as db:
            prefs_tool = UpdateUserPreferencesTool()
            result = await prefs_tool._arun(
                user_id=user_id,
                allergies=allergies,
                action=action,
                db=db
            )

            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            return {
                "success": True,
                "message": f"Allergies {action}",
                "data": {
                    "allergies": allergies,
                    "action": action
                }
            }

    except Exception as e:
        logger.error("Failed to update allergies", error=str(e), user_id=user_id)

        return {
            "success": False,
            "message": f"Failed to update allergies: {str(e)}",
            "data": {}
        }


async def update_favorite_cuisines(
    user_id: str,
    favorite_cuisines: List[str],
    action: str = "set"  # set, add, remove
) -> Dict[str, Any]:
    """
    Update user's favorite cuisines.

    Args:
        user_id: User identifier
        favorite_cuisines: List of favorite cuisines
        action: set (replace all), add (append), or remove

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info(
            "Updating favorite cuisines",
            user_id=user_id,
            cuisines=favorite_cuisines,
            action=action
        )

        async with get_db() as db:
            prefs_tool = UpdateUserPreferencesTool()
            result = await prefs_tool._arun(
                user_id=user_id,
                favorite_cuisines=favorite_cuisines,
                action=action,
                db=db
            )

            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            return {
                "success": True,
                "message": f"Favorite cuisines {action}",
                "data": {
                    "favorite_cuisines": favorite_cuisines,
                    "action": action
                }
            }

    except Exception as e:
        logger.error("Failed to update favorite cuisines", error=str(e), user_id=user_id)

        return {
            "success": False,
            "message": f"Failed to update favorite cuisines: {str(e)}",
            "data": {}
        }


async def update_spice_level(
    user_id: str,
    spice_level: str  # mild, medium, hot, extra_hot
) -> Dict[str, Any]:
    """
    Update user's preferred spice level.

    Args:
        user_id: User identifier
        spice_level: Preferred spice level

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info("Updating spice level", user_id=user_id, spice_level=spice_level)

        async with get_db() as db:
            prefs_tool = UpdateUserPreferencesTool()
            result = await prefs_tool._arun(
                user_id=user_id,
                spice_level=spice_level,
                db=db
            )

            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            return {
                "success": True,
                "message": f"Spice preference updated to '{spice_level}'",
                "data": {
                    "spice_level": spice_level
                }
            }

    except Exception as e:
        logger.error("Failed to update spice level", error=str(e), user_id=user_id)

        return {
            "success": False,
            "message": f"Failed to update spice level: {str(e)}",
            "data": {}
        }


async def update_preferred_seating(
    user_id: str,
    preferred_seating: str  # indoor, outdoor, bar, window
) -> Dict[str, Any]:
    """
    Update user's preferred seating.

    Args:
        user_id: User identifier
        preferred_seating: Preferred seating type

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info("Updating preferred seating", user_id=user_id, seating=preferred_seating)

        async with get_db() as db:
            prefs_tool = UpdateUserPreferencesTool()
            result = await prefs_tool._arun(
                user_id=user_id,
                preferred_seating=preferred_seating,
                db=db
            )

            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            return {
                "success": True,
                "message": f"Seating preference updated to '{preferred_seating}'",
                "data": {
                    "preferred_seating": preferred_seating
                }
            }

    except Exception as e:
        logger.error("Failed to update preferred seating", error=str(e), user_id=user_id)

        return {
            "success": False,
            "message": f"Failed to update seating preference: {str(e)}",
            "data": {}
        }


__all__ = [
    "get_user_preferences",
    "update_dietary_restrictions",
    "update_allergies",
    "update_favorite_cuisines",
    "update_spice_level",
    "update_preferred_seating"
]
