# Phase 5: Status, Handoff, and Distribution - Research

**Researched:** 2026-04-08
**Domain:** CLI aggregation commands, markdown generation, PyPI packaging, IDE skill file installation
**Confidence:** HIGH

## Summary

Phase 5 builds three new commands (`status`, `handoff`, `install`) and prepares the package for PyPI distribution. All three commands are read-only against existing state files and follow patterns already established in Phases 1-4: LazyGroup registration, `_find_diligence_dir` lookup, plain-text-by-default with `--json` flag, no color, no emojis.

The `status` and `handoff` commands are aggregators: they read all 8 state files plus task directories and produce formatted output. The `install` command writes files outside `.diligence/` (to `~/.claude/skills/` or `~/.agents/skills/`), which is new territory. Distribution requires resolving the PyPI name conflict (the name "diligent" is taken by an abandoned parquet-database tool, version 0.0.5 from January 2023), configuring hatchling to include `.md` skill template files as package data, and writing a README under 100 lines.

**Primary recommendation:** Build status and handoff first (they share the same state-reading infrastructure), then install command and skill templates, then packaging/README last. The clipboard helper is a small utility that plugs into handoff. PyPI name resolution should happen first as a prerequisite since it affects pyproject.toml.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Status output: sectioned report format with five sections (deal header, workstreams, stale artifacts, open questions, recent activity), each capped at ~5 items with "and N more" truncation
- Status header line: deal name, target name, stage, LOI date, days-in-diligence counter. Pre-LOI fallback: "N days tracking" from STATE.md created date
- Status workstreams section: one line per workstream with inline counts (facts, questions, artifacts, stale count)
- Status stale artifacts section: artifact path, count of changed facts, days since refresh
- Status open questions section: ID, origin tag [gate]/[manual], workstream, truncated question text. Capped at 5 with "and N more"
- Status recent activity section: derived from timestamps across all state files (no event log, no new data structure). Verb-past-tense format with relative time under 14 days, absolute date beyond
- Summary line at bottom: "N items need attention"
- Always deal-wide scope. No `--workstream` filter on status
- `--verbose` expands all sections; `--json` emits structured output
- Plain text, no emojis, no color by default
- Handoff: no hard token cap, "dumb and complete" approach
- Handoff default content: DEAL.md full, WORKSTREAMS.md full, recent TRUTH.md facts (14 days), recent SOURCES.md entries (14 days), all open questions, all stale/flagged artifacts, most recent SUMMARY.md from each active workstream
- Handoff recency rule: time window for facts/sources/activity; all open questions, flagged facts, and stale artifacts always included
- `--since` overrides 14-day default (e.g., `--since 7d`, `--since 2026-03-15`). Configurable default via `recent_window_days` in config.json (handoff default is double: 14 days)
- `--everything` bypasses time window, dumps complete state
- Instruction header at top of every handoff: brief block explaining diligent, key concepts, editorial principles
- `---` separator between header and deal state data
- Output to stdout by default. `--clip` copies to clipboard AND prints to stdout
- Clipboard helper: platform subprocess wrapper (~15 lines), clip.exe/pbcopy/wl-copy+xclip, returns bool, no crash on failure
- Skill files: grouped by domain (~6 files), not one-per-command. Prefixed dd: in namespace
- Skill content: description, when-to-use triggers, command reference, rules, common workflows
- Parameterized with `{{DILIGENT_PATH}}` only, replaced at install time via `shutil.which('diligent')`
- Skill templates shipped inside Python package (diligent/skills/)
- `diligent install --claude-code` writes to `~/.claude/skills/`, `--antigravity` writes to `~/.agents/skills/`
- `--path` flag overrides default directory
- `diligent install --uninstall` removes installed skill files by naming convention
- Fail with clear error if target directory doesn't exist
- PyPI: check availability of "diligent" first (CONFIRMED TAKEN -- see research below). Fallback preference: (1) different real word, (2) diligent-dd or diligent-cli, (3) dd-diligent
- CLI entry point stays `diligent` regardless of package name
- Reserve name on PyPI early (0.0.0 placeholder)
- pyproject.toml already has hatchling, entry point, BSL, dependencies. No new dependencies
- README: minimal + quickstart, under 100 lines. "What it is not" section
- Full command reference in USER-GUIDE.md, not README
- Manual smoke test on clean machine, no automated quickstart script in v1

### Claude's Discretion
- Exact section ordering within status output (workstreams first vs stale first)
- Activity event type list and rendering format details
- Handoff section ordering within the data portion
- Skill file exact content and wording (given the structured template pattern)
- Skill install path for Antigravity (needs verification -- CONFIRMED: `~/.agents/skills/`)
- README exact wording and quickstart step selection
- Whether `--since` accepts relative durations (7d) or only ISO dates, or both

### Deferred Ideas (OUT OF SCOPE)
- Skill packages for Cursor, Windsurf, and other AI-IDE runtimes (RT-01, v2)
- Auto-suggest which facts an ingested document might affect (ING-02, v2)
- USER-GUIDE.md full command reference (ships separately, not blocking v1 PyPI publish)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STATE-01 | `diligent status` provides full state summary | All 8 state readers exist; aggregation pattern in workstream_cmd.py `show` subcommand demonstrates cross-file reading |
| STATE-02 | Status output plain text, sectioned, --json flag | `output_result` helper in formatting.py; established dual-output pattern across all prior commands |
| STATE-03 | `diligent handoff` generates paste-ready markdown | Template rendering via `render_template`; state file readers provide all data |
| STATE-04 | Handoff reads DEAL.md, STATE.md, WORKSTREAMS.md, recent TRUTH/SOURCES, open questions, task SUMMARYs | All readers available: `read_deal`, `read_state`, `read_workstreams`, `read_truth`, `read_sources`, `read_questions`, `read_artifacts`; task reading via `_read_tasks` pattern in task_cmd.py |
| STATE-05 | Recent is configurable via config.json, defaults to 7 days + flagged/stale | `ConfigFile.recent_window_days` already exists; handoff doubles it to 14 days |
| STATE-06 | Handoff output is paste buffer, not file reference | stdout + optional clipboard via platform subprocess |
| DIST-01 | Package on PyPI, `pipx install` works | pyproject.toml already configured with hatchling; name "diligent" is taken, need fallback |
| DIST-02 | `install --antigravity` drops SKILL.md to skills dir | Confirmed path: `~/.agents/skills/`; `render_template` handles parameterization |
| DIST-03 | `install --claude-code` drops SKILL.md to skills dir | Confirmed path: `~/.claude/skills/`; same mechanism |
| DIST-04 | `install --uninstall` removes installed skill files | Naming convention (dd_*.md) enables cleanup |
| DIST-05 | SKILL.md parameterized with CLI binary path | `shutil.which('diligent')` resolves binary; `string.Template` substitution pattern exists |
| DIST-06 | One SKILL.md per domain (6 files), dd: prefix | 6 skill templates: dd_truth.md, dd_sources.md, dd_artifacts.md, dd_questions.md, dd_workstreams.md, dd_status.md |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=8.1 | CLI framework | Already used; LazyGroup pattern established |
| pyyaml | >=6.0 | YAML parsing in state files | Already used in all state readers |
| python-frontmatter | >=1.1 | DEAL.md/STATE.md frontmatter | Already used in deal.py, state_file.py |
| hatchling | >=1.26 | Build backend | Already configured in pyproject.toml |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| shutil | stdlib | `shutil.which()` for CLI binary lookup | install command parameterization |
| subprocess | stdlib | Clipboard (clip.exe/pbcopy/xclip) | handoff --clip flag |
| platform | stdlib | OS detection for clipboard | handoff --clip flag |
| datetime | stdlib | Date math for days-in-diligence, relative times | status and handoff time calculations |
| string.Template | stdlib | Skill file parameterization | install command |
| json | stdlib | --json output, config reading | All three new commands |
| pathlib | stdlib | Path manipulation | All three new commands |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| subprocess clipboard | pyperclip | Adds dependency; CONTEXT.md explicitly says no pyperclip |
| string.Template for skills | Jinja2 | Adds dependency; project has zero Jinja2 usage; string.Template is sufficient |

**Installation:**
No new dependencies. All libraries already in pyproject.toml or stdlib.

## Architecture Patterns

### New Files to Create
```
diligent/
  commands/
    status_cmd.py         # diligent status command
    handoff_cmd.py        # diligent handoff command
    install_cmd.py        # diligent install command
  helpers/
    clipboard.py          # Platform clipboard wrapper (~15 lines)
    time_utils.py         # Relative time formatting, --since parsing
  skills/                 # Skill template files (package data)
    dd_truth.md
    dd_sources.md
    dd_artifacts.md
    dd_questions.md
    dd_workstreams.md
    dd_status.md
README.md                 # PyPI readme, <100 lines
```

### Pattern 1: Aggregation Command (status, handoff)
**What:** Read-only commands that load multiple state files and produce formatted output
**When to use:** Any command that summarizes deal state without modifying it
**Example:**
```python
# Source: existing pattern in workstream_cmd.py workstream_show
# and reconcile_cmd.py reconcile_cmd
def _find_diligence_dir(env_cwd=None):
    """Standard pattern -- duplicated per command module per project convention."""
    if env_cwd:
        candidate = Path(env_cwd) / ".diligence"
        if candidate.is_dir():
            return candidate
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".diligence"
        if candidate.is_dir():
            return candidate
    raise click.ClickException("No .diligence/ directory found. Run 'diligent init' first.")

@click.command("status")
@click.option("--verbose", is_flag=True, default=False)
@click.option("--json", "json_mode", is_flag=True, default=False)
@click.pass_context
def status_cmd(ctx, verbose, json_mode):
    env_cwd = os.environ.get("DILIGENT_CWD")
    diligence = _find_diligence_dir(env_cwd)
    
    # Read state files (lazy imports inside function)
    from diligent.state.deal import read_deal
    from diligent.state.truth import read_truth
    # ... etc
    
    deal = read_deal(diligence / "DEAL.md")
    truth = read_truth(diligence / "TRUTH.md")
    # ... aggregate, format, output
```

### Pattern 2: LazyGroup Registration
**What:** Every new command registers in cli.py lazy_subcommands dict
**When to use:** All new top-level commands
**Example:**
```python
# In cli.py, add to lazy_subcommands dict:
"status": "diligent.commands.status_cmd.status_cmd",
"handoff": "diligent.commands.handoff_cmd.handoff_cmd",
"install": "diligent.commands.install_cmd.install_cmd",
```

### Pattern 3: Dual Output (text/JSON)
**What:** Build data structure first, then render as plain text or JSON
**When to use:** Every command with --json flag
**Example:**
```python
# Build structured data
data = {
    "deal": { ... },
    "workstreams": [ ... ],
    "stale_artifacts": [ ... ],
    "open_questions": [ ... ],
    "recent_activity": [ ... ],
    "attention_count": N,
}

if json_mode:
    click.echo(json.dumps(data, indent=2, default=str))
else:
    # Render plain text sections
    _print_header(data["deal"])
    _print_workstreams(data["workstreams"], verbose)
    # ...
```

### Pattern 4: Platform Clipboard
**What:** Subprocess-based clipboard with platform detection, never crashes
**When to use:** handoff --clip
**Example:**
```python
import platform
import subprocess

def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard. Returns True on success."""
    system = platform.system()
    try:
        if system == "Windows":
            proc = subprocess.run(
                ["clip.exe"], input=text, text=True, timeout=5,
                capture_output=True,
            )
        elif system == "Darwin":
            proc = subprocess.run(
                ["pbcopy"], input=text, text=True, timeout=5,
                capture_output=True,
            )
        else:  # Linux/FreeBSD
            for cmd in ["wl-copy", "xclip -selection clipboard"]:
                parts = cmd.split()
                try:
                    proc = subprocess.run(
                        parts, input=text, text=True, timeout=5,
                        capture_output=True,
                    )
                    return proc.returncode == 0
                except FileNotFoundError:
                    continue
            return False
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False
```

### Pattern 5: Time Window Filtering
**What:** Filter state entries by date relative to now, with configurable window
**When to use:** handoff default content, status recent activity
**Example:**
```python
from datetime import date, timedelta

def parse_since(since_str: str, default_days: int) -> date:
    """Parse --since flag. Accepts '7d', '14d', or ISO date '2026-03-15'."""
    if since_str is None:
        return date.today() - timedelta(days=default_days)
    if since_str.endswith("d"):
        days = int(since_str[:-1])
        return date.today() - timedelta(days=days)
    return date.fromisoformat(since_str)

def is_recent(entry_date_str: str, cutoff: date) -> bool:
    """Check if an entry date string is on or after the cutoff."""
    try:
        entry_date = date.fromisoformat(entry_date_str[:10])
        return entry_date >= cutoff
    except (ValueError, TypeError):
        return False
```

### Anti-Patterns to Avoid
- **Shared _find_diligence_dir utility**: The project convention is to duplicate this function per command module. Do not refactor into a shared module; that would break the pattern established in 7 existing modules.
- **Event log for recent activity**: CONTEXT.md explicitly says "no event log, no new data structure." Derive timestamps from existing state files.
- **Importing all state readers at module level**: Use lazy imports inside functions to preserve <200ms startup.
- **Color or emoji output**: The project convention is plain text only.
- **Interactive prompts in install**: XC-07 forbids interactive prompts.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing | Custom YAML parser | pyyaml (already used) | Fenced YAML blocks established in all state files |
| Template rendering | Custom templating | string.Template (already used) | render_template exists in templates/__init__.py |
| Atomic writes | Custom file write | atomic_write (already exists) | Not needed for read-only commands, but available if install needs it |
| State file reading | Direct file parsing | read_deal/read_truth/etc (already exist) | All 8 readers are battle-tested |
| CLI argument parsing | argparse | Click (already used) | LazyGroup pattern established |
| Clipboard | pyperclip library | subprocess + platform detection | CONTEXT.md says no pyperclip; ~15 lines of subprocess |

**Key insight:** Phase 5 is almost entirely composed of reading data structures built in Phases 1-4 and formatting them. Nearly all building blocks exist.

## Common Pitfalls

### Pitfall 1: Startup Time Regression
**What goes wrong:** Importing all state readers at module top-level pushes startup past 200ms
**Why it happens:** status and handoff need many state readers, tempting top-level imports
**How to avoid:** Import state readers inside the command function (lazy import pattern used in workstream_cmd.py)
**Warning signs:** `test_cli_startup.py` benchmark fails (exists since Phase 1)

### Pitfall 2: PyPI Name Conflict
**What goes wrong:** Publishing fails because "diligent" is taken
**Why it happens:** Name was reserved by another project (0.0.5, Jan 2023, abandoned parquet tool)
**How to avoid:** Resolve name before any packaging work. Check availability of fallback names. Reserve with 0.0.0 placeholder immediately.
**Warning signs:** `pip install diligent` installs the wrong package

### Pitfall 3: Missing Package Data in Wheel
**What goes wrong:** Skill template .md files not included in pip install
**Why it happens:** Hatchling only includes Python files by default; .md files in diligent/skills/ need explicit inclusion
**How to avoid:** Add `[tool.hatch.build.targets.wheel]` with `packages = ["diligent"]` (this already captures everything under diligent/), but verify .md files are included. If using .gitignore or hatch exclude patterns, ensure skills/*.md is not excluded.
**Warning signs:** `diligent install --claude-code` fails with FileNotFoundError on clean pip install

### Pitfall 4: Clipboard Failure Crashes Command
**What goes wrong:** `handoff --clip` crashes when clip.exe/pbcopy not available (e.g., headless server)
**Why it happens:** subprocess.run raises FileNotFoundError when binary not found
**How to avoid:** Wrap in try/except, return bool, print warning, continue outputting to stdout
**Warning signs:** Command fails on CI or in containers

### Pitfall 5: Date Parsing Edge Cases
**What goes wrong:** Relative time calculations fail on entries with missing or malformed dates
**Why it happens:** Some state file entries might have empty date strings, or dates that are datetime strings vs date strings
**How to avoid:** Always parse with try/except, slice to first 10 chars for ISO date portion, handle empty strings gracefully
**Warning signs:** TypeError or ValueError on `date.fromisoformat()` in status command

### Pitfall 6: Stale Artifact Count Mismatch with Reconcile
**What goes wrong:** Status shows different stale count than `diligent reconcile`
**Why it happens:** Status uses simplified staleness check (date comparison) while reconcile uses full engine (reconcile_anchors.py)
**How to avoid:** Import and use `compute_staleness` from reconcile_anchors.py for the stale artifact section in status, ensuring consistency
**Warning signs:** Users see different numbers between `diligent status` and `diligent reconcile`

### Pitfall 7: Windows Path Issues in Skill Templates
**What goes wrong:** `shutil.which('diligent')` returns Windows path with backslashes; template substitution breaks shell commands
**Why it happens:** Windows paths use backslashes by default
**How to avoid:** Convert `shutil.which()` result to forward slashes or use the path as-is (Windows handles both in most contexts). Or use `pathlib.Path(shutil.which('diligent')).as_posix()` if needed in shell-style contexts.
**Warning signs:** Skill files contain broken paths on Windows

## Code Examples

### Status Header Rendering
```python
# Source: CONTEXT.md locked decision
def _format_header(deal, state_created):
    """Format the status header line.
    
    Post-LOI: "Project Arrival -- OnTime 360 (Vesigo Studios, LLC)"
              "Stage: post-LOI | LOI: 2026-01-15 | 57 days in diligence"
    Pre-LOI:  "Stage: pre-LOI | 12 days tracking"
    """
    from datetime import date
    
    header = f"{deal.deal_code} -- {deal.target_common_name} ({deal.target_legal_name})"
    
    if deal.deal_stage == "post-LOI" and deal.loi_date:
        loi = date.fromisoformat(str(deal.loi_date)[:10])
        days = (date.today() - loi).days
        stage_line = f"Stage: {deal.deal_stage} | LOI: {deal.loi_date} | {days} days in diligence"
    else:
        created = date.fromisoformat(str(state_created)[:10])
        days = (date.today() - created).days
        stage_line = f"Stage: {deal.deal_stage} | {days} days tracking"
    
    return f"{header}\n{stage_line}"
```

### Recent Activity Derivation
```python
# Source: CONTEXT.md decision -- derive from timestamps, no event log
def _collect_activity(truth, sources, artifacts, questions, cutoff_days=14):
    """Collect recent activity from existing timestamps in state files."""
    from datetime import date, timedelta
    
    cutoff = date.today() - timedelta(days=cutoff_days)
    events = []
    
    # Facts updated recently
    for key, fact in truth.facts.items():
        fact_date = date.fromisoformat(fact.date[:10])
        if fact_date >= cutoff:
            events.append((fact_date, f"set fact '{key}' from {fact.source}"))
    
    # Sources ingested recently
    for src in sources.sources:
        src_date = date.fromisoformat(src.date_received[:10])
        if src_date >= cutoff:
            events.append((src_date, f"ingested {src.id} ({src.path})"))
    
    # Sort by date descending
    events.sort(key=lambda e: e[0], reverse=True)
    return events
```

### Handoff Instruction Header Template
```python
# Source: CONTEXT.md decision -- static template with deal name substitution
HANDOFF_HEADER = """# ${DEAL_CODE} Deal Context

You are resuming a due diligence engagement managed by **diligent**, a CLI for deal state management. This document contains the current state of the deal.

## Key concepts
- **TRUTH.md**: validated facts with source citations. Every fact has a source ID.
- **SOURCES.md**: registered source documents with dates and parties.
- **ARTIFACTS.md**: deliverables (memos, models, reports) with fact dependencies.
- **QUESTIONS.md**: open questions and answered questions with citations.
- **WORKSTREAMS.md**: organizational groupings for the diligence process.

## Editorial principles
- Source every claim. Never state a fact without a source citation.
- Never invent values. If a number is not in a source document, do not guess.
- Flag discrepancies rather than resolving silently. When two sources disagree, raise a question.
- No AI template phrasing. Write like an analyst, not a chatbot.

---
"""
```

### Skill File Template Pattern
```python
# Source: CONTEXT.md decision -- parameterized with {{DILIGENT_PATH}} only
# Example: diligent/skills/dd_truth.md
"""
# dd:truth

Manage validated facts in the deal's TRUTH.md file.

## When to use
- Analyst mentions recording a data point, metric, or finding
- Analyst asks to check or verify a fact
- Analyst wants to see the history of a value
- Analyst mentions flagging something for review

## Commands

### Set a fact
```bash
{{DILIGENT_PATH}} truth set <key> <value> --source <source-id> --workstream <ws>
```
...
"""
```

### LazyGroup Registration
```python
# Source: existing cli.py pattern
# Add three new entries to lazy_subcommands dict in cli.py:
lazy_subcommands={
    # ... existing entries ...
    "status": "diligent.commands.status_cmd.status_cmd",
    "handoff": "diligent.commands.handoff_cmd.handoff_cmd",
    "install": "diligent.commands.install_cmd.install_cmd",
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| setuptools | hatchling | 2023-2024 | Already using hatchling; no migration needed |
| setup.py + MANIFEST.in | pyproject.toml + [tool.hatch.build] | 2023-2024 | Include .md files via hatch build config |
| pyperclip for clipboard | subprocess + platform detection | Always available | Zero-dependency clipboard, per CONTEXT.md |

**Deprecated/outdated:**
- setup.py: project already uses pyproject.toml exclusively
- MANIFEST.in: replaced by hatchling include/exclude patterns

## PyPI Name Resolution

**Status:** The name "diligent" is taken on PyPI (version 0.0.5, published 2023-01-07, a parquet-database transformer tool by user "lipi"). The project appears abandoned with no updates in over 3 years.

**Fallback options per CONTEXT.md priority:**
1. Different real word from PRD list: tether, plumb, searchlight, bedrock, veritas, anchor
2. Suffix: diligent-dd, diligent-cli
3. Prefix: dd-diligent

**Recommendation:** Check availability of "diligent-dd" first (short, memorable, CLI entry point still `diligent`). The PRD alternate names change the entire brand identity, so the suffix approach is lower risk. The planner should include a task to check PyPI availability for fallback names and update pyproject.toml accordingly.

**Note:** It is possible to claim abandoned package names on PyPI via PEP 541, but this process is slow and uncertain. Do not depend on it for v1 timeline.

## Hatchling Package Data Configuration

Skill template `.md` files in `diligent/skills/` need to be included in the wheel. By default, hatchling includes all files tracked by VCS (git) under the package directory. Since `diligent/skills/*.md` will be new files added to git, they should be included automatically.

**Verify by running:**
```bash
hatch build
unzip -l dist/diligent-*.whl | grep skills
```

If files are missing, add explicit inclusion:
```toml
[tool.hatch.build.targets.wheel]
packages = ["diligent"]
```

This tells hatchling to include the entire `diligent/` directory tree, including non-Python files, as long as they are git-tracked.

## Skill Install Directory Paths

| Runtime | Path | Confirmed |
|---------|------|-----------|
| Claude Code | `~/.claude/skills/` | YES -- verified on this machine |
| Antigravity | `~/.agents/skills/` | YES -- verified on this machine |

Both directories exist on the development machine. The `install` command should expand `~` to the actual home directory using `pathlib.Path.home()`.

Naming convention for installed files: `dd_truth.md`, `dd_sources.md`, etc. The `dd_` prefix enables `--uninstall` to find and remove only diligent's files without affecting other skills.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/ -x --timeout=30` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STATE-01 | Status shows full deal state | integration | `pytest tests/test_status_cmd.py -x` | No -- Wave 0 |
| STATE-02 | Plain text + --json output | integration | `pytest tests/test_status_cmd.py::TestStatusJson -x` | No -- Wave 0 |
| STATE-03 | Handoff generates markdown doc | integration | `pytest tests/test_handoff_cmd.py -x` | No -- Wave 0 |
| STATE-04 | Handoff reads all state files | integration | `pytest tests/test_handoff_cmd.py::TestHandoffContent -x` | No -- Wave 0 |
| STATE-05 | Configurable recency window | unit | `pytest tests/test_handoff_cmd.py::TestHandoffRecency -x` | No -- Wave 0 |
| STATE-06 | Output is paste buffer (stdout) | integration | `pytest tests/test_handoff_cmd.py::TestHandoffOutput -x` | No -- Wave 0 |
| DIST-01 | Package installable from PyPI | manual-only | Manual: `pipx install` on clean machine | N/A |
| DIST-02 | install --antigravity drops skills | integration | `pytest tests/test_install_cmd.py::TestInstallAntigravity -x` | No -- Wave 0 |
| DIST-03 | install --claude-code drops skills | integration | `pytest tests/test_install_cmd.py::TestInstallClaudeCode -x` | No -- Wave 0 |
| DIST-04 | install --uninstall removes skills | integration | `pytest tests/test_install_cmd.py::TestUninstall -x` | No -- Wave 0 |
| DIST-05 | Skills parameterized with CLI path | unit | `pytest tests/test_install_cmd.py::TestSkillParameterization -x` | No -- Wave 0 |
| DIST-06 | 6 skill files, dd: domain grouping | unit | `pytest tests/test_install_cmd.py::TestSkillFileCount -x` | No -- Wave 0 |

### Additional Tests
| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| Clipboard helper | unit | `pytest tests/test_clipboard.py -x` | No -- Wave 0 |
| Time parsing (--since) | unit | `pytest tests/test_time_utils.py -x` | No -- Wave 0 |
| Relative time formatting | unit | `pytest tests/test_time_utils.py::TestRelativeTime -x` | No -- Wave 0 |
| Status under 2 seconds | performance | `pytest tests/test_performance.py -x -m "not slow"` | Exists (Phase 1) |
| CLI startup under 200ms | performance | `pytest tests/test_cli_startup.py -x` | Exists (Phase 1) |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x --timeout=30`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_status_cmd.py` -- covers STATE-01, STATE-02
- [ ] `tests/test_handoff_cmd.py` -- covers STATE-03, STATE-04, STATE-05, STATE-06
- [ ] `tests/test_install_cmd.py` -- covers DIST-02, DIST-03, DIST-04, DIST-05, DIST-06
- [ ] `tests/test_clipboard.py` -- covers clipboard helper
- [ ] `tests/test_time_utils.py` -- covers --since parsing and relative time formatting

## Open Questions

1. **PyPI package name fallback**
   - What we know: "diligent" is taken (abandoned since Jan 2023). CONTEXT.md lists fallback preferences.
   - What's unclear: Which fallback names are available on PyPI right now.
   - Recommendation: First task should check availability of "diligent-dd", then "diligent-cli", then PRD word list. Reserve whichever is available with 0.0.0 placeholder.

2. **README content scope**
   - What we know: Under 100 lines, quickstart format, "what it is not" section.
   - What's unclear: Exact quickstart steps to include.
   - Recommendation: init, ingest, truth set, reconcile, status, handoff -- covers the core loop in 6 steps. Defer to Claude's discretion per CONTEXT.md.

3. **Staleness computation reuse in status**
   - What we know: reconcile_anchors.py has `compute_staleness` which is the authoritative engine.
   - What's unclear: Whether status should use the full engine or a simpler heuristic.
   - Recommendation: Use `compute_staleness` directly. The function is pure (no I/O), fast, and already tested. Avoids count mismatches between status and reconcile.

## Sources

### Primary (HIGH confidence)
- Codebase analysis: cli.py, all command modules, all state modules, models.py, formatting.py, templates/__init__.py, io.py, conftest.py
- pyproject.toml: current build configuration
- CONTEXT.md: all locked decisions and discretion areas

### Secondary (MEDIUM confidence)
- [PyPI "diligent" package page](https://pypi.org/project/diligent/) -- confirmed taken, v0.0.5, Jan 2023
- [Hatchling build configuration docs](https://hatch.pypa.io/1.13/config/build/) -- package data inclusion patterns
- Machine verification: ~/.claude/skills/ and ~/.agents/skills/ paths confirmed locally

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, everything is stdlib or already in pyproject.toml
- Architecture: HIGH -- all patterns directly observed in existing codebase; new commands follow identical structure
- Pitfalls: HIGH -- based on concrete codebase analysis and confirmed PyPI conflict
- Distribution: MEDIUM -- hatchling package data inclusion needs build-time verification; PyPI name needs resolution

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable domain, no fast-moving dependencies)
