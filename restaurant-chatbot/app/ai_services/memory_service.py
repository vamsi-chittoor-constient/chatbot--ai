"""
Conversation Memory Service
============================
Semantic memory layer for personalized user experiences.

Stores and retrieves:
- User preferences (dietary restrictions, favorite dishes)
- Past interactions and context
- Learned behaviors and patterns
- Cross-session memory
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import json
import structlog
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.shared.models import Session, Conversation

logger = structlog.get_logger("services.memory")


class ConversationMemory:
    """Manages semantic memory for conversations."""

    def __init__(self):
        self.session_cache: Dict[str, Dict[str, Any]] = {}

    async def get_user_memory(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's semantic memory across all sessions.

        Returns:
            {
                "dietary_restrictions": ["vegetarian", "peanut_allergy"],
                "preferences": {
                    "favorite_dishes": ["Eggplant Parmesan"],
                    "usual_party_size": 2,
                    "preferred_time": "7pm"
                },
                "past_orders": [...],
                "past_bookings": [...],
                "interaction_history": {
                    "total_orders": 5,
                    "total_bookings": 3,
                    "complaints": 0,
                    "last_visit": "2025-01-15"
                }
            }
        """
        # Check cache first
        cache_key = user_id or session_id or phone_number
        if cache_key and cache_key in self.session_cache:
            return self.session_cache[cache_key]

        memory = {
            "dietary_restrictions": [],
            "preferences": {},
            "past_orders": [],
            "past_bookings": [],
            "interaction_history": {}
        }

        try:
            async with get_db_session() as db_session:
                # Get user sessions
                query = select(Session)

                if user_id:
                    query = query.where(Session.user_id == user_id)
                elif session_id:
                    query = query.where(Session.session_id == session_id)
                else:
                    return memory

                result = await db_session.execute(query)
                user_sessions = result.scalars().all()

                if not user_sessions:
                    return memory

                # Note: Session model doesn't have preferences field
                # Preferences would need to be stored in a separate user preferences table
                # or in the User model itself
                # For now, return basic memory structure

                # Deduplicate dietary restrictions
                memory["dietary_restrictions"] = list(set(memory["dietary_restrictions"]))

                # Get conversation contexts for this user
                if user_id:
                    conv_query = select(Conversation).where(
                        Conversation.user_id == user_id
                    ).order_by(Conversation.created_at.desc())

                    conv_result = await db_session.execute(conv_query)
                    conversations = conv_result.scalars().all()

                    # Build interaction history
                    memory["interaction_history"] = {
                        "total_conversations": len(conversations),
                        "last_interaction": conversations[0].created_at.isoformat() if conversations else None
                    }

                # Cache the memory
                if cache_key:
                    self.session_cache[cache_key] = memory

                return memory

        except Exception as e:
            logger.error("Failed to get user memory", error=str(e), exc_info=True)
            return memory

    async def update_user_memory(
        self,
        session_id: str,
        memory_updates: Dict[str, Any]
    ) -> bool:
        """
        Update user's semantic memory.

        Args:
            session_id: Session identifier
            memory_updates: {
                "dietary_restrictions": ["vegetarian"],
                "preferences": {
                    "favorite_dish": "Eggplant Parmesan"
                }
            }

        Returns:
            True if successful
        """
        try:
            async with get_db_session() as db_session:
                # Get session
                query = select(Session).where(Session.session_id == session_id)
                result = await db_session.execute(query)
                user_session = result.scalar_one_or_none()

                if not user_session:
                    logger.warning("Session not found", session_id=session_id)
                    return False

                # Note: Session model doesn't have preferences field
                # This would need to be stored in AgentMemory or User model
                # For now, just log the update and invalidate cache

                # Invalidate cache
                if session_id in self.session_cache:
                    del self.session_cache[session_id]

                logger.info("User memory update requested", session_id=session_id,
                           updates=memory_updates)
                return True

        except Exception as e:
            logger.error("Failed to update user memory", error=str(e), exc_info=True)
            return False

    async def extract_memory_from_conversation(
        self,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Extract semantic memory from conversation messages.

        Uses LLM to identify:
        - Dietary restrictions mentioned
        - Preferences stated
        - Patterns in behavior

        Args:
            messages: Conversation messages

        Returns:
            Extracted memory dict
        """
        # TODO: Use LLM to extract semantic information
        # For now, simple keyword matching

        memory = {
            "dietary_restrictions": [],
            "preferences": {}
        }

        conversation_text = " ".join([
            msg.get("content", "") for msg in messages
            if isinstance(msg.get("content"), str)
        ])
        text_lower = conversation_text.lower()

        # Dietary restrictions
        dietary_keywords = {
            "vegetarian": "vegetarian",
            "vegan": "vegan",
            "gluten-free": "gluten_free",
            "gluten free": "gluten_free",
            "dairy-free": "dairy_free",
            "dairy free": "dairy_free",
            "nut allergy": "nut_allergy",
            "peanut allergy": "peanut_allergy",
            "shellfish allergy": "shellfish_allergy"
        }

        for keyword, restriction in dietary_keywords.items():
            if keyword in text_lower:
                memory["dietary_restrictions"].append(restriction)

        # Preferences (simple extraction)
        if "table for" in text_lower or "party of" in text_lower:
            # Extract party size
            import re
            match = re.search(r'(?:table for|party of)\s+(\d+)', text_lower)
            if match:
                memory["preferences"]["usual_party_size"] = int(match.group(1))

        return memory

    def clear_cache(self, key: Optional[str] = None):
        """Clear memory cache."""
        if key:
            self.session_cache.pop(key, None)
        else:
            self.session_cache.clear()


# Global instance
conversation_memory = ConversationMemory()
