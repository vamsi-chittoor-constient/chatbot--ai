"""
Circuit Breaker Service for External API Protection
===================================================

Prevents cascading failures when external services (Razorpay, Twilio, OpenAI, WhatsApp) are down.

Circuit States:
- CLOSED: Normal operation (requests go through)
- OPEN: Service down (fast-fail, no requests sent)
- HALF_OPEN: Testing if service recovered (1 test request)

Example Usage:
    from app.services.circuit_breaker_service import (
        razorpay_breaker,
        openai_breaker,
        sms_breaker,
        whatsapp_breaker
    )

    @razorpay_breaker
    async def create_payment_order(...):
        # Protected Razorpay API call
        ...
"""

import pybreaker
from typing import Callable, Any
from app.core.logging_config import get_feature_logger

logger = get_feature_logger("circuit_breaker")


class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    """Custom listener to log circuit breaker state changes"""

    def __init__(self, service_name: str):
        self.service_name = service_name

    def state_change(self, cb: pybreaker.CircuitBreaker, old_state: pybreaker.CircuitBreakerState, new_state: pybreaker.CircuitBreakerState):
        """Log when circuit breaker state changes"""
        logger.warning(
            f"circuit_breaker_state_change: {self.service_name}",
            old_state=str(old_state),
            new_state=str(new_state),
            failure_count=cb.fail_counter,
        )

    def before_call(self, cb: pybreaker.CircuitBreaker, func: Callable, *args: Any, **kwargs: Any):
        """Log before making a call (only in HALF_OPEN state for debugging)"""
        if cb.current_state == pybreaker.STATE_HALF_OPEN:
            logger.info(
                f"circuit_breaker_testing_recovery: {self.service_name}",
                function=func.__name__,
            )

    def success(self, cb: pybreaker.CircuitBreaker):
        """Log successful call (only after HALF_OPEN test succeeds)"""
        if cb.current_state == pybreaker.STATE_CLOSED and cb.fail_counter == 0:
            logger.info(
                f"circuit_breaker_recovered: {self.service_name}",
            )

    def failure(self, cb: pybreaker.CircuitBreaker, exception: Exception):
        """Log failure"""
        logger.error(
            f"circuit_breaker_failure_recorded: {self.service_name}",
            exception=str(exception),
            failure_count=cb.fail_counter,
            fail_max=cb.fail_max,
        )

    def open(self, cb: pybreaker.CircuitBreaker):
        """Log when circuit opens (service marked as down)"""
        logger.error(
            f"circuit_breaker_opened: {self.service_name}",
            message=f"{self.service_name} circuit breaker OPENED - service is down, fast-failing requests",
            recovery_timeout=cb.recovery_timeout,
        )

    def half_open(self, cb: pybreaker.CircuitBreaker):
        """Log when circuit goes half-open (testing recovery)"""
        logger.info(
            f"circuit_breaker_half_open: {self.service_name}",
            message=f"{self.service_name} circuit breaker HALF_OPEN - testing service recovery",
        )


# ============================================================================
# Circuit Breaker Configurations for Each External Service
# ============================================================================

# OpenAI API Circuit Breaker
# Higher threshold because OpenAI is critical and usually reliable
openai_breaker = pybreaker.CircuitBreaker(
    fail_max=5,              # Open after 5 consecutive failures
    reset_timeout=120,       # Try recovery after 2 minutes (OpenAI might take time)
    name="OpenAI",
    listeners=[CircuitBreakerListener("OpenAI")],
    exclude=[
        KeyError,            # Don't count config errors as service failures
        ValueError,          # Don't count validation errors
        TypeError,           # Don't count type errors
    ],
)

# Razorpay Payment API Circuit Breaker
# Low threshold - fail fast for payment issues
razorpay_breaker = pybreaker.CircuitBreaker(
    fail_max=3,              # Open after 3 consecutive failures
    reset_timeout=60,        # Try recovery after 1 minute
    name="Razorpay",
    listeners=[CircuitBreakerListener("Razorpay")],
    exclude=[
        KeyError,
        ValueError,
        TypeError,
    ],
)

# SMS/Twilio Circuit Breaker
# Lower threshold - SMS is not as critical, fail fast
sms_breaker = pybreaker.CircuitBreaker(
    fail_max=3,              # Open after 3 consecutive failures
    reset_timeout=30,        # Try recovery after 30 seconds
    name="SMS",
    listeners=[CircuitBreakerListener("SMS/Twilio")],
    exclude=[
        KeyError,
        ValueError,
        TypeError,
    ],
)

# WhatsApp Business API Circuit Breaker
# Lower threshold - WhatsApp is optional
whatsapp_breaker = pybreaker.CircuitBreaker(
    fail_max=3,              # Open after 3 consecutive failures
    reset_timeout=30,        # Try recovery after 30 seconds
    name="WhatsApp",
    listeners=[CircuitBreakerListener("WhatsApp")],
    exclude=[
        KeyError,
        ValueError,
        TypeError,
    ],
)


# ============================================================================
# Helper Functions
# ============================================================================

def is_circuit_open(service_name: str) -> bool:
    """
    Check if a circuit breaker is currently open (service down).

    Args:
        service_name: Name of service ('openai', 'razorpay', 'sms', 'whatsapp')

    Returns:
        True if circuit is OPEN (service unavailable)
    """
    breakers = {
        'openai': openai_breaker,
        'razorpay': razorpay_breaker,
        'sms': sms_breaker,
        'whatsapp': whatsapp_breaker,
    }

    breaker = breakers.get(service_name.lower())
    if breaker:
        return breaker.current_state == pybreaker.STATE_OPEN
    return False


def get_circuit_status() -> dict:
    """
    Get status of all circuit breakers.

    Returns:
        Dictionary with status of each service
    """
    return {
        'openai': {
            'state': str(openai_breaker.current_state),
            'failure_count': openai_breaker.fail_counter,
            'fail_max': openai_breaker.fail_max,
        },
        'razorpay': {
            'state': str(razorpay_breaker.current_state),
            'failure_count': razorpay_breaker.fail_counter,
            'fail_max': razorpay_breaker.fail_max,
        },
        'sms': {
            'state': str(sms_breaker.current_state),
            'failure_count': sms_breaker.fail_counter,
            'fail_max': sms_breaker.fail_max,
        },
        'whatsapp': {
            'state': str(whatsapp_breaker.current_state),
            'failure_count': whatsapp_breaker.fail_counter,
            'fail_max': whatsapp_breaker.fail_max,
        },
    }


def reset_circuit_breaker(service_name: str) -> bool:
    """
    Manually reset a circuit breaker (admin operation).

    Args:
        service_name: Name of service to reset

    Returns:
        True if reset successful
    """
    breakers = {
        'openai': openai_breaker,
        'razorpay': razorpay_breaker,
        'sms': sms_breaker,
        'whatsapp': whatsapp_breaker,
    }

    breaker = breakers.get(service_name.lower())
    if breaker:
        breaker.call(lambda: None)  # Dummy successful call to close circuit
        logger.info(
            f"circuit_breaker_manually_reset: {service_name}",
        )
        return True
    return False
