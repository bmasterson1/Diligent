"""Tests for time_utils helper functions.

Pure function tests for parse_since, is_recent, and relative_time_str.
No fixtures needed beyond datetime imports.
"""

from datetime import date, timedelta

import pytest

from diligent.helpers.time_utils import is_recent, parse_since, relative_time_str


class TestParseSince:
    """Tests for parse_since(since_str, default_days)."""

    def test_none_returns_default_days_ago(self):
        """parse_since(None, 14) returns date 14 days ago."""
        result = parse_since(None, 14)
        expected = date.today() - timedelta(days=14)
        assert result == expected

    def test_relative_format_7d(self):
        """parse_since('7d', 14) returns date 7 days ago."""
        result = parse_since("7d", 14)
        expected = date.today() - timedelta(days=7)
        assert result == expected

    def test_iso_date_string(self):
        """parse_since('2026-03-15', 14) returns date(2026, 3, 15)."""
        result = parse_since("2026-03-15", 14)
        assert result == date(2026, 3, 15)


class TestIsRecent:
    """Tests for is_recent(entry_date_str, cutoff)."""

    def test_recent_date_returns_true(self):
        """is_recent('2026-04-01', cutoff=date(2026, 3, 25)) returns True."""
        result = is_recent("2026-04-01", cutoff=date(2026, 3, 25))
        assert result is True

    def test_old_date_returns_false(self):
        """is_recent('2026-03-01', cutoff=date(2026, 3, 25)) returns False."""
        result = is_recent("2026-03-01", cutoff=date(2026, 3, 25))
        assert result is False

    def test_empty_string_returns_false(self):
        """is_recent('', cutoff) returns False."""
        result = is_recent("", cutoff=date(2026, 3, 25))
        assert result is False

    def test_none_returns_false(self):
        """is_recent(None, cutoff) returns False."""
        result = is_recent(None, cutoff=date(2026, 3, 25))
        assert result is False

    def test_exact_cutoff_returns_true(self):
        """Date equal to cutoff is considered recent."""
        result = is_recent("2026-03-25", cutoff=date(2026, 3, 25))
        assert result is True


class TestRelativeTimeStr:
    """Tests for relative_time_str(days_ago, ref_date)."""

    def test_zero_returns_today(self):
        """relative_time_str(0) returns 'today'."""
        assert relative_time_str(0) == "today"

    def test_one_day(self):
        """relative_time_str(1) returns '1d ago'."""
        assert relative_time_str(1) == "1d ago"

    def test_seven_days(self):
        """relative_time_str(7) returns '7d ago'."""
        assert relative_time_str(7) == "7d ago"

    def test_fourteen_days_boundary(self):
        """relative_time_str(14) returns '14d ago' (boundary of relative)."""
        assert relative_time_str(14) == "14d ago"

    def test_beyond_fourteen_returns_iso_date(self):
        """relative_time_str(15, ref_date) returns ISO date string."""
        ref = date(2026, 4, 8)
        result = relative_time_str(15, ref_date=ref)
        # 15 days before 2026-04-08 = 2026-03-24
        assert result == "2026-03-24"

    def test_beyond_fourteen_no_ref_date(self):
        """relative_time_str(15) without ref_date uses today."""
        result = relative_time_str(15)
        expected = (date.today() - timedelta(days=15)).isoformat()
        assert result == expected
