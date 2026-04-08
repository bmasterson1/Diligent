---
phase: 02-sources-and-truth
plan: 05
subsystem: cli
tags: [openpyxl, python-docx, excel-diff, docx-diff, lazy-import, sources-diff]

# Dependency graph
requires:
  - phase: 02-sources-and-truth/02
    provides: "ingest command, sources list/show, SOURCES.md reader/writer, monotonic source IDs"
provides:
  - "diff_excel_summary for structured Excel file comparison (sheets, cells, rows, named ranges)"
  - "diff_docx_summary and diff_docx_verbose for paragraph-level Word document comparison"
  - "diligent sources diff <id-a> <id-b> command with --json and --verbose"
  - "Ingest auto-diff: compact Excel diff summary on --supersedes"
affects: []

# Tech tracking
tech-stack:
  added: [openpyxl, python-docx]
  patterns:
    - "Lazy-import pattern for heavy dependencies (import inside function body, not module top)"
    - "Compact diff output format locked from CONTEXT.md for consistency"
    - "Auto-diff on ingest wrapped in try/except to never block ingest flow"

key-files:
  created:
    - "diligent/diligent/helpers/diff_excel.py"
    - "diligent/diligent/helpers/diff_docx.py"
    - "diligent/tests/test_diff_excel.py"
    - "diligent/tests/test_sources_diff.py"
  modified:
    - "diligent/diligent/commands/sources_cmd.py"
    - "diligent/pyproject.toml"

key-decisions:
  - "openpyxl DefinedNameDict API uses .keys() not .definedName attribute in openpyxl 3.1.5+"
  - "Test fixtures created programmatically in tmp_path (no binary fixtures in git)"
  - "Excel diff uses read_only=True, data_only=True for low memory usage"
  - "Auto-diff only fires for Excel files on ingest, not Word or other formats (per CONTEXT.md)"

patterns-established:
  - "Lazy-import pattern: heavy libraries imported inside function bodies, verified by sys.modules test"
  - "Compact diff output format: locked format with aligned labels for terminal display"
  - "Auto-diff on ingest: wrapped in try/except, prints warning but never blocks"

requirements-completed: [SRC-05, SRC-06, SRC-07]

# Metrics
duration: 5min
completed: 2026-04-08
---

# Phase 02 Plan 05: Document Diff Helpers and Sources Diff Command Summary

**Excel and Word diff helpers with lazy imports, sources diff command, and ingest auto-diff on --supersedes**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-08T01:12:16Z
- **Completed:** 2026-04-08T01:17:30Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- diff_excel_summary compares two Excel files returning structured sheet/cell/row/named-range differences
- diff_docx_summary compares two Word documents returning paragraph-level difference counts
- `diligent sources diff <id-a> <id-b>` shows structured diff, dispatched by file type
- Ingest auto-diffs Excel files when --supersedes is provided, with compact inline summary
- openpyxl and python-docx are lazy-imported (never at module top level)
- Unsupported formats get "Diff not supported for {ext} files" message

## Task Commits

Each task was committed atomically:

1. **Task 1: Excel and Word diff helpers + test fixtures**
   - `9132ad7` (test: failing tests for diff helpers)
   - `c81ae2f` (feat: implement Excel and Word diff helpers)
2. **Task 2: Sources diff command + ingest auto-diff integration**
   - `b7f1a6c` (test: failing tests for sources diff and ingest auto-diff)
   - `09b063d` (feat: sources diff command and ingest auto-diff)

## Files Created/Modified
- `diligent/diligent/helpers/diff_excel.py` - diff_excel_summary: structured Excel comparison via openpyxl
- `diligent/diligent/helpers/diff_docx.py` - diff_docx_summary + diff_docx_verbose: paragraph-level Word comparison
- `diligent/diligent/commands/sources_cmd.py` - sources diff subcommand, ingest auto-diff, format helpers
- `diligent/pyproject.toml` - Added openpyxl>=3.1.5 and python-docx>=1.1.0 dependencies
- `diligent/tests/test_diff_excel.py` - 15 tests: Excel/Word diff, lazy imports, fixture validity
- `diligent/tests/test_sources_diff.py` - 12 tests: sources diff command, ingest auto-diff, error cases

## Decisions Made
- Used openpyxl DefinedNameDict.keys() API instead of .definedName attribute (API changed in 3.1.5+)
- Test fixtures created programmatically in tmp_path with pytest fixtures, avoiding binary files in git
- Auto-diff only fires for Excel-to-Excel comparisons on ingest (Word and other formats skipped per CONTEXT.md)
- Excel workbooks opened with read_only=True, data_only=True for minimal memory footprint

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed openpyxl defined_names API call**
- **Found during:** Task 1 (Excel diff helper implementation)
- **Issue:** Plan referenced `.definedName` attribute on openpyxl workbook, but openpyxl 3.1.5 uses DefinedNameDict which exposes `.keys()` instead
- **Fix:** Changed `{dn.name for dn in wb.defined_names.definedName}` to `set(wb.defined_names.keys())`
- **Files modified:** diligent/diligent/helpers/diff_excel.py
- **Verification:** All 15 diff tests pass
- **Committed in:** c81ae2f

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minor API adaptation. No scope creep.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 2 complete: all 5 plans executed
- Source registry fully operational: ingest, list, show, diff
- Truth management fully operational: set, get, list, trace, flag
- Verification gate functional with anchor tolerance
- Ready for Phase 3

## Self-Check: PASSED

All 6 files verified present. All 4 commits verified in git log.

---
*Phase: 02-sources-and-truth*
*Completed: 2026-04-08*
