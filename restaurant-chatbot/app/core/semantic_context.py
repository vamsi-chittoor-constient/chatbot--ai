"""
Semantic Context Manager
========================
Deterministic entity tracking for conversation context.

v20: No LLM preprocessing - graph updated by tool outputs.

Features:
- Entity graph per session (persisted to Redis)
- Tracks displayed menu (for "the 2nd one" resolution)
- Tracks last mentioned items (for "it", "that" resolution)
- Cart read directly from Redis (single source of truth)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import structlog

logger = structlog.get_logger(__name__)

# Redis key prefix for entity graphs
ENTITY_GRAPH_PREFIX = "entity_graph:"
ENTITY_GRAPH_TTL = 3600 * 24  # 24 hours


@dataclass
class EntityGraph:
    """
    Session-scoped entity graph for tracking conversation context.
    Persisted to Redis for durability across server restarts.

    Tracks:
    - Recently mentioned items (for context resolution)
    - Displayed menu order (for "the 2nd one" type references)
    - User preferences expressed in conversation

    NOTE: Cart items are read directly from Redis cart (single source of truth)
    """
    session_id: str
    last_mentioned_item: Optional[str] = None
    last_mentioned_items: List[str] = field(default_factory=list)  # For "them", "those"
    last_action: Optional[str] = None
    displayed_menu: List[str] = field(default_factory=list)  # Ordered list of menu items last shown
    preferences: Dict[str, Any] = field(default_factory=dict)

    def set_displayed_menu(self, items: List[str]):
        """Track the menu items displayed to user (in order)."""
        self.displayed_menu = items
        logger.debug("displayed_menu_tracked", session_id=self.session_id, items=items[:5])
        # Persist to Redis
        _save_entity_graph(self)

    def update_last_mentioned(self, item_name: str):
        """Update last mentioned item for context resolution."""
        self.last_mentioned_item = item_name
        if item_name not in self.last_mentioned_items:
            self.last_mentioned_items.append(item_name)
        # Keep only last 5 items
        self.last_mentioned_items = self.last_mentioned_items[-5:]
        # Persist to Redis
        _save_entity_graph(self)

    def get_item_by_position(self, position: int) -> Optional[str]:
        """Get menu item by position (1-indexed for natural language)."""
        if self.displayed_menu and 0 < position <= len(self.displayed_menu):
            return self.displayed_menu[position - 1]
        return None

    def get_context_summary(self) -> str:
        """
        Get a brief summary of the current context state.
        Used for initial crew context without a specific query.
        """
        parts = []
        if self.last_mentioned_item:
            parts.append(f"Last item: {self.last_mentioned_item}")
        if self.displayed_menu:
            parts.append(f"Menu shown: {len(self.displayed_menu)} items")
        cart_items = _get_cart_items_from_redis(self.session_id)
        if cart_items:
            parts.append(f"Cart: {len(cart_items)} items")
        return " | ".join(parts) if parts else "New conversation"

    def get_relevant_context(self, user_query: str) -> str:
        """
        RAG-based context retrieval - only include entities relevant to user query.
        Reduces token usage by 80-95% compared to full context.

        Returns minimal context based on query keywords.
        """
        query_lower = user_query.lower()
        parts = []

        # CRITICAL: Always include if user mentions pronouns/positions
        pronoun_keywords = ['it', 'that', 'this', 'them', 'those', 'one', '1st', '2nd', '3rd', 'first', 'second', 'third']
        needs_reference_context = any(keyword in query_lower for keyword in pronoun_keywords)

        if needs_reference_context:
            if self.last_mentioned_item:
                parts.append(f"Last: {self.last_mentioned_item}")
            if self.displayed_menu and any(pos in query_lower for pos in ['1', '2', '3', 'first', 'second', 'third', 'one']):
                # Only include first 3 items if position mentioned
                menu_str = ", ".join(f"{i+1}. {item}" for i, item in enumerate(self.displayed_menu[:3]))
                parts.append(f"Menu: {menu_str}")

        # Include cart only if user asks about cart/order/checkout
        cart_keywords = ['cart', 'order', 'checkout', 'remove', 'view', 'show', 'what', 'bill', 'total']
        if any(keyword in query_lower for keyword in cart_keywords):
            cart_items = _get_cart_items_from_redis(self.session_id)
            if cart_items:
                parts.append(f"Cart: {', '.join(cart_items[:5])}")  # Max 5 items

        # If query is very short (likely follow-up), include last mentioned
        if len(user_query.split()) <= 3 and self.last_mentioned_item:
            parts.append(f"Last: {self.last_mentioned_item}")

        return " | ".join(parts) if parts else "No prior context"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Redis storage."""
        return {
            "session_id": self.session_id,
            "last_mentioned_item": self.last_mentioned_item,
            "last_mentioned_items": self.last_mentioned_items,
            "last_action": self.last_action,
            "displayed_menu": self.displayed_menu,
            "preferences": self.preferences,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EntityGraph":
        """Create from dictionary (Redis retrieval)."""
        return cls(
            session_id=data.get("session_id", ""),
            last_mentioned_item=data.get("last_mentioned_item"),
            last_mentioned_items=data.get("last_mentioned_items", []),
            last_action=data.get("last_action"),
            displayed_menu=data.get("displayed_menu", []),
            preferences=data.get("preferences", {}),
        )


# ============================================================================
# REDIS PERSISTENCE
# ============================================================================

def _get_redis_client():
    """Get sync Redis client."""
    try:
        from app.core.redis import get_sync_redis_client
        return get_sync_redis_client()
    except Exception as e:
        logger.debug("redis_client_unavailable", error=str(e))
        return None


def _save_entity_graph(graph: EntityGraph):
    """Save entity graph to Redis."""
    try:
        client = _get_redis_client()
        if client:
            key = f"{ENTITY_GRAPH_PREFIX}{graph.session_id}"
            client.setex(key, ENTITY_GRAPH_TTL, json.dumps(graph.to_dict()))
            logger.debug("entity_graph_saved", session_id=graph.session_id)
    except Exception as e:
        logger.debug("entity_graph_save_failed", error=str(e))


def _load_entity_graph(session_id: str) -> Optional[EntityGraph]:
    """Load entity graph from Redis."""
    try:
        client = _get_redis_client()
        if client:
            key = f"{ENTITY_GRAPH_PREFIX}{session_id}"
            data = client.get(key)
            if data:
                return EntityGraph.from_dict(json.loads(data))
    except Exception as e:
        logger.debug("entity_graph_load_failed", error=str(e))
    return None


def _get_cart_items_from_redis(session_id: str) -> List[str]:
    """
    Get cart item names from PostgreSQL session_cart (event-sourced).
    This is the single source of truth for cart state.
    """
    try:
        from app.core.session_events import get_sync_session_tracker
        tracker = get_sync_session_tracker(session_id)
        cart_data = tracker.get_cart_summary()
        items = cart_data.get("items", [])
        # PostgreSQL returns item_name, fallback to name for compat
        return [item.get("item_name") or item.get("name", "") for item in items if item.get("item_name") or item.get("name")]
    except Exception as e:
        logger.debug("cart_read_failed", error=str(e))
        return []


# ============================================================================
# PUBLIC API
# ============================================================================

# In-memory cache (backed by Redis)
_ENTITY_GRAPHS: Dict[str, EntityGraph] = {}


def get_entity_graph(session_id: str) -> EntityGraph:
    """
    Get entity graph for session.
    Checks in-memory cache first, then Redis, then creates new.
    """
    # Check in-memory cache
    if session_id in _ENTITY_GRAPHS:
        return _ENTITY_GRAPHS[session_id]

    # Try loading from Redis
    graph = _load_entity_graph(session_id)
    if graph:
        _ENTITY_GRAPHS[session_id] = graph
        return graph

    # Create new graph
    graph = EntityGraph(session_id=session_id)
    _ENTITY_GRAPHS[session_id] = graph
    return graph


def clear_entity_graph(session_id: str):
    """Clear entity graph for session (from memory and Redis)."""
    # Clear from memory
    if session_id in _ENTITY_GRAPHS:
        del _ENTITY_GRAPHS[session_id]

    # Clear from Redis
    try:
        client = _get_redis_client()
        if client:
            key = f"{ENTITY_GRAPH_PREFIX}{session_id}"
            client.delete(key)
            logger.debug("entity_graph_cleared", session_id=session_id)
    except Exception as e:
        logger.debug("entity_graph_clear_failed", error=str(e))


def save_entity_graph(session_id: str):
    """Explicitly save current entity graph to Redis."""
    if session_id in _ENTITY_GRAPHS:
        _save_entity_graph(_ENTITY_GRAPHS[session_id])
