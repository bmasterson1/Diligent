"""Tests for diligent config get/set commands."""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.cli import cli


FULL_INIT_FLAGS = [
    "init",
    "--non-interactive",
    "--code", "TESTCO",
    "--target-legal", "Test Corp",
    "--target-common", "Test",
    "--stage", "loi",
    "--loi-date", "2026-01-15",
    "--principal", "Test Principal",
    "--principal-role", "Lead",
    "--seller", "Seller",
    "--broker", "Broker",
    "--thesis", "Test thesis",
    "--workstreams", "financial,legal",
]


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def initialized_deal(runner, tmp_path, monkeypatch):
    """Create a clean .diligence/ deal folder for config tests."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
    assert result.exit_code == 0, result.output
    return tmp_path


class TestConfigGet:
    def test_get_schema_version(self, runner, initialized_deal):
        result = runner.invoke(cli, ["config", "get", "schema_version"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "1" in result.output

    def test_get_deal_code(self, runner, initialized_deal):
        result = runner.invoke(cli, ["config", "get", "deal_code"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "TESTCO" in result.output

    def test_get_nonexistent_key_fails(self, runner, initialized_deal):
        result = runner.invoke(cli, ["config", "get", "nonexistent_key"], catch_exceptions=False)
        assert result.exit_code != 0


class TestConfigSet:
    def test_set_recent_window_days(self, runner, initialized_deal):
        result = runner.invoke(cli, ["config", "set", "recent_window_days", "14"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_get_after_set(self, runner, initialized_deal):
        runner.invoke(cli, ["config", "set", "recent_window_days", "14"], catch_exceptions=False)
        result = runner.invoke(cli, ["config", "get", "recent_window_days"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "14" in result.output

    def test_set_with_int_coercion(self, runner, initialized_deal):
        runner.invoke(cli, ["config", "set", "recent_window_days", "21"], catch_exceptions=False)
        config_path = initialized_deal / ".diligence" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["recent_window_days"] == 21
        assert isinstance(config["recent_window_days"], int)

    def test_set_with_float_coercion(self, runner, initialized_deal):
        runner.invoke(cli, ["config", "set", "anchor_tolerance_pct", "2.5"], catch_exceptions=False)
        config_path = initialized_deal / ".diligence" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["anchor_tolerance_pct"] == 2.5
        assert isinstance(config["anchor_tolerance_pct"], float)


class TestConfigJson:
    def test_get_json_output(self, runner, initialized_deal):
        result = runner.invoke(cli, ["config", "get", "schema_version", "--json"], catch_exceptions=False)
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "schema_version"
        assert data["value"] == 1

    def test_set_json_output(self, runner, initialized_deal):
        result = runner.invoke(
            cli, ["config", "set", "recent_window_days", "14", "--json"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "recent_window_days"
        assert data["value"] == 14
