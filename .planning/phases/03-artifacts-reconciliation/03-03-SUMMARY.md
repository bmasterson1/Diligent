---
phase: 03-artifacts-reconciliation
plan: 03
subsystem: reconcile
tags: [staleness, reconcile, pure-function, cli, dataclass]

# Dependency graph
requires:
  - phase: 03-artifacts-reconciliation
    plan: 01
    provides: "ArtifactEntry model, read_artifacts, ARTIFACTS.md state layer"
  - phase: 02-sources-truth
    provides: "FactEntry model, read_truth, SourceEntry model, read_sources"
provides:
  - "compute_staleness pure function engine (reconcile_anchors.py)"
  - "StaleArtifact and StaleFactInfo dataclasses"
  - "reconcile CLI command with --workstream, --strict, --all, --verbose, --json"
  - "Two-trigger staleness: value-changed and source-superseded with temporal guards"
  - "Flagged facts advisory subsystem (never marks artifact stale)"
affects: [03-04-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure function staleness engine with zero I/O imports for testability"
    - "Thin CLI wrapper: reads files, calls engine, formats output"
    - "Two-trigger staleness with temporal guards against false positives"
    - "Advisory-only flagged facts (separate from staleness)"

key-files:
  created:
    - diligent/diligent/helpers/reconcile_anchors.py
    - diligent/diligent/commands/reconcile_cmd.py
    - diligent/tests/test_reconcile_engine.py
    - diligent/tests/test_reconcile.py
  modified:
    - diligent/diligent/cli.py

key-decisions:
  - "reconcile_anchors.py is a pure function with zero I/O imports (no click, pathlib, os) for maximum testability"
  - "Source-superseded only fires when superseding source date > artifact last_refreshed (temporal guard prevents false positives from historical supersedes)"
  - "Flagged facts are strictly advisory: they populate a separate section but never set is_stale or affect exit code without --strict"
  - "reconcile registered as top-level LazyGroup command (not under artifact group) matching diligent reconcile UX"

patterns-established:
  - "Pure function engine + thin CLI wrapper separation for complex analysis commands"
  - "Two-trigger staleness detection with temporal guards"
  - "Advisory-only subsystem for flagged data"

requirements-completed: [ART-05, ART-06, ART-07, ART-08]

# Metrics
duration: 8min
completed: 2026-04-08
---

# Phase 3 Plan 03: Reconcile Engine and CLI Summary

**Pure function staleness engine computing two-trigger staleness (value-changed, source-superseded) plus flagged advisory, with thin CLI wrapper showing compact grouped output, exit codes, and --workstream/--strict/--all/--verbose/--json flags**

## Performance

- **Duration:** 8 min
- **Started:** 2026-04-08T11:48:16Z
- **Completed:** 2026-04-08T11:57:08Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- reconcile_anchors.py pure function engine with zero I/O imports, computing two-trigger staleness (value-changed when fact.date > last_refreshed, source-superseded when superseding source date > last_refreshed) plus advisory flagged facts
- reconcile CLI command with compact one-liner output grouped by artifact, sub-sections for value changed / source superseded / flagged, and summary line
- Full flag support: --workstream filter, --strict elevates flagged to non-zero exit, --all shows current artifacts, --verbose adds source detail lines, --json structured output
- 29 new tests (16 engine + 13 CLI) covering all staleness triggers, temporal guards, edge cases, output formatting, and exit codes

## Task Commits

Each task was committed atomically:

1. **Task 1: reconcile_anchors.py pure function staleness engine**
   - `df7aed8` (test: TDD RED - failing tests for engine)
   - `f55db2d` (feat: TDD GREEN - pure function implementation)
2. **Task 2: reconcile CLI command with formatting, filters, and exit codes**
   - `4718bb5` (test: TDD RED - failing tests for CLI)
   - `779cbc5` (feat: TDD GREEN - CLI implementation and LazyGroup registration)

_Note: TDD tasks have RED (test) and GREEN (feat) commits_

## Files Created/Modified
- `diligent/diligent/helpers/reconcile_anchors.py` - Pure function staleness engine: compute_staleness, StaleArtifact, StaleFactInfo
- `diligent/diligent/commands/reconcile_cmd.py` - Thin CLI wrapper: reads state files, calls engine, formats grouped output
- `diligent/diligent/cli.py` - Added reconcile to LazyGroup lazy_subcommands
- `diligent/tests/test_reconcile_engine.py` - 16 tests for engine: all staleness triggers, temporal guards, pure function validation
- `diligent/tests/test_reconcile.py` - 13 tests for CLI: output formatting, exit codes, all flags

## Decisions Made
- reconcile_anchors.py is a pure function with zero I/O imports (no click, pathlib, os) for maximum testability and separation of concerns
- Source-superseded only fires when superseding source date > artifact last_refreshed (temporal guard prevents false positives from historical supersedes)
- Flagged facts are strictly advisory: they populate a separate section but never set is_stale or affect exit code without --strict
- reconcile registered as top-level LazyGroup command (not under artifact group) matching `diligent reconcile` UX from CONTEXT.md

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing test failure discovered in `test_artifact_cmd.py::TestArtifactList::test_list_shows_all_artifacts_with_status` (exit_code 2 instead of 0). This is from Plan 02 and unrelated to Plan 03 changes. Logged to `deferred-items.md`.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Reconcile engine and CLI complete, ready for artifact scanner (Plan 04)
- compute_staleness is importable as a pure function for any future integration
- 290 total tests passing (excluding 1 pre-existing Plan 02 failure in test_artifact_cmd.py)

## Self-Check: PASSED

All 5 files verified on disk. All 4 commits verified in git log. SUMMARY.md exists.

---
*Phase: 03-artifacts-reconciliation*
*Completed: 2026-04-08*
