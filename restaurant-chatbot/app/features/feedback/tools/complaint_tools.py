"""
Complaint Tools
===============
Tools for complaint submission, tracking, and management.
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool

from app.tools.database.satisfaction_tools import (
    CreateComplaintTool,
    UpdateComplaintTool,
    GetComplaintTool,
    GetUserComplaintsTool
)
from app.tools.base.tool_base import ToolStatus


@tool
async def create_complaint(
    user_id: str,
    description: str,
    category: str,
    priority: str = "medium",
    order_id: Optional[str] = None,
    booking_id: Optional[str] = None,
    phone_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new customer complaint.

    Categories: food_quality, service, cleanliness, wait_time, billing, other
    Priority: low, medium, high, critical

    Args:
        user_id: Customer's user ID
        description: Detailed description of the issue
        category: Complaint category
        priority: Priority level (default: medium)
        order_id: Optional order ID
        booking_id: Optional booking ID
        phone_number: Optional phone for SMS notification

    Returns:
        Dict with complaint_id, ticket_id, status, message
    """
    complaint_tool = CreateComplaintTool()

    result = await complaint_tool.execute(
        user_id=user_id,
        description=description,
        category=category,
        priority=priority,
        order_id=order_id,
        booking_id=booking_id
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to create complaint"
        }

    return {
        "success": True,
        "complaint_id": result.data.get("complaint_id"),
        "ticket_id": result.data.get("ticket_id"),
        "status": result.data.get("status", "open"),
        "priority": result.data.get("priority"),
        "message": f"Complaint #{result.data.get('ticket_id')} created with {priority} priority. We'll address this promptly."
    }


@tool
async def update_complaint_status(
    complaint_id: str,
    status: Optional[str] = None,
    resolution: Optional[str] = None,
    compensation_offered: Optional[str] = None,
    updated_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update complaint status or resolution.

    Status values: open, in_progress, resolved, closed, escalated

    Args:
        complaint_id: ID of the complaint
        status: New status
        resolution: Resolution details
        compensation_offered: Compensation description
        updated_by: Who updated the complaint

    Returns:
        Dict with updated complaint details
    """
    update_tool = UpdateComplaintTool()

    result = await update_tool.execute(
        complaint_id=complaint_id,
        status=status,
        resolution=resolution,
        compensation_offered=compensation_offered
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to update complaint"
        }

    return {
        "success": True,
        "complaint_id": complaint_id,
        "status": result.data.get("status"),
        "resolution": result.data.get("resolution"),
        "message": f"Complaint status updated to: {result.data.get('status')}"
    }


@tool
async def get_complaint_details(complaint_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific complaint.

    Args:
        complaint_id: ID of the complaint

    Returns:
        Dict with complete complaint details
    """
    get_tool = GetComplaintTool()

    result = await get_tool.execute(complaint_id=complaint_id)

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Complaint not found"
        }

    return {
        "success": True,
        "complaint": result.data
    }


@tool
async def get_user_complaints(
    user_id: str,
    status: Optional[str] = None,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Get list of user's complaints.

    Args:
        user_id: Customer's user ID
        status: Filter by status (optional)
        limit: Maximum number of complaints to return

    Returns:
        Dict with list of complaints
    """
    list_tool = GetUserComplaintsTool()

    result = await list_tool.execute(
        user_id=user_id,
        status=status,
        limit=limit
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to retrieve complaints"
        }

    complaints = result.data.get("complaints", [])

    return {
        "success": True,
        "complaints": complaints,
        "count": len(complaints),
        "message": f"Found {len(complaints)} complaint(s)"
    }


@tool
async def escalate_complaint(
    complaint_id: str,
    escalation_reason: str
) -> Dict[str, Any]:
    """
    Escalate a complaint to management.

    Marks complaint as escalated and assigns to management team.

    Args:
        complaint_id: ID of the complaint to escalate
        escalation_reason: Reason for escalation

    Returns:
        Dict with escalation confirmation
    """
    update_tool = UpdateComplaintTool()

    result = await update_tool.execute(
        complaint_id=complaint_id,
        status="escalated",
        escalated_to="management",
        resolution=f"Escalated to management: {escalation_reason}"
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to escalate complaint"
        }

    return {
        "success": True,
        "complaint_id": complaint_id,
        "message": "Complaint has been escalated to management. You will be contacted within 24 hours."
    }


@tool
async def get_user_recent_orders(
    user_id: Optional[str] = None,
    phone_number: Optional[str] = None,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Get user's recent orders to help identify which order they're complaining about.

    Retrieves recent orders for a user so they can describe which one had issues.
    Returns order details including items, date, and order number.

    Args:
        user_id: User's ID (from state if authenticated)
        phone_number: User's phone number (if user_id not available)
        limit: Number of recent orders to retrieve (default 5)

    Returns:
        Dict with list of recent orders including order_number, items, date, total
    """
    from datetime import datetime, timezone
    from sqlalchemy import select, and_, desc
    from app.core.database import db_manager
    # from app.shared.models import Order, User, OrderItem, MenuItem
    from app.shared.models import User
    from app.features.food_ordering.models import Order, OrderItem, MenuItem
    from sqlalchemy.orm import selectinload

    try:
        # Get user_id from phone_number if not provided
        if not user_id and phone_number:
            async with db_manager.get_session() as session:
                user_query = select(User).where(User.phone_number == phone_number)
                user_result = await session.execute(user_query)
                user = user_result.scalar_one_or_none()

                if not user:
                    return {
                        "success": False,
                        "message": f"No account found with phone number {phone_number}. Have you ordered with us before?"
                    }

                user_id = user.id

        if not user_id:
            return {
                "success": False,
                "message": "Please provide either user_id or phone_number"
            }

        # Get recent orders
        async with db_manager.get_session() as session:
            orders_query = select(Order).options(
                selectinload(Order.order_items).selectinload(OrderItem.menu_item)
            ).where(
                Order.user_id == user_id
            ).order_by(
                desc(Order.created_at)
            ).limit(limit)

            result = await session.execute(orders_query)
            orders = result.scalars().all()

            if not orders:
                return {
                    "success": True,
                    "total_orders": 0,
                    "orders": [],
                    "message": "No previous orders found for this account"
                }

            # Format orders
            orders_list = []
            for order in orders:
                items_list = []
                for item in order.order_items:
                    items_list.append({
                        "name": item.menu_item.name if item.menu_item else "Unknown Item",
                        "quantity": item.quantity,
                        "price": float(item.unit_price) if item.unit_price else 0
                    })

                orders_list.append({
                    "order_number": order.order_number,
                    "order_id": order.id,
                    "date": order.created_at.strftime("%B %d, %Y at %I:%M %p"),
                    "items": items_list,
                    "total": float(order.total_amount),
                    "status": order.status,
                    "order_type": order.order_type
                })

            return {
                "success": True,
                "total_orders": len(orders_list),
                "orders": orders_list,
                "message": f"Found {len(orders_list)} recent order(s)"
            }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to retrieve orders: {str(e)}",
            "orders": []
        }


__all__ = [
    "create_complaint",
    "update_complaint_status",
    "get_complaint_details",
    "get_user_complaints",
    "escalate_complaint",
    "get_user_recent_orders"
]
