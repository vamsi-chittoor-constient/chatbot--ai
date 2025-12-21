"""
Feedback Tools
==============
Tools for feedback collection and rating submission.
"""

from typing import Dict, Any, Optional
from langchain_core.tools import tool

from app.tools.database.satisfaction_tools import CreateFeedbackTool
from app.tools.base.tool_base import ToolStatus


@tool
async def create_feedback(
    user_id: str,
    rating: int,
    review_text: Optional[str] = None,
    feedback_type: str = "general",
    order_id: Optional[str] = None,
    booking_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create customer feedback with rating.

    Rating scale: 1-5 stars
    Feedback types: general, food, service, ambiance, value

    Args:
        user_id: Customer's user ID
        rating: Rating from 1 to 5 stars
        review_text: Optional written feedback
        feedback_type: Type of feedback (default: general)
        order_id: Optional order ID
        booking_id: Optional booking ID

    Returns:
        Dict with feedback_id and confirmation
    """
    # Validate rating
    if not (1 <= rating <= 5):
        return {
            "success": False,
            "message": "Rating must be between 1 and 5 stars"
        }

    feedback_tool = CreateFeedbackTool()

    result = await feedback_tool.execute(
        user_id=user_id,
        rating=rating,
        comment=review_text,
        rating_type=feedback_type,
        order_id=order_id,
        booking_id=booking_id
    )

    if result.status != ToolStatus.SUCCESS:
        return {
            "success": False,
            "message": result.error or "Failed to submit feedback"
        }

    # Generate appropriate response based on rating
    if rating >= 4:
        response_msg = f"Thank you for your {rating}-star rating! We're glad you enjoyed your experience."
    elif rating == 3:
        response_msg = f"Thank you for your feedback. We'll work to improve your experience next time."
    else:  # 1-2 stars
        response_msg = f"We're sorry your experience wasn't great. Your {rating}-star rating helps us improve."

    return {
        "success": True,
        "feedback_id": result.data.get("feedback_id"),
        "rating": rating,
        "feedback_type": feedback_type,
        "message": response_msg,
        "auto_complaint_created": False  # Will be set by agent if negative feedback triggers complaint
    }


@tool
async def create_detailed_rating(
    user_id: str,
    overall_rating: int,
    food_rating: Optional[int] = None,
    service_rating: Optional[int] = None,
    ambiance_rating: Optional[int] = None,
    value_rating: Optional[int] = None,
    review_text: Optional[str] = None,
    order_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create detailed multi-aspect rating.

    Allows rating different aspects separately (1-5 stars each).

    Args:
        user_id: Customer's user ID
        overall_rating: Overall experience rating (1-5)
        food_rating: Food quality rating (1-5)
        service_rating: Service quality rating (1-5)
        ambiance_rating: Ambiance rating (1-5)
        value_rating: Value for money rating (1-5)
        review_text: Optional written review
        order_id: Optional order ID

    Returns:
        Dict with feedback IDs and confirmation
    """
    # Validate ratings
    ratings = {
        "overall": overall_rating,
        "food": food_rating,
        "service": service_rating,
        "ambiance": ambiance_rating,
        "value": value_rating
    }

    for rating_type, rating_value in ratings.items():
        if rating_value is not None and not (1 <= rating_value <= 5):
            return {
                "success": False,
                "message": f"{rating_type.title()} rating must be between 1 and 5 stars"
            }

    feedback_ids = []

    # Create overall feedback
    overall_result = await create_feedback(
        user_id=user_id,
        rating=overall_rating,
        review_text=review_text,
        feedback_type="general",
        order_id=order_id
    )

    if overall_result["success"]:
        feedback_ids.append(overall_result["feedback_id"])

    # Create aspect-specific ratings
    aspect_map = {
        "food": food_rating,
        "service": service_rating,
        "ambiance": ambiance_rating,
        "value": value_rating
    }

    for aspect, rating in aspect_map.items():
        if rating:
            aspect_result = await create_feedback(
                user_id=user_id,
                rating=rating,
                feedback_type=aspect,
                order_id=order_id
            )
            if aspect_result["success"]:
                feedback_ids.append(aspect_result["feedback_id"])

    return {
        "success": True,
        "feedback_ids": feedback_ids,
        "overall_rating": overall_rating,
        "aspect_ratings": {k: v for k, v in aspect_map.items() if v is not None},
        "message": f"Thank you for your detailed {overall_rating}-star rating!"
    }


__all__ = [
    "create_feedback",
    "create_detailed_rating"
]
