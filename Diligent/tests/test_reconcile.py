"""Tests for reconcile CLI command.

Tests reconcile_cmd.py: output formatting, exit codes, --workstream filter,
--strict flag, --all flag, --verbose flag, --json output, and CLI registration.
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from diligent.state.models import (
    ArtifactEntry,
    ArtifactsFile,
    FactEntry,
    SourceEntry,
    SourcesFile,
    SupersededValue,
    TruthFile,
)
from diligent.state.artifacts import write_artifacts
from diligent.state.sources import write_sources
from diligent.state.truth import write_truth


@pytest.fixture
def deal_dir(tmp_path):
    """Create a minimal .diligence/ dir with TRUTH.md, SOURCES.md, ARTIFACTS.md."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()

    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )

    (diligence / "TRUTH.md").write_text("# Truth\n", encoding="utf-8")
    (diligence / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")
    (diligence / "ARTIFACTS.md").write_text("# Artifacts\n", encoding="utf-8")

    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


def _seed_current_state(deal_dir):
    """Seed a state where all artifacts are current."""
    truth = TruthFile(
        facts={
            "revenue": FactEntry(
                key="revenue",
                value="$1M",
                source="SRC-001",
                date="2026-03-10",
                workstream="financial",
            ),
        }
    )
    write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

    artifacts = ArtifactsFile(
        artifacts=[
            ArtifactEntry(
                path="deliverables/report.docx",
                workstream="financial",
                registered="2026-03-01",
                last_refreshed="2026-03-15",
                references=["revenue"],
            ),
        ]
    )
    write_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md", artifacts)

    sources = SourcesFile(sources=[
        SourceEntry(id="SRC-001", path="sources/doc.xlsx", date_received="2026-03-05"),
    ])
    write_sources(deal_dir / ".diligence" / "SOURCES.md", sources)


def _seed_stale_state(deal_dir):
    """Seed a state where one artifact is stale (value changed)."""
    truth = TruthFile(
        facts={
            "revenue": FactEntry(
                key="revenue",
                value="$2M",
                source="SRC-002",
                date="2026-03-25",
                workstream="financial",
                supersedes=[
                    SupersededValue(value="$1M", source="SRC-001", date="2026-03-10"),
                ],
            ),
            "margin": FactEntry(
                key="margin",
                value="45%",
                source="SRC-001",
                date="2026-03-10",
                workstream="financial",
            ),
        }
    )
    write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

    artifacts = ArtifactsFile(
        artifacts=[
            ArtifactEntry(
                path="deliverables/report.docx",
                workstream="financial",
                registered="2026-03-01",
                last_refreshed="2026-03-15",
                references=["revenue", "margin"],
            ),
            ArtifactEntry(
                path="deliverables/summary.docx",
                workstream="financial",
                registered="2026-03-01",
                last_refreshed="2026-03-30",
                references=["revenue", "margin"],
            ),
        ]
    )
    write_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md", artifacts)

    sources = SourcesFile(sources=[
        SourceEntry(id="SRC-001", path="sources/doc.xlsx", date_received="2026-03-05"),
        SourceEntry(id="SRC-002", path="sources/doc_v2.xlsx", date_received="2026-03-20"),
    ])
    write_sources(deal_dir / ".diligence" / "SOURCES.md", sources)


class TestReconcileAllCurrent:
    """Test 1: reconcile with no stale artifacts shows all current and exits 0."""

    def test_all_current_exits_zero(self, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        _seed_current_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "current" in result.output.lower()


class TestReconcileStaleOutput:
    """Test 2: reconcile with stale artifacts shows grouped output and exits 1."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_stale_exits_one(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "STALE" in result.output


class TestReconcileCompactOutput:
    """Test 3: reconcile output format has compact one-liner per fact."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_compact_one_liner(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # Should show key, old -> new, source ID, days stale
        assert "->" in result.output
        assert "stale)" in result.output
        assert "SRC-002" in result.output


class TestReconcileGroupedByArtifact:
    """Test 4: reconcile groups output by artifact with header showing path and status."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_artifact_header_with_status(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert "deliverables/report.docx" in result.output
        assert "[STALE]" in result.output


class TestReconcileSubSections:
    """Test 5: reconcile shows sub-sections for value changed and source superseded."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_value_changed_subsection(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert "Value changed:" in result.output


class TestReconcileWorkstreamFilter:
    """Test 6: reconcile --workstream filters to one workstream."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_workstream_filter(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        # Add a legal artifact that is current
        truth = TruthFile(
            facts={
                "revenue": FactEntry(
                    key="revenue",
                    value="$2M",
                    source="SRC-002",
                    date="2026-03-25",
                    workstream="financial",
                    supersedes=[
                        SupersededValue(
                            value="$1M", source="SRC-001", date="2026-03-10"
                        ),
                    ],
                ),
                "clause_count": FactEntry(
                    key="clause_count",
                    value="42",
                    source="SRC-003",
                    date="2026-03-10",
                    workstream="legal",
                ),
            }
        )
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

        artifacts = ArtifactsFile(
            artifacts=[
                ArtifactEntry(
                    path="deliverables/fin_report.docx",
                    workstream="financial",
                    registered="2026-03-01",
                    last_refreshed="2026-03-15",
                    references=["revenue"],
                ),
                ArtifactEntry(
                    path="deliverables/legal_memo.docx",
                    workstream="legal",
                    registered="2026-03-01",
                    last_refreshed="2026-03-15",
                    references=["clause_count"],
                ),
            ]
        )
        write_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md", artifacts)

        result = runner.invoke(
            reconcile_cmd,
            ["--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert "fin_report" in result.output
        assert "legal_memo" not in result.output


class TestReconcileStrict:
    """Test 7: reconcile --strict exits non-zero when flagged facts exist."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_strict_with_flagged(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        truth = TruthFile(
            facts={
                "revenue": FactEntry(
                    key="revenue",
                    value="$1M",
                    source="SRC-001",
                    date="2026-03-10",
                    workstream="financial",
                    flagged={"reason": "needs recomputation", "date": "2026-03-18"},
                ),
            }
        )
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

        artifacts = ArtifactsFile(
            artifacts=[
                ArtifactEntry(
                    path="deliverables/report.docx",
                    workstream="financial",
                    registered="2026-03-01",
                    last_refreshed="2026-03-15",
                    references=["revenue"],
                ),
            ]
        )
        write_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md", artifacts)

        # Without --strict: exit 0 (flagged is advisory only)
        result_normal = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result_normal.exit_code == 0

        # With --strict: exit 1 (flagged facts elevate to non-zero)
        result_strict = runner.invoke(
            reconcile_cmd,
            ["--strict"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result_strict.exit_code == 1


class TestReconcileAll:
    """Test 8: reconcile --all shows every artifact including CURRENT."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_all_shows_current(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)

        # Default: only stale/advisory
        result_default = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # summary.docx is current (refreshed 2026-03-30, after fact update 2026-03-25)
        assert "[CURRENT]" not in result_default.output

        # --all: shows everything including CURRENT
        result_all = runner.invoke(
            reconcile_cmd,
            ["--all"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert "[CURRENT]" in result_all.output
        assert "summary.docx" in result_all.output


class TestReconcileVerbose:
    """Test 9: reconcile --verbose shows two-line format with source details."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_verbose_shows_extra_detail(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            ["--verbose"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # Verbose output should include the source path
        assert "sources/" in result.output or "SRC-" in result.output


class TestReconcileSummaryLine:
    """Test 10: reconcile summary line at bottom."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_summary_line_present(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # Summary line: "X artifacts stale, Y facts changed, Z artifacts current"
        assert "stale" in result.output.lower()
        assert "current" in result.output.lower()
        assert "facts changed" in result.output.lower() or "fact" in result.output.lower()


class TestReconcileJson:
    """Test 11: reconcile --json outputs structured result."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_json_output(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        _seed_stale_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            ["--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        data = json.loads(result.output)
        assert "artifacts" in data
        assert "summary" in data


class TestReconcileExitZeroCurrent:
    """Test 12: reconcile exits 0 when all current and no --strict flags."""

    def test_exit_zero_when_current(self, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        _seed_current_state(deal_dir)
        result = runner.invoke(
            reconcile_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0


class TestReconcileCLIHelp:
    """Test 13: CLI help shows reconcile command."""

    def test_reconcile_in_cli_help(self, runner):
        from diligent.cli import cli

        result = runner.invoke(cli, ["reconcile", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "reconcile" in result.output.lower()
        assert "--workstream" in result.output
        assert "--strict" in result.output


class TestReconcileFlaggedShowsReason:
    """Test 14: reconcile flagged output displays actual reason, not the fact key."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_reconcile_flagged_shows_reason(self, mock_date, deal_dir, runner):
        from diligent.commands.reconcile_cmd import reconcile_cmd

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        truth = TruthFile(
            facts={
                "revenue": FactEntry(
                    key="revenue",
                    value="$1M",
                    source="SRC-001",
                    date="2026-03-10",
                    workstream="financial",
                    flagged={"reason": "Revenue figure disputed by seller", "date": "2026-03-18"},
                ),
            }
        )
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

        artifacts = ArtifactsFile(
            artifacts=[
                ArtifactEntry(
                    path="deliverables/report.docx",
                    workstream="financial",
                    registered="2026-03-01",
                    last_refreshed="2026-03-15",
                    references=["revenue"],
                ),
            ]
        )
        write_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md", artifacts)

        sources = SourcesFile(sources=[
            SourceEntry(id="SRC-001", path="sources/doc.xlsx", date_received="2026-03-05"),
        ])
        write_sources(deal_dir / ".diligence" / "SOURCES.md", sources)

        # Run reconcile with --strict to force flagged output
        result = runner.invoke(
            reconcile_cmd,
            ["--strict"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # The flagged reason should appear in output
        assert "Revenue figure disputed by seller" in result.output
        # The key should NOT be used as the reason text
        # (the old bug was: flagged: "revenue" instead of flagged: "Revenue figure disputed by seller")
        assert 'flagged: "revenue"' not in result.output
