"""
Base class for all tools in the Restaurant AI Assistant.

This module provides the foundational ToolBase class that all tools inherit from.
Provides standardized input/output, error handling, performance monitoring, and validation.

Classes:
    ToolResult: Standard result format for all tools
    ToolError: Custom exception for tool-related errors
    ToolBase: Abstract base class for all tools

Functions:
    validate_tool_input: Validate tool input parameters
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import time
from enum import Enum
import traceback

# from app.core.logging_config import get_logger, get_performance_logger, log_async_performance
from app.core.logging_config import get_feature_logger, get_performance_logger, log_async_performance, get_logger


from app.core.config import config


class ToolStatus(Enum):
    """Tool execution status enumeration"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    RETRY = "retry"
    TIMEOUT = "timeout"


@dataclass
class ToolResult:
    """
    Standardized result format for all tools.

    Attributes:
        status: Tool execution status
        data: Tool execution result data
        error: Error message if execution failed
        metadata: Additional metadata about execution
        execution_time: Time taken to execute in seconds
        timestamp: When the tool was executed
    """
    status: ToolStatus
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ToolError(Exception):
    """
    Custom exception for tool-related errors.

    Attributes:
        message: Error message
        tool_name: Name of the tool that failed
        details: Additional error details
        retry_suggested: Whether retry is suggested
    """

    def __init__(self, message: str, tool_name: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None, retry_suggested: bool = False):
        """
        Initialize tool error.

        Args:
            message: Error message
            tool_name: Name of the tool that failed
            details: Additional error details
            retry_suggested: Whether retry is suggested
        """
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name
        self.details = details or {}
        self.retry_suggested = retry_suggested


class ToolBase(ABC):
    """
    Abstract base class for all tools.

    Provides common functionality for:
    - Input validation
    - Error handling and logging
    - Performance monitoring
    - Retry logic
    - Result standardization
    """

    def __init__(self, name: str, description: Optional[str] = None, max_retries: int = 3,
                 timeout_seconds: int = 30, retry_delay: float = 1.0):
        """
        Initialize tool base.

        Args:
            name: Tool name for identification
            description: Tool description for documentation
            max_retries: Maximum number of retry attempts
            timeout_seconds: Maximum execution timeout
            retry_delay: Delay between retry attempts in seconds
        """
        self.name = name
        self.description = description or f"Tool: {name}"
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self.retry_delay = retry_delay

        # Initialize logging
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.perf_logger = get_performance_logger()

        # Execution statistics
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0

        self.logger.info(f"Tool initialized: {self.name}")

    def __str__(self) -> str:
        """String representation of the tool"""
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        """Detailed string representation of the tool"""
        return (f"{self.__class__.__name__}(name='{self.name}', "
                f"max_retries={self.max_retries}, timeout={self.timeout_seconds})")

    @abstractmethod
    async def _execute_impl(self, **kwargs) -> ToolResult:
        """
        Implementation-specific execution logic.

        This method must be implemented by concrete tool classes.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Tool execution result

        Raises:
            ToolError: If execution fails
            NotImplementedError: If not implemented by subclass
        """
        raise NotImplementedError("Subclasses must implement _execute_impl method")

    def validate_input(self, **kwargs) -> Dict[str, Any]:
        """
        Validate input parameters for the tool.

        Override this method in subclasses for tool-specific validation.

        Args:
            **kwargs: Input parameters to validate

        Returns:
            Dict[str, Any]: Validated and potentially modified parameters

        Raises:
            ToolError: If validation fails
        """
        # Base implementation - can be overridden
        if not kwargs:
            raise ToolError(f"No input parameters provided for tool {self.name}")

        return kwargs

    async def _execute_with_timeout(self, **kwargs) -> ToolResult:
        """
        Execute tool with timeout protection.

        Args:
            **kwargs: Tool execution parameters

        Returns:
            ToolResult: Tool execution result

        Raises:
            ToolError: If execution times out
        """
        try:
            return await asyncio.wait_for(
                self._execute_impl(**kwargs),
                timeout=self.timeout_seconds
            )
        except asyncio.TimeoutError:
            error_msg = f"Tool {self.name} timed out after {self.timeout_seconds} seconds"
            self.logger.error(error_msg, tool_name=self.name)
            return ToolResult(
                status=ToolStatus.TIMEOUT,
                error=error_msg,
                metadata={"timeout_seconds": self.timeout_seconds}
            )

    @log_async_performance
    async def execute(self, **kwargs) -> ToolResult:
        """
        Execute the tool with validation, retry logic, and error handling.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Standardized tool execution result
        """
        start_time = time.time()
        self.execution_count += 1

        self.logger.info(f"Executing tool: {self.name}",
            tool_name=self.name,
            execution_count=self.execution_count,
            parameters=list(kwargs.keys())  # Log parameter names only
        )

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # Validate input parameters
                validated_params = self.validate_input(**kwargs)

                # Execute with timeout protection
                result = await self._execute_with_timeout(**validated_params)

                # Update statistics
                execution_time = time.time() - start_time
                result.execution_time = execution_time
                self.total_execution_time += execution_time

                if result.status == ToolStatus.SUCCESS:
                    self.success_count += 1
                    self.logger.info(f"Tool {self.name} executed successfully",
                        tool_name=self.name,
                        execution_time_seconds=execution_time,
                        attempt=attempt + 1,
                        result_data_keys=list(result.data.keys()) if result.data else [],
                        result_metadata=result.metadata
                    )

                    # Log performance metrics
                    if self.perf_logger:
                        self.perf_logger.log_execution_time(
                            f"tool.{self.name}",
                            execution_time
                        )
                else:
                    # Log failure details
                    self.logger.warning(f"Tool {self.name} completed with status {result.status}",
                        tool_name=self.name,
                        status=result.status.value if result.status else "unknown",
                        error=result.error,
                        execution_time_seconds=execution_time
                    )

                return result

            except ToolError as e:
                last_error = e
                self.logger.warning(f"Tool {self.name} failed (attempt {attempt + 1}): {e.message}",
                                  tool_name=self.name, attempt=attempt + 1, error=e.message)

                if not e.retry_suggested or attempt >= self.max_retries:
                    break

                # Wait before retry
                if attempt < self.max_retries:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff

            except Exception as e:
                last_error = ToolError(
                    message=f"Unexpected error in tool {self.name}: {str(e)}",
                    tool_name=self.name,
                    details={"exception_type": type(e).__name__, "traceback": traceback.format_exc()}
                )
                self.logger.error(f"Unexpected error in tool {self.name}: {str(e)}",
                                tool_name=self.name, exc_info=True)
                break

        # All retries failed
        self.failure_count += 1
        execution_time = time.time() - start_time

        error_message = last_error.message if last_error else f"Tool {self.name} failed after {self.max_retries + 1} attempts"

        self.logger.error(f"Tool {self.name} failed after all retries",
            tool_name=self.name,
            max_attempts=self.max_retries + 1,
            total_execution_time=execution_time
        )

        return ToolResult(
            status=ToolStatus.FAILURE,
            error=error_message,
            execution_time=execution_time,
            metadata={
                "attempts": self.max_retries + 1,
                "last_error": last_error.details if last_error else {}
            }
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get tool execution statistics.

        Returns:
            Dict[str, Any]: Tool execution statistics
        """
        success_rate = (self.success_count / self.execution_count * 100) if self.execution_count > 0 else 0
        avg_execution_time = (self.total_execution_time / self.execution_count) if self.execution_count > 0 else 0

        return {
            "tool_name": self.name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate_percent": round(success_rate, 2),
            "total_execution_time_seconds": round(self.total_execution_time, 4),
            "average_execution_time_seconds": round(avg_execution_time, 4)
        }

    def reset_statistics(self) -> None:
        """Reset tool execution statistics"""
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_execution_time = 0.0
        self.logger.info(f"Statistics reset for tool: {self.name}")

    async def health_check(self) -> ToolResult:
        """
        Perform health check for the tool.

        Override this method in subclasses for tool-specific health checks.

        Returns:
            ToolResult: Health check result
        """
        return ToolResult(
            status=ToolStatus.SUCCESS,
            data={"health": "ok", "tool_name": self.name},
            metadata={"health_check": True}
        )


# Utility functions for tool management

def validate_tool_input(required_params: List[str], provided_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that required parameters are provided.

    Args:
        required_params: List of required parameter names
        provided_params: Dictionary of provided parameters

    Returns:
        Dict[str, Any]: Validated parameters

    Raises:
        ToolError: If required parameters are missing
    """
    missing_params = [param for param in required_params if param not in provided_params]

    if missing_params:
        raise ToolError(f"Missing required parameters: {missing_params}")

    return provided_params


# TODO: Future enhancement - Add tool registry for dynamic tool discovery
# TODO: Future enhancement - Add tool dependency management
# TODO: Future enhancement - Add tool caching mechanism for expensive operations
# TODO: Future enhancement - Add tool metrics export to monitoring systems


if __name__ == "__main__":
    # Simple test implementation
    class TestTool(ToolBase):
        """Test tool implementation for demonstration"""

        async def _execute_impl(self, **kwargs) -> ToolResult:
            test_param = kwargs.get("test_param", "default")
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={"result": f"Processed: {test_param}"}
            )

        def validate_input(self, **kwargs) -> Dict[str, Any]:
            return validate_tool_input(["test_param"], kwargs)


    async def test_tool_base():
        """Test the tool base functionality"""
        print("Testing ToolBase implementation...")

        # Create test tool
        tool = TestTool("test_tool", "A test tool for demonstration")
        print(f"Created tool: {tool}")

        # Test successful execution
        result = await tool.execute(test_param="hello world")
        print(f"Execution result: {result}")

        # Test health check
        health = await tool.health_check()
        print(f"Health check: {health}")

        # Get statistics
        stats = tool.get_statistics()
        print(f"Tool statistics: {stats}")

        print("ToolBase test completed successfully!")

    # Run test
    asyncio.run(test_tool_base())
