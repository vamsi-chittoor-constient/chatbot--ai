"""
First Message Latency Test
==========================
Tests whether the LLM pre-warming optimization reduces first message latency.

Before optimization: First message ~5-10 seconds (LLM cold start)
After optimization: First message ~2-3 seconds (LLM pre-warmed)
"""

import asyncio
import aiohttp
import time
import uuid
import json

BASE_URL = "http://localhost:8000"
STREAM_ENDPOINT = f"{BASE_URL}/api/v1/chat/stream"
TEST_OTP = "123456"


async def send_message(session: aiohttp.ClientSession, message: str, session_id: str, device_id: str, history: list) -> tuple[str, float]:
    """Send message and measure response time."""
    payload = {
        "message": message,
        "session_id": session_id,
        "device_id": device_id,
        "conversation_history": history
    }

    start = time.time()
    response_text = ""

    try:
        async with session.post(STREAM_ENDPOINT, json=payload, timeout=aiohttp.ClientTimeout(total=60)) as response:
            async for line in response.content:
                line = line.decode('utf-8').strip()
                if line.startswith('data:'):
                    try:
                        data = json.loads(line[5:].strip())
                        if data.get('type') == 'TEXT_MESSAGE_CONTENT':
                            response_text += data.get('delta', '')
                        elif data.get('type') == 'RUN_FINISHED':
                            break
                    except:
                        continue
    except Exception as e:
        response_text = f"Error: {e}"

    return response_text, time.time() - start


async def test_first_message_latency():
    """Test first message latency with a fresh session."""
    print("=" * 60)
    print("FIRST MESSAGE LATENCY TEST")
    print("=" * 60)
    print()

    # Fresh session (no cache)
    session_id = f"latency_test_{uuid.uuid4().hex[:8]}"
    device_id = f"device_{uuid.uuid4().hex[:8]}"
    phone = f"+9199{int(time.time()) % 100000000:08d}"

    print(f"Session ID: {session_id}")
    print(f"Phone: {phone}")
    print()

    async with aiohttp.ClientSession() as http_session:
        history = []

        # Message 1: Initial "Hi" (triggers auth flow)
        print("Message 1: 'Hi' (auth flow start)...")
        response, latency = await send_message(http_session, "Hi", session_id, device_id, history)
        print(f"  Response time: {latency:.2f}s")
        print(f"  Response: {response[:100]}...")
        history.extend([f"User: Hi", f"Assistant: {response}"])
        print()

        # Message 2: Phone number
        print(f"Message 2: '{phone}' (phone input)...")
        response, latency = await send_message(http_session, phone, session_id, device_id, history)
        print(f"  Response time: {latency:.2f}s")
        print(f"  Response: {response[:100]}...")
        history.extend([f"User: {phone}", f"Assistant: {response}"])
        print()

        # Message 3: OTP
        print(f"Message 3: '{TEST_OTP}' (OTP verification)...")
        response, latency = await send_message(http_session, TEST_OTP, session_id, device_id, history)
        print(f"  Response time: {latency:.2f}s")
        print(f"  Response: {response[:100]}...")
        history.extend([f"User: {TEST_OTP}", f"Assistant: {response}"])
        print()

        # Message 4: Name (if new user)
        if "name" in response.lower():
            print("Message 4: 'TestUser' (name for new user)...")
            response, latency = await send_message(http_session, "TestUser", session_id, device_id, history)
            print(f"  Response time: {latency:.2f}s")
            print(f"  Response: {response[:100]}...")
            history.extend([f"User: TestUser", f"Assistant: {response}"])
            print()

        # Message 5: FIRST CREW MESSAGE - This is what we're measuring!
        print("=" * 60)
        print("FIRST CREWAI MESSAGE (after auth):")
        print("=" * 60)
        print("Message: 'Show me the menu'...")
        start = time.time()
        response, latency = await send_message(http_session, "Show me the menu", session_id, device_id, history)
        print(f"  *** FIRST MESSAGE LATENCY: {latency:.2f}s ***")
        print(f"  Response: {response[:150]}...")
        history.extend([f"User: Show me the menu", f"Assistant: {response}"])
        print()

        # Message 6: Second crew message (should be fast - crew cached)
        print("SECOND CREWAI MESSAGE (crew cached):")
        print("Message: 'Add a burger'...")
        response, latency = await send_message(http_session, "Add a burger", session_id, device_id, history)
        print(f"  Second message latency: {latency:.2f}s")
        print(f"  Response: {response[:150]}...")
        print()

        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print("With LLM pre-warming:")
        print("- LLM connection established at server startup")
        print("- Shared across all sessions (singleton)")
        print("- First message should be ~2-4s (not 8-10s)")
        print()


if __name__ == "__main__":
    asyncio.run(test_first_message_latency())
