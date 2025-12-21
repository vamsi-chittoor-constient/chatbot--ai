"""Test FAQ tools - these don't require menu data"""
import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://localhost:8000/api/v1/chat"

async def test_faq_tools():
    session_id = "faq-test-session"

    print("Testing FAQ tools (no menu data required)...")
    uri = f"{WS_URL}/{session_id}?tester_id=faq-test"

    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for welcome message...")

        # Receive welcome
        welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        print(f"Welcome: {json.loads(welcome).get('message', '')[:100]}...\n")

        # Test 1: FAQ search
        print("=" * 80)
        print("TEST 1: FAQ Search - 'What's your refund policy?'")
        print("=" * 80)
        await websocket.send(json.dumps({
            "message": "What's your refund policy?",
            "timestamp": datetime.now().isoformat()
        }))

        tool_called = False
        for _ in range(10):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)

                if data.get("message_type") == "typing_indicator":
                    print("  (AI is typing...)")
                elif data.get("message_type") == "agui_event":
                    if data.get("event_type") == "tool_activity":
                        tool_name = data.get("tool_name")
                        print(f"✅ TOOL CALLED: {tool_name}")
                        tool_called = True
                elif data.get("message_type") == "ai_response":
                    print(f"\nAI Response:\n{data.get('message', '')}\n")
                    break
            except asyncio.TimeoutError:
                print("  (timeout)")
                break

        if not tool_called:
            print("❌ NO TOOL CALLED!")

        # Test 2: Operating hours
        print("\n" + "=" * 80)
        print("TEST 2: Operating Hours - 'What time do you open?'")
        print("=" * 80)
        await websocket.send(json.dumps({
            "message": "What time do you open?",
            "timestamp": datetime.now().isoformat()
        }))

        tool_called = False
        for _ in range(10):
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                data = json.loads(response)

                if data.get("message_type") == "agui_event":
                    if data.get("event_type") == "tool_activity":
                        tool_name = data.get("tool_name")
                        print(f"✅ TOOL CALLED: {tool_name}")
                        tool_called = True
                elif data.get("message_type") == "ai_response":
                    print(f"\nAI Response:\n{data.get('message', '')}\n")
                    break
            except asyncio.TimeoutError:
                print("  (timeout)")
                break

        if not tool_called:
            print("❌ NO TOOL CALLED!")

        print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_faq_tools())
