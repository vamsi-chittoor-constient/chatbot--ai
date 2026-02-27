"""
Restaurant Information Tools
============================
Tools for restaurant operational information (hours, location, contact).
"""

from typing import Dict, Any, Optional
import structlog

from app.core.database import get_db_session as get_db
from app.shared.models.restaurant import Restaurant

logger = structlog.get_logger("general_queries.tools.restaurant")


async def get_restaurant_info(
    info_type: str = "general"
) -> Dict[str, Any]:
    """
    Get restaurant information.

    Args:
        info_type: Type of info (general, hours, location, contact, parking, policies)

    Returns:
        Dict with success status and restaurant info
    """
    try:
        logger.info("Getting restaurant info", info_type=info_type)

        async with get_db() as db:
            # Query Restaurant table (should have 1 record for single-location restaurant)
            restaurant = await db.execute(
                "SELECT * FROM restaurant LIMIT 1"
            )
            restaurant_data = restaurant.fetchone()

            if not restaurant_data:
                return {
                    "success": False,
                    "message": "Restaurant information not found",
                    "data": {}
                }

            # Build response based on info_type
            if info_type == "hours":
                return {
                    "success": True,
                    "message": "Business hours retrieved",
                    "data": {
                        "hours": restaurant_data.business_hours if hasattr(restaurant_data, 'business_hours') else {},
                        "info_type": "hours"
                    }
                }

            elif info_type == "location":
                return {
                    "success": True,
                    "message": "Location information retrieved",
                    "data": {
                        "address": restaurant_data.address if hasattr(restaurant_data, 'address') else "",
                        "branch_name": restaurant_data.branch_name if hasattr(restaurant_data, 'branch_name') else "",
                        "info_type": "location"
                    }
                }

            elif info_type == "contact":
                return {
                    "success": True,
                    "message": "Contact information retrieved",
                    "data": {
                        "phone": restaurant_data.phone if hasattr(restaurant_data, 'phone') else "",
                        "email": restaurant_data.email if hasattr(restaurant_data, 'email') else "",
                        "info_type": "contact"
                    }
                }

            elif info_type == "parking":
                policies = restaurant_data.policies if hasattr(restaurant_data, 'policies') else {}
                parking_info = policies.get("parking", "Parking information not available")

                return {
                    "success": True,
                    "message": "Parking information retrieved",
                    "data": {
                        "parking": parking_info,
                        "info_type": "parking"
                    }
                }

            else:  # general
                return {
                    "success": True,
                    "message": "Restaurant information retrieved",
                    "data": {
                        "name": restaurant_data.name if hasattr(restaurant_data, 'name') else "",
                        "address": restaurant_data.address if hasattr(restaurant_data, 'address') else "",
                        "phone": restaurant_data.phone if hasattr(restaurant_data, 'phone') else "",
                        "email": restaurant_data.email if hasattr(restaurant_data, 'email') else "",
                        "business_hours": restaurant_data.business_hours if hasattr(restaurant_data, 'business_hours') else {},
                        "info_type": "general"
                    }
                }

    except Exception as e:
        logger.error("Get restaurant info failed", error=str(e), info_type=info_type)

        return {
            "success": False,
            "message": f"Failed to retrieve restaurant information: {str(e)}",
            "data": {}
        }


async def get_business_hours() -> Dict[str, Any]:
    """
    Get restaurant business hours.

    Returns:
        Dict with success status and business hours
    """
    return await get_restaurant_info(info_type="hours")


async def get_location_info() -> Dict[str, Any]:
    """
    Get restaurant location and address.

    Returns:
        Dict with success status and location info
    """
    return await get_restaurant_info(info_type="location")


async def get_contact_info() -> Dict[str, Any]:
    """
    Get restaurant contact information.

    Returns:
        Dict with success status and contact info
    """
    return await get_restaurant_info(info_type="contact")


async def get_parking_info() -> Dict[str, Any]:
    """
    Get parking information.

    Returns:
        Dict with success status and parking info
    """
    return await get_restaurant_info(info_type="parking")


__all__ = [
    "get_restaurant_info",
    "get_business_hours",
    "get_location_info",
    "get_contact_info",
    "get_parking_info"
]
