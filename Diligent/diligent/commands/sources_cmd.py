"""Source document registry commands.

Provides:
- `ingest`: Register a new source document with metadata
- `sources list`: List all registered sources
- `sources show <id>`: Display full record for a single source
- `sources diff <id-a> <id-b>`: Compare two source documents
"""

import json as json_lib
import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.formatting import output_result
from diligent.state.config import read_config
from diligent.state.models import SourceEntry, SourcesFile
from diligent.state.sources import read_sources, write_sources


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


def _next_source_id(sources: SourcesFile, deal_code: str) -> str:
    """Generate the next source ID from existing SOURCES.md entries.

    Scans all source IDs matching {deal_code}- prefix, parses the
    numeric suffix, returns {deal_code}-{max+1:03d}. If no existing
    sources, returns {deal_code}-001.

    Self-healing: derives from SOURCES.md max, not a counter file.
    """
    pattern = re.compile(rf"^{re.escape(deal_code)}-(\d+)$")
    max_num = 0
    for entry in sources.sources:
        m = pattern.match(entry.id)
        if m:
            num = int(m.group(1))
            if num > max_num:
                max_num = num
    return f"{deal_code}-{max_num + 1:03d}"


def _resolve_relative_path(file_path: Path, deal_root: Path) -> str:
    """Resolve file_path to a relative path from deal_root.

    Deal root is the parent of .diligence/ directory.
    Returns posix string for cross-platform consistency in SOURCES.md.
    """
    abs_file = file_path.resolve()
    abs_root = deal_root.resolve()
    try:
        rel = abs_file.relative_to(abs_root)
    except ValueError:
        # File is outside deal root; store absolute as posix fallback
        return abs_file.as_posix()
    return rel.as_posix()


def _parse_parties(parties_str: str | None) -> list[str]:
    """Parse comma-separated parties string into a list.

    Splits on comma, strips whitespace, filters empty strings.
    """
    if not parties_str:
        return []
    return [p.strip() for p in parties_str.split(",") if p.strip()]


@click.command("ingest")
@click.argument("path", type=click.Path(exists=True))
@click.option("--date", "date_received", default=None,
              help="Date received (ISO format). Defaults to today.")
@click.option("--parties", default=None,
              help="Comma-separated party names.")
@click.option("--workstream", default=None,
              help="Workstream tag.")
@click.option("--supersedes", default=None,
              help="Prior source ID this document supersedes.")
@click.option("--notes", default=None,
              help="Free text notes.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON result.")
def ingest_cmd(path, date_received, parties, workstream, supersedes, notes, json_mode):
    """Register a source document with metadata."""
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence_dir = _find_diligence_dir(env_cwd)
    deal_root = diligence_dir.parent

    # Read config for deal code
    config = read_config(diligence_dir / "config.json")
    deal_code = config.deal_code

    # Read current sources
    sources_path = diligence_dir / "SOURCES.md"
    sources = read_sources(sources_path)

    # Generate next ID
    source_id = _next_source_id(sources, deal_code)

    # Resolve relative path
    file_path = Path(path)
    rel_path = _resolve_relative_path(file_path, deal_root)

    # Default date to today
    if date_received is None:
        date_received = date.today().isoformat()

    # Parse parties
    parties_list = _parse_parties(parties)

    # Workstream as list
    workstream_tags = [workstream] if workstream else []

    # Warn if supersedes ID not found (do not block)
    if supersedes:
        existing_ids = {s.id for s in sources.sources}
        if supersedes not in existing_ids:
            click.echo(f"WARNING: Superseded source '{supersedes}' not found in SOURCES.md.")

    # Create entry
    entry = SourceEntry(
        id=source_id,
        path=rel_path,
        date_received=date_received,
        parties=parties_list,
        workstream_tags=workstream_tags,
        supersedes=supersedes,
        notes=notes,
    )

    # Append and write
    sources.sources.append(entry)
    write_sources(sources_path, sources)

    # Output
    result_data = {
        "source_id": source_id,
        "path": rel_path,
        "date_received": date_received,
        "parties": parties_list,
        "workstream_tags": workstream_tags,
        "supersedes": supersedes,
        "notes": notes,
    }

    if json_mode:
        output_result(result_data, json_mode=True)
    else:
        click.echo(f"Registered {source_id}: {rel_path}")
        click.echo(click.style(
            f"Next: run 'diligent truth set <key> <value> --source {source_id}' to record facts from this document.",
            dim=True,
        ))

    # Auto-diff on ingest when --supersedes is provided and both files are Excel
    if supersedes:
        try:
            superseded_entry = _lookup_source(sources, supersedes)
            if superseded_entry is not None and _is_excel(superseded_entry.path) and _is_excel(rel_path):
                old_path = str(deal_root / superseded_entry.path)
                new_path = str(deal_root / rel_path)
                old_filename = Path(superseded_entry.path).name

                from diligent.helpers.diff_excel import diff_excel_summary

                diff_result = diff_excel_summary(old_path, new_path)
                click.echo(_format_ingest_auto_diff(diff_result, supersedes, old_filename, source_id))
        except Exception:
            # Auto-diff failure must not block ingest
            pass


@click.group("sources")
def sources_cmd():
    """Manage source documents."""
    pass


def _truncate(text: str, width: int) -> str:
    """Truncate text to width, adding ... if needed."""
    if len(text) <= width:
        return text
    return text[: width - 3] + "..."


def _source_to_dict(entry: SourceEntry) -> dict:
    """Convert a SourceEntry to a plain dict for JSON output."""
    return {
        "id": entry.id,
        "path": entry.path,
        "date_received": entry.date_received,
        "parties": entry.parties,
        "workstream_tags": entry.workstream_tags,
        "supersedes": entry.supersedes,
        "notes": entry.notes,
    }


@sources_cmd.command("list")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
def sources_list(json_mode):
    """List all registered source documents."""
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence_dir = _find_diligence_dir(env_cwd)
    sources_path = diligence_dir / "SOURCES.md"
    sources = read_sources(sources_path)

    if json_mode:
        data = [_source_to_dict(s) for s in sources.sources]
        output_result(data, json_mode=True)
        return

    count = len(sources.sources)
    if count == 0:
        click.echo("No sources registered.")
        click.echo(f"\n{count} sources registered")
        return

    # Column widths: ID=15, Date=10, Path=40, Tags=remainder
    header = f"{'ID':<15} {'Date':<10} {'Path':<40} {'Tags'}"
    click.echo(header)
    click.echo("-" * len(header))

    for entry in sources.sources:
        tags = ", ".join(entry.workstream_tags) if entry.workstream_tags else ""
        path_display = _truncate(entry.path, 40)
        click.echo(f"{entry.id:<15} {entry.date_received:<10} {path_display:<40} {tags}")

    click.echo(f"\n{count} sources registered")


@sources_cmd.command("show")
@click.argument("source_id")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
def sources_show(source_id, json_mode):
    """Display full record for a single source document."""
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence_dir = _find_diligence_dir(env_cwd)
    sources_path = diligence_dir / "SOURCES.md"
    sources = read_sources(sources_path)

    # Find entry by ID
    entry = None
    for s in sources.sources:
        if s.id == source_id:
            entry = s
            break

    if entry is None:
        click.echo(f"Source '{source_id}' not found.")
        raise SystemExit(1)

    if json_mode:
        output_result(_source_to_dict(entry), json_mode=True)
        return

    # Plain text output: labeled lines for each field
    click.echo(f"ID:            {entry.id}")
    click.echo(f"Path:          {entry.path}")
    click.echo(f"Date received: {entry.date_received}")
    click.echo(f"Parties:       {', '.join(entry.parties) if entry.parties else 'none'}")
    click.echo(f"Workstreams:   {', '.join(entry.workstream_tags) if entry.workstream_tags else 'none'}")
    click.echo(f"Supersedes:    {entry.supersedes or 'none'}")
    click.echo(f"Notes:         {entry.notes or 'none'}")


def _lookup_source(sources: SourcesFile, source_id: str) -> SourceEntry | None:
    """Find a source entry by ID."""
    for s in sources.sources:
        if s.id == source_id:
            return s
    return None


def _is_excel(path: str) -> bool:
    """Check if file path has an Excel extension."""
    lower = path.lower()
    return lower.endswith(".xlsx") or lower.endswith(".xls")


def _is_docx(path: str) -> bool:
    """Check if file path has a Word extension."""
    return path.lower().endswith(".docx")


def _format_excel_compact(diff_result: dict, id_a: str, id_b: str) -> str:
    """Format Excel diff result as compact summary (locked from CONTEXT.md)."""
    sheet_names = ", ".join(diff_result["changed_sheet_names"])
    lines = [
        f"Diff: {id_a} vs {id_b}",
        f"  sheets changed: {diff_result['sheets_changed']} of {diff_result['total_sheets']} ({sheet_names})",
        f"  cells differ:   {diff_result['cells_differ']}",
        f"  rows added:     {diff_result['rows_added']}",
        f"  rows removed:   {diff_result['rows_removed']}",
        f"  named ranges:   +{diff_result['named_ranges_added']}, -{diff_result['named_ranges_removed']}",
    ]
    return "\n".join(lines)


def _format_docx_compact(diff_result: dict, id_a: str, id_b: str) -> str:
    """Format Word diff result as compact summary."""
    lines = [
        f"Diff: {id_a} vs {id_b}",
        f"  paragraphs changed:  {diff_result['paragraphs_changed']}",
        f"  paragraphs added:    {diff_result['paragraphs_added']}",
        f"  paragraphs removed:  {diff_result['paragraphs_removed']}",
    ]
    return "\n".join(lines)


def _format_ingest_auto_diff(diff_result: dict, old_id: str, old_filename: str, new_id: str) -> str:
    """Format auto-diff for ingest output (locked from CONTEXT.md)."""
    sheet_names = ", ".join(diff_result["changed_sheet_names"])
    lines = [
        "",
        f"Diff vs {old_id} ({old_filename}):",
        f"  sheets changed: {diff_result['sheets_changed']} of {diff_result['total_sheets']} ({sheet_names})",
        f"  cells differ:   {diff_result['cells_differ']}",
        f"  rows added:     {diff_result['rows_added']}",
        f"  rows removed:   {diff_result['rows_removed']}",
        f"  named ranges:   +{diff_result['named_ranges_added']}, -{diff_result['named_ranges_removed']}",
        "",
        f"Run `diligent sources diff {old_id} {new_id}` for full detail.",
    ]
    return "\n".join(lines)


@sources_cmd.command("diff")
@click.argument("id_a")
@click.argument("id_b")
@click.option("--verbose", is_flag=True, default=False,
              help="Show detailed paragraph-level diffs for Word documents.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON result.")
def sources_diff(id_a, id_b, verbose, json_mode):
    """Compare two source documents by their IDs."""
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence_dir = _find_diligence_dir(env_cwd)
    deal_root = diligence_dir.parent

    sources_path = diligence_dir / "SOURCES.md"
    sources = read_sources(sources_path)

    # Look up both source entries
    entry_a = _lookup_source(sources, id_a)
    entry_b = _lookup_source(sources, id_b)

    if entry_a is None:
        click.echo(f"Source '{id_a}' not found.")
        raise SystemExit(1)
    if entry_b is None:
        click.echo(f"Source '{id_b}' not found.")
        raise SystemExit(1)

    # Resolve file paths relative to deal root
    path_a = str(deal_root / entry_a.path)
    path_b = str(deal_root / entry_b.path)

    # Determine file type from extension (use file A's extension)
    if _is_excel(entry_a.path):
        from diligent.helpers.diff_excel import diff_excel_summary

        diff_result = diff_excel_summary(path_a, path_b)

        if json_mode:
            output = {"diff_type": "excel", **diff_result}
            click.echo(json_lib.dumps(output, indent=2, default=str))
        else:
            click.echo(_format_excel_compact(diff_result, id_a, id_b))

    elif _is_docx(entry_a.path):
        from diligent.helpers.diff_docx import diff_docx_summary, diff_docx_verbose

        diff_result = diff_docx_summary(path_a, path_b)

        if json_mode:
            output = {"diff_type": "docx", **diff_result}
            click.echo(json_lib.dumps(output, indent=2, default=str))
        elif verbose:
            # Print summary first, then verbose diff
            click.echo(_format_docx_compact(diff_result, id_a, id_b))
            click.echo("")
            diff_lines = diff_docx_verbose(path_a, path_b)
            for line in diff_lines:
                click.echo(line)
        else:
            click.echo(_format_docx_compact(diff_result, id_a, id_b))

    else:
        ext = Path(entry_a.path).suffix
        if json_mode:
            output = {"diff_type": "unsupported", "format": ext}
            click.echo(json_lib.dumps(output, indent=2, default=str))
        else:
            click.echo(f"Diff not supported for {ext} files.")
