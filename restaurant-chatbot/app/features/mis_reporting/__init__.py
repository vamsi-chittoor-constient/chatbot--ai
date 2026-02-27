"""
MIS Reporting Feature
=====================

Management Information System (MIS) reporting and analytics.

Status: DORMANT (Not implemented yet)
Feature Flag: MIS_REPORTING (always disabled for now)

This folder is a placeholder for future MIS reporting functionality:
- Order analytics and reports
- Revenue forecasting
- Booking statistics
- Customer insights
- Performance dashboards

When implemented, this will include:
- app/features/mis_reporting/services/
- app/features/mis_reporting/models/
- app/features/mis_reporting/crew_agent.py

Current Status: Feature flag is hardcoded to False in feature_flags.py
"""

from app.core.feature_flags import FeatureFlags, Feature

# Check if feature is enabled (will always be False for now)
if not FeatureFlags.is_enabled(Feature.MIS_REPORTING):
    # Feature disabled - export nothing
    __all__ = []
else:
    # Feature enabled - export services (future)
    __all__ = []
