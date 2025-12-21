"""
Simple Knowledge Graph for Menu Items
=======================================
Lightweight relationship tracking WITHOUT complex graph database.

Uses simple PostgreSQL table to store:
- Item-to-item relationships (similar, complement, alternative)
- Auto-learned from order patterns
- Manual chef recommendations

Think: "Butter Chicken → Garlic Naan" (frequently ordered together)
"""

from typing import List, Dict, Any, Optional
from enum import Enum
import structlog
from sqlalchemy import select, and_, func, desc
from datetime import datetime, timedelta

from app.core.database import get_db_session
from app.features.food_ordering.models import Order, OrderItem, MenuItem

logger = structlog.get_logger("services.knowledge_graph")


class RelationshipType(str, Enum):
    """Types of item relationships."""
    SIMILAR = "similar"  # "Butter Chicken" → "Paneer Butter Masala" (similar dish, veg version)
    COMPLEMENT = "complement"  # "Biryani" → "Raita" (goes well together)
    ALTERNATIVE = "alternative"  # "Coke" → "Pepsi" (substitute)
    FREQUENTLY_WITH = "frequently_with"  # Learned from orders: often bought together


class SimpleKnowledgeGraph:
    """
    Manages item relationships for better recommendations.

    NO Neo4j or complex graph DB - just PostgreSQL with smart queries.
    """

    def __init__(self):
        # Common complementary patterns (chef's knowledge)
        self.chef_knowledge = {
            # Curries pair with breads/rice
            'curry': {
                'complements': ['naan', 'garlic naan', 'rice', 'raita', 'papad'],
                'reason': 'Perfect pairing for curries'
            },
            'biryani': {
                'complements': ['raita', 'pickle', 'papad', 'curd'],
                'reason': 'Traditional biryani sides'
            },
            'dosa': {
                'complements': ['sambar', 'chutney', 'vada', 'coffee'],
                'reason': 'South Indian combo'
            },
            'idli': {
                'complements': ['sambar', 'chutney', 'vada', 'coffee'],
                'reason': 'Breakfast staple pairing'
            },
            'pizza': {
                'complements': ['garlic bread', 'coke', 'pepsi', 'sprite'],
                'reason': 'Classic pizza combo'
            },
            'pasta': {
                'complements': ['garlic bread', 'soup', 'salad'],
                'reason': 'Italian meal pairing'
            },
            'burger': {
                'complements': ['fries', 'coke', 'pepsi', 'coleslaw'],
                'reason': 'Fast food combo'
            }
        }

    async def find_complementary_items(
        self,
        item_names: List[str],
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find items that complement the given items.

        Args:
            item_names: List of item names in cart
            limit: Max complementary items to return

        Returns:
            List of complementary items with reasons
        """
        try:
            complement_keywords = []

            # Extract complementary keywords from chef knowledge
            for item_name in item_names:
                item_lower = item_name.lower()
                for keyword, data in self.chef_knowledge.items():
                    if keyword in item_lower:
                        complement_keywords.extend(data['complements'])

            if not complement_keywords:
                return []

            # Search database for these items
            async with get_db_session() as session:
                from sqlalchemy import or_
                search_conditions = [
                    MenuItem.menu_item_name.ilike(f'%{keyword}%')
                    for keyword in complement_keywords
                ]

                query = select(MenuItem).where(
                    and_(
                        or_(*search_conditions),
                        MenuItem.menu_item_in_stock == True,
                        MenuItem.menu_item_status == 'active'
                    )
                ).limit(limit)

                result = await session.execute(query)
                items = result.scalars().all()

                complements = []
                for item in items:
                    complements.append({
                        'id': str(item.menu_item_id),
                        'name': item.menu_item_name,
                        'price': float(item.menu_item_price),
                        'description': item.menu_item_description or '',
                        'relationship': 'complement',
                        'reason': self._get_complement_reason(item.menu_item_name, item_names)
                    })

                logger.info(
                    "Found complementary items",
                    input_items=len(item_names),
                    complements_found=len(complements)
                )

                return complements

        except Exception as e:
            logger.error(
                "Failed to find complementary items",
                error=str(e),
                exc_info=True
            )
            return []

    def _get_complement_reason(self, complement_name: str, cart_items: List[str]) -> str:
        """Generate reason why item complements cart items."""
        complement_lower = complement_name.lower()

        # Check which cart item triggered this complement
        for cart_item in cart_items:
            cart_lower = cart_item.lower()
            for keyword, data in self.chef_knowledge.items():
                if keyword in cart_lower:
                    if any(comp in complement_lower for comp in data['complements']):
                        return data['reason']

        return "Goes well together"

    async def learn_from_orders(
        self,
        days_to_analyze: int = 30,
        min_co_occurrence: int = 5
    ) -> Dict[str, Any]:
        """
        Learn frequent item pairings from past orders.

        Analyzes: "What items are frequently ordered together?"

        Args:
            days_to_analyze: Look back this many days
            min_co_occurrence: Minimum times items must appear together

        Returns:
            Statistics about learned relationships
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_analyze)

            async with get_db_session() as session:
                # Query to find item pairs in same order
                # This is a simplified approach using SQLAlchemy
                query = select(
                    OrderItem.menu_item_id.label('item1_id'),
                    MenuItem.menu_item_name.label('item1_name'),
                    func.count(Order.id).label('pair_count')
                ).join(
                    Order,
                    OrderItem.order_id == Order.id
                ).join(
                    MenuItem,
                    OrderItem.menu_item_id == MenuItem.menu_item_id
                ).where(
                    Order.created_at >= cutoff_date,
                    Order.status.in_(['confirmed', 'preparing', 'ready'])
                ).group_by(
                    OrderItem.menu_item_id,
                    MenuItem.menu_item_name
                ).having(
                    func.count(Order.id) >= min_co_occurrence
                ).order_by(
                    desc(func.count(Order.id))
                ).limit(50)

                result = await session.execute(query)
                frequent_items = result.fetchall()

                logger.info(
                    "Learned frequent item patterns",
                    days_analyzed=days_to_analyze,
                    patterns_found=len(frequent_items),
                    min_occurrences=min_co_occurrence
                )

                return {
                    'patterns_found': len(frequent_items),
                    'days_analyzed': days_to_analyze,
                    'sample_patterns': [
                        {
                            'item': row.item1_name,
                            'frequency': row.pair_count
                        }
                        for row in frequent_items[:5]
                    ]
                }

        except Exception as e:
            logger.error(
                "Failed to learn from orders",
                error=str(e),
                exc_info=True
            )
            return {'patterns_found': 0}

    async def find_similar_items(
        self,
        item_id: str,
        same_category: bool = True,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find items similar to given item.

        Args:
            item_id: Item to find similarities for
            same_category: Limit to same category
            limit: Max similar items

        Returns:
            List of similar items
        """
        try:
            async with get_db_session() as session:
                # Get original item details
                item_query = select(MenuItem).where(
                    MenuItem.menu_item_id == item_id
                )
                item_result = await session.execute(item_query)
                original_item = item_result.scalar_one_or_none()

                if not original_item:
                    return []

                # Find similar items (same category, similar price range)
                from app.features.food_ordering.models import MenuItemCategoryMapping
                query = select(MenuItem).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                )

                if same_category:
                    # Get original item's category
                    cat_query = select(MenuItemCategoryMapping.menu_category_id).where(
                        and_(
                            MenuItemCategoryMapping.menu_item_id == item_id,
                            MenuItemCategoryMapping.is_primary == True
                        )
                    )
                    cat_result = await session.execute(cat_query)
                    original_category = cat_result.scalar_one_or_none()

                    if original_category:
                        query = query.where(
                            MenuItemCategoryMapping.menu_category_id == original_category
                        )

                # Similar price range (±30%)
                price = float(original_item.menu_item_price)
                price_min = price * 0.7
                price_max = price * 1.3

                query = query.where(
                    and_(
                        MenuItem.menu_item_id != item_id,  # Not the same item
                        MenuItem.menu_item_price >= price_min,
                        MenuItem.menu_item_price <= price_max,
                        MenuItem.menu_item_in_stock == True,
                        MenuItem.menu_item_status == 'active',
                        MenuItemCategoryMapping.is_primary == True
                    )
                ).limit(limit)

                result = await session.execute(query)
                items = result.scalars().all()

                similar = []
                for item in items:
                    similar.append({
                        'id': str(item.menu_item_id),
                        'name': item.menu_item_name,
                        'price': float(item.menu_item_price),
                        'description': item.menu_item_description or '',
                        'relationship': 'similar',
                        'reason': 'Similar price and category'
                    })

                return similar

        except Exception as e:
            logger.error(
                "Failed to find similar items",
                error=str(e),
                exc_info=True
            )
            return []


# Global singleton
_knowledge_graph = None


def get_knowledge_graph() -> SimpleKnowledgeGraph:
    """Get global knowledge graph instance."""
    global _knowledge_graph
    if _knowledge_graph is None:
        _knowledge_graph = SimpleKnowledgeGraph()
    return _knowledge_graph


__all__ = ["SimpleKnowledgeGraph", "get_knowledge_graph", "RelationshipType"]
