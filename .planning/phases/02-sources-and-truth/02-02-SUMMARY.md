---
phase: 02-sources-and-truth
plan: 02
subsystem: cli
tags: [click, source-registry, ingest, SOURCES.md, monotonic-ids]

# Dependency graph
requires:
  - phase: 02-sources-and-truth/01
    provides: "SourceEntry model, sources.py reader/writer, config.py reader, LazyGroup CLI scaffold"
provides:
  - "diligent ingest command for registering source documents with metadata"
  - "diligent sources list command with aligned column output"
  - "diligent sources show command for full record display"
  - "Monotonic source ID generation (DEAL_CODE-NNN) derived from SOURCES.md max"
affects: [02-sources-and-truth/03, 02-sources-and-truth/04, 02-sources-and-truth/05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Top-level ingest alias alongside sources group in LazyGroup"
    - "Source ID generation reads SOURCES.md max (self-healing, no counter file)"
    - "Relative path resolution via Path.relative_to for cross-platform SOURCES.md"

key-files:
  created:
    - "diligent/diligent/commands/sources_cmd.py"
    - "diligent/tests/test_ingest.py"
    - "diligent/tests/test_sources_cmd.py"
  modified:
    - "diligent/diligent/cli.py"

key-decisions:
  - "ingest registered as top-level LazyGroup command (not only under sources group) matching diligent ingest <path> UX"
  - "Source ID generation scans SOURCES.md entries for max numeric suffix; no counter file, self-healing after manual edits"
  - "Relative paths stored as posix strings via Path.as_posix() for cross-platform SOURCES.md consistency"

patterns-established:
  - "Command group + standalone alias pattern: sources group has list/show, ingest also registered as top-level"
  - "find_diligence_dir helper for .diligence/ discovery reused across subcommands"

requirements-completed: [SRC-01, SRC-02, SRC-03, SRC-04]

# Metrics
duration: 4min
completed: 2026-04-08
---

# Phase 02 Plan 02: Source Registry Commands Summary

**Ingest command with monotonic DEAL_CODE-NNN source IDs, metadata flags, and sources list/show query commands**

## Performance

- **Duration:** 4 min
- **Started:** 2026-04-08T00:54:30Z
- **Completed:** 2026-04-08T00:58:53Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `diligent ingest <path>` registers source documents with auto-generated monotonic IDs
- All metadata flags work: --date, --parties, --workstream, --supersedes, --notes, --json
- `diligent sources list` shows aligned column output with summary line
- `diligent sources show <id>` displays full record for a single source
- Source IDs derived from SOURCES.md max (self-healing after manual edits)
- Paths stored as relative posix strings for cross-platform consistency

## Task Commits

Each task was committed atomically:

1. **Task 1: Ingest command with source ID generation**
   - `2f6417d` (test: failing tests for ingest)
   - `9e23fd8` (feat: implement ingest command)
2. **Task 2: Sources list, show, and CLI registration**
   - `11f4ed7` (test: failing tests for sources list/show)
   - `5449c9d` (feat: implement sources list, show, CLI registration)

## Files Created/Modified
- `diligent/diligent/commands/sources_cmd.py` - Source registry commands: ingest, sources list, sources show
- `diligent/diligent/cli.py` - LazyGroup registration for ingest and sources
- `diligent/tests/test_ingest.py` - 13 tests: metadata, ID generation, relative paths, flags, errors
- `diligent/tests/test_sources_cmd.py` - 11 tests: list empty/populated, show full record, JSON, CLI help

## Decisions Made
- Registered `ingest` as a top-level lazy command (not only under `sources` group) to match the `diligent ingest <path>` UX pattern from the plan's success criteria
- Source ID generation reads max from SOURCES.md entries, not a counter file, making it self-healing after manual edits
- Relative paths stored as posix strings (`Path.as_posix()`) for SOURCES.md cross-platform consistency on OneDrive sync

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Test had `read_sources` import after usage in one test method; fixed inline during GREEN phase (not a plan deviation, just a test authoring bug)

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Source registry complete: ingest, list, show all functional
- Ready for Plan 03 (truth set/get) which references source IDs
- Ready for Plan 04 (sources diff) which extends the sources group

## Self-Check: PASSED

All 4 files verified present. All 4 commits verified in git log.

---
*Phase: 02-sources-and-truth*
*Completed: 2026-04-08*
