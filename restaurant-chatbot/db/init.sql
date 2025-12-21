-- =============================================================================
-- Restaurant AI Database Initialization
-- =============================================================================
-- This file is the entry point for PostgreSQL initialization in Docker.
-- It creates the database schema and seeds initial data.
--
-- Files loaded in order:
--   1. 01-schema.sql - Full database schema with all tables
--   2. 02-data.sql   - Restaurant data (menu items, config, etc.)
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'UTC';

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Restaurant AI database initialization starting...';
    RAISE NOTICE 'Schema and data will be loaded from separate SQL files.';
END $$;
