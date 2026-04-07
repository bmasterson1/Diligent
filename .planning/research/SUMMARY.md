# Project Research Summary

**Project:** Diligent - CLI state-management for acquisition due diligence
**Domain:** Local-filesystem Python CLI tool, markdown-as-database, AI-native workflow
**Researched:** 2026-04-07
**Confidence:** MEDIUM-HIGH (training data; web verification unavailable)

## Executive Summary

Diligent is a single-analyst CLI tool that replaces the Excel-tracker approach to M&A due diligence. The core value proposition is a provenance-linked truth store (TRUTH.md) with a dependency graph connecting source documents to validated facts to analyst deliverables, enabling automated staleness detection that no existing DD platform (DealRoom, Midaxo, Ansarada) provides. State files are plain markdown, machine-readable without translation, committed to git for a full audit trail.

The recommended approach is a layered Python CLI built with Click 8.1+, using PyYAML for state file I/O, openpyxl/python-docx/pdfplumber for document ingestion, and hatchling for packaging. The critical architectural decision is a strict state-file abstraction boundary: no command touches raw files directly; all reads and writes route through a typed state layer that owns parsing, validation, and atomic writes. This pattern (used by poetry and pre-commit) makes the system testable and keeps format-change blast radius to a single module per file type.

The dominant risks are Windows/OneDrive-specific and must be addressed in Phase 1: (1) os.replace() can fail when OneDrive sync agent holds a file handle; (2) YAML implicit type coercion silently corrupts financial figures; (3) fenced-block YAML parsing must use a state machine not regex. These are well-documented failures in this exact scenario.

## Key Findings

### Recommended Stack

The stack is lean: 5 core runtime dependencies, all mature and well-established. Click is preferred over Typer (which wraps Click and adds unnecessary abstraction). pdfplumber is chosen over pypdf for .extract_tables() capability, and over PyMuPDF because MuPDF GPL license conflicts with BSL 1.1. The build toolchain: hatchling + hatch + ruff (replaces flake8/black/isort) + mypy --strict. rich is optional so the core footprint stays minimal.

**Core technologies:**
- **Python >=3.11**: tomllib in stdlib, significant perf gains, better error messages
- **Click >=8.1**: Explicit command groups for 15 commands across 6 groups, no magic over Typer
- **PyYAML >=6.0.1**: YAML front-matter parsing via safe_load() only; never yaml.load()
- **openpyxl >=3.1.2**: Excel ingestion with read_only=True for memory-efficient streaming
- **python-docx >=1.1.0**: Word document text/table extraction for LOIs and agreements
- **pdfplumber >=0.11.0**: PDF text and table extraction; MIT license; no system dependencies
- **hatchling >=1.21**: PEP 621-native build backend; cleaner than setuptools for new projects
- **ruff >=0.4**: Replaces flake8 + black + isort in a single fast tool
- **mypy >=1.10**: Strict typing from day one; state file schemas benefit directly

All version numbers are from training data (May 2025 cutoff). Verify with pip index versions before locking pyproject.toml.

### Expected Features

The MVP priority order is unambiguous: init -> sources -> truth -> artifacts -> reconcile -> status -> handoff. Reconciliation is the killer feature but cannot ship until the three upstream registries are solid.

**Must have (table stakes):**
- diligent init -- zero-to-working in one command; all state files scaffolded
- Source document registry with supersedes chains -- v2-replaces-v1 logic is the key differentiator
- Fact storage with provenance (TRUTH.md) -- every validated number cites source, page, date; append-only with supersedes history
- Artifact tracking -- register deliverables and their fact dependencies
- Staleness detection / reconcile -- dependency graph walk (source -> fact -> artifact) that no existing DD tool provides
- diligent status -- one command, full deal state, under 2 seconds
- Session handoff -- structured prompt for AI context restore; critical for AI-native workflow
- diligent doctor -- validates all state files, detects corruption and OneDrive conflict copies
- Atomic file writes -- non-negotiable on Windows/OneDrive; trust prerequisite

**Should have (competitive differentiators):**
- Supersedes chains on facts -- full revision history; Excel trackers overwrite
- diligent sources diff -- shows what changed between v1 and v2 of a source document
- Structured reconcile output -- names the stale artifact, the upstream change, the days stale
- IDE skill file installation (diligent install --claude-code)
- Helper scripts (diff_excel_versions.py, fact_parser.py, extract_text.py)
- Git-diffable state -- stable sort order, consistent formatting

**Defer (v2+):**
- Workstream/task tracking -- add after core truth-tracking loop works
- Open questions tracking -- can be a markdown section initially
- diligent fmt -- canonical format normalization

**Explicit anti-features (do not build):** Web UI, built-in LLM integration, multi-user collaboration, database backend, document OCR, VDR/CRM integration, auto-commit, TUI, notification system, scoring/risk assessment.

### Architecture Approach

Diligent follows a layered architecture with a strict state-file abstraction boundary. CLI commands are thin dispatchers (5-15 lines); business logic lives in commands/; all file I/O routes through state/ that owns parsing, validation, and atomic writes; models/ contains pure dataclasses with no I/O; helpers/ are pure function libraries. Data flows strictly downward (CLI -> commands -> state/helpers).

**Major components:**
1. **CLI layer** (src/diligent/cli/) -- Click groups, argument parsing, output formatting; no file format knowledge
2. **Command logic** (src/diligent/commands/) -- One module per command group; testable without CLI
3. **State layer** (src/diligent/state/) -- Owns .diligence/ directory; parses markdown into typed dataclasses; atomic writes; schema validation on read
4. **Models** (src/diligent/models/) -- Pure dataclasses (TruthEntry, SourceDocument, Artifact); no I/O; imported by all layers
5. **Helpers** (src/diligent/helpers/) -- fact_parser, reconcile_anchors, diff_excel, extract_text, artifact_scanner; independently testable
6. **Skill templates** (src/diligent/skills/) -- Static SKILL.md files for Claude Code / Antigravity

**Key patterns:**
- Walk-up workspace discovery (find_workspace() walks up from cwd) -- same as git
- Atomic write: temp file in same dir -> fsync -> os.replace() with retry loop for Windows/OneDrive
- Parse-serialize pair per state file: read(path) -> Model and write(path, model) -> None
- Click LazyGroup for fast startup; heavy imports load only when command runs
- Command functions return typed data; CLI layer formats -- enables --json on every command

### Critical Pitfalls

1. **os.replace() fails on Windows when OneDrive holds a file handle** -- Wrap in retry loop with exponential backoff (3 attempts: 100ms/500ms/2s), catching PermissionError and OSError winerror 5/32. Leave .diligent-pending file on final failure.

2. **PyYAML implicit type coercion silently corrupts financial data** -- yes/no becomes bool, 2024-01-15 becomes datetime.date, 0123 becomes octal int 83. Store all fact values as quoted strings. Add schema validation on read. Run YAML torture test in CI.

3. **Fenced-block YAML parsing fails on edge cases with naive regex** -- Use a state-machine parser, not re.findall(). Normalize line endings before parsing. Add round-trip assertions on every write operation.

4. **Concurrent AI agent writes cause lost-update on TRUTH.md** -- Use filelock library (cross-platform) or sequence-number optimistic concurrency. AI agents in IDE tool-use loops fire rapid sequential commands. Phase 1 must establish locking before any write command is built.

5. **Supersedes chain references break if positional** -- Use UUID-based stable fact identifiers. Store supersedes chain within each fact YAML block, not as cross-file pointers. Design the identifier scheme in Phase 1 -- cannot be retrofitted.

6. **CLI output must be agent-hostile-free from day one** -- No interactive prompts; destructive operations require --force/--yes. Every data-returning command supports --json. Exit codes: 0=success, 1=user error, 2=system error.

## Implications for Roadmap

The architecture build order is the natural phase structure. The dependency graph is rigid: models and atomic I/O must exist before state readers/writers, which must exist before commands, which must exist before reconcile. There is no shortcut to the killer feature.

### Phase 1: Foundation -- File I/O, Models, CLI Scaffold, and Parser Correctness

**Rationale:** Everything else is built on top of these primitives. Getting atomic writes, YAML parsing, data models, and CLI output contract wrong in Phase 1 means rebuilding from zero. These failures have no safe retrofit path.

**Delivers:** Working diligent init, atomic write utility with OneDrive retry loop, workspace walk-up discovery, all dataclass models, TRUTH.md and SOURCES.md parse-serialize pairs with round-trip tests, CLI output contract. PyPI name resolution must happen before pyproject.toml is written.

**Addresses features:** Init/scaffold, atomic file writes, zero network/zero config

**Avoids pitfalls:** Atomic write failure on Windows/OneDrive (P1), YAML type coercion (P4), fenced-block parser fragility (P3), concurrent write lost-update (P5), supersedes chain corruption (P9), agent-hostile CLI output (P10), Windows path length issues (P7)

**Research flag:** Standard patterns -- no phase research needed.

---

### Phase 2: Core Truth Loop -- Sources, Facts, and Artifacts

**Rationale:** The three registries must be complete before reconciliation can be built. Once an analyst can record a validated fact citing a source and register an artifact that depends on it, they have replaced their Excel tracker.

**Delivers:** diligent ingest (source document ingestion with openpyxl/python-docx/pdfplumber), diligent sources list/show, diligent truth set/get/list/trace/flag with full supersedes chain logic, diligent artifact register/list, diligent doctor for state validation and OneDrive conflict copy detection.

**Addresses features:** Source document registry, fact storage with provenance, artifact tracking, data integrity validation

**Uses stack:** openpyxl read_only mode, python-docx, pdfplumber, PyYAML safe_load/safe_dump

**Implements architecture:** State layer readers/writers for all three core state files; fact_parser.py and extract_text.py helpers

**Avoids pitfalls:** Silent parse failures in Excel/Word/PDF (P6), OneDrive conflict copy detection (P2), human edit structural drift (P8)

**Research flag:** Standard patterns -- no deep research needed.

---

### Phase 3: Reconciliation, Status, and Handoff

**Rationale:** The dependency graph walk is the highest-value feature and depends on Phase 2 being solid. Status and handoff aggregate across all state files and require all state readers to be complete.

**Delivers:** diligent reconcile (dependency graph walk, structured staleness report), diligent status (deal dashboard under 2 seconds), diligent handoff (AI context restore prompt), diligent sources diff (document version comparison).

**Addresses features:** Staleness detection/reconciliation, full status/dashboard, session handoff, diff-based source comparison

**Implements architecture:** helpers/reconcile_anchors.py (timestamp comparison, graph walk), helpers/diff_excel.py, commands/reconcile.py (cross-cutting all state modules)

**Avoids pitfalls:** Computed state stored in files anti-pattern -- reconcile always recomputes fresh.

**Research flag:** Dependency graph walk semantics (partial staleness, chain traversal) warrants design review before implementation.

---

### Phase 4: Workstreams, Questions, Skill Files, and Distribution

**Rationale:** Lower-urgency features and distribution polish. Skill file installation has high perceived value but low complexity. Distribution finalizes the tool for external use.

**Delivers:** diligent workstream/task commands, diligent ask/answer/questions tracking, diligent install --claude-code (skill file installation), full CI pipeline, pipx install end-to-end test on clean Windows machine, PyPI publication.

**Addresses features:** Workstream and task tracking, open questions tracking, IDE skill file installation

**Avoids pitfalls:** pipx/Windows PATH edge cases (P12), PyPI name conflict (P11 -- must be pre-resolved before Phase 1)

**Research flag:** Verify uv tool install adoption trajectory before writing install docs. Standard patterns otherwise.

---

### Phase Ordering Rationale

- Foundation before everything: atomic write utility, file locking, and YAML parser correctness gate every phase. No retrofit path.
- State layer before commands: architecture explicit build order (models -> state -> commands -> CLI) drives phase structure.
- Sources before facts before artifacts before reconcile: feature dependency graph is unambiguous.
- Supplementary features last: workstreams and questions are not on the critical path.
- Distribution in Phase 4: dogfood on real deal work before optimizing distribution story.

### Research Flags

Phases needing deeper research during planning:
- **Phase 3 (Reconciliation):** Dependency graph walk semantics and partial staleness handling warrant design review before implementation.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** Atomic writes, Click scaffold, src layout, pytest -- all well-documented.
- **Phase 2 (Core Truth Loop):** Document parsing library behavior, YAML patterns, state machine parsers -- standard domain.
- **Phase 4 (Distribution):** hatchling packaging, pipx install flow -- standard Python packaging.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All libraries are mature and the established choices; versions from May 2025 training data -- verify before locking. |
| Features | MEDIUM-HIGH | Core feature set from PROJECT.md (HIGH). Competitor landscape from training data -- may be stale. |
| Architecture | HIGH | Patterns from established Python CLI tools (poetry, pre-commit, pip, black) with years of production use. |
| Pitfalls | HIGH | Critical pitfalls are well-documented, reproducible issues with known mitigations. Not theoretical. |

**Overall confidence:** HIGH for technical approach. MEDIUM for competitor landscape (web verification unavailable).

### Gaps to Address

- **PyPI name availability:** diligent may be taken on PyPI. Check pip index versions diligent before writing any code. This is pre-Phase 1.
- **OneDrive atomic write behavior:** Test on an actual OneDrive-synced folder during Phase 1, not just in CI.
- **Dependency version verification:** All version minimums are from training data. Run pip index versions for all dependencies before locking pyproject.toml.
- **Competitor feature verification:** DealRoom, Midaxo, Ansarada comparisons are from training data. Verify if competitive positioning matters.
- **TRUTH.md performance at scale:** Benchmark with synthetic data (100+ facts, multiple revisions) in Phase 2 before Phase 3 ships.

## Sources

### Primary (HIGH confidence)
- PROJECT.md -- project requirements, design constraints, explicit anti-features
- Python documentation: os.replace(), os.fsync(), pathlib, atomic write pattern
- Click documentation: group/command patterns, CliRunner for testing
- openpyxl documentation: read_only mode, merged cells handling
- pdfplumber GitHub: table extraction capability, pdfminer.six dependency
- Python Packaging Authority: src layout, hatchling, pyproject.toml PEP 621
- CommonMark specification: fenced code block edge cases
- PyYAML documentation: implicit type resolution (YAML 1.1 behavior)

### Secondary (MEDIUM confidence)
- GSD tool architecture as structural analog for layered CLI design
- Poetry, pre-commit, pip, black patterns for architecture decisions
- General M&A DD analyst workflow patterns from training data
- Microsoft OneDrive sync behavior and conflict copy documentation

### Tertiary (LOW confidence -- verify before acting)
- DealRoom, Midaxo, Datasite, Ansarada feature landscape (training data, may be stale)
- uv tool install adoption trajectory (training data, rapidly evolving ecosystem)

---
*Research completed: 2026-04-07*
*Ready for roadmap: yes*
