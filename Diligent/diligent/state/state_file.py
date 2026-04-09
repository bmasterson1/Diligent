"""STATE.md reader/writer.

YAML frontmatter with created and last_modified fields.
Uses python-frontmatter for parsing.
"""

from pathlib import Path

import frontmatter

from diligent.helpers.io import atomic_write
from diligent.state.models import StateFile


def read_state(path: Path) -> StateFile:
    """Read STATE.md into a StateFile dataclass."""
    post = frontmatter.load(str(path))
    meta = post.metadata

    return StateFile(
        created=str(meta.get("created", "")),
        last_modified=str(meta.get("last_modified", "")),
    )


def write_state(path: Path, state: StateFile) -> None:
    """Write a StateFile to STATE.md using atomic_write.

    Currently used only for round-trip fidelity testing. Not wired into
    v1 mutation commands because STATE.md is an init-time artifact in v1.
    Available for future use (e.g., diligent migrate, activity tracking).

    Preserves the markdown body (H1 + comment block) if the file
    already exists. Otherwise writes a default body.
    """
    # If file exists, preserve the body content
    body = "# State\n\n<!-- This file is maintained by diligent commands. Manual edits are\n     supported but not required. -->"
    if path.exists():
        existing = frontmatter.load(str(path))
        if existing.content.strip():
            body = existing.content.strip()

    post = frontmatter.Post(content=body)
    post.metadata["created"] = state.created
    post.metadata["last_modified"] = state.last_modified

    content = frontmatter.dumps(post) + "\n"

    def validate(c: str) -> bool:
        """Re-parse and verify key fields survived."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_state(tmp)
            return (
                reread.created == state.created
                and reread.last_modified == state.last_modified
            )
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
