"""task command group: new, list, complete subcommands.

Directory-based task management within workstreams. Each task gets
a numbered directory (NNN-slug/) containing SUMMARY.md, PLAN.md,
VERIFICATION.md, and status.yaml.
"""

import os
import re
from datetime import date
from pathlib import Path
from typing import Optional

import click
import yaml

from diligent.helpers.formatting import output_result
from diligent.templates import render_template


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


def _slugify(text: str, max_length: int = 40) -> str:
    """Generate a URL-safe slug from text.

    Lowercase, replace non-alphanumeric with hyphens, strip leading/trailing
    hyphens, truncate at max_length without trailing hyphen.
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug


def _next_task_id(tasks_dir: Path) -> int:
    """Determine next task ID by scanning existing directories.

    Returns the next monotonic integer (max existing + 1, or 1 if none).
    """
    max_num = 0
    if tasks_dir.exists():
        pattern = re.compile(r"^(\d{3})-")
        for child in tasks_dir.iterdir():
            if child.is_dir():
                m = pattern.match(child.name)
                if m:
                    num = int(m.group(1))
                    if num > max_num:
                        max_num = num
    return max_num + 1


def _read_tasks(tasks_dir: Path) -> list:
    """Read all task directories and return list of task dicts.

    Scans for NNN-* directories, reads status.yaml from each.
    Returns sorted list of dicts with id, dir_name, description,
    status, created, path.
    """
    tasks = []
    if not tasks_dir.exists():
        return tasks
    pattern = re.compile(r"^(\d{3})-")
    for child in sorted(tasks_dir.iterdir()):
        if child.is_dir() and pattern.match(child.name):
            status_file = child / "status.yaml"
            if status_file.exists():
                data = yaml.safe_load(status_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    tasks.append({
                        "id": child.name[:3],
                        "dir_name": child.name,
                        "description": data.get("description", ""),
                        "status": data.get("status", "open"),
                        "created": data.get("created", ""),
                        "path": str(child),
                    })
    return tasks


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments from text."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


@click.group("task")
def task_cmd():
    """Manage workstream tasks."""
    pass


@task_cmd.command("new")
@click.argument("workstream")
@click.argument("description")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def task_new(ctx, workstream, description, json_mode):
    """Create a new task in a workstream.

    Creates a numbered directory under the workstream's tasks/ folder
    with SUMMARY.md, PLAN.md, VERIFICATION.md, and status.yaml.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Validate workstream directory exists
    ws_dir = diligence / "workstreams" / workstream
    if not ws_dir.is_dir():
        click.echo(f"ERROR: Workstream '{workstream}' not found.")
        ctx.exit(1)
        return

    # Create tasks subdirectory
    tasks_dir = ws_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    # Get next ID and generate slug
    next_id = _next_task_id(tasks_dir)
    slug = _slugify(description)
    task_id = f"{next_id:03d}"
    dir_name = f"{task_id}-{slug}"
    task_dir = tasks_dir / dir_name
    task_dir.mkdir()

    # Render and write scaffold files
    today_iso = date.today().isoformat()
    template_context = {"TASK_DESC": description, "ISO_DATE": today_iso}

    (task_dir / "SUMMARY.md").write_text(
        render_template("task_summary.md.tmpl", template_context),
        encoding="utf-8",
    )
    (task_dir / "PLAN.md").write_text(
        render_template("task_plan.md.tmpl", template_context),
        encoding="utf-8",
    )
    (task_dir / "VERIFICATION.md").write_text(
        render_template("task_verification.md.tmpl", template_context),
        encoding="utf-8",
    )
    (task_dir / "status.yaml").write_text(
        render_template("task_status.yaml.tmpl", template_context),
        encoding="utf-8",
    )

    # Output
    if json_mode:
        output_result({
            "task_id": task_id,
            "path": str(task_dir),
            "workstream": workstream,
            "description": description,
            "status": "open",
            "created": today_iso,
        }, json_mode=True)
    else:
        click.echo(f"Created task {task_id} in {workstream}: {description}")
        click.echo(f"  {task_dir}")


@task_cmd.command("list")
@click.argument("workstream")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def task_list(ctx, workstream, json_mode):
    """List tasks in a workstream.

    Shows one line per task with ID, description, and status.
    Summary line shows open/complete counts.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Validate workstream directory exists
    ws_dir = diligence / "workstreams" / workstream
    if not ws_dir.is_dir():
        click.echo(f"ERROR: Workstream '{workstream}' not found.")
        ctx.exit(1)
        return

    tasks_dir = ws_dir / "tasks"
    tasks = _read_tasks(tasks_dir)

    if not tasks:
        if json_mode:
            output_result([], json_mode=True)
        else:
            click.echo(f"No tasks found in {workstream}")
        return

    if json_mode:
        output_result(tasks, json_mode=True)
        return

    # Plain text: aligned columns
    id_w = 5
    desc_w = 40
    status_w = 10

    header = f"{'ID':<{id_w}} {'DESCRIPTION':<{desc_w}} {'STATUS':<{status_w}}"
    click.echo(header)

    for task in tasks:
        desc = task["description"]
        if len(desc) > desc_w:
            desc = desc[:desc_w - 3] + "..."
        click.echo(f"{task['id']:<{id_w}} {desc:<{desc_w}} {task['status']:<{status_w}}")

    complete = sum(1 for t in tasks if t["status"] == "complete")
    open_count = len(tasks) - complete
    click.echo(f"\n{len(tasks)} tasks: {complete} complete, {open_count} open")


@task_cmd.command("complete")
@click.argument("workstream")
@click.argument("task_id")
@click.option("--json", "json_mode", is_flag=True, default=False,
              help="Output structured JSON.")
@click.pass_context
def task_complete(ctx, workstream, task_id, json_mode):
    """Mark a task as complete.

    Validates that SUMMARY.md has real content (not just template
    HTML comments) before allowing completion. The task_id argument
    is the 3-digit number (e.g., '001').
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    # Validate workstream directory exists
    ws_dir = diligence / "workstreams" / workstream
    if not ws_dir.is_dir():
        click.echo(f"ERROR: Workstream '{workstream}' not found.")
        ctx.exit(1)
        return

    # Locate task directory by scanning for matching prefix
    tasks_dir = ws_dir / "tasks"
    task_dir = None
    if tasks_dir.exists():
        for child in tasks_dir.iterdir():
            if child.is_dir() and child.name.startswith(f"{task_id}-"):
                task_dir = child
                break

    if task_dir is None:
        click.echo(f"ERROR: Task {task_id} not found in {workstream}.")
        ctx.exit(1)
        return

    # Read status.yaml
    status_file = task_dir / "status.yaml"
    data = yaml.safe_load(status_file.read_text(encoding="utf-8"))

    # Check if already complete
    if isinstance(data, dict) and data.get("status") == "complete":
        click.echo(f"ERROR: Task {task_id} is already complete.")
        ctx.exit(1)
        return

    # Validate SUMMARY.md has real content
    summary_path = task_dir / "SUMMARY.md"
    if summary_path.exists():
        raw = summary_path.read_text(encoding="utf-8")
    else:
        raw = ""

    # Strip HTML comments, markdown headings (# lines), and whitespace
    stripped = _strip_html_comments(raw)
    # Also strip lines that are just markdown headings
    lines = stripped.splitlines()
    content_lines = [
        line for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]
    if not content_lines:
        click.echo(
            f"ERROR: Write SUMMARY.md before completing task {task_id}."
        )
        ctx.exit(1)
        return

    # Update status.yaml to complete
    data["status"] = "complete"
    status_file.write_text(
        yaml.safe_dump(data, default_flow_style=False),
        encoding="utf-8",
    )

    # Output
    if json_mode:
        output_result({
            "task_id": task_id,
            "workstream": workstream,
            "description": data.get("description", ""),
            "status": "complete",
        }, json_mode=True)
    else:
        click.echo(f"Completed task {task_id} in {workstream}.")
        click.echo(click.style(
            f"Next: run 'diligent reconcile --workstream {workstream}' to verify task outputs.",
            dim=True,
        ))
