"""Tests for diligent doctor command.

Creates .diligence/ via init (non-interactive), then tests doctor
on clean state, corrupted files, and cross-reference violations.
"""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.cli import cli


FULL_INIT_FLAGS = [
    "init",
    "--non-interactive",
    "--code", "ARRIVAL",
    "--target-legal", "Arrival Corp",
    "--target-common", "Arrival",
    "--stage", "loi",
    "--loi-date", "2026-01-15",
    "--principal", "Bryce M",
    "--principal-role", "Deal Lead",
    "--seller", "John Doe",
    "--broker", "Jane Smith",
    "--thesis", "Test thesis",
    "--workstreams", "financial,legal",
]


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def initialized_deal(runner, tmp_path, monkeypatch):
    """Create a clean .diligence/ deal folder for doctor tests."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
    assert result.exit_code == 0, result.output
    return tmp_path


class TestDoctorClean:
    def test_clean_deal_exits_zero(self, runner, initialized_deal):
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 0, result.output

    def test_clean_deal_zero_findings(self, runner, initialized_deal):
        result = runner.invoke(cli, ["doctor", "--json"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert len(data) == 0

    def test_summary_line_on_clean(self, runner, initialized_deal):
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert "0 errors, 0 warnings, 0 info" in result.output


class TestDoctorMissingFile:
    def test_missing_truth_md_reports_error(self, runner, initialized_deal):
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        truth_path.unlink()
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "TRUTH.md" in result.output
        assert "ERROR" in result.output

    def test_missing_file_suggests_fix(self, runner, initialized_deal):
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        truth_path.unlink()
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert "init" in result.output.lower()


class TestDoctorCorruptFile:
    def test_corrupt_truth_md_parse_error(self, runner, initialized_deal):
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        # Write a TRUTH.md with a fact that has invalid YAML in the fenced block
        truth_path.write_text(
            "# Truth\n\n## bad_fact\n```yaml\nvalue: [invalid yaml\n```\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "ERROR" in result.output

    def test_corrupt_config_json(self, runner, initialized_deal):
        config_path = initialized_deal / ".diligence" / "config.json"
        config_path.write_text("not json", encoding="utf-8")
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "ERROR" in result.output


class TestDoctorCrossRef:
    def test_mismatched_workstream_warns(self, runner, initialized_deal):
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        # Write a fact that references a non-existent workstream
        truth_path.write_text(
            '# Truth\n\n## test_fact\n```yaml\nvalue: "100"\nsource: ARRIVAL-001\n'
            'date: "2026-01-01"\nworkstream: nonexistent\nsupersedes: []\n```\n',
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert "WARNING" in result.output or "warning" in result.output.lower()


class TestDoctorJsonOutput:
    def test_json_returns_array(self, runner, initialized_deal):
        # Delete a file to generate findings
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        truth_path.unlink()
        result = runner.invoke(cli, ["doctor", "--json"], catch_exceptions=False)
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) > 0
        finding = data[0]
        assert "severity" in finding
        assert "file" in finding
        assert "description" in finding


class TestDoctorStrict:
    def test_strict_exits_nonzero_on_warning(self, runner, initialized_deal):
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        truth_path.write_text(
            '# Truth\n\n## test_fact\n```yaml\nvalue: "100"\nsource: ARRIVAL-001\n'
            'date: "2026-01-01"\nworkstream: nonexistent\nsupersedes: []\n```\n',
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor", "--strict"], catch_exceptions=False)
        assert result.exit_code != 0


class TestDoctorQuestionsFile:
    """Tests for QUESTIONS.md in doctor checks."""

    def test_missing_questions_md_reports_error(self, runner, initialized_deal):
        """doctor reports missing QUESTIONS.md as ERROR."""
        questions_path = initialized_deal / ".diligence" / "QUESTIONS.md"
        questions_path.unlink()
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "QUESTIONS.md" in result.output
        assert "ERROR" in result.output

    def test_questions_md_parses_without_error(self, runner, initialized_deal):
        """doctor parses QUESTIONS.md without error on clean deal."""
        result = runner.invoke(cli, ["doctor", "--json"], catch_exceptions=False)
        assert result.exit_code == 0
        data = json.loads(result.output)
        # No errors related to QUESTIONS.md
        questions_findings = [f for f in data if "QUESTIONS.md" in f.get("file", "")]
        assert len(questions_findings) == 0

    def test_corrupt_questions_md_fenced_yaml(self, runner, initialized_deal):
        """doctor catches corrupt fenced YAML in QUESTIONS.md."""
        questions_path = initialized_deal / ".diligence" / "QUESTIONS.md"
        questions_path.write_text(
            "# Questions\n\n## Q-BAD\n```yaml\nquestion: [broken yaml\n```\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "ERROR" in result.output

    def test_questions_md_with_valid_entry_passes(self, runner, initialized_deal):
        """doctor validates a well-formed QUESTIONS.md without error."""
        questions_path = initialized_deal / ".diligence" / "QUESTIONS.md"
        questions_path.write_text(
            '# Questions\n\n## Q-001\n```yaml\nquestion: "Test?"\n'
            'workstream: financial\nowner: self\nstatus: open\n'
            'date_raised: "2026-04-07"\n```\n',
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor", "--json"], catch_exceptions=False)
        assert result.exit_code == 0


class TestDoctorArtifactsFile:
    """Tests for ARTIFACTS.md in doctor checks."""

    def test_missing_artifacts_md_reports_error(self, runner, initialized_deal):
        """doctor reports missing ARTIFACTS.md as ERROR."""
        artifacts_path = initialized_deal / ".diligence" / "ARTIFACTS.md"
        artifacts_path.unlink()
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "ARTIFACTS.md" in result.output
        assert "ERROR" in result.output

    def test_corrupt_artifacts_md_fenced_yaml(self, runner, initialized_deal):
        """doctor catches corrupt fenced YAML in ARTIFACTS.md."""
        artifacts_path = initialized_deal / ".diligence" / "ARTIFACTS.md"
        artifacts_path.write_text(
            "# Artifacts\n\n## bad/path.docx\n```yaml\nworkstream: [broken yaml\n```\n",
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "ERROR" in result.output

    def test_valid_artifacts_md_passes(self, runner, initialized_deal):
        """doctor validates a well-formed ARTIFACTS.md without error."""
        # Create a valid artifact entry
        artifacts_path = initialized_deal / ".diligence" / "ARTIFACTS.md"
        # Add a truth fact first so the reference is valid
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        truth_path.write_text(
            '# Truth\n\n## test_key\n```yaml\nvalue: "100"\nsource: ARRIVAL-001\n'
            'date: "2026-01-01"\nworkstream: financial\nsupersedes: []\n```\n',
            encoding="utf-8",
        )
        # Create the artifact file with a valid path on disk
        artifact_dir = initialized_deal / "deliverables"
        artifact_dir.mkdir()
        (artifact_dir / "test.docx").write_text("dummy", encoding="utf-8")
        artifacts_path.write_text(
            '# Artifacts\n\n## deliverables/test.docx\n```yaml\n'
            'workstream: "financial"\nregistered: "2026-04-01"\n'
            'last_refreshed: "2026-04-01"\nreferences:\n  - "test_key"\n'
            'scanner_findings: []\nnotes: ""\n```\n',
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor", "--json"], catch_exceptions=False)
        assert result.exit_code == 0

    def test_artifact_references_missing_truth_key_warns(self, runner, initialized_deal):
        """doctor warns when artifact references a truth key not in TRUTH.md."""
        artifacts_path = initialized_deal / ".diligence" / "ARTIFACTS.md"
        # Create artifact file with a path that exists
        artifact_dir = initialized_deal / "deliverables"
        artifact_dir.mkdir()
        (artifact_dir / "test.docx").write_text("dummy", encoding="utf-8")
        artifacts_path.write_text(
            '# Artifacts\n\n## deliverables/test.docx\n```yaml\n'
            'workstream: "financial"\nregistered: "2026-04-01"\n'
            'last_refreshed: "2026-04-01"\nreferences:\n  - "nonexistent_key"\n'
            'scanner_findings: []\nnotes: ""\n```\n',
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert "WARNING" in result.output or "warning" in result.output.lower()
        assert "nonexistent_key" in result.output

    def test_artifact_path_not_on_disk_warns(self, runner, initialized_deal):
        """doctor warns when artifact path does not exist on disk."""
        artifacts_path = initialized_deal / ".diligence" / "ARTIFACTS.md"
        artifacts_path.write_text(
            '# Artifacts\n\n## missing/file.docx\n```yaml\n'
            'workstream: "financial"\nregistered: "2026-04-01"\n'
            'last_refreshed: "2026-04-01"\nreferences: []\n'
            'scanner_findings: []\nnotes: ""\n```\n',
            encoding="utf-8",
        )
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        assert "WARNING" in result.output or "warning" in result.output.lower()
        assert "missing/file.docx" in result.output


class TestDoctorSummaryLine:
    def test_summary_format(self, runner, initialized_deal):
        truth_path = initialized_deal / ".diligence" / "TRUTH.md"
        truth_path.unlink()
        result = runner.invoke(cli, ["doctor"], catch_exceptions=False)
        # Should contain "N errors, N warnings, N info"
        assert "error" in result.output.lower()
        assert "warning" in result.output.lower()
        assert "info" in result.output.lower()
