"""
Food Ordering Models
====================

Menu, Order, and Payment database models for AI-powered conversational food ordering.
"""

# ============================================================================
# MENU MODELS
# ============================================================================

# Lookup Tables (5)
from app.features.food_ordering.models.meal_type import MealType
from app.features.food_ordering.models.meal_slot_timing import MealSlotTiming
from app.features.food_ordering.models.cuisine import Cuisine
from app.features.food_ordering.models.allergen import Allergen
from app.features.food_ordering.models.dietary_type import DietaryType

# Menu Hierarchy Tables (3)
from app.features.food_ordering.models.menu_section import MenuSection
from app.features.food_ordering.models.menu_category import MenuCategory
from app.features.food_ordering.models.menu_sub_category import MenuSubCategory

# Core Menu Tables (1)
from app.features.food_ordering.models.menu_item import MenuItem

# Mapping Tables (6)
from app.features.food_ordering.models.menu_item_category_mapping import MenuItemCategoryMapping
from app.features.food_ordering.models.menu_item_cuisine_mapping import MenuItemCuisineMapping
from app.features.food_ordering.models.menu_item_availability_schedule import MenuItemAvailabilitySchedule
from app.features.food_ordering.models.menu_item_ingredient import MenuItemIngredient
from app.features.food_ordering.models.menu_item_allergen_mapping import MenuItemAllergenMapping
from app.features.food_ordering.models.menu_item_dietary_mapping import MenuItemDietaryMapping

# Views (1)
from app.features.food_ordering.models.menu_item_enriched_view import MenuItemEnrichedView

# ============================================================================
# ORDER MODELS
# ============================================================================

# Order Lookup Tables (3)
from app.features.food_ordering.models.order_type import OrderType
from app.features.food_ordering.models.order_source_type import OrderSourceType
from app.features.food_ordering.models.order_status_type import OrderStatusType

# Core Order Tables (3)
from app.features.food_ordering.models.order import Order
from app.features.food_ordering.models.order_item import OrderItem
from app.features.food_ordering.models.order_total import OrderTotal

# Order Detail Tables (1)
from app.features.food_ordering.models.order_status_history import OrderStatusHistory

# Cart Tables (1)
from app.features.food_ordering.models.abandoned_cart import AbandonedCart

# ============================================================================
# PAYMENT MODELS
# ============================================================================

# Payment Lookup Tables (2)
from app.features.food_ordering.models.payment_gateway import PaymentGateway
from app.features.food_ordering.models.payment_status_type import PaymentStatusType

# Core Payment Tables (3)
from app.features.food_ordering.models.payment_order import PaymentOrder
from app.features.food_ordering.models.payment_transaction import PaymentTransaction
from app.features.food_ordering.models.payment_refund import PaymentRefund


__all__ = [
    # ========================================================================
    # MENU MODELS
    # ========================================================================
    # Lookup Tables (5)
    "MealType",
    "MealSlotTiming",
    "Cuisine",
    "Allergen",
    "DietaryType",
    # Menu Hierarchy Tables (3)
    "MenuSection",
    "MenuCategory",
    "MenuSubCategory",
    # Core Menu Tables (1)
    "MenuItem",
    # Mapping Tables (6)
    "MenuItemCategoryMapping",
    "MenuItemCuisineMapping",
    "MenuItemAvailabilitySchedule",
    "MenuItemIngredient",
    "MenuItemAllergenMapping",
    "MenuItemDietaryMapping",
    # Views (1)
    "MenuItemEnrichedView",

    # ========================================================================
    # ORDER MODELS
    # ========================================================================
    # Order Lookup Tables (3)
    "OrderType",
    "OrderSourceType",
    "OrderStatusType",
    # Core Order Tables (3)
    "Order",
    "OrderItem",
    "OrderTotal",
    # Order Detail Tables (1)
    "OrderStatusHistory",
    # Cart Tables (1)
    "AbandonedCart",

    # ========================================================================
    # PAYMENT MODELS
    # ========================================================================
    # Payment Lookup Tables (2)
    "PaymentGateway",
    "PaymentStatusType",
    # Core Payment Tables (3)
    "PaymentOrder",
    "PaymentTransaction",
    "PaymentRefund",
]
