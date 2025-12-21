"""
Authenticator Sub-Agent
=======================
Handles complete authentication flow: phone → OTP → verify → login/register

Responsibilities:
- Collect and validate phone number
- Send OTP verification code
- Verify OTP code
- Check if user exists (login) or create new user (register)
- Create authentication session
"""

from typing import Dict, Any
import structlog

from app.features.user_management.state import AuthenticationState
from app.features.user_management.tools import (
    send_otp,
    verify_otp,
    check_user_exists,
    create_user,
    create_session
)

logger = structlog.get_logger("user_management.agents.authenticator")


async def authenticator_agent(
    entities: Dict[str, Any],
    state: AuthenticationState
) -> Dict[str, Any]:
    """
    Authenticator sub-agent: Complete authentication flow.

    Flow:
    1. Collect phone number
    2. Send OTP
    3. Verify OTP
    4. Check if user exists → login or register
    5. Create session

    Args:
        entities: Extracted entities (phone, otp_code, full_name, email)
        state: Current authentication state

    Returns:
        Response dict with action, success, and data
    """
    session_id = state.get("session_id", "unknown")
    auth_progress = state.get("auth_progress")

    logger.info(
        "Authenticator agent executing",
        session_id=session_id,
        entities=entities
    )

    # Extract entities
    phone = entities.get("phone") or auth_progress.phone
    otp_code = entities.get("otp_code") or auth_progress.otp_code
    full_name = entities.get("full_name") or auth_progress.full_name
    email = entities.get("email")
    device_id = state.get("device_id") or auth_progress.device_id

    # Step 1: Collect phone number
    if not phone:
        logger.info("Phone number missing", session_id=session_id)
        return {
            "action": "collect_phone",
            "success": False,
            "data": {
                "message": "Please provide your phone number to continue."
            },
            "context": {
                "next_step": "collect_phone",
                "required_field": "phone"
            }
        }

    # Update progress
    auth_progress.phone = phone
    auth_progress.phone_collected = True
    auth_progress.auth_step = "send_otp"

    # Step 2: Send OTP if not already sent
    if not auth_progress.otp_sent or not otp_code:
        logger.info("Sending OTP", session_id=session_id, phone=phone)

        # Check if locked
        if auth_progress.is_locked():
            return {
                "action": "authentication_locked",
                "success": False,
                "data": {
                    "message": f"Too many attempts. Please try again later.",
                    "locked_until": str(auth_progress.locked_until)
                },
                "context": {
                    "locked": True
                }
            }

        # Check OTP send limit
        if not auth_progress.can_retry_otp():
            return {
                "action": "otp_limit_exceeded",
                "success": False,
                "data": {
                    "message": "OTP send limit exceeded. Please try again later."
                },
                "context": {
                    "otp_send_count": auth_progress.otp_send_count
                }
            }

        # Send OTP
        otp_result = await send_otp(phone, purpose="login")

        if not otp_result["success"]:
            logger.error(
                "OTP send failed",
                session_id=session_id,
                error=otp_result["message"]
            )
            return {
                "action": "otp_send_failed",
                "success": False,
                "data": {
                    "message": otp_result["message"]
                },
                "context": {}
            }

        # Update progress
        auth_progress.increment_otp_send()

        return {
            "action": "otp_sent",
            "success": True,
            "data": {
                "message": f"Verification code sent to {phone}. Please enter the code.",
                "phone": phone
            },
            "context": {
                "next_step": "verify_otp",
                "otp_sent": True
            }
        }

    # Step 3: Verify OTP
    if not auth_progress.otp_verified:
        logger.info("Verifying OTP", session_id=session_id)

        if not otp_code:
            return {
                "action": "collect_otp",
                "success": False,
                "data": {
                    "message": "Please enter the verification code sent to your phone."
                },
                "context": {
                    "next_step": "verify_otp",
                    "required_field": "otp_code"
                }
            }

        auth_progress.otp_code = otp_code
        auth_progress.auth_step = "verify_otp"

        # Verify OTP
        verify_result = await verify_otp(phone, otp_code, purpose="login")
        auth_progress.increment_otp_verification()

        if not verify_result["success"]:
            logger.warning(
                "OTP verification failed",
                session_id=session_id,
                attempts=auth_progress.otp_verification_attempts
            )

            return {
                "action": "otp_verification_failed",
                "success": False,
                "data": {
                    "message": verify_result["message"],
                    "attempts_remaining": 3 - auth_progress.otp_verification_attempts
                },
                "context": {
                    "verification_failed": True
                }
            }

        # OTP verified
        auth_progress.otp_verified = True
        auth_progress.auth_step = "check_user"

    # Step 4: Check if user exists
    user_check_result = await check_user_exists(phone_number=phone)

    if user_check_result["data"]["exists"]:
        # Existing user - Login flow
        user_data = user_check_result["data"]["user"]
        user_id = user_data.get("id") or user_data.get("user_id")

        logger.info(
            "User exists, logging in",
            session_id=session_id,
            user_id=user_id
        )

        # Create session
        if device_id:
            session_result = await create_session(user_id, device_id)

            if session_result["success"]:
                auth_progress.mark_authenticated(
                    user_id,
                    session_result["data"].get("session_token")
                )

                return {
                    "action": "login_successful",
                    "success": True,
                    "data": {
                        "message": f"Welcome back! You're now logged in.",
                        "user_id": user_id,
                        "session_token": session_result["data"].get("session_token")
                    },
                    "context": {
                        "authenticated": True,
                        "is_new_user": False
                    }
                }

        # Session creation failed or no device_id
        auth_progress.mark_authenticated(user_id, None)

        return {
            "action": "login_successful",
            "success": True,
            "data": {
                "message": f"Welcome back! You're now logged in.",
                "user_id": user_id
            },
            "context": {
                "authenticated": True,
                "is_new_user": False,
                "session_created": False
            }
        }

    else:
        # New user - Register flow
        logger.info(
            "New user, starting registration",
            session_id=session_id,
            phone=phone
        )

        # Check if name is provided
        if not full_name:
            auth_progress.auth_step = "collect_name"
            return {
                "action": "collect_name",
                "success": False,
                "data": {
                    "message": "Welcome! Please provide your full name to complete registration."
                },
                "context": {
                    "next_step": "collect_name",
                    "required_field": "full_name",
                    "is_new_user": True
                }
            }

        # Create user
        auth_progress.full_name = full_name
        auth_progress.email = email
        auth_progress.auth_step = "create_user"

        create_result = await create_user(phone, full_name, email)

        if not create_result["success"]:
            logger.error(
                "User creation failed",
                session_id=session_id,
                error=create_result["message"]
            )

            return {
                "action": "registration_failed",
                "success": False,
                "data": {
                    "message": create_result["message"]
                },
                "context": {}
            }

        user_id = create_result["data"]["user"].get("id")
        auth_progress.is_new_user = True

        # Create session
        if device_id:
            session_result = await create_session(user_id, device_id)

            if session_result["success"]:
                auth_progress.mark_authenticated(
                    user_id,
                    session_result["data"].get("session_token")
                )

                return {
                    "action": "registration_successful",
                    "success": True,
                    "data": {
                        "message": f"Welcome, {full_name}! Your account has been created.",
                        "user_id": user_id,
                        "session_token": session_result["data"].get("session_token")
                    },
                    "context": {
                        "authenticated": True,
                        "is_new_user": True
                    }
                }

        # Session creation failed or no device_id
        auth_progress.mark_authenticated(user_id, None)

        return {
            "action": "registration_successful",
            "success": True,
            "data": {
                "message": f"Welcome, {full_name}! Your account has been created.",
                "user_id": user_id
            },
            "context": {
                "authenticated": True,
                "is_new_user": True,
                "session_created": False
            }
        }


__all__ = ["authenticator_agent"]
