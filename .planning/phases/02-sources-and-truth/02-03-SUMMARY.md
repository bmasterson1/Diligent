---
phase: 02-sources-and-truth
plan: 03
subsystem: commands
tags: [verification-gate, truth-set, truth-get, numeric-parsing, click, tdd]

# Dependency graph
requires:
  - phase: 02-sources-and-truth
    provides: FactEntry anchor field, QuestionEntry model, questions.py reader/writer, truth.py reader/writer
provides:
  - numeric.py helper with try_parse_numeric and compute_gate_result
  - truth set command with verification gate (exit 2), --confirm override, --anchor sticky
  - truth get command with source citation and anchor/flagged labels
  - Gate rejection writes to QUESTIONS.md with structured context
  - truth group registered in CLI LazyGroup
affects: [02-sources-and-truth, 04-questions-and-reconcile]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "DILIGENT_CWD env var for test isolation of command cwd resolution"
    - "Verification gate uses exit code 2 for discrepancy (distinct from 1 for errors)"
    - "compute_gate_result returns None for no-op, dict for gate fire (pure function, no side effects)"
    - "Anchor sticky pattern: --anchor sets, --no-anchor demotes, absence preserves existing state"

key-files:
  created:
    - diligent/diligent/helpers/numeric.py
    - diligent/diligent/commands/truth_cmd.py
    - diligent/tests/test_verification_gate.py
    - diligent/tests/test_truth_cmd.py
  modified:
    - diligent/diligent/cli.py

key-decisions:
  - "DILIGENT_CWD env var for test isolation: commands check env before walking up from cwd"
  - "compute_gate_result is a pure function returning None or dict, keeping gate logic testable without CLI"
  - "Supersedes chain inserts at position 0 (most recent first) preserving existing chain entries"
  - "Gate rejection question text includes delta description for human readability"

patterns-established:
  - "Command cwd resolution: check DILIGENT_CWD env, then walk up parents for .diligence/"
  - "Verification gate pattern: compute_gate_result -> if fired and not --confirm -> print + write question + exit 2"
  - "No-op fast path: bytewise equal values short-circuit before any gate logic"

requirements-completed: [TRUTH-01, TRUTH-02, TRUTH-04, TRUTH-05, TRUTH-12]

# Metrics
duration: 5min
completed: 2026-04-08
---

# Phase 2 Plan 3: Truth Commands and Verification Gate Summary

**Verification gate with numeric tolerance comparison, truth set/get commands, and gate rejection routing to QUESTIONS.md**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-08T00:54:18Z
- **Completed:** 2026-04-08T00:59:10Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments
- numeric.py helper: try_parse_numeric strips $, commas, %, whitespace; compute_gate_result handles no-op, exact match, anchor tolerance, zero-to-nonzero
- truth set command: required --source, verification gate exits 2 with compact discrepancy, --confirm override, gate rejection writes to QUESTIONS.md, --anchor sticky, --no-anchor demotes, supersedes chain
- truth get command: value lookup with source citation, anchor/flagged labels, --json output
- truth group registered in CLI LazyGroup with set and get subcommands

## Task Commits

Each task was committed atomically (TDD: test then feat):

1. **Task 1: Verification gate logic (numeric.py) + truth set command**
   - `3b84486` (test: failing tests for verification gate and truth set/get)
   - `bdc945c` (feat: numeric.py and truth_cmd.py with set command)
2. **Task 2: Truth get command + CLI registration**
   - `ab90f9c` (test: failing tests for truth get and CLI registration)
   - `23ef5c4` (feat: truth get command and CLI registration)

## Files Created/Modified
- `diligent/helpers/numeric.py` - try_parse_numeric and compute_gate_result: gate comparison logic
- `diligent/commands/truth_cmd.py` - truth command group with set and get subcommands
- `diligent/cli.py` - truth group registered in LazyGroup lazy_subcommands
- `tests/test_verification_gate.py` - 12 tests for numeric parsing and gate comparison
- `tests/test_truth_cmd.py` - 22 tests for truth set (create, update, gate, confirm, anchor) and truth get

## Decisions Made
- DILIGENT_CWD env var for test isolation: commands check env before walking up from cwd
- compute_gate_result is a pure function returning None or dict, keeping gate logic testable without CLI
- Supersedes chain inserts at position 0 (most recent first) preserving existing chain entries
- Gate rejection question text includes delta description for human readability

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Verification gate (TRUTH-04) fully operational for truth set updates
- truth get ready for use by truth list, truth trace, and reconcile commands
- QUESTIONS.md receives gate rejections, ready for Phase 4 ask/answer CLI
- numeric.py helper reusable by any command needing numeric comparison

## Self-Check: PASSED

- All 5 created/modified files verified present
- All 4 commit hashes verified in git log
- SUMMARY.md verified present
- Full test suite: 191 passed (34 plan-specific tests)

---
*Phase: 02-sources-and-truth*
*Completed: 2026-04-08*
