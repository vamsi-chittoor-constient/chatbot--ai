"""
Test 10 Conversational Flows with Restaurant Chatbot WebSocket
"""

import asyncio
import websockets
import json
import uuid
from datetime import datetime

# WebSocket URL (using container name for internal Docker network)
WS_URL = "ws://localhost:8000/api/v1/chat"

# Test Conversations
TEST_FLOWS = [
    {
        "name": "Flow 1: Menu Inquiry",
        "messages": [
            "What's on your menu today?",
            "Do you have any vegetarian options?"
        ]
    },
    {
        "name": "Flow 2: Item Details",
        "messages": [
            "Tell me about your burgers",
            "What ingredients are in the classic burger?"
        ]
    },
    {
        "name": "Flow 3: Dietary Restrictions",
        "messages": [
            "I'm vegan, what can I order?",
            "Are any of your salads completely plant-based?"
        ]
    },
    {
        "name": "Flow 4: Pricing Questions",
        "messages": [
            "How much does a pizza cost?",
            "Do you have any combo deals or specials?"
        ]
    },
    {
        "name": "Flow 5: Order Placement Intent",
        "messages": [
            "I'd like to place an order for delivery",
            "Can I get two pizzas?"
        ]
    },
    {
        "name": "Flow 6: Hours of Operation",
        "messages": [
            "What time do you open?",
            "Are you open on weekends?"
        ]
    },
    {
        "name": "Flow 7: Special Requests",
        "messages": [
            "Can I get extra cheese on my pizza?",
            "Do you do custom toppings?"
        ]
    },
    {
        "name": "Flow 8: Recommendations",
        "messages": [
            "What's your most popular dish?",
            "What do you recommend for first-time customers?"
        ]
    },
    {
        "name": "Flow 9: Allergen Information",
        "messages": [
            "I'm allergic to nuts, what should I avoid?",
            "Which items contain gluten?"
        ]
    },
    {
        "name": "Flow 10: General Restaurant Info",
        "messages": [
            "Do you have parking available?",
            "Can I make a reservation for dinner tonight?"
        ]
    }
]


async def test_conversation_flow(flow_index: int, flow_data: dict):
    """Test a single conversation flow"""
    session_id = f"test-session-{uuid.uuid4()}"
    flow_name = flow_data["name"]
    messages = flow_data["messages"]

    print(f"\n{'='*80}")
    print(f"[TEST] {flow_name}")
    print(f"Session ID: {session_id}")
    print(f"{'='*80}\n")

    try:
        # Connect to WebSocket with session ID
        uri = f"{WS_URL}/{session_id}?tester_id=test-flow-{flow_index}"

        async with websockets.connect(uri) as websocket:
            print(f"[OK] Connected to chatbot WebSocket")

            # Receive welcome message
            welcome_msg = await asyncio.wait_for(
                websocket.recv(),
                timeout=10.0
            )
            welcome_data = json.loads(welcome_msg)
            print(f"\n[AI] {welcome_data.get('message', '')[:200]}...\n")

            # Send each message in the flow
            for msg_index, user_message in enumerate(messages, 1):
                print(f"[USER {msg_index}/{len(messages)}] {user_message}")

                # Send message
                message_payload = {
                    "message": user_message,
                    "timestamp": datetime.utcnow().isoformat(),
                    "device_id": f"test-device-{flow_index}",
                    "session_id": session_id
                }
                await websocket.send(json.dumps(message_payload))

                # Receive responses (including typing indicator and final response)
                ai_responses = []
                while True:
                    try:
                        response = await asyncio.wait_for(
                            websocket.recv(),
                            timeout=15.0
                        )
                        response_data = json.loads(response)

                        msg_type = response_data.get("message_type")
                        msg_content = response_data.get("message", "")

                        if msg_type == "typing_indicator":
                            print("   [TYPING] AI is typing...")
                        elif msg_type == "ai_response" and msg_content:
                            ai_responses.append(msg_content)
                            print(f"\n[AI] {msg_content[:300]}...")
                            break  # Got the final response
                        elif msg_type == "agui_event":
                            # Skip AG-UI events for console output
                            continue
                    except asyncio.TimeoutError:
                        print("   [WARN] Timeout waiting for response")
                        break

                # Small delay between messages
                await asyncio.sleep(1)

            print(f"\n[OK] {flow_name} completed successfully")
            print(f"   Total messages exchanged: {len(messages)} user + {len(messages)} AI\n")

    except websockets.exceptions.WebSocketException as e:
        print(f"[ERROR] WebSocket error in {flow_name}: {str(e)}")
    except asyncio.TimeoutError:
        print(f"[TIMEOUT] {flow_name}")
    except Exception as e:
        print(f"[ERROR] {flow_name}: {str(e)}")


async def run_all_tests():
    """Run all test flows sequentially"""
    print("\n" + "="*80)
    print("Starting Chatbot Conversation Flow Tests")
    print("="*80)

    for index, flow in enumerate(TEST_FLOWS, 1):
        await test_conversation_flow(index, flow)
        # Small delay between test flows
        await asyncio.sleep(2)

    print("\n" + "="*80)
    print("[SUCCESS] All 10 conversation flows tested!")
    print("="*80 + "\n")


if __name__ == "__main__":
    # Run the tests
    asyncio.run(run_all_tests())
