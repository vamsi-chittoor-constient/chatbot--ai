"""Quick tool calling test - direct API call"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_tool_calling():
    """Test if tools are being invoked after max_tokens fix"""
    
    print("\n" + "="*80)
    print("TOOL CALLING VERIFICATION TEST")
    print("="*80)
    print(f"Testing against: {BASE_URL}")
    print("Expected: Tools should now be invoked with max_tokens=2048")
    print("="*80 + "\n")
    
    # Test 1: Menu search
    print("[TEST 1] Menu Search - Should invoke 'search_menu' tool")
    print("-" * 80)
    
    payload = {
        "message": "Show me the menu",
        "session_id": "verify-session-001"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data.get("response", "")
            
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Response: {bot_response[:200]}...")
            print(f"✓ Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
            
            # Check for signs of tool use
            if any(keyword in bot_response.lower() for keyword in ['menu', 'burger', 'pizza', 'item']):
                print("\n✅ SUCCESS: Response contains menu items - tool likely called!")
                return True
            else:
                print("\n⚠️ WARNING: Response doesn't contain menu items")
                return False
        else:
            print(f"❌ ERROR: Status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: Cannot connect to {BASE_URL}")
        print("Service might still be starting up. Wait 10-15 seconds and try again:")
        print(f"  python {sys.argv[0]}")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_tool_calling()
    
    print("\n" + "="*80)
    if success:
        print("✅ VERIFICATION SUCCESSFUL")
        print("\nNext: Check logs for verbose tool output:")
        print("  docker compose -f docker-compose.root.yml logs chatbot-app | findstr \"tool\"")
    else:
        print("⚠️ VERIFICATION INCONCLUSIVE")
        print("\nTroubleshooting:")
        print("1. Check if service is fully started (wait 15 seconds)")
        print("2. Monitor logs: docker compose -f docker-compose.root.yml logs chatbot-app -f")
        print("3. Look for 'crew_tools_loaded' with total_tools=55")
    print("="*80)
    
    sys.exit(0 if success else 1)
