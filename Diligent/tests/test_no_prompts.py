"""Verifies non-init commands complete without stdin (XC-07).

Runs each non-init command via CliRunner with input=None to verify
they complete without hanging or raising an error about missing input.
"""

import os

import pytest
from click.testing import CliRunner

from diligent.cli import cli


FULL_INIT_FLAGS = [
    "init",
    "--non-interactive",
    "--code", "NOPROMPT",
    "--target-legal", "NoPrompt Corp",
    "--target-common", "NoPrompt",
    "--stage", "loi",
    "--loi-date", "2026-01-15",
    "--principal", "Test",
    "--principal-role", "Lead",
    "--seller", "Seller",
    "--broker", "Broker",
    "--thesis", "Test",
    "--workstreams", "financial",
]


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def initialized_deal(runner, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
    return tmp_path


def test_doctor_no_stdin(runner, initialized_deal):
    """Doctor completes without stdin input."""
    result = runner.invoke(cli, ["doctor"], input=None, catch_exceptions=False)
    # Should not hang or error about missing input
    assert result.exit_code == 0


def test_config_get_no_stdin(runner, initialized_deal):
    """Config get completes without stdin input."""
    result = runner.invoke(
        cli, ["config", "get", "schema_version"],
        input=None, catch_exceptions=False,
    )
    assert result.exit_code == 0


def test_config_set_no_stdin(runner, initialized_deal):
    """Config set completes without stdin input."""
    result = runner.invoke(
        cli, ["config", "set", "recent_window_days", "14"],
        input=None, catch_exceptions=False,
    )
    assert result.exit_code == 0


def test_migrate_no_stdin(runner, initialized_deal):
    """Migrate completes without stdin input."""
    result = runner.invoke(cli, ["migrate"], input=None, catch_exceptions=False)
    # May succeed or print "no migrations needed" -- either way, no prompt
    assert result.exit_code == 0
