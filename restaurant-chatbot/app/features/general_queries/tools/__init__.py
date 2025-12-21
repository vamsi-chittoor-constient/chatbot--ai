"""
General Queries Tools
====================
Tools for FAQ, policy, restaurant info, and analytics.
"""

from app.features.general_queries.tools.faq_tools import (
    search_faq,
    get_faq_by_id,
    get_featured_faqs,
    get_faqs_by_category
)

from app.features.general_queries.tools.policy_tools import (
    search_policies,
    get_policy_by_type,
    get_all_policies
)

from app.features.general_queries.tools.restaurant_tools import (
    get_restaurant_info,
    get_business_hours,
    get_location_info,
    get_contact_info,
    get_parking_info
)

from app.features.general_queries.tools.analytics_tools import (
    track_query,
    update_faq_satisfaction,
    get_query_statistics
)

__all__ = [
    # FAQ tools
    "search_faq",
    "get_faq_by_id",
    "get_featured_faqs",
    "get_faqs_by_category",
    
    # Policy tools
    "search_policies",
    "get_policy_by_type",
    "get_all_policies",
    
    # Restaurant tools
    "get_restaurant_info",
    "get_business_hours",
    "get_location_info",
    "get_contact_info",
    "get_parking_info",
    
    # Analytics tools
    "track_query",
    "update_faq_satisfaction",
    "get_query_statistics"
]
