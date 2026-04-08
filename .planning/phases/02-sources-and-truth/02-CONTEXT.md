# Phase 2: Sources and Truth - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

Source document registry (`diligent ingest`, `sources list/show/diff`) and the core fact management loop (`truth set/get/list/trace/flag`) with verification gate. The analyst can ingest source documents, record validated facts with citations, and trust that TRUTH.md is the single source of truth with full provenance.

Requirements: SRC-01 through SRC-07, TRUTH-01 through TRUTH-12.

QUESTIONS.md ships in this phase as a seventh state file so the verification gate's reject path has a real destination on day one. Phase 4 builds the CLI surface (`ask`, `answer`, `questions list`) on top of this file.

</domain>

<decisions>
## Implementation Decisions

### Verification gate (TRUTH-04)
- Exit-code gate, not interactive prompt. `truth set` exits non-zero (exit 2) with discrepancy details printed. Analyst re-runs with `--confirm` to accept. No prompt, fully scriptable, compatible with XC-07
- `--confirm` is per-invocation only. No persistent pending state. The analyst re-runs the same `truth set` command with `--confirm` added to force through. If not confirmed, nothing is stored
- Rejection writes directly to QUESTIONS.md with the discrepancy as context. The question captures: key, old value, new value, both source IDs, delta. Phase 4 builds the `ask`/`answer` CLI on top of this file
- Compact diff output on gate fire: key, old value (source, date), new value (source), delta if numeric, one-line verdict. Fits in a terminal without scrolling
- `--json` flag on truth set includes the discrepancy details in structured output when the gate fires

### Gate comparison logic
- Non-anchor facts: exact string match. Any difference in value triggers the gate. No normalization, no "close enough"
- Anchor facts: best-effort numeric parse. Strip currency symbols, commas, percent signs, whitespace, then float(). If both old and new parse as numbers, apply percentage tolerance. If either fails to parse, fall back to exact string match
- Zero-to-nonzero always fires regardless of tolerance (division by zero edge case)
- No-op fast path: if new value is bytewise equal to old value, exit 0 immediately. No supersedes chain write, no gate. Saves time on bulk re-ingestion
- Comparison uses absolute percentage delta: `abs((new - old) / old) * 100`

### Anchor facts (TRUTH-03)
- Explicit `--anchor` flag on `truth set` marks a fact as an anchor metric. Stored as a field in the fact YAML
- `--anchor` is sticky: once set, subsequent updates don't need to repeat the flag. The parser reads it from TRUTH.md
- `--no-anchor` explicitly demotes a fact. Both designation and demotion recorded in supersedes chain
- Global only in v1: one `anchor_tolerance_pct` in config.json, default 0.5%. Per-key overrides deferred to v2 (AN-01)

### Ingest workflow (SRC-01, SRC-07)
- All metadata via flags, no prompts. `diligent ingest <path> --date 2026-04-07 --parties "Seller,Broker" --workstream financial --supersedes ARRIVAL-003 --notes "Q3 update"`
- `--date` defaults to today. Missing optional fields are empty
- Reference only, never copy. SOURCES.md stores relative paths (relative to deal folder root). If the file moves, `doctor` catches the broken reference
- Source IDs generated as `{DEAL_CODE}-{NNN}` (zero-padded, monotonic, from config)

### Excel auto-diff on ingest (SRC-07)
- Summary only on ingest. Compact format: sheets changed, cells differ, rows added/removed, named ranges delta
- Full diff available via `diligent sources diff <old-id> <new-id>` separately
- Summary appears inline as part of ingest output, not as a separate section

### Sources diff (SRC-05, SRC-06)
- Excel (.xlsx/.xls): structured diff via diff_excel_versions.py (sheets, named ranges, cells)
- Word (.docx): text extraction diff via python-docx, paragraph-level. Compact by default (paragraph counts changed, sections added/removed), `--verbose` for actual paragraph-level diff text
- PDF and everything else: "Diff not supported for this format" message. No pdfplumber dependency

### Truth trace (TRUTH-07)
- Timeline format, reverse-chronological, most recent first. Compact by default:
  ```
  current  $20,065   ARRIVAL-019  2026-04-07  Customer_List_v2.xlsx
           $19,665   ARRIVAL-003  2026-03-15  Customer_List.xlsx
  ```
- Summary line at bottom: "N values, N supersedes. Run with --verbose for diffs."
- `--verbose` inlines the compact diff summary (same format as ingest auto-diff) for each value transition. Full diff still via `sources diff`
- Flag events included in timeline (raised, cleared) alongside value changes. Full provenance in one place
- No separate `truth show` command in v1. `truth get` returns current value, `truth trace` covers history

### Truth list (TRUTH-06)
- Three status states per fact: `current` (source is latest, no flag), `flagged` (manually marked for review), `stale` (source has been superseded by a newer ingest but fact not re-validated)
- `--stale` filter shows flagged OR source-superseded facts
- `--workstream` filter scopes to one workstream
- Summary line at bottom: "N facts: N current, N flagged, N stale"
- One line per fact: key, value (truncated), status, source ID. Aligned columns

### QUESTIONS.md (new state file)
- Ships in Phase 2 as a seventh core state file. Reader/writer, init scaffold, doctor check
- Format matches other state files: H2 per question, fenced YAML block with fields (question text, workstream, owner, source context, status, date)
- Update INIT-01: init now scaffolds 7 files, not 6
- Phase 4 builds `ask`/`answer`/`questions list` CLI commands on top of this data layer

### Claude's Discretion
- Source ID counter persistence mechanism (config.json vs SOURCES.md-derived)
- Exact diff_excel_versions.py implementation (openpyxl cell comparison strategy)
- docx diff paragraph extraction approach
- QUESTIONS.md field set and YAML structure (beyond the fields needed for gate rejection)
- `truth flag` internal implementation (how flagged object is structured in YAML)
- Whether `truth list` column widths are fixed or auto-sized

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SourceEntry` model (state/models.py): id, path, date_received, parties, workstream_tags, supersedes, notes. Ready for ingest commands
- `FactEntry` model (state/models.py): key, value, source, date, workstream, supersedes chain, computed_by, notes, flagged. Ready for truth commands
- `read_sources`/`write_sources` (state/sources.py): H2 + fenced YAML reader/writer with atomic_write validation. Handles HTML comments, preserves ordering
- `read_truth`/`write_truth` (state/truth.py): H2 + fenced YAML reader/writer. Values always quoted. Alphabetical sort on write
- `atomic_write` (helpers/io.py): temp file, fsync, os.replace with OneDrive retry and validation callback
- `LazyGroup` CLI scaffold (cli.py): deferred imports, existing command groups for init/doctor/config
- `formatting.py` helper: likely reusable for aligned column output
- `ConfigFile` model: already has `anchor_tolerance_pct` field

### Established Patterns
- H2 + fenced YAML per entry, replicated per state file module (not shared utility, per Phase 1 decision)
- Atomic write with validate_fn that re-parses output before commit
- HTML comment stripping before parsing (templates have commented examples)
- Values always stored as quoted strings to prevent YAML type coercion
- LazyGroup defers imports at group creation for <200ms startup

### Integration Points
- New command groups: `sources` (ingest, list, show, diff) and `truth` (set, get, list, trace, flag) under LazyGroup
- Config: `anchor_tolerance_pct` already exists in ConfigFile model, needs to be read by gate logic
- QUESTIONS.md: new state file needs model, reader/writer, template, init update, doctor checks
- diff_excel_versions.py: helper script in helpers/ directory, called by ingest and sources diff
- FactEntry model may need `anchor: bool` field added for the anchor flag

</code_context>

<specifics>
## Specific Ideas

- Gate output format locked: key, old value (source, date), new value (source), delta if numeric, one-line verdict. Compact, fits terminal
- Truth trace format locked: aligned columns, reverse-chronological, "current" label on top entry, flag events interleaved, summary line at bottom
- Ingest diff summary format locked:
  ```
  Diff vs ARRIVAL-003 (Customer_List_2026-02.xlsx):
    sheets changed: 2 of 4 (Customers, MRR_Detail)
    cells differ:   47
    rows added:     3
    rows removed:   0
    named ranges:   +2, -0

  Run `diligent sources diff ARRIVAL-003 ARRIVAL-019` for full detail.
  ```
- Gate comparison pseudocode locked (includes zero-to-nonzero, parse fallback, no-op fast path)
- The "11 PM Ctrl+F use case" from Phase 1 applies to truth trace: analyst opens terminal, types one command, gets the full story of a fact in 10 seconds
- Relative paths in SOURCES.md (not absolute) so deal folders survive OneDrive sync across machines

</specifics>

<deferred>
## Deferred Ideas

- Per-key tolerance overrides (AN-01) -- v2 requirement, deferred from this discussion
- PDF diff support via pdfplumber -- not worth the dependency cost; sellers replace PDFs wholesale
- `truth show` as a separate command -- `truth get` and `truth trace` cover the use cases
- Glob pattern support for batch ingestion (ING-01) -- v2 requirement

</deferred>

---

*Phase: 02-sources-and-truth*
*Context gathered: 2026-04-07*
