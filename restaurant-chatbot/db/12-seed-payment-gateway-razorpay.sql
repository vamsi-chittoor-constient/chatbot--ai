-- ============================================================================
-- Payment Gateway Seed Data - Razorpay Configuration
-- ============================================================================
--
-- This script inserts or updates the Razorpay payment gateway configuration
-- into the payment_gateway table.
--
-- TEST MODE Configuration:
--   - Uses test credentials: rzp_test_dXwWkc7Rw3f52T
--   - Test mode allows testing without real money
--   - Test cards: 4111 1111 1111 1111, any future expiry, any CVV
--
-- PRODUCTION: Replace with live credentials (rzp_live_XXX) before deployment
-- ============================================================================

-- Insert Razorpay payment gateway configuration
-- Uses ON CONFLICT to update if already exists
INSERT INTO payment_gateway (
    payment_gateway_id,
    payment_gateway_code,
    payment_gateway_name,
    payment_gateway_is_active,
    payment_gateway_config,
    created_at,
    updated_at
) VALUES (
    gen_random_uuid(),
    'razorpay',
    'Razorpay',
    true,
    '{
        "key_id": "rzp_test_dXwWkc7Rw3f52T",
        "key_secret": "bs6Jk9HhctjKCBPN3IE4iPsF",
        "mode": "test",
        "supported_payment_methods": ["card", "upi", "netbanking", "wallet"],
        "supported_currencies": ["INR"],
        "webhook_secret": "whsec_test_get_from_razorpay_dashboard",
        "features": {
            "payment_links": true,
            "payment_pages": true,
            "subscriptions": false,
            "smart_collect": false,
            "refunds": true,
            "international_payments": false
        },
        "dashboard_url": "https://dashboard.razorpay.com",
        "docs_url": "https://razorpay.com/docs/api"
    }'::jsonb,
    NOW(),
    NOW()
)
ON CONFLICT (payment_gateway_code)
DO UPDATE SET
    payment_gateway_name = EXCLUDED.payment_gateway_name,
    payment_gateway_is_active = EXCLUDED.payment_gateway_is_active,
    payment_gateway_config = EXCLUDED.payment_gateway_config,
    updated_at = NOW();

-- Verify insertion
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM payment_gateway WHERE payment_gateway_code = 'razorpay') THEN
        RAISE NOTICE 'SUCCESS: Razorpay payment gateway configured';
        RAISE NOTICE 'Mode: TEST (use rzp_test_dXwWkc7Rw3f52T)';
        RAISE NOTICE 'Supported methods: card, upi, netbanking, wallet';
        RAISE NOTICE 'WARNING: Replace with live credentials before production deployment!';
    ELSE
        RAISE WARNING 'FAILED: Razorpay payment gateway not found after insertion';
    END IF;
END $$;

-- Display current payment gateway configuration
SELECT
    payment_gateway_code AS code,
    payment_gateway_name AS name,
    payment_gateway_is_active AS active,
    payment_gateway_config->>'mode' AS mode,
    payment_gateway_config->>'key_id' AS key_id_prefix,
    created_at,
    updated_at
FROM payment_gateway
WHERE payment_gateway_code = 'razorpay';
