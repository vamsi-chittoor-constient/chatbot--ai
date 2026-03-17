"""
WhatsApp Web Pages API — serves data for mobile-optimized web pages
opened via WhatsApp CTA URL buttons. Replaces complex AGUI→WhatsApp
conversions with full web UI capability.

Pages:
- /menu/{token}    → Browse full menu, select items + qty, add to cart
- /cart/{token}    → View/edit cart, change quantities, checkout
- /search/{token}  → Search results with add-to-cart
- /order/{token}   → Order details and tracking

Flow:
1. WhatsApp bridge stores page data in Redis via POST /api/v1/wa/token
2. User taps CTA button → opens web page in WhatsApp's in-app browser
3. React page fetches GET /api/v1/wa/page/{token}
4. User interacts, submits via POST /api/v1/wa/action
5. Backend calls WhatsApp bridge to push result to chatbot
"""

import os
import uuid
import json
import logging
from typing import List, Optional, Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

WHATSAPP_BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://whatsapp-bridge:8002")

_redis_client = None


def _get_redis():
    global _redis_client
    if _redis_client is None:
        from app.core.redis import get_sync_redis_client
        _redis_client = get_sync_redis_client()
    return _redis_client


# ── Token management ──

def create_page_token(phone: str, page_type: str, data: dict = None) -> str:
    """Create a token that stores phone + page type + optional data. 30min TTL."""
    token = uuid.uuid4().hex
    redis = _get_redis()
    payload = json.dumps({"phone": phone, "page_type": page_type, "data": data or {}})
    redis.set(f"wa_page:{token}", payload, ex=1800)
    logger.info(f"Created {page_type} token for {phone}: {token[:8]}...")
    return token


def resolve_page_token(token: str) -> Optional[dict]:
    """Resolve token → {phone, page_type, data}. Returns None if expired."""
    redis = _get_redis()
    raw = redis.get(f"wa_page:{token}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


# ── Request/Response models ──

class TokenRequest(BaseModel):
    phone: str
    page_type: str  # menu, cart, search, order
    data: Dict[str, Any] = {}


class TokenResponse(BaseModel):
    token: str


class ActionRequest(BaseModel):
    token: str
    action: str  # add_to_cart, update_cart, checkout, etc.
    data: Dict[str, Any] = {}


# ── Endpoints ──

@router.post("/wa/token", response_model=TokenResponse)
async def create_token(req: TokenRequest):
    """Generate a page token. Called by WhatsApp bridge before sending CTA URL."""
    token = create_page_token(req.phone, req.page_type, req.data)
    return TokenResponse(token=token)


@router.get("/wa/page/{token}")
async def get_page_data(token: str):
    """Fetch page data for a WhatsApp web page. Token must be valid."""
    info = resolve_page_token(token)
    if not info:
        raise HTTPException(status_code=404, detail="Session expired. Please request this again from WhatsApp.")

    phone = info["phone"]
    page_type = info["page_type"]
    stored_data = info.get("data", {})

    # WhatsApp bot number for deeplink back to chat
    wa_number = os.getenv("WHATSAPP_PHONE_NUMBER", "")

    if page_type == "menu":
        result = await _get_menu_data(phone, stored_data)
    elif page_type == "cart":
        result = _get_cart_data(stored_data)
    elif page_type == "search":
        result = _get_search_data(stored_data)
    elif page_type == "order":
        result = _get_order_data(stored_data)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown page type: {page_type}")

    # Inject WhatsApp deeplink for "Return to WhatsApp" button
    if wa_number:
        result["wa_deeplink"] = f"https://wa.me/{wa_number}"

    return result


@router.post("/wa/action")
async def perform_action(req: ActionRequest):
    """Handle user actions from WhatsApp web pages (add to cart, checkout, etc.)."""
    info = resolve_page_token(req.token)
    if not info:
        raise HTTPException(status_code=401, detail="Session expired. Please go back to WhatsApp and try again.")

    phone = info["phone"]

    # Build the appropriate message/form_response for the bridge
    bridge_payload = {"phone": phone}

    if req.action == "add_to_cart":
        items = req.data.get("items", [])
        if not items:
            raise HTTPException(status_code=400, detail="No items selected.")
        bridge_payload["items"] = items
        bridge_payload["action"] = "add_to_cart"

    elif req.action == "update_cart":
        bridge_payload["updates"] = req.data.get("updates", [])
        bridge_payload["removes"] = req.data.get("removes", [])
        bridge_payload["action"] = "update_cart"

    elif req.action == "checkout":
        bridge_payload["action"] = "checkout"

    elif req.action == "add_more":
        bridge_payload["action"] = "add_more"

    else:
        # Generic message passthrough
        bridge_payload["action"] = "message"
        bridge_payload["message"] = req.data.get("message", req.action)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{WHATSAPP_BRIDGE_URL}/internal/wa-action",
                json=bridge_payload,
            )
            if resp.status_code != 200:
                logger.error(f"Bridge action failed: {resp.status_code} {resp.text}")
                raise HTTPException(status_code=502, detail="Failed to process action.")
            return resp.json()
    except httpx.ConnectError:
        logger.error("Cannot connect to WhatsApp bridge")
        raise HTTPException(status_code=502, detail="Service unavailable.")


# ── Page data builders ──

async def _get_menu_data(phone: str, stored_data: dict) -> dict:
    """Build menu page data from the preloaded menu cache."""
    from app.core.preloader import get_menu_preloader
    preloader = get_menu_preloader()
    items = preloader.search()

    if not items:
        raise HTTPException(status_code=404, detail="Menu is currently unavailable.")

    categories = []
    seen = set()
    for item in items:
        cat = item.get("category", "Other")
        if cat not in seen:
            categories.append(cat)
            seen.add(cat)

    return {
        "page_type": "menu",
        "items": items,
        "categories": categories,
        "phone_last4": phone[-4:],
    }


def _get_cart_data(stored_data: dict) -> dict:
    """Return cart data that was stored in the token."""
    return {
        "page_type": "cart",
        "items": stored_data.get("items", []),
        "total": stored_data.get("total", 0),
        "packaging_charge": stored_data.get("packaging_charge_per_item", 30),
    }


def _get_search_data(stored_data: dict) -> dict:
    """Return search results that were stored in the token."""
    return {
        "page_type": "search",
        "query": stored_data.get("query", ""),
        "items": stored_data.get("items", []),
        "current_meal_period": stored_data.get("current_meal_period", ""),
    }


def _get_order_data(stored_data: dict) -> dict:
    """Return order data that was stored in the token."""
    return {
        "page_type": "order",
        "order_id": stored_data.get("order_id", ""),
        "items": stored_data.get("items", []),
        "total": stored_data.get("total", 0),
        "status": stored_data.get("status", ""),
        "order_type": stored_data.get("order_type", ""),
    }


# ── Legacy endpoints (backward compatibility) ──

@router.post("/menu/token", response_model=TokenResponse)
async def create_menu_token_legacy(req: TokenRequest):
    """Legacy: Generate menu token. Redirects to new unified token system."""
    token = create_page_token(req.phone, "menu")
    return TokenResponse(token=token)
