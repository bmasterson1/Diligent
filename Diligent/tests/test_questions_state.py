"""Tests for QUESTIONS.md state layer and FactEntry anchor field.

Tests QuestionEntry model, questions.py reader/writer (H2 + fenced YAML),
QUESTIONS.md.tmpl template rendering, and FactEntry anchor round-trip.
"""

from pathlib import Path

import pytest

from diligent.state.models import FactEntry, SupersededValue, TruthFile


# --- FactEntry anchor field tests ---


class TestFactEntryAnchor:
    """FactEntry anchor field: defaults to False, round-trips through truth.py."""

    def test_anchor_defaults_to_false(self):
        """FactEntry anchor field defaults to False (backward compatible)."""
        entry = FactEntry(
            key="revenue",
            value="2400000",
            source="TEST-001",
            date="2026-01-01",
            workstream="financial",
        )
        assert entry.anchor is False

    def test_anchor_true_roundtrips_through_truth(self, tmp_path):
        """FactEntry with anchor=True round-trips through truth.py read/write."""
        from diligent.state.truth import read_truth, write_truth

        truth = TruthFile(
            facts={
                "annual_revenue": FactEntry(
                    key="annual_revenue",
                    value="2400000",
                    source="TEST-001",
                    date="2026-04-01",
                    workstream="financial",
                    anchor=True,
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        reread = read_truth(path)

        assert reread.facts["annual_revenue"].anchor is True

    def test_anchor_false_not_written_to_yaml(self, tmp_path):
        """FactEntry with anchor=False omits anchor line from YAML (backward compat)."""
        from diligent.state.truth import write_truth

        truth = TruthFile(
            facts={
                "test_fact": FactEntry(
                    key="test_fact",
                    value="100",
                    source="TEST-001",
                    date="2026-01-01",
                    workstream="financial",
                    anchor=False,
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        content = path.read_text(encoding="utf-8")
        assert "anchor" not in content

    def test_anchor_true_written_to_yaml(self, tmp_path):
        """FactEntry with anchor=True includes anchor: true in YAML."""
        from diligent.state.truth import write_truth

        truth = TruthFile(
            facts={
                "test_fact": FactEntry(
                    key="test_fact",
                    value="100",
                    source="TEST-001",
                    date="2026-01-01",
                    workstream="financial",
                    anchor=True,
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        content = path.read_text(encoding="utf-8")
        assert "anchor: true" in content

    def test_anchor_false_roundtrips(self, tmp_path):
        """FactEntry with anchor=False round-trips (default preserved)."""
        from diligent.state.truth import read_truth, write_truth

        truth = TruthFile(
            facts={
                "test_fact": FactEntry(
                    key="test_fact",
                    value="100",
                    source="TEST-001",
                    date="2026-01-01",
                    workstream="financial",
                    anchor=False,
                ),
            }
        )

        path = tmp_path / "TRUTH.md"
        write_truth(path, truth)
        reread = read_truth(path)
        assert reread.facts["test_fact"].anchor is False


# --- QuestionEntry model tests ---


class TestQuestionEntryModel:
    """QuestionEntry dataclass has all required fields."""

    def test_question_entry_fields(self):
        """QuestionEntry has: id, question, workstream, owner, status, date_raised, context."""
        from diligent.state.models import QuestionEntry

        entry = QuestionEntry(
            id="Q-001",
            question="Why did revenue drop 15%?",
            workstream="financial",
            owner="self",
            status="open",
            date_raised="2026-04-07",
            context={"key": "annual_revenue", "old_value": "2400000", "new_value": "2040000"},
        )
        assert entry.id == "Q-001"
        assert entry.question == "Why did revenue drop 15%?"
        assert entry.workstream == "financial"
        assert entry.owner == "self"
        assert entry.status == "open"
        assert entry.date_raised == "2026-04-07"
        assert entry.context["key"] == "annual_revenue"

    def test_question_entry_context_optional(self):
        """QuestionEntry context field defaults to None."""
        from diligent.state.models import QuestionEntry

        entry = QuestionEntry(
            id="Q-002",
            question="Manual question",
            workstream="legal",
            owner="principal",
            status="open",
            date_raised="2026-04-07",
        )
        assert entry.context is None

    def test_answer_fields_default_to_none(self):
        """QuestionEntry answer, answer_source, date_answered default to None."""
        from diligent.state.models import QuestionEntry

        entry = QuestionEntry(
            id="Q-003",
            question="Test?",
            workstream="financial",
            owner="self",
            status="open",
            date_raised="2026-04-07",
        )
        assert entry.answer is None
        assert entry.answer_source is None
        assert entry.date_answered is None

    def test_answer_fields_populated(self):
        """QuestionEntry accepts answer, answer_source, date_answered."""
        from diligent.state.models import QuestionEntry

        entry = QuestionEntry(
            id="Q-004",
            question="What is the ARR?",
            workstream="financial",
            owner="seller",
            status="answered",
            date_raised="2026-04-01",
            answer="$2.4M based on Q1 run rate",
            answer_source="ARRIVAL-003",
            date_answered="2026-04-05",
        )
        assert entry.answer == "$2.4M based on Q1 run rate"
        assert entry.answer_source == "ARRIVAL-003"
        assert entry.date_answered == "2026-04-05"

    def test_backward_compat_no_answer_args(self):
        """QuestionEntry without answer fields still works (backward compat)."""
        from diligent.state.models import QuestionEntry

        entry = QuestionEntry(
            id="Q-005",
            question="Old question",
            workstream="legal",
            owner="self",
            status="open",
            date_raised="2026-03-15",
            context={"key": "contract_terms"},
        )
        assert entry.context == {"key": "contract_terms"}
        assert entry.answer is None
        assert entry.answer_source is None
        assert entry.date_answered is None

    def test_questions_file_model(self):
        """QuestionsFile wraps a list of QuestionEntry."""
        from diligent.state.models import QuestionEntry, QuestionsFile

        qf = QuestionsFile(questions=[
            QuestionEntry(
                id="Q-001",
                question="Test?",
                workstream="financial",
                owner="self",
                status="open",
                date_raised="2026-04-07",
            ),
        ])
        assert len(qf.questions) == 1
        assert qf.questions[0].id == "Q-001"

    def test_questions_file_empty_default(self):
        """QuestionsFile defaults to empty questions list."""
        from diligent.state.models import QuestionsFile

        qf = QuestionsFile()
        assert qf.questions == []


# --- questions.py reader/writer tests ---


class TestQuestionsReaderWriter:
    """read_questions / write_questions with H2 + fenced YAML pattern."""

    def test_read_questions_parses_h2_fenced_yaml(self, tmp_path):
        """read_questions parses H2 + fenced YAML sections into list of QuestionEntry."""
        from diligent.state.questions import read_questions

        content = """# Questions

## Q-001
```yaml
question: "Why did revenue drop 15%?"
workstream: financial
owner: self
status: open
date_raised: "2026-04-07"
context:
  key: annual_revenue
  old_value: "2400000"
  new_value: "2040000"
```

## Q-002
```yaml
question: "Is the lease transferable?"
workstream: legal
owner: counsel
status: open
date_raised: "2026-04-08"
```
"""
        path = tmp_path / "QUESTIONS.md"
        path.write_text(content, encoding="utf-8")

        qf = read_questions(path)
        assert len(qf.questions) == 2
        assert qf.questions[0].id == "Q-001"
        assert qf.questions[0].question == "Why did revenue drop 15%?"
        assert qf.questions[0].workstream == "financial"
        assert qf.questions[0].owner == "self"
        assert qf.questions[0].status == "open"
        assert qf.questions[0].date_raised == "2026-04-07"
        assert qf.questions[0].context["key"] == "annual_revenue"
        assert qf.questions[1].id == "Q-002"
        assert qf.questions[1].question == "Is the lease transferable?"
        assert qf.questions[1].context is None

    def test_write_questions_roundtrip(self, tmp_path):
        """write_questions produces valid markdown that re-parses identically."""
        from diligent.state.models import QuestionEntry, QuestionsFile
        from diligent.state.questions import read_questions, write_questions

        qf = QuestionsFile(questions=[
            QuestionEntry(
                id="Q-001",
                question="Why did revenue drop 15%?",
                workstream="financial",
                owner="self",
                status="open",
                date_raised="2026-04-07",
                context={"key": "annual_revenue", "old_value": "2400000", "new_value": "2040000"},
            ),
            QuestionEntry(
                id="Q-002",
                question="Is the lease transferable?",
                workstream="legal",
                owner="counsel",
                status="open",
                date_raised="2026-04-08",
            ),
        ])

        path = tmp_path / "QUESTIONS.md"
        write_questions(path, qf)
        reread = read_questions(path)

        assert len(reread.questions) == 2
        assert reread.questions[0].id == "Q-001"
        assert reread.questions[0].question == "Why did revenue drop 15%?"
        assert reread.questions[0].workstream == "financial"
        assert reread.questions[0].owner == "self"
        assert reread.questions[0].status == "open"
        assert reread.questions[0].date_raised == "2026-04-07"
        assert reread.questions[0].context == {"key": "annual_revenue", "old_value": "2400000", "new_value": "2040000"}
        assert reread.questions[1].id == "Q-002"
        assert reread.questions[1].context is None

    def test_write_questions_uses_atomic_write(self, tmp_path):
        """write_questions uses atomic_write with validate_fn."""
        from unittest.mock import patch
        from diligent.state.models import QuestionEntry, QuestionsFile
        from diligent.state.questions import write_questions

        qf = QuestionsFile(questions=[
            QuestionEntry(
                id="Q-001",
                question="Test?",
                workstream="financial",
                owner="self",
                status="open",
                date_raised="2026-04-07",
            ),
        ])

        path = tmp_path / "QUESTIONS.md"
        with patch("diligent.state.questions.atomic_write") as mock_aw:
            write_questions(path, qf)
            mock_aw.assert_called_once()
            # Check validate_fn is passed
            call_kwargs = mock_aw.call_args
            # atomic_write(path, content, validate_fn=validate)
            assert call_kwargs[1].get("validate_fn") is not None or len(call_kwargs[0]) > 2

    def test_empty_questions_file_parses(self, tmp_path):
        """Empty QUESTIONS.md (H1 header only) parses into QuestionsFile with empty list."""
        path = tmp_path / "QUESTIONS.md"
        path.write_text("# Questions\n", encoding="utf-8")

        from diligent.state.questions import read_questions
        qf = read_questions(path)
        assert len(qf.questions) == 0

    def test_questions_with_html_comments_parsed(self, tmp_path):
        """HTML comments are stripped during parsing."""
        from diligent.state.questions import read_questions

        content = """# Questions

<!-- This is a comment with example format -->

## Q-001
```yaml
question: "Test question"
workstream: financial
owner: self
status: open
date_raised: "2026-04-07"
```
"""
        path = tmp_path / "QUESTIONS.md"
        path.write_text(content, encoding="utf-8")

        qf = read_questions(path)
        assert len(qf.questions) == 1
        assert qf.questions[0].id == "Q-001"

    def test_read_questions_without_answer_fields(self, tmp_path):
        """read_questions on QUESTIONS.md WITHOUT answer fields returns None defaults."""
        from diligent.state.questions import read_questions

        content = """# Questions

## Q-001
```yaml
question: "Why did revenue drop?"
workstream: financial
owner: self
status: open
date_raised: "2026-04-07"
```
"""
        path = tmp_path / "QUESTIONS.md"
        path.write_text(content, encoding="utf-8")

        qf = read_questions(path)
        assert qf.questions[0].answer is None
        assert qf.questions[0].answer_source is None
        assert qf.questions[0].date_answered is None

    def test_read_questions_with_answer_fields(self, tmp_path):
        """read_questions on QUESTIONS.md WITH answer fields populates them."""
        from diligent.state.questions import read_questions

        content = """# Questions

## Q-001
```yaml
question: "Why did revenue drop?"
workstream: financial
owner: self
status: answered
date_raised: "2026-04-07"
answer: "Seasonal decline in Q4"
answer_source: ARRIVAL-003
date_answered: "2026-04-08"
```
"""
        path = tmp_path / "QUESTIONS.md"
        path.write_text(content, encoding="utf-8")

        qf = read_questions(path)
        assert qf.questions[0].answer == "Seasonal decline in Q4"
        assert qf.questions[0].answer_source == "ARRIVAL-003"
        assert qf.questions[0].date_answered == "2026-04-08"

    def test_write_questions_omits_none_answer_fields(self, tmp_path):
        """write_questions omits answer/answer_source/date_answered when None."""
        from diligent.state.models import QuestionEntry, QuestionsFile
        from diligent.state.questions import write_questions

        qf = QuestionsFile(questions=[
            QuestionEntry(
                id="Q-001",
                question="Test?",
                workstream="financial",
                owner="self",
                status="open",
                date_raised="2026-04-07",
            ),
        ])

        path = tmp_path / "QUESTIONS.md"
        write_questions(path, qf)
        content = path.read_text(encoding="utf-8")

        assert "answer:" not in content
        assert "answer_source:" not in content
        assert "date_answered:" not in content

    def test_write_questions_includes_answer_fields_when_populated(self, tmp_path):
        """write_questions includes answer fields when populated."""
        from diligent.state.models import QuestionEntry, QuestionsFile
        from diligent.state.questions import read_questions, write_questions

        qf = QuestionsFile(questions=[
            QuestionEntry(
                id="Q-001",
                question="What is the ARR?",
                workstream="financial",
                owner="seller",
                status="answered",
                date_raised="2026-04-01",
                answer="$2.4M based on Q1 run rate",
                answer_source="ARRIVAL-003",
                date_answered="2026-04-05",
            ),
        ])

        path = tmp_path / "QUESTIONS.md"
        write_questions(path, qf)
        content = path.read_text(encoding="utf-8")

        assert "answer:" in content
        assert "$2.4M based on Q1 run rate" in content
        assert "answer_source: ARRIVAL-003" in content
        assert "date_answered:" in content
        assert "2026-04-05" in content

        # Verify round-trip
        reread = read_questions(path)
        assert reread.questions[0].answer == "$2.4M based on Q1 run rate"
        assert reread.questions[0].answer_source == "ARRIVAL-003"
        assert reread.questions[0].date_answered == "2026-04-05"


# --- QUESTIONS.md.tmpl template tests ---


class TestQuestionsTemplate:
    """QUESTIONS.md.tmpl renders into a valid empty scaffold."""

    def test_template_renders_valid_scaffold(self):
        """QUESTIONS.md.tmpl renders into markdown with H1 header + HTML comment."""
        from diligent.templates import render_template

        content = render_template("QUESTIONS.md.tmpl", {})
        assert content.startswith("# Questions")
        assert "<!--" in content
        assert "-->" in content

    def test_template_parses_as_empty_questions(self, tmp_path):
        """Rendered QUESTIONS.md.tmpl parses into QuestionsFile with empty list."""
        from diligent.templates import render_template
        from diligent.state.questions import read_questions

        content = render_template("QUESTIONS.md.tmpl", {})
        path = tmp_path / "QUESTIONS.md"
        path.write_text(content, encoding="utf-8")

        qf = read_questions(path)
        assert len(qf.questions) == 0


# --- anchor_tolerance_pct default tests ---


class TestAnchorToleranceDefault:
    """anchor_tolerance_pct default updated from 1.0 to 0.5."""

    def test_render_config_uses_0_5_default(self):
        """render_config sets anchor_tolerance_pct to 0.5."""
        import json
        from diligent.templates import render_config

        content = render_config({
            "DEAL_CODE": "TEST",
            "ISO_DATE": "2026-01-01T00:00:00Z",
            "WORKSTREAMS_JSON": ["financial"],
        })
        data = json.loads(content)
        assert data["anchor_tolerance_pct"] == 0.5
