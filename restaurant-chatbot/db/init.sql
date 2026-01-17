-- =============================================================================
-- Restaurant AI Database Initialization
-- =============================================================================
-- This file sets up the database foundation (extensions, timezone).
--
-- Migration Strategy (Hybrid Approach):
-- - Docker handles: 01-schema.sql, 02-data.sql, 03-app-tables.sql (initial setup)
-- - App handles: 04+ migrations (incremental changes via app/core/migrations.py)
--
-- This approach ensures:
-- - Docker properly initializes complex schema (pg_dump files, multi-statement DDL)
-- - App handles incremental migrations without destroying volumes
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- Note: pgvector extension not included in postgres:15-alpine
-- Install manually if needed: https://github.com/pgvector/pgvector

-- Set timezone
SET timezone = 'UTC';

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Restaurant AI Database Initialized';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Extensions enabled: uuid-ossp, pgcrypto';
    RAISE NOTICE 'Timezone: UTC';
    RAISE NOTICE '';
    RAISE NOTICE 'Initial schema will be loaded by Docker (01-03)';
    RAISE NOTICE 'Incremental migrations handled by app (04+)';
    RAISE NOTICE '========================================';
END $$;
