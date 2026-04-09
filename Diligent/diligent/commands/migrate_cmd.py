"""Stub migrate command for future schema migrations."""

import json
from pathlib import Path

import click


@click.command("migrate")
def migrate():
    """Run pending schema migrations on the deal state files."""
    diligence_dir = Path.cwd() / ".diligence"

    if not diligence_dir.is_dir():
        click.echo("No deal found. Run `diligent init` first.")
        raise SystemExit(1)

    config_path = diligence_dir / "config.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        version = config.get("schema_version", 1)
    else:
        version = 1

    click.echo(f"No migrations needed for schema version {version}")
