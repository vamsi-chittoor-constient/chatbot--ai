"""
Manual testing of 20 user flows - Real-time interaction with chatbot
Each flow touches all 50 tools over ~100 messages
"""
import requests
import json
import time
import sys
from typing import List, Dict, Tuple

# Fix Windows console encoding for emojis
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"

# Track issues found
issues_found = []

def send_message(session_id: str, message: str, flow_num: int, msg_num: int) -> Tuple[str, List[Dict]]:
    """Send a message and get response + quick replies"""
    print(f"\n{'='*80}")
    print(f"FLOW {flow_num} | MESSAGE {msg_num}")
    print(f"{'='*80}")
    print(f"USER: {message}")

    try:
        response = requests.post(
            f"{BASE_URL}/chat/stream",
            json={
                "session_id": session_id,
                "message": message
            },
            stream=True,
            timeout=60
        )

        if response.status_code != 200:
            error = f"HTTP {response.status_code}: {response.text}"
            print(f"❌ ERROR: {error}")
            issues_found.append({
                "flow": flow_num,
                "message": msg_num,
                "user_input": message,
                "error": error,
                "type": "http_error"
            })
            return "", []

        # Parse SSE stream
        bot_response = ""
        quick_replies = []
        tool_calls = []
        current_tool = None

        for line in response.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue

            data_str = line[6:]  # Remove "data: " prefix
            if data_str.strip() == "[DONE]":
                break

            try:
                event = json.loads(data_str)
                event_type = event.get("type", "")

                # Track tool calls
                if event_type == "TOOL_CALL_START":
                    current_tool = event.get("tool_name")
                    tool_calls.append(current_tool)
                    print(f"  🔧 Tool: {current_tool}")

                # Collect response text
                elif event_type == "TEXT_MESSAGE_CONTENT":
                    delta = event.get("delta", "")
                    bot_response += delta

                # Get quick replies
                elif event_type == "QUICK_REPLIES":
                    quick_replies = event.get("replies", [])

            except json.JSONDecodeError as e:
                print(f"  ⚠️ JSON parse error: {data_str[:100]}")

        # Display response
        print(f"\nBOT: {bot_response[:500]}{'...' if len(bot_response) > 500 else ''}")

        if tool_calls:
            print(f"\nTools Called: {', '.join(tool_calls)}")

        if quick_replies:
            print(f"\nQuick Replies ({len(quick_replies)}):")
            for i, qr in enumerate(quick_replies[:10], 1):
                label = qr.get("label", qr) if isinstance(qr, dict) else qr
                print(f"  {i}. {label}")
            if len(quick_replies) > 10:
                print(f"  ... and {len(quick_replies) - 10} more")
        else:
            print("\n⚠️ NO QUICK REPLIES")
            issues_found.append({
                "flow": flow_num,
                "message": msg_num,
                "user_input": message,
                "bot_response": bot_response[:200],
                "error": "No quick replies provided",
                "type": "missing_quick_replies"
            })

        # Check for errors in response
        if "error" in bot_response.lower() or "sorry" in bot_response.lower():
            issues_found.append({
                "flow": flow_num,
                "message": msg_num,
                "user_input": message,
                "bot_response": bot_response[:200],
                "error": "Bot apologized or mentioned error",
                "type": "bot_error_response"
            })

        return bot_response, quick_replies

    except requests.exceptions.Timeout:
        error = "Request timeout (>60s)"
        print(f"❌ ERROR: {error}")
        issues_found.append({
            "flow": flow_num,
            "message": msg_num,
            "user_input": message,
            "error": error,
            "type": "timeout"
        })
        return "", []

    except Exception as e:
        error = f"Exception: {str(e)}"
        print(f"❌ ERROR: {error}")
        issues_found.append({
            "flow": flow_num,
            "message": msg_num,
            "user_input": message,
            "error": error,
            "type": "exception"
        })
        return "", []


def flow_1_complete_ordering():
    """Flow 1: Complete ordering journey with all ordering tools"""
    session = "flow1_manual"
    flow_num = 1
    msg_count = 0

    print(f"\n{'#'*80}")
    print(f"FLOW 1: COMPLETE ORDERING JOURNEY")
    print(f"Goal: Touch all ordering, cart, payment, and tracking tools")
    print(f"{'#'*80}")

    # Message 1: Greeting
    msg_count += 1
    resp, qr = send_message(session, "Hi", flow_num, msg_count)
    time.sleep(1)

    # Message 2: Show menu
    msg_count += 1
    resp, qr = send_message(session, "show menu", flow_num, msg_count)
    time.sleep(1)

    # Message 3: Ask for popular items
    msg_count += 1
    resp, qr = send_message(session, "what's popular?", flow_num, msg_count)
    time.sleep(1)

    # Message 4: Ask about combo deals
    msg_count += 1
    resp, qr = send_message(session, "do you have combo deals?", flow_num, msg_count)
    time.sleep(1)

    # Message 5: Search for specific item
    msg_count += 1
    resp, qr = send_message(session, "search for pizza", flow_num, msg_count)
    time.sleep(1)

    # Message 6: Get item details
    msg_count += 1
    resp, qr = send_message(session, "tell me about margherita pizza", flow_num, msg_count)
    time.sleep(1)

    # Message 7: Check nutrition info
    msg_count += 1
    resp, qr = send_message(session, "show nutrition information", flow_num, msg_count)
    time.sleep(1)

    # Message 8: Check item availability
    msg_count += 1
    resp, qr = send_message(session, "is it available?", flow_num, msg_count)
    time.sleep(1)

    # Message 9: Add to cart
    msg_count += 1
    resp, qr = send_message(session, "add 2 margherita pizza to cart", flow_num, msg_count)
    time.sleep(1)

    # Message 10: Add more items
    msg_count += 1
    resp, qr = send_message(session, "add chicken burger", flow_num, msg_count)
    time.sleep(1)

    # Message 11: Add fries (upsell trigger)
    msg_count += 1
    resp, qr = send_message(session, "add french fries", flow_num, msg_count)
    time.sleep(1)

    # Message 12: View cart
    msg_count += 1
    resp, qr = send_message(session, "view cart", flow_num, msg_count)
    time.sleep(1)

    # Message 13: Update quantity
    msg_count += 1
    resp, qr = send_message(session, "change pizza quantity to 3", flow_num, msg_count)
    time.sleep(1)

    # Message 14: Add special instructions
    msg_count += 1
    resp, qr = send_message(session, "add instructions: extra cheese on pizza", flow_num, msg_count)
    time.sleep(1)

    # Message 15: Remove item
    msg_count += 1
    resp, qr = send_message(session, "remove fries from cart", flow_num, msg_count)
    time.sleep(1)

    # Message 16: View cart again
    msg_count += 1
    resp, qr = send_message(session, "show my cart", flow_num, msg_count)
    time.sleep(1)

    # Message 17: Apply promo code (should trigger if cart > Rs.500)
    msg_count += 1
    resp, qr = send_message(session, "apply promo code SAVE20", flow_num, msg_count)
    time.sleep(1)

    # Message 18: Validate promo code
    msg_count += 1
    resp, qr = send_message(session, "is this promo valid?", flow_num, msg_count)
    time.sleep(1)

    # Message 19: Checkout
    msg_count += 1
    resp, qr = send_message(session, "checkout", flow_num, msg_count)
    time.sleep(1)

    # Message 20: Select order type - dine in
    msg_count += 1
    resp, qr = send_message(session, "dine in", flow_num, msg_count)
    time.sleep(1)

    # Message 21: Continue order (skip booking suggestion)
    msg_count += 1
    resp, qr = send_message(session, "continue with order", flow_num, msg_count)
    time.sleep(1)

    # Message 22: Payment method
    msg_count += 1
    resp, qr = send_message(session, "I want to pay by card", flow_num, msg_count)
    time.sleep(1)

    # Message 23: Initiate payment (this should happen automatically)
    msg_count += 1
    resp, qr = send_message(session, "proceed with payment", flow_num, msg_count)
    time.sleep(1)

    # Message 24: Submit card details
    msg_count += 1
    resp, qr = send_message(session, "card number 1234567890123456", flow_num, msg_count)
    time.sleep(1)

    # Message 25: Verify OTP
    msg_count += 1
    resp, qr = send_message(session, "otp is 123456", flow_num, msg_count)
    time.sleep(1)

    # Message 26: Get order status
    msg_count += 1
    resp, qr = send_message(session, "track my order", flow_num, msg_count)
    time.sleep(1)

    # Message 27: Get receipt
    msg_count += 1
    resp, qr = send_message(session, "show receipt", flow_num, msg_count)
    time.sleep(1)

    # Message 28: Rate order
    msg_count += 1
    resp, qr = send_message(session, "rate 5 stars", flow_num, msg_count)
    time.sleep(1)

    # Message 29: Submit feedback
    msg_count += 1
    resp, qr = send_message(session, "food was excellent, fast delivery", flow_num, msg_count)
    time.sleep(1)

    # Message 30: Add to favorites
    msg_count += 1
    resp, qr = send_message(session, "add margherita pizza to favorites", flow_num, msg_count)
    time.sleep(1)

    print(f"\n✅ Flow 1 Complete: {msg_count} messages sent")
    return msg_count


# Run Flow 1
print("Starting Manual Flow Testing...")
print(f"Target: 20 flows, ~100 messages each, touching all 50 tools")
print(f"Base URL: {BASE_URL}")
print("\n")

total_messages = flow_1_complete_ordering()

# Summary
print(f"\n{'='*80}")
print(f"TESTING SUMMARY")
print(f"{'='*80}")
print(f"Total Messages Sent: {total_messages}")
print(f"Issues Found: {len(issues_found)}")

if issues_found:
    print(f"\n❌ ISSUES DETECTED:")
    for i, issue in enumerate(issues_found, 1):
        print(f"\n{i}. Flow {issue['flow']}, Message {issue['message']}")
        print(f"   User Input: {issue['user_input']}")
        print(f"   Error Type: {issue['type']}")
        print(f"   Error: {issue['error']}")
        if 'bot_response' in issue:
            print(f"   Bot Response: {issue['bot_response']}")
else:
    print("\n✅ NO ISSUES FOUND")

print(f"\n{'='*80}")
