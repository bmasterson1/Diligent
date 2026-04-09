"""Editor invocation for thesis input with fallback chain.

Opens $EDITOR with a git-style template for the analyst to write
their investment thesis. Falls back through platform-appropriate
editors, ending with a multi-line CLI input if no editor is found.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import click


THESIS_TEMPLATE = """\
# Write your investment thesis below.
# Lines starting with # will be stripped.
# Save and close the editor when done.
#
# What is the deal rationale? Why is this target worth pursuing?
# What makes the business defensible? What are the key risks?

"""


def get_editor() -> str | None:
    """Return editor command from env or platform default.

    Fallback chain: $EDITOR > $VISUAL > notepad (win32) > nano (linux) > vi (darwin).
    Returns None only if no editor can be found (unlikely on any standard OS).
    """
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        return editor
    if sys.platform == "win32":
        return "notepad"
    if sys.platform == "darwin":
        return "vi"
    # Linux / other Unix
    return "nano"


def collect_thesis() -> str:
    """Open editor for thesis input, return cleaned text.

    If no editor is available, falls back to multi-line CLI input
    (type END on its own line to finish).
    """
    editor = get_editor()

    if editor is None:
        return _collect_thesis_cli()

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(THESIS_TEMPLATE)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        text = Path(tmp_path).read_text(encoding="utf-8")
        # Strip comment lines
        lines = [ln for ln in text.split("\n") if not ln.startswith("#")]
        return "\n".join(lines).strip()
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def _collect_thesis_cli() -> str:
    """Fallback: collect thesis via multi-line CLI input."""
    click.echo("Enter your investment thesis (type END on its own line to finish):")
    lines = []
    while True:
        line = click.prompt("", default="", show_default=False, prompt_suffix="")
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines).strip()
