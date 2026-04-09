---
phase: 5
slug: status-handoff-distribution
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x --timeout=30` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x --timeout=30`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 0 | STATE-01, STATE-02 | unit stubs | `pytest tests/test_status_cmd.py -x` | No -- Wave 0 | ⬜ pending |
| 05-01-02 | 01 | 0 | STATE-03, STATE-04, STATE-05, STATE-06 | unit stubs | `pytest tests/test_handoff_cmd.py -x` | No -- Wave 0 | ⬜ pending |
| 05-01-03 | 01 | 0 | DIST-02, DIST-03, DIST-04, DIST-05, DIST-06 | unit stubs | `pytest tests/test_install_cmd.py -x` | No -- Wave 0 | ⬜ pending |
| 05-02-xx | 02 | 1 | STATE-01 | integration | `pytest tests/test_status_cmd.py -x` | No -- Wave 0 | ⬜ pending |
| 05-02-xx | 02 | 1 | STATE-02 | integration | `pytest tests/test_status_cmd.py::TestStatusJson -x` | No -- Wave 0 | ⬜ pending |
| 05-03-xx | 03 | 1 | STATE-03 | integration | `pytest tests/test_handoff_cmd.py -x` | No -- Wave 0 | ⬜ pending |
| 05-03-xx | 03 | 1 | STATE-04 | integration | `pytest tests/test_handoff_cmd.py::TestHandoffContent -x` | No -- Wave 0 | ⬜ pending |
| 05-03-xx | 03 | 1 | STATE-05 | unit | `pytest tests/test_handoff_cmd.py::TestHandoffRecency -x` | No -- Wave 0 | ⬜ pending |
| 05-03-xx | 03 | 1 | STATE-06 | integration | `pytest tests/test_handoff_cmd.py::TestHandoffOutput -x` | No -- Wave 0 | ⬜ pending |
| 05-04-xx | 04 | 2 | DIST-02 | integration | `pytest tests/test_install_cmd.py::TestInstallAntigravity -x` | No -- Wave 0 | ⬜ pending |
| 05-04-xx | 04 | 2 | DIST-03 | integration | `pytest tests/test_install_cmd.py::TestInstallClaudeCode -x` | No -- Wave 0 | ⬜ pending |
| 05-04-xx | 04 | 2 | DIST-04 | integration | `pytest tests/test_install_cmd.py::TestUninstall -x` | No -- Wave 0 | ⬜ pending |
| 05-04-xx | 04 | 2 | DIST-05 | unit | `pytest tests/test_install_cmd.py::TestSkillParameterization -x` | No -- Wave 0 | ⬜ pending |
| 05-04-xx | 04 | 2 | DIST-06 | unit | `pytest tests/test_install_cmd.py::TestSkillFileCount -x` | No -- Wave 0 | ⬜ pending |
| 05-05-xx | 05 | 3 | DIST-01 | manual-only | Manual: `pipx install` on clean machine | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_status_cmd.py` -- stubs for STATE-01, STATE-02
- [ ] `tests/test_handoff_cmd.py` -- stubs for STATE-03, STATE-04, STATE-05, STATE-06
- [ ] `tests/test_install_cmd.py` -- stubs for DIST-02, DIST-03, DIST-04, DIST-05, DIST-06
- [ ] `tests/test_clipboard.py` -- stubs for clipboard helper
- [ ] `tests/test_time_utils.py` -- stubs for --since parsing and relative time formatting

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| PyPI install on clean machine | DIST-01 | Requires clean environment + network | `pipx install <package>` on fresh Windows machine, then run `diligent --help` |
| 5-minute onboarding | SC-5 | End-to-end UX with real user | Follow README from scratch on clean machine, time it |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
