"""SOURCES.md reader/writer.

Same H2 + fenced YAML pattern as truth.py. Each source is an H2
with source ID, YAML block with fields.
"""

import re
from pathlib import Path
from typing import Optional

import yaml

from diligent.helpers.io import atomic_write
from diligent.state.models import SourceEntry, SourcesFile


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments from markdown text."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _extract_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into list of (H2 heading, section content) tuples.

    Returns a list (not dict) to preserve source ordering.
    """
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


def read_sources(path: Path) -> SourcesFile:
    """Read SOURCES.md into a SourcesFile dataclass.

    Strips HTML comments, extracts H2 sections, parses fenced YAML.
    Source ID comes from the H2 heading text.
    """
    text = path.read_text(encoding="utf-8")
    sections = _extract_h2_sections(text)

    sources: list[SourceEntry] = []
    for heading, section_text in sections:
        data = _parse_fenced_yaml(section_text)
        if data is not None:
            sources.append(
                SourceEntry(
                    id=heading,
                    path=str(data.get("path", "")),
                    date_received=str(data.get("date_received", "")),
                    parties=data.get("parties", []) or [],
                    workstream_tags=data.get("workstream_tags", []) or [],
                    supersedes=data.get("supersedes"),
                    notes=data.get("notes"),
                )
            )

    return SourcesFile(sources=sources)


def _format_source_yaml(entry: SourceEntry) -> str:
    """Format a single SourceEntry as a YAML block string."""
    data: dict = {
        "path": entry.path,
        "date_received": entry.date_received,
        "parties": entry.parties,
        "workstream_tags": entry.workstream_tags,
        "supersedes": entry.supersedes,
        "notes": entry.notes,
    }
    return yaml.safe_dump(data, default_flow_style=False, allow_unicode=True).rstrip()


def write_sources(path: Path, sources: SourcesFile) -> None:
    """Write a SourcesFile to SOURCES.md using atomic_write.

    Validates output by re-parsing and checking source count.
    """
    lines = ["# Sources", ""]

    # Preserve comment block if file exists
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        comment_match = re.search(r"(<!--.*?-->)", existing, flags=re.DOTALL)
        if comment_match:
            lines.append(comment_match.group(1))
            lines.append("")

    for entry in sources.sources:
        lines.append(f"## {entry.id}")
        lines.append("```yaml")
        lines.append(_format_source_yaml(entry))
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)

    def validate(c: str) -> bool:
        """Re-parse output and verify same number of sources."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_sources(tmp)
            return len(reread.sources) == len(sources.sources)
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
