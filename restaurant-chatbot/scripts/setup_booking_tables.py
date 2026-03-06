"""
Setup Booking Tables - Aligned with A24 Schema
===============================================
Tables (table_info, table_booking_info, etc.) already exist from the DB dump.
This script:
  1. Adds missing columns to table_booking_info (device_id, guest_name, etc.)
  2. Seeds 200 tables into table_info
  3. Seeds occasion types

Run:
    python scripts/setup_booking_tables.py
"""

import sys
sys.path.insert(0, '.')


def add_missing_columns():
    """Add columns needed by the chatbot that don't exist in the A24 dump schema."""
    from app.core.db_pool import SyncDBConnection

    alter_statements = [
        # table_booking_info: add chatbot-specific columns
        "ALTER TABLE table_booking_info ADD COLUMN IF NOT EXISTS device_id VARCHAR(255)",
        "ALTER TABLE table_booking_info ADD COLUMN IF NOT EXISTS guest_name VARCHAR(255)",
        "ALTER TABLE table_booking_info ADD COLUMN IF NOT EXISTS contact_phone VARCHAR(20)",
        "ALTER TABLE table_booking_info ADD COLUMN IF NOT EXISTS confirmation_code VARCHAR(20)",
        # Make customer_id nullable and drop FK (chatbot bookings don't have a customer record)
        "ALTER TABLE table_booking_info DROP CONSTRAINT IF EXISTS fk_table_booking_info_customer_id",
        "ALTER TABLE table_booking_info ALTER COLUMN customer_id DROP NOT NULL",
        # Indexes for chatbot queries
        "CREATE INDEX IF NOT EXISTS idx_booking_device ON table_booking_info(device_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_booking_confirmation ON table_booking_info(confirmation_code)",
        "CREATE INDEX IF NOT EXISTS idx_booking_date ON table_booking_info(booking_date)",
        "CREATE INDEX IF NOT EXISTS idx_booking_status ON table_booking_info(booking_status)",
    ]

    print("Adding missing columns to table_booking_info...")

    with SyncDBConnection() as conn:
        with conn.cursor() as cursor:
            for sql in alter_statements:
                try:
                    cursor.execute(sql)
                    conn.commit()
                except Exception as e:
                    msg = str(e).strip()
                    if 'already exists' in msg or 'duplicate' in msg.lower():
                        print(f"  (already done) {sql[:60]}...")
                    else:
                        print(f"  Warning: {msg}")
                    conn.rollback()

    print("[DONE] Columns ready")


def seed_tables():
    """Seed 200 tables into table_info."""
    from app.core.db_pool import SyncDBConnection
    from psycopg2.extras import RealDictCursor
    import random

    print("\nSeeding tables...")

    with SyncDBConnection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check if tables already exist
            cursor.execute("SELECT COUNT(*) as count FROM table_info")
            count = cursor.fetchone()['count']

            if count > 0:
                print(f"  Tables already seeded ({count} tables exist)")
                return

            # Get restaurant_id from restaurant_table (UUID)
            cursor.execute("SELECT restaurant_id FROM restaurant_table LIMIT 1")
            row = cursor.fetchone()
            if not row:
                print("  [ERROR] No restaurant_table found")
                return

            restaurant_id = row['restaurant_id']
            print(f"  Using restaurant_id: {restaurant_id}")

            # Generate 200 tables programmatically
            # Distribution: 40% 2-seat, 25% 4-seat, 15% 6-seat, 12% 8-seat, 8% 10-seat
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

            # Seed occasions (column is occasion_type in dump schema)
            occasions = ['Birthday', 'Anniversary', 'Business', 'Date Night', 'Family Gathering', 'Other']
            for occasion in occasions:
                cursor.execute("""
                    INSERT INTO table_booking_occasion_info (occasion_type)
                    VALUES (%s)
                    ON CONFLICT DO NOTHING
                """, (occasion,))

            conn.commit()

    print(f"  [DONE] Seeded 200 tables and occasions")


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

            # Check chatbot columns exist
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'table_booking_info'
                AND column_name IN ('device_id', 'guest_name', 'confirmation_code')
            """)
            cols = [r['column_name'] for r in cursor.fetchall()]
            print(f"  chatbot columns present: {', '.join(cols)}")

            # Capacity distribution
            cursor.execute("""
                SELECT table_capacity, COUNT(*) as cnt
                FROM table_info
                WHERE is_active = TRUE AND (is_deleted = FALSE OR is_deleted IS NULL)
                GROUP BY table_capacity
                ORDER BY table_capacity
            """)
            rows = cursor.fetchall()
            print("\n  Capacity distribution:")
            for r in rows:
                print(f"    {r['table_capacity']}-seat: {r['cnt']} tables")


if __name__ == "__main__":
    add_missing_columns()
    seed_tables()
    verify()
    print("\n[SUCCESS] Booking tables ready!")
