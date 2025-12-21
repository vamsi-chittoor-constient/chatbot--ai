"""Quick test of single chatbot conversation"""
import asyncio
import websockets
import json
from datetime import datetime

WS_URL = "ws://localhost:8000/api/v1/chat"

async def test_quick_chat():
    session_id = "quick-test-session"

    print("Connecting to chatbot...")
    uri = f"{WS_URL}/{session_id}?tester_id=quick-test"

    async with websockets.connect(uri) as websocket:
        print("Connected! Waiting for welcome message...")

        # Receive welcome
        welcome = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        print(f"Welcome: {json.loads(welcome).get('message', '')[:100]}...")

        # Send question
        print("\nSending: What's on your menu?")
        await websocket.send(json.dumps({
            "message": "What's on your menu?",
            "timestamp": datetime.utcnow().isoformat()
        }))

        # Wait for response
        print("Waiting for AI response...")
        for _ in range(5):  # Try up to 5 times
            response = await asyncio.wait_for(websocket.recv(), timeout=20.0)
            data = json.loads(response)

            if data.get("message_type") == "ai_response":
                print(f"\nAI Response:\n{data.get('message', '')}\n")
                break
            elif data.get("message_type") == "typing_indicator":
                print("  (AI is typing...)")

        print("Test completed!")

if __name__ == "__main__":
    asyncio.run(test_quick_chat())
