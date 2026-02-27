"""
Payment Database Tools
======================

Database-specific operations for payment data management:
- Payment status queries and retrieval
- Payment history and analytics
- Database-focused payment operations
- Payment data persistence operations

Separated from external API calls and event processing for clean architecture.
"""

from typing import Dict, Any
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus
from app.core.database import get_db_session
# from app.shared.models import PaymentOrder
from app.features.food_ordering.models import PaymentOrder
from app.core.logging_config import get_logger
from app.utils.validation_decorators import require_tables
from app.utils.schema_tool_integration import serialize_output_with_schema, safe_isoformat
from app.schemas.payment import (
    PaymentOrderResponse,
    PaymentTransactionResponse,
    PaymentAnalyticsResponse
)

logger = get_logger(__name__)


class PaymentStatusTool(ToolBase):
    """
    Database tool for querying payment status and history.
    Handles all database queries related to payment data.
    """

    def __init__(self):
        super().__init__(
            name="payment_status",
            description="Query payment status, history, and database operations"
        )

    @require_tables("payment_orders,payment_transactions")
    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Execute payment database operations

        Operations:
        - get_status: Get payment status for order or payment
        - get_history: Get payment history for user or order
        - get_analytics: Get payment analytics data
        """
        operation = kwargs.get("operation")

        try:
            async with get_db_session() as session:
                if operation == "get_status":
                    return await self._get_payment_status(session, kwargs)

                elif operation == "get_history":
                    return await self._get_payment_history(session, kwargs)

                elif operation == "get_analytics":
                    return await self._get_payment_analytics(session, kwargs)

                else:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        data={"error": f"Unknown operation: {operation}"}
                    )

        except Exception as e:
            logger.error(f"PaymentStatusTool error: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Payment database operation failed: {str(e)}"}
            )

    async def _get_payment_status(self, session, params: Dict[str, Any]) -> ToolResult:
        """Get payment status for order or payment"""
        order_id = params.get("order_id")
        payment_order_id = params.get("payment_order_id")

        if not order_id and not payment_order_id:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "Either order_id or payment_order_id is required"}
            )

        try:
            if payment_order_id:
                query = select(PaymentOrder).where(PaymentOrder.id == payment_order_id)
            else:
                query = select(PaymentOrder).where(PaymentOrder.order_id == order_id)

            query = query.options(
                selectinload(PaymentOrder.payment_transactions),
                selectinload(PaymentOrder.retry_attempts)
            )

            result = await session.execute(query)
            payment_order = result.scalar_one_or_none()

            if not payment_order:
                return ToolResult(
                    status=ToolStatus.FAILURE,
                    data={"error": "Payment order not found"}
                )

            # Get latest transaction
            latest_transaction = None
            if payment_order.payment_transactions:
                latest_transaction = max(
                    payment_order.payment_transactions,
                    key=lambda t: t.created_at
                )

            # Serialize payment order using schema
            payment_data = serialize_output_with_schema(
                PaymentOrderResponse,
                payment_order,
                "payment_status",
                from_orm=True
            )

            # Serialize latest transaction if exists
            if latest_transaction:
                transaction_data = serialize_output_with_schema(
                    PaymentTransactionResponse,
                    latest_transaction,
                    "payment_status",
                    from_orm=True
                )
            else:
                transaction_data = None

            # Add extra computed fields
            payment_data['latest_transaction'] = transaction_data
            payment_data['can_retry'] = payment_order.retry_count < payment_order.max_retry_attempts

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data=payment_data
            )

        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Failed to get payment status: {str(e)}"}
            )

    async def _get_payment_history(self, session, params: Dict[str, Any]) -> ToolResult:
        """Get payment history for user or order"""
        user_id = params.get("user_id")
        order_id = params.get("order_id")
        limit = params.get("limit", 50)

        if not user_id and not order_id:
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": "Either user_id or order_id is required"}
            )

        try:
            # Build query based on parameters
            query = select(PaymentOrder).options(
                selectinload(PaymentOrder.payment_transactions),
                selectinload(PaymentOrder.order)
            )

            if user_id:
                query = query.where(PaymentOrder.user_id == user_id)
            if order_id:
                query = query.where(PaymentOrder.order_id == order_id)

            query = query.order_by(PaymentOrder.created_at.desc()).limit(limit)

            result = await session.execute(query)
            payment_orders = result.scalars().all()

            payment_history = []
            for payment_order in payment_orders:
                # Get latest transaction for each payment order
                latest_transaction = None
                if payment_order.payment_transactions:
                    latest_transaction = max(
                        payment_order.payment_transactions,
                        key=lambda t: t.created_at
                    )

                # Serialize payment order
                payment_data = serialize_output_with_schema(
                    PaymentOrderResponse,
                    payment_order,
                    "payment_status",
                    from_orm=True
                )

                # Serialize latest transaction if exists
                if latest_transaction:
                    transaction_data = serialize_output_with_schema(
                        PaymentTransactionResponse,
                        latest_transaction,
                        "payment_status",
                        from_orm=True
                    )
                else:
                    transaction_data = None

                # Add extra fields
                payment_data['order_number'] = payment_order.order.order_number if payment_order.order else None
                payment_data['latest_transaction'] = transaction_data

                payment_history.append(payment_data)

            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    "payment_history": payment_history,
                    "total_count": len(payment_history),
                    "filters": {
                        "user_id": user_id,
                        "order_id": order_id,
                        "limit": limit
                    }
                }
            )

        except Exception as e:
            logger.error(f"Error getting payment history: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                data={"error": f"Failed to get payment history: {str(e)}"}
            )

    async def _get_payment_analytics(self, session, params: Dict[str, Any]) -> ToolResult:
        """Get payment analytics data"""
        # Mark session as used for future implementation
        _ = session  # Will be used for analytics queries
        _ = params  # Will be used for filtering parameters

        # Placeholder for analytics implementation
        analytics_data = serialize_output_with_schema(
            PaymentAnalyticsResponse,
            {
                "total_payments": 0,
                "successful_payments": 0,
                "failed_payments": 0,
                "pending_payments": 0,
                "success_rate": 0.0,
                "total_amount": 0,
                "average_amount": 0,
                "total_collected": 0
            },
            "payment_status",
            from_orm=False
        )
        # Add extra field
        analytics_data['message'] = "Payment analytics not implemented yet"

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data=analytics_data
        )


# Initialize tools for easy import
payment_status_tool = PaymentStatusTool()
