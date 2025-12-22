"""
Comprehensive flow testing - Finding all system issues
Tests multiple user journeys to stress-test all 50 tools
"""
import requests
import json
import time
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"
all_issues = []
tools_used = set()

def send_msg(session, msg, flow_name, msg_num):
    """Send message and track response"""
    global all_issues, tools_used

    print(f"\n[{flow_name}] MSG {msg_num}: {msg}")

    try:
        resp = requests.post(
            f"{BASE_URL}/chat/stream",
            json={"session_id": session, "message": msg},
            stream=True,
            timeout=60
        )

        if resp.status_code != 200:
            print(f"  ❌ HTTP {resp.status_code}")
            all_issues.append({
                "flow": flow_name,
                "msg": msg_num,
                "input": msg,
                "issue": f"http_error_{resp.status_code}"
            })
            return "", [], []

        text = ""
        qr = []
        tools = []

        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue

            data = line[6:]
            if data.strip() == "[DONE]":
                break

            try:
                event = json.loads(data)
                etype = event.get("type")

                if etype == "TOOL_CALL_START":
                    tool_name = event.get("tool_name")
                    tools.append(tool_name)
                    tools_used.add(tool_name)
                elif etype == "TEXT_MESSAGE_CONTENT":
                    text += event.get("delta", "")
                elif etype == "QUICK_REPLIES":
                    qr = event.get("replies", [])
            except:
                pass

        print(f"  BOT: {text[:150]}{'...' if len(text) > 150 else ''}")
        if tools:
            print(f"  TOOLS: {', '.join(tools)}")
        if qr:
            print(f"  QR ({len(qr)}): {', '.join([q.get('label', str(q))[:20] for q in qr[:5]])}")
        else:
            print(f"  ⚠️  NO QUICK REPLIES")
            all_issues.append({
                "flow": flow_name,
                "msg": msg_num,
                "input": msg,
                "issue": "no_quick_replies"
            })

        # Check for issues
        if "error" in text.lower() and "no error" not in text.lower():
            all_issues.append({
                "flow": flow_name,
                "msg": msg_num,
                "input": msg,
                "bot_response": text[:200],
                "issue": "bot_error_in_response"
            })

        if "sorry" in text.lower() or "can't" in text.lower() or "cannot" in text.lower():
            all_issues.append({
                "flow": flow_name,
                "msg": msg_num,
                "input": msg,
                "bot_response": text[:200],
                "issue": "bot_apologized_or_failed"
            })

        time.sleep(0.5)  # Rate limit
        return text, qr, tools

    except Exception as e:
        print(f"  ❌ EXCEPTION: {str(e)[:100]}")
        all_issues.append({
            "flow": flow_name,
            "msg": msg_num,
            "input": msg,
            "issue": f"exception: {str(e)[:100]}"
        })
        return "", [], []


print("="*80)
print("COMPREHENSIVE FLOW TESTING")
print("Testing multiple user journeys to find all system issues")
print("="*80)

# FLOW 2: Payment test
print("\n### FLOW 2: Payment Flow Test ###")
session = "flow2_pay"
for i, m in enumerate(["Hi", "show menu", "add chicken burger", "2", "view cart", "checkout", "take away", "card payment"], 1):
    send_msg(session, m, "FLOW2", i)

# FLOW 3: Booking test
print("\n### FLOW 3: Booking Test ###")
session = "flow3_book"
for i, m in enumerate(["Hi", "book a table", "tomorrow at 7pm", "4 people", "confirm"], 1):
    send_msg(session, m, "FLOW3", i)

# Summary
print("\n" + "="*80)
print(f"Issues: {len(all_issues)}, Tools Used: {len(tools_used)}")
if tools_used:
    print(f"Tools: {', '.join(sorted(list(tools_used)))}")
print("="*80)
