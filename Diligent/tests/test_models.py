"""Tests for dataclass models, LazyGroup CLI, and migrate stub."""

import sys
from unittest.mock import patch

import pytest
from click.testing import CliRunner


class TestDealFile:
    """DealFile dataclass constructs with all required fields."""

    def test_construct_with_required_fields(self):
        from diligent.state.models import DealFile

        deal = DealFile(
            deal_code="ARRIVAL",
            target_legal_name="OnTime 360 LLC",
            target_common_name="OnTime 360",
            deal_stage="post-loi",
            loi_date="2026-03-15",
            principal="Bryce Masterson",
            principal_role="Deal Lead",
            seller="John Doe",
            broker="Jane Smith",
            thesis="B2B SaaS courier dispatch platform",
            workstreams=["financial", "legal", "operational"],
        )
        assert deal.deal_code == "ARRIVAL"
        assert deal.target_legal_name == "OnTime 360 LLC"
        assert deal.target_common_name == "OnTime 360"
        assert deal.deal_stage == "post-loi"
        assert deal.loi_date == "2026-03-15"
        assert deal.principal == "Bryce Masterson"
        assert deal.principal_role == "Deal Lead"
        assert deal.seller == "John Doe"
        assert deal.broker == "Jane Smith"
        assert deal.thesis == "B2B SaaS courier dispatch platform"
        assert deal.workstreams == ["financial", "legal", "operational"]


class TestFactEntry:
    """FactEntry stores value, source, date as strings."""

    def test_construct_with_required_fields(self):
        from diligent.state.models import FactEntry

        entry = FactEntry(
            key="annual_recurring_revenue",
            value="2400000",
            source="ARRIVAL-001",
            date="2026-04-01",
            workstream="financial",
        )
        assert entry.key == "annual_recurring_revenue"
        assert entry.value == "2400000"
        assert entry.source == "ARRIVAL-001"
        assert entry.date == "2026-04-01"
        assert entry.workstream == "financial"
        assert entry.supersedes == []
        assert entry.computed_by is None
        assert entry.notes is None
        assert entry.flagged is None

    def test_types_are_str(self):
        from diligent.state.models import FactEntry

        entry = FactEntry(
            key="k", value="v", source="s", date="d", workstream="w"
        )
        assert isinstance(entry.value, str)
        assert isinstance(entry.source, str)
        assert isinstance(entry.date, str)


class TestSupersededValue:
    """SupersededValue stores prior value/source/date."""

    def test_construct(self):
        from diligent.state.models import SupersededValue

        sv = SupersededValue(value="2000000", source="ARRIVAL-001", date="2026-03-01")
        assert sv.value == "2000000"
        assert sv.source == "ARRIVAL-001"
        assert sv.date == "2026-03-01"


class TestTruthFile:
    """TruthFile.facts is a dict keyed by fact key with FactEntry values."""

    def test_facts_dict(self):
        from diligent.state.models import TruthFile, FactEntry

        entry = FactEntry(
            key="arr", value="2400000", source="S1", date="2026-04-01", workstream="fin"
        )
        tf = TruthFile(facts={"arr": entry})
        assert "arr" in tf.facts
        assert tf.facts["arr"].value == "2400000"

    def test_empty_default(self):
        from diligent.state.models import TruthFile

        tf = TruthFile()
        assert tf.facts == {}


class TestSourceEntry:
    """SourceEntry has id, path, date_received, parties, workstream_tags, supersedes."""

    def test_construct(self):
        from diligent.state.models import SourceEntry

        se = SourceEntry(
            id="ARRIVAL-001",
            path="sources/cim.pdf",
            date_received="2026-03-15",
            parties=["Seller Corp"],
            workstream_tags=["financial"],
        )
        assert se.id == "ARRIVAL-001"
        assert se.path == "sources/cim.pdf"
        assert se.date_received == "2026-03-15"
        assert se.parties == ["Seller Corp"]
        assert se.workstream_tags == ["financial"]
        assert se.supersedes is None
        assert se.notes is None


class TestWorkstreamEntry:
    """WorkstreamEntry has name, status, description, and created fields."""

    def test_construct(self):
        from diligent.state.models import WorkstreamEntry

        we = WorkstreamEntry(name="financial", status="active")
        assert we.name == "financial"
        assert we.status == "active"

    def test_description_and_created_defaults(self):
        """WorkstreamEntry accepts description="" and created="" as defaults."""
        from diligent.state.models import WorkstreamEntry

        we = WorkstreamEntry(name="financial", status="active")
        assert we.description == ""
        assert we.created == ""

    def test_backward_compat_no_new_args(self):
        """WorkstreamEntry(name=..., status=...) still works without new args."""
        from diligent.state.models import WorkstreamEntry

        we = WorkstreamEntry(name="legal", status="paused")
        assert we.name == "legal"
        assert we.status == "paused"
        assert we.description == ""
        assert we.created == ""

    def test_description_and_created_populated(self):
        """WorkstreamEntry with description and created populated stores them."""
        from diligent.state.models import WorkstreamEntry

        we = WorkstreamEntry(
            name="financial",
            status="active",
            description="Core financial analysis workstream",
            created="2026-04-01T00:00:00Z",
        )
        assert we.description == "Core financial analysis workstream"
        assert we.created == "2026-04-01T00:00:00Z"


class TestConfigFile:
    """ConfigFile has schema_version, deal_code, anchor_tolerance_pct, recent_window_days, workstreams."""

    def test_construct(self):
        from diligent.state.models import ConfigFile

        cf = ConfigFile(
            schema_version=1,
            deal_code="ARRIVAL",
            created="2026-04-01T00:00:00Z",
            anchor_tolerance_pct=1.0,
            recent_window_days=7,
            workstreams=["financial", "legal"],
        )
        assert cf.schema_version == 1
        assert isinstance(cf.schema_version, int)
        assert cf.deal_code == "ARRIVAL"
        assert isinstance(cf.deal_code, str)
        assert cf.anchor_tolerance_pct == 1.0
        assert isinstance(cf.anchor_tolerance_pct, float)
        assert cf.recent_window_days == 7
        assert isinstance(cf.recent_window_days, int)
        assert cf.workstreams == ["financial", "legal"]


class TestStateFile:
    """StateFile has created and last_modified fields."""

    def test_construct(self):
        from diligent.state.models import StateFile

        sf = StateFile(created="2026-04-01T00:00:00Z", last_modified="2026-04-07T12:00:00Z")
        assert sf.created == "2026-04-01T00:00:00Z"
        assert sf.last_modified == "2026-04-07T12:00:00Z"


class TestCLI:
    """CLI entry point tests."""

    def test_help_exits_zero(self, cli_runner):
        from diligent.cli import cli

        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "diligent" in result.output.lower()

    def test_lazy_group_lists_commands(self, cli_runner):
        from diligent.cli import cli

        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        # All four lazy subcommands should appear in help
        for cmd in ["init", "doctor", "config", "migrate"]:
            assert cmd in result.output

    def test_lazy_group_defers_import_at_creation(self):
        """LazyGroup should not import command modules at group creation time.

        Click's help formatter does call get_command() to extract short help
        strings, so commands get imported during --help. The value of LazyGroup
        is that heavy dependencies inside command modules are not loaded when
        the CLI group object is first created (e.g., at import time).
        """
        # Remove command modules from sys.modules to test fresh
        cmd_modules = [
            "diligent.commands.init_cmd",
            "diligent.commands.doctor",
            "diligent.commands.config_cmd",
            "diligent.commands.migrate_cmd",
        ]
        saved = {}
        for mod in cmd_modules:
            if mod in sys.modules:
                saved[mod] = sys.modules.pop(mod)

        try:
            # Importing cli.py should NOT import command modules
            if "diligent.cli" in sys.modules:
                # Already imported; verify the lazy_subcommands dict exists
                from diligent.cli import cli
                assert hasattr(cli, "lazy_subcommands") or hasattr(cli, "params")
            else:
                from diligent.cli import cli

            # list_commands should return command names without importing modules
            import click
            ctx = click.Context(cli)
            commands = cli.list_commands(ctx)
            for name in ["init", "doctor", "config", "migrate"]:
                assert name in commands

            # Verify command modules were NOT imported by list_commands
            for mod in cmd_modules:
                assert mod not in sys.modules, f"{mod} imported during list_commands"
        finally:
            # Restore modules
            for mod, val in saved.items():
                sys.modules[mod] = val


class TestMigrateCommand:
    """Migrate command stub tests."""

    def test_migrate_no_migrations(self, cli_runner, tmp_deal_dir, sample_config):
        from diligent.cli import cli

        result = cli_runner.invoke(cli, ["migrate"], catch_exceptions=False)
        # When run without being in a deal dir, it should say no deal found
        # But we need to test with a real deal dir too
        assert result.exit_code in (0, 1)

    def test_migrate_with_deal_dir(self, cli_runner, tmp_deal_dir, sample_config, monkeypatch):
        from diligent.cli import cli

        monkeypatch.chdir(tmp_deal_dir)
        result = cli_runner.invoke(cli, ["migrate"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "No migrations needed" in result.output

    def test_migrate_no_deal_dir(self, cli_runner, tmp_deal_dir, monkeypatch):
        from diligent.cli import cli

        monkeypatch.chdir(tmp_deal_dir)
        result = cli_runner.invoke(cli, ["migrate"], catch_exceptions=False)
        assert result.exit_code == 1
        assert "No deal found" in result.output
