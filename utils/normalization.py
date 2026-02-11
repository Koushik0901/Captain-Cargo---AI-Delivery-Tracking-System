"""Tracking ID normalization utilities."""

import re


def normalize_tracking_id(raw_id: str) -> str:
    """Normalize tracking ID by removing non-alphanumeric characters and uppercasing.

    Args:
        raw_id: The raw tracking ID from user input.

    Returns:
        Normalized tracking ID in uppercase, alphanumeric only.

    Raises:
        ValueError: If the normalized ID is empty or outside valid length range.
    """
    if not raw_id:
        raise ValueError("Tracking ID cannot be empty")

    cleaned = re.sub(r"[^A-Za-z0-9]", "", raw_id)
    normalized = cleaned.upper()

    if len(normalized) < 6:
        raise ValueError(
            f"Tracking ID too short after normalization: '{normalized}' (minimum 6 characters)"
        )
    if len(normalized) > 32:
        raise ValueError(
            f"Tracking ID too long after normalization: '{normalized}' (maximum 32 characters)"
        )

    return normalized


def validate_tracking_id(tracking_id: str) -> bool:
    """Check if a tracking ID is valid (already normalized).

    Args:
        tracking_id: The tracking ID to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        normalized = normalize_tracking_id(tracking_id)
        return normalized == tracking_id
    except ValueError:
        return False
