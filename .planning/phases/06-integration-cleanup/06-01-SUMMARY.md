---
phase: 06-integration-cleanup
plan: 01
subsystem: commands
tags: [click, env-var, config, parent-walk, test-isolation]

requires:
  - phase: 02-source-ingest
    provides: sources_cmd.py command module and DILIGENT_CWD pattern
  - phase: 05-status-handoff
    provides: status_cmd.py with _build_recent_activity and config.recent_window_days

provides:
  - Canonical _find_diligence_dir in sources_cmd.py (env_cwd + parent walk + click.ClickException)
  - Config-driven recent_window_days in status_cmd.py

affects: []

tech-stack:
  added: []
  patterns:
    - "All command modules use canonical _find_diligence_dir(env_cwd) pattern"
    - "All command modules read config for tunable parameters instead of hardcoding"

key-files:
  created: []
  modified:
    - Diligent/diligent/commands/sources_cmd.py
    - Diligent/diligent/commands/status_cmd.py
    - Diligent/tests/test_sources_cmd.py
    - Diligent/tests/test_status_cmd.py

key-decisions:
  - "Replicated canonical _find_diligence_dir from truth_cmd.py into sources_cmd.py (per Phase 1 decision: no shared utility)"
  - "status_cmd uses lazy import for read_config (consistent with other lazy imports in that module)"

patterns-established:
  - "Every command module _find_diligence_dir now identical: env_cwd param, parent walk, click.ClickException"

requirements-completed: [SRC-01, SRC-03, SRC-04, SRC-05, STATE-05]

duration: 3min
completed: 2026-04-08
---

# Phase 06 Plan 01: Cross-Phase Consistency Fixes Summary

**Canonical _find_diligence_dir in sources_cmd.py and config-driven recent_window_days in status_cmd.py**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-08T23:02:36Z
- **Completed:** 2026-04-08T23:06:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- sources_cmd._find_diligence_dir now matches the canonical pattern used by all other command modules (env_cwd support, parent directory walk, click.ClickException)
- All 4 sources_cmd caller sites (ingest, list, show, diff) pass DILIGENT_CWD env var
- status_cmd reads config.recent_window_days instead of hardcoding 14, with fallback for missing config
- 6 new regression tests (5 for sources_cmd, 1 for status_cmd) prove the fixes work
- Full test suite green: 504 tests, zero failures

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix sources_cmd._find_diligence_dir (INT-01)** - `fe16de0` (test RED), `5b72856` (feat GREEN)
2. **Task 2: Fix status_cmd config read for recent_window_days (INT-02)** - `8f125ba` (test RED), `0fe51c4` (feat GREEN)

_Note: TDD tasks each have two commits (test RED then feat GREEN)_

## Files Created/Modified

- `Diligent/diligent/commands/sources_cmd.py` - Replaced broken _find_diligence_dir with canonical version; updated all 4 call sites
- `Diligent/diligent/commands/status_cmd.py` - Added config read for recent_window_days before _build_recent_activity call
- `Diligent/tests/test_sources_cmd.py` - Added 5 tests: subdirectory walk, DILIGENT_CWD for list/show/ingest, click.ClickException
- `Diligent/tests/test_status_cmd.py` - Added 1 test: config.recent_window_days affects recent activity filtering

## Decisions Made

- Replicated canonical _find_diligence_dir from truth_cmd.py into sources_cmd.py (per Phase 1 decision: no shared utility, replicate per module for readability)
- status_cmd uses lazy import for read_config (consistent with existing lazy import patterns in that module)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All command modules now use consistent _find_diligence_dir pattern
- Config-driven parameters are respected across all commands
- Ready for remaining Phase 6 plans (06-02 already complete)

## Self-Check: PASSED

- All 4 modified files exist on disk
- All 4 TDD commits (fe16de0, 5b72856, 8f125ba, 0fe51c4) found in git log
- 504/504 tests pass

---
*Phase: 06-integration-cleanup*
*Completed: 2026-04-08*
