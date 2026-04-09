"""Numeric parsing and verification gate comparison logic.

Provides try_parse_numeric (strip currency/percent/whitespace, return float)
and compute_gate_result (gate comparison for truth set).

The gate comparison logic is the load-bearing behavior of the entire CLI:
when a fact value changes beyond tolerance, the gate fires, preventing
silent overwrites of validated data.
"""

import re
from typing import Optional

# Compiled regex: strip $, commas, %, whitespace
_STRIP_RE = re.compile(r"[\$,%\s]")


def try_parse_numeric(value: str) -> Optional[float]:
    """Attempt to parse a string as a numeric value.

    Strips currency symbols ($), commas, percent signs, and whitespace
    before attempting float conversion.

    Args:
        value: Raw string value (e.g., "$1,234.56", "15%", " $ 20,065 ").

    Returns:
        Parsed float, or None if the value cannot be parsed as a number.
    """
    if not value or not value.strip():
        return None

    cleaned = _STRIP_RE.sub("", value)
    if not cleaned:
        return None

    try:
        return float(cleaned)
    except ValueError:
        return None


def compute_gate_result(
    old_value: str,
    new_value: str,
    is_anchor: bool,
    tolerance_pct: float,
) -> Optional[dict]:
    """Compute whether the verification gate should fire.

    Implements the locked gate comparison logic:
    1. No-op fast path: bytewise equal values produce no gate.
    2. Non-anchor facts: any string difference fires the gate.
    3. Anchor facts: best-effort numeric parse. If both parse, apply
       percentage tolerance. If either fails, fall back to exact match.
    4. Zero-to-nonzero always fires (division by zero edge case).

    Args:
        old_value: Current stored value string.
        new_value: Proposed new value string.
        is_anchor: Whether the fact is marked as an anchor metric.
        tolerance_pct: Percentage tolerance for anchor comparison.

    Returns:
        None if no gate fires (no-op, within tolerance).
        Dict with keys: fired (bool), delta_str (str|None), verdict (str)
        when gate fires.
    """
    # 1. No-op fast path: bytewise equal
    if old_value == new_value:
        return None

    # 2. Non-anchor: any difference fires
    if not is_anchor:
        return {
            "fired": True,
            "delta_str": None,
            "verdict": "Value changed (non-anchor, exact match required)",
        }

    # 3. Anchor: attempt numeric comparison
    old_num = try_parse_numeric(old_value)
    new_num = try_parse_numeric(new_value)

    # If either side fails numeric parse, fall back to exact match
    if old_num is None or new_num is None:
        return {
            "fired": True,
            "delta_str": None,
            "verdict": "Value changed (non-numeric, exact match fallback)",
        }

    # 4. Zero-to-nonzero always fires
    if old_num == 0.0 and new_num != 0.0:
        delta_str = f"+{new_num:,.2f} (0 to non-zero)"
        return {
            "fired": True,
            "delta_str": delta_str,
            "verdict": "Zero-to-nonzero change (always requires confirmation)",
        }

    # Both numeric, old != 0: compute percentage delta
    pct_delta = abs((new_num - old_num) / old_num) * 100

    if pct_delta <= tolerance_pct:
        # Within tolerance: no gate
        return None

    # Beyond tolerance: fire
    direction = "+" if new_num > old_num else ""
    abs_delta = new_num - old_num
    delta_str = f"{direction}{abs_delta:,.2f} ({pct_delta:.1f}%)"

    return {
        "fired": True,
        "delta_str": delta_str,
        "verdict": f"Value changed by {pct_delta:.1f}% (tolerance: {tolerance_pct}%)",
    }
