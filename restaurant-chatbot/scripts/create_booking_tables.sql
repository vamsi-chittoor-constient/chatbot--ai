-- Create Tables for Booking System
-- Run: psql -d restaurant_ai_dev -f scripts/create_booking_tables.sql

-- Table for restaurant tables/seating
CREATE TABLE IF NOT EXISTS tables (
    id VARCHAR(20) PRIMARY KEY,
    restaurant_id VARCHAR(20) NOT NULL REFERENCES restaurant_config(id),
    table_number VARCHAR(20) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    location VARCHAR(100),
    features TEXT[],
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(restaurant_id, table_number)
);

CREATE INDEX IF NOT EXISTS idx_tables_restaurant ON tables(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_tables_capacity ON tables(capacity);
CREATE INDEX IF NOT EXISTS idx_tables_active ON tables(is_active);

-- Table for bookings/reservations
CREATE TABLE IF NOT EXISTS bookings (
    id VARCHAR(20) PRIMARY KEY,
    user_id VARCHAR(20) REFERENCES users(id),
    device_id VARCHAR(255) REFERENCES user_devices(device_id),
    restaurant_id VARCHAR(20) NOT NULL REFERENCES restaurant_config(id),
    table_id VARCHAR(20) REFERENCES tables(id),
    booking_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    party_size INTEGER NOT NULL CHECK (party_size > 0 AND party_size <= 20),
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    booking_status VARCHAR(20) NOT NULL DEFAULT 'active',
    special_requests TEXT,
    contact_phone VARCHAR(20) NOT NULL,
    contact_email VARCHAR(255),
    booking_date DATE,
    booking_time TIME,
    guest_name VARCHAR(255),
    confirmation_code VARCHAR(20) UNIQUE,
    is_waitlisted BOOLEAN DEFAULT FALSE,
    waitlist_position INTEGER,
    reminder_sent BOOLEAN DEFAULT FALSE,
    created_by VARCHAR(100),
    updated_by VARCHAR(100),
    origin_of_booking VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT booking_identity_check CHECK (user_id IS NOT NULL OR device_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_bookings_user ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_device ON bookings(device_id);
CREATE INDEX IF NOT EXISTS idx_bookings_datetime ON bookings(booking_datetime);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_booking_status ON bookings(booking_status);
CREATE INDEX IF NOT EXISTS idx_bookings_confirmation ON bookings(confirmation_code);
CREATE INDEX IF NOT EXISTS idx_bookings_guest_name ON bookings(guest_name);

-- Seed some sample tables
INSERT INTO tables (id, restaurant_id, table_number, capacity, location, features, is_active)
SELECT
    'tbl_' || LPAD((row_number() OVER())::text, 3, '0'),
    (SELECT id FROM restaurant_config LIMIT 1),
    'T' || (row_number() OVER()),
    capacity,
    location,
    features::TEXT[],
    TRUE
FROM (VALUES
    (2, 'Window', ARRAY['romantic', 'quiet']),
    (2, 'Window', ARRAY['romantic', 'quiet']),
    (4, 'Main Area', ARRAY['family-friendly']),
    (4, 'Main Area', ARRAY['family-friendly']),
    (4, 'Patio', ARRAY['outdoor', 'smoking']),
    (6, 'Main Area', ARRAY['large-group']),
    (6, 'Private Room', ARRAY['private', 'celebration']),
    (8, 'Private Room', ARRAY['private', 'large-group']),
    (10, 'Banquet Hall', ARRAY['events', 'large-group'])
) AS t(capacity, location, features)
WHERE NOT EXISTS (SELECT 1 FROM tables)
ON CONFLICT DO NOTHING;

-- Verify
SELECT 'Tables created: ' || COUNT(*) FROM tables;
SELECT 'Bookings table ready' WHERE EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'bookings');
