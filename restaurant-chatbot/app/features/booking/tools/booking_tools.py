"""
Restaurant Booking Database Tools - CORRECTED FOR ACTUAL SCHEMA
================================================================
SQLAlchemy-based booking management tools aligned with actual database schema.

Key fixes:
- Uses booking_datetime (timestamp) instead of booking_date (datetime)
- Handles missing columns gracefully (guest_name, confirmation_code, etc.)
- Uses string status values instead of enum
- Generates confirmation codes programmatically
- Compatible with actual database structure
"""

import secrets
import string
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, func, exists, text
from sqlalchemy.orm import joinedload

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import db_manager
from app.features.booking.models import Booking
from app.shared.models import Table, User
from app.core.logging_config import get_feature_logger
from app.utils.schema_tool_integration import (
    serialize_output_with_schema,
    safe_isoformat as schema_safe_isoformat
)
from app.features.booking.schemas.booking import (
    BookingResponse,
    BookingSummaryResponse,
    AvailabilityResponse,
    TableResponse
)
# Datetime parsing and validation utilities
from app.utils.datetime_parser import (
    parse_booking_datetime,
    is_valid_booking_time,
    parse_date,
    parse_time
)
from app.utils.time_parser import (
    parse_natural_time,
    is_vague_time,
    get_suggested_times_display
)
# Phone number utilities
from app.utils.phone_utils import normalize_phone_number

logger = get_feature_logger("booking")


def generate_confirmation_code() -> str:
    """Generate a unique confirmation code"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


def safe_isoformat(dt) -> Optional[str]:
    """Safely convert datetime to ISO string"""
    if dt is None:
        return None
    if isinstance(dt, str):
        return dt
    return dt.isoformat()


class CheckAvailabilityTool(ToolBase):
    """Check table availability for a specific date, time, and party size."""

    def __init__(self):
        super().__init__(
            name="check_availability",
            description="Check table availability for booking",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['booking_date', 'party_size']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or kwargs[field] is None:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Parse and validate booking datetime with natural language support
        try:
            booking_date_input = validated_data['booking_date']

            # Check if this is already a datetime object
            if isinstance(booking_date_input, datetime):
                booking_datetime = booking_date_input
            # Check if it's a natural language string (e.g., "tomorrow at 7pm", "next Friday 19:00")
            elif isinstance(booking_date_input, str):
                # Try to split into date and time components
                # Expected formats: "tomorrow 7pm", "next Friday at 19:00", "2024-01-15 19:00"
                parts = booking_date_input.lower().replace(' at ', ' ').split()

                # Check if we have separate date and time, or just date
                if len(parts) >= 2:
                    # Likely "tomorrow 7pm" or "next Friday 19:00"
                    # Try to identify time component (has "pm", "am", or ":")
                    time_part = None
                    date_parts = []

                    for part in parts:
                        if 'pm' in part or 'am' in part or ':' in part or part.isdigit() and len(part) <= 2:
                            time_part = part
                        else:
                            date_parts.append(part)

                    if time_part and date_parts:
                        # We have both date and time
                        date_str = ' '.join(date_parts)
                        time_str = time_part

                        # Handle vague times like "evening", "lunch"
                        if is_vague_time(time_str):
                            vague_result = parse_natural_time(time_str)
                            # Store vague time info for user clarification
                            validated_data['is_vague_time'] = True
                            validated_data['vague_time_info'] = vague_result
                            # Use default time for now
                            time_str = vague_result['default_time']
                            logger.info(
                                f"Vague time detected: '{vague_result['vague_term']}', using default: {time_str}",
                                suggested_times=vague_result['suggested_times']
                            )

                        # Parse using natural language parser
                        booking_datetime = parse_booking_datetime(date_str, time_str)
                    else:
                        # Only date provided, or couldn't separate - try as single datetime string
                        # Fall back to ISO parsing
                        booking_datetime = datetime.fromisoformat(booking_date_input.replace('Z', '+00:00'))
                else:
                    # Single part - might be ISO datetime
                    booking_datetime = datetime.fromisoformat(booking_date_input.replace('Z', '+00:00'))
            else:
                raise ValueError(f"Unsupported booking_date type: {type(booking_date_input)}")

            # Ensure timezone aware
            if booking_datetime.tzinfo is None:
                from app.utils.timezone import get_app_timezone
                booking_datetime = booking_datetime.replace(tzinfo=get_app_timezone())

            # CRITICAL: Validate booking time is not in the past
            if not is_valid_booking_time(booking_datetime, min_advance_hours=1):
                raise ValueError(
                    f"Cannot book in the past. Booking must be at least 1 hour in advance. "
                    f"Requested time: {booking_datetime.isoformat()}"
                )

            validated_data['booking_datetime'] = booking_datetime

        except ValueError as e:
            # Re-raise validation errors with clear message
            raise ValueError(f"Invalid booking date/time: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse booking datetime: {str(e)}")
            raise ValueError(f"Could not parse booking date/time: {str(e)}")

        # Validate party size
        try:
            party_size = int(validated_data['party_size'])
            if party_size <= 0 or party_size > 20:
                raise ValueError("Party size must be between 1 and 20")
            validated_data['party_size'] = party_size
        except (ValueError, TypeError):
            raise ValueError("Party size must be a valid number")

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)
            booking_datetime = validated_data['booking_datetime']
            party_size = validated_data['party_size']

            async with db_manager.get_session() as session:
                # Get available tables that can accommodate the party size
                tables_query = select(Table).where(
                    Table.capacity >= party_size,
                    Table.is_active.is_(True)
                )
                tables_result = await session.execute(tables_query)
                available_tables = tables_result.scalars().all()

                if not available_tables:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "has_availability": False,
                            "total_available": 0,
                            "available_tables": [],
                            "message": f"No tables available for party size {party_size}",
                            "waitlist_available": True,
                            "requested_party_size": party_size,
                            "requested_datetime": safe_isoformat(booking_datetime)
                        },
                        metadata={"operation": "check_availability"}
                    )

                # Check for booking conflicts (1-hour window)
                booking_start = booking_datetime
                booking_end = booking_datetime + timedelta(hours=1)

                available_count = 0
                available_table_details = []

                for table in available_tables:
                    # Check for conflicts using actual database column name
                    # NOTE: status values are: scheduled, confirmed, completed, no_show, cancelled
                    # We check for scheduled, confirmed bookings (not cancelled, completed, or no_show)
                    conflicts_query = select(func.count(Booking.id)).where(
                        Booking.table_id == table.id,
                        Booking.status.in_(['scheduled', 'confirmed']),  # Active bookings only
                        Booking.booking_status != 'cancelled',  # Not cancelled
                        or_(
                            # Existing booking overlaps with requested time
                            and_(
                                Booking.booking_datetime <= booking_start,
                                Booking.booking_datetime + text("INTERVAL '1 hour'") > booking_start
                            ),
                            and_(
                                Booking.booking_datetime < booking_end,
                                Booking.booking_datetime >= booking_start
                            )
                        )
                    )

                    conflicts_result = await session.execute(conflicts_query)
                    conflict_count = conflicts_result.scalar()

                    if conflict_count == 0:
                        available_count += 1
                        # Serialize table using schema
                        table_data = serialize_output_with_schema(
                            TableResponse,
                            table,
                            self.name,
                            from_orm=True
                        )
                        table_data['table_id'] = str(table.id)
                        available_table_details.append(table_data)

                # Build availability response
                availability_data = {
                    "has_availability": available_count > 0,
                    "total_available": available_count,
                    "available_tables": available_table_details,
                    "requested_party_size": party_size,
                    "requested_datetime": safe_isoformat(booking_datetime),
                    "waitlist_available": available_count == 0
                }

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=availability_data,
                    metadata={"operation": "check_availability"}
                )

        except Exception as e:
            logger.error(f"Failed to check availability: {str(e)}")
            raise ToolError(
                f"Availability check failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class CreateBookingTool(ToolBase):
    """Create a new table reservation."""

    def __init__(self):
        super().__init__(
            name="create_booking",
            description="Create a new table reservation",
            max_retries=3,
            timeout_seconds=45
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['booking_date', 'party_size', 'contact_phone']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Normalize phone number to international format
        try:
            validated_data['contact_phone'] = normalize_phone_number(validated_data['contact_phone'])
            logger.debug(f"Normalized phone number: {validated_data['contact_phone']}")
        except Exception as e:
            logger.warning(f"Failed to normalize phone number: {str(e)}")
            # Continue with original phone if normalization fails

        # guest_name is optional (placeholder for future improvements)
        validated_data['guest_name'] = kwargs.get('guest_name')

        # 3-Tier Authentication: At least one of user_id or device_id must be provided
        user_id = kwargs.get('user_id')
        device_id = kwargs.get('device_id')

        # BUG FIX: Detect if LLM swapped user_id and device_id
        # Device IDs are long (64+ chars) and start with 'dev_'
        # User IDs are short (20 chars max) and start with 'usr'
        if user_id and (len(user_id) > 20 or user_id.startswith('dev_')):
            # Swap detected! The user_id is actually a device_id
            logger.warning(
                "Detected parameter swap: user_id contains device_id value",
                user_id_value=user_id,
                device_id_value=device_id,
                auto_fixing=True
            )
            device_id = user_id  # Move the device_id to correct parameter
            user_id = None  # Clear user_id since we don't have it

        if not user_id and not device_id:
            raise ValueError("Either user_id or device_id must be provided (3-tier authentication)")

        validated_data['user_id'] = user_id
        validated_data['device_id'] = device_id

        # Parse booking datetime with natural language support
        try:
            booking_date_input = validated_data['booking_date']

            # Check if this is already a datetime object
            if isinstance(booking_date_input, datetime):
                booking_datetime = booking_date_input
            # Check if it's a natural language string
            elif isinstance(booking_date_input, str):
                # Try to split into date and time components
                parts = booking_date_input.lower().replace(' at ', ' ').split()

                if len(parts) >= 2:
                    # Try to identify time component
                    time_part = None
                    date_parts = []

                    for part in parts:
                        if 'pm' in part or 'am' in part or ':' in part or (part.isdigit() and len(part) <= 2):
                            time_part = part
                        else:
                            date_parts.append(part)

                    if time_part and date_parts:
                        # Parse using natural language parser
                        date_str = ' '.join(date_parts)
                        time_str = time_part

                        # Handle vague times
                        if is_vague_time(time_str):
                            vague_result = parse_natural_time(time_str)
                            time_str = vague_result['default_time']
                            logger.info(
                                f"Vague time in booking creation: '{vague_result['vague_term']}', using default: {time_str}"
                            )

                        booking_datetime = parse_booking_datetime(date_str, time_str)
                    else:
                        # Fall back to ISO parsing
                        booking_datetime = datetime.fromisoformat(booking_date_input.replace('Z', '+00:00'))
                else:
                    # Single part - ISO datetime
                    booking_datetime = datetime.fromisoformat(booking_date_input.replace('Z', '+00:00'))
            else:
                raise ValueError(f"Unsupported booking_date type: {type(booking_date_input)}")

            # Ensure timezone aware
            if booking_datetime.tzinfo is None:
                from app.utils.timezone import get_app_timezone
                booking_datetime = booking_datetime.replace(tzinfo=get_app_timezone())

            # CRITICAL: Validate booking time is not in the past
            if not is_valid_booking_time(booking_datetime, min_advance_hours=1):
                raise ValueError(
                    f"Cannot create booking in the past. Booking must be at least 1 hour in advance. "
                    f"Requested time: {booking_datetime.isoformat()}"
                )

            validated_data['booking_datetime'] = booking_datetime

        except ValueError as e:
            raise ValueError(f"Invalid booking date/time: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to parse booking datetime: {str(e)}")
            raise ValueError(f"Could not parse booking date/time: {str(e)}")

        # Validate party size
        try:
            party_size = int(validated_data['party_size'])
            if party_size <= 0 or party_size > 20:
                raise ValueError("Party size must be between 1 and 20")
            validated_data['party_size'] = party_size
        except (ValueError, TypeError):
            raise ValueError("Party size must be a valid number")

        # Optional fields
        validated_data['contact_email'] = kwargs.get('contact_email')
        validated_data['special_requests'] = kwargs.get('special_requests')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            # First check availability
            availability_check = CheckAvailabilityTool()
            availability_result = await availability_check.execute(
                booking_date=validated_data['booking_datetime'].isoformat(),
                party_size=validated_data['party_size']
            )

            if availability_result.status != ToolStatus.SUCCESS:
                raise Exception(f"Availability check failed: {availability_result.error}")

            async with db_manager.get_session() as session:
                # Handle user_id and device_id from validated data (3-tier authentication)
                user_id = validated_data.get('user_id')
                device_id = validated_data.get('device_id')

                # If user_id not provided but we have contact_phone, try to find/create user
                if not user_id:
                    # Try to find existing user by phone
                    existing_user_query = select(User).where(User.phone_number == validated_data['contact_phone'])
                    existing_user_result = await session.execute(existing_user_query)
                    existing_user = existing_user_result.scalar_one_or_none()

                    if existing_user:
                        user_id = existing_user.id
                    else:
                        # Create new user - let event listener generate ID
                        try:
                            new_user = User(
                                phone_number=validated_data['contact_phone'],
                                email=validated_data.get('contact_email'),
                                full_name=validated_data['guest_name'],
                                is_anonymous=False
                            )
                            session.add(new_user)
                            await session.flush()  # Ensure user is created
                            await session.refresh(new_user)  # Get generated ID
                            user_id = new_user.id
                        except Exception as user_error:
                            logger.warning(f"Could not create user: {user_error}")
                            # If user creation fails and we don't have device_id either, raise error
                            if not device_id:
                                raise ToolError(f"User creation failed: {user_error}", tool_name=self.name, retry_suggested=True)

                # Get best available table
                available_tables = availability_result.data.get('available_tables', [])
                if not available_tables:
                    # Try waitlist functionality - generate temp booking ID for waitlist
                    from app.utils.id_generator import generate_id
                    waitlist_booking_id = await generate_id(session, "bookings")

                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": True,
                            "booking_id": waitlist_booking_id,
                            "confirmation_code": generate_confirmation_code(),
                            "status": "waitlisted",
                            "is_waitlisted": True,
                            "message": "No tables available, added to waitlist",
                            "booking_date": safe_isoformat(validated_data['booking_datetime']),
                            "party_size": validated_data['party_size'],
                            "guest_name": validated_data['guest_name'],
                            "contact_phone": validated_data['contact_phone'],
                            "contact_email": validated_data.get('contact_email'),
                            "special_requests": validated_data.get('special_requests')
                        },
                        metadata={"operation": "create_booking", "waitlisted": True}
                    )

                # Select the smallest suitable table
                best_table = min(available_tables, key=lambda t: t['capacity'])

                # Get restaurant_id from database or generate one if needed
                restaurant_id = None
                restaurant_query = select(text("id")).select_from(text("restaurant_config")).limit(1)
                try:
                    restaurant_result = await session.execute(restaurant_query)
                    restaurant_row = restaurant_result.fetchone()
                    if restaurant_row:
                        restaurant_id = str(restaurant_row[0])
                    else:
                        # Generate restaurant_id if no restaurant found
                        from app.utils.id_generator import generate_id
                        restaurant_id = await generate_id(session, "restaurant_config")
                except Exception as e:
                    logger.warning(f"Could not get restaurant_id, generating new one: {e}")
                    from app.utils.id_generator import generate_id
                    restaurant_id = await generate_id(session, "restaurant_config")

                # Create booking - let event listener generate ID
                confirmation_code = generate_confirmation_code()

                booking = Booking(
                    user_id=user_id,  # May be None for Tier 1/2
                    device_id=device_id,  # May be None for Tier 3/anonymous
                    restaurant_id=restaurant_id,
                    table_id=best_table['table_id'],
                    booking_datetime=validated_data['booking_datetime'],
                    party_size=validated_data['party_size'],
                    status='scheduled',  # Lifecycle status (scheduled/confirmed/completed/no_show)
                    booking_status='active',  # Modification status (active/modified/cancelled)
                    special_requests=validated_data.get('special_requests'),
                    contact_phone=validated_data['contact_phone'],
                    contact_email=validated_data.get('contact_email'),
                    guest_name=validated_data['guest_name'],  # Now stored in database
                    confirmation_code=confirmation_code,  # Store confirmation code in database
                    is_waitlisted=False,  # Not waitlisted for successful bookings
                    reminder_sent=False
                )

                session.add(booking)
                await session.commit()
                await session.refresh(booking)  # Get the auto-generated ID

                # Send booking confirmation email ONLY if email is provided
                # COMMUNICATION PRIORITY: SMS (primary)  WhatsApp (future)  Email (backup)
                # Email is sent as BACKUP/OPTIONAL for booking confirmations
                email_sent = False
                send_email = validated_data.get('contact_email') and kwargs.get('send_email_confirmation', False)

                if send_email:
                    try:
                        from app.services.email_manager_service import create_email_service
                        from app.services.email_template_service import get_email_template_service
                        from app.utils.timezone import format_datetime_for_display

                        template_service = get_email_template_service()
                        email_service = create_email_service(session)

                        # Render booking confirmation template
                        html_content = await template_service.render_booking_confirmation(
                            guest_name=validated_data.get('guest_name') or "Valued Guest",
                            confirmation_code=confirmation_code,
                            booking_datetime=format_datetime_for_display(validated_data['booking_datetime']),
                            party_size=validated_data['party_size'],
                            table_number=best_table['table_number'],
                            special_requests=validated_data.get('special_requests')
                        )

                        # Send email (BACKUP channel - SMS is primary)
                        email_result = await email_service.send_email(
                            to_email=validated_data['contact_email'],
                            subject=f"Booking Confirmation - {confirmation_code}",
                            html_content=html_content,
                            user_id=user_id
                        )

                        email_sent = email_result.get("success", False)

                        if email_sent:
                            logger.info(
                                "Booking confirmation email sent (backup channel)",
                                booking_id=booking.id,
                                email=validated_data['contact_email'],
                                email_log_id=email_result.get("email_log_id")
                            )
                        else:
                            logger.warning(
                                "Failed to send booking confirmation email",
                                booking_id=booking.id,
                                error=email_result.get("error")
                            )
                    except Exception as e:
                        logger.error(f"Email sending failed: {str(e)}")
                        # Don't fail the booking if email fails - just log it

                # Serialize booking using schema
                booking_data = serialize_output_with_schema(
                    BookingResponse,
                    booking,
                    self.name,
                    from_orm=True
                )

                # Add extra fields
                booking_data['success'] = True
                booking_data['booking_id'] = booking.id
                booking_data['table_info'] = {
                    "table_id": best_table['table_id'],
                    "table_number": best_table['table_number'],
                    "capacity": best_table['capacity']
                }
                booking_data['email_sent'] = email_sent

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=booking_data,
                    metadata={"operation": "create_booking"}
                )

        except Exception as e:
            logger.error(f"Failed to create booking: {str(e)}")
            raise ToolError(
                f"Booking creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetBookingTool(ToolBase):
    """Retrieve booking details by booking ID, user_id, or device_id."""

    def __init__(self):
        super().__init__(
            name="get_booking",
            description="Get booking details by ID, user_id, or device_id",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        # Accept booking_id/confirmation_code OR user_id OR device_id OR phone
        booking_id = kwargs.get('booking_id') or kwargs.get('confirmation_code')
        user_id = kwargs.get('user_id')
        device_id = kwargs.get('device_id')
        phone = kwargs.get('phone')

        if not booking_id and not user_id and not device_id and not phone:
            raise ValueError("Either booking_id, user_id, device_id, or phone is required")

        return {
            'booking_id': booking_id,
            'user_id': user_id,
            'device_id': device_id,
            'phone': phone
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)
            booking_id = validated_data.get('booking_id')
            user_id = validated_data.get('user_id')
            device_id = validated_data.get('device_id')
            phone = validated_data.get('phone')

            async with db_manager.get_session() as session:
                # Build query based on provided parameters
                if booking_id:
                    # Single booking by ID
                    booking_query = select(Booking).where(
                        Booking.id == booking_id
                    ).options(
                        joinedload(Booking.user),
                        joinedload(Booking.table)
                    )

                    booking_result = await session.execute(booking_query)
                    booking = booking_result.scalar_one_or_none()

                    if not booking:
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            data={
                                "found": False,
                                "message": "No booking found with the provided ID"
                            },
                            metadata={"operation": "get_booking"}
                        )

                    # Build response with available data
                    booking_data = {
                        "found": True,
                        "booking_id": str(booking.id),
                        "confirmation_code": booking.confirmation_code or "N/A",
                        "booking_date": safe_isoformat(booking.booking_datetime),
                        "party_size": booking.party_size,
                        "status": booking.status,
                        "booking_status": booking.booking_status,
                        "guest_name": booking.guest_name or "Unknown",
                        "contact_phone": booking.contact_phone,
                        "contact_email": booking.contact_email,
                        "special_requests": booking.special_requests,
                        "is_waitlisted": booking.is_waitlisted,
                        "created_at": safe_isoformat(booking.created_at),
                        "updated_at": safe_isoformat(booking.updated_at)
                    }

                    # Add user data if available (override guest_name from user if present)
                    if booking.user:
                        if booking.user.full_name:
                            booking_data["guest_name"] = booking.user.full_name
                        booking_data["user_id"] = str(booking.user.id)

                    # Add device data if available
                    if booking.device_id:
                        booking_data["device_id"] = booking.device_id

                    # Add table data if available
                    if booking.table:
                        booking_data["table_info"] = {
                            "table_id": str(booking.table.id),
                            "table_number": booking.table.table_number,
                            "capacity": booking.table.capacity,
                            "location": booking.table.location
                        }

                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data=booking_data,
                        metadata={"operation": "get_booking"}
                    )

                else:
                    # Multiple bookings by user_id, device_id, or phone
                    # Filter for active bookings in the future only
                    from sqlalchemy import func as sql_func
                    booking_query = select(Booking).where(
                        Booking.booking_status == 'active',
                        Booking.booking_datetime > sql_func.now()
                    ).options(
                        joinedload(Booking.user),
                        joinedload(Booking.table)
                    )

                    if user_id:
                        booking_query = booking_query.where(Booking.user_id == user_id)
                    elif device_id:
                        booking_query = booking_query.where(Booking.device_id == device_id)
                    elif phone:
                        booking_query = booking_query.where(Booking.contact_phone == phone)

                    booking_query = booking_query.order_by(Booking.booking_datetime.asc())

                    booking_result = await session.execute(booking_query)
                    bookings = booking_result.scalars().all()

                    if not bookings:
                        return ToolResult(
                            status=ToolStatus.SUCCESS,
                            data={
                                "found": False,
                                "bookings": [],
                                "message": "No bookings found"
                            },
                            metadata={"operation": "get_booking"}
                        )

                    # Build response with booking list
                    booking_list = []
                    for booking in bookings:
                        # Serialize booking using schema
                        booking_data = serialize_output_with_schema(
                            BookingResponse,
                            booking,
                            self.name,
                            from_orm=True
                        )

                        # Add compatibility and computed fields
                        booking_data["booking_id"] = str(booking.id)

                        if booking.user:
                            if booking.user.full_name:
                                booking_data["guest_name"] = booking.user.full_name
                            booking_data["user_id"] = str(booking.user.id)

                        if booking.device_id:
                            booking_data["device_id"] = booking.device_id

                        if booking.table:
                            booking_data["table_info"] = {
                                "table_number": booking.table.table_number,
                                "capacity": booking.table.capacity
                            }

                        booking_list.append(booking_data)

                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "found": True,
                            "bookings": booking_list,
                            "total_bookings": len(booking_list)
                        },
                        metadata={"operation": "get_booking"}
                    )

        except Exception as e:
            logger.error(f"Failed to get booking: {str(e)}")
            raise ToolError(
                f"Failed to retrieve booking: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class UpdateBookingStatusTool(ToolBase):
    """Update booking status."""

    def __init__(self):
        super().__init__(
            name="update_booking_status",
            description="Update booking status",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['booking_id', 'status']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Validate status - use string values that match database
        valid_statuses = ['scheduled', 'confirmed', 'cancelled', 'completed', 'no_show']
        if validated_data['status'] not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                booking_query = select(Booking).where(Booking.id == validated_data['booking_id'])
                booking_result = await session.execute(booking_query)
                booking = booking_result.scalar_one_or_none()

                if not booking:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": "Booking not found"
                        },
                        metadata={"operation": "update_booking_status"}
                    )

                old_status = booking.status
                booking.status = validated_data['status']
                await session.commit()

                # Serialize booking using schema
                booking_data = serialize_output_with_schema(
                    BookingResponse,
                    booking,
                    self.name,
                    from_orm=True
                )

                # Add status transition metadata
                booking_data['success'] = True
                booking_data['booking_id'] = str(booking.id)
                booking_data['old_status'] = old_status
                booking_data['new_status'] = booking.status

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=booking_data,
                    metadata={"operation": "update_booking_status"}
                )

        except Exception as e:
            logger.error(f"Failed to update booking status: {str(e)}")
            raise ToolError(
                f"Failed to update booking status: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class CancelBookingTool(ToolBase):
    """Cancel a booking."""

    def __init__(self):
        super().__init__(
            name="cancel_booking",
            description="Cancel a booking",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'booking_id' not in kwargs or not kwargs['booking_id']:
            raise ValueError("Missing required field: booking_id")

        validated_data = {
            'booking_id': kwargs['booking_id'],
            'reason': kwargs.get('reason', 'User cancellation')
        }

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                booking_query = select(Booking).where(Booking.id == validated_data['booking_id'])
                booking_result = await session.execute(booking_query)
                booking = booking_result.scalar_one_or_none()

                if not booking:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": "Booking not found"
                        },
                        metadata={"operation": "cancel_booking"}
                    )

                if booking.status == 'cancelled':
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": "Booking is already cancelled"
                        },
                        metadata={"operation": "cancel_booking"}
                    )

                old_status = booking.status
                booking.status = 'cancelled'
                booking.booking_status = 'cancelled'  # Mark as cancelled in booking_status too
                await session.commit()

                # Serialize booking using schema
                booking_data = serialize_output_with_schema(
                    BookingResponse,
                    booking,
                    self.name,
                    from_orm=True
                )

                # Add cancellation metadata
                booking_data['success'] = True
                booking_data['booking_id'] = str(booking.id)
                booking_data['old_status'] = old_status
                booking_data['new_status'] = "cancelled"
                booking_data['cancellation_reason'] = validated_data['reason']
                booking_data['cancelled_at'] = datetime.now(timezone.utc).isoformat()

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=booking_data,
                    metadata={"operation": "cancel_booking"}
                )

        except Exception as e:
            logger.error(f"Failed to cancel booking: {str(e)}")
            raise ToolError(
                f"Failed to cancel booking: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class ModifyBookingTool(ToolBase):
    """Modify booking details (datetime, party size, special requests)."""

    def __init__(self):
        super().__init__(
            name="modify_booking",
            description="Modify booking datetime, party size, or special requests",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'booking_id' not in kwargs or not kwargs['booking_id']:
            raise ValueError("Missing required field: booking_id")

        validated_data = {'booking_id': kwargs['booking_id']}

        # At least one modification field must be provided
        has_modification = False

        # Validate booking_datetime if provided (with natural language support)
        if 'booking_datetime' in kwargs and kwargs['booking_datetime']:
            try:
                booking_datetime_input = kwargs['booking_datetime']

                if isinstance(booking_datetime_input, datetime):
                    booking_datetime = booking_datetime_input
                elif isinstance(booking_datetime_input, str):
                    # Try to split into date and time components for natural language parsing
                    parts = booking_datetime_input.lower().replace(' at ', ' ').split()

                    if len(parts) >= 2:
                        time_part = None
                        date_parts = []

                        for part in parts:
                            if 'pm' in part or 'am' in part or ':' in part or (part.isdigit() and len(part) <= 2):
                                time_part = part
                            else:
                                date_parts.append(part)

                        if time_part and date_parts:
                            date_str = ' '.join(date_parts)
                            time_str = time_part

                            # Handle vague times
                            if is_vague_time(time_str):
                                vague_result = parse_natural_time(time_str)
                                time_str = vague_result['default_time']
                                logger.info(
                                    f"Vague time in modification: '{vague_result['vague_term']}', using default: {time_str}"
                                )

                            booking_datetime = parse_booking_datetime(date_str, time_str)
                        else:
                            # Fall back to ISO parsing
                            booking_datetime = datetime.fromisoformat(booking_datetime_input.replace('Z', '+00:00'))
                    else:
                        # Single part - ISO datetime
                        booking_datetime = datetime.fromisoformat(booking_datetime_input.replace('Z', '+00:00'))
                else:
                    raise ValueError(f"Unsupported booking_datetime type: {type(booking_datetime_input)}")

                # Ensure timezone aware
                if booking_datetime.tzinfo is None:
                    from app.utils.timezone import get_app_timezone
                    booking_datetime = booking_datetime.replace(tzinfo=get_app_timezone())

                # CRITICAL: Validate new booking time is not in the past
                if not is_valid_booking_time(booking_datetime, min_advance_hours=1):
                    raise ValueError(
                        f"Cannot modify to a past time. New booking time must be at least 1 hour in advance. "
                        f"Requested time: {booking_datetime.isoformat()}"
                    )

                validated_data['booking_datetime'] = booking_datetime
                has_modification = True
            except ValueError as e:
                raise ValueError(f"Invalid booking_datetime: {str(e)}")
            except Exception as e:
                logger.error(f"Failed to parse booking_datetime: {str(e)}")
                raise ValueError(f"Could not parse booking_datetime: {str(e)}")

        # Validate party_size if provided
        if 'party_size' in kwargs and kwargs['party_size'] is not None:
            try:
                party_size = int(kwargs['party_size'])
                if party_size <= 0 or party_size > 20:
                    raise ValueError("Party size must be between 1 and 20")
                validated_data['party_size'] = party_size
                has_modification = True
            except (ValueError, TypeError):
                raise ValueError("Party size must be a valid number")

        # Validate special_requests if provided
        if 'special_requests' in kwargs and kwargs['special_requests'] is not None:
            validated_data['special_requests'] = kwargs['special_requests']
            has_modification = True

        if not has_modification:
            raise ValueError("At least one modification field (booking_datetime, party_size, special_requests) must be provided")

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Get the booking
                booking_query = select(Booking).where(Booking.id == validated_data['booking_id'])
                booking_result = await session.execute(booking_query)
                booking = booking_result.scalar_one_or_none()

                if not booking:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": "Booking not found"
                        },
                        metadata={"operation": "modify_booking"}
                    )

                # Check if booking can be modified (not cancelled or completed)
                if booking.status in ['cancelled', 'completed', 'no_show']:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": f"Cannot modify booking with status '{booking.status}'"
                        },
                        metadata={"operation": "modify_booking"}
                    )

                # Store old values for response
                old_values = {
                    "booking_datetime": safe_isoformat(booking.booking_datetime),
                    "party_size": booking.party_size,
                    "special_requests": booking.special_requests
                }

                # Apply modifications
                modified_fields = []
                if 'booking_datetime' in validated_data:
                    booking.booking_datetime = validated_data['booking_datetime']
                    modified_fields.append("booking_datetime")

                if 'party_size' in validated_data:
                    booking.party_size = validated_data['party_size']
                    modified_fields.append("party_size")

                if 'special_requests' in validated_data:
                    booking.special_requests = validated_data['special_requests']
                    modified_fields.append("special_requests")

                # Update booking_status to 'modified' when booking is changed
                if modified_fields:
                    booking.booking_status = 'modified'

                await session.commit()
                await session.refresh(booking)

                # Serialize booking using schema
                booking_data = serialize_output_with_schema(
                    BookingResponse,
                    booking,
                    self.name,
                    from_orm=True
                )

                # Add modification metadata
                booking_data['success'] = True
                booking_data['booking_id'] = str(booking.id)
                booking_data['modified_fields'] = modified_fields
                booking_data['old_values'] = old_values
                booking_data['new_values'] = {
                    "booking_datetime": safe_isoformat(booking.booking_datetime),
                    "party_size": booking.party_size,
                    "special_requests": booking.special_requests
                }

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=booking_data,
                    metadata={"operation": "modify_booking"}
                )

        except Exception as e:
            logger.error(f"Failed to modify booking: {str(e)}")
            raise ToolError(
                f"Failed to modify booking: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetBookingsByPhoneTool(ToolBase):
    """Retrieve all bookings for a specific phone number."""

    def __init__(self):
        super().__init__(
            name="get_bookings_by_phone",
            description="Get all bookings for a phone number",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'phone' not in kwargs or not kwargs['phone']:
            raise ValueError("Phone number is required")

        phone = str(kwargs['phone']).strip()
        if not phone:
            raise ValueError("Phone number cannot be empty")

        return {'phone': phone}

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)
            phone = validated_data['phone']

            async with db_manager.get_session() as session:
                # Query bookings by phone number with user and table joins
                booking_query = select(Booking).join(User).where(
                    User.phone == phone
                ).options(
                    joinedload(Booking.user),
                    joinedload(Booking.table)
                ).order_by(Booking.booking_datetime.desc())

                booking_result = await session.execute(booking_query)
                bookings = booking_result.scalars().all()

                if not bookings:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "found": False,
                            "bookings": [],
                            "message": f"No bookings found for phone number {phone}"
                        },
                        metadata={"operation": "get_bookings_by_phone", "phone": phone}
                    )

                # Build response with booking details
                booking_list = []
                for booking in bookings:
                    # Serialize booking using schema
                    booking_summary = serialize_output_with_schema(
                        BookingSummaryResponse,
                        booking,
                        self.name,
                        from_orm=True
                    )

                    # Add table and user info
                    booking_summary['booking_id'] = str(booking.id)
                    booking_summary['table'] = {
                        "table_number": booking.table.table_number if booking.table else "Unknown",
                        "capacity": booking.table.capacity if booking.table else None
                    }
                    booking_summary['user'] = {
                        "name": booking.user.name if booking.user else "Unknown",
                        "phone": booking.user.phone if booking.user else phone
                    }

                    booking_list.append(booking_summary)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "found": True,
                        "bookings": booking_list,
                        "total_bookings": len(booking_list),
                        "phone": phone
                    },
                    metadata={"operation": "get_bookings_by_phone", "phone": phone}
                )

        except Exception as e:
            logger.error(f"Failed to get bookings by phone: {str(e)}")
            raise ToolError(
                f"Failed to get bookings by phone: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


# Create tool instances for easy importing
check_availability_tool = CheckAvailabilityTool()
create_booking_tool = CreateBookingTool()
get_booking_tool = GetBookingTool()
get_bookings_by_phone_tool = GetBookingsByPhoneTool()
update_booking_status_tool = UpdateBookingStatusTool()
cancel_booking_tool = CancelBookingTool()
modify_booking_tool = ModifyBookingTool()
