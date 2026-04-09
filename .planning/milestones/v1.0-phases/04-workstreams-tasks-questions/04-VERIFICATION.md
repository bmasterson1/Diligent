---
phase: 04-workstreams-tasks-questions
verified: 2026-04-08T16:00:00Z
status: passed
score: 14/14 must-haves verified
re_verification: false
---

# Phase 4: Workstreams, Tasks, Questions Verification Report

**Phase Goal:** Analyst can organize deal work into workstreams with tasks and track open questions that surface naturally from the truth verification process
**Verified:** 2026-04-08
**Status:** passed
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | WorkstreamEntry has description and created fields with backward-compatible defaults | VERIFIED | models.py lines 67-69: `description: str = ""`, `created: str = ""` |
| 2  | QuestionEntry has answer, answer_source, and date_answered fields with None defaults | VERIFIED | models.py lines 127-129: all three Optional[str] = None |
| 3  | read_workstreams handles files with and without new fields | VERIFIED | workstreams.py line 91-92: `data.get("description", "")`, `data.get("created", "")` |
| 4  | read_questions handles files with and without answer fields | VERIFIED | questions.py lines 92-97: conditional None handling for all three answer fields |
| 5  | write_workstreams emits description/created only when populated | VERIFIED | workstreams.py lines 118-121: `if entry.description:` / `if entry.created:` guards |
| 6  | write_questions emits answer fields only when not None | VERIFIED | questions.py lines 131-137: `if entry.answer is not None:` / `if entry.answer_source is not None:` / `if entry.date_answered is not None:` |
| 7  | 6 tailored workstream CONTEXT.md templates exist with 3-4 commented section headers each | VERIFIED | financial.md (4 sections), retention.md, technical.md (4), legal.md (3), hr.md (3), integration.md (3) - all present |
| 8  | Generic RESEARCH.md template and ws_context.md.tmpl exist for all workstream types | VERIFIED | ws_research.md.tmpl and ws_context.md.tmpl both present and contain $WORKSTREAM_NAME substitution |
| 9  | Task directory templates exist for SUMMARY.md, PLAN.md, VERIFICATION.md, status.yaml | VERIFIED | task_summary.md.tmpl, task_plan.md.tmpl, task_verification.md.tmpl, task_status.yaml.tmpl all present |
| 10 | workstream new creates subdirectory with tailored or generic CONTEXT.md and RESEARCH.md | VERIFIED | workstream_cmd.py lines 125-140: template selection and file write logic; 21 tests pass |
| 11 | workstream new/list/show commands support --json and cross-file stat aggregation | VERIFIED | workstream_cmd.py: all three subcommands present, show aggregates from QUESTIONS.md, TRUTH.md, ARTIFACTS.md, tasks dir |
| 12 | ask/answer/questions list commands are fully implemented with Q-NNN IDs, owner taxonomy, and [gate]/[manual] tags | VERIFIED | question_cmd.py 276 lines; VALID_OWNERS = 5 values; _origin() derives [gate] from context != None; 33 tests pass |
| 13 | task new/list/complete commands are fully implemented with NNN-slug directories and SUMMARY.md gate | VERIFIED | task_cmd.py 326 lines; _slugify(), _next_task_id(), content validation strips HTML comments and headings; 21 tests pass |
| 14 | init creates workstream subdirectories for selected workstreams with tailored templates | VERIFIED | init_cmd.py lines 299-332: non-fatal try/except block creates workstreams dir, CONTEXT.md, RESEARCH.md per workstream |

**Score:** 14/14 truths verified

### Required Artifacts

| Artifact | Min Lines | Actual Lines | Status | Notes |
|----------|-----------|--------------|--------|-------|
| `diligent/diligent/state/models.py` | - | 157 | VERIFIED | WorkstreamEntry and QuestionEntry both extended |
| `diligent/diligent/state/workstreams.py` | - | 146 | VERIFIED | read/write both updated for new fields |
| `diligent/diligent/state/questions.py` | - | 188 | VERIFIED | read/write both updated for answer fields |
| `diligent/diligent/templates/workstreams/financial.md` | 10 | 16 | VERIFIED | 4 H2 sections with HTML comment guidance |
| `diligent/diligent/templates/ws_research.md.tmpl` | 5 | 3 | VERIFIED | Minimal by design - research is not pre-scaffolded |
| `diligent/diligent/commands/workstream_cmd.py` | 150 | 373 | VERIFIED | new/list/show fully implemented |
| `diligent/tests/test_workstream_cmd.py` | 100 | 435 | VERIFIED | 21 tests across all subcommands |
| `diligent/diligent/commands/question_cmd.py` | 150 | 276 | VERIFIED | ask/answer/questions list fully implemented |
| `diligent/tests/test_question_cmd.py` | 100 | 492 | VERIFIED | 33 tests across 5 test classes |
| `diligent/diligent/commands/task_cmd.py` | 150 | 326 | VERIFIED | new/list/complete fully implemented |
| `diligent/tests/test_task_cmd.py` | 100 | 534 | VERIFIED | 21 tests across TestTaskNew/List/Complete |

Note on ws_research.md.tmpl: 3 lines is intentional per plan spec ("Empty body - research is created during work, not scaffolded"). The min_lines: 5 in 04-01-PLAN would fail a strict tool check, but the plan's own prose explains the template is minimal by design. Content is substantive (H1 heading + HTML comment guidance).

### Key Link Verification

| From | To | Via | Status | Evidence |
|------|----|-----|--------|---------|
| workstreams.py | models.py | WorkstreamEntry import | VERIFIED | Line 13: `from diligent.state.models import WorkstreamEntry, WorkstreamsFile` |
| questions.py | models.py | QuestionEntry import | VERIFIED | Line 13: `from diligent.state.models import QuestionEntry, QuestionsFile` |
| workstream_cmd.py | workstreams.py | read_workstreams, write_workstreams | VERIFIED | Line 19: `from diligent.state.workstreams import read_workstreams, write_workstreams`; both called |
| workstream_cmd.py | templates/workstreams/ | TEMPLATE_DIR / "workstreams" / f"{name}.md" | VERIFIED | Line 127: tailored template path construction and read |
| cli.py | workstream_cmd.py | LazyGroup registration | VERIFIED | cli.py line 51: `"workstream": "diligent.commands.workstream_cmd.workstream_cmd"` |
| init_cmd.py | templates/workstreams/ | tailored template copy | VERIFIED | init_cmd.py lines 308-311: same VALID_WORKSTREAMS path pattern |
| question_cmd.py | questions.py | read_questions, write_questions | VERIFIED | Line 19: `from diligent.state.questions import read_questions, write_questions`; both called |
| question_cmd.py | models.py | QuestionEntry with answer fields | VERIFIED | Line 18: `from diligent.state.models import QuestionEntry, QuestionsFile` |
| cli.py | question_cmd.py | LazyGroup for ask, answer, questions | VERIFIED | cli.py lines 53-55: all three registered |
| task_cmd.py | templates/ | render_template for task files | VERIFIED | Line 17: `from diligent.templates import render_template`; called 4x in task_new |
| task_cmd.py | .diligence/workstreams/tasks/ | directory creation + status.yaml | VERIFIED | Lines 140-169: tasks_dir.mkdir, task_dir.mkdir, status.yaml write |
| cli.py | task_cmd.py | LazyGroup registration | VERIFIED | cli.py line 52: `"task": "diligent.commands.task_cmd.task_cmd"` |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|---------|
| WS-01 | 04-02 | `workstream new <name>` creates subdirectory with CONTEXT.md and RESEARCH.md | SATISFIED | workstream_cmd.py lines 121-140; test_workstream_cmd.py TestWorkstreamNew |
| WS-02 | 04-02 | `workstream list` shows all workstreams with status and task count | SATISFIED | workstream_cmd.py lines 170-252; list shows name/status/tasks/questions columns |
| WS-03 | 04-02 | `workstream show <name>` displays full workstream detail | SATISFIED | workstream_cmd.py lines 255-373; aggregates 5 data sources |
| WS-04 | 04-01 | Pre-defined workstream templates: financial, retention, technical, legal, hr, integration | SATISFIED | 6 files in diligent/templates/workstreams/; TEMPLATE_WORKSTREAMS list in workstream_cmd.py |
| WS-05 | 04-02 | Workstream customization at init time | SATISFIED | init_cmd.py --workstreams flag, _prompt_workstreams() for interactive mode |
| WS-06 | 04-01 | CLI reads state from files on every invocation; hand-edits picked up on next read | SATISFIED | workstreams.py reads WORKSTREAMS.md on every call; no in-memory cache; confirmed by TestHandEdits test |
| TASK-01 | 04-04 | `task new <ws> <desc>` creates task directory with SUMMARY.md scaffolded | SATISFIED | task_cmd.py task_new; creates NNN-slug/ with all 4 files |
| TASK-02 | 04-04 | `task list <ws>` lists tasks with status | SATISFIED | task_cmd.py task_list; shows ID/DESCRIPTION/STATUS columns with summary |
| TASK-03 | 04-04 | `task complete <ws> <task-id>` validates SUMMARY.md and writes complete | SATISFIED | task_cmd.py task_complete; strips HTML comments + headings; exits non-zero if empty |
| Q-01 | 04-03 | `diligent ask <text>` adds open question with --workstream and --owner | SATISFIED | question_cmd.py ask_cmd; auto Q-NNN, owner defaults to self |
| Q-02 | 04-03 | Owner taxonomy: self, principal, seller, broker, counsel | SATISFIED | VALID_OWNERS = ["self", "principal", "seller", "broker", "counsel"] in question_cmd.py |
| Q-03 | 04-03 | `diligent answer <q-id> <text>` closes question with optional --source | SATISFIED | question_cmd.py answer_cmd; sets answer/answer_source/date_answered/status=answered |
| Q-04 | 04-03 | `diligent questions list` shows open questions; supports --owner filter | SATISFIED | question_cmd.py questions_list; --owner and --workstream filters both present |
| Q-05 | 04-03 | Unsourced claims rejected by truth set pushed to questions queue | SATISFIED | Pre-existing from Phase 2/3; QuestionEntry.context field carries gate context; [gate] origin tag verified in questions list |

All 14 requirement IDs declared across phase plans are accounted for. No orphaned requirements found - REQUIREMENTS.md traceability table maps WS-01 through Q-05 to Phase 4 with status Complete.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| workstream_cmd.py | 83 | `pass` in `def workstream_cmd()` | Info | Normal Click group body - not a stub |

No blocking anti-patterns. The single `pass` is the required empty body for a Click group decorator pattern.

### Human Verification Required

#### 1. Interactive workstream selection during init

**Test:** Run `diligent init` without `--workstreams` flag and without `--non-interactive`
**Expected:** CLI prompts with numbered list of 6 workstreams, accepts comma-separated selection, creates subdirectories for selected workstreams
**Why human:** Requires interactive terminal input; CliRunner tests bypass the prompt

#### 2. Hand-edit round-trip in live deal folder

**Test:** Manually edit WORKSTREAMS.md in an active .diligence/ folder to add a new workstream entry without using CLI, then run `workstream list`
**Expected:** Hand-edited entry appears in output with correct counts (WS-06)
**Why human:** Tests cover this via CliRunner fixtures, but live file editing behavior warrants live confirmation

### Gaps Summary

No gaps. All 14 must-haves verified, all 14 requirement IDs satisfied, 429 tests pass with zero regressions. All command files exceed minimum line thresholds. All key links confirmed present and connected.

---
*Verified: 2026-04-08*
*Verifier: Claude (gsd-verifier)*
