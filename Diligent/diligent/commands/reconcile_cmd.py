"""reconcile command: check artifact staleness against truth and sources.

Thin CLI wrapper around reconcile_anchors.py pure function engine.
Handles I/O (reading state files), formatting, and exit codes only.
All staleness logic lives in the engine module.
"""

import json
import os
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.reconcile_anchors import (
    StaleArtifact,
    StaleFactInfo,
    compute_staleness,
)
from diligent.state.artifacts import read_artifacts
from diligent.state.models import SourcesFile
from diligent.state.sources import read_sources
from diligent.state.truth import read_truth


def _find_diligence_dir(env_cwd: Optional[str] = None) -> Path:
    """Locate the .diligence/ directory.

    Checks DILIGENT_CWD env override first (for testing), then walks
    up from cwd.

    Raises:
        click.ClickException: If .diligence/ not found.
    """
    if env_cwd:
        candidate = Path(env_cwd) / ".diligence"
        if candidate.is_dir():
            return candidate

    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".diligence"
        if candidate.is_dir():
            return candidate

    raise click.ClickException(
        "No .diligence/ directory found. Run 'diligent init' first."
    )


def _resolve_source_path(sources_list, source_id: str) -> str:
    """Look up file path for a source ID from the sources list."""
    for src in sources_list:
        if src.id == source_id:
            return src.path
    return source_id


def _format_value_changed_line(
    info: StaleFactInfo, key_width: int, verbose: bool, sources_list=None
) -> list[str]:
    """Format a value-changed fact as one or two lines."""
    value_pair = f"{info.old_value} -> {info.new_value}" if info.old_value else f"-> {info.new_value}"
    line = f"    {info.key:<{key_width}}  {value_pair}  {info.source_id}  ({info.days_stale}d stale)"
    lines = [line]
    if verbose and sources_list:
        path = _resolve_source_path(sources_list, info.source_id)
        lines.append(f"      source: {path}  date: {info.fact_date}")
    return lines


def _format_source_superseded_line(
    info: StaleFactInfo, key_width: int, verbose: bool, sources_list=None
) -> list[str]:
    """Format a source-superseded fact as one or two lines."""
    sup_id = info.superseding_source_id or "unknown"
    line = (
        f"    {info.key:<{key_width}}  "
        f"(source {info.source_id} superseded by {sup_id})  "
        f"({info.days_stale}d stale)"
    )
    lines = [line]
    if verbose and sources_list:
        path = _resolve_source_path(sources_list, sup_id)
        lines.append(f"      source: {path}  date: {info.fact_date}")
    return lines


def _format_flagged_line(info: StaleFactInfo, key_width: int) -> str:
    """Format a flagged fact as a single line."""
    reason = info.old_value if info.old_value else "no reason given"
    return f"    {info.key:<{key_width}}  flagged: \"{reason}\""


def _format_artifact(
    sa: StaleArtifact,
    key_width: int,
    verbose: bool,
    sources_list=None,
    show_current: bool = False,
) -> list[str]:
    """Format a single artifact's reconcile output."""
    lines: list[str] = []

    # Determine status marker
    if sa.is_stale:
        marker = "[STALE]"
    elif sa.is_advisory:
        marker = "[ADVISORY]"
    else:
        marker = "[CURRENT]"

    # Skip current artifacts unless --all
    if not sa.is_stale and not sa.is_advisory and not show_current:
        return []

    lines.append(f"## {sa.path}  {marker}")
    lines.append("")

    if sa.is_stale or sa.is_advisory:
        if sa.value_changed:
            lines.append("  Value changed:")
            for info in sa.value_changed:
                lines.extend(
                    _format_value_changed_line(info, key_width, verbose, sources_list)
                )
            lines.append("")

        if sa.source_superseded:
            lines.append("  Source superseded:")
            for info in sa.source_superseded:
                lines.extend(
                    _format_source_superseded_line(
                        info, key_width, verbose, sources_list
                    )
                )
            lines.append("")

        if sa.flagged:
            lines.append("  Flagged facts (advisory):")
            for info in sa.flagged:
                lines.append(_format_flagged_line(info, key_width))
            lines.append("")

    return lines


def _compute_key_width(results: list[StaleArtifact]) -> int:
    """Compute adaptive key column width from data, capped at 25."""
    max_key = 10  # minimum
    for sa in results:
        for info_list in (sa.value_changed, sa.source_superseded, sa.flagged):
            for info in info_list:
                if len(info.key) > max_key:
                    max_key = len(info.key)
    return min(max_key, 25)


def _build_json_output(results: list[StaleArtifact], summary: dict) -> dict:
    """Build structured JSON output."""
    artifacts_data = []
    for sa in results:
        art_dict = {
            "path": sa.path,
            "workstream": sa.workstream,
            "is_stale": sa.is_stale,
            "is_advisory": sa.is_advisory,
            "value_changed": [
                {
                    "key": f.key,
                    "old_value": f.old_value,
                    "new_value": f.new_value,
                    "source_id": f.source_id,
                    "days_stale": f.days_stale,
                    "fact_date": f.fact_date,
                }
                for f in sa.value_changed
            ],
            "source_superseded": [
                {
                    "key": f.key,
                    "source_id": f.source_id,
                    "superseding_source_id": f.superseding_source_id,
                    "days_stale": f.days_stale,
                    "fact_date": f.fact_date,
                }
                for f in sa.source_superseded
            ],
            "flagged": [
                {
                    "key": f.key,
                    "days_stale": f.days_stale,
                }
                for f in sa.flagged
            ],
        }
        artifacts_data.append(art_dict)

    return {"artifacts": artifacts_data, "summary": summary}


@click.command("reconcile")
@click.option("--workstream", default=None, help="Filter to one workstream.")
@click.option("--strict", is_flag=True, default=False, help="Exit non-zero on flagged facts.")
@click.option("--all", "show_all", is_flag=True, default=False, help="Show all artifacts including current.")
@click.option("--verbose", is_flag=True, default=False, help="Two-line format with source details.")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output structured JSON.")
@click.pass_context
def reconcile_cmd(ctx, workstream, strict, show_all, verbose, json_mode):
    """Check which artifacts are stale and need refresh.

    Compares artifact reference timestamps against truth and source
    state. Shows which facts changed, which sources were superseded,
    and which facts are flagged for review.

    Exit codes: 0 if all current, 1 if any stale. With --strict,
    also exits 1 if any facts are flagged.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Read the three state files
    artifacts_file = read_artifacts(diligence / "ARTIFACTS.md")
    truth_file = read_truth(diligence / "TRUTH.md")

    sources_path = diligence / "SOURCES.md"
    if sources_path.exists():
        sources_file = read_sources(sources_path)
    else:
        sources_file = SourcesFile(sources=[])

    # Run the pure staleness engine
    results = compute_staleness(
        artifacts=artifacts_file.artifacts,
        facts=truth_file.facts,
        sources=sources_file.sources,
        workstream=workstream,
    )

    # Compute summary counts
    stale_count = sum(1 for r in results if r.is_stale)
    advisory_count = sum(1 for r in results if r.is_advisory)
    current_count = sum(1 for r in results if not r.is_stale and not r.is_advisory)
    total_facts_changed = sum(
        len(r.value_changed) + len(r.source_superseded) for r in results
    )

    summary = {
        "stale_artifacts": stale_count,
        "facts_changed": total_facts_changed,
        "current_artifacts": current_count,
        "advisory_artifacts": advisory_count,
    }

    # Determine exit code
    has_stale = stale_count > 0
    has_flagged = any(len(r.flagged) > 0 for r in results)

    if has_stale:
        exit_code = 1
    elif strict and has_flagged:
        exit_code = 1
    else:
        exit_code = 0

    # --- JSON output ---
    if json_mode:
        output = _build_json_output(results, summary)
        click.echo(json.dumps(output, indent=2, default=str))
        ctx.exit(exit_code)
        return

    # --- Plain text output ---
    if stale_count == 0 and advisory_count == 0 and not show_all:
        click.echo("All artifacts current.")
        summary_line = (
            f"\n{stale_count} artifacts stale, "
            f"{total_facts_changed} facts changed, "
            f"{current_count} artifacts current"
        )
        click.echo(summary_line)
        ctx.exit(exit_code)
        return

    key_width = _compute_key_width(results)

    # Format each artifact
    output_lines: list[str] = []
    for sa in results:
        artifact_lines = _format_artifact(
            sa,
            key_width=key_width,
            verbose=verbose,
            sources_list=sources_file.sources,
            show_current=show_all,
        )
        output_lines.extend(artifact_lines)

    # Print artifact sections
    for line in output_lines:
        click.echo(line)

    # Summary line (always present)
    summary_line = (
        f"{stale_count} artifacts stale, "
        f"{total_facts_changed} facts changed, "
        f"{current_count} artifacts current"
    )
    click.echo(summary_line)

    ctx.exit(exit_code)
