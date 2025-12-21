"""
Complaint Formatting Utility
=============================
Centralized formatting for consistent presentation of complaints and resolutions.

Provides standardized formatting for:
- Complaint lists
- Complaint details
- Status updates
- Resolution summaries
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def format_complaint_list(
    complaints: List[Dict[str, Any]],
    include_status: bool = True,
    include_date: bool = True,
    numbered: bool = True,
    plain_text: bool = True
) -> str:
    """
    Format a list of complaints for display.

    Args:
        complaints: List of complaint dicts with keys: ticket_id, category, status, created_at
        include_status: Whether to show status
        include_date: Whether to show creation date
        numbered: Whether to use numbered list (True) or bullet points (False)
        plain_text: Whether to use plain text (True) or markdown with bold (False)

    Returns:
        Formatted string (plain text or markdown)

    Example (plain_text=True):
        1. Complaint #CMPL-001 - Food Quality (Open) - Jan 15, 2025
        2. Complaint #CMPL-002 - Service (Resolved) - Jan 14, 2025

    Example (plain_text=False):
        1. **Complaint #CMPL-001** - Food Quality (Open) - Jan 15, 2025
    """
    if not complaints:
        return "No complaints found."

    lines = []
    for idx, complaint in enumerate(complaints, 1):
        ticket_id = complaint.get("ticket_id") or complaint.get("complaint_ticket_id", "N/A")
        category = complaint.get("category", "Unknown")
        status = complaint.get("status", "unknown")
        created_at = complaint.get("created_at")

        # Build line
        prefix = f"{idx}. " if numbered else "- "

        # Format complaint ID
        id_formatted = f"Complaint #{ticket_id}" if plain_text else f"**Complaint #{ticket_id}**"
        line = f"{prefix}{id_formatted}"

        # Add category
        category_display = category.replace("_", " ").title()
        line += f" - {category_display}"

        # Add status
        if include_status:
            status_display = status.replace("_", " ").title()
            line += f" ({status_display})"

        # Add date
        if include_date and created_at:
            if isinstance(created_at, str):
                # Parse ISO datetime
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    date_str = dt.strftime("%b %d, %Y")
                except:
                    date_str = created_at[:10]  # Just take date part
            elif isinstance(created_at, datetime):
                date_str = created_at.strftime("%b %d, %Y")
            else:
                date_str = str(created_at)

            line += f" - {date_str}"

        lines.append(line)

    return "\n".join(lines)


def format_complaint_details(
    complaint: Dict[str, Any],
    include_resolution: bool = True,
    include_timestamps: bool = True,
    plain_text: bool = True
) -> str:
    """
    Format detailed complaint information.

    Args:
        complaint: Complaint dict with full details
        include_resolution: Whether to show resolution details
        include_timestamps: Whether to show timestamps
        plain_text: Whether to use plain text (True) or markdown with bold (False)

    Returns:
        Formatted string (plain text or markdown)

    Example (plain_text=True):
        Complaint #CMPL-001
        Category: Food Quality
        Priority: High
        Status: In Progress

        Description:
        The butter chicken was cold and the naan was burnt.

        Order: #ORD-123 (Jan 15, 2025)
        Created: Jan 15, 2025 at 7:30 PM
        Updated: Jan 15, 2025 at 8:15 PM

        Resolution:
        We sincerely apologize. We'll remake your order immediately.
    """
    ticket_id = complaint.get("ticket_id") or complaint.get("complaint_ticket_id", "N/A")
    category = complaint.get("category", "Unknown").replace("_", " ").title()
    priority = complaint.get("priority", "medium").title()
    status = complaint.get("status", "unknown").replace("_", " ").title()
    description = complaint.get("description", "No description provided")
    resolution = complaint.get("resolution")
    order_id = complaint.get("order_id")
    order_number = complaint.get("order_number")
    booking_id = complaint.get("booking_id")
    created_at = complaint.get("created_at")
    updated_at = complaint.get("updated_at")

    lines = []

    # Header
    header = f"Complaint #{ticket_id}" if plain_text else f"**Complaint #{ticket_id}**"
    lines.append(header)

    # Category and status
    category_label = "Category:" if plain_text else "**Category:**"
    priority_label = "Priority:" if plain_text else "**Priority:**"
    status_label = "Status:" if plain_text else "**Status:**"

    lines.append(f"{category_label} {category}")
    lines.append(f"{priority_label} {priority}")
    lines.append(f"{status_label} {status}")
    lines.append("")  # Empty line

    # Description
    desc_label = "Description:" if plain_text else "**Description:**"
    lines.append(desc_label)
    lines.append(description)
    lines.append("")  # Empty line

    # Order/Booking context
    if order_number:
        order_label = "Order:" if plain_text else "**Order:**"
        lines.append(f"{order_label} #{order_number}")
    elif order_id:
        order_label = "Order ID:" if plain_text else "**Order ID:**"
        lines.append(f"{order_label} {order_id}")

    if booking_id:
        booking_label = "Booking ID:" if plain_text else "**Booking ID:**"
        lines.append(f"{booking_label} {booking_id}")

    # Timestamps
    if include_timestamps:
        if created_at:
            created_label = "Created:" if plain_text else "**Created:**"
            created_str = _format_datetime(created_at)
            lines.append(f"{created_label} {created_str}")

        if updated_at and updated_at != created_at:
            updated_label = "Updated:" if plain_text else "**Updated:**"
            updated_str = _format_datetime(updated_at)
            lines.append(f"{updated_label} {updated_str}")

    # Resolution
    if include_resolution and resolution:
        lines.append("")  # Empty line
        resolution_label = "Resolution:" if plain_text else "**Resolution:**"
        lines.append(resolution_label)
        lines.append(resolution)

    return "\n".join(lines)


def format_status_update(
    old_status: str,
    new_status: str,
    resolution: Optional[str] = None,
    updated_by: Optional[str] = None,
    plain_text: bool = True
) -> str:
    """
    Format complaint status update message.

    Args:
        old_status: Previous status
        new_status: New status
        resolution: Resolution text (if status is resolved/closed)
        updated_by: Who updated the status
        plain_text: Whether to use plain text formatting

    Returns:
        Formatted update message

    Example:
        Status Updated: Open → In Progress

        Your complaint is now being reviewed by our team.
    """
    old_display = old_status.replace("_", " ").title()
    new_display = new_status.replace("_", " ").title()

    header = "Status Updated:" if plain_text else "**Status Updated:**"
    lines = [f"{header} {old_display} → {new_display}"]
    lines.append("")  # Empty line

    # Add contextual message based on new status
    if new_status == "in_progress":
        lines.append("Your complaint is now being reviewed by our team.")
    elif new_status == "resolved":
        lines.append("Your complaint has been resolved!")
        if resolution:
            lines.append("")
            resolution_label = "Resolution:" if plain_text else "**Resolution:**"
            lines.append(resolution_label)
            lines.append(resolution)
    elif new_status == "closed":
        lines.append("Your complaint has been closed. Thank you for your feedback!")
    elif new_status == "escalated":
        lines.append("Your complaint has been escalated to management for priority handling.")

    if updated_by:
        lines.append("")
        by_label = "Updated by:" if plain_text else "**Updated by:**"
        lines.append(f"{by_label} {updated_by}")

    return "\n".join(lines)


def format_complaint_confirmation(
    ticket_id: str,
    category: str,
    description: str,
    priority: str = "medium",
    estimated_response_time: Optional[str] = None,
    plain_text: bool = True
) -> str:
    """
    Format complaint confirmation message.

    Args:
        ticket_id: Complaint ticket ID
        category: Complaint category
        description: Brief description
        priority: Priority level
        estimated_response_time: When to expect response
        plain_text: Whether to use plain text formatting

    Returns:
        Formatted confirmation message

    Example:
        Complaint Submitted Successfully!

        Complaint ID: #CMPL-001
        Category: Food Quality
        Priority: High

        We've received your complaint and will address it promptly.
        Expected response: Within 2 hours
    """
    header = "Complaint Submitted Successfully!" if plain_text else "**Complaint Submitted Successfully!**"
    lines = [header, ""]

    id_label = "Complaint ID:" if plain_text else "**Complaint ID:**"
    category_label = "Category:" if plain_text else "**Category:**"
    priority_label = "Priority:" if plain_text else "**Priority:**"

    lines.append(f"{id_label} #{ticket_id}")
    lines.append(f"{category_label} {category.replace('_', ' ').title()}")
    lines.append(f"{priority_label} {priority.title()}")
    lines.append("")

    lines.append("We've received your complaint and will address it promptly.")

    if estimated_response_time:
        lines.append(f"Expected response: {estimated_response_time}")
    else:
        # Default response times based on priority
        if priority == "critical":
            lines.append("Expected response: Immediate")
        elif priority == "high":
            lines.append("Expected response: Within 2 hours")
        elif priority == "medium":
            lines.append("Expected response: Within 24 hours")
        else:
            lines.append("Expected response: Within 48 hours")

    return "\n".join(lines)


def _format_datetime(dt: Any) -> str:
    """Helper to format datetime consistently."""
    if isinstance(dt, str):
        try:
            dt_obj = datetime.fromisoformat(dt.replace('Z', '+00:00'))
            return dt_obj.strftime("%b %d, %Y at %I:%M %p")
        except:
            return dt
    elif isinstance(dt, datetime):
        return dt.strftime("%b %d, %Y at %I:%M %p")
    else:
        return str(dt)


__all__ = [
    "format_complaint_list",
    "format_complaint_details",
    "format_status_update",
    "format_complaint_confirmation"
]
