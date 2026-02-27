"""
Unit tests for WhatsApp Bridge AGUI conversions
Tests all conversion functions to ensure correct WhatsApp API payloads
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json

# Import the app module
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from app import (
    _convert_search_results,
    _convert_menu_data,
    _convert_cart_data,
    _convert_payment_methods,
    _convert_payment_link,
    _convert_payment_success,
    _convert_quick_replies,
    _convert_order_data,
    _convert_receipt_link,
    _send_cart_item_buttons,
    _truncate,
    send_whatsapp_interactive,
    send_whatsapp_reply,
    _extract_user_message,
    _handle_flow_response,
    _active_flows,
)


# ===================================================================
# FIXTURES
# ===================================================================

@pytest.fixture
def mock_send_interactive():
    """Mock send_whatsapp_interactive to capture payloads"""
    with patch('app.send_whatsapp_interactive', new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def mock_send_reply():
    """Mock send_whatsapp_reply to capture messages"""
    with patch('app.send_whatsapp_reply', new_callable=AsyncMock) as mock:
        yield mock


# ===================================================================
# TEST UTILITY FUNCTIONS
# ===================================================================

def test_truncate():
    """Test text truncation"""
    assert _truncate("Hello", 10) == "Hello"
    assert _truncate("Hello World", 8) == "Hello..."
    assert _truncate("Test", 4) == "Test"  # Exactly at limit
    assert _truncate("Testing", 5) == "Te..."


# ===================================================================
# TEST SEARCH_RESULTS CONVERSION
# ===================================================================

@pytest.mark.asyncio
async def test_search_results_small_available(mock_send_interactive):
    """Test search results with ≤3 available items"""
    agui = {
        "query": "parota",
        "items": [
            {"name": "Parota Plain", "price": 40, "is_available_now": True, "category": "Breakfast"},
            {"name": "Parota Egg", "price": 60, "is_available_now": True, "category": "Breakfast"}
        ]
    }
    
    await _convert_search_results("1234567890", agui)
    
    # Should send button message
    assert mock_send_interactive.called
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "button"
    assert "parota" in payload["body"]["text"].lower()
    assert len(payload["action"]["buttons"]) == 2
    assert payload["action"]["buttons"][0]["reply"]["title"] == "Parota Plain"


@pytest.mark.asyncio
async def test_search_results_with_unavailable(mock_send_interactive):
    """Test search results with unavailable items"""
    agui = {
        "query": "parota",
        "items": [
            {"name": "Parota Plain", "price": 40, "is_available_now": True},
            {"name": "Parota Special", "price": 80, "is_available_now": False, "meal_types": ["Lunch", "Dinner"]}
        ]
    }
    
    await _convert_search_results("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    # Should show availability indicators
    body = payload["body"]["text"]
    assert "✅" in body  # Available indicator
    assert "🕐" in body  # Unavailable indicator
    assert "Lunch" in body or "Dinner" in body


@pytest.mark.asyncio
async def test_search_results_large_list(mock_send_interactive, no_flow_ids):
    """Test search results with >3 items (list message) - fallback without Flow IDs"""
    items = [{"name": f"Item {i}", "price": 50, "is_available_now": True, "category": "Food"} for i in range(5)]
    agui = {"query": "food", "items": items}
    
    await _convert_search_results("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "list"
    assert payload["action"]["button"] == "View Items"
    assert len(payload["action"]["sections"]) >= 1
    assert "Available Now" in payload["action"]["sections"][0]["title"]


# ===================================================================
# TEST MENU_DATA CONVERSION
# ===================================================================

@pytest.mark.asyncio
async def test_menu_small(mock_send_interactive, no_flow_ids):
    """Test small menu (≤100 items) with categories - fallback without Flow IDs"""
    items = [
        {"name": "Idli", "price": 30, "category": "Breakfast"},
        {"name": "Dosa", "price": 50, "category": "Breakfast"},
        {"name": "Biryani", "price": 180, "category": "Main Course"}
    ]
    agui = {
        "items": items,
        "categories": ["Breakfast", "Main Course"],
        "current_meal_period": "Breakfast"
    }
    
    await _convert_menu_data("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "list"
    assert "☕" in payload["body"]["text"]  # Breakfast emoji
    assert "Breakfast Time" in payload["body"]["text"]
    assert len(payload["action"]["sections"]) == 2  # Two categories


@pytest.mark.asyncio
async def test_menu_large(mock_send_interactive):
    """Test large menu (>100 items) shows category picker"""
    items = [{"name": f"Item {i}", "price": 50, "category": f"Cat {i % 15}"} for i in range(150)]
    agui = {"items": items, "current_meal_period": "Lunch"}
    
    await _convert_menu_data("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "list"
    assert "Choose Category" in payload["action"]["button"]
    assert "150 items" in payload["body"]["text"]


# ===================================================================
# TEST CART_DATA CONVERSION
# ===================================================================

@pytest.mark.asyncio
async def test_cart_empty(mock_send_reply):
    """Test empty cart"""
    agui = {"items": [], "total": 0}
    
    await _convert_cart_data("1234567890", agui)
    
    assert mock_send_reply.called
    message = mock_send_reply.call_args[0][1]
    assert "empty" in message.lower()


@pytest.mark.asyncio
async def test_cart_small(mock_send_reply, mock_send_interactive):
    """Test small cart (≤3 items) sends per-item buttons"""
    items = [
        {"name": "Coke", "quantity": 2, "price": 60},
        {"name": "Pizza", "quantity": 1, "price": 250}
    ]
    agui = {"items": items, "total": 370, "packaging_charge_per_item": 30}
    
    await _convert_cart_data("1234567890", agui)
    
    # Should send summary + per-item cards + checkout buttons
    assert mock_send_reply.called  # Summary
    assert mock_send_interactive.call_count >= 3  # 2 item cards + 1 checkout
    
    # Check summary
    summary = mock_send_reply.call_args[0][1]
    assert "Your Cart" in summary
    assert "Coke" in summary
    assert "370" in summary


@pytest.mark.asyncio
async def test_cart_item_buttons(mock_send_interactive):
    """Test individual cart item button card"""
    item = {"name": "Coke Big", "quantity": 3, "price": 57}
    
    await _send_cart_item_buttons("1234567890", item)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "button"
    assert "Coke Big" in payload["body"]["text"]
    assert "Quantity: 3" in payload["body"]["text"]
    assert len(payload["action"]["buttons"]) == 3
    assert payload["action"]["buttons"][0]["reply"]["title"] == "➕ Add One"
    assert payload["action"]["buttons"][1]["reply"]["title"] == "➖ Remove One"
    assert payload["action"]["buttons"][2]["reply"]["title"] == "🗑️ Delete"


@pytest.mark.asyncio
async def test_cart_large(mock_send_reply, mock_send_interactive, no_flow_ids):
    """Test large cart (>3 items) uses list-based modification - fallback without Flow IDs"""
    items = [{"name": f"Item {i}", "quantity": 1, "price": 50} for i in range(5)]
    agui = {"items": items, "total": 250}
    
    await _convert_cart_data("1234567890", agui)
    
    # Should send summary + action buttons (not per-item cards)
    assert mock_send_reply.called
    assert mock_send_interactive.called
    
    # Check action buttons
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    assert payload["type"] == "button"
    assert len(payload["action"]["buttons"]) == 3
    button_titles = [b["reply"]["title"] for b in payload["action"]["buttons"]]
    assert "Modify Items" in button_titles
    assert "Checkout" in button_titles


# ===================================================================
# TEST PAYMENT CONVERSIONS
# ===================================================================

@pytest.mark.asyncio
async def test_payment_methods(mock_send_interactive):
    """Test payment method selection"""
    agui = {
        "methods": [
            {"label": "💳 Pay Online", "action": "pay_online", "description": "Card/UPI/NetBanking"},
            {"label": "💵 Cash", "action": "pay_cash", "description": "Pay on delivery"}
        ],
        "amount": 450,
        "order_id": "ORD-123"
    }
    
    await _convert_payment_methods("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "button"
    assert "₹450" in payload["body"]["text"]
    assert len(payload["action"]["buttons"]) == 2


@pytest.mark.asyncio
async def test_payment_link(mock_send_interactive):
    """Test payment link CTA button"""
    agui = {
        "payment_link": "https://rzp.io/l/test123",
        "amount": 450
    }
    
    await _convert_payment_link("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "cta_url"
    assert "₹450" in payload["body"]["text"]
    assert payload["action"]["name"] == "cta_url"
    assert payload["action"]["parameters"]["display_text"] == "Pay Now"
    assert payload["action"]["parameters"]["url"] == "https://rzp.io/l/test123"


@pytest.mark.asyncio
async def test_payment_success(mock_send_interactive):
    """Test payment success message"""
    agui = {
        "order_number": "ORD-ABC123",
        "amount": 450,
        "order_type": "takeaway",
        "quick_replies": [
            {"label": "📄 View Receipt", "action": "view_receipt"},
            {"label": "🍽️ Order More", "action": "order_more"}
        ]
    }
    
    await _convert_payment_success("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "button"
    assert "✅" in payload["body"]["text"]
    assert "ORD-ABC123" in payload["body"]["text"]
    assert "₹450" in payload["body"]["text"]
    assert len(payload["action"]["buttons"]) == 2


# ===================================================================
# TEST QUICK_REPLIES CONVERSION
# ===================================================================

@pytest.mark.asyncio
async def test_quick_replies_small(mock_send_interactive):
    """Test quick replies with ≤3 options"""
    agui = {
        "replies": [
            {"label": "Yes", "action": "yes"},
            {"label": "No", "action": "no"}
        ]
    }
    
    await _convert_quick_replies("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "button"
    assert len(payload["action"]["buttons"]) == 2


@pytest.mark.asyncio
async def test_quick_replies_medium_split(mock_send_interactive):
    """Test quick replies with 5 options split into 2 button messages (3+2)"""
    agui = {
        "replies": [{"label": f"Option {i}", "action": f"opt_{i}"} for i in range(5)]
    }

    await _convert_quick_replies("1234567890", agui)

    # Should send 2 button messages (3 + 2)
    assert mock_send_interactive.call_count == 2

    first = mock_send_interactive.call_args_list[0][0][1]
    assert first["type"] == "button"
    assert len(first["action"]["buttons"]) == 3
    assert first["body"]["text"] == "Choose an option:"

    second = mock_send_interactive.call_args_list[1][0][1]
    assert second["type"] == "button"
    assert len(second["action"]["buttons"]) == 2
    assert second["body"]["text"] == "More options:"


@pytest.mark.asyncio
async def test_quick_replies_10_split(mock_send_interactive):
    """Test 10 quick replies split into 4 button messages (3+3+3+1)"""
    agui = {
        "replies": [{"label": f"Opt {i}", "action": f"opt_{i}"} for i in range(10)]
    }
    await _convert_quick_replies("1234567890", agui)

    assert mock_send_interactive.call_count == 4
    for call in mock_send_interactive.call_args_list:
        assert call[0][1]["type"] == "button"


@pytest.mark.asyncio
async def test_quick_replies_11_list_fallback(mock_send_interactive):
    """Test >10 quick replies fall back to list message"""
    agui = {
        "replies": [{"label": f"Option {i}", "action": f"opt_{i}"} for i in range(11)]
    }
    await _convert_quick_replies("1234567890", agui)

    assert mock_send_interactive.call_count == 1
    payload = mock_send_interactive.call_args[0][1]
    assert payload["type"] == "list"
    assert len(payload["action"]["sections"][0]["rows"]) == 10


# ===================================================================
# TEST ORDER_DATA CONVERSION
# ===================================================================

@pytest.mark.asyncio
async def test_order_data(mock_send_reply):
    """Test order details formatting"""
    agui = {
        "order_id": "ORD-ABC123",
        "items": [
            {"name": "Coke", "quantity": 2, "price": 60},
            {"name": "Pizza", "quantity": 1, "price": 250}
        ],
        "total": 370,
        "status": "confirmed",
        "order_type": "dine_in"
    }
    
    await _convert_order_data("1234567890", agui)
    
    message = mock_send_reply.call_args[0][1]
    assert "📋" in message
    assert "ORD-ABC123" in message
    assert "Confirmed" in message
    assert "Dine In" in message
    assert "₹370" in message


# ===================================================================
# TEST RECEIPT_LINK CONVERSION
# ===================================================================

@pytest.mark.asyncio
async def test_receipt_link(mock_send_interactive):
    """Test receipt download link"""
    agui = {
        "order_number": "ORD-ABC123",
        "amount": 450,
        "download_url": "https://example.com/receipt.pdf",
        "items": [
            {"name": "Coke", "quantity": 2, "price": 60},
            {"name": "Pizza", "quantity": 1, "price": 250}
        ]
    }
    
    await _convert_receipt_link("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    assert payload["type"] == "cta_url"
    assert "🧾" in payload["body"]["text"]
    assert "ORD-ABC123" in payload["body"]["text"]
    assert "Coke × 2" in payload["body"]["text"]
    assert payload["action"]["parameters"]["display_text"] == "Download Receipt"
    assert payload["action"]["parameters"]["url"] == "https://example.com/receipt.pdf"


# ===================================================================
# TEST EDGE CASES
# ===================================================================

@pytest.mark.asyncio
async def test_empty_items_list(mock_send_interactive):
    """Test handling of empty items list"""
    agui = {"items": [], "query": "test"}
    
    await _convert_search_results("1234567890", agui)
    
    # Should not send anything
    assert not mock_send_interactive.called


@pytest.mark.asyncio
async def test_long_text_truncation(mock_send_interactive):
    """Test text truncation in various fields"""
    agui = {
        "query": "test",
        "items": [
            {
                "name": "A" * 50,  # Very long name
                "price": 100,
                "is_available_now": True,
                "category": "B" * 30
            }
        ]
    }
    
    await _convert_search_results("1234567890", agui)
    
    call_args = mock_send_interactive.call_args[0]
    payload = call_args[1]
    
    # Button title should be truncated to 20 chars
    button_title = payload["action"]["buttons"][0]["reply"]["title"]
    assert len(button_title) <= 20


@pytest.mark.asyncio
async def test_missing_optional_fields():
    """Test handling of missing optional fields"""
    agui = {
        "items": [{"name": "Test"}]  # Missing price, category, etc.
    }
    
    # Should not crash
    with patch('app.send_whatsapp_interactive', new_callable=AsyncMock):
        await _convert_search_results("1234567890", agui)


# ===================================================================
# TEST WHATSAPP API PAYLOAD STRUCTURE
# ===================================================================

@pytest.mark.asyncio
async def test_button_payload_structure():
    """Test button message payload matches WhatsApp API spec"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "test123"}]}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        payload = {
            "type": "button",
            "body": {"text": "Test message"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "btn1", "title": "Button 1"}}
                ]
            }
        }
        
        result = await send_whatsapp_interactive("1234567890", payload)
        
        assert result is True
        # Verify API call structure
        call_args = mock_client.return_value.__aenter__.return_value.post.call_args
        sent_payload = call_args[1]["json"]
        assert sent_payload["type"] == "interactive"
        assert sent_payload["interactive"]["type"] == "button"


@pytest.mark.asyncio
async def test_list_payload_structure():
    """Test list message payload matches WhatsApp API spec"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "test123"}]}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        payload = {
            "type": "list",
            "body": {"text": "Choose an option"},
            "action": {
                "button": "View Options",
                "sections": [
                    {
                        "title": "Section 1",
                        "rows": [
                            {"id": "row1", "title": "Row 1", "description": "Desc 1"}
                        ]
                    }
                ]
            }
        }
        
        result = await send_whatsapp_interactive("1234567890", payload)
        
        assert result is True


@pytest.mark.asyncio
async def test_cta_url_payload_structure():
    """Test CTA URL payload matches WhatsApp API spec"""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"messages": [{"id": "test123"}]}
        mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
        
        payload = {
            "type": "cta_url",
            "body": {"text": "Click to visit"},
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": "Visit Site",
                    "url": "https://example.com"
                }
            }
        }
        
        result = await send_whatsapp_interactive("1234567890", payload)
        
        assert result is True


# ===================================================================
# TEST NFM_REPLY EXTRACTION
# ===================================================================

def test_extract_nfm_reply():
    """Test nfm_reply extraction from Flow completion"""
    message = {
        "type": "interactive",
        "interactive": {
            "type": "nfm_reply",
            "nfm_reply": {
                "response_json": json.dumps({
                    "flow_type": "select_items",
                    "selected_items": ["Masala Dosa", "Coffee"]
                }),
                "body": "Sent",
                "name": "flow",
            },
        },
    }
    result = _extract_user_message(message, "interactive")
    assert result is not None
    assert result.startswith("__FLOW_RESPONSE__")
    assert "Masala Dosa" in result


def test_extract_nfm_reply_invalid_json():
    """Test nfm_reply with invalid JSON returns None"""
    message = {
        "type": "interactive",
        "interactive": {
            "type": "nfm_reply",
            "nfm_reply": {"response_json": "not valid json{{{"},
        },
    }
    result = _extract_user_message(message, "interactive")
    assert result is None


def test_extract_button_reply():
    """Existing button_reply still works"""
    message = {
        "interactive": {
            "type": "button_reply",
            "button_reply": {"id": "add Idli to cart", "title": "Idli"},
        },
    }
    result = _extract_user_message(message, "interactive")
    assert result == "add Idli to cart"


def test_extract_list_reply():
    """Existing list_reply still works"""
    message = {
        "interactive": {
            "type": "list_reply",
            "list_reply": {"id": "show Breakfast menu", "title": "Breakfast"},
        },
    }
    result = _extract_user_message(message, "interactive")
    assert result == "show Breakfast menu"


# ===================================================================
# TEST FLOW RESPONSE HANDLING
# ===================================================================

@pytest.mark.asyncio
async def test_handle_flow_select_items(mock_send_interactive, mock_send_reply):
    """Test select_items flow response converts to direct_add_to_cart"""
    with patch("app._send_form_response_to_chatbot", new_callable=AsyncMock) as mock_send:
        response_data = {
            "flow_type": "select_items",
            "selected_items": ["Masala Dosa", "Coffee"],
        }
        await _handle_flow_response("1234567890", response_data)

        mock_send.assert_called_once()
        fr = mock_send.call_args[0][1]
        assert fr["form_type"] == "direct_add_to_cart"
        assert len(fr["data"]["items"]) == 2
        assert fr["data"]["items"][0] == {"name": "Masala Dosa", "quantity": 1}
        assert fr["data"]["items"][1] == {"name": "Coffee", "quantity": 1}


@pytest.mark.asyncio
async def test_handle_flow_select_items_empty(mock_send_reply):
    """Test select_items with empty selection"""
    response_data = {"flow_type": "select_items", "selected_items": []}
    await _handle_flow_response("1234567890", response_data)
    assert mock_send_reply.called
    assert "no items" in mock_send_reply.call_args[0][1].lower()


@pytest.mark.asyncio
async def test_handle_flow_manage_cart():
    """Test manage_cart flow response routes updates and removes"""
    _active_flows["1234567890"] = {
        "type": "manage_cart",
        "item_names": ["Dosa", "Coffee", "Biryani"],
        "flow_token": "test_token",
        "ts": 0,
    }

    with patch("app._send_form_response_to_chatbot", new_callable=AsyncMock) as mock_send:
        response_data = {
            "flow_type": "manage_cart",
            "qty_0": "3",   # Dosa -> update to 3
            "qty_1": "0",   # Coffee -> remove
            "qty_2": "1",   # Biryani -> update to 1
        }
        await _handle_flow_response("1234567890", response_data)

        # Should have 3 calls: 1 remove (Coffee) + 2 updates (Dosa, Biryani)
        assert mock_send.call_count == 3

        # First call = remove Coffee (removes processed first)
        remove_call = mock_send.call_args_list[0][0][1]
        assert remove_call["form_type"] == "direct_remove_from_cart"
        assert remove_call["data"]["item_name"] == "Coffee"

        # Second call = update Dosa
        update1 = mock_send.call_args_list[1][0][1]
        assert update1["form_type"] == "direct_update_cart"
        assert update1["data"]["item_name"] == "Dosa"
        assert update1["data"]["quantity"] == 3


@pytest.mark.asyncio
async def test_handle_flow_manage_cart_no_context(mock_send_reply):
    """Test manage_cart with expired/missing flow context"""
    _active_flows.pop("1234567890", None)
    response_data = {"flow_type": "manage_cart", "qty_0": "2"}
    await _handle_flow_response("1234567890", response_data)
    assert mock_send_reply.called
    assert "expired" in mock_send_reply.call_args[0][1].lower()


# ===================================================================
# TEST FLOW-ENABLED MENU (with mocked Flow IDs)
# ===================================================================

@pytest.fixture
def no_flow_ids(monkeypatch):
    """Disable Flow IDs to test fallback behavior"""
    monkeypatch.setattr("app.FLOW_SELECT_ITEMS_ID", "")
    monkeypatch.setattr("app.FLOW_MANAGE_CART_ID", "")


@pytest.fixture
def mock_flow_ids(monkeypatch):
    """Enable Flow IDs for testing"""
    monkeypatch.setattr("app.FLOW_SELECT_ITEMS_ID", "test_flow_select_123")
    monkeypatch.setattr("app.FLOW_MANAGE_CART_ID", "test_flow_cart_456")


@pytest.mark.asyncio
async def test_menu_single_category_sends_flow(mock_send_interactive, mock_flow_ids):
    """Single-category menu with Flow enabled -> sends Item Selection Flow"""
    items = [
        {"name": "Idli", "price": 30, "category": "Breakfast", "is_available_now": True},
        {"name": "Dosa", "price": 50, "category": "Breakfast", "is_available_now": True},
    ]
    agui = {"items": items, "categories": ["Breakfast"], "current_meal_period": "Breakfast"}

    await _convert_menu_data("1234567890", agui)

    payload = mock_send_interactive.call_args[0][1]
    assert payload["type"] == "flow"
    assert payload["action"]["parameters"]["flow_id"] == "test_flow_select_123"
    assert payload["action"]["parameters"]["flow_action"] == "navigate"

    # Verify data payload has items
    data = payload["action"]["parameters"]["flow_action_payload"]["data"]
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == "Idli"


@pytest.mark.asyncio
async def test_menu_multi_category_sends_buttons(mock_send_interactive, mock_send_reply, mock_flow_ids):
    """Multi-category menu with >20 items and Flow -> sends category inline buttons"""
    # Need >20 items across multiple categories to trigger category buttons path
    items = (
        [{"name": f"Breakfast {i}", "price": 30 + i, "category": "Breakfast"} for i in range(8)]
        + [{"name": f"Main {i}", "price": 100 + i, "category": "Main Course"} for i in range(8)]
        + [{"name": f"Drink {i}", "price": 20 + i, "category": "Beverages"} for i in range(8)]
    )
    agui = {"items": items, "categories": ["Breakfast", "Main Course", "Beverages"]}

    await _convert_menu_data("1234567890", agui)

    # Should send text summary + 1 button message with 3 categories
    assert mock_send_reply.called
    assert mock_send_interactive.called
    payload = mock_send_interactive.call_args[0][1]
    assert payload["type"] == "button"
    assert len(payload["action"]["buttons"]) == 3


# ===================================================================
# TEST FLOW-ENABLED CART
# ===================================================================

@pytest.mark.asyncio
async def test_cart_large_sends_flow(mock_send_reply, mock_send_interactive, mock_flow_ids):
    """Large cart with Flow -> sends Cart Management Flow"""
    items = [{"name": f"Item {i}", "quantity": 1, "price": 50} for i in range(5)]
    agui = {"items": items, "total": 250, "packaging_charge_per_item": 30}

    await _convert_cart_data("1234567890", agui)

    # Find flow call among interactive calls
    flow_calls = [c for c in mock_send_interactive.call_args_list if c[0][1].get("type") == "flow"]
    assert len(flow_calls) == 1
    flow_payload = flow_calls[0][0][1]
    assert flow_payload["action"]["parameters"]["flow_id"] == "test_flow_cart_456"

    # Also has checkout buttons
    button_calls = [c for c in mock_send_interactive.call_args_list if c[0][1].get("type") == "button"]
    assert len(button_calls) >= 1


# ===================================================================
# TEST FLOW-ENABLED SEARCH RESULTS (upselling)
# ===================================================================

@pytest.mark.asyncio
async def test_search_large_sends_flow(mock_send_interactive, mock_flow_ids):
    """Large search results with Flow -> sends Item Selection Flow"""
    items = [
        {"name": f"Item {i}", "price": 50, "is_available_now": True, "category": "Food"}
        for i in range(5)
    ]
    agui = {"query": "food", "items": items}

    await _convert_search_results("1234567890", agui)

    payload = mock_send_interactive.call_args[0][1]
    assert payload["type"] == "flow"
    assert payload["action"]["parameters"]["flow_id"] == "test_flow_select_123"


# ===================================================================
# RUN TESTS
# ===================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
