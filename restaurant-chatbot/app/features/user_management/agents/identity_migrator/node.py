"""
Identity Migrator Sub-Agent
===========================
Handles migration of anonymous device data to authenticated user accounts.

Responsibilities:
- Migrate shopping cart items from device to user
- Migrate favorite items from device to user
- Migrate browsing history from device to user
- Migrate device preferences to user preferences
- Provide migration summary
"""

from typing import Dict, Any
import structlog

from app.features.user_management.state import AuthenticationState
from app.features.user_management.tools import (
    migrate_device_data,
    get_device_data_summary,
    link_device_to_user
)

logger = structlog.get_logger("user_management.agents.identity_migrator")


async def identity_migrator_agent(
    entities: Dict[str, Any],
    state: AuthenticationState
) -> Dict[str, Any]:
    """
    Identity Migrator sub-agent: Migrate device data to user account.

    Args:
        entities: Extracted entities (migration_type, device_id)
        state: Current authentication state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")
    device_id = state.get("device_id") or entities.get("device_id")
    auth_progress = state.get("auth_progress")

    logger.info(
        "Identity migrator agent executing",
        session_id=session_id,
        user_id=user_id,
        device_id=device_id
    )

    # Must be authenticated
    if not user_id:
        return {
            "action": "authentication_required",
            "success": False,
            "data": {
                "message": "You must be logged in to migrate data."
            },
            "context": {
                "requires_auth": True
            }
        }

    # Must have device_id
    if not device_id:
        return {
            "action": "missing_device_id",
            "success": False,
            "data": {
                "message": "Device identifier is required for data migration."
            },
            "context": {
                "required_field": "device_id"
            }
        }

    # Extract migration type
    migration_type = entities.get("migration_type", "all")  # all, cart, favorites, history

    # Check if already migrated
    if auth_progress and auth_progress.migration_completed:
        return {
            "action": "migration_already_completed",
            "success": True,
            "data": {
                "message": "Your device data has already been migrated to your account.",
                "migrated_data": auth_progress.migrated_data
            },
            "context": {
                "already_migrated": True
            }
        }

    # Get device data summary first
    logger.info(
        "Getting device data summary",
        device_id=device_id,
        user_id=user_id
    )

    summary_result = await get_device_data_summary(device_id)

    if not summary_result["success"]:
        logger.warning(
            "Failed to get device summary",
            error=summary_result["message"]
        )
        # Continue with migration anyway
        summary = {}
    else:
        summary = summary_result["data"]["summary"]

    # Check if there's data to migrate
    total_items = sum([
        summary.get("cart_items", 0),
        summary.get("favorites", 0),
        summary.get("browsing_history", 0)
    ])

    if total_items == 0 and not summary.get("has_preferences"):
        return {
            "action": "no_data_to_migrate",
            "success": True,
            "data": {
                "message": "There's no device data to migrate.",
                "summary": summary
            },
            "context": {
                "migration_needed": False
            }
        }

    # Perform migration
    logger.info(
        "Starting data migration",
        user_id=user_id,
        device_id=device_id,
        migration_type=migration_type,
        total_items=total_items
    )

    migration_result = await migrate_device_data(
        user_id=user_id,
        device_id=device_id,
        migration_type=migration_type
    )

    if not migration_result["success"]:
        logger.error(
            "Migration failed",
            error=migration_result["message"],
            user_id=user_id,
            device_id=device_id
        )

        return {
            "action": "migration_failed",
            "success": False,
            "data": {
                "message": migration_result["message"]
            },
            "context": {}
        }

    # Migration successful
    migration_results = migration_result["data"]["migration_results"]
    total_migrated = migration_result["data"]["total_items"]

    # Link device to user
    await link_device_to_user(user_id, device_id)

    # Update progress
    if auth_progress:
        auth_progress.migration_completed = True
        auth_progress.migrated_data = migration_results

    # Build user-friendly message
    migrated_items = []
    if migration_results.get("cart_items", 0) > 0:
        migrated_items.append(f"{migration_results['cart_items']} cart item(s)")
    if migration_results.get("favorites", 0) > 0:
        migrated_items.append(f"{migration_results['favorites']} favorite(s)")
    if migration_results.get("history", 0) > 0:
        migrated_items.append(f"{migration_results['history']} browsing history item(s)")

    if migrated_items:
        items_msg = ", ".join(migrated_items)
        message = f"Successfully migrated {items_msg} to your account."
    else:
        message = "Data migration completed."

    logger.info(
        "Migration completed successfully",
        user_id=user_id,
        device_id=device_id,
        total_migrated=total_migrated
    )

    return {
        "action": "migration_successful",
        "success": True,
        "data": {
            "message": message,
            "migration_results": migration_results,
            "total_items": total_migrated,
            "device_id": device_id
        },
        "context": {
            "migration_completed": True,
            "migration_type": migration_type
        }
    }


__all__ = ["identity_migrator_agent"]
