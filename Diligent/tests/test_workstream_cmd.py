"""Tests for workstream command group: new, list, show.

Tests cover WS-01 (new), WS-02 (list), WS-03 (show), WS-04 (templates),
WS-05 (init integration), WS-06 (hand-edits), and --json output for all.
"""

import json
import os
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def deal_dir(tmp_path):
    """Create a minimal .diligence/ for workstream command testing."""
    d = tmp_path / ".diligence"
    d.mkdir()

    # config.json
    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    (d / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    # WORKSTREAMS.md with two workstreams
    ws_content = """# Workstreams

## financial
```yaml
name: financial
status: active
description: Financial analysis and quality of earnings
created: "2026-01-01"
```

## legal
```yaml
name: legal
status: active
description: Legal structure, contracts, and regulatory
created: "2026-01-01"
```
"""
    (d / "WORKSTREAMS.md").write_text(ws_content, encoding="utf-8")

    # QUESTIONS.md (empty)
    (d / "QUESTIONS.md").write_text("# Questions\n", encoding="utf-8")

    # TRUTH.md (empty)
    (d / "TRUTH.md").write_text("# Truth\n", encoding="utf-8")

    # ARTIFACTS.md (empty)
    (d / "ARTIFACTS.md").write_text("# Artifacts\n", encoding="utf-8")

    # SOURCES.md (empty)
    (d / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")

    # Create workstreams directory
    (d / "workstreams").mkdir()

    return tmp_path


class TestWorkstreamNew:
    """Test workstream new subcommand."""

    def test_creates_directory_with_context_and_research(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["new", "custom-ws"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        ws_dir = deal_dir / ".diligence" / "workstreams" / "custom-ws"
        assert ws_dir.is_dir()
        assert (ws_dir / "CONTEXT.md").exists()
        assert (ws_dir / "RESEARCH.md").exists()

    def test_tailored_template_for_financial(self, runner, deal_dir):
        """financial workstream uses tailored CONTEXT.md with Revenue Quality etc."""
        from diligent.commands.workstream_cmd import workstream_cmd

        # Remove financial from WORKSTREAMS.md to avoid duplicate
        ws_content = """# Workstreams

## legal
```yaml
name: legal
status: active
```
"""
        (deal_dir / ".diligence" / "WORKSTREAMS.md").write_text(ws_content, encoding="utf-8")

        result = runner.invoke(
            workstream_cmd,
            ["new", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        ctx_path = deal_dir / ".diligence" / "workstreams" / "financial" / "CONTEXT.md"
        content = ctx_path.read_text(encoding="utf-8")
        assert "Revenue Quality" in content
        assert "Cost Structure" in content

    def test_generic_template_for_custom_name(self, runner, deal_dir):
        """Custom workstream names get generic CONTEXT.md with Scope, Key Contacts."""
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["new", "custom-ws"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        ctx_path = deal_dir / ".diligence" / "workstreams" / "custom-ws" / "CONTEXT.md"
        content = ctx_path.read_text(encoding="utf-8")
        assert "Scope" in content
        assert "Key Contacts" in content
        assert "Open Areas" in content

    def test_research_md_uses_generic_template(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        # Remove financial to avoid duplicate
        ws_content = "# Workstreams\n"
        (deal_dir / ".diligence" / "WORKSTREAMS.md").write_text(ws_content, encoding="utf-8")

        result = runner.invoke(
            workstream_cmd,
            ["new", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        research_path = deal_dir / ".diligence" / "workstreams" / "financial" / "RESEARCH.md"
        content = research_path.read_text(encoding="utf-8")
        assert "Research" in content

    def test_appends_workstream_entry(self, runner, deal_dir):
        """workstream new appends entry to WORKSTREAMS.md with status=active."""
        from diligent.commands.workstream_cmd import workstream_cmd
        from diligent.state.workstreams import read_workstreams

        result = runner.invoke(
            workstream_cmd,
            ["new", "custom-ws"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        ws = read_workstreams(deal_dir / ".diligence" / "WORKSTREAMS.md")
        names = [w.name for w in ws.workstreams]
        assert "custom-ws" in names
        custom = [w for w in ws.workstreams if w.name == "custom-ws"][0]
        assert custom.status == "active"
        assert custom.created != ""

    def test_template_workstream_has_description(self, runner, deal_dir):
        """Template workstreams get a description in WORKSTREAMS.md."""
        from diligent.commands.workstream_cmd import workstream_cmd
        from diligent.state.workstreams import read_workstreams

        # Remove financial to avoid dup
        ws_content = "# Workstreams\n"
        (deal_dir / ".diligence" / "WORKSTREAMS.md").write_text(ws_content, encoding="utf-8")

        result = runner.invoke(
            workstream_cmd,
            ["new", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        ws = read_workstreams(deal_dir / ".diligence" / "WORKSTREAMS.md")
        financial = [w for w in ws.workstreams if w.name == "financial"][0]
        assert financial.description != ""

    def test_rejects_duplicate_name(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["new", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_rejects_invalid_name(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["new", "Bad Name!"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_rejects_uppercase_name(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["new", "Financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_json_output(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["new", "custom-ws", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["name"] == "custom-ws"
        assert "path" in data
        assert "files_created" in data


class TestWorkstreamList:
    """Test workstream list subcommand."""

    def test_shows_workstreams_with_columns(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "financial" in result.output
        assert "legal" in result.output
        assert "active" in result.output

    def test_shows_summary_line(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "2 workstreams" in result.output

    def test_shows_task_and_question_counts(self, runner, deal_dir):
        """List shows task count and question count columns."""
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        # With no tasks or questions, counts should be 0
        assert "0" in result.output

    def test_json_output(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["list", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] in ("financial", "legal")

    def test_empty_workstreams(self, runner, deal_dir):
        """List with no workstreams shows helpful message."""
        from diligent.commands.workstream_cmd import workstream_cmd

        (deal_dir / ".diligence" / "WORKSTREAMS.md").write_text(
            "# Workstreams\n", encoding="utf-8"
        )
        result = runner.invoke(
            workstream_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "No workstreams found" in result.output


class TestWorkstreamShow:
    """Test workstream show subcommand."""

    def test_shows_workstream_detail(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["show", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "financial" in result.output
        assert "active" in result.output

    def test_shows_aggregated_counts(self, runner, deal_dir):
        """show displays task, question, fact, and artifact counts."""
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["show", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        # All zeros for empty deal
        output = result.output.lower()
        assert "task" in output
        assert "question" in output
        assert "fact" in output
        assert "artifact" in output

    def test_nonexistent_workstream_exits_nonzero(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["show", "nonexistent"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_json_output(self, runner, deal_dir):
        from diligent.commands.workstream_cmd import workstream_cmd

        result = runner.invoke(
            workstream_cmd,
            ["show", "financial", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["name"] == "financial"
        assert "tasks_open" in data
        assert "tasks_complete" in data
        assert "questions" in data
        assert "facts" in data
        assert "artifacts" in data


class TestHandEdits:
    """Test WS-06: hand-edited WORKSTREAMS.md entries are readable."""

    def test_minimal_entry_without_description_or_created(self, runner, deal_dir):
        """Entries with only name and status should be readable."""
        from diligent.commands.workstream_cmd import workstream_cmd

        ws_content = """# Workstreams

## manual-ws
```yaml
name: manual-ws
status: active
```
"""
        (deal_dir / ".diligence" / "WORKSTREAMS.md").write_text(
            ws_content, encoding="utf-8"
        )
        result = runner.invoke(
            workstream_cmd,
            ["list"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "manual-ws" in result.output

    def test_show_hand_edited_entry(self, runner, deal_dir):
        """show works with minimal hand-edited entry."""
        from diligent.commands.workstream_cmd import workstream_cmd

        ws_content = """# Workstreams

## manual-ws
```yaml
name: manual-ws
status: on-hold
```
"""
        (deal_dir / ".diligence" / "WORKSTREAMS.md").write_text(
            ws_content, encoding="utf-8"
        )
        # Create workstreams dir for the entry
        (deal_dir / ".diligence" / "workstreams" / "manual-ws").mkdir(parents=True, exist_ok=True)

        result = runner.invoke(
            workstream_cmd,
            ["show", "manual-ws"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "on-hold" in result.output
