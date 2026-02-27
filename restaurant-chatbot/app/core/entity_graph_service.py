"""
Entity Graph Service
====================
In-memory graph database using NetworkX with Redis persistence.

Provides:
- Persistent cart storage (survives server restart)
- Entity tracking (user preferences, history)

Architecture:
- NetworkX: Fast in-memory graph operations
- Redis: Persistent storage (JSON serialization)
- Auto-sync: Saves graph to Redis after modifications
"""

import json
from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import structlog
import networkx as nx
import redis
import os

logger = structlog.get_logger("core.entity_graph")


class EntityGraphService:
    """
    In-memory entity graph with Redis persistence.

    Node types:
    - USER: User entity (user_id, name, phone)
    - CART: Shopping cart (cart_id, items, subtotal)
    - MENU_ITEM: Menu item (item_id, name, price)
    - ORDER: Completed order (order_id, order_number)
    - PREFERENCE: User preference (type, value)

    Edge types:
    - HAS_CART: User -> Cart (current active cart)
    - CONTAINS: Cart -> MenuItem (cart items with quantity)
    - PREFERS: User -> Preference (dietary, spice level, etc.)
    - ORDERED: User -> Order (order history)
    - FAVORITE: User -> MenuItem (favorite items)
    """

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize graph service with Redis persistence."""
        # Use provided client or create synchronous Redis client
        if redis_client is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            self.redis = redis.from_url(redis_url, decode_responses=True)
        else:
            self.redis = redis_client

        self.graph = nx.MultiDiGraph()  # Directed graph with multiple edges
        self._graph_key = "entity_graph:global"

        # Load existing graph from Redis
        self._load_from_redis()

        logger.info("Entity graph service initialized", nodes=self.graph.number_of_nodes())

    def _load_from_redis(self) -> None:
        """Load graph from Redis persistence."""
        try:
            graph_data = self.redis.get(self._graph_key)
            if graph_data:
                data = json.loads(graph_data)
                self.graph = nx.node_link_graph(data, directed=True, multigraph=True)
                logger.info("Graph loaded from Redis", nodes=self.graph.number_of_nodes())
            else:
                logger.info("No existing graph in Redis, starting fresh")
        except Exception as e:
            logger.error("Failed to load graph from Redis", error=str(e))
            self.graph = nx.MultiDiGraph()

    def _save_to_redis(self) -> None:
        """Save graph to Redis persistence."""
        try:
            data = nx.node_link_data(self.graph)
            self.redis.set(self._graph_key, json.dumps(data))
            logger.debug("Graph saved to Redis", nodes=self.graph.number_of_nodes())
        except Exception as e:
            logger.error("Failed to save graph to Redis", error=str(e))

    # ==================== USER OPERATIONS ====================

    def get_or_create_user(self, user_id: str, **attributes) -> Dict[str, Any]:
        """Get or create user node."""
        node_id = f"user:{user_id}"

        if not self.graph.has_node(node_id):
            self.graph.add_node(
                node_id,
                type="USER",
                user_id=user_id,
                created_at=datetime.now().isoformat(),
                **attributes
            )
            self._save_to_redis()
            logger.info("User node created", user_id=user_id)

        return dict(self.graph.nodes[node_id])

    def update_user(self, user_id: str, **attributes) -> None:
        """Update user attributes."""
        node_id = f"user:{user_id}"
        if self.graph.has_node(node_id):
            self.graph.nodes[node_id].update(attributes)
            self._save_to_redis()

    # ==================== CART OPERATIONS ====================

    def get_user_cart(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's active cart (persistent across sessions)."""
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return None

        # Find HAS_CART edge
        for _, target, key, edge_data in self.graph.out_edges(user_node, keys=True, data=True):
            if edge_data.get("type") == "HAS_CART":
                cart_node = target
                cart_data = dict(self.graph.nodes[cart_node])

                # Get cart items
                items = []
                for _, item_node, key, item_edge in self.graph.out_edges(cart_node, keys=True, data=True):
                    if item_edge.get("type") == "CONTAINS":
                        item_data = dict(self.graph.nodes[item_node])
                        items.append({
                            **item_data,
                            "quantity": item_edge.get("quantity", 1)
                        })

                return {
                    **cart_data,
                    "items": items
                }

        return None

    def create_or_update_cart(self, user_id: str, items: List[Dict[str, Any]], subtotal: float) -> Dict[str, Any]:
        """
        Create or update user's cart with items.

        Args:
            user_id: User identifier
            items: List of cart items [{"menu_item_id": "...", "item_name": "...", "quantity": 2, "price": 12.99}, ...]
            subtotal: Cart subtotal

        Returns:
            Updated cart data
        """
        user_node = f"user:{user_id}"
        self.get_or_create_user(user_id)

        # Remove old cart if exists
        for _, target, key, edge_data in list(self.graph.out_edges(user_node, keys=True, data=True)):
            if edge_data.get("type") == "HAS_CART":
                old_cart = target
                # Remove old cart and its items
                self.graph.remove_node(old_cart)

        # Create new cart
        cart_id = f"cart:{user_id}:{datetime.now().timestamp()}"
        self.graph.add_node(
            cart_id,
            type="CART",
            user_id=user_id,
            subtotal=subtotal,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        # Link user -> cart
        self.graph.add_edge(user_node, cart_id, type="HAS_CART")

        # Add cart items
        for item in items:
            item_id = item.get("menu_item_id") or item.get("item_name", "unknown")
            menu_item_node = f"menu_item:{item_id}"

            # Create menu item node if not exists
            if not self.graph.has_node(menu_item_node):
                self.graph.add_node(
                    menu_item_node,
                    type="MENU_ITEM",
                    menu_item_id=item.get("menu_item_id"),
                    item_name=item.get("item_name"),
                    price=item.get("price", 0.0)
                )

            # Link cart -> menu item (with quantity)
            self.graph.add_edge(
                cart_id,
                menu_item_node,
                type="CONTAINS",
                quantity=item.get("quantity", 1)
            )

        self._save_to_redis()
        logger.info("Cart updated", user_id=user_id, items=len(items), subtotal=subtotal)

        return self.get_user_cart(user_id)

    def clear_cart(self, user_id: str) -> None:
        """Clear user's cart."""
        user_node = f"user:{user_id}"

        # Remove cart node
        for _, target, key, edge_data in list(self.graph.out_edges(user_node, keys=True, data=True)):
            if edge_data.get("type") == "HAS_CART":
                self.graph.remove_node(target)

        self._save_to_redis()
        logger.info("Cart cleared", user_id=user_id)

    # ==================== ITEM TRACKING ====================

    def set_last_mentioned_item(self, user_id: str, item_name: str, menu_item_id: Optional[str] = None) -> None:
        """
        Track last mentioned item for context resolution.

        When user says "I want that" or "add it", we know what "that"/"it" refers to.
        """
        user_node = f"user:{user_id}"
        self.get_or_create_user(user_id)

        # Remove old LAST_MENTIONED edges
        for _, target, key, edge_data in list(self.graph.out_edges(user_node, keys=True, data=True)):
            if edge_data.get("type") == "LAST_MENTIONED":
                self.graph.remove_edge(user_node, target, key)

        # Create or get menu item node
        item_id = menu_item_id or item_name
        menu_item_node = f"menu_item:{item_id}"

        if not self.graph.has_node(menu_item_node):
            self.graph.add_node(
                menu_item_node,
                type="MENU_ITEM",
                menu_item_id=menu_item_id,
                item_name=item_name
            )

        # Add LAST_MENTIONED edge
        self.graph.add_edge(
            user_node,
            menu_item_node,
            type="LAST_MENTIONED",
            timestamp=datetime.now().isoformat()
        )

        self._save_to_redis()
        logger.info("Last mentioned item set", user_id=user_id, item=item_name)

    def get_last_mentioned_item(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get last mentioned item (for context resolution)."""
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return None

        for _, target, key, edge_data in self.graph.out_edges(user_node, keys=True, data=True):
            if edge_data.get("type") == "LAST_MENTIONED":
                return dict(self.graph.nodes[target])

        return None

    # ==================== USER PREFERENCES ====================

    def add_preference(self, user_id: str, preference_type: str, value: Any) -> None:
        """
        Add user preference.

        Examples:
        - add_preference("user123", "spice_level", "medium")
        - add_preference("user123", "dietary", "vegetarian")
        - add_preference("user123", "allergic_to", "nuts")
        """
        user_node = f"user:{user_id}"
        self.get_or_create_user(user_id)

        pref_id = f"pref:{user_id}:{preference_type}"

        if not self.graph.has_node(pref_id):
            self.graph.add_node(
                pref_id,
                type="PREFERENCE",
                preference_type=preference_type,
                value=value
            )
            self.graph.add_edge(user_node, pref_id, type="PREFERS")
        else:
            self.graph.nodes[pref_id]["value"] = value

        self._save_to_redis()
        logger.info("Preference added", user_id=user_id, type=preference_type, value=value)

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get all user preferences."""
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return {}

        preferences = {}
        for _, target, key, edge_data in self.graph.out_edges(user_node, keys=True, data=True):
            if edge_data.get("type") == "PREFERS":
                pref_data = self.graph.nodes[target]
                preferences[pref_data["preference_type"]] = pref_data["value"]

        return preferences

    # ==================== ORDER HISTORY ====================

    def add_order(self, user_id: str, order_id: str, order_number: str, items: List[Dict[str, Any]], total: float) -> None:
        """Add completed order to user's history."""
        user_node = f"user:{user_id}"
        self.get_or_create_user(user_id)

        order_node = f"order:{order_id}"
        self.graph.add_node(
            order_node,
            type="ORDER",
            order_id=order_id,
            order_number=order_number,
            total=total,
            created_at=datetime.now().isoformat()
        )

        # Link user -> order
        self.graph.add_edge(user_node, order_node, type="ORDERED")

        # Link order -> menu items
        for item in items:
            item_id = item.get("menu_item_id") or item.get("item_name")
            menu_item_node = f"menu_item:{item_id}"

            if not self.graph.has_node(menu_item_node):
                self.graph.add_node(
                    menu_item_node,
                    type="MENU_ITEM",
                    menu_item_id=item.get("menu_item_id"),
                    item_name=item.get("item_name")
                )

            self.graph.add_edge(order_node, menu_item_node, type="CONTAINS", quantity=item.get("quantity", 1))

        self._save_to_redis()
        logger.info("Order added to history", user_id=user_id, order_number=order_number)

    def get_last_order(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's most recent order (for "same as last time")."""
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return None

        # Find all ORDERED edges
        orders = []
        for _, target, key, edge_data in self.graph.out_edges(user_node, keys=True, data=True):
            if edge_data.get("type") == "ORDERED":
                order_data = dict(self.graph.nodes[target])

                # Get order items
                items = []
                for _, item_node, key, item_edge in self.graph.out_edges(target, keys=True, data=True):
                    if item_edge.get("type") == "CONTAINS":
                        item_data = dict(self.graph.nodes[item_node])
                        items.append({
                            **item_data,
                            "quantity": item_edge.get("quantity", 1)
                        })

                orders.append({
                    **order_data,
                    "items": items
                })

        # Return most recent
        if orders:
            orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return orders[0]

        return None

    # ==================== FAVORITES ====================

    def add_favorite(self, user_id: str, item_name: str, menu_item_id: Optional[str] = None) -> None:
        """Mark item as favorite."""
        user_node = f"user:{user_id}"
        self.get_or_create_user(user_id)

        item_id = menu_item_id or item_name
        menu_item_node = f"menu_item:{item_id}"

        if not self.graph.has_node(menu_item_node):
            self.graph.add_node(
                menu_item_node,
                type="MENU_ITEM",
                menu_item_id=menu_item_id,
                item_name=item_name
            )

        self.graph.add_edge(user_node, menu_item_node, type="FAVORITE")
        self._save_to_redis()
        logger.info("Favorite added", user_id=user_id, item=item_name)

    def get_favorites(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user's favorite items."""
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return []

        favorites = []
        for _, target, key, edge_data in self.graph.out_edges(user_node, keys=True, data=True):
            if edge_data.get("type") == "FAVORITE":
                favorites.append(dict(self.graph.nodes[target]))

        return favorites

    # ==================== CONVERSATION STATE TRACKING ====================

    def set_active_intent(
        self,
        user_id: str,
        session_id: str,
        sub_intent: str,
        entities: Dict[str, Any],
        entity_collection_step: Optional[str] = None
    ) -> None:
        """
        Store active conversation state in graph.
        
        Tracks current intent + entities for multi-turn conversations.
        Enables context persistence within session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            sub_intent: Current sub-intent (e.g., "manage_cart")
            entities: Collected entities so far
            entity_collection_step: If collecting entities, which one we're waiting for
        """
        user_node = f"user:{user_id}"
        self.get_or_create_user(user_id)

        # Remove old active intent edges for this session
        for _, target, key, edge_data in list(self.graph.out_edges(user_node, keys=True, data=True)):
            if edge_data.get("type") == "HAS_ACTIVE_INTENT" and edge_data.get("session_id") == session_id:
                self.graph.remove_edge(user_node, target, key)
                # Also remove the conversation turn node if no other edges point to it
                if self.graph.in_degree(target) == 0:
                    self.graph.remove_node(target)

        # Create new conversation turn node
        turn_id = f"conv_turn:{session_id}:{datetime.now().timestamp()}"
        self.graph.add_node(
            turn_id,
            type="CONVERSATION_TURN",
            session_id=session_id,
            sub_intent=sub_intent,
            entities=entities,
            entity_collection_step=entity_collection_step,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        # Link user -> conversation turn
        self.graph.add_edge(
            user_node,
            turn_id,
            type="HAS_ACTIVE_INTENT",
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )

        self._save_to_redis()
        logger.info(
            "Active intent set in graph",
            user_id=user_id,
            session_id=session_id,
            sub_intent=sub_intent,
            entity_collection_step=entity_collection_step
        )

    def get_active_intent(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve active conversation state from graph.
        
        Returns current intent + entities for the session.
        
        Args:
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Dict with {sub_intent, entities, entity_collection_step, timestamp} or None
        """
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return None

        # Find HAS_ACTIVE_INTENT edge for this session
        for _, target, key, edge_data in self.graph.out_edges(user_node, keys=True, data=True):
            if edge_data.get("type") == "HAS_ACTIVE_INTENT" and edge_data.get("session_id") == session_id:
                turn_data = dict(self.graph.nodes[target])
                turn_data["timestamp"] = edge_data.get("timestamp")
                return turn_data

        return None

    def clear_active_intent(self, user_id: str, session_id: str) -> None:
        """Clear active conversation state for session."""
        user_node = f"user:{user_id}"

        if not self.graph.has_node(user_node):
            return

        # Remove active intent edges for this session
        for _, target, key, edge_data in list(self.graph.out_edges(user_node, keys=True, data=True)):
            if edge_data.get("type") == "HAS_ACTIVE_INTENT" and edge_data.get("session_id") == session_id:
                self.graph.remove_edge(user_node, target, key)
                # Remove the conversation turn node
                if self.graph.in_degree(target) == 0:
                    self.graph.remove_node(target)

        self._save_to_redis()
        logger.info("Active intent cleared from graph", user_id=user_id, session_id=session_id)


    # ==================== UTILITY METHODS ====================

    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics."""
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "node_types": {
                node_type: sum(1 for _, data in self.graph.nodes(data=True) if data.get("type") == node_type)
                for node_type in ["USER", "CART", "MENU_ITEM", "ORDER", "PREFERENCE"]
            }
        }


# Global singleton
_entity_graph_service: Optional[EntityGraphService] = None


def get_entity_graph_service() -> EntityGraphService:
    """Get or create global entity graph service."""
    global _entity_graph_service
    if _entity_graph_service is None:
        _entity_graph_service = EntityGraphService()
    return _entity_graph_service


__all__ = ["EntityGraphService", "get_entity_graph_service"]
