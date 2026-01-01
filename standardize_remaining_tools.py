"""
Tool Description Standardization Script
========================================
Helps batch-update remaining tool descriptions to follow the standard template.

This script generates standardized docstrings for all remaining tools.
"""

# Remaining tools to standardize
REMAINING_TOOLS = {
    # Menu Browsing (2 tools)
    "show_popular_items": {
        "brief": "Display popular and recommended menu items.",
        "detail": "Shows highly-rated and frequently ordered items based on customer ratings and order history. Helps customers discover best-sellers.",
        "args": [
            ("limit", "int", "Number of items to show (default: 10, e.g., 5, 10, 15)")
        ],
        "returns": "List of popular items with names, prices, ratings, and descriptions.",
        "examples": [
            'show_popular_items(10) → Shows top 10 popular items',
            'show_popular_items(5) → Shows top 5 bestsellers',
            'show_popular_items() → Shows default 10 popular items',
        ],
        "triggers": [
            'Customer: "what\'s popular?" → show_popular_items()',
            'Customer: "show me bestsellers" → show_popular_items()',
            'Customer: "what do people usually order?" → show_popular_items()',
        ]
    },

    "filter_by_cuisine": {
        "brief": "Filter menu items by cuisine type.",
        "detail": "Filters menu to show only items from specified cuisine (Italian, Chinese, Indian, etc.). Helps customers browse by their preferred cooking style.",
        "args": [
            ("cuisine", "str", "Cuisine type (e.g., 'Italian', 'Chinese', 'Indian', 'Mexican')")
        ],
        "returns": "Menu card with filtered items from specified cuisine.",
        "examples": [
            'filter_by_cuisine("Italian") → Shows Italian dishes only',
            'filter_by_cuisine("Chinese") → Shows Chinese dishes',
            'filter_by_cuisine("Indian") → Shows Indian cuisine',
        ],
        "triggers": [
            'Customer: "show me Italian food" → filter_by_cuisine("Italian")',
            'Customer: "Chinese dishes please" → filter_by_cuisine("Chinese")',
            'Customer: "I want Indian" → filter_by_cuisine("Indian")',
        ]
    },

    # Payment Tools (4 tools)
    "initiate_payment": {
        "brief": "Initiate online payment and generate Razorpay payment link.",
        "detail": "Creates Razorpay payment link for online payment (card/UPI/netbanking). Sends payment link to customer and tracks payment status. Used after checkout for online payment method.",
        "args": [
            ("order_id", "str", "Order ID to pay for (e.g., 'ORD-123')")
        ],
        "returns": "Payment link URL with instructions for completing payment.",
        "examples": [
            'initiate_payment("ORD-123") → Generates Razorpay link for order',
            'initiate_payment("ORD-456") → Creates payment link',
        ],
        "triggers": [
            'Customer: "I want to pay online" → initiate_payment(order_id)',
            'Customer: "pay by card" → initiate_payment(order_id)',
            'Customer: "send payment link" → initiate_payment(order_id)',
        ]
    },

    "check_payment_status": {
        "brief": "Check if payment was completed successfully.",
        "detail": "Verifies payment status with Razorpay to confirm if customer completed payment. Returns success/pending/failed status.",
        "args": [
            ("order_id", "str", "Order ID to check payment for (e.g., 'ORD-123')")
        ],
        "returns": "Payment status (success/pending/failed) with transaction details.",
        "examples": [
            'check_payment_status("ORD-123") → Checks if payment completed',
            'check_payment_status("ORD-456") → Verifies payment status',
        ],
        "triggers": [
            'Customer: "did my payment go through?" → check_payment_status(order_id)',
            'Customer: "check payment status" → check_payment_status(order_id)',
            'Customer: "was payment successful?" → check_payment_status(order_id)',
        ]
    },

    "apply_coupon": {
        "brief": "Apply discount coupon code to order.",
        "detail": "Applies promotional code or discount coupon to cart/order. Validates coupon code and calculates discounted total.",
        "args": [
            ("coupon_code", "str", "Coupon code to apply (e.g., 'SAVE20', 'FIRST10')")
        ],
        "returns": "Confirmation of discount applied with new total amount.",
        "examples": [
            'apply_coupon("SAVE20") → Applies 20% discount coupon',
            'apply_coupon("FIRST10") → Applies first-order 10% off',
            'apply_coupon("WELCOME") → Applies welcome discount',
        ],
        "triggers": [
            'Customer: "I have a coupon code SAVE20" → apply_coupon("SAVE20")',
            'Customer: "apply discount" → (ask for code) → apply_coupon(code)',
            'Customer: "use promo code" → (ask for code) → apply_coupon(code)',
        ]
    },

    "remove_coupon": {
        "brief": "Remove applied coupon from order.",
        "detail": "Removes discount coupon from cart/order and recalculates total to original price.",
        "args": [],
        "returns": "Confirmation that coupon was removed with updated total.",
        "examples": [
            'remove_coupon() → Removes applied coupon, restores original price',
        ],
        "triggers": [
            'Customer: "remove the coupon" → remove_coupon()',
            'Customer: "cancel discount" → remove_coupon()',
            'Customer: "don\'t use coupon" → remove_coupon()',
        ]
    },
}

# Template for generating standardized docstrings
DOCSTRING_TEMPLATE = '''"""
{brief}

{detail}

Args:
{args_section}

Returns:
    {returns}

Examples:
{examples_section}

Common triggers:
{triggers_section}
"""'''

def generate_docstring(tool_name, tool_spec):
    """Generate standardized docstring for a tool."""

    # Args section
    if tool_spec["args"]:
        args_lines = []
        for arg_name, arg_type, arg_desc in tool_spec["args"]:
            args_lines.append(f"    {arg_name}: {arg_desc}")
        args_section = "\n".join(args_lines)
    else:
        args_section = "    None"

    # Examples section
    examples_lines = [f"    - {ex}" for ex in tool_spec["examples"]]
    examples_section = "\n".join(examples_lines)

    # Triggers section
    triggers_lines = [f"    - {tr}" for tr in tool_spec["triggers"]]
    triggers_section = "\n".join(triggers_lines)

    # Generate docstring
    docstring = DOCSTRING_TEMPLATE.format(
        brief=tool_spec["brief"],
        detail=tool_spec["detail"],
        args_section=args_section,
        returns=tool_spec["returns"],
        examples_section=examples_section,
        triggers_section=triggers_section
    )

    return docstring

def main():
    """Generate standardized docstrings for all remaining tools."""
    print("=" * 80)
    print("STANDARDIZED TOOL DOCSTRINGS")
    print("=" * 80)
    print()

    for tool_name, tool_spec in REMAINING_TOOLS.items():
        print(f"\n{'='*80}")
        print(f"TOOL: {tool_name}")
        print(f"{'='*80}")
        print(generate_docstring(tool_name, tool_spec))
        print()

if __name__ == "__main__":
    main()
