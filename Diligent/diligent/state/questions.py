"""QUESTIONS.md reader/writer.

Same H2 + fenced YAML pattern as truth.py and sources.py. Each question
is an H2 with the question ID, YAML block with fields.
"""

import re
from pathlib import Path
from typing import Optional

import yaml

from diligent.helpers.io import atomic_write
from diligent.state.models import QuestionEntry, QuestionsFile


def _strip_html_comments(text: str) -> str:
    """Remove HTML comments from markdown text."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _extract_h2_sections(text: str) -> list[tuple[str, str]]:
    """Split markdown into list of (H2 heading, section content) tuples.

    Returns a list (not dict) to preserve question ordering.
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


def read_questions(path: Path) -> QuestionsFile:
    """Read QUESTIONS.md into a QuestionsFile dataclass.

    Strips HTML comments, extracts H2 sections, parses fenced YAML.
    Question ID comes from the H2 heading text.
    """
    text = path.read_text(encoding="utf-8")
    sections = _extract_h2_sections(text)

    questions: list[QuestionEntry] = []
    for heading, section_text in sections:
        data = _parse_fenced_yaml(section_text)
        if data is not None:
            answer_raw = data.get("answer")
            answer = str(answer_raw) if answer_raw is not None else None
            answer_source_raw = data.get("answer_source")
            answer_source = str(answer_source_raw) if answer_source_raw is not None else None
            date_answered_raw = data.get("date_answered")
            date_answered = str(date_answered_raw) if date_answered_raw is not None else None

            questions.append(
                QuestionEntry(
                    id=heading,
                    question=str(data.get("question", "")),
                    workstream=str(data.get("workstream", "")),
                    owner=str(data.get("owner", "")),
                    status=str(data.get("status", "open")),
                    date_raised=str(data.get("date_raised", "")),
                    context=data.get("context"),
                    answer=answer,
                    answer_source=answer_source,
                    date_answered=date_answered,
                )
            )

    return QuestionsFile(questions=questions)


def _format_question_yaml(entry: QuestionEntry) -> str:
    """Format a single QuestionEntry as a YAML block string.

    The question field is always explicitly quoted. Context is rendered
    via yaml.safe_dump for nested dict handling.
    """
    lines = []
    escaped_q = entry.question.replace("\\", "\\\\").replace('"', '\\"')
    lines.append(f'question: "{escaped_q}"')
    lines.append(f"workstream: {entry.workstream}")
    lines.append(f"owner: {entry.owner}")
    lines.append(f"status: {entry.status}")
    lines.append(f'date_raised: "{entry.date_raised}"')

    if entry.answer is not None:
        escaped_a = entry.answer.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'answer: "{escaped_a}"')
    if entry.answer_source is not None:
        lines.append(f"answer_source: {entry.answer_source}")
    if entry.date_answered is not None:
        lines.append(f'date_answered: "{entry.date_answered}"')

    if entry.context is not None:
        context_yaml = yaml.safe_dump(
            {"context": entry.context}, default_flow_style=False
        ).strip()
        lines.append(context_yaml)

    return "\n".join(lines)


def write_questions(path: Path, questions: QuestionsFile) -> None:
    """Write a QuestionsFile to QUESTIONS.md using atomic_write.

    Validates output by re-parsing and checking question count.
    """
    lines = ["# Questions", ""]

    # Preserve comment block if file exists
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        comment_match = re.search(r"(<!--.*?-->)", existing, flags=re.DOTALL)
        if comment_match:
            lines.append(comment_match.group(1))
            lines.append("")

    for entry in questions.questions:
        lines.append(f"## {entry.id}")
        lines.append("```yaml")
        lines.append(_format_question_yaml(entry))
        lines.append("```")
        lines.append("")

    content = "\n".join(lines)

    def validate(c: str) -> bool:
        """Re-parse output and verify same number of questions."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as f:
            f.write(c)
            tmp = Path(f.name)
        try:
            reread = read_questions(tmp)
            return len(reread.questions) == len(questions.questions)
        finally:
            tmp.unlink(missing_ok=True)

    atomic_write(path, content, validate_fn=validate)
