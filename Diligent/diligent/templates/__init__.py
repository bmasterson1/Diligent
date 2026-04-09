"""Template rendering for diligent init.

Uses string.Template for .tmpl files and direct dict construction for
config.json. No Jinja2 dependency.
"""

import json
from pathlib import Path
from string import Template


TEMPLATE_DIR = Path(__file__).parent


def render_template(template_name: str, context: dict) -> str:
    """Render a .tmpl file with string.Template substitution.

    Args:
        template_name: Name of the template file (e.g., 'DEAL.md.tmpl').
        context: Dict of variable names to values for substitution.

    Returns:
        Rendered template string with variables replaced.
    """
    template_path = TEMPLATE_DIR / template_name
    raw = template_path.read_text(encoding="utf-8")
    tmpl = Template(raw)
    return tmpl.safe_substitute(context)


def render_config(context: dict) -> str:
    """Render config.json from context dict.

    Builds the JSON structure directly rather than using string
    substitution, since JSON does not support string.Template syntax.

    Args:
        context: Dict with keys DEAL_CODE, ISO_DATE, WORKSTREAMS_JSON.
            WORKSTREAMS_JSON should be a list of strings.

    Returns:
        JSON string with trailing newline.
    """
    data = {
        "schema_version": 1,
        "deal_code": context["DEAL_CODE"],
        "created": context["ISO_DATE"],
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": context.get("WORKSTREAMS_JSON", []),
    }
    return json.dumps(data, indent=2) + "\n"
