"""
Restaurant management database tools.

This module provides database operations for restaurant configuration
and table management.

Classes:
    GetRestaurantTool: Retrieve restaurant configuration
    GetTablesTool: Retrieve tables and availability
"""

from typing import Optional, Dict, Any
from sqlalchemy import select

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.shared.models import Restaurant, Table
from app.core.logging_config import get_logger
from app.utils.schema_tool_integration import (
    serialize_output_with_schema,
    safe_isoformat
)
from app.schemas.internal import RestaurantConfigResponse
from app.features.booking.schemas.booking import TableResponse

logger = get_logger(__name__)


class GetRestaurantTool(ToolBase):
    """Retrieve restaurant configuration and operational information."""

    def __init__(self):
        super().__init__(
            name="get_restaurant",
            description="Retrieve restaurant configuration and settings",
            max_retries=2,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                restaurant_id = kwargs.get('restaurant_id')

                if restaurant_id:
                    query = select(Restaurant).where(Restaurant.id == restaurant_id)
                else:
                    query = select(Restaurant).limit(1)

                result = await session.execute(query)
                restaurant = result.scalar_one_or_none()

                if not restaurant:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Restaurant configuration not found"
                    )

                # Serialize restaurant using schema
                restaurant_data = serialize_output_with_schema(
                    RestaurantConfigResponse,
                    restaurant,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=restaurant_data,
                    metadata={"operation": "get_restaurant"}
                )

        except Exception as e:
            logger.error(f"Failed to retrieve restaurant: {str(e)}")
            raise ToolError(
                f"Database error while retrieving restaurant: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetTablesTool(ToolBase):
    """Retrieve restaurant tables and their availability."""

    def __init__(self):
        super().__init__(
            name="get_tables",
            description="Retrieve restaurant tables and availability",
            max_retries=2,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            async with get_db_session() as session:
                query = select(Table)

                restaurant_id = kwargs.get('restaurant_id')
                if restaurant_id:
                    query = query.where(Table.restaurant_id == restaurant_id)

                is_active = kwargs.get('is_active')
                if is_active is not None:
                    query = query.where(Table.is_active == is_active)

                query = query.order_by(Table.table_number)
                result = await session.execute(query)
                tables = result.scalars().all()

                # Serialize tables using schema
                tables_data = []
                for table in tables:
                    table_data = serialize_output_with_schema(
                        TableResponse,
                        table,
                        self.name,
                        from_orm=True
                    )
                    tables_data.append(table_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "tables": tables_data,
                        "total_count": len(tables_data)
                    },
                    metadata={"operation": "get_tables"}
                )

        except Exception as e:
            logger.error(f"Failed to retrieve tables: {str(e)}")
            raise ToolError(
                f"Database error while retrieving tables: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )
