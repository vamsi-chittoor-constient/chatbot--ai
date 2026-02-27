"""
Context Recommendation Engine
===============================
Lightweight, relatable contextual recommendations.

Simple factors (NO heavy stuff like weather/GPS):
- Time of day (breakfast/lunch/dinner)
- Past orders (what they liked before)
- Current cart (what pairs well)
- Popular items (crowd favorites)

Think like a real waiter: "Hey, people usually order naan with that curry!"
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, time
import structlog
from sqlalchemy import select, func, and_

from app.core.database import get_db_session
from app.features.food_ordering.models import MenuItem, Order, OrderItem, MenuCategory, MenuItemCategoryMapping

logger = structlog.get_logger("services.context_recommendations")


class ContextRecommendationEngine:
    """
    Simple, practical recommendation engine.

    Like a friendly waiter who knows:
    - What time it is (breakfast vs dinner)
    - What you ordered before
    - What goes well together
    """

    def __init__(self):
        self.time_based_categories = {
            'breakfast': ['breakfast', 'beverages', 'coffee', 'tea'],
            'lunch': ['appetizers', 'main course', 'salads', 'beverages'],
            'dinner': ['appetizers', 'main course', 'desserts', 'beverages'],
            'late_night': ['snacks', 'beverages', 'desserts']
        }

        # Common item pairings (what goes together)
        # Like a waiter saying "Want some naan with that curry?"
        self.common_pairings = {
            'curry': ['naan', 'rice', 'raita', 'papad'],
            'biryani': ['raita', 'pickle', 'papad', 'curd'],
            'pizza': ['garlic bread', 'soft drink', 'salad'],
            'pasta': ['garlic bread', 'soup', 'salad'],
            'burger': ['fries', 'soft drink', 'coleslaw'],
            'sandwich': ['chips', 'soup', 'soft drink'],
            'rice': ['curry', 'dal', 'sambar', 'pickle'],
            'dosa': ['sambar', 'chutney', 'coffee', 'filter coffee'],
            'idli': ['sambar', 'chutney', 'vada', 'coffee']
        }

    def get_current_meal_time(self) -> str:
        """
        Determine current meal time.
        Simple time-based logic.
        """
        current_hour = datetime.now().hour

        if 6 <= current_hour < 11:
            return 'breakfast'
        elif 11 <= current_hour < 16:
            return 'lunch'
        elif 16 <= current_hour < 23:
            return 'dinner'
        else:
            return 'late_night'

    async def get_contextual_recommendations(
        self,
        user_id: Optional[str] = None,
        cart_items: Optional[List[Dict[str, Any]]] = None,
        limit: int = 5
    ) -> Dict[str, Any]:
        """
        Get contextual recommendations based on simple, relatable factors.

        Args:
            user_id: User ID (for past order history)
            cart_items: Current cart items (for pairing suggestions)
            limit: Max recommendations

        Returns:
            {
                'recommendations': [...],
                'reasons': [...],
                'context': {...}
            }
        """
        try:
            meal_time = self.get_current_meal_time()
            recommendations = []
            reasons = []

            logger.info(
                "Generating contextual recommendations",
                user_id=user_id,
                meal_time=meal_time,
                cart_items_count=len(cart_items) if cart_items else 0
            )

            # Factor 1: Cart-based pairing suggestions (highest priority)
            if cart_items and len(cart_items) > 0:
                pairing_recs = await self._get_pairing_recommendations(
                    cart_items, limit=3
                )
                if pairing_recs:
                    recommendations.extend(pairing_recs)
                    reasons.append(
                        f"These items pair perfectly with what's in your cart"
                    )

            # Factor 2: Past order favorites (if user is logged in)
            if user_id and len(recommendations) < limit:
                past_fav_recs = await self._get_past_favorites(
                    user_id, limit=2
                )
                if past_fav_recs:
                    recommendations.extend(past_fav_recs)
                    reasons.append(
                        "You loved these before!"
                    )

            # Factor 3: Time-based popular items
            if len(recommendations) < limit:
                popular_recs = await self._get_popular_for_time(
                    meal_time, limit=limit - len(recommendations)
                )
                if popular_recs:
                    recommendations.extend(popular_recs)
                    reasons.append(
                        f"Popular choices for {meal_time}"
                    )

            # Deduplicate (don't recommend what's already in cart)
            if cart_items:
                cart_item_ids = {item.get('id') for item in cart_items}
                recommendations = [
                    rec for rec in recommendations
                    if rec.get('id') not in cart_item_ids
                ]

            # Limit to requested count
            recommendations = recommendations[:limit]

            logger.info(
                "Context recommendations generated",
                user_id=user_id,
                count=len(recommendations),
                factors_used=len(reasons)
            )

            return {
                'recommendations': recommendations,
                'reasons': reasons,
                'context': {
                    'meal_time': meal_time,
                    'has_cart_items': bool(cart_items),
                    'is_returning_customer': bool(user_id)
                }
            }

        except Exception as e:
            logger.error(
                "Failed to generate context recommendations",
                error=str(e),
                exc_info=True
            )
            return {
                'recommendations': [],
                'reasons': [],
                'context': {}
            }

    async def _get_pairing_recommendations(
        self,
        cart_items: List[Dict[str, Any]],
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Suggest items that pair well with what's in the cart.

        Like a waiter: "Want some garlic naan with that butter chicken?"
        """
        pairing_items = []

        # Extract item names from cart
        cart_item_names = [
            item.get('name', '').lower() for item in cart_items
        ]

        # Find pairings based on keywords in cart items
        for cart_name in cart_item_names:
            for keyword, pairings in self.common_pairings.items():
                if keyword in cart_name:
                    pairing_items.extend(pairings)

        if not pairing_items:
            return []

        # Search database for these pairing items
        async with get_db_session() as session:
            # Build search conditions for pairing items
            search_conditions = [
                MenuItem.menu_item_name.ilike(f'%{item}%')
                for item in pairing_items
            ]

            if not search_conditions:
                return []

            from sqlalchemy import or_
            query = select(
                MenuItem,
                MenuCategory.menu_category_name
            ).join(
                MenuItemCategoryMapping,
                MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
            ).join(
                MenuCategory,
                MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
            ).where(
                and_(
                    or_(*search_conditions),
                    MenuItem.menu_item_in_stock == True,
                    MenuItem.menu_item_status == 'active',
                    MenuItemCategoryMapping.is_primary == True
                )
            ).limit(limit)

            result = await session.execute(query)
            items = result.fetchall()

            recommendations = []
            for item, category_name in items:
                recommendations.append({
                    'id': str(item.menu_item_id),
                    'name': item.menu_item_name,
                    'description': item.menu_item_description or '',
                    'price': float(item.menu_item_price),
                    'category': category_name,
                    'reason': 'Pairs well with your selection'
                })

            return recommendations

    async def _get_past_favorites(
        self,
        user_id: str,
        limit: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get items user ordered before and loved.

        Like: "You always order the chicken biryani!"
        """
        try:
            async with get_db_session() as session:
                # Find items this user ordered multiple times
                query = select(
                    MenuItem,
                    MenuCategory.menu_category_name,
                    func.count(OrderItem.id).label('order_count')
                ).join(
                    OrderItem,
                    MenuItem.menu_item_id == OrderItem.menu_item_id
                ).join(
                    Order,
                    OrderItem.order_id == Order.id
                ).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                ).join(
                    MenuCategory,
                    MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                ).where(
                    and_(
                        Order.user_id == user_id,
                        MenuItem.menu_item_in_stock == True,
                        MenuItem.menu_item_status == 'active',
                        MenuItemCategoryMapping.is_primary == True
                    )
                ).group_by(
                    MenuItem.menu_item_id,
                    MenuCategory.menu_category_name
                ).order_by(
                    func.count(OrderItem.id).desc()  # Most ordered first
                ).limit(limit)

                result = await session.execute(query)
                items = result.fetchall()

                recommendations = []
                for item, category_name, order_count in items:
                    recommendations.append({
                        'id': str(item.menu_item_id),
                        'name': item.menu_item_name,
                        'description': item.menu_item_description or '',
                        'price': float(item.menu_item_price),
                        'category': category_name,
                        'reason': f'You ordered this {order_count} times before!'
                    })

                return recommendations

        except Exception as e:
            logger.warning(
                "Failed to get past favorites",
                user_id=user_id,
                error=str(e)
            )
            return []

    async def _get_popular_for_time(
        self,
        meal_time: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Get popular items for current time of day.

        Like: "The pancakes are really popular for breakfast!"
        """
        try:
            # Get categories for this meal time
            relevant_categories = self.time_based_categories.get(
                meal_time, ['main course', 'beverages']
            )

            async with get_db_session() as session:
                # Get popular items from relevant categories
                query = select(
                    MenuItem,
                    MenuCategory.menu_category_name
                ).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                ).join(
                    MenuCategory,
                    MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                ).where(
                    and_(
                        MenuItem.menu_item_in_stock == True,
                        MenuItem.menu_item_status == 'active',
                        MenuItem.menu_item_favorite == True,  # Popular items
                        MenuItemCategoryMapping.is_primary == True,
                        MenuCategory.menu_category_name.in_(relevant_categories)
                    )
                ).order_by(
                    MenuItem.menu_item_name
                ).limit(limit)

                result = await session.execute(query)
                items = result.fetchall()

                recommendations = []
                for item, category_name in items:
                    recommendations.append({
                        'id': str(item.menu_item_id),
                        'name': item.menu_item_name,
                        'description': item.menu_item_description or '',
                        'price': float(item.menu_item_price),
                        'category': category_name,
                        'reason': f'Crowd favorite for {meal_time}'
                    })

                return recommendations

        except Exception as e:
            logger.warning(
                "Failed to get popular items",
                meal_time=meal_time,
                error=str(e)
            )
            return []


# Global singleton
_recommendation_engine = None


def get_recommendation_engine() -> ContextRecommendationEngine:
    """Get global recommendation engine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = ContextRecommendationEngine()
    return _recommendation_engine


__all__ = ["ContextRecommendationEngine", "get_recommendation_engine"]
