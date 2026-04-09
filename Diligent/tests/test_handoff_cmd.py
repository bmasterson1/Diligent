"""Tests for the diligent handoff command.

Integration tests using CliRunner + DILIGENT_CWD pattern.
Creates fully populated .diligence/ directories to test
instruction header, state aggregation, time-window filtering,
--since/--everything/--clip/--json flags.
"""

import json
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from diligent.commands.handoff_cmd import handoff_cmd


def _write_deal_md(diligence: Path, deal_code="TEST"):
    """Write a DEAL.md with frontmatter."""
    content = f"""---
deal_code: {deal_code}
target_legal_name: Target Legal Inc
target_common_name: Target
deal_stage: post-LOI
loi_date: "2026-01-15"
principal: John Doe
principal_role: Managing Director
seller: Seller Corp
broker: Broker LLC
workstreams:
  - financial
  - legal
---

Investment thesis: Target is a compelling acquisition candidate.
"""
    (diligence / "DEAL.md").write_text(content, encoding="utf-8")


def _write_state_md(diligence: Path):
    """Write a STATE.md."""
    content = f"""---
created: "2026-01-10T00:00:00Z"
last_modified: "{date.today().isoformat()}T00:00:00Z"
---

# State
"""
    (diligence / "STATE.md").write_text(content, encoding="utf-8")


def _write_config_json(diligence: Path, recent_window_days=7):
    """Write a config.json."""
    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 1.0,
        "recent_window_days": recent_window_days,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def _write_workstreams_md(diligence: Path, names=None):
    """Write WORKSTREAMS.md."""
    if names is None:
        names = ["financial", "legal"]
    lines = ["# Workstreams", ""]
    for name in names:
        lines.append(f"## {name}")
        lines.append("```yaml")
        lines.append(f"name: {name}")
        lines.append("status: active")
        lines.append(f'description: "{name} workstream"')
        lines.append('created: "2026-01-15"')
        lines.append("```")
        lines.append("")
    (diligence / "WORKSTREAMS.md").write_text("\n".join(lines), encoding="utf-8")


def _write_truth_md(diligence: Path, recent_days=3, old_days=30):
    """Write TRUTH.md with recent and old facts, plus a flagged fact.

    recent_days: days ago for 'recent' facts
    old_days: days ago for 'old' facts
    """
    recent_date = (date.today() - timedelta(days=recent_days)).isoformat()
    old_date = (date.today() - timedelta(days=old_days)).isoformat()
    flag_date = (date.today() - timedelta(days=old_days)).isoformat()

    content = f"""# Truth

## annual_revenue
```yaml
value: "$5M"
source: SRC-001
date: "{recent_date}"
workstream: financial
supersedes: []
```

## employee_count
```yaml
value: "50"
source: SRC-001
date: "{old_date}"
workstream: legal
supersedes: []
```

## contract_term
```yaml
value: "3 years"
source: SRC-002
date: "{old_date}"
workstream: legal
supersedes: []
flagged:
  reason: "Conflicting terms in side letter"
  date: "{flag_date}"
```
"""
    (diligence / "TRUTH.md").write_text(content, encoding="utf-8")


def _write_sources_md(diligence: Path, recent_days=3, old_days=30):
    """Write SOURCES.md with recent and old sources."""
    recent_date = (date.today() - timedelta(days=recent_days)).isoformat()
    old_date = (date.today() - timedelta(days=old_days)).isoformat()

    content = f"""# Sources

## SRC-001
```yaml
path: sources/financials.xlsx
date_received: "{recent_date}"
parties:
  - seller
workstream_tags:
  - financial
```

## SRC-002
```yaml
path: sources/old-contract.pdf
date_received: "{old_date}"
parties:
  - seller
workstream_tags:
  - legal
```
"""
    (diligence / "SOURCES.md").write_text(content, encoding="utf-8")


def _write_artifacts_md(diligence: Path):
    """Write ARTIFACTS.md with an artifact that will be stale."""
    old_refresh = (date.today() - timedelta(days=20)).isoformat()
    content = f"""# Artifacts

## reports/financial-model.xlsx
```yaml
workstream: financial
registered: "2026-03-01"
last_refreshed: "{old_refresh}"
references:
  - "annual_revenue"
scanner_findings: []
notes: ""
```
"""
    (diligence / "ARTIFACTS.md").write_text(content, encoding="utf-8")


def _write_questions_md(diligence: Path):
    """Write QUESTIONS.md with open and answered questions."""
    old_date = (date.today() - timedelta(days=60)).isoformat()
    content = f"""# Questions

## Q-001
```yaml
question: "Revenue changed from $2M to $5M. Which value is correct?"
workstream: financial
owner: self
status: open
date_raised: "{old_date}"
context:
  key: annual_revenue
  new_value: $5M
  old_value: $2M
  type: gate_rejection
```

## Q-002
```yaml
question: "What is the customer churn rate?"
workstream: financial
owner: principal
status: answered
date_raised: "{old_date}"
answer: "Monthly churn is 2.5%"
answer_source: SRC-001
date_answered: "{date.today().isoformat()}"
```

## Q-003
```yaml
question: "Are there any pending lawsuits?"
workstream: legal
owner: counsel
status: open
date_raised: "{old_date}"
```
"""
    (diligence / "QUESTIONS.md").write_text(content, encoding="utf-8")


def _write_task_summary(diligence: Path, workstream: str, task_name: str, content: str):
    """Create a task directory with a SUMMARY.md and status.yaml for a workstream."""
    ws_dir = diligence / "workstreams" / workstream
    ws_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = ws_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    task_dir = tasks_dir / task_name
    task_dir.mkdir(exist_ok=True)
    (task_dir / "SUMMARY.md").write_text(content, encoding="utf-8")
    (task_dir / "status.yaml").write_text(
        "description: Test task\nstatus: complete\n", encoding="utf-8"
    )


@pytest.fixture
def populated_deal(tmp_path):
    """Create a fully populated .diligence/ directory for handoff tests."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()
    _write_deal_md(diligence)
    _write_state_md(diligence)
    _write_config_json(diligence)
    _write_workstreams_md(diligence)
    _write_truth_md(diligence)
    _write_sources_md(diligence)
    _write_artifacts_md(diligence)
    _write_questions_md(diligence)
    _write_task_summary(
        diligence, "financial", "001-analyze-revenue",
        "# Revenue Analysis\n\nCompleted detailed revenue breakdown by segment.\n"
    )
    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


class TestHandoffInstructionHeader:
    """Tests for the instruction header section."""

    def test_header_contains_deal_code(self, populated_deal, runner):
        """Instruction header substitutes the deal code."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "TEST Deal Context" in result.output

    def test_header_has_separator(self, populated_deal, runner):
        """Header ends with --- separator before data sections."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "---" in result.output

    def test_header_explains_editorial_principles(self, populated_deal, runner):
        """Header includes editorial guidance for the receiving agent."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        output = result.output.lower()
        # Should mention sourcing claims and not inventing values
        assert "source" in output
        assert "never invent" in output or "do not invent" in output or "never fabricate" in output


class TestHandoffDealSection:
    """Tests for the Deal section."""

    def test_deal_section_present(self, populated_deal, runner):
        """Handoff includes full DEAL.md content section."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "## Deal" in result.output
        assert "Target Legal Inc" in result.output
        assert "post-LOI" in result.output
        assert "Investment thesis" in result.output


class TestHandoffWorkstreamsSection:
    """Tests for the Workstreams section."""

    def test_workstreams_section_present(self, populated_deal, runner):
        """Handoff includes full WORKSTREAMS.md content."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "## Workstreams" in result.output
        assert "financial" in result.output
        assert "legal" in result.output


class TestHandoffTruthSection:
    """Tests for truth fact filtering by time window."""

    def test_recent_facts_included(self, populated_deal, runner):
        """Facts within the 14-day window (default) are included."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # annual_revenue is 3 days old (within 14-day window)
        assert "annual_revenue" in result.output

    def test_old_facts_excluded(self, populated_deal, runner):
        """Facts outside the 14-day window are excluded (unless flagged)."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # employee_count is 30 days old and not flagged, should be excluded
        assert "employee_count" not in result.output

    def test_flagged_facts_always_included(self, populated_deal, runner):
        """Flagged facts are included regardless of date."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # contract_term is 30 days old but flagged, should still appear
        assert "contract_term" in result.output


class TestHandoffQuestionsSection:
    """Tests for open questions (always included regardless of date)."""

    def test_open_questions_always_included(self, populated_deal, runner):
        """Open questions appear regardless of their date_raised age."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # Q-001 and Q-003 are open (even though date_raised is 60 days ago)
        assert "Q-001" in result.output
        assert "Q-003" in result.output

    def test_answered_questions_excluded(self, populated_deal, runner):
        """Answered questions are not in the open questions section."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # Q-002 is answered, should not appear in the Open Questions section
        # (It might appear elsewhere, but not as an open question entry)
        output_after_open_qs = result.output.split("## Open Questions")
        if len(output_after_open_qs) > 1:
            # Get the section between "## Open Questions" and next "##"
            section = output_after_open_qs[1].split("##")[0]
            assert "Q-002" not in section


class TestHandoffStaleArtifacts:
    """Tests for stale artifacts section."""

    def test_stale_artifacts_always_included(self, populated_deal, runner):
        """Stale artifacts appear regardless of date."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "## Stale Artifacts" in result.output
        assert "financial-model.xlsx" in result.output


class TestHandoffTaskSummaries:
    """Tests for task summary inclusion."""

    def test_task_summary_included(self, populated_deal, runner):
        """Most recent SUMMARY.md from active workstream is included."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "Revenue Analysis" in result.output or "Task Summar" in result.output


class TestHandoffSinceFlag:
    """Tests for --since flag."""

    def test_since_7d_narrows_window(self, populated_deal, runner):
        """--since 7d uses a 7-day window instead of default 14."""
        result = runner.invoke(
            handoff_cmd,
            ["--since", "7d"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # annual_revenue (3 days old) should still be within 7-day window
        assert "annual_revenue" in result.output
        # employee_count (30 days old) should be excluded
        assert "employee_count" not in result.output

    def test_since_iso_date(self, populated_deal, runner):
        """--since YYYY-MM-DD uses that specific date as cutoff."""
        # Use a date far enough back to include everything
        cutoff = (date.today() - timedelta(days=60)).isoformat()
        result = runner.invoke(
            handoff_cmd,
            ["--since", cutoff],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # With a 60-day-ago cutoff, both recent and old facts should appear
        assert "annual_revenue" in result.output
        assert "employee_count" in result.output


class TestHandoffEverythingFlag:
    """Tests for --everything flag."""

    def test_everything_includes_all(self, populated_deal, runner):
        """--everything includes all entries regardless of date."""
        result = runner.invoke(
            handoff_cmd,
            ["--everything"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "annual_revenue" in result.output
        assert "employee_count" in result.output
        assert "contract_term" in result.output

    def test_everything_changes_section_title(self, populated_deal, runner):
        """--everything uses 'Truth (All)' instead of 'Truth (Recent)'."""
        result = runner.invoke(
            handoff_cmd,
            ["--everything"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "Truth (All)" in result.output


class TestHandoffClipFlag:
    """Tests for --clip flag."""

    @patch("diligent.commands.handoff_cmd.copy_to_clipboard", return_value=True)
    def test_clip_copies_and_prints(self, mock_clip, populated_deal, runner):
        """--clip calls copy_to_clipboard AND still prints to stdout."""
        result = runner.invoke(
            handoff_cmd,
            ["--clip"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        mock_clip.assert_called_once()
        # Should still have content in stdout
        assert "TEST Deal Context" in result.output

    @patch("diligent.commands.handoff_cmd.copy_to_clipboard", return_value=True)
    def test_clip_success_message(self, mock_clip, populated_deal, runner):
        """--clip prints 'Copied to clipboard.' on success."""
        result = runner.invoke(
            handoff_cmd,
            ["--clip"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # Message goes to stderr
        assert "Copied to clipboard." in result.stderr

    @patch("diligent.commands.handoff_cmd.copy_to_clipboard", return_value=False)
    def test_clip_failure_message(self, mock_clip, populated_deal, runner):
        """--clip prints warning on failure."""
        result = runner.invoke(
            handoff_cmd,
            ["--clip"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "Clipboard not available on this system" in result.stderr


class TestHandoffJsonFlag:
    """Tests for --json flag."""

    def test_json_output_valid(self, populated_deal, runner):
        """--json produces valid JSON output."""
        result = runner.invoke(
            handoff_cmd,
            ["--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, dict)

    def test_json_has_sections(self, populated_deal, runner):
        """JSON output has expected section keys."""
        result = runner.invoke(
            handoff_cmd,
            ["--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "instruction_header" in data
        assert "deal" in data
        assert "workstreams" in data
        assert "truth" in data
        assert "sources" in data
        assert "open_questions" in data
        assert "stale_artifacts" in data


class TestHandoffExitAndErrors:
    """Tests for exit codes and error conditions."""

    def test_exit_code_zero(self, populated_deal, runner):
        """handoff exits 0 on success."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0

    def test_no_diligence_dir_errors(self, tmp_path, runner):
        """handoff outside .diligence/ directory errors."""
        result = runner.invoke(
            handoff_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(tmp_path)},
        )
        assert result.exit_code != 0
