"""Tests for the reconcile engine (pure function staleness computation).

Tests reconcile_anchors.py: compute_staleness with value-changed, source-
superseded, and flagged fact detection. The engine is a pure function with
zero I/O imports (no click, pathlib, os).
"""

import ast
import inspect
from datetime import date
from unittest.mock import patch

import pytest

from diligent.state.models import (
    ArtifactEntry,
    FactEntry,
    SourceEntry,
    SupersededValue,
)


def _make_artifact(
    path="deliverables/analysis.docx",
    workstream="financial",
    last_refreshed="2026-03-20",
    references=None,
):
    return ArtifactEntry(
        path=path,
        workstream=workstream,
        registered="2026-03-01",
        last_refreshed=last_refreshed,
        references=references or [],
        scanner_findings=[],
        notes="",
    )


def _make_fact(
    key="revenue",
    value="$100",
    source="SRC-001",
    fact_date="2026-03-15",
    workstream="financial",
    supersedes=None,
    flagged=None,
):
    return FactEntry(
        key=key,
        value=value,
        source=source,
        date=fact_date,
        workstream=workstream,
        supersedes=supersedes or [],
        flagged=flagged,
    )


def _make_source(
    id="SRC-001",
    path="sources/doc.xlsx",
    date_received="2026-03-10",
    supersedes=None,
):
    return SourceEntry(
        id=id,
        path=path,
        date_received=date_received,
        supersedes=supersedes,
    )


class TestComputeStalenessEmpty:
    """Test 1: compute_staleness returns empty list when no artifacts registered."""

    def test_no_artifacts_returns_empty(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        result = compute_staleness(
            artifacts=[],
            facts={},
            sources=[],
        )
        assert result == []


class TestComputeStalenessAllCurrent:
    """Test 2: compute_staleness returns empty list when all artifacts current."""

    def test_all_current_returns_no_stale(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        # Fact date is BEFORE last_refreshed, so artifact is current
        art = _make_artifact(
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "revenue": _make_fact(
                key="revenue", fact_date="2026-03-15"
            ),
        }
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=[],
        )
        # All artifacts should have no stale items
        stale_artifacts = [r for r in result if r.is_stale]
        assert len(stale_artifacts) == 0


class TestValueChangedDetection:
    """Test 3: Value-changed detection when fact.date > artifact.last_refreshed."""

    def test_value_changed_marks_stale(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art = _make_artifact(
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "revenue": _make_fact(
                key="revenue",
                value="$200",
                source="SRC-002",
                fact_date="2026-03-25",
                supersedes=[
                    SupersededValue(value="$100", source="SRC-001", date="2026-03-10")
                ],
            ),
        }
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=[],
        )
        stale = [r for r in result if r.is_stale]
        assert len(stale) == 1
        assert len(stale[0].value_changed) == 1

        info = stale[0].value_changed[0]
        assert info.key == "revenue"
        assert info.new_value == "$200"
        assert info.old_value == "$100"
        assert info.source_id == "SRC-002"
        assert info.category == "value_changed"
        assert info.fact_date == "2026-03-25"


class TestSourceSupersededDetection:
    """Test 4: Source-superseded detection when fact's source was superseded."""

    def test_source_superseded_marks_stale(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art = _make_artifact(
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        # Fact uses SRC-001, which was superseded by SRC-002
        facts = {
            "revenue": _make_fact(
                key="revenue",
                value="$100",
                source="SRC-001",
                fact_date="2026-03-15",
            ),
        }
        sources = [
            _make_source(id="SRC-001", date_received="2026-03-10"),
            _make_source(
                id="SRC-002",
                date_received="2026-03-25",
                supersedes="SRC-001",
            ),
        ]
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=sources,
        )
        stale = [r for r in result if r.is_stale]
        assert len(stale) == 1
        assert len(stale[0].source_superseded) == 1

        info = stale[0].source_superseded[0]
        assert info.key == "revenue"
        assert info.category == "source_superseded"
        assert info.superseding_source_id == "SRC-002"


class TestSourceSupersededTemporalGuard:
    """Test 5: Source-superseded only fires for supersedes events AFTER last_refreshed."""

    def test_historical_supersede_no_false_positive(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        # Artifact refreshed on 2026-03-20
        # SRC-002 superseded SRC-001 on 2026-03-15 (BEFORE refresh)
        # Should NOT be stale
        art = _make_artifact(
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "revenue": _make_fact(
                key="revenue",
                value="$100",
                source="SRC-001",
                fact_date="2026-03-10",
            ),
        }
        sources = [
            _make_source(id="SRC-001", date_received="2026-03-05"),
            _make_source(
                id="SRC-002",
                date_received="2026-03-15",
                supersedes="SRC-001",
            ),
        ]
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=sources,
        )
        stale = [r for r in result if r.is_stale]
        assert len(stale) == 0


class TestFlaggedFactsAdvisoryOnly:
    """Test 6: Flagged facts produce advisory, do NOT make artifact stale."""

    def test_flagged_does_not_set_is_stale(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art = _make_artifact(
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "revenue": _make_fact(
                key="revenue",
                fact_date="2026-03-15",
                flagged={"reason": "needs recomputation", "date": "2026-03-18"},
            ),
        }
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=[],
        )
        # Should not be stale
        assert len([r for r in result if r.is_stale]) == 0

        # But should have flagged entry
        flagged_artifacts = [r for r in result if len(r.flagged) > 0]
        assert len(flagged_artifacts) == 1
        info = flagged_artifacts[0].flagged[0]
        assert info.category == "flagged"
        assert info.key == "revenue"


class TestMixedCategories:
    """Test 7: Artifact with value_changed + source_superseded + flagged facts."""

    def test_all_three_categories_populated(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art = _make_artifact(
            references=["revenue", "margin", "growth"],
            last_refreshed="2026-03-20",
        )
        facts = {
            # Value changed
            "revenue": _make_fact(
                key="revenue",
                value="$200",
                source="SRC-002",
                fact_date="2026-03-25",
                supersedes=[
                    SupersededValue(value="$100", source="SRC-001", date="2026-03-10")
                ],
            ),
            # Source superseded (fact uses SRC-003, which was superseded by SRC-004 after refresh)
            "margin": _make_fact(
                key="margin",
                value="45%",
                source="SRC-003",
                fact_date="2026-03-15",
            ),
            # Flagged
            "growth": _make_fact(
                key="growth",
                value="12%",
                source="SRC-005",
                fact_date="2026-03-15",
                flagged={"reason": "needs recomputation", "date": "2026-03-22"},
            ),
        }
        sources = [
            _make_source(id="SRC-003", date_received="2026-03-10"),
            _make_source(
                id="SRC-004",
                date_received="2026-03-25",
                supersedes="SRC-003",
            ),
        ]
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=sources,
        )
        # Should have the one artifact with all three categories
        assert len(result) >= 1
        stale_art = result[0]
        assert stale_art.is_stale is True
        assert len(stale_art.value_changed) == 1
        assert len(stale_art.source_superseded) == 1
        assert len(stale_art.flagged) == 1


class TestNonExistentKeysSkipped:
    """Test 8: References to non-existent truth keys are silently skipped."""

    def test_missing_keys_no_crash(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art = _make_artifact(
            references=["nonexistent_key", "also_missing"],
            last_refreshed="2026-03-20",
        )
        result = compute_staleness(
            artifacts=[art],
            facts={},
            sources=[],
        )
        # Should not crash, and artifact should not be stale
        stale = [r for r in result if r.is_stale]
        assert len(stale) == 0


class TestDaysStalecalculation:
    """Test 9: StaleFactInfo.days_stale calculated correctly."""

    @patch("diligent.helpers.reconcile_anchors.date")
    def test_days_stale_value_changed(self, mock_date):
        from diligent.helpers.reconcile_anchors import compute_staleness

        mock_date.today.return_value = date(2026, 3, 29)
        mock_date.fromisoformat = date.fromisoformat

        art = _make_artifact(
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "revenue": _make_fact(
                key="revenue",
                value="$200",
                source="SRC-002",
                fact_date="2026-03-25",
                supersedes=[
                    SupersededValue(value="$100", source="SRC-001", date="2026-03-10")
                ],
            ),
        }
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=[],
        )
        stale = [r for r in result if r.is_stale]
        assert len(stale) == 1
        # 2026-03-29 - 2026-03-25 = 4 days
        assert stale[0].value_changed[0].days_stale == 4


class TestIsStaleProperty:
    """Test 10: StaleArtifact.is_stale is True only when value_changed or source_superseded non-empty."""

    def test_is_stale_true_when_value_changed(self):
        from diligent.helpers.reconcile_anchors import StaleArtifact, StaleFactInfo

        sa = StaleArtifact(
            path="test.docx",
            workstream="financial",
            value_changed=[
                StaleFactInfo(
                    key="k",
                    old_value="a",
                    new_value="b",
                    source_id="S",
                    days_stale=1,
                    category="value_changed",
                    fact_date="2026-03-25",
                )
            ],
            source_superseded=[],
            flagged=[],
        )
        assert sa.is_stale is True

    def test_is_stale_false_when_only_flagged(self):
        from diligent.helpers.reconcile_anchors import StaleArtifact, StaleFactInfo

        sa = StaleArtifact(
            path="test.docx",
            workstream="financial",
            value_changed=[],
            source_superseded=[],
            flagged=[
                StaleFactInfo(
                    key="k",
                    old_value="",
                    new_value="",
                    source_id="",
                    days_stale=1,
                    category="flagged",
                    fact_date="2026-03-18",
                )
            ],
        )
        assert sa.is_stale is False


class TestIsAdvisoryProperty:
    """Test 11: StaleArtifact.is_advisory is True only when flagged non-empty and is_stale is False."""

    def test_is_advisory_true(self):
        from diligent.helpers.reconcile_anchors import StaleArtifact, StaleFactInfo

        sa = StaleArtifact(
            path="test.docx",
            workstream="financial",
            value_changed=[],
            source_superseded=[],
            flagged=[
                StaleFactInfo(
                    key="k",
                    old_value="",
                    new_value="",
                    source_id="",
                    days_stale=1,
                    category="flagged",
                    fact_date="2026-03-18",
                )
            ],
        )
        assert sa.is_advisory is True

    def test_is_advisory_false_when_stale(self):
        from diligent.helpers.reconcile_anchors import StaleArtifact, StaleFactInfo

        sa = StaleArtifact(
            path="test.docx",
            workstream="financial",
            value_changed=[
                StaleFactInfo(
                    key="k",
                    old_value="a",
                    new_value="b",
                    source_id="S",
                    days_stale=1,
                    category="value_changed",
                    fact_date="2026-03-25",
                )
            ],
            source_superseded=[],
            flagged=[
                StaleFactInfo(
                    key="k2",
                    old_value="",
                    new_value="",
                    source_id="",
                    days_stale=1,
                    category="flagged",
                    fact_date="2026-03-18",
                )
            ],
        )
        assert sa.is_advisory is False


class TestFactOrdering:
    """Test 12: Facts within a stale artifact ordered by most recently changed first."""

    def test_value_changed_ordered_newest_first(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art = _make_artifact(
            references=["alpha", "beta", "gamma"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "alpha": _make_fact(
                key="alpha",
                value="A2",
                source="SRC-002",
                fact_date="2026-03-22",
                supersedes=[SupersededValue(value="A1", source="SRC-001", date="2026-03-10")],
            ),
            "beta": _make_fact(
                key="beta",
                value="B2",
                source="SRC-003",
                fact_date="2026-03-28",
                supersedes=[SupersededValue(value="B1", source="SRC-001", date="2026-03-10")],
            ),
            "gamma": _make_fact(
                key="gamma",
                value="G2",
                source="SRC-004",
                fact_date="2026-03-25",
                supersedes=[SupersededValue(value="G1", source="SRC-001", date="2026-03-10")],
            ),
        }
        result = compute_staleness(
            artifacts=[art],
            facts=facts,
            sources=[],
        )
        stale = [r for r in result if r.is_stale]
        assert len(stale) == 1
        vc = stale[0].value_changed
        assert len(vc) == 3
        # Most recent first: beta (03-28), gamma (03-25), alpha (03-22)
        assert vc[0].key == "beta"
        assert vc[1].key == "gamma"
        assert vc[2].key == "alpha"


class TestNoPureImports:
    """Test 13: Module has NO imports from click, pathlib, or os."""

    def test_no_io_imports(self):
        import diligent.helpers.reconcile_anchors as mod

        source = inspect.getsource(mod)
        tree = ast.parse(source)

        forbidden = {"click", "pathlib", "os"}
        found_forbidden = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_module = alias.name.split(".")[0]
                    if root_module in forbidden:
                        found_forbidden.add(root_module)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_module = node.module.split(".")[0]
                    if root_module in forbidden:
                        found_forbidden.add(root_module)

        assert found_forbidden == set(), (
            f"reconcile_anchors.py imports forbidden modules: {found_forbidden}"
        )


class TestWorkstreamFilter:
    """Test 14: compute_staleness with workstream parameter filters artifacts."""

    def test_workstream_filter(self):
        from diligent.helpers.reconcile_anchors import compute_staleness

        art_fin = _make_artifact(
            path="deliverables/fin.docx",
            workstream="financial",
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        art_legal = _make_artifact(
            path="deliverables/legal.docx",
            workstream="legal",
            references=["revenue"],
            last_refreshed="2026-03-20",
        )
        facts = {
            "revenue": _make_fact(
                key="revenue",
                value="$200",
                source="SRC-002",
                fact_date="2026-03-25",
                supersedes=[
                    SupersededValue(value="$100", source="SRC-001", date="2026-03-10")
                ],
            ),
        }
        result = compute_staleness(
            artifacts=[art_fin, art_legal],
            facts=facts,
            sources=[],
            workstream="financial",
        )
        # Only financial artifact should be returned
        assert len(result) == 1
        assert result[0].workstream == "financial"
