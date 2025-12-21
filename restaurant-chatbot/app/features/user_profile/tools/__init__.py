"""
User Profile Tools
=================
Tools for preferences, favorites, and history management.
"""

from app.features.user_profile.tools.preference_tools import (
    get_user_preferences,
    update_dietary_restrictions,
    update_allergies,
    update_favorite_cuisines,
    update_spice_level,
    update_preferred_seating
)

from app.features.user_profile.tools.favorite_tools import (
    add_to_favorites,
    remove_from_favorites,
    get_user_favorites
)

from app.features.user_profile.tools.history_tools import (
    get_order_history,
    get_booking_history,
    get_browsing_history,
    reorder_from_history
)

__all__ = [
    # Preference tools
    "get_user_preferences",
    "update_dietary_restrictions",
    "update_allergies",
    "update_favorite_cuisines",
    "update_spice_level",
    "update_preferred_seating",
    
    # Favorite tools
    "add_to_favorites",
    "remove_from_favorites",
    "get_user_favorites",
    
    # History tools
    "get_order_history",
    "get_booking_history",
    "get_browsing_history",
    "reorder_from_history"
]
