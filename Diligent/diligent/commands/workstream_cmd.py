"""workstream command group: new, list, show subcommands.

Manage deal workstreams. Workstreams are the organizational spine
connecting tasks, questions, facts, and artifacts. Each workstream
gets a subdirectory under .diligence/workstreams/ with CONTEXT.md
and RESEARCH.md files.
"""

import re
from datetime import date
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.formatting import output_result
from diligent.state.models import WorkstreamEntry
from diligent.state.workstreams import read_workstreams, write_workstreams
from diligent.templates import TEMPLATE_DIR, render_template


TEMPLATE_WORKSTREAMS = [
    "financial", "retention", "technical", "legal", "hr", "integration"
]

DESCRIPTIONS = {
    "financial": "Financial analysis and quality of earnings",
    "retention": "Customer retention and commercial diligence",
    "technical": "Technology, product, and engineering assessment",
    "legal": "Legal structure, contracts, and regulatory",
    "hr": "Workforce, compensation, and employment matters",
    "integration": "Post-close integration planning",
}

_WS_NAME_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")


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


def _validate_ws_name(name: str) -> Optional[str]:
    """Validate workstream name. Return error message or None if valid.

    Must be lowercase alphanumeric with internal hyphens only.
    """
    if not name:
        return "Workstream name is required."
    if not _WS_NAME_RE.match(name):
        return (
            f"Invalid workstream name '{name}'. "
            "Must be lowercase alphanumeric with hyphens only "
            "(e.g., 'financial', 'custom-ws')."
        )
    return None


@click.group("workstream")
def workstream_cmd():
    """Manage deal workstreams."""
    pass


@workstream_cmd.command("new")
@click.argument("name")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def workstream_new(ctx, name, json_mode):
    """Create a new workstream with subdirectory and templates.

    NAME must be lowercase alphanumeric with hyphens. If NAME matches
    a pre-defined template (financial, retention, technical, legal, hr,
    integration), a tailored CONTEXT.md is used. Otherwise, a generic
    template is rendered.
    """
    import os as _os
    env_cwd = _os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Validate name
    err = _validate_ws_name(name)
    if err:
        click.echo(f"ERROR: {err}")
        ctx.exit(1)
        return

    # Read existing workstreams
    ws_file = read_workstreams(diligence / "WORKSTREAMS.md")
    existing_names = {w.name for w in ws_file.workstreams}

    # Check for duplicate
    if name in existing_names:
        click.echo(f"ERROR: Workstream '{name}' already exists.")
        ctx.exit(1)
        return

    # Create workstream directory
    ws_dir = diligence / "workstreams" / name
    ws_dir.mkdir(parents=True, exist_ok=True)

    # Write CONTEXT.md
    if name in TEMPLATE_WORKSTREAMS:
        # Tailored template
        template_path = TEMPLATE_DIR / "workstreams" / f"{name}.md"
        context_content = template_path.read_text(encoding="utf-8")
    else:
        # Generic template
        context_content = render_template(
            "ws_context.md.tmpl", {"WORKSTREAM_NAME": name}
        )
    (ws_dir / "CONTEXT.md").write_text(context_content, encoding="utf-8")

    # Write RESEARCH.md
    research_content = render_template(
        "ws_research.md.tmpl", {"WORKSTREAM_NAME": name}
    )
    (ws_dir / "RESEARCH.md").write_text(research_content, encoding="utf-8")

    # Append WorkstreamEntry
    today = date.today().isoformat()
    description = DESCRIPTIONS.get(name, "")
    new_entry = WorkstreamEntry(
        name=name,
        status="active",
        description=description,
        created=today,
    )
    ws_file.workstreams.append(new_entry)
    write_workstreams(diligence / "WORKSTREAMS.md", ws_file)

    # Output
    files_created = ["CONTEXT.md", "RESEARCH.md"]
    if json_mode:
        output_result({
            "name": name,
            "path": str(ws_dir),
            "files_created": files_created,
            "status": "active",
            "description": description,
        }, json_mode=True)
    else:
        click.echo(f"Created workstream '{name}' at {ws_dir}")
        for f in files_created:
            click.echo(f"  {f}")


@workstream_cmd.command("list")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def workstream_list(ctx, json_mode):
    """List all workstreams with status and counts.

    Shows one line per workstream with name, status, task count,
    and question count. Summary line at the bottom.
    """
    import os as _os
    env_cwd = _os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    ws_file = read_workstreams(diligence / "WORKSTREAMS.md")

    if not ws_file.workstreams:
        if json_mode:
            output_result([], json_mode=True)
        else:
            click.echo("No workstreams found.")
        return

    # Lazy-import to avoid startup cost
    from diligent.state.questions import read_questions

    # Read questions for count
    questions_path = diligence / "QUESTIONS.md"
    if questions_path.exists():
        qf = read_questions(questions_path)
    else:
        from diligent.state.models import QuestionsFile
        qf = QuestionsFile()

    # Build data for each workstream
    rows = []
    for ws in ws_file.workstreams:
        # Count tasks by scanning workstream tasks directory
        tasks_dir = diligence / "workstreams" / ws.name / "tasks"
        task_count = 0
        if tasks_dir.exists():
            task_count = sum(
                1 for child in tasks_dir.iterdir() if child.is_dir()
            )

        # Count questions scoped to this workstream
        question_count = sum(
            1 for q in qf.questions if q.workstream == ws.name
        )

        rows.append({
            "name": ws.name,
            "status": ws.status,
            "tasks": task_count,
            "questions": question_count,
        })

    if json_mode:
        output_result(rows, json_mode=True)
        return

    # Plain text: aligned columns
    name_w = 20
    status_w = 10
    tasks_w = 6
    questions_w = 10

    header = (
        f"{'NAME':<{name_w}} {'STATUS':<{status_w}} "
        f"{'TASKS':<{tasks_w}} {'QUESTIONS':<{questions_w}}"
    )
    click.echo(header)

    for row in rows:
        name_str = row["name"]
        if len(name_str) > name_w:
            name_str = name_str[:name_w - 3] + "..."
        click.echo(
            f"{name_str:<{name_w}} {row['status']:<{status_w}} "
            f"{row['tasks']:<{tasks_w}} {row['questions']:<{questions_w}}"
        )

    click.echo(f"\n{len(rows)} workstreams")


@workstream_cmd.command("show")
@click.argument("name")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def workstream_show(ctx, name, json_mode):
    """Display detailed workstream information.

    Aggregates stats from WORKSTREAMS.md, QUESTIONS.md, TRUTH.md,
    ARTIFACTS.md, and task directories. Shows description, status,
    task counts, question count, fact count, and artifact count.
    """
    import os as _os
    env_cwd = _os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    ws_file = read_workstreams(diligence / "WORKSTREAMS.md")
    entry = None
    for w in ws_file.workstreams:
        if w.name == name:
            entry = w
            break

    if entry is None:
        click.echo(f"ERROR: Workstream '{name}' not found.")
        ctx.exit(1)
        return

    # Count tasks
    tasks_dir = diligence / "workstreams" / name / "tasks"
    tasks_open = 0
    tasks_complete = 0
    if tasks_dir.exists():
        import yaml
        for child in tasks_dir.iterdir():
            if child.is_dir():
                status_file = child / "status.yaml"
                if status_file.exists():
                    try:
                        data = yaml.safe_load(
                            status_file.read_text(encoding="utf-8")
                        )
                        if isinstance(data, dict) and data.get("status") == "complete":
                            tasks_complete += 1
                        else:
                            tasks_open += 1
                    except Exception:
                        tasks_open += 1
                else:
                    tasks_open += 1

    # Lazy-import state readers
    from diligent.state.questions import read_questions
    from diligent.state.truth import read_truth
    from diligent.state.artifacts import read_artifacts

    # Count questions
    questions_path = diligence / "QUESTIONS.md"
    question_count = 0
    if questions_path.exists():
        qf = read_questions(questions_path)
        question_count = sum(
            1 for q in qf.questions
            if q.workstream == name and q.status == "open"
        )

    # Count facts
    truth_path = diligence / "TRUTH.md"
    fact_count = 0
    if truth_path.exists():
        tf = read_truth(truth_path)
        fact_count = sum(
            1 for f in tf.facts.values() if f.workstream == name
        )

    # Count artifacts
    artifacts_path = diligence / "ARTIFACTS.md"
    artifact_count = 0
    artifact_stale = 0
    if artifacts_path.exists():
        af = read_artifacts(artifacts_path)
        for a in af.artifacts:
            if a.workstream == name:
                artifact_count += 1
                # Basic staleness: check if any referenced fact has been
                # updated after artifact last_refreshed
                if truth_path.exists():
                    for ref_key in a.references:
                        fact = tf.facts.get(ref_key)
                        if fact and fact.date > a.last_refreshed:
                            artifact_stale += 1
                            break

    if json_mode:
        output_result({
            "name": entry.name,
            "status": entry.status,
            "description": entry.description,
            "created": entry.created,
            "tasks_open": tasks_open,
            "tasks_complete": tasks_complete,
            "questions": question_count,
            "facts": fact_count,
            "artifacts": artifact_count,
            "artifacts_stale": artifact_stale,
        }, json_mode=True)
        return

    # Plain text output
    click.echo(f"Workstream: {entry.name}")
    if entry.description:
        click.echo(f"Description: {entry.description}")
    click.echo(f"Status: {entry.status}")
    if entry.created:
        click.echo(f"Created: {entry.created}")
    click.echo(f"Tasks: {tasks_open} open / {tasks_complete} complete")
    click.echo(f"Questions: {question_count} open")
    click.echo(f"Facts: {fact_count}")
    click.echo(f"Artifacts: {artifact_count} ({artifact_stale} stale)")
