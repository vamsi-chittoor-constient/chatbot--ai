"""
General Queries Database Tools
=============================
SQLAlchemy-based tools for managing FAQ, policies, and query analytics.
Used by GeneralQueriesAgent for knowledge management and query resolution.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import joinedload
from decimal import Decimal

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import db_manager
from app.shared.models import FAQ, RestaurantPolicy, QueryAnalytics, User
from app.core.logging_config import get_logger
from app.utils.schema_tool_integration import serialize_output_with_schema, safe_isoformat
from app.schemas.queries import (
    FAQResponse,
    RestaurantPolicyResponse,
    QueryAnalyticsResponse,
    FAQListResponse,
    RestaurantPolicyListResponse
)

logger = get_logger(__name__)


class CreateFAQTool(ToolBase):
    """Create a new FAQ item with vector embeddings support."""

    def __init__(self):
        super().__init__(
            name="create_faq",
            description="Create a new FAQ item with search optimization",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['question', 'answer', 'category']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Optional fields
        validated_data['subcategory'] = kwargs.get('subcategory')
        validated_data['question_variations'] = kwargs.get('question_variations', [])
        validated_data['keywords'] = kwargs.get('keywords', [])
        validated_data['difficulty_level'] = kwargs.get('difficulty_level', 'easy')
        validated_data['is_featured'] = kwargs.get('is_featured', False)
        validated_data['display_order'] = kwargs.get('display_order', 100)
        validated_data['confidence_threshold'] = kwargs.get('confidence_threshold', 0.80)
        validated_data['embedding'] = kwargs.get('embedding')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Don't manually set ID - let SQLAlchemy event listener generate it automatically
                faq = FAQ(
                    question=validated_data['question'],
                    answer=validated_data['answer'],
                    category=validated_data['category'],
                    subcategory=validated_data.get('subcategory'),
                    question_variations=validated_data.get('question_variations'),
                    keywords=validated_data.get('keywords'),
                    difficulty_level=validated_data['difficulty_level'],
                    is_featured=validated_data['is_featured'],
                    display_order=validated_data['display_order'],
                    confidence_threshold=Decimal(str(validated_data['confidence_threshold'])),
                    embedding=validated_data.get('embedding')
                )

                session.add(faq)
                await session.commit()
                await session.refresh(faq)  # Get the auto-generated ID

                faq_data = serialize_output_with_schema(
                    FAQResponse,
                    faq,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=faq_data,
                    metadata={"operation": "create_faq"}
                )

        except Exception as e:
            logger.error(f"Failed to create FAQ: {str(e)}")
            raise ToolError(
                f"FAQ creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class SearchFAQTool(ToolBase):
    """Search FAQ items by question similarity and keywords."""

    def __init__(self):
        super().__init__(
            name="search_faq",
            description="Search FAQ items for matching questions",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'query' not in kwargs or not kwargs['query']:
            raise ValueError("Missing required field: query")

        validated_data = {
            'query': kwargs['query'],
            'category': kwargs.get('category'),
            'limit': kwargs.get('limit', 5),
            'confidence_threshold': kwargs.get('confidence_threshold', 0.7),
            'embedding': kwargs.get('embedding')
        }

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Build base query
                query = select(FAQ).where(FAQ.status == 'active')

                if validated_data.get('category'):
                    query = query.where(FAQ.category == validated_data['category'])

                # If we have embedding, use vector similarity search
                if validated_data.get('embedding'):
                    # Vector similarity search using cosine distance
                    query = query.order_by(
                        FAQ.embedding.cosine_distance(validated_data['embedding'])
                    ).limit(validated_data['limit'])
                else:
                    # Fallback to text search
                    search_query = validated_data['query'].lower()
                    query = query.where(
                        or_(
                            func.lower(FAQ.question).contains(search_query),
                            func.lower(FAQ.answer).contains(search_query),
                            FAQ.keywords.op('&&')(func.string_to_array(search_query, ' '))
                        )
                    ).order_by(FAQ.question_count.desc(), FAQ.satisfaction_score.desc()).limit(validated_data['limit'])

                result = await session.execute(query)
                faqs = result.scalars().all()

                faq_results = []
                for faq in faqs:
                    # Calculate relevance score (simplified)
                    relevance_score = 0.8  # Default score for now

                    # Update question count
                    faq.question_count += 1
                    faq.last_asked = datetime.now(timezone.utc)

                    # Serialize FAQ using schema
                    faq_data = serialize_output_with_schema(
                        FAQResponse,
                        faq,
                        self.name,
                        from_orm=True
                    )
                    # Add extra field
                    faq_data['relevance_score'] = relevance_score

                    faq_results.append(faq_data)

                await session.commit()

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "query": validated_data['query'],
                        "total_results": len(faq_results),
                        "results": faq_results,
                        "search_method": "vector" if validated_data.get('embedding') else "text"
                    },
                    metadata={"operation": "search_faq"}
                )

        except Exception as e:
            logger.error(f"Failed to search FAQ: {str(e)}")
            raise ToolError(
                f"FAQ search failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetFAQTool(ToolBase):
    """Get specific FAQ item by ID."""

    def __init__(self):
        super().__init__(
            name="get_faq",
            description="Get FAQ item by ID",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'faq_id' not in kwargs or not kwargs['faq_id']:
            raise ValueError("Missing required field: faq_id")
        return {'faq_id': kwargs['faq_id']}

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                faq_query = select(FAQ).where(FAQ.id == validated_data['faq_id'])
                result = await session.execute(faq_query)
                faq = result.scalar_one_or_none()

                if not faq:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "found": False,
                            "message": "FAQ not found"
                        },
                        metadata={"operation": "get_faq"}
                    )

                faq_data = serialize_output_with_schema(
                    FAQResponse,
                    faq,
                    self.name,
                    from_orm=True
                )
                # Add extra field
                faq_data['found'] = True

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=faq_data,
                    metadata={"operation": "get_faq"}
                )

        except Exception as e:
            logger.error(f"Failed to get FAQ: {str(e)}")
            raise ToolError(
                f"Failed to retrieve FAQ: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class CreateRestaurantPolicyTool(ToolBase):
    """Create a new restaurant policy."""

    def __init__(self):
        super().__init__(
            name="create_restaurant_policy",
            description="Create a new restaurant policy",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['policy_name', 'policy_category', 'policy_type', 'short_description', 'full_policy']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Optional fields
        validated_data['exceptions'] = kwargs.get('exceptions')
        validated_data['enforcement_level'] = kwargs.get('enforcement_level', 'strict')
        validated_data['applies_to'] = kwargs.get('applies_to', 'all')
        validated_data['effective_date'] = kwargs.get('effective_date')
        validated_data['expiry_date'] = kwargs.get('expiry_date')
        validated_data['legal_requirement'] = kwargs.get('legal_requirement', False)
        validated_data['compliance_level'] = kwargs.get('compliance_level')
        validated_data['related_policies'] = kwargs.get('related_policies', [])
        validated_data['created_by'] = kwargs.get('created_by')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Don't manually set ID - let SQLAlchemy event listener generate it automatically
                policy = RestaurantPolicy(
                    policy_name=validated_data['policy_name'],
                    policy_category=validated_data['policy_category'],
                    policy_type=validated_data['policy_type'],
                    short_description=validated_data['short_description'],
                    full_policy=validated_data['full_policy'],
                    exceptions=validated_data.get('exceptions'),
                    enforcement_level=validated_data['enforcement_level'],
                    applies_to=validated_data['applies_to'],
                    effective_date=validated_data.get('effective_date', datetime.now(timezone.utc).date()),
                    expiry_date=validated_data.get('expiry_date'),
                    legal_requirement=validated_data['legal_requirement'],
                    compliance_level=validated_data.get('compliance_level'),
                    related_policies=validated_data.get('related_policies'),
                    created_by=validated_data.get('created_by')
                )

                session.add(policy)
                await session.commit()
                await session.refresh(policy)  # Get the auto-generated ID

                policy_data = serialize_output_with_schema(
                    RestaurantPolicyResponse,
                    policy,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=policy_data,
                    metadata={"operation": "create_restaurant_policy"}
                )

        except Exception as e:
            logger.error(f"Failed to create restaurant policy: {str(e)}")
            raise ToolError(
                f"Restaurant policy creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class SearchRestaurantPolicyTool(ToolBase):
    """Search restaurant policies by category and content."""

    def __init__(self):
        super().__init__(
            name="search_restaurant_policy",
            description="Search restaurant policies",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        validated_data = {
            'query': kwargs.get('query'),
            'policy_category': kwargs.get('policy_category'),
            'policy_type': kwargs.get('policy_type'),
            'applies_to': kwargs.get('applies_to'),
            'legal_requirement': kwargs.get('legal_requirement'),
            'limit': kwargs.get('limit', 10)
        }

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Build query
                query = select(RestaurantPolicy).where(RestaurantPolicy.status == 'active')

                if validated_data.get('policy_category'):
                    query = query.where(RestaurantPolicy.policy_category == validated_data['policy_category'])

                if validated_data.get('policy_type'):
                    query = query.where(RestaurantPolicy.policy_type == validated_data['policy_type'])

                if validated_data.get('applies_to'):
                    query = query.where(
                        or_(
                            RestaurantPolicy.applies_to == validated_data['applies_to'],
                            RestaurantPolicy.applies_to == 'all'
                        )
                    )

                if validated_data.get('legal_requirement') is not None:
                    query = query.where(RestaurantPolicy.legal_requirement == validated_data['legal_requirement'])

                # Text search if query provided
                if validated_data.get('query'):
                    search_query = validated_data['query'].lower()
                    query = query.where(
                        or_(
                            func.lower(RestaurantPolicy.policy_name).contains(search_query),
                            func.lower(RestaurantPolicy.short_description).contains(search_query),
                            func.lower(RestaurantPolicy.full_policy).contains(search_query)
                        )
                    )

                query = query.order_by(
                    RestaurantPolicy.reference_count.desc(),
                    RestaurantPolicy.policy_name
                ).limit(validated_data['limit'])

                result = await session.execute(query)
                policies = result.scalars().all()

                policy_results = []
                for policy in policies:
                    # Update reference count
                    policy.reference_count += 1

                    # Serialize policy using schema
                    policy_data = serialize_output_with_schema(
                        RestaurantPolicyResponse,
                        policy,
                        self.name,
                        from_orm=True
                    )

                    policy_results.append(policy_data)

                await session.commit()

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "total_results": len(policy_results),
                        "results": policy_results,
                        "search_criteria": {
                            "query": validated_data.get('query'),
                            "policy_category": validated_data.get('policy_category'),
                            "applies_to": validated_data.get('applies_to')
                        }
                    },
                    metadata={"operation": "search_restaurant_policy"}
                )

        except Exception as e:
            logger.error(f"Failed to search restaurant policies: {str(e)}")
            raise ToolError(
                f"Restaurant policy search failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class CreateQueryAnalyticsTool(ToolBase):
    """Create query analytics record for performance tracking."""

    def __init__(self):
        super().__init__(
            name="create_query_analytics",
            description="Create query analytics record",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['query_text', 'agent_name']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Optional fields
        validated_data['user_id'] = kwargs.get('user_id')
        validated_data['session_id'] = kwargs.get('session_id')
        validated_data['query_category'] = kwargs.get('query_category')
        validated_data['query_intent'] = kwargs.get('query_intent')
        validated_data['response_type'] = kwargs.get('response_type')
        validated_data['confidence_score'] = kwargs.get('confidence_score')
        validated_data['response_text'] = kwargs.get('response_text')
        validated_data['source_id'] = kwargs.get('source_id')
        validated_data['source_type'] = kwargs.get('source_type')
        validated_data['user_satisfied'] = kwargs.get('user_satisfied')
        validated_data['required_escalation'] = kwargs.get('required_escalation', False)
        validated_data['escalated_to'] = kwargs.get('escalated_to')
        validated_data['response_time_ms'] = kwargs.get('response_time_ms')
        validated_data['follow_up_questions'] = kwargs.get('follow_up_questions', 0)
        validated_data['fully_resolved'] = kwargs.get('fully_resolved', False)
        validated_data['resolution_method'] = kwargs.get('resolution_method')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Don't manually set ID - let SQLAlchemy event listener generate it automatically
                analytics = QueryAnalytics(
                    user_id=validated_data.get('user_id'),
                    session_id=validated_data.get('session_id'),
                    query_text=validated_data['query_text'],
                    query_category=validated_data.get('query_category'),
                    query_intent=validated_data.get('query_intent'),
                    agent_name=validated_data['agent_name'],
                    response_type=validated_data.get('response_type'),
                    confidence_score=Decimal(str(validated_data['confidence_score'])) if validated_data.get('confidence_score') else None,
                    response_text=validated_data.get('response_text'),
                    source_id=validated_data.get('source_id'),
                    source_type=validated_data.get('source_type'),
                    user_satisfied=validated_data.get('user_satisfied'),
                    required_escalation=validated_data['required_escalation'],
                    escalated_to=validated_data.get('escalated_to'),
                    response_time_ms=validated_data.get('response_time_ms'),
                    follow_up_questions=validated_data['follow_up_questions'],
                    fully_resolved=validated_data['fully_resolved'],
                    resolution_method=validated_data.get('resolution_method')
                )

                session.add(analytics)
                await session.commit()
                await session.refresh(analytics)  # Get the auto-generated ID

                analytics_data = serialize_output_with_schema(
                    QueryAnalyticsResponse,
                    analytics,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=analytics_data,
                    metadata={"operation": "create_query_analytics"}
                )

        except Exception as e:
            logger.error(f"Failed to create query analytics: {str(e)}")
            raise ToolError(
                f"Query analytics creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetFeaturedFAQsTool(ToolBase):
    """Get featured FAQ items for quick access."""

    def __init__(self):
        super().__init__(
            name="get_featured_faqs",
            description="Get featured FAQ items",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        validated_data = {
            'category': kwargs.get('category'),
            'limit': kwargs.get('limit', 10)
        }
        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                query = select(FAQ).where(
                    and_(
                        FAQ.is_featured == True,
                        FAQ.status == 'active'
                    )
                )

                if validated_data.get('category'):
                    query = query.where(FAQ.category == validated_data['category'])

                query = query.order_by(FAQ.display_order, FAQ.satisfaction_score.desc()).limit(validated_data['limit'])

                result = await session.execute(query)
                faqs = result.scalars().all()

                featured_faqs = []
                for faq in faqs:
                    # Serialize FAQ using schema
                    faq_data = serialize_output_with_schema(
                        FAQResponse,
                        faq,
                        self.name,
                        from_orm=True
                    )
                    featured_faqs.append(faq_data)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "total_featured": len(featured_faqs),
                        "featured_faqs": featured_faqs,
                        "category_filter": validated_data.get('category')
                    },
                    metadata={"operation": "get_featured_faqs"}
                )

        except Exception as e:
            logger.error(f"Failed to get featured FAQs: {str(e)}")
            raise ToolError(
                f"Failed to retrieve featured FAQs: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class UpdateFAQSatisfactionTool(ToolBase):
    """Update FAQ satisfaction score based on user feedback."""

    def __init__(self):
        super().__init__(
            name="update_faq_satisfaction",
            description="Update FAQ satisfaction score",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['faq_id', 'user_satisfaction']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or kwargs[field] is None:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Validate satisfaction (boolean or numeric)
        satisfaction = validated_data['user_satisfaction']
        if isinstance(satisfaction, bool):
            validated_data['satisfaction_score'] = 1.0 if satisfaction else 0.0
        elif isinstance(satisfaction, (int, float)):
            if satisfaction < 0 or satisfaction > 1:
                raise ValueError("Satisfaction score must be between 0 and 1")
            validated_data['satisfaction_score'] = float(satisfaction)
        else:
            raise ValueError("User satisfaction must be boolean or numeric (0-1)")

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                faq_query = select(FAQ).where(FAQ.id == validated_data['faq_id'])
                result = await session.execute(faq_query)
                faq = result.scalar_one_or_none()

                if not faq:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": "FAQ not found"
                        },
                        metadata={"operation": "update_faq_satisfaction"}
                    )

                # Update satisfaction score using simple averaging
                # In production, you might want more sophisticated weighting
                current_score = float(faq.satisfaction_score)
                new_feedback = validated_data['satisfaction_score']

                # Simple running average (can be improved with proper weighting)
                updated_score = (current_score + new_feedback) / 2

                faq.satisfaction_score = float(updated_score)
                await session.commit()

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "success": True,
                        "faq_id": validated_data['faq_id'],
                        "previous_score": current_score,
                        "new_score": updated_score,
                        "user_feedback": validated_data['satisfaction_score']
                    },
                    metadata={"operation": "update_faq_satisfaction"}
                )

        except Exception as e:
            logger.error(f"Failed to update FAQ satisfaction: {str(e)}")
            raise ToolError(
                f"FAQ satisfaction update failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


# Create tool instances for easy importing
create_faq_tool = CreateFAQTool()
search_faq_tool = SearchFAQTool()
get_faq_tool = GetFAQTool()
create_restaurant_policy_tool = CreateRestaurantPolicyTool()
search_restaurant_policy_tool = SearchRestaurantPolicyTool()
create_query_analytics_tool = CreateQueryAnalyticsTool()
get_featured_faqs_tool = GetFeaturedFAQsTool()
update_faq_satisfaction_tool = UpdateFAQSatisfactionTool()
