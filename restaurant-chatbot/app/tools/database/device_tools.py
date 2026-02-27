"""
Device management database tools.

This module provides database operations for device tracking and management
to support the 3-tier authentication system.

3-Tier Authentication:
    Tier 1: Anonymous (no device_id, no user_id)
    Tier 2: Device recognized (has device_id, no user_id)
    Tier 3: Authenticated user (has user_id, may have device_id linked)

Classes:
    CreateDeviceTool: Register a new device
    GetDeviceTool: Retrieve device by device_id
    LinkDeviceToUserTool: Link a device to a user when they authenticate
    UpdateDeviceActivityTool: Update device last_seen_at timestamp
"""

from typing import Optional, Dict, Any
from sqlalchemy import select, update
from datetime import datetime, timezone

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.shared.models import UserDevice
from app.core.logging_config import get_logger
from app.utils.schema_tool_integration import (
    serialize_output_with_schema,
    safe_isoformat
)
from app.schemas.internal import DeviceTrackingResponse

logger = get_logger(__name__)


class CreateDeviceTool(ToolBase):
    """
    Register a new device for Tier 2 authentication.

    Creates a device record for tracking anonymous/recognized users.
    """

    def __init__(self):
        super().__init__(
            name="create_device",
            description="Register a new device for tracking",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate device creation parameters"""
        device_id = kwargs.get('device_id')

        if not device_id:
            raise ToolError(
                "device_id is required to create a device",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Create a new device record"""
        try:
            async with get_db_session() as session:
                device_id = kwargs['device_id']

                # Check if device already exists
                query = select(UserDevice).where(UserDevice.device_id == device_id)
                existing_device = await session.execute(query)
                existing = existing_device.scalar_one_or_none()

                if existing:
                    # Device already exists - return existing device info
                    device_data = serialize_output_with_schema(
                        DeviceTrackingResponse,
                        existing,
                        self.name,
                        from_orm=True
                    )
                    # Add extra field
                    device_data['already_exists'] = True

                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data=device_data,
                        metadata={"operation": "get_existing_device"}
                    )

                # Create new device
                new_device = UserDevice(
                    device_id=device_id,
                    user_id=kwargs.get('user_id'),  # Optional - will be None for Tier 2
                    device_fingerprint=kwargs.get('device_fingerprint'),
                    is_active=True
                )

                session.add(new_device)
                await session.commit()
                await session.refresh(new_device)

                logger.info(f"Created device: {new_device.id}",
                    device_id=device_id,
                    user_id=new_device.user_id,
                    tier="Tier 3" if new_device.user_id else "Tier 2"
                )

                device_data = serialize_output_with_schema(
                    DeviceTrackingResponse,
                    new_device,
                    self.name,
                    from_orm=True
                )
                # Add extra field
                device_data['already_exists'] = False

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=device_data,
                    metadata={"operation": "create_device"}
                )

        except Exception as e:
            logger.error(f"Failed to create device: {str(e)}")
            raise ToolError(
                f"Database error while creating device: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetDeviceTool(ToolBase):
    """
    Retrieve device information by device_id.

    Used to check if a device is recognized and which user it belongs to.
    """

    def __init__(self):
        super().__init__(
            name="get_device",
            description="Retrieve device by device_id",
            max_retries=2,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate device lookup parameters"""
        device_id = kwargs.get('device_id')

        if not device_id:
            raise ToolError(
                "device_id is required for device lookup",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Retrieve device information"""
        try:
            async with get_db_session() as session:
                device_id = kwargs['device_id']

                query = select(UserDevice).where(UserDevice.device_id == device_id)
                result = await session.execute(query)
                device = result.scalar_one_or_none()

                if not device:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Device not found"
                    )

                # Update last_seen_at
                device.last_seen_at = datetime.now(timezone.utc)
                await session.commit()

                device_data = serialize_output_with_schema(
                    DeviceTrackingResponse,
                    device,
                    self.name,
                    from_orm=True
                )
                # Add extra field
                device_data['tier'] = "Tier 3" if device.user_id else "Tier 2"

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=device_data,
                    metadata={"operation": "get_device"}
                )

        except Exception as e:
            logger.error(f"Failed to retrieve device: {str(e)}")
            raise ToolError(
                f"Database error while retrieving device: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class LinkDeviceToUserTool(ToolBase):
    """
    Link a device to a user when they authenticate.

    Upgrades from Tier 2 (device-only) to Tier 3 (authenticated).
    """

    def __init__(self):
        super().__init__(
            name="link_device_to_user",
            description="Link a device to a user account",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate link parameters"""
        device_id = kwargs.get('device_id')
        user_id = kwargs.get('user_id')

        if not device_id:
            raise ToolError(
                "device_id is required",
                tool_name=self.name
            )

        if not user_id:
            raise ToolError(
                "user_id is required",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Link device to user"""
        try:
            async with get_db_session() as session:
                device_id = kwargs['device_id']
                user_id = kwargs['user_id']

                # Get device
                query = select(UserDevice).where(UserDevice.device_id == device_id)
                result = await session.execute(query)
                device = result.scalar_one_or_none()

                if not device:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Device not found"
                    )

                # Link device to user
                old_user_id = device.user_id
                device.user_id = user_id
                device.last_seen_at = datetime.now(timezone.utc)

                await session.commit()
                await session.refresh(device)

                logger.info("Linked device to user",
                    device_id=device_id,
                    old_user_id=old_user_id,
                    new_user_id=user_id,
                    upgrade="Tier 2  Tier 3" if not old_user_id else "User change"
                )

                device_data = serialize_output_with_schema(
                    DeviceTrackingResponse,
                    device,
                    self.name,
                    from_orm=True
                )
                # Add extra fields
                device_data['previous_user_id'] = old_user_id
                device_data['linked'] = True
                device_data['tier'] = "Tier 3"

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=device_data,
                    metadata={"operation": "link_device_to_user"}
                )

        except Exception as e:
            logger.error(f"Failed to link device to user: {str(e)}")
            raise ToolError(
                f"Database error while linking device: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class UpdateDeviceActivityTool(ToolBase):
    """
    Update device last_seen_at timestamp and activity data.
    """

    def __init__(self):
        super().__init__(
            name="update_device_activity",
            description="Update device activity timestamp",
            max_retries=2,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate update parameters"""
        device_id = kwargs.get('device_id')

        if not device_id:
            raise ToolError(
                "device_id is required",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Update device activity"""
        try:
            async with get_db_session() as session:
                device_id = kwargs['device_id']

                # Get device
                query = select(UserDevice).where(UserDevice.device_id == device_id)
                result = await session.execute(query)
                device = result.scalar_one_or_none()

                if not device:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Device not found"
                    )

                # Update activity
                device.last_seen_at = datetime.now(timezone.utc)

                # Update optional fields if provided
                if 'last_order_items' in kwargs:
                    device.last_order_items = kwargs['last_order_items']

                if 'preferred_items' in kwargs:
                    device.preferred_items = kwargs['preferred_items']

                await session.commit()
                await session.refresh(device)

                device_data = serialize_output_with_schema(
                    DeviceTrackingResponse,
                    device,
                    self.name,
                    from_orm=True
                )
                # Add extra field
                device_data['updated'] = True

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=device_data,
                    metadata={"operation": "update_device_activity"}
                )

        except Exception as e:
            logger.error(f"Failed to update device activity: {str(e)}")
            raise ToolError(
                f"Database error while updating device activity: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


if __name__ == "__main__":
    # Test device management tools
    import asyncio

    async def test_device_tools():
        """Test device management tools functionality"""
        print("Testing device management tools...")

        # Initialize database connection
        from app.database.connection import init_database
        await init_database(create_tables=False)

        try:
            # Test creating a device
            create_tool = CreateDeviceTool()
            test_device_id = "test_device_12345"
            result = await create_tool.execute(device_id=test_device_id)

            if result.status == ToolStatus.SUCCESS:
                print(f"Created device: {result.data['device_id']} (Tier 2)")

                # Test retrieving the device
                get_tool = GetDeviceTool()
                result = await get_tool.execute(device_id=test_device_id)

                if result.status == ToolStatus.SUCCESS:
                    print(f"Retrieved device: {result.data['device_id']} - {result.data['tier']}")

                    # Test linking device to user
                    # Note: Replace with actual user_id from your test database
                    link_tool = LinkDeviceToUserTool()
                    result = await link_tool.execute(
                        device_id=test_device_id,
                        user_id="usr000001"  # Replace with actual user ID
                    )

                    if result.status == ToolStatus.SUCCESS:
                        print(f"Linked device to user: {result.data['user_id']} ({result.data['tier']})")
                        print("All device management tools working correctly!")
                    else:
                        print(f"Device link failed: {result.error}")
                else:
                    print(f"Device retrieval failed: {result.error}")
            else:
                print(f"Device creation failed: {result.error}")

        except Exception as e:
            print(f"Device tools test failed: {str(e)}")

    # Run test
    asyncio.run(test_device_tools())
