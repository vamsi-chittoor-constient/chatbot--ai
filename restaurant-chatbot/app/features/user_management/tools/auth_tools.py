"""
Authentication Tools
====================
Tools for user authentication workflows.
"""

from typing import Dict, Any, Optional
import structlog

from app.tools.database.user_tools import GetUserTool
from app.tools.database.otp_tools import ValidateOTPTool
from app.tools.base.tool_base import ToolStatus

logger = structlog.get_logger("user_management.tools.auth")


async def get_user(
    user_id: Optional[str] = None,
    phone_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get user account details (authentication info only).

    Retrieve basic user profile information by user ID or phone number.

    Args:
        user_id: User's ID (optional if phone_number provided)
        phone_number: User's phone number (optional if user_id provided)

    Returns:
        Dict with user profile details
    """
    user_tool = GetUserTool()

    result = await user_tool.execute(
        user_id=user_id,
        phone_number=phone_number
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "User not found"
        }

    return {
        "success": True,
        "user": result.data,
        "message": "User profile retrieved"
    }


async def authenticate_user(
    phone_number: str,
    otp_code: str,
    device_id: Optional[str] = None,
    purpose: str = "phone_verification"
) -> Dict[str, Any]:
    """
    Authenticate user with phone and OTP.

    Complete authentication flow: verify OTP, link device, and return session token.

    Args:
        phone_number: User's phone number
        otp_code: OTP code to verify
        device_id: Device identifier (optional, for device linking)
        purpose: Purpose of verification

    Returns:
        Dict with authentication result, user details, and session token
    """
    # Normalize phone number to match format used when OTP was created
    from app.utils.phone_utils import normalize_phone_number
    normalized_phone = normalize_phone_number(phone_number)

    # First verify OTP
    validate_tool = ValidateOTPTool()
    otp_result = await validate_tool.execute(
        phone_number=normalized_phone,
        otp_code=otp_code,
        purpose=purpose
    )

    if otp_result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "authenticated": False,
            "message": otp_result.error or "Invalid or expired OTP"
        }

    # Then get user details (if user exists)
    user_tool = GetUserTool()
    user_result = await user_tool.execute(phone_number=normalized_phone)

    user_data = None
    user_id = None

    if user_result.status == ToolStatus.SUCCESS:
        # User exists in system
        user_data = user_result.data
        user_id = user_data.get("user_id")
    # else: User doesn't exist yet (new customer) - this is OK!
    # Agent will create user account after authentication succeeds

    # Link device and generate session token if device_id AND user_id provided
    session_token = None

    logger.info(
        "authenticate_user_device_check",
        has_device_id=bool(device_id),
        has_user_id=bool(user_id),
        device_id_preview=device_id[:30] + "..." if device_id else "None"
    )

    if device_id and user_id:
        from app.services.identity_service import identity_service

        try:
            session_token = await identity_service.link_device_to_user(
                device_id=device_id,
                user_id=user_id
            )
            logger.info(
                "session_token_generated",
                user_id=user_id,
                has_token=bool(session_token)
            )
        except Exception as e:
            # Log error but don't fail authentication
            logger.warning(
                "Failed to link device during authentication",
                device_id=device_id,
                user_id=user_id,
                error=str(e)
            )
    else:
        logger.warning(
            "session_token_not_generated",
            reason="missing_device_id_or_user_id",
            has_device_id=bool(device_id),
            has_user_id=bool(user_id)
        )

    return {
        "success": True,
        "authenticated": True,
        "user": user_data,  # Will be None for new customers, dict for existing users
        "session_token": session_token,  # Will be None if user doesn't exist yet (created after user account creation)
        "message": f"Welcome back, {user_data.get('full_name', 'user')}!" if user_data else "Phone verified!",
        "debug_info": {
            "device_id_provided": bool(device_id),
            "user_id_found": bool(user_id),
            "token_generated": bool(session_token)
        }
    }


__all__ = ["get_user", "authenticate_user"]
