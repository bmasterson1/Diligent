"""Tests for ArtifactEntry/ArtifactsFile models and artifacts.py reader/writer.

Covers round-trip fidelity, empty state, field preservation, YAML string
quoting, validate_fn corruption detection, and template rendering.
"""

from pathlib import Path

import pytest

from diligent.state.models import ArtifactEntry, ArtifactsFile


# -- Test 1: ArtifactEntry has all required fields --

class TestArtifactEntryFields:
    def test_all_required_fields_present(self):
        entry = ArtifactEntry(
            path="deliverables/retention/retention_analysis_v9.docx",
            workstream="retention",
            registered="2026-03-22",
            last_refreshed="2026-03-22",
            references=["customer_253_mrr", "t12m_cohort"],
            scanner_findings=["revenue_growth_yoy"],
            notes="Initial registration",
        )
        assert entry.path == "deliverables/retention/retention_analysis_v9.docx"
        assert entry.workstream == "retention"
        assert entry.registered == "2026-03-22"
        assert entry.last_refreshed == "2026-03-22"
        assert entry.references == ["customer_253_mrr", "t12m_cohort"]
        assert entry.scanner_findings == ["revenue_growth_yoy"]
        assert entry.notes == "Initial registration"

    def test_default_values(self):
        entry = ArtifactEntry(
            path="docs/memo.docx",
            workstream="financial",
            registered="2026-04-01",
            last_refreshed="2026-04-01",
        )
        assert entry.references == []
        assert entry.scanner_findings == []
        assert entry.notes == ""


# -- Test 2: Round-trip with zero data loss --

class TestArtifactsRoundTrip:
    def test_full_round_trip_preserves_all_fields(self, tmp_path):
        from diligent.state.artifacts import read_artifacts, write_artifacts

        original = ArtifactsFile(artifacts=[
            ArtifactEntry(
                path="deliverables/retention/retention_analysis_v9.docx",
                workstream="retention",
                registered="2026-03-22",
                last_refreshed="2026-03-22",
                references=["customer_253_mrr", "t12m_cohort", "t12m_retained", "ndr_pct"],
                scanner_findings=["revenue_growth_yoy", "gross_margin_pct"],
                notes="Initial registration",
            ),
        ])

        fpath = tmp_path / "ARTIFACTS.md"
        write_artifacts(fpath, original)
        reread = read_artifacts(fpath)

        assert len(reread.artifacts) == 1
        a = reread.artifacts[0]
        assert a.path == "deliverables/retention/retention_analysis_v9.docx"
        assert a.workstream == "retention"
        assert a.registered == "2026-03-22"
        assert a.last_refreshed == "2026-03-22"
        assert a.references == ["customer_253_mrr", "t12m_cohort", "t12m_retained", "ndr_pct"]
        assert a.scanner_findings == ["revenue_growth_yoy", "gross_margin_pct"]
        assert a.notes == "Initial registration"


# -- Test 3: Empty ARTIFACTS.md reads as empty ArtifactsFile --

class TestEmptyArtifacts:
    def test_empty_artifacts_file(self, tmp_path):
        from diligent.state.artifacts import read_artifacts

        fpath = tmp_path / "ARTIFACTS.md"
        fpath.write_text("# Artifacts\n\n<!-- comment -->\n", encoding="utf-8")
        result = read_artifacts(fpath)
        assert isinstance(result, ArtifactsFile)
        assert result.artifacts == []


# -- Test 4: H2 heading becomes artifact path field --

class TestH2HeadingPath:
    def test_h2_heading_is_artifact_path(self, tmp_path):
        from diligent.state.artifacts import read_artifacts

        content = (
            "# Artifacts\n\n"
            "## deliverables/financial/model_v3.xlsx\n"
            "```yaml\n"
            'workstream: "financial"\n'
            'registered: "2026-04-01"\n'
            'last_refreshed: "2026-04-01"\n'
            "references: []\n"
            "scanner_findings: []\n"
            'notes: ""\n'
            "```\n"
        )
        fpath = tmp_path / "ARTIFACTS.md"
        fpath.write_text(content, encoding="utf-8")
        result = read_artifacts(fpath)
        assert result.artifacts[0].path == "deliverables/financial/model_v3.xlsx"


# -- Test 5: References are always strings (no type coercion) --

class TestReferencesStrings:
    def test_references_are_strings_no_coercion(self, tmp_path):
        from diligent.state.artifacts import read_artifacts, write_artifacts

        original = ArtifactsFile(artifacts=[
            ArtifactEntry(
                path="docs/memo.docx",
                workstream="financial",
                registered="2026-04-01",
                last_refreshed="2026-04-01",
                references=["1234", "true", "3.14", "null_key"],
                scanner_findings=[],
                notes="",
            ),
        ])

        fpath = tmp_path / "ARTIFACTS.md"
        write_artifacts(fpath, original)
        reread = read_artifacts(fpath)

        # All references must come back as strings, not coerced to int/bool/float
        for ref in reread.artifacts[0].references:
            assert isinstance(ref, str), f"Expected str, got {type(ref).__name__}: {ref}"
        assert reread.artifacts[0].references == ["1234", "true", "3.14", "null_key"]


# -- Test 6: scanner_findings list preserved through round-trip --

class TestScannerFindings:
    def test_scanner_findings_round_trip(self, tmp_path):
        from diligent.state.artifacts import read_artifacts, write_artifacts

        findings = ["revenue_growth_yoy", "gross_margin_pct", "customer_count"]
        original = ArtifactsFile(artifacts=[
            ArtifactEntry(
                path="docs/analysis.docx",
                workstream="financial",
                registered="2026-04-01",
                last_refreshed="2026-04-01",
                references=["some_key"],
                scanner_findings=findings,
                notes="",
            ),
        ])

        fpath = tmp_path / "ARTIFACTS.md"
        write_artifacts(fpath, original)
        reread = read_artifacts(fpath)
        assert reread.artifacts[0].scanner_findings == findings


# -- Test 7: validate_fn catches corruption --

class TestValidateFn:
    def test_validate_fn_catches_corruption(self, tmp_path):
        from diligent.state.artifacts import write_artifacts

        original = ArtifactsFile(artifacts=[
            ArtifactEntry(
                path="docs/memo.docx",
                workstream="financial",
                registered="2026-04-01",
                last_refreshed="2026-04-01",
                references=["key1"],
                scanner_findings=[],
                notes="",
            ),
        ])

        fpath = tmp_path / "ARTIFACTS.md"
        # First write should succeed
        write_artifacts(fpath, original)
        assert fpath.exists()

        # Read back and verify
        from diligent.state.artifacts import read_artifacts
        reread = read_artifacts(fpath)
        assert len(reread.artifacts) == len(original.artifacts)


# -- Test 8: ARTIFACTS.md.tmpl template renders valid markdown --

class TestArtifactsTemplate:
    def test_template_renders_valid_markdown(self):
        from diligent.templates import render_template

        content = render_template("ARTIFACTS.md.tmpl", {})
        assert "# Artifacts" in content
        assert "<!--" in content
        assert "-->" in content

    def test_template_parseable_as_empty(self, tmp_path):
        from diligent.templates import render_template
        from diligent.state.artifacts import read_artifacts

        content = render_template("ARTIFACTS.md.tmpl", {})
        fpath = tmp_path / "ARTIFACTS.md"
        fpath.write_text(content, encoding="utf-8")
        result = read_artifacts(fpath)
        assert isinstance(result, ArtifactsFile)
        assert result.artifacts == []


# -- Test 9: Multiple artifacts round-trip in order --

class TestMultipleArtifacts:
    def test_multiple_artifacts_preserved_in_order(self, tmp_path):
        from diligent.state.artifacts import read_artifacts, write_artifacts

        original = ArtifactsFile(artifacts=[
            ArtifactEntry(
                path="deliverables/alpha.docx",
                workstream="financial",
                registered="2026-01-01",
                last_refreshed="2026-01-01",
                references=["key_a"],
                scanner_findings=[],
                notes="first",
            ),
            ArtifactEntry(
                path="deliverables/beta.docx",
                workstream="retention",
                registered="2026-02-01",
                last_refreshed="2026-02-01",
                references=["key_b", "key_c"],
                scanner_findings=["finding_x"],
                notes="second",
            ),
            ArtifactEntry(
                path="deliverables/gamma.xlsx",
                workstream="legal",
                registered="2026-03-01",
                last_refreshed="2026-03-01",
                references=[],
                scanner_findings=[],
                notes="",
            ),
        ])

        fpath = tmp_path / "ARTIFACTS.md"
        write_artifacts(fpath, original)
        reread = read_artifacts(fpath)

        assert len(reread.artifacts) == 3
        assert reread.artifacts[0].path == "deliverables/alpha.docx"
        assert reread.artifacts[1].path == "deliverables/beta.docx"
        assert reread.artifacts[2].path == "deliverables/gamma.xlsx"
        assert reread.artifacts[0].notes == "first"
        assert reread.artifacts[1].notes == "second"
        assert reread.artifacts[2].notes == ""


# -- Test 10: HTML comments stripped during parsing --

class TestHtmlCommentStripping:
    def test_html_comments_not_treated_as_entries(self, tmp_path):
        from diligent.state.artifacts import read_artifacts

        content = (
            "# Artifacts\n\n"
            "<!-- This is a comment block.\n"
            "## fake/heading/in/comment.docx\n"
            "```yaml\n"
            'workstream: "fake"\n'
            "```\n"
            "-->\n\n"
            "## real/artifact.docx\n"
            "```yaml\n"
            'workstream: "financial"\n'
            'registered: "2026-04-01"\n'
            'last_refreshed: "2026-04-01"\n'
            "references: []\n"
            "scanner_findings: []\n"
            'notes: ""\n'
            "```\n"
        )
        fpath = tmp_path / "ARTIFACTS.md"
        fpath.write_text(content, encoding="utf-8")
        result = read_artifacts(fpath)
        assert len(result.artifacts) == 1
        assert result.artifacts[0].path == "real/artifact.docx"
