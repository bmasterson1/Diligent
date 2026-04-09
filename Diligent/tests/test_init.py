"""End-to-end tests for diligent init command.

Tests non-interactive mode primarily (avoids editor/prompt mocking).
Tests validation failures, idempotency guard, deal code validation,
and JSON output.
"""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.cli import cli


# -- Helpers --

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
    """CliRunner instance."""
    return CliRunner()


@pytest.fixture
def in_tmp_dir(tmp_path, monkeypatch):
    """Change working directory to tmp_path for the duration of the test."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


# -- Test: Non-interactive init creates .diligence/ with all 6 files --

class TestNonInteractiveInit:
    def test_creates_diligence_dir_with_8_files(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        d = in_tmp_dir / ".diligence"
        assert d.is_dir()
        expected_files = [
            "config.json",
            "DEAL.md",
            "TRUTH.md",
            "SOURCES.md",
            "WORKSTREAMS.md",
            "STATE.md",
            "QUESTIONS.md",
            "ARTIFACTS.md",
        ]
        for f in expected_files:
            assert (d / f).exists(), f"Missing {f}"
            assert (d / f).stat().st_size > 0, f"Empty {f}"

    def test_config_has_schema_version_and_deal_code(self, runner, in_tmp_dir):
        runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        config_path = in_tmp_dir / ".diligence" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        assert config["schema_version"] == 1
        assert config["deal_code"] == "ARRIVAL"

    def test_deal_md_has_correct_frontmatter(self, runner, in_tmp_dir):
        runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        deal_path = in_tmp_dir / ".diligence" / "DEAL.md"
        from diligent.state.deal import read_deal
        deal = read_deal(deal_path)
        assert deal.deal_code == "ARRIVAL"
        assert deal.target_legal_name == "Arrival Corp"
        assert deal.target_common_name == "Arrival"

    def test_deal_md_body_contains_thesis(self, runner, in_tmp_dir):
        runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        deal_path = in_tmp_dir / ".diligence" / "DEAL.md"
        from diligent.state.deal import read_deal
        deal = read_deal(deal_path)
        assert "Test thesis" in deal.thesis

    def test_workstreams_md_contains_selected(self, runner, in_tmp_dir):
        runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        ws_path = in_tmp_dir / ".diligence" / "WORKSTREAMS.md"
        from diligent.state.workstreams import read_workstreams
        ws = read_workstreams(ws_path)
        names = [w.name for w in ws.workstreams]
        assert "financial" in names
        assert "legal" in names

    def test_truth_md_parses_with_zero_facts(self, runner, in_tmp_dir):
        runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        truth_path = in_tmp_dir / ".diligence" / "TRUTH.md"
        from diligent.state.truth import read_truth
        truth = read_truth(truth_path)
        assert len(truth.facts) == 0

    def test_sources_md_parses_with_zero_sources(self, runner, in_tmp_dir):
        runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        sources_path = in_tmp_dir / ".diligence" / "SOURCES.md"
        from diligent.state.sources import read_sources
        sources = read_sources(sources_path)
        assert len(sources.sources) == 0

    def test_questions_md_exists_and_parseable(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        questions_path = in_tmp_dir / ".diligence" / "QUESTIONS.md"
        assert questions_path.exists()
        from diligent.state.questions import read_questions
        qf = read_questions(questions_path)
        assert len(qf.questions) == 0

    def test_init_reports_files_created(self, runner, in_tmp_dir):
        args = list(FULL_INIT_FLAGS) + ["--json"]
        result = runner.invoke(cli, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        # 8 state files + 2 workstream dirs x 2 files each = 12
        assert len(data["files_created"]) >= 8
        assert "QUESTIONS.md" in data["files_created"]
        assert "ARTIFACTS.md" in data["files_created"]
        # Workstream subdirectory files included
        assert "workstreams/financial/CONTEXT.md" in data["files_created"]
        assert "workstreams/legal/CONTEXT.md" in data["files_created"]

    def test_artifacts_md_parseable_after_init(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        artifacts_path = in_tmp_dir / ".diligence" / "ARTIFACTS.md"
        assert artifacts_path.exists()
        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(artifacts_path)
        assert len(af.artifacts) == 0


# -- Test: Init fails if .diligence/ already exists --

class TestIdempotencyGuard:
    def test_fails_if_diligence_exists(self, runner, in_tmp_dir):
        (in_tmp_dir / ".diligence").mkdir()
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code != 0
        assert ".diligence/" in result.output

    def test_error_message_is_clear(self, runner, in_tmp_dir):
        (in_tmp_dir / ".diligence").mkdir()
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert "already exists" in result.output.lower()


# -- Test: Non-interactive mode fails with missing required field --

class TestNonInteractiveValidation:
    def test_fails_without_code(self, runner, in_tmp_dir):
        args = [a for a in FULL_INIT_FLAGS if a not in ("--code", "ARRIVAL")]
        result = runner.invoke(cli, args, catch_exceptions=False)
        assert result.exit_code != 0
        assert "code" in result.output.lower()


# -- Test: Deal code validation --

class TestDealCodeValidation:
    @pytest.mark.parametrize("code,reason", [
        ("arrival", "lowercase"),
        ("AB", "too short"),
        ("ABCDEFGHIJKLM", "too long (13 chars)"),
        ("ARR1", "non-alpha"),
        ("ARR VAL", "contains space"),
    ])
    def test_rejects_invalid_deal_codes(self, runner, in_tmp_dir, code, reason):
        args = list(FULL_INIT_FLAGS)
        idx = args.index("--code")
        args[idx + 1] = code
        result = runner.invoke(cli, args, catch_exceptions=False)
        assert result.exit_code != 0, f"Should reject {reason}: {code}"

    def test_accepts_valid_deal_codes(self, runner, in_tmp_dir):
        args = list(FULL_INIT_FLAGS)
        idx = args.index("--code")
        args[idx + 1] = "ABC"
        result = runner.invoke(cli, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output


# -- Test: JSON output --

class TestInitWorkstreamDirs:
    """Test that init creates workstream subdirectories with templates."""

    def test_creates_workstream_subdirectories(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        ws_dir = in_tmp_dir / ".diligence" / "workstreams"
        assert ws_dir.is_dir()
        assert (ws_dir / "financial").is_dir()
        assert (ws_dir / "legal").is_dir()

    def test_financial_has_context_and_research(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        fin_dir = in_tmp_dir / ".diligence" / "workstreams" / "financial"
        assert (fin_dir / "CONTEXT.md").exists()
        assert (fin_dir / "RESEARCH.md").exists()

    def test_financial_context_is_tailored(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        ctx_path = in_tmp_dir / ".diligence" / "workstreams" / "financial" / "CONTEXT.md"
        content = ctx_path.read_text(encoding="utf-8")
        assert "Revenue Quality" in content
        assert "Cost Structure" in content

    def test_legal_context_is_tailored(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        ctx_path = in_tmp_dir / ".diligence" / "workstreams" / "legal" / "CONTEXT.md"
        content = ctx_path.read_text(encoding="utf-8")
        assert "Corporate Structure" in content
        assert "Contracts" in content

    def test_research_has_generic_template(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        research_path = in_tmp_dir / ".diligence" / "workstreams" / "financial" / "RESEARCH.md"
        content = research_path.read_text(encoding="utf-8")
        assert "Research" in content

    def test_workstreams_md_has_description_and_created(self, runner, in_tmp_dir):
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        from diligent.state.workstreams import read_workstreams
        ws = read_workstreams(in_tmp_dir / ".diligence" / "WORKSTREAMS.md")
        financial = [w for w in ws.workstreams if w.name == "financial"][0]
        assert financial.description != ""
        assert financial.created != ""

    def test_existing_init_tests_unaffected(self, runner, in_tmp_dir):
        """Sanity check that init still creates all 8 files."""
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        d = in_tmp_dir / ".diligence"
        for f in ["config.json", "DEAL.md", "TRUTH.md", "SOURCES.md",
                   "WORKSTREAMS.md", "STATE.md", "QUESTIONS.md", "ARTIFACTS.md"]:
            assert (d / f).exists(), f"Missing {f}"

    def test_subdirectory_failure_is_nonfatal(self, runner, in_tmp_dir, monkeypatch):
        """If subdirectory creation fails, state files should still be valid."""
        original_mkdir = Path.mkdir

        call_count = [0]

        def failing_mkdir(self, *args, **kwargs):
            # Let the initial .diligence mkdir work, plus workstreams dir,
            # but fail on the first workstream subdir
            call_count[0] += 1
            if "workstreams" in str(self) and self.name != "workstreams":
                raise PermissionError("Simulated failure")
            return original_mkdir(self, *args, **kwargs)

        monkeypatch.setattr(Path, "mkdir", failing_mkdir)
        result = runner.invoke(cli, FULL_INIT_FLAGS, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        # State files should still exist
        d = in_tmp_dir / ".diligence"
        assert (d / "config.json").exists()
        assert (d / "WORKSTREAMS.md").exists()


class TestJsonOutput:
    def test_init_json_output(self, runner, in_tmp_dir):
        args = list(FULL_INIT_FLAGS) + ["--json"]
        result = runner.invoke(cli, args, catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["deal_code"] == "ARRIVAL"
        assert "files_created" in data
