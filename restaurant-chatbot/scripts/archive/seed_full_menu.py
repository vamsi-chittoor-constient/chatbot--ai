"""
Full Menu Seeder with Meal Types
================================
Seeds a comprehensive menu with 40+ items, categories, and meal type assignments.
"""
import asyncio
from uuid import uuid4
from decimal import Decimal

# ============================================================================
# MEAL TYPES
# ============================================================================
MEAL_TYPES = [
    {"name": "Breakfast", "order": 1},
    {"name": "Lunch", "order": 2},
    {"name": "Dinner", "order": 3},
    {"name": "All Day", "order": 4},
]

# ============================================================================
# CATEGORIES
# ============================================================================
CATEGORIES = [
    {"name": "Breakfast", "description": "Start your day right"},
    {"name": "Starters", "description": "Appetizers and small bites"},
    {"name": "Pizza", "description": "Wood-fired pizzas"},
    {"name": "Burgers", "description": "Gourmet burgers"},
    {"name": "Pasta", "description": "Italian classics"},
    {"name": "Main Course", "description": "Hearty mains"},
    {"name": "Salads", "description": "Fresh and healthy"},
    {"name": "Desserts", "description": "Sweet endings"},
    {"name": "Beverages", "description": "Hot and cold drinks"},
    {"name": "Snacks", "description": "Light bites"},
]

# ============================================================================
# MENU ITEMS (40+ items with meal type assignments)
# ============================================================================
MENU_ITEMS = [
    # === BREAKFAST ITEMS (Breakfast only) ===
    {"name": "Classic Eggs Benedict", "category": "Breakfast", "price": 249, "meal_type": "Breakfast",
     "description": "Poached eggs on English muffin with hollandaise sauce", "is_recommended": True},
    {"name": "Masala Omelette", "category": "Breakfast", "price": 149, "meal_type": "Breakfast",
     "description": "Fluffy omelette with onions, tomatoes, and green chilies"},
    {"name": "Pancake Stack", "category": "Breakfast", "price": 199, "meal_type": "Breakfast",
     "description": "Fluffy pancakes with maple syrup and butter", "is_recommended": True},
    {"name": "Avocado Toast", "category": "Breakfast", "price": 229, "meal_type": "Breakfast",
     "description": "Smashed avocado on sourdough with poached egg"},
    {"name": "French Toast", "category": "Breakfast", "price": 179, "meal_type": "Breakfast",
     "description": "Classic french toast with cinnamon and honey"},
    {"name": "Breakfast Burrito", "category": "Breakfast", "price": 219, "meal_type": "Breakfast",
     "description": "Scrambled eggs, beans, cheese, and salsa in a tortilla"},

    # === STARTERS (Lunch & Dinner) ===
    {"name": "Crispy Chicken Wings", "category": "Starters", "price": 299, "meal_type": "Lunch",
     "description": "Spicy buffalo wings with blue cheese dip", "is_recommended": True},
    {"name": "Paneer Tikka", "category": "Starters", "price": 279, "meal_type": "Dinner",
     "description": "Marinated cottage cheese grilled to perfection"},
    {"name": "Spring Rolls", "category": "Starters", "price": 199, "meal_type": "All Day",
     "description": "Crispy vegetable spring rolls with sweet chili sauce"},
    {"name": "Garlic Bread", "category": "Starters", "price": 149, "meal_type": "All Day",
     "description": "Toasted bread with garlic butter and herbs"},
    {"name": "Soup of the Day", "category": "Starters", "price": 129, "meal_type": "All Day",
     "description": "Chef's special soup - ask your server"},

    # === PIZZA (Lunch & Dinner) ===
    {"name": "Margherita Pizza", "category": "Pizza", "price": 299, "meal_type": "All Day",
     "description": "Classic tomato, mozzarella, and fresh basil", "is_recommended": True},
    {"name": "Pepperoni Pizza", "category": "Pizza", "price": 349, "meal_type": "Dinner",
     "description": "Loaded with spicy pepperoni and cheese"},
    {"name": "BBQ Chicken Pizza", "category": "Pizza", "price": 379, "meal_type": "Dinner",
     "description": "Grilled chicken with BBQ sauce and onions", "is_recommended": True},
    {"name": "Veggie Supreme Pizza", "category": "Pizza", "price": 329, "meal_type": "Lunch",
     "description": "Bell peppers, mushrooms, olives, and onions"},
    {"name": "Four Cheese Pizza", "category": "Pizza", "price": 359, "meal_type": "Dinner",
     "description": "Mozzarella, cheddar, parmesan, and gorgonzola"},

    # === BURGERS (Lunch & Dinner) ===
    {"name": "Classic Chicken Burger", "category": "Burgers", "price": 229, "meal_type": "Lunch",
     "description": "Grilled chicken patty with lettuce and mayo", "is_recommended": True},
    {"name": "Beef Burger Deluxe", "category": "Burgers", "price": 299, "meal_type": "Dinner",
     "description": "Juicy beef patty with cheese, bacon, and special sauce"},
    {"name": "Veggie Burger", "category": "Burgers", "price": 199, "meal_type": "Lunch",
     "description": "Crispy vegetable patty with fresh toppings"},
    {"name": "Spicy Lamb Burger", "category": "Burgers", "price": 329, "meal_type": "Dinner",
     "description": "Tender lamb patty with mint chutney"},
    {"name": "Fish Burger", "category": "Burgers", "price": 279, "meal_type": "Lunch",
     "description": "Crispy fish fillet with tartar sauce"},

    # === PASTA (Lunch & Dinner) ===
    {"name": "Spaghetti Carbonara", "category": "Pasta", "price": 299, "meal_type": "Dinner",
     "description": "Creamy bacon pasta with parmesan", "is_recommended": True},
    {"name": "Penne Arrabbiata", "category": "Pasta", "price": 249, "meal_type": "Lunch",
     "description": "Spicy tomato sauce with garlic and chilies"},
    {"name": "Fettuccine Alfredo", "category": "Pasta", "price": 279, "meal_type": "Dinner",
     "description": "Rich creamy parmesan sauce"},
    {"name": "Lasagna", "category": "Pasta", "price": 349, "meal_type": "Dinner",
     "description": "Layered pasta with meat sauce and cheese", "is_recommended": True},
    {"name": "Mushroom Risotto", "category": "Pasta", "price": 319, "meal_type": "Dinner",
     "description": "Creamy arborio rice with wild mushrooms"},

    # === MAIN COURSE (Dinner focused) ===
    {"name": "Grilled Salmon", "category": "Main Course", "price": 549, "meal_type": "Dinner",
     "description": "Atlantic salmon with lemon butter sauce", "is_recommended": True},
    {"name": "Butter Chicken", "category": "Main Course", "price": 349, "meal_type": "Dinner",
     "description": "Creamy tomato-based chicken curry"},
    {"name": "Lamb Chops", "category": "Main Course", "price": 599, "meal_type": "Dinner",
     "description": "Herb-crusted lamb chops with mint sauce"},
    {"name": "Chicken Tikka Masala", "category": "Main Course", "price": 329, "meal_type": "Dinner",
     "description": "Grilled chicken in spiced tomato gravy"},
    {"name": "Vegetable Biryani", "category": "Main Course", "price": 279, "meal_type": "Lunch",
     "description": "Fragrant basmati rice with mixed vegetables"},

    # === SALADS (All Day) ===
    {"name": "Caesar Salad", "category": "Salads", "price": 199, "meal_type": "All Day",
     "description": "Romaine lettuce with caesar dressing and croutons", "is_recommended": True},
    {"name": "Greek Salad", "category": "Salads", "price": 219, "meal_type": "All Day",
     "description": "Feta cheese, olives, tomatoes, and cucumber"},
    {"name": "Garden Fresh Salad", "category": "Salads", "price": 179, "meal_type": "Lunch",
     "description": "Mixed greens with seasonal vegetables"},
    {"name": "Grilled Chicken Salad", "category": "Salads", "price": 279, "meal_type": "Lunch",
     "description": "Grilled chicken strips on fresh greens"},

    # === DESSERTS (All Day) ===
    {"name": "Chocolate Brownie", "category": "Desserts", "price": 149, "meal_type": "All Day",
     "description": "Warm brownie with vanilla ice cream", "is_recommended": True},
    {"name": "Tiramisu", "category": "Desserts", "price": 199, "meal_type": "Dinner",
     "description": "Classic Italian coffee-flavored dessert"},
    {"name": "Cheesecake", "category": "Desserts", "price": 179, "meal_type": "All Day",
     "description": "New York style with berry compote"},
    {"name": "Gulab Jamun", "category": "Desserts", "price": 129, "meal_type": "Dinner",
     "description": "Sweet milk dumplings in cardamom syrup"},
    {"name": "Ice Cream Sundae", "category": "Desserts", "price": 159, "meal_type": "All Day",
     "description": "Three scoops with chocolate sauce and nuts"},

    # === BEVERAGES (All Day) ===
    {"name": "Coca Cola", "category": "Beverages", "price": 50, "meal_type": "All Day",
     "description": "Chilled soft drink"},
    {"name": "Fresh Orange Juice", "category": "Beverages", "price": 99, "meal_type": "Breakfast",
     "description": "Freshly squeezed orange juice", "is_recommended": True},
    {"name": "Mango Lassi", "category": "Beverages", "price": 89, "meal_type": "All Day",
     "description": "Sweet yogurt drink with mango"},
    {"name": "Masala Chai", "category": "Beverages", "price": 49, "meal_type": "All Day",
     "description": "Traditional Indian spiced tea"},
    {"name": "Cold Coffee", "category": "Beverages", "price": 99, "meal_type": "All Day",
     "description": "Iced coffee with cream"},
    {"name": "Fresh Lime Soda", "category": "Beverages", "price": 59, "meal_type": "All Day",
     "description": "Refreshing lime with soda"},
    {"name": "Hot Cappuccino", "category": "Beverages", "price": 129, "meal_type": "Breakfast",
     "description": "Rich espresso with steamed milk foam"},

    # === SNACKS (All Day) ===
    {"name": "French Fries", "category": "Snacks", "price": 129, "meal_type": "All Day",
     "description": "Crispy golden fries with ketchup"},
    {"name": "Onion Rings", "category": "Snacks", "price": 149, "meal_type": "All Day",
     "description": "Crispy battered onion rings"},
    {"name": "Nachos Grande", "category": "Snacks", "price": 229, "meal_type": "All Day",
     "description": "Loaded nachos with cheese, salsa, and sour cream"},
    {"name": "Chicken Nuggets", "category": "Snacks", "price": 179, "meal_type": "All Day",
     "description": "Crispy chicken nuggets with dipping sauce"},
]


async def seed_full_menu():
    """Seed the complete menu with meal types."""
    from app.core.db_pool import get_async_pool

    pool = await get_async_pool()

    async with pool.acquire() as conn:
        print("\n" + "="*60)
        print("SEEDING FULL MENU WITH MEAL TYPES")
        print("="*60)

        # Get restaurant_id
        restaurant = await conn.fetchrow("SELECT restaurant_id FROM restaurant_table LIMIT 1")
        if not restaurant:
            print("[ERROR] No restaurant found! Please seed restaurant first.")
            return
        restaurant_id = restaurant['restaurant_id']
        print(f"[OK] Using restaurant: {restaurant_id}")

        # ====================================================================
        # 0. CREATE MISSING TABLES (meal_type, menu_item_availability_schedule)
        # ====================================================================
        print("\n--- Ensuring Required Tables Exist ---")

        # Create meal_type table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS meal_type (
                meal_type_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                meal_type_name VARCHAR(50) NOT NULL UNIQUE,
                display_order INTEGER NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMPTZ,
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        print("  [OK] meal_type table ready")

        # Create menu_item_availability_schedule table if not exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS menu_item_availability_schedule (
                schedule_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                menu_item_id UUID NOT NULL REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,
                meal_type_id UUID REFERENCES meal_type(meal_type_id) ON DELETE SET NULL,
                day_of_week VARCHAR(20),
                time_from TIME,
                time_to TIME,
                is_available BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                created_by UUID,
                updated_by UUID,
                deleted_at TIMESTAMPTZ,
                is_deleted BOOLEAN DEFAULT FALSE
            )
        """)
        print("  [OK] menu_item_availability_schedule table ready")

        # ====================================================================
        # 1. SEED MEAL TYPES
        # ====================================================================
        print("\n--- Seeding Meal Types ---")
        meal_type_ids = {}

        for mt in MEAL_TYPES:
            # Check if exists
            existing = await conn.fetchrow(
                "SELECT meal_type_id FROM meal_type WHERE meal_type_name = $1 AND is_deleted = FALSE",
                mt["name"]
            )
            if existing:
                meal_type_ids[mt["name"]] = existing['meal_type_id']
                print(f"  [EXISTS] {mt['name']}")
            else:
                new_id = uuid4()
                await conn.execute("""
                    INSERT INTO meal_type (meal_type_id, meal_type_name, display_order)
                    VALUES ($1, $2, $3)
                """, new_id, mt["name"], mt["order"])
                meal_type_ids[mt["name"]] = new_id
                print(f"  [ADDED] {mt['name']}")

        # ====================================================================
        # 2. SEED CATEGORIES
        # ====================================================================
        print("\n--- Seeding Categories ---")
        category_ids = {}

        for cat in CATEGORIES:
            # Note: table name is menu_categories (with 's')
            existing = await conn.fetchrow(
                "SELECT menu_category_id FROM menu_categories WHERE menu_category_name = $1 AND is_deleted = FALSE",
                cat["name"]
            )
            if existing:
                category_ids[cat["name"]] = existing['menu_category_id']
                print(f"  [EXISTS] {cat['name']}")
            else:
                new_id = uuid4()
                await conn.execute("""
                    INSERT INTO menu_categories (menu_category_id, restaurant_id, menu_category_name, menu_category_description)
                    VALUES ($1, $2, $3, $4)
                """, new_id, restaurant_id, cat["name"], cat["description"])
                category_ids[cat["name"]] = new_id
                print(f"  [ADDED] {cat['name']}")

        # ====================================================================
        # 3. SEED MENU ITEMS
        # ====================================================================
        print("\n--- Seeding Menu Items ---")
        added_count = 0
        updated_count = 0

        for item in MENU_ITEMS:
            # Check if exists
            existing = await conn.fetchrow(
                "SELECT menu_item_id FROM menu_item WHERE menu_item_name = $1 AND is_deleted = FALSE",
                item["name"]
            )

            if existing:
                # Update existing item
                await conn.execute("""
                    UPDATE menu_item SET
                        menu_item_description = $2,
                        menu_item_price = $3,
                        menu_item_is_recommended = $4,
                        menu_item_in_stock = TRUE,
                        menu_item_status = 'active'
                    WHERE menu_item_id = $1
                """, existing['menu_item_id'], item["description"], Decimal(str(item["price"])),
                    item.get("is_recommended", False))

                menu_item_id = existing['menu_item_id']
                updated_count += 1
            else:
                # Insert new item
                menu_item_id = uuid4()
                await conn.execute("""
                    INSERT INTO menu_item (
                        menu_item_id, restaurant_id, menu_item_name, menu_item_description,
                        menu_item_price, menu_item_is_recommended, menu_item_in_stock, menu_item_status
                    ) VALUES ($1, $2, $3, $4, $5, $6, TRUE, 'active')
                """, menu_item_id, restaurant_id, item["name"], item["description"],
                    Decimal(str(item["price"])), item.get("is_recommended", False))
                added_count += 1

            # ================================================================
            # 4. LINK TO CATEGORY (menu_item_category_mapping)
            # ================================================================
            cat_id = category_ids.get(item["category"])
            if cat_id:
                # Remove old mapping and add new one
                await conn.execute(
                    "DELETE FROM menu_item_category_mapping WHERE menu_item_id = $1",
                    menu_item_id
                )
                await conn.execute("""
                    INSERT INTO menu_item_category_mapping (mapping_id, menu_item_id, menu_category_id, restaurant_id, is_primary)
                    VALUES ($1, $2, $3, $4, TRUE)
                    ON CONFLICT DO NOTHING
                """, uuid4(), menu_item_id, cat_id, restaurant_id)

            # ================================================================
            # 5. LINK TO MEAL TYPE (menu_item_availability_schedule)
            # ================================================================
            meal_type_id = meal_type_ids.get(item["meal_type"])
            if meal_type_id:
                # Remove old schedule and add new one
                await conn.execute(
                    "DELETE FROM menu_item_availability_schedule WHERE menu_item_id = $1",
                    menu_item_id
                )
                await conn.execute("""
                    INSERT INTO menu_item_availability_schedule (schedule_id, menu_item_id, meal_type_id, is_available)
                    VALUES ($1, $2, $3, TRUE)
                """, uuid4(), menu_item_id, meal_type_id)

        print(f"  [ADDED] {added_count} new items")
        print(f"  [UPDATED] {updated_count} existing items")

        # ====================================================================
        # SUMMARY
        # ====================================================================
        total_items = await conn.fetchval("SELECT COUNT(*) FROM menu_item WHERE is_deleted = FALSE")
        total_categories = await conn.fetchval("SELECT COUNT(*) FROM menu_categories WHERE is_deleted = FALSE")
        total_meal_types = await conn.fetchval("SELECT COUNT(*) FROM meal_type WHERE is_deleted = FALSE")

        print("\n" + "="*60)
        print("SEEDING COMPLETE!")
        print("="*60)
        print(f"Total Menu Items: {total_items}")
        print(f"Total Categories: {total_categories}")
        print(f"Total Meal Types: {total_meal_types}")

        # Show sample by meal type
        print("\n--- Items by Meal Type ---")
        for meal_name in ["Breakfast", "Lunch", "Dinner", "All Day"]:
            count = await conn.fetchval("""
                SELECT COUNT(DISTINCT mi.menu_item_id)
                FROM menu_item mi
                JOIN menu_item_availability_schedule mas ON mi.menu_item_id = mas.menu_item_id
                JOIN meal_type mt ON mas.meal_type_id = mt.meal_type_id
                WHERE mt.meal_type_name = $1 AND mi.is_deleted = FALSE
            """, meal_name)
            print(f"  {meal_name}: {count} items")


if __name__ == "__main__":
    asyncio.run(seed_full_menu())
