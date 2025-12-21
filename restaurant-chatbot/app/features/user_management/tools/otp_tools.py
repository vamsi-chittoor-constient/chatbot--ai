"""
OTP Tools
=========
Tools for OTP generation, sending, and verification.
"""

from typing import Dict, Any, Optional
import structlog

from app.tools.database.otp_tools import CreateOTPTool, ValidateOTPTool
from app.tools.database.user_tools import GetUserTool, CreateUserTool
from app.tools.base.tool_base import ToolStatus
from app.core.database import get_db_session as get_db

logger = structlog.get_logger("user_management.tools.otp")


async def send_otp(
    phone_number: str,
    purpose: str = "login"
) -> Dict[str, Any]:
    """
    Send OTP to phone number.

    Args:
        phone_number: Phone number to send OTP to
        purpose: Purpose of OTP (login, register, verification)

    Returns:
        Dict with success status and message
    """
    try:
        logger.info(
            "Sending OTP",
            phone=phone_number,
            purpose=purpose
        )

        otp_tool = CreateOTPTool()
        result = await otp_tool.execute(
            phone_number=phone_number,
            purpose=purpose
        )

        if result.status != ToolStatus.SUCCESS:
            return {
                "success": False,
                "message": result.error or "Failed to send OTP",
                "data": {}
            }

        return {
            "success": True,
            "message": f"OTP sent to {phone_number}",
            "data": {
                "phone_number": phone_number,
                "purpose": purpose,
                **result.data
            }
        }

    except Exception as e:
        logger.error(
            "Failed to send OTP",
            error=str(e),
            phone=phone_number
        )

        return {
            "success": False,
            "message": f"Failed to send OTP: {str(e)}",
            "data": {}
        }


async def verify_otp(
    phone_number: str,
    otp_code: str,
    purpose: str = "login"
) -> Dict[str, Any]:
    """
    Verify OTP code.

    Args:
        phone_number: Phone number
        otp_code: OTP code to verify
        purpose: Purpose of OTP

    Returns:
        Dict with success status, message, and verification result
    """
    try:
        logger.info(
            "Verifying OTP",
            phone=phone_number,
            purpose=purpose
        )

        # Check for test OTP bypass (for load testing)
        from app.core.config import config
        if config.TEST_OTP_ENABLED and otp_code == config.TEST_OTP_CODE:
            logger.info("Test OTP bypass activated", phone=phone_number)
            return {
                "success": True,
                "message": "OTP verified successfully (test mode)",
                "data": {
                    "verified": True,
                    "phone_number": phone_number,
                    "test_mode": True
                }
            }

        otp_tool = ValidateOTPTool()
        result = await otp_tool.execute(
            phone_number=phone_number,
            otp_code=otp_code,
            purpose=purpose
        )

        if result.status == ToolStatus.SUCCESS:
            return {
                "success": True,
                "message": "OTP verified successfully",
                "data": {
                    "verified": True,
                    "phone_number": phone_number
                }
            }
        else:
            return {
                "success": False,
                "message": result.error or "OTP verification failed",
                "data": {
                    "verified": False
                }
            }

    except Exception as e:
        logger.error(
            "Failed to verify OTP",
            error=str(e),
            phone=phone_number
        )

        return {
            "success": False,
            "message": f"OTP verification failed: {str(e)}",
            "data": {
                "verified": False
            }
        }


async def check_user_exists(
    phone_number: Optional[str] = None,
    email: Optional[str] = None,
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check if user exists by phone, email, or user_id.

    Args:
        phone_number: Phone number to check
        email: Email to check
        user_id: User ID to check

    Returns:
        Dict with exists status and user data if found
    """
    try:
        logger.info(
            "Checking if user exists",
            phone=phone_number,
            email=email,
            user_id=user_id
        )

        user_tool = GetUserTool()

        # Try to get user
        result = await user_tool.execute(
            phone_number=phone_number,
            email=email,
            user_id=user_id
        )

        if result.status != ToolStatus.SUCCESS:
            return {
                "success": True,
                "message": "User does not exist",
                "data": {
                    "exists": False,
                    "user": None
                }
            }
        else:
            return {
                "success": True,
                "message": "User exists",
                "data": {
                    "exists": True,
                    "user": result.data
                }
            }

    except Exception as e:
        logger.error(
            "Failed to check user existence",
            error=str(e)
        )

        return {
            "success": False,
            "message": f"Failed to check user: {str(e)}",
            "data": {
                "exists": False,
                "user": None
            }
        }


async def create_user(
    phone_number: str,
    full_name: str,
    email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new user account.

    Args:
        phone_number: User's phone number
        full_name: User's full name
        email: User's email (optional)

    Returns:
        Dict with success status and user data
    """
    try:
        logger.info(
            "Creating new user",
            phone=phone_number,
            name=full_name
        )

        create_tool = CreateUserTool()
        result = await create_tool.execute(
            phone_number=phone_number,
            full_name=full_name,
            email=email,
            is_anonymous=False
        )

        if result.status != ToolStatus.SUCCESS:
            return {
                "success": False,
                "message": result.error or "Failed to create user",
                "data": {}
            }

        return {
            "success": True,
            "message": "User account created successfully",
            "data": {
                "user": result.data,
                "phone_number": phone_number,
                "full_name": full_name
            }
        }

    except Exception as e:
        logger.error(
            "Failed to create user",
            error=str(e),
            phone=phone_number
        )

        return {
            "success": False,
            "message": f"Failed to create user: {str(e)}",
            "data": {}
        }


__all__ = [
    "send_otp",
    "verify_otp",
    "check_user_exists",
    "create_user"
]
