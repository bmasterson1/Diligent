# Phase 4: Workstreams, Tasks, and Questions - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Organizational layer for structuring deal work. `diligent workstream new/list/show`, `diligent task new/list/complete`, and `diligent ask/answer/questions list`. The analyst can organize deal work into workstreams with tasks and track open questions that surface naturally from the truth verification process.

Requirements: WS-01 through WS-06, TASK-01 through TASK-03, Q-01 through Q-05.

QUESTIONS.md and WORKSTREAMS.md already exist as state files with readers/writers from prior phases. This phase adds the CLI surface and extends the models where needed.

</domain>

<decisions>
## Implementation Decisions

### Workstream structure (WS-01)
- `workstream new <name>` creates subdirectory under `.diligence/workstreams/<name>/` with CONTEXT.md and RESEARCH.md
- CONTEXT.md holds durable scope: what this workstream investigates, who is involved, what is in/out of scope
- RESEARCH.md holds growing record of findings. Starts generic (no workstream-specific template). Different write cadence, different lifespan, different reader than CONTEXT.md
- Both files start from templates with HTML comment guidance, same pattern as top-level state files

### Workstream templates (WS-04)
- 6 pre-defined templates: financial, retention, technical, legal, hr, integration
- Each template has a tailored CONTEXT.md with 3-4 commented section headers suggesting common areas to cover (e.g., financial gets revenue quality, cost structure, working capital, add-backs)
- RESEARCH.md stays generic across all templates -- real research does not fit a template
- Tailoring is light: enough to orient, not enough to prescribe

### Workstream customization at init (WS-05)
- During `diligent init`, present the 6 defaults as a checklist. Analyst toggles which ones they want
- Selected workstreams get created with subdirectories and tailored CONTEXT.md files
- Non-interactive mode: `--workstreams financial,retention,technical` flag accepts comma-separated list
- Custom workstream names beyond the 6 templates: `workstream new <name>` uses generic CONTEXT.md template

### WorkstreamEntry model extension
- Add `description` field (one-line, from tailored template or analyst input)
- Add `created` field (ISO 8601 date, auto-recorded)
- Status values: active, complete, on-hold

### Workstream show (WS-03)
- Lightweight summary aggregating stats from existing state files scoped to that workstream
- Shows: description, status, task counts (open/complete), open question count, fact count, artifact count (with stale count)
- Reads WORKSTREAMS.md, QUESTIONS.md, TRUTH.md, ARTIFACTS.md, and task directories. No new data structures

### Workstream list (WS-02)
- One line per workstream: name, status, task count, question count. Aligned columns
- Summary line at bottom

### Task directory structure (TASK-01)
- `task new <workstream> <desc>` creates numbered directory under workstream: `.diligence/workstreams/<ws>/tasks/NNN-<slug>/`
- Task ID is zero-padded monotonic number (001, 002, ...), scanned from existing directories (self-healing, no counter)
- Directory contains SUMMARY.md (scaffolded empty), PLAN.md (optional template), VERIFICATION.md (optional template)
- Slug derived from description (lowercase, hyphens, truncated)

### Task status
- Two states only: open, complete
- No in-progress, blocked, or deferred. The analyst knows what they are working on. Questions track open items separately

### Task complete (TASK-03)
- `task complete <workstream> <task-id>` marks status as complete
- Validates SUMMARY.md is non-empty. If empty, exits non-zero with message: "Write SUMMARY.md before completing"
- No prompts, no editor launch. SUMMARY.md is written during the task work by the analyst or AI. Consistent with XC-07

### Task list (TASK-02)
- One line per task: ID, description, status. Aligned columns
- Summary line at bottom: "N tasks: N complete, N open"
- Requires workstream as positional argument

### Question ask (Q-01)
- `diligent ask "<text>" --workstream <ws> --owner <owner>`
- Question text is positional. Workstream and owner are optional flags (default to empty string and "self" respectively)
- Question ID auto-generated: Q-NNN format, zero-padded, monotonic, scanned from QUESTIONS.md max (self-healing)
- No deal code prefix -- questions are deal-internal

### Question answer (Q-03)
- `diligent answer <q-id> "<text>" --source <source-id>`
- Answer text is positional. --source is optional (some questions do not have source-doc answers)
- Status changes to "answered". Answer text and source stored in the QuestionEntry

### QuestionEntry model extension
- Add `answer` field (Optional[str]) -- the answer text
- Add `answer_source` field (Optional[str]) -- source ID if provided
- Add `date_answered` field (Optional[str]) -- ISO 8601 when closed

### Question list (Q-04)
- One line per question: ID, origin tag [gate] or [manual], question text (truncated), workstream, owner, status. Aligned columns
- Gate-rejected questions have context field populated; manual questions do not. Origin derived from whether context is None
- Summary line at bottom: "N questions: N open, N answered"
- `--owner` filter supported per Q-04

### Gate-rejected vs manual questions (Q-05)
- All questions in one list, same QUESTIONS.md file, same answer flow
- Origin indicator in list output: [gate] vs [manual], derived from context field presence
- Gate-rejected questions keep their context (key, old/new values, sources, delta) for provenance

### Cross-entity relationships
- Workstream is the only structural link between entities (tasks, questions, facts, artifacts)
- All list/filter commands use consistent `--workstream` flag for scoping
- Tasks are positional: `task list <workstream>`, `task new <workstream> <desc>`, `task complete <workstream> <task-id>`
- No formal references field on tasks. If analyst wants to note which truth keys a task investigated, they write it in SUMMARY.md

### Claude's Discretion
- Exact workstream template content (the 3-4 section headers per workstream type)
- RESEARCH.md generic template content
- Task slug generation algorithm (lowercase, hyphens, truncation rules)
- PLAN.md and VERIFICATION.md optional template content
- Column alignment widths in list outputs
- Whether `workstream list` shows description or just name

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `WorkstreamEntry` model (state/models.py): exists with name + status. Needs description + created fields added
- `WorkstreamsFile` model + `read_workstreams`/`write_workstreams` (state/workstreams.py): full H2+YAML reader/writer. Needs update for new fields
- `QuestionEntry` model (state/models.py): exists with id, question, workstream, owner, status, date_raised, context. Needs answer, answer_source, date_answered fields added
- `QuestionsFile` model + `read_questions`/`write_questions` (state/questions.py): full H2+YAML reader/writer. Needs update for new fields
- `atomic_write` (helpers/io.py): temp file, fsync, os.replace with OneDrive retry
- `LazyGroup` CLI scaffold (cli.py): new command groups register here
- `formatting.py` helper: output_result for --json, reusable for aligned column output
- Template rendering (templates/__init__.py): render_template with string.Template substitution
- Gate rejection already writes to QUESTIONS.md in truth_cmd.py -- questions from gate have context populated

### Established Patterns
- H2 + fenced YAML per entry, replicated per state file module
- Atomic write with validate_fn that re-parses output before commit
- Exit-code gate pattern for confirmations (truth set --confirm, artifact register --confirm)
- Monotonic ID generation by scanning existing entries (source IDs scan SOURCES.md)
- Relative paths stored as posix strings for cross-platform OneDrive sync
- HTML comment stripping before parsing
- LazyGroup defers imports at group creation for <200ms startup
- No interactive prompts in commands (XC-07). Init is the only exception

### Integration Points
- New command groups: `workstream` (new, list, show), `task` (new, list, complete), `ask`/`answer`/`questions` under LazyGroup
- Init command: update to include workstream checklist (WS-05) and create subdirectories
- Doctor: validate workstream subdirectory integrity, cross-reference workstream names in QUESTIONS.md and TRUTH.md against WORKSTREAMS.md
- WorkstreamEntry model extension: add description, created fields
- QuestionEntry model extension: add answer, answer_source, date_answered fields
- workstream show: reads TRUTH.md, QUESTIONS.md, ARTIFACTS.md, and task directories for aggregated stats

</code_context>

<specifics>
## Specific Ideas

- CONTEXT.md vs RESEARCH.md split rationale: different write cadences, different lifespans, different readers. CONTEXT.md is the durable scope document. RESEARCH.md is the growing record. Collapsing them creates a file that grows unbounded or gets treated as a scratchpad
- Workstream templates are not checklists. 3-4 commented section headers per workstream type. Enough to orient a new analyst on what a financial workstream typically covers, not enough to prescribe a structure they abandon after the first deal
- Task completion validates SUMMARY.md is non-empty but does not prompt for content. The work product is the SUMMARY.md file itself, written during the task, not captured at completion time
- Answer --source is optional because not every question has a source-document answer. "What's Phil's preference on holdback structure?" comes from a conversation. Forcing --source pushes analysts to invent fake sources or skip the command
- Gate-rejected vs manual questions: same list, same answer flow, just an origin tag. The analyst does not care about the provenance system when resolving questions -- they care about the question itself

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 04-workstreams-tasks-questions*
*Context gathered: 2026-04-08*
