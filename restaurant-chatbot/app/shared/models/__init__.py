"""
Shared Database Models
=====================

This package contains all SQLAlchemy models organized by feature.
All models are re-exported here for convenient importing.

Usage:
    from app.shared.models import User, MenuItem, Order
"""

# Base imports
from app.shared.models.base import (
    Base,
    UserStatus,
    BookingStatus,
    OrderStatus,
    PaymentStatus,
    MessageDirection,
    MessageChannel,
    ComplaintStatus
)

# User models
from app.shared.models.user import User, UserPreferences, UserDevice, SessionToken, UserFavorite, UserBrowsingHistory

# Auth models
from app.shared.models.auth import OTPVerification, AuthSession, OTPRateLimit

# Menu models (moved to app.features.food_ordering.models but re-exported for SQLAlchemy relationships)
# from app.features.food_ordering.models import (
#     MenuItem,
#     MenuSection,
#     MenuCategory,
#     MenuSubCategory,
#     MealType,
#     Cuisine,
#     Allergen,
#     DietaryType,
#     MenuItemCategoryMapping,
#     MenuItemCuisineMapping,
#     MenuItemAvailabilitySchedule,
#     MenuItemIngredient,
#     MenuItemAllergenMapping,
#     MenuItemDietaryMapping,
#     MenuItemEnrichedView
# )

# Restaurant models
from app.shared.models.restaurant import Restaurant, Table

# Booking models (moved to app.features.booking.models but re-exported for SQLAlchemy relationships)
# from app.features.booking.models import Booking, Waitlist, AbandonedBooking

# Order models (moved to app.features.food_ordering.models but re-exported for SQLAlchemy relationships)
# from app.features.food_ordering.models import Order, OrderItem, AbandonedCart

# Payment models (moved to app.features.food_ordering.models)
# from app.features.food_ordering.models import PaymentOrder, PaymentTransaction, PaymentRefund, PaymentGateway, PaymentStatusType
# Legacy payment models (kept for backward compatibility)
# from app.shared.models.payment import Payment, WebhookEvent, PaymentRetryAttempt

# Feedback models (moved to app.features.feedback.models but re-exported for SQLAlchemy relationships)
# from app.features.feedback.models import Complaint, Rating, Feedback, CustomerFeedbackDetails, SatisfactionMetrics, ComplaintResolutionTemplate

# Communication models
from app.shared.models.communication import Session, Conversation, Message, MessageTemplate, MessageLog, EmailLog

# System models
from app.shared.models.system import AgentMemory, SystemLog, KnowledgeBase, FAQ, RestaurantPolicy, QueryAnalytics, APIKeyUsage

__all__ = [
    # Enums
    "UserStatus",
    "BookingStatus",
    "OrderStatus",
    "PaymentStatus",
    "MessageDirection",
    "MessageChannel",
    "ComplaintStatus",

    # User models
    "User",
    "UserPreferences",
    "UserDevice",
    "SessionToken",
    "UserFavorite",
    "UserBrowsingHistory",

    # Auth models
    "OTPVerification",
    "AuthSession",
    "OTPRateLimit",

    # Menu models
    # "MenuItem",
    # "MenuSection",
    # "MenuCategory",
    # "MenuSubCategory",
    # "MealType",
    # "Cuisine",
    # "Allergen",
    # "DietaryType",
    # "MenuItemCategoryMapping",
    # "MenuItemCuisineMapping",
    # "MenuItemAvailabilitySchedule",
    # "MenuItemIngredient",
    # "MenuItemAllergenMapping",
    # "MenuItemDietaryMapping",
    # "MenuItemEnrichedView",

    # Restaurant models
    "Restaurant",
    "Table",

    # Booking models
    # "Booking",
    # "Waitlist",
    # "AbandonedBooking",

    # Order models
    # "Order",
    # "OrderItem",
    # "AbandonedCart",

    # Payment models (from food_ordering)
    # "PaymentOrder",
    # "PaymentTransaction",
    # "PaymentRefund",
    # "PaymentGateway",
    # "PaymentStatusType",
    # Legacy payment models
    # "Payment",
    # "WebhookEvent",
    # "PaymentRetryAttempt",

    # Feedback models
    # "Complaint",
    # "Rating",
    # "Feedback",
    # "CustomerFeedbackDetails",
    # "SatisfactionMetrics",
    # "ComplaintResolutionTemplate",

    # Communication models
    "Session",
    "Conversation",
    "Message",
    "MessageTemplate",
    "MessageLog",
    "EmailLog",

    # System models
    "AgentMemory",
    "SystemLog",
    "KnowledgeBase",
    "FAQ",
    "RestaurantPolicy",
    "QueryAnalytics",
    "APIKeyUsage",

]