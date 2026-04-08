# Phase 3: Artifacts and Reconciliation - Research

**Researched:** 2026-04-08
**Domain:** Artifact tracking, dependency-graph staleness detection, docx citation scanning
**Confidence:** HIGH

## Summary

Phase 3 adds the artifact tracking layer and the reconciliation engine to diligent. The artifact subsystem introduces ARTIFACTS.md as the 8th core state file (H2 + fenced YAML, same as all others), with `artifact register`, `artifact list`, and `artifact refresh` commands. The reconcile engine reads TRUTH.md, SOURCES.md, and ARTIFACTS.md to build a dependency graph and report which deliverables are stale and why.

The codebase is well-positioned for this phase. All infrastructure patterns are established: H2 + fenced YAML reader/writer (replicated per module), atomic write with validation callback, LazyGroup CLI registration, DILIGENT_CWD for test isolation, exit-code gate pattern (--confirm), and --json dual output. The new code follows these patterns exactly. No new dependencies are needed; python-docx 1.2.0 is already installed for the .docx scanner (ART-09).

**Primary recommendation:** Build in dependency order: ArtifactEntry model -> artifacts.py reader/writer -> ARTIFACTS.md template + init update -> artifact commands -> reconcile engine -> doctor integration -> docx scanner. The reconcile engine is a pure function (no I/O) that takes three parsed state files and returns structured output, making it straightforward to test.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Reconcile output format: grouped by artifact, facts ordered most recently changed first, compact one-liner per fact (key, old->new, source ID, days stale), `--verbose` for two-line format, default shows only stale/advisory, `--all` for everything, summary line at bottom
- Staleness definition: two triggers (value changed, source superseded), both relative to artifact's last_refreshed timestamp. Source-superseded only fires for supersedes events AFTER last refresh. Flagged facts in separate third sub-section, advisory only
- Artifact register workflow: `--references key1,key2,key3` comma-separated, upsert with `--confirm` flag, truth key validation at registration (warn on missing, succeed), docx scanner runs by default on .docx registrations, `--references` authoritative when provided, scanner_findings stored separately
- ARTIFACTS.md format: H2 heading = relative path (posix, forward slashes), fields: workstream, registered, last_refreshed, references (list), scanner_findings (list), notes
- Exit code: 0 if all current, non-zero if any stale. `--strict` elevates flagged facts to non-zero

### Claude's Discretion
- reconcile_anchors.py internal implementation (dependency graph walk algorithm)
- artifact_scanner.py docx parsing approach (python-docx paragraph walking, regex for citation tags)
- Exact column alignment widths in reconcile output
- How `artifact refresh` updates last_refreshed (simple timestamp update, no validation beyond confirming artifact exists)
- Whether the H2+YAML walker logic is extracted as shared utility or replicated per module (Phase 1 decision was replicate, but 8 files may justify extraction)

### Deferred Ideas (OUT OF SCOPE)
- Shared H2+YAML walker utility extraction (8 files may justify it, but Phase 1 decision was replicate per module)
- Per-key tolerance overrides affecting artifact staleness thresholds (AN-01, v2)
- .pptx and .xlsx scanner support (DOC-02, v2)
- Auto-suggest which facts an ingested document might affect (ING-02, v2)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ART-01 | `diligent artifact register <path> --references <key1,key2,...>` registers a deliverable with explicit fact dependencies | New click command under `artifact` group, upsert with --confirm gate pattern, writes ARTIFACTS.md via artifacts.py writer |
| ART-02 | ARTIFACTS.md stores registered artifacts with path, references, workstream, dates, staleness status | New state file: ArtifactEntry model, artifacts.py H2+YAML reader/writer, ARTIFACTS.md.tmpl template, init scaffolding update |
| ART-03 | `diligent artifact list` shows all registered artifacts; supports --stale filter | Click subcommand reading ARTIFACTS.md + TRUTH.md + SOURCES.md for live staleness computation |
| ART-04 | `diligent artifact refresh <path>` marks artifact as refreshed (updates last_refreshed timestamp) | Simple timestamp update command, confirms artifact exists, writes via atomic_write |
| ART-05 | `diligent reconcile` walks dependency graph, reports stale artifacts with structured output | reconcile_anchors.py pure function: reads three state files, computes staleness, formats output |
| ART-06 | `diligent reconcile --workstream <name>` scopes to one workstream | Filter parameter on reconcile output, applied after graph walk |
| ART-07 | `diligent reconcile --strict` exits non-zero on any staleness | Exit code logic: strict elevates flagged facts to non-zero in addition to stale artifacts |
| ART-08 | reconcile_anchors.py is the deterministic engine behind reconcile | Pure function module, no CLI coupling, takes parsed state file data and returns structured result |
| ART-09 | artifact_scanner.py scans .docx files for `{{truth:key}}` citation tags | python-docx 1.2.0 paragraph walker with regex, lazy import, scanner runs by default on .docx registrations |
| XC-01 | All commands return in under 2 seconds for typical deal folder | Benchmark test: artifact register, list, refresh all under 2s with 100+ entries |
| XC-02 | `diligent reconcile` completes in under 10 seconds for typical deal folder | Benchmark test: reconcile with 200 sources, 500 facts, 100 artifacts under 10s |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| click | >=8.1 | CLI framework | Already in use, LazyGroup pattern established |
| pyyaml | >=6.0 | YAML parsing in fenced blocks | Already in use for all state files |
| python-docx | >=1.1.0 (installed: 1.2.0) | .docx paragraph extraction for scanner | Already dependency, lazy-imported in diff_docx.py |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re (stdlib) | - | Regex for citation tag matching `{{truth:key}}` | artifact_scanner.py |
| datetime (stdlib) | - | ISO date parsing and days-stale calculation | reconcile_anchors.py |
| pathlib (stdlib) | - | Path normalization to posix strings | artifact path handling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual date math | python-dateutil | Not needed. ISO 8601 dates parse with `date.fromisoformat()` (stdlib, Python 3.11+). No new dependency. |
| Replicated H2+YAML walker | Shared utility | Phase 1 decision was replicate. 8 files is at the threshold but extraction is deferred (CONTEXT.md). |

**Installation:**
No new dependencies needed. All libraries already in pyproject.toml.

## Architecture Patterns

### Recommended Project Structure
```
diligent/
  state/
    models.py          # Add ArtifactEntry, ArtifactsFile dataclasses
    artifacts.py       # NEW: read_artifacts / write_artifacts (H2+YAML walker)
  commands/
    artifact_cmd.py    # NEW: artifact register, list, refresh
    reconcile_cmd.py   # NEW: reconcile command (top-level)
  helpers/
    reconcile_anchors.py  # NEW: pure function staleness engine
    artifact_scanner.py   # NEW: docx citation tag scanner
  templates/
    ARTIFACTS.md.tmpl  # NEW: template for init scaffolding
```

### Pattern 1: H2 + Fenced YAML Reader/Writer (Replicated)
**What:** Each state file module (truth.py, sources.py, questions.py, now artifacts.py) has its own _strip_html_comments, _extract_h2_sections, _parse_fenced_yaml functions.
**When to use:** Every new state file module.
**Example:**
```python
# Source: existing pattern from diligent/state/questions.py
def read_artifacts(path: Path) -> ArtifactsFile:
    text = path.read_text(encoding="utf-8")
    sections = _extract_h2_sections(text)
    artifacts = []
    for heading, section_text in sections:
        data = _parse_fenced_yaml(section_text)
        if data is not None:
            artifacts.append(_parse_artifact_entry(heading, data))
    return ArtifactsFile(artifacts=artifacts)
```

### Pattern 2: Exit-Code Gate (--confirm)
**What:** Command exits non-zero with details when a destructive/overwriting action is attempted. Re-running with --confirm overrides.
**When to use:** artifact register when re-registering an existing artifact (upsert).
**Example:**
```python
# Source: established pattern from truth_cmd.py truth_set
existing = lookup_artifact(artifacts, path)
if existing is not None and not confirm_flag:
    click.echo(f"Artifact already registered: {path}")
    click.echo(f"  references: {', '.join(existing.references)}")
    click.echo("Re-run with --confirm to update.")
    ctx.exit(1)
    return
```

### Pattern 3: LazyGroup Registration
**What:** New command groups register in cli.py lazy_subcommands dict.
**When to use:** Adding artifact and reconcile command groups.
**Example:**
```python
# Source: diligent/cli.py
lazy_subcommands={
    # ... existing entries ...
    "artifact": "diligent.commands.artifact_cmd.artifact_cmd",
    "reconcile": "diligent.commands.reconcile_cmd.reconcile_cmd",
}
```

### Pattern 4: Pure Function Engine + CLI Wrapper
**What:** Core logic in a pure function module (no Click, no I/O), CLI command is a thin wrapper that reads files, calls the engine, formats output.
**When to use:** reconcile_anchors.py computes staleness from parsed data; reconcile_cmd.py handles I/O and formatting.
**Example:**
```python
# reconcile_anchors.py (pure function, no imports from click or pathlib)
def compute_staleness(
    artifacts: list[ArtifactEntry],
    facts: dict[str, FactEntry],
    sources: list[SourceEntry],
) -> list[StaleArtifact]:
    """Deterministic staleness computation. No I/O."""
    ...
```

### Pattern 5: DILIGENT_CWD for Test Isolation
**What:** Commands check DILIGENT_CWD env var before walking up from cwd, allowing tests to point at tmp_path.
**When to use:** All new commands that locate .diligence/.
**Example:**
```python
# Source: diligent/commands/truth_cmd.py
env_cwd = os.environ.get("DILIGENT_CWD")
diligence = _find_diligence_dir(env_cwd)
```

### Pattern 6: Posix Path Normalization
**What:** File paths stored in ARTIFACTS.md use forward slashes (posix) for cross-platform OneDrive sync. Normalized on write.
**When to use:** artifact register stores path as `Path(input).as_posix()` relative to deal root.
**Example:**
```python
# Source: pattern from diligent/commands/sources_cmd.py _resolve_relative_path
rel = abs_file.relative_to(abs_root)
return rel.as_posix()  # Always forward slashes
```

### Anti-Patterns to Avoid
- **Importing click or pathlib in reconcile_anchors.py:** Keep the engine pure. All I/O in reconcile_cmd.py.
- **Using datetime.datetime for date comparison:** Facts store ISO date strings (YYYY-MM-DD). Use `date.fromisoformat()` for comparison, not datetime parsing.
- **Shared utility extraction:** Phase 1 decision was replicate H2+YAML walker per module. This is deferred per CONTEXT.md.
- **Modifying fact or source state during reconcile:** Reconcile is read-only. It never mutates TRUTH.md or SOURCES.md.
- **Importing python-docx at module level in artifact_scanner.py:** Must lazy-import inside function body per INIT-08 (<200ms startup).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML parsing in fenced blocks | Custom YAML tokenizer | yaml.safe_load on extracted block text | Edge cases in YAML spec are endless; PyYAML handles them |
| Date arithmetic (days stale) | Manual string math | `(date.today() - date.fromisoformat(d)).days` | stdlib handles leap years, month lengths |
| Docx text extraction | Manual ZIP/XML parsing | python-docx Document.paragraphs | Word XML schema is complex; python-docx abstracts it |
| Atomic file writes | Raw open/write | existing `atomic_write` from helpers/io.py | OneDrive retry, fsync, validation already handled |
| CLI dual output (text/json) | Inline conditional | existing `output_result` from helpers/formatting.py | Consistent --json behavior across all commands |

**Key insight:** Every infrastructure pattern needed for this phase already exists in the codebase. The task is extending the pattern to a new domain (artifacts), not inventing new infrastructure.

## Common Pitfalls

### Pitfall 1: Stale-on-Registration False Positive
**What goes wrong:** Artifact registers at time T. A fact it references was last updated before T. If staleness is checked as "fact date < artifact refresh date," the artifact appears current. But if the fact's source was superseded before T and the fact hasn't been re-validated, the artifact should actually show as stale under "source superseded."
**Why it happens:** The two staleness triggers (value changed, source superseded) have different temporal semantics.
**How to avoid:** Check both triggers independently. Value changed: `fact.date > artifact.last_refreshed`. Source superseded: walk SOURCES.md to find if any supersedes event for the fact's source occurred after `artifact.last_refreshed`.
**Warning signs:** Tests pass when only checking value changes but miss the "new source ingested, old facts not yet re-validated" window.

### Pitfall 2: Source Supersedes Chain Walk Direction
**What goes wrong:** SOURCES.md records `supersedes: DEAL-001` on the NEW source (DEAL-002). To find if a fact's source (DEAL-001) has been superseded, you need to check if any OTHER source lists DEAL-001 in its supersedes field. This is the inverse lookup.
**Why it happens:** Supersedes is stored on the new entry pointing backward, but staleness needs to query forward ("was this source replaced?").
**How to avoid:** Build a `superseded_by: dict[str, SourceEntry]` index at reconcile time. Key = old source ID, value = new source that superseded it. Existing `_build_superseded_source_set` in truth_cmd.py does this partially (returns a set), but reconcile needs the superseding source's date to compare against artifact refresh timestamp.
**Warning signs:** Source-superseded staleness never fires, or fires for all historical supersedes regardless of artifact refresh date.

### Pitfall 3: Artifact Path Matching
**What goes wrong:** Analyst registers `deliverables/analysis.docx` but the file system path is `deliverables\analysis.docx` on Windows. Or the artifact was registered with a trailing slash. Lookup fails silently.
**Why it happens:** Windows backslash vs posix forward slash, case sensitivity differences.
**How to avoid:** Normalize all artifact paths to posix (forward slashes) on write, as already done for SOURCES.md paths. Use `PurePosixPath` for comparison. H2 heading in ARTIFACTS.md is the canonical posix path.
**Warning signs:** `artifact refresh` says "artifact not found" for paths that exist in ARTIFACTS.md but with different slash conventions.

### Pitfall 4: Docx Scanner False Matches
**What goes wrong:** Scanner finds `{{truth:key}}` patterns in document text, but the text is inside a comment, header, footer, or table cell that python-docx `doc.paragraphs` doesn't cover.
**Why it happens:** `Document.paragraphs` only returns body paragraphs. Tables, headers, footers are separate document parts.
**How to avoid:** For v1, document this limitation. The scanner is advisory (findings stored separately from authoritative --references). `doc.paragraphs` covers the main body where most citation tags would appear. If needed later, add `doc.tables` iteration.
**Warning signs:** Scanner misses tags in tables. Since scanner is advisory, this is acceptable for v1.

### Pitfall 5: YAML List Quoting for References
**What goes wrong:** References like `customer_253_mrr` are stored as YAML list items. PyYAML might interpret numeric-looking keys differently.
**Why it happens:** YAML type coercion (the same problem TRUTH.md solves by quoting values).
**How to avoid:** References are always key names (strings). Quote them in the writer: `- "key_name"`. The reader gets strings from yaml.safe_load list items naturally.
**Warning signs:** A key like `123_revenue` gets parsed as integer 123 followed by `_revenue` parsing error.

### Pitfall 6: Init Must Be Updated Atomically
**What goes wrong:** Init scaffolding is updated to create ARTIFACTS.md, but doctor's expected files list is not updated simultaneously. Doctor reports ARTIFACTS.md as "missing" on old deal folders, or fails to check it on new ones.
**Why it happens:** Multiple files must be updated in lockstep: init_cmd.py STATE_FILES, doctor.py EXPECTED_FILES, template.
**How to avoid:** Update all three in the same plan/task: init_cmd.py, doctor.py, ARTIFACTS.md.tmpl.
**Warning signs:** Doctor fails on fresh init, or doctor doesn't catch ARTIFACTS.md corruption.

## Code Examples

### ArtifactEntry Model
```python
# New dataclass in state/models.py
@dataclass
class ArtifactEntry:
    """A registered deliverable artifact in ARTIFACTS.md."""
    path: str  # Relative posix path from deal root (H2 heading)
    workstream: str
    registered: str  # ISO 8601 date
    last_refreshed: str  # ISO 8601 date
    references: list[str] = field(default_factory=list)  # Truth keys
    scanner_findings: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ArtifactsFile:
    """ARTIFACTS.md state file: list of registered artifact deliverables."""
    artifacts: list[ArtifactEntry] = field(default_factory=list)
```

### ARTIFACTS.md Template
```
# Artifacts

<!-- This file tracks registered deliverable artifacts and their
     dependencies on validated facts in TRUTH.md. Each artifact is
     an H2 heading with the relative path from deal folder root,
     followed by a fenced YAML code block with metadata.

     Format:

     ## deliverables/retention/retention_analysis_v9.docx
     ```yaml
     workstream: "retention"
     registered: "2026-03-22"
     last_refreshed: "2026-03-22"
     references:
       - "customer_253_mrr"
       - "t12m_cohort"
     scanner_findings:
       - "revenue_growth_yoy"
     notes: ""
     ```

     Paths use forward slashes on all platforms.
     References must match keys in TRUTH.md.
     Scanner findings are advisory (not authoritative).

     This file is managed by diligent commands. Manual edits are
     supported but must preserve the H2 + fenced YAML structure. -->
```

### Reconcile Engine Core Logic
```python
# helpers/reconcile_anchors.py - pure function, no I/O
from dataclasses import dataclass, field
from datetime import date


@dataclass
class StaleFactInfo:
    """A single stale fact within an artifact."""
    key: str
    old_value: str
    new_value: str
    source_id: str
    days_stale: int
    category: str  # "value_changed" | "source_superseded" | "flagged"
    fact_date: str  # ISO date when fact was updated


@dataclass
class StaleArtifact:
    """Reconciliation result for one artifact."""
    path: str
    workstream: str
    value_changed: list[StaleFactInfo] = field(default_factory=list)
    source_superseded: list[StaleFactInfo] = field(default_factory=list)
    flagged: list[StaleFactInfo] = field(default_factory=list)

    @property
    def is_stale(self) -> bool:
        return bool(self.value_changed or self.source_superseded)

    @property
    def is_advisory(self) -> bool:
        return bool(self.flagged) and not self.is_stale
```

### Supersedes Index for Reconcile
```python
# Build reverse index: which source ID was superseded by which newer source
def _build_supersedes_index(sources: list[SourceEntry]) -> dict[str, SourceEntry]:
    """Map old_source_id -> new_source_entry that superseded it.

    Used to determine if a fact's source has been replaced and when.
    """
    index: dict[str, SourceEntry] = {}
    for src in sources:
        if src.supersedes:
            index[src.supersedes] = src
    return index
```

### Docx Citation Scanner
```python
# helpers/artifact_scanner.py
import re

CITATION_PATTERN = re.compile(r"\{\{truth:([a-zA-Z0-9_]+)\}\}")

def scan_docx_citations(path: str) -> list[str]:
    """Extract truth key references from a .docx file.

    Scans paragraph text for {{truth:key_name}} citation tags.
    Lazy-imports python-docx to keep CLI startup fast.

    Returns sorted unique list of referenced truth keys.
    """
    from docx import Document
    doc = Document(path)
    keys: set[str] = set()
    for para in doc.paragraphs:
        for match in CITATION_PATTERN.finditer(para.text):
            keys.add(match.group(1))
    return sorted(keys)
```

### Days-Stale Calculation
```python
# Simple stdlib date arithmetic
from datetime import date

def days_stale(fact_date_str: str, artifact_refresh_str: str) -> int:
    """Calculate days between fact update and today.

    Both inputs are ISO 8601 date strings (YYYY-MM-DD).
    Returns number of days since the fact was updated.
    """
    fact_date = date.fromisoformat(fact_date_str)
    return (date.today() - fact_date).days
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| manifest.json (original ART-02) | ARTIFACTS.md (H2+YAML) | CONTEXT.md decision | Consistent with all other state files; AI-readable |
| `--scan` flag on register | Scanner runs by default on .docx | CONTEXT.md decision | No flag needed; --references is authoritative override |
| Single staleness trigger | Two-trigger model (value changed + source superseded) | CONTEXT.md decision | Catches "new source ingested but facts not yet re-validated" window |

**Deprecated/outdated:**
- manifest.json format: replaced by ARTIFACTS.md before implementation started
- `--scan` flag: scanner runs automatically on .docx files, no opt-in flag

## Open Questions

1. **Column alignment widths for reconcile output**
   - What we know: Compact one-liner format locked. Key, old->new, source ID, (Xd stale).
   - What's unclear: Exact character widths for each column.
   - Recommendation: Use adaptive widths based on actual data (max key length, max value length), capped at terminal-friendly maximums. Start with key=25, value_pair=30, source=12, stale=10. This is Claude's discretion per CONTEXT.md.

2. **H2+YAML walker replication vs extraction**
   - What we know: Phase 1 decision was replicate. CONTEXT.md lists extraction as deferred.
   - What's unclear: N/A (decision is made).
   - Recommendation: Replicate for artifacts.py. 9th copy if you count doctor's inline parser. Deferred per CONTEXT.md.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ART-01 | artifact register creates entry in ARTIFACTS.md | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactRegister -x` | Wave 0 |
| ART-01 | artifact register upsert with --confirm | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactRegisterUpsert -x` | Wave 0 |
| ART-02 | ARTIFACTS.md round-trip read/write fidelity | unit | `python -m pytest tests/test_artifacts_state.py::TestArtifactsRoundTrip -x` | Wave 0 |
| ART-03 | artifact list shows all artifacts with staleness | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactList -x` | Wave 0 |
| ART-04 | artifact refresh updates last_refreshed | unit | `python -m pytest tests/test_artifact_cmd.py::TestArtifactRefresh -x` | Wave 0 |
| ART-05 | reconcile detects value-changed staleness | unit | `python -m pytest tests/test_reconcile.py::TestReconcileValueChanged -x` | Wave 0 |
| ART-05 | reconcile detects source-superseded staleness | unit | `python -m pytest tests/test_reconcile.py::TestReconcileSourceSuperseded -x` | Wave 0 |
| ART-06 | reconcile --workstream filters output | unit | `python -m pytest tests/test_reconcile.py::TestReconcileWorkstream -x` | Wave 0 |
| ART-07 | reconcile --strict exits non-zero on flagged facts | unit | `python -m pytest tests/test_reconcile.py::TestReconcileStrict -x` | Wave 0 |
| ART-08 | reconcile_anchors.py is pure function, no I/O | unit | `python -m pytest tests/test_reconcile_engine.py -x` | Wave 0 |
| ART-09 | artifact_scanner finds citation tags in .docx | unit | `python -m pytest tests/test_artifact_scanner.py -x` | Wave 0 |
| XC-01 | All commands under 2 seconds | integration | `python -m pytest tests/test_performance.py::test_artifact_commands_under_2s -x` | Wave 0 |
| XC-02 | Reconcile under 10 seconds at scale | integration | `python -m pytest tests/test_performance.py::test_reconcile_under_10s -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green (all 243 existing + new tests) before /gsd:verify-work

### Wave 0 Gaps
- [ ] `tests/test_artifacts_state.py` -- covers ART-02 (round-trip read/write)
- [ ] `tests/test_artifact_cmd.py` -- covers ART-01, ART-03, ART-04 (CLI commands)
- [ ] `tests/test_reconcile_engine.py` -- covers ART-08 (pure function engine)
- [ ] `tests/test_reconcile.py` -- covers ART-05, ART-06, ART-07 (CLI reconcile)
- [ ] `tests/test_artifact_scanner.py` -- covers ART-09 (docx scanner)
- [ ] `tests/test_performance.py` -- covers XC-01, XC-02 (performance benchmarks)

## Sources

### Primary (HIGH confidence)
- Existing codebase: diligent/state/models.py, truth.py, sources.py, questions.py -- established H2+YAML patterns
- Existing codebase: diligent/commands/truth_cmd.py -- CLI patterns, DILIGENT_CWD, exit-code gate, --json
- Existing codebase: diligent/helpers/diff_docx.py -- python-docx lazy import and paragraph extraction pattern
- Existing codebase: diligent/commands/init_cmd.py, doctor.py -- scaffolding and validation patterns
- CONTEXT.md: locked decisions on reconcile format, staleness triggers, ARTIFACTS.md format, scanner behavior

### Secondary (MEDIUM confidence)
- python-docx 1.2.0 installed, Document.paragraphs API verified through existing diff_docx.py usage
- Python 3.11+ date.fromisoformat() verified as stdlib (no external dep needed for ISO date parsing)

### Tertiary (LOW confidence)
- None. All findings verified against existing codebase or stdlib documentation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies, all libraries already in use
- Architecture: HIGH -- all patterns established in Phases 1-2, this phase extends them
- Pitfalls: HIGH -- identified from reading actual code paths and understanding the two-trigger staleness model
- Reconcile engine: HIGH -- pure function design maps clearly to existing codebase patterns (compute_gate_result precedent)
- Docx scanner: HIGH -- python-docx already used in diff_docx.py, paragraph walker pattern proven

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable -- no external API changes expected, all stdlib + existing deps)
