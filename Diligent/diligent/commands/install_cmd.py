"""install command: deploy skill files to AI IDE directories.

Writes parameterized skill templates to the target IDE's skills
directory. Each template has {{DILIGENT_PATH}} replaced with the
actual CLI binary path resolved via shutil.which.

This is a global command -- no deal directory or DILIGENT_CWD needed.
"""

import json
import shutil
from pathlib import Path

import click

from diligent.skills import SKILLS_DIR


@click.command("install")
@click.option(
    "--claude-code",
    is_flag=True,
    default=False,
    help="Install to Claude Code skills directory (~/.claude/skills/).",
)
@click.option(
    "--antigravity",
    is_flag=True,
    default=False,
    help="Install to Antigravity skills directory (~/.agents/skills/).",
)
@click.option(
    "--path",
    "custom_path",
    default=None,
    type=click.Path(),
    help="Custom install directory.",
)
@click.option(
    "--uninstall",
    is_flag=True,
    default=False,
    help="Remove installed skill files.",
)
@click.option(
    "--json",
    "json_mode",
    is_flag=True,
    default=False,
    help="Output as JSON.",
)
def install_cmd(claude_code, antigravity, custom_path, uninstall, json_mode):
    """Install or remove diligent skill files for AI agents."""
    # Resolve target directory
    target_dir = _resolve_target(claude_code, antigravity, custom_path)

    if not target_dir.is_dir():
        raise click.ClickException(f"Directory does not exist: {target_dir}")

    if uninstall:
        _uninstall_skills(target_dir, json_mode)
    else:
        _install_skills(target_dir, json_mode)


def _resolve_target(claude_code, antigravity, custom_path):
    """Resolve the target directory from flags.

    Priority: --path > --claude-code > --antigravity.
    """
    if custom_path:
        return Path(custom_path)
    if claude_code:
        return Path.home() / ".claude" / "skills"
    if antigravity:
        return Path.home() / ".agents" / "skills"
    raise click.ClickException(
        "Specify --claude-code, --antigravity, or --path"
    )


def _install_skills(target_dir, json_mode):
    """Read skill templates, parameterize, and write to target."""
    diligent_path = shutil.which("diligent")
    if diligent_path is None:
        click.echo(
            "WARNING: Could not find diligent binary in PATH; "
            "using 'diligent' as default."
        )
        diligent_path = "diligent"

    templates = sorted(SKILLS_DIR.glob("dd_*.md"))
    count = 0
    files_written = []

    for tmpl in templates:
        content = tmpl.read_text(encoding="utf-8")
        content = content.replace("{{DILIGENT_PATH}}", diligent_path)
        dest = target_dir / tmpl.name
        dest.write_text(content, encoding="utf-8")
        files_written.append(tmpl.name)
        count += 1

    if json_mode:
        click.echo(json.dumps({
            "action": "install",
            "count": count,
            "target_dir": str(target_dir),
            "files": files_written,
            "diligent_path": diligent_path,
        }, indent=2))
    else:
        click.echo(f"Installed {count} skill files to {target_dir}")


def _uninstall_skills(target_dir, json_mode):
    """Remove dd_*.md files from target directory."""
    files = sorted(target_dir.glob("dd_*.md"))

    if not files:
        if json_mode:
            click.echo(json.dumps({
                "action": "uninstall",
                "removed": 0,
                "target_dir": str(target_dir),
                "files": [],
            }, indent=2))
        else:
            click.echo(f"No skill files found in {target_dir}")
        return

    removed = []
    for f in files:
        f.unlink()
        removed.append(f.name)

    if json_mode:
        click.echo(json.dumps({
            "action": "uninstall",
            "removed": len(removed),
            "target_dir": str(target_dir),
            "files": removed,
        }, indent=2))
    else:
        click.echo(f"Removed {len(removed)} skill files from {target_dir}")
