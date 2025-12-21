"""
LLM Callback Handlers
====================
Callbacks for tracking LLM usage and enabling proactive fallback.
"""

import structlog
from typing import Any, Dict, List
from langchain.callbacks.base import BaseCallbackHandler
from langchain_core.outputs import LLMResult

logger = structlog.get_logger(__name__)


class TokenTrackingCallback(BaseCallbackHandler):
    """
    Callback handler that tracks token usage and records it in the LLM Manager.

    This enables accurate capacity monitoring even when agents use bind_tools()
    and call LLM directly instead of going through manager.ainvoke().
    """

    def __init__(self, provider_name: str, tracker: Any, agent_name: str = "unknown"):
        """
        Initialize callback handler.

        Args:
            provider_name: Name of the LLM provider (for logging)
            tracker: LLMUsageTracker instance to record usage
            agent_name: Name of the agent using this LLM
        """
        super().__init__()
        self.provider_name = provider_name
        self.tracker = tracker
        self.agent_name = agent_name
        self._request_start_times: Dict[str, float] = {}

    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        **kwargs: Any
    ) -> None:
        """
        Called when LLM starts processing a request.

        We estimate tokens here as a safety measure, but actual usage
        will be recorded in on_llm_end using the response metadata.
        """
        # Estimate tokens for proactive monitoring
        # (actual usage tracked in on_llm_end)
        total_chars = sum(len(prompt) for prompt in prompts)
        estimated_tokens = int((total_chars / 4) * 1.2)

        logger.debug(
            "llm_request_started",
            provider=self.provider_name,
            agent=self.agent_name,
            estimated_tokens=estimated_tokens,
            prompt_count=len(prompts)
        )

    def on_llm_end(
        self,
        response: LLMResult,
        **kwargs: Any
    ) -> None:
        """
        Called when LLM completes a request.

        Extracts actual token usage from the response and records it
        in the usage tracker for accurate capacity monitoring.

        Uses OpenAI token usage format.
        """
        try:
            total_tokens = 0
            prompt_tokens = 0
            completion_tokens = 0

            # Extract token usage from response metadata
            # OpenAI format: response.llm_output["token_usage"]
            if response.llm_output and "token_usage" in response.llm_output:
                token_usage = response.llm_output["token_usage"]
                total_tokens = token_usage.get("total_tokens", 0)
                prompt_tokens = token_usage.get("prompt_tokens", 0)
                completion_tokens = token_usage.get("completion_tokens", 0)

                if total_tokens > 0:
                    # Record actual usage in tracker
                    self.tracker.record_request(total_tokens)

                    logger.info(
                        "llm_request_completed_tracked",
                        provider=self.provider_name,
                        agent=self.agent_name,
                        total_tokens=total_tokens,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )
                else:
                    logger.warning(
                        "llm_response_missing_token_count",
                        provider=self.provider_name,
                        agent=self.agent_name
                    )
            else:
                logger.warning(
                    "llm_response_missing_usage_metadata",
                    provider=self.provider_name,
                    agent=self.agent_name
                )

        except Exception as e:
            logger.error(
                "token_tracking_callback_error",
                provider=self.provider_name,
                agent=self.agent_name,
                error=str(e)
            )

    def on_llm_error(
        self,
        error: Exception,
        **kwargs: Any
    ) -> None:
        """
        Called when LLM encounters an error.

        Logs errors for monitoring and debugging.
        """
        error_str = str(error)
        is_rate_limit = "429" in error_str or "rate_limit" in error_str.lower()

        if is_rate_limit:
            logger.error(
                "llm_rate_limit_error_detected",
                provider=self.provider_name,
                agent=self.agent_name,
                error=error_str
            )
        else:
            logger.error(
                "llm_request_error",
                provider=self.provider_name,
                agent=self.agent_name,
                error=error_str
            )

