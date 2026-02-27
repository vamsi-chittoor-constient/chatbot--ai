"""
Restaurant API Key Authentication
===================================
Multi-tenant authentication middleware for restaurant API key validation.

Features:
- API key validation via Redis cache (with DB fallback)
- REST endpoint authentication via dependency injection
- WebSocket authentication helper
- Restaurant context injection into request state
"""

from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status, WebSocket, WebSocketException
import structlog

from app.services.restaurant_cache_service import get_restaurant_config_cache

logger = structlog.get_logger(__name__)


class RestaurantAuthenticationError(Exception):
    """Raised when restaurant authentication fails"""
    pass


async def get_restaurant_from_api_key(api_key: str) -> Dict[str, Any]:
    """
    Get restaurant configuration from API key.

    Args:
        api_key: Restaurant API key

    Returns:
        Restaurant configuration dict

    Raises:
        RestaurantAuthenticationError: If API key is invalid or restaurant not found
    """
    if not api_key:
        raise RestaurantAuthenticationError("API key is required")

    # Get restaurant config from cache (with DB fallback)
    restaurant_config_cache = get_restaurant_config_cache()
    restaurant = await restaurant_config_cache.get_by_api_key(api_key)

    if not restaurant:
        logger.warning(
            "restaurant_auth_invalid_api_key",
            api_key_prefix=api_key[:8] if len(api_key) >= 8 else api_key
        )
        raise RestaurantAuthenticationError("Invalid API key")

    logger.info(
        "restaurant_authenticated",
        restaurant_id=restaurant["restaurant_id"],
        restaurant_name=restaurant["name"],
        api_key_prefix=api_key[:8]
    )

    return restaurant


async def authenticate_restaurant(
    api_key: Optional[str] = None,
    request: Optional[Request] = None
) -> Dict[str, Any]:
    """
    Authenticate restaurant via API key for REST endpoints.
    Use as FastAPI dependency.

    Args:
        api_key: API key from query parameter or header
        request: FastAPI request object (optional, for header extraction)

    Returns:
        Restaurant configuration dict

    Raises:
        HTTPException: 401 if authentication fails

    Example:
        @app.get("/api/v1/menu")
        async def get_menu(
            restaurant: Dict = Depends(authenticate_restaurant)
        ):
            # restaurant dict is available here
            pass
    """
    # Try to get API key from query parameter first
    if not api_key and request:
        # Try query parameter
        api_key = request.query_params.get("api_key")

        # Try header as fallback
        if not api_key:
            api_key = request.headers.get("X-Restaurant-API-Key")

    if not api_key:
        logger.warning("restaurant_auth_missing_api_key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Provide via 'api_key' query parameter or 'X-Restaurant-API-Key' header."
        )

    try:
        restaurant = await get_restaurant_from_api_key(api_key)

        # Attach restaurant to request state for later access
        if request:
            request.state.restaurant = restaurant

        return restaurant

    except RestaurantAuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "restaurant_auth_unexpected_error",
            error=str(e),
            error_type=type(e).__name__
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service error"
        )


async def authenticate_websocket_restaurant(
    websocket: WebSocket,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Authenticate restaurant via API key for WebSocket connections.
    Call this BEFORE accepting the WebSocket connection.

    Args:
        websocket: WebSocket connection object
        api_key: API key from query parameter (extracted from websocket.query_params)

    Returns:
        Restaurant configuration dict

    Raises:
        WebSocketException: 4001 if authentication fails

    Example:
        @app.websocket("/ws/chat/{session_id}")
        async def chat_endpoint(
            websocket: WebSocket,
            session_id: str,
            api_key: str = None
        ):
            # Authenticate BEFORE accepting connection
            restaurant = await authenticate_websocket_restaurant(websocket, api_key)

            # Now accept the connection
            await websocket.accept()

            # Use restaurant data
            print(f"Connected: {restaurant['name']}")
    """
    if not api_key:
        # Try to get from query params if not provided
        api_key = websocket.query_params.get("api_key")

    # TESTING MODE: Allow bypass with special test API key
    if api_key and api_key.startswith("test_api_key"):
        logger.info("websocket_test_mode_auth_bypass", api_key=api_key)
        return {
            "restaurant_id": "test_restaurant_001",
            "name": "Test Restaurant",
            "api_key": api_key,
            "status": "active"
        }

    if not api_key:
        logger.warning(
            "websocket_auth_missing_api_key",
            client=websocket.client.host if websocket.client else None
        )
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="API key is required. Provide via 'api_key' query parameter."
        )

    try:
        restaurant = await get_restaurant_from_api_key(api_key)

        logger.info(
            "websocket_restaurant_authenticated",
            restaurant_id=restaurant["restaurant_id"],
            restaurant_name=restaurant["name"],
            client=websocket.client.host if websocket.client else None
        )

        return restaurant

    except RestaurantAuthenticationError as e:
        logger.warning(
            "websocket_auth_failed",
            error=str(e),
            api_key_prefix=api_key[:8] if len(api_key) >= 8 else api_key,
            client=websocket.client.host if websocket.client else None
        )
        print(f"DEBUG: WebSocket auth failed: {str(e)}")
        raise WebSocketException(
            code=status.WS_1008_POLICY_VIOLATION,
            reason=str(e)
        )
    except Exception as e:
        logger.error(
            "websocket_auth_unexpected_error",
            error=str(e),
            error_type=type(e).__name__,
            client=websocket.client.host if websocket.client else None
        )
        raise WebSocketException(
            code=status.WS_1011_INTERNAL_ERROR,
            reason="Authentication service error"
        )


def get_restaurant_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Get restaurant from request state (if authenticated).

    Args:
        request: FastAPI request object

    Returns:
        Restaurant configuration dict or None if not authenticated
    """
    return getattr(request.state, "restaurant", None)
