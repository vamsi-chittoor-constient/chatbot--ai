"""
Feature-Level Metrics and Monitoring
====================================

Prometheus metrics for tracking feature performance and errors.

Metrics:
- Request counters by feature/sub-intent
- Latency histograms
- Error counters
- Tool execution tracking
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
from time import time
from typing import Callable, Any
import asyncio


# ============================================================================
# FEATURE METRICS
# ============================================================================

# Request counter
feature_requests_total = Counter(
    'feature_requests_total',
    'Total requests processed by feature',
    ['feature', 'sub_intent']
)

# Latency histogram
feature_latency_seconds = Histogram(
    'feature_latency_seconds',
    'Feature processing latency in seconds',
    ['feature', 'sub_intent'],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
)

# Error counter
feature_errors_total = Counter(
    'feature_errors_total',
    'Total errors by feature',
    ['feature', 'error_type']
)

# Active sessions gauge
feature_active_sessions = Gauge(
    'feature_active_sessions',
    'Number of active sessions',
    ['feature']
)


# ============================================================================
# TOOL METRICS
# ============================================================================

# Tool execution counter
tool_executions_total = Counter(
    'tool_executions_total',
    'Total tool executions',
    ['feature', 'tool_name', 'status']
)

# Tool latency histogram
tool_latency_seconds = Histogram(
    'tool_latency_seconds',
    'Tool execution latency in seconds',
    ['feature', 'tool_name'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)
)


# ============================================================================
# DATABASE METRICS
# ============================================================================

# Database query counter
db_queries_total = Counter(
    'db_queries_total',
    'Total database queries',
    ['feature', 'operation', 'table']
)

# Database query latency
db_query_latency_seconds = Histogram(
    'db_query_latency_seconds',
    'Database query latency in seconds',
    ['feature', 'operation'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0)
)


# ============================================================================
# CACHE METRICS
# ============================================================================

# Cache hit/miss counter
cache_operations_total = Counter(
    'cache_operations_total',
    'Total cache operations',
    ['feature', 'operation', 'result']  # operation: get/set/delete, result: hit/miss/success/error
)


# ============================================================================
# DECORATORS
# ============================================================================

def track_feature_metrics(feature: str):
    """
    Decorator to track feature request metrics.

    Usage:
        @track_feature_metrics("food_ordering")
        async def process_cart_operation(sub_intent: str, **kwargs):
            # ... processing
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            sub_intent = kwargs.get('sub_intent', 'unknown')
            start_time = time()

            try:
                # Increment request counter
                feature_requests_total.labels(
                    feature=feature,
                    sub_intent=sub_intent
                ).inc()

                # Execute function
                result = await func(*args, **kwargs)

                # Record latency
                latency = time() - start_time
                feature_latency_seconds.labels(
                    feature=feature,
                    sub_intent=sub_intent
                ).observe(latency)

                return result

            except Exception as e:
                # Record error
                feature_errors_total.labels(
                    feature=feature,
                    error_type=type(e).__name__
                ).inc()
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            sub_intent = kwargs.get('sub_intent', 'unknown')
            start_time = time()

            try:
                # Increment request counter
                feature_requests_total.labels(
                    feature=feature,
                    sub_intent=sub_intent
                ).inc()

                # Execute function
                result = func(*args, **kwargs)

                # Record latency
                latency = time() - start_time
                feature_latency_seconds.labels(
                    feature=feature,
                    sub_intent=sub_intent
                ).observe(latency)

                return result

            except Exception as e:
                # Record error
                feature_errors_total.labels(
                    feature=feature,
                    error_type=type(e).__name__
                ).inc()
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_tool_execution(feature: str, tool_name: str):
    """
    Decorator to track tool execution metrics.

    Usage:
        @track_tool_execution("food_ordering", "add_to_cart")
        async def execute_tool(**kwargs):
            # ... tool execution
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time()
            status = "success"

            try:
                result = await func(*args, **kwargs)

                # Determine status from result
                if hasattr(result, 'status'):
                    status = result.status.value if hasattr(result.status, 'value') else str(result.status)

                return result

            except Exception as e:
                status = "error"
                raise

            finally:
                # Record execution
                tool_executions_total.labels(
                    feature=feature,
                    tool_name=tool_name,
                    status=status
                ).inc()

                # Record latency
                latency = time() - start_time
                tool_latency_seconds.labels(
                    feature=feature,
                    tool_name=tool_name
                ).observe(latency)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time()
            status = "success"

            try:
                result = func(*args, **kwargs)

                # Determine status from result
                if hasattr(result, 'status'):
                    status = result.status.value if hasattr(result.status, 'value') else str(result.status)

                return result

            except Exception as e:
                status = "error"
                raise

            finally:
                # Record execution
                tool_executions_total.labels(
                    feature=feature,
                    tool_name=tool_name,
                    status=status
                ).inc()

                # Record latency
                latency = time() - start_time
                tool_latency_seconds.labels(
                    feature=feature,
                    tool_name=tool_name
                ).observe(latency)

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


# ============================================================================
# MANUAL METRIC RECORDING
# ============================================================================

def record_cache_operation(feature: str, operation: str, result: str):
    """
    Record cache operation metric.

    Args:
        feature: Feature name
        operation: Operation type (get, set, delete)
        result: Result (hit, miss, success, error)
    """
    cache_operations_total.labels(
        feature=feature,
        operation=operation,
        result=result
    ).inc()


def record_db_query(feature: str, operation: str, table: str, latency: float):
    """
    Record database query metric.

    Args:
        feature: Feature name
        operation: Operation type (select, insert, update, delete)
        table: Table name
        latency: Query latency in seconds
    """
    db_queries_total.labels(
        feature=feature,
        operation=operation,
        table=table
    ).inc()

    db_query_latency_seconds.labels(
        feature=feature,
        operation=operation
    ).observe(latency)
