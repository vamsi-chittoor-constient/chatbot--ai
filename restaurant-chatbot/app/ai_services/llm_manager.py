"""
LLM Manager Service - Unified Multi-Account Resource Manager
=============================================================
Manages 20 OpenAI accounts with per-model resource tracking and cooldown mechanism.
Supports both gpt-4o and gpt-4o-mini with separate rate limit tracking per account.

Features:
- Validates API keys on startup (checks for credits)
- Only adds accounts with valid credits to the pool
- Round-robin load balancing across valid accounts
"""

import os
import asyncio
from datetime import datetime, timedelta
from collections import deque
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
import structlog
from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from openai import OpenAI, AuthenticationError, RateLimitError, APIError

logger = structlog.get_logger(__name__)


def validate_api_key(api_key: str, account_num: int) -> Tuple[bool, str]:
    """
    Validate an API key by making a minimal completion call.
    This actually verifies the account has credits (not just valid key).

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        client = OpenAI(api_key=api_key)
        # Make a minimal completion call to verify credits exist
        # Uses gpt-4o-mini (cheapest) with max_tokens=1 for minimal cost
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "hi"}],
            max_tokens=1
        )
        # If we get here, the account has credits
        return True, ""
    except AuthenticationError as e:
        return False, f"Invalid API key: {str(e)[:50]}"
    except RateLimitError as e:
        # Rate limit could mean quota exceeded or just rate limited
        error_msg = str(e).lower()
        if "quota" in error_msg or "exceeded" in error_msg or "billing" in error_msg or "insufficient_quota" in error_msg:
            return False, f"No credits/quota: {str(e)[:50]}"
        # Rate limited but key is valid (temporary rate limit)
        return True, ""
    except APIError as e:
        error_msg = str(e).lower()
        if "insufficient_quota" in error_msg or "billing" in error_msg or "quota" in error_msg:
            return False, f"No credits: {str(e)[:50]}"
        # Other API errors - assume key might be valid
        logger.warning("api_key_validation_uncertain", account=account_num, error=str(e)[:50])
        return True, ""
    except Exception as e:
        logger.warning("api_key_validation_error", account=account_num, error=str(e)[:50])
        return False, f"Validation error: {str(e)[:50]}"


class CooldownState(Enum):
    """Account cooldown states"""
    AVAILABLE = "available"
    COOLING_DOWN = "cooling_down"


class ModelUsageTracker:
    """
    Track usage for a specific model (gpt-4o or gpt-4o-mini) in sliding window.

    Monitors:
    - Requests per minute (RPM)
    - Tokens per minute (TPM)
    - Buffer thresholds to prevent hitting limits
    - Cooldown state
    """

    def __init__(
        self,
        model_name: str,
        rpm_limit: int,
        tpm_limit: int,
        buffer_percent: int = 80,
        provider_name: str = "unknown"
    ):
        """
        Initialize model-specific usage tracker.

        Args:
            model_name: Model name (gpt-4o or gpt-4o-mini)
            rpm_limit: Maximum requests per minute for this model
            tpm_limit: Maximum tokens per minute for this model
            buffer_percent: Switch at this % of capacity (default 80%)
            provider_name: Name for logging (e.g., "account_1_gpt4o")
        """
        self.model_name = model_name
        self.rpm_limit = rpm_limit
        self.tpm_limit = tpm_limit
        self.buffer_percent = buffer_percent
        self.provider_name = provider_name

        # Sliding window: (timestamp, token_count)
        self.requests: deque = deque()

        # Cooldown state
        self.cooldown_state = CooldownState.AVAILABLE
        self.cooldown_until: Optional[datetime] = None

        logger.info(
            "model_tracker_initialized",
            provider=provider_name,
            model=model_name,
            rpm_limit=rpm_limit,
            tpm_limit=tpm_limit,
            buffer_percent=buffer_percent
        )

    def _clean_old_requests(self):
        """Remove requests older than 1 minute"""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)

        while self.requests and self.requests[0][0] < one_minute_ago:
            self.requests.popleft()

    def _check_cooldown_expired(self):
        """Check if cooldown period has expired and update state"""
        if self.cooldown_state == CooldownState.COOLING_DOWN and self.cooldown_until:
            if datetime.now() >= self.cooldown_until:
                # Check if usage has dropped below buffer
                self._clean_old_requests()
                current_rpm = len(self.requests)
                current_tpm = sum(tokens for _, tokens in self.requests)

                rpm_utilization = (current_rpm / self.rpm_limit) * 100
                tpm_utilization = (current_tpm / self.tpm_limit) * 100

                if rpm_utilization < self.buffer_percent and tpm_utilization < self.buffer_percent:
                    self.cooldown_state = CooldownState.AVAILABLE
                    self.cooldown_until = None
                    logger.info(
                        "cooldown_expired_released",
                        provider=self.provider_name,
                        rpm_utilization=round(rpm_utilization, 2),
                        tpm_utilization=round(tpm_utilization, 2)
                    )
                else:
                    # Still at capacity - extend cooldown
                    self.cooldown_until = datetime.now() + timedelta(seconds=30)
                    logger.warning(
                        "cooldown_extended_still_at_capacity",
                        provider=self.provider_name,
                        rpm_utilization=round(rpm_utilization, 2),
                        tpm_utilization=round(tpm_utilization, 2),
                        extended_until=self.cooldown_until.isoformat()
                    )

    def can_handle_request(self, estimated_tokens: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if we can handle request without exceeding limits.

        Args:
            estimated_tokens: Estimated tokens for this request

        Returns:
            Tuple of (can_handle: bool, usage_stats: dict)
        """
        # Check if in cooldown
        self._check_cooldown_expired()

        if self.cooldown_state == CooldownState.COOLING_DOWN:
            return False, {
                "provider": self.provider_name,
                "model": self.model_name,
                "can_handle": False,
                "reason": "cooling_down",
                "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None
            }

        self._clean_old_requests()

        # Calculate current usage
        current_rpm = len(self.requests)
        current_tpm = sum(tokens for _, tokens in self.requests)

        # Calculate thresholds
        rpm_threshold = self.rpm_limit * (self.buffer_percent / 100)
        tpm_threshold = self.tpm_limit * (self.buffer_percent / 100)

        # Check if adding this request would exceed thresholds
        would_exceed_rpm = (current_rpm + 1) > rpm_threshold
        would_exceed_tpm = (current_tpm + estimated_tokens) > tpm_threshold

        can_handle = not (would_exceed_rpm or would_exceed_tpm)

        usage_stats = {
            "provider": self.provider_name,
            "model": self.model_name,
            "current_rpm": current_rpm,
            "rpm_limit": self.rpm_limit,
            "rpm_threshold": int(rpm_threshold),
            "rpm_utilization_percent": round((current_rpm / self.rpm_limit * 100), 2),
            "current_tpm": current_tpm,
            "tpm_limit": self.tpm_limit,
            "tpm_threshold": int(tpm_threshold),
            "tpm_utilization_percent": round((current_tpm / self.tpm_limit * 100), 2),
            "estimated_request_tokens": estimated_tokens,
            "can_handle": can_handle,
            "would_exceed_rpm": would_exceed_rpm,
            "would_exceed_tpm": would_exceed_tpm,
            "cooldown_state": self.cooldown_state.value
        }

        return can_handle, usage_stats

    def record_request(self, token_count: int, cooldown_seconds: int = 60):
        """
        Record a successful request and check if cooldown should be triggered.

        Args:
            token_count: Actual tokens used in the request
            cooldown_seconds: Cooldown duration if buffer exceeded
        """
        self.requests.append((datetime.now(), token_count))

        # Check if we should enter cooldown
        self._clean_old_requests()
        current_rpm = len(self.requests)
        current_tpm = sum(tokens for _, tokens in self.requests)

        rpm_utilization = (current_rpm / self.rpm_limit) * 100
        tpm_utilization = (current_tpm / self.tpm_limit) * 100

        # If we've hit or exceeded buffer, enter cooldown
        if rpm_utilization >= self.buffer_percent or tpm_utilization >= self.buffer_percent:
            self.cooldown_state = CooldownState.COOLING_DOWN
            self.cooldown_until = datetime.now() + timedelta(seconds=cooldown_seconds)

            logger.warning(
                "cooldown_triggered",
                provider=self.provider_name,
                model=self.model_name,
                rpm_utilization=round(rpm_utilization, 2),
                tpm_utilization=round(tpm_utilization, 2),
                cooldown_until=self.cooldown_until.isoformat(),
                cooldown_seconds=cooldown_seconds
            )
        else:
            logger.debug(
                "request_recorded",
                provider=self.provider_name,
                model=self.model_name,
                tokens=token_count,
                rpm_utilization=round(rpm_utilization, 2),
                tpm_utilization=round(tpm_utilization, 2)
            )

    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current usage statistics.

        Returns:
            Dictionary with current usage metrics
        """
        self._clean_old_requests()
        self._check_cooldown_expired()

        current_rpm = len(self.requests)
        current_tpm = sum(tokens for _, tokens in self.requests)

        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "current_rpm": current_rpm,
            "rpm_limit": self.rpm_limit,
            "rpm_utilization_percent": round((current_rpm / self.rpm_limit * 100), 2),
            "current_tpm": current_tpm,
            "tpm_limit": self.tpm_limit,
            "tpm_utilization_percent": round((current_tpm / self.tpm_limit * 100), 2),
            "cooldown_state": self.cooldown_state.value,
            "cooldown_until": self.cooldown_until.isoformat() if self.cooldown_until else None
        }


class LLMAccountProvider:
    """
    Single OpenAI account with dual-model tracking (gpt-4o and gpt-4o-mini).

    Each account has separate usage trackers for each model, allowing the same
    account to serve both models simultaneously without confusion.
    """

    def __init__(
        self,
        account_number: int,
        api_key: str,
        gpt4o_rpm: int,
        gpt4o_tpm: int,
        gpt4o_mini_rpm: int,
        gpt4o_mini_tpm: int,
        buffer_percent: int = 80
    ):
        """
        Initialize account provider with dual-model tracking.

        Args:
            account_number: Account number (1-20)
            api_key: OpenAI API key for this account
            gpt4o_rpm: gpt-4o requests per minute limit
            gpt4o_tpm: gpt-4o tokens per minute limit
            gpt4o_mini_rpm: gpt-4o-mini requests per minute limit
            gpt4o_mini_tpm: gpt-4o-mini tokens per minute limit
            buffer_percent: Buffer threshold for both models
        """
        self.account_number = account_number
        self.api_key = api_key
        self.buffer_percent = buffer_percent

        # Create separate trackers for each model
        self.gpt4o_tracker = ModelUsageTracker(
            model_name="gpt-4o",
            rpm_limit=gpt4o_rpm,
            tpm_limit=gpt4o_tpm,
            buffer_percent=buffer_percent,
            provider_name=f"account_{account_number}_gpt4o"
        )

        self.gpt4o_mini_tracker = ModelUsageTracker(
            model_name="gpt-4o-mini",
            rpm_limit=gpt4o_mini_rpm,
            tpm_limit=gpt4o_mini_tpm,
            buffer_percent=buffer_percent,
            provider_name=f"account_{account_number}_gpt4o_mini"
        )

        logger.info(
            "account_provider_initialized",
            account_number=account_number,
            api_key_prefix=f"...{api_key[-10:]}" if len(api_key) > 10 else "***",
            gpt4o_limits=f"{gpt4o_rpm}RPM/{gpt4o_tpm}TPM",
            gpt4o_mini_limits=f"{gpt4o_mini_rpm}RPM/{gpt4o_mini_tpm}TPM"
        )

    def get_tracker_for_model(self, model: str) -> ModelUsageTracker:
        """Get the appropriate tracker for the specified model"""
        if "gpt-4o-mini" in model.lower() or "gpt4o-mini" in model.lower():
            return self.gpt4o_mini_tracker
        else:  # gpt-4o or gpt4o
            return self.gpt4o_tracker

    def can_handle_request(self, model: str, estimated_tokens: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if this account can handle a request for the specified model.

        Args:
            model: Model name (gpt-4o or gpt-4o-mini)
            estimated_tokens: Estimated tokens for this request

        Returns:
            Tuple of (can_handle: bool, usage_stats: dict)
        """
        tracker = self.get_tracker_for_model(model)
        return tracker.can_handle_request(estimated_tokens)

    def record_request(self, model: str, token_count: int, cooldown_seconds: int = 60):
        """
        Record a successful request for the specified model.

        Args:
            model: Model name
            token_count: Actual tokens used
            cooldown_seconds: Cooldown duration if buffer exceeded
        """
        tracker = self.get_tracker_for_model(model)
        tracker.record_request(token_count, cooldown_seconds)

    def get_usage_stats(self, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage statistics for specified model or both models.

        Args:
            model: Optional model name, if None returns both

        Returns:
            Dictionary with usage stats
        """
        if model:
            tracker = self.get_tracker_for_model(model)
            return tracker.get_current_usage()
        else:
            return {
                "account_number": self.account_number,
                "gpt4o": self.gpt4o_tracker.get_current_usage(),
                "gpt4o_mini": self.gpt4o_mini_tracker.get_current_usage()
            }


class UnifiedLLMManager:
    """
    Unified LLM Manager with 20-account support and per-model resource tracking.

    Features:
    - Manages 20 OpenAI accounts
    - Separate tracking for gpt-4o and gpt-4o-mini per account
    - Cooldown mechanism when accounts hit capacity
    - Retry queue for when all accounts busy
    - Round-robin distribution within available accounts
    """

    def __init__(self):
        """Initialize Unified LLM Manager with 20 accounts"""
        self.accounts: List[LLMAccountProvider] = []
        self._current_index: int = 0  # For round-robin
        self._cooldown_seconds: int = int(os.getenv("LLM_COOLDOWN_SECONDS", "60"))
        self._retry_timeout: int = int(os.getenv("LLM_RETRY_TIMEOUT_SECONDS", "30"))
        self._retry_poll_interval: int = int(os.getenv("LLM_RETRY_POLL_SECONDS", "5"))

        self._initialize_accounts()

        logger.info(
            "unified_llm_manager_initialized",
            total_accounts=len(self.accounts),
            cooldown_seconds=self._cooldown_seconds,
            retry_timeout=self._retry_timeout,
            retry_poll_interval=self._retry_poll_interval
        )

    def _initialize_accounts(self):
        """Initialize all 20 accounts from environment configuration with credit validation"""

        # Track validation results
        validated_count = 0
        skipped_count = 0
        invalid_count = 0

        logger.info("starting_account_validation", message="Validating API keys for credits...")

        # Load all 20 accounts
        for account_num in range(1, 21):
            api_key = os.getenv(f"ACCOUNT_{account_num}_API_KEY")

            # Skip if API key not configured or is placeholder
            if not api_key or api_key == "YOUR_API_KEY_HERE":
                skipped_count += 1
                continue

            # Validate API key has credits before adding to pool
            is_valid, error_msg = validate_api_key(api_key, account_num)

            if not is_valid:
                invalid_count += 1
                logger.warning(
                    "account_skipped_no_credits",
                    account_number=account_num,
                    reason=error_msg
                )
                continue

            # Get rate limits for this account (defaults are Tier 2 limits)
            gpt4o_rpm = int(os.getenv(f"ACCOUNT_{account_num}_GPT4O_RPM_LIMIT", "5000"))
            gpt4o_tpm = int(os.getenv(f"ACCOUNT_{account_num}_GPT4O_TPM_LIMIT", "450000"))
            gpt4o_mini_rpm = int(os.getenv(f"ACCOUNT_{account_num}_GPT4O_MINI_RPM_LIMIT", "5000"))
            gpt4o_mini_tpm = int(os.getenv(f"ACCOUNT_{account_num}_GPT4O_MINI_TPM_LIMIT", "2000000"))
            buffer_percent = int(os.getenv(f"ACCOUNT_{account_num}_BUFFER_PERCENT", "80"))

            # Create account provider
            account = LLMAccountProvider(
                account_number=account_num,
                api_key=api_key,
                gpt4o_rpm=gpt4o_rpm,
                gpt4o_tpm=gpt4o_tpm,
                gpt4o_mini_rpm=gpt4o_mini_rpm,
                gpt4o_mini_tpm=gpt4o_mini_tpm,
                buffer_percent=buffer_percent
            )

            self.accounts.append(account)
            validated_count += 1

            logger.info(
                "account_loaded",
                account_number=account_num,
                gpt4o_limits=f"{gpt4o_rpm}RPM/{gpt4o_tpm}TPM",
                gpt4o_mini_limits=f"{gpt4o_mini_rpm}RPM/{gpt4o_mini_tpm}TPM"
            )

        logger.info(
            "account_validation_complete",
            validated=validated_count,
            skipped_not_configured=skipped_count,
            invalid_no_credits=invalid_count,
            total_available=len(self.accounts)
        )

        # Validate we have at least one account
        if not self.accounts:
            # Fallback to OPENAI_API_KEY if no accounts configured
            fallback_api_key = os.getenv("OPENAI_API_KEY")
            if fallback_api_key and fallback_api_key != "YOUR_API_KEY_HERE":
                # Validate fallback key too
                is_valid, error_msg = validate_api_key(fallback_api_key, 0)

                if is_valid:
                    logger.warning(
                        "no_account_keys_found_using_fallback",
                        message="No valid ACCOUNT_X_API_KEY configured, using OPENAI_API_KEY"
                    )

                    account = LLMAccountProvider(
                        account_number=1,
                        api_key=fallback_api_key,
                        gpt4o_rpm=5000,
                        gpt4o_tpm=450000,
                        gpt4o_mini_rpm=5000,
                        gpt4o_mini_tpm=2000000,
                        buffer_percent=80
                    )

                    self.accounts.append(account)
                    logger.info("fallback_account_configured")
                else:
                    raise ValueError(
                        f"OPENAI_API_KEY fallback also has no credits: {error_msg}. "
                        "Please add credits to at least one account."
                    )
            else:
                raise ValueError(
                    "No LLM API keys configured. Please set ACCOUNT_1_API_KEY through ACCOUNT_20_API_KEY "
                    "or OPENAI_API_KEY in your .env file"
                )

    def _estimate_tokens(self, messages: List[BaseMessage]) -> int:
        """
        Estimate token count for messages.
        Uses rough approximation: 1 token ≈ 4 characters

        Args:
            messages: List of messages to estimate

        Returns:
            Estimated token count
        """
        total_chars = 0
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            total_chars += len(content)

        # Rough estimate: 1 token ≈ 4 characters
        # Add 20% buffer for safety
        estimated_tokens = int((total_chars / 4) * 1.2)

        return max(estimated_tokens, 100)  # Minimum 100 tokens

    async def _find_available_account(
        self,
        model: str,
        estimated_tokens: int,
        timeout_seconds: Optional[int] = None
    ) -> Optional[LLMAccountProvider]:
        """
        Find an available account for the specified model with retry logic.

        Args:
            model: Model name (gpt-4o or gpt-4o-mini)
            estimated_tokens: Estimated tokens needed
            timeout_seconds: Max time to wait for account (None = use default)

        Returns:
            Available account or None if timeout
        """
        timeout = timeout_seconds if timeout_seconds is not None else self._retry_timeout
        start_time = datetime.now()
        num_accounts = len(self.accounts)

        while (datetime.now() - start_time).total_seconds() < timeout:
            # Try round-robin through all accounts
            for i in range(num_accounts):
                # Calculate account index with wraparound
                account_index = (self._current_index + i) % num_accounts
                account = self.accounts[account_index]

                # Check if this account can handle the request
                can_handle, stats = account.can_handle_request(model, estimated_tokens)

                if can_handle:
                    # Found available account - update index for next request
                    self._current_index = (account_index + 1) % num_accounts

                    # Remove 'model' from stats to avoid conflict (we have llm_model)
                    stats_for_log = {k: v for k, v in stats.items() if k != 'model'}

                    logger.info(
                        "account_selected",
                        account_number=account.account_number,
                        llm_model=model,
                        **stats_for_log
                    )

                    return account

            # All accounts busy - wait and retry
            logger.warning(
                "all_accounts_busy_retrying",
                llm_model=model,
                total_accounts=num_accounts,
                retry_in_seconds=self._retry_poll_interval
            )

            await asyncio.sleep(self._retry_poll_interval)

        # Timeout - no account available
        logger.error(
            "no_account_available_timeout",
            llm_model=model,
            timeout_seconds=timeout,
            total_accounts=num_accounts
        )

        return None

    async def ainvoke(
        self,
        messages: List[BaseMessage],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Invoke LLM with unified account management.

        Args:
            messages: List of messages to send to LLM
            model: Model to use (gpt-4o or gpt-4o-mini), defaults to gpt-4o-mini
            temperature: Temperature for generation
            **kwargs: Additional arguments for LLM

        Returns:
            LLM response

        Raises:
            Exception: If no account available within timeout
        """
        if not self.accounts:
            raise Exception("No LLM accounts configured")

        # Default to gpt-4o-mini if not specified
        model = model or "gpt-4o-mini"
        temperature = temperature if temperature is not None else 0.3

        # Remove model and temperature from kwargs if present (we handle them explicitly)
        kwargs.pop('model', None)
        kwargs.pop('temperature', None)

        # Estimate tokens
        estimated_tokens = self._estimate_tokens(messages)

        # Find available account with retry
        account = await self._find_available_account(model, estimated_tokens)

        if not account:
            # Log usage stats for all accounts
            usage_stats = [acc.get_usage_stats() for acc in self.accounts]
            logger.error(
                "all_accounts_exhausted",
                llm_model=model,
                total_accounts=len(self.accounts),
                usage_stats=usage_stats
            )

            raise Exception(
                f"All {len(self.accounts)} accounts are at capacity or cooling down for {model}. "
                "Please try again in a moment."
            )

        # Create LLM instance for this account
        try:
            llm = ChatOpenAI(
                model=model,
                api_key=account.api_key,
                temperature=temperature
            )

            # Invoke LLM
            response = await llm.ainvoke(messages, **kwargs)

            # Record usage
            account.record_request(model, estimated_tokens, self._cooldown_seconds)

            logger.info(
                "llm_request_success",
                account_number=account.account_number,
                llm_model=model,
                estimated_tokens=estimated_tokens
            )

            return response

        except Exception as e:
            logger.error(
                "llm_request_failed",
                account_number=account.account_number,
                llm_model=model,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    async def get_llm_with_structured_output(
        self,
        schema: Any,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> Any:
        """
        Get an LLM instance with structured output (Pydantic schema).

        This method finds an available account and returns an LLM configured
        with .with_structured_output() for type-safe responses.

        Args:
            schema: Pydantic model class for structured output
            model: Model to use (gpt-4o or gpt-4o-mini), defaults to gpt-4o-mini
            temperature: Temperature for generation

        Returns:
            LLM instance with structured output applied

        Raises:
            Exception: If no account available
        """
        if not self.accounts:
            raise Exception("No LLM accounts configured")

        # Default to gpt-4o-mini if not specified
        model = model or "gpt-4o-mini"
        temperature = temperature if temperature is not None else 0.3

        # Estimate tokens (conservative estimate for structured output)
        estimated_tokens = 1000  # Reasonable estimate for structured responses

        # Find available account with retry
        account = await self._find_available_account(model, estimated_tokens)

        if not account:
            raise Exception(
                f"All {len(self.accounts)} accounts are at capacity or cooling down for {model}. "
                "Please try again in a moment."
            )

        # Create LLM instance with structured output
        llm = ChatOpenAI(
            model=model,
            api_key=account.api_key,
            temperature=temperature
        )

        # Apply structured output using function calling method
        # (works with Dict[str, Any] fields, unlike default strict schema mode)
        structured_llm = llm.with_structured_output(schema, method="function_calling")

        # Record that we're using this account (will record actual tokens after call)
        account.record_request(model, estimated_tokens, self._cooldown_seconds)

        logger.info(
            "structured_llm_created",
            account_number=account.account_number,
            llm_model=model,
            schema=schema.__name__
        )

        return structured_llm

    def get_all_usage_stats(self) -> List[Dict[str, Any]]:
        """
        Get usage statistics for all accounts.

        Returns:
            List of usage statistics dictionaries
        """
        return [account.get_usage_stats() for account in self.accounts]

    def get_model_usage_stats(self, model: str) -> List[Dict[str, Any]]:
        """
        Get usage statistics for a specific model across all accounts.

        Args:
            model: Model name (gpt-4o or gpt-4o-mini)

        Returns:
            List of usage statistics for the specified model
        """
        return [account.get_usage_stats(model) for account in self.accounts]

    def get_next_api_key(self) -> str:
        """
        Get the next available API key using round-robin distribution.

        This is useful for external components like CrewAI that need
        an API key but can't use the async LLM manager directly.

        Returns:
            API key string

        Raises:
            Exception: If no accounts available
        """
        if not self.accounts:
            raise Exception("No LLM accounts configured")

        # Simple round-robin - get next account
        account = self.accounts[self._current_index]
        self._current_index = (self._current_index + 1) % len(self.accounts)

        logger.info(
            "api_key_distributed",
            account_number=account.account_number,
            total_accounts=len(self.accounts)
        )

        return account.api_key

    def get_account_count(self) -> int:
        """Get the number of validated accounts in the pool."""
        return len(self.accounts)


# Global singleton instance
_llm_manager_instance: Optional[UnifiedLLMManager] = None


def get_llm_manager() -> UnifiedLLMManager:
    """
    Get or create the global Unified LLM Manager instance.

    Returns:
        Global Unified LLM Manager singleton
    """
    global _llm_manager_instance

    if _llm_manager_instance is None:
        _llm_manager_instance = UnifiedLLMManager()

    return _llm_manager_instance
