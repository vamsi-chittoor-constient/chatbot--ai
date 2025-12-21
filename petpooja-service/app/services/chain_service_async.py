"""
Chain Service - ASYNC VERSION
Async wrapper for chain operations with non-blocking database and HTTP
"""

import logging
import uuid
import httpx
from typing import Dict, Any, List, Optional
from datetime import time as time_type
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.models.integration_models import IntegrationCredentialsTable, IntegrationConfigTable, IntegrationProviderTable
from app.models.chain_models import ChainInfoTable, ChainContactTable, ChainLocationTable
from app.models.location_models import PincodeTable, CityTable, StateTable, CountryTable
from app.models.branch_models import BranchInfoTable, BranchContactTable, BranchLocationTable, BranchTimingPolicy
from app.models.other_models import RestaurantTable, Cuisines, VariationGroups
from app.models.menu_models import (
    MenuSections, MenuCategories, MenuSubCategories, MenuItem,
    MenuItemAddonGroup, MenuItemAddonItem, MenuItemAddonMapping,
    MenuItemAttribute, MenuItemTag, MenuItemTagMapping,
    MenuItemVariation, MenuItemTaxMapping, MenuItemCuisineMapping
)
from app.utils.encryption import get_encryption_service, EncryptionError, generate_api_key
from app.schemas.petpooja_chain import StoreChainDetailsPetpoojaRequest

logger = logging.getLogger(__name__)


class ChainServiceError(Exception):
    """Custom exception for chain service errors"""
    pass


async def decrypt_credentials_for_use_async(db: AsyncSession, integration_config_id: str) -> Dict[str, Any]:
    """
    Retrieve and decrypt credentials from database for API usage (ASYNC).
    This function safely decrypts only the configured sensitive fields (app_key, app_secret, access_token)
    and leaves other fields like restaurant_mapping_id and petpooja_restaurantid unencrypted.

    Args:
        db: Async database session
        integration_config_id: Integration config ID to retrieve credentials for

    Returns:
        Dictionary with decrypted credential values

    Raises:
        Exception: If integration config or credentials not found
        EncryptionError: If decryption fails due to key mismatch
    """
    # Query all credentials for the integration config - ASYNC
    result = await db.execute(
        select(IntegrationCredentialsTable).where(
            IntegrationCredentialsTable.integration_config_id == integration_config_id,
            IntegrationCredentialsTable.is_deleted == False
        )
    )
    creds = result.scalars().all()

    if not creds:
        raise Exception(f"No credentials found for integration_config_id: {integration_config_id}")

    # Build credentials dictionary
    credentials_dict = {cred.credential_key: cred.credential_value for cred in creds}

    # Decrypt sensitive fields
    encryption_service = get_encryption_service()
    try:
        return encryption_service.decrypt_credentials(credentials_dict)
    except EncryptionError as e:
        logger.error(f"Failed to decrypt credentials for integration_config_id {integration_config_id}: {e}")
        raise Exception(f"Credential decryption failed.")


async def fetch_menu_from_petpooja_with_credentials_only_async(
    restaurant_id: str,
    app_key: str,
    app_secret: str,
    access_token: str,
    sandbox_enabled: bool
) -> Dict[str, Any]:
    """
    Fetch menu from PetPooja API using custom credentials - data only, no storage (ASYNC)

    Args:
        restaurant_id: Internal restaurant ID
        app_key: PetPooja app key
        app_secret: PetPooja app secret
        access_token: PetPooja access token
        sandbox_enabled: Whether to use sandbox environment

    Returns:
        Dict containing menu data only

    Raises:
        ChainServiceError: If fetching menu fails
    """
    try:
        # Determine base URL
        if sandbox_enabled:
            base_url = settings.PETPOOJA_SANDBOX_BASE_URL
            logger.info(f"Fetching menu in SANDBOX mode for restaurant {restaurant_id}")
        else:
            base_url = settings.PETPOOJA_BASE_URL
            logger.info(f"Fetching menu in PRODUCTION mode for restaurant {restaurant_id}")

        # Prepare request
        menu_endpoint = getattr(settings, 'PETPOOJA_FETCH_MENU_ENDPOINT', '/mapped_restaurant_menus')
        url = f"{base_url}{menu_endpoint}"

        headers = {
            "Content-Type": "application/json",
            "app-key": app_key,
            "app-secret": app_secret,
            "access-token": access_token
        }

        payload = {
            "restID": restaurant_id
        }

        # Make request - ASYNC
        async with httpx.AsyncClient(timeout=settings.HTTP_TIMEOUT) as client:
            response = await client.post(url, json=payload, headers=headers)

            # Parse response
            try:
                response_data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise ChainServiceError(f"Invalid JSON response: {str(e)}")

            # Check HTTP status
            if response.status_code != 200:
                error_msg = response_data.get("message", "Unknown error")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise ChainServiceError(f"API returned {response.status_code}: {error_msg}")

            # Check success field
            if not response_data.get("success", False):
                error_msg = response_data.get("message", "Request failed")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise ChainServiceError(f"Failed to fetch menu from PetPooja: {error_msg}")

            logger.info(f"Menu fetched successfully for restaurant {restaurant_id}")

            return {
                "success": True,
                "message": "Menu fetched successfully",
                "data": response_data
            }

    except httpx.HTTPError as e:
        logger.error(f"HTTP Error: {str(e)}")
        raise ChainServiceError(f"HTTP request failed: {str(e)}")
    except ChainServiceError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching menu: {str(e)}")
        raise ChainServiceError(f"Failed to fetch menu: {str(e)}")


async def get_chain_by_name_async(db: AsyncSession, name: str) -> List[Dict[str, Any]]:
    """
    Get chain information by name with contacts and location (ASYNC).

    Args:
        db: Async database session
        name: Chain name to search for

    Returns:
        List of chain information dictionaries
    """
    # Query chains - ASYNC
    result = await db.execute(
        select(ChainInfoTable).where(
            ChainInfoTable.chain_name.ilike(f"%{name}%"),
            ChainInfoTable.is_deleted == False
        ).limit(5)
    )
    chains = result.scalars().all()

    result_list = []

    for i, chain in enumerate(chains):
        # Get primary contact - ASYNC
        contact_result = await db.execute(
            select(ChainContactTable).where(
                ChainContactTable.chain_id == chain.chain_id,
                ChainContactTable.is_deleted == False
            ).order_by(ChainContactTable.is_primary.desc())
        )
        contact = contact_result.scalars().first()

        # Get location - ASYNC
        location_result = await db.execute(
            select(ChainLocationTable).where(
                ChainLocationTable.chain_id == chain.chain_id,
                ChainLocationTable.is_deleted == False
            )
        )
        location = location_result.scalars().first()

        city_name = state_name = country_name = None
        pincode_value = None

        if location and location.pincode_id:
            # Get pincode - ASYNC
            pincode_result = await db.execute(
                select(PincodeTable).where(
                    PincodeTable.pincode_id == location.pincode_id,
                    PincodeTable.is_deleted == False
                )
            )
            pincode = pincode_result.scalar_one_or_none()

            if pincode:
                pincode_value = pincode.pincode

                # Get city - ASYNC
                city_result = await db.execute(
                    select(CityTable).where(
                        CityTable.city_id == pincode.city_id,
                        CityTable.is_deleted == False
                    )
                )
                city = city_result.scalar_one_or_none()

                if city:
                    city_name = city.city_name

                    # Get state - ASYNC
                    state_result = await db.execute(
                        select(StateTable).where(
                            StateTable.state_id == city.state_id,
                            StateTable.is_deleted == False
                        )
                    )
                    state = state_result.scalar_one_or_none()

                    if state:
                        state_name = state.state_name

                        # Get country - ASYNC
                        country_result = await db.execute(
                            select(CountryTable).where(
                                CountryTable.country_id == state.country_id,
                                CountryTable.is_deleted == False
                            )
                        )
                        country = country_result.scalar_one_or_none()

                        if country:
                            country_name = country.country_name

        result_list.append({
            "chainIndex": i,
            "chainId": str(chain.chain_id),
            "chainName": chain.chain_name,
            "website": chain.chain_website_url,
            "logoUrl": chain.chain_logo_url,
            "contactType": contact.contact_type if contact else None,
            "contactValue": contact.contact_value if contact else None,
            "contactLabel": contact.contact_label if contact else None,
            "address": location.address_line if location else None,
            "landmark": location.landmark if location else None,
            "pincode": pincode_value if pincode_value else None,
            "city": city_name if city_name else None,
            "state": state_name if state_name else None,
            "country": country_name if country_name else None,
            "latitude": str(location.latitude) if location and location.latitude else None,
            "longitude": str(location.longitude) if location and location.longitude else None,
        })

    return result_list
