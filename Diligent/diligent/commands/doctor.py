"""diligent doctor command.

Validates deal state file integrity with three check layers:
  1. Existence: all 8 files present
  2. Parse: each file parses without error
  3. Cross-references: inter-file references are valid

Report-only. Never mutates state files.
"""

import json
import os
import re
from pathlib import Path

import click
import yaml

from diligent.helpers.formatting import output_findings


EXPECTED_FILES = [
    "config.json",
    "DEAL.md",
    "TRUTH.md",
    "SOURCES.md",
    "WORKSTREAMS.md",
    "STATE.md",
    "QUESTIONS.md",
    "ARTIFACTS.md",
]


def _check_existence(diligence_dir: Path) -> list[dict]:
    """Layer 1: Check all 8 files exist."""
    findings = []
    for fname in EXPECTED_FILES:
        fpath = diligence_dir / fname
        if not fpath.exists():
            findings.append({
                "severity": "ERROR",
                "file": f".diligence/{fname}",
                "location": "-",
                "description": f"Missing file: {fname}",
                "fix": "Run `diligent init` to create missing files.",
            })
    return findings


def _check_parse(diligence_dir: Path) -> tuple[list[dict], dict]:
    """Layer 2: Parse each existing file.

    Returns (findings, parsed_data) where parsed_data is a dict
    of filename -> parsed object (or None if parse failed).
    """
    findings = []
    parsed = {}

    # config.json
    config_path = diligence_dir / "config.json"
    if config_path.exists():
        try:
            from diligent.state.config import read_config
            parsed["config.json"] = read_config(config_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/config.json",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # DEAL.md
    deal_path = diligence_dir / "DEAL.md"
    if deal_path.exists():
        try:
            from diligent.state.deal import read_deal
            parsed["DEAL.md"] = read_deal(deal_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/DEAL.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # TRUTH.md
    truth_path = diligence_dir / "TRUTH.md"
    if truth_path.exists():
        try:
            from diligent.state.truth import read_truth
            parsed["TRUTH.md"] = read_truth(truth_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/TRUTH.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # SOURCES.md
    sources_path = diligence_dir / "SOURCES.md"
    if sources_path.exists():
        try:
            from diligent.state.sources import read_sources
            parsed["SOURCES.md"] = read_sources(sources_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/SOURCES.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # WORKSTREAMS.md
    ws_path = diligence_dir / "WORKSTREAMS.md"
    if ws_path.exists():
        try:
            from diligent.state.workstreams import read_workstreams
            parsed["WORKSTREAMS.md"] = read_workstreams(ws_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/WORKSTREAMS.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # STATE.md
    state_path = diligence_dir / "STATE.md"
    if state_path.exists():
        try:
            from diligent.state.state_file import read_state
            parsed["STATE.md"] = read_state(state_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/STATE.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # QUESTIONS.md
    questions_path = diligence_dir / "QUESTIONS.md"
    if questions_path.exists():
        try:
            from diligent.state.questions import read_questions
            parsed["QUESTIONS.md"] = read_questions(questions_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/QUESTIONS.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    # ARTIFACTS.md
    artifacts_path = diligence_dir / "ARTIFACTS.md"
    if artifacts_path.exists():
        try:
            from diligent.state.artifacts import read_artifacts
            parsed["ARTIFACTS.md"] = read_artifacts(artifacts_path)
        except Exception as e:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/ARTIFACTS.md",
                "location": "-",
                "description": f"Parse failure: {e}",
                "fix": "Check file syntax. Compare against a known-good file.",
            })

    return findings, parsed


def _check_fenced_yaml_integrity(diligence_dir: Path) -> list[dict]:
    """Check files with fenced YAML blocks for parse errors.

    read_truth/read_sources/read_workstreams silently skip unparseable
    YAML blocks. Doctor needs to catch those as errors.
    """
    findings = []

    for fname in ("TRUTH.md", "SOURCES.md", "WORKSTREAMS.md", "QUESTIONS.md", "ARTIFACTS.md"):
        fpath = diligence_dir / fname
        if not fpath.exists():
            continue

        text = fpath.read_text(encoding="utf-8")
        # Strip HTML comments
        clean = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

        # Find H2 sections
        current_heading = None
        in_block = False
        yaml_lines = []

        for line in clean.split("\n"):
            if line.startswith("## "):
                current_heading = line[3:].strip()
                in_block = False
                yaml_lines = []
            elif current_heading is not None:
                stripped = line.strip()
                if not in_block and stripped in ("```yaml", "```yml"):
                    in_block = True
                    yaml_lines = []
                elif in_block and stripped == "```":
                    in_block = False
                    if yaml_lines:
                        yaml_text = "\n".join(yaml_lines)
                        try:
                            data = yaml.safe_load(yaml_text)
                            if not isinstance(data, dict):
                                findings.append({
                                    "severity": "ERROR",
                                    "file": f".diligence/{fname}",
                                    "location": f"## {current_heading}",
                                    "description": f"YAML block is not a mapping (got {type(data).__name__})",
                                    "fix": "Check file syntax. Compare against a known-good file.",
                                })
                        except yaml.YAMLError as e:
                            findings.append({
                                "severity": "ERROR",
                                "file": f".diligence/{fname}",
                                "location": f"## {current_heading}",
                                "description": f"Invalid YAML in fenced block: {e}",
                                "fix": "Check file syntax. Compare against a known-good file.",
                            })
                elif in_block:
                    yaml_lines.append(line)

    return findings


def _check_cross_refs(parsed: dict, diligence_dir: Path) -> list[dict]:
    """Layer 3: Cross-reference validation between parsed files."""
    findings = []

    config = parsed.get("config.json")
    deal = parsed.get("DEAL.md")
    truth = parsed.get("TRUTH.md")
    workstreams = parsed.get("WORKSTREAMS.md")

    # Get valid workstream names
    valid_workstreams = set()
    if workstreams is not None:
        valid_workstreams = {w.name for w in workstreams.workstreams}

    # Check schema_version
    if config is not None:
        if config.schema_version != 1:
            findings.append({
                "severity": "WARNING",
                "file": ".diligence/config.json",
                "location": "schema_version",
                "description": f"Unexpected schema version: {config.schema_version} (expected 1)",
                "fix": "Run `diligent migrate` to update schema.",
            })

    # Check config deal_code matches DEAL.md deal_code
    if config is not None and deal is not None:
        if config.deal_code != deal.deal_code:
            findings.append({
                "severity": "ERROR",
                "file": ".diligence/config.json",
                "location": "deal_code",
                "description": (
                    f"config.json deal_code '{config.deal_code}' does not match "
                    f"DEAL.md deal_code '{deal.deal_code}'"
                ),
                "fix": "Update deal_code in config.json or DEAL.md to match.",
            })

    # Check TRUTH.md facts reference valid workstreams
    if truth is not None and valid_workstreams:
        for key, fact in truth.facts.items():
            if fact.workstream and fact.workstream not in valid_workstreams:
                findings.append({
                    "severity": "WARNING",
                    "file": ".diligence/TRUTH.md",
                    "location": f"## {key}",
                    "description": (
                        f"Fact references unknown workstream '{fact.workstream}'"
                    ),
                    "fix": (
                        f"Check spelling. Valid workstreams: "
                        f"{', '.join(sorted(valid_workstreams))}"
                    ),
                })

    # Check ARTIFACTS.md cross-file references
    artifacts = parsed.get("ARTIFACTS.md")
    if artifacts is not None:
        truth_keys = set()
        if truth is not None:
            truth_keys = set(truth.facts.keys())

        deal_root = diligence_dir.parent

        for artifact in artifacts.artifacts:
            # Check each reference exists as a truth key
            if truth is not None:
                for ref in artifact.references:
                    if ref not in truth_keys:
                        findings.append({
                            "severity": "WARNING",
                            "file": ".diligence/ARTIFACTS.md",
                            "location": f"## {artifact.path}",
                            "description": (
                                f"Artifact references truth key '{ref}' "
                                f"not found in TRUTH.md"
                            ),
                            "fix": (
                                "Check spelling. Use `diligent truth list` "
                                "to see valid keys."
                            ),
                        })

            # Check artifact path exists on disk relative to deal root
            artifact_abs = deal_root / artifact.path.replace("/", os.sep)
            if not artifact_abs.exists():
                findings.append({
                    "severity": "WARNING",
                    "file": ".diligence/ARTIFACTS.md",
                    "location": f"## {artifact.path}",
                    "description": (
                        f"Artifact path '{artifact.path}' does not exist on disk"
                    ),
                    "fix": (
                        "File may have been moved or renamed. "
                        "Update the artifact path or remove the entry."
                    ),
                })

    # Check TRUTH.md source IDs follow {DEAL_CODE}-NNN format
    if truth is not None and config is not None:
        deal_code = config.deal_code
        for key, fact in truth.facts.items():
            if fact.source and not fact.source.startswith(f"{deal_code}-"):
                findings.append({
                    "severity": "WARNING",
                    "file": ".diligence/TRUTH.md",
                    "location": f"## {key}",
                    "description": (
                        f"Source ID '{fact.source}' does not follow "
                        f"expected format '{deal_code}-NNN'"
                    ),
                    "fix": f"Source IDs should start with '{deal_code}-'.",
                })

    return findings


@click.command("doctor")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output structured JSON findings.")
@click.option("--strict", is_flag=True, default=False, help="Treat warnings as errors (exit non-zero).")
def doctor(json_mode, strict):
    """Validate deal state file integrity and report issues."""
    diligence_dir = Path.cwd() / ".diligence"

    if not diligence_dir.is_dir():
        if json_mode:
            click.echo(json.dumps([{
                "severity": "ERROR",
                "file": ".diligence/",
                "location": "-",
                "description": "No deal found. .diligence/ directory does not exist.",
                "fix": "Run `diligent init` to create a deal.",
            }], indent=2))
        else:
            click.echo("ERROR: No deal found. Run `diligent init` first.")
        raise SystemExit(1)

    findings = []

    # Layer 1: Existence
    findings.extend(_check_existence(diligence_dir))

    # Layer 2: Parse (only check files that exist)
    parse_findings, parsed = _check_parse(diligence_dir)
    findings.extend(parse_findings)

    # Layer 2b: Deep fenced YAML integrity check
    findings.extend(_check_fenced_yaml_integrity(diligence_dir))

    # Layer 3: Cross-references (only if we have parsed data)
    if parsed:
        findings.extend(_check_cross_refs(parsed, diligence_dir))

    # Output
    output_findings(findings, json_mode)

    # Exit code
    errors = sum(1 for f in findings if f["severity"] == "ERROR")
    warnings = sum(1 for f in findings if f["severity"] == "WARNING")

    if errors > 0:
        raise SystemExit(1)
    if strict and warnings > 0:
        raise SystemExit(1)
