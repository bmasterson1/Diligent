# Technology Stack

**Project:** Diligent - CLI state-management for acquisition due diligence
**Researched:** 2026-04-07
**Verification note:** WebSearch, WebFetch, and Bash were unavailable during research. All version numbers are from training data (cutoff May 2025) and should be verified with `pip index versions <package>` before locking. The libraries recommended are mature and stable; version drift risk is LOW.

## Recommended Stack

### Python Runtime

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Python | >=3.11,<3.14 | Runtime | 3.11 is the floor (tomllib in stdlib, ExceptionGroup, significant perf gains). 3.12+ brings better error messages. 3.11 keeps compatibility with older pipx installs. | HIGH |

### CLI Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Click | >=8.1 | CLI framework | Typer adds a type-hint layer over Click but introduces unnecessary indirection for this project. Click is the direct, battle-tested choice: explicit decorators, composable groups, excellent help generation, zero magic. Diligent has ~15 commands across 6 groups -- Click handles this perfectly with `@click.group()` nesting. No need for Typer's auto-discovery when command structure is designed upfront. | HIGH |

**Why Click over Typer:** Typer is a wrapper around Click. For a tool where command signatures are stable and designed in advance (not discovered from function signatures), Click gives you full control with less abstraction. Typer's value proposition -- "just add type hints" -- matters for rapid prototyping, not for a tool with carefully designed CLI ergonomics. Click also has fewer transitive dependencies (Typer pulls in Click anyway, plus typing-extensions and rich by default).

**Why not argparse:** Verbose, no built-in command groups, poor help formatting, painful to compose. Click is the standard for non-trivial Python CLIs.

### State File I/O

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| PyYAML | >=6.0.1 | YAML front-matter parsing | De facto standard. Handles the YAML blocks inside markdown state files. Use `yaml.safe_load()` / `yaml.safe_dump()` exclusively -- never `yaml.load()`. | HIGH |
| tomllib (stdlib) | N/A (Python 3.11+) | pyproject.toml parsing | In stdlib since 3.11. No dependency needed for reading project config. | HIGH |

**Why not ruamel.yaml:** ruamel.yaml preserves comments and formatting, which sounds appealing for round-tripping YAML front-matter. But it adds complexity and a C extension dependency. PyYAML is sufficient because diligent controls the YAML schema -- you write what you read, so comment preservation is not needed. If round-trip fidelity of user-edited YAML becomes a requirement later, ruamel.yaml is the upgrade path.

**Why not toml for state files:** YAML is the standard for markdown front-matter (Jekyll, Hugo, Obsidian). Using TOML would confuse every user who has seen `---` delimited blocks.

### Document Parsing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| openpyxl | >=3.1.2 | Excel (.xlsx) reading | The only serious choice for .xlsx in Python. Read-only mode (`load_workbook(read_only=True)`) is fast and memory-efficient for large financial models. Handles formulas, named ranges, sheets. | HIGH |
| python-docx | >=1.1.0 | Word (.docx) reading | De facto standard. Reads paragraphs, tables, headers. Sufficient for extracting text and structure from LOIs, purchase agreements, diligence reports. | HIGH |
| pdfplumber | >=0.11.0 | PDF text extraction | Better than pypdf for table extraction and layout-aware text. Built on pdfminer.six. Critical for extracting structured data from financial statements, tax returns, and broker packages that arrive as PDF. | MEDIUM |

**Why pdfplumber over pypdf:** pypdf (formerly PyPDF2) is good for PDF manipulation (merge, split, metadata) but weaker at text extraction, especially from PDFs with complex layouts (multi-column financial statements, tables). pdfplumber wraps pdfminer.six and provides `.extract_tables()` which is directly useful for financial document parsing. The tradeoff: pdfplumber is heavier (~pdfminer.six dependency tree). Worth it for this domain.

**Why not PyMuPDF (fitz):** PyMuPDF is faster and handles more edge cases, but it is GPL-licensed (via MuPDF). Diligent is BSL 1.1 -- mixing GPL creates license complications. pdfplumber (MIT) is the safe choice.

**Why not camelot/tabula:** Both are excellent for table extraction but require Java (tabula) or Ghostscript (camelot) as system dependencies. Diligent must be `pipx install` and go -- no system dependency installation. pdfplumber's table extraction is good enough without external dependencies.

### Terminal Output

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| rich | >=13.7 | Formatted terminal output (optional) | Tables for `diligent status`, colored diffs for `diligent sources diff`, progress indicators. Mark as optional dependency (`pip install diligent[rich]`). Plain-text fallback when rich is absent. | HIGH |

**Why optional:** The project constraint says "no network requests, no API keys." Rich is cosmetic, not functional. Making it optional keeps the core dependency footprint minimal and avoids issues on minimal server environments. Use a thin wrapper: `if rich available, use rich.table; else, format with string padding`.

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | >=8.0 | Test runner | Standard. No reason to use anything else. | HIGH |
| pytest-cov | >=5.0 | Coverage reporting | Pairs with pytest. | HIGH |
| click.testing.CliRunner | (bundled) | CLI integration tests | Click ships its own test runner that invokes commands in-process. Perfect for testing all `diligent` commands without subprocess overhead. | HIGH |

### Build and Distribution

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| hatchling | >=1.21 | Build backend | Modern, fast, PEP 621 native. Better than setuptools for new projects: less config, sane defaults, built-in version management. | HIGH |
| hatch | >=1.9 | Project manager (dev) | Manages virtualenvs, runs scripts, builds packages. Single tool for dev workflow. | MEDIUM |
| ruff | >=0.4 | Linter + formatter | Replaces flake8, isort, black, pyflakes, and pycodestyle. Single tool, written in Rust, extremely fast. The 2025 standard for Python linting. | HIGH |
| mypy | >=1.10 | Type checking | Diligent's state file schemas benefit from strict typing. Use `--strict` from day one. | HIGH |
| pre-commit | >=3.7 | Git hooks | Runs ruff and mypy before commits. Prevents lint/type regressions. | HIGH |

**Why hatchling over setuptools:** setuptools works but requires more configuration (setup.cfg or setup.py alongside pyproject.toml). Hatchling is pyproject.toml-native, faster to build, and handles version strings cleanly. For a new project in 2025+, hatchling is the default recommendation from the Python Packaging Authority.

**Why hatchling over flit:** Flit is simpler but less flexible. Hatchling handles build hooks and custom build steps if needed later (e.g., bundling SKILL.md templates).

**Why not poetry:** Poetry's dependency resolver is slower, its lock file adds complexity for a CLI tool (end users don't use lock files), and it uses a non-standard build backend. Hatch/hatchling aligns with PEP standards.

### File Safety

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| atomicwrites | >=1.4 | Atomic file writes | Write-to-temp, fsync, rename pattern. Prevents corruption from crashes mid-write. Critical for TRUTH.md integrity. Small, focused library. | MEDIUM |

**Alternative: hand-roll it.** The atomic write pattern is ~15 lines of Python (`tempfile.NamedTemporaryFile` + `os.replace`). atomicwrites handles Windows edge cases (which matter here -- Windows is the primary platform and `os.replace` has NTFS quirks). If you want zero non-essential deps, hand-roll but test thoroughly on Windows with OneDrive-synced folders.

**Note on OneDrive:** OneDrive file sync can interfere with atomic renames. Test the write-temp-rename pattern on an OneDrive-synced folder. If OneDrive locks the target file during sync, you may need a retry loop with short backoff. This is a known Windows pain point.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CLI | Click | Typer | Unnecessary abstraction layer; pulls Click anyway; auto-discovery not needed |
| CLI | Click | argparse | No command groups, verbose, poor help output |
| YAML | PyYAML | ruamel.yaml | Comment preservation not needed; adds C extension complexity |
| Excel | openpyxl | xlrd | xlrd dropped .xlsx support; openpyxl is the successor |
| PDF | pdfplumber | pypdf | Weaker text/table extraction for financial documents |
| PDF | pdfplumber | PyMuPDF | GPL license incompatible with BSL 1.1 |
| PDF | pdfplumber | camelot/tabula | Require Java or Ghostscript system dependencies |
| Build | hatchling | setuptools | More config, less modern, no advantage for new projects |
| Build | hatchling | poetry | Non-standard build backend, slower resolver, lock file overhead |
| Lint | ruff | flake8+black+isort | Three tools where one suffices; ruff is faster and unified |
| Output | rich (optional) | colorama | Rich is more capable; colorama is just color codes |

## Full Dependency Tree

### Core (required)

```
click>=8.1
pyyaml>=6.0.1
openpyxl>=3.1.2
python-docx>=1.1.0
pdfplumber>=0.11.0
```

**Total core dependencies: 5** (plus their transitive deps: pdfminer.six, lxml, et-xmlfile, Pillow via pdfplumber). This is lean for what the tool does.

### Optional

```
rich>=13.7  # via diligent[rich]
```

### Dev

```
pytest>=8.0
pytest-cov>=5.0
mypy>=1.10
ruff>=0.4
pre-commit>=3.7
hatch>=1.9
```

## Installation

```bash
# End user
pipx install diligent

# End user with rich output
pipx install "diligent[rich]"

# Developer setup
git clone <repo>
cd diligent
hatch env create
hatch run test       # runs pytest
hatch run lint       # runs ruff + mypy
```

## pyproject.toml Skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "diligent"
version = "0.1.0"
description = "CLI state-management for acquisition due diligence"
requires-python = ">=3.11"
license = {text = "BSL-1.1"}
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0.1",
    "openpyxl>=3.1.2",
    "python-docx>=1.1.0",
    "pdfplumber>=0.11.0",
]

[project.optional-dependencies]
rich = ["rich>=13.7"]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
    "mypy>=1.10",
    "ruff>=0.4",
    "pre-commit>=3.7",
]

[project.scripts]
diligent = "diligent.cli:main"

[tool.ruff]
target-version = "py311"
line-length = 99

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "RUF"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Key Architecture Decisions Driven by Stack

1. **Click groups map 1:1 to command domains:** `diligent sources`, `diligent truth`, `diligent artifact`, `diligent workstream`, `diligent task`, `diligent question`. Top-level commands: `init`, `doctor`, `ingest`, `reconcile`, `status`, `handoff`, `install`.

2. **YAML parsing is always safe_load:** Never allow arbitrary Python object construction from state files.

3. **openpyxl read_only mode for ingest:** Financial models can be 10MB+. Read-only mode streams rows without loading the full workbook into memory.

4. **pdfplumber for structured extraction, not OCR:** The project explicitly excludes OCR. pdfplumber extracts text from text-layer PDFs. Scanned-only PDFs will return empty text -- this is correct behavior per the project scope.

5. **Rich is a progressive enhancement:** Core logic never imports rich. A `diligent.output` module checks availability and delegates to rich or plain-text formatters.

## Version Verification Needed

All versions below are from training data (May 2025 cutoff). Before locking `pyproject.toml`, run:

```bash
pip index versions click openpyxl python-docx pdfplumber pyyaml rich hatchling ruff mypy pytest
```

This will confirm the latest stable releases. The minimum versions specified above are conservative and should be valid, but the latest patch versions may include important fixes.

## Sources

- Training data knowledge (May 2025 cutoff) -- all recommendations based on established ecosystem patterns
- Click documentation: https://click.palletsprojects.com/
- openpyxl documentation: https://openpyxl.readthedocs.io/
- pdfplumber GitHub: https://github.com/jsvine/pdfplumber
- python-docx documentation: https://python-docx.readthedocs.io/
- Hatch documentation: https://hatch.pypa.io/
- Ruff documentation: https://docs.astral.sh/ruff/
- Python Packaging User Guide: https://packaging.python.org/

**Confidence caveat:** Could not verify current versions via PyPI API (tools were unavailable). Version minimums are conservative. The library choices themselves are HIGH confidence -- these are the established tools in this ecosystem with no credible alternatives emerging as of May 2025.
