"""truth command group: set, get, list, trace, and flag subcommands.

Manage validated facts in TRUTH.md. The verification gate (truth set)
is the load-bearing behavior: when a fact value changes beyond tolerance,
it exits 2 with a compact discrepancy, writes the rejection to QUESTIONS.md,
and requires --confirm to override.
"""

from datetime import date
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.formatting import output_result
from diligent.helpers.numeric import compute_gate_result
from diligent.state.config import read_config
from diligent.state.models import (
    FactEntry,
    QuestionEntry,
    QuestionsFile,
    SourcesFile,
    SupersededValue,
)
from diligent.state.questions import read_questions, write_questions
from diligent.state.sources import read_sources
from diligent.state.truth import read_truth, write_truth


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


def _next_question_id(questions: QuestionsFile) -> str:
    """Derive next Q-{NNN} from max existing question ID.

    Parses existing IDs like Q-001, Q-042, etc. and returns the next
    sequential ID. Starts at Q-001 if no questions exist.
    """
    max_num = 0
    for q in questions.questions:
        if q.id.startswith("Q-"):
            try:
                num = int(q.id[2:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"Q-{max_num + 1:03d}"


def _build_superseded_source_set(sources: SourcesFile) -> set[str]:
    """Build a set of source IDs that have been superseded by another source.

    Walk sources list; for each source with a `supersedes` field, add the
    superseded ID to the set. Used to determine if a fact's source has
    been replaced by a newer ingest.
    """
    superseded: set[str] = set()
    for src in sources.sources:
        if src.supersedes:
            superseded.add(src.supersedes)
    return superseded


def _compute_fact_status(fact: FactEntry, superseded_sources: set[str]) -> str:
    """Determine display status for a fact.

    Returns "flagged" if fact has a flag set, "stale" if the fact's
    source has been superseded, "current" otherwise.
    """
    if fact.flagged is not None:
        return "flagged"
    if fact.source in superseded_sources:
        return "stale"
    return "current"


@click.group("truth")
def truth_cmd():
    """Manage validated facts."""
    pass


@truth_cmd.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--source", required=True, help="Source ID (required).")
@click.option("--workstream", default="", help="Workstream name.")
@click.option("--anchor/--no-anchor", default=None, help="Mark as anchor metric.")
@click.option("--confirm", "confirm_flag", is_flag=True, default=False,
              help="Override verification gate.")
@click.option("--computed-by", default=None, help="Formula or derivation.")
@click.option("--notes", default=None, help="Free-text notes.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def truth_set(ctx, key, value, source, workstream, anchor, confirm_flag,
              computed_by, notes, json_mode):
    """Record or update a validated fact.

    Requires --source citation. If updating an existing fact, the
    verification gate fires when the value changes beyond tolerance.
    Use --confirm to override the gate.
    """
    # Resolve .diligence/ dir
    env_cwd = ctx.color  # Not used; check env var
    import os
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Read config and truth
    config = read_config(diligence / "config.json")
    truth = read_truth(diligence / "TRUTH.md")

    today = date.today().isoformat()
    existing = truth.facts.get(key)

    # --- No-op fast path ---
    if existing is not None and existing.value == value:
        if json_mode:
            output_result({"status": "no_change", "key": key, "value": value}, json_mode=True)
        else:
            click.echo(f"No change: {key} already set to that value.")
        ctx.exit(0)
        return

    # --- Determine anchor status ---
    if anchor is True:
        is_anchor = True
    elif anchor is False:
        is_anchor = False
    elif existing is not None:
        # Sticky: preserve existing anchor state
        is_anchor = existing.anchor
    else:
        is_anchor = False

    # --- Verification gate ---
    if existing is not None:
        gate = compute_gate_result(
            old_value=existing.value,
            new_value=value,
            is_anchor=is_anchor,
            tolerance_pct=config.anchor_tolerance_pct,
        )

        if gate is not None and gate["fired"] and not confirm_flag:
            # Gate fired: print discrepancy, write to QUESTIONS.md, exit 2
            delta_line = ""
            if gate["delta_str"]:
                delta_line = f"  delta:     {gate['delta_str']}\n"

            compact = (
                f"  key:       {key}\n"
                f"  current:   {existing.value} (source: {existing.source}, date: {existing.date})\n"
                f"  proposed:  {value} (source: {source})\n"
                f"{delta_line}"
                f"  verdict:   {gate['verdict']}. Re-run with --confirm to accept."
            )

            if json_mode:
                output_result({
                    "status": "discrepancy",
                    "key": key,
                    "current_value": existing.value,
                    "proposed_value": value,
                    "current_source": existing.source,
                    "proposed_source": source,
                    "delta": gate["delta_str"],
                    "verdict": gate["verdict"],
                }, json_mode=True)
            else:
                click.echo(compact)

            # Write rejection to QUESTIONS.md
            questions = read_questions(diligence / "QUESTIONS.md")
            q_id = _next_question_id(questions)
            delta_desc = f" ({gate['delta_str']})" if gate["delta_str"] else ""
            question_text = (
                f"{key} changed from {existing.value} to {value}{delta_desc}. "
                f"Which value is correct?"
            )
            questions.questions.append(
                QuestionEntry(
                    id=q_id,
                    question=question_text,
                    workstream=existing.workstream or workstream,
                    owner="self",
                    status="open",
                    date_raised=today,
                    context={
                        "type": "gate_rejection",
                        "key": key,
                        "old_value": existing.value,
                        "new_value": value,
                        "old_source": existing.source,
                        "new_source": source,
                        "delta": gate["delta_str"],
                    },
                )
            )
            write_questions(diligence / "QUESTIONS.md", questions)

            ctx.exit(2)
            return

    # --- Build supersedes chain ---
    supersedes = []
    if existing is not None:
        # Push current value to supersedes chain
        supersedes = list(existing.supersedes)  # preserve existing chain
        supersedes.insert(0, SupersededValue(
            value=existing.value,
            source=existing.source,
            date=existing.date,
        ))

    # --- Build new FactEntry ---
    new_fact = FactEntry(
        key=key,
        value=value,
        source=source,
        date=today,
        workstream=workstream if workstream else (existing.workstream if existing else ""),
        supersedes=supersedes,
        computed_by=computed_by,
        notes=notes,
        flagged=existing.flagged if existing else None,
        anchor=is_anchor,
    )

    # Store and write
    truth.facts[key] = new_fact
    write_truth(diligence / "TRUTH.md", truth)

    status = "updated" if existing else "created"

    if json_mode:
        output_result({
            "status": status,
            "key": key,
            "value": value,
            "source": source,
        }, json_mode=True)
    else:
        click.echo(f"Fact {status}: {key} = {value} (source: {source})")
        if status == "updated":
            try:
                from diligent.state.artifacts import read_artifacts
                artifacts = read_artifacts(diligence / "ARTIFACTS.md")
                n = sum(1 for a in artifacts.artifacts if key in a.references)
                if n > 0:
                    click.echo(click.style(
                        f"Note: {n} artifact(s) may now be stale. Run 'diligent reconcile' to check.",
                        dim=True,
                    ))
            except FileNotFoundError:
                pass


@truth_cmd.command("get")
@click.argument("key")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def truth_get(ctx, key, json_mode):
    """Look up a validated fact by key.

    Shows the current value with source citation. Displays anchor and
    flagged status when applicable.
    """
    import os
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    truth = read_truth(diligence / "TRUTH.md")
    fact = truth.facts.get(key)

    if fact is None:
        click.echo(f"Fact '{key}' not found.")
        ctx.exit(1)
        return

    if json_mode:
        output_result({
            "key": fact.key,
            "value": fact.value,
            "source": fact.source,
            "date": fact.date,
            "workstream": fact.workstream,
            "anchor": fact.anchor,
            "flagged": fact.flagged,
            "supersedes_count": len(fact.supersedes),
        }, json_mode=True)
    else:
        line = f"{key}: {fact.value} (source: {fact.source}, date: {fact.date})"
        if fact.flagged:
            reason = fact.flagged.get("reason", "unknown")
            line += f" [FLAGGED: {reason}]"
        if fact.anchor:
            line += " [anchor]"
        click.echo(line)


@truth_cmd.command("list")
@click.option("--stale", "stale_flag", is_flag=True, default=False,
              help="Show only flagged or stale facts.")
@click.option("--workstream", default=None, help="Filter by workstream.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def truth_list(ctx, stale_flag, workstream, json_mode):
    """List all validated facts with status.

    Shows one line per fact with aligned columns: key, value (truncated),
    status (current/flagged/stale), and source ID. Staleness is detected
    by cross-referencing SOURCES.md supersedes chains.
    """
    import os
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    truth = read_truth(diligence / "TRUTH.md")

    # Read sources for staleness detection; empty set if missing/empty
    sources_path = diligence / "SOURCES.md"
    if sources_path.exists():
        sources = read_sources(sources_path)
    else:
        sources = SourcesFile(sources=[])
    superseded = _build_superseded_source_set(sources)

    # Compute status for ALL facts (needed for summary line)
    all_facts = []
    for key in sorted(truth.facts.keys()):
        fact = truth.facts[key]
        status = _compute_fact_status(fact, superseded)
        all_facts.append((key, fact, status))

    # Summary counts (always from ALL facts)
    count_current = sum(1 for _, _, s in all_facts if s == "current")
    count_flagged = sum(1 for _, _, s in all_facts if s == "flagged")
    count_stale = sum(1 for _, _, s in all_facts if s == "stale")
    total = len(all_facts)

    # Apply filters for display
    display_facts = all_facts
    if workstream:
        display_facts = [(k, f, s) for k, f, s in display_facts
                         if f.workstream == workstream]
    if stale_flag:
        display_facts = [(k, f, s) for k, f, s in display_facts
                         if s in ("flagged", "stale")]

    if json_mode:
        result = []
        for key, fact, status in display_facts:
            result.append({
                "key": key,
                "value": fact.value,
                "status": status,
                "source": fact.source,
                "date": fact.date,
                "workstream": fact.workstream,
                "anchor": fact.anchor,
            })
        output_result(result, json_mode=True)
        return

    # Plain text output
    if total == 0:
        click.echo("No facts recorded.")
        click.echo(
            f"\n{total} facts: {count_current} current, "
            f"{count_flagged} flagged, {count_stale} stale"
        )
        return

    # Column widths: key=25, value=30 (truncated with ...), status=8, source=15
    key_w = 25
    val_w = 30
    status_w = 8
    source_w = 15

    for key, fact, status in display_facts:
        # Truncate value to val_w chars
        val = fact.value
        if len(val) > val_w:
            val = val[:val_w - 3] + "..."

        line = (
            f"{key:<{key_w}} {val:<{val_w}} "
            f"{status:<{status_w}} {fact.source:<{source_w}}"
        )
        click.echo(line)

    click.echo(
        f"\n{total} facts: {count_current} current, "
        f"{count_flagged} flagged, {count_stale} stale"
    )


def _resolve_source_path(sources: SourcesFile, source_id: str) -> str:
    """Look up the file path for a source ID from SOURCES.md.

    Returns the path string if found, or the source ID itself if not found.
    """
    for src in sources.sources:
        if src.id == source_id:
            return src.path
    return source_id


@truth_cmd.command("trace")
@click.argument("key")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON timeline.")
@click.option("--verbose", is_flag=True, default=False,
              help="Include inline diff summaries (requires source files).")
@click.pass_context
def truth_trace(ctx, key, json_mode, verbose):
    """Show full revision history for a fact.

    Displays the current value first, then the supersedes chain in
    reverse-chronological order. Source file paths are resolved from
    SOURCES.md. Flag events are interleaved in the timeline.
    """
    import os
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    truth = read_truth(diligence / "TRUTH.md")
    fact = truth.facts.get(key)

    if fact is None:
        click.echo(f"Fact '{key}' not found.")
        ctx.exit(1)
        return

    # Read sources for path resolution
    sources_path = diligence / "SOURCES.md"
    if sources_path.exists():
        sources = read_sources(sources_path)
    else:
        sources = SourcesFile(sources=[])

    # Build timeline: current value first, then supersedes chain
    timeline = []

    # Current value entry
    current_path = _resolve_source_path(sources, fact.source)
    timeline.append({
        "label": "current",
        "value": fact.value,
        "source": fact.source,
        "date": fact.date,
        "path": current_path,
        "type": "value",
    })

    # Flag event (if flagged, insert after current value)
    if fact.flagged is not None:
        timeline.append({
            "label": "flagged",
            "value": fact.flagged.get("reason", ""),
            "source": "",
            "date": fact.flagged.get("date", ""),
            "path": "",
            "type": "flag",
        })

    # Supersedes chain (already reverse-chronological in the model)
    for s in fact.supersedes:
        s_path = _resolve_source_path(sources, s.source)
        timeline.append({
            "label": "",
            "value": s.value,
            "source": s.source,
            "date": s.date,
            "path": s_path,
            "type": "value",
        })

    num_values = 1 + len(fact.supersedes)
    num_supersedes = len(fact.supersedes)

    if json_mode:
        output_result(timeline, json_mode=True)
        return

    # Plain text output
    # Column alignment: label (8), value (15), source (15), date (10), path (remainder)
    label_w = 8
    val_w = 15
    source_w = 15
    date_w = 12

    for entry in timeline:
        if entry["type"] == "flag":
            click.echo(
                f"{'flagged':<{label_w}} {entry['value']:<{val_w}} "
                f"{'':<{source_w}} {entry['date']:<{date_w}}"
            )
        else:
            val = entry["value"]
            if len(val) > val_w:
                val = val[:val_w - 3] + "..."
            path = entry["path"]
            click.echo(
                f"{entry['label']:<{label_w}} {val:<{val_w}} "
                f"{entry['source']:<{source_w}} {entry['date']:<{date_w}} {path}"
            )

    if verbose:
        click.echo("\nVerbose diff summaries require source files.")

    click.echo(
        f"\n{num_values} values, {num_supersedes} supersedes."
    )


@truth_cmd.command("flag")
@click.argument("key")
@click.option("--reason", default=None, help="Reason for flagging.")
@click.option("--clear", "clear_flag", is_flag=True, default=False,
              help="Remove the flag from the fact.")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def truth_flag(ctx, key, reason, clear_flag, json_mode):
    """Flag a fact for review or clear an existing flag.

    Use --reason to flag a fact with a reason. Use --clear to remove
    an existing flag. --reason and --clear are mutually exclusive.
    """
    import os
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Validate mutually exclusive options
    if clear_flag and reason:
        raise click.UsageError("--reason and --clear are mutually exclusive.")
    if not clear_flag and not reason:
        raise click.UsageError("Either --reason or --clear is required.")

    truth = read_truth(diligence / "TRUTH.md")
    fact = truth.facts.get(key)

    if fact is None:
        click.echo(f"Fact '{key}' not found.")
        ctx.exit(1)
        return

    today = date.today().isoformat()

    if clear_flag:
        fact.flagged = None
        truth.facts[key] = fact
        write_truth(diligence / "TRUTH.md", truth)

        if json_mode:
            output_result({
                "status": "cleared",
                "key": key,
                "reason": None,
            }, json_mode=True)
        else:
            click.echo(f"Flag cleared for '{key}'.")
    else:
        fact.flagged = {"reason": reason, "date": today}
        truth.facts[key] = fact
        write_truth(diligence / "TRUTH.md", truth)

        if json_mode:
            output_result({
                "status": "flagged",
                "key": key,
                "reason": reason,
            }, json_mode=True)
        else:
            click.echo(f"Flagged '{key}': {reason}")
