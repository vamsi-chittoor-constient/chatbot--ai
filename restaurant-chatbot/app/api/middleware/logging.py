"""
Structured Logging Configuration
=================================
Admin-ready logging system for conversation analytics
"""

import sys
import os
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import config
from app.core.logging_config import setup_logging as setup_detailed_logging


def setup_logging():
    """
    Configure structured logging for the application
    Admin-ready: All logs structured for easy analytics queries

    Uses the detailed logger from app.utils.logger for full debugging information.
    """

    # Use the detailed logger configuration from utils/logger.py
    # This provides full debugging info with all context fields
    log_level = "DEBUG" if config.DEBUG else "INFO"

    # Check if user wants to force colors via environment variable
    force_colors = None
    if os.environ.get('FORCE_COLOR', '').lower() in ('1', 'true', 'yes'):
        force_colors = True
    elif os.environ.get('NO_COLOR', '').lower() in ('1', 'true', 'yes'):
        force_colors = False

    setup_detailed_logging(
        log_level=log_level,
        log_file="logs/restaurant_ai.log",
        console_output=True,
        force_colors=force_colors
    )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log all HTTP requests for admin analytics
    Captures performance metrics and usage patterns
    """

    async def dispatch(self, request: Request, call_next):
        """Log request/response for admin analytics"""

        # Start timing
        start_time = datetime.now(timezone.utc)

        # Get logger
        logger = structlog.get_logger("api.requests")

        # Log request start
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            timestamp=start_time.isoformat(),
            # Admin analytics fields
            restaurant_id=request.path_params.get("restaurant_id"),
            session_id=request.path_params.get("session_id"),
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            # Log successful response
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_seconds=duration,
                response_size=response.headers.get("content-length"),
                timestamp=end_time.isoformat(),
                # Admin analytics fields
                restaurant_id=request.path_params.get("restaurant_id"),
                session_id=request.path_params.get("session_id"),
            )

            return response

        except Exception as e:
            # Calculate duration for failed requests
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            # Log error
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=duration,
                timestamp=end_time.isoformat(),
                # Admin analytics fields
                restaurant_id=request.path_params.get("restaurant_id"),
                session_id=request.path_params.get("session_id"),
            )

            raise


def log_chat_message(
    session_id: str,
    message_type: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log chat messages for conversation analytics
    Admin-ready: Structured for admin dashboard queries

    Enhanced: Shows full conversation messages with visual separators
    """

    logger = structlog.get_logger("ai.chat")

    log_data = {
        "event": "chat_message",
        "session_id": session_id,
        "message_type": message_type,  # "user_message" or "ai_response"
        "content_length": len(content),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Add metadata for admin analytics
    if metadata:
        log_data.update(metadata)

    # Always show full content in development for easier debugging
    if config.DEBUG or config.ENVIRONMENT == 'development':
        # Show full message (no truncation) for visibility
        log_data["content_preview"] = content

        # Add visual separator for readability
        if message_type == "user_message":
            # User messages clearly marked
            logger.info(
                "\n" + "="*80 + "\n" +
                f"USER MESSAGE (session: {session_id[:8]}...)\n" +
                f"{'-'*80}\n" +
                f"{content}\n" +
                "="*80
            )
        elif message_type == "ai_response":
            # AI responses clearly marked
            logger.info(
                "\n" + "="*80 + "\n" +
                f"ASSISTANT RESPONSE (session: {session_id[:8]}...)\n" +
                f"{'-'*80}\n" +
                f"{content}\n" +
                "="*80
            )

    # Log structured data for analytics (always)
    logger.info(**log_data)


def log_ai_agent_call(
    session_id: str,
    agent_name: str,
    action: str,
    success: bool,
    duration_seconds: float,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Log AI agent calls for performance monitoring
    Admin-ready: Agent performance analytics
    """

    logger = structlog.get_logger("ai.agents")

    log_data = {
        "event": "agent_call",
        "session_id": session_id,
        "agent_name": agent_name,
        "action": action,
        "success": success,
        "duration_seconds": duration_seconds,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Add metadata
    if metadata:
        log_data.update(metadata)

    if success:
        logger.info(**log_data)
    else:
        logger.error(**log_data)


def log_system_event(
    event_type: str,
    details: Dict[str, Any],
    level: str = "info"
):
    """
    Log system events for admin monitoring
    Admin-ready: System health and performance tracking
    """

    logger = structlog.get_logger("system.events")

    log_data = {
        "event": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **details
    }

    if level == "error":
        logger.error(**log_data)
    elif level == "warning":
        logger.warning(**log_data)
    else:
        logger.info(**log_data)
