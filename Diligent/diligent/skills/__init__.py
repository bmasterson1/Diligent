"""Skill template files for AI agent integration.

Templates are parameterized with {{DILIGENT_PATH}} which is replaced
at install time with the actual CLI binary path.
"""

from pathlib import Path

SKILLS_DIR = Path(__file__).parent
