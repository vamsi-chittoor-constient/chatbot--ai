"""
User Profile Feature
====================
User profile and preferences management feature with sub-agent architecture.

Features:
- Dietary and cuisine preferences management
- Favorite menu items management
- Order and booking history viewing
- Quick reorder functionality

Sub-Agents:
- preference_manager: Manage dietary restrictions, cuisines, allergies
- favorites_manager: Manage favorite menu items
- history_manager: View history and reorder
"""

from app.features.user_profile.node import user_profile_node
from app.features.user_profile.state import ProfileState, ProfileProgress
from app.features.user_profile.graph import create_user_profile_graph

__all__ = [
    "user_profile_node",
    "ProfileState",
    "ProfileProgress",
    "create_user_profile_graph"
]
