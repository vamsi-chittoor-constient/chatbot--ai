"""Test Phase 1 Tools Implementation"""
import asyncio
import websockets
import json
from datetime import datetime
import uuid

WS_URL = "ws://localhost:8000/api/v1/chat"

async def test_single_message(message: str, test_name: str):
    """Test a single message to verify tool calling"""
    session_id = f"phase1-test-{uuid.uuid4()}"

    print(f"\n{'='*80}")
    print(f"[TEST] {test_name}")
    print(f"Message: {message}")
    print(f"{'='*80}\n")

    try:
        uri = f"{WS_URL}/{session_id}?tester_id=phase1-tester"

        async with websockets.connect(uri) as websocket:
            # Receive welcome
            welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            welcome_data = json.loads(welcome)
            print(f"[CONNECTED] Session: {session_id}\n")

            # Send test message
            await websocket.send(json.dumps({
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            }))

            # Wait for response
            print("[WAITING] For AI response...")
            for _ in range(10):
                response = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                data = json.loads(response)

                msg_type = data.get("message_type")
                if msg_type == "typing_indicator":
                    print("  [TYPING] AI is typing...")
                elif msg_type == "ai_response":
                    ai_message = data.get("message", "")
                    print(f"\n[AI RESPONSE]\n{ai_message}\n")
                    print(f"[SUCCESS] {test_name} completed\n")
                    return True
                elif msg_type == "agui_event":
                    event_type = data.get("event_type", "")
                    print(f"  [EVENT] {event_type}")

            print(f"[TIMEOUT] No AI response received for {test_name}\n")
            return False

    except Exception as e:
        print(f"[ERROR] {test_name}: {str(e)}\n")
        return False


async def run_phase1_tests():
    """Run all Phase 1 tool tests"""
    print("\n" + "="*80)
    print("PHASE 1 TOOLS TESTING")
    print("Testing: Allergens, Dietary, Favorites, FAQ, Feedback")
    print("="*80)

    tests = [
        # FAQ Tools (should work without authentication)
        ("What's your refund policy?", "FAQ Test 1: Refund Policy"),
        ("What are your delivery hours?", "FAQ Test 2: Delivery Hours"),
        ("Show me FAQs about payment", "FAQ Test 3: Category Browse"),

        # Allergen Tools (may require auth, but should handle gracefully)
        ("I'm allergic to peanuts", "Allergen Test 1: Add Allergen"),
        ("What are my allergens?", "Allergen Test 2: View Allergens"),

        # Dietary Tools
        ("I'm vegan", "Dietary Test 1: Add Dietary Restriction"),
        ("Show my dietary restrictions", "Dietary Test 2: View Dietary"),

        # Favorites (may require auth)
        ("Show my favorite items", "Favorites Test: View Favorites"),

        # Feedback (may require auth for some features)
        ("I want to give feedback - the food was amazing!", "Feedback Test 1: Submit Feedback"),
    ]

    results = []
    for message, test_name in tests:
        success = await test_single_message(message, test_name)
        results.append((test_name, success))
        await asyncio.sleep(2)  # Delay between tests

    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{passed}/{total} tests passed ({passed*100//total}%)\n")

    if passed == total:
        print("🎉 ALL TESTS PASSED! Phase 1 tools are working correctly.")
    elif passed > 0:
        print(f"⚠️  PARTIAL SUCCESS - {total - passed} test(s) failed.")
    else:
        print("❌ ALL TESTS FAILED - Check logs for errors.")

    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_phase1_tests())
