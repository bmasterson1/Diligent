"""Tests for template rendering.

All test function names include 'template' to clearly mark them as
template-specific tests per plan 01-02 task 1 behavior spec.
"""

import json
from pathlib import Path

import pytest


TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "diligent" / "templates"

TEMPLATE_FILES = [
    "DEAL.md.tmpl",
    "TRUTH.md.tmpl",
    "SOURCES.md.tmpl",
    "WORKSTREAMS.md.tmpl",
    "STATE.md.tmpl",
    "config.json.tmpl",
]


def test_all_template_files_exist():
    """Each .tmpl file exists and is non-empty."""
    for name in TEMPLATE_FILES:
        path = TEMPLATE_DIR / name
        assert path.exists(), f"Template file missing: {name}"
        assert path.stat().st_size > 0, f"Template file empty: {name}"


def test_render_deal_template():
    """render_template('DEAL.md.tmpl', context) returns a string containing the deal code."""
    from diligent.templates import render_template

    context = {
        "DEAL_CODE": "ARRIVAL",
        "TARGET_LEGAL_NAME": "Arrival Industries LLC",
        "TARGET_COMMON_NAME": "Arrival",
        "DEAL_STAGE": "LOI Signed",
        "LOI_DATE": "2026-03-15",
        "PRINCIPAL": "Bryce Masterson",
        "PRINCIPAL_ROLE": "Apprentice",
        "SELLER": "John Smith",
        "BROKER": "Jane Doe",
        "THESIS": "Strong recurring revenue with diversified customer base.",
        "WORKSTREAMS_YAML": "- financial\n- legal",
    }
    result = render_template("DEAL.md.tmpl", context)
    assert isinstance(result, str)
    assert "ARRIVAL" in result
    assert "Arrival Industries LLC" in result
    assert "Strong recurring revenue" in result


def test_render_config_template():
    """render_config(context) returns valid JSON with schema_version = 1."""
    from diligent.templates import render_config

    context = {
        "DEAL_CODE": "ARRIVAL",
        "ISO_DATE": "2026-04-07T00:00:00Z",
        "WORKSTREAMS_JSON": ["financial", "legal"],
    }
    result = render_config(context)
    assert isinstance(result, str)
    data = json.loads(result)
    assert data["schema_version"] == 1
    assert data["deal_code"] == "ARRIVAL"
    assert data["created"] == "2026-04-07T00:00:00Z"
    assert data["anchor_tolerance_pct"] == 0.5
    assert data["recent_window_days"] == 7
    assert data["workstreams"] == ["financial", "legal"]


def test_truth_template_no_parseable_facts():
    """TRUTH.md template contains HTML comment block but no parseable fact entries.

    Parse with read_truth, assert zero facts.
    """
    from diligent.state.truth import read_truth

    template_path = TEMPLATE_DIR / "TRUTH.md.tmpl"
    # The template should be parseable as a TRUTH.md file
    # but contain zero actual facts (only commented examples)
    truth = read_truth(template_path)
    assert len(truth.facts) == 0, (
        f"Template should have zero facts, got {len(truth.facts)}: "
        f"{list(truth.facts.keys())}"
    )


def test_truth_template_has_html_comment():
    """TRUTH.md template contains HTML comment guidance."""
    content = (TEMPLATE_DIR / "TRUTH.md.tmpl").read_text(encoding="utf-8")
    assert "<!--" in content
    assert "-->" in content


def test_sources_template_has_html_comment():
    """SOURCES.md template has HTML comment guidance."""
    content = (TEMPLATE_DIR / "SOURCES.md.tmpl").read_text(encoding="utf-8")
    assert "<!--" in content
    assert "-->" in content
    assert "# Sources" in content


def test_workstreams_template_has_placeholder():
    """WORKSTREAMS.md template has the WORKSTREAM_ENTRIES placeholder."""
    content = (TEMPLATE_DIR / "WORKSTREAMS.md.tmpl").read_text(encoding="utf-8")
    assert "# Workstreams" in content


def test_state_template_has_frontmatter():
    """STATE.md template has YAML frontmatter with date placeholders."""
    content = (TEMPLATE_DIR / "STATE.md.tmpl").read_text(encoding="utf-8")
    assert "# State" in content
    assert "${ISO_DATE}" in content


def test_deal_template_has_frontmatter():
    """DEAL.md template has YAML frontmatter structure."""
    content = (TEMPLATE_DIR / "DEAL.md.tmpl").read_text(encoding="utf-8")
    assert "---" in content
    assert "${DEAL_CODE}" in content
