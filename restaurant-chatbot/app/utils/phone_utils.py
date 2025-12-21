"""
Phone Number Utilities
======================
Shared utilities for consistent phone number formatting across the application.
"""


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to international format with country code.
    Handles Indian phone numbers (adds +91 if missing).

    Args:
        phone: Phone number in any format (with or without country code)

    Returns:
        Phone number in international format (+919566070120)

    Examples:
        >>> normalize_phone_number("9566070120")
        '+919566070120'
        >>> normalize_phone_number("919566070120")
        '+919566070120'
        >>> normalize_phone_number("+919566070120")
        '+919566070120'
    """
    # Remove all non-digit characters except leading +
    if phone.startswith('+'):
        digits_only = '+' + ''.join(filter(str.isdigit, phone[1:]))
    else:
        digits_only = ''.join(filter(str.isdigit, phone))

    # If starts with 91 and has 12 digits total (91 + 10 digits), add +
    if digits_only.startswith('91') and len(digits_only) == 12:
        return f'+{digits_only}'

    # If 10 digits (Indian mobile), add +91
    if len(digits_only) == 10:
        return f'+91{digits_only}'

    # If already has + prefix and looks valid, return as is
    if digits_only.startswith('+'):
        return digits_only

    # Default: assume Indian number and add +91
    return f'+91{digits_only}'
