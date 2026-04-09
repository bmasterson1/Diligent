"""Dual output helpers: plain text and JSON.

Every command produces structured data internally,
rendered as plain text by default or JSON with --json.
"""

import json
from typing import Any

import click


def output_result(data: Any, json_mode: bool) -> None:
    """Render a result as plain text or JSON.

    Args:
        data: The data to render. If json_mode, serialized with json.dumps.
              Otherwise, converted to string and echoed.
        json_mode: If True, output as formatted JSON.
    """
    if json_mode:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(str(data))


def output_findings(findings: list[dict], json_mode: bool) -> None:
    """Render diagnostic findings as plain text or JSON.

    Used by doctor-style commands that produce lists of findings
    with severity, file, location, description, and fix fields.

    Args:
        findings: List of finding dicts with keys: severity, file,
                  location, description, fix.
        json_mode: If True, output as formatted JSON array.
    """
    if json_mode:
        click.echo(json.dumps(findings, indent=2))
        return

    for f in findings:
        click.echo(
            f"{f['severity']}: {f['file']}:{f['location']} - {f['description']}"
        )
        click.echo(f"  Fix: {f['fix']}")

    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warnings = sum(1 for f in findings if f["severity"] == "WARNING")
    info = sum(1 for f in findings if f["severity"] == "INFO")
    click.echo(f"\n{errors} errors, {warnings} warnings, {info} info")
