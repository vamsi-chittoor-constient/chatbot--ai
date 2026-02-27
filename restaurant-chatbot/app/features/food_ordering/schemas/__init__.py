"""
Food Ordering Feature Schemas
==============================
Pydantic schemas for food ordering menu and order management.
"""

# Menu schemas
from app.features.food_ordering.schemas.menu import (
    # Category Request Models
    MenuCategoryCreateRequest,
    MenuCategoryUpdateRequest,
    MenuCategorySearchRequest,

    # Menu Item Request Models
    MenuItemCreateRequest,
    MenuItemUpdateRequest,
    MenuItemSearchRequest,

    # Category Response Models
    MenuCategoryResponse,
    MenuCategoryListResponse,
    MenuCategoryCreateResponse,
    MenuCategoryUpdateResponse,

    # Menu Item Response Models
    MenuItemResponse,
    MenuItemSummaryResponse,
    MenuItemListResponse,
    MenuItemSummaryListResponse,
    MenuItemCreateResponse,
    MenuItemUpdateResponse,

    # LLM Agent Schemas
    MenuCategoryForLLM,
    MenuItemForLLM,

    # Statistics & Bulk Operations
    MenuStatsResponse,
    MenuBulkUpdateResponse,
    FullMenuResponse,
)

# Order schemas
from app.features.food_ordering.schemas.order import (
    # Order Item Request Models
    OrderItemAddRequest,
    OrderItemUpdateRequest,

    # Order Request Models
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    OrderSearchRequest,

    # Order Item Response Models
    OrderItemResponse,

    # Order Response Models
    OrderResponse,
    OrderSummaryResponse,
    OrderCalculationResponse,
    OrderListResponse,
    OrderSummaryListResponse,
    OrderHistoryResponse,

    # Payment Response
    PaymentResponse,

    # Action Responses
    OrderCreateResponse,
    OrderUpdateResponse,
    OrderItemAddResponse,
    OrderItemUpdateResponse,

    # Statistics & History
    OrderStatusHistoryResponse,
    OrderStatsResponse,
)

__all__ = [
    # Menu Category Request Models
    "MenuCategoryCreateRequest",
    "MenuCategoryUpdateRequest",
    "MenuCategorySearchRequest",

    # Menu Item Request Models
    "MenuItemCreateRequest",
    "MenuItemUpdateRequest",
    "MenuItemSearchRequest",

    # Category Response Models
    "MenuCategoryResponse",
    "MenuCategoryListResponse",
    "MenuCategoryCreateResponse",
    "MenuCategoryUpdateResponse",

    # Menu Item Response Models
    "MenuItemResponse",
    "MenuItemSummaryResponse",
    "MenuItemListResponse",
    "MenuItemSummaryListResponse",
    "MenuItemCreateResponse",
    "MenuItemUpdateResponse",

    # LLM Agent Schemas
    "MenuCategoryForLLM",
    "MenuItemForLLM",

    # Menu Statistics
    "MenuStatsResponse",
    "MenuBulkUpdateResponse",
    "FullMenuResponse",

    # Order Item Request Models
    "OrderItemAddRequest",
    "OrderItemUpdateRequest",

    # Order Request Models
    "OrderCreateRequest",
    "OrderStatusUpdateRequest",
    "OrderSearchRequest",

    # Order Item Response Models
    "OrderItemResponse",

    # Order Response Models
    "OrderResponse",
    "OrderSummaryResponse",
    "OrderCalculationResponse",
    "OrderListResponse",
    "OrderSummaryListResponse",
    "OrderHistoryResponse",

    # Payment Response
    "PaymentResponse",

    # Order Action Responses
    "OrderCreateResponse",
    "OrderUpdateResponse",
    "OrderItemAddResponse",
    "OrderItemUpdateResponse",

    # Order Statistics
    "OrderStatusHistoryResponse",
    "OrderStatsResponse",
]
