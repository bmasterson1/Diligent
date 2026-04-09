"""diligent status command: morning-coffee deal state summary.

Displays 5 sections: deal header, workstreams, stale artifacts,
open questions, and recent activity. Supports --json and --verbose flags.
"""

import json
import os
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

import click


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


def _build_deal_header(diligence: Path) -> dict:
    """Build the deal header section data."""
    from diligent.state.deal import read_deal
    from diligent.state.state_file import read_state

    deal = read_deal(diligence / "DEAL.md")
    state = read_state(diligence / "STATE.md")

    today = date.today()

    # Compute days counter
    if deal.deal_stage == "pre-LOI" or not deal.loi_date:
        # Pre-LOI: days since tracking started
        try:
            created_date = date.fromisoformat(state.created[:10])
            days = (today - created_date).days
        except (ValueError, TypeError):
            days = 0
        days_label = f"{days} days tracking"
    else:
        # Post-LOI: days since LOI
        try:
            loi_date = date.fromisoformat(deal.loi_date[:10])
            days = (today - loi_date).days
        except (ValueError, TypeError):
            days = 0
        days_label = f"{days} days in diligence"

    return {
        "deal_code": deal.deal_code,
        "target_legal_name": deal.target_legal_name,
        "target_common_name": deal.target_common_name,
        "deal_stage": deal.deal_stage,
        "loi_date": deal.loi_date,
        "days": days,
        "days_label": days_label,
    }


def _build_workstreams(diligence: Path, stale_by_ws: dict) -> list[dict]:
    """Build workstreams section data."""
    from diligent.state.artifacts import read_artifacts
    from diligent.state.questions import read_questions
    from diligent.state.truth import read_truth
    from diligent.state.workstreams import read_workstreams

    ws_file = read_workstreams(diligence / "WORKSTREAMS.md")

    # Read truth for fact counts
    truth_path = diligence / "TRUTH.md"
    facts = {}
    if truth_path.exists():
        tf = read_truth(truth_path)
        facts = tf.facts

    # Read questions for question counts
    questions_path = diligence / "QUESTIONS.md"
    questions = []
    if questions_path.exists():
        qf = read_questions(questions_path)
        questions = qf.questions

    # Read artifacts for artifact counts
    artifacts_path = diligence / "ARTIFACTS.md"
    artifacts = []
    if artifacts_path.exists():
        af = read_artifacts(artifacts_path)
        artifacts = af.artifacts

    rows = []
    for ws in ws_file.workstreams:
        fact_count = sum(1 for f in facts.values() if f.workstream == ws.name)
        question_count = sum(
            1 for q in questions
            if q.workstream == ws.name and q.status == "open"
        )
        artifact_count = sum(
            1 for a in artifacts if a.workstream == ws.name
        )
        stale_count = stale_by_ws.get(ws.name, 0)

        rows.append({
            "name": ws.name,
            "facts": fact_count,
            "questions": question_count,
            "artifacts": artifact_count,
            "stale": stale_count,
        })

    return rows


def _compute_stale_artifacts(diligence: Path) -> list[dict]:
    """Compute stale artifacts using the reconcile engine."""
    from diligent.helpers.reconcile_anchors import compute_staleness
    from diligent.state.artifacts import read_artifacts
    from diligent.state.sources import read_sources
    from diligent.state.truth import read_truth

    artifacts_path = diligence / "ARTIFACTS.md"
    truth_path = diligence / "TRUTH.md"
    sources_path = diligence / "SOURCES.md"

    if not artifacts_path.exists() or not truth_path.exists():
        return []

    af = read_artifacts(artifacts_path)
    tf = read_truth(truth_path)

    sources = []
    if sources_path.exists():
        sf = read_sources(sources_path)
        sources = sf.sources

    stale_results = compute_staleness(af.artifacts, tf.facts, sources)

    stale_list = []
    for sa in stale_results:
        if not sa.is_stale:
            continue

        total_changed = len(sa.value_changed) + len(sa.source_superseded)

        # Compute max days stale across all info entries
        all_info = sa.value_changed + sa.source_superseded
        max_days = max((info.days_stale for info in all_info), default=0)

        stale_list.append({
            "path": sa.path,
            "workstream": sa.workstream,
            "facts_changed": total_changed,
            "days_since_refresh": max_days,
        })

    return stale_list


def _build_open_questions(diligence: Path) -> list[dict]:
    """Build open questions section data."""
    from diligent.state.questions import read_questions

    questions_path = diligence / "QUESTIONS.md"
    if not questions_path.exists():
        return []

    qf = read_questions(questions_path)
    open_qs = [q for q in qf.questions if q.status == "open"]

    rows = []
    for q in open_qs:
        origin = "[gate]" if q.context is not None else "[manual]"
        text = q.question
        if len(text) > 60:
            text = text[:57] + "..."

        rows.append({
            "id": q.id,
            "origin": origin,
            "workstream": q.workstream,
            "question": text,
        })

    return rows


def _build_recent_activity(diligence: Path, window_days: int = 14) -> list[dict]:
    """Build recent activity section from timestamps across state files."""
    from diligent.helpers.time_utils import is_recent

    today = date.today()
    cutoff = today - timedelta(days=window_days)
    events: list[dict] = []

    # Facts: use fact.date
    truth_path = diligence / "TRUTH.md"
    if truth_path.exists():
        from diligent.state.truth import read_truth
        tf = read_truth(truth_path)
        for key, fact in tf.facts.items():
            if is_recent(fact.date, cutoff):
                days = (today - date.fromisoformat(fact.date[:10])).days
                events.append({
                    "date": fact.date,
                    "days_ago": days,
                    "text": f"set fact '{key}'",
                })

    # Sources: use src.date_received
    sources_path = diligence / "SOURCES.md"
    if sources_path.exists():
        from diligent.state.sources import read_sources
        sf = read_sources(sources_path)
        for src in sf.sources:
            if is_recent(src.date_received, cutoff):
                days = (today - date.fromisoformat(src.date_received[:10])).days
                events.append({
                    "date": src.date_received,
                    "days_ago": days,
                    "text": f"ingested {src.id}",
                })

    # Artifacts: registered and refreshed
    artifacts_path = diligence / "ARTIFACTS.md"
    if artifacts_path.exists():
        from diligent.state.artifacts import read_artifacts
        af = read_artifacts(artifacts_path)
        for a in af.artifacts:
            if is_recent(a.registered, cutoff):
                days = (today - date.fromisoformat(a.registered[:10])).days
                events.append({
                    "date": a.registered,
                    "days_ago": days,
                    "text": f"registered {a.path}",
                })
            if a.last_refreshed != a.registered and is_recent(a.last_refreshed, cutoff):
                days = (today - date.fromisoformat(a.last_refreshed[:10])).days
                events.append({
                    "date": a.last_refreshed,
                    "days_ago": days,
                    "text": f"refreshed {a.path}",
                })

    # Questions: raised and answered
    questions_path = diligence / "QUESTIONS.md"
    if questions_path.exists():
        from diligent.state.questions import read_questions
        qf = read_questions(questions_path)
        for q in qf.questions:
            if is_recent(q.date_raised, cutoff):
                days = (today - date.fromisoformat(q.date_raised[:10])).days
                events.append({
                    "date": q.date_raised,
                    "days_ago": days,
                    "text": f"raised {q.id}",
                })
            if q.date_answered and is_recent(q.date_answered, cutoff):
                days = (today - date.fromisoformat(q.date_answered[:10])).days
                events.append({
                    "date": q.date_answered,
                    "days_ago": days,
                    "text": f"answered {q.id}",
                })

    # Sort by date descending
    events.sort(key=lambda e: e["date"], reverse=True)

    return events


def _count_flagged_facts(diligence: Path) -> int:
    """Count flagged facts for the attention counter."""
    truth_path = diligence / "TRUTH.md"
    if not truth_path.exists():
        return 0

    from diligent.state.truth import read_truth
    tf = read_truth(truth_path)
    return sum(1 for f in tf.facts.values() if f.flagged is not None)


def _render_section(title: str, items: list, formatter, verbose: bool, cap: int = 5) -> list[str]:
    """Render a capped section with optional truncation.

    Args:
        title: Section heading text.
        items: List of data items.
        formatter: Callable that takes an item and returns a string line.
        verbose: If True, show all items.
        cap: Maximum items in non-verbose mode.

    Returns:
        List of output lines.
    """
    lines = [f"\n{title}"]

    if not items:
        lines.append("  None")
        return lines

    display_items = items if verbose else items[:cap]
    for item in display_items:
        lines.append(formatter(item))

    if not verbose and len(items) > cap:
        remaining = len(items) - cap
        lines.append(f"  and {remaining} more...")

    return lines


@click.command("status")
@click.option("--verbose", is_flag=True, default=False, help="Show all items without truncation.")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output structured JSON.")
@click.pass_context
def status_cmd(ctx, verbose, json_mode):
    """Display a full deal state summary.

    Shows 5 sections: deal header, workstreams, stale artifacts,
    open questions, and recent activity. Summary line at bottom
    counts items needing attention.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Build all section data
    header = _build_deal_header(diligence)
    stale_artifacts = _compute_stale_artifacts(diligence)

    # Build workstream stale counts for inline display
    stale_by_ws: dict[str, int] = {}
    for sa in stale_artifacts:
        ws = sa["workstream"]
        stale_by_ws[ws] = stale_by_ws.get(ws, 0) + 1

    workstreams = _build_workstreams(diligence, stale_by_ws)
    open_questions = _build_open_questions(diligence)

    # Read config for recent_window_days (not hardcoded 14)
    config_path = diligence / "config.json"
    if config_path.exists():
        from diligent.state.config import read_config
        config = read_config(config_path)
        window_days = config.recent_window_days
    else:
        window_days = 14

    recent_activity = _build_recent_activity(diligence, window_days=window_days)
    flagged_count = _count_flagged_facts(diligence)

    # Attention count: stale artifacts + open questions + flagged facts
    attention_count = len(stale_artifacts) + len(open_questions) + flagged_count

    # JSON mode
    if json_mode:
        data = {
            "deal": header,
            "workstreams": workstreams,
            "stale_artifacts": stale_artifacts,
            "open_questions": open_questions,
            "recent_activity": recent_activity,
            "attention_count": attention_count,
        }
        click.echo(json.dumps(data, indent=2, default=str))
        return

    # Plain text output
    lines: list[str] = []

    # Section 1: Deal header
    lines.append(f"{header['deal_code']} -- {header['target_common_name']} ({header['target_legal_name']})")
    if header["deal_stage"] == "pre-LOI" or not header["loi_date"]:
        lines.append(f"Stage: {header['deal_stage']} | {header['days_label']}")
    else:
        lines.append(f"Stage: {header['deal_stage']} | LOI: {header['loi_date']} | {header['days_label']}")

    # Section 2: Workstreams
    def fmt_ws(ws):
        return (
            f"  {ws['name']:<20} {ws['facts']} facts, {ws['questions']} questions, "
            f"{ws['artifacts']} artifacts, {ws['stale']} stale"
        )
    lines.extend(_render_section("Workstreams", workstreams, fmt_ws, verbose))

    # Section 3: Stale Artifacts
    def fmt_stale(sa):
        return f"  {sa['path']}: {sa['facts_changed']} facts changed, {sa['days_since_refresh']}d since refresh"
    lines.extend(_render_section("Stale Artifacts", stale_artifacts, fmt_stale, verbose))

    # Section 4: Open Questions
    def fmt_question(q):
        return f"  {q['id']} {q['origin']} {q['workstream']:<12} {q['question']}"
    lines.extend(_render_section("Open Questions", open_questions, fmt_question, verbose))

    # Section 5: Recent Activity
    from diligent.helpers.time_utils import relative_time_str

    def fmt_activity(evt):
        rel = relative_time_str(evt["days_ago"])
        return f"  {rel:<8} {evt['text']}"
    lines.extend(_render_section("Recent Activity", recent_activity, fmt_activity, verbose))

    # Summary line
    if attention_count == 0:
        lines.append("\nNo items need attention")
    else:
        lines.append(f"\n{attention_count} items need attention")

    click.echo("\n".join(lines))
