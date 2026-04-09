---
phase: 3
slug: artifacts-reconciliation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-08
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.0+ |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/ -x -q` |
| **Full suite command** | `python -m pytest tests/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 0 | ART-02 | unit | `python -m pytest tests/test_artifacts_state.py::TestArtifactsRoundTrip -x` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 0 | ART-01 | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactRegister -x` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 0 | ART-01 | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactRegisterUpsert -x` | ❌ W0 | ⬜ pending |
| 03-01-04 | 01 | 0 | ART-03 | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactList -x` | ❌ W0 | ⬜ pending |
| 03-01-05 | 01 | 0 | ART-04 | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactRefresh -x` | ❌ W0 | ⬜ pending |
| 03-01-06 | 01 | 0 | ART-08 | unit | `python -m pytest tests/test_reconcile_engine.py -x` | ❌ W0 | ⬜ pending |
| 03-01-07 | 01 | 0 | ART-05 | unit | `python -m pytest tests/test_reconcile.py::TestReconcileValueChanged -x` | ❌ W0 | ⬜ pending |
| 03-01-08 | 01 | 0 | ART-05 | unit | `python -m pytest tests/test_reconcile.py::TestReconcileSourceSuperseded -x` | ❌ W0 | ⬜ pending |
| 03-01-09 | 01 | 0 | ART-06 | unit | `python -m pytest tests/test_reconcile.py::TestReconcileWorkstream -x` | ❌ W0 | ⬜ pending |
| 03-01-10 | 01 | 0 | ART-07 | unit | `python -m pytest tests/test_reconcile.py::TestReconcileStrict -x` | ❌ W0 | ⬜ pending |
| 03-01-11 | 01 | 0 | ART-09 | unit | `python -m pytest tests/test_artifact_scanner.py -x` | ❌ W0 | ⬜ pending |
| 03-01-12 | 01 | 0 | XC-01 | integration | `python -m pytest tests/test_performance.py::test_artifact_commands_under_2s -x` | ❌ W0 | ⬜ pending |
| 03-01-13 | 01 | 0 | XC-02 | integration | `python -m pytest tests/test_performance.py::test_reconcile_under_10s -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_artifacts_state.py` — stubs for ART-02 (round-trip read/write)
- [ ] `tests/test_artifact_cmd.py` — stubs for ART-01, ART-03, ART-04 (CLI commands)
- [ ] `tests/test_reconcile_engine.py` — stubs for ART-08 (pure function engine)
- [ ] `tests/test_reconcile.py` — stubs for ART-05, ART-06, ART-07 (CLI reconcile)
- [ ] `tests/test_artifact_scanner.py` — stubs for ART-09 (docx scanner)
- [ ] `tests/test_performance.py` — stubs for XC-01, XC-02 (performance benchmarks)

---

## Manual-Only Verifications

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
