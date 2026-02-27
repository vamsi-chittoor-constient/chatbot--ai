#!/bin/bash
# =============================================================================
# Database Initialization Script
# =============================================================================
# Runs all SQL init files in order with error tolerance.
# PetPooja schema dump may have minor INSERT mismatches that are non-fatal
# (tables are created correctly, only some seed data INSERTs may fail).
# Using ON_ERROR_STOP=0 so one bad INSERT doesn't block everything.
# =============================================================================

set -e

echo "=== A24 Database Initialization ==="

for f in /sql-init/*.sql; do
    echo "--- Running: $(basename $f) ---"
    psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$f"
    echo "--- Completed: $(basename $f) ---"
done

echo "=== Database initialization complete ==="
