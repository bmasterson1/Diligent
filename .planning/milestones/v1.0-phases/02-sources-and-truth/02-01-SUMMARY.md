---
phase: 02-sources-and-truth
plan: 01
subsystem: state
tags: [dataclass, yaml, questions, anchor, atomic-write, templates]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: state models, truth.py reader/writer, sources.py pattern, init_cmd, doctor, atomic_write, templates
provides:
  - FactEntry anchor field for verification gate tolerance comparison
  - QuestionEntry + QuestionsFile models for gate rejection destination
  - questions.py reader/writer (H2 + fenced YAML, atomic_write)
  - QUESTIONS.md.tmpl template for init scaffold
  - 7-file init and doctor awareness
  - anchor_tolerance_pct default 0.5
affects: [02-sources-and-truth, 04-questions-and-reconcile]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Questions state file follows same H2 + fenced YAML pattern as truth.py and sources.py"
    - "Anchor field omitted from YAML when False for backward compatibility"

key-files:
  created:
    - diligent/diligent/state/questions.py
    - diligent/diligent/templates/QUESTIONS.md.tmpl
    - diligent/tests/test_questions_state.py
  modified:
    - diligent/diligent/state/models.py
    - diligent/diligent/state/truth.py
    - diligent/diligent/templates/__init__.py
    - diligent/diligent/templates/config.json.tmpl
    - diligent/diligent/commands/init_cmd.py
    - diligent/diligent/commands/doctor.py
    - diligent/tests/test_init.py
    - diligent/tests/test_doctor.py
    - diligent/tests/test_templates.py

key-decisions:
  - "anchor field omitted from YAML output when False to preserve backward compatibility with existing TRUTH.md files"
  - "QuestionEntry context field is Optional[dict] to hold gate rejection data (key, old_value, new_value, source IDs)"
  - "questions.py replicates H2 + fenced YAML parsing pipeline per Phase 1 decision (no shared utility)"

patterns-established:
  - "Anchor field pattern: sticky bool written only when True, read with default False"
  - "QUESTIONS.md follows same lifecycle as other state files: model, reader/writer, template, init, doctor"

requirements-completed: [TRUTH-03, TRUTH-09, TRUTH-10, TRUTH-11]

# Metrics
duration: 7min
completed: 2026-04-08
---

# Phase 2 Plan 1: Data Layer Extension Summary

**FactEntry anchor field, QuestionEntry model with questions.py reader/writer, QUESTIONS.md template, and 7-file init/doctor awareness**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-08T00:42:30Z
- **Completed:** 2026-04-08T00:50:16Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments
- FactEntry gains anchor: bool field that round-trips through truth.py (sticky, backward compatible)
- QuestionEntry + QuestionsFile models, questions.py reader/writer with atomic_write validation
- QUESTIONS.md.tmpl template and 7-file awareness in init + doctor
- anchor_tolerance_pct default updated from 1.0 to 0.5 per locked decision

## Task Commits

Each task was committed atomically (TDD: test then feat):

1. **Task 1: QuestionEntry model + questions.py reader/writer + template**
   - `64fc3ef` (test: failing tests for anchor, QuestionEntry, questions.py, template)
   - `d5b20b5` (feat: models, truth.py anchor, questions.py, QUESTIONS.md.tmpl, 0.5 default)
2. **Task 2: Update init (7 files) and doctor (7 files) for QUESTIONS.md**
   - `12922f4` (test: failing tests for init 7-file and doctor QUESTIONS.md)
   - `fe8ec88` (feat: init_cmd.py and doctor.py updated for 7 files)

## Files Created/Modified
- `diligent/state/models.py` - Added anchor field to FactEntry, QuestionEntry + QuestionsFile dataclasses
- `diligent/state/truth.py` - Updated _format_fact_yaml and _parse_fact_entry for anchor field
- `diligent/state/questions.py` - New reader/writer: read_questions, write_questions with atomic_write
- `diligent/templates/QUESTIONS.md.tmpl` - New template for init scaffold
- `diligent/templates/__init__.py` - render_config anchor_tolerance_pct 1.0 -> 0.5
- `diligent/templates/config.json.tmpl` - anchor_tolerance_pct 1.0 -> 0.5
- `diligent/commands/init_cmd.py` - STATE_FILES 6 -> 7, QUESTIONS.md rendering
- `diligent/commands/doctor.py` - EXPECTED_FILES 6 -> 7, QUESTIONS.md parse + YAML integrity check
- `tests/test_questions_state.py` - 17 tests for anchor, QuestionEntry, questions.py, template
- `tests/test_init.py` - Updated for 7 files, added QUESTIONS.md parseability test
- `tests/test_doctor.py` - Added QUESTIONS.md missing/corrupt/valid tests
- `tests/test_templates.py` - Updated anchor_tolerance_pct assertion to 0.5

## Decisions Made
- anchor field omitted from YAML output when False to preserve backward compatibility with existing TRUTH.md files
- QuestionEntry context field is Optional[dict] to hold gate rejection data (key, old_value, new_value, source IDs)
- questions.py replicates H2 + fenced YAML parsing pipeline per Phase 1 decision (no shared utility)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Updated existing test_templates.py assertion**
- **Found during:** Task 1 (anchor_tolerance_pct default change)
- **Issue:** test_render_config_template asserted anchor_tolerance_pct == 1.0, now 0.5
- **Fix:** Updated assertion to match new default
- **Files modified:** tests/test_templates.py
- **Verification:** Full test suite passes (133 tests)
- **Committed in:** d5b20b5 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Necessary correction for intentional default change. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- QuestionEntry model and questions.py reader/writer ready for gate rejection writes (02-04, 02-05)
- FactEntry anchor field ready for verification gate tolerance comparison (02-04)
- QUESTIONS.md scaffold ready for Phase 4 CLI commands (ask, answer, questions list)
- 7-file awareness established in init and doctor for all subsequent plans

## Self-Check: PASSED

- All 12 created/modified files verified present
- All 4 commit hashes verified in git log
- SUMMARY.md verified present
- Full test suite: 133 passed

---
*Phase: 02-sources-and-truth*
*Completed: 2026-04-08*
