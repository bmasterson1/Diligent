"""Performance benchmark tests for XC-01 and XC-02.

XC-01: All artifact commands (register, list, refresh) complete in under 2 seconds.
XC-02: reconcile completes in under 10 seconds at typical deal folder scale.

Tests are marked @pytest.mark.slow so they can be skipped in quick runs:
    pytest -m "not slow"

Each test creates a tmp_path deal folder with programmatically generated
state files at target scale, then times the CLI command.
"""

import json
import random
import time
from datetime import date, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.state.models import (
    ArtifactEntry,
    ArtifactsFile,
    FactEntry,
    SourceEntry,
    SourcesFile,
    TruthFile,
)
from diligent.state.artifacts import write_artifacts
from diligent.state.sources import write_sources
from diligent.state.truth import write_truth


def _generate_sources(n: int) -> SourcesFile:
    """Create a SourcesFile with n source entries, some with supersedes chains."""
    sources = []
    base_date = date(2026, 1, 1)

    for i in range(n):
        src_id = f"SRC-{i + 1:04d}"
        src_date = (base_date + timedelta(days=i)).isoformat()

        # Every 10th source supersedes the one before it
        supersedes = None
        if i > 0 and i % 10 == 0:
            supersedes = f"SRC-{i:04d}"

        sources.append(SourceEntry(
            id=src_id,
            path=f"sources/document_{i + 1}.xlsx",
            date_received=src_date,
            parties=["Party A", "Party B"],
            workstream_tags=["financial"],
            supersedes=supersedes,
        ))

    return SourcesFile(sources=sources)


def _generate_facts(n: int, source_ids: list[str]) -> TruthFile:
    """Create a TruthFile with n facts referencing random source IDs.

    Some facts are flagged, some have supersedes chains.
    """
    facts = {}
    base_date = date(2026, 1, 1)
    random.seed(42)  # Deterministic for reproducibility

    for i in range(n):
        key = f"fact_{i + 1:04d}"
        src = random.choice(source_ids)
        fact_date = (base_date + timedelta(days=random.randint(0, 90))).isoformat()

        flagged = None
        if i % 50 == 0:  # 2% flagged
            flagged = {"reason": "under review", "date": fact_date}

        entry = FactEntry(
            key=key,
            value=f"${random.randint(1000, 999999):,}",
            source=src,
            date=fact_date,
            workstream="financial",
            flagged=flagged,
        )
        facts[key] = entry

    return TruthFile(facts=facts)


def _generate_artifacts(n: int, fact_keys: list[str]) -> ArtifactsFile:
    """Create an ArtifactsFile with n artifacts, each referencing 3-10 random fact keys.

    Various last_refreshed dates create a mix of stale and current.
    """
    artifacts = []
    base_date = date(2026, 1, 1)
    random.seed(99)  # Deterministic

    for i in range(n):
        num_refs = random.randint(3, min(10, len(fact_keys)))
        refs = random.sample(fact_keys, num_refs)

        # Mix of refresh dates: some recent (current), some old (stale)
        days_ago = random.randint(0, 60)
        refresh_date = (base_date + timedelta(days=90 - days_ago)).isoformat()

        artifacts.append(ArtifactEntry(
            path=f"deliverables/report_{i + 1:04d}.docx",
            workstream="financial",
            registered="2026-01-01",
            last_refreshed=refresh_date,
            references=refs,
            notes="",
        ))

    return ArtifactsFile(artifacts=artifacts)


def _setup_deal_dir(tmp_path: Path, sources: SourcesFile, truth: TruthFile,
                    artifacts: ArtifactsFile) -> Path:
    """Create a deal directory with state files and return the deal root path."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()

    config = {
        "schema_version": 1,
        "deal_code": "PERF-TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial"],
    }
    (diligence / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    write_sources(diligence / "SOURCES.md", sources)
    write_truth(diligence / "TRUTH.md", truth)
    write_artifacts(diligence / "ARTIFACTS.md", artifacts)

    return tmp_path


@pytest.mark.slow
class TestArtifactRegisterPerformance:
    """artifact register completes under 2 seconds with 100 existing artifacts."""

    def test_register_under_2_seconds_with_100_artifacts(self, tmp_path):
        """XC-01: artifact register < 2s with 100 existing artifacts."""
        from diligent.commands.artifact_cmd import artifact_cmd

        sources = _generate_sources(50)
        source_ids = [s.id for s in sources.sources]
        truth = _generate_facts(200, source_ids)
        fact_keys = list(truth.facts.keys())
        artifacts = _generate_artifacts(100, fact_keys)

        deal_root = _setup_deal_dir(tmp_path, sources, truth, artifacts)
        runner = CliRunner()

        start = time.perf_counter()
        result = runner.invoke(
            artifact_cmd,
            ["register", "deliverables/new_report.docx",
             "--references", ",".join(fact_keys[:5])],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_root)},
        )
        elapsed = time.perf_counter() - start

        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
        assert elapsed < 2.0, f"artifact register took {elapsed:.2f}s (limit: 2.0s)"


@pytest.mark.slow
class TestArtifactListPerformance:
    """artifact list completes under 2 seconds with 100 artifacts, 500 facts, 200 sources."""

    def test_list_under_2_seconds_at_scale(self, tmp_path):
        """XC-01: artifact list < 2s with 100 artifacts, 500 facts, 200 sources."""
        from diligent.commands.artifact_cmd import artifact_cmd

        sources = _generate_sources(200)
        source_ids = [s.id for s in sources.sources]
        truth = _generate_facts(500, source_ids)
        fact_keys = list(truth.facts.keys())
        artifacts = _generate_artifacts(100, fact_keys)

        deal_root = _setup_deal_dir(tmp_path, sources, truth, artifacts)
        runner = CliRunner()

        start = time.perf_counter()
        result = runner.invoke(
            artifact_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_root)},
        )
        elapsed = time.perf_counter() - start

        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
        assert elapsed < 2.0, f"artifact list took {elapsed:.2f}s (limit: 2.0s)"


@pytest.mark.slow
class TestArtifactRefreshPerformance:
    """artifact refresh completes under 2 seconds with 100 existing artifacts."""

    def test_refresh_under_2_seconds_with_100_artifacts(self, tmp_path):
        """XC-01: artifact refresh < 2s with 100 existing artifacts."""
        from diligent.commands.artifact_cmd import artifact_cmd

        sources = _generate_sources(50)
        source_ids = [s.id for s in sources.sources]
        truth = _generate_facts(200, source_ids)
        fact_keys = list(truth.facts.keys())
        artifacts = _generate_artifacts(100, fact_keys)

        deal_root = _setup_deal_dir(tmp_path, sources, truth, artifacts)
        runner = CliRunner()

        # Refresh the first artifact
        start = time.perf_counter()
        result = runner.invoke(
            artifact_cmd,
            ["refresh", "deliverables/report_0001.docx"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_root)},
        )
        elapsed = time.perf_counter() - start

        assert result.exit_code == 0, f"Exit code {result.exit_code}: {result.output}"
        assert elapsed < 2.0, f"artifact refresh took {elapsed:.2f}s (limit: 2.0s)"


@pytest.mark.slow
class TestReconcilePerformance:
    """reconcile completes under 10 seconds at typical deal scale."""

    def test_reconcile_under_10_seconds_typical_scale(self, tmp_path):
        """XC-02: reconcile < 10s with 200 sources, 500 facts, 100 artifacts."""
        from diligent.commands.reconcile_cmd import reconcile_cmd

        sources = _generate_sources(200)
        source_ids = [s.id for s in sources.sources]
        truth = _generate_facts(500, source_ids)
        fact_keys = list(truth.facts.keys())
        artifacts = _generate_artifacts(100, fact_keys)

        deal_root = _setup_deal_dir(tmp_path, sources, truth, artifacts)
        runner = CliRunner()

        start = time.perf_counter()
        result = runner.invoke(
            reconcile_cmd,
            ["--all"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_root)},
        )
        elapsed = time.perf_counter() - start

        # reconcile may exit 0 or 1 depending on staleness state
        assert result.exit_code in (0, 1), f"Unexpected exit code {result.exit_code}: {result.output}"
        assert elapsed < 10.0, f"reconcile took {elapsed:.2f}s (limit: 10.0s)"

    def test_reconcile_under_2_seconds_small_scale(self, tmp_path):
        """XC-01: reconcile < 2s with 50 sources, 50 facts, 20 artifacts (small deal)."""
        from diligent.commands.reconcile_cmd import reconcile_cmd

        sources = _generate_sources(50)
        source_ids = [s.id for s in sources.sources]
        truth = _generate_facts(50, source_ids)
        fact_keys = list(truth.facts.keys())
        artifacts = _generate_artifacts(20, fact_keys)

        deal_root = _setup_deal_dir(tmp_path, sources, truth, artifacts)
        runner = CliRunner()

        start = time.perf_counter()
        result = runner.invoke(
            reconcile_cmd,
            ["--all"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_root)},
        )
        elapsed = time.perf_counter() - start

        assert result.exit_code in (0, 1), f"Unexpected exit code {result.exit_code}: {result.output}"
        assert elapsed < 2.0, f"reconcile took {elapsed:.2f}s (limit: 2.0s)"
