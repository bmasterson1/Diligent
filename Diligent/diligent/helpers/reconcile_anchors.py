"""Pure function staleness engine for reconcile.

Computes two-trigger staleness (value changed, source superseded) plus
flagged advisory for artifacts. Zero I/O imports: no click, pathlib, or os.
All data is passed in as arguments; all results returned as dataclasses.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from diligent.state.models import ArtifactEntry, FactEntry, SourceEntry


@dataclass
class StaleFactInfo:
    """Information about a single stale/flagged fact within an artifact."""

    key: str
    old_value: str
    new_value: str
    source_id: str
    days_stale: int
    category: str  # "value_changed" | "source_superseded" | "flagged"
    fact_date: str
    superseding_source_id: Optional[str] = None  # For source_superseded category


@dataclass
class StaleArtifact:
    """Staleness results for a single artifact."""

    path: str
    workstream: str
    value_changed: list[StaleFactInfo] = field(default_factory=list)
    source_superseded: list[StaleFactInfo] = field(default_factory=list)
    flagged: list[StaleFactInfo] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        """True when value_changed or source_superseded non-empty."""
        return len(self.value_changed) > 0 or len(self.source_superseded) > 0

    @property
    def is_advisory(self) -> bool:
        """True when flagged non-empty and is_stale is False."""
        return len(self.flagged) > 0 and not self.is_stale


def _build_superseded_by_index(
    sources: list[SourceEntry],
) -> dict[str, SourceEntry]:
    """Build reverse lookup: old_source_id -> SourceEntry that superseded it.

    Walks the sources list. For each source with a `supersedes` field,
    maps the superseded source ID to the superseding SourceEntry.
    """
    index: dict[str, SourceEntry] = {}
    for src in sources:
        if src.supersedes:
            index[src.supersedes] = src
    return index


def compute_staleness(
    artifacts: list[ArtifactEntry],
    facts: dict[str, FactEntry],
    sources: list[SourceEntry],
    workstream: Optional[str] = None,
) -> list[StaleArtifact]:
    """Compute staleness for artifacts against truth and source state.

    Pure function: no I/O, no side effects. All data passed in, results
    returned as StaleArtifact list.

    Two staleness triggers:
    - Value changed: fact.date > artifact.last_refreshed
    - Source superseded: fact's source was superseded by a newer source
      AND the superseding source's date_received > artifact.last_refreshed

    Flagged facts are advisory only: they populate the flagged list but
    never set is_stale to True.

    Args:
        artifacts: List of ArtifactEntry from ARTIFACTS.md
        facts: Dict of key -> FactEntry from TRUTH.md
        sources: List of SourceEntry from SOURCES.md
        workstream: Optional filter to scope to one workstream

    Returns:
        List of StaleArtifact, one per artifact (filtered by workstream if set)
    """
    superseded_by = _build_superseded_by_index(sources)
    today = date.today()

    # Filter artifacts by workstream if specified
    target_artifacts = artifacts
    if workstream is not None:
        target_artifacts = [a for a in artifacts if a.workstream == workstream]

    results: list[StaleArtifact] = []

    for artifact in target_artifacts:
        value_changed: list[StaleFactInfo] = []
        source_superseded: list[StaleFactInfo] = []
        flagged_list: list[StaleFactInfo] = []

        for ref_key in artifact.references:
            # Skip non-existent truth keys
            if ref_key not in facts:
                continue

            fact = facts[ref_key]

            # --- Value changed detection ---
            if fact.date > artifact.last_refreshed:
                # Get old value from supersedes chain if available
                old_value = ""
                if fact.supersedes:
                    old_value = fact.supersedes[0].value

                days = (today - date.fromisoformat(fact.date)).days
                value_changed.append(
                    StaleFactInfo(
                        key=ref_key,
                        old_value=old_value,
                        new_value=fact.value,
                        source_id=fact.source,
                        days_stale=days,
                        category="value_changed",
                        fact_date=fact.date,
                    )
                )

            # --- Source superseded detection ---
            if fact.source in superseded_by:
                superseding = superseded_by[fact.source]
                # Only fire if superseding source date > artifact's last_refreshed
                if superseding.date_received > artifact.last_refreshed:
                    days = (
                        today - date.fromisoformat(superseding.date_received)
                    ).days
                    source_superseded.append(
                        StaleFactInfo(
                            key=ref_key,
                            old_value=fact.value,
                            new_value="",
                            source_id=fact.source,
                            days_stale=days,
                            category="source_superseded",
                            fact_date=superseding.date_received,
                            superseding_source_id=superseding.id,
                        )
                    )

            # --- Flagged facts detection ---
            if fact.flagged is not None:
                flagged_date = fact.flagged.get("date", fact.date)
                reason = fact.flagged.get("reason", "")
                days = (today - date.fromisoformat(flagged_date)).days
                flagged_list.append(
                    StaleFactInfo(
                        key=ref_key,
                        old_value=reason,
                        new_value="",
                        source_id=fact.source,
                        days_stale=days,
                        category="flagged",
                        fact_date=flagged_date,
                    )
                )

        # Sort value_changed and source_superseded by fact_date descending
        value_changed.sort(key=lambda f: f.fact_date, reverse=True)
        source_superseded.sort(key=lambda f: f.fact_date, reverse=True)

        results.append(
            StaleArtifact(
                path=artifact.path,
                workstream=artifact.workstream,
                value_changed=value_changed,
                source_superseded=source_superseded,
                flagged=flagged_list,
            )
        )

    return results
