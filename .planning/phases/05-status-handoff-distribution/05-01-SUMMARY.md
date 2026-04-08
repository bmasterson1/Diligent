---
phase: 05-status-handoff-distribution
plan: 01
subsystem: cli
tags: [click, status, time-utils, json-output]

# Dependency graph
requires:
  - phase: 03-reconciliation-staleness
    provides: compute_staleness engine for stale artifact detection
  - phase: 04-questions-tasks-workstreams
    provides: questions, workstreams, artifacts state readers
provides:
  - diligent status command with 5-section deal summary
  - time_utils.py shared utilities (parse_since, is_recent, relative_time_str)
  - --json and --verbose output modes for status
affects: [05-02-handoff, 05-03-distribution]

# Tech tracking
tech-stack:
  added: []
  patterns: [section-capping with "and N more" truncation, activity event collection from timestamps]

key-files:
  created:
    - Diligent/diligent/helpers/time_utils.py
    - Diligent/diligent/commands/status_cmd.py
    - Diligent/tests/test_time_utils.py
    - Diligent/tests/test_status_cmd.py
  modified:
    - Diligent/diligent/cli.py

key-decisions:
  - "Status command delegates stale artifact detection to compute_staleness from reconcile_anchors.py for consistency"
  - "Attention count = stale artifacts + open questions + flagged facts"
  - "Recent activity derived from timestamps across all state files with 14-day window"
  - "Section capping at 5 items with 'and N more' truncation in normal mode"

patterns-established:
  - "_render_section helper for capped list display with verbose override"
  - "Activity event collection pattern: scan state files for timestamps, build verb-past-tense events"

requirements-completed: [STATE-01, STATE-02]

# Metrics
duration: 4min
completed: 2026-04-08
---

# Phase 5 Plan 1: Status Command Summary

**diligent status: 5-section deal summary with header, workstreams, stale artifacts, open questions, recent activity, plus --json and --verbose modes**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-08T21:19:45Z
- **Completed:** 2026-04-08T21:23:36Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 5

## Accomplishments
- Full deal state summary in one command: deal header, workstream counts, stale artifacts, open questions, recent activity
- Post-LOI header shows "N days in diligence" from LOI date; pre-LOI shows "N days tracking" from created date
- Stale artifact detection uses compute_staleness engine for consistency with `diligent reconcile`
- --json emits structured JSON with deal, workstreams, stale_artifacts, open_questions, recent_activity, attention_count
- --verbose removes all section truncation
- time_utils.py provides parse_since, is_recent, relative_time_str reusable for handoff (Plan 02)
- 27 tests covering all sections, both output modes, truncation, and error cases

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for time_utils and status_cmd** - `bae8051` (test)
2. **Task 1 (GREEN): Implement time_utils and status command** - `c24e43e` (feat)

## Files Created/Modified
- `Diligent/diligent/helpers/time_utils.py` - parse_since, is_recent, relative_time_str pure functions
- `Diligent/diligent/commands/status_cmd.py` - status command with 5 sections, --json, --verbose
- `Diligent/diligent/cli.py` - Register status as lazy subcommand
- `Diligent/tests/test_time_utils.py` - 14 tests for time utility functions
- `Diligent/tests/test_status_cmd.py` - 13 tests for status command integration

## Decisions Made
- Status command delegates stale artifact detection to compute_staleness from reconcile_anchors.py, ensuring consistency with `diligent reconcile`
- Attention count sums stale artifacts + open questions + flagged facts (three categories of items needing analyst attention)
- Recent activity derived from timestamps across all state files (facts, sources, artifacts, questions) with a 14-day window
- Section capping at 5 items with "and N more..." truncation in normal mode; --verbose shows all

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- time_utils.py is ready for Plan 02 (handoff command) to import parse_since/is_recent/relative_time_str
- Status command provides the morning-coffee UX; handoff and distribution commands build on the same data readers

## Self-Check: PASSED

- All 6 files verified present on disk
- Both commits (bae8051, c24e43e) verified in git history
- 27/27 tests passing, 456/456 full suite passing (excluding pre-existing install_cmd failure)

---
*Phase: 05-status-handoff-distribution*
*Completed: 2026-04-08*
