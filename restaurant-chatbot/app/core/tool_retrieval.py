"""
Tool Retrieval System
=====================
Manages tool definitions and retrieval for agent tool selection.
"""

from typing import Dict, List, Callable, Literal
import chromadb
from chromadb.config import Settings
import structlog

logger = structlog.get_logger(__name__)

AgentType = Literal["food_ordering", "booking"]

# =============================================================================
# FOOD ORDERING AGENT TOOLS (25 tools)
# =============================================================================
# IMPORTANT: These names MUST match the @tool("name") decorators in the actual
# tool factories. Mismatches cause phantom tools that waste RAG retrieval slots.

FOOD_ORDERING_TOOLS = {
    # =========================================================================
    # Menu Browsing (2 tools)
    # =========================================================================
    "search_menu": {
        "name": "search_menu",
        "description": "Search and browse restaurant menu items with optional filters for query, cuisine, or meal type. Use for any food item search.",
        "usage": "When customer wants to see menu, browse items, search for specific food, asks about any food item, filter by cuisine or meal",
        "examples": [
            "show me the menu", "do you have burgers", "what's available", "show breakfast items",
            "do you have dosa", "do you have idli", "do you have biryani", "do you have paneer",
            "do you have pizza", "do you have naan", "do you have paratha", "do you have samosa",
            "is dosa available", "is biryani available", "what food do you have", "any south indian food",
            "dosa", "idli", "vada", "biryani", "paneer", "tikka", "masala", "korma", "roti", "naan"
        ],
        "category": "menu_browsing",
        "priority": 10
    },
    "filter_by_cuisine": {
        "name": "filter_by_cuisine",
        "description": "Filter menu items by cuisine type (Italian, Chinese, Indian, etc.)",
        "usage": "When customer wants to browse by cuisine type",
        "examples": ["browse by cuisine", "show Italian food", "Chinese dishes", "filter by cuisine"],
        "category": "menu_browsing",
        "priority": 8
    },

    # =========================================================================
    # Cart Management (8 tools)
    # =========================================================================
    "add_to_cart": {
        "name": "add_to_cart",
        "description": "Add a single menu item to customer's cart with specified quantity.",
        "usage": "When customer wants to add ONE item to cart, order something, select an item, or says 'add X' or 'I want X'",
        "examples": [
            "add 2 burgers", "I want pizza", "add to cart", "order chicken",
            "add dosa", "add 2 dosa", "add masala dosa", "I want idli", "add biryani",
            "add two masala dosa", "I'll take paneer tikka", "give me 2 naan",
            "add paratha", "I want samosa", "order 3 vada", "add butter chicken"
        ],
        "category": "cart_management",
        "priority": 10
    },
    "batch_add_to_cart": {
        "name": "batch_add_to_cart",
        "description": "Add multiple different items to cart in one call. Use when customer orders 2+ items at once.",
        "usage": "When customer mentions multiple items in one message, e.g. '2 dosa and 1 idli'",
        "examples": [
            "add 2 dosa and 1 idli", "I want pizza and coke", "order burger fries and drink",
            "add masala dosa and vada", "get me 2 biryani and 1 raita", "one naan and two paneer"
        ],
        "category": "cart_management",
        "priority": 10
    },
    "correct_order": {
        "name": "correct_order",
        "description": "Fix order mistakes by removing wrong items and adding correct ones in a single call.",
        "usage": "When customer corrects their order, says 'I meant X not Y', or wants to swap items",
        "examples": [
            "I said ghee dosa not plain dosa", "no I wanted chicken not paneer",
            "that's wrong I asked for masala", "change it to butter naan",
            "remove burger and add pizza instead", "swap the fries for salad"
        ],
        "category": "cart_management",
        "priority": 9
    },
    "view_cart": {
        "name": "view_cart",
        "description": "Display current cart contents with items, quantities, and total price",
        "usage": "When customer wants to see cart, review order, check what's in cart, how much total",
        "examples": ["view cart", "show my cart", "what's in my order", "cart summary", "what's the total", "how much"],
        "category": "cart_management",
        "priority": 9
    },
    "update_quantity": {
        "name": "update_quantity",
        "description": "Update the quantity of an item already in the cart",
        "usage": "When customer wants to change quantity, increase/decrease amount",
        "examples": ["change burger quantity to 3", "make it 2", "update quantity", "increase to 5"],
        "category": "cart_management",
        "priority": 8
    },
    "remove_from_cart": {
        "name": "remove_from_cart",
        "description": "Remove a specific item from the cart",
        "usage": "When customer wants to remove, delete, or take out items from cart",
        "examples": ["remove burger", "delete pizza", "take out fries", "remove this"],
        "category": "cart_management",
        "priority": 7
    },
    "clear_cart": {
        "name": "clear_cart",
        "description": "Clear ALL items from the cart. Empties the entire cart so customer can start fresh.",
        "usage": "When customer wants to clear cart, empty cart, remove everything, or start over",
        "examples": [
            "clear cart", "clear my cart", "empty cart", "empty my cart",
            "remove everything", "start over", "delete everything from cart",
            "clear all items", "empty everything"
        ],
        "category": "cart_management",
        "priority": 8
    },
    "set_special_instructions": {
        "name": "set_special_instructions",
        "description": "Set special cooking instructions or notes for a cart item",
        "usage": "When customer wants to add special requests like extra spicy, no onions, less oil",
        "examples": ["extra spicy", "no onions please", "less oil", "make it extra crispy", "special instructions"],
        "category": "cart_management",
        "priority": 6
    },

    # =========================================================================
    # Order Processing (6 tools)
    # =========================================================================
    "checkout": {
        "name": "checkout",
        "description": "Complete the order, place it, and show payment options. MUST be called when customer is ready to order.",
        "usage": "When customer wants to checkout, place order, finalize, pay, or complete purchase",
        "examples": [
            "checkout", "place order", "proceed to checkout", "I want to checkout",
            "place my order", "done ordering", "that's all", "ready to pay",
            "finalize order", "complete order", "order now", "let's pay"
        ],
        "category": "order_processing",
        "priority": 10
    },
    "get_order_status": {
        "name": "get_order_status",
        "description": "Check the current status of customer's order",
        "usage": "When customer wants to track order, check status, see progress",
        "examples": ["track my order", "order status", "where's my food", "check order"],
        "category": "order_processing",
        "priority": 9
    },
    "get_order_receipt": {
        "name": "get_order_receipt",
        "description": "Retrieve formatted receipt for the order",
        "usage": "When customer wants receipt, bill, invoice, or order details",
        "examples": ["show receipt", "get bill", "invoice", "order summary"],
        "category": "order_processing",
        "priority": 8
    },
    "cancel_order": {
        "name": "cancel_order",
        "description": "Cancel an existing order",
        "usage": "When customer wants to cancel their order",
        "examples": ["cancel order", "cancel my order", "I want to cancel"],
        "category": "order_processing",
        "priority": 7
    },
    "get_order_history": {
        "name": "get_order_history",
        "description": "Retrieve customer's past orders",
        "usage": "When customer wants to see previous orders, order history, past purchases",
        "examples": ["show order history", "my past orders", "previous orders", "what did I order before"],
        "category": "order_processing",
        "priority": 6
    },
    "reorder_last_order": {
        "name": "reorder_last_order",
        "description": "Reorder items from the customer's most recent order",
        "usage": "When customer wants to order same thing again, repeat last order",
        "examples": ["order again", "same as last time", "reorder", "repeat my order", "reorder last order"],
        "category": "order_processing",
        "priority": 5
    },

    # =========================================================================
    # Item Details (1 tool)
    # =========================================================================
    "get_item_details": {
        "name": "get_item_details",
        "description": "Get detailed information about a specific menu item including ingredients, allergens, nutrition",
        "usage": "When customer asks about ingredients, allergens, nutrition, or details of a specific item",
        "examples": ["what's in the burger", "ingredients of dosa", "is it vegan", "allergen info", "nutrition facts"],
        "category": "menu_browsing",
        "priority": 7
    },

    # =========================================================================
    # Payment Processing (5 tools)
    # =========================================================================
    "select_payment_method": {
        "name": "select_payment_method",
        "description": "Select a payment method for the order (online, cash, or card at counter)",
        "usage": "When customer chooses how to pay after checkout",
        "examples": ["pay by card", "cash on delivery", "UPI payment", "pay online", "cash", "card at counter"],
        "category": "payment",
        "priority": 10
    },
    "initiate_payment": {
        "name": "initiate_payment",
        "description": "Initiate online payment process and generate Razorpay payment link for card/UPI/online payment",
        "usage": "When customer wants to pay online, pay by card, complete payment, or proceed with online payment after checkout",
        "examples": ["pay online", "pay by card", "I want to pay now", "online payment", "card payment", "pay with UPI", "generate payment link"],
        "category": "payment",
        "priority": 9
    },
    "check_payment_status": {
        "name": "check_payment_status",
        "description": "Check the status of a payment transaction",
        "usage": "When customer wants to check if payment was successful or check payment status",
        "examples": ["payment status", "check payment", "was payment successful", "did payment go through"],
        "category": "payment",
        "priority": 8
    },
    "verify_payment_otp": {
        "name": "verify_payment_otp",
        "description": "Verify OTP for payment authentication",
        "usage": "When customer needs to verify payment OTP",
        "examples": ["verify OTP", "payment OTP", "enter OTP"],
        "category": "payment",
        "priority": 6
    },
    "cancel_payment": {
        "name": "cancel_payment",
        "description": "Cancel an initiated payment transaction",
        "usage": "When customer wants to cancel payment or stop payment process",
        "examples": ["cancel payment", "stop payment", "don't want to pay", "abort payment"],
        "category": "payment",
        "priority": 5
    },

    # =========================================================================
    # Support & Complaints (3 tools)
    # =========================================================================
    "create_complaint": {
        "name": "create_complaint",
        "description": "Submit customer feedback, complaint, or report an issue with food or service",
        "usage": "When customer has feedback, complaint, issue, or problem with food or service",
        "examples": ["I have a complaint", "report issue", "problem with order", "food was cold", "bad service"],
        "category": "support",
        "priority": 6
    },
    "get_user_complaints": {
        "name": "get_user_complaints",
        "description": "View customer's previously submitted complaints",
        "usage": "When customer wants to see their complaints or check complaint history",
        "examples": ["my complaints", "show my complaints", "complaint history", "previous complaints"],
        "category": "support",
        "priority": 5
    },
    "check_complaint_status": {
        "name": "check_complaint_status",
        "description": "Check the status of a specific complaint",
        "usage": "When customer wants to check if their complaint has been resolved",
        "examples": ["complaint status", "is my complaint resolved", "check complaint", "complaint update"],
        "category": "support",
        "priority": 5
    },
}

# =============================================================================
# BOOKING AGENT TOOLS (4 tools)
# =============================================================================

BOOKING_TOOLS = {
    "check_table_availability": {
        "name": "check_table_availability",
        "description": "Check table availability for date, time, and party size",
        "usage": "When customer wants to check table availability",
        "examples": ["check availability", "table for 4", "any tables free"],
        "category": "booking",
        "priority": 10
    },
}

# =============================================================================
# TOOL RETRIEVER
# =============================================================================

class AgentToolRetriever:
    """Tool retrieval using in-memory ChromaDB with separate collections per agent."""

    def __init__(self):
        """Initialize in-memory ChromaDB client and collections."""
        # Create in-memory ChromaDB client
        self.client = chromadb.Client(Settings(
            is_persistent=False,
            anonymized_telemetry=False
        ))

        # Collection names
        self.collection_names = {
            "food_ordering": "food_ordering_tools",
            "booking": "booking_tools"
        }

        # Initialize collections
        self.collections = {}
        self._setup_collections()

        logger.info(
            "chromadb_retriever_initialized",
            collections=list(self.collection_names.values()),
            storage="in-memory"
        )

    def _setup_collections(self):
        """Create ChromaDB collections and index tools."""
        for agent_type, collection_name in self.collection_names.items():
            # Create collection with default embedding function
            collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.collections[agent_type] = collection

            # Index tools for this agent
            self._index_agent_tools(agent_type, collection)

    def _index_agent_tools(self, agent_type: AgentType, collection):
        """Index tools for a specific agent into ChromaDB."""
        tools = FOOD_ORDERING_TOOLS if agent_type == "food_ordering" else BOOKING_TOOLS

        documents = []
        metadatas = []
        ids = []

        for tool_name, tool_info in tools.items():
            # Create rich text for embedding
            text = f"{tool_info['description']} {tool_info['usage']} {' '.join(tool_info['examples'])}"

            documents.append(text)
            metadatas.append({
                "tool_name": tool_name,
                "description": tool_info["description"],
                "usage": tool_info["usage"],
                "category": tool_info["category"],
                "priority": tool_info["priority"]
            })
            ids.append(tool_name)

        # Add to ChromaDB
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        logger.info(
            "tools_indexed",
            agent_type=agent_type,
            collection=collection.name,
            count=len(documents)
        )

    def retrieve_tools(
        self,
        user_query: str,
        agent_type: AgentType,
        k: int = 6
    ) -> List[str]:
        """
        Retrieve top-k relevant tools from agent's collection.

        Args:
            user_query: User's message/query
            agent_type: "food_ordering" or "booking"
            k: Number of tools to retrieve

        Returns:
            List of tool names
        """
        collection = self.collections[agent_type]

        # Query ChromaDB
        results = collection.query(
            query_texts=[user_query],
            n_results=min(k, collection.count())
        )

        # Extract tool names from metadata
        tool_names = []
        if results and results['metadatas'] and len(results['metadatas']) > 0:
            for metadata in results['metadatas'][0]:
                tool_names.append(metadata["tool_name"])

        logger.info(
            "tools_retrieved",
            agent_type=agent_type,
            query=user_query[:50],
            retrieved_tools=tool_names,
            count=len(tool_names)
        )

        return tool_names

# =============================================================================
# SINGLETON INSTANCE - Initialize at module import time (eager loading)
# =============================================================================

# Initialize immediately to avoid repeated initialization during requests
_retriever_instance = AgentToolRetriever()

def get_agent_tool_retriever() -> AgentToolRetriever:
    """Get singleton instance of AgentToolRetriever (initialized at module import)."""
    return _retriever_instance

# =============================================================================
# PUBLIC API
# =============================================================================

def get_relevant_tools_for_agent(
    user_message: str,
    all_tools: Dict[str, Callable],
    agent_type: AgentType,
    max_tools: int = 6
) -> List[Callable]:
    """
    Get relevant tools for a specific agent based on user message.

    Args:
        user_message: The user's message
        all_tools: Dictionary of all available tools {name: callable}
        agent_type: "food_ordering" or "booking"
        max_tools: Maximum number of tools to return

    Returns:
        List of relevant tool callables
    """
    retriever = get_agent_tool_retriever()

    # Get relevant tool names from RAG
    relevant_tool_names = retriever.retrieve_tools(
        user_query=user_message,
        agent_type=agent_type,
        k=max_tools
    )

    # Convert tool names to callables
    relevant_tools = []
    included_names = set()
    for tool_name in relevant_tool_names:
        if tool_name in all_tools:
            relevant_tools.append(all_tools[tool_name])
            included_names.add(tool_name)
        else:
            logger.warning("rag_tool_not_in_registry", tool_name=tool_name)

    # =========================================================================
    # CRITICAL TOOL FAILSAFE
    # =========================================================================
    # Ensure critical tools are always available when the user intent clearly
    # matches, even if RAG scoring didn't rank them in the top-k.
    if agent_type == "food_ordering":
        msg_lower = user_message.lower()
        _must_include: List[str] = []

        # Menu / search intent
        if any(kw in msg_lower for kw in [
            "show menu", "menu", "what do you have", "what's available",
            "do you have", "is there", "browse", "search",
            "dosa", "idli", "biryani", "pizza", "burger", "naan",
        ]):
            _must_include.append("search_menu")

        # Checkout intent
        if any(kw in msg_lower for kw in ["checkout", "place order", "place my order", "ready to pay", "done ordering", "that's all i want", "finalize"]):
            _must_include.append("checkout")

        # View cart intent
        if any(kw in msg_lower for kw in ["view cart", "show cart", "my cart", "what's in my cart", "show my cart"]):
            _must_include.append("view_cart")

        # Clear cart intent
        if any(kw in msg_lower for kw in ["clear cart", "empty cart", "clear my cart", "empty my cart", "remove everything", "start over"]):
            _must_include.append("clear_cart")

        # Payment intent (natural language like "I want to pay online")
        if any(kw in msg_lower for kw in ["pay online", "pay cash", "pay by card", "payment", "pay now", "i want to pay"]):
            _must_include.append("select_payment_method")

        for must_tool in _must_include:
            if must_tool not in included_names and must_tool in all_tools:
                relevant_tools.append(all_tools[must_tool])
                included_names.add(must_tool)
                logger.info("critical_tool_force_included", tool_name=must_tool, query=user_message[:50])

    logger.info(
        "relevant_tools_selected",
        agent_type=agent_type,
        total_tools=len(all_tools),
        relevant_count=len(relevant_tools),
        tool_names=list(included_names),
        reduction_pct=int((1 - len(relevant_tools) / len(all_tools)) * 100) if all_tools else 0
    )

    return relevant_tools

def get_relevant_tools(
    user_message: str,
    all_tools: Dict[str, Callable],
    max_tools: int = 6
) -> List[Callable]:
    """
    Backwards compatible wrapper - defaults to food_ordering agent.

    Args:
        user_message: The user's message
        all_tools: Dictionary of all available tools
        max_tools: Maximum number of tools to return

    Returns:
        List of relevant tool callables
    """
    return get_relevant_tools_for_agent(
        user_message=user_message,
        all_tools=all_tools,
        agent_type="food_ordering",  # Default to food ordering
        max_tools=max_tools
    )
