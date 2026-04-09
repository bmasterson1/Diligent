"""ARTIFACTS.md reader/writer.

Same H2 + fenced YAML pattern as sources.py and truth.py. Each artifact
is an H2 heading with the relative path, followed by a fenced YAML block.
Replicated per module per Phase 1 decision (no shared utility).
"""

import re
from pathlib import Path
from typing import Optional

import yaml

from diligent.helpers.io import atomic_write
from diligent.state.models import ArtifactEntry, ArtifactsFile


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments from markdown text."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _extract_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into list of (H2 heading, section content) tuples.

    Returns a list (not dict) to preserve artifact ordering.
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


def read_artifacts(path: Path) -> ArtifactsFile:
    """Read ARTIFACTS.md into an ArtifactsFile dataclass.

    Strips HTML comments, extracts H2 sections, parses fenced YAML.
    Artifact path comes from the H2 heading text.
    """
    text = path.read_text(encoding="utf-8")
    sections = _extract_h2_sections(text)

    artifacts: list[ArtifactEntry] = []
    for heading, section_text in sections:
        data = _parse_fenced_yaml(section_text)
        if data is not None:
            # Ensure references and scanner_findings are always lists of strings
            references_raw = data.get("references", []) or []
            references = [str(r) for r in references_raw]

            scanner_raw = data.get("scanner_findings", []) or []
            scanner_findings = [str(s) for s in scanner_raw]

            artifacts.append(
                ArtifactEntry(
                    path=heading,
                    workstream=str(data.get("workstream", "")),
                    registered=str(data.get("registered", "")),
                    last_refreshed=str(data.get("last_refreshed", "")),
                    references=references,
                    scanner_findings=scanner_findings,
                    notes=str(data.get("notes", "") or ""),
                )
            )

    return ArtifactsFile(artifacts=artifacts)


def _format_artifact_yaml(entry: ArtifactEntry) -> str:
    """Format a single ArtifactEntry as a YAML block string.

    Manually constructs YAML to ensure all list items are quoted strings,
    preventing type coercion of numeric-looking or boolean-looking values.
    """
    lines = [
        f'workstream: "{entry.workstream}"',
        f'registered: "{entry.registered}"',
        f'last_refreshed: "{entry.last_refreshed}"',
    ]

    # references: always quote each item as string
    if entry.references:
        lines.append("references:")
        for ref in entry.references:
            lines.append(f'  - "{ref}"')
    else:
        lines.append("references: []")

    # scanner_findings: always quote each item as string
    if entry.scanner_findings:
        lines.append("scanner_findings:")
        for sf in entry.scanner_findings:
            lines.append(f'  - "{sf}"')
    else:
        lines.append("scanner_findings: []")

    # notes
    lines.append(f'notes: "{entry.notes}"')

    return "\n".join(lines)


def write_artifacts(path: Path, artifacts: ArtifactsFile) -> None:
    """Write an ArtifactsFile to ARTIFACTS.md using atomic_write.

    Validates output by re-parsing and checking artifact count.
    """
    lines = ["# Artifacts", ""]

    # Preserve comment block if file exists
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        comment_match = re.search(r"(<!--.*?-->)", existing, flags=re.DOTALL)
        if comment_match:
            lines.append(comment_match.group(1))
            lines.append("")

    for entry in artifacts.artifacts:
        lines.append(f"## {entry.path}")
        lines.append("```yaml")
        lines.append(_format_artifact_yaml(entry))
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)

    def validate(c: str) -> bool:
        """Re-parse output and verify same number of artifacts."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_artifacts(tmp)
            return len(reread.artifacts) == len(artifacts.artifacts)
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
