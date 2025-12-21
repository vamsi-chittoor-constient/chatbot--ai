"""
Session Management Tools
=======================
Tools for managing user sessions and devices.
"""

from typing import Dict, Any, Optional, List
import structlog

from app.services.auth_session_service import AuthSessionService
from app.core.database import get_db_session as get_db

logger = structlog.get_logger("user_management.tools.session")


async def get_active_sessions(
    user_id: str
) -> Dict[str, Any]:
    """
    Get all active sessions for a user.

    Args:
        user_id: User identifier

    Returns:
        Dict with success status and list of active sessions
    """
    try:
        logger.info(
            "Getting active sessions",
            user_id=user_id
        )

        async with get_db() as db:
            service = AuthSessionService(db)
            sessions = await service.get_user_sessions(user_id)

            return {
                "success": True,
                "message": f"Found {len(sessions)} active session(s)",
                "data": {
                    "sessions": sessions,
                    "count": len(sessions)
                }
            }

    except Exception as e:
        logger.error(
            "Failed to get active sessions",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to retrieve sessions: {str(e)}",
            "data": {
                "sessions": [],
                "count": 0
            }
        }


async def revoke_session(
    user_id: str,
    session_token: Optional[str] = None,
    device_id: Optional[str] = None,
    revoke_all: bool = False
) -> Dict[str, Any]:
    """
    Revoke user session(s).

    Args:
        user_id: User identifier
        session_token: Specific session token to revoke
        device_id: Device ID to revoke sessions for
        revoke_all: If True, revoke all user sessions

    Returns:
        Dict with success status and revocation details
    """
    try:
        logger.info(
            "Revoking session",
            user_id=user_id,
            revoke_all=revoke_all,
            has_token=bool(session_token),
            has_device=bool(device_id)
        )

        async with get_db() as db:
            service = AuthSessionService(db)

            if revoke_all:
                # Revoke all user sessions
                result = await service.revoke_all_sessions(user_id)
                message = "All sessions revoked successfully"
            elif session_token:
                # Revoke specific session
                result = await service.revoke_session(session_token)
                message = "Session revoked successfully"
            elif device_id:
                # Revoke sessions for specific device
                result = await service.revoke_device_sessions(user_id, device_id)
                message = f"Sessions for device {device_id} revoked"
            else:
                return {
                    "success": False,
                    "message": "Must provide session_token, device_id, or set revoke_all=True",
                    "data": {}
                }

            return {
                "success": True,
                "message": message,
                "data": {
                    "revoked": True,
                    "result": result
                }
            }

    except Exception as e:
        logger.error(
            "Failed to revoke session",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to revoke session: {str(e)}",
            "data": {
                "revoked": False
            }
        }


async def create_session(
    user_id: str,
    device_id: str
) -> Dict[str, Any]:
    """
    Create a new authentication session.

    Args:
        user_id: User identifier
        device_id: Device identifier

    Returns:
        Dict with success status and session token
    """
    try:
        logger.info(
            "Creating session",
            user_id=user_id,
            device_id=device_id
        )

        async with get_db() as db:
            service = AuthSessionService(db)
            session_token = await service.create_session(user_id, device_id)

            return {
                "success": True,
                "message": "Session created successfully",
                "data": {
                    "session_token": session_token,
                    "user_id": user_id,
                    "device_id": device_id
                }
            }

    except Exception as e:
        logger.error(
            "Failed to create session",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to create session: {str(e)}",
            "data": {}
        }


async def get_user_devices(
    user_id: str
) -> Dict[str, Any]:
    """
    Get all devices associated with a user.

    Args:
        user_id: User identifier

    Returns:
        Dict with success status and list of devices
    """
    try:
        logger.info(
            "Getting user devices",
            user_id=user_id
        )

        async with get_db() as db:
            service = AuthSessionService(db)
            devices = await service.get_user_devices(user_id)

            return {
                "success": True,
                "message": f"Found {len(devices)} device(s)",
                "data": {
                    "devices": devices,
                    "count": len(devices)
                }
            }

    except Exception as e:
        logger.error(
            "Failed to get user devices",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to retrieve devices: {str(e)}",
            "data": {
                "devices": [],
                "count": 0
            }
        }


async def update_device_name(
    device_id: str,
    device_name: str,
    user_id: str
) -> Dict[str, Any]:
    """
    Update device name for easier identification.

    Args:
        device_id: Device identifier
        device_name: New name for device
        user_id: User identifier (for verification)

    Returns:
        Dict with success status
    """
    try:
        logger.info(
            "Updating device name",
            device_id=device_id,
            device_name=device_name,
            user_id=user_id
        )

        async with get_db() as db:
            service = AuthSessionService(db)
            result = await service.update_device_name(device_id, device_name, user_id)

            return {
                "success": True,
                "message": f"Device renamed to '{device_name}'",
                "data": {
                    "device_id": device_id,
                    "device_name": device_name
                }
            }

    except Exception as e:
        logger.error(
            "Failed to update device name",
            error=str(e),
            device_id=device_id
        )

        return {
            "success": False,
            "message": f"Failed to update device name: {str(e)}",
            "data": {}
        }


__all__ = [
    "get_active_sessions",
    "revoke_session",
    "create_session",
    "get_user_devices",
    "update_device_name"
]
