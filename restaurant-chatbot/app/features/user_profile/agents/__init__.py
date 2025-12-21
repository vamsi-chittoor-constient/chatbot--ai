"""
User Profile Sub-Agents
=======================
Sub-agents for profile and preference management.
"""

from app.features.user_profile.agents.preference_manager import preference_manager_agent
from app.features.user_profile.agents.favorites_manager import favorites_manager_agent
from app.features.user_profile.agents.history_manager import history_manager_agent

__all__ = [
    "preference_manager_agent",
    "favorites_manager_agent",
    "history_manager_agent"
]
