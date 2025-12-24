"""
Complaints Module Feature
==========================

Customer complaints and feedback management system.

Status: DORMANT (Not implemented yet)
Feature Flag: COMPLAINTS_MODULE (always disabled for now)

This folder is a placeholder for future complaints management functionality:
- Complaint registration
- Issue tracking and resolution
- Feedback collection
- Customer satisfaction surveys
- Escalation workflows

When implemented, this will include:
- app/features/complaints/services/
- app/features/complaints/models/
- app/features/complaints/crew_agent.py

Current Status: Feature flag is hardcoded to False in feature_flags.py
"""

from app.core.feature_flags import FeatureFlags, Feature

# Check if feature is enabled (will always be False for now)
if not FeatureFlags.is_enabled(Feature.COMPLAINTS_MODULE):
    # Feature disabled - export nothing
    __all__ = []
else:
    # Feature enabled - export services (future)
    __all__ = []
