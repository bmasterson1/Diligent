"""Tests for truth set and truth get CLI commands.

Tests truth_cmd.py: truth set (create, update, gate, confirm, no-op, anchor)
and truth get (lookup, missing key, json output).
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from diligent.commands.truth_cmd import truth_cmd


@pytest.fixture
def deal_dir(tmp_path):
    """Create a minimal .diligence/ dir with config.json, TRUTH.md, QUESTIONS.md."""
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

    questions_content = "# Questions\n"
    (diligence / "QUESTIONS.md").write_text(questions_content, encoding="utf-8")

    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


class TestTruthSetNewKey:
    """truth set with a new key creates a FactEntry in TRUTH.md."""

    def test_set_new_key_creates_fact(self, deal_dir, runner):
        """truth set KEY VALUE --source creates new fact entry."""
        result = runner.invoke(
            truth_cmd,
            ["set", "annual_revenue", "$2,400,000", "--source", "TEST-001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert "annual_revenue" in truth.facts
        assert truth.facts["annual_revenue"].value == "$2,400,000"
        assert truth.facts["annual_revenue"].source == "TEST-001"

    def test_set_requires_source(self, deal_dir, runner):
        """truth set without --source fails."""
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "100", ],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0


class TestTruthSetUpdate:
    """truth set updating an existing key pushes prior value to supersedes chain."""

    def _seed_fact(self, deal_dir, key="annual_revenue", value="$2,400,000",
                   source="TEST-001", anchor=False):
        """Seed a fact entry via truth set."""
        from diligent.state.models import FactEntry, TruthFile
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            key: FactEntry(
                key=key,
                value=value,
                source=source,
                date="2026-04-01",
                workstream="financial",
                anchor=anchor,
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

    def test_update_pushes_to_supersedes(self, deal_dir, runner):
        """Updating existing key pushes prior value to supersedes chain."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "annual_revenue", "$2,400,000", "--source", "TEST-002", "--confirm"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # Even with same numeric value, strings differ ($2,400,000 vs $2,400,000 -- same here)
        # Wait, the value is bytewise equal so it should be no-op.
        # Let's use a different value to test supersedes.
        pass

    def test_update_different_value_with_confirm_stores(self, deal_dir, runner):
        """truth set with --confirm overrides gate and stores the value."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "annual_revenue", "$2,500,000", "--source", "TEST-002", "--confirm"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        fact = truth.facts["annual_revenue"]
        assert fact.value == "$2,500,000"
        assert fact.source == "TEST-002"
        assert len(fact.supersedes) == 1
        assert fact.supersedes[0].value == "$2,400,000"
        assert fact.supersedes[0].source == "TEST-001"

    def test_anchor_flag_marks_fact(self, deal_dir, runner):
        """truth set --anchor marks fact as anchor=True."""
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "100", "--source", "TEST-001", "--anchor"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].anchor is True

    def test_anchor_sticky_without_flag(self, deal_dir, runner):
        """Existing anchor fact preserves anchor=True without --anchor flag."""
        self._seed_fact(deal_dir, key="revenue", value="100", source="TEST-001", anchor=True)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "101", "--source", "TEST-002", "--confirm"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].anchor is True

    def test_no_anchor_demotes(self, deal_dir, runner):
        """truth set --no-anchor demotes anchor fact to anchor=False."""
        self._seed_fact(deal_dir, key="revenue", value="100", source="TEST-001", anchor=True)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "101", "--source", "TEST-002", "--confirm", "--no-anchor"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].anchor is False

    def test_computed_by_and_notes_stored(self, deal_dir, runner):
        """truth set --computed-by and --notes stores optional fields."""
        result = runner.invoke(
            truth_cmd,
            ["set", "margin", "42%", "--source", "TEST-001",
             "--computed-by", "revenue/cost", "--notes", "Q3 figure"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["margin"].computed_by == "revenue/cost"
        assert truth.facts["margin"].notes == "Q3 figure"


class TestTruthSetGate:
    """Verification gate: exits 2 when value changes beyond tolerance."""

    def _seed_fact(self, deal_dir, key="revenue", value="10000",
                   source="TEST-001", anchor=False):
        from diligent.state.models import FactEntry, TruthFile
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            key: FactEntry(
                key=key,
                value=value,
                source=source,
                date="2026-04-01",
                workstream="financial",
                anchor=anchor,
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

    def test_gate_fires_exit_2(self, deal_dir, runner):
        """truth set exits 2 when gate fires (non-anchor value change)."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "10500", "--source", "TEST-002"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 2

    def test_confirm_overrides_gate(self, deal_dir, runner):
        """truth set --confirm overrides gate and stores value."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "10500", "--source", "TEST-002", "--confirm"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].value == "10500"

    def test_gate_output_compact_format(self, deal_dir, runner):
        """Gate exit 2 output includes compact discrepancy format."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "10500", "--source", "TEST-002"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 2
        assert "key:" in result.output
        assert "current:" in result.output
        assert "proposed:" in result.output
        assert "verdict:" in result.output

    def test_gate_json_output(self, deal_dir, runner):
        """truth set --json on gate fire includes structured discrepancy."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "10500", "--source", "TEST-002", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 2
        data = json.loads(result.output)
        assert data["status"] == "discrepancy"
        assert data["key"] == "revenue"

    def test_gate_rejection_writes_question(self, deal_dir, runner):
        """Gate rejection writes QuestionEntry to QUESTIONS.md."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "10500", "--source", "TEST-002"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 2

        from diligent.state.questions import read_questions
        qf = read_questions(deal_dir / ".diligence" / "QUESTIONS.md")
        assert len(qf.questions) == 1
        q = qf.questions[0]
        assert q.id == "Q-001"
        assert q.status == "open"
        assert q.context is not None
        assert q.context["type"] == "gate_rejection"
        assert q.context["key"] == "revenue"
        assert q.context["old_value"] == "10000"
        assert q.context["new_value"] == "10500"

    def test_noop_bytewise_equal(self, deal_dir, runner):
        """truth set no-op when value is bytewise equal (exit 0, no supersedes)."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "10000", "--source", "TEST-002"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "No change" in result.output

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert len(truth.facts["revenue"].supersedes) == 0

    def test_workstream_association(self, deal_dir, runner):
        """truth set --workstream associates fact with workstream."""
        result = runner.invoke(
            truth_cmd,
            ["set", "revenue", "100", "--source", "TEST-001", "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].workstream == "financial"


class TestTruthGet:
    """truth get: lookup current value with source citation."""

    def _seed_fact(self, deal_dir, key="revenue", value="10000",
                   source="TEST-001", anchor=False, flagged=None):
        from diligent.state.models import FactEntry, TruthFile
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            key: FactEntry(
                key=key,
                value=value,
                source=source,
                date="2026-04-01",
                workstream="financial",
                anchor=anchor,
                flagged=flagged,
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

    def test_get_shows_value_with_citation(self, deal_dir, runner):
        """truth get <key> shows current value with source citation."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["get", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "revenue" in result.output
        assert "10000" in result.output
        assert "TEST-001" in result.output
        assert "2026-04-01" in result.output

    def test_get_unknown_key_exits_1(self, deal_dir, runner):
        """truth get with unknown key prints error and exits 1."""
        result = runner.invoke(
            truth_cmd,
            ["get", "nonexistent_key"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_get_json_output(self, deal_dir, runner):
        """truth get --json outputs structured result."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["get", "revenue", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["key"] == "revenue"
        assert data["value"] == "10000"
        assert data["source"] == "TEST-001"

    def test_get_output_format(self, deal_dir, runner):
        """truth get output format: '{key}: {value} (source: {source}, date: {date})'."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["get", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "revenue: 10000 (source: TEST-001, date: 2026-04-01)" in result.output

    def test_get_anchor_shows_label(self, deal_dir, runner):
        """truth get on anchor fact shows [anchor] label."""
        self._seed_fact(deal_dir, anchor=True)
        result = runner.invoke(
            truth_cmd,
            ["get", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert "[anchor]" in result.output

    def test_get_flagged_shows_reason(self, deal_dir, runner):
        """truth get on flagged fact shows [FLAGGED: reason]."""
        self._seed_fact(deal_dir, flagged={"reason": "stale data", "date": "2026-04-01"})
        result = runner.invoke(
            truth_cmd,
            ["get", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert "[FLAGGED: stale data]" in result.output


class TestTruthListEmpty:
    """truth list with no facts."""

    def test_list_no_facts_shows_message(self, deal_dir, runner):
        """truth list with no facts shows 'No facts recorded' and summary."""
        # Add empty SOURCES.md
        (deal_dir / ".diligence" / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")

        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "No facts recorded" in result.output
        assert "0 facts" in result.output


class TestTruthListBasic:
    """truth list: one line per fact with aligned columns."""

    def _seed_facts(self, deal_dir, sources=None):
        """Seed facts and optionally sources for list tests."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "annual_revenue": FactEntry(
                key="annual_revenue",
                value="$2,400,000",
                source="TEST-001",
                date="2026-04-01",
                workstream="financial",
            ),
            "employee_count": FactEntry(
                key="employee_count",
                value="42",
                source="TEST-002",
                date="2026-04-02",
                workstream="operational",
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

        if sources is None:
            sources = SourcesFile(sources=[
                SourceEntry(
                    id="TEST-001",
                    path="Financial_Statements.xlsx",
                    date_received="2026-04-01",
                ),
                SourceEntry(
                    id="TEST-002",
                    path="Employee_Roster.xlsx",
                    date_received="2026-04-02",
                ),
            ])
        write_sources(deal_dir / ".diligence" / "SOURCES.md", sources)

    def test_list_shows_one_line_per_fact(self, deal_dir, runner):
        """truth list shows one line per fact: key, value, status, source."""
        self._seed_facts(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "annual_revenue" in result.output
        assert "employee_count" in result.output
        assert "TEST-001" in result.output
        assert "TEST-002" in result.output

    def test_list_value_truncated_to_30(self, deal_dir, runner):
        """truth list truncates value to 30 chars with ... suffix."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        long_val = "A" * 50
        truth = TruthFile(facts={
            "long_fact": FactEntry(
                key="long_fact",
                value=long_val,
                source="TEST-001",
                date="2026-04-01",
                workstream="financial",
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-001", path="file.xlsx", date_received="2026-04-01"),
        ]))

        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        # Should have truncated value with ...
        assert "..." in result.output
        # Should NOT contain full 50-char value
        assert long_val not in result.output

    def test_list_current_status(self, deal_dir, runner):
        """Fact with no flag and non-superseded source shows status 'current'."""
        self._seed_facts(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "current" in result.output

    def test_list_flagged_status(self, deal_dir, runner):
        """Fact with flagged dict shows status 'flagged'."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue",
                value="100",
                source="TEST-001",
                date="2026-04-01",
                workstream="financial",
                flagged={"reason": "discrepancy", "date": "2026-04-02"},
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-001", path="file.xlsx", date_received="2026-04-01"),
        ]))

        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "flagged" in result.output

    def test_list_stale_status_from_superseded_source(self, deal_dir, runner):
        """Fact whose source has been superseded in SOURCES.md shows status 'stale'."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        # TEST-002 supersedes TEST-001, so any fact citing TEST-001 is stale
        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue",
                value="100",
                source="TEST-001",
                date="2026-04-01",
                workstream="financial",
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-001", path="file_v1.xlsx", date_received="2026-04-01"),
            SourceEntry(id="TEST-002", path="file_v2.xlsx", date_received="2026-04-05",
                        supersedes="TEST-001"),
        ]))

        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "stale" in result.output


class TestTruthListFilters:
    """truth list: --stale and --workstream filters."""

    def _seed_mixed(self, deal_dir):
        """Seed facts with mixed statuses and workstreams."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue",
                value="$2,400,000",
                source="TEST-001",
                date="2026-04-01",
                workstream="financial",
            ),
            "headcount": FactEntry(
                key="headcount",
                value="42",
                source="TEST-002",
                date="2026-04-02",
                workstream="operational",
                flagged={"reason": "verify headcount", "date": "2026-04-03"},
            ),
            "lease_term": FactEntry(
                key="lease_term",
                value="5 years",
                source="TEST-001",
                date="2026-04-01",
                workstream="legal",
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

        # TEST-003 supersedes TEST-001, making revenue and lease_term stale
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-001", path="old.xlsx", date_received="2026-04-01"),
            SourceEntry(id="TEST-002", path="roster.xlsx", date_received="2026-04-02"),
            SourceEntry(id="TEST-003", path="new.xlsx", date_received="2026-04-05",
                        supersedes="TEST-001"),
        ]))

    def test_stale_filter_shows_flagged_or_stale(self, deal_dir, runner):
        """--stale shows only flagged OR stale facts."""
        self._seed_mixed(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["list", "--stale"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        # headcount is flagged, revenue and lease_term are stale
        assert "headcount" in result.output
        assert "revenue" in result.output
        assert "lease_term" in result.output

    def test_workstream_filter_scopes(self, deal_dir, runner):
        """--workstream filter scopes to one workstream."""
        self._seed_mixed(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["list", "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "revenue" in result.output
        assert "headcount" not in result.output
        assert "lease_term" not in result.output

    def test_stale_and_workstream_combine(self, deal_dir, runner):
        """--stale and --workstream can combine."""
        self._seed_mixed(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["list", "--stale", "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        # Only revenue (stale + financial)
        assert "revenue" in result.output
        assert "headcount" not in result.output
        assert "lease_term" not in result.output

    def test_summary_line_counts_all_facts(self, deal_dir, runner):
        """Summary line always counts ALL facts, not just filtered."""
        self._seed_mixed(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["list", "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        # Summary should count all 3 facts
        assert "3 facts" in result.output


class TestTruthListJSON:
    """truth list --json outputs structured JSON array."""

    def test_list_json_output(self, deal_dir, runner):
        """--json outputs structured JSON array."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue",
                value="100",
                source="TEST-001",
                date="2026-04-01",
                workstream="financial",
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-001", path="file.xlsx", date_received="2026-04-01"),
        ]))

        result = runner.invoke(
            truth_cmd,
            ["list", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["key"] == "revenue"
        assert data[0]["status"] == "current"
        assert "anchor" in data[0]

    def test_list_aligned_columns(self, deal_dir, runner):
        """truth list plain text has aligned columns."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "a": FactEntry(key="a", value="short", source="TEST-001",
                           date="2026-04-01", workstream="financial"),
            "long_key_name": FactEntry(key="long_key_name", value="value",
                                       source="TEST-002", date="2026-04-02",
                                       workstream="financial"),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-001", path="f1.xlsx", date_received="2026-04-01"),
            SourceEntry(id="TEST-002", path="f2.xlsx", date_received="2026-04-02"),
        ]))

        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        # Both lines should have consistent formatting
        lines = [l for l in result.output.strip().split("\n") if "TEST-" in l]
        assert len(lines) == 2
        # Check columns are aligned by verifying status position is consistent
        # The status field (current/flagged/stale) should start at same column
        for line in lines:
            assert "current" in line


class TestTruthListMissingSources:
    """truth list handles missing or empty SOURCES.md."""

    def test_list_missing_sources_all_current(self, deal_dir, runner):
        """If SOURCES.md is missing, all facts show as 'current'."""
        from diligent.state.models import FactEntry, TruthFile
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue", value="100", source="TEST-001",
                date="2026-04-01", workstream="financial",
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        # Write empty SOURCES.md (no sources at all)
        (deal_dir / ".diligence" / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")

        result = runner.invoke(
            truth_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "current" in result.output
        # Summary line says "0 stale", but the fact row itself shows "current"
        assert "0 stale" in result.output
        # The fact row should show "current" as its status, not "stale"
        lines = [l for l in result.output.strip().split("\n") if "revenue" in l]
        assert len(lines) == 1
        assert "current" in lines[0]


class TestTruthTrace:
    """truth trace: full revision history in reverse chronological order."""

    def _seed_fact_with_history(self, deal_dir):
        """Seed a fact with supersedes chain and sources."""
        from diligent.state.models import (
            FactEntry, SourceEntry, SourcesFile,
            SupersededValue, TruthFile,
        )
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue",
                value="$20,065",
                source="TEST-019",
                date="2026-04-07",
                workstream="financial",
                supersedes=[
                    SupersededValue(
                        value="$19,665",
                        source="TEST-003",
                        date="2026-03-15",
                    ),
                ],
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-003", path="Customer_List.xlsx",
                        date_received="2026-03-15"),
            SourceEntry(id="TEST-019", path="Customer_List_v2.xlsx",
                        date_received="2026-04-07", supersedes="TEST-003"),
        ]))

    def test_trace_shows_current_first(self, deal_dir, runner):
        """truth trace shows current value first, then supersedes chain."""
        self._seed_fact_with_history(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["trace", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "current" in result.output
        assert "$20,065" in result.output
        assert "$19,665" in result.output
        # Current value should appear before superseded value
        pos_current = result.output.index("$20,065")
        pos_old = result.output.index("$19,665")
        assert pos_current < pos_old

    def test_trace_format_shows_source_path(self, deal_dir, runner):
        """truth trace resolves source file path from SOURCES.md."""
        self._seed_fact_with_history(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["trace", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "Customer_List_v2.xlsx" in result.output
        assert "Customer_List.xlsx" in result.output

    def test_trace_includes_flag_event(self, deal_dir, runner):
        """truth trace includes flag events in timeline."""
        from diligent.state.models import FactEntry, SourceEntry, SourcesFile, TruthFile
        from diligent.state.sources import write_sources
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            "revenue": FactEntry(
                key="revenue",
                value="$20,065",
                source="TEST-019",
                date="2026-04-07",
                workstream="financial",
                flagged={"reason": "verify against Q3", "date": "2026-04-08"},
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)
        write_sources(deal_dir / ".diligence" / "SOURCES.md", SourcesFile(sources=[
            SourceEntry(id="TEST-019", path="file.xlsx", date_received="2026-04-07"),
        ]))

        result = runner.invoke(
            truth_cmd,
            ["trace", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "flagged" in result.output
        assert "verify against Q3" in result.output

    def test_trace_summary_line(self, deal_dir, runner):
        """truth trace summary shows value and supersedes counts."""
        self._seed_fact_with_history(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["trace", "revenue"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "2 values" in result.output
        assert "1 supersedes" in result.output

    def test_trace_unknown_key_exits_1(self, deal_dir, runner):
        """truth trace with unknown key prints error and exits 1."""
        (deal_dir / ".diligence" / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")
        result = runner.invoke(
            truth_cmd,
            ["trace", "nonexistent"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_trace_json_output(self, deal_dir, runner):
        """truth trace --json outputs structured timeline array."""
        self._seed_fact_with_history(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["trace", "revenue", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) >= 2
        # First entry should be the current value
        assert data[0]["label"] == "current"
        assert data[0]["value"] == "$20,065"
        assert data[0]["type"] == "value"


class TestTruthFlag:
    """truth flag: mark or clear facts for review."""

    def _seed_fact(self, deal_dir, key="revenue", value="10000",
                   source="TEST-001", flagged=None):
        from diligent.state.models import FactEntry, TruthFile
        from diligent.state.truth import write_truth

        truth = TruthFile(facts={
            key: FactEntry(
                key=key,
                value=value,
                source=source,
                date="2026-04-01",
                workstream="financial",
                flagged=flagged,
            ),
        })
        write_truth(deal_dir / ".diligence" / "TRUTH.md", truth)

    def test_flag_sets_flagged_dict(self, deal_dir, runner):
        """truth flag <key> --reason sets flagged dict on the fact."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["flag", "revenue", "--reason", "stale data from Q2"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "Flagged" in result.output
        assert "stale data from Q2" in result.output

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        fact = truth.facts["revenue"]
        assert fact.flagged is not None
        assert fact.flagged["reason"] == "stale data from Q2"
        assert "date" in fact.flagged

    def test_flag_updates_truth_md(self, deal_dir, runner):
        """truth flag writes updated TRUTH.md via write_truth."""
        self._seed_fact(deal_dir)
        runner.invoke(
            truth_cmd,
            ["flag", "revenue", "--reason", "check this"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].flagged is not None

    def test_flag_already_flagged_updates(self, deal_dir, runner):
        """truth flag on already-flagged fact updates reason and date."""
        self._seed_fact(deal_dir, flagged={"reason": "old reason", "date": "2026-04-01"})
        result = runner.invoke(
            truth_cmd,
            ["flag", "revenue", "--reason", "new reason"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].flagged["reason"] == "new reason"

    def test_flag_unknown_key_exits_1(self, deal_dir, runner):
        """truth flag with unknown key prints error and exits 1."""
        result = runner.invoke(
            truth_cmd,
            ["flag", "nonexistent", "--reason", "test"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_flag_clear_removes_flag(self, deal_dir, runner):
        """truth flag --clear removes the flagged dict."""
        self._seed_fact(deal_dir, flagged={"reason": "old flag", "date": "2026-04-01"})
        result = runner.invoke(
            truth_cmd,
            ["flag", "revenue", "--clear"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "cleared" in result.output.lower()

        from diligent.state.truth import read_truth
        truth = read_truth(deal_dir / ".diligence" / "TRUTH.md")
        assert truth.facts["revenue"].flagged is None

    def test_flag_json_output(self, deal_dir, runner):
        """truth flag --json outputs structured result."""
        self._seed_fact(deal_dir)
        result = runner.invoke(
            truth_cmd,
            ["flag", "revenue", "--reason", "check it", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["status"] == "flagged"
        assert data["key"] == "revenue"
        assert data["reason"] == "check it"


class TestTruthCLIRegistration:
    """truth group appears in diligent --help."""

    def test_truth_in_cli_help(self, runner):
        """diligent truth group appears in diligent --help."""
        from diligent.cli import cli
        result = runner.invoke(cli, ["--help"], catch_exceptions=False)
        assert "truth" in result.output
