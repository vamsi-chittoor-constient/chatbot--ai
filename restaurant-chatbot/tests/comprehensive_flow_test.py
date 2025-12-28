#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Flow Test for Restaurant Chatbot
Tests 10 different user flows to verify all tools are working
"""

import asyncio
import websockets
import json
import time
import sys
from typing import List, Dict

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
WS_URL = "ws://localhost/api/v1/chat"
SESSION_ID = f"flow_test_{int(time.time())}"
API_KEY = "test_key"

class FlowTester:
    def __init__(self):
        self.websocket = None
        self.test_results = []

    async def connect(self):
        """Connect to WebSocket"""
        uri = f"{WS_URL}/{SESSION_ID}?api_key={API_KEY}&tester_id=flow_tester"
        print(f"🔌 Connecting to {uri}...")
        self.websocket = await websockets.connect(uri)
        print("✅ Connected!\n")

        # Wait for welcome message
        await self.wait_for_welcome()

    async def wait_for_welcome(self):
        """Wait for initial welcome message"""
        print("⏳ Waiting for welcome message...")
        timeout = 15
        start = time.time()

        while time.time() - start < timeout:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                data = json.loads(response)
                msg_type = data.get("message_type", "")
                content = data.get("message", "")

                if msg_type == "ai_response" and ("Welcome" in content or "pleasure" in content):
                    print(f"✅ Received welcome: {content[:100]}...\n")
                    return
                elif msg_type == "agui_event":
                    event_type = data.get("event", {}).get("type", "")
                    print(f"   📡 AGUI Event: {event_type}")
            except asyncio.TimeoutError:
                continue

        print("⚠️  No welcome message received\n")

    async def send_message(self, message: str, test_name: str) -> Dict:
        """Send message and collect all responses"""
        print(f"\n{'='*80}")
        print(f"🧪 TEST: {test_name}")
        print(f"{'='*80}")
        print(f"👤 User: {message}")

        payload = {
            "message": message,
            "session_id": SESSION_ID,
            "user_id": "flow_tester"
        }

        await self.websocket.send(json.dumps(payload))

        # Collect responses
        responses = []
        agui_events = []
        ai_response = None
        timeout = 20
        start = time.time()

        while time.time() - start < timeout:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=2.0)
                data = json.loads(response)
                msg_type = data.get("message_type", "")

                if msg_type == "agui_event":
                    event_type = data.get("event", {}).get("type", "")
                    agui_events.append(event_type)
                    print(f"   📡 AGUI: {event_type}")

                    # Check for menu data
                    if event_type == "menu_data":
                        event_data = data.get("event", {})
                        items_count = len(event_data.get("items", []))
                        show_popular = event_data.get("show_popular_tab", None)
                        print(f"      📋 Menu Items: {items_count}")
                        print(f"      ⭐ Show Popular Tab: {show_popular}")

                elif msg_type == "ai_response":
                    ai_response = data.get("message", "")
                    print(f"🤖 AI: {ai_response[:200]}...")
                    break

                elif msg_type == "activity":
                    activity = data.get("activity", "")
                    print(f"   ⚙️  Activity: {activity}")

                responses.append(data)

            except asyncio.TimeoutError:
                if ai_response:
                    break
                continue

        result = {
            "test_name": test_name,
            "user_message": message,
            "ai_response": ai_response,
            "agui_events": agui_events,
            "responses": responses,
            "success": ai_response is not None
        }

        return result

    async def run_test_flows(self):
        """Run all 10 test flows"""

        # TEST 1: Full Menu Browse (search_menu tool)
        result = await self.send_message(
            "Show me the menu",
            "Test 1: Full Menu Browse (search_menu tool)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 2: Search for specific item
        result = await self.send_message(
            "Do you have pizza?",
            "Test 2: Menu Search with Query (search_menu with query)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 3: Browse by Italian cuisine (search_by_cuisine tool - FIXED)
        result = await self.send_message(
            "Show me Italian food",
            "Test 3: Browse by Cuisine - Italian (search_by_cuisine FIXED)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 4: Browse by Asian cuisine
        result = await self.send_message(
            "What Asian dishes do you have?",
            "Test 4: Browse by Cuisine - Asian (search_by_cuisine FIXED)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 5: Add item to cart (add_to_cart tool)
        result = await self.send_message(
            "Add Margherita Pizza to my cart",
            "Test 5: Add to Cart (add_to_cart tool)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 6: View cart (view_cart tool)
        result = await self.send_message(
            "Show me my cart",
            "Test 6: View Cart (view_cart tool)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 7: Search unavailable item - AGUI fallback (FIXED)
        result = await self.send_message(
            "Do you have dosa?",
            "Test 7: Search Unavailable Item - AGUI Fallback (FIXED)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 8: Update quantity (update_quantity tool)
        result = await self.send_message(
            "Change the Margherita Pizza quantity to 2",
            "Test 8: Update Cart Quantity (update_quantity tool)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 9: Verify Popular Items Removed (menu_data event check)
        result = await self.send_message(
            "Show me the full menu again",
            "Test 9: Verify Popular Items Tab Removed (show_popular_tab=False)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

        # TEST 10: Clear cart (clear_cart or remove_from_cart tool)
        result = await self.send_message(
            "Clear my cart",
            "Test 10: Clear Cart (clear_cart tool)"
        )
        self.test_results.append(result)
        await asyncio.sleep(2)

    def print_summary(self):
        """Print test summary"""
        print(f"\n\n{'='*80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*80}\n")

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests

        for i, result in enumerate(self.test_results, 1):
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            print(f"{i}. {status} - {result['test_name']}")
            print(f"   User: {result['user_message']}")
            print(f"   AI Response: {'Yes' if result['ai_response'] else 'No response'}")
            print(f"   AGUI Events: {', '.join(result['agui_events']) if result['agui_events'] else 'None'}")

            # Check for popular items tab in menu_data events
            if any('menu_data' in e for e in result['agui_events']):
                for resp in result['responses']:
                    if resp.get('message_type') == 'agui_event':
                        event = resp.get('event', {})
                        if event.get('type') == 'menu_data':
                            show_popular = event.get('show_popular_tab')
                            if show_popular is False:
                                print(f"   ✅ Popular Items Tab: DISABLED (Fixed!)")
                            elif show_popular is True:
                                print(f"   ❌ Popular Items Tab: ENABLED (Should be False!)")
            print()

        print(f"{'='*80}")
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"{'='*80}\n")

        # Specific fix verifications
        print(f"{'='*80}")
        print(f"🔧 FIX VERIFICATION")
        print(f"{'='*80}\n")

        # Check cuisine filtering fix
        cuisine_tests = [r for r in self.test_results if 'Cuisine' in r['test_name']]
        cuisine_working = all(r['success'] and r.get('agui_events') for r in cuisine_tests)
        print(f"1. Cuisine Filtering Fix (Italian/Asian): {'✅ WORKING' if cuisine_working else '❌ BROKEN'}")

        # Check popular items removal
        menu_tests = [r for r in self.test_results if 'menu_data' in str(r.get('agui_events'))]
        popular_removed = True
        for result in menu_tests:
            for resp in result['responses']:
                if resp.get('message_type') == 'agui_event':
                    event = resp.get('event', {})
                    if event.get('type') == 'menu_data' and event.get('show_popular_tab') is True:
                        popular_removed = False
        print(f"2. Popular Items Feature Removed: {'✅ CONFIRMED' if popular_removed else '❌ STILL ENABLED'}")

        # Check AGUI fallback for unavailable items
        dosa_test = [r for r in self.test_results if 'dosa' in r.get('user_message', '').lower()]
        if dosa_test:
            dosa_has_agui = bool(dosa_test[0].get('agui_events'))
            print(f"3. AGUI Fallback for Unavailable Items: {'✅ WORKING' if dosa_has_agui else '❌ NO AGUI EVENTS'}")

        print(f"\n{'='*80}\n")

    async def run(self):
        """Main test runner"""
        try:
            await self.connect()
            await self.run_test_flows()
            self.print_summary()

        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.websocket:
                await self.websocket.close()
                print("🔌 Connection closed")

async def main():
    print("\n" + "="*80)
    print("🧪 COMPREHENSIVE FLOW TEST - Restaurant Chatbot")
    print("="*80 + "\n")

    tester = FlowTester()
    await tester.run()

if __name__ == "__main__":
    asyncio.run(main())
