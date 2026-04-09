"""Question commands: ask, answer, and questions list.

ask adds an open question to QUESTIONS.md with auto-generated Q-NNN ID.
answer closes a question with answer text and optional source citation.
questions list shows all questions with [gate]/[manual] origin tags.
"""

import os
from datetime import date
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.formatting import output_result
from diligent.state.models import QuestionEntry, QuestionsFile
from diligent.state.questions import read_questions, write_questions


VALID_OWNERS = ["self", "principal", "seller", "broker", "counsel"]


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


def _next_question_id(questions: QuestionsFile) -> str:
    """Derive next Q-{NNN} from max existing question ID.

    Parses existing IDs like Q-001, Q-042, etc. and returns the next
    sequential ID. Starts at Q-001 if no questions exist.
    """
    max_num = 0
    for q in questions.questions:
        if q.id.startswith("Q-"):
            try:
                num = int(q.id[2:])
                if num > max_num:
                    max_num = num
            except ValueError:
                pass
    return f"Q-{max_num + 1:03d}"


@click.command("ask")
@click.argument("text")
@click.option("--workstream", default="", help="Workstream scope.")
@click.option(
    "--owner",
    default="self",
    help="Question owner (self, principal, seller, broker, counsel).",
)
@click.option(
    "--json", "json_mode", is_flag=True, default=False, help="Output JSON."
)
@click.pass_context
def ask_cmd(ctx, text, workstream, owner, json_mode):
    """Add an open question to the questions queue.

    TEXT is the question to ask. Auto-generates a Q-NNN ID.
    Defaults owner to self; use --owner to assign elsewhere.
    """
    # Validate owner
    if owner not in VALID_OWNERS:
        click.echo(
            f"Invalid owner '{owner}'. Must be one of: {', '.join(VALID_OWNERS)}"
        )
        ctx.exit(1)
        return

    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    questions = read_questions(diligence / "QUESTIONS.md")
    q_id = _next_question_id(questions)
    today = date.today().isoformat()

    entry = QuestionEntry(
        id=q_id,
        question=text,
        workstream=workstream,
        owner=owner,
        status="open",
        date_raised=today,
        context=None,
    )
    questions.questions.append(entry)
    write_questions(diligence / "QUESTIONS.md", questions)

    if json_mode:
        output_result(
            {
                "id": q_id,
                "question": text,
                "owner": owner,
                "workstream": workstream,
                "status": "open",
                "date_raised": today,
            },
            json_mode=True,
        )
    else:
        click.echo(f"Added {q_id}")


@click.command("answer")
@click.argument("question_id")
@click.argument("text")
@click.option("--source", default=None, help="Source ID for the answer.")
@click.option(
    "--json", "json_mode", is_flag=True, default=False, help="Output JSON."
)
@click.pass_context
def answer_cmd(ctx, question_id, text, source, json_mode):
    """Answer an open question.

    QUESTION_ID is the Q-NNN identifier. TEXT is the answer.
    Optionally provide --source to cite a source document.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    questions = read_questions(diligence / "QUESTIONS.md")

    # Find question by ID (case-insensitive)
    target = None
    for q in questions.questions:
        if q.id.upper() == question_id.upper():
            target = q
            break

    if target is None:
        click.echo(f"Question {question_id} not found.")
        ctx.exit(1)
        return

    if target.status == "answered":
        click.echo(f"Question {target.id} is already answered.")
        ctx.exit(1)
        return

    today = date.today().isoformat()
    target.answer = text
    target.answer_source = source
    target.date_answered = today
    target.status = "answered"

    write_questions(diligence / "QUESTIONS.md", questions)

    if json_mode:
        output_result(
            {
                "id": target.id,
                "question": target.question,
                "status": target.status,
                "answer": target.answer,
                "answer_source": target.answer_source,
                "date_answered": target.date_answered,
            },
            json_mode=True,
        )
    else:
        click.echo(f"Answered {target.id}")


@click.group("questions")
def questions_cmd():
    """View and manage questions."""
    pass


@questions_cmd.command("list")
@click.option("--owner", default=None, help="Filter by owner.")
@click.option("--workstream", default=None, help="Filter by workstream.")
@click.option(
    "--json", "json_mode", is_flag=True, default=False, help="Output JSON."
)
def questions_list(owner, workstream, json_mode):
    """List all questions with origin tags and summary.

    Shows [gate] for questions created by the verification gate and
    [manual] for questions added via ask. Supports --owner and
    --workstream filters. Summary line always counts all questions.
    """
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)

    questions = read_questions(diligence / "QUESTIONS.md")
    all_questions = questions.questions

    if not all_questions:
        click.echo("No questions found")
        return

    # Summary counts from ALL questions (regardless of filters)
    total = len(all_questions)
    count_open = sum(1 for q in all_questions if q.status == "open")
    count_answered = sum(1 for q in all_questions if q.status == "answered")

    # Derive origin for each question
    def _origin(q: QuestionEntry) -> str:
        return "[gate]" if q.context is not None else "[manual]"

    # Apply filters for display
    display = list(all_questions)
    if owner:
        display = [q for q in display if q.owner == owner]
    if workstream:
        display = [q for q in display if q.workstream == workstream]

    if json_mode:
        result = []
        for q in display:
            result.append({
                "id": q.id,
                "question": q.question,
                "workstream": q.workstream,
                "owner": q.owner,
                "status": q.status,
                "date_raised": q.date_raised,
                "origin": _origin(q),
                "context": q.context,
                "answer": q.answer,
                "answer_source": q.answer_source,
                "date_answered": q.date_answered,
            })
        output_result(result, json_mode=True)
        return

    # Column widths
    id_w = 7
    origin_w = 8
    question_w = 35
    ws_w = 15
    owner_w = 10
    status_w = 10

    for q in display:
        origin = _origin(q)
        # Truncate question text
        qtxt = q.question
        if len(qtxt) > question_w:
            qtxt = qtxt[: question_w - 3] + "..."

        line = (
            f"{q.id:<{id_w}} {origin:<{origin_w}} {qtxt:<{question_w}} "
            f"{q.workstream:<{ws_w}} {q.owner:<{owner_w}} {q.status:<{status_w}}"
        )
        click.echo(line)

    click.echo(
        f"\n{total} questions: {count_open} open, {count_answered} answered"
    )
