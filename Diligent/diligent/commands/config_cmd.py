"""diligent config get/set commands.

Reads and writes values in .diligence/config.json.
"""

import json
from pathlib import Path

import click

from diligent.helpers.formatting import output_result


def _coerce_value(value: str):
    """Coerce string value to int, float, or keep as string.

    Type coercion: if value looks like int, convert. If looks like
    float, convert. Otherwise string.
    """
    # Try int first
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Boolean-like strings
    if value.lower() in ("true", "false"):
        return value.lower() == "true"

    return value


def _get_config_path() -> Path:
    """Return path to .diligence/config.json."""
    return Path.cwd() / ".diligence" / "config.json"


def _read_config_dict(config_path: Path) -> dict:
    """Read config.json as a plain dict."""
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_config_dict(config_path: Path, data: dict) -> None:
    """Write config dict to config.json via atomic_write."""
    from diligent.helpers.io import atomic_write
    content = json.dumps(data, indent=2) + "\n"
    atomic_write(config_path, content)


@click.group("config")
def config_cmd():
    """Get or set deal configuration values."""
    pass


@config_cmd.command("get")
@click.argument("key")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output structured JSON.")
def config_get(key, json_mode):
    """Get a configuration value by key."""
    config_path = _get_config_path()

    if not config_path.exists():
        click.echo("ERROR: No deal found. Run `diligent init` first.")
        raise SystemExit(1)

    data = _read_config_dict(config_path)

    if key not in data:
        click.echo(f"ERROR: Key '{key}' not found in config.json.")
        raise SystemExit(1)

    value = data[key]

    if json_mode:
        output_result({"key": key, "value": value}, json_mode=True)
    else:
        click.echo(str(value))


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output structured JSON.")
def config_set(key, value, json_mode):
    """Set a configuration value."""
    config_path = _get_config_path()

    if not config_path.exists():
        click.echo("ERROR: No deal found. Run `diligent init` first.")
        raise SystemExit(1)

    data = _read_config_dict(config_path)
    coerced = _coerce_value(value)
    data[key] = coerced
    _write_config_dict(config_path, data)

    if json_mode:
        output_result({"key": key, "value": coerced}, json_mode=True)
    else:
        click.echo(f"{key} = {coerced}")
