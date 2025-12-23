"""
Simple chat interface for testing the Restaurant Chatbot locally
"""
import asyncio
import websockets
import json
from datetime import datetime
import uuid

WS_URL = "ws://localhost:8000/api/v1/chat/{session_id}"

async def chat_with_bot():
    session_id = f"chat-{uuid.uuid4().hex[:8]}"
    url = WS_URL.format(session_id=session_id)

    print("=" * 80)
    print("🤖 RESTAURANT CHATBOT - Local Test Interface")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Connected to: {url}")
    print("=" * 80)
    print("\nType your message and press Enter. Type 'quit' to exit.\n")

    async with websockets.connect(url) as websocket:

        async def receive_messages():
            """Listen for messages from the bot"""
            response_text = ""

            async for msg in websocket:
                try:
                    data = json.loads(msg)
                    event_type = data.get("type", "")

                    # Collect text response
                    if event_type == "TEXT_MESSAGE_CONTENT":
                        content = data.get("content", "")
                        response_text += content
                        print(content, end="", flush=True)

                    # Show when run finishes
                    elif event_type == "RUN_FINISHED":
                        print("\n")
                        result = data.get("result", "")
                        if result and result != response_text:
                            print(f"Bot: {result}")
                        print("-" * 80)
                        response_text = ""

                    # Show activities
                    elif event_type == "ACTIVITY_START":
                        activity = data.get("activity", "")
                        if activity:
                            print(f"[Bot is {activity}...]", end=" ", flush=True)

                except json.JSONDecodeError:
                    pass
                except Exception as e:
                    print(f"\n[Error processing message: {e}]")

        # Start background task to receive messages
        receive_task = asyncio.create_task(receive_messages())

        try:
            while True:
                # Get user input
                user_input = await asyncio.get_event_loop().run_in_executor(
                    None, input, "\nYou: "
                )

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                if not user_input.strip():
                    continue

                # Send message to bot
                message = {
                    "message": user_input,
                    "timestamp": datetime.now().isoformat()
                }

                await websocket.send(json.dumps(message))
                print("\nBot: ", end="", flush=True)

                # Wait a moment for response
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")

        finally:
            receive_task.cancel()

if __name__ == "__main__":
    try:
        asyncio.run(chat_with_bot())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the chatbot service is running:")
        print("  docker compose -f docker-compose.root.yml ps")
