---
phase: 4
slug: workstreams-tasks-questions
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >= 8.0 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `cd Diligent && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd Diligent && python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd Diligent && python -m pytest tests/ -x -q`
- **After every plan wave:** Run `cd Diligent && python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | WS-01 | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamNew -x` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | WS-02 | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamList -x` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | WS-03 | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamShow -x` | ❌ W0 | ⬜ pending |
| 04-01-04 | 01 | 1 | WS-04 | unit | `pytest tests/test_workstream_cmd.py::TestWorkstreamTemplates -x` | ❌ W0 | ⬜ pending |
| 04-01-05 | 01 | 1 | WS-05 | unit | `pytest tests/test_init.py::TestInitWorkstreamDirs -x` | ❌ W0 | ⬜ pending |
| 04-01-06 | 01 | 1 | WS-06 | unit | `pytest tests/test_workstream_cmd.py::TestHandEdits -x` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | TASK-01 | unit | `pytest tests/test_task_cmd.py::TestTaskNew -x` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 2 | TASK-02 | unit | `pytest tests/test_task_cmd.py::TestTaskList -x` | ❌ W0 | ⬜ pending |
| 04-02-03 | 02 | 2 | TASK-03 | unit | `pytest tests/test_task_cmd.py::TestTaskComplete -x` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | Q-01 | unit | `pytest tests/test_question_cmd.py::TestAsk -x` | ❌ W0 | ⬜ pending |
| 04-03-02 | 03 | 2 | Q-02 | unit | `pytest tests/test_question_cmd.py::TestOwnerValidation -x` | ❌ W0 | ⬜ pending |
| 04-03-03 | 03 | 2 | Q-03 | unit | `pytest tests/test_question_cmd.py::TestAnswer -x` | ❌ W0 | ⬜ pending |
| 04-03-04 | 03 | 2 | Q-04 | unit | `pytest tests/test_question_cmd.py::TestQuestionsList -x` | ❌ W0 | ⬜ pending |
| 04-03-05 | 03 | 2 | Q-05 | unit | `pytest tests/test_question_cmd.py::TestGateOrigin -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_workstream_cmd.py` -- stubs for WS-01 through WS-06
- [ ] `tests/test_task_cmd.py` -- stubs for TASK-01 through TASK-03
- [ ] `tests/test_question_cmd.py` -- stubs for Q-01 through Q-05
- [ ] Verify existing tests still pass after WorkstreamEntry and QuestionEntry model changes (backward compat)

*Existing infrastructure (pytest, conftest.py) covers framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Hand-edits to WORKSTREAMS.md picked up on next read | WS-06 | Verifiable via unit test | Automated -- no manual step needed |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
