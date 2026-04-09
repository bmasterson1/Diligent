---
phase: 2
slug: sources-and-truth
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-XX | 01 | 0 | SRC-01..SRC-07, TRUTH-01..TRUTH-12 | stubs | `python -m pytest tests/ -x -q` | Wave 0 | ⬜ pending |
| 02-XX-XX | 01 | 1 | SRC-01 | integration | `python -m pytest tests/test_ingest.py -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 01 | 1 | SRC-02 | unit | `python -m pytest tests/test_source_ids.py -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 01 | 1 | SRC-03 | integration | `python -m pytest tests/test_sources_cmd.py::test_list -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 01 | 1 | SRC-04 | integration | `python -m pytest tests/test_sources_cmd.py::test_show -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 02 | 1 | SRC-05 | integration | `python -m pytest tests/test_sources_diff.py -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 02 | 1 | SRC-06 | unit | `python -m pytest tests/test_diff_excel.py -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 02 | 1 | SRC-07 | integration | `python -m pytest tests/test_ingest.py::test_auto_diff -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-01 | integration | `python -m pytest tests/test_truth_cmd.py::test_set_new -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-02 | integration | `python -m pytest tests/test_truth_cmd.py::test_set_update -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-03 | unit | `python -m pytest tests/test_verification_gate.py::test_anchor_tolerance -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-04 | integration | `python -m pytest tests/test_verification_gate.py -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-05 | integration | `python -m pytest tests/test_truth_cmd.py::test_get -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-06 | integration | `python -m pytest tests/test_truth_cmd.py::test_list -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-07 | integration | `python -m pytest tests/test_truth_cmd.py::test_trace -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-08 | integration | `python -m pytest tests/test_truth_cmd.py::test_flag -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-09 | unit | `python -m pytest tests/test_truth_cmd.py::test_append_only -x` | Wave 0 | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-10 | unit | Already covered by test_state_roundtrip.py | Exists | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-11 | unit | Already covered by test_state_roundtrip.py | Exists | ⬜ pending |
| 02-XX-XX | 03 | 2 | TRUTH-12 | integration | `python -m pytest tests/test_truth_cmd.py::test_optional_flags -x` | Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ingest.py` -- stubs for SRC-01, SRC-02, SRC-07
- [ ] `tests/test_sources_cmd.py` -- stubs for SRC-03, SRC-04
- [ ] `tests/test_sources_diff.py` -- stubs for SRC-05
- [ ] `tests/test_diff_excel.py` -- stubs for SRC-06 (needs sample .xlsx fixtures)
- [ ] `tests/test_truth_cmd.py` -- stubs for TRUTH-01, TRUTH-02, TRUTH-05, TRUTH-06, TRUTH-07, TRUTH-08, TRUTH-09, TRUTH-12
- [ ] `tests/test_verification_gate.py` -- stubs for TRUTH-03, TRUTH-04
- [ ] `tests/test_questions_state.py` -- stubs for QUESTIONS.md reader/writer round-trip
- [ ] `tests/fixtures/` -- sample .xlsx files for Excel diff tests, sample .docx for Word diff tests
- [ ] Update `tests/test_init.py` -- verify 7 files scaffolded (was 6)
- [ ] Update `tests/test_doctor.py` -- verify QUESTIONS.md existence check

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| CLI startup < 200ms with lazy imports | SRC-06, TRUTH-* | Timing-sensitive, machine-dependent | `time diligent --help` after importing openpyxl/python-docx |
| Excel diff renders readable table output | SRC-06 | Visual rendering quality | Run `diligent sources diff` on two sample .xlsx files, inspect output |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
