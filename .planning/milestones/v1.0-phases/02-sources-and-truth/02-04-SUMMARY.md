---
phase: 02-sources-and-truth
plan: 04
subsystem: commands
tags: [truth-list, truth-trace, truth-flag, staleness-detection, supersedes, click, tdd]

# Dependency graph
requires:
  - phase: 02-sources-and-truth
    provides: truth set/get commands, FactEntry model with flagged/supersedes, sources.py read_sources, truth.py read/write
provides:
  - truth list command with three-state status (current/flagged/stale) and staleness detection via SOURCES.md supersedes
  - truth trace command with reverse-chronological timeline and source path resolution
  - truth flag command to mark/clear facts for review
  - _build_superseded_source_set helper for cross-referencing source supersedes chains
  - _compute_fact_status helper for deriving fact display status
affects: [02-sources-and-truth, 03-reconcile-engine, 04-questions-and-reconcile]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Staleness detection: build set of superseded source IDs from SOURCES.md, check fact.source membership"
    - "Summary line always counts ALL facts, filters only affect displayed rows"
    - "truth trace timeline: current value first, flag event interleaved, then supersedes chain"
    - "Mutually exclusive Click options enforced with manual validation (--reason vs --clear)"

key-files:
  created: []
  modified:
    - diligent/diligent/commands/truth_cmd.py
    - diligent/tests/test_truth_cmd.py

key-decisions:
  - "Staleness detection cross-references SOURCES.md supersedes chains rather than timestamp comparison"
  - "Summary line counts all facts regardless of active filters for consistent totals"
  - "Flag events in trace timeline appear after current value entry, before supersedes chain"
  - "Source path resolution falls back to source ID string when source not found in SOURCES.md"

patterns-established:
  - "Staleness pattern: _build_superseded_source_set builds lookup set, _compute_fact_status derives status per fact"
  - "Column-aligned output: fixed widths (key=25, value=30, status=8, source=15) with f-string formatting"
  - "Trace timeline: list of dicts with label/value/source/date/path/type fields"

requirements-completed: [TRUTH-06, TRUTH-07, TRUTH-08]

# Metrics
duration: 5min
completed: 2026-04-08
---

# Phase 2 Plan 4: Truth Display and Management Commands Summary

**Truth list with three-state staleness detection via SOURCES.md supersedes, truth trace with reverse-chronological timeline, and truth flag for marking facts for review**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-08T01:03:22Z
- **Completed:** 2026-04-08T01:08:42Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- truth list: aligned per-fact output with three-state status (current/flagged/stale) driven by SOURCES.md supersedes chain cross-reference
- truth list filters: --stale shows flagged OR stale, --workstream scopes to one workstream, filters combine, summary line always counts all facts
- truth trace: reverse-chronological timeline with source file path resolution from SOURCES.md and flag events interleaved
- truth flag: sets/clears flagged dict with reason and date, mutually exclusive --reason/--clear options

## Task Commits

Each task was committed atomically (TDD: test then feat):

1. **Task 1: Truth list with staleness detection**
   - `434bb6a` (test: failing tests for truth list with staleness detection)
   - `8213f70` (feat: implement truth list with staleness detection)
2. **Task 2: Truth trace and truth flag commands**
   - `9a80943` (test: failing tests for truth trace and truth flag)
   - `2b51514` (feat: implement truth trace and truth flag commands)

## Files Created/Modified
- `diligent/commands/truth_cmd.py` - Added list, trace, flag subcommands plus _build_superseded_source_set and _compute_fact_status helpers
- `tests/test_truth_cmd.py` - 25 new tests (13 list + 6 trace + 6 flag), total 47 truth command tests

## Decisions Made
- Staleness detection cross-references SOURCES.md supersedes chains rather than timestamp comparison
- Summary line counts all facts regardless of active filters for consistent totals
- Flag events in trace timeline appear after current value entry, before supersedes chain
- Source path resolution falls back to source ID string when source not found in SOURCES.md

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- truth list with staleness detection ready for reconcile engine (Phase 3) to consume
- truth trace provides full provenance for analyst fact investigation
- truth flag marking enables reconcile workflow to surface facts needing review
- All three commands support --json for programmatic consumption

## Self-Check: PASSED
