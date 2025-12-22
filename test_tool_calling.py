"""Test chatbot with real conversation to verify tool calling after max_tokens fix"""
import requests
import json
import time

BASE_URL = "http://localhost"

def test_chat(message: str, session_id: str = "test-session-001"):
    """Send a chat message and get response"""
    url = f"{BASE_URL}/api/v1/chat"
    
    payload = {
        "message": message,
        "session_id": session_id
    }
    
    print(f"\n{'='*80}")
    print(f"USER: {message}")
    print(f"{'='*80}\n")
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        bot_response = data.get("response", "No response")
        
        print(f"BOT: {bot_response}\n")
        print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
        
        return data
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    print("\n" + "="*80)
    print("CHATBOT TOOL CALLING TEST - After max_tokens Fix (512 -> 2048)")
    print("="*80)
    print("\nExpected behavior: Tools should now be invoked!")
    print("Watch for tool calls in verbose logs...")
    print("\n" + "="*80)
    
    # Test 1: Simple menu search (should trigger search_menu tool)
    print("\n[TEST 1] Menu Search - Should invoke search_menu tool")
    test_chat("Show me the menu")
    time.sleep(2)
    
    # Test 2: Add to cart (should trigger add_to_cart tool)
    print("\n[TEST 2] Add to Cart - Should invoke add_to_cart tool")
    test_chat("Add 2 beef burgers to my cart")
    time.sleep(2)
    
    # Test 3: View cart (should trigger view_cart tool)
    print("\n[TEST 3] View Cart - Should invoke view_cart tool")
    test_chat("Show my cart")
    time.sleep(2)
    
    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print("\nIf you saw tool calls in the chatbot logs above,")
    print("the max_tokens fix (512 -> 2048) has SOLVED the issue! ✓")
    print("\nCheck chatbot logs with:")
    print("docker compose -f docker-compose.root.yml logs chatbot-app -f")
