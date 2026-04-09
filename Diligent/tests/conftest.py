"""Shared test fixtures for diligent test suite."""

import json
import pytest
from click.testing import CliRunner
from pathlib import Path


@pytest.fixture
def tmp_deal_dir(tmp_path):
    """Create a temporary directory simulating a deal folder."""
    return tmp_path


@pytest.fixture
def diligence_dir(tmp_deal_dir):
    """Create a .diligence/ directory inside the deal folder."""
    d = tmp_deal_dir / ".diligence"
    d.mkdir()
    return d


@pytest.fixture
def cli_runner():
    """Return a Click CliRunner with separate stderr."""
    return CliRunner()


@pytest.fixture
def sample_config(diligence_dir):
    """Write a minimal config.json for tests that need one."""
    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 1.0,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    config_path = diligence_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config_path
