-- =============================================================================
-- Populate Restaurant Config with Default Data
-- =============================================================================
-- This migration populates restaurant_config table with default data if empty.
-- Ensures the application has a restaurant configuration to work with.
--
-- Business hours: 24/7 (00:00 - 23:59) for easy testing
-- =============================================================================
DO $$
DECLARE
    restaurant_count INTEGER;
BEGIN
    -- Check if restaurant_config is empty
    SELECT COUNT(*) INTO restaurant_count FROM restaurant_config;

    IF restaurant_count = 0 THEN
        INSERT INTO restaurant_config (
            id,
            name,
            description,
            address,
            phone,
            email,
            website,
            timezone,
            currency,
            tax_rate,
            service_charge_rate,
            opening_time,
            closing_time,
            is_open,
            settings,
            created_at,
            updated_at
        ) VALUES (
            gen_random_uuid(),
            'A24 Restaurant',
            'Modern dining experience with authentic flavors and exceptional service',
            '123 Main Street, City Center, Mumbai, Maharashtra 400001',
            '+919876543210',
            'contact@a24restaurant.com',
            'https://www.a24restaurant.com',
            'Asia/Kolkata',
            'INR',
            5.00,  -- 5% tax
            10.00, -- 10% service charge
            '00:00:00'::time,  -- 24/7 opening time
            '23:59:59'::time,  -- 24/7 closing time
            true,
            jsonb_build_object(
                'business_hours', jsonb_build_object(
                    'monday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true),
                    'tuesday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true),
                    'wednesday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true),
                    'thursday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true),
                    'friday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true),
                    'saturday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true),
                    'sunday', jsonb_build_object('open', '00:00', 'close', '23:59', 'is_open', true)
                ),
                'policies', jsonb_build_object(
                    'cancellation_policy', 'Free cancellation up to 2 hours before reservation time',
                    'reservation_policy', 'Reservations are held for 15 minutes past the booking time',
                    'payment_policy', 'We accept cash, cards, and UPI payments',
                    'child_policy', 'Children of all ages are welcome',
                    'pet_policy', 'Pets are not allowed inside the restaurant'
                )
            ),
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        );

        RAISE NOTICE 'Restaurant config populated with default data (24/7 hours)';
    ELSE
        RAISE NOTICE 'Restaurant config already exists, skipping population';
    END IF;
END $$;
