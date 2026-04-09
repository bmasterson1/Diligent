"""Round-trip fidelity tests for all 6 state file types.

Each test creates a file with the writer, reads it back, and compares
all fields. Tests cover edge cases: empty lists, optional None fields,
multiline strings, special YAML characters, supersedes chains, and
backtick-containing values.
"""

from pathlib import Path

import pytest

from diligent.state.models import (
    ConfigFile,
    DealFile,
    FactEntry,
    SourceEntry,
    SourcesFile,
    StateFile,
    SupersededValue,
    TruthFile,
    WorkstreamEntry,
    WorkstreamsFile,
)


# --- TRUTH.md tests ---


class TestTruthRoundTrip:
    """Round-trip tests for TRUTH.md reader/writer."""

    def test_read_truth_template_zero_facts(self, tmp_path):
        """read_truth on TRUTH.md template returns TruthFile with zero facts."""
        from diligent.state.truth import read_truth

        template_dir = (
            Path(__file__).resolve().parent.parent / "diligent" / "templates"
        )
        truth = read_truth(template_dir / "TRUTH.md.tmpl")
        assert len(truth.facts) == 0

    def test_write_read_roundtrip_preserves_all_fields(self, tmp_path):
        """write_truth -> read_truth round-trip preserves all FactEntry fields."""
        from diligent.state.truth import read_truth, write_truth

        truth = TruthFile(
            facts={
                "annual_revenue": FactEntry(
                    key="annual_revenue",
                    value="2400000",
                    source="ARRIVAL-001",
                    date="2026-04-01",
                    workstream="financial",
                    supersedes=[
                        SupersededValue(
                            value="2200000",
                            source="ARRIVAL-001",
                            date="2026-03-01",
                        )
                    ],
                    computed_by="scripts/revenue_calc.py",
                    notes="Annualized from Q1 run rate",
                    flagged=None,
                ),
                "customer_count": FactEntry(
                    key="customer_count",
                    value="573",
                    source="ARRIVAL-002",
                    date="2026-04-01",
                    workstream="retention",
                    supersedes=[],
                    computed_by=None,
                    notes=None,
                    flagged={"reason": "Needs recount", "date": "2026-04-05"},
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        reread = read_truth(path)

        assert len(reread.facts) == 2
        assert set(reread.facts.keys()) == {"annual_revenue", "customer_count"}

        ar = reread.facts["annual_revenue"]
        assert ar.value == "2400000"
        assert ar.source == "ARRIVAL-001"
        assert ar.date == "2026-04-01"
        assert ar.workstream == "financial"
        assert len(ar.supersedes) == 1
        assert ar.supersedes[0].value == "2200000"
        assert ar.supersedes[0].source == "ARRIVAL-001"
        assert ar.supersedes[0].date == "2026-03-01"
        assert ar.computed_by == "scripts/revenue_calc.py"
        assert ar.notes == "Annualized from Q1 run rate"
        assert ar.flagged is None

        cc = reread.facts["customer_count"]
        assert cc.value == "573"
        assert cc.flagged is not None
        assert cc.flagged["reason"] == "Needs recount"

    def test_values_always_quoted_strings(self, tmp_path):
        """TRUTH.md fact values written as quoted strings."""
        from diligent.state.truth import write_truth

        truth = TruthFile(
            facts={
                "test_fact": FactEntry(
                    key="test_fact",
                    value="yes",
                    source="TEST-001",
                    date="2026-01-01",
                    workstream="test",
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)

        content = path.read_text(encoding="utf-8")
        # Value should be quoted (not parsed as YAML boolean)
        assert 'value: "yes"' in content

    def test_facts_alphabetical_order(self, tmp_path):
        """TRUTH.md facts written in alphabetical order by key."""
        from diligent.state.truth import write_truth

        truth = TruthFile(
            facts={
                "zebra": FactEntry(
                    key="zebra",
                    value="z",
                    source="T-001",
                    date="2026-01-01",
                    workstream="test",
                ),
                "alpha": FactEntry(
                    key="alpha",
                    value="a",
                    source="T-001",
                    date="2026-01-01",
                    workstream="test",
                ),
                "middle": FactEntry(
                    key="middle",
                    value="m",
                    source="T-001",
                    date="2026-01-01",
                    workstream="test",
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)

        content = path.read_text(encoding="utf-8")
        alpha_pos = content.index("## alpha")
        middle_pos = content.index("## middle")
        zebra_pos = content.index("## zebra")
        assert alpha_pos < middle_pos < zebra_pos

    def test_backtick_containing_values_roundtrip(self, tmp_path):
        """TRUTH.md with backtick-containing values round-trips correctly."""
        from diligent.state.truth import read_truth, write_truth

        truth = TruthFile(
            facts={
                "code_snippet": FactEntry(
                    key="code_snippet",
                    value="Use `diligent init` to start",
                    source="DOC-001",
                    date="2026-01-01",
                    workstream="technical",
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        reread = read_truth(path)

        assert reread.facts["code_snippet"].value == "Use `diligent init` to start"

    def test_empty_truth_file_roundtrip(self, tmp_path):
        """Empty TruthFile round-trips correctly."""
        from diligent.state.truth import read_truth, write_truth

        truth = TruthFile(facts={})
        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        reread = read_truth(path)
        assert len(reread.facts) == 0


# --- DEAL.md tests ---


class TestDealRoundTrip:
    """Round-trip tests for DEAL.md reader/writer."""

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        """read_deal -> write_deal -> read_deal preserves all DealFile fields."""
        from diligent.state.deal import read_deal, write_deal

        deal = DealFile(
            deal_code="ARRIVAL",
            target_legal_name="Arrival Industries LLC",
            target_common_name="Arrival",
            deal_stage="LOI Signed",
            loi_date="2026-03-15",
            principal="Bryce Masterson",
            principal_role="Apprentice",
            seller="John Smith",
            broker="Jane Doe",
            thesis="Strong recurring revenue with diversified customer base.",
            workstreams=["financial", "legal", "retention"],
        )

        path = tmp_path / "DEAL.md"
        write_deal(path, deal)
        reread = read_deal(path)

        assert reread.deal_code == "ARRIVAL"
        assert reread.target_legal_name == "Arrival Industries LLC"
        assert reread.target_common_name == "Arrival"
        assert reread.deal_stage == "LOI Signed"
        assert reread.loi_date == "2026-03-15"
        assert reread.principal == "Bryce Masterson"
        assert reread.principal_role == "Apprentice"
        assert reread.seller == "John Smith"
        assert reread.broker == "Jane Doe"
        assert reread.thesis == "Strong recurring revenue with diversified customer base."
        assert reread.workstreams == ["financial", "legal", "retention"]

    def test_multiline_thesis_roundtrip(self, tmp_path):
        """DEAL.md thesis with multiline prose round-trips correctly."""
        from diligent.state.deal import read_deal, write_deal

        thesis = """This is a multi-paragraph thesis.

The target company has strong fundamentals:
- Recurring revenue of $2.4M ARR
- 573 active customers
- Low churn rate of 3% monthly

We believe the acquisition will generate returns within 3 years."""

        deal = DealFile(
            deal_code="TEST",
            target_legal_name="Test Corp",
            target_common_name="Test",
            deal_stage="LOI",
            loi_date="2026-01-01",
            principal="Analyst",
            principal_role="Lead",
            seller="Seller",
            broker="Broker",
            thesis=thesis,
            workstreams=["financial"],
        )

        path = tmp_path / "DEAL.md"
        write_deal(path, deal)
        reread = read_deal(path)

        assert reread.thesis == thesis

    def test_empty_workstreams_roundtrip(self, tmp_path):
        """DEAL.md with empty workstreams list round-trips."""
        from diligent.state.deal import read_deal, write_deal

        deal = DealFile(
            deal_code="EMPTY",
            target_legal_name="Empty Corp",
            target_common_name="Empty",
            deal_stage="Screening",
            loi_date="2026-01-01",
            principal="A",
            principal_role="B",
            seller="C",
            broker="D",
            thesis="Minimal.",
            workstreams=[],
        )

        path = tmp_path / "DEAL.md"
        write_deal(path, deal)
        reread = read_deal(path)

        assert reread.workstreams == []


# --- SOURCES.md tests ---


class TestSourcesRoundTrip:
    """Round-trip tests for SOURCES.md reader/writer."""

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        """read_sources -> write_sources -> read_sources preserves all SourceEntry fields."""
        from diligent.state.sources import read_sources, write_sources

        sources = SourcesFile(
            sources=[
                SourceEntry(
                    id="ARRIVAL-001",
                    path="documents/cim.pdf",
                    date_received="2026-01-15",
                    parties=["Seller LLC", "Broker Inc"],
                    workstream_tags=["financial", "legal"],
                    supersedes=None,
                    notes="Confidential Information Memorandum",
                ),
                SourceEntry(
                    id="ARRIVAL-002",
                    path="documents/financials_2025.xlsx",
                    date_received="2026-02-01",
                    parties=["Seller LLC"],
                    workstream_tags=["financial"],
                    supersedes="ARRIVAL-001",
                    notes=None,
                ),
            ]
        )

        path = tmp_path / "SOURCES.md"
        write_sources(path, sources)
        reread = read_sources(path)

        assert len(reread.sources) == 2

        s1 = reread.sources[0]
        assert s1.id == "ARRIVAL-001"
        assert s1.path == "documents/cim.pdf"
        assert s1.date_received == "2026-01-15"
        assert s1.parties == ["Seller LLC", "Broker Inc"]
        assert s1.workstream_tags == ["financial", "legal"]
        assert s1.supersedes is None
        assert s1.notes == "Confidential Information Memorandum"

        s2 = reread.sources[1]
        assert s2.id == "ARRIVAL-002"
        assert s2.supersedes == "ARRIVAL-001"
        assert s2.notes is None

    def test_empty_sources_roundtrip(self, tmp_path):
        """Empty SourcesFile round-trips correctly."""
        from diligent.state.sources import read_sources, write_sources

        sources = SourcesFile(sources=[])
        path = tmp_path / "SOURCES.md"
        write_sources(path, sources)
        reread = read_sources(path)
        assert len(reread.sources) == 0


# --- WORKSTREAMS.md tests ---


class TestWorkstreamsRoundTrip:
    """Round-trip tests for WORKSTREAMS.md reader/writer."""

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        """read_workstreams -> write_workstreams -> read_workstreams preserves all fields."""
        from diligent.state.workstreams import read_workstreams, write_workstreams

        ws = WorkstreamsFile(
            workstreams=[
                WorkstreamEntry(name="financial", status="active"),
                WorkstreamEntry(name="legal", status="active"),
                WorkstreamEntry(name="retention", status="paused"),
            ]
        )

        path = tmp_path / "WORKSTREAMS.md"
        write_workstreams(path, ws)
        reread = read_workstreams(path)

        assert len(reread.workstreams) == 3
        assert reread.workstreams[0].name == "financial"
        assert reread.workstreams[0].status == "active"
        assert reread.workstreams[2].name == "retention"
        assert reread.workstreams[2].status == "paused"

    def test_empty_workstreams_roundtrip(self, tmp_path):
        """Empty WorkstreamsFile round-trips correctly."""
        from diligent.state.workstreams import read_workstreams, write_workstreams

        ws = WorkstreamsFile(workstreams=[])
        path = tmp_path / "WORKSTREAMS.md"
        write_workstreams(path, ws)
        reread = read_workstreams(path)
        assert len(reread.workstreams) == 0

    def test_read_workstreams_without_new_fields(self, tmp_path):
        """read_workstreams on WORKSTREAMS.md WITHOUT description/created returns empty defaults."""
        from diligent.state.workstreams import read_workstreams

        content = """# Workstreams

## financial
```yaml
name: financial
status: active
```

## legal
```yaml
name: legal
status: paused
```
"""
        path = tmp_path / "WORKSTREAMS.md"
        path.write_text(content, encoding="utf-8")
        ws = read_workstreams(path)

        assert len(ws.workstreams) == 2
        assert ws.workstreams[0].description == ""
        assert ws.workstreams[0].created == ""
        assert ws.workstreams[1].description == ""
        assert ws.workstreams[1].created == ""

    def test_read_workstreams_with_new_fields(self, tmp_path):
        """read_workstreams on WORKSTREAMS.md WITH description/created populates them."""
        from diligent.state.workstreams import read_workstreams

        content = """# Workstreams

## financial
```yaml
name: financial
status: active
description: Core financial analysis
created: "2026-04-01T00:00:00Z"
```
"""
        path = tmp_path / "WORKSTREAMS.md"
        path.write_text(content, encoding="utf-8")
        ws = read_workstreams(path)

        assert ws.workstreams[0].description == "Core financial analysis"
        assert ws.workstreams[0].created == "2026-04-01T00:00:00Z"

    def test_write_workstreams_omits_empty_description_and_created(self, tmp_path):
        """write_workstreams omits description when empty, omits created when empty."""
        from diligent.state.workstreams import write_workstreams

        ws = WorkstreamsFile(
            workstreams=[
                WorkstreamEntry(name="financial", status="active"),
            ]
        )
        path = tmp_path / "WORKSTREAMS.md"
        write_workstreams(path, ws)
        content = path.read_text(encoding="utf-8")

        assert "description" not in content
        assert "created" not in content

    def test_write_workstreams_includes_populated_fields(self, tmp_path):
        """write_workstreams includes description and created when populated."""
        from diligent.state.workstreams import read_workstreams, write_workstreams

        ws = WorkstreamsFile(
            workstreams=[
                WorkstreamEntry(
                    name="financial",
                    status="active",
                    description="Core financial analysis",
                    created="2026-04-01T00:00:00Z",
                ),
            ]
        )
        path = tmp_path / "WORKSTREAMS.md"
        write_workstreams(path, ws)
        content = path.read_text(encoding="utf-8")

        assert "description" in content
        assert "Core financial analysis" in content
        assert "created" in content
        assert "2026-04-01T00:00:00Z" in content

        # Verify round-trip
        reread = read_workstreams(path)
        assert reread.workstreams[0].description == "Core financial analysis"
        assert reread.workstreams[0].created == "2026-04-01T00:00:00Z"


# --- STATE.md tests ---


class TestStateFileRoundTrip:
    """Round-trip tests for STATE.md reader/writer."""

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        """read_state -> write_state -> read_state preserves all StateFile fields."""
        from diligent.state.state_file import read_state, write_state

        state = StateFile(
            created="2026-04-07T00:00:00Z",
            last_modified="2026-04-07T12:30:00Z",
        )

        path = tmp_path / "STATE.md"
        write_state(path, state)
        reread = read_state(path)

        assert reread.created == "2026-04-07T00:00:00Z"
        assert reread.last_modified == "2026-04-07T12:30:00Z"


# --- config.json tests ---


class TestConfigRoundTrip:
    """Round-trip tests for config.json reader/writer."""

    def test_roundtrip_preserves_all_fields(self, tmp_path):
        """read_config -> write_config -> read_config preserves all ConfigFile fields."""
        from diligent.state.config import read_config, write_config

        config = ConfigFile(
            schema_version=1,
            deal_code="ARRIVAL",
            created="2026-04-07T00:00:00Z",
            anchor_tolerance_pct=1.5,
            recent_window_days=14,
            workstreams=["financial", "legal", "retention"],
        )

        path = tmp_path / "config.json"
        write_config(path, config)
        reread = read_config(path)

        assert reread.schema_version == 1
        assert reread.deal_code == "ARRIVAL"
        assert reread.created == "2026-04-07T00:00:00Z"
        assert reread.anchor_tolerance_pct == 1.5
        assert reread.recent_window_days == 14
        assert reread.workstreams == ["financial", "legal", "retention"]

    def test_schema_version_preserved(self, tmp_path):
        """Schema version field is preserved through round-trip."""
        from diligent.state.config import read_config, write_config

        config = ConfigFile(
            schema_version=2,
            deal_code="TEST",
            created="2026-01-01T00:00:00Z",
            anchor_tolerance_pct=1.0,
            recent_window_days=7,
            workstreams=[],
        )

        path = tmp_path / "config.json"
        write_config(path, config)
        reread = read_config(path)

        assert reread.schema_version == 2

    def test_empty_workstreams_roundtrip(self, tmp_path):
        """config.json with empty workstreams list round-trips."""
        from diligent.state.config import read_config, write_config

        config = ConfigFile(
            schema_version=1,
            deal_code="EMPTY",
            created="2026-01-01T00:00:00Z",
            anchor_tolerance_pct=1.0,
            recent_window_days=7,
            workstreams=[],
        )

        path = tmp_path / "config.json"
        write_config(path, config)
        reread = read_config(path)

        assert reread.workstreams == []
