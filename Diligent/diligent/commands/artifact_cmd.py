"""artifact command group: register, list, and refresh subcommands.

Manage deliverable tracking in ARTIFACTS.md. Register links artifacts
to truth keys, list shows current staleness status, refresh marks an
artifact as up-to-date.
"""

import os
from datetime import date
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.formatting import output_result
from diligent.state.artifacts import read_artifacts, write_artifacts
from diligent.state.models import ArtifactEntry, SourceEntry, SourcesFile
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


def _normalize_path(raw_path: str, deal_root: Path) -> str:
    """Normalize a file path to posix forward slashes relative to deal root.

    If the path is absolute, compute relative to deal_root. If relative,
    normalize separators. Always returns posix-style forward slashes.
    """
    p = Path(raw_path)

    # If absolute, make relative to deal_root
    if p.is_absolute():
        try:
            p = p.relative_to(deal_root)
        except ValueError:
            pass  # Keep as-is if not under deal root

    # Convert to posix with forward slashes
    return p.as_posix()


@click.group("artifact")
def artifact_cmd():
    """Manage deliverable artifacts."""
    pass


@artifact_cmd.command("register")
@click.argument("path")
@click.option("--references", default=None,
              help="Comma-separated truth keys this artifact references.")
@click.option("--workstream", default="", help="Workstream name.")
@click.option("--notes", default="", help="Free-text notes.")
@click.option("--confirm", "confirm_flag", is_flag=True, default=False,
              help="Confirm upsert of existing artifact.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def register(ctx, path, references, workstream, notes, confirm_flag, json_mode):
    """Register or update an artifact with truth key references.

    PATH is the deliverable file path (relative to deal root).
    Re-registering an existing artifact requires --confirm to update.

    For .docx files, the scanner runs automatically to find
    {{truth:key_name}} citation tags. --references is authoritative
    when provided; scanner findings are stored separately as advisory.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)
    deal_root = diligence.parent

    # Normalize path to posix
    normalized = _normalize_path(path, deal_root)

    # Determine if this is a .docx file
    is_docx = normalized.lower().endswith(".docx")

    # For non-.docx files, --references is required
    if not is_docx and not references:
        click.echo("Error: --references is required for non-.docx files.")
        ctx.exit(1)
        return

    # Run scanner on .docx files
    scanner_findings: list[str] = []
    if is_docx:
        from diligent.helpers.artifact_scanner import scan_docx_citations

        # Resolve absolute path for scanner
        abs_docx_path = deal_root / normalized
        scanner_findings = scan_docx_citations(str(abs_docx_path))

    # Handle .docx without --references
    if is_docx and not references:
        if scanner_findings:
            click.echo(
                f"Scanner found these truth keys: {', '.join(scanner_findings)}. "
                "Re-run with --references to confirm."
            )
        else:
            click.echo(
                "No citation tags found in .docx. Provide --references."
            )
        ctx.exit(1)
        return

    # Parse comma-separated references
    ref_list = [r.strip() for r in references.split(",") if r.strip()]

    # Validate references against TRUTH.md
    truth = read_truth(diligence / "TRUTH.md")
    missing_keys = [k for k in ref_list if k not in truth.facts]
    if missing_keys:
        for mk in missing_keys:
            click.echo(f"WARNING: Truth key '{mk}' not found in TRUTH.md.")

    # Scanner advisory: print keys found by scanner but not in --references
    if is_docx and scanner_findings:
        ref_set = set(ref_list)
        extra_keys = [k for k in scanner_findings if k not in ref_set]
        if extra_keys:
            click.echo(
                f"Scanner also found these keys you didn't list: "
                f"{', '.join(extra_keys)}"
            )

    # Read existing artifacts
    artifacts = read_artifacts(diligence / "ARTIFACTS.md")

    # Check for existing artifact with same path
    existing_idx = None
    for i, a in enumerate(artifacts.artifacts):
        if a.path == normalized:
            existing_idx = i
            break

    today = date.today().isoformat()

    if existing_idx is not None:
        existing = artifacts.artifacts[existing_idx]
        if not confirm_flag:
            # Show current references and exit 1
            click.echo(f"Artifact already registered: {normalized}")
            click.echo(f"Current references: {', '.join(existing.references)}")
            click.echo("Re-run with --confirm to update.")
            ctx.exit(1)
            return

        # Upsert: update references, last_refreshed, workstream, notes
        existing.references = ref_list
        existing.last_refreshed = today
        existing.workstream = workstream
        existing.notes = notes
        existing.scanner_findings = scanner_findings
        artifacts.artifacts[existing_idx] = existing
        status = "updated"
    else:
        # New artifact
        entry = ArtifactEntry(
            path=normalized,
            workstream=workstream,
            registered=today,
            last_refreshed=today,
            references=ref_list,
            scanner_findings=scanner_findings,
            notes=notes,
        )
        artifacts.artifacts.append(entry)
        status = "created"

    write_artifacts(diligence / "ARTIFACTS.md", artifacts)

    if json_mode:
        output_result({
            "status": status,
            "path": normalized,
            "references": ref_list,
        }, json_mode=True)
    else:
        click.echo(f"Artifact {status}: {normalized}")


def _build_superseded_by_index(sources: SourcesFile) -> dict[str, SourceEntry]:
    """Build a mapping from superseded source ID to the newer SourceEntry.

    Walk sources list; for each source with a `supersedes` field, map the
    old source ID to the new source entry. Used for source-superseded
    staleness detection.
    """
    index: dict[str, SourceEntry] = {}
    for src in sources.sources:
        if src.supersedes:
            index[src.supersedes] = src
    return index


def _compute_artifact_status(
    artifact: ArtifactEntry,
    truth_facts: dict,
    superseded_by: dict,
) -> str:
    """Compute live staleness status for an artifact.

    Returns "STALE" if any referenced fact has value_changed or source_superseded,
    "ADVISORY" if only flagged facts (no staleness), "CURRENT" otherwise.
    """
    has_stale = False
    has_flagged = False

    for ref_key in artifact.references:
        fact = truth_facts.get(ref_key)
        if fact is None:
            continue

        # Value changed: fact date is after artifact last_refreshed
        if fact.date > artifact.last_refreshed:
            has_stale = True

        # Source superseded: fact's source was superseded by a newer source
        # AND the newer source's date_received is after artifact last_refreshed
        if fact.source in superseded_by:
            newer_source = superseded_by[fact.source]
            if newer_source.date_received > artifact.last_refreshed:
                has_stale = True

        # Flagged fact
        if fact.flagged is not None:
            has_flagged = True

    if has_stale:
        return "STALE"
    if has_flagged:
        return "ADVISORY"
    return "CURRENT"


@artifact_cmd.command("list")
@click.option("--stale", "stale_flag", is_flag=True, default=False,
              help="Show only stale and advisory artifacts.")
@click.option("--workstream", default=None, help="Filter by workstream.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def list_cmd(ctx, stale_flag, workstream, json_mode):
    """List all registered artifacts with live staleness status.

    Shows status column: CURRENT, STALE (value changed or source superseded),
    or ADVISORY (flagged facts only). Use --stale to filter to stale/advisory.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    artifacts = read_artifacts(diligence / "ARTIFACTS.md")
    truth = read_truth(diligence / "TRUTH.md")

    # Read sources for staleness detection
    sources_path = diligence / "SOURCES.md"
    if sources_path.exists():
        sources = read_sources(sources_path)
    else:
        sources = SourcesFile(sources=[])

    superseded_by = _build_superseded_by_index(sources)

    if not artifacts.artifacts:
        if json_mode:
            output_result([], json_mode=True)
        else:
            click.echo("No artifacts registered.")
        return

    # Compute status for all artifacts
    all_entries = []
    for a in artifacts.artifacts:
        status = _compute_artifact_status(a, truth.facts, superseded_by)
        all_entries.append((a, status))

    # Summary counts (always from ALL artifacts)
    count_stale = sum(1 for _, s in all_entries if s == "STALE")
    count_advisory = sum(1 for _, s in all_entries if s == "ADVISORY")
    count_current = sum(1 for _, s in all_entries if s == "CURRENT")

    # Apply filters for display
    display = all_entries
    if workstream:
        display = [(a, s) for a, s in display if a.workstream == workstream]
    if stale_flag:
        display = [(a, s) for a, s in display if s in ("STALE", "ADVISORY")]

    if json_mode:
        result = []
        for a, status in display:
            result.append({
                "path": a.path,
                "workstream": a.workstream,
                "status": status,
                "references": a.references,
                "registered": a.registered,
                "last_refreshed": a.last_refreshed,
            })
        output_result(result, json_mode=True)
        return

    # Plain text output: aligned columns
    path_w = 40
    ws_w = 15
    status_w = 10

    for a, status in display:
        p = a.path
        if len(p) > path_w:
            p = p[:path_w - 3] + "..."
        ws = a.workstream
        if len(ws) > ws_w:
            ws = ws[:ws_w - 3] + "..."
        click.echo(f"{p:<{path_w}} {ws:<{ws_w}} {status:<{status_w}}")

    click.echo(f"\n{count_stale} stale, {count_advisory} advisory, {count_current} current")


@artifact_cmd.command("refresh")
@click.argument("path")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def refresh(ctx, path, json_mode):
    """Mark an artifact as refreshed, updating its last_refreshed timestamp.

    PATH is the deliverable file path (relative to deal root).
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)
    deal_root = diligence.parent

    # Normalize path
    normalized = _normalize_path(path, deal_root)

    artifacts = read_artifacts(diligence / "ARTIFACTS.md")

    # Find artifact by normalized path
    found_idx = None
    for i, a in enumerate(artifacts.artifacts):
        if a.path == normalized:
            found_idx = i
            break

    if found_idx is None:
        click.echo(f"Artifact not found: {normalized}")
        ctx.exit(1)
        return

    today = date.today().isoformat()
    artifacts.artifacts[found_idx].last_refreshed = today
    write_artifacts(diligence / "ARTIFACTS.md", artifacts)

    if json_mode:
        output_result({
            "status": "refreshed",
            "path": normalized,
            "last_refreshed": today,
        }, json_mode=True)
    else:
        click.echo(f"Artifact refreshed: {normalized}")
