"""
Response Sanitizer
==================
Security layer to prevent internal errors, JSON, and system states from reaching frontend.

All responses MUST pass through this layer before being sent to users.
"""

import re
import json
import structlog
from typing import Any, Dict, Optional

logger = structlog.get_logger("core.response_sanitizer")


class ResponseSanitizer:
    """
    Sanitizes all responses to ensure:
    1. No raw JSON objects in responses
    2. No Python error messages or stack traces
    3. No internal system states
    4. Only user-friendly natural language
    """

    # Patterns that indicate internal leakage
    FORBIDDEN_PATTERNS = [
        r'\{["\']name["\']\s*:\s*["\'].+?["\']\s*,',  # JSON objects like {"name": "item", ...}
        r'Traceback \(most recent call last\)',         # Python tracebacks
        r'File "[^"]+", line \d+',                      # Python file references
        r'Error: .+ is not defined',                    # Python NameError
        r'Exception: ',                                 # Python exceptions
        r'KeyError: ',                                  # Python KeyError
        r'AttributeError: ',                            # Python AttributeError
        r'TypeError: ',                                 # Python TypeError
        r'\[TOOL_\w+\]',                                # Tool execution markers
        r'\[DEBUG\]',                                   # Debug markers
        r'\[INTERNAL\]',                                # Internal markers
    ]

    # User-friendly error replacements
    ERROR_REPLACEMENTS = {
        "datetime": "We encountered a technical issue while processing your order. Please try again.",
        "not defined": "We encountered a technical issue. Our team has been notified. Please try again.",
        "Traceback": "Oops! Something went wrong. Please try again or contact support.",
        "Exception": "We're experiencing a technical difficulty. Please try again in a moment.",
        "KeyError": "We couldn't find the information needed. Please try rephrasing your request.",
        "AttributeError": "We encountered an unexpected issue. Please try again.",
        "TypeError": "We received invalid data. Please try again with different input.",
    }

    @staticmethod
    def sanitize_response(response: str) -> str:
        """
        Sanitize a response before sending to frontend.

        Args:
            response: Raw response from crew agent or system

        Returns:
            Sanitized, user-friendly response
        """
        if not response or not isinstance(response, str):
            return "I'm here to help! What would you like to order?"

        original_response = response

        try:
            # Step 1: Check for forbidden patterns
            for pattern in ResponseSanitizer.FORBIDDEN_PATTERNS:
                if re.search(pattern, response, re.IGNORECASE):
                    logger.warning(
                        "forbidden_pattern_detected",
                        pattern=pattern,
                        response_preview=response[:100]
                    )

                    # Try to extract user-friendly parts
                    response = ResponseSanitizer._extract_user_friendly_content(response)
                    break

            # Step 2: BLOCK raw JSON objects entirely (LLM should never return JSON)
            if ResponseSanitizer._contains_raw_json(response):
                logger.error(
                    "raw_json_blocked_llm_returned_incorrectly",
                    response_preview=response[:100]
                )
                # Crew execution completed but returned wrong format - ask user to retry
                return "I apologize, I couldn't process that correctly. Could you please try again or rephrase your request?"

            # Step 3: Replace technical errors with user-friendly messages
            for error_keyword, replacement in ResponseSanitizer.ERROR_REPLACEMENTS.items():
                if error_keyword.lower() in response.lower():
                    logger.error(
                        "technical_error_in_response",
                        error_keyword=error_keyword,
                        response_preview=response[:100]
                    )
                    return replacement

            # Step 4: Remove any remaining technical markers
            response = re.sub(r'\[TOOL_\w+\]', '', response)
            response = re.sub(r'\[DEBUG\]', '', response)
            response = re.sub(r'\[INTERNAL\]', '', response)

            # Step 4b: Remove internal food-ordering context markers
            # These are meant for the LLM agent, not for user display.
            response = re.sub(
                r'\[(?:SEARCH RESULTS DISPLAYED|MENU CARD DISPLAYED|MENU DISPLAYED'
                r'|CART CARD DISPLAYED|EMPTY CART|ALTERNATIVE CATEGORY MENU DISPLAYED'
                r'|INVALID QUANTITY|INVALID INSTRUCTIONS'
                r'|CHECKOUT COMPLETE|PAYMENT CONFIRMED|PAYMENT LINK SENT)[^\]]*\]\s*',
                '', response
            )

            # Step 4c: Remove leaked language directive prefixes
            response = re.sub(
                r'\[RESPOND IN (?:HINGLISH|TANGLISH)[^\]]*\]\s*',
                '', response, flags=re.IGNORECASE
            )

            # Step 5: Ensure response is not empty after sanitization
            response = response.strip()
            if not response or len(response) < 5:
                return "I'm ready to help! What would you like to order?"

            return response

        except Exception as e:
            logger.error(
                "sanitization_failed",
                error=str(e),
                original_response_preview=original_response[:100]
            )
            # Fallback to safe default message
            return "I'm here to help you with your order. What can I get for you?"

    @staticmethod
    def _contains_raw_json(text: str) -> bool:
        """
        Check if text contains raw JSON objects.

        JSON in responses means the LLM returned prematurely instead of calling tools.
        This is a bug that should be blocked entirely.
        """
        # Remove markdown code fences if present
        text_clean = re.sub(r'```(?:json)?\s*', '', text)
        text_clean = text_clean.strip()

        # Strategy 1: Try to parse as JSON
        # If it's valid JSON starting with {, it's definitely JSON
        if text_clean.startswith('{'):
            try:
                json.loads(text_clean)
                # Successfully parsed as JSON - this is a leak!
                return True
            except (json.JSONDecodeError, ValueError):
                pass  # Not valid JSON, continue checking

        # Strategy 2: Look for JSON-like patterns (handles partial JSON or JSON in text)
        # Match: { "key": "value" } or { key: value } with optional whitespace/newlines
        json_patterns = [
            r'\{\s*["\']?\w+["\']?\s*:\s*["\']?[^}]*["\']?\s*,?\s*["\']?\w+["\']?\s*:\s*',  # Multiple key-value pairs
            r'\{\s*["\']?\w+["\']?\s*:\s*(?:["\'][^"\']*["\']|\d+)\s*\}',  # Single key-value pair
        ]

        for pattern in json_patterns:
            if re.search(pattern, text_clean, re.DOTALL):
                return True

        return False

    @staticmethod
    def _extract_user_friendly_content(text: str) -> str:
        """
        Extract user-friendly content from text that may contain technical details.

        Strategy: Look for complete sentences that don't contain technical markers.
        """
        # Split by sentences
        sentences = re.split(r'[.!?]+', text)

        user_friendly_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()

            # Skip if too short
            if len(sentence) < 10:
                continue

            # Skip if contains technical markers
            has_technical = False
            for pattern in ResponseSanitizer.FORBIDDEN_PATTERNS:
                if re.search(pattern, sentence, re.IGNORECASE):
                    has_technical = True
                    break

            if not has_technical:
                user_friendly_sentences.append(sentence)

        if user_friendly_sentences:
            return ". ".join(user_friendly_sentences) + "."
        else:
            # No user-friendly content found - return safe default
            return "I apologize for the confusion. Could you please rephrase your request?"

    @staticmethod
    def sanitize_error(error: Exception) -> str:
        """
        Convert technical errors to user-friendly messages.

        Args:
            error: Exception object

        Returns:
            User-friendly error message
        """
        error_str = str(error).lower()

        # Check for specific error types
        if "datetime" in error_str or "not defined" in error_str:
            return "We're experiencing a technical issue. Our team has been notified. Please try again."
        elif "database" in error_str or "connection" in error_str:
            return "We're having trouble connecting to our system. Please try again in a moment."
        elif "timeout" in error_str:
            return "This is taking longer than expected. Please try again."
        elif "permission" in error_str or "forbidden" in error_str:
            return "We couldn't complete that action. Please contact support if this continues."
        else:
            return "Something went wrong. Please try again or rephrase your request."


# Singleton instance
_sanitizer = ResponseSanitizer()


def sanitize_response(response: str) -> str:
    """Global function to sanitize responses."""
    return _sanitizer.sanitize_response(response)


def sanitize_error(error: Exception) -> str:
    """Global function to sanitize errors."""
    return _sanitizer.sanitize_error(error)
