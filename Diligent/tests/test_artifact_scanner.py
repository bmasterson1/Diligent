"""Tests for artifact_scanner.py: docx citation tag extraction.

Tests scan_docx_citations function which extracts {{truth:key_name}} tags
from Word document paragraphs. Uses python-docx to create test fixtures
programmatically in tmp_path (no binary fixtures in git).
"""

import sys
from pathlib import Path

import pytest


def _create_docx(path: Path, paragraphs: list[str]) -> None:
    """Create a .docx file with the given paragraph texts."""
    from docx import Document

    doc = Document()
    for text in paragraphs:
        doc.add_paragraph(text)
    doc.save(str(path))


class TestScanDocxCitations:
    """scan_docx_citations extracts {{truth:key_name}} tags from .docx paragraphs."""

    def test_extracts_single_citation_tag(self, tmp_path):
        """Extracts a single {{truth:key_name}} tag from paragraph text."""
        docx_path = tmp_path / "test.docx"
        _create_docx(docx_path, ["Revenue is {{truth:revenue}} per year."])

        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(docx_path))
        assert result == ["revenue"]

    def test_returns_sorted_unique_keys(self, tmp_path):
        """Returns sorted unique list of key names (no duplicates)."""
        docx_path = tmp_path / "test.docx"
        _create_docx(docx_path, [
            "Revenue {{truth:revenue}} and margin {{truth:margin}}.",
            "Also revenue again: {{truth:revenue}}.",
            "And alpha: {{truth:alpha_key}}.",
        ])

        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(docx_path))
        assert result == ["alpha_key", "margin", "revenue"]

    def test_returns_empty_for_no_citations(self, tmp_path):
        """Returns empty list for docx with no citation tags."""
        docx_path = tmp_path / "test.docx"
        _create_docx(docx_path, [
            "This document has no citation tags.",
            "Just regular text.",
        ])

        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(docx_path))
        assert result == []

    def test_multiple_tags_in_single_paragraph(self, tmp_path):
        """Handles multiple tags in a single paragraph."""
        docx_path = tmp_path / "test.docx"
        _create_docx(docx_path, [
            "Revenue {{truth:revenue}} and margin {{truth:margin}} and growth {{truth:growth}}.",
        ])

        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(docx_path))
        assert result == ["growth", "margin", "revenue"]

    def test_tags_across_multiple_paragraphs(self, tmp_path):
        """Handles tags spread across multiple paragraphs."""
        docx_path = tmp_path / "test.docx"
        _create_docx(docx_path, [
            "First paragraph with {{truth:key_a}}.",
            "Second paragraph with {{truth:key_b}}.",
            "Third paragraph with {{truth:key_c}}.",
        ])

        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(docx_path))
        assert result == ["key_a", "key_b", "key_c"]

    def test_lazy_import_not_at_module_level(self):
        """python-docx is NOT imported at module level (lazy import check)."""
        # Remove docx from sys.modules if present
        docx_was_loaded = "docx" in sys.modules
        if docx_was_loaded:
            saved = sys.modules.pop("docx")

        # Remove artifact_scanner if already imported
        if "diligent.helpers.artifact_scanner" in sys.modules:
            del sys.modules["diligent.helpers.artifact_scanner"]

        # Import the module
        import diligent.helpers.artifact_scanner  # noqa: F401

        # Verify docx is NOT in sys.modules after module import alone
        assert "docx" not in sys.modules, "python-docx should not be imported at module level"

        # Restore if it was loaded before
        if docx_was_loaded:
            sys.modules["docx"] = saved

    def test_handles_missing_file_gracefully(self, tmp_path):
        """Returns empty list for missing/unreadable file (no crash)."""
        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(tmp_path / "nonexistent.docx"))
        assert result == []

    def test_handles_corrupt_file_gracefully(self, tmp_path):
        """Returns empty list for corrupt (non-docx) file."""
        corrupt_path = tmp_path / "corrupt.docx"
        corrupt_path.write_text("This is not a real docx file.")

        from diligent.helpers.artifact_scanner import scan_docx_citations

        result = scan_docx_citations(str(corrupt_path))
        assert result == []
