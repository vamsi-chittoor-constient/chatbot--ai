"""
Identity Migrator Sub-Agent
===========================
Migrate anonymous device data to user account
"""

from app.features.user_management.agents.identity_migrator.node import identity_migrator_agent

__all__ = ["identity_migrator_agent"]
