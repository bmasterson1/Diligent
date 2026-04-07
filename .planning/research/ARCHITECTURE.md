# Architecture Patterns

**Domain:** Local-filesystem Python CLI state-management tool
**Project:** diligent
**Researched:** 2026-04-07

## Recommended Architecture

diligent follows a **layered architecture with a state-file abstraction boundary**. The key insight: the CLI layer must never touch raw files directly. Every file read/write goes through a state layer that owns parsing, validation, and atomic writes. This is the same pattern used by tools like poetry, pipenv, and pre-commit -- CLI commands are thin dispatchers; the real logic lives in a domain layer that operates on typed data models.

```
+------------------+
|   CLI (click)    |  Thin command definitions, argument parsing, output formatting
+--------+---------+
         |
+--------v---------+
|  Command Logic   |  Business rules: reconcile, ingest, trace, flag
+--------+---------+
         |
+--------v---------+
|   State Layer    |  Read/write state files through typed models
+--+-----+-----+--+
   |     |     |
   v     v     v
 DEAL  TRUTH  SOURCES  WORKSTREAMS  STATE  config.json
 .md   .md    .md      .md          .md
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **CLI entry point** (`cli/`) | Argument parsing, option validation, output formatting (plain text, rich). Knows nothing about file formats. | Command Logic |
| **Command Logic** (`commands/`) | Orchestrates business operations. One module per command group (truth, sources, artifacts, reconcile, etc.). | State Layer, Helpers |
| **State Layer** (`state/`) | Owns the `.diligence/` directory. Parses markdown/JSON into typed dataclasses. Writes back via atomic ops. Validates schema on read. | Filesystem only |
| **Models** (`models/`) | Pure dataclasses/TypedDicts representing the in-memory shape of each state file. No I/O, no side effects. | Nothing (data containers) |
| **Helpers** (`helpers/`) | Standalone scripts: fact_parser, reconcile_anchors, diff_excel_versions, extract_text, artifact_scanner. Each is a pure function library. | Models (input/output), filesystem (read-only for source docs) |
| **Skill Templates** (`skills/`) | Static markdown files for Antigravity/Claude Code. Installed by `diligent install`. | Filesystem (write to IDE config dirs) |

### Why These Boundaries

1. **State Layer as the chokepoint** -- Every file mutation goes through one place. Atomic writes, validation, and format changes are isolated. When TRUTH.md format evolves, only `state/truth.py` changes.

2. **Models separate from I/O** -- Dataclasses are testable without touching disk. Commands operate on models, not raw strings. This prevents the "parse markdown in 15 different places" problem.

3. **Helpers are libraries, not scripts** -- Each helper exposes functions that accept and return typed data. The CLI calls them through command logic; they never import from CLI or State. This makes them independently testable and reusable.

## Data Flow

### Read Path (e.g., `diligent truth list`)

```
1. CLI parses args              cli/truth.py
2. Command finds .diligence/    commands/truth.py  (walks up from cwd)
3. State reads TRUTH.md         state/truth.py     (parse markdown -> TruthEntry[])
4. Command filters/formats      commands/truth.py  (apply any --flag filters)
5. CLI renders output           cli/truth.py       (table, plain text, or JSON)
```

### Write Path (e.g., `diligent truth set`)

```
1. CLI parses args + value      cli/truth.py
2. Command validates business   commands/truth.py  (citation required, etc.)
3. State reads current file     state/truth.py     (load existing entries)
4. Command builds new model     commands/truth.py  (append-only: old value -> supersedes)
5. State writes atomically      state/truth.py     (temp file -> fsync -> rename)
```

### Reconcile Path (most complex)

```
1. CLI invokes reconcile        cli/reconcile.py
2. Command loads TRUTH.md       state/truth.py     (all facts with timestamps)
3. Command loads SOURCES.md     state/sources.py   (all sources with timestamps)
4. Command loads STATE.md       state/state.py     (all artifacts with deps)
5. Helper walks dep graph       helpers/reconcile_anchors.py
6. Helper compares timestamps   helpers/reconcile_anchors.py
7. Command produces report      commands/reconcile.py  (stale artifacts list)
8. CLI renders report           cli/reconcile.py
```

### Key Data Flow Rules

- **Data flows down only.** CLI -> Commands -> State/Helpers. Never upward.
- **State layer never imports from commands or CLI.** It is a library.
- **Helpers never import from state.** They receive typed data as arguments.
- **Models are imported by everyone** but import nothing from the project.

## Suggested Package Layout

```
src/diligent/
    __init__.py
    __main__.py              # python -m diligent
    cli/
        __init__.py          # click group, entry point
        init.py              # diligent init
        truth.py             # diligent truth set/get/list/trace/flag
        sources.py           # diligent ingest, sources list/show/diff
        artifacts.py         # diligent artifact register/list/refresh
        reconcile.py         # diligent reconcile
        workstreams.py       # diligent workstream/task commands
        questions.py         # diligent ask/answer/questions
        status.py            # diligent status
        handoff.py           # diligent handoff
        doctor.py            # diligent doctor
        install.py           # diligent install
    commands/
        __init__.py
        init.py
        truth.py
        sources.py
        artifacts.py
        reconcile.py
        workstreams.py
        questions.py
        status.py
        handoff.py
        doctor.py
        install.py
    state/
        __init__.py
        workspace.py         # Find .diligence/, workspace root discovery
        deal.py              # DEAL.md reader/writer
        truth.py             # TRUTH.md reader/writer (append-only semantics)
        sources.py           # SOURCES.md reader/writer
        workstreams.py       # WORKSTREAMS.md reader/writer
        state_file.py        # STATE.md reader/writer (artifact registry)
        config.py            # config.json reader/writer
        atomic.py            # Atomic write utility (temp -> fsync -> rename)
    models/
        __init__.py
        deal.py              # DealInfo dataclass
        truth.py             # TruthEntry, SupersedesChain dataclasses
        source.py            # SourceDocument dataclass
        workstream.py        # Workstream, Task dataclasses
        artifact.py          # Artifact, Dependency dataclasses
        question.py          # Question dataclass
    helpers/
        __init__.py
        fact_parser.py
        reconcile_anchors.py
        diff_excel.py
        extract_text.py
        artifact_scanner.py
    skills/
        antigravity/
            SKILL.md
        claude_code/
            SKILL.md
```

## Patterns to Follow

### Pattern 1: Workspace Discovery (Walk-Up Search)

**What:** Find `.diligence/` by walking up from cwd toward filesystem root, like how git finds `.git/`.
**When:** Every command except `init` and `install`.
**Why:** User can run commands from any subdirectory of the deal folder.

```python
# state/workspace.py
from pathlib import Path

class WorkspaceNotFoundError(Exception):
    pass

def find_workspace(start: Path | None = None) -> Path:
    """Walk up from start (default: cwd) to find .diligence/ directory."""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        candidate = parent / ".diligence"
        if candidate.is_dir():
            return candidate
    raise WorkspaceNotFoundError(
        "Not inside a diligent workspace. Run 'diligent init' first."
    )
```

### Pattern 2: Atomic File Writes

**What:** Write to temp file in same directory, fsync, then atomic rename.
**When:** Every state file mutation.
**Why:** Crash during write must never corrupt state. OneDrive sync can interrupt at any point.

```python
# state/atomic.py
import os
import tempfile
from pathlib import Path

def atomic_write(path: Path, content: str) -> None:
    """Write content to path atomically."""
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)  # atomic on POSIX; near-atomic on Windows NTFS
    except:
        os.unlink(tmp)
        raise
```

### Pattern 3: State File as Parse-Serialize Pair

**What:** Each state module exposes `read(path) -> Model` and `write(path, model) -> None`. The markdown format is an implementation detail hidden behind these functions.
**When:** Always. No other code touches raw markdown.
**Why:** Format changes are isolated. Round-trip fidelity is testable per-file.

```python
# state/truth.py
from pathlib import Path
from diligent.models.truth import TruthEntry
from diligent.state.atomic import atomic_write

def read(path: Path) -> list[TruthEntry]:
    """Parse TRUTH.md into structured entries."""
    ...

def write(path: Path, entries: list[TruthEntry]) -> None:
    """Serialize entries back to TRUTH.md format, atomically."""
    content = _serialize(entries)
    atomic_write(path, content)
```

### Pattern 4: Click Group with Lazy Loading

**What:** Use click's group/command pattern with one file per command group. Use lazy loading so `diligent --help` does not import openpyxl.
**When:** CLI entry point.
**Why:** Startup time matters (< 2s requirement). Heavy imports (openpyxl, pdfplumber) should only load when needed.

```python
# cli/__init__.py
import click

class LazyGroup(click.Group):
    """Lazily load subcommands to keep startup fast."""
    ...

@click.group(cls=LazyGroup)
def cli():
    """diligent: structured due diligence state management."""
    pass
```

### Pattern 5: Command Logic Returns Data, CLI Formats It

**What:** Command functions return typed results (lists, dataclasses, status objects). CLI layer decides formatting (plain text, table, JSON).
**When:** Every command.
**Why:** Testability. Commands are tested without capturing stdout. Future output formats (JSON for scripting) are trivial to add.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Regex-Heavy Markdown Parsing

**What:** Using ad-hoc regexes scattered across files to parse markdown sections.
**Why bad:** Fragile, hard to test, breaks on edge cases (code blocks containing `##`, etc.). Different commands parse the same file with slightly different regexes that drift apart.
**Instead:** Build a small section-based markdown parser in the state layer. Each file type has one parser that understands its specific section structure. Use a line-by-line state machine, not regex.

### Anti-Pattern 2: CLI Commands That Do Everything

**What:** Putting business logic directly in click command functions.
**Why bad:** Untestable without invoking CLI. Business rules become coupled to argument parsing. Impossible to reuse logic across commands (e.g., reconcile needs truth-reading logic that also appears in `truth list`).
**Instead:** CLI functions are 5-15 lines: parse args, call command logic, format output. All business logic lives in `commands/`.

### Anti-Pattern 3: Global State or Singletons for Workspace

**What:** A global `WORKSPACE` variable set at import time or via module-level initialization.
**Why bad:** Breaks testing (cannot test multiple workspaces). Race conditions if ever parallelized. Import order dependencies.
**Instead:** `find_workspace()` returns a `Path`. Pass it explicitly through the call chain. Use click's context object (`@click.pass_context`) to thread the workspace path.

### Anti-Pattern 4: Storing Computed State in Files

**What:** Writing reconciliation results or derived data back into state files.
**Why bad:** Stale computed state is worse than recomputing. Creates cache invalidation problems in a system designed to detect staleness.
**Instead:** Compute on read. The only persisted state is source-of-truth data entered by the analyst. Reconciliation results are always computed fresh.

## Build Order (Dependencies Between Components)

The architecture has clear dependency layers. Build bottom-up:

```
Phase 1: Foundation
    models/          (zero dependencies, pure dataclasses)
    state/atomic.py  (zero dependencies, utility)
    state/workspace.py (zero dependencies, path walking)

Phase 2: State Layer
    state/deal.py, state/truth.py, state/sources.py, etc.
    (depends on: models, atomic)
    -- Each state module is independent of the others --

Phase 3: Command Logic
    commands/init.py    (depends on: state layer)
    commands/truth.py   (depends on: state/truth)
    commands/sources.py (depends on: state/sources)
    -- Each command module depends on its state modules --

Phase 4: CLI Wiring
    cli/__init__.py     (depends on: commands)
    cli/truth.py, etc.  (thin wrappers around commands)

Phase 5: Cross-Cutting Commands
    commands/reconcile.py  (depends on: state/truth, state/sources, state/state_file, helpers)
    commands/status.py     (depends on: all state modules)
    commands/doctor.py     (depends on: all state modules for validation)
    commands/handoff.py    (depends on: all state modules)

Phase 6: Helpers
    helpers/fact_parser.py         (can build anytime after models)
    helpers/reconcile_anchors.py   (after models, before reconcile command)
    helpers/diff_excel.py          (independent, needs openpyxl)
    helpers/extract_text.py        (independent, needs pypdf/python-docx)
    helpers/artifact_scanner.py    (after models)

Phase 7: Skill Files
    skills/   (static files, no code deps, but needs working CLI to be useful)
```

**Critical path:** Models -> State Layer -> Commands -> CLI. Everything else can parallelize around this spine.

**The most important ordering constraint:** State readers/writers for TRUTH.md and SOURCES.md must be rock-solid before building reconcile. Reconcile is the highest-value feature but depends on correct parsing of every upstream file.

## Scalability Considerations

| Concern | Typical deal (50 files) | Large deal (500 files) | Edge case (2000+ files) |
|---------|------------------------|------------------------|------------------------|
| State file size | TRUTH.md < 100 entries, instant parse | TRUTH.md ~1000 entries, still instant | Consider streaming parser if > 5000 entries |
| Reconcile time | < 1s | < 5s | May need caching of parsed state across command invocation |
| Source doc scanning | Trivial | openpyxl/pdfplumber load time dominates | Parallelize with concurrent.futures if needed |
| Startup time | < 200ms with lazy loading | Same | Same (startup is CLI + workspace discovery, not data-dependent) |

For the target use case (single analyst, one deal at a time, < 500 source documents), the architecture handles everything without optimization. The atomic write pattern adds ~1ms overhead per write. Markdown parsing of a 1000-entry TRUTH.md will take < 50ms in Python.

## Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| **click over typer** | click has no pydantic dependency, more mature, explicit over magic. Typer adds overhead for type inference that is unnecessary when commands are hand-written. |
| **src layout** (`src/diligent/`) | Prevents accidental imports from project root. Standard for PyPI packages. |
| **Dataclasses over Pydantic for models** | Zero external dependency for core models. Validation happens in the state layer during parse, not in the model constructors. Keeps models fast and simple. |
| **No plugin system** | 15 commands is manageable without dynamic dispatch. A plugin system adds complexity that is not justified for a single-developer tool. |
| **Explicit path threading over DI framework** | Pass `workspace_path` via click context. No dependency injection container needed for a tool this size. |

## Sources

- Architecture patterns drawn from established Python CLI tools: poetry (layered architecture, models separate from I/O), pre-commit (workspace discovery walk-up), pip (lazy command loading), black (atomic file writes).
- Python Packaging Authority recommendations for src layout.
- click documentation for group/command patterns.
- Confidence: HIGH for all patterns. These are well-established conventions in the Python CLI ecosystem with years of production use.
