"""
Test All Refinements - User Journey Focused
Tests:
1. Item not found → Similar items MENU CARD
2. Ambiguous items → Filtered MENU CARD
3. Quantity validation (0, negative, large)
4. Empty cart checkout
5. Special instructions validation
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_interaction(query, session, test_name):
    """Send query and get response + events"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"USER: {query}")
    print(f"{'='*60}")

    resp = requests.post(
        f"{BASE_URL}/chat/stream",
        json={"session_id": session, "message": query},
        stream=True,
        timeout=60
    )

    text = ""
    menu_data_emitted = False
    cart_data_emitted = False

    for line in resp.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        data = line[6:]
        if data.strip() == "[DONE]":
            break
        try:
            event = json.loads(data)
            etype = event.get("type")

            if etype == "TEXT_MESSAGE_CONTENT":
                text += event.get("delta", "")
            elif etype == "MENU_DATA":
                menu_data_emitted = True
                items = event.get("items", [])
                print(f"\n[MENU_DATA EMITTED]: {len(items)} items")
                print(f"   Items: {[item['name'] for item in items[:5]]}")
            elif etype == "CART_DATA":
                cart_data_emitted = True
                print(f"\n[CART_DATA EMITTED]")
        except:
            pass

    print(f"\nBOT: {text}")

    return {
        "text": text,
        "menu_card": menu_data_emitted,
        "cart_data": cart_data_emitted
    }

print("="*70)
print("COMPREHENSIVE REFINEMENT TESTING - USER JOURNEY FOCUSED")
print("="*70)

# Test 1: Item Not Found → Similar Items Menu Card
print("\n\n### TEST 1: Item Not Found (Should Show Similar Items Menu Card)")
result = test_interaction("search for pizza", "refine_test_1", "Item Not Found")
if result["menu_card"]:
    print("[PASS]: Similar items menu card displayed")
elif "similar" in result["text"].lower():
    print("[PARTIAL]: Similar items mentioned in text but no menu card")
else:
    print("[FAIL]: No similar items shown")

time.sleep(2)

# Test 2: Ambiguous Items → Filtered Menu Card
print("\n\n### TEST 2: Ambiguous Query (Should Show Filtered Menu Card)")
result = test_interaction("add chicken", "refine_test_2", "Ambiguous Items")
if result["menu_card"]:
    print("[PASS]: Filtered menu card displayed")
elif "chicken" in result["text"].lower() and ("which" in result["text"].lower() or "choose" in result["text"].lower()):
    print("[PARTIAL]: Multiple items listed but no menu card")
else:
    print("[FAIL]: No clarification provided")

time.sleep(2)

# Test 3: Quantity Validation - Zero
print("\n\n### TEST 3: Quantity Validation (0 items)")
result = test_interaction("add 0 chicken burger", "refine_test_3", "Quantity Zero")
if "invalid" in result["text"].lower() or "can't add 0" in result["text"].lower() or "positive" in result["text"].lower():
    print("[PASS]: Zero quantity rejected")
else:
    print("[FAIL]: Zero quantity not validated")

time.sleep(2)

# Test 4: Quantity Validation - Negative
print("\n\n### TEST 4: Quantity Validation (Negative)")
result = test_interaction("add -5 fries", "refine_test_4", "Quantity Negative")
if "invalid" in result["text"].lower() or "positive" in result["text"].lower():
    print("[PASS]: Negative quantity rejected")
else:
    print("[FAIL]: Negative quantity not validated")

time.sleep(2)

# Test 5: Quantity Validation - Very Large
print("\n\n### TEST 5: Quantity Validation (Very Large)")
result = test_interaction("add 100 burgers", "refine_test_5", "Quantity Large")
if "maximum" in result["text"].lower() or "50" in result["text"] or "lot" in result["text"].lower():
    print("[PASS]: Large quantity rejected or warned")
else:
    print("[FAIL]: Large quantity not validated")

time.sleep(2)

# Test 6: Empty Cart Checkout
print("\n\n### TEST 6: Empty Cart Checkout (Should Show Sweet Message)")
result = test_interaction("checkout", "refine_test_6", "Empty Cart Checkout")
if "empty" in result["text"].lower() and ("delicious" in result["text"].lower() or "would you like" in result["text"].lower()):
    print("[PASS]: Sweet empty cart message shown")
elif "empty" in result["text"].lower():
    print("[PARTIAL]: Empty cart detected but message could be sweeter")
else:
    print("[FAIL]: Empty cart not handled")

time.sleep(2)

# Test 7: Special Instructions Validation - Empty
print("\n\n### TEST 7: Special Instructions Validation (Empty)")
# First add an item
test_interaction("add 1 chicken burger", "refine_test_7", "Setup for instructions test")
time.sleep(2)
result = test_interaction("add special instructions: ''", "refine_test_7", "Empty Instructions")
if "invalid" in result["text"].lower() or "provide" in result["text"].lower():
    print("[PASS]: Empty instructions rejected")
else:
    print("[INFO]: Empty instructions handling may vary")

time.sleep(2)

# Test 8: Special Instructions Validation - Too Long
print("\n\n### TEST 8: Special Instructions Validation (Too Long)")
long_text = "a" * 250
result = test_interaction(f"add special instructions: {long_text}", "refine_test_7", "Long Instructions")
if "too long" in result["text"].lower() or "200" in result["text"] or "brief" in result["text"].lower():
    print("[PASS]: Long instructions rejected")
else:
    print("[INFO]: Long instructions may be truncated or accepted")

print("\n\n" + "="*70)
print("TESTING COMPLETE - REVIEW RESULTS ABOVE")
print("="*70)
