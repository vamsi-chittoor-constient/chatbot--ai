"""
User management database tools.

This module provides database operations for user management including
user creation, authentication, profile management, and preferences.

Classes:
    CreateUserTool: Create new users with progressive authentication
    GetUserTool: Retrieve user by ID, email, or phone
    UpdateUserTool: Update user profile information
    DeleteUserTool: Soft delete user accounts
    GetUserPreferencesTool: Retrieve user preferences
    UpdateUserPreferencesTool: Update user dietary and notification preferences
    AuthenticateUserTool: Authenticate user credentials
"""

from typing import Optional, Dict, Any, List
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.shared.models import User, UserPreferences, UserStatus
from app.core.logging_config import get_logger
from app.utils.schema_tool_integration import (
    validate_input_with_schema,
    serialize_output_with_schema,
    safe_isoformat
)
from app.schemas.user import (
    UserResponse,
    UserProfileResponse
)
from app.schemas.internal import (
    UserPreferencesRequest,
    UserPreferencesResponse
)

logger = get_logger(__name__)


class CreateUserTool(ToolBase):
    """
    Create new user accounts with progressive authentication support.

    Supports anonymous users that can later be upgraded to registered users.
    """

    def __init__(self):
        super().__init__(
            name="create_user",
            description="Create new user account with progressive authentication",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate user creation parameters"""
        # For anonymous users, no validation needed
        # For registered users, require either phone or email
        is_anonymous = kwargs.get('is_anonymous', True)

        if not is_anonymous:
            phone_number = kwargs.get('phone_number')
            email = kwargs.get('email')

            if not phone_number and not email:
                raise ToolError(
                    "Either phone_number or email is required for registered users",
                    tool_name=self.name
                )

            if phone_number and not phone_number.startswith('+'):
                raise ToolError(
                    "Phone number must include country code (e.g., +1234567890)",
                    tool_name=self.name
                )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Create a new user account"""
        try:
            async with get_db_session() as session:
                # Check for existing user if email/phone provided
                phone_number = kwargs.get('phone_number')
                email = kwargs.get('email')

                if phone_number or email:
                    query = select(User)
                    if phone_number:
                        query = query.where(User.phone_number == phone_number)
                    elif email:
                        query = query.where(User.email == email)

                    existing_user = await session.execute(query)
                    if existing_user.scalar_one_or_none():
                        return ToolResult(
                            status=ToolStatus.FAILURE,
                            error="User already exists with this phone number or email"
                        )

                # Create new user
                new_user = User(
                    phone_number=phone_number,
                    email=email,
                    full_name=kwargs.get('full_name'),
                    password_hash=kwargs.get('password_hash'),
                    is_anonymous=kwargs.get('is_anonymous', True)
                    # status will use the default from the model (UserStatus.ACTIVE)
                )

                session.add(new_user)
                await session.commit()
                await session.refresh(new_user)

                logger.info(f"Created user: {new_user.id}",
                    user_id=new_user.id,
                    is_anonymous=new_user.is_anonymous,
                    has_phone=bool(new_user.phone_number),
                    has_email=bool(new_user.email)
                )

                # Serialize response using schema
                user_data = serialize_output_with_schema(
                    UserResponse,
                    new_user,
                    self.name,
                    from_orm=True
                )

                # Add compatibility field for legacy code
                if 'id' in user_data and 'user_id' not in user_data:
                    user_data['user_id'] = user_data['id']

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=user_data,
                    metadata={"operation": "create_user"}
                )

        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise ToolError(
                f"Database error while creating user: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetUserTool(ToolBase):
    """
    Retrieve user information by various identifiers.

    Supports lookup by user ID, email, or phone number.
    """

    def __init__(self):
        super().__init__(
            name="get_user",
            description="Retrieve user by ID, email, or phone number",
            max_retries=2,
            timeout_seconds=5
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate user lookup parameters"""
        user_id = kwargs.get('user_id')
        email = kwargs.get('email')
        phone_number = kwargs.get('phone_number')

        if not any([user_id, email, phone_number]):
            raise ToolError(
                "Must provide user_id, email, or phone_number for lookup",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Retrieve user information"""
        try:
            async with get_db_session() as session:
                query = select(User).options(selectinload(User.user_preferences))

                # Build query based on provided identifier
                user_id = kwargs.get('user_id')
                email = kwargs.get('email')
                phone_number = kwargs.get('phone_number')

                if user_id:
                    query = query.where(User.id == user_id)
                elif email:
                    query = query.where(User.email == email)
                elif phone_number:
                    query = query.where(User.phone_number == phone_number)

                result = await session.execute(query)
                user = result.scalar_one_or_none()

                if not user:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="User not found"
                    )

                # Check if user is active (None/null is considered active by default)
                if user.status and user.status not in ["ACTIVE", "active"]:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error=f"User account is {user.status or 'inactive'}"
                    )

                # Serialize user data using schema (includes preferences if available)
                if user.user_preferences:
                    user_data = serialize_output_with_schema(
                        UserProfileResponse,
                        user,
                        self.name,
                        from_orm=True
                    )
                else:
                    user_data = serialize_output_with_schema(
                        UserResponse,
                        user,
                        self.name,
                        from_orm=True
                    )

                # Add compatibility field for legacy code
                if 'id' in user_data and 'user_id' not in user_data:
                    user_data['user_id'] = user_data['id']

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=user_data,
                    metadata={"operation": "get_user", "lookup_method": "user_id" if user_id else "email" if email else "phone"}
                )

        except Exception as e:
            logger.error(f"Failed to retrieve user: {str(e)}")
            raise ToolError(
                f"Database error while retrieving user: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class UpdateUserTool(ToolBase):
    """
    Update user profile information and account status.

    Supports upgrading anonymous users to registered users.
    """

    def __init__(self):
        super().__init__(
            name="update_user",
            description="Update user profile information",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate user update parameters"""
        user_id = kwargs.get('user_id')
        if not user_id:
            raise ToolError(
                "user_id is required for user updates",
                tool_name=self.name
            )

        # Validate phone format if provided
        phone_number = kwargs.get('phone_number')
        if phone_number and not phone_number.startswith('+'):
            raise ToolError(
                "Phone number must include country code (e.g., +1234567890)",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Update user information"""
        try:
            async with get_db_session() as session:
                user_id = kwargs['user_id']

                # Get existing user
                result = await session.execute(select(User).where(User.id == user_id))
                user = result.scalar_one_or_none()

                if not user:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="User not found"
                    )

                # Update allowed fields
                updated_fields = []

                if 'phone_number' in kwargs:
                    user.phone_number = kwargs['phone_number']
                    updated_fields.append('phone_number')

                if 'email' in kwargs:
                    user.email = kwargs['email']
                    updated_fields.append('email')

                if 'full_name' in kwargs:
                    user.full_name = kwargs['full_name']
                    updated_fields.append('full_name')

                if 'password_hash' in kwargs:
                    user.password_hash = kwargs['password_hash']
                    updated_fields.append('password')

                if 'is_anonymous' in kwargs:
                    user.is_anonymous = kwargs['is_anonymous']
                    updated_fields.append('is_anonymous')

                if 'email_verified' in kwargs:
                    user.email_verified = kwargs['email_verified']
                    updated_fields.append('email_verified')

                if 'phone_verified' in kwargs:
                    user.phone_verified = kwargs['phone_verified']
                    updated_fields.append('phone_verified')

                if 'status' in kwargs:
                    user.status = kwargs['status']
                    updated_fields.append('status')

                await session.commit()
                await session.refresh(user)

                logger.info(f"Updated user: {user.id}",
                    user_id=user.id,
                    updated_fields=updated_fields
                )

                # Serialize response using schema
                user_data = serialize_output_with_schema(
                    UserResponse,
                    user,
                    self.name,
                    from_orm=True
                )

                # Add metadata about what was updated
                user_data['updated_fields'] = updated_fields

                # Add compatibility field for legacy code
                if 'id' in user_data and 'user_id' not in user_data:
                    user_data['user_id'] = user_data['id']

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=user_data,
                    metadata={"operation": "update_user"}
                )

        except Exception as e:
            logger.error(f"Failed to update user: {str(e)}")
            raise ToolError(
                f"Database error while updating user: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class UpdateUserPreferencesTool(ToolBase):
    """
    Update user dietary preferences and notification settings.
    """

    def __init__(self):
        super().__init__(
            name="update_user_preferences",
            description="Update user dietary preferences and settings",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """Validate preferences update parameters"""
        user_id = kwargs.get('user_id')
        if not user_id:
            raise ToolError(
                "user_id is required for preferences update",
                tool_name=self.name
            )

        return kwargs

    async def _execute_impl(self, **kwargs) -> ToolResult:
        """Update user preferences"""
        try:
            async with get_db_session() as session:
                user_id = kwargs['user_id']

                # Check if user exists
                user_result = await session.execute(select(User).where(User.id == user_id))
                if not user_result.scalar_one_or_none():
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="User not found"
                    )

                # Get or create preferences
                prefs_result = await session.execute(
                    select(UserPreferences).where(UserPreferences.user_id == user_id)
                )
                preferences = prefs_result.scalar_one_or_none()

                if not preferences:
                    preferences = UserPreferences(user_id=user_id)
                    session.add(preferences)

                # Update preference fields
                updated_fields = []

                if 'dietary_restrictions' in kwargs:
                    preferences.dietary_restrictions = kwargs['dietary_restrictions']
                    updated_fields.append('dietary_restrictions')

                if 'allergies' in kwargs:
                    preferences.allergies = kwargs['allergies']
                    updated_fields.append('allergies')

                if 'favorite_cuisines' in kwargs:
                    preferences.favorite_cuisines = kwargs['favorite_cuisines']
                    updated_fields.append('favorite_cuisines')

                if 'spice_level' in kwargs:
                    preferences.spice_level = kwargs['spice_level']
                    updated_fields.append('spice_level')

                if 'preferred_seating' in kwargs:
                    preferences.preferred_seating = kwargs['preferred_seating']
                    updated_fields.append('preferred_seating')

                if 'special_occasions' in kwargs:
                    preferences.special_occasions = kwargs['special_occasions']
                    updated_fields.append('special_occasions')

                if 'notification_preferences' in kwargs:
                    preferences.notification_preferences = kwargs['notification_preferences']
                    updated_fields.append('notification_preferences')

                await session.commit()
                await session.refresh(preferences)

                logger.info(f"Updated preferences for user: {user_id}",
                    user_id=user_id,
                    updated_fields=updated_fields
                )

                # Serialize response using schema
                prefs_data = serialize_output_with_schema(
                    UserPreferencesResponse,
                    preferences,
                    self.name,
                    from_orm=True
                )

                # Add metadata about what was updated
                prefs_data['updated_fields'] = updated_fields

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=prefs_data,
                    metadata={"operation": "update_user_preferences"}
                )

        except Exception as e:
            logger.error(f"Failed to update user preferences: {str(e)}")
            raise ToolError(
                f"Database error while updating preferences: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


# TODO: Future enhancement - Add user authentication tool with password hashing
# TODO: Future enhancement - Add user activity logging
# TODO: Future enhancement - Add user search and filtering capabilities


if __name__ == "__main__":
    # Test user management tools
    import asyncio

    async def test_user_tools():
        """Test user management tools functionality"""
        print("Testing user management tools...")

        # Initialize database connection
        from app.database.connection import init_database
        await init_database(create_tables=False)

        try:
            # Test creating an anonymous user
            create_tool = CreateUserTool()
            result = await create_tool.execute(is_anonymous=True)

            if result.status == ToolStatus.SUCCESS:
                user_id = result.data['user_id']
                print(f"Created anonymous user: {user_id}")

                # Test retrieving the user
                get_tool = GetUserTool()
                result = await get_tool.execute(user_id=user_id)

                if result.status == ToolStatus.SUCCESS:
                    print(f"Retrieved user: {result.data['full_name'] or 'Anonymous'}")

                    # Test updating user to registered
                    update_tool = UpdateUserTool()
                    result = await update_tool.execute(
                        user_id=user_id,
                        email="test@example.com",
                        full_name="Test User",
                        is_anonymous=False
                    )

                    if result.status == ToolStatus.SUCCESS:
                        print("Updated user to registered account")

                        # Test updating preferences
                        prefs_tool = UpdateUserPreferencesTool()
                        result = await prefs_tool.execute(
                            user_id=user_id,
                            dietary_restrictions=["vegetarian"],
                            spice_level="medium",
                            favorite_cuisines=["Italian", "Indian"]
                        )

                        if result.status == ToolStatus.SUCCESS:
                            print("Updated user preferences")
                            print("All user management tools working correctly!")
                        else:
                            print(f"Preferences update failed: {result.error}")
                    else:
                        print(f"User update failed: {result.error}")
                else:
                    print(f"User retrieval failed: {result.error}")
            else:
                print(f"User creation failed: {result.error}")

        except Exception as e:
            print(f"User tools test failed: {str(e)}")

    # Run test
    asyncio.run(test_user_tools())
