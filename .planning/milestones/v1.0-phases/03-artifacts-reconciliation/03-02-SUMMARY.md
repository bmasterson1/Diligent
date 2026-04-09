---
phase: 03-artifacts-reconciliation
plan: 02
subsystem: commands
tags: [click, cli, artifact, staleness, tdd]

# Dependency graph
requires:
  - phase: 03-artifacts-reconciliation
    plan: 01
    provides: "ArtifactEntry/ArtifactsFile models, read_artifacts/write_artifacts, ARTIFACTS.md template"
  - phase: 02-sources-truth
    provides: "read_truth, read_sources, FactEntry with flagged field, SourceEntry with supersedes"
provides:
  - "artifact register CLI command with --confirm upsert gate and truth key validation"
  - "artifact list CLI command with live staleness computation (value-changed, source-superseded, flagged)"
  - "artifact refresh CLI command with last_refreshed timestamp update"
  - "LazyGroup registration for artifact command group"
affects: [03-03-PLAN, 03-04-PLAN]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Staleness computation: value-changed (fact.date > artifact.last_refreshed) and source-superseded (superseding source date > artifact.last_refreshed)"
    - "Three-state artifact status: CURRENT, STALE, ADVISORY"
    - "Upsert gate pattern: exit 1 without --confirm, update with --confirm (matching truth set pattern)"

key-files:
  created:
    - diligent/diligent/commands/artifact_cmd.py
  modified:
    - diligent/diligent/cli.py
    - diligent/tests/test_artifact_cmd.py

key-decisions:
  - "Staleness is ISO date string comparison (lexicographic works for ISO 8601 dates)"
  - "Source-superseded staleness uses superseded_by index mapping old source ID to new SourceEntry"
  - "Flagged facts produce ADVISORY status (not STALE), consistent with CONTEXT.md spec"
  - "Summary line always counts all artifacts regardless of active filters"

patterns-established:
  - "artifact_cmd.py follows same _find_diligence_dir + DILIGENT_CWD pattern as truth_cmd.py"
  - "Path normalization to posix forward slashes via Path.as_posix() for cross-platform consistency"

requirements-completed: [ART-01, ART-03, ART-04]

# Metrics
duration: 7min
completed: 2026-04-08
---

# Phase 3 Plan 02: Artifact CLI Commands Summary

**artifact register/list/refresh CLI commands with --confirm upsert gate, live staleness computation (value-changed, source-superseded, flagged), and LazyGroup registration**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-08T11:47:55Z
- **Completed:** 2026-04-08T11:54:55Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- artifact register with posix path normalization, comma-separated --references, truth key validation warnings, and --confirm upsert gate
- artifact list with live staleness computation: value-changed (fact date after last_refreshed), source-superseded (newer source after last_refreshed), flagged facts as ADVISORY
- artifact refresh updating last_refreshed timestamp with unknown-path exit code
- All three commands support --json output, artifact registered in CLI LazyGroup

## Task Commits

Each task was committed atomically:

1. **Task 1: artifact register command with --confirm upsert gate**
   - `a550fad` (test: TDD RED - failing tests)
   - `25106df` (feat: TDD GREEN - implementation)
2. **Task 2: artifact list, artifact refresh, and CLI registration**
   - `7d60fa0` (test: TDD RED - failing tests)
   - `d54cd13` (feat: TDD GREEN - implementation)

_Note: TDD tasks have RED (test) and GREEN (feat) commits_

## Files Created/Modified
- `diligent/diligent/commands/artifact_cmd.py` - artifact register, list, refresh subcommands with staleness engine
- `diligent/diligent/cli.py` - Added artifact to LazyGroup lazy_subcommands
- `diligent/tests/test_artifact_cmd.py` - 22 tests covering all artifact command behaviors

## Decisions Made
- Staleness is ISO date string comparison (lexicographic ordering works for ISO 8601 format)
- Source-superseded staleness builds superseded_by index (dict mapping old source ID to new SourceEntry) for efficient lookup
- Flagged facts produce ADVISORY status, not STALE, per CONTEXT.md spec (does not mark artifact stale, does not affect exit code)
- Summary line in artifact list always counts all artifacts regardless of --stale or --workstream filters, matching truth list pattern

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- artifact_cmd.py exports artifact_cmd group, ready for reconcile to consume staleness logic (Plan 03)
- _compute_artifact_status is a module-level function, callable from reconcile engine
- 299 total tests passing, full suite green

## Self-Check: PASSED

All 3 files verified on disk. All 4 commits verified in git log. SUMMARY.md exists.

---
*Phase: 03-artifacts-reconciliation*
*Completed: 2026-04-08*
