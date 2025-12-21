"""
Preference Manager Sub-Agent
============================
Handles user dietary and cuisine preferences.

Responsibilities:
- Update dietary restrictions (vegetarian, vegan, gluten-free, etc.)
- Manage allergies
- Set favorite cuisines
- Configure spice level preference
- Set preferred seating
- View current preferences
"""

from typing import Dict, Any
import structlog

from app.features.user_profile.state import ProfileState
from app.features.user_profile.tools import (
    get_user_preferences,
    update_dietary_restrictions,
    update_allergies,
    update_favorite_cuisines,
    update_spice_level,
    update_preferred_seating
)

logger = structlog.get_logger("user_profile.agents.preference_manager")


async def preference_manager_agent(
    entities: Dict[str, Any],
    state: ProfileState
) -> Dict[str, Any]:
    """
    Preference Manager sub-agent: Manage user preferences.

    Args:
        entities: Extracted entities (dietary_restrictions, allergies, cuisines, etc.)
        state: Current profile state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")

    logger.info(
        "Preference manager agent executing",
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
                "message": "You must be logged in to manage preferences."
            },
            "context": {
                "requires_auth": True
            }
        }

    # Extract entities
    action = entities.get("action", "view")  # view, add, remove, set
    dietary_restrictions = entities.get("dietary_restrictions", [])
    allergies = entities.get("allergies", [])
    favorite_cuisines = entities.get("favorite_cuisines", [])
    spice_level = entities.get("spice_level")
    preferred_seating = entities.get("preferred_seating")

    # View current preferences
    if action == "view" and not any([dietary_restrictions, allergies, favorite_cuisines, spice_level, preferred_seating]):
        logger.info("Viewing user preferences", user_id=user_id)

        prefs_result = await get_user_preferences(user_id)

        if not prefs_result["success"]:
            return {
                "action": "preferences_fetch_failed",
                "success": False,
                "data": {
                    "message": prefs_result["message"]
                },
                "context": {}
            }

        preferences = prefs_result["data"].get("preferences", {})

        return {
            "action": "preferences_retrieved",
            "success": True,
            "data": {
                "message": "Here are your current preferences:",
                "preferences": preferences
            },
            "context": {
                "action_completed": "view"
            }
        }

    # Update preferences
    updated_fields = []
    errors = []

    # Update dietary restrictions
    if dietary_restrictions:
        logger.info("Updating dietary restrictions", user_id=user_id, restrictions=dietary_restrictions)

        result = await update_dietary_restrictions(user_id, dietary_restrictions, action)

        if result["success"]:
            updated_fields.append("dietary restrictions")
        else:
            errors.append(f"dietary restrictions: {result['message']}")

    # Update allergies
    if allergies:
        logger.info("Updating allergies", user_id=user_id, allergies=allergies)

        result = await update_allergies(user_id, allergies, action)

        if result["success"]:
            updated_fields.append("allergies")
        else:
            errors.append(f"allergies: {result['message']}")

    # Update favorite cuisines
    if favorite_cuisines:
        logger.info("Updating favorite cuisines", user_id=user_id, cuisines=favorite_cuisines)

        result = await update_favorite_cuisines(user_id, favorite_cuisines, action)

        if result["success"]:
            updated_fields.append("favorite cuisines")
        else:
            errors.append(f"favorite cuisines: {result['message']}")

    # Update spice level
    if spice_level:
        logger.info("Updating spice level", user_id=user_id, spice_level=spice_level)

        result = await update_spice_level(user_id, spice_level)

        if result["success"]:
            updated_fields.append("spice level")
        else:
            errors.append(f"spice level: {result['message']}")

    # Update preferred seating
    if preferred_seating:
        logger.info("Updating preferred seating", user_id=user_id, seating=preferred_seating)

        result = await update_preferred_seating(user_id, preferred_seating)

        if result["success"]:
            updated_fields.append("seating preference")
        else:
            errors.append(f"seating preference: {result['message']}")

    # Check if any updates were made
    if not updated_fields and not errors:
        return {
            "action": "no_updates",
            "success": False,
            "data": {
                "message": "No preference updates were provided."
            },
            "context": {}
        }

    # Build response message
    if updated_fields and not errors:
        message = f"Successfully updated: {', '.join(updated_fields)}."
        success = True
        action_name = "preferences_updated"
    elif updated_fields and errors:
        message = f"Partially updated: {', '.join(updated_fields)}. Errors: {', '.join(errors)}."
        success = True
        action_name = "preferences_partially_updated"
    else:
        message = f"Failed to update preferences. Errors: {', '.join(errors)}."
        success = False
        action_name = "preferences_update_failed"

    logger.info(
        "Preferences update completed",
        user_id=user_id,
        updated_fields=updated_fields,
        errors=errors
    )

    return {
        "action": action_name,
        "success": success,
        "data": {
            "message": message,
            "updated_fields": updated_fields,
            "errors": errors
        },
        "context": {
            "action_completed": "update",
            "updated_count": len(updated_fields)
        }
    }


__all__ = ["preference_manager_agent"]
