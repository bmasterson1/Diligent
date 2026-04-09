"""Tests for the diligent status command.

Integration tests using CliRunner + DILIGENT_CWD pattern.
Creates fully populated .diligence/ directories for testing
all 5 sections: deal header, workstreams, stale artifacts,
open questions, recent activity.
"""

import json
from datetime import date, timedelta
from pathlib import Path

import pytest
from click.testing import CliRunner

from diligent.commands.status_cmd import status_cmd


def _write_deal_md(diligence: Path, stage="post-LOI", loi_date="2026-01-15"):
    """Write a DEAL.md with frontmatter."""
    content = f"""---
deal_code: TEST
target_legal_name: Target Legal
target_common_name: Target
deal_stage: {stage}
loi_date: "{loi_date}"
principal: John Doe
principal_role: Managing Director
seller: Seller Corp
broker: Broker LLC
workstreams:
  - financial
  - legal
---

Investment thesis text here.
"""
    (diligence / "DEAL.md").write_text(content, encoding="utf-8")


def _write_state_md(diligence: Path, created="2026-01-10T00:00:00Z"):
    """Write a STATE.md."""
    content = f"""---
created: "{created}"
last_modified: "{date.today().isoformat()}T00:00:00Z"
---

# State
"""
    (diligence / "STATE.md").write_text(content, encoding="utf-8")


def _write_config_json(diligence: Path):
    """Write a config.json."""
    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 1.0,
        "recent_window_days": 14,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )


def _write_workstreams_md(diligence: Path, names=None):
    """Write a WORKSTREAMS.md with given workstream names."""
    if names is None:
        names = ["financial", "legal"]
    lines = ["# Workstreams", ""]
    for name in names:
        lines.append(f"## {name}")
        lines.append("```yaml")
        lines.append(f"name: {name}")
        lines.append("status: active")
        lines.append("```")
        lines.append("")
    (diligence / "WORKSTREAMS.md").write_text("\n".join(lines), encoding="utf-8")


def _write_truth_md(diligence: Path):
    """Write a TRUTH.md with facts for financial and legal workstreams."""
    today = date.today().isoformat()
    old_date = (date.today() - timedelta(days=5)).isoformat()
    content = f"""# Truth

## annual_revenue
```yaml
value: "$5M"
source: SRC-001
date: "{today}"
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
  reason: "Needs verification"
  date: "{old_date}"
```
"""
    (diligence / "TRUTH.md").write_text(content, encoding="utf-8")


def _write_sources_md(diligence: Path):
    """Write a SOURCES.md with two sources."""
    content = """# Sources

## SRC-001
```yaml
path: sources/financials.xlsx
date_received: "2026-04-01"
parties:
  - seller
workstream_tags:
  - financial
  - legal
```

## SRC-002
```yaml
path: sources/contract.pdf
date_received: "2026-03-20"
parties:
  - seller
workstream_tags:
  - legal
```
"""
    (diligence / "SOURCES.md").write_text(content, encoding="utf-8")


def _write_artifacts_md(diligence: Path):
    """Write ARTIFACTS.md with artifacts referencing truth keys."""
    old_refresh = (date.today() - timedelta(days=10)).isoformat()
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

## reports/legal-summary.docx
```yaml
workstream: legal
registered: "2026-03-01"
last_refreshed: "{old_refresh}"
references:
  - "employee_count"
  - "contract_term"
scanner_findings: []
notes: ""
```
"""
    (diligence / "ARTIFACTS.md").write_text(content, encoding="utf-8")


def _write_questions_md(diligence: Path, count=3):
    """Write QUESTIONS.md with open and answered questions."""
    today = date.today().isoformat()
    recent = (date.today() - timedelta(days=2)).isoformat()
    lines = ["# Questions", ""]

    # Q-001: open, gate, financial
    lines.extend([
        "## Q-001",
        "```yaml",
        f'question: "Revenue changed from $2M to $5M. Which value is correct?"',
        "workstream: financial",
        "owner: self",
        "status: open",
        f'date_raised: "{recent}"',
        "context:",
        "  key: annual_revenue",
        "  new_value: $5M",
        "  old_value: $2M",
        "  type: gate_rejection",
        "```",
        "",
    ])

    # Q-002: answered
    lines.extend([
        "## Q-002",
        "```yaml",
        'question: "What is the customer churn rate?"',
        "workstream: financial",
        "owner: principal",
        "status: answered",
        f'date_raised: "{recent}"',
        f'answer: "Monthly churn is 2.5%"',
        "answer_source: SRC-001",
        f'date_answered: "{today}"',
        "```",
        "",
    ])

    # Q-003 through Q-00N: open, manual, legal
    for i in range(3, count + 1):
        lines.extend([
            f"## Q-{i:03d}",
            "```yaml",
            f'question: "Legal question number {i} that is fairly long to test truncation behavior"',
            "workstream: legal",
            "owner: counsel",
            "status: open",
            f'date_raised: "{recent}"',
            "```",
            "",
        ])

    (diligence / "QUESTIONS.md").write_text("\n".join(lines), encoding="utf-8")


@pytest.fixture
def populated_deal(tmp_path):
    """Create a fully populated .diligence/ directory for status tests."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()
    _write_deal_md(diligence)
    _write_state_md(diligence)
    _write_config_json(diligence)
    _write_workstreams_md(diligence)
    _write_truth_md(diligence)
    _write_sources_md(diligence)
    _write_artifacts_md(diligence)
    _write_questions_md(diligence, count=3)
    return tmp_path


@pytest.fixture
def pre_loi_deal(tmp_path):
    """Create a pre-LOI .diligence/ directory."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()
    _write_deal_md(diligence, stage="pre-LOI", loi_date="")
    _write_state_md(diligence, created="2026-03-01T00:00:00Z")
    _write_config_json(diligence)
    _write_workstreams_md(diligence)
    _write_truth_md(diligence)
    _write_sources_md(diligence)
    _write_artifacts_md(diligence)
    _write_questions_md(diligence, count=2)
    return tmp_path


@pytest.fixture
def many_questions_deal(tmp_path):
    """Create a deal with >5 open questions to test truncation."""
    diligence = tmp_path / ".diligence"
    diligence.mkdir()
    _write_deal_md(diligence)
    _write_state_md(diligence)
    _write_config_json(diligence)
    _write_workstreams_md(diligence)
    _write_truth_md(diligence)
    _write_sources_md(diligence)
    _write_artifacts_md(diligence)
    _write_questions_md(diligence, count=8)
    return tmp_path


@pytest.fixture
def runner():
    return CliRunner()


class TestStatusHeader:
    """Tests for the deal header section."""

    def test_post_loi_header(self, populated_deal, runner):
        """Post-LOI deal shows deal code, target name, stage, LOI date, days in diligence."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "TEST" in result.output
        assert "Target" in result.output
        assert "Target Legal" in result.output
        assert "post-LOI" in result.output
        assert "2026-01-15" in result.output
        assert "days in diligence" in result.output

    def test_pre_loi_header(self, pre_loi_deal, runner):
        """Pre-LOI deal shows stage and 'days tracking' instead of 'days in diligence'."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(pre_loi_deal)},
        )
        assert result.exit_code == 0
        assert "pre-LOI" in result.output
        assert "days tracking" in result.output
        assert "days in diligence" not in result.output


class TestStatusWorkstreams:
    """Tests for the workstreams section."""

    def test_workstreams_shown(self, populated_deal, runner):
        """Workstreams section shows one line per workstream with inline counts."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "financial" in result.output
        assert "legal" in result.output
        assert "facts" in result.output


class TestStatusStaleArtifacts:
    """Tests for the stale artifacts section."""

    def test_stale_artifacts_shown(self, populated_deal, runner):
        """Stale artifacts section shows artifact path and fact count."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # The financial model references annual_revenue which was updated today,
        # so it should be stale (fact date > last_refreshed)
        assert "financial-model.xlsx" in result.output
        assert "facts changed" in result.output


class TestStatusOpenQuestions:
    """Tests for the open questions section."""

    def test_open_questions_shown(self, populated_deal, runner):
        """Open questions section shows question IDs with origin tags."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "Q-001" in result.output
        assert "[gate]" in result.output
        assert "[manual]" in result.output

    def test_truncation_at_five(self, many_questions_deal, runner):
        """More than 5 open questions shows 'and N more' truncation."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(many_questions_deal)},
        )
        assert result.exit_code == 0
        assert "and" in result.output
        assert "more" in result.output


class TestStatusRecentActivity:
    """Tests for the recent activity section."""

    def test_recent_activity_shown(self, populated_deal, runner):
        """Recent activity section shows verb-past-tense format."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        # Should show some activity from truth facts, sources, etc.
        # Check for common activity verbs
        output = result.output
        has_activity = (
            "set fact" in output
            or "ingested" in output
            or "registered" in output
            or "raised" in output
        )
        assert has_activity, f"No activity verbs found in output:\n{output}"


class TestStatusSummary:
    """Tests for the summary/attention line."""

    def test_summary_line(self, populated_deal, runner):
        """Summary line shows 'N items need attention' at bottom."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        assert "items need attention" in result.output


class TestStatusJson:
    """Tests for --json output."""

    def test_json_output_valid(self, populated_deal, runner):
        """--json outputs valid JSON with expected keys."""
        result = runner.invoke(
            status_cmd,
            ["--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "deal" in data
        assert "workstreams" in data
        assert "stale_artifacts" in data
        assert "open_questions" in data
        assert "recent_activity" in data
        assert "attention_count" in data

    def test_json_deal_has_fields(self, populated_deal, runner):
        """JSON deal section has deal_code, target, stage."""
        result = runner.invoke(
            status_cmd,
            ["--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        data = json.loads(result.output)
        deal = data["deal"]
        assert deal["deal_code"] == "TEST"
        assert deal["target_common_name"] == "Target"
        assert deal["deal_stage"] == "post-LOI"


class TestStatusVerbose:
    """Tests for --verbose flag."""

    def test_verbose_removes_truncation(self, many_questions_deal, runner):
        """--verbose shows all items without truncation."""
        result = runner.invoke(
            status_cmd,
            ["--verbose"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(many_questions_deal)},
        )
        assert result.exit_code == 0
        # With 8 questions (7 open + 1 answered), all open should appear
        # No "and N more" line
        lines = result.output.strip().split("\n")
        more_lines = [l for l in lines if "and" in l and "more" in l]
        assert len(more_lines) == 0, f"Found truncation in verbose mode: {more_lines}"


class TestStatusExitCode:
    """Tests for exit code behavior."""

    def test_success_exits_zero(self, populated_deal, runner):
        """status exits 0 on success."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(populated_deal)},
        )
        assert result.exit_code == 0

    def test_no_diligence_dir_errors(self, tmp_path, runner):
        """status outside .diligence/ directory errors."""
        result = runner.invoke(
            status_cmd,
            [],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(tmp_path)},
        )
        assert result.exit_code != 0


class TestStatusConfigWindowDays:
    """Tests for config.recent_window_days being read by status command."""

    def test_status_reads_config_window_days(self, tmp_path, runner):
        """Changing recent_window_days in config.json affects which events appear in recent activity.

        Sets window to 3 days. Creates a source from 5 days ago (outside window)
        and a source from 2 days ago (inside window). Only the 2-day-old source
        should appear in recent activity.
        """
        diligence = tmp_path / ".diligence"
        diligence.mkdir()

        # Config with narrow 3-day window
        config = {
            "schema_version": 1,
            "deal_code": "TEST",
            "created": "2026-01-01T00:00:00Z",
            "anchor_tolerance_pct": 1.0,
            "recent_window_days": 3,
            "workstreams": ["financial"],
        }
        (diligence / "config.json").write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )

        _write_deal_md(diligence)
        _write_state_md(diligence)
        _write_workstreams_md(diligence, names=["financial"])

        # Empty artifacts and questions
        (diligence / "ARTIFACTS.md").write_text("# Artifacts\n", encoding="utf-8")
        (diligence / "QUESTIONS.md").write_text("# Questions\n", encoding="utf-8")

        # Truth: empty (no facts)
        (diligence / "TRUTH.md").write_text("# Truth\n", encoding="utf-8")

        # Sources: one from 5 days ago, one from 2 days ago
        old_date = (date.today() - timedelta(days=5)).isoformat()
        recent_date = (date.today() - timedelta(days=2)).isoformat()
        sources_content = f"""# Sources

## SRC-OLD
```yaml
path: sources/old_doc.pdf
date_received: "{old_date}"
parties:
  - seller
workstream_tags:
  - financial
```

## SRC-NEW
```yaml
path: sources/new_doc.pdf
date_received: "{recent_date}"
parties:
  - seller
workstream_tags:
  - financial
```
"""
        (diligence / "SOURCES.md").write_text(sources_content, encoding="utf-8")

        # Run status in JSON mode to inspect recent_activity
        result = runner.invoke(
            status_cmd,
            ["--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(tmp_path)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)

        recent = data["recent_activity"]
        recent_texts = [evt["text"] for evt in recent]

        # SRC-NEW (2 days ago) should be in recent activity (within 3-day window)
        assert any("SRC-NEW" in t for t in recent_texts), (
            f"SRC-NEW should appear in recent activity with 3-day window: {recent_texts}"
        )
        # SRC-OLD (5 days ago) should NOT be in recent activity (outside 3-day window)
        assert not any("SRC-OLD" in t for t in recent_texts), (
            f"SRC-OLD should NOT appear in recent activity with 3-day window: {recent_texts}"
        )
