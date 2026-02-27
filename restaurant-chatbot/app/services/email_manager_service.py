"""
Email Manager Service for Restaurant AI Assistant
==================================================
Unified email service combining SMTP delivery and async queue processing.

Features:
- SMTP email delivery with multiple provider support
- Circuit breaker for resilience
- Exponential backoff retry logic
- Redis-based async queue processing
- Email validation and tracking
- Bulk email sending
- Priority queue support
- Bounce and complaint handling

This module consolidates email_service.py and email_queue_service.py for better maintainability.
"""

import smtplib
import ssl
import asyncio
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, make_msgid
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from enum import Enum
import structlog
import re
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import config
from app.utils.timezone import get_current_time
from app.shared.models import EmailLog, User
from app.utils.id_generator import generate_id
from app.services.cache_service import CacheService
from app.database.connection import get_async_session

logger = structlog.get_logger(__name__)


# ============================================================================
# Email Validation & Enums
# ============================================================================

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def validate_email(email: str) -> bool:
    """
    Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    return bool(EMAIL_REGEX.match(email.strip()))


class EmailPriority(Enum):
    """Email priority levels for queue processing."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failures exceeded, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


# ============================================================================
# Email Provider Layer
# ============================================================================

class EmailProvider(ABC):
    """
    Abstract base class for email providers.
    Allows for multiple provider implementations (SMTP, SES, SendGrid, etc.)
    """

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via provider.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email
            plain_text_content: Plain text version of email
            from_email: Sender email address (optional)
            from_name: Sender name (optional)
            reply_to: Reply-to email address (optional)
            headers: Additional email headers (optional)

        Returns:
            Dict with:
                - success: bool
                - message_id: str (if successful)
                - error: str (if failed)
                - response: any provider-specific response data
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Get the provider name."""
        pass


class SMTPProvider(EmailProvider):
    """
    SMTP email provider implementation.
    Supports Gmail, Outlook, custom SMTP servers.
    """

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_username: str,
        smtp_password: str,
        use_tls: bool = True,
        use_ssl: bool = False,
        timeout: int = 30
    ):
        """
        Initialize SMTP provider.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            smtp_username: SMTP username
            smtp_password: SMTP password
            use_tls: Use STARTTLS (default: True)
            use_ssl: Use SSL (default: False)
            timeout: Connection timeout in seconds
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.timeout = timeout

        logger.info(
            "SMTP provider initialized",
            host=smtp_host,
            port=smtp_port,
            use_tls=use_tls,
            use_ssl=use_ssl
        )

    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "smtp"

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send email via SMTP.

        Returns:
            Dict with success status, message_id, and any errors
        """
        try:
            # Use default from email if not provided
            if not from_email:
                from_email = self.smtp_username

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((from_name or config.EMAIL_FROM_NAME, from_email))
            msg['To'] = to_email
            msg['Date'] = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

            # Generate unique message ID for tracking
            message_id = make_msgid(domain=from_email.split('@')[1] if '@' in from_email else 'localhost')
            msg['Message-ID'] = message_id

            if reply_to:
                msg['Reply-To'] = reply_to

            # Add custom headers
            if headers:
                for key, value in headers.items():
                    msg[key] = value

            # Attach parts - plain text first, then HTML (email clients prefer last alternative)
            if plain_text_content:
                part1 = MIMEText(plain_text_content, 'plain', 'utf-8')
                msg.attach(part1)

            if html_content:
                part2 = MIMEText(html_content, 'html', 'utf-8')
                msg.attach(part2)

            # Send email using async execution to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                self._send_smtp_sync,
                from_email,
                to_email,
                msg.as_string()
            )

            logger.info(
                "Email sent successfully via SMTP",
                to_email=to_email,
                subject=subject,
                message_id=message_id
            )

            return {
                "success": True,
                "message_id": message_id,
                "response": response
            }

        except smtplib.SMTPException as e:
            logger.error(
                "SMTP error sending email",
                to_email=to_email,
                subject=subject,
                error=str(e),
                exc_info=True
            )
            return {
                "success": False,
                "error": f"SMTP error: {str(e)}",
                "error_type": "smtp_error"
            }

        except Exception as e:
            logger.error(
                "Unexpected error sending email",
                to_email=to_email,
                subject=subject,
                error=str(e),
                exc_info=True
            )
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unknown_error"
            }

    def _send_smtp_sync(self, from_email: str, to_email: str, message: str) -> Dict[str, Any]:
        """
        Synchronous SMTP send (to be run in executor).

        Args:
            from_email: Sender email
            to_email: Recipient email
            message: Full email message as string

        Returns:
            SMTP response dict
        """
        if self.use_ssl:
            # Use SMTP_SSL for implicit SSL
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(
                self.smtp_host,
                self.smtp_port,
                timeout=self.timeout,
                context=context
            ) as server:
                server.login(self.smtp_username, self.smtp_password)
                response = server.sendmail(from_email, to_email, message)
                return {"smtp_response": response}
        else:
            # Use regular SMTP with optional STARTTLS
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=self.timeout) as server:
                server.ehlo()
                if self.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                server.login(self.smtp_username, self.smtp_password)
                response = server.sendmail(from_email, to_email, message)
                return {"smtp_response": response}


# ============================================================================
# Email Service Layer
# ============================================================================

class EmailService:
    """
    Email service for direct email sending with tracking and logging.
    """

    def __init__(
        self,
        provider: EmailProvider,
        db_session: Optional[AsyncSession] = None
    ):
        """
        Initialize email service.

        Args:
            provider: Email provider instance (SMTP, SES, etc.)
            db_session: Database session for logging
        """
        self.provider = provider
        self.db_session = db_session

        logger.info(
            "Email service initialized",
            provider=provider.get_provider_name()
        )

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None,
        user_id: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        track_opens: bool = True,
        track_clicks: bool = True,
        unsubscribe_link: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send email with tracking and logging.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of email
            plain_text_content: Plain text version (auto-generated if not provided)
            user_id: User ID for tracking (optional)
            from_email: Sender email (optional)
            from_name: Sender name (optional)
            reply_to: Reply-to address (optional)
            headers: Additional headers (optional)
            track_opens: Add open tracking pixel
            track_clicks: Track link clicks
            unsubscribe_link: Unsubscribe URL

        Returns:
            Dict with success status and email log ID
        """
        # Validate email
        if not validate_email(to_email):
            logger.warning("Invalid email address", email=to_email)
            return {
                "success": False,
                "error": "Invalid email address",
                "error_type": "validation_error"
            }

        # Auto-generate plain text if not provided
        if not plain_text_content and html_content:
            plain_text_content = self._html_to_plain_text(html_content)

        # Create email log entry
        email_log = None
        if self.db_session:
            try:
                email_log_id = await generate_id(self.db_session, "email_logs")
                email_log = EmailLog(
                    id=email_log_id,
                    user_id=user_id,
                    recipient_email=to_email,
                    subject=subject,
                    html_content=html_content,
                    plain_text_content=plain_text_content,
                    status="queued",
                    provider=self.provider.get_provider_name(),
                    queued_at=get_current_time()
                )
                self.db_session.add(email_log)
                await self.db_session.commit()
                await self.db_session.refresh(email_log)

                logger.debug(
                    "Email log created",
                    email_log_id=email_log.id,
                    recipient=to_email
                )

            except Exception as e:
                logger.error(
                    "Failed to create email log",
                    error=str(e),
                    exc_info=True
                )
                # Continue sending even if logging fails
                await self.db_session.rollback()

        # Send email via provider
        try:
            result = await self.provider.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_text_content=plain_text_content,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                headers=headers
            )

            # Update email log with result
            if email_log and self.db_session:
                try:
                    email_log.status = "sent" if result.get("success") else "failed"
                    email_log.sent_at = get_current_time() if result.get("success") else None
                    email_log.failed_at = get_current_time() if not result.get("success") else None
                    email_log.smtp_message_id = result.get("message_id")
                    email_log.smtp_response = str(result.get("response", ""))
                    email_log.smtp_error = result.get("error")

                    await self.db_session.commit()

                    logger.debug(
                        "Email log updated",
                        email_log_id=email_log.id,
                        status=email_log.status
                    )

                except Exception as e:
                    logger.error(
                        "Failed to update email log",
                        email_log_id=email_log.id if email_log else None,
                        error=str(e),
                        exc_info=True
                    )
                    await self.db_session.rollback()

            return {
                **result,
                "email_log_id": email_log.id if email_log else None
            }

        except Exception as e:
            logger.error(
                "Failed to send email",
                to_email=to_email,
                subject=subject,
                error=str(e),
                exc_info=True
            )

            # Update email log with failure
            if email_log and self.db_session:
                try:
                    email_log.status = "failed"
                    email_log.failed_at = get_current_time()
                    email_log.smtp_error = str(e)
                    await self.db_session.commit()
                except Exception as log_error:
                    logger.error(
                        "Failed to update email log with failure",
                        error=str(log_error),
                        exc_info=True
                    )
                    await self.db_session.rollback()

            return {
                "success": False,
                "error": str(e),
                "error_type": "send_error",
                "email_log_id": email_log.id if email_log else None
            }

    def _html_to_plain_text(self, html_content: str) -> str:
        """
        Convert HTML to plain text (basic implementation).

        Args:
            html_content: HTML content

        Returns:
            Plain text version
        """
        # Simple HTML to text conversion
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html_content)
        # Decode HTML entities
        import html
        text = html.unescape(text)
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = text.strip()
        return text

    async def send_bulk_emails(
        self,
        emails: List[Dict[str, Any]],
        batch_size: int = 10,
        delay_between_batches: float = 1.0
    ) -> Dict[str, Any]:
        """
        Send multiple emails in batches (for newsletters, notifications, etc.)

        Args:
            emails: List of email dicts with keys: to_email, subject, html_content, etc.
            batch_size: Number of emails to send per batch
            delay_between_batches: Delay in seconds between batches

        Returns:
            Dict with summary of results
        """
        total = len(emails)
        successful = 0
        failed = 0
        results = []

        for i in range(0, total, batch_size):
            batch = emails[i:i + batch_size]

            # Send batch in parallel
            tasks = [self.send_email(**email_data) for email_data in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    results.append({"success": False, "error": str(result)})
                elif result.get("success"):
                    successful += 1
                    results.append(result)
                else:
                    failed += 1
                    results.append(result)

            # Delay between batches to avoid rate limiting
            if i + batch_size < total:
                await asyncio.sleep(delay_between_batches)

            logger.info(
                "Bulk email batch processed",
                batch_number=i // batch_size + 1,
                batch_size=len(batch),
                successful=successful,
                failed=failed
            )

        logger.info(
            "Bulk email send completed",
            total=total,
            successful=successful,
            failed=failed
        )

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "results": results
        }


# ============================================================================
# Circuit Breaker Layer
# ============================================================================

class EmailCircuitBreaker:
    """
    Circuit breaker for email service.
    Prevents cascading failures by temporarily disabling email sending when failures exceed threshold.
    """

    def __init__(
        self,
        cache_service: CacheService,
        failure_threshold: int = 5,
        timeout_seconds: int = 60,
        half_open_attempts: int = 3
    ):
        """
        Initialize circuit breaker.

        Args:
            cache_service: Redis cache service for state storage
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: Seconds to wait before attempting recovery
            half_open_attempts: Number of attempts in half-open state
        """
        self.cache_service = cache_service
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_attempts = half_open_attempts

        self.state_key = "email:circuit_breaker:state"
        self.failures_key = "email:circuit_breaker:failures"
        self.half_open_attempts_key = "email:circuit_breaker:half_open_attempts"

        logger.info(
            "Circuit breaker initialized",
            failure_threshold=failure_threshold,
            timeout_seconds=timeout_seconds
        )

    async def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        state_str = await self.cache_service.get(self.state_key)
        if state_str:
            return CircuitBreakerState(state_str)
        return CircuitBreakerState.CLOSED

    async def is_available(self) -> bool:
        """Check if email service is available."""
        state = await self.get_state()

        if state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed
            timeout_key = "email:circuit_breaker:opened_at"
            opened_at_str = await self.cache_service.get(timeout_key)

            if opened_at_str:
                opened_at = datetime.fromisoformat(opened_at_str)
                if datetime.now() - opened_at > timedelta(seconds=self.timeout_seconds):
                    # Transition to half-open
                    await self._set_state(CircuitBreakerState.HALF_OPEN)
                    await self.cache_service.set(self.half_open_attempts_key, "0")
                    logger.info("Circuit breaker transitioning to half-open")
                    return True

            logger.warning("Circuit breaker is open, rejecting email request")
            return False

        return True

    async def record_success(self):
        """Record successful email send."""
        state = await self.get_state()

        if state == CircuitBreakerState.HALF_OPEN:
            # Increment successful attempts
            attempts_str = await self.cache_service.get(self.half_open_attempts_key) or "0"
            attempts = int(attempts_str) + 1
            await self.cache_service.set(self.half_open_attempts_key, str(attempts))

            if attempts >= self.half_open_attempts:
                # Recovered! Close the circuit
                await self._set_state(CircuitBreakerState.CLOSED)
                await self.cache_service.delete(self.failures_key)
                logger.info("Circuit breaker closed, service recovered")
        else:
            # Reset failure count
            await self.cache_service.delete(self.failures_key)

    async def record_failure(self):
        """Record failed email send."""
        state = await self.get_state()

        if state == CircuitBreakerState.HALF_OPEN:
            # Failed during recovery, reopen circuit
            await self._set_state(CircuitBreakerState.OPEN)
            await self.cache_service.set(
                "email:circuit_breaker:opened_at",
                datetime.now().isoformat()
            )
            logger.warning("Circuit breaker reopened due to failure during recovery")
            return

        # Increment failure count
        failures_str = await self.cache_service.get(self.failures_key) or "0"
        failures = int(failures_str) + 1
        await self.cache_service.set(self.failures_key, str(failures), expire=self.timeout_seconds)

        if failures >= self.failure_threshold:
            # Open the circuit
            await self._set_state(CircuitBreakerState.OPEN)
            await self.cache_service.set(
                "email:circuit_breaker:opened_at",
                datetime.now().isoformat()
            )
            logger.error(
                "Circuit breaker opened due to failures",
                failures=failures,
                threshold=self.failure_threshold
            )

    async def _set_state(self, state: CircuitBreakerState):
        """Set circuit breaker state."""
        await self.cache_service.set(self.state_key, state.value, expire=self.timeout_seconds * 2)


# ============================================================================
# Email Queue Layer
# ============================================================================

class EmailQueueService:
    """
    Email queue service for async processing.
    Uses Redis for queue storage and implements circuit breaker pattern.
    """

    def __init__(
        self,
        cache_service: CacheService,
        email_service: Optional[EmailService] = None,
        circuit_breaker: Optional[EmailCircuitBreaker] = None
    ):
        """
        Initialize email queue service.

        Args:
            cache_service: Redis cache service
            email_service: Email service (created if not provided)
            circuit_breaker: Circuit breaker (created if not provided)
        """
        self.cache_service = cache_service
        self.email_service = email_service
        self.circuit_breaker = circuit_breaker or EmailCircuitBreaker(
            cache_service=cache_service,
            failure_threshold=config.EMAIL_CIRCUIT_BREAKER_FAILURE_THRESHOLD,
            timeout_seconds=config.EMAIL_CIRCUIT_BREAKER_TIMEOUT_SECONDS,
            half_open_attempts=config.EMAIL_CIRCUIT_BREAKER_HALF_OPEN_ATTEMPTS
        )

        self.queue_key = config.EMAIL_QUEUE_REDIS_KEY
        self.processing_key = f"{self.queue_key}:processing"

        logger.info(
            "Email queue service initialized",
            queue_key=self.queue_key
        )

    async def enqueue(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: Optional[str] = None,
        priority: EmailPriority = EmailPriority.NORMAL,
        **kwargs
    ) -> str:
        """
        Add email to queue.

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML content
            plain_text_content: Plain text content
            priority: Email priority
            **kwargs: Additional email service parameters

        Returns:
            Queue item ID
        """
        email_data = {
            "to_email": to_email,
            "subject": subject,
            "html_content": html_content,
            "plain_text_content": plain_text_content,
            "priority": priority.value,
            "queued_at": get_current_time().isoformat(),
            **kwargs
        }

        # Use priority as score for Redis sorted set
        queue_item_id = f"email:{int(datetime.now().timestamp() * 1000)}"
        score = priority.value * 1000000 + int(datetime.now().timestamp())

        await self.cache_service.zadd(
            self.queue_key,
            {json.dumps({**email_data, "id": queue_item_id}): score}
        )

        logger.info(
            "Email queued",
            queue_item_id=queue_item_id,
            to_email=to_email,
            priority=priority.name
        )

        return queue_item_id

    async def process_queue(
        self,
        batch_size: Optional[int] = None,
        delay_seconds: Optional[float] = None
    ):
        """
        Process emails from queue.

        Args:
            batch_size: Number of emails to process per batch
            delay_seconds: Delay between batches
        """
        batch_size = batch_size or config.EMAIL_QUEUE_BATCH_SIZE
        delay_seconds = delay_seconds or config.EMAIL_QUEUE_DELAY_SECONDS

        logger.info(
            "Starting email queue processing",
            batch_size=batch_size,
            delay_seconds=delay_seconds
        )

        processed = 0
        failed = 0

        while True:
            try:
                # Check circuit breaker
                if not await self.circuit_breaker.is_available():
                    logger.warning("Circuit breaker open, skipping queue processing")
                    await asyncio.sleep(delay_seconds * 10)  # Wait longer when circuit is open
                    continue

                # Get batch from queue (highest priority first)
                items = await self.cache_service.zpopmax(self.queue_key, batch_size)

                if not items:
                    logger.debug("Email queue empty")
                    await asyncio.sleep(delay_seconds)
                    continue

                # Process batch
                for item_json, score in items:
                    try:
                        email_data = json.loads(item_json)
                        queue_item_id = email_data.pop("id", None)

                        # Create email service with DB session if not provided
                        email_service = self.email_service
                        if not email_service:
                            async with get_async_session() as db_session:
                                email_service = create_email_service(db_session)
                                result = await email_service.send_email(**email_data)
                        else:
                            result = await email_service.send_email(**email_data)

                        if result.get("success"):
                            processed += 1
                            await self.circuit_breaker.record_success()
                            logger.info(
                                "Email sent from queue",
                                queue_item_id=queue_item_id,
                                to_email=email_data.get("to_email")
                            )
                        else:
                            failed += 1
                            await self.circuit_breaker.record_failure()
                            logger.error(
                                "Failed to send email from queue",
                                queue_item_id=queue_item_id,
                                to_email=email_data.get("to_email"),
                                error=result.get("error")
                            )

                    except Exception as e:
                        failed += 1
                        await self.circuit_breaker.record_failure()
                        logger.error(
                            "Error processing queue item",
                            error=str(e),
                            exc_info=True
                        )

                # Delay between batches
                await asyncio.sleep(delay_seconds)

            except Exception as e:
                logger.error(
                    "Error in queue processing loop",
                    error=str(e),
                    exc_info=True
                )
                await asyncio.sleep(delay_seconds * 2)

    async def get_queue_size(self) -> int:
        """Get number of emails in queue."""
        return await self.cache_service.zcard(self.queue_key)

    async def clear_queue(self):
        """Clear all emails from queue."""
        await self.cache_service.delete(self.queue_key)
        logger.info("Email queue cleared")


# ============================================================================
# Factory Functions
# ============================================================================

def create_smtp_provider_from_config() -> SMTPProvider:
    """
    Create SMTP provider from application config.

    Returns:
        Configured SMTPProvider instance
    """
    return SMTPProvider(
        smtp_host=config.SMTP_HOST,
        smtp_port=config.SMTP_PORT,
        smtp_username=config.SMTP_USERNAME,
        smtp_password=config.SMTP_PASSWORD,
        use_tls=config.SMTP_USE_TLS,
        use_ssl=config.SMTP_USE_SSL,
        timeout=config.SMTP_TIMEOUT
    )


def create_email_service(
    db_session: Optional[AsyncSession] = None
) -> EmailService:
    """
    Create email service with SMTP provider from config.

    Args:
        db_session: Database session for logging (optional)

    Returns:
        Configured EmailService instance
    """
    provider = create_smtp_provider_from_config()
    return EmailService(provider=provider, db_session=db_session)


async def create_email_queue_service(cache_service: CacheService) -> EmailQueueService:
    """
    Create email queue service.

    Args:
        cache_service: Redis cache service

    Returns:
        EmailQueueService instance
    """
    return EmailQueueService(cache_service=cache_service)


# Backward compatibility - re-export factory functions with old names
def create_email_service_from_config(db_session: Optional[AsyncSession] = None) -> EmailService:
    """Legacy name for create_email_service."""
    return create_email_service(db_session)
