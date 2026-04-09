---
phase: 04-workstreams-tasks-questions
plan: 02
subsystem: cli
tags: [click, workstream, templates, init, lazy-group, yaml]

requires:
  - phase: 04-workstreams-tasks-questions
    provides: "WorkstreamEntry with description/created fields, tailored template files, generic ws_context/ws_research templates"
  - phase: 01-foundation
    provides: "LazyGroup CLI, atomic_write, output_result, render_template"
provides:
  - "workstream new/list/show CLI commands"
  - "Init workstream subdirectory creation with tailored templates"
  - "task_cmd.py stub for Plan 04-03"
  - "LazyGroup registration for workstream and task commands"
affects: [04-03, 04-04]

tech-stack:
  added: []
  patterns:
    - "Workstream command module replicates _find_diligence_dir per established pattern"
    - "Lazy-import of state readers inside function body to avoid startup cost"
    - "Non-fatal subdirectory creation in init: state files remain valid on failure"

key-files:
  created:
    - "diligent/commands/workstream_cmd.py"
    - "diligent/commands/task_cmd.py"
    - "tests/test_workstream_cmd.py"
  modified:
    - "diligent/commands/init_cmd.py"
    - "diligent/cli.py"
    - "tests/test_init.py"

key-decisions:
  - "Workstream subdirectory creation in init is non-fatal: wrapped in try/except after state files are written"
  - "WORKSTREAMS.md entries from init now include description and created fields via updated _build_workstream_entries"
  - "Updated existing test_init_reports_8_files_created to test_init_reports_files_created to account for workstream dir files"

patterns-established:
  - "Non-fatal post-init directory scaffolding: create after state files succeed, warn on failure"
  - "Workstream show lazy-imports state readers to keep startup fast"

requirements-completed: [WS-01, WS-02, WS-03, WS-05]

duration: 5min
completed: 2026-04-08
---

# Phase 4 Plan 02: Workstream Commands Summary

**Workstream new/list/show CLI with tailored templates, init subdirectory creation, and cross-file stat aggregation**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-08T15:20:13Z
- **Completed:** 2026-04-08T15:25:22Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- workstream new creates subdirectories with tailored CONTEXT.md (for known templates) or generic CONTEXT.md (for custom names), plus generic RESEARCH.md
- workstream list shows aligned columns with task and question counts aggregated from filesystem and QUESTIONS.md
- workstream show aggregates cross-file stats from WORKSTREAMS.md, QUESTIONS.md, TRUTH.md, ARTIFACTS.md, and task directories
- Init extended to create workstream subdirectories with tailored templates during deal initialization
- WORKSTREAMS.md entries from init now include description and created fields
- 408 tests pass with zero regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement workstream_cmd.py with new, list, show subcommands** - `ee4ea00` (test: failing tests) + `babc219` (feat: implementation)
2. **Task 2: Extend init command to create workstream subdirectories** - `f7b7e58` (test: failing tests) + `ed25136` (feat: implementation)

**Plan metadata:** [pending] (docs: complete plan)

_Note: Both tasks used TDD with separate RED and GREEN commits._

## Files Created/Modified
- `diligent/commands/workstream_cmd.py` - workstream new/list/show commands with name validation, template rendering, cross-file aggregation
- `diligent/commands/task_cmd.py` - Stub for Plan 04-03 LazyGroup registration
- `diligent/commands/init_cmd.py` - Updated _build_workstream_entries with description/created, added subdirectory creation after state files
- `diligent/cli.py` - Registered workstream and task commands in LazyGroup
- `tests/test_workstream_cmd.py` - 21 tests covering new/list/show/hand-edits/json output
- `tests/test_init.py` - 8 new tests for init workstream subdirectory creation, updated existing test assertion

## Decisions Made
- Workstream subdirectory creation in init is non-fatal: wrapped in try/except after state files are written. If directory creation fails (e.g., permissions), the deal folder still has valid state files.
- Updated _build_workstream_entries to accept iso_date parameter and emit description/created fields. Known workstreams get descriptions from WORKSTREAM_DESCRIPTIONS dict.
- Updated existing test from exact 8-file count to >= 8 and added assertions for workstream directory files in the output.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing test assertion for files_created count**
- **Found during:** Task 2 (init extension)
- **Issue:** test_init_reports_8_files_created expected exactly 8 files, but init now reports 12 (8 state + 4 workstream files)
- **Fix:** Renamed test to test_init_reports_files_created, changed assertion to >= 8, added workstream file assertions
- **Files modified:** tests/test_init.py
- **Verification:** All 28 init tests pass
- **Committed in:** ed25136 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Test assertion update necessary for correctness. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Workstream commands ready for 04-03 (task commands) which will use workstream subdirectories for task directory creation
- task_cmd.py stub in place for Plan 04-03 to implement task new/list/complete
- question_cmd.py already exists with ask/answer/questions list implementations (created in a prior session)

## Self-Check: PASSED

All 6 created/modified files verified present on disk. All 4 commits (ee4ea00, babc219, f7b7e58, ed25136) verified in git log. workstream_cmd.py: 373 lines (min 150). test_workstream_cmd.py: 435 lines (min 100).

---
*Phase: 04-workstreams-tasks-questions*
*Completed: 2026-04-08*
