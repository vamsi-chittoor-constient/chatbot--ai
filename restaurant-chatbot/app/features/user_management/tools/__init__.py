"""
User Management Tools
====================
Tools for authentication, session management, identity, and migration.
"""

from app.features.user_management.tools.otp_tools import (
    send_otp,
    verify_otp,
    check_user_exists,
    create_user
)

from app.features.user_management.tools.session_tools import (
    get_active_sessions,
    revoke_session,
    create_session,
    get_user_devices,
    update_device_name
)

from app.features.user_management.tools.identity_tools import (
    get_user_identity,
    update_user_name,
    update_user_email,
    update_user_phone,
    update_user_profile
)

from app.features.user_management.tools.migration_tools import (
    migrate_device_data,
    get_device_data_summary,
    link_device_to_user
)

from app.features.user_management.tools.auth_tools import (
    get_user,
    authenticate_user
)

__all__ = [
    # OTP tools
    "send_otp",
    "verify_otp",
    "check_user_exists",
    "create_user",

    # Session tools
    "get_active_sessions",
    "revoke_session",
    "create_session",
    "get_user_devices",
    "update_device_name",

    # Identity tools
    "get_user_identity",
    "update_user_name",
    "update_user_email",
    "update_user_phone",
    "update_user_profile",

    # Migration tools
    "migrate_device_data",
    "get_device_data_summary",
    "link_device_to_user",

    # Auth tools
    "get_user",
    "authenticate_user"
]
