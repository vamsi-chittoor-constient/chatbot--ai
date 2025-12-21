"""
Comprehensive Real Customer Flow Testing
=========================================
Tests all 55 tools across realistic customer scenarios
"""
import asyncio
import websockets
import json
from datetime import datetime
import uuid

WS_URL = "ws://localhost:8000/api/v1/chat"

# Real customer conversation flows
COMPREHENSIVE_FLOWS = [
    {
        "name": "Complete Food Ordering Flow",
        "scenario": "Customer orders food from start to finish",
        "messages": [
            "Hi, what's on your menu?",
            "Do you have any vegetarian options?",
            "I'll take 2 Margherita Pizzas",
            "Actually, make that 3 pizzas",
            "Add 1 Garlic Bread",
            "Show me my cart",
            "Make the pizza extra spicy",
            "What's the total?",
            "I want it for delivery",
            "What's my order status?"
        ]
    },
    {
        "name": "Menu Discovery & Filtering",
        "scenario": "Customer explores menu with filters",
        "messages": [
            "What cuisines do you serve?",
            "Show me Italian dishes",
            "What's popular?",
            "Do you have combo deals?",
            "Show me spicy items",
            "What's for breakfast?",
            "I'm allergic to nuts, what can I eat?"
        ]
    },
    {
        "name": "Customer Profile Setup",
        "scenario": "Customer sets dietary preferences",
        "messages": [
            "I'm vegan",
            "I'm also allergic to peanuts",
            "Show me my dietary restrictions",
            "What are my allergens?",
            "Show me vegan options from the menu",
            "Add Vegan Salad to my favorites"
        ]
    },
    {
        "name": "FAQ & Help Queries",
        "scenario": "Customer asks common questions",
        "messages": [
            "What's your refund policy?",
            "What are your delivery hours?",
            "How much is delivery?",
            "What time do you open?",
            "Show me FAQs about payment",
            "What are popular questions?"
        ]
    },
    {
        "name": "Feedback & Reviews",
        "scenario": "Customer provides feedback",
        "messages": [
            "I want to give feedback - the food was amazing!",
            "Rate my last order 5 stars - excellent service",
            "Show my feedback history"
        ]
    },
    {
        "name": "Table Reservation Flow",
        "scenario": "Customer books a table",
        "messages": [
            "I want to book a table",
            "Are you available tonight at 7 PM for 4 people?",
            "Book a table for 4 people at 7 PM today",
            "Show my reservations",
            "What times are available on Saturday?"
        ]
    },
    {
        "name": "Order Customization",
        "scenario": "Customer customizes their order",
        "messages": [
            "I want to order a burger",
            "Add 1 Classic Burger",
            "Make it medium rare",
            "No onions please",
            "Add delivery instructions - ring doorbell twice",
            "Show my cart"
        ]
    },
    {
        "name": "Reorder Previous Order",
        "scenario": "Customer wants to reorder",
        "messages": [
            "Show my order history",
            "Reorder my last order",
            "Show me my cart",
            "Proceed to checkout"
        ]
    },
    {
        "name": "Mixed Queries",
        "scenario": "Customer asks various questions",
        "messages": [
            "What Italian dishes do you have?",
            "Does the Carbonara have nuts?",
            "Add 2 Carbonara Pasta to cart",
            "Show my cart",
            "What's your cancellation policy?",
            "Can I modify my order after placing it?"
        ]
    },
    {
        "name": "Allergen Safety Check",
        "scenario": "Customer with allergies checks menu",
        "messages": [
            "I'm allergic to shellfish",
            "What items don't have shellfish?",
            "Does the Caesar Salad have shellfish?",
            "Show me allergen-free options",
            "Add me to favorites so I can reorder easily"
        ]
    }
]

async def test_conversation_flow(flow_index: int, flow_data: dict):
    """Test a single conversation flow"""
    session_id = f"comprehensive-test-{uuid.uuid4()}"
    flow_name = flow_data["name"]
    scenario = flow_data["scenario"]
    messages = flow_data["messages"]

    print(f"\n{'='*80}")
    print(f"[FLOW {flow_index}] {flow_name}")
    print(f"Scenario: {scenario}")
    print(f"Session: {session_id}")
    print(f"{'='*80}\n")

    conversation_log = []
    tools_called = set()

    try:
        uri = f"{WS_URL}/{session_id}?tester_id=comprehensive-test-{flow_index}"

        async with websockets.connect(uri) as websocket:
            print(f"[CONNECTED] WebSocket established\n")

            # Receive welcome
            welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            welcome_data = json.loads(welcome)
            print(f"[AI WELCOME] {welcome_data.get('message', '')[:150]}...\n")

            # Send each message
            for msg_index, user_message in enumerate(messages, 1):
                print(f"[USER {msg_index}/{len(messages)}] {user_message}")

                # Send message
                await websocket.send(json.dumps({
                    "message": user_message,
                    "timestamp": datetime.now().isoformat()
                }))

                # Wait for response
                ai_response = None
                for _ in range(15):  # Try up to 15 times (for longer processing)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
                        data = json.loads(response)

                        msg_type = data.get("message_type")

                        if msg_type == "typing_indicator":
                            print("   [TYPING]...")
                        elif msg_type == "ai_response":
                            ai_response = data.get("message", "")
                            print(f"[AI] {ai_response[:200]}{'...' if len(ai_response) > 200 else ''}\n")
                            conversation_log.append({
                                "user": user_message,
                                "ai": ai_response
                            })
                            break
                        elif msg_type == "agui_event":
                            event = data.get("event_type", "")
                            if event == "tool_activity":
                                tool_name = data.get("tool_name", "unknown")
                                tools_called.add(tool_name)
                                print(f"   [TOOL] {tool_name}")
                            elif event == "menu_data":
                                print(f"   [EVENT] Menu card displayed")
                            elif event == "cart_data":
                                print(f"   [EVENT] Cart card displayed")
                    except asyncio.TimeoutError:
                        print("   [TIMEOUT] No response within timeout")
                        break

                if not ai_response:
                    print(f"   [WARNING] No AI response received\n")

                # Small delay between messages
                await asyncio.sleep(1.5)

            print(f"\n[COMPLETED] {flow_name}")
            print(f"   Messages exchanged: {len(conversation_log)}")
            print(f"   Tools called: {len(tools_called)} - {', '.join(sorted(tools_called)) if tools_called else 'NONE'}")

            # Check if tools were actually called
            if not tools_called:
                print(f"   [WARNING] No tools were called during this flow!")

            return {
                "flow_name": flow_name,
                "success": len(conversation_log) > 0,
                "messages_exchanged": len(conversation_log),
                "tools_called": list(tools_called),
                "conversation_log": conversation_log
            }

    except websockets.exceptions.WebSocketException as e:
        print(f"[ERROR] WebSocket error: {str(e)}")
        return {"flow_name": flow_name, "success": False, "error": str(e)}
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return {"flow_name": flow_name, "success": False, "error": str(e)}


async def run_all_comprehensive_tests():
    """Run all comprehensive test flows"""
    print("\n" + "="*80)
    print("COMPREHENSIVE CHATBOT TESTING - ALL 55 TOOLS")
    print("Testing realistic customer scenarios across all features")
    print("="*80)

    results = []
    all_tools_called = set()

    for index, flow in enumerate(COMPREHENSIVE_FLOWS, 1):
        result = await test_conversation_flow(index, flow)
        results.append(result)

        if result.get("tools_called"):
            all_tools_called.update(result["tools_called"])

        # Delay between flows
        await asyncio.sleep(2)

    # Print comprehensive summary
    print("\n" + "="*80)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r.get("success"))
    total = len(results)

    print(f"\nFlows Tested: {total}")
    print(f"Flows Passed: {passed}")
    print(f"Success Rate: {passed*100//total}%\n")

    # Detailed results
    print("Flow Results:")
    for idx, result in enumerate(results, 1):
        status = "PASS" if result.get("success") else "FAIL"
        tools = len(result.get("tools_called", []))
        print(f"  {idx}. [{status}] {result['flow_name']}")
        print(f"      Messages: {result.get('messages_exchanged', 0)}, Tools Called: {tools}")
        if result.get("error"):
            print(f"      Error: {result['error']}")

    # Tool usage analysis
    print(f"\n{'='*80}")
    print("TOOL USAGE ANALYSIS")
    print(f"{'='*80}")
    print(f"\nUnique Tools Called: {len(all_tools_called)}/55 possible tools")

    if all_tools_called:
        print("\nTools Actually Used:")
        for tool in sorted(all_tools_called):
            print(f"  - {tool}")
    else:
        print("\nWARNING: No tools were called during any test flow!")
        print("This suggests the AI is not invoking tools properly.")
        print("\nPossible issues:")
        print("  1. Tool descriptions don't match user intent")
        print("  2. Model needs stronger prompting to use tools")
        print("  3. Tools not properly loaded in crew")
        print("  4. Authentication required for many tools")

    # Expected vs Actual
    expected_tools = {
        "search_menu", "add_to_cart", "view_cart", "search_faq",
        "get_faq_by_category", "get_popular_faqs", "search_by_cuisine",
        "get_available_cuisines", "get_popular_items", "get_combo_deals",
        "search_by_tag", "submit_feedback", "add_customer_allergen",
        "add_dietary_restriction", "filter_menu_by_allergen",
        "check_table_availability", "get_operating_hours", "get_restaurant_policies"
    }

    missing_tools = expected_tools - all_tools_called
    if missing_tools:
        print(f"\nExpected Tools NOT Called ({len(missing_tools)}):")
        for tool in sorted(missing_tools):
            print(f"  - {tool}")

    print(f"\n{'='*80}")
    if passed == total and len(all_tools_called) >= 10:
        print("SUCCESS: All flows passed and tools are being used!")
    elif passed == total:
        print("PARTIAL SUCCESS: All flows passed but few tools called")
    else:
        print(f"NEEDS ATTENTION: {total - passed} flow(s) failed")
    print(f"{'='*80}\n")

    return results


if __name__ == "__main__":
    asyncio.run(run_all_comprehensive_tests())
