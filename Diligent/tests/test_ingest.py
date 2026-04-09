"""Tests for diligent ingest command.

Tests: metadata capture, source ID generation (monotonic, zero-padded,
self-healing from SOURCES.md max), relative path storage, all metadata
flags, JSON output, error handling.
"""

import json
import os
from datetime import date
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def deal_dir(tmp_path, monkeypatch):
    """Create a deal folder with .diligence/ and minimal config, empty SOURCES.md."""
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

    # Empty SOURCES.md (just heading)
    (diligence / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def source_file(deal_dir):
    """Create a sample source file in the deal directory."""
    doc = deal_dir / "documents" / "cim.pdf"
    doc.parent.mkdir(parents=True, exist_ok=True)
    doc.write_text("fake pdf content", encoding="utf-8")
    return doc


class TestIngestCreatesEntry:
    def test_ingest_creates_source_entry_with_all_metadata(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
            "--date", "2026-04-07",
            "--parties", "Seller LLC,Broker Inc",
            "--workstream", "financial",
            "--notes", "Confidential memo",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert len(sf.sources) == 1
        entry = sf.sources[0]
        assert entry.date_received == "2026-04-07"
        assert entry.parties == ["Seller LLC", "Broker Inc"]
        assert entry.workstream_tags == ["financial"]
        assert entry.notes == "Confidential memo"


class TestSourceIdGeneration:
    def test_first_ingest_produces_deal_code_001(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert sf.sources[0].id == "ARRIVAL-001"

    def test_subsequent_ingests_produce_monotonic_ids(self, runner, deal_dir):
        # Create two files
        doc1 = deal_dir / "doc1.txt"
        doc1.write_text("content1", encoding="utf-8")
        doc2 = deal_dir / "doc2.txt"
        doc2.write_text("content2", encoding="utf-8")

        runner.invoke(cli, ["ingest", str(doc1)], catch_exceptions=False)
        runner.invoke(cli, ["ingest", str(doc2)], catch_exceptions=False)

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert len(sf.sources) == 2
        assert sf.sources[0].id == "ARRIVAL-001"
        assert sf.sources[1].id == "ARRIVAL-002"

    def test_source_id_derives_from_sources_md_max_not_counter(self, runner, deal_dir, source_file):
        """ID generation is self-healing: reads max from SOURCES.md, not a counter file."""
        from diligent.state.models import SourceEntry, SourcesFile
        from diligent.state.sources import read_sources, write_sources

        # Pre-populate with ARRIVAL-005 (simulating manual edits)
        sf = SourcesFile(sources=[
            SourceEntry(
                id="ARRIVAL-005",
                path="old/doc.pdf",
                date_received="2026-01-01",
            ),
        ])
        write_sources(deal_dir / ".diligence" / "SOURCES.md", sf)

        result = runner.invoke(cli, ["ingest", str(source_file)], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        sf2 = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        # Should be ARRIVAL-006, not ARRIVAL-002
        ids = [s.id for s in sf2.sources]
        assert "ARRIVAL-006" in ids


class TestRelativePaths:
    def test_path_stored_as_relative_to_deal_root(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, ["ingest", str(source_file)], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        stored_path = sf.sources[0].path
        # Should be relative, not absolute
        assert not Path(stored_path).is_absolute()
        # Should be relative to deal folder root (parent of .diligence/)
        assert stored_path == "documents/cim.pdf"


class TestDefaultDate:
    def test_date_defaults_to_today_when_omitted(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, ["ingest", str(source_file)], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert sf.sources[0].date_received == date.today().isoformat()


class TestPartiesFlag:
    def test_parties_accepts_comma_separated_string_stored_as_list(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
            "--parties", "Seller LLC, Broker Inc, Counsel",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert sf.sources[0].parties == ["Seller LLC", "Broker Inc", "Counsel"]


class TestWorkstreamFlag:
    def test_workstream_accepts_single_tag(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
            "--workstream", "financial",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert sf.sources[0].workstream_tags == ["financial"]


class TestSupersedesFlag:
    def test_supersedes_accepts_prior_source_id(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
            "--supersedes", "ARRIVAL-001",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert sf.sources[0].supersedes == "ARRIVAL-001"


class TestNotesFlag:
    def test_notes_accepts_free_text(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
            "--notes", "Q3 quarterly update, revised figures",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        from diligent.state.sources import read_sources
        sf = read_sources(deal_dir / ".diligence" / "SOURCES.md")
        assert sf.sources[0].notes == "Q3 quarterly update, revised figures"


class TestJsonOutput:
    def test_json_outputs_structured_result(self, runner, deal_dir, source_file):
        result = runner.invoke(cli, [
            "ingest", str(source_file),
            "--date", "2026-04-07",
            "--parties", "Seller",
            "--workstream", "financial",
            "--json",
        ], catch_exceptions=False)
        assert result.exit_code == 0, result.output

        data = json.loads(result.output)
        assert "source_id" in data
        assert data["source_id"] == "ARRIVAL-001"
        assert "path" in data
        assert "date_received" in data


class TestIngestErrors:
    def test_fails_if_file_does_not_exist(self, runner, deal_dir):
        result = runner.invoke(cli, [
            "ingest", "nonexistent_file.pdf",
        ], catch_exceptions=False)
        assert result.exit_code != 0

    def test_fails_if_diligence_dir_not_found(self, runner, tmp_path, monkeypatch):
        """Ingest fails if .diligence/ is not found in cwd."""
        # Use a directory without .diligence/
        bare_dir = tmp_path / "bare"
        bare_dir.mkdir()
        monkeypatch.chdir(bare_dir)

        # Create a file to ingest
        doc = bare_dir / "test.txt"
        doc.write_text("content", encoding="utf-8")

        result = runner.invoke(cli, ["ingest", str(doc)], catch_exceptions=False)
        assert result.exit_code != 0
        assert ".diligence" in result.output.lower() or "not found" in result.output.lower()
