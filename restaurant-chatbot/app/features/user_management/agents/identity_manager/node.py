"""
Identity Manager Sub-Agent
==========================
Handles updates to user identity information.

Responsibilities:
- Update user's full name
- Update user's email address
- Update user's phone number (with verification)
- Batch update multiple identity fields
- Retrieve current identity information
"""

from typing import Dict, Any
import structlog

from app.features.user_management.state import AuthenticationState
from app.features.user_management.tools import (
    get_user_identity,
    update_user_name,
    update_user_email,
    update_user_phone,
    update_user_profile
)

logger = structlog.get_logger("user_management.agents.identity_manager")


async def identity_manager_agent(
    entities: Dict[str, Any],
    state: AuthenticationState
) -> Dict[str, Any]:
    """
    Identity Manager sub-agent: Update user identity information.

    Args:
        entities: Extracted entities (field, value, full_name, email, phone)
        state: Current authentication state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")

    logger.info(
        "Identity manager agent executing",
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
                "message": "You must be logged in to update your identity information."
            },
            "context": {
                "requires_auth": True
            }
        }

    # Extract entities
    field = entities.get("field")  # name, email, phone, or None for batch update
    value = entities.get("value")
    full_name = entities.get("full_name")
    email = entities.get("email")
    phone = entities.get("phone_number") or entities.get("phone")

    # Action: View current identity
    if not any([field, full_name, email, phone]):
        logger.info("Retrieving user identity", user_id=user_id)

        identity_result = await get_user_identity(user_id)

        if not identity_result["success"]:
            return {
                "action": "identity_fetch_failed",
                "success": False,
                "data": {
                    "message": identity_result["message"]
                },
                "context": {}
            }

        return {
            "action": "identity_retrieved",
            "success": True,
            "data": {
                "message": "Here's your current identity information:",
                "user": identity_result["data"]["user"]
            },
            "context": {
                "action_completed": "view"
            }
        }

    # Batch update if multiple fields provided
    if sum([bool(full_name), bool(email), bool(phone)]) > 1:
        logger.info(
            "Batch updating identity",
            user_id=user_id,
            has_name=bool(full_name),
            has_email=bool(email),
            has_phone=bool(phone)
        )

        update_result = await update_user_profile(
            user_id=user_id,
            full_name=full_name,
            email=email,
            phone_number=phone
        )

        if not update_result["success"]:
            return {
                "action": "batch_update_failed",
                "success": False,
                "data": {
                    "message": update_result["message"]
                },
                "context": {}
            }

        return {
            "action": "identity_updated",
            "success": True,
            "data": {
                "message": update_result["message"],
                "updated_fields": update_result["data"]["updated_fields"]
            },
            "context": {
                "action_completed": "batch_update"
            }
        }

    # Single field update
    update_result = None

    # Update name
    if field == "name" or full_name:
        logger.info("Updating user name", user_id=user_id)

        name_value = value or full_name
        if not name_value:
            return {
                "action": "missing_value",
                "success": False,
                "data": {
                    "message": "Please provide your new name."
                },
                "context": {
                    "required_field": "full_name"
                }
            }

        update_result = await update_user_name(user_id, name_value)
        field_name = "name"

    # Update email
    elif field == "email" or email:
        logger.info("Updating user email", user_id=user_id)

        email_value = value or email
        if not email_value:
            return {
                "action": "missing_value",
                "success": False,
                "data": {
                    "message": "Please provide your new email address."
                },
                "context": {
                    "required_field": "email"
                }
            }

        update_result = await update_user_email(user_id, email_value)
        field_name = "email"

    # Update phone
    elif field == "phone" or phone:
        logger.info("Updating user phone", user_id=user_id)

        phone_value = value or phone
        if not phone_value:
            return {
                "action": "missing_value",
                "success": False,
                "data": {
                    "message": "Please provide your new phone number."
                },
                "context": {
                    "required_field": "phone"
                }
            }

        # Note: In production, this should trigger OTP verification
        # before allowing phone number change
        update_result = await update_user_phone(user_id, phone_value)
        field_name = "phone"

        # Add verification reminder
        if update_result and update_result["success"]:
            update_result["data"]["message"] += " Please verify your new number."

    else:
        return {
            "action": "unknown_field",
            "success": False,
            "data": {
                "message": f"Unknown field to update: {field}"
            },
            "context": {}
        }

    # Check update result
    if not update_result or not update_result["success"]:
        logger.error(
            "Identity update failed",
            user_id=user_id,
            field=field_name,
            error=update_result.get("message") if update_result else "Unknown error"
        )

        return {
            "action": "update_failed",
            "success": False,
            "data": {
                "message": update_result["message"] if update_result else "Update failed"
            },
            "context": {}
        }

    # Update successful
    logger.info(
        "Identity updated successfully",
        user_id=user_id,
        field=field_name
    )

    return {
        "action": "identity_updated",
        "success": True,
        "data": {
            "message": update_result["message"],
            "field": field_name,
            "updated_value": value or full_name or email or phone
        },
        "context": {
            "action_completed": "update",
            "updated_field": field_name
        }
    }


__all__ = ["identity_manager_agent"]
