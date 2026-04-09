"""Tests for task command group: new, list, complete.

Tests cover TASK-01 (new), TASK-02 (list), TASK-03 (complete),
including directory-based task management, status.yaml lifecycle,
SUMMARY.md validation, and --json output.
"""

import json
import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def deal_dir(tmp_path):
    """Create a minimal .diligence/ for task command testing.

    Includes config.json, WORKSTREAMS.md with 'financial' entry,
    and workstreams/financial/ directory with CONTEXT.md and RESEARCH.md.
    """
    d = tmp_path / ".diligence"
    d.mkdir()

    # config.json
    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial"],
    }
    (d / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")

    # WORKSTREAMS.md with financial workstream
    ws_content = """# Workstreams

## financial
```yaml
name: financial
status: active
description: Financial analysis and quality of earnings
created: "2026-01-01"
```
"""
    (d / "WORKSTREAMS.md").write_text(ws_content, encoding="utf-8")

    # QUESTIONS.md (empty)
    (d / "QUESTIONS.md").write_text("# Questions\n", encoding="utf-8")

    # Create workstreams/financial/ directory
    ws_dir = d / "workstreams" / "financial"
    ws_dir.mkdir(parents=True)
    (ws_dir / "CONTEXT.md").write_text("# Financial\n", encoding="utf-8")
    (ws_dir / "RESEARCH.md").write_text("# Research\n", encoding="utf-8")

    return tmp_path


class TestTaskNew:
    """Test task new subcommand."""

    def test_creates_task_directory(self, runner, deal_dir):
        """task new creates numbered directory under workstream tasks/."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Verify revenue quality"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        tasks_dir = deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
        assert tasks_dir.is_dir()
        task_dir = tasks_dir / "001-verify-revenue-quality"
        assert task_dir.is_dir()

    def test_creates_scaffold_files(self, runner, deal_dir):
        """Created directory contains SUMMARY.md, PLAN.md, VERIFICATION.md, status.yaml."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Verify revenue quality"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        task_dir = (
            deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
            / "001-verify-revenue-quality"
        )
        assert (task_dir / "SUMMARY.md").exists()
        assert (task_dir / "PLAN.md").exists()
        assert (task_dir / "VERIFICATION.md").exists()
        assert (task_dir / "status.yaml").exists()

    def test_status_yaml_content(self, runner, deal_dir):
        """status.yaml has description, status=open, and created date."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Verify revenue quality"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        task_dir = (
            deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
            / "001-verify-revenue-quality"
        )
        data = yaml.safe_load((task_dir / "status.yaml").read_text(encoding="utf-8"))
        assert data["description"] == "Verify revenue quality"
        assert data["status"] == "open"
        assert data["created"] != ""

    def test_summary_md_has_template_content(self, runner, deal_dir):
        """SUMMARY.md has rendered template with task description."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Verify revenue quality"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        task_dir = (
            deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
            / "001-verify-revenue-quality"
        )
        content = (task_dir / "SUMMARY.md").read_text(encoding="utf-8")
        assert "Verify revenue quality" in content

    def test_second_task_gets_002(self, runner, deal_dir):
        """Second task new creates 002-another-task/."""
        from diligent.commands.task_cmd import task_cmd

        # First task
        runner.invoke(
            task_cmd,
            ["new", "financial", "First task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        # Second task
        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Another task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        tasks_dir = deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
        assert (tasks_dir / "002-another-task").is_dir()

    def test_nonexistent_workstream_exits_nonzero(self, runner, deal_dir):
        """task new with nonexistent workstream exits non-zero."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "nonexistent", "Some task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_json_output(self, runner, deal_dir):
        """task new --json returns JSON with task_id, path, workstream, description."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Verify revenue quality", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["task_id"] == "001"
        assert "path" in data
        assert data["workstream"] == "financial"
        assert data["description"] == "Verify revenue quality"

    def test_slug_generation_special_chars(self, runner, deal_dir):
        """Slug: 'Review P&L Statement (FY2024)' becomes truncated slug."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["new", "financial", "Review P&L Statement (FY2024)"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        tasks_dir = deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
        # Find the created directory
        dirs = [d for d in tasks_dir.iterdir() if d.is_dir()]
        assert len(dirs) == 1
        dir_name = dirs[0].name
        # Should start with 001-
        assert dir_name.startswith("001-")
        slug = dir_name[4:]
        # Slug should be lowercase, only alphanumeric and hyphens
        assert slug == slug.lower()
        assert all(c in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in slug)
        # Should be at most 40 chars
        assert len(slug) <= 40
        # Should contain key words
        assert "review" in slug
        assert "fy2024" in slug


class TestTaskList:
    """Test task list subcommand."""

    def test_list_with_tasks_shows_columns(self, runner, deal_dir):
        """task list shows aligned columns: ID, DESCRIPTION, STATUS."""
        from diligent.commands.task_cmd import task_cmd

        # Create two tasks
        runner.invoke(
            task_cmd,
            ["new", "financial", "First task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        runner.invoke(
            task_cmd,
            ["new", "financial", "Second task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        result = runner.invoke(
            task_cmd,
            ["list", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "001" in result.output
        assert "002" in result.output
        assert "First task" in result.output
        assert "Second task" in result.output
        assert "open" in result.output

    def test_list_summary_line(self, runner, deal_dir):
        """task list shows summary line with open/complete counts."""
        from diligent.commands.task_cmd import task_cmd

        runner.invoke(
            task_cmd,
            ["new", "financial", "First task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        runner.invoke(
            task_cmd,
            ["new", "financial", "Second task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        result = runner.invoke(
            task_cmd,
            ["list", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "2 tasks" in result.output
        assert "0 complete" in result.output
        assert "2 open" in result.output

    def test_list_no_tasks(self, runner, deal_dir):
        """task list with no tasks shows 'No tasks found in financial'."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["list", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        assert "No tasks found in financial" in result.output

    def test_list_nonexistent_workstream(self, runner, deal_dir):
        """task list with nonexistent workstream exits non-zero."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["list", "nonexistent"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code != 0

    def test_list_json_output(self, runner, deal_dir):
        """task list --json returns JSON array."""
        from diligent.commands.task_cmd import task_cmd

        runner.invoke(
            task_cmd,
            ["new", "financial", "First task"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        result = runner.invoke(
            task_cmd,
            ["list", "financial", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["id"] == "001"
        assert data[0]["description"] == "First task"
        assert data[0]["status"] == "open"


@pytest.fixture
def deal_dir_with_task(deal_dir):
    """deal_dir with a pre-created task 001 for complete testing."""
    tasks_dir = deal_dir / ".diligence" / "workstreams" / "financial" / "tasks"
    tasks_dir.mkdir(exist_ok=True)
    task_dir = tasks_dir / "001-verify-revenue"
    task_dir.mkdir()

    # status.yaml: open
    (task_dir / "status.yaml").write_text(
        'description: "Verify revenue quality"\nstatus: open\ncreated: "2026-01-01"\n',
        encoding="utf-8",
    )
    # SUMMARY.md: template only (HTML comments)
    (task_dir / "SUMMARY.md").write_text(
        "# Verify revenue quality\n\n"
        "<!-- Write your findings, analysis, and conclusions here. "
        "This file must be non-empty to mark the task complete. -->\n",
        encoding="utf-8",
    )
    (task_dir / "PLAN.md").write_text("# Plan\n", encoding="utf-8")
    (task_dir / "VERIFICATION.md").write_text("# Verification\n", encoding="utf-8")

    return deal_dir


class TestTaskComplete:
    """Test task complete subcommand."""

    def test_complete_with_nonempty_summary(self, runner, deal_dir_with_task):
        """task complete with non-empty SUMMARY.md updates status to complete."""
        from diligent.commands.task_cmd import task_cmd

        # Write real content to SUMMARY.md
        task_dir = (
            deal_dir_with_task / ".diligence" / "workstreams" / "financial"
            / "tasks" / "001-verify-revenue"
        )
        (task_dir / "SUMMARY.md").write_text(
            "# Verify revenue quality\n\nRevenue is clean. ARR recognized correctly.\n",
            encoding="utf-8",
        )

        result = runner.invoke(
            task_cmd,
            ["complete", "financial", "001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code == 0, result.output

        # Verify status.yaml updated
        data = yaml.safe_load(
            (task_dir / "status.yaml").read_text(encoding="utf-8")
        )
        assert data["status"] == "complete"

    def test_complete_with_empty_summary_exits_nonzero(self, runner, deal_dir_with_task):
        """task complete with empty SUMMARY.md exits non-zero."""
        from diligent.commands.task_cmd import task_cmd

        # Write truly empty SUMMARY.md
        task_dir = (
            deal_dir_with_task / ".diligence" / "workstreams" / "financial"
            / "tasks" / "001-verify-revenue"
        )
        (task_dir / "SUMMARY.md").write_text("", encoding="utf-8")

        result = runner.invoke(
            task_cmd,
            ["complete", "financial", "001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code != 0
        assert "SUMMARY.md" in result.output

    def test_complete_with_comments_only_exits_nonzero(self, runner, deal_dir_with_task):
        """SUMMARY.md containing only HTML comments counts as empty."""
        from diligent.commands.task_cmd import task_cmd

        # SUMMARY.md already has only template content (heading + HTML comment)
        # The fixture sets this up

        result = runner.invoke(
            task_cmd,
            ["complete", "financial", "001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code != 0
        assert "SUMMARY.md" in result.output

    def test_complete_nonexistent_task(self, runner, deal_dir_with_task):
        """task complete with nonexistent task ID exits non-zero."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["complete", "financial", "999"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code != 0
        assert "999" in result.output

    def test_complete_nonexistent_workstream(self, runner, deal_dir_with_task):
        """task complete with nonexistent workstream exits non-zero."""
        from diligent.commands.task_cmd import task_cmd

        result = runner.invoke(
            task_cmd,
            ["complete", "nonexistent", "001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code != 0

    def test_complete_already_complete_exits_nonzero(self, runner, deal_dir_with_task):
        """task complete on already-complete task exits non-zero."""
        from diligent.commands.task_cmd import task_cmd

        # Mark task as already complete
        task_dir = (
            deal_dir_with_task / ".diligence" / "workstreams" / "financial"
            / "tasks" / "001-verify-revenue"
        )
        (task_dir / "status.yaml").write_text(
            'description: "Verify revenue quality"\nstatus: complete\ncreated: "2026-01-01"\n',
            encoding="utf-8",
        )
        (task_dir / "SUMMARY.md").write_text(
            "# Verify revenue quality\n\nDone.\n", encoding="utf-8"
        )

        result = runner.invoke(
            task_cmd,
            ["complete", "financial", "001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code != 0
        assert "already complete" in result.output

    def test_complete_json_output(self, runner, deal_dir_with_task):
        """task complete --json returns JSON with updated task status."""
        from diligent.commands.task_cmd import task_cmd

        # Write real content
        task_dir = (
            deal_dir_with_task / ".diligence" / "workstreams" / "financial"
            / "tasks" / "001-verify-revenue"
        )
        (task_dir / "SUMMARY.md").write_text(
            "# Verify revenue quality\n\nRevenue verified.\n", encoding="utf-8"
        )

        result = runner.invoke(
            task_cmd,
            ["complete", "financial", "001", "--json"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["task_id"] == "001"
        assert data["status"] == "complete"
        assert data["workstream"] == "financial"

    def test_complete_then_list_shows_complete(self, runner, deal_dir_with_task):
        """After complete, task list shows task as complete."""
        from diligent.commands.task_cmd import task_cmd

        # Write real content
        task_dir = (
            deal_dir_with_task / ".diligence" / "workstreams" / "financial"
            / "tasks" / "001-verify-revenue"
        )
        (task_dir / "SUMMARY.md").write_text(
            "# Verify revenue quality\n\nRevenue verified.\n", encoding="utf-8"
        )

        # Complete
        runner.invoke(
            task_cmd,
            ["complete", "financial", "001"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )

        # List
        result = runner.invoke(
            task_cmd,
            ["list", "financial"],
            catch_exceptions=False,
            env={"DILIGENT_CWD": str(deal_dir_with_task)},
        )
        assert result.exit_code == 0, result.output
        assert "complete" in result.output
        assert "1 complete" in result.output
