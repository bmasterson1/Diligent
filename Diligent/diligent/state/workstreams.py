"""WORKSTREAMS.md reader/writer.

H2 per workstream, YAML block with name and status.
"""

import re
from pathlib import Path
from typing import Optional

import yaml

from diligent.helpers.io import atomic_write
from diligent.state.models import WorkstreamEntry, WorkstreamsFile


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments from markdown text."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _extract_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into list of (H2 heading, section content) tuples."""
    clean = _strip_html_comments(text)
    sections: list[tuple[str, str]] = []
    current_heading: Optional[str] = None
    current_lines: list[str] = []

    for line in clean.split("\n"):
        if line.startswith("## "):
            if current_heading is not None:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    return sections


def _parse_fenced_yaml(section_text: str) -> Optional[dict]:
    """Extract and parse the first fenced YAML block from section text."""
    lines = section_text.split("\n")
    in_block = False
    yaml_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not in_block and (stripped == "```yaml" or stripped == "```yml"):
            in_block = True
            yaml_lines = []
        elif in_block and stripped == "```":
            in_block = False
            break
        elif in_block:
            yaml_lines.append(line)

    if not yaml_lines:
        return None

    yaml_text = "\n".join(yaml_lines)
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None

    if not isinstance(data, dict):
        return None

    return data


def read_workstreams(path: Path) -> WorkstreamsFile:
    """Read WORKSTREAMS.md into a WorkstreamsFile dataclass.

    Strips HTML comments, extracts H2 sections, parses fenced YAML.
    """
    text = path.read_text(encoding="utf-8")
    sections = _extract_h2_sections(text)

    workstreams: list[WorkstreamEntry] = []
    for heading, section_text in sections:
        data = _parse_fenced_yaml(section_text)
        if data is not None:
            workstreams.append(
                WorkstreamEntry(
                    name=str(data.get("name", heading)),
                    status=str(data.get("status", "active")),
                    description=str(data.get("description", "")),
                    created=str(data.get("created", "")),
                )
            )

    return WorkstreamsFile(workstreams=workstreams)


def write_workstreams(path: Path, ws: WorkstreamsFile) -> None:
    """Write a WorkstreamsFile to WORKSTREAMS.md using atomic_write.

    Validates output by re-parsing and checking workstream count.
    """
    lines = ["# Workstreams", ""]

    # Preserve comment block if file exists
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        comment_match = re.search(r"(<!--.*?-->)", existing, flags=re.DOTALL)
        if comment_match:
            lines.append(comment_match.group(1))
            lines.append("")

    for entry in ws.workstreams:
        lines.append(f"## {entry.name}")
        lines.append("```yaml")
        data = {"name": entry.name, "status": entry.status}
        if entry.description:
            data["description"] = entry.description
        if entry.created:
            data["created"] = entry.created
        lines.append(
            yaml.safe_dump(data, default_flow_style=False, allow_unicode=True).rstrip()
        )
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)

    def validate(c: str) -> bool:
        """Re-parse output and verify same number of workstreams."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_workstreams(tmp)
            return len(reread.workstreams) == len(ws.workstreams)
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
