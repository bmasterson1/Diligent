---
phase: 01-foundation
plan: 01
subsystem: cli
tags: [click, dataclasses, atomic-write, lazygroup, bsl-1.1]

# Dependency graph
requires:
  - phase: none
    provides: greenfield project
provides:
  - installable Python package with diligent CLI entry point
  - typed dataclass models for all 6 state file types
  - atomic_write utility with OneDrive retry and validation gate
  - LazyGroup CLI shell with lazy subcommand loading
  - migrate stub command for future schema migrations
  - formatting helpers for dual plain text / JSON output
  - BSL 1.1 license
affects: [01-02, 01-03, all-future-plans]

# Tech tracking
tech-stack:
  added: [click-8.1, pyyaml-6.0, python-frontmatter-1.1, hatchling, pytest-8, pytest-cov-5]
  patterns: [LazyGroup-CLI, atomic-write-with-retry, stdlib-dataclasses, TDD]

key-files:
  created:
    - Diligent/pyproject.toml
    - Diligent/LICENSE
    - Diligent/diligent/__init__.py
    - Diligent/diligent/cli.py
    - Diligent/diligent/state/models.py
    - Diligent/diligent/state/config.py
    - Diligent/diligent/helpers/io.py
    - Diligent/diligent/helpers/formatting.py
    - Diligent/diligent/commands/migrate_cmd.py
    - Diligent/diligent/commands/init_cmd.py
    - Diligent/diligent/commands/doctor.py
    - Diligent/diligent/commands/config_cmd.py
    - Diligent/tests/conftest.py
    - Diligent/tests/test_models.py
    - Diligent/tests/test_atomic_write.py
  modified: []

key-decisions:
  - "LazyGroup defers command module imports until invocation, not until help display (Click 8.x calls get_command for help strings)"
  - "Stub command modules created for init, doctor, config to allow CLI help to resolve"
  - "fd ownership tracked explicitly in atomic_write to handle fdopen failure cleanup on Windows"
  - "CliRunner mix_stderr parameter removed (deprecated in Click 8.3)"

patterns-established:
  - "LazyGroup CLI: all subcommands registered via lazy_subcommands dict, imports deferred"
  - "Atomic write: tempfile.mkstemp in same dir, fsync, os.replace with retry loop"
  - "Stdlib dataclasses for all models: no pydantic, no external validation library"
  - "TDD: tests written first, then implementation, verified green before commit"

requirements-completed: [INIT-05, INIT-06, INIT-07, INIT-08, XC-03, XC-05, XC-08]

# Metrics
duration: 7min
completed: 2026-04-07
---

# Phase 1 Plan 01: Package Scaffold Summary

**Installable Python package with LazyGroup CLI, typed dataclass models for all 6 state files, and atomic_write with OneDrive retry/validation gate**

## Performance

- **Duration:** 7 min
- **Started:** 2026-04-07T23:13:15Z
- **Completed:** 2026-04-07T23:20:43Z
- **Tasks:** 2
- **Files modified:** 18

## Accomplishments
- Installable Python package (`pip install -e ".[dev]"`) with `diligent --help` working via LazyGroup
- All 6 state file types defined as stdlib dataclasses: DealFile, TruthFile, SourcesFile, WorkstreamsFile, StateFile, ConfigFile
- Atomic write utility handles normal write, OneDrive PermissionError retry with exponential backoff, validation gate, and temp file cleanup on all failure paths
- BSL 1.1 license with Additional Use Grant for individual non-commercial use
- 32 tests passing across models, CLI, migrate stub, and atomic write

## Task Commits

Each task was committed atomically:

1. **Task 1: Package scaffold, models, LazyGroup CLI, migrate stub** - `7e82d46` (feat)
2. **Task 2: Atomic write with OneDrive retry and validation** - `89f2068` (feat)

_Both tasks followed TDD: RED (failing tests) -> GREEN (implementation) -> verify._

## Files Created/Modified
- `Diligent/pyproject.toml` - hatchling build config, BSL 1.1 license, console_scripts entry point
- `Diligent/LICENSE` - Full BSL 1.1 license text
- `Diligent/diligent/__init__.py` - Package version (0.1.0)
- `Diligent/diligent/cli.py` - LazyGroup CLI entry point with 4 lazy subcommands
- `Diligent/diligent/state/models.py` - Dataclass definitions for all 6 state file types (10 classes)
- `Diligent/diligent/state/config.py` - config.json reader/writer using atomic_write
- `Diligent/diligent/helpers/io.py` - Atomic write with OneDrive retry and validation gate
- `Diligent/diligent/helpers/formatting.py` - Dual output (plain text + JSON) helpers
- `Diligent/diligent/commands/migrate_cmd.py` - Stub migrate command (reads schema_version)
- `Diligent/diligent/commands/init_cmd.py` - Stub init command (placeholder for plan 01-03)
- `Diligent/diligent/commands/doctor.py` - Stub doctor command (placeholder for plan 01-03)
- `Diligent/diligent/commands/config_cmd.py` - Stub config command (placeholder for plan 01-03)
- `Diligent/tests/conftest.py` - Shared fixtures: tmp_deal_dir, diligence_dir, cli_runner, sample_config
- `Diligent/tests/test_models.py` - 16 tests for models, CLI, LazyGroup, migrate
- `Diligent/tests/test_atomic_write.py` - 16 tests for atomic write utility

## Decisions Made
- LazyGroup defers imports at group creation time but Click 8.x's help formatter calls get_command() to extract short help text, so modules do get imported during `--help`. The real value is deferring heavy deps (openpyxl, pdfplumber) until command invocation.
- Created stub command modules for init, doctor, config so LazyGroup can resolve all subcommands during help display. Full implementations come in plan 01-03.
- Track fd ownership explicitly in atomic_write to handle the edge case where os.fdopen fails (the raw fd must be closed before temp file can be unlinked on Windows).
- Removed Click CliRunner `mix_stderr=False` parameter (deprecated/removed in Click 8.3.x).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] CliRunner mix_stderr parameter removed**
- **Found during:** Task 1
- **Issue:** Click 8.3.x removed the `mix_stderr` parameter from CliRunner.__init__()
- **Fix:** Changed `CliRunner(mix_stderr=False)` to `CliRunner()` in conftest.py
- **Files modified:** Diligent/tests/conftest.py
- **Verification:** All CLI tests pass
- **Committed in:** 7e82d46

**2. [Rule 3 - Blocking] Created stub command modules for init, doctor, config**
- **Found during:** Task 1
- **Issue:** LazyGroup could not resolve commands during --help because init_cmd, doctor, and config_cmd modules did not exist
- **Fix:** Created minimal stub click commands that print "not yet implemented" messages
- **Files modified:** Diligent/diligent/commands/init_cmd.py, doctor.py, config_cmd.py
- **Verification:** `diligent --help` lists all four subcommands
- **Committed in:** 7e82d46

**3. [Rule 1 - Bug] Fixed LazyGroup import test to match Click 8.x behavior**
- **Found during:** Task 1
- **Issue:** Test asserted command modules not imported during --help, but Click 8.x calls get_command() for help text extraction. The real property to test is that modules are not imported at group creation time.
- **Fix:** Rewrote test to verify list_commands returns names without importing modules
- **Files modified:** Diligent/tests/test_models.py
- **Verification:** Test correctly validates lazy behavior
- **Committed in:** 7e82d46

**4. [Rule 2 - Missing Critical] Added .gitignore**
- **Found during:** Task 2
- **Issue:** No .gitignore existed; __pycache__ and build artifacts would be committed
- **Fix:** Created .gitignore excluding __pycache__, .pyc, egg-info, dist, build, .pytest_cache, .tmp, .coverage
- **Files modified:** Diligent/.gitignore
- **Verification:** git status no longer shows __pycache__ dirs
- **Committed in:** 89f2068

**5. [Rule 1 - Bug] Fixed fd leak in atomic_write on fdopen failure**
- **Found during:** Task 2
- **Issue:** When os.fdopen raised an exception, the raw file descriptor from mkstemp was never closed, preventing temp file cleanup on Windows
- **Fix:** Track fd_closed flag; if fdopen fails, explicitly os.close(fd) before os.unlink(tmp_path)
- **Files modified:** Diligent/diligent/helpers/io.py
- **Verification:** test_cleans_up_on_write_failure passes (no temp files left behind)
- **Committed in:** 89f2068

---

**Total deviations:** 5 auto-fixed (2 bugs, 1 blocking, 1 missing critical, 1 bug)
**Impact on plan:** All auto-fixes necessary for correctness and test infrastructure. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviations above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Package scaffold complete: all subsequent plans can import from `diligent.*`
- Models defined: plan 01-02 (state readers/writers) can implement serialization for all 6 types
- Atomic write ready: every state mutation in plans 01-02 and 01-03 uses this utility
- LazyGroup CLI shell ready: plan 01-03 fills in the real init, doctor, config commands
- Test infrastructure established: conftest fixtures, TDD pattern, 32 tests as baseline

## Self-Check: PASSED

All 12 key files verified present. Both task commits (7e82d46, 89f2068) confirmed in git log.

---
*Phase: 01-foundation*
*Completed: 2026-04-07*
