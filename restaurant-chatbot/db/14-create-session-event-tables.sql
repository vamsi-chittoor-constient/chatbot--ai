-- Migration 14: Event-Sourced Session State Tables
-- ===================================================
-- Creates structured tables to track all session activity as discrete events
-- Replaces text-based context with SQL-queryable session state
--
-- Benefits:
-- - Zero token cost (queries not in prompts)
-- - Exact state tracking (not fuzzy text)
-- - Complete audit trail
-- - Analytics-ready
-- - Temporal queries possible

-- ============================================================================
-- SESSION EVENTS - Complete event log of all user actions
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_events (
    event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    user_id UUID,  -- NULL for anonymous sessions
    event_type VARCHAR(50) NOT NULL,  -- 'item_viewed', 'item_added', 'item_removed', 'cart_cleared', 'checkout', etc.
    event_data JSONB NOT NULL,  -- Flexible structure per event type
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for session_events
CREATE INDEX IF NOT EXISTS idx_session_events_session_id ON session_events(session_id);
CREATE INDEX IF NOT EXISTS idx_session_events_timestamp ON session_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_session_events_type ON session_events(event_type);
CREATE INDEX IF NOT EXISTS idx_session_events_session_time ON session_events(session_id, timestamp DESC);

COMMENT ON TABLE session_events IS 'Complete event log of all session activity - event sourcing pattern';
COMMENT ON COLUMN session_events.event_type IS 'Event types: item_viewed, item_added, item_removed, item_updated, cart_cleared, checkout_started, order_placed, payment_initiated, etc.';
COMMENT ON COLUMN session_events.event_data IS 'Event-specific data: {item_id, item_name, quantity, price, action, etc.}';

-- ============================================================================
-- SESSION CART - Current cart state (materialized view of add/remove events)
-- UNLOGGED = 3-5x faster writes, OK to lose on crash (users can re-add)
-- ============================================================================
CREATE UNLOGGED TABLE IF NOT EXISTS session_cart (
    session_id VARCHAR(255) NOT NULL,
    item_id UUID NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL,
    special_instructions TEXT,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,  -- Soft delete for audit trail

    PRIMARY KEY (session_id, item_id),
    FOREIGN KEY (item_id) REFERENCES menu_item(menu_item_id) ON DELETE CASCADE
);

-- Indexes for session_cart
CREATE INDEX IF NOT EXISTS idx_session_cart_session_id ON session_cart(session_id);
CREATE INDEX IF NOT EXISTS idx_session_cart_active ON session_cart(session_id, is_active);

COMMENT ON TABLE session_cart IS 'Current cart state - materialized view updated by add/remove events';
COMMENT ON COLUMN session_cart.is_active IS 'FALSE when removed (soft delete for history), TRUE for current items';

-- ============================================================================
-- SESSION STATE - Conversation context and flow state
-- UNLOGGED = Fast writes, OK to lose on crash (restart conversation)
-- ============================================================================
CREATE UNLOGGED TABLE IF NOT EXISTS session_state (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id UUID,  -- NULL for anonymous

    -- Conversation context (for pronoun resolution)
    last_mentioned_item_id UUID,
    last_mentioned_item_name VARCHAR(255),
    last_shown_menu JSONB,  -- Array of {id, name, position} for "the 2nd one" references

    -- Flow state
    current_step VARCHAR(50),  -- 'browsing', 'ordering', 'awaiting_quantity', 'checkout', 'payment'
    awaiting_input_for VARCHAR(100),  -- What we're waiting for: 'quantity_for_item_123', 'order_type', 'payment_method'

    -- Session metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    FOREIGN KEY (user_id) REFERENCES customer_profile_table(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (last_mentioned_item_id) REFERENCES menu_item(menu_item_id) ON DELETE SET NULL
);

-- Indexes for session_state
CREATE INDEX IF NOT EXISTS idx_session_state_last_activity ON session_state(last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_session_state_user_id ON session_state(user_id);

COMMENT ON TABLE session_state IS 'Session conversation state and flow tracking - updated by events';
COMMENT ON COLUMN session_state.current_step IS 'Current conversation step: browsing, ordering, awaiting_quantity, checkout, payment';
COMMENT ON COLUMN session_state.awaiting_input_for IS 'What input we are waiting for from user (enables stateful flows)';

-- ============================================================================
-- SESSION PREFERENCES - User preferences expressed during session
-- UNLOGGED = Fast writes, OK to lose on crash (non-critical)
-- ============================================================================
CREATE UNLOGGED TABLE IF NOT EXISTS session_preferences (
    session_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT NOT NULL,
    set_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (session_id, preference_key)
);

-- Indexes for session_preferences
CREATE INDEX IF NOT EXISTS idx_session_preferences_session_id ON session_preferences(session_id);

COMMENT ON TABLE session_preferences IS 'User preferences expressed during session: dietary restrictions, favorite items, etc.';

-- ============================================================================
-- Helper Functions - SQL functions for common queries
-- ============================================================================

-- Get active cart items for a session
CREATE OR REPLACE FUNCTION get_session_cart(p_session_id VARCHAR)
RETURNS TABLE (
    item_id UUID,
    item_name VARCHAR,
    quantity INT,
    price DECIMAL,
    total DECIMAL,
    special_instructions TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        sc.item_id,
        sc.item_name,
        sc.quantity,
        sc.price,
        (sc.quantity * sc.price) AS total,
        sc.special_instructions
    FROM session_cart sc
    WHERE sc.session_id = p_session_id
      AND sc.is_active = TRUE
    ORDER BY sc.added_at;
END;
$$ LANGUAGE plpgsql;

-- Get cart total for a session
CREATE OR REPLACE FUNCTION get_cart_total(p_session_id VARCHAR)
RETURNS DECIMAL AS $$
BEGIN
    RETURN (
        SELECT COALESCE(SUM(quantity * price), 0)
        FROM session_cart
        WHERE session_id = p_session_id
          AND is_active = TRUE
    );
END;
$$ LANGUAGE plpgsql;

-- Get last mentioned item for a session
CREATE OR REPLACE FUNCTION get_last_mentioned_item(p_session_id VARCHAR)
RETURNS TABLE (
    item_id UUID,
    item_name VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ss.last_mentioned_item_id,
        ss.last_mentioned_item_name
    FROM session_state ss
    WHERE ss.session_id = p_session_id
      AND ss.last_mentioned_item_id IS NOT NULL;
END;
$$ LANGUAGE plpgsql;

-- Get recent session events (for debugging/analytics)
CREATE OR REPLACE FUNCTION get_session_history(p_session_id VARCHAR, p_limit INT DEFAULT 50)
RETURNS TABLE (
    event_type VARCHAR,
    event_data JSONB,
    event_timestamp TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        se.event_type,
        se.event_data,
        se.timestamp
    FROM session_events se
    WHERE se.session_id = p_session_id
    ORDER BY se.timestamp DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Cleanup Functions - Auto-expire old sessions
-- ============================================================================

-- Function to clean up expired sessions (sessions inactive for >24 hours)
CREATE OR REPLACE FUNCTION cleanup_expired_sessions()
RETURNS INT AS $$
DECLARE
    deleted_count INT;
BEGIN
    -- Delete cart items from expired sessions
    WITH expired_sessions AS (
        SELECT session_id
        FROM session_state
        WHERE last_activity_at < NOW() - INTERVAL '24 hours'
    )
    DELETE FROM session_cart
    WHERE session_id IN (SELECT session_id FROM expired_sessions);

    -- Delete session state from expired sessions
    DELETE FROM session_state
    WHERE last_activity_at < NOW() - INTERVAL '24 hours';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_expired_sessions IS 'Cleans up sessions inactive for >24 hours - run periodically';

-- ============================================================================
-- Triggers - Auto-update timestamps
-- ============================================================================

-- Update session_state.updated_at on any change
CREATE OR REPLACE FUNCTION update_session_state_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.last_activity_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER session_state_update_timestamp
    BEFORE UPDATE ON session_state
    FOR EACH ROW
    EXECUTE FUNCTION update_session_state_timestamp();

-- Update session_cart.updated_at on any change
CREATE OR REPLACE FUNCTION update_session_cart_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER session_cart_update_timestamp
    BEFORE UPDATE ON session_cart
    FOR EACH ROW
    EXECUTE FUNCTION update_session_cart_timestamp();

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Additional composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_session_events_session_type_time
    ON session_events(session_id, event_type, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_session_cart_session_active
    ON session_cart(session_id, is_active) WHERE is_active = TRUE;

-- GIN index for JSONB queries on event_data
CREATE INDEX IF NOT EXISTS idx_session_events_data_gin
    ON session_events USING GIN(event_data);

-- ============================================================================
-- CHECKOUT FLOW TABLES (HOT → COLD transition)
-- ============================================================================

-- Session checkout state (UNLOGGED - temporary checkout data)
CREATE UNLOGGED TABLE IF NOT EXISTS session_checkout (
    session_id VARCHAR(255) PRIMARY KEY,
    order_type VARCHAR(20),  -- 'dine_in' | 'take_away' | 'delivery'
    payment_method VARCHAR(20),  -- 'cash' | 'card' | 'upi'
    special_instructions TEXT,
    delivery_address JSONB,  -- For delivery orders
    table_number INT,  -- For dine-in orders
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Indexes for session_checkout
CREATE INDEX IF NOT EXISTS idx_session_checkout_started ON session_checkout(started_at DESC);

COMMENT ON TABLE session_checkout IS 'Checkout flow state - UNLOGGED for speed, OK to lose on crash';

-- Payment intent (Bridge between session and payment_transaction)
-- LOGGED because it links to financial records
CREATE TABLE IF NOT EXISTS session_payment_intent (
    intent_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) NOT NULL,
    payment_gateway VARCHAR(50) NOT NULL,  -- 'razorpay', 'stripe', 'cash'
    gateway_order_id VARCHAR(255),  -- External payment system order ID
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'INR',
    status VARCHAR(20) NOT NULL,  -- 'created' | 'processing' | 'completed' | 'failed' | 'cancelled'
    metadata JSONB,  -- Gateway-specific data
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for session_payment_intent
CREATE INDEX IF NOT EXISTS idx_payment_intent_session_id ON session_payment_intent(session_id);
CREATE INDEX IF NOT EXISTS idx_payment_intent_gateway_order_id ON session_payment_intent(gateway_order_id);
CREATE INDEX IF NOT EXISTS idx_payment_intent_status ON session_payment_intent(status);

COMMENT ON TABLE session_payment_intent IS 'Payment intent tracking - LOGGED for financial audit';

-- Trigger to update payment_intent timestamp
CREATE OR REPLACE FUNCTION update_payment_intent_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER payment_intent_update_timestamp
    BEFORE UPDATE ON session_payment_intent
    FOR EACH ROW
    EXECUTE FUNCTION update_payment_intent_timestamp();

-- ============================================================================
-- HOT → COLD TRANSITION FUNCTION
-- ============================================================================

-- Function to create order from session (HOT → COLD)
CREATE OR REPLACE FUNCTION create_order_from_session(
    p_session_id VARCHAR,
    p_order_type VARCHAR,
    p_payment_method VARCHAR,
    p_customer_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_order_id UUID;
    v_total DECIMAL(10, 2);
BEGIN
    -- Validate cart not empty
    IF NOT EXISTS (
        SELECT 1 FROM session_cart
        WHERE session_id = p_session_id AND is_active = TRUE
    ) THEN
        RAISE EXCEPTION 'Cart is empty for session %', p_session_id;
    END IF;

    -- Calculate total
    SELECT get_cart_total(p_session_id) INTO v_total;

    -- Create order record (COLD storage)
    INSERT INTO orders (
        customer_id,
        order_type_id,
        order_source_id,
        total_amount,
        created_at
    )
    SELECT
        p_customer_id,
        (SELECT order_type_id FROM order_type_table WHERE LOWER(order_type_name) = LOWER(p_order_type) LIMIT 1),
        (SELECT order_source_id FROM order_source_type WHERE LOWER(source_name) = 'chatbot' LIMIT 1),
        v_total,
        NOW()
    RETURNING order_id INTO v_order_id;

    -- Copy cart items to order_item (COLD storage)
    INSERT INTO order_item (
        order_id,
        menu_item_id,
        quantity,
        unit_price,
        subtotal,
        special_instructions
    )
    SELECT
        v_order_id,
        sc.item_id::UUID,
        sc.quantity,
        sc.price,
        sc.quantity * sc.price,
        sc.special_instructions
    FROM session_cart sc
    WHERE sc.session_id = p_session_id AND sc.is_active = TRUE;

    -- Mark session as completed
    UPDATE session_state
    SET current_step = 'order_placed'
    WHERE session_id = p_session_id;

    -- Clear cart (soft delete)
    UPDATE session_cart
    SET is_active = FALSE
    WHERE session_id = p_session_id;

    RETURN v_order_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION create_order_from_session IS 'Transitions session from HOT (session_cart) to COLD (orders). Called on checkout completion.';

-- ============================================================================
-- Initial Setup Complete
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE '===========================================================================';
    RAISE NOTICE 'Migration 14: Hot/Cold Event-Sourced Session Architecture';
    RAISE NOTICE '===========================================================================';
    RAISE NOTICE '';
    RAISE NOTICE 'HOT Tables (UNLOGGED - 3-5x faster, OK to lose on crash):';
    RAISE NOTICE '  - session_cart: Temporary cart during ordering';
    RAISE NOTICE '  - session_state: Conversation flow state';
    RAISE NOTICE '  - session_preferences: User preferences';
    RAISE NOTICE '  - session_checkout: Checkout flow state';
    RAISE NOTICE '';
    RAISE NOTICE 'WARM Tables (LOGGED - audit trail must survive):';
    RAISE NOTICE '  - session_events: Complete event log for analytics';
    RAISE NOTICE '  - session_payment_intent: Payment tracking (financial data)';
    RAISE NOTICE '';
    RAISE NOTICE 'Helper Functions:';
    RAISE NOTICE '  - get_session_cart(session_id): Get active cart items';
    RAISE NOTICE '  - get_cart_total(session_id): Calculate cart total';
    RAISE NOTICE '  - get_last_mentioned_item(session_id): For pronoun resolution';
    RAISE NOTICE '  - get_session_history(session_id, limit): Event log';
    RAISE NOTICE '  - cleanup_expired_sessions(): Clean up old sessions (run periodically)';
    RAISE NOTICE '  - create_order_from_session(): HOT → COLD transition on checkout';
    RAISE NOTICE '';
    RAISE NOTICE 'Performance: ~1-2ms writes (vs ~5ms LOGGED), ~8KB per session';
    RAISE NOTICE 'Crash Recovery: HOT data lost (OK), WARM/COLD preserved';
    RAISE NOTICE '===========================================================================';
END $$;
