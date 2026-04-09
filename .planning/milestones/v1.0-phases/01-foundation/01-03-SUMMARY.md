---
phase: 01-foundation
plan: 03
subsystem: cli
tags: [click, init, doctor, config, tdd, benchmarking, bsl-1.1, cross-cutting]

# Dependency graph
requires:
  - phase: 01-foundation-01
    provides: installable Python package with LazyGroup CLI, typed dataclass models, atomic_write
  - phase: 01-foundation-02
    provides: read/write functions for all 6 state files, template rendering
provides:
  - diligent init command with interactive and non-interactive modes
  - diligent doctor with 3-layer validation (existence, parse, cross-references)
  - diligent config get/set for config.json management
  - editor helper with platform fallback chain for thesis input
  - CLI startup benchmark proving sub-200ms
  - cross-cutting validation tests (no-network, no-prompts, license)
affects: [02-source-mgmt, all-future-phases]

# Tech tracking
tech-stack:
  added: []
  patterns: [non-interactive-cli-flags, 3-layer-validation, fenced-yaml-integrity-check, type-coercion-config]

key-files:
  created:
    - Diligent/diligent/commands/init_cmd.py
    - Diligent/diligent/commands/doctor.py
    - Diligent/diligent/commands/config_cmd.py
    - Diligent/diligent/helpers/editor.py
    - Diligent/diligent/__main__.py
    - Diligent/tests/test_init.py
    - Diligent/tests/test_doctor.py
    - Diligent/tests/test_config.py
    - Diligent/tests/test_cli_startup.py
    - Diligent/tests/test_json_output.py
    - Diligent/tests/test_no_network.py
    - Diligent/tests/test_no_prompts.py
    - Diligent/tests/test_license.py
  modified:
    - Diligent/pyproject.toml

key-decisions:
  - "Doctor performs deep fenced YAML integrity check beyond what read_truth returns, catching corrupt entries the reader silently skips"
  - "Config set uses type coercion: int first, then float, then string -- no explicit type flag needed"
  - "Added __main__.py for python -m diligent support, enabling subprocess-based startup benchmark"

patterns-established:
  - "Non-interactive mode: --non-interactive flag requires all fields, fails with clear error on missing"
  - "3-layer doctor validation: existence, parse, cross-references with structured findings"
  - "Config type coercion: CLI string values auto-coerced to int/float/string"

requirements-completed: [INIT-01, INIT-03, INIT-04, INIT-08, XC-03, XC-06, XC-07, XC-08]

# Metrics
duration: 7min
completed: 2026-04-07
---

# Phase 1 Plan 03: CLI Commands Summary

**Init, doctor, and config commands with 3-layer validation, startup benchmark under 200ms, and cross-cutting tests for no-network/no-prompts/license**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-07T23:36:19Z
- **Completed:** 2026-04-07T23:44:18Z
- **Tasks:** 2
- **Files modified:** 14

## Accomplishments
- diligent init with 12 CLI flags, interactive prompts, non-interactive mode, deal code validation (A-Z, 3-12 chars), and .diligence/ scaffolding of all 6 state files
- diligent doctor with 3-layer validation (existence, parse, cross-references), deep fenced YAML integrity check, --json and --strict flags
- diligent config get/set with type coercion (int, float, string), --json output
- 52 new tests (110 total), 82% coverage, all passing
- CLI startup under 200ms confirmed via subprocess benchmark
- Cross-cutting tests: no network imports (XC-03), no stdin prompts except init (XC-07), BSL license present (XC-08)

## Task Commits

Each task was committed atomically:

1. **Task 1: diligent init with interactive and non-interactive modes** - `97c2309` (feat)
2. **Task 2: doctor, config, startup benchmark, and cross-cutting tests** - `6fd859d` (feat)

_Both tasks followed TDD: RED (failing tests) -> GREEN (implementation) -> verify._

## Files Created/Modified
- `Diligent/diligent/commands/init_cmd.py` - Full init command replacing stub, 12 flags, validation, template rendering
- `Diligent/diligent/commands/doctor.py` - Full doctor command replacing stub, 3-layer validation, structured findings
- `Diligent/diligent/commands/config_cmd.py` - Full config group replacing stub, get/set subcommands with type coercion
- `Diligent/diligent/helpers/editor.py` - Editor invocation for thesis input, platform fallback chain
- `Diligent/diligent/__main__.py` - Module entry point for python -m diligent
- `Diligent/pyproject.toml` - Added slow pytest marker registration
- `Diligent/tests/test_init.py` - 17 tests: creation, validation, idempotency, JSON output
- `Diligent/tests/test_doctor.py` - 11 tests: clean deal, missing files, corrupt YAML, cross-refs, --strict, --json
- `Diligent/tests/test_config.py` - 9 tests: get, set, type coercion, JSON output, nonexistent key error
- `Diligent/tests/test_cli_startup.py` - 1 benchmark test: --help under 200ms (3-run average)
- `Diligent/tests/test_json_output.py` - 6 tests: valid JSON output for init, doctor, config; --help mentions --json
- `Diligent/tests/test_no_network.py` - 1 static analysis test: no network imports in diligent source
- `Diligent/tests/test_no_prompts.py` - 4 tests: doctor, config get, config set, migrate complete without stdin
- `Diligent/tests/test_license.py` - 3 tests: LICENSE exists, contains BSL text, contains Bryce Masterson

## Decisions Made
- Doctor performs a deep fenced YAML integrity check separate from the reader modules. The readers silently skip unparseable YAML blocks (returning zero entries), but doctor needs to report those as errors. This is a deliberate separation: readers are tolerant, doctor is strict.
- Config set uses simple type coercion (try int, then float, then keep string) rather than requiring an explicit --type flag. This keeps the CLI simple for the primary use case (setting numeric values like recent_window_days).
- Added __main__.py to support `python -m diligent --help` in the startup benchmark test. The alternative (using subprocess with the installed console_script) was less portable across test environments.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added __main__.py for module invocation**
- **Found during:** Task 2 (startup benchmark test)
- **Issue:** `python -m diligent --help` failed because no __main__.py existed
- **Fix:** Created diligent/__main__.py importing and invoking cli()
- **Files modified:** Diligent/diligent/__main__.py
- **Verification:** Startup benchmark test passes
- **Committed in:** 6fd859d

**2. [Rule 2 - Missing Critical] Deep fenced YAML integrity check in doctor**
- **Found during:** Task 2 (doctor corrupt file test)
- **Issue:** read_truth silently skips YAML blocks that fail to parse, returning zero facts. Doctor saw no parse error.
- **Fix:** Added _check_fenced_yaml_integrity() that walks H2 sections and individually validates each fenced YAML block, reporting errors the reader skips.
- **Files modified:** Diligent/diligent/commands/doctor.py
- **Verification:** test_corrupt_truth_md_parse_error passes
- **Committed in:** 6fd859d

---

**Total deviations:** 2 auto-fixed (2 missing critical)
**Impact on plan:** Both fixes were necessary for correctness. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None -- no external service configuration required.

## Next Phase Readiness
- Phase 1 complete: all 3 plans delivered, full CLI scaffold with state layer
- Init scaffolds deal folders, doctor validates integrity, config manages settings
- 110 tests as regression safety net for Phase 2 (source management)
- Cross-cutting constraints verified: no network, no prompts (except init), BSL license
- All 6 state files have read/write/template support with atomic writes and validation

## Self-Check: PASSED

All 13 key files verified present. Both task commits (97c2309, 6fd859d) confirmed in git log.

---
*Phase: 01-foundation*
*Completed: 2026-04-07*
