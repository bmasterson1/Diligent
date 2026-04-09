"""LazyGroup CLI entry point for diligent.

Uses lazy subcommand loading to keep startup under 200ms.
Heavy imports (openpyxl, pdfplumber, etc.) are deferred
until the specific command that needs them is invoked.
"""

import importlib

import click

from diligent import __version__


class LazyGroup(click.Group):
    """Click Group subclass that defers subcommand module imports until invoked."""

    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_name):
        import_path = self.lazy_subcommands[cmd_name]
        modname, cmdname = import_path.rsplit(".", 1)
        mod = importlib.import_module(modname)
        return getattr(mod, cmdname)


@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "init": "diligent.commands.init_cmd.init_cmd",
        "doctor": "diligent.commands.doctor.doctor",
        "config": "diligent.commands.config_cmd.config_cmd",
        "install": "diligent.commands.install_cmd.install_cmd",
        "migrate": "diligent.commands.migrate_cmd.migrate",
        "ingest": "diligent.commands.sources_cmd.ingest_cmd",
        "reconcile": "diligent.commands.reconcile_cmd.reconcile_cmd",
        "sources": "diligent.commands.sources_cmd.sources_cmd",
        "truth": "diligent.commands.truth_cmd.truth_cmd",
        "artifact": "diligent.commands.artifact_cmd.artifact_cmd",
        "workstream": "diligent.commands.workstream_cmd.workstream_cmd",
        "task": "diligent.commands.task_cmd.task_cmd",
        "ask": "diligent.commands.question_cmd.ask_cmd",
        "answer": "diligent.commands.question_cmd.answer_cmd",
        "questions": "diligent.commands.question_cmd.questions_cmd",
        "status": "diligent.commands.status_cmd.status_cmd",
        "handoff": "diligent.commands.handoff_cmd.handoff_cmd",
    },
)
@click.version_option(version=__version__)
def cli():
    """diligent: due diligence state management."""
    pass
