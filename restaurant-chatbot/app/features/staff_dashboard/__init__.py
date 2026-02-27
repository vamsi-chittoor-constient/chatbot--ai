"""
Staff Dashboard Feature
========================

Staff management interface for restaurant operations.

Status: DORMANT (Not implemented yet)
Feature Flag: STAFF_DASHBOARD (always disabled for now)

This folder is a placeholder for future staff dashboard functionality:
- Front desk operations
- Manager controls
- Housekeeping coordination
- Staff task management
- Real-time status updates

When implemented, this will include:
- app/features/staff_dashboard/services/
- app/features/staff_dashboard/models/
- app/features/staff_dashboard/crew_agent.py

Current Status: Feature flag is hardcoded to False in feature_flags.py
"""

from app.core.feature_flags import FeatureFlags, Feature

# Check if feature is enabled (will always be False for now)
if not FeatureFlags.is_enabled(Feature.STAFF_DASHBOARD):
    # Feature disabled - export nothing
    __all__ = []
else:
    # Feature enabled - export services (future)
    __all__ = []
