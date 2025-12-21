"""
API Key Management Utility
Dynamic API key generation and management for multi-tenant restaurants
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from app.shared.models import Restaurant
from app.core.database import get_db_session

logger = structlog.get_logger(__name__)


class APIKeyManager:
    """
    Manages API key generation, validation, and lifecycle.
    Provides dynamic control over API keys for multi-tenant system.
    """

    def __init__(self):
        self.key_prefix = "rest_"
        self.key_length = 48

    def generate_api_key(self) -> str:
        """
        Generate secure API key with restaurant prefix.

        Format: rest_<48_random_hex_characters>
        Example: rest_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2

        Returns:
            str: Secure API key
        """
        random_part = secrets.token_hex(self.key_length // 2)
        api_key = f"{self.key_prefix}{random_part}"

        logger.info("api_key_generated", key_prefix=self.key_prefix, key_length=len(api_key))
        return api_key

    def hash_api_key(self, api_key: str) -> str:
        """
        Generate SHA-256 hash of API key for secure storage comparison.

        Args:
            api_key: API key to hash

        Returns:
            str: SHA-256 hash
        """
        return hashlib.sha256(api_key.encode()).hexdigest()

    async def create_api_key_for_restaurant(
        self,
        restaurant_id: str,
        session: AsyncSession
    ) -> Optional[str]:
        """
        Generate and assign new API key to restaurant.

        Args:
            restaurant_id: Restaurant ID
            session: Database session

        Returns:
            str: New API key or None if failed
        """
        try:
            query = select(Restaurant).where(Restaurant.id == restaurant_id)
            result = await session.execute(query)
            restaurant = result.scalar_one_or_none()

            if not restaurant:
                logger.error("create_api_key_failed_restaurant_not_found", restaurant_id=restaurant_id)
                return None

            new_api_key = self.generate_api_key()

            update_stmt = (
                update(Restaurant)
                .where(Restaurant.id == restaurant_id)
                .values(api_key=new_api_key, updated_at=datetime.now())
            )

            await session.execute(update_stmt)
            await session.commit()

            logger.info(
                "api_key_created_for_restaurant",
                restaurant_id=restaurant_id,
                restaurant_name=restaurant.name
            )

            return new_api_key

        except Exception as e:
            await session.rollback()
            logger.error(
                "create_api_key_error",
                restaurant_id=restaurant_id,
                error=str(e)
            )
            return None

    async def validate_api_key(
        self,
        api_key: str,
        session: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        Validate API key and return restaurant info.

        Args:
            api_key: API key to validate
            session: Database session

        Returns:
            dict: Restaurant info if valid, None if invalid
        """
        try:
            query = select(Restaurant).where(Restaurant.api_key == api_key)
            result = await session.execute(query)
            restaurant = result.scalar_one_or_none()

            if not restaurant:
                logger.warning("api_key_validation_failed_invalid_key")
                return None

            logger.info(
                "api_key_validated",
                restaurant_id=restaurant.id,
                restaurant_name=restaurant.name
            )

            return {
                "restaurant_id": restaurant.id,
                "restaurant_name": restaurant.name,
                "phone": restaurant.phone,
                "email": restaurant.email
            }

        except Exception as e:
            logger.error("api_key_validation_error", error=str(e))
            return None

    async def regenerate_api_key(
        self,
        restaurant_id: str,
        session: AsyncSession
    ) -> Optional[str]:
        """
        Regenerate API key for restaurant (rotation).

        Args:
            restaurant_id: Restaurant ID
            session: Database session

        Returns:
            str: New API key or None if failed
        """
        logger.warning("api_key_regeneration_initiated", restaurant_id=restaurant_id)
        return await self.create_api_key_for_restaurant(restaurant_id, session)

    async def get_restaurant_by_api_key(
        self,
        api_key: str,
        session: AsyncSession
    ) -> Optional[Restaurant]:
        """
        Get full restaurant object by API key.

        Args:
            api_key: API key
            session: Database session

        Returns:
            Restaurant: Restaurant object or None
        """
        try:
            query = select(Restaurant).where(Restaurant.api_key == api_key)
            result = await session.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error("get_restaurant_by_api_key_error", error=str(e))
            return None


_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    """Get or create singleton API key manager"""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
