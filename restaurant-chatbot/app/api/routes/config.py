"""
Restaurant Configuration Endpoints
===================================
Manage restaurant-specific settings for AI assistant
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import structlog

from app.core.config import config
from app.schemas.common import BaseResponse

router = APIRouter()
logger = structlog.get_logger("api.config")


class RestaurantInfo(BaseModel):
    """Basic restaurant information"""
    name: str
    description: str
    cuisine_type: str
    phone: str
    email: str
    address: Dict[str, str]
    business_hours: Dict[str, str]
    website: Optional[str] = None


class AIConfiguration(BaseModel):
    """AI assistant configuration"""
    welcome_message: str
    personality_tone: str = "friendly"  # friendly, professional, casual
    supported_languages: List[str] = ["en"]
    max_conversation_length: int = 50
    enable_personalization: bool = True
    enable_recommendations: bool = True


class IntegrationSettings(BaseModel):
    """External service integration settings"""
    payment_gateway_enabled: bool = False
    sms_notifications_enabled: bool = True
    email_notifications_enabled: bool = False
    loyalty_program_enabled: bool = False


class RestaurantConfig(BaseModel):
    """Complete restaurant configuration"""
    restaurant: RestaurantInfo
    ai_config: AIConfiguration
    integrations: IntegrationSettings
    last_updated: str
    version: str


class RestaurantConfigResponse(BaseResponse):
    """Restaurant configuration API response"""
    data: RestaurantConfig


@router.get("/config/restaurant", response_model=RestaurantConfigResponse)
async def get_restaurant_config():
    """
    Get restaurant configuration for AI assistant
    Admin-ready: Configuration that AI agents use for personalization
    """

    logger.info("restaurant_config_requested")

    try:
        # In a real implementation, this would load from database
        # For now, using default configuration
        restaurant_config = RestaurantConfig(
            restaurant=RestaurantInfo(
                name="Demo Restaurant",
                description="A delicious restaurant serving amazing food",
                cuisine_type="Multi-cuisine",
                phone="+1234567890",
                email="contact@demorestaurant.com",
                address={
                    "street": "123 Main Street",
                    "city": "Demo City",
                    "state": "Demo State",
                    "postal_code": "12345",
                    "country": "Demo Country"
                },
                business_hours={
                    "monday": "9:00 AM - 10:00 PM",
                    "tuesday": "9:00 AM - 10:00 PM",
                    "wednesday": "9:00 AM - 10:00 PM",
                    "thursday": "9:00 AM - 10:00 PM",
                    "friday": "9:00 AM - 11:00 PM",
                    "saturday": "9:00 AM - 11:00 PM",
                    "sunday": "10:00 AM - 9:00 PM"
                },
                website="https://demorestaurant.com"
            ),
            ai_config=AIConfiguration(
                welcome_message="Hello! Welcome to Demo Restaurant! I'm your AI assistant. You can explore our menu, place orders, or book a table.",
                personality_tone="friendly",
                supported_languages=["en"],
                max_conversation_length=50,
                enable_personalization=True,
                enable_recommendations=True
            ),
            integrations=IntegrationSettings(
                payment_gateway_enabled=False,
                sms_notifications_enabled=True,
                email_notifications_enabled=False,
                loyalty_program_enabled=False
            ),
            last_updated=datetime.now(timezone.utc).isoformat(),
            version=config.APP_VERSION
        )

        logger.info(
            "restaurant_config_loaded",
            restaurant_name=restaurant_config.restaurant.name,
            ai_personality=restaurant_config.ai_config.personality_tone,
            languages_supported=len(restaurant_config.ai_config.supported_languages)
        )

        return RestaurantConfigResponse(
            success=True,
            message="Restaurant configuration loaded successfully",
            data=restaurant_config
        )

    except Exception as e:
        logger.error("restaurant_config_load_failed", error=str(e))

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to load restaurant configuration",
                "error": str(e)
            }
        )


@router.get("/config/ai/welcome-message")
async def get_welcome_message():
    """
    Get AI welcome message for chat initialization
    Admin-ready: Customizable welcome message per restaurant
    """

    logger.info("welcome_message_requested")

    try:
        # Load restaurant config (simplified for now)
        welcome_message = "Hello! Welcome to Demo Restaurant! I'm your AI assistant. You can explore our menu, place orders, or book a table."

        logger.info("welcome_message_provided")

        return {
            "success": True,
            "message": "Welcome message retrieved",
            "data": {
                "welcome_message": welcome_message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    except Exception as e:
        logger.error("welcome_message_load_failed", error=str(e))

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to load welcome message",
                "error": str(e)
            }
        )


@router.get("/config/business-hours")
async def get_business_hours():
    """
    Get restaurant business hours
    Admin-ready: AI uses this to inform customers about availability
    """

    logger.info("business_hours_requested")

    try:
        business_hours = {
            "monday": "9:00 AM - 10:00 PM",
            "tuesday": "9:00 AM - 10:00 PM",
            "wednesday": "9:00 AM - 10:00 PM",
            "thursday": "9:00 AM - 10:00 PM",
            "friday": "9:00 AM - 11:00 PM",
            "saturday": "9:00 AM - 11:00 PM",
            "sunday": "10:00 AM - 9:00 PM"
        }

        # Check if currently open (basic implementation)
        current_time = datetime.now()
        current_day = current_time.strftime("%A").lower()
        is_open = True  # Simplified - would need proper time parsing

        logger.info(
            "business_hours_provided",
            current_day=current_day,
            is_currently_open=is_open
        )

        return {
            "success": True,
            "message": "Business hours retrieved",
            "data": {
                "business_hours": business_hours,
                "current_day": current_day,
                "is_currently_open": is_open,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        }

    except Exception as e:
        logger.error("business_hours_load_failed", error=str(e))

        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "message": "Failed to load business hours",
                "error": str(e)
            }
        )
