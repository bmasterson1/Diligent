"""diligent init command.

Scaffolds a .diligence/ directory with all 8 state files from templates.
Supports interactive mode (default) and --non-interactive for scripting.
"""

import re
from datetime import datetime, timezone
from pathlib import Path

import click

from diligent.helpers.formatting import output_result
from diligent.helpers.io import atomic_write
from diligent.templates import render_config, render_template


VALID_WORKSTREAMS = ["financial", "retention", "technical", "legal", "hr", "integration"]
DEAL_CODE_PATTERN = re.compile(r"^[A-Z]{3,12}$")

STATE_FILES = [
    "config.json",
    "DEAL.md",
    "TRUTH.md",
    "SOURCES.md",
    "WORKSTREAMS.md",
    "STATE.md",
    "QUESTIONS.md",
    "ARTIFACTS.md",
]


def _validate_deal_code(code: str) -> str | None:
    """Validate deal code. Return error message or None if valid."""
    if not code:
        return "Deal code is required."
    if not DEAL_CODE_PATTERN.match(code):
        if not code.isalpha():
            return f"Deal code must contain only letters A-Z, got '{code}'."
        if code != code.upper():
            return f"Deal code must be uppercase, got '{code}'."
        if len(code) < 3:
            return f"Deal code must be 3-12 characters, got {len(code)}."
        if len(code) > 12:
            return f"Deal code must be 3-12 characters, got {len(code)}."
        return f"Invalid deal code '{code}'. Must be 3-12 uppercase letters (A-Z)."
    return None


WORKSTREAM_DESCRIPTIONS = {
    "financial": "Financial analysis and quality of earnings",
    "retention": "Customer retention and commercial diligence",
    "technical": "Technology, product, and engineering assessment",
    "legal": "Legal structure, contracts, and regulatory",
    "hr": "Workforce, compensation, and employment matters",
    "integration": "Post-close integration planning",
}


def _build_workstream_entries(workstreams: list[str], iso_date: str = "") -> str:
    """Build WORKSTREAM_ENTRIES block for template substitution.

    Includes description (for known templates) and created date fields.
    """
    date_part = iso_date[:10] if iso_date else ""
    lines = []
    for ws in workstreams:
        lines.append(f"## {ws}")
        lines.append("```yaml")
        lines.append(f"name: {ws}")
        lines.append("status: active")
        desc = WORKSTREAM_DESCRIPTIONS.get(ws, "")
        if desc:
            lines.append(f"description: {desc}")
        if date_part:
            lines.append(f'created: "{date_part}"')
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def _build_workstreams_yaml(workstreams: list[str]) -> str:
    """Build YAML list items for DEAL.md frontmatter workstreams field."""
    if not workstreams:
        return "  []"
    return "\n".join(f"  - {ws}" for ws in workstreams)


def _prompt_workstreams() -> list[str]:
    """Interactively prompt user to select workstreams."""
    click.echo("Available workstreams:")
    for i, ws in enumerate(VALID_WORKSTREAMS, 1):
        click.echo(f"  {i}. {ws}")
    selection = click.prompt(
        "Select workstreams (comma-separated numbers or names)",
        type=str,
    )
    selected = []
    for item in selection.split(","):
        item = item.strip()
        if item.isdigit():
            idx = int(item) - 1
            if 0 <= idx < len(VALID_WORKSTREAMS):
                selected.append(VALID_WORKSTREAMS[idx])
        elif item.lower() in VALID_WORKSTREAMS:
            selected.append(item.lower())
    if not selected:
        click.echo("No valid workstreams selected. Using 'financial' as default.")
        selected = ["financial"]
    return selected


@click.command("init")
@click.option("--code", default=None, help="Deal code (uppercase A-Z, 3-12 chars).")
@click.option("--target-legal", default=None, help="Target legal entity name.")
@click.option("--target-common", default=None, help="Target common/short name.")
@click.option("--stage", default=None, help="Deal stage (e.g., loi, dd, closing).")
@click.option("--loi-date", default=None, help="LOI date (ISO format).")
@click.option("--principal", default=None, help="Principal name.")
@click.option("--principal-role", default=None, help="Principal role.")
@click.option("--seller", default=None, help="Seller contact.")
@click.option("--broker", default=None, help="Broker contact.")
@click.option("--thesis", default=None, help="Thesis text (if absent, opens editor in interactive mode).")
@click.option("--workstreams", default=None, help="Comma-separated workstream names.")
@click.option("--non-interactive", is_flag=True, default=False, help="Fail if any required field is missing.")
@click.option("--json", "json_mode", is_flag=True, default=False, help="Output structured JSON result.")
def init_cmd(code, target_legal, target_common, stage, loi_date, principal,
             principal_role, seller, broker, thesis, workstreams,
             non_interactive, json_mode):
    """Initialize a new deal folder with .diligence/ state files."""
    diligence_dir = Path.cwd() / ".diligence"

    # Check .diligence/ does not exist
    if diligence_dir.exists():
        click.echo(
            "ERROR: .diligence/ already exists. "
            "Remove it first or use a different directory."
        )
        raise SystemExit(1)

    # Parse workstreams from comma-separated string
    ws_list = None
    if workstreams is not None:
        ws_list = [w.strip() for w in workstreams.split(",") if w.strip()]

    # Collect all required fields
    required_fields = {
        "code": code,
        "target_legal": target_legal,
        "target_common": target_common,
        "stage": stage,
        "loi_date": loi_date,
        "principal": principal,
        "principal_role": principal_role,
        "seller": seller,
        "broker": broker,
        "thesis": thesis,
        "workstreams": ws_list,
    }

    if non_interactive:
        # Validate all required fields are present
        missing = [k for k, v in required_fields.items() if v is None]
        if missing:
            click.echo(f"ERROR: Missing required fields for --non-interactive: {', '.join(missing)}")
            raise SystemExit(1)
    else:
        # Interactive mode: prompt for missing fields
        if code is None:
            code = click.prompt("Deal code (uppercase A-Z, 3-12 chars)")
        required_fields["code"] = code

        if target_legal is None:
            target_legal = click.prompt("Target legal entity name")
        required_fields["target_legal"] = target_legal

        if target_common is None:
            target_common = click.prompt("Target common/short name")
        required_fields["target_common"] = target_common

        if stage is None:
            stage = click.prompt("Deal stage (loi, dd, closing)")
        required_fields["stage"] = stage

        if loi_date is None:
            loi_date = click.prompt("LOI date (YYYY-MM-DD)")
        required_fields["loi_date"] = loi_date

        if principal is None:
            principal = click.prompt("Principal name")
        required_fields["principal"] = principal

        if principal_role is None:
            principal_role = click.prompt("Principal role")
        required_fields["principal_role"] = principal_role

        if seller is None:
            seller = click.prompt("Seller contact")
        required_fields["seller"] = seller

        if broker is None:
            broker = click.prompt("Broker contact")
        required_fields["broker"] = broker

        if thesis is None:
            from diligent.helpers.editor import collect_thesis
            thesis = collect_thesis()
        required_fields["thesis"] = thesis

        if ws_list is None:
            ws_list = _prompt_workstreams()
        required_fields["workstreams"] = ws_list

    # Re-assign from dict for clarity after interactive prompts
    code = required_fields["code"]
    target_legal = required_fields["target_legal"]
    target_common = required_fields["target_common"]
    stage = required_fields["stage"]
    loi_date = required_fields["loi_date"]
    principal = required_fields["principal"]
    principal_role = required_fields["principal_role"]
    seller = required_fields["seller"]
    broker = required_fields["broker"]
    thesis = required_fields["thesis"]
    ws_list = required_fields["workstreams"]

    # Validate deal code
    code_err = _validate_deal_code(code)
    if code_err:
        click.echo(f"ERROR: {code_err}")
        raise SystemExit(1)

    # Build template context
    iso_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    context = {
        "DEAL_CODE": code,
        "TARGET_LEGAL_NAME": target_legal,
        "TARGET_COMMON_NAME": target_common,
        "DEAL_STAGE": stage,
        "LOI_DATE": loi_date,
        "PRINCIPAL": principal,
        "PRINCIPAL_ROLE": principal_role,
        "SELLER": seller,
        "BROKER": broker,
        "THESIS": thesis,
        "WORKSTREAMS_YAML": _build_workstreams_yaml(ws_list),
        "WORKSTREAM_ENTRIES": _build_workstream_entries(ws_list, iso_date),
        "ISO_DATE": iso_date,
        "WORKSTREAMS_JSON": ws_list,
    }

    # Create .diligence/ directory
    diligence_dir.mkdir(parents=True)

    # Render and write all 8 files
    try:
        # config.json (special: JSON rendering, not string.Template)
        config_content = render_config(context)
        atomic_write(diligence_dir / "config.json", config_content)

        # DEAL.md
        deal_content = render_template("DEAL.md.tmpl", context)
        atomic_write(diligence_dir / "DEAL.md", deal_content)

        # TRUTH.md
        truth_content = render_template("TRUTH.md.tmpl", context)
        atomic_write(diligence_dir / "TRUTH.md", truth_content)

        # SOURCES.md
        sources_content = render_template("SOURCES.md.tmpl", context)
        atomic_write(diligence_dir / "SOURCES.md", sources_content)

        # WORKSTREAMS.md
        ws_content = render_template("WORKSTREAMS.md.tmpl", context)
        atomic_write(diligence_dir / "WORKSTREAMS.md", ws_content)

        # STATE.md
        state_content = render_template("STATE.md.tmpl", context)
        atomic_write(diligence_dir / "STATE.md", state_content)

        # QUESTIONS.md
        questions_content = render_template("QUESTIONS.md.tmpl", context)
        atomic_write(diligence_dir / "QUESTIONS.md", questions_content)

        # ARTIFACTS.md
        artifacts_content = render_template("ARTIFACTS.md.tmpl", context)
        atomic_write(diligence_dir / "ARTIFACTS.md", artifacts_content)

    except Exception as e:
        # Clean up on failure
        import shutil
        shutil.rmtree(diligence_dir, ignore_errors=True)
        click.echo(f"ERROR: Failed to initialize: {e}")
        raise SystemExit(1)

    # Create workstream subdirectories (non-fatal if this fails)
    ws_dirs_created = []
    try:
        workstreams_dir = diligence_dir / "workstreams"
        workstreams_dir.mkdir(exist_ok=True)
        for ws_name in ws_list:
            ws_dir = workstreams_dir / ws_name
            ws_dir.mkdir(exist_ok=True)
            # Write CONTEXT.md
            if ws_name in VALID_WORKSTREAMS:
                # Tailored template
                template_path = Path(__file__).parent.parent / "templates" / "workstreams" / f"{ws_name}.md"
                context_content = template_path.read_text(encoding="utf-8")
            else:
                # Generic template
                context_content = render_template(
                    "ws_context.md.tmpl", {"WORKSTREAM_NAME": ws_name}
                )
            (ws_dir / "CONTEXT.md").write_text(context_content, encoding="utf-8")
            # Write RESEARCH.md
            research_content = render_template(
                "ws_research.md.tmpl", {"WORKSTREAM_NAME": ws_name}
            )
            (ws_dir / "RESEARCH.md").write_text(research_content, encoding="utf-8")
            ws_dirs_created.append(ws_name)
    except Exception as e:
        click.echo(f"WARNING: Failed to create workstream directories: {e}")
        # State files are valid; subdirectory creation is non-fatal

    # Output
    files_created = list(STATE_FILES)
    for ws_name in ws_dirs_created:
        files_created.append(f"workstreams/{ws_name}/CONTEXT.md")
        files_created.append(f"workstreams/{ws_name}/RESEARCH.md")
    if json_mode:
        output_result(
            {
                "deal_code": code,
                "target_common": target_common,
                "path": str(diligence_dir),
                "files_created": files_created,
            },
            json_mode=True,
        )
    else:
        click.echo(f"Initialized .diligence/ for {code} ({target_common})")
        for f in files_created:
            click.echo(f"  {f}")
        click.echo(click.style(
            "Next: run 'diligent ingest <file>' to register your source documents.",
            dim=True,
        ))
