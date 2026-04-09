"""Tests for diligent sources list and sources show commands.

Tests: empty list output, populated list output with aligned columns,
JSON list output, show full record, show unknown ID error, show JSON
output, sources group in CLI help, summary line.
"""

import json
from pathlib import Path

import click
import pytest
from click.testing import CliRunner

from diligent.cli import cli
from diligent.state.models import SourceEntry, SourcesFile
from diligent.state.sources import write_sources


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def deal_dir(tmp_path, monkeypatch):
    """Create a deal folder with .diligence/, config, and empty SOURCES.md."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()

    config = {
        "schema_version": 1,
        "deal_code": "ARRIVAL",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 1.0,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    (diligence / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def populated_deal_dir(deal_dir):
    """Deal dir with two sources already registered."""
    sf = SourcesFile(sources=[
        SourceEntry(
            id="ARRIVAL-001",
            path="documents/cim.pdf",
            date_received="2026-01-15",
            parties=["Seller LLC", "Broker Inc"],
            workstream_tags=["financial"],
            supersedes=None,
            notes="Confidential Information Memorandum",
        ),
        SourceEntry(
            id="ARRIVAL-002",
            path="documents/financials_2025.xlsx",
            date_received="2026-02-01",
            parties=["Seller LLC"],
            workstream_tags=["financial", "legal"],
            supersedes="ARRIVAL-001",
            notes=None,
        ),
    ])
    write_sources(deal_dir / ".diligence" / "SOURCES.md", sf)
    return deal_dir


class TestSourcesListEmpty:
    def test_no_sources_shows_message(self, runner, deal_dir):
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "no sources registered" in result.output.lower()

    def test_no_sources_shows_summary_line(self, runner, deal_dir):
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "0 sources registered" in result.output.lower()


class TestSourcesListPopulated:
    def test_shows_all_sources_one_line_each(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "ARRIVAL-001" in result.output
        assert "ARRIVAL-002" in result.output

    def test_shows_id_date_path_workstream(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "2026-01-15" in result.output
        assert "cim.pdf" in result.output
        assert "financial" in result.output

    def test_summary_line_at_bottom(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "2 sources registered" in result.output.lower()


class TestSourcesListJson:
    def test_json_outputs_array_of_source_objects(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "list", "--json"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["id"] == "ARRIVAL-001"
        assert data[1]["id"] == "ARRIVAL-002"


class TestSourcesShow:
    def test_shows_full_record_all_fields(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "show", "ARRIVAL-001"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "ARRIVAL-001" in result.output
        assert "documents/cim.pdf" in result.output
        assert "2026-01-15" in result.output
        assert "Seller LLC" in result.output
        assert "Broker Inc" in result.output
        assert "financial" in result.output
        assert "Confidential Information Memorandum" in result.output

    def test_shows_supersedes_field(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "show", "ARRIVAL-002"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "ARRIVAL-001" in result.output  # supersedes reference

    def test_unknown_id_prints_error_and_exits_1(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "show", "ARRIVAL-999"], catch_exceptions=False)
        assert result.exit_code != 0
        assert "not found" in result.output.lower()


class TestSourcesShowJson:
    def test_json_outputs_single_source_dict(self, runner, populated_deal_dir):
        result = runner.invoke(cli, ["sources", "show", "ARRIVAL-001", "--json"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, dict)
        assert data["id"] == "ARRIVAL-001"
        assert data["path"] == "documents/cim.pdf"
        assert data["parties"] == ["Seller LLC", "Broker Inc"]


class TestSourcesFindDiligenceDir:
    """Tests for _find_diligence_dir: subdirectory walk and DILIGENT_CWD support."""

    def test_sources_list_from_subdirectory(self, runner, populated_deal_dir, monkeypatch):
        """sources list finds .diligence/ when run from a subdirectory."""
        subdir = populated_deal_dir / "subdir" / "nested"
        subdir.mkdir(parents=True)
        monkeypatch.chdir(subdir)
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "ARRIVAL-001" in result.output

    def test_sources_list_with_diligent_cwd(self, runner, populated_deal_dir, monkeypatch, tmp_path):
        """sources list finds .diligence/ via DILIGENT_CWD env var."""
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        monkeypatch.chdir(other_dir)
        monkeypatch.setenv("DILIGENT_CWD", str(populated_deal_dir))
        result = runner.invoke(cli, ["sources", "list"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "ARRIVAL-001" in result.output

    def test_sources_show_with_diligent_cwd(self, runner, populated_deal_dir, monkeypatch, tmp_path):
        """sources show works with DILIGENT_CWD env var."""
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        monkeypatch.chdir(other_dir)
        monkeypatch.setenv("DILIGENT_CWD", str(populated_deal_dir))
        result = runner.invoke(cli, ["sources", "show", "ARRIVAL-001"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "ARRIVAL-001" in result.output

    def test_ingest_with_diligent_cwd(self, runner, deal_dir, monkeypatch, tmp_path):
        """ingest works with DILIGENT_CWD env var."""
        # Create a file to ingest in the deal dir
        doc = deal_dir / "test_doc.pdf"
        doc.write_text("dummy", encoding="utf-8")
        other_dir = tmp_path / "other"
        other_dir.mkdir()
        monkeypatch.chdir(other_dir)
        monkeypatch.setenv("DILIGENT_CWD", str(deal_dir))
        result = runner.invoke(cli, ["ingest", str(doc)], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "Registered" in result.output

    def test_missing_diligence_raises_click_exception(self, monkeypatch, tmp_path):
        """Missing .diligence/ raises click.ClickException, not SystemExit."""
        monkeypatch.chdir(tmp_path)
        from diligent.commands.sources_cmd import _find_diligence_dir
        with pytest.raises(click.ClickException):
            _find_diligence_dir()


class TestSourcesGroupInHelp:
    def test_sources_group_appears_in_cli_help(self, runner):
        result = runner.invoke(cli, ["--help"], catch_exceptions=False)
        assert result.exit_code == 0, result.output
        assert "sources" in result.output.lower()
