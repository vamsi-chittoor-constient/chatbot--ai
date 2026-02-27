"""
PetPooja Menu Client
HTTP client for menu-related operations
"""

import httpx
import logging
import asyncio
from typing import Dict, Any, Optional
from functools import lru_cache
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.config import settings
from app.core.db_session import get_db
from app.models.branch_models import BranchInfoTable
from app.models.other_models import RestaurantTable
from app.models.integration_models import IntegrationConfigTable, IntegrationCredentialsTable
from app.utils.encryption import CredentialsEncryption

logger = logging.getLogger(__name__)


class PetpoojaAPIError(Exception):
    """Custom exception for PetPooja API errors"""
    pass


# Credentials cache with TTL
_credentials_cache: Dict[str, tuple] = {}  # {restaurant_id: (credentials_dict, expiry_time)}
CACHE_TTL_SECONDS = settings.CREDENTIALS_CACHE_TTL_SECONDS


def _get_cached_credentials(restaurant_id: str) -> Optional[Dict[str, str]]:
    """Get credentials from cache if not expired"""
    if restaurant_id in _credentials_cache:
        credentials, expiry = _credentials_cache[restaurant_id]
        if datetime.now() < expiry:
            logger.debug(f"Cache hit for credentials: {restaurant_id}")
            return credentials
        else:
            # Expired, remove from cache
            del _credentials_cache[restaurant_id]
    return None


def _set_cached_credentials(restaurant_id: str, credentials: Dict[str, str]):
    """Store credentials in cache with TTL"""
    expiry = datetime.now() + timedelta(seconds=CACHE_TTL_SECONDS)
    _credentials_cache[restaurant_id] = (credentials, expiry)
    logger.debug(f"Cached credentials for: {restaurant_id}")


class MenuClient:
    """
    HTTP client for PetPooja Menu API

    Features:
    - Fetch menu from PetPooja (async)
    - Error handling
    - Request/response logging
    - Credentials caching
    - Optimized single-query credential lookup
    """

    def __init__(self):
        """Initialize Menu client with configuration"""
        # Use sandbox or production URL
        if settings.PETPOOJA_SANDBOX_ENABLED:
            self.base_url = settings.PETPOOJA_SANDBOX_BASE_URL
            logger.info(f"Menu Client initialized in SANDBOX mode")
        else:
            self.base_url = settings.PETPOOJA_BASE_URL
            logger.info(f"Menu Client initialized in PRODUCTION mode")

        self.timeout = settings.HTTP_TIMEOUT

        # Create async HTTP client for better performance
        self._async_client: Optional[httpx.AsyncClient] = None
        # Keep sync client for backwards compatibility
        self._sync_client: Optional[httpx.Client] = None

        # Initialize encryption service
        self.encryption = CredentialsEncryption()

    @property
    def async_client(self) -> httpx.AsyncClient:
        """Lazy initialization of async client"""
        if self._async_client is None:
            self._async_client = httpx.AsyncClient(timeout=self.timeout)
        return self._async_client

    @property
    def client(self) -> httpx.Client:
        """Lazy initialization of sync client (for backwards compatibility)"""
        if self._sync_client is None:
            self._sync_client = httpx.Client(timeout=self.timeout)
        return self._sync_client

    async def close(self):
        """Cleanup HTTP clients"""
        if self._async_client:
            await self._async_client.aclose()
            self._async_client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None

    def __del__(self):
        """Cleanup HTTP client"""
        try:
            if self._sync_client:
                self._sync_client.close()
        except:
            pass

    def get_credentials(self, restaurant_id: str) -> Dict[str, str]:
        """
        Get PetPooja credentials from database with caching and optimized query.
        Uses a single JOIN query instead of 4 separate queries.

        Args:
            restaurant_id: PetPooja restaurant ID (string)

        Returns:
            Dict with decrypted credentials: app_key, app_secret, access_token

        Raises:
            PetpoojaAPIError: If credentials not found
        """
        # Check cache first
        cached = _get_cached_credentials(restaurant_id)
        if cached:
            return cached

        session: Session = next(get_db())

        try:
            # OPTIMIZED: Single query with JOINs instead of 4 separate queries
            # This reduces database round-trips from 4 to 1
            results = session.query(
                IntegrationCredentialsTable.credential_key,
                IntegrationCredentialsTable.credential_value
            ).select_from(BranchInfoTable).join(
                RestaurantTable,
                and_(
                    RestaurantTable.chain_id == BranchInfoTable.chain_id,
                    RestaurantTable.branch_id == BranchInfoTable.branch_id,
                    RestaurantTable.is_deleted == False
                )
            ).join(
                IntegrationConfigTable,
                and_(
                    IntegrationConfigTable.restaurant_id == RestaurantTable.restaurant_id,
                    IntegrationConfigTable.is_enabled == True,
                    IntegrationConfigTable.is_deleted == False
                )
            ).join(
                IntegrationCredentialsTable,
                and_(
                    IntegrationCredentialsTable.integration_config_id == IntegrationConfigTable.integration_config_id,
                    IntegrationCredentialsTable.is_deleted == False
                )
            ).filter(
                BranchInfoTable.ext_petpooja_restaurant_id == restaurant_id,
                BranchInfoTable.is_deleted == False
            ).all()

            if not results:
                raise PetpoojaAPIError(f"No credentials found for restaurant_id: {restaurant_id}")

            # Build credentials dict and decrypt sensitive fields
            credentials_dict = {row.credential_key: row.credential_value for row in results}
            credential_dict = self.encryption.decrypt_credentials(credentials_dict)

            logger.info(f"Successfully retrieved and decrypted {len(credential_dict)} credentials for {restaurant_id}")

            # Cache the decrypted credentials
            _set_cached_credentials(restaurant_id, credential_dict)

            return credential_dict

        except PetpoojaAPIError:
            raise
        except Exception as e:
            logger.error(f"Error retrieving credentials: {e}")
            raise PetpoojaAPIError(f"Failed to retrieve credentials: {str(e)}")
        finally:
            session.close()

    async def fetch_menu_async(self, restaurant_id: str) -> Dict[str, Any]:
        """
        Fetch menu data from PetPooja (async version - preferred)

        Args:
            restaurant_id: PetPooja restaurant ID

        Returns:
            API response with menu data

        Raises:
            PetpoojaAPIError: If API request fails
        """
        logger.info(f"Fetching menu for restaurant: {restaurant_id}")

        # Get credentials from database
        credentials = self.get_credentials(restaurant_id)

        # Prepare request
        menu_endpoint = getattr(settings, 'PETPOOJA_FETCH_MENU_ENDPOINT', '/mapped_restaurant_menus')
        url = f"{self.base_url}{menu_endpoint}"

        # Credentials go in headers
        headers = {
            "Content-Type": "application/json",
            "app-key": credentials.get("app_key"),
            "app-secret": credentials.get("app_secret"),
            "access-token": credentials.get("access_token")
        }

        # Only restID in body
        payload = {
            "restID": restaurant_id
        }

        try:
            logger.debug(f"Making async request to PetPooja Menu API: {url}")
            # Make async POST request
            response = await self.async_client.post(url, json=payload, headers=headers)
            logger.info(f"PetPooja API Response Status: {response.status_code}")

            # Parse JSON response
            try:
                response_data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise PetpoojaAPIError(f"Invalid JSON response: {str(e)}")

            # Check HTTP status
            if response.status_code != 200:
                error_msg = response_data.get("message", "Unknown error")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise PetpoojaAPIError(f"API returned {response.status_code}: {error_msg}")

            # Check success field
            if not response_data.get("success", False):
                error_msg = response_data.get("message", "Request failed")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise PetpoojaAPIError(error_msg)

            # Log success
            items_count = len(response_data.get("data", {}).get("items", []))
            logger.info(f"Menu fetched successfully: {items_count} items")

            return response_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise PetpoojaAPIError(f"HTTP request failed: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise PetpoojaAPIError(f"Request failed: {str(e)}")

    def fetch_menu(self, restaurant_id: str) -> Dict[str, Any]:
        """
        Fetch menu data from PetPooja (sync version - for backwards compatibility)

        Args:
            restaurant_id: PetPooja restaurant ID

        Returns:
            API response with menu data

        Raises:
            PetpoojaAPIError: If API request fails
        """
        logger.info(f"Fetching menu for restaurant: {restaurant_id}")

        # Get credentials from database
        credentials = self.get_credentials(restaurant_id)

        # Prepare request
        menu_endpoint = getattr(settings, 'PETPOOJA_FETCH_MENU_ENDPOINT', '/mapped_restaurant_menus')
        url = f"{self.base_url}{menu_endpoint}"

        # Credentials go in headers
        headers = {
            "Content-Type": "application/json",
            "app-key": credentials.get("app_key"),
            "app-secret": credentials.get("app_secret"),
            "access-token": credentials.get("access_token")
        }

        # Only restID in body
        payload = {
            "restID": restaurant_id
        }

        try:
            logger.debug(f"Making request to PetPooja Menu API: {url}")
            # Make POST request
            response = self.client.post(url, json=payload, headers=headers)
            logger.info(f"PetPooja API Response Status: {response.status_code}")

            # Parse JSON response
            try:
                response_data = response.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON response: {e}")
                raise PetpoojaAPIError(f"Invalid JSON response: {str(e)}")

            # Check HTTP status
            if response.status_code != 200:
                error_msg = response_data.get("message", "Unknown error")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise PetpoojaAPIError(f"API returned {response.status_code}: {error_msg}")

            # Check success field
            if not response_data.get("success", False):
                error_msg = response_data.get("message", "Request failed")
                logger.error(f"PetPooja API Error: {error_msg}")
                raise PetpoojaAPIError(error_msg)

            # Log success
            items_count = len(response_data.get("data", {}).get("items", []))
            logger.info(f"Menu fetched successfully: {items_count} items")

            return response_data

        except httpx.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            raise PetpoojaAPIError(f"HTTP request failed: {str(e)}")

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise PetpoojaAPIError(f"Request failed: {str(e)}")


# Singleton instance
_menu_client: Optional[MenuClient] = None


def get_menu_client() -> MenuClient:
    """Get singleton instance of MenuClient"""
    global _menu_client
    if _menu_client is None:
        _menu_client = MenuClient()
    return _menu_client
