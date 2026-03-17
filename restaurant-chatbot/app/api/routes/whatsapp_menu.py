"""
WhatsApp Menu API — serves menu data and processes cart submissions
from the mobile-optimized menu web page opened via WhatsApp CTA URL.

Flow:
1. WhatsApp bridge generates a token via POST /api/v1/menu/token
2. User opens /menu/{token} in WhatsApp's in-app browser
3. React page fetches GET /api/v1/menu/whatsapp/{token}
4. User selects items, submits via POST /api/v1/cart/whatsapp
5. This endpoint calls the WhatsApp bridge to push cart to the chatbot
"""

import os
import uuid
import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
logger = logging.getLogger(__name__)

# WhatsApp bridge internal URL (Docker service name)
WHATSAPP_BRIDGE_URL = os.getenv("WHATSAPP_BRIDGE_URL", "http://whatsapp-bridge:8002")

# Redis for token storage
_redis_client = None


def _get_redis():
    """Get sync Redis client (lazy init)."""
    global _redis_client
    if _redis_client is None:
        from app.core.redis import get_sync_redis_client
        _redis_client = get_sync_redis_client()
    return _redis_client


# ── Token management ──

def generate_menu_token(phone: str) -> str:
    """Create a short-lived token mapping to a phone number. Stored in Redis with 30min TTL."""
    token = uuid.uuid4().hex
    redis = _get_redis()
    redis.set(f"menu_token:{token}", phone, ex=1800)  # 30 min
    logger.info(f"Generated menu token for {phone}: {token[:8]}...")
    return token


def resolve_menu_token(token: str) -> Optional[str]:
    """Resolve a token to a phone number. Returns None if expired/invalid."""
    redis = _get_redis()
    phone = redis.get(f"menu_token:{token}")
    return phone


# ── Request/Response models ──

class TokenRequest(BaseModel):
    phone: str


class TokenResponse(BaseModel):
    token: str


class CartItem(BaseModel):
    name: str
    quantity: int
    price: float = 0


class CartSubmitRequest(BaseModel):
    token: str
    items: List[CartItem]


# ── Endpoints ──

@router.post("/menu/token", response_model=TokenResponse)
async def create_menu_token(req: TokenRequest):
    """Generate a menu browsing token for a WhatsApp phone number."""
    token = generate_menu_token(req.phone)
    return TokenResponse(token=token)


@router.get("/menu/whatsapp/{token}")
async def get_whatsapp_menu(token: str):
    """Fetch menu items for the WhatsApp menu page. Token must be valid."""
    phone = resolve_menu_token(token)
    if not phone:
        raise HTTPException(status_code=404, detail="Menu session expired. Please request the menu again from WhatsApp.")

    from app.core.preloader import get_menu_preloader
    preloader = get_menu_preloader()
    items = preloader.search()  # All available items

    if not items:
        raise HTTPException(status_code=404, detail="Menu is currently unavailable.")

    # Group by category for the frontend
    categories = []
    seen = set()
    for item in items:
        cat = item.get("category", "Other")
        if cat not in seen:
            categories.append(cat)
            seen.add(cat)

    return {
        "items": items,
        "categories": categories,
        "phone": phone[-4:],  # Last 4 digits only (privacy)
    }


@router.post("/cart/whatsapp")
async def submit_whatsapp_cart(req: CartSubmitRequest):
    """
    Receive cart selections from the WhatsApp menu page.
    Forwards to the WhatsApp bridge which pushes it through the chatbot WebSocket.
    """
    phone = resolve_menu_token(req.token)
    if not phone:
        raise HTTPException(status_code=401, detail="Session expired. Please request the menu again from WhatsApp.")

    if not req.items:
        raise HTTPException(status_code=400, detail="No items selected.")

    # Invalidate token (one-time use for cart submission)
    redis = _get_redis()
    redis.delete(f"menu_token:{req.token}")

    # Call WhatsApp bridge internal endpoint to add items to cart
    items_payload = [{"name": it.name, "quantity": it.quantity, "price": it.price} for it in req.items]

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{WHATSAPP_BRIDGE_URL}/internal/add-to-cart",
                json={"phone": phone, "items": items_payload},
            )
            if resp.status_code != 200:
                logger.error(f"Bridge add-to-cart failed: {resp.status_code} {resp.text}")
                raise HTTPException(status_code=502, detail="Failed to add items to cart.")
    except httpx.ConnectError:
        logger.error("Cannot connect to WhatsApp bridge")
        raise HTTPException(status_code=502, detail="WhatsApp bridge unavailable.")

    return {"success": True, "message": "Items added to cart! You can close this page and return to WhatsApp."}
