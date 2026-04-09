# Phase 2: Sources and Truth - Research

**Researched:** 2026-04-07
**Domain:** Source document registry, fact management with verification gate, Excel/Word diffing
**Confidence:** HIGH

## Summary

Phase 2 builds the two core command groups (`sources` and `truth`) on top of the state layer established in Phase 1. The existing `SourceEntry`, `FactEntry`, and `SupersededValue` models are already defined in `state/models.py`. The `read_sources`/`write_sources` and `read_truth`/`write_truth` functions are working with atomic writes and validation callbacks. The `ConfigFile` model already has `anchor_tolerance_pct`. The LazyGroup pattern in `cli.py` is ready to accept new command groups.

The primary complexity lives in three areas: (1) the verification gate on `truth set` with its numeric parsing, tolerance comparison, exit-code-based flow, and `--confirm` override; (2) the Excel diff helper using openpyxl to compare sheets, cells, rows, and named ranges; and (3) the QUESTIONS.md state file that ships as a data layer destination for gate rejections, with CLI commands deferred to Phase 4. The Word (.docx) diff is simpler -- paragraph-level text extraction via python-docx with difflib.

**Primary recommendation:** Build in dependency order: model extensions first (anchor field, QuestionEntry), then QUESTIONS.md state layer, then source commands (ingest, list, show, diff), then Excel/Word diff helpers, then truth commands (set with gate, get, list, trace, flag), then doctor/init updates for 7-file awareness.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Verification gate (TRUTH-04): Exit-code gate, not interactive prompt. `truth set` exits non-zero (exit 2) with discrepancy details printed. Analyst re-runs with `--confirm` to accept. No prompt, fully scriptable, compatible with XC-07
- `--confirm` is per-invocation only. No persistent pending state. The analyst re-runs the same `truth set` command with `--confirm` added to force through. If not confirmed, nothing is stored
- Rejection writes directly to QUESTIONS.md with the discrepancy as context. The question captures: key, old value, new value, both source IDs, delta. Phase 4 builds the `ask`/`answer` CLI on top of this file
- Compact diff output on gate fire: key, old value (source, date), new value (source), delta if numeric, one-line verdict. Fits in a terminal without scrolling
- `--json` flag on truth set includes the discrepancy details in structured output when the gate fires
- Gate comparison logic: Non-anchor facts use exact string match. Anchor facts use best-effort numeric parse (strip currency, commas, percent, whitespace, then float()). If both parse, apply percentage tolerance. Otherwise fall back to exact string match
- Zero-to-nonzero always fires regardless of tolerance (division by zero edge case)
- No-op fast path: if new value is bytewise equal to old value, exit 0 immediately. No supersedes chain write, no gate
- Comparison uses absolute percentage delta: `abs((new - old) / old) * 100`
- Anchor facts (TRUTH-03): Explicit `--anchor` flag on `truth set` marks a fact as an anchor metric. Stored as field in fact YAML. Sticky once set. `--no-anchor` explicitly demotes. Both designation and demotion recorded in supersedes chain. Global only in v1: one `anchor_tolerance_pct` in config.json, default 0.5%
- Ingest workflow (SRC-01, SRC-07): All metadata via flags, no prompts. `--date` defaults to today. Reference only, never copy. SOURCES.md stores relative paths. Source IDs generated as `{DEAL_CODE}-{NNN}` (zero-padded, monotonic, from config)
- Excel auto-diff on ingest (SRC-07): Summary only on ingest. Compact format locked. Full diff via `diligent sources diff` separately
- Sources diff (SRC-05, SRC-06): Excel structured diff via diff_excel_versions.py. Word paragraph-level diff via python-docx. PDF and others: "Diff not supported for this format" message. No pdfplumber dependency
- Truth trace (TRUTH-07): Timeline format, reverse-chronological, most recent first. Compact by default. Flag events interleaved. Summary line at bottom. `--verbose` inlines compact diff summary. No separate `truth show` command
- Truth list (TRUTH-06): Three status states: current, flagged, stale. `--stale` filter shows flagged OR source-superseded. `--workstream` filter. Summary line at bottom. One line per fact, aligned columns
- QUESTIONS.md ships in Phase 2 as seventh core state file. Reader/writer, init scaffold, doctor check. Phase 4 builds CLI commands on top

### Claude's Discretion
- Source ID counter persistence mechanism (config.json vs SOURCES.md-derived)
- Exact diff_excel_versions.py implementation (openpyxl cell comparison strategy)
- docx diff paragraph extraction approach
- QUESTIONS.md field set and YAML structure (beyond the fields needed for gate rejection)
- `truth flag` internal implementation (how flagged object is structured in YAML)
- Whether `truth list` column widths are fixed or auto-sized

### Deferred Ideas (OUT OF SCOPE)
- Per-key tolerance overrides (AN-01) -- v2 requirement
- PDF diff support via pdfplumber -- not worth the dependency cost
- `truth show` as a separate command -- `truth get` and `truth trace` cover the use cases
- Glob pattern support for batch ingestion (ING-01) -- v2 requirement
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SRC-01 | `diligent ingest <path>` logs source with metadata and --supersedes pointer | Existing SourceEntry model, write_sources, LazyGroup pattern for new command group |
| SRC-02 | Source IDs follow `{DEAL_CODE}-{NNN}` convention | Config has deal_code; counter can derive from SOURCES.md max ID or config.json field |
| SRC-03 | `diligent sources list` shows all registered sources | Existing read_sources, formatting.py output_result pattern |
| SRC-04 | `diligent sources show <source-id>` displays full record | Existing read_sources with ID lookup |
| SRC-05 | `diligent sources diff <id-a> <id-b>` diffs two source files | New diff_excel_versions.py helper + python-docx paragraph diff |
| SRC-06 | diff_excel_versions.py reports sheets, named ranges, cells differ | openpyxl 3.1.5: load_workbook, defined_names, iter_rows for cell comparison |
| SRC-07 | Ingest auto-invokes diff when superseding an Excel source | Ingest command checks --supersedes, resolves file paths, calls diff helper |
| TRUTH-01 | `truth set <key> <value> --source <id>` records fact with citation | Existing FactEntry model, write_truth; new command with required --source option |
| TRUTH-02 | `truth set` updates existing key: prior value pushed to supersedes chain | SupersededValue model already exists; push current to chain before overwrite |
| TRUTH-03 | Tolerance config: exact for non-anchor, percentage for anchor metrics | ConfigFile already has anchor_tolerance_pct; add anchor field to FactEntry |
| TRUTH-04 | Verification gate stops on beyond-tolerance change, requires --confirm | Exit-code gate (exit 2), compact output, --confirm re-run, rejection writes QUESTIONS.md |
| TRUTH-05 | `truth get <key>` shows current value with source citation | Simple read_truth + key lookup |
| TRUTH-06 | `truth list` with --workstream and --stale filters | Three-state status logic (current/flagged/stale), aligned column output |
| TRUTH-07 | `truth trace <key>` shows full supersedes history | Reverse-chronological timeline from supersedes chain + flag events |
| TRUTH-08 | `truth flag <key> --reason` marks fact for review | Existing flagged dict field on FactEntry; set reason + date |
| TRUTH-09 | TRUTH.md append-only at entry level | write_truth already handles this -- push to supersedes, never delete entries |
| TRUTH-10 | fact_parser.py is canonical reader/writer | Existing truth.py already serves this role; may rename or alias |
| TRUTH-11 | All values stored as quoted strings | Already implemented in _format_fact_yaml with explicit quoting |
| TRUTH-12 | Optional --computed-by and --notes flags on truth set | FactEntry already has computed_by and notes fields |
</phase_requirements>

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=8.1 | CLI framework | Already used; LazyGroup pattern established |
| pyyaml | >=6.0 | YAML parsing for state files | Already used in all state readers/writers |
| python-frontmatter | >=1.1 | DEAL.md/STATE.md frontmatter parsing | Already used |

### New Dependencies
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openpyxl | >=3.1.5 | Excel file reading for diff | Lazy-imported only by diff_excel_versions.py and ingest auto-diff |
| python-docx | >=1.1.0 | Word document text extraction for diff | Lazy-imported only by docx diff path in sources diff |

### No New Dependencies Needed
| Problem | Solved With |
|---------|-------------|
| Text diffing | stdlib `difflib` (already available) |
| Date handling | stdlib `datetime` (already used in init_cmd) |
| Numeric parsing | stdlib `re` for stripping + `float()` |
| Aligned column output | stdlib string formatting or existing formatting.py |
| Temporary file comparison | stdlib `tempfile` (already used in atomic_write) |

**Installation (add to pyproject.toml dependencies):**
```
"openpyxl>=3.1.5",
"python-docx>=1.1.0",
```

**Critical: Both must be lazy-imported.** They are heavy imports (openpyxl especially). Only imported inside the specific functions that need them, never at module top level. This preserves the <200ms CLI startup requirement (INIT-08/XC-01).

## Architecture Patterns

### New Files and Structure
```
diligent/
  commands/
    sources_cmd.py     # ingest, list, show, diff subcommands
    truth_cmd.py       # set, get, list, trace, flag subcommands
  helpers/
    diff_excel.py      # Excel comparison (openpyxl, lazy-imported)
    diff_docx.py       # Word comparison (python-docx, lazy-imported)
    numeric.py         # Numeric parsing/comparison for verification gate
  state/
    models.py          # Add QuestionEntry, anchor field to FactEntry
    questions.py       # QUESTIONS.md reader/writer (H2 + fenced YAML)
    truth.py           # Existing, no changes needed to reader/writer
    sources.py         # Existing, no changes needed to reader/writer
    config.py          # Existing, no changes needed
  templates/
    QUESTIONS.md.tmpl  # New template for init scaffold
```

### Pattern 1: Command Group Registration (LazyGroup)
**What:** New command groups registered in cli.py lazy_subcommands dict
**When to use:** Every new command group
**Example:**
```python
# cli.py -- add to lazy_subcommands dict
@click.group(
    cls=LazyGroup,
    lazy_subcommands={
        "init": "diligent.commands.init_cmd.init_cmd",
        "doctor": "diligent.commands.doctor.doctor",
        "config": "diligent.commands.config_cmd.config_cmd",
        "migrate": "diligent.commands.migrate_cmd.migrate",
        "sources": "diligent.commands.sources_cmd.sources_cmd",  # NEW
        "truth": "diligent.commands.truth_cmd.truth_cmd",        # NEW
    },
)
```

### Pattern 2: Nested Command Group (Click group-of-commands)
**What:** `sources` and `truth` are Click groups with subcommands (like `config` already is)
**When to use:** When a command has sub-operations (list, show, get, set, etc.)
**Example:**
```python
# sources_cmd.py
@click.group("sources")
def sources_cmd():
    """Manage source documents."""
    pass

@sources_cmd.command("list")
@click.option("--json", "json_mode", is_flag=True, default=False)
def sources_list(json_mode):
    """List all registered source documents."""
    ...

@sources_cmd.command("ingest")
@click.argument("path")
@click.option("--date", default=None)
@click.option("--source", "source_id", default=None)  # NOT used; ID is auto-generated
@click.option("--supersedes", default=None)
@click.option("--parties", default=None)
@click.option("--workstream", default=None)
@click.option("--notes", default=None)
@click.option("--json", "json_mode", is_flag=True, default=False)
def ingest(path, date, supersedes, parties, workstream, notes, json_mode):
    """Register a source document."""
    ...
```

### Pattern 3: State File Read-Modify-Write Cycle
**What:** Read state file, modify in-memory model, write back with atomic_write + validation
**When to use:** Every command that mutates state (ingest, truth set, truth flag)
**Example:**
```python
def _do_truth_set(diligence_dir, key, value, source, workstream, ...):
    truth_path = diligence_dir / "TRUTH.md"
    truth = read_truth(truth_path)
    
    # Check if key exists (for gate logic)
    if key in truth.facts:
        existing = truth.facts[key]
        # ... gate comparison ...
        # Push existing to supersedes
        truth.facts[key].supersedes.insert(0, SupersededValue(
            value=existing.value,
            source=existing.source,
            date=existing.date,
        ))
    
    # Update or create
    truth.facts[key] = FactEntry(
        key=key, value=value, source=source, ...
    )
    
    write_truth(truth_path, truth)
```

### Pattern 4: Exit-Code Gate (Non-Interactive Verification)
**What:** Command exits with specific code (2) on discrepancy, user re-runs with --confirm
**When to use:** truth set when value change exceeds tolerance
**Example:**
```python
# truth_cmd.py -- truth set
if discrepancy_detected and not confirm:
    # Print compact discrepancy report
    click.echo(f"  key:       {key}")
    click.echo(f"  current:   {old_value} (source: {old_source}, date: {old_date})")
    click.echo(f"  proposed:  {new_value} (source: {new_source})")
    if delta_str:
        click.echo(f"  delta:     {delta_str}")
    click.echo(f"  verdict:   Value changed beyond tolerance. Re-run with --confirm to accept.")
    
    if json_mode:
        output_result({
            "status": "discrepancy",
            "key": key,
            "current_value": old_value,
            "proposed_value": new_value,
            "current_source": old_source,
            "proposed_source": new_source,
            "delta": delta_str,
        }, json_mode=True)
    
    raise SystemExit(2)
```

### Pattern 5: Source ID Generation
**What:** Monotonic, zero-padded, never-reused source IDs
**Recommendation (Claude's discretion):** Derive next ID from SOURCES.md, not config.json. Reading the current max from SOURCES.md is reliable, avoids a second file mutation on every ingest, and is self-healing if someone manually adds an entry.
**Example:**
```python
def _next_source_id(sources: SourcesFile, deal_code: str) -> str:
    """Generate next source ID from existing sources."""
    max_num = 0
    prefix = f"{deal_code}-"
    for s in sources.sources:
        if s.id.startswith(prefix):
            try:
                num = int(s.id[len(prefix):])
                max_num = max(max_num, num)
            except ValueError:
                continue
    return f"{deal_code}-{max_num + 1:03d}"
```

### Pattern 6: Lazy Import for Heavy Dependencies
**What:** openpyxl and python-docx imported inside functions, not at module level
**When to use:** Any code path touching Excel or Word files
**Example:**
```python
def diff_excel_versions(path_a: str, path_b: str) -> dict:
    """Compare two Excel files and return structured diff summary."""
    from openpyxl import load_workbook  # Lazy import
    
    wb_a = load_workbook(path_a, read_only=True, data_only=True)
    wb_b = load_workbook(path_b, read_only=True, data_only=True)
    try:
        # ... comparison logic ...
    finally:
        wb_a.close()
        wb_b.close()
```

### Anti-Patterns to Avoid
- **Top-level openpyxl/python-docx import:** Kills startup time. Always lazy-import inside the function that uses them.
- **Interactive prompts in gate:** The gate must be exit-code based. No `click.confirm()`, no `input()`. XC-07 compliance.
- **Storing absolute paths in SOURCES.md:** Must be relative to deal folder root. OneDrive sync breaks absolute paths.
- **Modifying source documents:** XC-04 says the tool never modifies files the analyst placed in the deal folder. Read-only access.
- **Persistent pending state for gate:** No "pending confirmation" stored anywhere. The gate is stateless. Re-run with `--confirm` or don't.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Excel cell comparison | Custom binary parser | openpyxl load_workbook(read_only=True, data_only=True) | .xlsx is a complex ZIP+XML format; openpyxl handles all edge cases |
| Word text extraction | Custom XML parser | python-docx Document().paragraphs | .docx is also ZIP+XML; python-docx handles encoding, styles, etc. |
| Text differencing | Custom diff algorithm | stdlib difflib.unified_diff or difflib.Differ | Well-tested, handles edge cases, standard output format |
| YAML serialization | Manual string building for complex structures | pyyaml safe_dump (for non-value fields) | Already established pattern; _format_fact_yaml manually quotes value field only |
| Numeric parsing (currency) | Full locale-aware parser | Simple regex strip + float() | Locked decision: strip $, commas, %, whitespace, then float(). Best-effort, fallback to string compare |

**Key insight:** The only custom logic is the verification gate comparison -- the actual tolerance check and gate flow. Everything else (file I/O, parsing, diffing) has established libraries or existing project patterns.

## Common Pitfalls

### Pitfall 1: YAML Type Coercion on Fact Values
**What goes wrong:** PyYAML's safe_load interprets `"yes"` as `True`, `"1.5"` as `1.5`, `"2026-04-07"` as a `datetime.date`
**Why it happens:** YAML 1.1 implicit type resolution. Financial data is full of these edge cases.
**How to avoid:** Already solved in Phase 1. `_format_fact_yaml` manually quotes the value field. `_parse_fact_entry` validates value is a string. Maintain this discipline for any new fields that hold user data.
**Warning signs:** Round-trip test fails with type mismatch.

### Pitfall 2: Division by Zero in Gate Comparison
**What goes wrong:** `abs((new - old) / old) * 100` crashes when old value is 0
**Why it happens:** Zero-to-nonzero is a real scenario (new product line, new customer, previously zero revenue)
**How to avoid:** Locked decision: zero-to-nonzero always fires the gate regardless of tolerance. Check for old == 0 before computing percentage delta. Return a special "zero-to-nonzero" verdict.
**Warning signs:** ZeroDivisionError in gate comparison function.

### Pitfall 3: openpyxl Memory on Large Spreadsheets
**What goes wrong:** Loading two large Excel files fully into memory doubles RAM usage
**Why it happens:** Default load_workbook reads all cells, styles, charts, images into memory
**How to avoid:** Use `load_workbook(path, read_only=True, data_only=True)`. `read_only=True` uses lazy loading and dramatically reduces memory. `data_only=True` gives calculated values instead of formulas. Always `close()` the workbook after use.
**Warning signs:** Slow ingest, high memory during diff.

### Pitfall 4: Stale Status Depends on Source Supersedes Chain
**What goes wrong:** `truth list --stale` doesn't catch facts whose source has been superseded
**Why it happens:** Staleness requires cross-referencing TRUTH.md facts against SOURCES.md supersedes chains -- if source X was superseded by source Y, all facts citing source X are potentially stale
**How to avoid:** Build a reverse lookup: for each source ID, find its superseding source (if any). For each fact, check if its source has been superseded. Cache this mapping during `truth list` execution.
**Warning signs:** Facts show as "current" even though their source document was replaced.

### Pitfall 5: Anchor Flag Stickiness Across Updates
**What goes wrong:** Analyst sets `--anchor` on first `truth set`. Subsequent updates without `--anchor` lose the designation.
**Why it happens:** If the command doesn't read the existing anchor state before writing, it defaults to false.
**How to avoid:** When updating an existing fact, read the current `anchor` value and preserve it unless `--no-anchor` is explicitly passed. `--anchor` sets it, `--no-anchor` clears it, absence preserves current state.
**Warning signs:** Anchor facts lose their designation on routine updates.

### Pitfall 6: Path Resolution for Source References
**What goes wrong:** `diligent ingest ../documents/file.xlsx` stores the wrong relative path
**Why it happens:** The path needs to be relative to the deal folder root (parent of `.diligence/`), not the current working directory
**How to avoid:** Resolve the input path to absolute, then compute relative path from the deal folder root. Use `pathlib.Path.resolve()` then `relative_to()`.
**Warning signs:** `doctor` reports broken source references; `sources diff` can't find files.

### Pitfall 7: Config Default for anchor_tolerance_pct
**What goes wrong:** CONTEXT.md says default 0.5%, but existing config template uses 1.0
**Why it happens:** The template was written in Phase 1 before the detailed Phase 2 discussion
**How to avoid:** Update the template default from 1.0 to 0.5 in Phase 2, or document which default is canonical. The CONTEXT.md decision says 0.5%. The existing template says 1.0. The planner must resolve this.
**Warning signs:** Gate fires at unexpected thresholds.

## Code Examples

### Verification Gate Numeric Parsing
```python
# helpers/numeric.py
import re

_STRIP_PATTERN = re.compile(r"[\$,\%\s]")

def try_parse_numeric(value: str) -> float | None:
    """Best-effort numeric parse: strip currency/comma/percent/whitespace, then float().
    
    Returns float or None if parse fails.
    """
    stripped = _STRIP_PATTERN.sub("", value)
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def compute_gate_result(old_value: str, new_value: str, is_anchor: bool, tolerance_pct: float) -> dict | None:
    """Compare old and new values. Returns discrepancy dict or None if no gate fires.
    
    Returns None if:
    - Values are bytewise equal (no-op fast path)
    - Non-anchor and values differ (gate fires, but this returns the discrepancy)
    - Anchor within tolerance
    
    Returns dict with keys: fired, delta_str, verdict
    """
    # No-op fast path
    if old_value == new_value:
        return None  # No change, no gate
    
    if not is_anchor:
        # Non-anchor: any difference fires
        return {
            "fired": True,
            "delta_str": None,
            "verdict": "Value changed (exact match required for non-anchor facts).",
        }
    
    # Anchor: try numeric comparison
    old_num = try_parse_numeric(old_value)
    new_num = try_parse_numeric(new_value)
    
    if old_num is None or new_num is None:
        # Can't parse both as numbers; fall back to exact match
        return {
            "fired": True,
            "delta_str": None,
            "verdict": "Value changed (non-numeric anchor, exact match applied).",
        }
    
    # Zero-to-nonzero: always fires
    if old_num == 0.0 and new_num != 0.0:
        return {
            "fired": True,
            "delta_str": f"{old_num} -> {new_num} (zero-to-nonzero)",
            "verdict": "Zero-to-nonzero change always requires confirmation.",
        }
    
    # Percentage delta
    if old_num == 0.0:
        # Both zero -- no change
        return None
    
    pct_delta = abs((new_num - old_num) / old_num) * 100
    delta_str = f"{pct_delta:.2f}% ({old_num} -> {new_num})"
    
    if pct_delta > tolerance_pct:
        return {
            "fired": True,
            "delta_str": delta_str,
            "verdict": f"Delta {pct_delta:.2f}% exceeds tolerance {tolerance_pct}%.",
        }
    
    # Within tolerance
    return None
```

### Excel Diff Summary
```python
# helpers/diff_excel.py
def diff_excel_summary(path_a: str, path_b: str) -> dict:
    """Compare two Excel files. Returns structured summary.
    
    Returns dict with keys: sheets_changed, total_sheets,
    cells_differ, rows_added, rows_removed, named_ranges_added,
    named_ranges_removed, changed_sheet_names.
    """
    from openpyxl import load_workbook
    
    wb_a = load_workbook(path_a, read_only=True, data_only=True)
    wb_b = load_workbook(path_b, read_only=True, data_only=True)
    
    try:
        sheets_a = set(wb_a.sheetnames)
        sheets_b = set(wb_b.sheetnames)
        
        # Named ranges
        names_a = set(wb_a.defined_names.definedName) if hasattr(wb_a.defined_names, 'definedName') else set()
        names_b = set(wb_b.defined_names.definedName) if hasattr(wb_b.defined_names, 'definedName') else set()
        # Simpler: compare name strings
        name_strs_a = {dn.name for dn in wb_a.defined_names.definedName} if wb_a.defined_names.definedName else set()
        name_strs_b = {dn.name for dn in wb_b.defined_names.definedName} if wb_b.defined_names.definedName else set()
        
        common_sheets = sheets_a & sheets_b
        cells_differ = 0
        rows_added = 0
        rows_removed = 0
        changed_sheets = []
        
        for sheet_name in common_sheets:
            ws_a = wb_a[sheet_name]
            ws_b = wb_b[sheet_name]
            # Compare cell values row by row
            # ... (implementation iterates rows, counts differences)
        
        return {
            "sheets_changed": len(changed_sheets),
            "total_sheets": len(sheets_b),
            "cells_differ": cells_differ,
            "rows_added": rows_added,
            "rows_removed": rows_removed,
            "named_ranges_added": len(name_strs_b - name_strs_a),
            "named_ranges_removed": len(name_strs_a - name_strs_b),
            "changed_sheet_names": changed_sheets,
        }
    finally:
        wb_a.close()
        wb_b.close()
```

### QUESTIONS.md Structure (Claude's Discretion Recommendation)
```yaml
# QUESTIONS.md -- H2 + fenced YAML, same as other state files

## Q-001
```yaml
question: "Revenue changed from $19,665 to $20,065 (2.03% delta) between ARRIVAL-003 and ARRIVAL-019. Which value is correct?"
workstream: financial
owner: self
status: open
date_raised: "2026-04-07"
context:
  type: gate_rejection
  key: annual_recurring_revenue
  old_value: "$19,665"
  new_value: "$20,065"
  old_source: ARRIVAL-003
  new_source: ARRIVAL-019
  delta: "2.03%"
```

Fields:
- question: human-readable text
- workstream: scoped to a workstream (optional, can be empty)
- owner: who needs to answer (self, principal, seller, broker, counsel)
- status: open | answered
- date_raised: ISO date
- context: structured context, type field distinguishes gate_rejection from manual ask (Phase 4)
```

### FactEntry Model Extension
```python
# state/models.py -- updated FactEntry
@dataclass
class FactEntry:
    """A single validated fact in TRUTH.md."""
    key: str
    value: str
    source: str
    date: str
    workstream: str
    supersedes: list[SupersededValue] = field(default_factory=list)
    computed_by: Optional[str] = None
    notes: Optional[str] = None
    flagged: Optional[dict] = None
    anchor: bool = False  # NEW: sticky anchor designation
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| openpyxl full load | read_only=True, data_only=True | openpyxl 2.4+ | 5-10x less memory for large files |
| python-docx 0.x | python-docx 1.1+ | 2024 | Stable API for paragraph extraction |
| Click interactive prompts | Exit-code gates + --confirm flags | This project's design | Scriptable, AI-agent compatible |

**Deprecated/outdated:**
- openpyxl `get_named_ranges()` -- replaced by `defined_names` property in openpyxl 3.x
- python-docx `Document.paragraphs` does not include text inside tables -- use `iter_inner_content()` if table text needed (not needed for this use case; paragraph-level diff is sufficient per locked decision)

## Open Questions

1. **anchor_tolerance_pct default: 0.5% vs 1.0%**
   - What we know: CONTEXT.md says "default 0.5%". Existing config.json template and render_config() use 1.0.
   - What's unclear: Which is canonical for existing deal folders initialized before Phase 2.
   - Recommendation: Update template to 0.5%. Existing deals keep their 1.0 until the analyst changes it via `config set`. Document this in the phase.

2. **Source ID counter edge case: manual entries**
   - What we know: IDs are derived from SOURCES.md max. Manual edits could create gaps or out-of-order IDs.
   - What's unclear: Whether to warn on non-monotonic IDs during doctor checks.
   - Recommendation: Doctor should warn (not error) if source IDs are non-monotonic. The counter always uses max+1 regardless of gaps.

3. **TRUTH-10: fact_parser.py naming**
   - What we know: Requirements say "fact_parser.py is the canonical TRUTH.md reader/writer". The existing code uses `truth.py` for this role.
   - What's unclear: Whether to rename truth.py to fact_parser.py or treat truth.py as fulfilling TRUTH-10.
   - Recommendation: Keep truth.py as-is. It already fulfills TRUTH-10's intent. Add a one-line alias or note in docs. Renaming would break all Phase 1 imports.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRC-01 | ingest registers source with metadata | integration | `python -m pytest tests/test_ingest.py -x` | Wave 0 |
| SRC-02 | Source IDs follow {DEAL_CODE}-{NNN} | unit | `python -m pytest tests/test_source_ids.py -x` | Wave 0 |
| SRC-03 | sources list shows all sources | integration | `python -m pytest tests/test_sources_cmd.py::test_list -x` | Wave 0 |
| SRC-04 | sources show displays full record | integration | `python -m pytest tests/test_sources_cmd.py::test_show -x` | Wave 0 |
| SRC-05 | sources diff diffs two files | integration | `python -m pytest tests/test_sources_diff.py -x` | Wave 0 |
| SRC-06 | diff_excel reports sheets, cells, named ranges | unit | `python -m pytest tests/test_diff_excel.py -x` | Wave 0 |
| SRC-07 | ingest auto-diffs when superseding Excel | integration | `python -m pytest tests/test_ingest.py::test_auto_diff -x` | Wave 0 |
| TRUTH-01 | truth set records fact with --source | integration | `python -m pytest tests/test_truth_cmd.py::test_set_new -x` | Wave 0 |
| TRUTH-02 | truth set pushes prior to supersedes chain | integration | `python -m pytest tests/test_truth_cmd.py::test_set_update -x` | Wave 0 |
| TRUTH-03 | anchor tolerance vs exact match | unit | `python -m pytest tests/test_verification_gate.py::test_anchor_tolerance -x` | Wave 0 |
| TRUTH-04 | verification gate fires and requires --confirm | integration | `python -m pytest tests/test_verification_gate.py -x` | Wave 0 |
| TRUTH-05 | truth get shows current value | integration | `python -m pytest tests/test_truth_cmd.py::test_get -x` | Wave 0 |
| TRUTH-06 | truth list with filters | integration | `python -m pytest tests/test_truth_cmd.py::test_list -x` | Wave 0 |
| TRUTH-07 | truth trace shows full history | integration | `python -m pytest tests/test_truth_cmd.py::test_trace -x` | Wave 0 |
| TRUTH-08 | truth flag marks for review | integration | `python -m pytest tests/test_truth_cmd.py::test_flag -x` | Wave 0 |
| TRUTH-09 | append-only at entry level | unit | `python -m pytest tests/test_truth_cmd.py::test_append_only -x` | Wave 0 |
| TRUTH-10 | truth.py is canonical reader/writer | unit | Already covered by test_state_roundtrip.py | Exists |
| TRUTH-11 | values stored as quoted strings | unit | Already covered by test_state_roundtrip.py | Exists |
| TRUTH-12 | --computed-by and --notes flags | integration | `python -m pytest tests/test_truth_cmd.py::test_optional_flags -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q` (quick, stop on first failure)
- **Per wave merge:** `python -m pytest tests/ -v --tb=short` (full suite, verbose)
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_ingest.py` -- covers SRC-01, SRC-02, SRC-07
- [ ] `tests/test_sources_cmd.py` -- covers SRC-03, SRC-04
- [ ] `tests/test_sources_diff.py` -- covers SRC-05
- [ ] `tests/test_diff_excel.py` -- covers SRC-06 (needs sample .xlsx fixtures)
- [ ] `tests/test_truth_cmd.py` -- covers TRUTH-01, TRUTH-02, TRUTH-05, TRUTH-06, TRUTH-07, TRUTH-08, TRUTH-09, TRUTH-12
- [ ] `tests/test_verification_gate.py` -- covers TRUTH-03, TRUTH-04 (the most critical test file)
- [ ] `tests/test_questions_state.py` -- covers QUESTIONS.md reader/writer round-trip
- [ ] `tests/fixtures/` -- sample .xlsx files for Excel diff tests, sample .docx for Word diff tests
- [ ] Update `tests/test_init.py` -- verify 7 files scaffolded (was 6)
- [ ] Update `tests/test_doctor.py` -- verify QUESTIONS.md existence check

## Sources

### Primary (HIGH confidence)
- Project codebase: `state/models.py`, `state/truth.py`, `state/sources.py`, `cli.py`, `commands/doctor.py`, `helpers/io.py` -- directly read and analyzed
- openpyxl official docs (https://openpyxl.readthedocs.io/en/stable/) -- load_workbook, defined_names, read_only mode
- Click official docs (https://click.palletsprojects.com/en/stable/complex/) -- LazyGroup pattern, nested command groups
- Phase 2 CONTEXT.md -- locked decisions, all verification gate behavior

### Secondary (MEDIUM confidence)
- openpyxl PyPI (https://pypi.org/project/openpyxl/) -- version 3.1.5 confirmed
- python-docx docs (https://python-docx.readthedocs.io/en/latest/) -- paragraphs API, tables API

### Tertiary (LOW confidence)
- None -- all findings verified against primary sources or existing codebase

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all libraries already in project or well-established with verified docs
- Architecture: HIGH -- extends existing patterns directly; no new architectural patterns needed
- Pitfalls: HIGH -- most pitfalls identified from reading the actual code and locked decisions
- Verification gate: HIGH -- logic fully specified in CONTEXT.md decisions, pseudocode locked

**Research date:** 2026-04-07
**Valid until:** 2026-05-07 (stable domain; openpyxl/python-docx APIs are mature)
