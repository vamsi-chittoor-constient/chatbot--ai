
import asyncio
import websockets
import json
import time
import random

# Configuration
WS_URL = "ws://localhost/api/v1/chat"
NUM_USERS = 20
TEST_DURATION = 30  # seconds

async def sim_user(user_id):
    session_id = f"loadtest_user_{user_id}_{int(time.time())}"
    uri = f"{WS_URL}/{session_id}?api_key=test_key&tester_id=load_tester"
    
    print(f"[User {user_id}] Connecting with session: {session_id}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"[User {user_id}] Connected!")
            
            # Wait for initial messages (Welcome / Auth)
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(response)
                    msg_type = data.get("message_type")
                    content = data.get("message", "")
                    
                    print(f"[User {user_id}] Received: {msg_type} - {content[:50]}...")
                    
                    if msg_type == "ai_response" and "Welcome" in content:
                        break
                    if "Setting up your personal waiter" in content or "thinking" in content:
                        continue
                        
            except asyncio.TimeoutError:
                print(f"[User {user_id}] Timeout waiting for welcome")

            # Simulate simple interaction
            await asyncio.sleep(random.uniform(1, 5))
            msg = "Hi, what's on the menu?"
            payload = {
                "message": msg,
                "session_id": session_id,
                "user_id": f"user_{user_id}"
            }
            await websocket.send(json.dumps(payload))
            print(f"[User {user_id}] Sent: {msg}")
            
            # Wait for response
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                    data = json.loads(response)
                    msg_type = data.get("message_type")
                    content = data.get("message", "")
                    print(f"[User {user_id}] Response: {content[:50]}...")
                    if msg_type == "ai_response":
                        break
            except asyncio.TimeoutError:
                print(f"[User {user_id}] Timeout waiting for AI response")
                
            print(f"[User {user_id}] Finished session")

    except Exception as e:
        print(f"[User {user_id}] Error: {e}")

async def main():
    print(f"Starting load test with {NUM_USERS} users...")
    tasks = []
    for i in range(NUM_USERS):
        tasks.append(sim_user(i))
        # Stagger starts slightly to be realistic
        await asyncio.sleep(0.1)
    
    start_time = time.time()
    await asyncio.gather(*tasks)
    duration = time.time() - start_time
    print(f"\nLoad test completed in {duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(main())
