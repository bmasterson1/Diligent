---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-07
---

# Phase 1 -- Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` |
| **Quick run command** | `pytest tests/ -x --tb=short` |
| **Full suite command** | `pytest tests/ --cov=diligent --cov-report=term-missing` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x --tb=short`
- **After every plan wave:** Run `pytest tests/ --cov=diligent --cov-report=term-missing`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | INIT-05 | smoke | `hatch build` | Wave 0 | pending |
| 01-02-01 | 02 | 1 | INIT-02 | unit | `pytest tests/test_state_roundtrip.py -x` | Wave 0 | pending |
| 01-02-02 | 02 | 1 | INIT-06 | unit | `pytest tests/test_atomic_write.py -x` | Wave 0 | pending |
| 01-02-03 | 02 | 1 | XC-05 | unit | `pytest tests/test_atomic_write.py::test_validation_failure -x` | Wave 0 | pending |
| 01-03-01 | 03 | 2 | INIT-01 | integration | `pytest tests/test_init.py -x` | Wave 0 | pending |
| 01-03-02 | 03 | 2 | INIT-04 | unit | `pytest tests/test_config.py -x` | Wave 0 | pending |
| 01-03-03 | 03 | 2 | INIT-07 | unit | `pytest tests/test_config.py::test_schema_version -x` | Wave 0 | pending |
| 01-03-04 | 03 | 2 | INIT-03 | integration | `pytest tests/test_doctor.py -x` | Wave 0 | pending |
| 01-03-05 | 03 | 2 | INIT-08 | benchmark | `pytest tests/test_cli_startup.py -x` | Wave 0 | pending |
| 01-03-06 | 03 | 2 | XC-03 | unit | `pytest tests/test_no_network.py -x` | Wave 0 | pending |
| 01-03-07 | 03 | 2 | XC-06 | integration | `pytest tests/test_json_output.py -x` | Wave 0 | pending |
| 01-03-08 | 03 | 2 | XC-07 | integration | `pytest tests/test_no_prompts.py -x` | Wave 0 | pending |
| 01-03-09 | 03 | 2 | XC-08 | smoke | `pytest tests/test_license.py -x` | Wave 0 | pending |
| 01-03-10 | 03 | 2 | XC-04 | architectural | Manual review + test assertions | Wave 0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` -- shared fixtures (tmp_path deal folder, pre-populated .diligence/)
- [ ] `tests/test_state_roundtrip.py` -- covers INIT-02
- [ ] `tests/test_atomic_write.py` -- covers INIT-06, XC-05
- [ ] `tests/test_init.py` -- covers INIT-01
- [ ] `tests/test_doctor.py` -- covers INIT-03
- [ ] `tests/test_config.py` -- covers INIT-04, INIT-07
- [ ] `tests/test_cli_startup.py` -- covers INIT-08
- [ ] `tests/test_json_output.py` -- covers XC-06
- [ ] `tests/test_no_network.py` -- covers XC-03
- [ ] `tests/test_no_prompts.py` -- covers XC-07
- [ ] `tests/test_license.py` -- covers XC-08
- [ ] `pyproject.toml` -- pytest config section
- [ ] Framework install: `pip install pytest pytest-cov`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Source documents read-only | XC-04 | Architectural constraint, not a runtime check | Review code for write operations on source docs; add assertion tests |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
