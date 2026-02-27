"""
Customer Satisfaction Database Tools
===================================
SQLAlchemy-based tools for managing complaints, feedback, and satisfaction metrics.
Used by CustomerSatisfactionAgent for comprehensive satisfaction tracking.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import joinedload
from decimal import Decimal

from app.tools.base.tool_base import ToolBase, ToolResult, ToolStatus, ToolError
from app.core.database import db_manager
from app.features.feedback.models import (
    Complaint, Rating, CustomerFeedbackDetails, SatisfactionMetrics,
    ComplaintResolutionTemplate
)
from app.shared.models import User
from app.core.logging_config import get_logger
from app.utils.schema_tool_integration import serialize_output_with_schema, safe_isoformat
from app.features.feedback.schemas.satisfaction import (
    ComplaintResponse,
    FeedbackResponse,
    FeedbackDetailsResponse,
    SatisfactionMetricResponse,
    ComplaintResolutionTemplateResponse
)

logger = get_logger(__name__)


class CreateComplaintTool(ToolBase):
    """Create a new customer complaint with automated analysis."""

    def __init__(self):
        super().__init__(
            name="create_complaint",
            description="Create a new customer complaint with sentiment analysis",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['user_id', 'description', 'category']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # If title is provided, prepend it to description for context
        if kwargs.get('title'):
            validated_data['description'] = f"{kwargs['title']}: {validated_data['description']}"

        # Store title separately for email notification if provided
        validated_data['title'] = kwargs.get('title', 'Customer Complaint')

        # Optional fields (only those that exist in Complaint model)
        validated_data['priority'] = kwargs.get('priority', 'medium')
        validated_data['order_id'] = kwargs.get('order_id')
        validated_data['booking_id'] = kwargs.get('booking_id')
        validated_data['sentiment_score'] = kwargs.get('sentiment_score')
        validated_data['sentiment_label'] = kwargs.get('sentiment_label')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Don't manually set ID - let SQLAlchemy event listener generate it automatically
                # Only use fields that exist in the Complaint model
                complaint = Complaint(
                    user_id=validated_data['user_id'],
                    description=validated_data['description'],
                    category=validated_data['category'],
                    priority=validated_data['priority'],
                    order_id=validated_data.get('order_id'),
                    booking_id=validated_data.get('booking_id'),
                    sentiment_score=validated_data.get('sentiment_score'),
                    sentiment_label=validated_data.get('sentiment_label')
                )

                session.add(complaint)
                await session.commit()
                await session.refresh(complaint)  # Refresh to get the generated ID

                # COMMUNICATION PRIORITY FOR COMPLAINTS: Email + SMS EQUAL PRIORITY
                # For complaints, both channels have the same priority and should be used
                # This ensures the complaint is acknowledged through multiple channels
                sms_sent = False
                email_sent = False

                try:
                    # Get user details for notifications
                    from app.shared.models import User
                    user_query = select(User).where(User.id == validated_data['user_id'])
                    user_result = await session.execute(user_query)
                    user = user_result.scalar_one_or_none()

                    if user:
                        # Send SMS notification (Priority 1 - Equal)
                        if user.phone_number:
                            try:
                                from app.services.sms_service import get_sms_service
                                sms_service = get_sms_service()

                                sms_message = f"Your complaint #{complaint.id[:8]} has been registered with {validated_data['priority']} priority. We'll address this promptly. Thank you for your feedback."

                                sms_result = await sms_service.send_notification(
                                    phone_number=user.phone_number,
                                    message=sms_message,
                                    notification_type="complaint_confirmation"
                                )

                                sms_sent = sms_result.get("success", False)
                                if sms_sent:
                                    logger.info("Complaint confirmation SMS sent", complaint_id=complaint.id, phone=user.phone_number[-4:])
                            except Exception as e:
                                logger.error(f"Failed to send complaint SMS: {str(e)}")

                        # Send Email notification (Priority 1 - Equal)
                        if user.email:
                            try:
                                from app.services.email_manager_service import create_email_service
                                from app.services.email_template_service import get_email_template_service

                                # TODO: Create complaint_confirmation.html template
                                # For now, use a simple HTML message
                                html_content = f"""
                                <html>
                                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                                    <h2>Complaint Registered</h2>
                                    <p>Dear {user.full_name or 'Valued Customer'},</p>
                                    <p>We have received your complaint and take your concerns very seriously.</p>
                                    <p><strong>Complaint Details:</strong></p>
                                    <ul>
                                        <li><strong>ID:</strong> {complaint.id[:8]}</li>
                                        <li><strong>Title:</strong> {validated_data['title']}</li>
                                        <li><strong>Category:</strong> {validated_data['category']}</li>
                                        <li><strong>Priority:</strong> {validated_data['priority'].upper()}</li>
                                    </ul>
                                    <p>We will investigate this matter and respond to you shortly.</p>
                                    <p>Thank you for bringing this to our attention.</p>
                                    <br>
                                    <p>Best regards,<br>Restaurant AI Team</p>
                                </body>
                                </html>
                                """

                                email_service = create_email_service(session)
                                email_result = await email_service.send_email(
                                    to_email=user.email,
                                    subject=f"Complaint Registered - {complaint.id[:8]}",
                                    html_content=html_content,
                                    user_id=user.id
                                )

                                email_sent = email_result.get("success", False)
                                if email_sent:
                                    logger.info("Complaint confirmation email sent", complaint_id=complaint.id, email=user.email, email_log_id=email_result.get("email_log_id"))
                            except Exception as e:
                                logger.error(f"Failed to send complaint email: {str(e)}")

                except Exception as e:
                    logger.error(f"Failed to send complaint notifications: {str(e)}")
                    # Don't fail the complaint creation if notifications fail

                complaint_data = serialize_output_with_schema(
                    ComplaintResponse,
                    complaint,
                    self.name,
                    from_orm=True
                )
                # Add extra fields
                complaint_data['sms_sent'] = sms_sent
                complaint_data['email_sent'] = email_sent

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=complaint_data,
                    metadata={"operation": "create_complaint"}
                )

        except Exception as e:
            logger.error(f"Failed to create complaint: {str(e)}")
            raise ToolError(
                f"Complaint creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class UpdateComplaintTool(ToolBase):
    """Update complaint status and resolution details."""

    def __init__(self):
        super().__init__(
            name="update_complaint",
            description="Update complaint status, resolution, and assignment",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'complaint_id' not in kwargs or not kwargs['complaint_id']:
            raise ValueError("Missing required field: complaint_id")

        validated_data = {'complaint_id': kwargs['complaint_id']}

        # Optional update fields (only those that exist in Complaint model)
        validated_data['status'] = kwargs.get('status')
        validated_data['resolution'] = kwargs.get('resolution')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                complaint_query = select(Complaint).where(
                    Complaint.id == validated_data['complaint_id']
                )
                result = await session.execute(complaint_query)
                complaint = result.scalar_one_or_none()

                if not complaint:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "success": False,
                            "message": "Complaint not found"
                        },
                        metadata={"operation": "update_complaint"}
                    )

                # Update fields if provided (only those that exist in Complaint model)
                updates_made = []
                if validated_data.get('status'):
                    old_status = complaint.status
                    complaint.status = validated_data['status']
                    updates_made.append(f"status: {old_status}  {validated_data['status']}")

                if validated_data.get('resolution'):
                    complaint.resolution = validated_data['resolution']
                    updates_made.append("resolution added")

                await session.commit()

                complaint_data = serialize_output_with_schema(
                    ComplaintResponse,
                    complaint,
                    self.name,
                    from_orm=True
                )
                complaint_data['updates_made'] = updates_made

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=complaint_data,
                    metadata={"operation": "update_complaint"}
                )

        except Exception as e:
            logger.error(f"Failed to update complaint: {str(e)}")
            raise ToolError(
                f"Complaint update failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetComplaintTool(ToolBase):
    """Retrieve complaint details by ID."""

    def __init__(self):
        super().__init__(
            name="get_complaint",
            description="Get complaint details by ID",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'complaint_id' not in kwargs or not kwargs['complaint_id']:
            raise ValueError("Missing required field: complaint_id")
        return {'complaint_id': kwargs['complaint_id']}

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                complaint_query = select(Complaint).where(
                    Complaint.id == validated_data['complaint_id']
                ).options(joinedload(Complaint.user))

                result = await session.execute(complaint_query)
                complaint = result.scalar_one_or_none()

                if not complaint:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "found": False,
                            "message": "Complaint not found"
                        },
                        metadata={"operation": "get_complaint"}
                    )

                complaint_data = serialize_output_with_schema(
                    ComplaintResponse,
                    complaint,
                    self.name,
                    from_orm=True
                )
                complaint_data['found'] = True

                if complaint.user:
                    complaint_data["user"] = {
                        "user_id": str(complaint.user.id),
                        "full_name": complaint.user.full_name,
                        "email": complaint.user.email,
                        "phone": complaint.user.phone_number
                    }

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=complaint_data,
                    metadata={"operation": "get_complaint"}
                )

        except Exception as e:
            logger.error(f"Failed to get complaint: {str(e)}")
            raise ToolError(
                f"Failed to retrieve complaint: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class CreateFeedbackTool(ToolBase):
    """Create customer feedback record."""

    def __init__(self):
        super().__init__(
            name="create_feedback",
            description="Create customer feedback with ratings",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['user_id', 'rating', 'feedback_type']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or kwargs[field] is None:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Validate rating
        rating = validated_data['rating']
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            raise ValueError("Rating must be an integer between 1 and 5")

        # Optional fields
        validated_data['comment'] = kwargs.get('comment')
        validated_data['order_id'] = kwargs.get('order_id')
        validated_data['booking_id'] = kwargs.get('booking_id')
        validated_data['sentiment_score'] = kwargs.get('sentiment_score')
        validated_data['sentiment_label'] = kwargs.get('sentiment_label')
        validated_data['is_public'] = kwargs.get('is_public', True)

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Don't manually set ID - let SQLAlchemy event listener generate it automatically
                feedback = Rating(
                    user_id=validated_data['user_id'],
                    rating_type=validated_data['feedback_type'],
                    rating=validated_data['rating'],
                    comment=validated_data.get('comment'),
                    order_id=validated_data.get('order_id'),
                    booking_id=validated_data.get('booking_id'),
                    sentiment_score=validated_data.get('sentiment_score'),
                    sentiment_label=validated_data.get('sentiment_label'),
                    is_public=validated_data['is_public']
                )

                session.add(feedback)
                await session.commit()
                await session.refresh(feedback)  # Refresh to get the generated ID

                feedback_data = serialize_output_with_schema(
                    FeedbackResponse,
                    feedback,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=feedback_data,
                    metadata={"operation": "create_feedback"}
                )

        except Exception as e:
            logger.error(f"Failed to create feedback: {str(e)}")
            raise ToolError(
                f"Feedback creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class CreateSatisfactionMetricTool(ToolBase):
    """Create satisfaction metrics (NPS, CSAT, CES)."""

    def __init__(self):
        super().__init__(
            name="create_satisfaction_metric",
            description="Create satisfaction metrics for analytics",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['metric_type', 'score']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or kwargs[field] is None:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        # Validate metric type
        valid_types = ['nps', 'csat', 'ces', 'overall_experience']
        if validated_data['metric_type'] not in valid_types:
            raise ValueError(f"Invalid metric_type. Must be one of: {', '.join(valid_types)}")

        # Validate score
        score = validated_data['score']
        max_score = kwargs.get('max_score', 10.0)
        if score < 0 or score > max_score:
            raise ValueError(f"Score must be between 0 and {max_score}")

        # Optional fields
        validated_data['user_id'] = kwargs.get('user_id')
        validated_data['max_score'] = max_score
        validated_data['interaction_type'] = kwargs.get('interaction_type')
        validated_data['session_id'] = kwargs.get('session_id')
        validated_data['reference_id'] = kwargs.get('reference_id')
        validated_data['reference_type'] = kwargs.get('reference_type')
        validated_data['category'] = kwargs.get('category')
        validated_data['subcategory'] = kwargs.get('subcategory')
        validated_data['collection_method'] = kwargs.get('collection_method', 'ai_conversation')
        validated_data['additional_data'] = kwargs.get('additional_data', {})

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Don't manually set ID - let SQLAlchemy event listener generate it automatically
                metric = SatisfactionMetrics(
                    user_id=validated_data.get('user_id'),
                    metric_type=validated_data['metric_type'],
                    score=Decimal(str(validated_data['score'])),
                    max_score=Decimal(str(validated_data['max_score'])),
                    interaction_type=validated_data.get('interaction_type'),
                    session_id=validated_data.get('session_id'),
                    reference_id=validated_data.get('reference_id'),
                    reference_type=validated_data.get('reference_type'),
                    category=validated_data.get('category'),
                    subcategory=validated_data.get('subcategory'),
                    collection_method=validated_data['collection_method'],
                    additional_data=validated_data['additional_data']
                )

                session.add(metric)
                await session.commit()
                await session.refresh(metric)  # Refresh to get the generated ID

                metric_data = serialize_output_with_schema(
                    SatisfactionMetricResponse,
                    metric,
                    self.name,
                    from_orm=True
                )

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=metric_data,
                    metadata={"operation": "create_satisfaction_metric"}
                )

        except Exception as e:
            logger.error(f"Failed to create satisfaction metric: {str(e)}")
            raise ToolError(
                f"Satisfaction metric creation failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetComplaintResolutionTemplateTool(ToolBase):
    """Get appropriate resolution template for complaint category."""

    def __init__(self):
        super().__init__(
            name="get_complaint_resolution_template",
            description="Get resolution template for complaint category",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        required_fields = ['category']
        validated_data = {}

        for field in required_fields:
            if field not in kwargs or not kwargs[field]:
                raise ValueError(f"Missing required field: {field}")
            validated_data[field] = kwargs[field]

        validated_data['subcategory'] = kwargs.get('subcategory')
        validated_data['priority'] = kwargs.get('priority')

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                # Build query with category and optional subcategory
                query = select(ComplaintResolutionTemplate).where(
                    and_(
                        ComplaintResolutionTemplate.category == validated_data['category'],
                        ComplaintResolutionTemplate.is_active == True
                    )
                )

                if validated_data.get('subcategory'):
                    query = query.where(
                        ComplaintResolutionTemplate.subcategory == validated_data['subcategory']
                    )

                # Order by success rate and usage count
                query = query.order_by(
                    ComplaintResolutionTemplate.success_rate.desc(),
                    ComplaintResolutionTemplate.usage_count.desc()
                )

                result = await session.execute(query)
                template = result.scalar_one_or_none()

                if not template:
                    # Try to find a more general template
                    general_query = select(ComplaintResolutionTemplate).where(
                        and_(
                            ComplaintResolutionTemplate.category == validated_data['category'],
                            ComplaintResolutionTemplate.subcategory.is_(None),
                            ComplaintResolutionTemplate.is_active == True
                        )
                    ).order_by(ComplaintResolutionTemplate.success_rate.desc())

                    general_result = await session.execute(general_query)
                    template = general_result.scalar_one_or_none()

                if not template:
                    return ToolResult(
                        status=ToolStatus.SUCCESS,
                        data={
                            "found": False,
                            "message": f"No resolution template found for category '{validated_data['category']}'"
                        },
                        metadata={"operation": "get_complaint_resolution_template"}
                    )

                # Update usage count
                template.usage_count += 1
                await session.commit()

                template_data = serialize_output_with_schema(
                    ComplaintResolutionTemplateResponse,
                    template,
                    self.name,
                    from_orm=True
                )
                template_data['found'] = True

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data=template_data,
                    metadata={"operation": "get_complaint_resolution_template"}
                )

        except Exception as e:
            logger.error(f"Failed to get resolution template: {str(e)}")
            raise ToolError(
                f"Resolution template retrieval failed: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


class GetUserComplaintsTool(ToolBase):
    """Get all complaints for a specific user."""

    def __init__(self):
        super().__init__(
            name="get_user_complaints",
            description="Get all complaints for a specific user",
            max_retries=3,
            timeout_seconds=30
        )

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        if 'user_id' not in kwargs or not kwargs['user_id']:
            raise ValueError("Missing required field: user_id")

        validated_data = {
            'user_id': kwargs['user_id'],
            'status_filter': kwargs.get('status_filter'),
            'limit': kwargs.get('limit', 10)
        }

        return validated_data

    async def _execute_impl(self, **kwargs) -> ToolResult:
        try:
            validated_data = self.validate_input(**kwargs)

            async with db_manager.get_session() as session:
                query = select(Complaint).where(
                    Complaint.user_id == validated_data['user_id']
                )

                if validated_data.get('status_filter'):
                    query = query.where(Complaint.status == validated_data['status_filter'])

                query = query.order_by(Complaint.created_at.desc()).limit(validated_data['limit'])

                result = await session.execute(query)
                complaints = result.scalars().all()

                complaints_data = []
                for complaint in complaints:
                    complaint_summary = serialize_output_with_schema(
                        ComplaintResponse,
                        complaint,
                        self.name,
                        from_orm=True
                    )
                    # Truncate description for list view
                    if len(complaint.description) > 100:
                        complaint_summary['description'] = complaint.description[:100] + "..."
                    complaints_data.append(complaint_summary)

                return ToolResult(
                    status=ToolStatus.SUCCESS,
                    data={
                        "user_id": validated_data['user_id'],
                        "total_complaints": len(complaints_data),
                        "complaints": complaints_data,
                        "status_filter": validated_data.get('status_filter')
                    },
                    metadata={"operation": "get_user_complaints"}
                )

        except Exception as e:
            logger.error(f"Failed to get user complaints: {str(e)}")
            raise ToolError(
                f"Failed to retrieve user complaints: {str(e)}",
                tool_name=self.name,
                retry_suggested=True
            )


# Create tool instances for easy importing
create_complaint_tool = CreateComplaintTool()
update_complaint_tool = UpdateComplaintTool()
get_complaint_tool = GetComplaintTool()
create_feedback_tool = CreateFeedbackTool()
create_satisfaction_metric_tool = CreateSatisfactionMetricTool()
get_complaint_resolution_template_tool = GetComplaintResolutionTemplateTool()
get_user_complaints_tool = GetUserComplaintsTool()
