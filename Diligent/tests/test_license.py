"""Verifies LICENSE file contains BSL text (XC-08)."""

from pathlib import Path

import pytest


def test_license_file_exists():
    """LICENSE file exists at Diligent/LICENSE."""
    license_path = Path(__file__).parent.parent / "LICENSE"
    assert license_path.exists(), f"LICENSE not found at {license_path}"


def test_license_contains_bsl():
    """LICENSE contains 'Business Source License' text."""
    license_path = Path(__file__).parent.parent / "LICENSE"
    content = license_path.read_text(encoding="utf-8")
    assert "Business Source License" in content


def test_license_contains_licensor():
    """LICENSE contains 'Bryce Masterson' as licensor."""
    license_path = Path(__file__).parent.parent / "LICENSE"
    content = license_path.read_text(encoding="utf-8")
    assert "Bryce Masterson" in content
