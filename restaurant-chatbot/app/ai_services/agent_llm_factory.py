"""
Agent LLM Factory
=================
Provides LLM instances to agents compatible with the Unified LLM Manager.

Uses ManagedChatOpenAI - a custom wrapper that routes all API calls through
UnifiedLLMManager for proper load balancing, failover, and account rotation
across all 20 OpenAI accounts.
"""

import structlog
from typing import Any, Optional, List, Union, Sequence
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatResult, ChatGeneration
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from app.ai_services.llm_manager import get_llm_manager, UnifiedLLMManager
from app.core.config import config

logger = structlog.get_logger(__name__)


class ManagedChatOpenAI(BaseChatModel):
    """
    A ChatOpenAI-compatible LLM that routes all calls through UnifiedLLMManager.

    This wrapper ensures:
    - Proper load balancing across all 20 OpenAI accounts
    - Automatic failover when an account hits rate limits or quota
    - Cooldown management per account
    - Full compatibility with LangChain agent frameworks
    """

    model: str = "gpt-4o-mini"
    temperature: float = 0.3
    agent_name: str = "unknown"
    _manager: Optional[UnifiedLLMManager] = None
    _bound_tools: Optional[List[Any]] = None

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        agent_name: str = "unknown",
        **kwargs
    ):
        super().__init__(
            model=model,
            temperature=temperature,
            agent_name=agent_name,
            **kwargs
        )
        self._manager = get_llm_manager()
        self._bound_tools = None

        logger.info(
            "managed_chat_openai_created",
            agent_name=agent_name,
            model=model,
            temperature=temperature
        )

    @property
    def _llm_type(self) -> str:
        return "managed-chat-openai"

    @property
    def _identifying_params(self) -> dict:
        return {
            "model": self.model,
            "temperature": self.temperature,
            "agent_name": self.agent_name
        }

    def bind_tools(
        self,
        tools: Sequence[Union[dict, type, callable, BaseTool]],
        **kwargs
    ) -> "ManagedChatOpenAI":
        """
        Bind tools to this LLM instance.

        Returns a new ManagedChatOpenAI with tools bound.
        """
        new_instance = ManagedChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            agent_name=self.agent_name
        )
        new_instance._bound_tools = list(tools)
        new_instance._tool_kwargs = kwargs

        logger.info(
            "tools_bound_to_managed_llm",
            agent_name=self.agent_name,
            tool_count=len(tools)
        )

        return new_instance

    def with_structured_output(
        self,
        schema: Any,
        **kwargs
    ) -> "ManagedChatOpenAI":
        """
        Return a new ManagedChatOpenAI that outputs structured data.

        This enables structured output with full failover support.
        When ainvoke() is called, the response will be parsed into
        the specified Pydantic schema.

        Args:
            schema: Pydantic model class for structured output
            **kwargs: Additional arguments (e.g., method="function_calling")

        Returns:
            New ManagedChatOpenAI instance with structured output enabled
        """
        new_instance = ManagedChatOpenAI(
            model=self.model,
            temperature=self.temperature,
            agent_name=self.agent_name
        )
        new_instance._structured_schema = schema
        new_instance._structured_kwargs = kwargs

        logger.info(
            "structured_output_bound_to_managed_llm",
            agent_name=self.agent_name,
            schema=schema.__name__ if hasattr(schema, '__name__') else str(schema)
        )

        return new_instance

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs
    ) -> ChatResult:
        """Sync generation - not recommended, use async instead."""
        import asyncio
        return asyncio.get_event_loop().run_until_complete(
            self._agenerate(messages, stop, run_manager, **kwargs)
        )

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs
    ) -> ChatResult:
        """
        Async generation through UnifiedLLMManager with full failover.

        Supports:
        - Regular chat completion
        - Tool binding (for tool-calling agents)
        - Structured output (for intent classifiers)
        """
        try:
            # Find available account with failover
            estimated_tokens = self._manager._estimate_tokens(messages)
            account = await self._manager._find_available_account(
                self.model,
                estimated_tokens
            )

            if not account:
                raise Exception(
                    f"All accounts exhausted for model {self.model}. "
                    "Please try again in a moment."
                )

            # Create ChatOpenAI with selected account
            llm = ChatOpenAI(
                model=self.model,
                api_key=account.api_key,
                temperature=self.temperature
            )

            # Apply structured output if set
            structured_schema = getattr(self, '_structured_schema', None)
            if structured_schema:
                structured_kwargs = getattr(self, '_structured_kwargs', {})
                llm = llm.with_structured_output(structured_schema, **structured_kwargs)

            # Bind tools if present
            if self._bound_tools:
                tool_kwargs = getattr(self, '_tool_kwargs', {})
                llm = llm.bind_tools(self._bound_tools, **tool_kwargs)

            # Invoke LLM
            response = await llm.ainvoke(messages, stop=stop, **kwargs)

            # Record usage
            account.record_request(
                self.model,
                estimated_tokens,
                self._manager._cooldown_seconds
            )

            logger.info(
                "managed_llm_request_success",
                agent_name=self.agent_name,
                account_number=account.account_number,
                model=self.model,
                structured_output=structured_schema is not None
            )

            # For structured output, response is already the parsed object
            if structured_schema:
                # Store the structured response for retrieval
                self._last_structured_response = response
                # Return a ChatResult with a placeholder message
                from langchain_core.messages import AIMessage
                return ChatResult(
                    generations=[ChatGeneration(message=AIMessage(content=str(response)))]
                )

            # Convert response to ChatResult
            return ChatResult(
                generations=[ChatGeneration(message=response)]
            )

        except Exception as e:
            error_str = str(e)

            # Check if it's a rate limit/quota error - try next account
            if "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower():
                logger.warning(
                    "account_error_attempting_failover",
                    agent_name=self.agent_name,
                    error=error_str,
                    model=self.model
                )

                # Retry with failover
                return await self._retry_with_failover(messages, stop, **kwargs)

            logger.error(
                "managed_llm_request_failed",
                agent_name=self.agent_name,
                error=error_str,
                model=self.model
            )
            raise

    async def _retry_with_failover(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        max_retries: int = 5,
        **kwargs
    ) -> ChatResult:
        """
        Retry request with different accounts on failure.

        Supports structured output and tool binding.
        """
        last_error = None
        structured_schema = getattr(self, '_structured_schema', None)

        for attempt in range(max_retries):
            try:
                estimated_tokens = self._manager._estimate_tokens(messages)
                account = await self._manager._find_available_account(
                    self.model,
                    estimated_tokens
                )

                if not account:
                    raise Exception("No accounts available for retry")

                llm = ChatOpenAI(
                    model=self.model,
                    api_key=account.api_key,
                    temperature=self.temperature
                )

                # Apply structured output if set
                if structured_schema:
                    structured_kwargs = getattr(self, '_structured_kwargs', {})
                    llm = llm.with_structured_output(structured_schema, **structured_kwargs)

                # Bind tools if present
                if self._bound_tools:
                    tool_kwargs = getattr(self, '_tool_kwargs', {})
                    llm = llm.bind_tools(self._bound_tools, **tool_kwargs)

                response = await llm.ainvoke(messages, stop=stop, **kwargs)

                account.record_request(
                    self.model,
                    estimated_tokens,
                    self._manager._cooldown_seconds
                )

                logger.info(
                    "failover_retry_success",
                    agent_name=self.agent_name,
                    account_number=account.account_number,
                    attempt=attempt + 1,
                    structured_output=structured_schema is not None
                )

                # For structured output, store and return appropriately
                if structured_schema:
                    self._last_structured_response = response
                    from langchain_core.messages import AIMessage
                    return ChatResult(
                        generations=[ChatGeneration(message=AIMessage(content=str(response)))]
                    )

                return ChatResult(
                    generations=[ChatGeneration(message=response)]
                )

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Check if rate limit error - continue to next account
                if "429" in error_str or "rate" in error_str.lower() or "quota" in error_str.lower():
                    logger.warning(
                        "failover_retry_rate_limit",
                        agent_name=self.agent_name,
                        attempt=attempt + 1,
                        error=error_str
                    )
                    continue

                # Non-rate-limit error
                logger.warning(
                    "failover_retry_failed",
                    agent_name=self.agent_name,
                    attempt=attempt + 1,
                    error=error_str
                )
                continue

        raise Exception(f"All failover retries exhausted: {last_error}")

    async def ainvoke_structured(
        self,
        messages: List[BaseMessage],
        **kwargs
    ) -> Any:
        """
        Invoke and return structured output directly.

        This is a convenience method for structured output that returns
        the parsed Pydantic object directly instead of ChatResult.

        Args:
            messages: Messages to send to LLM
            **kwargs: Additional arguments

        Returns:
            Parsed response matching the structured schema
        """
        structured_schema = getattr(self, '_structured_schema', None)
        if not structured_schema:
            raise ValueError("No structured schema set. Use with_structured_output() first.")

        # Call _agenerate which will set _last_structured_response
        await self._agenerate(messages, **kwargs)

        # Return the structured response
        return self._last_structured_response


class AgentLLMFactory:
    """
    Factory for providing LLM instances to agents.

    Now returns ManagedChatOpenAI instances that route all API calls through
    UnifiedLLMManager for proper load balancing and failover across all 20 accounts.
    """

    def __init__(self):
        """Initialize factory with reference to LLM manager"""
        self.manager = get_llm_manager()
        logger.info("agent_llm_factory_initialized")

    def get_llm(
        self,
        agent_name: str,
        temperature: float = 0.3,
        prefer_quality: bool = True,
        model: Optional[str] = None
    ) -> ManagedChatOpenAI:
        """
        Get a ManagedChatOpenAI instance for an agent.

        This LLM routes all calls through UnifiedLLMManager for:
        - Load balancing across 20 OpenAI accounts
        - Automatic failover on rate limits or quota errors
        - Cooldown management per account

        Args:
            agent_name: Name of the agent requesting LLM
            temperature: Temperature for response generation
            prefer_quality: If True, use gpt-4o; otherwise use gpt-4o-mini
            model: Override model selection

        Returns:
            ManagedChatOpenAI instance compatible with LangChain agents
        """
        if not self.manager.accounts:
            raise Exception("No LLM accounts configured")

        # Determine model to use
        if model:
            model_to_use = model
        elif prefer_quality:
            model_to_use = config.INTENT_CLASSIFICATION_MODEL  # gpt-4o
        else:
            model_to_use = config.AGENT_MODEL  # gpt-4o-mini

        # Create ManagedChatOpenAI that routes through UnifiedLLMManager
        llm = ManagedChatOpenAI(
            model=model_to_use,
            temperature=temperature,
            agent_name=agent_name
        )

        logger.info(
            "agent_llm_provided",
            agent_name=agent_name,
            model=model_to_use,
            temperature=temperature,
            note="Using ManagedChatOpenAI with full failover support"
        )

        return llm

    async def invoke_llm_with_manager(
        self,
        messages,
        agent_name: str,
        model: Optional[str] = None,
        temperature: float = 0.3,
        **kwargs
    ):
        """
        Invoke LLM through the UnifiedLLMManager for proper load balancing.

        This method should be used instead of calling llm.ainvoke() directly
        when you want full account rotation and cooldown management.

        Args:
            messages: Messages to send to LLM
            agent_name: Name of the agent making the request
            model: Model to use (gpt-4o or gpt-4o-mini)
            temperature: Temperature for generation
            **kwargs: Additional arguments for LLM

        Returns:
            LLM response
        """
        model_to_use = model or config.AGENT_MODEL

        logger.info(
            "invoking_llm_via_manager",
            agent_name=agent_name,
            model=model_to_use,
            temperature=temperature
        )

        response = await self.manager.ainvoke(
            messages=messages,
            model=model_to_use,
            temperature=temperature,
            **kwargs
        )

        return response


# Global instance
_agent_llm_factory = None


def get_agent_llm_factory() -> AgentLLMFactory:
    """Get or create the global AgentLLMFactory instance"""
    global _agent_llm_factory
    if _agent_llm_factory is None:
        _agent_llm_factory = AgentLLMFactory()
    return _agent_llm_factory


def get_llm_for_agent(
    agent_name: str,
    temperature: float = 0.3,
    prefer_quality: bool = True,
    model: Optional[str] = None
):
    """
    Compatibility function for old code.

    DEPRECATED: Use get_agent_llm_factory().get_llm() instead.
    """
    factory = get_agent_llm_factory()
    return factory.get_llm(
        agent_name=agent_name,
        temperature=temperature,
        prefer_quality=prefer_quality,
        model=model
    )


async def invoke_llm_with_fallback(
    llm,
    messages,
    agent_name: str,
    **kwargs
):
    """
    Compatibility function - invokes LLM through the UnifiedLLMManager.

    DEPRECATED: The new UnifiedLLMManager handles all fallback and account
    rotation automatically. This function now routes through the manager.

    Args:
        llm: Ignored (kept for compatibility)
        messages: Messages to send to LLM
        agent_name: Name of the agent making the request
        **kwargs: Additional arguments for LLM

    Returns:
        LLM response
    """
    factory = get_agent_llm_factory()

    # Extract model and temperature from kwargs if present
    model = kwargs.pop('model', None)
    temperature = kwargs.pop('temperature', 0.3)

    return await factory.invoke_llm_with_manager(
        messages=messages,
        agent_name=agent_name,
        model=model,
        temperature=temperature,
        **kwargs
    )
