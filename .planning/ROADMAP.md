# Roadmap: diligent

## Overview

diligent is built in strict dependency order: the state layer must exist before any command can read or write it, the three registries (sources, truth, artifacts) must be solid before reconciliation can walk the dependency graph, and organizational/output features layer on top. The verification gate on truth set (TRUTH-04) is the single most important behavior in the CLI. The "done" bar: Bryce uses diligent as the real state layer on Project Arrival, and reconcile catches real staleness.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Models, state layer, atomic writes, CLI scaffold, and `diligent init` (completed 2026-04-07)
- [ ] **Phase 2: Sources and Truth** - Source document registry and the core fact management loop with verification gate
- [ ] **Phase 3: Artifacts and Reconciliation** - Deliverable tracking and the dependency-graph staleness engine
- [ ] **Phase 4: Workstreams, Tasks, and Questions** - Organizational layer for structuring deal work
- [ ] **Phase 5: Status, Handoff, and Distribution** - Aggregation commands, AI session restore, skill files, and PyPI ship
- [ ] **Phase 6: Integration and Cleanup** - Fix cross-phase integration inconsistencies and accumulated tech debt before milestone close

## Phase Details

### Phase 1: Foundation
**Goal**: Analyst can scaffold a deal folder and trust that every state file read/write is atomic, correct, and round-trip safe
**Depends on**: Nothing (first phase)
**Requirements**: INIT-01, INIT-02, INIT-03, INIT-04, INIT-05, INIT-06, INIT-07, INIT-08, XC-03, XC-04, XC-05, XC-06, XC-07, XC-08
**Success Criteria** (what must be TRUE):
  1. `diligent init` creates `.diligence/` with all 6 state files from templates in a new deal folder
  2. Every state file can be read into a typed model and written back without data loss or format drift (round-trip fidelity)
  3. `diligent doctor` detects and reports corruption in any state file with actionable fix suggestions
  4. File writes survive simulated crash (atomic write with OneDrive retry) and never leave partial state on disk
  5. CLI starts in under 200ms; all commands support --json output; no interactive prompts break agent tool-use
**Plans:** 3/3 plans complete

Plans:
- [x] 01-01-PLAN.md -- Package scaffold, typed models, atomic write utility, LazyGroup CLI
- [ ] 01-02-PLAN.md -- State file readers/writers and templates for all 6 file types
- [ ] 01-03-PLAN.md -- Commands: init, doctor, config, startup benchmark, JSON output

### Phase 2: Sources and Truth
**Goal**: Analyst can ingest source documents, record validated facts with citations, and trust that TRUTH.md is the single source of truth with full provenance
**Depends on**: Phase 1
**Requirements**: SRC-01, SRC-02, SRC-03, SRC-04, SRC-05, SRC-06, SRC-07, TRUTH-01, TRUTH-02, TRUTH-03, TRUTH-04, TRUTH-05, TRUTH-06, TRUTH-07, TRUTH-08, TRUTH-09, TRUTH-10, TRUTH-11, TRUTH-12
**Success Criteria** (what must be TRUE):
  1. `diligent ingest` registers a source document with metadata and supersedes chain; ingesting an Excel file that supersedes a prior version automatically shows what changed
  2. `diligent truth set` requires --source citation and stores values as quoted strings; updating an existing fact pushes the prior value into a visible supersedes chain
  3. When `truth set` would change a value beyond tolerance, the verification gate stops, surfaces the discrepancy with both sources, and requires explicit confirmation before proceeding; rejection routes the discrepancy to the questions queue
  4. `diligent truth trace` shows full revision history for any fact: every value, source, date, and the diff between source documents
  5. `diligent sources list/show` and `diligent truth get/list/flag` all work with --json output and complete in under 2 seconds
**Plans:** 3/5 plans executed

Plans:
- [ ] 02-01-PLAN.md -- Model extensions (anchor field, QuestionEntry), QUESTIONS.md state layer, init/doctor 7-file updates
- [ ] 02-02-PLAN.md -- Source commands: ingest with source ID generation, sources list, sources show
- [ ] 02-03-PLAN.md -- Truth set with verification gate (TRUTH-04), numeric comparison helper, truth get
- [ ] 02-04-PLAN.md -- Truth list with staleness detection, truth trace with revision timeline, truth flag
- [ ] 02-05-PLAN.md -- Excel/Word diff helpers, sources diff command, ingest auto-diff integration

### Phase 3: Artifacts and Reconciliation
**Goal**: Analyst types one command and gets a definitive answer about which deliverables are stale and why
**Depends on**: Phase 2
**Requirements**: ART-01, ART-02, ART-03, ART-04, ART-05, ART-06, ART-07, ART-08, ART-09, XC-01, XC-02
**Success Criteria** (what must be TRUE):
  1. `diligent artifact register` links a deliverable to specific truth keys; `artifact list` shows all registered artifacts with staleness status
  2. `diligent reconcile` walks source -> fact -> artifact dependency graph and reports which artifacts are stale, which fact changed, when, from what source, and how many days stale
  3. `diligent reconcile --workstream` scopes to one workstream; `--strict` exits non-zero on any staleness for scripted checks
  4. All commands complete in under 2 seconds; reconcile completes in under 10 seconds for a typical deal folder (50-200 sources, 50-500 facts, 20-100 artifacts)
**Plans:** 2/4 plans executed

Plans:
- [ ] 03-01-PLAN.md -- ArtifactEntry model, artifacts.py state layer, ARTIFACTS.md template, init/doctor 8-file update
- [ ] 03-02-PLAN.md -- Artifact CLI commands: register with --confirm upsert, list with staleness, refresh
- [ ] 03-03-PLAN.md -- Reconcile engine (pure function) and reconcile CLI with formatting, filters, exit codes
- [ ] 03-04-PLAN.md -- Docx citation scanner, register integration, performance benchmarks (XC-01, XC-02)

### Phase 4: Workstreams, Tasks, and Questions
**Goal**: Analyst can organize deal work into workstreams with tasks and track open questions that surface naturally from the truth verification process
**Depends on**: Phase 2 (questions queue referenced by TRUTH-04 verification gate)
**Requirements**: WS-01, WS-02, WS-03, WS-04, WS-05, WS-06, TASK-01, TASK-02, TASK-03, Q-01, Q-02, Q-03, Q-04, Q-05
**Success Criteria** (what must be TRUE):
  1. `diligent workstream new` creates a workstream with subdirectory and context files; 6 pre-defined templates available at init time
  2. `diligent task new/list/complete` creates, lists, and closes tasks within a workstream with summary content
  3. `diligent ask` adds open questions with owner and workstream; `diligent answer` closes them with optional source citation
  4. Questions rejected by the truth verification gate (TRUTH-04) appear in `diligent questions list`; all question commands support --owner filter
  5. Hand-edits to WORKSTREAMS.md are picked up on next CLI read (CLI is convenience, not gate)
**Plans:** 3/4 plans executed

Plans:
- [ ] 04-01-PLAN.md -- Model extensions (WorkstreamEntry + QuestionEntry), state layer updates, workstream and task templates
- [ ] 04-02-PLAN.md -- Workstream commands (new, list, show) and init extension for workstream subdirectories
- [ ] 04-03-PLAN.md -- Question commands (ask, answer, questions list) with origin tags and owner filter
- [ ] 04-04-PLAN.md -- Task commands (new, list, complete) with directory-based storage and SUMMARY.md validation

### Phase 5: Status, Handoff, and Distribution
**Goal**: Analyst gets full deal state in one command, can restore AI context in a fresh session, and can install diligent from PyPI with IDE skill files
**Depends on**: Phase 3 and Phase 4
**Requirements**: STATE-01, STATE-02, STATE-03, STATE-04, STATE-05, STATE-06, DIST-01, DIST-02, DIST-03, DIST-04, DIST-05, DIST-06
**Success Criteria** (what must be TRUE):
  1. `diligent status` shows full deal state (truth counts, stale flags, recent ingests, workstream status, artifact counts, open questions) in plain text under 2 seconds; --json available
  2. `diligent handoff` generates a single paste-ready markdown document that restores AI context in a fresh session, including deal context, state, recent truth/source entries, and open questions
  3. `pipx install diligent` works on a clean Windows machine; the package is published to PyPI
  4. `diligent install --claude-code` and `--antigravity` drop parameterized SKILL.md files into the correct IDE directories; `--uninstall` removes them
  5. A second person on a clean machine can go from zero to working `.diligence/` in under five minutes following only the README (catches install-path bugs, missing dependencies, and documentation gaps)
**Plans:** 4/4 plans complete

Plans:
- [x] 05-01-PLAN.md -- Status command with time utilities, 5-section deal summary, --verbose, --json
- [x] 05-02-PLAN.md -- Handoff command with clipboard helper, instruction header, time-window filtering, --clip
- [x] 05-03-PLAN.md -- Skill template files (6 domains) and install command with --claude-code, --antigravity, --uninstall
- [x] 05-04-PLAN.md -- PyPI name resolution, pyproject.toml packaging, README, build verification

### Phase 6: Integration and Cleanup
**Goal**: All cross-phase integration is consistent and accumulated tech debt is resolved before milestone close
**Depends on**: Phase 5
**Requirements**: SRC-01, SRC-03, SRC-04, SRC-05, STATE-05, TASK-03, DIST-05
**Gap Closure:** Closes INT-01, INT-02, INT-03, and broken "AI agent task completion" flow from v1.0 audit
**Success Criteria** (what must be TRUE):
  1. `sources_cmd._find_diligence_dir` walks parent directories and supports `DILIGENT_CWD`, consistent with all 10 other command modules
  2. `status_cmd._build_recent_activity` reads `config.recent_window_days` instead of hardcoding 14 days
  3. `dd_workstreams.md` skill file documents the correct `task complete <ws> <task_id>` signature; AI agents can complete tasks without Click usage errors
  4. `reconcile_cmd.py` displays actual reason text for flagged facts, not the fact key
  5. REQUIREMENTS.md wording for ART-02 and ART-09 reflects actual implementation (ARTIFACTS.md, auto-scan)
  6. Orphaned `write_state` usage is removed or STATE.MD is wired to update on state changes
**Plans:** 0/1 plans complete

Plans:
- [ ] 06-01-PLAN.md -- Integration fixes (INT-01, INT-02, INT-03), tech debt cleanup (reconcile cosmetic, stale docs, orphaned write_state)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6
Phase 4 depends on Phase 2 (verification gate routes to questions queue), NOT on Phase 3.
Phases 3 and 4 can run in parallel or swap order based on dogfooding feedback after Phase 2.
Default order keeps 3 before 4 because reconcile is the feature that justifies the tool.
Phase 5 requires both Phase 3 and Phase 4.
Phase 6 is a gap closure phase from the v1.0 milestone audit; runs after Phase 5.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete   | 2026-04-07 |
| 2. Sources and Truth | 3/5 | In Progress|  |
| 3. Artifacts and Reconciliation | 2/4 | In Progress|  |
| 4. Workstreams, Tasks, and Questions | 3/4 | In Progress|  |
| 5. Status, Handoff, and Distribution | 4/4 | Complete | 2026-04-08 |
| 6. Integration and Cleanup | 0/1 | Pending |  |
