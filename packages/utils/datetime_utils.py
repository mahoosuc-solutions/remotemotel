"""
Datetime utilities for handling UTC timestamps

Provides future-proof datetime functions that work across Python versions.
Python 3.12+ deprecated datetime.utcnow() in favor of datetime.now(datetime.UTC).
"""

from datetime import datetime, timezone
import sys

# Check Python version for UTC handling
PYTHON_VERSION = sys.version_info


def utc_now() -> datetime:
    """
    Get current UTC datetime

    Returns timezone-aware UTC datetime compatible with all Python versions.
    Uses datetime.now(timezone.utc) which is the modern recommended approach.

    Returns:
        datetime: Current UTC time (timezone-aware)
    """
    return datetime.now(timezone.utc)


def utc_timestamp() -> float:
    """
    Get current UTC timestamp (seconds since epoch)

    Returns:
        float: UTC timestamp in seconds
    """
    return datetime.now(timezone.utc).timestamp()


def to_utc(dt: datetime) -> datetime:
    """
    Convert datetime to UTC

    Args:
        dt: Datetime to convert (naive or aware)

    Returns:
        datetime: UTC datetime (timezone-aware)
    """
    if dt.tzinfo is None:
        # Assume naive datetime is already UTC
        return dt.replace(tzinfo=timezone.utc)
    else:
        # Convert to UTC
        return dt.astimezone(timezone.utc)


def to_iso_string(dt: datetime) -> str:
    """
    Convert datetime to ISO 8601 string

    Args:
        dt: Datetime to convert

    Returns:
        str: ISO 8601 formatted string (e.g., "2025-10-23T10:30:45.123456+00:00")
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def from_timestamp(ts: float) -> datetime:
    """
    Create UTC datetime from timestamp

    Args:
        ts: Unix timestamp (seconds since epoch)

    Returns:
        datetime: UTC datetime (timezone-aware)
    """
    return datetime.fromtimestamp(ts, tz=timezone.utc)


# Backward compatibility aliases (for migration)
def utcnow() -> datetime:
    """
    DEPRECATED: Use utc_now() instead

    Provided for backward compatibility during migration.
    """
    return utc_now()
