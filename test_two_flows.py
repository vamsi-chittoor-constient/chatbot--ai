"""Test two specific chatbot flows with real menu data"""
import asyncio
import websockets
import json
from datetime import datetime
import uuid

WS_URL = "ws://localhost:8000/api/v1/chat"

async def test_menu_search_flow():
    """Flow 1: Menu Search - Test if AI actually calls search_menu tool"""
    session_id = f"menu-search-{uuid.uuid4().hex[:8]}"

    print("\n" + "="*80)
    print("FLOW 1: Menu Search & Discovery")
    print("Testing if AI calls search_menu tool when asked about menu")
    print("="*80)

    uri = f"{WS_URL}/{session_id}?tester_id=flow-test"

    try:
        async with websockets.connect(uri) as websocket:
            # Get welcome
            welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"[OK] Connected - Session: {session_id}\n")

            # Test 1: Ask about menu
            print("[USER] What's on your menu?")
            await websocket.send(json.dumps({
                "message": "What's on your menu?",
                "timestamp": datetime.now().isoformat()
            }))

            tools_called = []
            ai_response = None

            for _ in range(15):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(msg)

                    if data.get("message_type") == "agui_event":
                        if data.get("event_type") == "tool_activity":
                            tool = data.get("tool_name")
                            tools_called.append(tool)
                            print(f"  [TOOL] {tool}")

                    elif data.get("message_type") == "ai_response":
                        ai_response = data.get("message", "")
                        print(f"\n[AI] {ai_response[:200]}...")
                        break

                except asyncio.TimeoutError:
                    break

            # Analyze results
            print(f"\n[RESULTS]")
            print(f"   Tools Called: {len(tools_called)} - {tools_called if tools_called else 'NONE [FAIL]'}")
            print(f"   Expected: search_menu")

            if "search_menu" in tools_called:
                print("   [SUCCESS] AI called search_menu tool!")
            else:
                print("   [FAILURE] AI did not call search_menu tool")

            return len(tools_called) > 0

    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def test_cart_flow():
    """Flow 2: Add to Cart - Test if AI can add items and show cart"""
    session_id = f"cart-test-{uuid.uuid4().hex[:8]}"

    print("\n" + "="*80)
    print("FLOW 2: Add to Cart & View Cart")
    print("Testing if AI calls add_to_cart and view_cart tools")
    print("="*80)

    uri = f"{WS_URL}/{session_id}?tester_id=flow-test"

    try:
        async with websockets.connect(uri) as websocket:
            # Get welcome
            await asyncio.wait_for(websocket.recv(), timeout=10.0)
            print(f"[OK] Connected - Session: {session_id}\n")

            # Test 1: Add item to cart
            print("[USER] Add 2 Chicken Fillet Burger to my cart")
            await websocket.send(json.dumps({
                "message": "Add 2 Chicken Fillet Burger to my cart",
                "timestamp": datetime.now().isoformat()
            }))

            tools_called = []

            for _ in range(15):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(msg)

                    if data.get("message_type") == "agui_event":
                        if data.get("event_type") == "tool_activity":
                            tool = data.get("tool_name")
                            tools_called.append(tool)
                            print(f"  [TOOL] {tool}")

                    elif data.get("message_type") == "ai_response":
                        print(f"\n[AI] {data.get('message', '')[:200]}...")
                        break

                except asyncio.TimeoutError:
                    break

            # Test 2: View cart
            print("\n[USER] Show me my cart")
            await websocket.send(json.dumps({
                "message": "Show me my cart",
                "timestamp": datetime.now().isoformat()
            }))

            for _ in range(15):
                try:
                    msg = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(msg)

                    if data.get("message_type") == "agui_event":
                        if data.get("event_type") == "tool_activity":
                            tool = data.get("tool_name")
                            tools_called.append(tool)
                            print(f"  [TOOL] {tool}")

                    elif data.get("message_type") == "ai_response":
                        print(f"\n[AI] {data.get('message', '')[:300]}...")
                        break

                except asyncio.TimeoutError:
                    break

            # Analyze results
            print(f"\n[RESULTS]")
            print(f"   Tools Called: {len(tools_called)} - {tools_called if tools_called else 'NONE [FAIL]'}")
            print(f"   Expected: add_to_cart, view_cart")

            success = False
            if "add_to_cart" in tools_called or "view_cart" in tools_called:
                print("   [SUCCESS] AI called cart-related tools!")
                success = True
            else:
                print("   [FAILURE] AI did not call expected tools")

            return success

    except Exception as e:
        print(f"[ERROR] {e}")
        return False


async def main():
    print("\n" + "="*80)
    print("TESTING CHATBOT WITH REAL PETPOOJA MENU DATA")
    print("Database has 97 menu items synced from PetPooja")
    print("="*80)

    # Run both flows
    flow1_success = await test_menu_search_flow()
    await asyncio.sleep(2)
    flow2_success = await test_cart_flow()

    # Summary
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"Flow 1 (Menu Search): {'[PASS]' if flow1_success else '[FAIL] - Tools not called'}")
    print(f"Flow 2 (Cart Operations): {'[PASS]' if flow2_success else '[FAIL] - Tools not called'}")

    if not flow1_success and not flow2_success:
        print("\n[WARNING] CRITICAL ISSUE: AI is not calling tools!")
        print("Possible causes:")
        print("  1. Tool registration issue in CrewAI")
        print("  2. Task description not prompting tool usage")
        print("  3. LLM not configured for function calling")
        print("  4. Customer_id required but not set")

    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
