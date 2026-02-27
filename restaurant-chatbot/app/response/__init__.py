"""
Response Module (Virtual Waiter)
=================================
Exit point of the agentic AI system.

Transforms structured ActionResults from specialist agents into warm,
casual, hospitality-focused responses.

This module provides a consistent virtual waiter personality across all
user interactions, regardless of which backend specialist agent handled
the request.

Personality: Casual & Friendly (neighborhood restaurant)
Upselling: Contextual (helpful, not pushy)
Special Cases: Always Warm (even errors sound friendly)
"""

from app.response.node import response_agent_node

__all__ = ["response_agent_node"]
