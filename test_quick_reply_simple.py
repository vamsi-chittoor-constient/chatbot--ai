"""Simple test to check if quick replies are being returned"""
import requests
import json

url = "http://localhost:8000/api/v1/chat/stream"
data = {
    "session_id": "test_quick_simple",
    "message": "Hi"
}

print(f"Sending request to {url}")
print(f"Data: {json.dumps(data, indent=2)}\n")

response = requests.post(url, json=data, stream=True)

print(f"Response status: {response.status_code}\n")
print("="*80)
print("RAW RESPONSE EVENTS:")
print("="*80)

found_quick_replies = False
event_count = 0

for line in response.iter_lines(decode_unicode=True):
    if not line or not line.startswith("data: "):
        continue

    data_str = line[6:]
    event_count += 1

    print(f"\nEvent {event_count}:")
    print(data_str)

    if data_str.strip() == "[DONE]":
        break

    try:
        event = json.loads(data_str)
        event_type = event.get("type", "")

        if event_type == "QUICK_REPLIES":
            found_quick_replies = True
            print("  *** QUICK REPLIES FOUND ***")
            print(f"  Options: {event.get('options', [])}")
    except:
        pass

print("\n" + "="*80)
print(f"Total events: {event_count}")
print(f"Quick replies found: {found_quick_replies}")
print("="*80)
