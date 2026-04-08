# Phase 4: Workstreams, Tasks, and Questions - Research

**Researched:** 2026-04-08
**Domain:** CLI command groups, filesystem-backed task management, state file extension
**Confidence:** HIGH

## Summary

Phase 4 builds the organizational layer on top of the existing state infrastructure. It adds three command groups (`workstream`, `task`, `ask`/`answer`/`questions`) and extends two existing models (`WorkstreamEntry`, `QuestionEntry`). The code patterns are fully established: H2+YAML state files, Click command groups registered via LazyGroup, `_find_diligence_dir` with `DILIGENT_CWD` for test isolation, atomic writes with validation, and aligned-column text output with `--json` mode.

The key implementation challenge is that tasks live in filesystem directories (`.diligence/workstreams/<ws>/tasks/NNN-<slug>/`) rather than in a state file, making them the first entity that uses directory scanning instead of markdown parsing. Everything else follows directly from existing patterns. The workstream templates (WS-04/WS-05) require extending `init_cmd.py` to create subdirectories with tailored `CONTEXT.md` files during initialization.

**Primary recommendation:** Follow the existing per-module pattern exactly. Replicate `_find_diligence_dir`, replicate H2+YAML parsing, replicate aligned-column output. The codebase prioritizes readability and local reasoning over DRY. All new commands get `--json` mode and use `DILIGENT_CWD` for test isolation.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- `workstream new <name>` creates subdirectory `.diligence/workstreams/<name>/` with CONTEXT.md and RESEARCH.md
- CONTEXT.md holds durable scope; RESEARCH.md holds growing findings record. Both start from templates with HTML comment guidance
- 6 pre-defined templates: financial, retention, technical, legal, hr, integration. Each template has tailored CONTEXT.md with 3-4 commented section headers
- RESEARCH.md stays generic across all templates
- During `diligent init`, present 6 defaults as checklist. Non-interactive: `--workstreams financial,retention,technical`
- WorkstreamEntry model: add `description` field and `created` field (ISO 8601). Status values: active, complete, on-hold
- `workstream show` aggregates stats: description, status, task counts, open question count, fact count, artifact count (with stale count)
- `workstream list`: one line per workstream with name, status, task count, question count. Summary line at bottom
- Task directory: `.diligence/workstreams/<ws>/tasks/NNN-<slug>/` with SUMMARY.md, PLAN.md (optional), VERIFICATION.md (optional)
- Task ID: zero-padded monotonic (001, 002, ...), scanned from existing directories (self-healing)
- Two task states only: open, complete. No in-progress, blocked, or deferred
- `task complete` validates SUMMARY.md is non-empty. No prompts, no editor launch
- `task list`: one line per task with ID, description, status. Summary line at bottom
- `diligent ask "<text>" --workstream <ws> --owner <owner>` -- question text positional, flags optional. Owner defaults to "self"
- Question ID: Q-NNN format, zero-padded, monotonic, scanned from QUESTIONS.md max
- `diligent answer <q-id> "<text>" --source <source-id>` -- answer text positional, --source optional
- QuestionEntry extension: add `answer`, `answer_source`, `date_answered` fields (all Optional)
- `questions list`: shows origin tag [gate] vs [manual] derived from context field presence. Supports --owner filter
- All questions in one list, same QUESTIONS.md, same answer flow
- Cross-entity: workstream is the only structural link. All list/filter commands use `--workstream` flag
- Tasks are positional: `task list <workstream>`, `task new <workstream> <desc>`, `task complete <workstream> <task-id>`

### Claude's Discretion
- Exact workstream template content (the 3-4 section headers per workstream type)
- RESEARCH.md generic template content
- Task slug generation algorithm (lowercase, hyphens, truncation rules)
- PLAN.md and VERIFICATION.md optional template content
- Column alignment widths in list outputs
- Whether `workstream list` shows description or just name

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WS-01 | `workstream new <name>` creates workstream with subdirectory containing CONTEXT.md and RESEARCH.md | New Click command group, filesystem mkdir + template rendering, WorkstreamEntry model extension |
| WS-02 | `workstream list` shows all workstreams with status and task count | H2+YAML reader on WORKSTREAMS.md, directory scan for task counts, aligned-column output pattern |
| WS-03 | `workstream show <name>` displays full workstream detail | Cross-file aggregation reading WORKSTREAMS.md, QUESTIONS.md, TRUTH.md, ARTIFACTS.md, task dirs |
| WS-04 | Pre-defined workstream templates (6 total) | Template files with string.Template, tailored CONTEXT.md per workstream type |
| WS-05 | Workstream customization at init time | Extend init_cmd.py to create workstream subdirectories and tailored templates |
| WS-06 | CLI reads from files on every invocation; hand-edits picked up | Existing pattern: every read is from disk, no caching. Requires WorkstreamEntry reader to handle new fields gracefully |
| TASK-01 | `task new <workstream> <desc>` creates task directory with SUMMARY.md | Directory creation, slug generation, monotonic ID from dir scan, template scaffolding |
| TASK-02 | `task list <workstream>` lists tasks with status | Directory scan for task dirs, read status from each, aligned-column output |
| TASK-03 | `task complete <ws> <task-id>` marks complete with SUMMARY.md validation | Read SUMMARY.md, check non-empty, update task status marker |
| Q-01 | `ask <text>` adds open question with --workstream and --owner | Existing QUESTIONS.md writer + QuestionEntry model, new CLI surface as top-level command |
| Q-02 | Owner taxonomy: self, principal, seller, broker, counsel | Validation in Click command, Choice type or manual validation |
| Q-03 | `answer <q-id> <text>` closes question with optional --source | Existing reader/writer + model extension for answer fields |
| Q-04 | `questions list` shows open questions with --owner filter | Existing reader + aligned-column output + filter logic |
| Q-05 | Gate-rejected questions appear in questions list | Already implemented in truth_cmd.py gate logic; this phase adds origin tag display |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=8.1 | CLI framework | Already in use. LazyGroup pattern established |
| pyyaml | >=6.0 | YAML parsing in state files | Already in use. H2+YAML pipeline replicated per module |
| pytest | >=8.0 | Test framework | Already in use with click.testing.CliRunner |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| string.Template | stdlib | Template rendering | Workstream CONTEXT.md and RESEARCH.md scaffolding |
| pathlib | stdlib | Path manipulation | Task directory creation, slug paths, directory scanning |
| re | stdlib | Regex for slug generation | Task slug: lowercase, hyphens, truncation |
| os | stdlib | DILIGENT_CWD env var, fsync | Test isolation, atomic writes |
| dataclasses | stdlib | Model definitions | WorkstreamEntry and QuestionEntry field extensions |

### Alternatives Considered
None. All patterns are locked by existing codebase conventions.

**Installation:**
No new dependencies. All work uses existing stdlib and already-installed packages.

## Architecture Patterns

### Project Structure (New Files)
```
Diligent/diligent/
  commands/
    workstream_cmd.py   # workstream new/list/show
    task_cmd.py         # task new/list/complete
    question_cmd.py     # ask, answer, questions list
  templates/
    workstreams/        # Per-workstream-type CONTEXT.md templates
      financial.md
      retention.md
      technical.md
      legal.md
      hr.md
      integration.md
    ws_context.md.tmpl  # Generic CONTEXT.md template (fallback)
    ws_research.md.tmpl # Generic RESEARCH.md template (all workstreams)
    task_summary.md.tmpl
    task_plan.md.tmpl
    task_verification.md.tmpl
  state/
    models.py           # Extended (WorkstreamEntry, QuestionEntry)
    workstreams.py       # Updated reader/writer for new fields
    questions.py         # Updated reader/writer for answer fields
```

### Pattern 1: Command Module Structure
**What:** Each command module is self-contained with its own `_find_diligence_dir`, local helpers, and Click command group.
**When to use:** All three new command modules.
**Example:**
```python
# Source: existing pattern from artifact_cmd.py, truth_cmd.py
import os
from pathlib import Path
from typing import Optional

import click

from diligent.helpers.formatting import output_result


def _find_diligence_dir(env_cwd: Optional[str] = None) -> Path:
    if env_cwd:
        candidate = Path(env_cwd) / ".diligence"
        if candidate.is_dir():
            return candidate
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".diligence"
        if candidate.is_dir():
            return candidate
    raise click.ClickException(
        "No .diligence/ directory found. Run 'diligent init' first."
    )


@click.group("workstream")
def workstream_cmd():
    """Manage deal workstreams."""
    pass
```

### Pattern 2: LazyGroup Registration
**What:** New command groups register in cli.py's lazy_subcommands dict.
**When to use:** Registering workstream, task, ask, answer, questions commands.
**Example:**
```python
# Source: existing pattern from cli.py
lazy_subcommands={
    # ... existing commands ...
    "workstream": "diligent.commands.workstream_cmd.workstream_cmd",
    "task": "diligent.commands.task_cmd.task_cmd",
    "ask": "diligent.commands.question_cmd.ask_cmd",
    "answer": "diligent.commands.question_cmd.answer_cmd",
    "questions": "diligent.commands.question_cmd.questions_cmd",
}
```

### Pattern 3: Monotonic ID from Directory Scan
**What:** Task ID derived by scanning existing directories, not a counter file.
**When to use:** `task new` to generate next task ID.
**Example:**
```python
# Source: existing pattern from truth_cmd.py _next_question_id
import re

def _next_task_id(tasks_dir: Path) -> int:
    """Derive next task number from existing directories.
    
    Scans NNN-* pattern directories, returns max+1.
    Self-healing: no counter file needed.
    """
    max_num = 0
    if tasks_dir.exists():
        pattern = re.compile(r"^(\d{3})-")
        for child in tasks_dir.iterdir():
            if child.is_dir():
                m = pattern.match(child.name)
                if m:
                    num = int(m.group(1))
                    if num > max_num:
                        max_num = num
    return max_num + 1
```

### Pattern 4: Task Slug Generation
**What:** Convert description to filesystem-safe slug for task directory name.
**When to use:** `task new` to create task directory.
**Example:**
```python
import re

def _slugify(text: str, max_length: int = 40) -> str:
    """Convert text to lowercase-hyphenated slug.
    
    Strips non-alphanumeric, collapses hyphens, truncates.
    """
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    return slug
```

### Pattern 5: Task Status Tracking
**What:** Task status stored as a simple marker file or YAML in a status file within the task directory. Since tasks are directory-based (not state-file-based), status needs a lightweight storage mechanism.
**When to use:** `task new`, `task list`, `task complete`.
**Recommendation:** Use a small `status.yaml` file in each task directory containing `status: open` or `status: complete`, plus the description. This keeps status alongside the task work product (SUMMARY.md) and is hand-editable (WS-06 spirit). Alternative: embed status in SUMMARY.md frontmatter. The `status.yaml` approach is cleaner because SUMMARY.md is the analyst's work product and should not have CLI-managed frontmatter.
```python
# status.yaml in each task directory
# .diligence/workstreams/financial/tasks/001-revenue-quality/status.yaml
description: "Verify revenue quality metrics from CIM"
status: open
created: "2026-04-08"
```

### Pattern 6: Aligned Column Output
**What:** Fixed-width columns with summary line at bottom.
**When to use:** All list commands (workstream list, task list, questions list).
**Example:**
```python
# Source: existing pattern from truth_cmd.py truth_list
id_w = 6
desc_w = 40
status_w = 10

for task in tasks:
    desc = task.description
    if len(desc) > desc_w:
        desc = desc[:desc_w - 3] + "..."
    click.echo(f"{task.id:<{id_w}} {desc:<{desc_w}} {task.status:<{status_w}}")

click.echo(f"\n{total} tasks: {n_complete} complete, {n_open} open")
```

### Anti-Patterns to Avoid
- **Shared utility extraction:** Do NOT extract `_find_diligence_dir` into a shared helper. The codebase explicitly replicates it per module for readability and local reasoning (Phase 1 decision).
- **Interactive prompts in commands:** XC-07 prohibits interactive prompts except in `init`. `task complete` validates SUMMARY.md silently, exits non-zero if empty.
- **Counter files:** Do NOT use counter files for ID generation. Always scan existing state (self-healing pattern from source ID and question ID generation).
- **Complex status machines:** Tasks have exactly two states (open, complete). No FSM, no transitions table, no blocked/deferred states.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML serialization | Custom YAML emitter | PyYAML safe_dump with manual quoting for strings | Edge cases in YAML spec (colons, special chars in values) |
| Atomic file writes | Custom temp file + rename | `atomic_write` from helpers/io.py | OneDrive retry, fsync, fd ownership tracking already handled |
| CLI argument parsing | Manual argparse | Click decorators (@click.group, @click.command, @click.argument, @click.option) | Established pattern, LazyGroup integration |
| Template rendering | f-strings in code | string.Template via templates/__init__.py render_template | Consistent with all existing template files |
| Test CLI invocation | subprocess calls | click.testing.CliRunner with env={"DILIGENT_CWD": ...} | Established test pattern, in-process, deterministic |

**Key insight:** This phase introduces zero new external dependencies. Every building block already exists in the codebase. The work is composition and extension, not invention.

## Common Pitfalls

### Pitfall 1: WorkstreamEntry Backward Compatibility
**What goes wrong:** Adding `description` and `created` fields to WorkstreamEntry breaks reading of existing WORKSTREAMS.md files that lack these fields.
**Why it happens:** Existing WORKSTREAMS.md written by Phase 1 init only has `name` and `status` in YAML blocks.
**How to avoid:** Use defaults in `read_workstreams`: `description=data.get("description", "")` and `created=data.get("created", "")`. Write new fields only when populated. Existing files read cleanly with empty defaults.
**Warning signs:** Tests using Phase 1 fixtures fail on missing field errors.

### Pitfall 2: QuestionEntry Backward Compatibility
**What goes wrong:** Adding `answer`, `answer_source`, `date_answered` fields breaks reading of existing QUESTIONS.md entries.
**Why it happens:** Gate-rejected questions written by truth_cmd.py in Phase 2 do not have answer fields.
**How to avoid:** All new fields are Optional with None defaults. Reader uses `.get()` with None fallback. Writer only emits answer fields when not None.
**Warning signs:** test_verification_gate.py or test_truth_cmd.py tests fail after model changes.

### Pitfall 3: Task Directory Path on Windows/OneDrive
**What goes wrong:** Path separators, case sensitivity, or OneDrive sync locks when creating task directories.
**Why it happens:** Windows uses backslashes; OneDrive may lock newly created directories briefly.
**How to avoid:** Use pathlib consistently (never string concatenation for paths). Use `Path.mkdir(parents=True, exist_ok=True)` for directory creation. Template files written via `atomic_write` already handle OneDrive retry.
**Warning signs:** PermissionError on fresh directory creation during tests.

### Pitfall 4: Workstream Name Validation
**What goes wrong:** Workstream names with spaces, special characters, or uppercase create broken directory names.
**Why it happens:** Workstream name is used as both a display name (WORKSTREAMS.md) and a directory name (.diligence/workstreams/<name>/).
**How to avoid:** Validate workstream names: lowercase alphanumeric plus hyphens only. Reject names that would create invalid directory paths. This matches the existing 6 template names (all lowercase, no special chars).
**Warning signs:** `workstream new "Revenue Quality"` creates a directory with a space that breaks path parsing.

### Pitfall 5: _next_question_id Duplication
**What goes wrong:** Question ID generation logic exists in truth_cmd.py (_next_question_id). The new `ask` command also needs it. Duplicating it creates drift risk.
**Why it happens:** Per-module replication pattern means the function gets copied.
**How to avoid:** This is acceptable per project convention. Copy the function into question_cmd.py. It is 12 lines and unlikely to change. The alternative (extracting to a shared module) violates the established "replicate per module" decision.
**Warning signs:** Question IDs collide or skip numbers when gate and manual questions interleave.

### Pitfall 6: Init Command Extension Scope
**What goes wrong:** Modifying init_cmd.py to create workstream subdirectories introduces regressions in existing init tests.
**Why it happens:** Init is the most complex command with interactive/non-interactive modes and 8 file writes.
**How to avoid:** Add subdirectory creation AFTER the existing file writes succeed. If subdirectory creation fails, the deal folder still has valid state files. Test the extension in isolation using `--non-interactive --workstreams financial,legal`.
**Warning signs:** test_init.py failures on unrelated assertions.

### Pitfall 7: Task Complete Status Persistence
**What goes wrong:** Marking a task complete without a clear persistence mechanism means the status is lost on next read.
**Why it happens:** Tasks are directory-based, not state-file-based. There is no TASKS.md to write to.
**How to avoid:** Use status.yaml per task directory as the status store. `task complete` reads status.yaml, validates SUMMARY.md is non-empty, writes updated status. `task list` scans directories and reads each status.yaml.
**Warning signs:** Task shows as "complete" immediately after completion but reverts to "open" on next `task list`.

## Code Examples

### WorkstreamEntry Model Extension
```python
# Source: existing models.py pattern
@dataclass
class WorkstreamEntry:
    """A single workstream entry."""
    name: str
    status: str  # active, complete, on-hold
    description: str = ""
    created: str = ""  # ISO 8601
```

### QuestionEntry Model Extension
```python
# Source: existing models.py pattern
@dataclass
class QuestionEntry:
    """A single question entry in QUESTIONS.md."""
    id: str
    question: str
    workstream: str
    owner: str  # self, principal, seller, broker, counsel
    status: str  # open, answered
    date_raised: str  # ISO 8601
    context: Optional[dict] = None
    answer: Optional[str] = None
    answer_source: Optional[str] = None
    date_answered: Optional[str] = None
```

### Updated write_workstreams for New Fields
```python
# Source: existing workstreams.py write pattern
for entry in ws.workstreams:
    lines.append(f"## {entry.name}")
    lines.append("```yaml")
    data = {"name": entry.name, "status": entry.status}
    if entry.description:
        data["description"] = entry.description
    if entry.created:
        data["created"] = entry.created
    lines.append(
        yaml.safe_dump(data, default_flow_style=False, allow_unicode=True).rstrip()
    )
    lines.append("```")
    lines.append("")
```

### Updated _format_question_yaml for Answer Fields
```python
# Source: existing questions.py _format_question_yaml pattern
def _format_question_yaml(entry: QuestionEntry) -> str:
    lines = []
    escaped_q = entry.question.replace("\\", "\\\\").replace('"', '\\"')
    lines.append(f'question: "{escaped_q}"')
    lines.append(f"workstream: {entry.workstream}")
    lines.append(f"owner: {entry.owner}")
    lines.append(f"status: {entry.status}")
    lines.append(f'date_raised: "{entry.date_raised}"')

    if entry.answer is not None:
        escaped_a = entry.answer.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'answer: "{escaped_a}"')
    if entry.answer_source is not None:
        lines.append(f"answer_source: {entry.answer_source}")
    if entry.date_answered is not None:
        lines.append(f'date_answered: "{entry.date_answered}"')

    if entry.context is not None:
        context_yaml = yaml.safe_dump(
            {"context": entry.context}, default_flow_style=False
        ).strip()
        lines.append(context_yaml)

    return "\n".join(lines)
```

### CLI Test Pattern for New Commands
```python
# Source: existing test_truth_cmd.py pattern
@pytest.fixture
def deal_dir(tmp_path):
    diligence = tmp_path / ".diligence"
    diligence.mkdir()
    # config.json
    config = {
        "schema_version": 1,
        "deal_code": "TEST",
        "created": "2026-01-01T00:00:00Z",
        "anchor_tolerance_pct": 0.5,
        "recent_window_days": 7,
        "workstreams": ["financial", "legal"],
    }
    (diligence / "config.json").write_text(
        json.dumps(config, indent=2), encoding="utf-8"
    )
    # WORKSTREAMS.md
    ws_content = """# Workstreams

## financial
```yaml
name: financial
status: active
```

## legal
```yaml
name: legal
status: active
```
"""
    (diligence / "WORKSTREAMS.md").write_text(ws_content, encoding="utf-8")
    # QUESTIONS.md
    (diligence / "QUESTIONS.md").write_text("# Questions\n", encoding="utf-8")
    # TRUTH.md
    (diligence / "TRUTH.md").write_text("# Truth\n", encoding="utf-8")
    # ARTIFACTS.md
    (diligence / "ARTIFACTS.md").write_text("# Artifacts\n", encoding="utf-8")
    # SOURCES.md
    (diligence / "SOURCES.md").write_text("# Sources\n", encoding="utf-8")
    return tmp_path


def test_workstream_new(deal_dir, runner):
    result = runner.invoke(
        workstream_cmd,
        ["new", "custom-ws"],
        catch_exceptions=False,
        env={"DILIGENT_CWD": str(deal_dir)},
    )
    assert result.exit_code == 0
    ws_dir = deal_dir / ".diligence" / "workstreams" / "custom-ws"
    assert ws_dir.is_dir()
    assert (ws_dir / "CONTEXT.md").exists()
    assert (ws_dir / "RESEARCH.md").exists()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| WorkstreamEntry: name + status only | WorkstreamEntry: name + status + description + created | Phase 4 | Reader must handle missing fields with defaults |
| QuestionEntry: no answer fields | QuestionEntry: answer + answer_source + date_answered | Phase 4 | Writer must conditionally emit answer fields |
| Questions only from gate rejection | Questions from gate + manual `ask` command | Phase 4 | Origin derived from context field presence |
| Workstreams as tags only | Workstreams as directories with content files | Phase 4 | First filesystem-directory-backed entity type |

**Deprecated/outdated:**
- Nothing deprecated. All Phase 1-3 patterns remain current.

## Open Questions

1. **Task status file format**
   - What we know: Tasks are directory-based. Status needs persistent storage. SUMMARY.md is the analyst's work product.
   - What's unclear: Whether to use status.yaml or a simpler marker (e.g., a `.complete` sentinel file).
   - Recommendation: Use `status.yaml` with description, status, and created fields. It is human-readable, hand-editable (consistent with WS-06 spirit), and extensible. A sentinel file would require reading the description from elsewhere.

2. **Workstream list: show description column?**
   - What we know: Context says "one line per workstream: name, status, task count, question count."
   - What's unclear: Claude's discretion item asks whether to show description or just name.
   - Recommendation: Show name only in list (keeps lines shorter). Description shown in `workstream show`. Consistent with how `task list` shows ID and description but not full content.

3. **Ask/answer as top-level commands vs subgroup**
   - What we know: Context specifies `diligent ask`, `diligent answer`, `diligent questions list`.
   - What's unclear: Whether `ask` and `answer` should be top-level LazyGroup commands or subcommands of a `questions` group.
   - Recommendation: Register `ask` and `answer` as top-level commands (matching `ingest` and `reconcile` patterns). Register `questions` as a group with `list` subcommand. This matches the UX specified in CONTEXT.md and the established pattern of top-level shortcuts for frequently-used commands.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >= 8.0 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run command | `cd Diligent && python -m pytest tests/ -x -q` |
| Full suite command | `cd Diligent && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| WS-01 | workstream new creates subdir + files | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamNew -x` | Wave 0 |
| WS-02 | workstream list shows name, status, counts | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamList -x` | Wave 0 |
| WS-03 | workstream show aggregates cross-file stats | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamShow -x` | Wave 0 |
| WS-04 | 6 pre-defined templates with tailored CONTEXT.md | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamTemplates -x` | Wave 0 |
| WS-05 | init creates workstream subdirs for selected types | unit | `pytest tests/test_init.py::TestInitWorkstreamDirs -x` | Wave 0 |
| WS-06 | hand-edits to WORKSTREAMS.md picked up | unit | `pytest tests/test_workstream_cmd.py::TestHandEdits -x` | Wave 0 |
| TASK-01 | task new creates numbered dir with SUMMARY.md | unit | `pytest tests/test_task_cmd.py::TestTaskNew -x` | Wave 0 |
| TASK-02 | task list shows tasks with status | unit | `pytest tests/test_task_cmd.py::TestTaskList -x` | Wave 0 |
| TASK-03 | task complete validates SUMMARY.md non-empty | unit | `pytest tests/test_task_cmd.py::TestTaskComplete -x` | Wave 0 |
| Q-01 | ask adds open question with flags | unit | `pytest tests/test_question_cmd.py::TestAsk -x` | Wave 0 |
| Q-02 | owner taxonomy validation | unit | `pytest tests/test_question_cmd.py::TestOwnerValidation -x` | Wave 0 |
| Q-03 | answer closes question with optional source | unit | `pytest tests/test_question_cmd.py::TestAnswer -x` | Wave 0 |
| Q-04 | questions list with --owner filter | unit | `pytest tests/test_question_cmd.py::TestQuestionsList -x` | Wave 0 |
| Q-05 | gate-rejected questions appear with [gate] tag | unit | `pytest tests/test_question_cmd.py::TestGateOrigin -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `cd Diligent && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd Diligent && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_workstream_cmd.py` -- covers WS-01 through WS-06
- [ ] `tests/test_task_cmd.py` -- covers TASK-01 through TASK-03
- [ ] `tests/test_question_cmd.py` -- covers Q-01 through Q-05
- [ ] Verify existing tests still pass after WorkstreamEntry and QuestionEntry model changes (backward compat)

## Sources

### Primary (HIGH confidence)
- Codebase inspection: models.py, workstreams.py, questions.py, cli.py, truth_cmd.py, artifact_cmd.py, init_cmd.py, doctor.py
- Codebase inspection: templates/__init__.py, conftest.py, test_truth_cmd.py, test_questions_state.py
- pyproject.toml: dependency versions, pytest config, build system

### Secondary (MEDIUM confidence)
- None needed. All patterns are derived from existing codebase.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies, all patterns established in Phases 1-3
- Architecture: HIGH - direct extension of existing command/model/state patterns
- Pitfalls: HIGH - backward compatibility concerns are concrete and verifiable from existing code

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable codebase, no external dependency changes expected)
