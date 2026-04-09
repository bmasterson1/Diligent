"""Tests for ask, answer, and questions list CLI commands.

Tests question_cmd.py: ask (add questions with auto-generated IDs,
owner validation, workstream scoping), answer (close questions with
text and optional source), questions list (origin tags, filters, summary).
"""

import json
from datetime import date
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.commands.question_cmd import ask_cmd, answer_cmd, questions_cmd


@pytest.fixture
def deal_dir(tmp_path):
    """Create a minimal .diligence/ dir with config.json, QUESTIONS.md, WORKSTREAMS.md."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()

    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )

    questions_content = "# Questions\n"
    (diligence / "QUESTIONS.md").write_text(questions_content, encoding="utf-8")

    workstreams_content = "# Workstreams\n"
    (diligence / "WORKSTREAMS.md").write_text(workstreams_content, encoding="utf-8")

    return tmp_path


@pytest.fixture
def deal_dir_with_questions(tmp_path):
    """Create .diligence/ with pre-populated questions including a gate question."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()

    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )

    questions_content = """# Questions

## Q-001
```yaml
question: "Revenue changed from $2M to $3M. Which value is correct?"
workstream: financial
owner: self
status: open
date_raised: "2026-04-01"
context:
  key: annual_revenue
  new_value: $3M
  old_value: $2M
  type: gate_rejection
```

## Q-002
```yaml
question: "What is the customer churn rate?"
workstream: retention
owner: principal
status: answered
date_raised: "2026-04-02"
answer: "Monthly churn is 2.5%"
answer_source: ARR-001
date_answered: "2026-04-05"
```

## Q-003
```yaml
question: "Are there pending lawsuits?"
workstream: legal
owner: counsel
status: open
date_raised: "2026-04-03"
```
"""
    (diligence / "QUESTIONS.md").write_text(questions_content, encoding="utf-8")

    workstreams_content = "# Workstreams\n"
    (diligence / "WORKSTREAMS.md").write_text(workstreams_content, encoding="utf-8")

    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


class TestAsk:
    """Tests for the ask command."""

    def test_ask_adds_question_with_defaults(self, deal_dir, runner):
        """ask adds Q-001 with owner=self, status=open, date_raised=today."""
        result = runner.invoke(
            ask_cmd,
            ["What is the revenue run rate?"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "Q-001" in result.output

        from diligent.state.questions import read_questions

        qs = read_questions(deal_dir / ".diligence" / "QUESTIONS.md")
        assert len(qs.questions) == 1
        q = qs.questions[0]
        assert q.id == "Q-001"
        assert q.question == "What is the revenue run rate?"
        assert q.owner == "self"
        assert q.status == "open"
        assert q.date_raised == date.today().isoformat()

    def test_ask_with_owner_and_workstream(self, deal_dir, runner):
        """ask with --owner and --workstream sets them correctly."""
        result = runner.invoke(
            ask_cmd,
            ["Question text", "--owner", "principal", "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

        from diligent.state.questions import read_questions

        qs = read_questions(deal_dir / ".diligence" / "QUESTIONS.md")
        q = qs.questions[0]
        assert q.owner == "principal"
        assert q.workstream == "financial"

    def test_ask_invalid_owner_exits_nonzero(self, deal_dir, runner):
        """ask with invalid owner exits non-zero."""
        result = runner.invoke(
            ask_cmd,
            ["Text", "--owner", "invalid"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_ask_no_text_exits_nonzero(self, deal_dir, runner):
        """ask with no text argument exits non-zero."""
        result = runner.invoke(
            ask_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_ask_json_output(self, deal_dir, runner):
        """ask --json returns JSON with id, question, owner, workstream, status."""
        result = runner.invoke(
            ask_cmd,
            ["Question text", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "Q-001"
        assert data["question"] == "Question text"
        assert data["owner"] == "self"
        assert data["status"] == "open"

    def test_sequential_asks_increment_ids(self, deal_dir, runner):
        """Sequential asks generate incrementing IDs: Q-001, Q-002, Q-003."""
        for i in range(3):
            result = runner.invoke(
                ask_cmd,
                [f"Question {i + 1}"],
                catch_exceptions=False,
                env={"DILIGENT_CWD": str(deal_dir)},
            )
            assert result.exit_code == 0

        from diligent.state.questions import read_questions

        qs = read_questions(deal_dir / ".diligence" / "QUESTIONS.md")
        assert len(qs.questions) == 3
        assert qs.questions[0].id == "Q-001"
        assert qs.questions[1].id == "Q-002"
        assert qs.questions[2].id == "Q-003"

    def test_ask_with_existing_gate_question(self, deal_dir_with_questions, runner):
        """ask with existing gate Q-001 generates Q-004 (scans max, not count)."""
        result = runner.invoke(
            ask_cmd,
            ["New question after gate"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "Q-004" in result.output

        from diligent.state.questions import read_questions

        qs = read_questions(
            deal_dir_with_questions / ".diligence" / "QUESTIONS.md"
        )
        # Should now have Q-001, Q-002, Q-003 (pre-existing) + Q-004 (new)
        assert len(qs.questions) == 4
        assert qs.questions[3].id == "Q-004"


class TestAnswer:
    """Tests for the answer command."""

    def test_answer_closes_question(self, deal_dir_with_questions, runner):
        """answer Q-001 sets status=answered, answer text, date_answered."""
        result = runner.invoke(
            answer_cmd,
            ["Q-001", "Revenue is 5M ARR"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "Q-001" in result.output

        from diligent.state.questions import read_questions

        qs = read_questions(
            deal_dir_with_questions / ".diligence" / "QUESTIONS.md"
        )
        q = next(q for q in qs.questions if q.id == "Q-001")
        assert q.status == "answered"
        assert q.answer == "Revenue is 5M ARR"
        assert q.date_answered == date.today().isoformat()

    def test_answer_with_source(self, deal_dir_with_questions, runner):
        """answer with --source sets answer_source."""
        result = runner.invoke(
            answer_cmd,
            ["Q-001", "Revenue is 5M ARR", "--source", "ARR-001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0

        from diligent.state.questions import read_questions

        qs = read_questions(
            deal_dir_with_questions / ".diligence" / "QUESTIONS.md"
        )
        q = next(q for q in qs.questions if q.id == "Q-001")
        assert q.answer_source == "ARR-001"

    def test_answer_nonexistent_question_exits_nonzero(
        self, deal_dir_with_questions, runner
    ):
        """answer Q-999 exits non-zero (question not found)."""
        result = runner.invoke(
            answer_cmd,
            ["Q-999", "Some text"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code != 0

    def test_answer_already_answered_exits_nonzero(
        self, deal_dir_with_questions, runner
    ):
        """answer on already-answered Q-002 exits non-zero."""
        result = runner.invoke(
            answer_cmd,
            ["Q-002", "New answer"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code != 0
        assert "already answered" in result.output.lower()

    def test_answer_json_output(self, deal_dir_with_questions, runner):
        """answer --json returns JSON with updated question."""
        result = runner.invoke(
            answer_cmd,
            ["Q-001", "Revenue is 5M ARR", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["id"] == "Q-001"
        assert data["status"] == "answered"
        assert data["answer"] == "Revenue is 5M ARR"


class TestOwnerValidation:
    """Tests for owner taxonomy validation."""

    @pytest.mark.parametrize(
        "owner", ["self", "principal", "seller", "broker", "counsel"]
    )
    def test_valid_owners_accepted(self, deal_dir, runner, owner):
        """All valid owner values are accepted."""
        result = runner.invoke(
            ask_cmd,
            ["Question text", "--owner", owner],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0

    @pytest.mark.parametrize("owner", ["invalid", "team", "admin", "SELF", "Self"])
    def test_invalid_owners_rejected(self, deal_dir, runner, owner):
        """Invalid owner values are rejected."""
        result = runner.invoke(
            ask_cmd,
            ["Question text", "--owner", owner],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0


class TestQuestionsList:
    """Tests for the questions list command."""

    def test_list_shows_columns(self, deal_dir_with_questions, runner):
        """questions list with 3 questions shows ID, ORIGIN, QUESTION, WORKSTREAM, OWNER, STATUS."""
        result = runner.invoke(
            questions_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "Q-001" in result.output
        assert "Q-002" in result.output
        assert "Q-003" in result.output

    def test_list_origin_tags(self, deal_dir_with_questions, runner):
        """Origin shows [gate] when context not None, [manual] when None."""
        result = runner.invoke(
            questions_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "[gate]" in result.output
        assert "[manual]" in result.output

    def test_list_summary_line(self, deal_dir_with_questions, runner):
        """Summary line shows 'N questions: N open, N answered'."""
        result = runner.invoke(
            questions_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "3 questions" in result.output
        assert "2 open" in result.output
        assert "1 answered" in result.output

    def test_list_owner_filter(self, deal_dir_with_questions, runner):
        """questions list --owner principal shows only principal's questions."""
        result = runner.invoke(
            questions_cmd,
            ["list", "--owner", "principal"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "Q-002" in result.output
        # Q-001 and Q-003 should not be in display
        lines = result.output.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("Q-")]
        assert len(data_lines) == 1

    def test_list_owner_filter_summary_counts_all(
        self, deal_dir_with_questions, runner
    ):
        """Summary line counts all questions, not just filtered."""
        result = runner.invoke(
            questions_cmd,
            ["list", "--owner", "principal"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "3 questions" in result.output

    def test_list_json_output(self, deal_dir_with_questions, runner):
        """questions list --json returns JSON array with all fields."""
        result = runner.invoke(
            questions_cmd,
            ["list", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 3
        # Check origin field added
        origins = [q["origin"] for q in data]
        assert "[gate]" in origins
        assert "[manual]" in origins

    def test_list_no_questions(self, deal_dir, runner):
        """questions list with no questions shows 'No questions found'."""
        result = runner.invoke(
            questions_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0
        assert "No questions found" in result.output

    def test_list_workstream_filter(self, deal_dir_with_questions, runner):
        """questions list --workstream financial filters by workstream."""
        result = runner.invoke(
            questions_cmd,
            ["list", "--workstream", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert result.exit_code == 0
        assert "Q-001" in result.output
        lines = result.output.strip().split("\n")
        data_lines = [l for l in lines if l.startswith("Q-")]
        assert len(data_lines) == 1


class TestGateOrigin:
    """Tests for gate vs manual origin display."""

    def test_gate_question_shows_gate_tag(self, deal_dir_with_questions, runner):
        """Gate-rejected question (with context) shows [gate] origin."""
        result = runner.invoke(
            questions_cmd,
            ["list", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        data = json.loads(result.output)
        q1 = next(q for q in data if q["id"] == "Q-001")
        assert q1["origin"] == "[gate]"
        assert q1["context"] is not None

    def test_manual_question_shows_manual_tag(
        self, deal_dir_with_questions, runner
    ):
        """Manual question (context=None) shows [manual] origin."""
        result = runner.invoke(
            questions_cmd,
            ["list", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        data = json.loads(result.output)
        q3 = next(q for q in data if q["id"] == "Q-003")
        assert q3["origin"] == "[manual]"
        assert q3["context"] is None

    def test_mixed_origins_in_list(self, deal_dir_with_questions, runner):
        """Both [gate] and [manual] origins appear in plain text list."""
        result = runner.invoke(
            questions_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_questions)},
        )
        assert "[gate]" in result.output
        assert "[manual]" in result.output
