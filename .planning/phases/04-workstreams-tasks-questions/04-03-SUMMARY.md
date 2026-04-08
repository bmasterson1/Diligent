---
phase: 04-workstreams-tasks-questions
plan: 03
subsystem: commands
tags: [click, questions, ask, answer, list, gate-origin, owner-taxonomy]

requires:
  - phase: 04-workstreams-tasks-questions
    provides: "QuestionEntry with answer fields, questions.py reader/writer"
provides:
  - "ask_cmd: add questions with auto Q-NNN ID, owner validation, workstream scoping"
  - "answer_cmd: close questions with answer text and optional source citation"
  - "questions_cmd list: display all questions with [gate]/[manual] origin tags, filters, summary"
  - "CLI registration for ask, answer, questions in LazyGroup"
affects: [04-04]

tech-stack:
  added: []
  patterns:
    - "Top-level Click commands (ask, answer) alongside Click group (questions) in same module"
    - "Origin tag derivation: context is not None = [gate], else [manual]"
    - "Summary line always counts all questions regardless of active filters"

key-files:
  created:
    - "diligent/commands/question_cmd.py"
  modified:
    - "diligent/cli.py"
    - "tests/test_question_cmd.py"

key-decisions:
  - "ask and answer are top-level commands, questions is a group with list subcommand, matching plan UX spec"
  - "Owner validation rejects case-sensitive mismatches (SELF, Self are invalid)"
  - "Summary line counts all questions regardless of --owner/--workstream filters, matching truth list pattern"

patterns-established:
  - "Question origin derivation: context != None -> [gate], context == None -> [manual]"
  - "Reuse _next_question_id and _find_diligence_dir per module (no shared utility)"

requirements-completed: [Q-01, Q-02, Q-03, Q-04, Q-05]

duration: 5min
completed: 2026-04-08
---

# Phase 4 Plan 03: Question Commands Summary

**ask/answer/questions list CLI commands with auto Q-NNN IDs, owner taxonomy, gate-origin tags, and filters**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-08T15:19:46Z
- **Completed:** 2026-04-08T15:25:07Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- ask command adds questions with auto-generated Q-NNN IDs, validates owner against 5-value taxonomy, supports --workstream scoping
- answer command closes questions with answer text, optional --source citation, rejects already-answered and nonexistent IDs
- questions list shows [gate]/[manual] origin tags, aligned columns, summary line with open/answered counts
- --owner and --workstream filters on questions list with summary counting all questions
- All commands support --json output
- 33 tests pass across 5 test classes

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement ask and answer commands** - `9221e19` (test: RED) + `2b2b7c6` (feat: GREEN)
2. **Task 2: Implement questions list with origin tags** - `7a6a340` (test: RED) + `5917dbb` (feat: GREEN)

**Plan metadata:** [pending] (docs: complete plan)

_Note: Both tasks used TDD with separate RED and GREEN commits._

## Files Created/Modified
- `diligent/commands/question_cmd.py` - ask_cmd, answer_cmd, questions_cmd with list subcommand (276 lines)
- `diligent/cli.py` - Registered ask, answer, questions in LazyGroup lazy_subcommands
- `tests/test_question_cmd.py` - 33 tests: TestAsk, TestAnswer, TestOwnerValidation, TestQuestionsList, TestGateOrigin (492 lines)

## Decisions Made
- ask and answer are top-level Click commands (not subcommands of a group) matching the planned UX of `diligent ask "text"` and `diligent answer Q-001 "text"`. questions is a Click group with list subcommand.
- Owner validation is case-sensitive: "SELF" and "Self" are rejected. Only exact lowercase matches from the taxonomy (self, principal, seller, broker, counsel) are accepted.
- Summary line in questions list counts all questions regardless of active filters, matching the established pattern from truth list and sources list.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Question commands complete: ask, answer, and questions list fully operational
- Ready for 04-04 (task commands) which completes the workstream/task/question command surface

## Self-Check: PASSED

All 2 created/modified source files verified present on disk. All 4 commits (9221e19, 2b2b7c6, 7a6a340, 5917dbb) verified in git log.

---
*Phase: 04-workstreams-tasks-questions*
*Completed: 2026-04-08*
