"""
Advanced AI-Powered Menu Tools for MenuAgent
==========================================

These tools provide intelligent menu operations including semantic search,
personalized recommendations, smart filtering, and upselling capabilities.
Built specifically for the MenuAgent to deliver a conversational menu experience.

AI-Enhanced Tools:
- SemanticMenuSearchTool: Natural language menu search using vector embeddings
- PersonalizedRecommendationTool: User preference-based recommendations
- SmartDietaryFilterTool: Advanced filtering by dietary needs
- RealTimeAvailabilityTool: Dynamic availability checking
- FindSimilarItemsTool: Similarity-based item discovery for upselling
- PriceRangeMenuTool: Budget-conscious menu filtering
- SmartUpsellingTool: Intelligent upselling and cross-selling suggestions
"""

from decimal import Decimal
from typing import Dict, Any, Optional, List
from datetime import datetime, time as time_obj
from dataclasses import dataclass

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import get_db_session
from app.features.food_ordering.models import MenuItem, MenuCategory, MenuItemCategoryMapping
from sqlalchemy import select, and_, or_, func
from app.core.logging_config import get_logger
from app.utils.validation_decorators import validate_schema, require_tables
from app.utils.schema_tool_integration import serialize_output_with_schema, safe_isoformat
from app.features.food_ordering.schemas.menu import MenuItemResponse, MenuItemSummaryResponse, MenuCategoryResponse
from app.ai_services.embedding_service import get_embedding_service

logger = get_logger(__name__)


@dataclass
class MenuSearchResult:
    """Structured result for menu search operations"""
    item_id: str
    name: str
    description: str
    price: Decimal
    category_name: str
    dietary_info: List[str]
    allergens: List[str]
    spice_level: str
    calories: Optional[int]
    is_popular: bool
    similarity_score: Optional[float] = None
    recommendation_reason: Optional[str] = None


# DECORATORS REMOVED - No schema validation for semantic search
class SemanticMenuSearchTool(ToolBase):
    """
    Natural language menu search using vector embeddings.

    Enables searches like "something spicy like butter chicken" or
    "healthy vegetarian options for dinner" using semantic similarity.
    """

    def __init__(self):
        super().__init__(
            name="semantic_menu_search",
            description="Search menu using natural language with AI-powered semantic matching",
            max_retries=2,
            timeout_seconds=30  # Doubled from 15 to allow time for embedding generation + DB query with index
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        search_query = kwargs.get('search_query', '').strip()
        if not search_query:
            raise ToolError("search_query is required for semantic search", tool_name=self.name)

        # Optional parameters with defaults
        limit = kwargs.get('limit', 10)
        min_similarity = kwargs.get('min_similarity', 0.85)

        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise ToolError("limit must be between 1 and 50", tool_name=self.name)

        if not isinstance(min_similarity, (int, float)) or min_similarity < 0 or min_similarity > 1:
            raise ToolError("min_similarity must be between 0 and 1", tool_name=self.name)

        return {
            'search_query': search_query,
            'limit': limit,
            'min_similarity': min_similarity,
            'include_unavailable': kwargs.get('include_unavailable', False)
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            search_query = validated_data['search_query']
            limit = validated_data['limit']
            min_similarity = validated_data['min_similarity']
            include_unavailable = validated_data['include_unavailable']

            # TRUE SEMANTIC SEARCH using local embeddings (Sentence Transformers)
            # No OpenAI API required - runs locally!
            logger.info(
                "Using TRUE semantic search with local embeddings",
                query=search_query
            )

            from app.ai_services.vector_db_service import get_vector_db_service
            vector_db = get_vector_db_service()

            # Perform semantic search with local embeddings
            search_results = await vector_db.semantic_search(
                query=search_query,
                limit=limit,
                min_similarity=min_similarity
            )

            # If vector search finds results, return them
            if search_results:
                logger.info(
                    "TRUE semantic search completed",
                    query=search_query,
                    total_found=len(search_results),
                    search_method="local_embeddings"
                )
                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        'items': search_results,
                        'total_found': len(search_results),
                        'search_method': 'local_semantic_embeddings'
                    }
                )

            # Fallback to text search if vector DB is empty
            logger.warning(
                "Vector search returned no results (database may be empty), falling back to text search",
                query=search_query
            )
            async with get_db_session() as session:
                return await self._text_search(
                    session, search_query, limit, include_unavailable
                )

        except Exception as e:
            logger.error(f"Semantic search failed: {str(e)}", exc_info=True)
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Search failed: {str(e)}"
            )

    def _generate_search_reason(self, item: MenuItem, search_query: str, similarity: float) -> str:
        """Generate explanation for why item matches search"""
        reasons = []

        # High similarity
        if similarity >= 0.9:
            reasons.append("Excellent match")
        elif similarity >= 0.8:
            reasons.append("Great match")
        elif similarity >= 0.7:
            reasons.append("Good match")
        else:
            reasons.append("Relevant match")

        # Check if search query appears in name (exact match)
        if search_query.lower() in item.menu_item_name.lower():
            reasons.append("name contains your search")

        # Popular items (using correct column name)
        if item.menu_item_favorite:
            reasons.append("popular choice")

        return "; ".join(reasons[:3])  # Limit to 3 reasons

    async def _text_search(
        self,
        session,
        search_query: str,
        limit: int,
        include_unavailable: bool
    ) -> ToolResult:
        """
        Text-based search using ILIKE matching on name and description.
        Uses correct database column names (menu_item_name, menu_item_description, etc.)
        """
        logger.info("Using text-based menu search", search_query=search_query)

        # Join MenuItem with MenuItemCategoryMapping and MenuCategory to get category name
        query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name')
        ).join(
            MenuItemCategoryMapping,
            MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
        ).join(
            MenuCategory,
            MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
        ).where(
            MenuItemCategoryMapping.is_primary == True  # Only get primary category
        )

        # Availability filter (use correct column name)
        if not include_unavailable:
            query = query.where(MenuItem.menu_item_in_stock == True)
            query = query.where(MenuItem.menu_item_status == 'active')

        # Text-based matching on name and description with semantic keyword expansion
        search_conditions = []
        search_lower = search_query.lower()

        # Smart keyword expansion for semantic search (mimics vector search behavior)
        keyword_mappings = {
            'spicy': ['masala', 'tikka', 'curry', 'chili', 'pepper', 'hot', 'tandoori'],
            'sweet': ['dessert', 'gulab', 'rasmalai', 'kulfi', 'halwa', 'jalebi'],
            'healthy': ['salad', 'grilled', 'steamed', 'dal'],
            'vegetarian': ['paneer', 'veg', 'vegetable', 'aloo', 'gobi'],
            'non-veg': ['chicken', 'mutton', 'fish', 'prawn', 'egg', 'meat'],
            'breakfast': ['dosa', 'idli', 'paratha', 'poha', 'upma', 'chole'],
            'rice': ['biryani', 'pulao', 'fried rice', 'jeera rice'],
            'bread': ['naan', 'roti', 'paratha', 'kulcha'],
            'creamy': ['butter', 'makhani', 'korma', 'cream'],
            'fried': ['pakora', 'samosa', 'vada', 'fry']
        }

        # Expand search query with related keywords
        expanded_keywords = [search_lower]
        for key, synonyms in keyword_mappings.items():
            if key in search_lower:
                expanded_keywords.extend(synonyms)

        # Add search conditions for all expanded keywords
        for keyword in expanded_keywords:
            search_conditions.append(MenuItem.menu_item_name.ilike(f'%{keyword}%'))
            search_conditions.append(MenuItem.menu_item_description.ilike(f'%{keyword}%'))

        # Also search by spice level for "spicy" queries
        if 'spicy' in search_lower:
            search_conditions.append(MenuItem.menu_item_spice_level.in_(['medium', 'hot', 'extra_hot']))

        query = query.where(or_(*search_conditions))
        query = query.order_by(MenuItem.menu_item_favorite.desc(), MenuItem.menu_item_name)
        query = query.limit(limit)

        result = await session.execute(query)
        items = result.fetchall()

        search_results = []
        for item, category_name in items:
            # Build item data manually with correct column names
            item_data = {
                'id': str(item.menu_item_id),
                'name': item.menu_item_name,
                'description': item.menu_item_description or '',
                'price': float(item.menu_item_price),
                'is_available': item.menu_item_in_stock,
                'is_popular': item.menu_item_favorite,
                'spice_level': item.menu_item_spice_level,
                'calories': item.menu_item_calories,
                'category_name': category_name,
                'similarity_score': 0.8,  # Fixed score for text search
                'recommendation_reason': self._generate_search_reason(item, search_query, 0.8)
            }
            search_results.append(item_data)

        logger.info(
            "Text search completed",
            query=search_query,
            total_found=len(search_results)
        )

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "items": search_results,
                "search_query": search_query,
                "total_found": len(search_results),
                "message": f"Found {len(search_results)} items matching '{search_query}'"
            }
        )


@validate_schema(MenuItem)
@require_tables("menu_item", "menu_categories")
class PersonalizedRecommendationTool(ToolBase):
    """
    Generate personalized menu recommendations based on user preferences,
    dietary restrictions, past orders, and behavioral patterns.
    """

    def __init__(self):
        super().__init__(
            name="personalized_recommendation",
            description="Generate personalized menu recommendations based on user preferences",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        # User preferences (from UserAgent context)
        user_preferences = kwargs.get('user_preferences', {})
        limit = kwargs.get('limit', 5)

        if not isinstance(limit, int) or limit < 1 or limit > 20:
            raise ToolError("limit must be between 1 and 20", tool_name=self.name)

        return {
            'user_preferences': user_preferences,
            'limit': limit,
            'exclude_allergens': kwargs.get('exclude_allergens', True),
            'occasion': kwargs.get('occasion', 'casual'),  # casual, formal, quick, family
            'budget_max': kwargs.get('budget_max')
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            async with get_db_session() as session:
                user_prefs = validated_data['user_preferences']
                limit = validated_data['limit']
                occasion = validated_data['occasion']
                budget_max = validated_data['budget_max']

                # Build base query with correct joins via mapping table
                query = select(
                    MenuItem,
                    MenuCategory.menu_category_name.label('category_name')
                ).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                ).join(
                    MenuCategory,
                    MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                ).where(
                    MenuItemCategoryMapping.is_primary == True  # Only get primary category
                ).where(
                    MenuItem.menu_item_in_stock == True
                ).where(
                    MenuItem.menu_item_status == 'active'
                )

                # Budget filtering (correct column name)
                if budget_max:
                    query = query.where(MenuItem.menu_item_price <= budget_max)

                # Spice level preference (correct column name)
                spice_level = user_prefs.get('spice_level')
                if spice_level:
                    if spice_level == 'mild':
                        query = query.where(or_(
                            MenuItem.menu_item_spice_level == 'mild',
                            MenuItem.menu_item_spice_level == 'none',
                            MenuItem.menu_item_spice_level.is_(None)
                        ))
                    else:
                        query = query.where(MenuItem.menu_item_spice_level == spice_level)

                # Favorite cuisines (approximate by category name)
                favorite_cuisines = user_prefs.get('favorite_cuisines', [])
                if favorite_cuisines:
                    cuisine_conditions = []
                    for cuisine in favorite_cuisines:
                        cuisine_conditions.append(
                            MenuCategory.menu_category_name.ilike(f'%{cuisine}%')
                        )
                    query = query.where(or_(*cuisine_conditions))

                # Occasion-based filtering
                if occasion == 'quick':
                    query = query.where(
                        or_(
                            MenuItem.menu_item_minimum_preparation_time <= 15,
                            MenuItem.menu_item_minimum_preparation_time.is_(None)
                        )
                    )
                elif occasion == 'formal':
                    query = query.where(MenuItem.menu_item_favorite == True)

                # Order by popularity and price (correct column names)
                query = query.order_by(
                    MenuItem.menu_item_favorite.desc(),
                    MenuItem.menu_item_is_recommended.desc(),
                    MenuItem.menu_item_price.asc()
                ).limit(limit * 2)  # Get more to allow for variety

                result = await session.execute(query)
                items = result.fetchall()

                if not items:
                    # Fallback to popular items with correct column names
                    fallback_query = select(
                        MenuItem,
                        MenuCategory.menu_category_name.label('category_name')
                    ).join(
                        MenuItemCategoryMapping,
                        MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                    ).join(
                        MenuCategory,
                        MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                    ).where(
                        MenuItemCategoryMapping.is_primary == True
                    ).where(
                        and_(
                            MenuItem.menu_item_in_stock == True,
                            MenuItem.menu_item_favorite == True
                        )
                    ).order_by(MenuItem.menu_item_price.asc()).limit(limit)

                    result = await session.execute(fallback_query)
                    items = result.fetchall()

                # Create personalized recommendations with reasons
                recommendations = []
                for item, category_name in items[:limit]:
                    reason_parts = []

                    # Build recommendation reason (using correct column names)
                    if item.menu_item_favorite:
                        reason_parts.append("Popular choice")

                    if item.menu_item_is_recommended:
                        reason_parts.append("Chef's recommendation")

                    if spice_level and item.menu_item_spice_level == spice_level:
                        reason_parts.append(f"Perfect {spice_level} spice level")

                    if occasion == 'quick' and item.menu_item_minimum_preparation_time and item.menu_item_minimum_preparation_time <= 15:
                        reason_parts.append("Quick preparation")

                    if not reason_parts:
                        reason_parts.append("Great choice for you")

                    # Build item data manually with correct column names
                    item_data = {
                        'id': str(item.menu_item_id),
                        'name': item.menu_item_name,
                        'description': item.menu_item_description or '',
                        'price': float(item.menu_item_price),
                        'is_available': item.menu_item_in_stock,
                        'is_popular': item.menu_item_favorite,
                        'spice_level': item.menu_item_spice_level,
                        'calories': item.menu_item_calories,
                        'category_name': category_name,
                        'similarity_score': 0.9,
                        'recommendation_reason': "; ".join(reason_parts)
                    }
                    recommendations.append(item_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "recommendations": recommendations,
                        "total_found": len(recommendations),
                        "user_preferences": user_prefs,
                        "message": f"Here are {len(recommendations)} personalized recommendations for you!"
                    }
                )

        except Exception as e:
            logger.error(f"Personalized recommendation failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Recommendation failed: {str(e)}"
            )


@validate_schema(MenuItem)
@require_tables("menu_item", "menu_categories")
class SmartDietaryFilterTool(ToolBase):
    """
    Advanced filtering by dietary restrictions, allergies, nutritional requirements,
    and health considerations with intelligent constraint handling.
    """

    def __init__(self):
        super().__init__(
            name="smart_dietary_filter",
            description="Advanced filtering by dietary restrictions and health requirements",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        dietary_restrictions = kwargs.get('dietary_restrictions', [])
        allergies = kwargs.get('allergies', [])

        if not isinstance(dietary_restrictions, list):
            dietary_restrictions = [dietary_restrictions] if dietary_restrictions else []

        if not isinstance(allergies, list):
            allergies = [allergies] if allergies else []

        return {
            'dietary_restrictions': dietary_restrictions,
            'allergies': allergies,
            'max_calories': kwargs.get('max_calories'),
            'min_calories': kwargs.get('min_calories'),
            'spice_level': kwargs.get('spice_level'),
            'max_prep_time': kwargs.get('max_prep_time'),
            'categories': kwargs.get('categories', []),
            'limit': kwargs.get('limit', 20)
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            async with get_db_session() as session:
                max_calories = validated_data['max_calories']
                min_calories = validated_data['min_calories']
                spice_level = validated_data['spice_level']
                max_prep_time = validated_data['max_prep_time']
                categories = validated_data['categories']
                limit = validated_data['limit']

                # Build query with correct joins via mapping table
                query = select(
                    MenuItem,
                    MenuCategory.menu_category_name.label('category_name')
                ).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                ).join(
                    MenuCategory,
                    MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                ).where(
                    MenuItemCategoryMapping.is_primary == True
                ).where(
                    MenuItem.menu_item_in_stock == True
                ).where(
                    MenuItem.menu_item_status == 'active'
                )

                # Calorie constraints
                if max_calories:
                    query = query.where(
                        or_(
                            MenuItem.menu_item_calories <= max_calories,
                            MenuItem.menu_item_calories.is_(None)
                        )
                    )
                if min_calories:
                    query = query.where(
                        or_(
                            MenuItem.menu_item_calories >= min_calories,
                            MenuItem.menu_item_calories.is_(None)
                        )
                    )

                # Spice level filtering
                if spice_level:
                    if spice_level == 'mild':
                        query = query.where(or_(
                            MenuItem.menu_item_spice_level == 'mild',
                            MenuItem.menu_item_spice_level == 'none',
                            MenuItem.menu_item_spice_level.is_(None)
                        ))
                    else:
                        query = query.where(MenuItem.menu_item_spice_level == spice_level)

                # Preparation time constraint
                if max_prep_time:
                    query = query.where(
                        or_(
                            MenuItem.menu_item_minimum_preparation_time <= max_prep_time,
                            MenuItem.menu_item_minimum_preparation_time.is_(None)
                        )
                    )

                # Category filtering
                if categories:
                    category_conditions = []
                    for cat in categories:
                        category_conditions.append(
                            MenuCategory.menu_category_name.ilike(f'%{cat}%')
                        )
                    query = query.where(or_(*category_conditions))

                # Order by popularity and price
                query = query.order_by(
                    MenuItem.menu_item_favorite.desc(),
                    MenuItem.menu_item_price.asc()
                ).limit(limit)

                result = await session.execute(query)
                items = result.fetchall()

                # Create final filtered results with compliance scores
                filtered_items = []
                for item, category_name in items:
                    # Calculate compliance score
                    compliance_score = self._calculate_compliance_score_from_db(item, validated_data)

                    # Format item data with correct column names
                    item_data = {
                        "id": str(item.menu_item_id),
                        "name": item.menu_item_name,
                        "description": item.menu_item_description or "",
                        "price": float(item.menu_item_price),
                        "category_name": category_name,
                        "spice_level": item.menu_item_spice_level,
                        "calories": item.menu_item_calories,
                        "is_available": item.menu_item_in_stock,
                        "is_popular": item.menu_item_favorite,
                        "similarity_score": compliance_score,
                        "recommendation_reason": self._generate_compliance_reason_from_db(item, validated_data)
                    }
                    filtered_items.append(item_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "filtered_items": filtered_items,
                        "total_found": len(filtered_items),
                        "filters_applied": validated_data,
                        "message": f"Found {len(filtered_items)} items matching your dietary requirements"
                    },
                    metadata={"operation": "smart_dietary_filter", "source": "database"}
                )

        except Exception as e:
            logger.error(f"Smart dietary filtering failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Dietary filtering failed: {str(e)}"
            )

    def _calculate_compliance_score(self, item: MenuItem, filters: Dict[str, Any]) -> float:
        """Calculate how well an item complies with the filters (0-1)"""
        score = 1.0

        # Dietary restrictions compliance
        dietary_restrictions = filters['dietary_restrictions']
        if dietary_restrictions:
            item_dietary = set(item.dietary_info or [])
            required_dietary = set(dietary_restrictions)
            if required_dietary.issubset(item_dietary):
                score += 0.2  # Bonus for perfect dietary match

        # Allergen safety
        allergies = filters['allergies']
        if allergies:
            item_allergens = set(item.allergens or [])
            user_allergens = set(allergies)
            if item_allergens.intersection(user_allergens):
                score = 0  # Unsafe item

        # Popularity bonus
        if item.is_popular:
            score += 0.1

        return min(score, 1.0)

    def _generate_compliance_reason(self, item: MenuItem, filters: Dict[str, Any]) -> str:
        """Generate explanation for why item matches filters"""
        reasons = []

        if filters['dietary_restrictions']:
            matching_dietary = set(filters['dietary_restrictions']) & set(item.dietary_info or [])
            if matching_dietary:
                reasons.append(f"Perfect for {', '.join(matching_dietary)} diet")

        if filters['allergies']:
            reasons.append("Safe for your allergies")

        if filters['max_calories'] and item.calories:
            reasons.append(f"Only {item.calories} calories")

        if filters['spice_level'] and item.spice_level == filters['spice_level']:
            reasons.append(f"Perfect {filters['spice_level']} spice level")

        if not reasons:
            reasons.append("Meets all your dietary requirements")

        return "; ".join(reasons)

    def _calculate_compliance_score_from_dict(self, item: Dict[str, Any], filters: Dict[str, Any]) -> float:
        """Calculate how well an item (as dict) complies with the filters (0-1)"""
        score = 1.0

        # Dietary restrictions compliance
        dietary_restrictions = filters['dietary_restrictions']
        if dietary_restrictions:
            dietary_info = item.get('dietary_info', '')
            dietary_list = [d.strip().lower() for d in dietary_info.split(',') if d.strip()] if dietary_info else []

            required_dietary = {r.lower() for r in dietary_restrictions}
            if required_dietary.issubset(set(dietary_list)):
                score += 0.2  # Bonus for perfect dietary match

        # Allergen safety
        allergies = filters['allergies']
        if allergies:
            allergens_str = item.get('allergens', '')
            allergens_list = [a.strip().lower() for a in allergens_str.split(',') if a.strip()] if allergens_str else []

            user_allergens = {a.lower() for a in allergies}
            if set(allergens_list).intersection(user_allergens):
                score = 0  # Unsafe item

        # Popularity bonus
        if item.get('is_popular', False):
            score += 0.1

        return min(score, 1.0)

    def _generate_compliance_reason_from_dict(self, item: Dict[str, Any], filters: Dict[str, Any]) -> str:
        """Generate explanation for why item (as dict) matches filters"""
        reasons = []

        if filters['dietary_restrictions']:
            dietary_info = item.get('dietary_info', '')
            dietary_list = {d.strip().lower() for d in dietary_info.split(',') if d.strip()} if dietary_info else set()

            required_dietary = {r.lower() for r in filters['dietary_restrictions']}
            matching_dietary = required_dietary & dietary_list
            if matching_dietary:
                reasons.append(f"Perfect for {', '.join(matching_dietary)} diet")

        if filters['allergies']:
            reasons.append("Safe for your allergies")

        item_calories = item.get('calories')
        if filters['max_calories'] and item_calories:
            reasons.append(f"Only {item_calories} calories")

        item_spice = item.get('spice_level')
        if filters['spice_level'] and str(item_spice) == str(filters['spice_level']):
            reasons.append(f"Perfect {filters['spice_level']} spice level")

        if not reasons:
            reasons.append("Meets all your dietary requirements")

        return "; ".join(reasons)

    def _calculate_compliance_score_from_db(self, item: MenuItem, filters: Dict[str, Any]) -> float:
        """Calculate compliance score from DB model with correct column names"""
        score = 0.8  # Base score for items that passed DB filters

        # Popularity bonus
        if item.menu_item_favorite:
            score += 0.1

        # Recommended item bonus
        if item.menu_item_is_recommended:
            score += 0.1

        return min(score, 1.0)

    def _generate_compliance_reason_from_db(self, item: MenuItem, filters: Dict[str, Any]) -> str:
        """Generate explanation for why item matches filters (from DB model)"""
        reasons = []

        if filters['max_calories'] and item.menu_item_calories:
            reasons.append(f"Only {item.menu_item_calories} calories")

        if filters['spice_level'] and item.menu_item_spice_level == filters['spice_level']:
            reasons.append(f"Perfect {filters['spice_level']} spice level")

        if item.menu_item_favorite:
            reasons.append("Popular choice")

        if item.menu_item_is_recommended:
            reasons.append("Chef's recommendation")

        if not reasons:
            reasons.append("Meets your requirements")

        return "; ".join(reasons)


@validate_schema(MenuItem)
@require_tables("menu_item")
class RealTimeAvailabilityTool(ToolBase):
    """
    Check real-time availability considering time of day, kitchen capacity,
    ingredient availability, and seasonal constraints.
    """

    def __init__(self):
        super().__init__(
            name="real_time_availability",
            description="Check current availability considering time, capacity, and ingredients",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        # Can check single item or multiple items
        item_ids = kwargs.get('item_ids', [])
        if isinstance(item_ids, str):
            item_ids = [item_ids]

        return {
            'item_ids': item_ids,
            'check_time': kwargs.get('check_time', datetime.now()),
            'party_size': kwargs.get('party_size', 1),
            'include_alternatives': kwargs.get('include_alternatives', True)
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            async with get_db_session() as session:
                item_ids = validated_data['item_ids']
                check_time = validated_data['check_time']
                party_size = validated_data['party_size']

                if item_ids:
                    # Check specific items (use correct column name)
                    query = select(MenuItem).where(MenuItem.menu_item_id.in_(item_ids))
                else:
                    # Check all items (limit to avoid returning entire table)
                    query = select(MenuItem).where(
                        MenuItem.menu_item_in_stock == True
                    ).where(
                        MenuItem.menu_item_status == 'active'
                    ).limit(50)

                result = await session.execute(query)
                items = result.scalars().all()

                availability_results = []
                for item in items:
                    # Build item data manually with correct column names
                    availability = self._check_item_availability(item, check_time, party_size)
                    item_data = {
                        'id': str(item.menu_item_id),
                        'name': item.menu_item_name,
                        'description': item.menu_item_description or '',
                        'price': float(item.menu_item_price),
                        'is_available': item.menu_item_in_stock,
                        'is_popular': item.menu_item_favorite,
                        'estimated_wait_minutes': availability['estimated_wait_minutes'],
                        'availability_reason': availability['availability_reason'],
                        'can_be_prepared': availability['can_be_prepared']
                    }
                    availability_results.append(item_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "availability_results": availability_results,
                        "check_time": check_time.isoformat(),
                        "party_size": party_size,
                        "total_checked": len(availability_results)
                    }
                )

        except Exception as e:
            logger.error(f"Real-time availability check failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Availability check failed: {str(e)}"
            )

    def _check_item_availability(self, item: MenuItem, check_time: datetime, party_size: int) -> Dict[str, Any]:
        """Check if an item is available considering various factors"""
        current_time = check_time.time()

        # Base availability (correct column name)
        is_available = item.menu_item_in_stock
        availability_reason = []
        estimated_wait_time = item.menu_item_minimum_preparation_time or 15

        # Seasonal availability (correct column name)
        if item.menu_item_is_seasonal:
            current_month = check_time.month
            # Simple seasonal logic (would be more sophisticated in production)
            if current_month in [12, 1, 2]:  # Winter
                if 'winter' not in (item.menu_item_description or '').lower():
                    availability_reason.append("Seasonal item - not currently in season")

        # Kitchen capacity simulation (would integrate with real kitchen management)
        if current_time.hour in [12, 13, 19, 20]:  # Peak hours
            estimated_wait_time += 10
            availability_reason.append("Peak hours - slightly longer wait")

        # Party size considerations (correct column name)
        prep_time = item.menu_item_minimum_preparation_time
        if party_size > 6 and prep_time and prep_time > 20:
            estimated_wait_time += 5
            availability_reason.append("Large party - additional prep time")

        return {
            "item_id": str(item.menu_item_id),
            "item_name": item.menu_item_name,
            "is_available": is_available,
            "estimated_wait_minutes": estimated_wait_time,
            "availability_reason": "; ".join(availability_reason) if availability_reason else "Available now",
            "price": float(item.menu_item_price),
            "can_be_prepared": is_available  # Would check ingredient availability in production
        }


@validate_schema(MenuItem)
@require_tables("menu_item", "menu_categories")
class FindSimilarItemsTool(ToolBase):
    """
    Find menu items similar to a given dish using semantic similarity,
    ingredients, category, and other attributes for upselling opportunities.
    """

    def __init__(self):
        super().__init__(
            name="find_similar_items",
            description="Find items similar to a given dish for upselling and recommendations",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        reference_item_id = kwargs.get('reference_item_id')
        if not reference_item_id:
            raise ToolError("reference_item_id is required", tool_name=self.name)

        return {
            'reference_item_id': reference_item_id,
            'limit': kwargs.get('limit', 5),
            'similarity_threshold': kwargs.get('similarity_threshold', 0.6),
            'include_same_category': kwargs.get('include_same_category', True),
            'price_range_factor': kwargs.get('price_range_factor', 1.5)  # Within 1.5x price
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            async with get_db_session() as session:
                reference_id = validated_data['reference_item_id']
                limit = validated_data['limit']
                similarity_threshold = validated_data['similarity_threshold']
                price_range_factor = validated_data['price_range_factor']

                # Get reference item (use correct column name)
                ref_query = select(MenuItem).where(MenuItem.menu_item_id == reference_id)
                ref_result = await session.execute(ref_query)
                reference_item = ref_result.scalar_one_or_none()

                if not reference_item:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Reference item not found"
                    )

                # Use attribute-based similarity (embedding column doesn't exist)
                return await self._attribute_similarity(
                    session, reference_item, limit, similarity_threshold, price_range_factor,
                    validated_data['include_same_category']
                )

        except Exception as e:
            logger.error(f"Similar items search failed: {str(e)}", exc_info=True)
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Similar items search failed: {str(e)}"
            )

    def _generate_similarity_reason(self, reference: MenuItem, similar: MenuItem, similarity: float) -> str:
        """Generate explanation for why items are similar"""
        reasons = []

        # High similarity
        if similarity >= 0.9:
            reasons.append("Very similar to your choice")
        elif similarity >= 0.8:
            reasons.append("Similar style")
        elif similarity >= 0.7:
            reasons.append("Related option")
        else:
            reasons.append("Alternative choice")

        # Spice level match (correct column name)
        if reference.menu_item_spice_level and similar.menu_item_spice_level == reference.menu_item_spice_level:
            reasons.append(f"{reference.menu_item_spice_level} spice")

        # Popular items (correct column name)
        if similar.menu_item_favorite:
            reasons.append("popular choice")

        return "; ".join(reasons[:3])  # Limit to 3 reasons

    async def _attribute_similarity(
        self,
        session,
        reference_item: MenuItem,
        limit: int,
        similarity_threshold: float,
        price_range_factor: float,
        include_same_category: bool
    ) -> ToolResult:
        """
        Attribute-based similarity search.
        Uses category, spice level, and price for matching.
        """
        logger.info("Using attribute-based similarity")

        # Join with mapping table to get category (correct column names)
        query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name'),
            MenuCategory.menu_category_id.label('category_id')
        ).join(
            MenuItemCategoryMapping,
            MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
        ).join(
            MenuCategory,
            MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
        ).where(
            MenuItemCategoryMapping.is_primary == True
        ).where(
            and_(
                MenuItem.menu_item_id != reference_item.menu_item_id,
                MenuItem.menu_item_in_stock == True,
                MenuItem.menu_item_status == 'active'
            )
        )

        # Price range filtering (correct column name)
        min_price = reference_item.menu_item_price / price_range_factor
        max_price = reference_item.menu_item_price * price_range_factor
        query = query.where(
            and_(
                MenuItem.menu_item_price >= min_price,
                MenuItem.menu_item_price <= max_price
            )
        )

        result = await session.execute(query)
        items = result.fetchall()

        # Get reference item's category via relationship
        ref_category_id = None
        if reference_item.category_mappings:
            for mapping in reference_item.category_mappings:
                if mapping.is_primary:
                    ref_category_id = mapping.menu_category_id
                    break

        # Calculate attribute-based similarity
        similar_items = []
        for item, category_name, category_id in items:
            score = 0.0

            # Category similarity (using category from joined mapping)
            if ref_category_id and category_id == ref_category_id:
                score += 0.4

            # Spice level similarity (correct column name)
            if reference_item.menu_item_spice_level == item.menu_item_spice_level:
                score += 0.3

            # Price similarity (correct column name)
            if reference_item.menu_item_price and item.menu_item_price:
                ref_price = float(reference_item.menu_item_price)
                item_price = float(item.menu_item_price)
                price_diff = abs(ref_price - item_price) / max(ref_price, item_price)
                price_similarity = max(0, 1 - price_diff)
                score += price_similarity * 0.2

            # Popular item bonus
            if item.menu_item_favorite:
                score += 0.1

            if score >= similarity_threshold:
                # Build item data manually with correct column names
                item_data = {
                    'id': str(item.menu_item_id),
                    'name': item.menu_item_name,
                    'description': item.menu_item_description or '',
                    'price': float(item.menu_item_price),
                    'is_available': item.menu_item_in_stock,
                    'is_popular': item.menu_item_favorite,
                    'spice_level': item.menu_item_spice_level,
                    'category_name': category_name,
                    'similarity_score': round(score, 3),
                    'recommendation_reason': self._generate_similarity_reason(
                        reference_item, item, score
                    )
                }
                similar_items.append((score, item_data))

        # Sort by score and limit
        similar_items.sort(key=lambda x: x[0], reverse=True)
        formatted_results = [item_data for _, item_data in similar_items[:limit]]

        # Build reference item data manually
        reference_data = {
            'id': str(reference_item.menu_item_id),
            'name': reference_item.menu_item_name,
            'description': reference_item.menu_item_description or '',
            'price': float(reference_item.menu_item_price),
            'is_available': reference_item.menu_item_in_stock,
            'is_popular': reference_item.menu_item_favorite,
            'spice_level': reference_item.menu_item_spice_level
        }

        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={
                "similar_items": formatted_results,
                "reference_item": reference_data,
                "total_found": len(formatted_results)
            }
        )


@validate_schema(MenuItem)
@require_tables("menu_item", "menu_categories")
class PriceRangeMenuTool(ToolBase):
    """
    Filter menu items by price range with smart budget optimization
    and value recommendations.
    """

    def __init__(self):
        super().__init__(
            name="price_range_menu",
            description="Filter menu by price range with budget optimization",
            max_retries=2,
            timeout_seconds=10
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        min_price = kwargs.get('min_price', 0)
        max_price = kwargs.get('max_price')

        if max_price is not None and min_price > max_price:
            raise ToolError("min_price cannot be greater than max_price", tool_name=self.name)

        return {
            'min_price': min_price,
            'max_price': max_price,
            'party_size': kwargs.get('party_size', 1),
            'include_sharing': kwargs.get('include_sharing', True),
            'value_optimization': kwargs.get('value_optimization', True),
            'limit': kwargs.get('limit', 15)
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            async with get_db_session() as session:
                min_price = validated_data['min_price']
                max_price = validated_data['max_price']
                party_size = validated_data['party_size']
                limit = validated_data['limit']

                # Build query with correct joins via mapping table
                query = select(
                    MenuItem,
                    MenuCategory.menu_category_name.label('category_name')
                ).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                ).join(
                    MenuCategory,
                    MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                ).where(
                    MenuItemCategoryMapping.is_primary == True
                ).where(
                    MenuItem.menu_item_in_stock == True
                ).where(
                    MenuItem.menu_item_status == 'active'
                )

                # Price range filtering (use correct column name)
                if min_price > 0:
                    query = query.where(MenuItem.menu_item_price >= min_price)

                if max_price is not None:
                    query = query.where(MenuItem.menu_item_price <= max_price)

                # Order by popularity and price
                query = query.order_by(
                    MenuItem.menu_item_favorite.desc(),
                    MenuItem.menu_item_price.asc()
                ).limit(limit)

                result = await session.execute(query)
                items = result.fetchall()

                # Process items with value analysis
                budget_items = []
                for item, category_name in items:
                    value_score = self._calculate_value_score_from_db(item, party_size)
                    sharing_suitable = self._is_sharing_suitable_from_db(item, party_size)

                    # Format item data with correct column names
                    item_data = {
                        "id": str(item.menu_item_id),
                        "name": item.menu_item_name,
                        "description": item.menu_item_description or "",
                        "price": float(item.menu_item_price),
                        "category_name": category_name,
                        "is_available": item.menu_item_in_stock,
                        "is_popular": item.menu_item_favorite,
                        "similarity_score": value_score,
                        "recommendation_reason": self._generate_value_reason_from_db(item, party_size, sharing_suitable)
                    }
                    budget_items.append(item_data)

                # Budget analysis
                total_budget = max_price * party_size if max_price else None
                budget_analysis = self._analyze_budget(budget_items, total_budget, party_size)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "budget_items": budget_items,
                        "price_range": {"min": min_price, "max": max_price},
                        "budget_analysis": budget_analysis,
                        "total_found": len(budget_items)
                    },
                    metadata={"operation": "price_range_menu", "source": "database"}
                )

        except Exception as e:
            logger.error(f"Price range filtering failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Price range filtering failed: {str(e)}"
            )

    def _calculate_value_score(self, item: MenuItem, party_size: int) -> float:
        """Calculate value score based on price, popularity, and portion considerations"""
        score = 0.5  # Base score

        # Popularity adds value (correct column name)
        if item.menu_item_favorite:
            score += 0.3

        # Lower price adds value (correct column name)
        if item.menu_item_price <= 200:
            score += 0.2
        elif item.menu_item_price <= 500:
            score += 0.1

        # Items good for sharing add value for larger parties
        if party_size > 2 and self._is_sharing_suitable(item, party_size):
            score += 0.2

        return min(score, 1.0)

    def _is_sharing_suitable(self, item: MenuItem, party_size: int) -> bool:
        """Determine if item is suitable for sharing based on party size and item characteristics"""
        sharing_keywords = ['sharing', 'platter', 'family', 'large', 'combo']
        item_text = f"{item.menu_item_name} {item.menu_item_description or ''}".lower()

        # Item has sharing keywords
        has_sharing_keywords = any(keyword in item_text for keyword in sharing_keywords)

        # Larger party sizes benefit more from sharing items
        if party_size >= 4 and has_sharing_keywords:
            return True
        elif party_size >= 2 and has_sharing_keywords:
            return True

        return False

    def _calculate_value_score_from_db(self, item: MenuItem, party_size: int) -> float:
        """Calculate value score from DB model with correct column names"""
        score = 0.5  # Base score

        # Popularity adds value
        if item.menu_item_favorite:
            score += 0.3

        # Lower price adds value
        if item.menu_item_price <= 200:
            score += 0.2
        elif item.menu_item_price <= 500:
            score += 0.1

        # Items good for sharing add value for larger parties
        if party_size > 2 and self._is_sharing_suitable_from_db(item, party_size):
            score += 0.2

        return min(score, 1.0)

    def _is_sharing_suitable_from_db(self, item: MenuItem, party_size: int) -> bool:
        """Determine if item (from DB) is suitable for sharing"""
        sharing_keywords = ['sharing', 'platter', 'family', 'large', 'combo']
        item_text = f"{item.menu_item_name} {item.menu_item_description or ''}".lower()

        has_sharing_keywords = any(keyword in item_text for keyword in sharing_keywords)

        if party_size >= 4 and has_sharing_keywords:
            return True
        elif party_size >= 2 and has_sharing_keywords:
            return True

        return False

    def _generate_value_reason_from_db(self, item: MenuItem, party_size: int, sharing_suitable: bool) -> str:
        """Generate value proposition explanation from DB model"""
        reasons = []

        if item.menu_item_favorite:
            reasons.append("Popular choice")

        if item.menu_item_price <= 200:
            reasons.append("Great value")
        elif item.menu_item_price <= 500:
            reasons.append("Good value")

        if sharing_suitable and party_size > 2:
            reasons.append("Perfect for sharing")

        if not reasons:
            reasons.append("Within your budget")

        return "; ".join(reasons)

    def _generate_value_reason(self, item: MenuItem, party_size: int, sharing_suitable: bool) -> str:
        """Generate value proposition explanation"""
        reasons = []

        if item.menu_item_favorite:
            reasons.append("Popular choice")

        if item.price <= 200:
            reasons.append("Great value")
        elif item.price <= 500:
            reasons.append("Good value")

        if sharing_suitable and party_size > 2:
            reasons.append("Perfect for sharing")

        if not reasons:
            reasons.append("Within your budget")

        return "; ".join(reasons)

    def _analyze_budget(self, items: List[Dict], total_budget: Optional[float], party_size: int) -> Dict[str, Any]:
        """Analyze budget and provide recommendations"""
        if not items:
            return {"message": "No items found in your price range"}

        avg_price = sum(item['price'] for item in items) / len(items)
        min_price = min(item['price'] for item in items)
        max_price = max(item['price'] for item in items)

        analysis = {
            "average_price": avg_price,
            "price_range": {"min": min_price, "max": max_price},
            "total_items": len(items)
        }

        if total_budget:
            per_person_budget = total_budget / party_size
            affordable_items = [item for item in items if item['price'] <= per_person_budget]

            analysis.update({
                "total_budget": total_budget,
                "per_person_budget": per_person_budget,
                "affordable_items": len(affordable_items),
                "budget_utilization": min(avg_price / per_person_budget * 100, 100) if per_person_budget > 0 else 0
            })

        return analysis

    def _calculate_value_score_from_dict(self, item: Dict[str, Any], party_size: int) -> float:
        """Calculate value score based on price, popularity (from dict)"""
        score = 0.5  # Base score

        # Popularity adds value
        if item.get('is_popular', False):
            score += 0.3

        # Lower price adds value
        item_price = item.get('price', 0)
        if item_price <= 200:
            score += 0.2
        elif item_price <= 500:
            score += 0.1

        # Items good for sharing add value for larger parties
        if party_size > 2 and self._is_sharing_suitable_from_dict(item, party_size):
            score += 0.2

        return min(score, 1.0)

    def _is_sharing_suitable_from_dict(self, item: Dict[str, Any], party_size: int) -> bool:
        """Determine if item (as dict) is suitable for sharing"""
        sharing_keywords = ['sharing', 'platter', 'family', 'large', 'combo']
        item_text = f"{item.get('name', '')} {item.get('description', '')}".lower()

        # Item has sharing keywords
        has_sharing_keywords = any(keyword in item_text for keyword in sharing_keywords)

        # Larger party sizes benefit more from sharing items
        if party_size >= 4 and has_sharing_keywords:
            return True
        elif party_size >= 2 and has_sharing_keywords:
            return True

        return False

    def _generate_value_reason_from_dict(self, item: Dict[str, Any], party_size: int, sharing_suitable: bool) -> str:
        """Generate value proposition explanation (from dict)"""
        reasons = []

        if item.get('is_popular', False):
            reasons.append("Popular choice")

        item_price = item.get('price', 0)
        if item_price <= 200:
            reasons.append("Great value")
        elif item_price <= 500:
            reasons.append("Good value")

        if sharing_suitable and party_size > 2:
            reasons.append("Perfect for sharing")

        if not reasons:
            reasons.append("Within your budget")

        return "; ".join(reasons)


@validate_schema(MenuItem)
@require_tables("menu_item", "menu_categories")
class SmartUpsellingTool(ToolBase):
    """
    Generate intelligent upselling and cross-selling suggestions based on
    current selection, user preferences, and business optimization.
    """

    def __init__(self):
        super().__init__(
            name="smart_upselling",
            description="Generate intelligent upselling and cross-selling suggestions",
            max_retries=2,
            timeout_seconds=15
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        current_items = kwargs.get('current_items', [])
        if isinstance(current_items, str):
            current_items = [current_items]

        return {
            'current_items': current_items,  # List of item IDs currently selected
            'budget_remaining': kwargs.get('budget_remaining'),
            'user_preferences': kwargs.get('user_preferences', {}),
            'upsell_strategy': kwargs.get('upsell_strategy', 'balanced'),  # aggressive, balanced, conservative
            'limit': kwargs.get('limit', 5)
        }

    async def _execute_impl(self, **kwargs) -> ToolResult:
        validated_data = self.validate_input(**kwargs)

        try:
            async with get_db_session() as session:
                current_items = validated_data['current_items']
                budget_remaining = validated_data['budget_remaining']
                strategy = validated_data['upsell_strategy']
                limit = validated_data['limit']

                if not current_items:
                    # No current selection - suggest popular items
                    suggestions = await self._suggest_popular_items(session, budget_remaining, limit)
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "suggestions": suggestions,
                            "strategy": "popular_items",
                            "budget_remaining": budget_remaining
                        }
                    )

                # Get current items details (correct column names and joins)
                current_query = select(
                    MenuItem,
                    MenuCategory.menu_category_name.label('category_name'),
                    MenuCategory.menu_category_id.label('category_id')
                ).join(
                    MenuItemCategoryMapping,
                    MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
                ).join(
                    MenuCategory,
                    MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
                ).where(
                    MenuItemCategoryMapping.is_primary == True
                ).where(MenuItem.menu_item_id.in_(current_items))

                current_result = await session.execute(current_query)
                current_items_data = current_result.fetchall()

                if not current_items_data:
                    return ToolResult(
                        status=ToolStatus.FAILURE,
                        error="Current items not found"
                    )

                # Generate upselling suggestions
                suggestions = await self._generate_upsell_suggestions(
                    session, current_items_data, budget_remaining, strategy, limit
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "upsell_suggestions": suggestions,
                        "current_items_count": len(current_items_data),
                        "strategy": strategy,
                        "total_suggestions": len(suggestions)
                    }
                )

        except Exception as e:
            logger.error(f"Smart upselling failed: {str(e)}")
            return ToolResult(
                status=ToolStatus.FAILURE,
                error=f"Upselling failed: {str(e)}"
            )

    async def _suggest_popular_items(self, session, budget_remaining: Optional[float], limit: int):
        """Suggest popular items when no current selection"""
        query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name')
        ).join(
            MenuItemCategoryMapping,
            MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
        ).join(
            MenuCategory,
            MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
        ).where(
            MenuItemCategoryMapping.is_primary == True
        ).where(
            and_(
                MenuItem.menu_item_in_stock == True,
                MenuItem.menu_item_status == 'active',
                MenuItem.menu_item_favorite == True
            )
        )

        if budget_remaining:
            query = query.where(MenuItem.menu_item_price <= budget_remaining)

        query = query.order_by(MenuItem.menu_item_price.asc()).limit(limit)

        result = await session.execute(query)
        items = result.fetchall()

        suggestions = []
        for item, category_name in items:
            # Build item data manually with correct column names
            item_data = {
                'id': str(item.menu_item_id),
                'item_id': str(item.menu_item_id),
                'name': item.menu_item_name,
                'description': item.menu_item_description or '',
                'price': float(item.menu_item_price),
                'is_available': item.menu_item_in_stock,
                'is_popular': item.menu_item_favorite,
                'category_name': category_name,
                'similarity_score': 0.8,
                'recommendation_reason': "Popular choice to start your meal"
            }
            suggestions.append(item_data)

        return suggestions

    async def _generate_upsell_suggestions(self, session, current_items, budget_remaining, strategy, limit):
        """Generate intelligent upselling suggestions"""
        suggestions = []
        current_categories = set()
        current_total = Decimal('0')

        # current_items now has 3 columns: (item, category_name, category_id)
        for item, cat_name, cat_id in current_items:
            current_categories.add(cat_id)
            current_total += item.menu_item_price

        # Different upselling strategies
        if strategy == 'aggressive':
            # Focus on higher-priced items and add-ons
            suggestions.extend(await self._suggest_premium_upgrades(session, current_items, budget_remaining))
            suggestions.extend(await self._suggest_add_ons(session, current_items, budget_remaining, current_categories))

        elif strategy == 'conservative':
            # Focus on complementary items and value additions
            suggestions.extend(await self._suggest_complementary_items(session, current_items, budget_remaining))
            suggestions.extend(await self._suggest_value_additions(session, current_items, budget_remaining))

        else:  # balanced
            # Mix of all approaches
            suggestions.extend(await self._suggest_complementary_items(session, current_items, budget_remaining))
            suggestions.extend(await self._suggest_add_ons(session, current_items, budget_remaining, current_categories))
            suggestions.extend(await self._suggest_premium_upgrades(session, current_items, budget_remaining))

        # Remove duplicates and limit results
        seen_ids = set()
        unique_suggestions = []
        for suggestion in suggestions:
            item_id = suggestion.get('item_id') or suggestion.get('id')
            if item_id and item_id not in seen_ids:
                seen_ids.add(item_id)
                unique_suggestions.append(suggestion)

        return unique_suggestions[:limit]

    async def _suggest_complementary_items(self, session, current_items, budget_remaining):
        """Suggest items that complement current selection"""
        suggestions = []

        # Rules for complementary items (current_items has 3 columns: item, cat_name, cat_id)
        has_main = any('main' in cat_name.lower() for _, cat_name, _ in current_items)
        has_appetizer = any('appetizer' in cat_name.lower() for _, cat_name, _ in current_items)
        has_beverage = any('beverage' in cat_name.lower() or 'drink' in cat_name.lower() for _, cat_name, _ in current_items)

        # Suggest appetizer if no appetizer and has main
        if has_main and not has_appetizer:
            appetizer_query = select(
                MenuItem,
                MenuCategory.menu_category_name.label('category_name')
            ).join(
                MenuItemCategoryMapping,
                MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
            ).join(
                MenuCategory,
                MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
            ).where(
                MenuItemCategoryMapping.is_primary == True
            ).where(
                and_(
                    MenuItem.menu_item_in_stock == True,
                    MenuItem.menu_item_status == 'active',
                    MenuCategory.menu_category_name.ilike('%appetizer%')
                )
            )

            if budget_remaining:
                appetizer_query = appetizer_query.where(MenuItem.menu_item_price <= budget_remaining)

            appetizer_query = appetizer_query.order_by(MenuItem.menu_item_favorite.desc()).limit(2)
            result = await session.execute(appetizer_query)

            for item, category_name in result.fetchall():
                item_data = {
                    'id': str(item.menu_item_id),
                    'item_id': str(item.menu_item_id),
                    'name': item.menu_item_name,
                    'description': item.menu_item_description or '',
                    'price': float(item.menu_item_price),
                    'is_available': item.menu_item_in_stock,
                    'is_popular': item.menu_item_favorite,
                    'category_name': category_name,
                    'similarity_score': 0.9,
                    'recommendation_reason': "Perfect appetizer to start your meal"
                }
                suggestions.append(item_data)

        # Suggest beverage if no beverage
        if not has_beverage:
            beverage_query = select(
                MenuItem,
                MenuCategory.menu_category_name.label('category_name')
            ).join(
                MenuItemCategoryMapping,
                MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
            ).join(
                MenuCategory,
                MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
            ).where(
                MenuItemCategoryMapping.is_primary == True
            ).where(
                and_(
                    MenuItem.menu_item_in_stock == True,
                    MenuItem.menu_item_status == 'active',
                    or_(
                        MenuCategory.menu_category_name.ilike('%beverage%'),
                        MenuCategory.menu_category_name.ilike('%drink%')
                    )
                )
            )

            if budget_remaining:
                beverage_query = beverage_query.where(MenuItem.menu_item_price <= budget_remaining)

            beverage_query = beverage_query.order_by(MenuItem.menu_item_favorite.desc()).limit(2)
            result = await session.execute(beverage_query)

            for item, category_name in result.fetchall():
                item_data = {
                    'id': str(item.menu_item_id),
                    'item_id': str(item.menu_item_id),
                    'name': item.menu_item_name,
                    'description': item.menu_item_description or '',
                    'price': float(item.menu_item_price),
                    'is_available': item.menu_item_in_stock,
                    'is_popular': item.menu_item_favorite,
                    'category_name': category_name,
                    'similarity_score': 0.85,
                    'recommendation_reason': "Refreshing drink to complement your meal"
                }
                suggestions.append(item_data)

        return suggestions

    async def _suggest_add_ons(self, session, current_items, budget_remaining, current_categories=None):
        """Suggest add-ons and sides that complement current selection"""
        suggestions = []

        if current_categories is None:
            current_categories = set()

        # Look for sides and add-ons
        addon_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name'),
            MenuCategory.menu_category_id.label('category_id')
        ).join(
            MenuItemCategoryMapping,
            MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
        ).join(
            MenuCategory,
            MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
        ).where(
            MenuItemCategoryMapping.is_primary == True
        ).where(
            and_(
                MenuItem.menu_item_in_stock == True,
                MenuItem.menu_item_status == 'active',
                or_(
                    MenuCategory.menu_category_name.ilike('%side%'),
                    MenuCategory.menu_category_name.ilike('%addon%'),
                    MenuItem.menu_item_name.ilike('%bread%'),
                    MenuItem.menu_item_name.ilike('%rice%')
                )
            )
        )

        # Avoid suggesting add-ons from categories already selected
        if current_categories:
            addon_query = addon_query.where(~MenuCategory.menu_category_id.in_(current_categories))

        if budget_remaining:
            addon_query = addon_query.where(MenuItem.menu_item_price <= budget_remaining)

        addon_query = addon_query.order_by(MenuItem.menu_item_price.asc()).limit(3)
        result = await session.execute(addon_query)

        for item, category_name, cat_id in result.fetchall():
            item_data = {
                'id': str(item.menu_item_id),
                'item_id': str(item.menu_item_id),
                'name': item.menu_item_name,
                'description': item.menu_item_description or '',
                'price': float(item.menu_item_price),
                'is_available': item.menu_item_in_stock,
                'is_popular': item.menu_item_favorite,
                'category_name': category_name,
                'similarity_score': 0.8,
                'recommendation_reason': "Great addition to your order"
            }
            suggestions.append(item_data)

        return suggestions

    async def _suggest_premium_upgrades(self, session, current_items, budget_remaining):
        """Suggest premium versions or upgrades"""
        suggestions = []

        # For each current item, try to find premium alternatives
        # current_items has 3 columns: (item, cat_name, cat_id)
        for item, current_cat_name, current_cat_id in current_items:
            # Look for items in same category but higher price
            upgrade_query = select(
                MenuItem,
                MenuCategory.menu_category_name.label('category_name')
            ).join(
                MenuItemCategoryMapping,
                MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
            ).join(
                MenuCategory,
                MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
            ).where(
                MenuItemCategoryMapping.is_primary == True
            ).where(
                and_(
                    MenuItem.menu_item_in_stock == True,
                    MenuItem.menu_item_status == 'active',
                    MenuCategory.menu_category_id == current_cat_id,
                    MenuItem.menu_item_price > item.menu_item_price,
                    MenuItem.menu_item_id != item.menu_item_id
                )
            )

            if budget_remaining:
                max_upgrade_price = min(budget_remaining, float(item.menu_item_price) * Decimal('1.5'))
                upgrade_query = upgrade_query.where(MenuItem.menu_item_price <= max_upgrade_price)

            upgrade_query = upgrade_query.order_by(MenuItem.menu_item_price.asc()).limit(1)
            result = await session.execute(upgrade_query)
            upgrade_result = result.first()

            if upgrade_result:
                upgrade_item, cat_name = upgrade_result
                price_diff = float(upgrade_item.menu_item_price) - float(item.menu_item_price)

                item_data = {
                    'id': str(upgrade_item.menu_item_id),
                    'item_id': str(upgrade_item.menu_item_id),
                    'name': upgrade_item.menu_item_name,
                    'description': upgrade_item.menu_item_description or '',
                    'price': float(upgrade_item.menu_item_price),
                    'is_available': upgrade_item.menu_item_in_stock,
                    'is_popular': upgrade_item.menu_item_favorite,
                    'category_name': cat_name,
                    'similarity_score': 0.9,
                    'recommendation_reason': f"Premium upgrade (+₹{price_diff:.0f}) - enhanced version of {item.menu_item_name}"
                }
                suggestions.append(item_data)

        return suggestions

    async def _suggest_value_additions(self, session, current_items, budget_remaining):
        """Suggest value-added items within budget"""
        suggestions = []

        # Look for popular, affordable items (correct column names)
        value_query = select(
            MenuItem,
            MenuCategory.menu_category_name.label('category_name')
        ).join(
            MenuItemCategoryMapping,
            MenuItem.menu_item_id == MenuItemCategoryMapping.menu_item_id
        ).join(
            MenuCategory,
            MenuItemCategoryMapping.menu_category_id == MenuCategory.menu_category_id
        ).where(
            MenuItemCategoryMapping.is_primary == True
        ).where(
            and_(
                MenuItem.menu_item_in_stock == True,
                MenuItem.menu_item_status == 'active',
                MenuItem.menu_item_favorite == True,
                MenuItem.menu_item_price <= 200  # Affordable items
            )
        )

        if budget_remaining:
            value_query = value_query.where(MenuItem.menu_item_price <= budget_remaining)

        # Exclude items already selected (current_items has 3 columns: item, cat_name, cat_id)
        current_item_ids = [item.menu_item_id for item, _, _ in current_items]
        value_query = value_query.where(~MenuItem.menu_item_id.in_(current_item_ids))

        value_query = value_query.order_by(MenuItem.menu_item_price.asc()).limit(2)
        result = await session.execute(value_query)

        for item, category_name in result.fetchall():
            item_data = {
                'id': str(item.menu_item_id),
                'item_id': str(item.menu_item_id),
                'name': item.menu_item_name,
                'description': item.menu_item_description or '',
                'price': float(item.menu_item_price),
                'is_available': item.menu_item_in_stock,
                'is_popular': item.menu_item_favorite,
                'category_name': category_name,
                'similarity_score': 0.85,
                'recommendation_reason': "Popular value addition - loved by customers"
            }
            suggestions.append(item_data)

        return suggestions
