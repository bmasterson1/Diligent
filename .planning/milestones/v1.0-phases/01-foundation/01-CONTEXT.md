# Phase 1: Foundation - Context

**Gathered:** 2026-04-07
**Status:** Ready for planning

<domain>
## Phase Boundary

CLI scaffold, typed models for all 6 state files, atomic writes with OneDrive retry, `diligent init`, `diligent doctor`, `diligent config get/set`, and pyproject.toml packaging. The analyst can scaffold a deal folder and trust that every state file read/write is atomic, correct, and round-trip safe.

Requirements: INIT-01 through INIT-08, XC-03 through XC-08.

</domain>

<decisions>
## Implementation Decisions

### Init experience
- Interactive prompts by default. `--non-interactive` flag as opt-in escape hatch for scripting/automation
- XC-07 ("no interactive prompts") scoped to commands invoked during normal agent operation. Init is exempt: it is run once per deal by a human, never by an agent
- Full DEAL.md frontmatter collected at init: deal code, target name (legal + common), deal stage, LOI date, key people (principal + role, seller, broker), thesis, workstream selection
- `diligent init` with no flags: prompts for all fields interactively
- `diligent init --code ARRIVAL` (partial flags): uses provided values, prompts only for what's missing
- `diligent init --non-interactive --code ARRIVAL ...`: no prompts, fails with clear error if any required field is missing

### Deal code format
- Short uppercase alpha only (A-Z), 3-12 characters
- Used as prefix for source IDs: `{DEAL_CODE}-{NNN}` (zero-padded, monotonic)
- Enforced at init and validated by doctor

### Thesis input
- `$EDITOR` opened with a git-style template (comment lines explaining what to write, blank space below)
- Comment lines prefixed with `#`, stripped before saving to DEAL.md body
- Fallback chain when `$EDITOR` is unset: notepad (Windows) > nano (Linux) > vi (macOS) > multi-line CLI input with "type END on its own line to finish"
- Fallback chain is invisible in the happy path; analyst is never asked "which editor"

### TRUTH.md fact format
- YAML inside fenced code blocks under markdown H2 headings (one heading per fact key)
- Flat alphabetical order by key (no workstream grouping in the file; workstream is a tag in the YAML metadata, filtered at query time via `truth list --workstream`)
- Core field set per fact entry:
  - `value` (quoted string, always) -- prevents YAML type coercion of financial data
  - `source` (source ID, required) -- non-negotiable, CLI rejects truth set without --source
  - `date` (ISO 8601, auto-recorded) -- never typed by hand
  - `workstream` (string, must match WORKSTREAMS.md entry, validated at write time)
  - `supersedes` (list of prior value/source/date triples) -- the audit trail
  - `computed_by` (optional, script reference) -- distinguishes "read from CIM" vs "computed from invoice file"
  - `notes` (optional, free text) -- escape hatch for context that doesn't fit other fields
  - `flagged` (optional, structured object: reason + date) -- pushed into supersedes chain on resolution; absent when not flagged

### Template content depth
- Structural + commented guidance (HTML comments with `<!-- -->`)
- Each template has full section structure (headings, frontmatter keys) plus comment blocks explaining what goes where, why, and showing the exact entry format
- Zero example data entries (no fake facts, no fake sources)
- Comment blocks include one illustrative entry structure (inside the comment, not parseable as real data)
- Files parse cleanly and are structurally valid immediately after init
- Parser requirement: HTML-comment-aware walking that skips content between `<!--` and `-->` -- prevents commented examples from being parsed as real entries
- Phase 1 test required: parse TRUTH.md template containing example comment block, confirm zero facts returned
- DEAL.md: frontmatter has structured fields from init prompts, body is the analyst's thesis prose (not in frontmatter; multiline YAML strings are fragile)
- WORKSTREAMS.md: pre-populated with the workstreams the analyst selected at init time (real entries, not examples)
- STATE.md: comment explaining the file is mostly written by other commands

### Doctor behavior
- Three check layers: (1) all 6 files exist and are non-empty, (2) each file parses without error per its schema, (3) cross-file references are valid (source IDs in TRUTH.md exist in SOURCES.md, workstream tags match WORKSTREAMS.md)
- Report-only, always. Doctor never mutates state files. No --fix flag. Analyst runs suggested commands or edits manually
- Three severity levels: error (broken, must fix), warning (suspicious, should check), info (cosmetic/status)
- Each finding has: severity, file (relative path), location (line number or section name), description (one sentence), fix (one sentence naming a specific command or action)
- Exit code reflects highest severity: 0 for clean/info-only, 1 for errors, configurable via --strict to treat warnings as errors
- Plain text by default, no emojis, no color by default. Severity conveyed by leading word (ERROR, WARNING, INFO)
- `--json` flag for structured output (array of finding objects with same fields)
- `--strict` flag treats warnings as errors (exits non-zero on any warning)
- Summary line at bottom: "N errors, N warnings, N info"

### CLI output contract (cross-cutting)
- Every list and report command supports `--json` for agent consumption
- Plain text for humans by default, no emojis, no color by default
- No interactive prompts in any command except init (XC-07 scoped to agent-invoked commands)

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- None. Greenfield project with no existing Python code.

### Established Patterns
- No patterns yet. Phase 1 establishes the foundational patterns all subsequent phases build on.
- PRD specifies: click for CLI framework, pyyaml for YAML, hatchling build backend
- PRD specifies package layout: `diligent/` package with `cli.py`, `commands/`, `state/`, `helpers/`, `skills/`, `templates/` subdirectories

### Integration Points
- `Diligent/` subdirectory exists as a git submodule (has its own `.git`). The Python package likely lives here.
- `PRD/` directory contains the full PRD and context brief for reference during development.

</code_context>

<specifics>
## Specific Ideas

- Init thesis prompt should use git-commit-style template: 3-4 commented prompt lines, blank space below, comment lines stripped on save
- TRUTH.md format driven by the "11 PM Ctrl+F use case": analyst opens the file in a text editor, scrolls to find a fact, and reads value/source/history with their eyes. Format must survive that use case.
- Doctor output modeled after real diagnostic tools: no AI template phrasing, severity as leading word, fix suggestions are copy-pasteable commands
- The analyst must be able to rip out `.diligence/` and lose nothing except the state layer. Source documents are never moved or modified.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-04-07*
