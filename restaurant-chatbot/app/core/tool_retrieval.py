"""
RAG-based Tool Retrieval System with Agent-Specific Collections
================================================================
Each agent has its own ChromaDB collection for focused tool retrieval.
- Food Ordering Agent: 22 tools
- Booking Agent: 4 tools
- Complaint handling: 3 tools (integrated in food ordering)

Benefits:
- 80-90% context reduction per agent
- No cross-agent tool pollution
- Better semantic accuracy
- <4s response time target
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Callable, Literal
import structlog
from functools import lru_cache

logger = structlog.get_logger()

AgentType = Literal["food_ordering", "booking"]


# ============================================================================
# FOOD ORDERING AGENT TOOLS (22 tools)
# ============================================================================

FOOD_ORDERING_TOOLS = {
    # Menu Browsing (3 tools)
    "search_menu": {
        "name": "search_menu",
        "description": "Search and browse restaurant menu items with filters",
        "usage": "When customer wants to see menu, browse items, search for specific food, filter by category",
        "examples": ["show me the menu", "do you have burgers", "what's available", "show me chicken items", "browse menu", "show lunch items"],
        "category": "menu_browsing",
        "priority": 10
    },

    "filter_by_cuisine": {
        "name": "filter_by_cuisine",
        "description": "Filter menu items by cuisine type (Italian, Asian, American, Indian, etc.)",
        "usage": "When customer wants to browse by cuisine or see available cuisines",
        "examples": ["browse by cuisine", "show Italian dishes", "what cuisines do you have", "show me Asian food", "Indian options"],
        "category": "menu_browsing",
        "priority": 8
    },

    "show_popular_items": {
        "name": "show_popular_items",
        "description": "Show popular, recommended, or best-selling menu items",
        "usage": "When customer asks for popular items, recommendations, or best sellers",
        "examples": ["show popular items", "what's popular", "best sellers", "what do you recommend", "what's good here", "trending items"],
        "category": "menu_browsing",
        "priority": 8
    },

    # Cart Management (7 tools)
    "add_to_cart": {
        "name": "add_to_cart",
        "description": "Add food items to shopping cart with quantity",
        "usage": "When customer wants to order or add items",
        "examples": ["add 2 burgers", "I want 3 Chicken Fillet Burger", "order one pizza", "get me 2 coffees", "add to cart"],
        "category": "cart_management",
        "priority": 10
    },

    "view_cart": {
        "name": "view_cart",
        "description": "View current shopping cart contents and total",
        "usage": "When customer wants to see their cart or check what they ordered",
        "examples": ["view cart", "show my cart", "what's in my cart", "show my order", "cart status"],
        "category": "cart_management",
        "priority": 9
    },

    "remove_from_cart": {
        "name": "remove_from_cart",
        "description": "Remove items from shopping cart",
        "usage": "When customer wants to remove or delete items from cart",
        "examples": ["remove burger from cart", "delete the pizza", "take out the coffee", "I don't want the salad anymore"],
        "category": "cart_management",
        "priority": 7
    },

    "update_quantity": {
        "name": "update_quantity",
        "description": "Update quantity of items already in cart (not add/remove, just change number)",
        "usage": "When customer wants to change item quantity",
        "examples": ["change burger quantity to 3", "make it 5 burgers", "update to 2", "change quantity to 4"],
        "category": "cart_management",
        "priority": 7
    },

    "clear_cart": {
        "name": "clear_cart",
        "description": "Empty the entire shopping cart",
        "usage": "When customer wants to start over or clear everything",
        "examples": ["clear cart", "empty my cart", "start over", "clear everything", "reset cart"],
        "category": "cart_management",
        "priority": 5
    },

    "set_special_instructions": {
        "name": "set_special_instructions",
        "description": "Add special cooking instructions or delivery notes to cart items",
        "usage": "When customer has special requests like 'extra spicy', 'no onions', etc.",
        "examples": ["make it extra spicy", "no onions please", "add extra cheese", "well done", "less salt"],
        "category": "cart_management",
        "priority": 6
    },

    "get_item_details": {
        "name": "get_item_details",
        "description": "Get detailed information about a specific menu item",
        "usage": "When customer asks for details, ingredients, or info about an item",
        "examples": ["what's in the burger", "tell me about this item", "ingredients of pizza", "what's this made of", "nutritional info"],
        "category": "cart_management",
        "priority": 5
    },

    # Order Processing (7 tools)
    "checkout": {
        "name": "checkout",
        "description": "Complete order and proceed to payment - creates order in database",
        "usage": "When customer wants to finalize order, pay, or complete checkout",
        "examples": ["checkout", "place order", "checkout for dine in", "pay now", "finalize order", "proceed to checkout", "I'm ready to order"],
        "category": "order_processing",
        "priority": 10
    },

    "get_order_status": {
        "name": "get_order_status",
        "description": "Check status of an existing order",
        "usage": "When customer wants to track their order or check order status",
        "examples": ["track my order", "where is my order", "order status", "check my order", "how's my order coming"],
        "category": "order_processing",
        "priority": 8
    },

    "get_order_receipt": {
        "name": "get_order_receipt",
        "description": "Get detailed receipt for a completed order",
        "usage": "When customer wants to see receipt, invoice, or bill",
        "examples": ["show receipt", "view my receipt", "show me the bill", "I need my invoice", "print receipt"],
        "category": "order_processing",
        "priority": 7
    },

    "get_order_history": {
        "name": "get_order_history",
        "description": "View past orders and order history",
        "usage": "When customer wants to see previous orders",
        "examples": ["show my orders", "order history", "past orders", "my previous orders", "what did I order before"],
        "category": "order_processing",
        "priority": 6
    },

    "reorder_last_order": {
        "name": "reorder_last_order",
        "description": "Reorder items from previous order",
        "usage": "When customer wants to repeat their last order",
        "examples": ["reorder my last order", "order the same thing", "repeat my order", "same as last time"],
        "category": "order_processing",
        "priority": 7
    },

    "cancel_order": {
        "name": "cancel_order",
        "description": "Cancel a pending order",
        "usage": "When customer wants to cancel their current or recent order",
        "examples": ["cancel my order", "cancel the order", "I want to cancel", "stop my order"],
        "category": "order_processing",
        "priority": 6
    },

    "reorder_by_id": {
        "name": "reorder_by_id",
        "description": "Reorder items from a specific past order by order ID",
        "usage": "When customer wants to reorder a specific previous order",
        "examples": ["reorder order #123", "repeat order ORD-ABC", "reorder that order"],
        "category": "order_processing",
        "priority": 5
    },

    # Payment Processing (5 tools)
    "initiate_payment": {
        "name": "initiate_payment",
        "description": "Start payment process after checkout",
        "usage": "When customer wants to pay for their order",
        "examples": ["initiate payment", "start payment", "I want to pay", "proceed to payment"],
        "category": "payment",
        "priority": 8
    },

    "submit_card_details": {
        "name": "submit_card_details",
        "description": "Submit credit/debit card details for payment",
        "usage": "When customer provides card information",
        "examples": ["pay with card", "use my credit card", "card payment"],
        "category": "payment",
        "priority": 7
    },

    "verify_payment_otp": {
        "name": "verify_payment_otp",
        "description": "Verify OTP for payment authorization",
        "usage": "When customer needs to verify payment OTP",
        "examples": ["verify OTP", "enter OTP", "payment verification code"],
        "category": "payment",
        "priority": 6
    },

    "check_payment_status": {
        "name": "check_payment_status",
        "description": "Check status of payment transaction",
        "usage": "When customer wants to check if payment went through",
        "examples": ["check payment", "payment status", "did my payment go through"],
        "category": "payment",
        "priority": 6
    },

    "cancel_payment": {
        "name": "cancel_payment",
        "description": "Cancel ongoing payment transaction",
        "usage": "When customer wants to cancel payment",
        "examples": ["cancel payment", "stop payment", "I don't want to pay"],
        "category": "payment",
        "priority": 5
    },
}

# Complaint Tools (3 tools - part of food ordering agent)
COMPLAINT_TOOLS = {
    "create_complaint": {
        "name": "create_complaint",
        "description": "Log customer complaints about food quality, service, or other issues",
        "usage": "When customer complains about food, service, wait time, billing, etc.",
        "examples": ["the burger was cold", "service is too slow", "this tastes bad", "I have a complaint", "food quality issue"],
        "category": "support",
        "priority": 8
    },

    "get_complaints": {
        "name": "get_complaints",
        "description": "View customer's complaint history",
        "usage": "When customer wants to see their previous complaints",
        "examples": ["show my complaints", "my complaint history", "what complaints did I make", "view complaints"],
        "category": "support",
        "priority": 4
    },

    "check_complaint_status": {
        "name": "check_complaint_status",
        "description": "Check status of a specific complaint",
        "usage": "When customer wants to check on their complaint",
        "examples": ["check my complaint", "complaint status", "what happened to my complaint", "update on complaint"],
        "category": "support",
        "priority": 5
    },
}

# Merge food ordering and complaint tools
FOOD_ORDERING_TOOLS.update(COMPLAINT_TOOLS)


# ============================================================================
# BOOKING AGENT TOOLS (4 tools)
# ============================================================================

BOOKING_TOOLS = {
    "check_table_availability": {
        "name": "check_table_availability",
        "description": "Check if tables are available for reservation at specific date/time",
        "usage": "When customer wants to know if tables are available",
        "examples": ["do you have tables available", "check availability", "can I book for 4 people", "is there space tonight"],
        "category": "booking",
        "priority": 10
    },

    "make_reservation": {
        "name": "make_reservation",
        "description": "Book a table for customer with date, time, party size",
        "usage": "When customer wants to reserve a table",
        "examples": ["book a table", "make reservation", "reserve for 6 pm", "table for 4 people"],
        "category": "booking",
        "priority": 10
    },

    "get_my_bookings": {
        "name": "get_my_bookings",
        "description": "View customer's booking history and upcoming reservations",
        "usage": "When customer wants to see their bookings",
        "examples": ["show my bookings", "my reservations", "upcoming bookings", "booking history"],
        "category": "booking",
        "priority": 7
    },

    "cancel_reservation": {
        "name": "cancel_reservation",
        "description": "Cancel an existing table reservation",
        "usage": "When customer wants to cancel their booking",
        "examples": ["cancel my booking", "cancel reservation", "I can't make it", "remove my reservation"],
        "category": "booking",
        "priority": 7
    },
}


# ============================================================================
# CHROMADB WITH AGENT-SPECIFIC COLLECTIONS
# ============================================================================

class AgentToolRetriever:
    """RAG-based tool retrieval with separate collections per agent."""

    def __init__(self):
        """Initialize ChromaDB with agent-specific collections."""
        # Use in-memory ChromaDB
        self.client = chromadb.Client(Settings(
            anonymized_telemetry=False,
            allow_reset=True
        ))

        # Create separate collections for each agent
        self.collections = {}

        # Food Ordering Collection
        try:
            self.collections["food_ordering"] = self.client.create_collection(
                name="food_ordering_tools",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            self.collections["food_ordering"] = self.client.get_collection("food_ordering_tools")

        # Booking Collection
        try:
            self.collections["booking"] = self.client.create_collection(
                name="booking_tools",
                metadata={"hnsw:space": "cosine"}
            )
        except Exception:
            self.collections["booking"] = self.client.get_collection("booking_tools")

        # Index tools into their respective collections
        self._index_tools()

        logger.info(
            "agent_tool_retriever_initialized",
            food_ordering_tools=len(FOOD_ORDERING_TOOLS),
            booking_tools=len(BOOKING_TOOLS),
            total_tools=len(FOOD_ORDERING_TOOLS) + len(BOOKING_TOOLS)
        )

    def _index_tools(self):
        """Index tools into agent-specific collections."""
        # Index food ordering tools
        self._index_collection("food_ordering", FOOD_ORDERING_TOOLS)

        # Index booking tools
        self._index_collection("booking", BOOKING_TOOLS)

    def _index_collection(self, agent_type: str, tool_catalog: Dict[str, Any]):
        """Index tools for a specific agent."""
        documents = []
        metadatas = []
        ids = []

        for tool_name, tool_data in tool_catalog.items():
            # Create rich document
            doc = f"""
Tool: {tool_data['name']}
Description: {tool_data['description']}
Usage: {tool_data['usage']}
Examples: {', '.join(tool_data['examples'])}
Category: {tool_data['category']}
            """.strip()

            documents.append(doc)
            metadatas.append({
                "tool_name": tool_name,
                "category": tool_data["category"],
                "priority": tool_data["priority"],
                "agent": agent_type
            })
            ids.append(f"{agent_type}_{tool_name}")

        # Add to collection
        self.collections[agent_type].add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(
            "tools_indexed",
            agent=agent_type,
            count=len(documents)
        )

    def retrieve_tools(
        self,
        user_query: str,
        agent_type: AgentType,
        k: int = 6
    ) -> List[str]:
        """
        Retrieve top-k most relevant tools for user query FROM AGENT'S COLLECTION ONLY.

        Args:
            user_query: The user's message/intent
            agent_type: Which agent (food_ordering or booking)
            k: Number of tools to retrieve (default 6)

        Returns:
            List of tool names, ordered by relevance
        """
        try:
            # Query ONLY the agent's collection
            collection = self.collections[agent_type]
            results = collection.query(
                query_texts=[user_query],
                n_results=k
            )

            tool_names = []
            if results and results['ids'] and len(results['ids']) > 0:
                # Extract tool names from IDs (remove agent prefix)
                tool_names = [
                    id.replace(f"{agent_type}_", "")
                    for id in results['ids'][0]
                ]

            logger.info(
                "tools_retrieved_for_agent",
                agent=agent_type,
                query=user_query[:50],
                tools=tool_names,
                count=len(tool_names)
            )

            return tool_names

        except Exception as e:
            logger.error("tool_retrieval_failed", agent=agent_type, error=str(e))
            # Fallback to essential tools for this agent
            if agent_type == "food_ordering":
                return ["search_menu", "add_to_cart", "view_cart", "checkout", "create_complaint"]
            else:  # booking
                return ["check_table_availability", "make_reservation", "get_my_bookings", "cancel_reservation"]


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

@lru_cache(maxsize=1)
def get_agent_tool_retriever() -> AgentToolRetriever:
    """Get singleton AgentToolRetriever instance."""
    return AgentToolRetriever()


# ============================================================================
# AGENT-SPECIFIC TOOL FILTERING
# ============================================================================

def get_relevant_tools_for_agent(
    user_message: str,
    all_tools: Dict[str, Callable],
    agent_type: AgentType,
    max_tools: int = 6
) -> List[Callable]:
    """
    Get only relevant tools for the user message FROM THIS AGENT'S COLLECTION.

    Args:
        user_message: User's input message
        all_tools: Dictionary of {tool_name: tool_function}
        agent_type: Which agent (food_ordering or booking)
        max_tools: Maximum number of tools to return

    Returns:
        List of relevant tool functions
    """
    retriever = get_agent_tool_retriever()
    relevant_tool_names = retriever.retrieve_tools(user_message, agent_type, k=max_tools)

    # Return tool functions in order of relevance
    relevant_tools = []
    for tool_name in relevant_tool_names:
        if tool_name in all_tools:
            relevant_tools.append(all_tools[tool_name])

    logger.info(
        "filtered_tools_for_agent",
        agent=agent_type,
        original_count=len(all_tools),
        filtered_count=len(relevant_tools),
        reduction_pct=int((1 - len(relevant_tools)/len(all_tools)) * 100) if all_tools else 0
    )

    return relevant_tools


# Convenience wrapper for backwards compatibility
def get_relevant_tools(user_message: str, all_tools: Dict[str, Callable], max_tools: int = 6) -> List[Callable]:
    """Default to food_ordering agent for backwards compatibility."""
    return get_relevant_tools_for_agent(user_message, all_tools, "food_ordering", max_tools)
