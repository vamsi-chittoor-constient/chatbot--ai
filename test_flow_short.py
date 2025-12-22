"""Short flow test - 10 messages to check system behavior"""
import requests
import json
import time
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://localhost:8000/api/v1"
issues = []

def send_msg(session, msg, num):
    print(f"\n{'='*60}")
    print(f"MSG {num}: {msg}")
    print(f"{'='*60}")

    resp = requests.post(
        f"{BASE_URL}/chat/stream",
        json={"session_id": session, "message": msg},
        stream=True,
        timeout=60
    )

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
                tools.append(event.get("tool_name"))
            elif etype == "TEXT_MESSAGE_CONTENT":
                text += event.get("delta", "")
            elif etype == "QUICK_REPLIES":
                qr = event.get("replies", [])
        except:
            pass

    print(f"BOT: {text[:300]}{'...' if len(text) > 300 else ''}")

    if tools:
        print(f"TOOLS: {', '.join(tools)}")

    if qr:
        print(f"QUICK REPLIES ({len(qr)}):")
        for i, q in enumerate(qr[:8], 1):
            print(f"  {i}. {q.get('label', q)}")
    else:
        print("⚠️  NO QUICK REPLIES!")
        issues.append({"msg": num, "input": msg, "issue": "no_quick_replies"})

    time.sleep(1)
    return text, qr, tools

print("Starting short flow test (10 messages)...")

msgs = [
    "Hi",
    "show me the menu",
    "what's popular?",
    "add chicken burger",
    "add 2",
    "view cart",
    "checkout",
    "dine in",
    "continue order",
    "pay by card"
]

session = "flow_short_test"
for i, m in enumerate(msgs, 1):
    send_msg(session, m, i)

print(f"\n{'='*60}")
print(f"SUMMARY: {len(issues)} issues found")
for issue in issues:
    print(f"  Msg {issue['msg']}: {issue['input']} - {issue['issue']}")
print(f"{'='*60}")
