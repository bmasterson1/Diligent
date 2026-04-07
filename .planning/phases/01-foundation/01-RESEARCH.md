# Phase 1: Foundation - Research

**Researched:** 2026-04-07
**Domain:** Python CLI scaffold, typed state models, atomic file I/O, YAML/Markdown parsing
**Confidence:** HIGH

## Summary

Phase 1 builds the entire foundation for diligent: pyproject.toml packaging, the click CLI entry point with lazy-loaded subcommands, typed models for all 6 state files, atomic file writes with OneDrive retry, template-based `diligent init`, `diligent doctor`, and `diligent config get/set`. This is a greenfield Python project with no existing code.

The primary technical risks are: (1) YAML round-trip fidelity for TRUTH.md's fenced-code-block-inside-markdown format, (2) atomic writes on Windows with OneDrive file locking, and (3) CLI startup time under 200ms requiring lazy imports. All three have well-known solutions. PyYAML with careful custom handling (not ruamel.yaml, which is overkill here) handles the YAML portions. The markdown-with-embedded-YAML format requires a custom parser that walks H2 headings and extracts fenced YAML blocks, which is straightforward but must be built carefully. Atomic writes use the standard write-temp/fsync/os.replace pattern with exponential backoff retry for WinError 32.

**Primary recommendation:** Build models as Python dataclasses (stdlib, zero dependency, fast instantiation), parse each state file format with dedicated reader/writer modules in `diligent/state/`, use click LazyGroup for sub-200ms startup, and implement atomic writes as a shared utility in `diligent/helpers/io.py`.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- Interactive prompts by default for `diligent init`; `--non-interactive` flag as opt-in escape hatch
- XC-07 scoped: init is exempt from "no interactive prompts" rule (run once by human, never by agent)
- Full DEAL.md frontmatter collected at init: deal code, target name (legal + common), deal stage, LOI date, key people, thesis, workstream selection
- Deal code: short uppercase alpha only (A-Z), 3-12 characters
- Source IDs: `{DEAL_CODE}-{NNN}` (zero-padded, monotonic)
- Thesis input: `$EDITOR` with git-style template, fallback chain (notepad > nano > vi > multi-line CLI)
- TRUTH.md: YAML inside fenced code blocks under markdown H2 headings, flat alphabetical order by key
- TRUTH.md fact fields: value (quoted string always), source (required), date (auto), workstream (validated), supersedes, computed_by (optional), notes (optional), flagged (optional structured object)
- Template content: structural + commented guidance (HTML comments), zero example data entries, parser must skip HTML comments
- Doctor: three check layers (existence, parse, cross-ref), report-only (never mutates), three severity levels (error/warning/info), exit code 0/1, plain text default, no emojis, no color
- Doctor findings: severity, file, location, description, fix (copy-pasteable command)
- CLI output: `--json` on every list/report command, plain text default, no emojis, no color

### Claude's Discretion
- Internal architecture choices (module layout, class hierarchy, error handling patterns)
- Test organization and fixture design
- Specific validation logic implementation details

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INIT-01 | `diligent init` scaffolds `.diligence/` with all 6 state files from templates | Template rendering, click command with prompts, workstream selection |
| INIT-02 | State file readers/writers round-trip all 6 files without data loss | Custom markdown+YAML parser, dataclass models, dedicated reader/writer per file |
| INIT-03 | `diligent doctor` validates integrity, detects corruption, suggests fixes | Three-layer validation (exists, parses, cross-refs), structured finding output |
| INIT-04 | `diligent config get/set` reads/writes config.json (low priority, cut first) | Simple JSON read/write with atomic write |
| INIT-05 | pyproject.toml with hatchling, BSL 1.1 license, package metadata | Hatchling build backend, LicenseRef- for BSL, console_scripts entry point |
| INIT-06 | Atomic file writes with retry/backoff for OneDrive file locks | write-to-temp, fsync, os.replace, exponential backoff on WinError 32/PermissionError |
| INIT-07 | Schema version in config.json; migrate path for future changes | Version field in config.json, stub `diligent migrate` command |
| INIT-08 | CLI startup under 200ms via lazy command loading | Click LazyGroup, defer heavy imports (openpyxl/pdfplumber/python-docx) |
| XC-03 | No network requests, no API keys, no telemetry | Architectural constraint, no HTTP imports, verify at test time |
| XC-04 | Source documents read-only; tool never modifies user files | Architectural constraint, enforced by code review and tests |
| XC-05 | All writes validate resulting file before committing; failure preserves prior state | Validate-after-write pattern in atomic write utility |
| XC-06 | `--json` output flag on every command | JSON serialization for all command output models |
| XC-07 | No interactive prompts that break agent tool-use (scoped: init exempt) | Only init uses prompts; all other commands take input via flags |
| XC-08 | BSL 1.1 license with Additional Use Grant | LICENSE file, license headers in source files |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | 8.1+ | CLI framework | PRD specifies click. LazyGroup for startup perf. CliRunner for testing. |
| pyyaml | 6.0+ | YAML parsing for state files | PRD specifies pyyaml. safe_load/safe_dump for security. |
| hatchling | 1.26+ | Build backend | PRD specifies hatchling. PEP 639 license support. |
| python-frontmatter | 1.1+ | YAML frontmatter parsing for DEAL.md | Handles `---` delimited frontmatter + body separation cleanly. |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.0+ | Test framework | All unit and integration tests |
| pytest-cov | 5.0+ | Coverage reporting | CI and local coverage checks |

### Not Needed Yet (Phase 1)
| Library | Phase | Why Deferred |
|---------|-------|--------------|
| openpyxl | Phase 2+ | Excel diffing, not needed for foundation |
| python-docx | Phase 3+ | Artifact scanning, not needed for foundation |
| pdfplumber | Phase 2+ | Text extraction, not needed for foundation |
| rich | Optional | Pretty output; plain text is the default and only output in Phase 1 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pyyaml | ruamel.yaml | ruamel preserves comments/formatting on round-trip but adds complexity and dependency weight. Not needed: we control the write format entirely via custom serializers. |
| dataclasses | pydantic | Pydantic adds runtime validation but costs ~50ms import time and is a heavy dependency. Dataclasses are stdlib, fast, and validation can be explicit in reader/writer code. |
| python-frontmatter | manual regex | Frontmatter parsing is deceptively fiddly. python-frontmatter handles edge cases (multiline values, encoding). Worth the small dependency. |

**Installation:**
```bash
pip install click pyyaml python-frontmatter
# Dev dependencies
pip install pytest pytest-cov
```

## Architecture Patterns

### Recommended Project Structure
```
diligent/                        # Python package (inside Diligent/ repo root)
  __init__.py                    # Version string only
  cli.py                         # LazyGroup entry point, minimal imports
  commands/                      # One module per subcommand
    __init__.py
    init_cmd.py                  # diligent init (avoid shadowing builtin 'init')
    doctor.py                    # diligent doctor
    config_cmd.py                # diligent config get/set
  state/                         # State file readers/writers
    __init__.py
    models.py                    # Dataclass definitions for all 6 file types
    deal.py                      # DEAL.md reader/writer
    truth.py                     # TRUTH.md reader/writer (the critical one)
    sources.py                   # SOURCES.md reader/writer
    workstreams.py               # WORKSTREAMS.md reader/writer
    state_file.py                # STATE.md reader/writer
    config.py                    # config.json reader/writer
  helpers/                       # Shared utilities
    __init__.py
    io.py                        # Atomic write, OneDrive retry
    formatting.py                # Plain text + JSON output helpers
  templates/                     # Jinja-free string templates for init
    DEAL.md.tmpl
    TRUTH.md.tmpl
    SOURCES.md.tmpl
    WORKSTREAMS.md.tmpl
    STATE.md.tmpl
    config.json.tmpl
tests/
  conftest.py                    # Shared fixtures (tmp_path deal folders, etc.)
  test_models.py                 # Dataclass construction and validation
  test_state_roundtrip.py        # Round-trip fidelity for all 6 files
  test_atomic_write.py           # Atomic write + crash simulation
  test_init.py                   # Init command end-to-end
  test_doctor.py                 # Doctor validation checks
  test_config.py                 # Config get/set
  test_cli_startup.py            # Startup time benchmark
```

### Pattern 1: LazyGroup for Sub-200ms Startup
**What:** Click Group subclass that defers subcommand module imports until invoked.
**When to use:** Always, as the CLI entry point.
**Example:**
```python
# diligent/cli.py
import importlib
import click

class LazyGroup(click.Group):
    def __init__(self, *args, lazy_subcommands=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.lazy_subcommands = lazy_subcommands or {}

    def list_commands(self, ctx):
        base = super().list_commands(ctx)
        lazy = sorted(self.lazy_subcommands.keys())
        return base + lazy

    def get_command(self, ctx, cmd_name):
        if cmd_name in self.lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)

    def _lazy_load(self, cmd_name):
        import_path = self.lazy_subcommands[cmd_name]
        modname, cmdname = import_path.rsplit(".", 1)
        mod = importlib.import_module(modname)
        return getattr(mod, cmdname)

@click.group(cls=LazyGroup, lazy_subcommands={
    "init": "diligent.commands.init_cmd.init_cmd",
    "doctor": "diligent.commands.doctor.doctor",
    "config": "diligent.commands.config_cmd.config_cmd",
})
@click.version_option()
def cli():
    """diligent: due diligence state management."""
    pass
```

### Pattern 2: Atomic Write with OneDrive Retry
**What:** Write to temp file in same directory, fsync, os.replace, with retry on PermissionError.
**When to use:** Every state file mutation.
**Example:**
```python
# diligent/helpers/io.py
import os
import time
import tempfile
from pathlib import Path

MAX_RETRIES = 5
BASE_DELAY = 0.1  # 100ms

def atomic_write(target: Path, content: str, validate_fn=None) -> None:
    """Write content atomically with OneDrive retry.

    Args:
        target: Final file path.
        content: String content to write.
        validate_fn: Optional callable(content) -> bool. If provided,
            content is validated before committing. On failure,
            prior state is preserved and ValueError is raised.
    """
    if validate_fn and not validate_fn(content):
        raise ValueError(f"Validation failed for {target}; prior state preserved.")

    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory (same filesystem for os.replace)
    fd, tmp_path = tempfile.mkstemp(dir=parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        # Retry os.replace for OneDrive file locks
        for attempt in range(MAX_RETRIES):
            try:
                os.replace(tmp_path, target)
                return
            except PermissionError:
                if attempt == MAX_RETRIES - 1:
                    raise
                delay = BASE_DELAY * (2 ** attempt)
                time.sleep(delay)
    except:
        # Clean up temp file on any failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
```

### Pattern 3: State File Reader/Writer (TRUTH.md example)
**What:** Each state file has a dedicated module that reads markdown into a typed dataclass and writes it back.
**When to use:** Every state file read or write.
**Example:**
```python
# diligent/state/models.py
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

@dataclass
class SupersededValue:
    value: str
    source: str
    date: str  # ISO 8601

@dataclass
class FactEntry:
    key: str
    value: str  # Always quoted string in YAML
    source: str
    date: str  # ISO 8601, auto-recorded
    workstream: str
    supersedes: list[SupersededValue] = field(default_factory=list)
    computed_by: Optional[str] = None
    notes: Optional[str] = None
    flagged: Optional[dict] = None  # {reason: str, date: str}

@dataclass
class TruthFile:
    facts: dict[str, FactEntry] = field(default_factory=dict)
    # Keyed by fact key, alphabetical order enforced on write
```

### Pattern 4: HTML Comment-Aware Markdown Walker
**What:** Parser that skips content between `<!--` and `-->` when extracting structured data.
**When to use:** All state file parsers (prevents commented examples from being parsed as real entries).
**Example:**
```python
import re

def strip_html_comments(text: str) -> str:
    """Remove HTML comments from markdown text."""
    return re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)

def extract_h2_sections(text: str) -> dict[str, str]:
    """Split markdown into dict of H2 heading -> section content."""
    clean = strip_html_comments(text)
    sections = {}
    current_heading = None
    current_lines = []

    for line in clean.split('\n'):
        if line.startswith('## '):
            if current_heading:
                sections[current_heading] = '\n'.join(current_lines).strip()
            current_heading = line[3:].strip()
            current_lines = []
        elif current_heading is not None:
            current_lines.append(line)

    if current_heading:
        sections[current_heading] = '\n'.join(current_lines).strip()

    return sections
```

### Pattern 5: Dual Output (Plain Text + JSON)
**What:** Every command produces structured data internally, rendered as plain text by default or JSON with `--json`.
**When to use:** Every command.
**Example:**
```python
import json
import click

def output_findings(findings: list[dict], json_mode: bool) -> None:
    """Render findings as plain text or JSON."""
    if json_mode:
        click.echo(json.dumps(findings, indent=2))
        return
    for f in findings:
        click.echo(f"{f['severity']}: {f['file']}:{f['location']} - {f['description']}")
        click.echo(f"  Fix: {f['fix']}")
    errors = sum(1 for f in findings if f['severity'] == 'ERROR')
    warnings = sum(1 for f in findings if f['severity'] == 'WARNING')
    info = sum(1 for f in findings if f['severity'] == 'INFO')
    click.echo(f"\n{errors} errors, {warnings} warnings, {info} info")
```

### Anti-Patterns to Avoid
- **Importing openpyxl/pdfplumber/python-docx at module level:** Kills startup time. These libraries are 100-300ms each to import. Always import inside the function that needs them.
- **Using yaml.dump for TRUTH.md:** PyYAML's dump reorders keys and mangles formatting. Write TRUTH.md with explicit string formatting, using yaml.dump only for the YAML block inside each fact's fenced code block.
- **Storing thesis in YAML frontmatter:** Multiline YAML strings are fragile. DEAL.md body (after frontmatter) holds the thesis as plain markdown prose.
- **Using ruamel.yaml for "better" round-trip:** Adds complexity and a dependency. We control the write format, so round-trip preservation of arbitrary YAML is not needed.
- **Global mutable state:** Each command reads state from disk on every invocation. No in-memory caches or singletons across commands.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML frontmatter parsing | Regex-based `---` splitter | python-frontmatter | Edge cases: encoding, multiline values, empty frontmatter |
| CLI framework | argparse boilerplate | click with LazyGroup | Help generation, subcommands, CliRunner for testing |
| YAML parsing | Custom YAML tokenizer | pyyaml safe_load/safe_dump | Security (no arbitrary code exec), correctness |
| Temp file management | Manual open/write/rename | tempfile.mkstemp in same dir | Cross-platform, avoids cross-device rename failures |

**Key insight:** The custom work in this phase is the markdown-with-embedded-YAML format for TRUTH.md/SOURCES.md. That parser must be hand-built because no library handles "YAML fenced code blocks under H2 headings in markdown with HTML comment stripping." Everything else has a standard solution.

## Common Pitfalls

### Pitfall 1: PyYAML Implicit Type Coercion
**What goes wrong:** `yaml.safe_load("revenue: 2.4M")` might parse as a string, but `yaml.safe_load("yes: true")` silently converts to boolean. Financial data like `"1,234,567"` or `"N/A"` can be mistyped.
**Why it happens:** YAML spec has implicit type resolution rules. PyYAML follows them.
**How to avoid:** All fact values stored as quoted strings in YAML. The writer must always emit `value: "..."`. The reader must verify the loaded type is str and raise if not.
**Warning signs:** Tests that pass with numeric-looking values but fail with values like "yes", "no", "null", "1.2e3".

### Pitfall 2: os.replace Fails on Windows with OneDrive
**What goes wrong:** `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`.
**Why it happens:** OneDrive's sync process holds file locks briefly during sync. Also affects antivirus scanners.
**How to avoid:** Exponential backoff retry (100ms, 200ms, 400ms, 800ms, 1600ms). Five retries covers ~3 seconds of lock contention, which exceeds typical OneDrive sync lock duration.
**Warning signs:** Intermittent failures on Windows machines with OneDrive enabled, works fine on macOS/Linux.

### Pitfall 3: Cross-Device os.replace
**What goes wrong:** `OSError: [Errno 18] Invalid cross-device link` when temp file is on a different filesystem than target.
**Why it happens:** tempfile.mkstemp defaults to system temp directory, which may be on a different drive/partition than the deal folder.
**How to avoid:** Always create temp file in the same directory as the target (`tempfile.mkstemp(dir=target.parent)`).
**Warning signs:** Works in dev (same drive), fails in production (deal folder on D:, temp on C:).

### Pitfall 4: Click Startup Time Regression
**What goes wrong:** Adding a new command with a top-level `import openpyxl` adds 200ms to every CLI invocation, even `diligent --help`.
**Why it happens:** Python imports are eager by default. Click loads all registered command modules at group creation time unless LazyGroup is used.
**How to avoid:** LazyGroup pattern (see Architecture Patterns). Add a startup time benchmark test that fails if `diligent --help` exceeds 200ms.
**Warning signs:** `time diligent --help` gradually increasing as commands are added.

### Pitfall 5: YAML Fenced Block Parsing Ambiguity
**What goes wrong:** A fact's YAML block contains a line that looks like a fenced code block closer (` ``` `), breaking the parser.
**Why it happens:** Naive regex splitting on ` ``` ` without tracking open/close state.
**How to avoid:** Track fenced block state: opening ` ```yaml ` sets "in block", next bare ` ``` ` closes it. Do not split on ` ``` ` that appears inside a value string.
**Warning signs:** Round-trip tests pass with simple values but fail with values containing backticks.

### Pitfall 6: Template Comment Blocks Parsed as Data
**What goes wrong:** HTML-commented example entries in template files are parsed as real facts, showing phantom data.
**Why it happens:** Parser does not strip HTML comments before extracting structured data.
**How to avoid:** Strip `<!-- ... -->` blocks (including multiline) before parsing. Add a test: parse TRUTH.md template, assert zero facts returned.
**Warning signs:** `diligent doctor` reports facts or sources that nobody entered.

## Code Examples

### pyproject.toml
```toml
[build-system]
requires = ["hatchling>=1.26"]
build-backend = "hatchling.build"

[project]
name = "diligent"
version = "0.1.0"
description = "Due diligence state management CLI"
requires-python = ">=3.11"
license = "LicenseRef-BSL-1.1"
license-files = ["LICENSE"]
authors = [
    { name = "Bryce Masterson" },
]
dependencies = [
    "click>=8.1",
    "pyyaml>=6.0",
    "python-frontmatter>=1.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=5.0",
]

[project.scripts]
diligent = "diligent.cli:cli"
```

### config.json Template
```json
{
    "schema_version": 1,
    "deal_code": "${DEAL_CODE}",
    "created": "${ISO_DATE}",
    "anchor_tolerance_pct": 1.0,
    "recent_window_days": 7,
    "workstreams": []
}
```

### TRUTH.md Format (what the parser reads/writes)
```markdown
# Truth

<!-- This file contains validated facts about the target business.
     Each fact is an H2 heading with a YAML code block containing
     the current value, source citation, and supersedes history.

     Example format (not parsed as data):
     ## example_key
     ```yaml
     value: "example value"
     source: DEAL-001
     date: "2026-01-01"
     workstream: financial
     supersedes: []
     ```
-->

## annual_recurring_revenue
```yaml
value: "2400000"
source: ARRIVAL-001
date: "2026-04-01"
workstream: financial
supersedes: []
```

## customer_count
```yaml
value: "573"
source: ARRIVAL-001
date: "2026-04-01"
workstream: retention
supersedes: []
```
```

### Editor Invocation for Thesis
```python
import os
import subprocess
import sys
import tempfile
from pathlib import Path

THESIS_TEMPLATE = """
# Write your investment thesis below.
# Lines starting with # will be stripped.
# Save and close the editor when done.

"""

def get_editor() -> str | None:
    """Return editor command or None if no editor available."""
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        return editor
    if sys.platform == "win32":
        return "notepad"
    if sys.platform == "darwin":
        return "vi"
    return "nano"

def collect_thesis() -> str:
    """Open editor for thesis input, return cleaned text."""
    editor = get_editor()
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(THESIS_TEMPLATE)
        tmp_path = f.name
    try:
        subprocess.run([editor, tmp_path], check=True)
        text = Path(tmp_path).read_text(encoding="utf-8")
        # Strip comment lines
        lines = [ln for ln in text.split("\n") if not ln.startswith("#")]
        return "\n".join(lines).strip()
    finally:
        os.unlink(tmp_path)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| setup.py + setuptools | pyproject.toml + hatchling | 2022-2023 | Hatchling is now standard for new projects. PEP 639 license support in hatchling 1.26+. |
| argparse | click 8.x with LazyGroup | 2023+ | LazyGroup pattern is the standard for CLIs with many subcommands. |
| atomicwrites library | stdlib tempfile + os.replace | 2022+ | atomicwrites is unmaintained. The stdlib pattern is preferred. |
| pydantic v1 | pydantic v2 or stdlib dataclasses | 2023+ | For lightweight models without API validation needs, dataclasses are preferred to avoid the import cost. |

**Deprecated/outdated:**
- `atomicwrites` library: Last release 2021, unmaintained. Use stdlib tempfile + os.replace instead.
- `yaml.load()` without Loader: Security risk. Always use `yaml.safe_load()`.
- `setup.py` / `setup.cfg`: Replaced by `pyproject.toml`. Hatchling is the modern build backend.

## Open Questions

1. **PyPI name availability for "diligent"**
   - What we know: STATE.md flags this as a blocker. Must resolve before pyproject.toml is finalized.
   - What's unclear: Whether the name is taken or squatted.
   - Recommendation: Check PyPI immediately. Have a backup name ready. This blocks INIT-05 but not the rest of Phase 1 (package name can be patched later).

2. **OneDrive atomic write behavior on actual synced folder**
   - What we know: WinError 32 is the expected failure mode. Retry with backoff should handle it.
   - What's unclear: Exact lock duration and frequency. Whether os.replace specifically triggers locks vs. normal writes.
   - Recommendation: Implement the retry pattern, then test on a real OneDrive-synced folder during Phase 1. Log retry attempts so we can tune the backoff.

3. **TRUTH.md fenced YAML block: exact fence syntax**
   - What we know: User decided YAML inside fenced code blocks under H2 headings.
   - What's unclear: Whether to use ` ```yaml ` or ` ``` ` for the fence opener. Whether indentation matters.
   - Recommendation: Use ` ```yaml ` for syntax highlighting in editors. Parser should accept both. No indentation inside the block.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ -x --tb=short` |
| Full suite command | `pytest tests/ --cov=diligent --cov-report=term-missing` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INIT-01 | init creates .diligence/ with 6 files | integration | `pytest tests/test_init.py -x` | Wave 0 |
| INIT-02 | Round-trip fidelity for all 6 files | unit | `pytest tests/test_state_roundtrip.py -x` | Wave 0 |
| INIT-03 | Doctor detects corruption, suggests fixes | integration | `pytest tests/test_doctor.py -x` | Wave 0 |
| INIT-04 | Config get/set works | unit | `pytest tests/test_config.py -x` | Wave 0 |
| INIT-05 | pyproject.toml valid, package builds | smoke | `hatch build` | Wave 0 |
| INIT-06 | Atomic write survives simulated crash | unit | `pytest tests/test_atomic_write.py -x` | Wave 0 |
| INIT-07 | Schema version in config.json | unit | `pytest tests/test_config.py::test_schema_version -x` | Wave 0 |
| INIT-08 | CLI startup under 200ms | benchmark | `pytest tests/test_cli_startup.py -x` | Wave 0 |
| XC-03 | No network requests | unit | `pytest tests/test_no_network.py -x` | Wave 0 |
| XC-04 | Source documents read-only | architectural | Manual review + test assertions | Wave 0 |
| XC-05 | Writes validate before committing | unit | `pytest tests/test_atomic_write.py::test_validation_failure -x` | Wave 0 |
| XC-06 | --json output on every command | integration | `pytest tests/test_json_output.py -x` | Wave 0 |
| XC-07 | No interactive prompts (except init) | integration | `pytest tests/test_no_prompts.py -x` | Wave 0 |
| XC-08 | BSL 1.1 license present | smoke | `pytest tests/test_license.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x --tb=short`
- **Per wave merge:** `pytest tests/ --cov=diligent --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` -- shared fixtures (tmp_path deal folder, pre-populated .diligence/)
- [ ] `tests/test_state_roundtrip.py` -- covers INIT-02
- [ ] `tests/test_atomic_write.py` -- covers INIT-06, XC-05
- [ ] `tests/test_init.py` -- covers INIT-01
- [ ] `tests/test_doctor.py` -- covers INIT-03
- [ ] `tests/test_config.py` -- covers INIT-04, INIT-07
- [ ] `tests/test_cli_startup.py` -- covers INIT-08
- [ ] `tests/test_json_output.py` -- covers XC-06
- [ ] `pyproject.toml` -- pytest config section
- [ ] Framework install: `pip install pytest pytest-cov`

## Sources

### Primary (HIGH confidence)
- [Click Complex Applications - LazyGroup pattern](https://click.palletsprojects.com/en/stable/complex/)
- [Click Testing - CliRunner](https://click.palletsprojects.com/en/stable/testing/)
- [Python Packaging Guide - pyproject.toml](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [PyYAML Documentation](https://pyyaml.org/wiki/PyYAMLDocumentation)
- [python-frontmatter documentation](https://python-frontmatter.readthedocs.io/)
- [hatchling PyPI](https://pypi.org/project/hatchling/)

### Secondary (MEDIUM confidence)
- [atomicwrites pattern](https://github.com/untitaker/python-atomicwrites) - unmaintained but pattern is sound
- [Click performance discussion](https://github.com/pallets/click/discussions/2692) - confirms lazy loading solves startup
- [PyYAML tips for avoiding type coercion](https://reorx.com/blog/python-yaml-tips/)

### Tertiary (LOW confidence)
- OneDrive file locking specifics: no official documentation found on exact lock duration/behavior. Retry pattern is based on community experience, not Microsoft docs.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - PRD specifies click/pyyaml/hatchling; versions verified against PyPI
- Architecture: HIGH - LazyGroup, atomic write, dataclass models are well-established patterns
- Pitfalls: HIGH - YAML coercion, OneDrive locking, cross-device rename are well-documented issues
- TRUTH.md parser: MEDIUM - Custom format requires hand-built parser; design is sound but implementation needs careful testing

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (stable domain, 30 days)
