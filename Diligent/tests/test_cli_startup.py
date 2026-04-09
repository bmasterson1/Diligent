"""Benchmark test for CLI startup time.

Verifies diligent --help completes in under 200ms via subprocess
(not CliRunner -- subprocess measures real import time).
"""

import subprocess
import sys
import time

import pytest


@pytest.mark.slow
def test_cli_help_under_200ms():
    """diligent --help must complete in under 200ms (average of 3 runs)."""
    times = []
    for _ in range(3):
        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, "-m", "diligent", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        elapsed = time.perf_counter() - start
        times.append(elapsed)
        assert result.returncode == 0, result.stderr

    avg_ms = (sum(times) / len(times)) * 1000
    assert avg_ms < 200, f"Average startup time {avg_ms:.0f}ms exceeds 200ms limit"
