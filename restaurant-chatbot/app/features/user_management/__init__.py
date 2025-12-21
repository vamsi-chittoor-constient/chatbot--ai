"""
User Management Feature
=======================
Authentication and identity management feature with sub-agent architecture.

Features:
- User authentication (phone → OTP → verify → login/register)
- Session and device management
- Identity data updates (name, email, phone)
- Device data migration

NOTE: LangGraph implementation removed. System now uses Sticky Crew orchestrator.
Only schemas, models, and tools remain for potential future use.

Sub-Agents (REMOVED - using Sticky Crew):
- authenticator: Complete authentication flow
- session_manager: Session/device management
- identity_migrator: Migrate anonymous device data
- identity_manager: Update user identity information
"""

# LangGraph imports removed - using Sticky Crew orchestrator instead
# from app.features.user_management.node import user_management_node
# from app.features.user_management.state import AuthenticationState, AuthProgress
# from app.features.user_management.graph import create_user_management_graph

__all__ = [
    # LangGraph components removed - using Sticky Crew
    # "user_management_node",
    # "AuthenticationState",
    # "AuthProgress",
    # "create_user_management_graph"
]
