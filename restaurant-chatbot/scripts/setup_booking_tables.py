"""
Setup Booking Tables - Aligned with A24 Schema
===============================================
Create table_info and table_booking_info tables matching the dump schema.

Run:
    python scripts/setup_booking_tables.py
"""

import sys
sys.path.insert(0, '.')


def create_tables():
    """Create tables matching A24_restaurant_dev_dump.sql schema."""
    from app.core.db_pool import SyncDBConnection

    sql_statements = [
        # Enable uuid-ossp extension for uuid_generate_v4()
        'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"',

        # Create table_info (restaurant tables/seating)
        # Note: restaurant_id uses VARCHAR to match existing restaurant_config.id
        """
        CREATE TABLE IF NOT EXISTS table_info (
            table_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            restaurant_id VARCHAR(50) NOT NULL,
            table_number INTEGER,
            table_capacity INTEGER,
            table_type VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            floor_location VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,
        # Create indexes for table_info
        "CREATE INDEX IF NOT EXISTS idx_table_info_restaurant ON table_info(restaurant_id)",
        "CREATE INDEX IF NOT EXISTS idx_table_info_capacity ON table_info(table_capacity)",
        "CREATE INDEX IF NOT EXISTS idx_table_info_active ON table_info(is_active)",

        # Create table_special_features
        """
        CREATE TABLE IF NOT EXISTS table_special_features (
            table_feature_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            table_id UUID NOT NULL REFERENCES table_info(table_id),
            feature_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create table_booking_occasion_info
        """
        CREATE TABLE IF NOT EXISTS table_booking_occasion_info (
            occasion_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            occasion_name VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE
        )
        """,

        # Create table_booking_info (reservations)
        # Note: restaurant_id uses VARCHAR to match existing restaurant_config.id
        """
        CREATE TABLE IF NOT EXISTS table_booking_info (
            table_booking_id UUID DEFAULT public.uuid_generate_v4() PRIMARY KEY,
            restaurant_id VARCHAR(50) NOT NULL,
            table_id UUID NOT NULL REFERENCES table_info(table_id),
            meal_slot_timing_id UUID,
            previous_slot_id UUID,
            customer_id UUID,
            occasion_id UUID REFERENCES table_booking_occasion_info(occasion_id),
            party_size INTEGER,
            booking_date DATE,
            booking_time TIME WITHOUT TIME ZONE,
            booking_status VARCHAR(20),
            special_request TEXT,
            cancellation_reason TEXT,
            is_advance_booking BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by UUID,
            updated_by UUID,
            deleted_at TIMESTAMP WITH TIME ZONE,
            is_deleted BOOLEAN DEFAULT FALSE,
            -- Extra fields for chat agent
            device_id VARCHAR(255),
            guest_name VARCHAR(255),
            contact_phone VARCHAR(20),
            confirmation_code VARCHAR(20) UNIQUE
        )
        """,
        # Create indexes for table_booking_info
        "CREATE INDEX IF NOT EXISTS idx_booking_restaurant ON table_booking_info(restaurant_id)",
        "CREATE INDEX IF NOT EXISTS idx_booking_table ON table_booking_info(table_id)",
        "CREATE INDEX IF NOT EXISTS idx_booking_customer ON table_booking_info(customer_id)",
        "CREATE INDEX IF NOT EXISTS idx_booking_date ON table_booking_info(booking_date)",
        "CREATE INDEX IF NOT EXISTS idx_booking_status ON table_booking_info(booking_status)",
        "CREATE INDEX IF NOT EXISTS idx_booking_device ON table_booking_info(device_id)",
        "CREATE INDEX IF NOT EXISTS idx_booking_confirmation ON table_booking_info(confirmation_code)",
    ]

    print("Creating booking tables (A24 schema)...")

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


def seed_tables():
    """Seed sample table data."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor

    print("\nSeeding sample tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check if tables already exist
            cursor.execute("SELECT COUNT(*) as count FROM table_info")
            count = cursor.fetchone()['count']

            if count > 0:
                print(f"  Tables already seeded ({count} tables exist)")
                return

            # Get restaurant_id from restaurant_config
            cursor.execute("SELECT id FROM restaurant_config LIMIT 1")
            row = cursor.fetchone()
            if not row:
                print("  [ERROR] No restaurant_config found")
                return

            restaurant_id = row['id']

            # Generate 200 tables programmatically
            # Distribution: 40% 2-seat, 25% 4-seat, 15% 6-seat, 12% 8-seat, 8% 10-seat
            import random
            random.seed(42)  # Reproducible

            capacity_distribution = (
                [(2, 'romantic')] * 80 +
                [(4, 'family')] * 50 +
                [(6, 'group')] * 30 +
                [(8, 'private')] * 24 +
                [(10, 'events')] * 16
            )
            locations = ['Main Area', 'Window', 'Patio', 'Garden', 'Bar Area', 'Private Room', 'Banquet Hall', 'Terrace']
            feature_map = {
                'Window': 'Window View', 'Patio': 'Outdoor Seating', 'Garden': 'Garden View',
                'Terrace': 'Outdoor Seating', 'Private Room': 'Private Dining',
                'Banquet Hall': 'Stage View', 'Bar Area': 'Bar Seating',
            }

            for tbl_num, (capacity, tbl_type) in enumerate(capacity_distribution, start=1):
                location = random.choice(locations)
                cursor.execute("""
                    INSERT INTO table_info (restaurant_id, table_number, table_capacity, table_type, floor_location, is_active)
                    VALUES (%s, %s, %s, %s, %s, TRUE)
                """, (restaurant_id, tbl_num, capacity, tbl_type, location))

                # Add feature if location has one
                feature = feature_map.get(location)
                if feature:
                    cursor.execute("""
                        INSERT INTO table_special_features (table_id, feature_name)
                        SELECT table_id, %s FROM table_info
                        WHERE restaurant_id = %s AND table_number = %s
                    """, (feature, restaurant_id, tbl_num))

            print(f"  Inserted {len(capacity_distribution)} tables")

            # Seed occasions
            occasions = ['Birthday', 'Anniversary', 'Business', 'Date Night', 'Family Gathering', 'Other']
            for occasion in occasions:
                cursor.execute("""
                    INSERT INTO table_booking_occasion_info (occasion_name)
                    VALUES (%s)
                    ON CONFLICT DO NOTHING
                """, (occasion,))

            conn.commit()

    print(f"  [DONE] Seeded {len(sample_tables)} tables and {len(occasions)} occasions")


def verify():
    """Verify the tables were created."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor

    print("\nVerifying tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check table_info
            cursor.execute("SELECT COUNT(*) as count FROM table_info")
            tables_count = cursor.fetchone()['count']
            print(f"  table_info: {tables_count} rows")

            # Check table_booking_info
            cursor.execute("SELECT COUNT(*) as count FROM table_booking_info")
            bookings_count = cursor.fetchone()['count']
            print(f"  table_booking_info: {bookings_count} rows")

            # Check occasions
            cursor.execute("SELECT COUNT(*) as count FROM table_booking_occasion_info")
            occasions_count = cursor.fetchone()['count']
            print(f"  table_booking_occasion_info: {occasions_count} rows")

            # Show sample tables
            cursor.execute("SELECT table_number, table_capacity, floor_location FROM table_info ORDER BY table_capacity LIMIT 5")
            rows = cursor.fetchall()
            print("\n  Sample tables:")
            for r in rows:
                print(f"    T{r['table_number']}: {r['table_capacity']} seats ({r['floor_location']})")


if __name__ == "__main__":
    create_tables()
    seed_tables()
    verify()
    print("\n[SUCCESS] Booking tables ready (A24 schema)!")
