"""
Menu Service - ASYNC VERSION
Async wrapper for menu operations with non-blocking database and HTTP
"""

import logging
import uuid
import httpx
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.integration_models import IntegrationConfigTable, IntegrationProviderTable

logger = logging.getLogger(__name__)


class MenuServiceError(Exception):
    """Custom exception for menu service errors"""
    pass


async def fetch_and_sync_menu_by_restaurant_id(
    restaurant_id: uuid.UUID,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Fetch PetPooja credentials from database using restaurant_id (ASYNC),
    call PetPooja API to get menu, and store/update in database.

    Args:
        restaurant_id: UUID of the restaurant
        db: Async database session

    Returns:
        Dict with success status, message, and menu data
    """
    try:
        # Fetch integration config - ASYNC
        result = await db.execute(
            select(IntegrationConfigTable)
            .join(
                IntegrationProviderTable,
                IntegrationConfigTable.provider_id == IntegrationProviderTable.provider_id
            )
            .where(
                IntegrationConfigTable.restaurant_id == restaurant_id,
                IntegrationProviderTable.provider_name.ilike("%petpooja%"),
                IntegrationConfigTable.is_enabled == True,
                IntegrationConfigTable.is_deleted == False
            )
        )
        integration_config = result.scalar_one_or_none()

        if not integration_config:
            raise MenuServiceError(
                f"No active PetPooja integration found for restaurant_id: {restaurant_id}"
            )

        # Get credentials - ASYNC
        from app.services.chain_service_async import decrypt_credentials_for_use_async
        cred_dict = await decrypt_credentials_for_use_async(db, integration_config.integration_config_id)

        logger.info(f"Decrypted credentials keys: {list(cred_dict.keys())}")

        # Extract credentials
        app_key = cred_dict.get("app_key") or cred_dict.get("app-key")
        app_secret = cred_dict.get("app_secret") or cred_dict.get("app-secret")
        access_token = cred_dict.get("access_token") or cred_dict.get("access-token")
        petpooja_rest_id = cred_dict.get("petpooja_restaurantid") or cred_dict.get("restID")
        menusharingcode = cred_dict.get("restaurant_mapping_id")
        sandbox_enabled = str(cred_dict.get("sandbox_enabled", "true")).lower() == "true"

        # Validate credentials
        if not all([app_key, app_secret, access_token, petpooja_rest_id]):
            missing = []
            if not app_key: missing.append("app_key")
            if not app_secret: missing.append("app_secret")
            if not access_token: missing.append("access_token")
            if not petpooja_rest_id: missing.append("petpooja_restaurantid")
            raise MenuServiceError(f"Missing required credentials: {', '.join(missing)}")

        # Prepare API request
        base_url = settings.PETPOOJA_SANDBOX_BASE_URL if sandbox_enabled else settings.PETPOOJA_BASE_URL
        url = f"{base_url}{getattr(settings, 'PETPOOJA_FETCH_MENU_ENDPOINT', '/mapped_restaurant_menus')}"

        headers = {
            "Content-Type": "application/json",
            "app-key": app_key,
            "app-secret": app_secret,
            "access-token": access_token
        }
        payload = {"restID": menusharingcode}

        logger.info(f"Fetching menu from PetPooja for restaurant_id: {restaurant_id}")
        logger.info(f"PetPooja URL: {url}")
        logger.info(f"Sandbox enabled: {sandbox_enabled}")

        # HTTP request - ASYNC
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)
            response_data = response.json()

            logger.info(f"PetPooja response status: {response.status_code}")
            logger.info(f"PetPooja response success: {response_data.get('success')}")

            if response.status_code != 200 or not response_data.get("success", False):
                logger.error(f"PetPooja API failed: {response_data}")
                raise MenuServiceError(response_data.get("message", "PetPooja API request failed"))

            # Store menu data - ASYNC
            from app.services.menu_service_async_store import store_menu_async
            store_result = await store_menu_async(
                response_data,
                menusharingcode,
                db,
                internal_restaurant_id=restaurant_id
            )
            await db.commit()

            logger.info(f"Store result: {store_result}")
            logger.info(f"Menu synced successfully for restaurant_id: {restaurant_id}")

            return {
                "success": True,
                "message": "Menu fetched and stored successfully",
                "data": response_data,
                "store_result": store_result
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP error fetching menu: {str(e)}")
        raise MenuServiceError(f"Failed to fetch menu from PetPooja: {str(e)}")

    except MenuServiceError:
        raise

    except Exception as e:
        logger.error(f"Unexpected error in menu sync: {str(e)}", exc_info=True)
        raise MenuServiceError(f"Menu sync failed: {str(e)}")
