"""Tests for verification gate comparison logic in numeric.py.

Tests try_parse_numeric (currency/percentage/whitespace stripping) and
compute_gate_result (no-op fast path, exact match, anchor tolerance,
zero-to-nonzero, parse fallback).
"""

import pytest

from diligent.helpers.numeric import compute_gate_result, try_parse_numeric


class TestTryParseNumeric:
    """try_parse_numeric: strip currency/percent/whitespace, return float or None."""

    def test_currency_with_commas(self):
        """try_parse_numeric('$1,234.56') returns 1234.56."""
        assert try_parse_numeric("$1,234.56") == pytest.approx(1234.56)

    def test_percentage(self):
        """try_parse_numeric('15%') returns 15.0."""
        assert try_parse_numeric("15%") == pytest.approx(15.0)

    def test_currency_with_spaces_and_commas(self):
        """try_parse_numeric(' $ 20,065 ') returns 20065.0."""
        assert try_parse_numeric(" $ 20,065 ") == pytest.approx(20065.0)

    def test_non_numeric_returns_none(self):
        """try_parse_numeric('N/A') returns None."""
        assert try_parse_numeric("N/A") is None

    def test_empty_string_returns_none(self):
        """try_parse_numeric('') returns None."""
        assert try_parse_numeric("") is None


class TestComputeGateResult:
    """compute_gate_result: gate comparison logic for truth set."""

    def test_bytewise_equal_returns_none(self):
        """Bytewise equal values produce no gate (no-op fast path)."""
        result = compute_gate_result("$1,234", "$1,234", is_anchor=False, tolerance_pct=0.5)
        assert result is None

    def test_non_anchor_different_values_fires(self):
        """Non-anchor fact with different value fires gate."""
        result = compute_gate_result("100", "101", is_anchor=False, tolerance_pct=0.5)
        assert result is not None
        assert result["fired"] is True

    def test_anchor_within_tolerance_returns_none(self):
        """Anchor fact within tolerance produces no gate."""
        # 0.1% change, well within 0.5% tolerance
        result = compute_gate_result("10000", "10005", is_anchor=True, tolerance_pct=0.5)
        assert result is None

    def test_anchor_beyond_tolerance_fires(self):
        """Anchor fact beyond tolerance fires gate with delta_str."""
        # 5% change, well beyond 0.5% tolerance
        result = compute_gate_result("10000", "10500", is_anchor=True, tolerance_pct=0.5)
        assert result is not None
        assert result["fired"] is True
        assert result["delta_str"] is not None

    def test_zero_to_nonzero_fires(self):
        """Old=0, new=100 always fires regardless of tolerance."""
        result = compute_gate_result("0", "100", is_anchor=True, tolerance_pct=0.5)
        assert result is not None
        assert result["fired"] is True

    def test_both_zero_returns_none(self):
        """Old=0, new=0 is bytewise equal, returns None."""
        result = compute_gate_result("0", "0", is_anchor=True, tolerance_pct=0.5)
        assert result is None

    def test_anchor_non_numeric_fallback_fires(self):
        """Anchor where one side fails numeric parse falls back to exact match (fires)."""
        result = compute_gate_result("old text", "new text", is_anchor=True, tolerance_pct=0.5)
        assert result is not None
        assert result["fired"] is True
