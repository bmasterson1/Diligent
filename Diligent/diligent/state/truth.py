"""TRUTH.md reader/writer.

Handles the markdown-with-embedded-YAML format:
- H1 header "# Truth"
- HTML comment blocks (stripped during parsing)
- H2 headings per fact key
- Fenced YAML code blocks (```yaml ... ```) under each H2

Round-trip fidelity: read_truth -> write_truth -> read_truth produces
identical TruthFile. Values are always stored as quoted strings.
"""

import re
from pathlib import Path
from typing import Optional

import yaml

from diligent.helpers.io import atomic_write
from diligent.state.models import FactEntry, SupersededValue, TruthFile


def strip_html_comments(text: str) -> str:
    """Remove HTML comments from markdown text."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _extract_h2_sections(text: str) -> dict[str, str]:
    """Split markdown into dict of H2 heading -> section content.

    Only processes content after HTML comments are stripped.
    """
    clean = strip_html_comments(text)
    sections: dict[str, str] = {}
    current_heading: Optional[str] = None
    current_lines: list[str] = []

    for line in clean.split("\n"):
        if line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = "\n".join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = "\n".join(current_lines).strip()

    return sections


def _parse_fenced_yaml(section_text: str) -> Optional[dict]:
    """Extract and parse the first fenced YAML block from section text.

    Tracks fenced block state to handle backticks in values correctly.
    Returns parsed dict or None if no fenced block found.
    """
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


def _parse_fact_entry(key: str, data: dict) -> FactEntry:
    """Build a FactEntry from parsed YAML dict.

    Validates that value is a string (no YAML type coercion allowed).
    """
    value = data.get("value", "")
    if not isinstance(value, str):
        raise ValueError(
            f"Fact '{key}' value must be a string, got {type(value).__name__}: {value!r}"
        )

    supersedes_raw = data.get("supersedes", [])
    supersedes: list[SupersededValue] = []
    if supersedes_raw:
        for s in supersedes_raw:
            supersedes.append(
                SupersededValue(
                    value=str(s.get("value", "")),
                    source=str(s.get("source", "")),
                    date=str(s.get("date", "")),
                )
            )

    return FactEntry(
        key=key,
        value=value,
        source=str(data.get("source", "")),
        date=str(data.get("date", "")),
        workstream=str(data.get("workstream", "")),
        supersedes=supersedes,
        computed_by=data.get("computed_by"),
        notes=data.get("notes"),
        flagged=data.get("flagged"),
        anchor=bool(data.get("anchor", False)),
    )


def read_truth(path: Path) -> TruthFile:
    """Read TRUTH.md into a TruthFile dataclass.

    Strips HTML comments, extracts H2 sections, parses fenced YAML
    blocks within each section. Returns TruthFile with facts keyed
    by H2 heading text.
    """
    text = path.read_text(encoding="utf-8")
    sections = _extract_h2_sections(text)

    facts: dict[str, FactEntry] = {}
    for heading, section_text in sections.items():
        data = _parse_fenced_yaml(section_text)
        if data is not None:
            entry = _parse_fact_entry(heading, data)
            facts[heading] = entry

    return TruthFile(facts=facts)


def _escape_yaml_string(value: str) -> str:
    """Escape a string for use in double-quoted YAML."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _format_fact_yaml(entry: FactEntry) -> str:
    """Format a single FactEntry as a YAML block string.

    The value field is always explicitly quoted. Other fields use
    yaml.safe_dump for correctness.
    """
    lines = []
    lines.append(f'value: "{_escape_yaml_string(entry.value)}"')
    lines.append(f"source: {entry.source}")
    lines.append(f'date: "{entry.date}"')
    lines.append(f"workstream: {entry.workstream}")

    # Supersedes chain
    if entry.supersedes:
        lines.append("supersedes:")
        for s in entry.supersedes:
            lines.append(f'  - value: "{_escape_yaml_string(s.value)}"')
            lines.append(f"    source: {s.source}")
            lines.append(f'    date: "{s.date}"')
    else:
        lines.append("supersedes: []")

    # Anchor field (only written when True for backward compat)
    if entry.anchor:
        lines.append("anchor: true")

    # Optional fields
    if entry.computed_by is not None:
        lines.append(f"computed_by: {entry.computed_by}")
    if entry.notes is not None:
        # Notes may contain special characters; quote them
        lines.append(f'notes: "{_escape_yaml_string(entry.notes)}"')
    if entry.flagged is not None:
        flagged_yaml = yaml.safe_dump(
            {"flagged": entry.flagged}, default_flow_style=False
        ).strip()
        lines.append(flagged_yaml)

    return "\n".join(lines)


def write_truth(path: Path, truth: TruthFile) -> None:
    """Write a TruthFile to TRUTH.md using atomic_write.

    Facts are sorted alphabetically by key. Values are always
    stored as quoted strings. Validates output by re-parsing.
    """
    lines = ["# Truth", ""]

    # Preserve comment block if the file already exists
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        # Extract leading comment block
        comment_match = re.search(r"(<!--.*?-->)", existing, flags=re.DOTALL)
        if comment_match:
            lines.append(comment_match.group(1))
            lines.append("")

    # Write facts in alphabetical order
    for key in sorted(truth.facts.keys()):
        entry = truth.facts[key]
        lines.append(f"## {key}")
        lines.append("```yaml")
        lines.append(_format_fact_yaml(entry))
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)

    def validate(c: str) -> bool:
        """Re-parse output and verify same number of facts."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_truth(tmp)
            return len(reread.facts) == len(truth.facts)
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
