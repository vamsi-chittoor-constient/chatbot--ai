"""PetPooja Order Client - ASYNC HTTP client for order operations"""

import httpx
import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class PetpoojaAPIError(Exception):
    """Custom exception for PetPooja API errors"""
    pass


class AsyncOrderClient:
    """Async HTTP client for PetPooja Order API"""

    def __init__(self):
        if settings.PETPOOJA_SANDBOX_ENABLED:
            self.base_url = settings.PETPOOJA_SANDBOX_ORDER_URL
        else:
            self.base_url = settings.PETPOOJA_BASE_URL

        self.app_key = settings.PETPOOJA_APP_KEY
        self.app_secret = settings.PETPOOJA_APP_SECRET
        self.access_token = settings.PETPOOJA_ACCESS_TOKEN
        self.timeout = settings.HTTP_TIMEOUT
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        """Async context manager entry"""
        self._client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_keepalive_connections=settings.HTTPX_MAX_KEEPALIVE_CONNECTIONS,
                max_connections=settings.HTTPX_MAX_CONNECTIONS
            )
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get or create async client"""
        if self._client is None:
            # Create a persistent client for singleton usage
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=settings.HTTPX_MAX_KEEPALIVE_CONNECTIONS,
                    max_connections=settings.HTTPX_MAX_CONNECTIONS
                )
            )
        return self._client

    async def close(self):
        """Close the async client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_credentials(self, credentials: Optional[Dict[str, str]]) -> tuple:
        """Get credentials from provided dict or defaults"""
        app_key = credentials.get("app_key") if credentials and credentials.get("app_key") else self.app_key
        app_secret = credentials.get("app_secret") if credentials and credentials.get("app_secret") else self.app_secret
        access_token = credentials.get("access_token") if credentials and credentials.get("access_token") else self.access_token
        return app_key, app_secret, access_token

    async def save_order(
        self,
        order_data: Dict[str, Any],
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Save order to PetPooja POS - ASYNC"""
        app_key, app_secret, access_token = self._get_credentials(credentials)

        payload = {
            "app_key": app_key,
            "app_secret": app_secret,
            "access_token": access_token,
            "orderinfo": order_data.get("orderinfo", {}),
            "udid": order_data.get("udid", settings.PETPOOJA_ORDER_UDID),
            "device_type": order_data.get("device_type", settings.PETPOOJA_ORDER_DEVICE_TYPE)
        }

        try:
            response = await self.client.post(
                f"{self.base_url}/save_order",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            response_data = response.json()

            if response.status_code != 200:
                raise PetpoojaAPIError(
                    f"API returned {response.status_code}: {response_data.get('message', 'Unknown error')}"
                )

            if not response_data.get("success", False):
                raise PetpoojaAPIError(response_data.get("message", "Request failed"))

            return response_data

        except httpx.HTTPError as e:
            raise PetpoojaAPIError(f"HTTP request failed: {str(e)}")

    async def update_order_status(
        self,
        rest_id: str,
        client_order_id: str,
        status: str,
        cancel_reason: str = "",
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Update order status at PetPooja POS - ASYNC"""
        app_key, app_secret, access_token = self._get_credentials(credentials)

        payload = {
            "app_key": app_key,
            "app_secret": app_secret,
            "access_token": access_token,
            "restID": rest_id,
            "orderID": "",
            "clientorderID": client_order_id,
            "cancelReason": cancel_reason,
            "status": status
        }

        try:
            # Use base_url instead of hardcoded URL
            response = await self.client.post(
                f"{self.base_url}/update_order_status",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            response_data = response.json()

            if response.status_code != 200:
                raise PetpoojaAPIError(
                    f"API returned {response.status_code}: {response_data.get('message', 'Unknown error')}"
                )

            if not response_data.get("success", False):
                raise PetpoojaAPIError(response_data.get("message", "Request failed"))

            return response_data

        except httpx.HTTPError as e:
            raise PetpoojaAPIError(f"HTTP request failed: {str(e)}")


# Singleton instance
_async_order_client: Optional[AsyncOrderClient] = None


def get_async_order_client() -> AsyncOrderClient:
    """Get singleton instance of AsyncOrderClient"""
    global _async_order_client
    if _async_order_client is None:
        _async_order_client = AsyncOrderClient()
    return _async_order_client


async def close_async_order_client():
    """Close the singleton async client on shutdown"""
    global _async_order_client
    if _async_order_client:
        await _async_order_client.close()
        _async_order_client = None
