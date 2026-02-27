"""
OTP management Pydantic models for the Restaurant AI Assistant API.

Provides type-safe request/response models for OTP creation, validation,
phone number verification, and SMS-based authentication workflows.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict

from .common import (
    BaseResponse, PhoneNumberField
)


# OTP Request Models
class OTPCreateRequest(BaseModel):
    """Request model for creating a new OTP"""
    phone_number: PhoneNumberField = Field(..., description="Phone number for OTP delivery")
    purpose: str = Field(..., description="Purpose of OTP verification")

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        """Validate OTP purpose"""
        valid_purposes = ['registration', 'login', 'booking', 'password_reset', 'phone_verification']

        if v not in valid_purposes:
            raise ValueError(f'Purpose must be one of: {", ".join(valid_purposes)}')

        return v

class OTPValidateRequest(BaseModel):
    """Request model for validating an OTP"""
    phone_number: PhoneNumberField = Field(..., description="Phone number used for OTP")
    otp_code: str = Field(..., min_length=4, max_length=10, description="OTP code to validate")
    purpose: str = Field(..., description="Purpose of OTP verification")

    @field_validator('otp_code')
    @classmethod
    def validate_otp_code(cls, v):
        """Validate OTP code format"""
        # Remove any spaces or special characters
        cleaned = ''.join(filter(str.isdigit, v))

        if len(cleaned) not in [4, 6]:
            raise ValueError('OTP code must be 4 or 6 digits')

        return cleaned

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        """Validate OTP purpose"""
        valid_purposes = ['registration', 'login', 'booking', 'password_reset', 'phone_verification']

        if v not in valid_purposes:
            raise ValueError(f'Purpose must be one of: {", ".join(valid_purposes)}')

        return v

class OTPResendRequest(BaseModel):
    """Request model for resending an OTP"""
    phone_number: PhoneNumberField = Field(..., description="Phone number for OTP resend")
    purpose: str = Field(..., description="Purpose of OTP verification")

    @field_validator('purpose')
    @classmethod
    def validate_purpose(cls, v):
        """Validate OTP purpose"""
        valid_purposes = ['registration', 'login', 'booking', 'password_reset', 'phone_verification']

        if v not in valid_purposes:
            raise ValueError(f'Purpose must be one of: {", ".join(valid_purposes)}')

        return v

class OTPResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for OTP operations"""
    id: str = Field(..., description="OTP verification ID")
    phone_number: str = Field(..., description="Phone number (masked for security)")
    purpose: str = Field(..., description="OTP purpose")
    expires_at: datetime = Field(..., description="OTP expiration time")
    attempts_remaining: int = Field(..., description="Number of verification attempts remaining")
    is_verified: bool = Field(..., description="Whether OTP has been verified")
    can_resend: bool = Field(..., description="Whether OTP can be resent")
    resend_cooldown_seconds: Optional[int] = Field(None, description="Seconds until resend is allowed")

    @field_validator('phone_number', mode='before')
    @classmethod
    def mask_phone_number(cls, v):
        """Mask phone number for security"""
        if not v:
            return v

        # Keep country code and last 4 digits, mask the middle
        if len(v) >= 8:
            country_code = v[:3]  # +91 or similar
            last_four = v[-4:]
            masked_middle = 'X' * (len(v) - 7)
            return f"{country_code}{masked_middle}{last_four}"

        return v

class OTPValidationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for OTP validation results"""
    is_valid: bool = Field(..., description="Whether OTP validation was successful")
    verification_id: str = Field(..., description="OTP verification ID")
    phone_number: str = Field(..., description="Phone number (masked)")
    purpose: str = Field(..., description="OTP purpose")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    attempts_used: int = Field(..., description="Number of attempts used")
    verification_token: Optional[str] = Field(None, description="Token for authenticated operations")

    @field_validator('phone_number', mode='before')
    @classmethod
    def mask_phone_number(cls, v):
        """Mask phone number for security"""
        if not v:
            return v

        if len(v) >= 8:
            country_code = v[:3]
            last_four = v[-4:]
            masked_middle = 'X' * (len(v) - 7)
            return f"{country_code}{masked_middle}{last_four}"

        return v

class OTPCreateResponse(BaseResponse):
    """Response model for OTP creation"""
    otp: OTPResponse = Field(..., description="Created OTP information")
    delivery_method: str = Field(..., description="OTP delivery method")
    estimated_delivery_time: int = Field(..., description="Estimated delivery time in seconds")

class OTPValidateResponse(BaseResponse):
    """Response model for OTP validation"""
    validation: OTPValidationResponse = Field(..., description="Validation result")
    next_steps: Optional[str] = Field(None, description="Guidance for next steps")

class OTPResendResponse(BaseResponse):
    """Response model for OTP resend"""
    otp: OTPResponse = Field(..., description="Resent OTP information")
    delivery_method: str = Field(..., description="OTP delivery method")
    cooldown_applied: bool = Field(..., description="Whether cooldown period was applied")

class OTPStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for OTP statistics"""
    total_otps_sent: int = Field(..., description="Total OTPs sent")
    successful_verifications: int = Field(..., description="Successful verifications")
    failed_verifications: int = Field(..., description="Failed verifications")
    expired_otps: int = Field(..., description="Expired OTPs")
    success_rate: float = Field(..., description="OTP verification success rate")
    average_verification_time: Optional[float] = Field(None, description="Average time to verify (seconds)")
    stats_by_purpose: dict = Field(..., description="Statistics grouped by purpose")

class OTPHealthCheckResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    """Response model for OTP service health check"""
    sms_service_status: str = Field(..., description="SMS service status")
    database_connectivity: str = Field(..., description="Database connectivity status")
    recent_delivery_rate: float = Field(..., description="Recent delivery success rate")
    average_delivery_time: float = Field(..., description="Average delivery time in seconds")
    error_count_last_hour: int = Field(..., description="Number of errors in last hour")
    service_health: str = Field(..., description="Overall service health status")

