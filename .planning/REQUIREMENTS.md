# Requirements: diligent

**Defined:** 2026-04-07
**Core Value:** When the analyst types one command, they get a definitive answer about what is current truth and which deliverables need to be refreshed.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Initialization

- [ ] **INIT-01**: `diligent init` scaffolds `.diligence/` directory with all 6 core state files (DEAL.md, TRUTH.md, SOURCES.md, WORKSTREAMS.md, STATE.md, config.json) from templates
- [ ] **INIT-02**: State file readers/writers round-trip all 6 core files without data loss or format drift
- [ ] **INIT-03**: `diligent doctor` validates file integrity across all state files, detects corruption, reports issues with suggested fixes
- [ ] **INIT-04**: `diligent config get/set` reads and writes config.json values from CLI (low priority; cut first if Phase 1 runs long)
- [x] **INIT-05**: pyproject.toml scaffold with hatchling build backend, BSL 1.1 license header, package metadata
- [x] **INIT-06**: Atomic file writes (write to temp file, fsync, os.replace) for all state file mutations, with retry/backoff for OneDrive file locks
- [x] **INIT-07**: Schema version recorded in config.json; `diligent migrate` path for future schema changes
- [x] **INIT-08**: CLI startup under 200ms via lazy command loading (defer openpyxl/pdfplumber/python-docx imports until needed)

### Sources

- [ ] **SRC-01**: `diligent ingest <path>` logs a source document with date received, parties, workstream tags, and optional --supersedes pointer to a prior source ID
- [ ] **SRC-02**: Source IDs follow `{DEAL_CODE}-{NNN}` convention (zero-padded, monotonic, never reused)
- [ ] **SRC-03**: `diligent sources list` shows all registered sources with date and status
- [ ] **SRC-04**: `diligent sources show <source-id>` displays full record for a single source
- [ ] **SRC-05**: `diligent sources diff <id-a> <id-b>` diffs two source files using helper scripts
- [ ] **SRC-06**: diff_excel_versions.py helper reports which sheets, named ranges, and cells differ between two Excel files
- [ ] **SRC-07**: Ingest automatically invokes diff_excel_versions.py when the ingested file supersedes a known prior Excel source

### Truth

- [ ] **TRUTH-01**: `diligent truth set <key> <value> --source <source-id>` records a fact with citation; --source is required
- [ ] **TRUTH-02**: `truth set` updates an existing key: prior value pushed into supersedes chain with timestamp and new source on confirmation
- [ ] **TRUTH-03**: Tolerance config in config.json: exact match for non-anchor facts, configurable percentage for anchor metrics
- [ ] **TRUTH-04**: Verification gate: when `truth set` would change an existing value beyond tolerance, the command stops, surfaces the discrepancy (old value, new value, delta, both sources), and requires explicit confirmation before proceeding. On rejection, the proposed value is pushed to the open questions queue via `ask` with the discrepancy as context. This is the load-bearing behavior connecting truth management to the questions queue.
- [ ] **TRUTH-05**: `diligent truth get <key>` shows current value with source citation
- [ ] **TRUTH-06**: `diligent truth list` lists all facts; supports --workstream and --stale filters
- [ ] **TRUTH-07**: `diligent truth trace <key>` shows full supersedes history: every value, source, date, and the diff between source documents
- [ ] **TRUTH-08**: `diligent truth flag <key> --reason` marks a fact as needing review; flagged facts appear in status and truth list --stale
- [ ] **TRUTH-09**: TRUTH.md is append-only at the entry level: updates write a new value and push the prior value into supersedes chain, never overwrite
- [ ] **TRUTH-10**: fact_parser.py is the canonical TRUTH.md reader/writer; all CLI commands use it; round-trip fidelity is guaranteed
- [ ] **TRUTH-11**: All fact values stored as quoted strings in YAML to prevent PyYAML implicit type coercion (no silent retyping of financial data)
- [ ] **TRUTH-12**: Optional --computed-by and --notes flags on truth set for script references and uncertainty context

### Artifacts

- [ ] **ART-01**: `diligent artifact register <path> --references <key1,key2,...>` registers a deliverable with explicit fact dependencies
- [ ] **ART-02**: artifacts/manifest.json stores registered artifacts with fields for path, references, workstream, registration date, last refresh timestamp, and staleness status
- [ ] **ART-03**: `diligent artifact list` shows all registered artifacts; supports --stale filter
- [ ] **ART-04**: `diligent artifact refresh <path>` marks artifact as refreshed (updates last refresh timestamp)
- [ ] **ART-05**: `diligent reconcile` walks the dependency graph (source -> fact -> artifact), reports stale artifacts with structured output: which fact changed, when, from what source, how many days stale
- [ ] **ART-06**: `diligent reconcile --workstream <name>` scopes reconciliation to one workstream
- [ ] **ART-07**: `diligent reconcile --strict` exits non-zero on any staleness (for scripted checks)
- [ ] **ART-08**: reconcile_anchors.py is the deterministic engine behind `diligent reconcile`
- [ ] **ART-09**: artifact_scanner.py scans .docx files for embedded `{{truth:key}}` citation tags; opt-in via --scan flag on artifact register; .docx only in v1. Manual --references is the default and supported path. --scan is supplementary and experimental. Milestone 3 acceptance test runs against manual --references, not --scan.

### Workstreams

- [ ] **WS-01**: `diligent workstream new <name>` creates a workstream with subdirectory under .diligence/workstreams/ containing CONTEXT.md and RESEARCH.md
- [ ] **WS-02**: `diligent workstream list` shows all workstreams with status and task count
- [ ] **WS-03**: `diligent workstream show <name>` displays full workstream detail
- [ ] **WS-04**: Pre-defined workstream templates shipped as defaults: financial, retention/commercial, technical, legal, HR, integration (6 total)
- [ ] **WS-05**: Workstream customization at init time ("which workstreams do you want for this deal?")
- [ ] **WS-06**: CLI reads state from files on every invocation; hand-edits to WORKSTREAMS.md are picked up on next read (CLI is convenience, not gate)

### Tasks

- [ ] **TASK-01**: `diligent task new <workstream> <desc>` creates task directory with empty SUMMARY.md; PLAN.md and VERIFICATION.md scaffolded as templates but not enforced
- [ ] **TASK-02**: `diligent task list <workstream>` lists tasks with status
- [ ] **TASK-03**: `diligent task complete <ws> <task-id>` prompts for summary content and writes SUMMARY.md

### Questions

- [ ] **Q-01**: `diligent ask <text>` adds an open question with --workstream and --owner flags
- [ ] **Q-02**: Owner taxonomy: self, principal, seller, broker, counsel (from PRD 4.1.6)
- [ ] **Q-03**: `diligent answer <q-id> <text>` closes a question with optional --source citation
- [ ] **Q-04**: `diligent questions list` shows open questions; supports --owner filter
- [ ] **Q-05**: Unsourced claims rejected by truth set are automatically pushed to the questions queue

### State & Handoff

- [ ] **STATE-01**: `diligent status` provides full state summary: DEAL.md context, TRUTH.md counts and stale flags, recent ingests, workstream status, artifact counts, open questions
- [ ] **STATE-02**: Status output is plain text, sectioned, no color by default; --json flag for agent consumption; no emojis
- [ ] **STATE-03**: `diligent handoff` generates a single markdown document the analyst pastes into a fresh AI session
- [ ] **STATE-04**: Handoff reads DEAL.md (full), STATE.md (full), WORKSTREAMS.md (full), recent TRUTH.md/SOURCES.md entries, open questions, and recent task SUMMARY.md files
- [ ] **STATE-05**: "Recent" is configurable in config.json, defaults to everything touched in last 7 days plus everything flagged or stale
- [ ] **STATE-06**: Handoff output is a paste buffer, not a file-on-disk reference (portable across runtimes)

### Distribution

- [ ] **DIST-01**: Package published to PyPI, installable via `pipx install diligent` (name resolution required before first publish)
- [ ] **DIST-02**: `diligent install --antigravity` drops SKILL.md files into Antigravity's skills directory (verify install path before building)
- [ ] **DIST-03**: `diligent install --claude-code` drops SKILL.md files into Claude Code's skills directory
- [ ] **DIST-04**: `diligent install --uninstall` removes installed skill files cleanly
- [ ] **DIST-05**: SKILL.md files parameterized with absolute path to diligent CLI binary at install time
- [ ] **DIST-06**: One SKILL.md per CLI command, prefixed `dd:` in runtime command namespace

### Cross-Cutting

- [ ] **XC-01**: All commands return in under 2 seconds for typical deal folder (50-200 sources, 50-500 facts, 20-100 artifacts)
- [ ] **XC-02**: `diligent reconcile` completes in under 10 seconds for typical deal folder
- [x] **XC-03**: No network requests, no API keys, no telemetry, no phone-home during normal operation
- [ ] **XC-04**: Source documents are read-only from diligent's perspective; the tool never modifies files the analyst placed in the deal folder
- [x] **XC-05**: All state file writes validate the resulting file structure before committing; validation failure preserves prior state
- [ ] **XC-06**: --json output flag available on every command for AI agent consumption
- [ ] **XC-07**: No interactive prompts that would break AI agent tool-use loop; all input via CLI flags
- [x] **XC-08**: BSL 1.1 license with Additional Use Grant for individual use; commercial service-provider use requires separate license

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Document Helpers

- **DOC-01**: extract_text.py wrapper for document text extraction (PDF, DOCX, XLSX); deferred because AI runtimes already read these natively
- **DOC-02**: artifact_scanner.py expanded to .pptx and .xlsx formats (v1 is .docx only)

### Enhanced Ingestion

- **ING-01**: Glob pattern support for batch ingestion (`diligent ingest *.xlsx`)
- **ING-02**: Auto-suggest which TRUTH.md facts an ingested document might affect

### Git Integration

- **GIT-01**: Optional `diligent commit` wrapping `git commit` for state file changes
- **GIT-02**: Auto-commit on state file writes (opt-in)

### Additional Runtimes

- **RT-01**: Skill packages for Cursor, Windsurf, and other AI-IDE runtimes

### Schema & Migration

- **MIG-01**: `diligent migrate` command for upgrading deal folders across schema versions

### Analytics

- **AN-01**: Per-key or per-category tolerance overrides beyond the global anchor tolerance

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web UI or dashboard | IDE is the UI. Web layer adds server, auth, database, deployment pipeline. |
| Multi-user collaboration | Single analyst per deal folder. Multi-user forces relational model, sync, hosted backend. |
| Database backend (SQLite/DuckDB) | Destroys AI-readability. Agent cannot cat TRUTH.md if truth lives in a database. |
| Built-in LLM integration | Zero-credential, zero-cost, runtime-agnostic. AI is a consumer, not a component. |
| Document OCR / automated extraction | Scope explosion. Wrong extractions pollute TRUTH.md. Analyst + AI agent is the extraction engine. |
| VDR / CRM / accounting integration | Every deal uses different systems. Integration maintenance is unbounded. |
| TUI (interactive terminal UI) | Breaks AI agent tool-use loop. Adds curses/textual dependency. |
| Notification system / alerts | Implies polling, background processes, or daemon. Pull-based: analyst asks, tool answers. |
| Scoring or risk assessment | Subjective, deal-specific. Track facts and questions; let analyst synthesize risk. |
| Auto-commit / git orchestration | Git workflow is personal. Auto-commits create noise. |
| Template library for deliverables | Every deal is different. Templates become opinionated about deal structure. |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| INIT-01 | Phase 1 | Pending |
| INIT-02 | Phase 1 | Pending |
| INIT-03 | Phase 1 | Pending |
| INIT-04 | Phase 1 | Pending |
| INIT-05 | Phase 1 | Complete |
| INIT-06 | Phase 1 | Complete |
| INIT-07 | Phase 1 | Complete |
| INIT-08 | Phase 1 | Complete |
| SRC-01 | Phase 2 | Pending |
| SRC-02 | Phase 2 | Pending |
| SRC-03 | Phase 2 | Pending |
| SRC-04 | Phase 2 | Pending |
| SRC-05 | Phase 2 | Pending |
| SRC-06 | Phase 2 | Pending |
| SRC-07 | Phase 2 | Pending |
| TRUTH-01 | Phase 2 | Pending |
| TRUTH-02 | Phase 2 | Pending |
| TRUTH-03 | Phase 2 | Pending |
| TRUTH-04 | Phase 2 | Pending |
| TRUTH-05 | Phase 2 | Pending |
| TRUTH-06 | Phase 2 | Pending |
| TRUTH-07 | Phase 2 | Pending |
| TRUTH-08 | Phase 2 | Pending |
| TRUTH-09 | Phase 2 | Pending |
| TRUTH-10 | Phase 2 | Pending |
| TRUTH-11 | Phase 2 | Pending |
| TRUTH-12 | Phase 2 | Pending |
| ART-01 | Phase 3 | Pending |
| ART-02 | Phase 3 | Pending |
| ART-03 | Phase 3 | Pending |
| ART-04 | Phase 3 | Pending |
| ART-05 | Phase 3 | Pending |
| ART-06 | Phase 3 | Pending |
| ART-07 | Phase 3 | Pending |
| ART-08 | Phase 3 | Pending |
| ART-09 | Phase 3 | Pending |
| WS-01 | Phase 4 | Pending |
| WS-02 | Phase 4 | Pending |
| WS-03 | Phase 4 | Pending |
| WS-04 | Phase 4 | Pending |
| WS-05 | Phase 4 | Pending |
| WS-06 | Phase 4 | Pending |
| TASK-01 | Phase 4 | Pending |
| TASK-02 | Phase 4 | Pending |
| TASK-03 | Phase 4 | Pending |
| Q-01 | Phase 4 | Pending |
| Q-02 | Phase 4 | Pending |
| Q-03 | Phase 4 | Pending |
| Q-04 | Phase 4 | Pending |
| Q-05 | Phase 4 | Pending |
| STATE-01 | Phase 5 | Pending |
| STATE-02 | Phase 5 | Pending |
| STATE-03 | Phase 5 | Pending |
| STATE-04 | Phase 5 | Pending |
| STATE-05 | Phase 5 | Pending |
| STATE-06 | Phase 5 | Pending |
| DIST-01 | Phase 5 | Pending |
| DIST-02 | Phase 5 | Pending |
| DIST-03 | Phase 5 | Pending |
| DIST-04 | Phase 5 | Pending |
| DIST-05 | Phase 5 | Pending |
| DIST-06 | Phase 5 | Pending |
| XC-01 | Phase 3 | Pending |
| XC-02 | Phase 3 | Pending |
| XC-03 | Phase 1 | Complete |
| XC-04 | Phase 1 | Pending |
| XC-05 | Phase 1 | Complete |
| XC-06 | Phase 1 | Pending |
| XC-07 | Phase 1 | Pending |
| XC-08 | Phase 1 | Complete |

**Coverage:**
- v1 requirements: 70 total
- Mapped to phases: 70
- Unmapped: 0

Note: Actual count is 70, not 60 as previously stated. Recount: INIT(8) + SRC(7) + TRUTH(12) + ART(9) + WS(6) + TASK(3) + Q(5) + STATE(6) + DIST(6) + XC(8) = 70.

---
*Requirements defined: 2026-04-07*
*Last updated: 2026-04-07 after roadmap creation*
