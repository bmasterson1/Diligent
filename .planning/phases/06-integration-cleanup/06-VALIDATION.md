---
phase: 6
slug: integration-cleanup
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest >=8.0 |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` (if present) or pytest defaults |
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
| 06-01-01 | 01 | 1 | SRC-01, SRC-03, SRC-04, SRC-05 | integration | `python -m pytest tests/test_sources_cmd.py -x -k "subdir or parent or env_cwd"` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | STATE-05 | integration | `python -m pytest tests/test_status_cmd.py -x -k "window"` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | TASK-03, DIST-05 | unit | `python -m pytest tests/test_install_cmd.py -x -k "skill"` | ⚠️ partial | ⬜ pending |
| 06-01-04 | 01 | 1 | SRC-01 | unit | `python -m pytest tests/test_reconcile.py -x -k "flagged_reason"` | ❌ W0 | ⬜ pending |
| 06-01-05 | 01 | 1 | — | docs | visual diff of REQUIREMENTS.md wording | N/A manual | ⬜ pending |
| 06-01-06 | 01 | 1 | STATE-05 | unit | `python -m pytest tests/test_state_file.py -x -k "write_state"` | ⚠️ partial | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_sources_cmd.py` — add tests for DILIGENT_CWD and parent-dir walk (new test functions in existing file)
- [ ] `tests/test_status_cmd.py` — add test verifying config.recent_window_days is read (new test function in existing file)
- [ ] `tests/test_reconcile.py` — add test for flagged reason display text (new test function in existing file)

*Existing infrastructure covers framework and fixtures. Only new test functions needed in existing files.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| REQUIREMENTS.md wording for ART-02 and ART-09 | — | Documentation review | Visual diff: verify wording matches actual implementation (ARTIFACTS.md, auto-scan) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
