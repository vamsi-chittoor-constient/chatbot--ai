"""
Identity Management Tools
========================
Tools for updating user identity information (name, email, phone).
"""

from typing import Dict, Any, Optional
import structlog

from app.tools.database.user_tools import UpdateUserTool, GetUserTool
from app.core.database import get_db_session as get_db

logger = structlog.get_logger("user_management.tools.identity")


async def get_user_identity(
    user_id: str
) -> Dict[str, Any]:
    """
    Get user identity information.

    Args:
        user_id: User identifier

    Returns:
        Dict with success status and user identity data
    """
    try:
        logger.info(
            "Getting user identity",
            user_id=user_id
        )

        async with get_db() as db:
            user_tool = GetUserTool()
            result = await user_tool._arun(
                user_id=user_id,
                db=db
            )

            if "not found" in result.lower():
                return {
                    "success": False,
                    "message": "User not found",
                    "data": {}
                }

            return {
                "success": True,
                "message": "User identity retrieved",
                "data": {
                    "user": result
                }
            }

    except Exception as e:
        logger.error(
            "Failed to get user identity",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to retrieve user: {str(e)}",
            "data": {}
        }


async def update_user_name(
    user_id: str,
    full_name: str
) -> Dict[str, Any]:
    """
    Update user's full name.

    Args:
        user_id: User identifier
        full_name: New full name

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info(
            "Updating user name",
            user_id=user_id,
            new_name=full_name
        )

        async with get_db() as db:
            update_tool = UpdateUserTool()
            result = await update_tool._arun(
                user_id=user_id,
                full_name=full_name,
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
                "message": f"Name updated to '{full_name}'",
                "data": {
                    "full_name": full_name,
                    "updated_field": "full_name"
                }
            }

    except Exception as e:
        logger.error(
            "Failed to update user name",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to update name: {str(e)}",
            "data": {}
        }


async def update_user_email(
    user_id: str,
    email: str
) -> Dict[str, Any]:
    """
    Update user's email address.

    Args:
        user_id: User identifier
        email: New email address

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info(
            "Updating user email",
            user_id=user_id,
            new_email=email
        )

        async with get_db() as db:
            update_tool = UpdateUserTool()
            result = await update_tool._arun(
                user_id=user_id,
                email=email,
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
                "message": f"Email updated to '{email}'",
                "data": {
                    "email": email,
                    "updated_field": "email",
                    "email_verified": False  # Requires re-verification
                }
            }

    except Exception as e:
        logger.error(
            "Failed to update user email",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to update email: {str(e)}",
            "data": {}
        }


async def update_user_phone(
    user_id: str,
    phone_number: str
) -> Dict[str, Any]:
    """
    Update user's phone number.

    Note: This requires OTP verification before update.

    Args:
        user_id: User identifier
        phone_number: New phone number

    Returns:
        Dict with success status and updated data
    """
    try:
        logger.info(
            "Updating user phone",
            user_id=user_id,
            new_phone=phone_number
        )

        async with get_db() as db:
            update_tool = UpdateUserTool()
            result = await update_tool._arun(
                user_id=user_id,
                phone_number=phone_number,
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
                "message": f"Phone number updated to '{phone_number}'",
                "data": {
                    "phone_number": phone_number,
                    "updated_field": "phone_number",
                    "phone_verified": False  # Requires re-verification
                }
            }

    except Exception as e:
        logger.error(
            "Failed to update user phone",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to update phone: {str(e)}",
            "data": {}
        }


async def update_user_profile(
    user_id: str,
    full_name: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update multiple user identity fields at once.

    Args:
        user_id: User identifier
        full_name: New full name (optional)
        email: New email (optional)
        phone_number: New phone number (optional)

    Returns:
        Dict with success status and updated fields
    """
    try:
        logger.info(
            "Updating user profile",
            user_id=user_id,
            has_name=bool(full_name),
            has_email=bool(email),
            has_phone=bool(phone_number)
        )

        if not any([full_name, email, phone_number]):
            return {
                "success": False,
                "message": "No fields provided to update",
                "data": {}
            }

        async with get_db() as db:
            update_tool = UpdateUserTool()
            result = await update_tool._arun(
                user_id=user_id,
                full_name=full_name,
                email=email,
                phone_number=phone_number,
                db=db
            )

            if "error" in result.lower() or "failed" in result.lower():
                return {
                    "success": False,
                    "message": result,
                    "data": {}
                }

            updated_fields = []
            if full_name:
                updated_fields.append("name")
            if email:
                updated_fields.append("email")
            if phone_number:
                updated_fields.append("phone")

            return {
                "success": True,
                "message": f"Updated {', '.join(updated_fields)} successfully",
                "data": {
                    "updated_fields": updated_fields,
                    "full_name": full_name,
                    "email": email,
                    "phone_number": phone_number
                }
            }

    except Exception as e:
        logger.error(
            "Failed to update user profile",
            error=str(e),
            user_id=user_id
        )

        return {
            "success": False,
            "message": f"Failed to update profile: {str(e)}",
            "data": {}
        }


__all__ = [
    "get_user_identity",
    "update_user_name",
    "update_user_email",
    "update_user_phone",
    "update_user_profile"
]
