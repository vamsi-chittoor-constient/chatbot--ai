"""
Initialize Database Tables
===========================
Creates all required tables in the database.

IMPORTANT: All models must be imported before create_all_tables() is called
so SQLAlchemy knows about them and can resolve foreign key dependencies.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database import db_manager
import structlog

logger = structlog.get_logger("scripts.init_database")

# =============================================================================
# IMPORT ALL MODELS - Required for SQLAlchemy to know about them
# =============================================================================
# Models must be imported BEFORE create_all_tables() is called so they are
# registered with SQLAlchemy's Base metadata and foreign keys resolve correctly.

# 1. Food Ordering Models (Menu, Orders, Payments) - IMPORT FIRST
# These are referenced by user models (UserFavorite -> menu_items)
from app.features.food_ordering.models import (
    # Lookup Tables
    MealType,
    MealSlotTiming,
    Cuisine,
    Allergen,
    DietaryType,
    # Menu Hierarchy
    MenuSection,
    MenuCategory,
    MenuSubCategory,
    # Core Menu
    MenuItem,
    # Menu Mappings
    MenuItemCategoryMapping,
    MenuItemCuisineMapping,
    MenuItemAvailabilitySchedule,
    MenuItemIngredient,
    MenuItemAllergenMapping,
    MenuItemDietaryMapping,
    MenuItemEnrichedView,
    # Order Lookup Tables
    OrderType,
    OrderSourceType,
    OrderStatusType,
    # Core Order Tables
    Order,
    OrderItem,
    OrderTotal,
    OrderStatusHistory,
    AbandonedCart,
    # Payment Tables
    PaymentGateway,
    PaymentStatusType,
    PaymentOrder,
    PaymentTransaction,
    PaymentRefund,
)

# 2. Shared Models (Users, Auth, Restaurant, Communication, System)
from app.shared.models import (
    # User models
    User,
    UserPreferences,
    UserDevice,
    SessionToken,
    UserFavorite,
    UserBrowsingHistory,
    # Auth models
    OTPVerification,
    AuthSession,
    OTPRateLimit,
    # Restaurant models
    Restaurant,
    Table,
    # Communication models
    Session,
    Conversation,
    Message,
    MessageTemplate,
    MessageLog,
    EmailLog,
    # System models
    AgentMemory,
    SystemLog,
    KnowledgeBase,
    FAQ,
    RestaurantPolicy,
    QueryAnalytics,
    APIKeyUsage,
)

# 3. Booking Models
from app.features.booking.models import (
    Booking,
    Waitlist,
    AbandonedBooking,
)

# 4. Feedback Models
from app.features.feedback.models import (
    Complaint,
    Rating,
    Feedback,
    CustomerFeedbackDetails,
    SatisfactionMetrics,
    ComplaintResolutionTemplate,
)

logger.info("All models imported successfully")


async def init_database():
    """Initialize database and create all tables."""
    logger.info("Initializing database connection")

    # Initialize database connection
    db_manager.init_database()

    logger.info("Creating all database tables")

    # Create all tables
    await db_manager.create_all_tables()

    logger.info("Database initialization completed successfully")
    print("\n✅ Database tables created successfully!")
    print("📋 You can now:")
    print("   1. Populate menu items")
    print("   2. Index menu to vector database: python scripts/index_menu_to_vector_db.py")
    print("   3. Run tests: python scripts/test_chatbot_realtime.py")


if __name__ == "__main__":
    asyncio.run(init_database())
