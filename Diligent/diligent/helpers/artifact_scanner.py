"""Docx citation tag scanner for artifact registration.

Extracts {{truth:key_name}} citation tags from Word document paragraphs.
python-docx is lazy-imported inside the function body to keep CLI
startup under 200ms (same pattern as diff_docx.py).
"""

import re

CITATION_PATTERN = re.compile(r"\{\{truth:([a-zA-Z0-9_]+)\}\}")


def scan_docx_citations(path: str) -> list[str]:
    """Extract truth key references from a .docx file.

    Scans paragraph text for {{truth:key_name}} citation tags.
    Lazy-imports python-docx to keep CLI startup fast.

    Returns sorted unique list of referenced truth keys.
    Returns empty list if file cannot be read.
    """
    try:
        from docx import Document

        doc = Document(path)
        keys: set[str] = set()
        for para in doc.paragraphs:
            for match in CITATION_PATTERN.finditer(para.text):
                keys.add(match.group(1))
        return sorted(keys)
    except Exception:
        return []
