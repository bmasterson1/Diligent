"""Tests that all commands produce valid JSON when --json is used.

Verifies no non-JSON text in stdout when --json is used.
"""

import json
import os

import pytest
from click.testing import CliRunner

from diligent.cli import cli


FULL_INIT_FLAGS = [
    "init",
    "--non-interactive",
    "--code", "JSONTEST",
    "--target-legal", "JSON Test Corp",
    "--target-common", "JSONTest",
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
    monkeypatch.chdir(tmp_path)
    runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
    return tmp_path


class TestInitJsonOutput:
    def test_init_json_is_valid(self, runner, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(cli, FULL_INIT_FLAGS + ["--json"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, dict)


class TestDoctorJsonOutput:
    def test_doctor_json_is_valid(self, runner, initialized_deal):
        result = runner.invoke(cli, ["doctor", "--json"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestConfigJsonOutput:
    def test_config_get_json_is_valid(self, runner, initialized_deal):
        result = runner.invoke(
            cli, ["config", "get", "schema_version", "--json"],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, dict)


class TestHelpIncludesJsonFlag:
    def test_init_help_mentions_json(self, runner):
        result = runner.invoke(cli, ["init", "--help"], catch_exceptions=False)
        assert "--json" in result.output

    def test_doctor_help_mentions_json(self, runner):
        result = runner.invoke(cli, ["doctor", "--help"], catch_exceptions=False)
        assert "--json" in result.output

    def test_config_help_mentions_json(self, runner):
        # config get --help should mention --json
        result = runner.invoke(cli, ["config", "get", "--help"], catch_exceptions=False)
        assert "--json" in result.output
