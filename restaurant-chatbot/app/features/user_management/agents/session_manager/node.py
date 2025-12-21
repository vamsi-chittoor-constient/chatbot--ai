"""
Session Manager Sub-Agent
=========================
Handles session and device management.

Responsibilities:
- View active sessions across all devices
- Revoke specific sessions (logout)
- Revoke all sessions (logout from all devices)
- Rename devices for easier identification
- View all user devices
"""

from typing import Dict, Any
import structlog

from app.features.user_management.state import AuthenticationState
from app.features.user_management.tools import (
    get_active_sessions,
    revoke_session,
    get_user_devices,
    update_device_name
)

logger = structlog.get_logger("user_management.agents.session_manager")


async def session_manager_agent(
    entities: Dict[str, Any],
    state: AuthenticationState
) -> Dict[str, Any]:
    """
    Session Manager sub-agent: Manage user sessions and devices.

    Args:
        entities: Extracted entities (action, session_id, device_id, device_name)
        state: Current authentication state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    user_id = state.get("user_id")
    auth_progress = state.get("auth_progress")

    logger.info(
        "Session manager agent executing",
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
                "message": "You must be logged in to manage sessions."
            },
            "context": {
                "requires_auth": True
            }
        }

    # Extract entities
    action = entities.get("action", "view")  # view, revoke, rename
    target_session_id = entities.get("session_id")
    target_device_id = entities.get("device_id")
    device_name = entities.get("device_name")
    revoke_all = entities.get("revoke_all", False)

    # Action: View sessions
    if action == "view" or action == "list":
        logger.info("Viewing active sessions", user_id=user_id)

        sessions_result = await get_active_sessions(user_id)

        if not sessions_result["success"]:
            return {
                "action": "sessions_fetch_failed",
                "success": False,
                "data": {
                    "message": sessions_result["message"]
                },
                "context": {}
            }

        sessions = sessions_result["data"]["sessions"]
        count = sessions_result["data"]["count"]

        if count == 0:
            message = "You have no active sessions."
        elif count == 1:
            message = "You have 1 active session."
        else:
            message = f"You have {count} active sessions."

        # Format sessions for display
        formatted_sessions = []
        for sess in sessions:
            formatted_sessions.append({
                "session_id": sess.get("session_id"),
                "device_id": sess.get("device_id"),
                "device_name": sess.get("device_name", "Unknown Device"),
                "created_at": sess.get("created_at"),
                "last_used": sess.get("last_used_at"),
                "is_current": sess.get("device_id") == state.get("device_id")
            })

        return {
            "action": "sessions_listed",
            "success": True,
            "data": {
                "message": message,
                "sessions": formatted_sessions,
                "count": count
            },
            "context": {
                "action_completed": "view"
            }
        }

    # Action: View devices
    elif action == "devices":
        logger.info("Viewing user devices", user_id=user_id)

        devices_result = await get_user_devices(user_id)

        if not devices_result["success"]:
            return {
                "action": "devices_fetch_failed",
                "success": False,
                "data": {
                    "message": devices_result["message"]
                },
                "context": {}
            }

        devices = devices_result["data"]["devices"]
        count = devices_result["data"]["count"]

        return {
            "action": "devices_listed",
            "success": True,
            "data": {
                "message": f"You have {count} registered device(s).",
                "devices": devices,
                "count": count
            },
            "context": {
                "action_completed": "devices"
            }
        }

    # Action: Revoke session (logout)
    elif action == "revoke" or action == "logout":
        logger.info(
            "Revoking session",
            user_id=user_id,
            revoke_all=revoke_all,
            has_session_id=bool(target_session_id),
            has_device_id=bool(target_device_id)
        )

        revoke_result = await revoke_session(
            user_id=user_id,
            session_token=target_session_id,
            device_id=target_device_id,
            revoke_all=revoke_all
        )

        if not revoke_result["success"]:
            return {
                "action": "revoke_failed",
                "success": False,
                "data": {
                    "message": revoke_result["message"]
                },
                "context": {}
            }

        if revoke_all:
            message = "You have been logged out from all devices."
        elif target_device_id:
            message = f"Logged out from device {target_device_id}."
        else:
            message = "Session revoked successfully."

        return {
            "action": "session_revoked",
            "success": True,
            "data": {
                "message": message,
                "revoked": True
            },
            "context": {
                "action_completed": "revoke",
                "revoke_all": revoke_all
            }
        }

    # Action: Rename device
    elif action == "rename":
        logger.info(
            "Renaming device",
            user_id=user_id,
            device_id=target_device_id,
            new_name=device_name
        )

        if not target_device_id:
            return {
                "action": "missing_device_id",
                "success": False,
                "data": {
                    "message": "Please specify which device to rename."
                },
                "context": {
                    "required_field": "device_id"
                }
            }

        if not device_name:
            return {
                "action": "missing_device_name",
                "success": False,
                "data": {
                    "message": "Please provide a new name for the device."
                },
                "context": {
                    "required_field": "device_name"
                }
            }

        rename_result = await update_device_name(
            target_device_id,
            device_name,
            user_id
        )

        if not rename_result["success"]:
            return {
                "action": "rename_failed",
                "success": False,
                "data": {
                    "message": rename_result["message"]
                },
                "context": {}
            }

        return {
            "action": "device_renamed",
            "success": True,
            "data": {
                "message": rename_result["message"],
                "device_id": target_device_id,
                "device_name": device_name
            },
            "context": {
                "action_completed": "rename"
            }
        }

    # Unknown action
    else:
        return {
            "action": "unknown_action",
            "success": False,
            "data": {
                "message": f"Unknown session management action: {action}"
            },
            "context": {}
        }


__all__ = ["session_manager_agent"]
