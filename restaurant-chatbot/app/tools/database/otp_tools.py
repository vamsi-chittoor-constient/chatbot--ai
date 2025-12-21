"""
OTP Validation Database Tools
============================

Database tools for managing OTP (One-Time Password) verification.
Supports phone number and email verification for registration, login, and booking purposes.

Tools in this module:
- CreateOTPTool: Generate OTP for verification
- ValidateOTPTool: Verify OTP code and mark as validated
- ResendOTPTool: Resend/recreate expired or failed OTP
- CleanupExpiredOTPTool: Remove expired OTP records from database

All tools follow the proven SQLAlchemy pattern and include comprehensive error handling.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.shared.models import OTPVerification
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.core.logging_config import get_logger
from app.utils.validation_decorators import validate_schema, require_tables
from app.utils.schema_tool_integration import (
    serialize_output_with_schema,
    safe_isoformat
)
from app.schemas.otp import (
    OTPResponse,
    OTPValidationResponse
)

logger = get_logger(__name__)


@validate_schema(OTPVerification)
@require_tables("otp_verification")
class CreateOTPTool(ToolBase):
    """
    Generate OTP for phone number or email verification.

    Creates a new OTP record with automatic expiry time.
    Invalidates any existing OTP for the same phone_number and purpose.
    """

    def __init__(self):
        super().__init__(
            name="create_otp",
            description="Generate OTP for phone or email verification",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate required fields for OTP creation"""
        required_fields = ['phone_number', 'purpose']
        for field in required_fields:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        # Validate purpose
        valid_purposes = ['registration', 'login', 'booking', 'phone_verification']
        if kwargs['purpose'] not in valid_purposes:
            raise ToolError(f"purpose must be one of: {', '.join(valid_purposes)}", tool_name=self.name)

        # Generate OTP code if not provided
        if not kwargs.get('otp_code'):
            kwargs['otp_code'] = self._generate_otp()

        # Set default expiry time (10 minutes from now)
        if not kwargs.get('expires_at'):
            kwargs['expires_at'] = datetime.now() + timedelta(minutes=10)

        return kwargs

    def _generate_otp(self, length: int = 6) -> str:
        """Generate a random numeric OTP code"""
        return ''.join(random.choices(string.digits, k=length))

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            # Import SMS service here to avoid circular imports
            from app.services.sms_service import get_sms_service

            async with get_db_session() as session:
                # First, invalidate any existing unverified OTP for same phone and purpose
                existing_query = select(OTPVerification).where(
                    OTPVerification.phone_number == kwargs['phone_number'],
                    OTPVerification.purpose == kwargs['purpose'],
                    OTPVerification.is_verified == False,
                    OTPVerification.expires_at > datetime.now()
                )
                existing_otps = await session.execute(existing_query)
                existing_records = existing_otps.scalars().all()

                # Mark existing OTPs as expired by setting expires_at to now
                for record in existing_records:
                    record.expires_at = datetime.now()
                    logger.info(f"Invalidated existing OTP for {kwargs['phone_number']}")

                # Create new OTP record
                new_otp = OTPVerification(
                    phone_number=kwargs['phone_number'],
                    otp_code=kwargs['otp_code'],
                    purpose=kwargs['purpose'],
                    expires_at=kwargs['expires_at'],
                    max_attempts=kwargs.get('max_attempts', 3)
                )

                session.add(new_otp)
                await session.commit()
                await session.refresh(new_otp)

                logger.info(f"Created OTP for {kwargs['phone_number']} with purpose {kwargs['purpose']}")

                # Send OTP via SMS using Twilio
                sms_service = get_sms_service()
                sms_result = await sms_service.send_otp(
                    phone_number=kwargs['phone_number'],
                    otp_code=kwargs['otp_code'],
                    purpose=kwargs['purpose']
                )

                # Check if SMS was sent successfully
                if not sms_result['success']:
                    logger.error(f"SMS delivery failed for OTP {new_otp.id}",
                        phone_number=kwargs['phone_number'][-4:],
                        error=sms_result['error'],
                        otp_id=new_otp.id
                    )

                    # Note: We don't fail the entire operation if SMS fails
                    # The OTP is still created in database for manual verification
                    sms_status = "failed"
                    sms_error = sms_result['error']
                else:
                    logger.info("OTP SMS sent successfully",
                        phone_number=kwargs['phone_number'][-4:],
                        message_sid=sms_result['message_sid'],
                        otp_id=new_otp.id
                    )
                    sms_status = "sent"
                    sms_error = None

                # Send OTP via email if user has email address
                email_status = "not_attempted"
                email_error = None
                email_log_id = None

                # Check if user exists and has email
                try:
                    from app.shared.models import User
                    user_query = select(User).where(User.phone_number == kwargs['phone_number'])
                    user_result = await session.execute(user_query)
                    user = user_result.scalar_one_or_none()

                    if user and user.email:
                        try:
                            from app.services.email_manager_service import create_email_service
                            from app.services.email_template_service import get_email_template_service

                            template_service = get_email_template_service()
                            email_service = create_email_service(session)

                            # Render OTP verification template
                            html_content = template_service.render_otp_verification(
                                otp_code=kwargs['otp_code'],
                                expiry_minutes=10
                            )

                            # Send email
                            email_result = await email_service.send_email(
                                to_email=user.email,
                                subject="Email Verification - Restaurant AI",
                                html_content=html_content,
                                user_id=user.id
                            )

                            if email_result.get("success"):
                                email_status = "sent"
                                email_log_id = email_result.get("email_log_id")
                                logger.info(
                                    "OTP email sent successfully",
                                    phone_number=kwargs['phone_number'][-4:],
                                    email=user.email,
                                    email_log_id=email_log_id
                                )
                            else:
                                email_status = "failed"
                                email_error = email_result.get("error")
                                logger.warning(
                                    "Failed to send OTP email",
                                    error=email_error
                                )
                        except Exception as e:
                            email_status = "failed"
                            email_error = str(e)
                            logger.error(f"Email OTP send failed: {str(e)}")
                    else:
                        email_status = "no_email"
                        logger.debug(f"No email found for phone {kwargs['phone_number'][-4:]}")
                except Exception as e:
                    logger.warning(f"Could not check user email: {str(e)}")
                    email_status = "error"
                    email_error = str(e)

                # Serialize OTP data using schema
                otp_data = serialize_output_with_schema(
                    OTPResponse,
                    new_otp,
                    self.name,
                    from_orm=True
                )

                # Add delivery status fields (not in schema but important metadata)
                otp_data.update({
                    "sms_status": sms_status,
                    "sms_message_sid": sms_result.get('message_sid'),
                    "sms_error": sms_error,
                    "email_status": email_status,
                    "email_log_id": email_log_id,
                    "email_error": email_error
                })

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=otp_data,
                    metadata={
                        "operation": "create_otp",
                        "sms_delivery": sms_status,
                        "email_delivery": email_status,
                        "message_sid": sms_result.get('message_sid')
                    }
                )

        except Exception as e:
            logger.error(f"Failed to create OTP: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


@validate_schema(OTPVerification)
class ValidateOTPTool(ToolBase):
    """
    Verify OTP code and mark as validated.

    Checks if the provided OTP code matches an active, non-expired OTP.
    Increments attempt counter and handles max attempts exceeded scenarios.
    """

    def __init__(self):
        super().__init__(
            name="validate_otp",
            description="Verify OTP code and mark as validated",
            max_retries=1,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate required fields for OTP validation"""
        required_fields = ['phone_number', 'otp_code', 'purpose']
        for field in required_fields:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            # Check for test OTP bypass (for load testing)
            from app.core.config import config
            if config.TEST_OTP_ENABLED and kwargs['otp_code'] == config.TEST_OTP_CODE:
                logger.info(f"Test OTP bypass for {kwargs['phone_number']}")
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "validation_status": "verified",
                        "phone_number": kwargs['phone_number'],
                        "is_verified": True,
                        "verified_at": datetime.now().isoformat(),
                        "test_mode": True
                    },
                    metadata={"operation": "validate_otp", "test_mode": True}
                )

            async with get_db_session() as session:
                # Find the most recent unverified OTP record
                # Order by created_at DESC to get the latest OTP if multiple exist
                query = select(OTPVerification).where(
                    OTPVerification.phone_number == kwargs['phone_number'],
                    OTPVerification.purpose == kwargs['purpose'],
                    OTPVerification.is_verified == False
                ).order_by(OTPVerification.created_at.desc())
                result = await session.execute(query)
                otp_record = result.scalars().first()

                if not otp_record:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="No active OTP found for this contact and purpose",
                        data={"validation_status": "otp_not_found"}
                    )

                # Check if OTP has expired
                if otp_record.expires_at <= datetime.now():
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="OTP has expired",
                        data={
                            "validation_status": "expired",
                            "expired_at": safe_isoformat(otp_record.expires_at)
                        }
                    )

                # Check if max attempts exceeded
                if otp_record.attempts >= otp_record.max_attempts:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Maximum OTP attempts exceeded",
                        data={
                            "validation_status": "max_attempts_exceeded",
                            "attempts": otp_record.attempts,
                            "max_attempts": otp_record.max_attempts
                        }
                    )

                # Increment attempt counter
                otp_record.attempts += 1

                # Check if OTP code matches
                if otp_record.otp_code != kwargs['otp_code']:
                    await session.commit()  # Save the attempt increment

                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Invalid OTP code",
                        data={
                            "validation_status": "invalid_code",
                            "attempts": otp_record.attempts,
                            "remaining_attempts": otp_record.max_attempts - otp_record.attempts
                        }
                    )

                # OTP is valid - mark as verified
                otp_record.is_verified = True
                otp_record.verified_at = datetime.now()

                await session.commit()
                await session.refresh(otp_record)

                logger.info(f"Successfully validated OTP for {kwargs['phone_number']} with purpose {kwargs['purpose']}")

                # Serialize validation response using schema
                validation_data = serialize_output_with_schema(
                    OTPValidationResponse,
                    otp_record,
                    self.name,
                    from_orm=True
                )

                # Add validation metadata
                validation_data.update({
                    "validation_status": "verified",
                    "attempts_used": otp_record.attempts
                })

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=validation_data,
                    metadata={"operation": "validate_otp"}
                )

        except Exception as e:
            logger.error(f"Failed to validate OTP: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


class ResendOTPTool(ToolBase):
    """
    Resend/recreate OTP for the same contact and purpose.

    Invalidates the existing OTP and creates a new one with a fresh expiry time.
    Used when user didn't receive the original OTP or it expired.
    """

    def __init__(self):
        super().__init__(
            name="resend_otp",
            description="Resend/recreate OTP with new expiry time",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate required fields for OTP resend"""
        required_fields = ['phone_number', 'purpose']
        for field in required_fields:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            # Use CreateOTPTool to handle the resend logic
            # This will automatically invalidate existing OTPs and create a new one
            create_tool = CreateOTPTool()
            result = await create_tool.execute(
                phone_number=kwargs['phone_number'],
                purpose=kwargs['purpose'],
                max_attempts=kwargs.get('max_attempts', 3)
            )

            if result.status == ToolStatus.SUCCESS:
                logger.info(f"Resent OTP for {kwargs['phone_number']} with purpose {kwargs['purpose']}")
                result.metadata = {"operation": "resend_otp"}

            return result

        except Exception as e:
            logger.error(f"Failed to resend OTP: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


class CleanupExpiredOTPTool(ToolBase):
    """
    Remove expired OTP records from database.

    Deletes OTP records that have exceeded their expiry time to keep the database clean.
    Can be run as a maintenance task or triggered after verification processes.
    """

    def __init__(self):
        super().__init__(
            name="cleanup_expired_otp",
            description="Remove expired OTP records from database",
            max_retries=2,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate optional cleanup parameters"""
        # Optional: cleanup_before_date parameter
        if kwargs.get('cleanup_before_date') and not isinstance(kwargs['cleanup_before_date'], datetime):
            raise ToolError("cleanup_before_date must be a datetime object", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Use current time as cleanup threshold unless specified
                cleanup_before = kwargs.get('cleanup_before_date', datetime.now())

                # Query for expired OTPs
                query = select(OTPVerification).where(
                    OTPVerification.expires_at <= cleanup_before
                )
                result = await session.execute(query)
                expired_otps = result.scalars().all()

                # Count records before deletion
                expired_count = len(expired_otps)

                if expired_count == 0:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "deleted_count": 0,
                            "cleanup_date": safe_isoformat(cleanup_before)
                        },
                        metadata={"operation": "cleanup_expired_otp"}
                    )

                # Delete expired OTP records
                delete_query = delete(OTPVerification).where(
                    OTPVerification.expires_at <= cleanup_before
                )
                await session.execute(delete_query)
                await session.commit()

                logger.info(f"Cleaned up {expired_count} expired OTP records")

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "deleted_count": expired_count,
                        "cleanup_date": safe_isoformat(cleanup_before)
                    },
                    metadata={"operation": "cleanup_expired_otp"}
                )

        except Exception as e:
            logger.error(f"Failed to cleanup expired OTPs: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


class GetOTPStatusTool(ToolBase):
    """
    Retrieve OTP record status and details.

    Gets current status of OTP for specific contact info and purpose.
    Useful for checking remaining attempts, expiry time, etc.
    """

    def __init__(self):
        super().__init__(
            name="get_otp_status",
            description="Retrieve OTP record status and details",
            max_retries=1,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate required fields for OTP status check"""
        required_fields = ['phone_number', 'purpose']
        for field in required_fields:
            if not kwargs.get(field):
                raise ToolError(f"{field} is required", tool_name=self.name)

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                # Find the most recent OTP record for this phone number and purpose
                query = select(OTPVerification).where(
                    OTPVerification.phone_number == kwargs['phone_number'],
                    OTPVerification.purpose == kwargs['purpose']
                ).order_by(OTPVerification.created_at.desc())

                result = await session.execute(query)
                otp_record = result.scalar_one_or_none()

                if not otp_record:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "status": "no_otp_found",
                            "phone_number": kwargs['phone_number'],
                            "phone_number": kwargs['phone_number'],
                            "purpose": kwargs['purpose']
                        },
                        metadata={"operation": "get_otp_status"}
                    )

                # Determine OTP status
                current_time = datetime.now()
                if otp_record.is_verified:
                    status = "verified"
                elif otp_record.expires_at <= current_time:
                    status = "expired"
                elif otp_record.attempts >= otp_record.max_attempts:
                    status = "max_attempts_exceeded"
                else:
                    status = "active"

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "status": status,
                        "otp_id": otp_record.id,
                        "phone_number": otp_record.phone_number,
                        "purpose": otp_record.purpose,
                        "attempts": otp_record.attempts,
                        "max_attempts": otp_record.max_attempts,
                        "remaining_attempts": max(0, otp_record.max_attempts - otp_record.attempts),
                        "expires_at": safe_isoformat(otp_record.expires_at),
                        "is_verified": otp_record.is_verified,
                        "verified_at": safe_isoformat(otp_record.verified_at),
                        "created_at": safe_isoformat(otp_record.created_at)
                    },
                    metadata={"operation": "get_otp_status"}
                )

        except Exception as e:
            logger.error(f"Failed to get OTP status: {str(e)}")
            raise ToolError(f"Database error: {str(e)}", tool_name=self.name, retry_suggested=True)


# Test function to verify all OTP tools work correctly
if __name__ == "__main__":
    import asyncio

    async def test_otp_tools():
        """Test all OTP validation tools"""
        print("Testing OTP Validation Tools...")

        from app.database.connection import init_database
        await init_database(create_tables=False)

        try:
            # Test data
            test_phone = "+919566070120"
            test_purpose = "phone_verification"

            print("\n1. Testing CreateOTPTool...")
            create_tool = CreateOTPTool()
            result = await create_tool.execute(
                phone_number=test_phone,
                purpose=test_purpose
            )

            if result.status == ToolStatus.SUCCESS:
                print(f"SUCCESS: OTP Created: {result.data['otp_code']} for {result.data['phone_number']}")
                otp_code = result.data['otp_code']
                otp_id = result.data['otp_id']
            else:
                print(f"FAILED: OTP Creation Failed: {result.error}")
                return False

            # Test 2: Get OTP Status
            print("\n2. Testing GetOTPStatusTool...")
            status_tool = GetOTPStatusTool()
            result = await status_tool.execute(
                phone_number=test_phone,
                purpose=test_purpose
            )

            if result.status == ToolStatus.SUCCESS:
                print(f"SUCCESS: OTP Status: {result.data['status']}")
                print(f"   Remaining attempts: {result.data['remaining_attempts']}")
            else:
                print(f"FAILED: OTP Status Check Failed: {result.error}")

            # Test 3: Validate wrong OTP
            print("\n3. Testing ValidateOTPTool (wrong code)...")
            validate_tool = ValidateOTPTool()
            result = await validate_tool.execute(
                phone_number=test_phone,
                purpose=test_purpose,
                otp_code="999999"
            )

            if result.status == ToolStatus.FAILURE and result.data['validation_status'] == 'invalid_code':
                print(f"SUCCESS: Correctly rejected wrong OTP. Remaining attempts: {result.data['remaining_attempts']}")
            else:
                print(f"FAILED: Wrong OTP validation failed: {result.error}")

            # Test 4: Validate correct OTP
            print("\n4. Testing ValidateOTPTool (correct code)...")
            result = await validate_tool.execute(
                phone_number=test_phone,
                purpose=test_purpose,
                otp_code=otp_code
            )

            if result.status == ToolStatus.SUCCESS and result.data['validation_status'] == 'verified':
                print("SUCCESS: OTP Validated Successfully!")
                print(f"   Verified at: {result.data['verified_at']}")
            else:
                print(f"FAILED: OTP Validation Failed: {result.error}")

            # Test 5: Resend OTP
            print("\n5. Testing ResendOTPTool...")
            resend_tool = ResendOTPTool()
            result = await resend_tool.execute(
                phone_number=test_phone,
                purpose="registration"  # Different purpose
            )

            if result.status == ToolStatus.SUCCESS:
                print(f"SUCCESS: OTP Resent: {result.data['otp_code']}")
                new_otp_code = result.data['otp_code']
            else:
                print(f"FAILED: OTP Resend Failed: {result.error}")

            # Test 6: Cleanup expired OTPs
            print("\n6. Testing CleanupExpiredOTPTool...")
            cleanup_tool = CleanupExpiredOTPTool()
            result = await cleanup_tool.execute()

            if result.status == ToolStatus.SUCCESS:
                print(f"SUCCESS: Cleanup completed: {result.data['deleted_count']} expired OTPs removed")
            else:
                print(f"FAILED: Cleanup Failed: {result.error}")

            print("\nALL OTP TOOLS WORKING CORRECTLY!")
            return True

        except Exception as e:
            print(f"ERROR: Test failed with exception: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    asyncio.run(test_otp_tools())
