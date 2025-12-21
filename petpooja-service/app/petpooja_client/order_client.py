"""PetPooja Order Client - HTTP client for order operations"""

import httpx
import logging
from typing import Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class PetpoojaAPIError(Exception):
    """Custom exception for PetPooja API errors"""
    pass


class OrderClient:
    """HTTP client for PetPooja Order API"""

    def __init__(self):
        if settings.PETPOOJA_SANDBOX_ENABLED:
            self.base_url = settings.PETPOOJA_SANDBOX_ORDER_URL
        else:
            self.base_url = settings.PETPOOJA_BASE_URL

        self.app_key = settings.PETPOOJA_APP_KEY
        self.app_secret = settings.PETPOOJA_APP_SECRET
        self.access_token = settings.PETPOOJA_ACCESS_TOKEN
        self.timeout = settings.HTTP_TIMEOUT
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def __del__(self):
        try:
            if self._client:
                self._client.close()
        except:
            pass

    def _get_credentials(self, credentials: Optional[Dict[str, str]]) -> tuple:
        app_key = credentials.get("app_key") if credentials and credentials.get("app_key") else self.app_key
        app_secret = credentials.get("app_secret") if credentials and credentials.get("app_secret") else self.app_secret
        access_token = credentials.get("access_token") if credentials and credentials.get("access_token") else self.access_token
        return app_key, app_secret, access_token

    def save_order(self, order_data: Dict[str, Any], credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Save order to PetPooja POS"""
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
            response = self.client.post(
                f"{self.base_url}/save_order",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            response_data = response.json()

            if response.status_code != 200:
                raise PetpoojaAPIError(f"API returned {response.status_code}: {response_data.get('message', 'Unknown error')}")

            if not response_data.get("success", False):
                raise PetpoojaAPIError(response_data.get("message", "Request failed"))

            return response_data

        except httpx.HTTPError as e:
            raise PetpoojaAPIError(f"HTTP request failed: {str(e)}")

    def update_order_status(
        self,
        rest_id: str,
        client_order_id: str,
        status: str,
        cancel_reason: str = "",
        credentials: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Update order status at PetPooja POS"""
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

        # Use sandbox update order URL if sandbox is enabled, otherwise use base URL
        update_url = (
            settings.PETPOOJA_SANDBOX_UPDATE_ORDER_URL
            if settings.PETPOOJA_SANDBOX_ENABLED
            else f"{self.base_url}/update_order_status"
        )

        try:
            response = self.client.post(
                update_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            response_data = response.json()

            if response.status_code != 200:
                raise PetpoojaAPIError(f"API returned {response.status_code}: {response_data.get('message', 'Unknown error')}")

            if not response_data.get("success", False):
                raise PetpoojaAPIError(response_data.get("message", "Request failed"))

            return response_data

        except httpx.HTTPError as e:
            raise PetpoojaAPIError(f"HTTP request failed: {str(e)}")


_order_client: Optional[OrderClient] = None


def get_order_client() -> OrderClient:
    """Get singleton instance of OrderClient"""
    global _order_client
    if _order_client is None:
        _order_client = OrderClient()
    return _order_client
