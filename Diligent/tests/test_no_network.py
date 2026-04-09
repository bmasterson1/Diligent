"""Verifies no HTTP/network imports in diligent source (XC-03).

Static analysis test: scans all .py files under diligent/ and checks
that none import network libraries.
"""

import re
from pathlib import Path

import pytest


NETWORK_IMPORT_PATTERN = re.compile(
    r"^\s*(import|from)\s+(requests|urllib|http\.client|httpx|aiohttp|socket)\b",
    re.MULTILINE,
)


def test_no_network_imports():
    """No .py file under diligent/ imports network libraries."""
    package_dir = Path(__file__).parent.parent / "diligent"
    assert package_dir.is_dir(), f"Package directory not found: {package_dir}"

    violations = []
    for py_file in package_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        matches = NETWORK_IMPORT_PATTERN.findall(content)
        if matches:
            violations.append(
                f"{py_file.relative_to(package_dir.parent)}: imports {[m[1] for m in matches]}"
            )

    assert not violations, (
        "Network imports found in source files:\n" + "\n".join(violations)
    )
