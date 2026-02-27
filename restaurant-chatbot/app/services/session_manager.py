"""
Session management service using Redis for restaurant AI assistant.

Features:
- User session management with automatic expiry
- Conversation context persistence
- Multi-tenant session isolation
- Real-time session synchronization
"""

import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, asdict

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from app.services.redis_service import get_redis_service, RedisService
except ImportError:
    # Fallback for direct execution
    from redis_service import get_redis_service, RedisService

logger = logging.getLogger(__name__)


@dataclass
class UserSession:
    """User session data structure"""
    session_id: str
    tenant_id: str
    user_id: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    is_authenticated: bool = False
    preferences: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.last_active is None:
            self.last_active = datetime.now(timezone.utc)
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ConversationContext:
    """Conversation context data structure"""
    conversation_id: str
    session_id: str
    tenant_id: str
    user_id: Optional[str] = None
    messages: Optional[List[Dict[str, Any]]] = None
    active_intents: Optional[List[str]] = None
    incomplete_tasks: Optional[Dict[str, Any]] = None
    user_context: Optional[Dict[str, Any]] = None
    agent_context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.messages is None:
            self.messages = []
        if self.active_intents is None:
            self.active_intents = []
        if self.incomplete_tasks is None:
            self.incomplete_tasks = {}
        if self.user_context is None:
            self.user_context = {}
        if self.agent_context is None:
            self.agent_context = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.updated_at is None:
            self.updated_at = datetime.now(timezone.utc)


class SessionManager:
    """
    Redis-based session manager for the restaurant AI assistant

    Handles:
    - User session lifecycle
    - Conversation context management
    - Multi-tenant session isolation
    - Automatic cleanup of expired sessions
    """

    def __init__(self, redis_service: Optional[RedisService] = None):
        self.redis = redis_service or get_redis_service()

        # Note: Session persistence now handled by PostgreSQL
        # NoSQL/MongoDB integration removed as it's no longer needed
        self.enable_persistence = False
        self.nosql = None

        # Configuration
        self.session_ttl = 3600  # 1 hour default
        self.conversation_ttl = 7200  # 2 hours default
        self.max_messages_per_conversation = 1000

        # Key prefixes
        self.session_prefix = "session"
        self.conversation_prefix = "conversation"
        self.user_sessions_prefix = "user_sessions"
        self.tenant_sessions_prefix = "tenant_sessions"

    def _session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.session_prefix}:{session_id}"

    def _conversation_key(self, conversation_id: str) -> str:
        """Generate Redis key for conversation"""
        return f"{self.conversation_prefix}:{conversation_id}"

    def _user_sessions_key(self, user_id: str) -> str:
        """Generate Redis key for user's active sessions"""
        return f"{self.user_sessions_prefix}:{user_id}"

    def _tenant_sessions_key(self, tenant_id: str) -> str:
        """Generate Redis key for tenant's active sessions"""
        return f"{self.tenant_sessions_prefix}:{tenant_id}"

    # ==================== SESSION MANAGEMENT ====================

    async def create_session(self, tenant_id: str, user_id: Optional[str] = None,
                      phone_number: Optional[str] = None, email: Optional[str] = None,
                      ttl: Optional[int] = None, session_id: Optional[str] = None) -> UserSession:
        """
        Create a new user session

        Args:
            tenant_id: Restaurant/tenant identifier
            user_id: User ID (optional for anonymous sessions)
            phone_number: User phone number
            email: User email
            ttl: Session time-to-live in seconds
            session_id: Optional session ID (if not provided, generates a new UUID)

        Returns:
            UserSession: Created session object
        """
        session_id = session_id or str(uuid.uuid4())
        ttl = ttl or self.session_ttl

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            phone_number=phone_number,
            email=email,
            is_authenticated=bool(user_id)
        )

        # Store session in Redis
        session_data = asdict(session)
        session_data['created_at'] = session.created_at.isoformat() if session.created_at else None
        session_data['last_active'] = session.last_active.isoformat() if session.last_active else None

        success = await self.redis.set(self._session_key(session_id), session_data, ttl)

        if success:
            # Track session for user and tenant
            if user_id:
                await self._add_user_session(user_id, session_id, ttl)
            await self._add_tenant_session(tenant_id, session_id, ttl)

        return session

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        """
        Retrieve session by ID

        Args:
            session_id: Session identifier

        Returns:
            UserSession or None if not found
        """
        session_data = await self.redis.get(self._session_key(session_id))
        if not session_data:
            return None

        # Parse timestamps
        if 'created_at' in session_data:
            session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
        if 'last_active' in session_data:
            session_data['last_active'] = datetime.fromisoformat(session_data['last_active'])

        return UserSession(**session_data)

    async def update_session(self, session_id: str, **updates) -> bool:
        """
        Update session data

        Args:
            session_id: Session identifier
            **updates: Fields to update

        Returns:
            bool: Success status
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        # Update fields
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)

        session.last_active = datetime.now(timezone.utc)

        # Save back to Redis
        session_data = asdict(session)
        session_data['created_at'] = session.created_at.isoformat() if session.created_at else None
        session_data['last_active'] = session.last_active.isoformat() if session.last_active else None

        return await self.redis.set(self._session_key(session_id), session_data, self.session_ttl)

    async def close_session(self, session_id: str, session_outcome: Optional[str] = None,
                     user_satisfaction: Optional[float] = None,
                     save_to_persistent_store: bool = False) -> bool:
        """
        Close a session

        Note: Session persistence is now handled by PostgreSQL.
        This method only cleans up Redis cache.

        Args:
            session_id: Session identifier
            session_outcome: Final outcome (deprecated, kept for compatibility)
            user_satisfaction: User satisfaction score (deprecated, kept for compatibility)
            save_to_persistent_store: Deprecated, no longer used

        Returns:
            bool: Success status
        """
        session = await self.get_session(session_id)
        if not session:
            return False

        conversation_id = getattr(session, 'active_conversation_id', None)

        # Clean up from Redis
        return await self._cleanup_session_from_redis(session_id, session, conversation_id)

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session without persistence (backward compatibility)

        Args:
            session_id: Session identifier

        Returns:
            bool: Success status
        """
        return await self.close_session(session_id, save_to_persistent_store=False)

    async def extend_session(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """
        Extend session TTL

        Args:
            session_id: Session identifier
            ttl: New TTL in seconds

        Returns:
            bool: Success status
        """
        ttl = ttl or self.session_ttl
        return await self.redis.expire(self._session_key(session_id), ttl)

    async def authenticate_session(self, session_id: str, user_id: str) -> bool:
        """
        Mark session as authenticated with user ID

        Args:
            session_id: Session identifier
            user_id: Authenticated user ID

        Returns:
            bool: Success status
        """
        return await self.update_session(
            session_id,
            user_id=user_id,
            is_authenticated=True
        )

    # ==================== CONVERSATION MANAGEMENT ====================

    async def create_conversation(self, session_id: str, tenant_id: str,
                          user_id: Optional[str] = None, ttl: Optional[int] = None) -> ConversationContext:
        """
        Create a new conversation context

        Args:
            session_id: Associated session ID
            tenant_id: Restaurant/tenant identifier
            user_id: User ID (optional)
            ttl: Conversation TTL in seconds

        Returns:
            ConversationContext: Created conversation
        """
        conversation_id = str(uuid.uuid4())
        ttl = ttl or self.conversation_ttl

        conversation = ConversationContext(
            conversation_id=conversation_id,
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id
        )

        # Store conversation
        conversation_data = asdict(conversation)
        conversation_data['created_at'] = conversation.created_at.isoformat() if conversation.created_at else None
        conversation_data['updated_at'] = conversation.updated_at.isoformat() if conversation.updated_at else None

        success = await self.redis.set(self._conversation_key(conversation_id), conversation_data, ttl)

        if success:
            # Link conversation to session
            session = await self.get_session(session_id)
            if session:
                if not session.metadata:
                    session.metadata = {}
                session.metadata['active_conversation'] = conversation_id
                await self.update_session(session_id, metadata=session.metadata)

        return conversation

    async def get_conversation(self, conversation_id: str) -> Optional[ConversationContext]:
        """
        Retrieve conversation by ID

        Args:
            conversation_id: Conversation identifier

        Returns:
            ConversationContext or None if not found
        """
        conversation_data = await self.redis.get(self._conversation_key(conversation_id))
        if not conversation_data:
            return None

        # Parse timestamps
        if 'created_at' in conversation_data:
            conversation_data['created_at'] = datetime.fromisoformat(conversation_data['created_at'])
        if 'updated_at' in conversation_data:
            conversation_data['updated_at'] = datetime.fromisoformat(conversation_data['updated_at'])

        return ConversationContext(**conversation_data)

    async def add_message(self, conversation_id: str, role: str, content: str,
                   metadata: Optional[Dict[str, Any]] = None,
                   detected_intent: Optional[str] = None,
                   intent_confidence: Optional[float] = None,
                   extracted_entities: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a message to conversation with intent tracking

        Args:
            conversation_id: Conversation identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Additional message metadata
            detected_intent: Detected intent for this message (e.g., 'book_table', 'order_food')
            intent_confidence: Confidence score for detected intent (0.0-1.0)
            extracted_entities: Extracted entities from the message (e.g., {'party_size': 4, 'time': '7pm'})

        Returns:
            bool: Success status
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False

        # Prepare intent information
        intent_info = {}
        if detected_intent:
            intent_info = {
                "detected_intent": detected_intent,
                "intent_confidence": intent_confidence,
                "extracted_entities": extracted_entities or {},
                "intent_detected_at": datetime.now(timezone.utc).isoformat()
            }

        message = {
            "id": str(uuid.uuid4()),
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {},
            "intent": intent_info  # New intent tracking field
        }

        if conversation.messages:
            conversation.messages.append(message)
        else:
            conversation.messages = [message]
        conversation.updated_at = datetime.now(timezone.utc)

        # Limit message history
        if conversation.messages and len(conversation.messages) > self.max_messages_per_conversation:
            conversation.messages = conversation.messages[-self.max_messages_per_conversation:]

        # Save back to Redis
        conversation_data = asdict(conversation)
        conversation_data['created_at'] = conversation.created_at.isoformat() if conversation.created_at else None
        conversation_data['updated_at'] = conversation.updated_at.isoformat() if conversation.updated_at else None

        return await self.redis.set(self._conversation_key(conversation_id),
                            conversation_data, self.conversation_ttl)

    async def update_conversation_context(self, conversation_id: str,
                                  user_context: Optional[Dict] = None,
                                  agent_context: Optional[Dict] = None,
                                  active_intents: Optional[List[str]] = None,
                                  incomplete_tasks: Optional[Dict] = None) -> bool:
        """
        Update conversation context

        Args:
            conversation_id: Conversation identifier
            user_context: User-specific context updates
            agent_context: Agent-specific context updates
            active_intents: Current active intents
            incomplete_tasks: Incomplete task data

        Returns:
            bool: Success status
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False

        if user_context:
            if conversation.user_context:
                conversation.user_context.update(user_context)
            else:
                conversation.user_context = user_context
        if agent_context:
            if conversation.agent_context:
                conversation.agent_context.update(agent_context)
            else:
                conversation.agent_context = agent_context
        if active_intents is not None:
            conversation.active_intents = active_intents
        if incomplete_tasks:
            if conversation.incomplete_tasks:
                conversation.incomplete_tasks.update(incomplete_tasks)
            else:
                conversation.incomplete_tasks = incomplete_tasks

        conversation.updated_at = datetime.now(timezone.utc)

        # Save back to Redis
        conversation_data = asdict(conversation)
        conversation_data['created_at'] = conversation.created_at.isoformat() if conversation.created_at else None
        conversation_data['updated_at'] = conversation.updated_at.isoformat() if conversation.updated_at else None

        return await self.redis.set(self._conversation_key(conversation_id),
                            conversation_data, self.conversation_ttl)

    # ==================== USER & TENANT SESSION TRACKING ====================

    async def _add_user_session(self, user_id: str, session_id: str, ttl: int):
        """Add session to user's active sessions list"""
        key = self._user_sessions_key(user_id)
        sessions = await self.redis.get(key) or []
        if session_id not in sessions:
            sessions.append(session_id)
        await self.redis.set(key, sessions, ttl)

    async def _remove_user_session(self, user_id: str, session_id: str):
        """Remove session from user's active sessions list"""
        key = self._user_sessions_key(user_id)
        sessions = await self.redis.get(key) or []
        if session_id in sessions:
            sessions.remove(session_id)
            if sessions:
                await self.redis.set(key, sessions, self.session_ttl)
            else:
                await self.redis.delete(key)

    async def _add_tenant_session(self, tenant_id: str, session_id: str, ttl: int):
        """Add session to tenant's active sessions list"""
        key = self._tenant_sessions_key(tenant_id)
        sessions = await self.redis.get(key) or []
        if session_id not in sessions:
            sessions.append(session_id)
        await self.redis.set(key, sessions, ttl)

    async def _remove_tenant_session(self, tenant_id: str, session_id: str):
        """Remove session from tenant's active sessions list"""
        key = self._tenant_sessions_key(tenant_id)
        sessions = await self.redis.get(key) or []
        if session_id in sessions:
            sessions.remove(session_id)
            if sessions:
                await self.redis.set(key, sessions, self.session_ttl)
            else:
                await self.redis.delete(key)

    async def get_user_sessions(self, user_id: str) -> List[str]:
        """Get all active sessions for a user"""
        return await self.redis.get(self._user_sessions_key(user_id)) or []

    async def get_tenant_sessions(self, tenant_id: str) -> List[str]:
        """Get all active sessions for a tenant"""
        return await self.redis.get(self._tenant_sessions_key(tenant_id)) or []

    # ==================== INTENT TRACKING METHODS ====================

    async def get_conversation_intent_history(self, conversation_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get intent history for a conversation

        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of intent records to return

        Returns:
            List of intent records with message context
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return []

        intent_history = []
        for message in reversed(conversation.messages):
            if message.get('intent') and message['intent'].get('detected_intent'):
                intent_record = {
                    'message_id': message.get('id'),
                    'timestamp': message.get('timestamp'),
                    'role': message.get('role'),
                    'content': (message.get('content', '')[:100] + '...'
                               if len(message.get('content', '')) > 100
                               else message.get('content', '')),
                    'detected_intent': message['intent']['detected_intent'],
                    'intent_confidence': message['intent'].get('intent_confidence', 0.0),
                    'extracted_entities': message['intent'].get('extracted_entities', {}),
                    'intent_detected_at': message['intent'].get('intent_detected_at')
                }
                intent_history.append(intent_record)

                if len(intent_history) >= limit:
                    break

        return list(reversed(intent_history))  # Return in chronological order

    async def get_recent_intents(self, conversation_id: str, intent_type: Optional[str] = None, hours: int = 24) -> List[str]:
        """
        Get recent intents from conversation

        Args:
            conversation_id: Conversation identifier
            intent_type: Filter by specific intent type (optional)
            hours: Look back this many hours

        Returns:
            List of recent intent names
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation or not conversation.messages:
            return []

        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_intents = []

        for message in conversation.messages:
            if not message.get('intent') or not message['intent'].get('detected_intent'):
                continue

            try:
                message_time = datetime.fromisoformat(message['timestamp'].replace('Z', '+00:00'))
                if message_time < cutoff_time:
                    continue

                detected_intent = message['intent']['detected_intent']
                if intent_type is None or detected_intent == intent_type:
                    recent_intents.append(detected_intent)

            except (ValueError, KeyError):
                continue

        return recent_intents

    async def get_dominant_intent(self, conversation_id: str, hours: int = 2) -> Optional[Dict[str, Any]]:
        """
        Get the most frequent intent in recent conversation

        Args:
            conversation_id: Conversation identifier
            hours: Look back this many hours

        Returns:
            Dict with dominant intent info or None
        """
        recent_intents = await self.get_recent_intents(conversation_id, hours=hours)
        if not recent_intents:
            return None

        # Count intent frequencies
        intent_counts = {}
        for intent in recent_intents:
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        # Find most frequent
        dominant_intent = max(intent_counts.items(), key=lambda x: x[1])

        return {
            'intent': dominant_intent[0],
            'frequency': dominant_intent[1],
            'total_messages': len(recent_intents),
            'confidence_ratio': dominant_intent[1] / len(recent_intents)
        }

    async def update_conversation_context_with_intents(self, conversation_id: str,
                                              user_context: Optional[Dict[str, Any]] = None,
                                              intent_confidence_threshold: float = 0.7) -> bool:
        """
        Update conversation context with intent-aware information

        Args:
            conversation_id: Conversation identifier
            user_context: Updated user context
            intent_confidence_threshold: Minimum confidence to consider intent active

        Returns:
            bool: Success status
        """
        conversation = await self.get_conversation(conversation_id)
        if not conversation:
            return False

        # Get recent high-confidence intents
        active_intents = []
        intent_history = await self.get_conversation_intent_history(conversation_id, limit=5)
        for record in intent_history:
            if (record['intent_confidence'] >= intent_confidence_threshold and
                record['detected_intent'] not in active_intents):
                active_intents.append(record['detected_intent'])

        # Update conversation attributes directly (not through a .context attribute)
        if user_context:
            if conversation.user_context:
                conversation.user_context.update(user_context)
            else:
                conversation.user_context = user_context

        # Update active intents
        conversation.active_intents = active_intents
        conversation.updated_at = datetime.now(timezone.utc)

        # Save back to Redis
        conversation_data = asdict(conversation)
        conversation_data['created_at'] = conversation.created_at.isoformat() if conversation.created_at else None
        conversation_data['updated_at'] = conversation.updated_at.isoformat() if conversation.updated_at else None

        return await self.redis.set(self._conversation_key(conversation_id), conversation_data, self.conversation_ttl)

    # ==================== DEPRECATED: NOSQL PERSISTENCE HELPERS ====================
    # Note: These methods are deprecated. Session persistence is now handled by PostgreSQL.

    def _create_session_summary(self, session: UserSession, conversation: Optional[ConversationContext],
                               session_end_time: datetime, session_outcome: Optional[str],
                               user_satisfaction: Optional[float]):
        """Deprecated: Create session summary for NoSQL persistence"""
        logger.warning("_create_session_summary is deprecated. Deprecated.")
        return None

    def _create_conversation_record(self, conversation: ConversationContext,
                                  session: UserSession, session_end_time: datetime):
        """Deprecated: Create conversation record for ML training data"""
        logger.warning("_create_conversation_record is deprecated. Deprecated.")
        return None

    def _update_user_profile(self, session: UserSession, session_summary):
        """Deprecated: Update or create user profile based on session data"""
        logger.warning("_update_user_profile is deprecated. Deprecated.")
        return None

    def _calculate_business_value_score(self, session_outcome: Optional[str],
                                      user_satisfaction: Optional[float],
                                      total_intents: int, total_messages: int) -> float:
        """Calculate business value score for session (0.0-1.0)"""

        score = 0.0

        # Outcome scoring
        if session_outcome == 'booking':
            score += 0.4
        elif session_outcome == 'order':
            score += 0.5
        elif session_outcome == 'inquiry':
            score += 0.2

        # Satisfaction scoring
        if user_satisfaction:
            score += (user_satisfaction / 5.0) * 0.3

        # Engagement scoring
        if total_messages > 0:
            engagement_score = min(total_intents / total_messages, 1.0) * 0.2
            score += engagement_score

        return min(score, 1.0)

    async def _cleanup_session_from_redis(self, session_id: str, session: UserSession,
                                  conversation_id: Optional[str]) -> bool:
        """Clean up session and conversation data from Redis"""

        cleanup_success = True

        try:
            # Remove from tracking lists
            if session.user_id:
                await self._remove_user_session(session.user_id, session_id)
            await self._remove_tenant_session(session.tenant_id, session_id)

            # Delete session data
            session_deleted = await self.redis.delete(self._session_key(session_id)) > 0

            # Delete conversation data if exists
            conversation_deleted = True
            if conversation_id:
                conversation_deleted = await self.redis.delete(self._conversation_key(conversation_id)) > 0

            cleanup_success = session_deleted and conversation_deleted

        except Exception as e:
            logger.error(f"Error cleaning up session {session_id} from Redis: {e}")
            cleanup_success = False

        return cleanup_success

    # ==================== UTILITY METHODS ====================

    async def cleanup_expired_sessions(self) -> Dict[str, int]:
        """
        Clean up expired sessions and conversations

        Returns:
            Dict with cleanup statistics
        """
        stats = {"sessions_cleaned": 0, "conversations_cleaned": 0}

        # Get all session keys
        session_keys = await self.redis.keys(f"{self.session_prefix}:*")

        for key in session_keys:
            if not await self.redis.exists(key):
                stats["sessions_cleaned"] += 1

        # Get all conversation keys
        conversation_keys = await self.redis.keys(f"{self.conversation_prefix}:*")

        for key in conversation_keys:
            if not await self.redis.exists(key):
                stats["conversations_cleaned"] += 1

        return stats

    async def get_session_stats(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get session statistics

        Args:
            tenant_id: Filter by tenant (optional)

        Returns:
            Dict with session statistics
        """
        if tenant_id:
            sessions = await self.get_tenant_sessions(tenant_id)
            active_count = len(sessions)
        else:
            all_sessions = await self.redis.keys(f"{self.session_prefix}:*")
            active_count = len(all_sessions)

        all_conversations = await self.redis.keys(f"{self.conversation_prefix}:*")
        conversation_count = len(all_conversations)

        return {
            "active_sessions": active_count,
            "active_conversations": conversation_count,
            "tenant_id": tenant_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# ==================== SINGLETON INSTANCE ====================

_session_manager_instance = None

def get_session_manager() -> SessionManager:
    """Get singleton session manager instance"""
    global _session_manager_instance
    if _session_manager_instance is None:
        _session_manager_instance = SessionManager()
    return _session_manager_instance


if __name__ == "__main__":

    def test_session_manager():
        """Test session manager functionality"""
        print("Testing Session Manager...")

        sm = SessionManager()

        # Test session creation
        session = sm.create_session("restaurant_123", phone_number="+919566070120")
        print(f"Created session: {session.session_id}")

        # Test session retrieval
        retrieved = sm.get_session(session.session_id)
        if retrieved:
            print(f"Retrieved session: {retrieved.phone_number}")

        # Test conversation creation
        conversation = sm.create_conversation(session.session_id, "restaurant_123")
        print(f"Created conversation: {conversation.conversation_id}")

        # Test adding messages with intent tracking
        sm.add_message(conversation.conversation_id, "user", "I want to book a table",
                      detected_intent="book_table", intent_confidence=0.95,
                      extracted_entities={"request_type": "reservation"})

        sm.add_message(conversation.conversation_id, "assistant", "Sure! For how many people?")

        sm.add_message(conversation.conversation_id, "user", "4 people at 7pm please",
                      detected_intent="book_table", intent_confidence=0.92,
                      extracted_entities={"party_size": 4, "time": "7pm", "request_type": "reservation"})

        sm.add_message(conversation.conversation_id, "user", "Also, can I see the menu?",
                      detected_intent="view_menu", intent_confidence=0.88,
                      extracted_entities={"request_type": "menu_inquiry"})

        # Test conversation retrieval
        updated_conversation = sm.get_conversation(conversation.conversation_id)
        if updated_conversation and updated_conversation.messages:
            print(f"Conversation messages: {len(updated_conversation.messages)}")

            # Test intent tracking features
            intent_history = sm.get_conversation_intent_history(conversation.conversation_id)
            print(f"Intent history: {len(intent_history)} detected intents")

            for record in intent_history:
                print(f"  Intent: {record['detected_intent']} (confidence: {record['intent_confidence']:.2f})")
                print(f"    Message: {record['content']}")
                print(f"    Entities: {record['extracted_entities']}")

            # Test dominant intent detection
            dominant = sm.get_dominant_intent(conversation.conversation_id)
            if dominant:
                print(f"Dominant intent: {dominant['intent']} (frequency: {dominant['frequency']}/{dominant['total_messages']})")

            # Test recent intents
            recent_intents = sm.get_recent_intents(conversation.conversation_id)
            print(f"Recent intents: {recent_intents}")
        else:
            print("No conversation or messages found")

        # Test statistics
        stats = sm.get_session_stats("restaurant_123")
        print(f"Session stats: {stats}")

        # Note: NoSQL persistence removed - now handled by PostgreSQL
        print("\nWARNING: NoSQL persistence deprecated - session state managed by PostgreSQL")
        sm.delete_session(session.session_id)

        print("\nSession Manager test completed!")

    test_session_manager()
