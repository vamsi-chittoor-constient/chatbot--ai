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
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Indexes for fast queries
    INDEX idx_session_events_session_id (session_id),
    INDEX idx_session_events_timestamp (timestamp),
    INDEX idx_session_events_type (event_type),
    INDEX idx_session_events_session_time (session_id, timestamp DESC)
);

COMMENT ON TABLE session_events IS 'Complete event log of all session activity - event sourcing pattern';
COMMENT ON COLUMN session_events.event_type IS 'Event types: item_viewed, item_added, item_removed, item_updated, cart_cleared, checkout_started, order_placed, payment_initiated, etc.';
COMMENT ON COLUMN session_events.event_data IS 'Event-specific data: {item_id, item_name, quantity, price, action, etc.}';

-- ============================================================================
-- SESSION CART - Current cart state (materialized view of add/remove events)
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_cart (
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
    FOREIGN KEY (item_id) REFERENCES menu_item(menu_item_id) ON DELETE CASCADE,

    INDEX idx_session_cart_session_id (session_id),
    INDEX idx_session_cart_active (session_id, is_active)
);

COMMENT ON TABLE session_cart IS 'Current cart state - materialized view updated by add/remove events';
COMMENT ON COLUMN session_cart.is_active IS 'FALSE when removed (soft delete for history), TRUE for current items';

-- ============================================================================
-- SESSION STATE - Conversation context and flow state
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_state (
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

    FOREIGN KEY (user_id) REFERENCES customer(customer_id) ON DELETE SET NULL,
    FOREIGN KEY (last_mentioned_item_id) REFERENCES menu_item(menu_item_id) ON DELETE SET NULL,

    INDEX idx_session_state_last_activity (last_activity_at DESC),
    INDEX idx_session_state_user_id (user_id)
);

COMMENT ON TABLE session_state IS 'Session conversation state and flow tracking - updated by events';
COMMENT ON COLUMN session_state.current_step IS 'Current conversation step: browsing, ordering, awaiting_quantity, checkout, payment';
COMMENT ON COLUMN session_state.awaiting_input_for IS 'What input we are waiting for from user (enables stateful flows)';

-- ============================================================================
-- SESSION PREFERENCES - User preferences expressed during session
-- ============================================================================
CREATE TABLE IF NOT EXISTS session_preferences (
    session_id VARCHAR(255) NOT NULL,
    preference_key VARCHAR(100) NOT NULL,
    preference_value TEXT NOT NULL,
    set_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (session_id, preference_key),
    INDEX idx_session_preferences_session_id (session_id)
);

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
    timestamp TIMESTAMPTZ
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
-- Initial Setup Complete
-- ============================================================================

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Migration 14: Event-sourced session tables created successfully';
    RAISE NOTICE 'Tables: session_events, session_cart, session_state, session_preferences';
    RAISE NOTICE 'Helper functions: get_session_cart, get_cart_total, get_last_mentioned_item, get_session_history';
    RAISE NOTICE 'Cleanup function: cleanup_expired_sessions (run periodically)';
END $$;
