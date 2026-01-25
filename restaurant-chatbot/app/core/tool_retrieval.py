"""
RAG-based Tool Retrieval System with Agent-Specific Collections (ChromaDB)
===========================================================================
Each agent has its own ChromaDB collection for focused tool retrieval.
- Food Ordering Agent: 25 tools
- Booking Agent: 4 tools
- Uses in-memory ChromaDB (already included in CrewAI dependencies)
- No additional dependencies required
"""

from typing import Dict, List, Callable, Literal
import chromadb
from chromadb.config import Settings
import structlog

logger = structlog.get_logger(__name__)

AgentType = Literal["food_ordering", "booking"]

# =============================================================================
# FOOD ORDERING AGENT TOOLS (29 tools)
# =============================================================================

FOOD_ORDERING_TOOLS = {
    # =========================================================================
    # Menu Browsing (3 tools)
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
    "show_popular_items": {
        "name": "show_popular_items",
        "description": "Display popular and recommended menu items based on ratings and recommendations",
        "usage": "When customer asks for popular, recommended, best-sellers, or trending items",
        "examples": ["show popular items", "what's recommended", "best sellers", "trending food"],
        "category": "menu_browsing",
        "priority": 9
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
    # Cart Management (7 tools)
    # =========================================================================
    "add_to_cart": {
        "name": "add_to_cart",
        "description": "Add menu items to customer's cart with specified quantity. Use when customer wants to order any food item.",
        "usage": "When customer wants to add items to cart, order something, select items, or says 'add X' or 'I want X'",
        "examples": [
            "add 2 burgers", "I want pizza", "add to cart", "order chicken",
            "add dosa", "add 2 dosa", "add masala dosa", "I want idli", "add biryani",
            "add two masala dosa", "I'll take paneer tikka", "give me 2 naan",
            "add paratha", "I want samosa", "order 3 vada", "add butter chicken"
        ],
        "category": "cart_management",
        "priority": 10
    },
    "view_cart": {
        "name": "view_cart",
        "description": "Display current cart contents with items, quantities, and total price",
        "usage": "When customer wants to see cart, review order, check what's in cart",
        "examples": ["view cart", "show my cart", "what's in my order", "cart summary"],
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
        "description": "Remove all items from the cart and start fresh",
        "usage": "When customer wants to empty cart, clear everything, start over",
        "examples": ["clear cart", "empty my cart", "remove everything", "start over"],
        "category": "cart_management",
        "priority": 6
    },
    "get_cart_total": {
        "name": "get_cart_total",
        "description": "Get the total price of all items in the cart",
        "usage": "When customer asks for total, price, cost, or amount",
        "examples": ["what's the total", "how much", "cart price", "total cost"],
        "category": "cart_management",
        "priority": 7
    },
    "get_cart_item_count": {
        "name": "get_cart_item_count",
        "description": "Get the number of items currently in the cart",
        "usage": "When customer asks how many items in cart",
        "examples": ["how many items", "cart count", "number of items"],
        "category": "cart_management",
        "priority": 5
    },

    # =========================================================================
    # Order Processing (7 tools)
    # =========================================================================
    "checkout": {
        "name": "checkout",
        "description": "Complete the order and place it with optional order type (dine-in, takeaway, delivery)",
        "usage": "When customer wants to checkout, place order, finalize, pay, or complete purchase",
        "examples": ["checkout", "place order", "proceed to checkout", "checkout for dine in", "pay now"],
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
    "reorder_previous": {
        "name": "reorder_previous",
        "description": "Reorder items from a previous order",
        "usage": "When customer wants to order same thing again, repeat order",
        "examples": ["order again", "same as last time", "reorder", "repeat my order"],
        "category": "order_processing",
        "priority": 5
    },
    "get_estimated_delivery_time": {
        "name": "get_estimated_delivery_time",
        "description": "Get estimated delivery or preparation time for order",
        "usage": "When customer asks how long, when will it arrive, delivery time",
        "examples": ["how long", "when will it arrive", "delivery time", "estimated time"],
        "category": "order_processing",
        "priority": 6
    },

    # =========================================================================
    # Payment Processing (9 tools)
    # =========================================================================
    "apply_coupon": {
        "name": "apply_coupon",
        "description": "Apply a discount coupon code to the order",
        "usage": "When customer has coupon, discount code, promo code",
        "examples": ["apply coupon", "use discount code", "I have a promo", "coupon code"],
        "category": "payment",
        "priority": 7
    },
    "remove_coupon": {
        "name": "remove_coupon",
        "description": "Remove applied coupon from the order",
        "usage": "When customer wants to remove coupon",
        "examples": ["remove coupon", "cancel discount", "don't use coupon"],
        "category": "payment",
        "priority": 5
    },
    "get_available_payment_methods": {
        "name": "get_available_payment_methods",
        "description": "Get list of available payment methods",
        "usage": "When customer asks about payment options, how to pay",
        "examples": ["payment methods", "how can I pay", "payment options", "accepted payments"],
        "category": "payment",
        "priority": 6
    },
    "set_payment_method": {
        "name": "set_payment_method",
        "description": "Set the payment method for the order",
        "usage": "When customer specifies payment method",
        "examples": ["pay by card", "cash on delivery", "UPI payment", "credit card"],
        "category": "payment",
        "priority": 7
    },
    "validate_payment": {
        "name": "validate_payment",
        "description": "Validate and process payment for the order",
        "usage": "Internal tool for payment validation",
        "examples": [],
        "category": "payment",
        "priority": 4
    },
    "initiate_payment": {
        "name": "initiate_payment",
        "description": "Initiate online payment process and generate Razorpay payment link for card/UPI/online payment",
        "usage": "When customer wants to pay online, pay by card, complete payment, or proceed with online payment after checkout",
        "examples": ["pay online", "pay by card", "I want to pay now", "online payment", "card payment", "pay with UPI", "generate payment link"],
        "category": "payment",
        "priority": 10
    },
    "verify_payment_otp": {
        "name": "verify_payment_otp",
        "description": "Verify OTP for payment authentication",
        "usage": "When customer needs to verify payment OTP",
        "examples": ["verify OTP", "payment OTP", "enter OTP"],
        "category": "payment",
        "priority": 6
    },
    "check_payment_status": {
        "name": "check_payment_status",
        "description": "Check the status of a payment transaction",
        "usage": "When customer wants to check if payment was successful or check payment status",
        "examples": ["payment status", "check payment", "was payment successful", "did payment go through"],
        "category": "payment",
        "priority": 8
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
    "submit_feedback": {
        "name": "submit_feedback",
        "description": "Submit customer feedback or complaint",
        "usage": "When customer has feedback, complaint, issue, or problem",
        "examples": ["submit feedback", "I have a complaint", "report issue", "problem with order"],
        "category": "support",
        "priority": 6
    },
    "get_support_info": {
        "name": "get_support_info",
        "description": "Get customer support contact information",
        "usage": "When customer asks for help, support, contact",
        "examples": ["contact support", "help", "customer service", "talk to human"],
        "category": "support",
        "priority": 5
    },
    "escalate_issue": {
        "name": "escalate_issue",
        "description": "Escalate customer issue to human support",
        "usage": "When customer wants to talk to manager, human, or escalate issue",
        "examples": ["talk to manager", "human support", "escalate", "supervisor"],
        "category": "support",
        "priority": 7
    },
}

# =============================================================================
# BOOKING AGENT TOOLS (4 tools)
# =============================================================================

BOOKING_TOOLS = {
    "check_table_availability": {
        "name": "check_table_availability",
        "description": "Check table availability for date, time, and party size",
        "usage": "When customer wants to check table availability, book table, make reservation",
        "examples": ["check availability", "table for 4", "book table", "reservation"],
        "category": "booking",
        "priority": 10
    },
    "make_reservation": {
        "name": "make_reservation",
        "description": "Create a table reservation for specified date, time, and party size",
        "usage": "When customer wants to book, reserve, or make reservation",
        "examples": ["book table", "make reservation", "reserve for 6pm", "table booking"],
        "category": "booking",
        "priority": 10
    },
    "get_my_bookings": {
        "name": "get_my_bookings",
        "description": "Retrieve customer's current and upcoming reservations",
        "usage": "When customer wants to see their bookings, reservations, or table bookings",
        "examples": ["my bookings", "show reservations", "upcoming tables", "my reservations"],
        "category": "booking",
        "priority": 8
    },
    "cancel_reservation": {
        "name": "cancel_reservation",
        "description": "Cancel an existing table reservation",
        "usage": "When customer wants to cancel reservation or booking",
        "examples": ["cancel reservation", "cancel booking", "cancel table"],
        "category": "booking",
        "priority": 7
    },
}

# =============================================================================
# CHROMADB-BASED TOOL RETRIEVER
# =============================================================================

class AgentToolRetriever:
    """RAG-based tool retrieval using in-memory ChromaDB with separate collections per agent."""

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
    Get relevant tools for a specific agent using RAG.

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
    for tool_name in relevant_tool_names:
        if tool_name in all_tools:
            relevant_tools.append(all_tools[tool_name])
        else:
            logger.warning(f"tool_not_found", tool_name=tool_name)

    logger.info(
        "relevant_tools_selected",
        agent_type=agent_type,
        total_tools=len(all_tools),
        relevant_count=len(relevant_tools),
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
