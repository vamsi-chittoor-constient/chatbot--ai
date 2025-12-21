"""
Setup Order Tables - Aligned with A24 Schema
=============================================
Create orders, order_item, and lookup tables matching the A24 dump schema.
Adds extra fields needed for chat agent (quantity, device_id, etc.)

Run:
    python scripts/setup_order_tables.py
"""

import sys
sys.path.insert(0, '.')


def create_tables():
    """Create tables matching A24_restaurant_dev_dump.sql schema."""
    from app.core.db_pool import SyncDBConnection

    sql_statements = [
        # Enable uuid-ossp extension for uuid_generate_v4()
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',

        # Create order_type_table (dine_in, take_away, delivery, etc.)
        """
        CREATE TABLE IF NOT EXISTS order_type_table (
            order_type_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_type_code VARCHAR(20),
            order_type_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create order_status_type (pending, confirmed, preparing, ready, completed, cancelled)
        """
        CREATE TABLE IF NOT EXISTS order_status_type (
            order_status_type_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_status_code VARCHAR(20),
            order_status_name VARCHAR(255),
            order_status_description TEXT,
            order_status_is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create order_source_type (chat_agent, pos, web, app, etc.)
        """
        CREATE TABLE IF NOT EXISTS order_source_type (
            order_source_type_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_source_type_code VARCHAR(20),
            order_source_type_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create orders (main order table)
        # Note: restaurant_id uses VARCHAR to match existing restaurant_config.id
        """
        CREATE TABLE IF NOT EXISTS orders (
            order_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            restaurant_id VARCHAR(50),
            table_booking_id UUID,
            order_number BIGINT,
            order_invoice_number VARCHAR(20),
            order_vr_order_id VARCHAR(255),
            order_external_reference_id VARCHAR(255),
            order_type_id UUID REFERENCES order_type_table(order_type_id),
            order_source_type_id UUID REFERENCES order_source_type(order_source_type_id),
            order_status_type_id UUID REFERENCES order_status_type(order_status_type_id),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE,
            -- Extra fields for chat agent
            device_id VARCHAR(255),
            order_display_id VARCHAR(20) UNIQUE,
            total_amount NUMERIC(12,2),
            cancelled_at TIMESTAMP WITH TIME ZONE,
            cancellation_reason TEXT
        )
        """,
        # Create indexes for orders
        "CREATE INDEX IF NOT EXISTS idx_orders_restaurant ON orders(restaurant_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_device ON orders(device_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_display_id ON orders(order_display_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(order_status_type_id)",
        "CREATE INDEX IF NOT EXISTS idx_orders_created ON orders(created_at)",

        # Create order_item (line items)
        """
        CREATE TABLE IF NOT EXISTS order_item (
            order_item_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_id UUID REFERENCES orders(order_id),
            menu_item_id UUID,
            menu_item_variation_id UUID,
            sku VARCHAR(100),
            hsn_code VARCHAR(20),
            category_id UUID,
            category_name VARCHAR(100),
            base_price NUMERIC(10,2),
            discount_amount NUMERIC(10,2) DEFAULT 0,
            tax_amount NUMERIC(10,2) DEFAULT 0,
            addon_total NUMERIC(10,2) DEFAULT 0,
            is_available BOOLEAN DEFAULT TRUE,
            unavailable_reason TEXT,
            substitute_item_id UUID,
            cooking_instructions TEXT,
            spice_level VARCHAR(20),
            customizations JSONB,
            item_status VARCHAR(50),
            prepared_at TIMESTAMP WITH TIME ZONE,
            served_at TIMESTAMP WITH TIME ZONE,
            cancelled_at TIMESTAMP WITH TIME ZONE,
            cancellation_reason TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE,
            -- Extra fields for chat agent
            item_name VARCHAR(255),
            quantity INTEGER DEFAULT 1,
            unit_price NUMERIC(10,2),
            line_total NUMERIC(10,2)
        )
        """,
        # Create indexes for order_item
        "CREATE INDEX IF NOT EXISTS idx_order_item_order ON order_item(order_id)",
        "CREATE INDEX IF NOT EXISTS idx_order_item_menu ON order_item(menu_item_id)",

        # Create order_total (totals breakdown)
        """
        CREATE TABLE IF NOT EXISTS order_total (
            order_total_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            order_id UUID REFERENCES orders(order_id),
            items_total NUMERIC(12,2),
            addons_total NUMERIC(12,2) DEFAULT 0,
            charges_total NUMERIC(12,2) DEFAULT 0,
            discount_total NUMERIC(12,2) DEFAULT 0,
            tax_total NUMERIC(12,2) DEFAULT 0,
            platform_fee NUMERIC(10,2) DEFAULT 0,
            convenience_fee NUMERIC(10,2) DEFAULT 0,
            subtotal NUMERIC(12,2),
            roundoff_amount NUMERIC(10,2) DEFAULT 0,
            total_before_tip NUMERIC(12,2),
            tip_amount NUMERIC(10,2) DEFAULT 0,
            final_amount NUMERIC(12,2),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,
    ]

    print("Creating order tables (A24 schema)...")

    with SyncDBConnection() as conn:
        with conn.cursor() as cursor:
            for sql in sql_statements:
                try:
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    print(f"Warning: {e}")
                    conn.rollback()

    print("[DONE] Tables created successfully")


def seed_lookup_tables():
    """Seed lookup tables with default values."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor

    print("\nSeeding lookup tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Seed order_type_table
            order_types = [
                ('dine_in', 'Dine In'),
                ('take_away', 'Take Away'),
                ('delivery', 'Delivery'),
            ]
            for code, name in order_types:
                cursor.execute("""
                    INSERT INTO order_type_table (order_type_code, order_type_name)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (code, name))

            # Seed order_status_type
            order_statuses = [
                ('pending', 'Pending', 'Order placed, awaiting confirmation'),
                ('confirmed', 'Confirmed', 'Order confirmed by restaurant'),
                ('preparing', 'Preparing', 'Order being prepared in kitchen'),
                ('ready', 'Ready', 'Order ready for pickup/serving'),
                ('completed', 'Completed', 'Order completed and served'),
                ('cancelled', 'Cancelled', 'Order cancelled'),
            ]
            for code, name, desc in order_statuses:
                cursor.execute("""
                    INSERT INTO order_status_type (order_status_code, order_status_name, order_status_description)
                    VALUES (%s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (code, name, desc))

            # Seed order_source_type
            order_sources = [
                ('chat_agent', 'Chat Agent'),
                ('pos', 'Point of Sale'),
                ('web', 'Website'),
                ('app', 'Mobile App'),
            ]
            for code, name in order_sources:
                cursor.execute("""
                    INSERT INTO order_source_type (order_source_type_code, order_source_type_name)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (code, name))

            conn.commit()

    print("  [DONE] Lookup tables seeded")


def verify():
    """Verify the tables were created."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor

    print("\nVerifying tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check each table
            tables = [
                'order_type_table',
                'order_status_type',
                'order_source_type',
                'orders',
                'order_item',
                'order_total',
            ]

            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"  {table}: {count} rows")

            # Show order types
            print("\n  Order types:")
            cursor.execute("SELECT order_type_code, order_type_name FROM order_type_table")
            for row in cursor.fetchall():
                print(f"    - {row['order_type_code']}: {row['order_type_name']}")

            # Show order statuses
            print("\n  Order statuses:")
            cursor.execute("SELECT order_status_code, order_status_name FROM order_status_type")
            for row in cursor.fetchall():
                print(f"    - {row['order_status_code']}: {row['order_status_name']}")


if __name__ == "__main__":
    create_tables()
    seed_lookup_tables()
    verify()
    print("\n[SUCCESS] Order tables ready (A24 schema)!")
