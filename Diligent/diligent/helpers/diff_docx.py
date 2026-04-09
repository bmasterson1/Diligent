"""Word document diff helper.

Provides paragraph-level comparison between two Word (.docx) files.

python-docx is lazy-imported inside function bodies to avoid loading at
module import time (keeps CLI startup under 200ms).
"""

from __future__ import annotations

import difflib


def _extract_paragraphs(path: str) -> list[str]:
    """Extract paragraph text from a Word document.

    Lazy-imports python-docx. Filters out empty paragraphs
    (blank lines between content).
    """
    from docx import Document

    doc = Document(path)
    return [p.text for p in doc.paragraphs if p.text.strip()]


def diff_docx_summary(path_a: str, path_b: str) -> dict:
    """Compare two Word documents and return paragraph-level difference counts.

    Uses difflib.SequenceMatcher to compute differences between
    paragraph text lists.

    Returns dict with keys:
        paragraphs_changed: int - paragraphs with different text
        paragraphs_added: int - paragraphs in B not in A
        paragraphs_removed: int - paragraphs in A not in B
        total_paragraphs_a: int - total paragraphs in file A
        total_paragraphs_b: int - total paragraphs in file B
    """
    paras_a = _extract_paragraphs(path_a)
    paras_b = _extract_paragraphs(path_b)

    matcher = difflib.SequenceMatcher(None, paras_a, paras_b)

    changed = 0
    added = 0
    removed = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "replace":
            # Paragraphs were changed: min count as changed, excess as added/removed
            n_a = i2 - i1
            n_b = j2 - j1
            changed += min(n_a, n_b)
            if n_b > n_a:
                added += n_b - n_a
            elif n_a > n_b:
                removed += n_a - n_b
        elif tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1

    return {
        "paragraphs_changed": changed,
        "paragraphs_added": added,
        "paragraphs_removed": removed,
        "total_paragraphs_a": len(paras_a),
        "total_paragraphs_b": len(paras_b),
    }


def diff_docx_verbose(path_a: str, path_b: str) -> list[str]:
    """Compare two Word documents and return unified diff lines.

    Returns actual paragraph-level diff text for --verbose display.
    Uses difflib.unified_diff.
    """
    paras_a = _extract_paragraphs(path_a)
    paras_b = _extract_paragraphs(path_b)

    return list(difflib.unified_diff(
        paras_a,
        paras_b,
        fromfile="old",
        tofile="new",
        lineterm="",
    ))
