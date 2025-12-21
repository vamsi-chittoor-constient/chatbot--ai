"""
Authenticator Sub-Agent
=======================
Complete authentication flow: phone → OTP → verify → login/register
"""

from app.features.user_management.agents.authenticator.node import authenticator_agent

__all__ = ["authenticator_agent"]
