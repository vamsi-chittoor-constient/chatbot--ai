"""
Email Template Service
======================
Jinja2-based email template rendering service for the Restaurant AI Assistant.

Provides pre-built templates for:
- Booking confirmations
- OTP verification
- Order confirmations/receipts
- Feedback requests
"""

from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound

from app.core.config import config

logger = structlog.get_logger(__name__)

# Template directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"


class EmailTemplateService:
    """
    Email template rendering service using Jinja2.
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize email template service.

        Args:
            templates_dir: Path to templates directory (defaults to app/templates/emails)
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR

        if not self.templates_dir.exists():
            logger.warning(
                "Email templates directory not found",
                path=str(self.templates_dir)
            )
            self.templates_dir.mkdir(parents=True, exist_ok=True)

        # Create Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )

        logger.info(
            "Email template service initialized",
            templates_dir=str(self.templates_dir)
        )

    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        restaurant_id: Optional[str] = None
    ) -> str:
        """
        Render email template with context.

        Args:
            template_name: Template filename (e.g., 'booking_confirmation.html')
            context: Template context variables
            restaurant_id: Restaurant ID for multi-tenant support (if None, uses default config)

        Returns:
            Rendered HTML string

        Raises:
            TemplateNotFound: If template doesn't exist
        """
        try:
            # Add default restaurant info to context (multi-tenant support)
            full_context = await self._get_default_context(restaurant_id)
            full_context.update(context)

            template = self.env.get_template(template_name)
            html = template.render(**full_context)

            logger.debug(
                "Template rendered successfully",
                template=template_name,
                restaurant_id=restaurant_id
            )

            return html

        except TemplateNotFound:
            logger.error(
                "Template not found",
                template=template_name,
                templates_dir=str(self.templates_dir)
            )
            raise

        except Exception as e:
            logger.error(
                "Failed to render template",
                template=template_name,
                error=str(e),
                exc_info=True
            )
            raise

    async def _get_default_context(self, restaurant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get default context variables for all templates.

        Args:
            restaurant_id: Restaurant ID for fetching restaurant-specific info from cache

        Returns:
            Dict with default restaurant info
        """
        # Multi-tenant: Fetch restaurant info from cache if restaurant_id provided
        if restaurant_id:
            try:
                from app.services.restaurant_cache_service import get_restaurant_config_cache

                # Get restaurant config from cache (cache-first, DB fallback)
                restaurant_cache = get_restaurant_config_cache()
                restaurant_data = await restaurant_cache.get_by_id(restaurant_id)

                if restaurant_data:
                    return {
                        "restaurant_name": restaurant_data.get("name") or config.APP_NAME,
                        "restaurant_email": restaurant_data.get("email") or config.EMAIL_FROM_ADDRESS or "info@restaurant.com",
                        "restaurant_phone": restaurant_data.get("phone") or "",
                        "restaurant_address": restaurant_data.get("address") or "",
                        # Social media URLs (optional) - can be added to DB later
                        "facebook_url": None,
                        "instagram_url": None,
                        "twitter_url": None,
                    }

            except Exception as e:
                logger.warning(
                    "Failed to fetch restaurant info for email template, using defaults",
                    restaurant_id=restaurant_id,
                    error=str(e)
                )

        # Fallback to default config if no restaurant_id or fetch failed
        return {
            "restaurant_name": config.APP_NAME,
            "restaurant_email": config.EMAIL_FROM_ADDRESS or "info@restaurant.com",
            "restaurant_phone": "",  # No default phone
            "restaurant_address": "",  # No default address
            # Social media URLs (optional)
            "facebook_url": None,
            "instagram_url": None,
            "twitter_url": None,
        }

    async def render_booking_confirmation(
        self,
        guest_name: str,
        confirmation_code: str,
        booking_datetime: str,
        party_size: int,
        table_number: Optional[str] = None,
        special_requests: Optional[str] = None,
        manage_booking_url: Optional[str] = None,
        restaurant_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Render booking confirmation email.

        Args:
            guest_name: Guest name
            confirmation_code: Booking confirmation code
            booking_datetime: Formatted date/time string
            party_size: Number of people
            table_number: Table number (optional)
            special_requests: Special requests (optional)
            manage_booking_url: URL to manage booking (optional)
            restaurant_id: Restaurant ID for multi-tenant support (optional)
            **kwargs: Additional context variables

        Returns:
            Rendered HTML email
        """
        context = {
            "guest_name": guest_name,
            "confirmation_code": confirmation_code,
            "booking_datetime": booking_datetime,
            "party_size": party_size,
            "table_number": table_number,
            "special_requests": special_requests,
            "manage_booking_url": manage_booking_url,
            **kwargs
        }

        return await self.render_template("booking_confirmation.html", context, restaurant_id)

    async def render_otp_verification(
        self,
        otp_code: str,
        expiry_minutes: int = 10,
        restaurant_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Render OTP verification email.

        Args:
            otp_code: One-time password code
            expiry_minutes: Minutes until OTP expires (default: 10)
            restaurant_id: Restaurant ID for multi-tenant support (optional)
            **kwargs: Additional context variables

        Returns:
            Rendered HTML email
        """
        context = {
            "otp_code": otp_code,
            "expiry_minutes": expiry_minutes,
            **kwargs
        }

        return await self.render_template("otp_verification.html", context, restaurant_id)

    async def render_order_confirmation(
        self,
        customer_name: str,
        order_number: str,
        order_type: str,
        order_time: str,
        order_items: list,
        subtotal: float,
        tax_amount: float,
        discount_amount: float,
        total_amount: float,
        estimated_ready_time: Optional[str] = None,
        payment_status: Optional[str] = None,
        payment_method: Optional[str] = None,
        track_order_url: Optional[str] = None,
        restaurant_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Render order confirmation/receipt email.

        Args:
            customer_name: Customer name
            order_number: Order number
            order_type: Order type (dine_in, takeout)
            order_time: Formatted order time
            order_items: List of order items with quantity, name, total_price
            subtotal: Order subtotal
            tax_amount: Tax amount
            discount_amount: Discount amount
            total_amount: Total amount
            estimated_ready_time: Estimated ready time (optional)
            payment_status: Payment status (optional)
            payment_method: Payment method (optional)
            track_order_url: URL to track order (optional)
            restaurant_id: Restaurant ID for multi-tenant support (optional)
            **kwargs: Additional context variables

        Returns:
            Rendered HTML email
        """
        context = {
            "customer_name": customer_name,
            "order_number": order_number,
            "order_type": order_type,
            "order_time": order_time,
            "order_items": order_items,
            "subtotal": subtotal,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "estimated_ready_time": estimated_ready_time,
            "payment_status": payment_status,
            "payment_method": payment_method,
            "track_order_url": track_order_url,
            **kwargs
        }

        return await self.render_template("order_confirmation.html", context, restaurant_id)

    async def render_feedback_request(
        self,
        customer_name: str,
        feedback_url: Optional[str] = None,
        recent_order: Optional[Dict[str, Any]] = None,
        quick_rating_links: Optional[Dict[int, str]] = None,
        restaurant_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Render feedback request email.

        Args:
            customer_name: Customer name
            feedback_url: URL to full feedback form (optional)
            recent_order: Recent order info with date, order_type (optional)
            quick_rating_links: Dict mapping ratings (1-5) to URLs (optional)
            restaurant_id: Restaurant ID for multi-tenant support (optional)
            **kwargs: Additional context variables

        Returns:
            Rendered HTML email
        """
        context = {
            "customer_name": customer_name,
            "feedback_url": feedback_url,
            "recent_order": recent_order,
            "quick_rating_links": quick_rating_links,
            **kwargs
        }

        return await self.render_template("feedback_request.html", context, restaurant_id)


# Global template service instance
_template_service: Optional[EmailTemplateService] = None


def get_email_template_service() -> EmailTemplateService:
    """
    Get global email template service instance (singleton).

    Returns:
        EmailTemplateService instance
    """
    global _template_service
    if _template_service is None:
        _template_service = EmailTemplateService()
    return _template_service
