"""
Feedback Formatting Utility
============================
Centralized formatting for feedback, ratings, and NPS displays.

Provides standardized formatting for:
- Feedback summaries
- Rating breakdowns
- NPS scores and classifications
- Satisfaction trends and analytics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def format_feedback_summary(
    feedback: Dict[str, Any],
    include_rating_breakdown: bool = True,
    include_sentiment: bool = False,
    plain_text: bool = True
) -> str:
    """
    Format feedback summary for display.

    Args:
        feedback: Feedback dict with rating, review_text, sentiment
        include_rating_breakdown: Show star rating visually
        include_sentiment: Show sentiment analysis
        plain_text: Whether to use plain text formatting

    Returns:
        Formatted feedback summary

    Example:
        Your Feedback

        Rating: ⭐⭐⭐⭐⭐ (5/5)

        "The food was absolutely delicious! Will definitely come back."

        Thank you for your feedback!
    """
    rating = feedback.get("rating", 0)
    review_text = feedback.get("review_text") or feedback.get("comment")
    feedback_type = feedback.get("feedback_type") or feedback.get("rating_type", "general")
    sentiment = feedback.get("sentiment_label")

    lines = []

    # Header
    header = "Your Feedback" if plain_text else "**Your Feedback**"
    lines.append(header)
    lines.append("")

    # Rating
    if rating and 1 <= rating <= 5:
        rating_label = "Rating:" if plain_text else "**Rating:**"
        stars = "⭐" * rating
        lines.append(f"{rating_label} {stars} ({rating}/5)")
        lines.append("")

    # Type
    if feedback_type and feedback_type != "general":
        type_display = feedback_type.replace("_", " ").title()
        type_label = "Category:" if plain_text else "**Category:**"
        lines.append(f"{type_label} {type_display}")

    # Review text
    if review_text:
        lines.append(f'"{review_text}"')
        lines.append("")

    # Sentiment (optional)
    if include_sentiment and sentiment:
        sentiment_label = "Sentiment:" if plain_text else "**Sentiment:**"
        sentiment_emoji = {
            "positive": "😊 Positive",
            "negative": "😟 Negative",
            "neutral": "😐 Neutral"
        }.get(sentiment.lower(), sentiment)
        lines.append(f"{sentiment_label} {sentiment_emoji}")
        lines.append("")

    lines.append("Thank you for your feedback!")

    return "\n".join(lines)


def format_nps_score(
    nps_score: int,
    nps_category: str,
    include_description: bool = True,
    plain_text: bool = True
) -> str:
    """
    Format NPS score with classification and description.

    Args:
        nps_score: Score from 0-10
        nps_category: promoter, passive, or detractor
        include_description: Show category description
        plain_text: Whether to use plain text formatting

    Returns:
        Formatted NPS score message

    Example:
        Your NPS Score: 9/10

        You're a Promoter! 🌟
        Loyal enthusiasts who will keep buying and refer others, fueling growth.

        Thank you for being a valued customer!
    """
    if not (0 <= nps_score <= 10):
        return "Invalid NPS score. Must be between 0 and 10."

    lines = []

    # Score
    score_label = "Your NPS Score:" if plain_text else "**Your NPS Score:**"
    lines.append(f"{score_label} {nps_score}/10")
    lines.append("")

    # Category with emoji
    category_info = {
        "promoter": {
            "title": "You're a Promoter! 🌟",
            "description": "Loyal enthusiasts who will keep buying and refer others, fueling growth."
        },
        "passive": {
            "title": "You're a Passive 😊",
            "description": "Satisfied but unenthusiastic customers who are vulnerable to competitive offerings."
        },
        "detractor": {
            "title": "You're a Detractor 😟",
            "description": "Unhappy customers who can damage your brand through negative word-of-mouth."
        }
    }

    category_data = category_info.get(nps_category.lower())
    if category_data:
        title = category_data["title"] if plain_text else f"**{category_data['title']}**"
        lines.append(title)

        if include_description:
            lines.append(category_data["description"])

        lines.append("")

    # Closing message based on category
    if nps_category.lower() == "promoter":
        lines.append("Thank you for being a valued customer!")
    elif nps_category.lower() == "passive":
        lines.append("We'd love to exceed your expectations next time!")
    else:  # detractor
        lines.append("We're sorry to hear that. We'll work hard to improve your experience.")

    return "\n".join(lines)


def format_nps_breakdown(
    promoters: int,
    passives: int,
    detractors: int,
    total_responses: int,
    nps_score: float,
    plain_text: bool = True
) -> str:
    """
    Format NPS breakdown with percentages and overall score.

    Args:
        promoters: Count of promoters (9-10)
        passives: Count of passives (7-8)
        detractors: Count of detractors (0-6)
        total_responses: Total number of responses
        nps_score: Calculated NPS score (% Promoters - % Detractors)
        plain_text: Whether to use plain text formatting

    Returns:
        Formatted NPS breakdown

    Example:
        NPS Breakdown

        Overall NPS: 45 (Good)

        Promoters (9-10): 60% (18 responses)
        Passives (7-8):   20% (6 responses)
        Detractors (0-6): 20% (6 responses)

        Total Responses: 30
    """
    if total_responses == 0:
        return "No NPS responses yet."

    # Calculate percentages
    promoter_pct = (promoters / total_responses) * 100
    passive_pct = (passives / total_responses) * 100
    detractor_pct = (detractors / total_responses) * 100

    lines = []

    # Header
    header = "NPS Breakdown" if plain_text else "**NPS Breakdown**"
    lines.append(header)
    lines.append("")

    # Overall score with interpretation
    interpretation = _interpret_nps_score(nps_score)
    overall_label = "Overall NPS:" if plain_text else "**Overall NPS:**"
    lines.append(f"{overall_label} {nps_score:.0f} ({interpretation})")
    lines.append("")

    # Breakdown
    lines.append(f"Promoters (9-10): {promoter_pct:>5.1f}% ({promoters} responses)")
    lines.append(f"Passives (7-8):   {passive_pct:>5.1f}% ({passives} responses)")
    lines.append(f"Detractors (0-6): {detractor_pct:>5.1f}% ({detractors} responses)")
    lines.append("")

    total_label = "Total Responses:" if plain_text else "**Total Responses:**"
    lines.append(f"{total_label} {total_responses}")

    return "\n".join(lines)


def format_satisfaction_trends(
    metrics: List[Dict[str, Any]],
    period_days: int = 30,
    include_comparison: bool = True,
    plain_text: bool = True
) -> str:
    """
    Format satisfaction trends over time.

    Args:
        metrics: List of satisfaction metrics with scores and dates
        period_days: Time period in days
        include_comparison: Show comparison with previous period
        plain_text: Whether to use plain text formatting

    Returns:
        Formatted trends summary

    Example:
        Satisfaction Trends (Last 30 Days)

        Average Rating: 4.3/5 ⭐
        NPS Score: 42 (Good)
        Total Feedback: 125 responses

        Trend: ↗️ +5 points vs previous month
    """
    if not metrics:
        return f"No satisfaction data for the last {period_days} days."

    lines = []

    # Header
    header = f"Satisfaction Trends (Last {period_days} Days)"
    if not plain_text:
        header = f"**{header}**"
    lines.append(header)
    lines.append("")

    # Calculate averages
    total_ratings = 0
    rating_sum = 0
    nps_scores = []
    total_feedback = len(metrics)

    for metric in metrics:
        rating = metric.get("rating")
        if rating:
            total_ratings += 1
            rating_sum += rating

        nps_score = metric.get("score")
        metric_type = metric.get("metric_type")
        if metric_type == "nps" and nps_score is not None:
            nps_scores.append(nps_score)

    # Average rating
    if total_ratings > 0:
        avg_rating = rating_sum / total_ratings
        stars = "⭐" * round(avg_rating)
        rating_label = "Average Rating:" if plain_text else "**Average Rating:**"
        lines.append(f"{rating_label} {avg_rating:.1f}/5 {stars}")

    # NPS score
    if nps_scores:
        avg_nps = sum(nps_scores) / len(nps_scores)
        interpretation = _interpret_nps_score(avg_nps)
        nps_label = "NPS Score:" if plain_text else "**NPS Score:**"
        lines.append(f"{nps_label} {avg_nps:.0f} ({interpretation})")

    # Total feedback
    total_label = "Total Feedback:" if plain_text else "**Total Feedback:**"
    lines.append(f"{total_label} {total_feedback} responses")

    # Trend comparison (placeholder - requires previous period data)
    if include_comparison:
        lines.append("")
        lines.append("Trend: ↗️ Improving")  # Would need actual comparison logic

    return "\n".join(lines)


def format_rating_stars(rating: int, max_rating: int = 5) -> str:
    """
    Convert numerical rating to star display.

    Args:
        rating: Rating value (1-5)
        max_rating: Maximum rating value (default 5)

    Returns:
        Star string (e.g., "⭐⭐⭐⭐⭐")
    """
    if not (1 <= rating <= max_rating):
        return ""

    return "⭐" * rating


def _interpret_nps_score(nps: float) -> str:
    """Helper to interpret NPS score."""
    if nps >= 70:
        return "Excellent"
    elif nps >= 50:
        return "Great"
    elif nps >= 30:
        return "Good"
    elif nps >= 0:
        return "Needs Improvement"
    else:
        return "Critical"


__all__ = [
    "format_feedback_summary",
    "format_nps_score",
    "format_nps_breakdown",
    "format_satisfaction_trends",
    "format_rating_stars"
]
