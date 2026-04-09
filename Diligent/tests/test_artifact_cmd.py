"""Tests for artifact register, list, and refresh CLI commands.

Tests artifact_cmd.py: register (create, upsert gate, truth key validation,
path normalization, JSON output), list (staleness status, filters, summary),
and refresh (timestamp update, unknown path).
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from diligent.commands.artifact_cmd import artifact_cmd


@pytest.fixture
def deal_dir(tmp_path):
    """Create a minimal .diligence/ dir with config.json, TRUTH.md, SOURCES.md, ARTIFACTS.md."""
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
    (diligence / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    truth_content = "# Truth\n"
    (diligence / "TRUTH.md").write_text(truth_content, encoding="utf-8")

    sources_content = "# Sources\n"
    (diligence / "SOURCES.md").write_text(sources_content, encoding="utf-8")

    artifacts_content = "# Artifacts\n"
    (diligence / "ARTIFACTS.md").write_text(artifacts_content, encoding="utf-8")

    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


def _seed_truth(deal_dir, facts):
    """Seed TRUTH.md with facts. facts is a dict of key -> {value, source, date, workstream}."""
    from diligent.state.models import FactEntry, TruthFile
    from diligent.state.truth import write_truth

    entries = {}
    for key, data in facts.items():
        entries[key] = FactEntry(
            key=key,
            value=data.get("value", ""),
            source=data.get("source", "TEST-001"),
            date=data.get("date", "2026-03-01"),
            workstream=data.get("workstream", "financial"),
        )
    truth = TruthFile(facts=entries)
    write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)


def _seed_artifacts(deal_dir, artifacts):
    """Seed ARTIFACTS.md with artifact entries.

    artifacts is a list of dicts with keys: path, workstream, registered,
    last_refreshed, references, scanner_findings, notes.
    """
    from diligent.state.models import ArtifactEntry, ArtifactsFile
    from diligent.state.artifacts import write_artifacts

    entries = []
    for a in artifacts:
        entries.append(ArtifactEntry(
            path=a.get("path", ""),
            workstream=a.get("workstream", ""),
            registered=a.get("registered", "2026-03-01"),
            last_refreshed=a.get("last_refreshed", "2026-03-01"),
            references=a.get("references", []),
            scanner_findings=a.get("scanner_findings", []),
            notes=a.get("notes", ""),
        ))
    write_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md", ArtifactsFile(artifacts=entries))


class TestArtifactRegister:
    """artifact register creates new artifact entries in ARTIFACTS.md."""

    def test_register_creates_new_artifact(self, deal_dir, runner):
        """register creates artifact entry with path, workstream, references, today's dates."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "deliverables/report.docx", "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert len(af.artifacts) == 1
        assert af.artifacts[0].path == "deliverables/report.docx"
        assert af.artifacts[0].references == ["revenue"]
        assert af.artifacts[0].registered == date.today().isoformat()
        assert af.artifacts[0].last_refreshed == date.today().isoformat()

    def test_register_normalizes_path_to_posix(self, deal_dir, runner):
        """register normalizes backslashes to forward slashes."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "deliverables\\subdir\\report.docx", "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].path == "deliverables/subdir/report.docx"

    def test_register_comma_separated_references(self, deal_dir, runner):
        """register with --references key1,key2,key3 stores as list."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M"},
            "margin": {"value": "42%"},
            "growth": {"value": "15%"},
        })

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue,margin,growth"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].references == ["revenue", "margin", "growth"]

    def test_register_warns_on_missing_truth_keys(self, deal_dir, runner):
        """register warns on truth keys not found in TRUTH.md but succeeds."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue,nonexistent_key"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "WARNING" in result.output
        assert "nonexistent_key" in result.output

        # Still creates the artifact
        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert len(af.artifacts) == 1
        assert "nonexistent_key" in af.artifacts[0].references

    def test_reregister_without_confirm_shows_refs_exits_1(self, deal_dir, runner):
        """Re-registering existing artifact without --confirm shows current refs and exits 1."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "revenue" in result.output
        assert "--confirm" in result.output

    def test_reregister_with_confirm_upserts(self, deal_dir, runner):
        """Re-registering with --confirm updates references and last_refreshed."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M"},
            "margin": {"value": "42%"},
        })
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "workstream": "financial",
            "registered": "2026-03-01",
            "last_refreshed": "2026-03-01",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue,margin",
             "--confirm", "--workstream", "legal"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].references == ["revenue", "margin"]
        assert af.artifacts[0].workstream == "legal"
        assert af.artifacts[0].last_refreshed == date.today().isoformat()
        # registered date should NOT change on upsert
        assert af.artifacts[0].registered == "2026-03-01"

    def test_register_with_workstream(self, deal_dir, runner):
        """register with --workstream sets workstream field."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue",
             "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].workstream == "financial"

    def test_register_with_notes(self, deal_dir, runner):
        """register with --notes sets notes field."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue",
             "--notes", "Draft version"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].notes == "Draft version"

    def test_register_json_output(self, deal_dir, runner):
        """register --json outputs structured result."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "created"
        assert data["path"] == "report.docx"

    def test_register_fails_without_diligence_dir(self, tmp_path, runner):
        """register exits 1 if .diligence/ not found."""
        result = runner.invoke(
            artifact_cmd,
            ["register", "report.docx", "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(tmp_path)},
        )
        assert result.exit_code != 0


def _seed_sources(deal_dir, sources):
    """Seed SOURCES.md with source entries.

    sources is a list of dicts with keys: id, path, date_received, supersedes.
    """
    from diligent.state.models import SourceEntry, SourcesFile
    from diligent.state.sources import write_sources

    entries = []
    for s in sources:
        entries.append(SourceEntry(
            id=s.get("id", ""),
            path=s.get("path", ""),
            date_received=s.get("date_received", "2026-03-01"),
            supersedes=s.get("supersedes"),
        ))
    write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=entries))


def _seed_truth_with_flags(deal_dir, facts):
    """Seed TRUTH.md with facts including flagged field support.

    facts is a dict of key -> {value, source, date, workstream, flagged}.
    """
    from diligent.state.models import FactEntry, TruthFile
    from diligent.state.truth import write_truth

    entries = {}
    for key, data in facts.items():
        entries[key] = FactEntry(
            key=key,
            value=data.get("value", ""),
            source=data.get("source", "TEST-001"),
            date=data.get("date", "2026-03-01"),
            workstream=data.get("workstream", "financial"),
            flagged=data.get("flagged"),
        )
    truth = TruthFile(facts=entries)
    write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)


class TestArtifactList:
    """artifact list shows all artifacts with staleness status."""

    def test_list_shows_all_artifacts_with_status(self, deal_dir, runner):
        """list shows all artifacts with CURRENT/STALE/ADVISORY status."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M", "date": "2026-03-01"},
        })
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-15",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "report.docx" in result.output
        assert "CURRENT" in result.output

    def test_list_stale_filter(self, deal_dir, runner):
        """list --stale shows only stale and advisory artifacts."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M", "date": "2026-03-20"},
            "margin": {"value": "42%", "date": "2026-03-01"},
        })
        _seed_artifacts(deal_dir, [
            {
                "path": "stale_report.docx",
                "references": ["revenue"],
                "last_refreshed": "2026-03-10",
                "workstream": "financial",
            },
            {
                "path": "current_report.docx",
                "references": ["margin"],
                "last_refreshed": "2026-03-15",
                "workstream": "financial",
            },
        ])

        result = runner.invoke(
            artifact_cmd,
            ["list", "--stale"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "stale_report.docx" in result.output
        assert "current_report.docx" not in result.output

    def test_list_no_artifacts(self, deal_dir, runner):
        """list with no artifacts shows 'No artifacts registered.'"""
        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "No artifacts registered." in result.output

    def test_list_json_output(self, deal_dir, runner):
        """list --json outputs structured list."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M", "date": "2026-03-01"},
        })
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-15",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["list", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["path"] == "report.docx"
        assert data[0]["status"] == "CURRENT"

    def test_list_detects_value_changed_staleness(self, deal_dir, runner):
        """list detects staleness when fact date is after artifact last_refreshed."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M", "date": "2026-03-20"},
        })
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-10",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "STALE" in result.output

    def test_list_detects_source_superseded_staleness(self, deal_dir, runner):
        """list detects staleness when source was superseded after artifact last_refreshed."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M", "source": "SRC-001", "date": "2026-03-01"},
        })
        _seed_sources(deal_dir, [
            {"id": "SRC-001", "path": "old.xlsx", "date_received": "2026-03-01"},
            {"id": "SRC-002", "path": "new.xlsx", "date_received": "2026-03-20",
             "supersedes": "SRC-001"},
        ])
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-10",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "STALE" in result.output

    def test_list_shows_flagged_as_advisory(self, deal_dir, runner):
        """list shows flagged facts as ADVISORY, not STALE."""
        _seed_truth_with_flags(deal_dir, {
            "revenue": {
                "value": "$1M",
                "date": "2026-03-01",
                "flagged": {"reason": "under review", "date": "2026-03-05"},
            },
        })
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-15",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "ADVISORY" in result.output

    def test_list_summary_line_shows_counts(self, deal_dir, runner):
        """list summary line shows counts of stale, advisory, current."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M", "date": "2026-03-20"},
            "margin": {"value": "42%", "date": "2026-03-01"},
        })
        _seed_artifacts(deal_dir, [
            {
                "path": "stale.docx",
                "references": ["revenue"],
                "last_refreshed": "2026-03-10",
            },
            {
                "path": "current.docx",
                "references": ["margin"],
                "last_refreshed": "2026-03-15",
            },
        ])

        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "1 stale" in result.output
        assert "1 current" in result.output


class TestArtifactRefresh:
    """artifact refresh updates last_refreshed timestamp."""

    def test_refresh_updates_last_refreshed(self, deal_dir, runner):
        """refresh updates last_refreshed to today for existing artifact."""
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-01",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["refresh", "report.docx"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].last_refreshed == date.today().isoformat()

    def test_refresh_unknown_path_exits_1(self, deal_dir, runner):
        """refresh exits 1 for unknown artifact path."""
        result = runner.invoke(
            artifact_cmd,
            ["refresh", "nonexistent.docx"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1

    def test_refresh_json_output(self, deal_dir, runner):
        """refresh --json outputs structured result."""
        _seed_artifacts(deal_dir, [{
            "path": "report.docx",
            "references": ["revenue"],
            "last_refreshed": "2026-03-01",
            "workstream": "financial",
        }])

        result = runner.invoke(
            artifact_cmd,
            ["refresh", "report.docx", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "refreshed"
        assert data["path"] == "report.docx"


def _create_docx(path, paragraphs):
    """Create a .docx file with given paragraph texts."""
    from docx import Document

    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))


class TestArtifactRegisterScanner:
    """artifact register scanner integration for .docx files."""

    def test_docx_register_runs_scanner_automatically(self, deal_dir, runner):
        """register on .docx file runs scanner automatically (no --scan flag needed)."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}, "margin": {"value": "42%"}})

        # Create a .docx with citation tags
        docx_path = deal_dir / "deliverables" / "report.docx"
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        _create_docx(docx_path, ["Revenue is {{truth:revenue}} and margin {{truth:margin}}."])

        result = runner.invoke(
            artifact_cmd,
            ["register", str(docx_path), "--references", "revenue,margin"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert len(af.artifacts) == 1
        # Scanner findings stored separately
        assert af.artifacts[0].scanner_findings == ["margin", "revenue"]

    def test_docx_references_authoritative_scanner_advisory(self, deal_dir, runner):
        """With --references: references from flag are authoritative, scanner findings stored separately."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M"},
            "margin": {"value": "42%"},
            "growth": {"value": "15%"},
        })

        # Docx has revenue and margin tags, but --references only lists revenue
        docx_path = deal_dir / "deliverables" / "report.docx"
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        _create_docx(docx_path, [
            "Revenue is {{truth:revenue}} and margin {{truth:margin}} and growth {{truth:growth}}.",
        ])

        result = runner.invoke(
            artifact_cmd,
            ["register", str(docx_path), "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].references == ["revenue"]
        assert af.artifacts[0].scanner_findings == ["growth", "margin", "revenue"]

    def test_docx_scanner_advisory_for_undiscovered_keys(self, deal_dir, runner):
        """Scanner prints advisory when it finds keys not in --references."""
        _seed_truth(deal_dir, {
            "revenue": {"value": "$1M"},
            "margin": {"value": "42%"},
        })

        docx_path = deal_dir / "deliverables" / "report.docx"
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        _create_docx(docx_path, [
            "Revenue {{truth:revenue}} and margin {{truth:margin}}.",
        ])

        result = runner.invoke(
            artifact_cmd,
            ["register", str(docx_path), "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "Scanner also found" in result.output
        assert "margin" in result.output

    def test_docx_no_references_scanner_finds_keys_exits_1(self, deal_dir, runner):
        """register .docx without --references: scanner runs, prints keys, exits 1."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        docx_path = deal_dir / "deliverables" / "report.docx"
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        _create_docx(docx_path, ["Revenue is {{truth:revenue}}."])

        result = runner.invoke(
            artifact_cmd,
            ["register", str(docx_path)],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "revenue" in result.output
        assert "--references" in result.output

    def test_docx_no_references_no_scanner_findings_exits_1(self, deal_dir, runner):
        """register .docx without --references and no tags: exits 1 asking for --references."""
        docx_path = deal_dir / "deliverables" / "report.docx"
        docx_path.parent.mkdir(parents=True, exist_ok=True)
        _create_docx(docx_path, ["No citation tags here."])

        result = runner.invoke(
            artifact_cmd,
            ["register", str(docx_path)],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "--references" in result.output

    def test_non_docx_scanner_does_not_run(self, deal_dir, runner):
        """register on non-.docx file: scanner does not run."""
        _seed_truth(deal_dir, {"revenue": {"value": "$1M"}})

        result = runner.invoke(
            artifact_cmd,
            ["register", "report.pdf", "--references", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(deal_dir / ".diligence" / "ARTIFACTS.md")
        assert af.artifacts[0].scanner_findings == []

    def test_non_docx_without_references_errors(self, deal_dir, runner):
        """register non-.docx without --references: error."""
        result = runner.invoke(
            artifact_cmd,
            ["register", "report.pdf"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0


class TestArtifactCLI:
    """artifact command group registered in CLI LazyGroup."""

    def test_cli_help_shows_artifact_commands(self, runner):
        """CLI help shows artifact command group with register, list, refresh."""
        from diligent.cli import cli

        result = runner.invoke(cli, ["artifact", "--help"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "register" in result.output
        assert "list" in result.output
        assert "refresh" in result.output
