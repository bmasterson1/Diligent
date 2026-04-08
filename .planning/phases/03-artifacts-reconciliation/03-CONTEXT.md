# Phase 3: Artifacts and Reconciliation - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliverable tracking (`diligent artifact register`, `artifact list`, `artifact refresh`) and the dependency-graph staleness engine (`diligent reconcile`). The analyst types one command and gets a definitive answer about which deliverables are stale and why.

Requirements: ART-01 through ART-09, XC-01, XC-02.

ARTIFACTS.md ships in this phase as an 8th core state file (joining DEAL.md, TRUTH.md, SOURCES.md, WORKSTREAMS.md, STATE.md, QUESTIONS.md, config.json). Init scaffolds it at deal creation time. ART-02 updated from manifest.json to ARTIFACTS.md (H2 + YAML pattern).

</domain>

<decisions>
## Implementation Decisions

### Reconcile output format
- Grouped by artifact. Each stale artifact is a section, listing its stale facts underneath
- Within an artifact group, facts ordered most recently changed first
- Compact one-liner per fact: key, old value arrow new value, source ID, (Xd stale), aligned columns
  ```
  customer_253_mrr     $19,665 -> $20,065   ARRIVAL-019   (4d stale)
  t12m_retained        491 -> 492           ARRIVAL-020   (1d stale)
  ```
- `--verbose` flag: two-line format with source filename and date on second line
- Default output shows only stale and advisory artifacts. `--all` flag shows every registered artifact with status markers (CURRENT, STALE, ADVISORY)
- Summary line at bottom, counts only: "3 artifacts stale, 5 facts changed, 12 artifacts current"
- Exit code: 0 if all current, non-zero if any stale. `--strict` elevates flagged facts to non-zero as well

### Staleness definition (two triggers, layered)
- **Value changed**: artifact is stale when any referenced fact's value was updated via `truth set` after the artifact's last refresh timestamp. Direct dependency chain: fact changed, artifact needs update
- **Source superseded**: artifact is stale when any referenced fact's source was superseded by a newer ingest, but the fact has not yet been re-validated against the new source. Catches the window between "new source ingested" and "facts re-validated"
- Source-superseded only fires for supersedes events that happened AFTER the artifact's last refresh timestamp. No false positives from historical supersedes
- Two sub-sections per stale artifact in reconcile output: "value changed" (actionable, regenerate artifact) and "source superseded" (pending, re-validate facts first then regenerate)
- **Flagged facts**: separate third sub-section ("flagged facts"), advisory only. Does not mark the artifact stale. Does not affect exit code unless `--strict`

### Artifact register workflow
- `--references key1,key2,key3` comma-separated inline. Single flag
- Re-registering an existing artifact: upsert with `--confirm` flag (exit-code gate pattern matching truth set). Shows current references, exits non-zero without `--confirm`
- Truth key validation: check each referenced key against TRUTH.md at registration time. Warn on missing keys (registration succeeds with warning). Doctor catches broken references later
- **Docx scanning (ART-09)**: scanner runs by default on .docx registrations, no `--scan` flag. `--references` is always authoritative when provided. If analyst passes `--references`, those are stored; scanner still runs and prints advisory suggestions for any additional keys it found ("scanner also found these keys you didn't list: ..."). If no `--references` provided, scanner runs and asks analyst to confirm found keys
- `scanner_findings` field in ARTIFACTS.md records what the scanner found but the analyst didn't confirm. Advisory information for reconcile to optionally surface
- Non-docx files: scanner does not run. `--references` is the only path

### Manifest storage format (ART-02 updated)
- **ARTIFACTS.md** (H2 + fenced YAML), not manifest.json. Consistent with all other state files
- H2 heading = relative path from deal folder root, forward slashes on all platforms (diligent normalizes path separators on write)
- Fields per artifact: workstream, registered, last_refreshed, references (list), scanner_findings (list), notes
- Init scaffolds ARTIFACTS.md as the 8th core state file with HTML comment template
- Doctor validates ARTIFACTS.md presence and structural integrity, including cross-file reference checks (truth keys exist in TRUTH.md, paths exist on disk)
- Parser follows the same H2 + fenced YAML walker pattern as fact_parser.py

### Claude's Discretion
- reconcile_anchors.py internal implementation (dependency graph walk algorithm)
- artifact_scanner.py docx parsing approach (python-docx paragraph walking, regex for citation tags)
- Exact column alignment widths in reconcile output
- How `artifact refresh` updates last_refreshed (simple timestamp update, no validation beyond confirming artifact exists)
- Whether the H2+YAML walker logic is extracted as shared utility or replicated per module (Phase 1 decision was replicate, but 8 files may justify extraction)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `FactEntry` model (state/models.py): has supersedes chain, source, date, anchor, flagged fields -- reconcile reads all of these
- `SourceEntry` model (state/models.py): has supersedes field for source-superseded staleness detection
- `read_truth`/`write_truth` (state/truth.py): H2 + fenced YAML reader/writer. ARTIFACTS.md parser will follow same pattern
- `read_sources` (state/sources.py): needed by reconcile to walk supersedes chains
- `atomic_write` (helpers/io.py): temp file, fsync, os.replace with OneDrive retry and validation callback
- `formatting.py` helper: output_result for --json, output_findings for diagnostic output
- `LazyGroup` CLI scaffold (cli.py): artifact and reconcile command groups register here
- `numeric.py` helper: numeric comparison logic, potentially reusable for staleness date calculations
- `strip_html_comments` (state/truth.py): reusable for ARTIFACTS.md template parsing

### Established Patterns
- H2 + fenced YAML per entry, replicated per state file module (not shared utility)
- Atomic write with validate_fn that re-parses output before commit
- Exit-code gate pattern: command exits non-zero with details, analyst re-runs with --confirm
- LazyGroup defers imports at group creation for <200ms startup
- Relative paths stored as posix strings for cross-platform OneDrive sync
- HTML comment stripping before parsing (templates have commented examples)

### Integration Points
- New command groups: `artifact` (register, list, refresh) and `reconcile` (top-level) under LazyGroup
- New state file: ARTIFACTS.md needs model (ArtifactEntry), reader/writer, template, init update, doctor checks
- Init scaffold: update from 7 to 8 files (ARTIFACTS.md added)
- Doctor: add ARTIFACTS.md structural validation + cross-file reference checks (truth keys, disk paths)
- reconcile reads TRUTH.md, SOURCES.md, and ARTIFACTS.md to build dependency graph

</code_context>

<specifics>
## Specific Ideas

- Reconcile output format locked: compact one-liner with aligned columns, arrow transition, source ID, days stale in parens. Reads left-to-right as "what changed, where it came from, how urgent"
- Two-category staleness in reconcile output: "value changed" = actionable (regenerate now), "source superseded" = pending (re-validate facts first). Different next actions, different urgency, shown separately
- The analyst's order of operations for fixing reconcile output: resolve source-superseded items first (run truth set against new source), then regenerate artifacts against the updated value-changed list
- ARTIFACTS.md format example locked:
  ```
  ## deliverables/retention/retention_analysis_v9.docx
  ```yaml
  workstream: "retention"
  registered: "2026-03-22"
  last_refreshed: "2026-03-22"
  references:
    - customer_253_mrr
    - t12m_cohort
    - t12m_retained
    - ndr_pct
  scanner_findings:
    - revenue_growth_yoy
    - gross_margin_pct
  notes: ""
  ```
- Scanner-as-default on docx: no --scan flag. Scanner runs automatically, --references is authoritative override. Scanner findings stored separately from references in ARTIFACTS.md
- reconcile --all for full artifact inventory. Default shows only stale/advisory. Matches compact-by-default-with-flag-for-detail pattern

</specifics>

<deferred>
## Deferred Ideas

- Shared H2+YAML walker utility extraction (8 files may justify it, but Phase 1 decision was replicate per module)
- Per-key tolerance overrides affecting artifact staleness thresholds (AN-01, v2)
- .pptx and .xlsx scanner support (DOC-02, v2)
- Auto-suggest which facts an ingested document might affect (ING-02, v2)

</deferred>

---

*Phase: 03-artifacts-reconciliation*
*Context gathered: 2026-04-08*
