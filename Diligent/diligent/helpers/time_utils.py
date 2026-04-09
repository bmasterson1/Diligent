"""Time utilities shared by status and handoff commands.

Three pure functions, no I/O imports. Used for date parsing,
recency checks, and human-readable relative time display.
"""

import re
from datetime import date, timedelta
from typing import Optional


_RELATIVE_RE = re.compile(r"^(\d+)d$")


def parse_since(since_str: Optional[str], default_days: int) -> date:
    """Parse a since string into a cutoff date.

    Accepts:
    - None: returns date default_days ago from today
    - "Nd" relative format (e.g., "7d"): returns date N days ago
    - "YYYY-MM-DD" ISO date string: returns that date

    Args:
        since_str: The since string to parse, or None for default.
        default_days: Number of days ago to use when since_str is None.

    Returns:
        A date object representing the cutoff.
    """
    if since_str is None:
        return date.today() - timedelta(days=default_days)

    match = _RELATIVE_RE.match(since_str)
    if match:
        days = int(match.group(1))
        return date.today() - timedelta(days=days)

    return date.fromisoformat(since_str)


def is_recent(entry_date_str: Optional[str], cutoff: date) -> bool:
    """Check if an entry date string is recent relative to a cutoff.

    Parses the first 10 characters of entry_date_str as an ISO date.
    Returns True if the parsed date >= cutoff. Returns False on empty
    string, None, or parse failure.

    Args:
        entry_date_str: ISO date string (may include time portion).
        cutoff: The cutoff date for recency.

    Returns:
        True if the entry date is on or after the cutoff.
    """
    if not entry_date_str:
        return False

    try:
        entry_date = date.fromisoformat(entry_date_str[:10])
        return entry_date >= cutoff
    except (ValueError, TypeError):
        return False


def relative_time_str(days_ago: int, ref_date: Optional[date] = None) -> str:
    """Format a number of days ago as a human-readable string.

    If days_ago <= 14, returns relative format ("today", "1d ago", etc.).
    If days_ago > 14, returns the ISO date string computed from ref_date
    (defaults to today).

    Args:
        days_ago: Number of days in the past.
        ref_date: Reference date for computing absolute date. Defaults to today.

    Returns:
        Human-readable time string.
    """
    if days_ago == 0:
        return "today"

    if days_ago <= 14:
        return f"{days_ago}d ago"

    if ref_date is None:
        ref_date = date.today()
    return (ref_date - timedelta(days=days_ago)).isoformat()
