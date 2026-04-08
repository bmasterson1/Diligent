# Phase 5: Status, Handoff, and Distribution - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Full deal state aggregation (`diligent status`), AI session restore document (`diligent handoff`), PyPI packaging and publishing, and IDE skill file installation (`diligent install --claude-code`, `--antigravity`). The analyst gets the whole deal at a glance in one command, can restore AI context in a fresh session by pasting a single document, and can install diligent from PyPI with skill files that teach AI agents how to use the CLI.

Requirements: STATE-01 through STATE-06, DIST-01 through DIST-06.

</domain>

<decisions>
## Implementation Decisions

### Status output (STATE-01, STATE-02)
- Sectioned report format by default: deal header, workstreams, stale artifacts, open questions, recent activity. Five sections, each capped at ~5 items with "and N more" truncation
- Header line: deal name, target name, stage, LOI date, days-in-diligence counter. Counter uses LOI date as the baseline. Pre-LOI fallback: "N days tracking" from STATE.md created date, different label
- Workstreams section: one line per workstream with inline counts (facts, questions, artifacts, stale count)
- Stale artifacts section: artifact path, count of changed facts, days since refresh
- Open questions section: ID, origin tag [gate]/[manual], workstream, truncated question text. Capped at 5 with "and N more" line
- Recent activity section: derived from timestamps across all state files (no event log, no new data structure). Verb-past-tense format: "2d ago  ingested ...", "4d ago  completed ...". Relative time under 14 days, absolute date beyond
- Summary line at bottom: "N items need attention"
- Always deal-wide scope. No `--workstream` filter. Workstream-scoped view comes from `workstream show`
- `--verbose` expands each section to show all items
- `--json` emits structured output for agent consumption
- Plain text, no emojis, no color by default (consistent with all prior phases)

### Handoff document (STATE-03, STATE-04, STATE-05, STATE-06)
- No hard token cap. Handoff is "dumb and complete": include everything, let the analyst trim before pasting
- Default content: DEAL.md in full, WORKSTREAMS.md in full, recent TRUTH.md facts (touched in last 14 days), recent SOURCES.md entries (ingested in last 14 days), all open questions, all stale/flagged artifacts, most recent SUMMARY.md from each active workstream
- Recency + urgency rule: time window applies to facts/sources/activity, but all open questions, flagged facts, and stale artifacts are always included regardless of date
- `--since` flag overrides the 14-day default (e.g., `--since 7d`, `--since 2026-03-15`). Configurable default via `recent_window_days` in config.json (already exists, default 7 -- handoff default is 14 days, double the config value)
- `--everything` bypasses the time window entirely and dumps complete state files
- Instruction header at the top of every handoff document: brief block explaining what diligent is, key concepts (TRUTH.md, SOURCES.md, ARTIFACTS.md, QUESTIONS.md, WORKSTREAMS.md), and editorial principles (source every claim, never invent values, flag discrepancies rather than resolving silently, no AI template phrasing). Header is static template content with deal name substituted in
- `---` separator between header and deal state data
- Output to stdout by default. `--clip` flag copies to clipboard AND prints to stdout. Clipboard via platform subprocess calls (clip.exe on Windows, pbcopy on macOS, xclip/wl-copy on Linux). If clipboard unavailable, warning message, no crash
- Paste buffer, not file-on-disk reference (STATE-06). Portable across runtimes

### Skill file design (DIST-02, DIST-03, DIST-05, DIST-06)
- Grouped by domain, not one-per-command. ~6 SKILL.md files: dd:truth, dd:sources, dd:artifacts, dd:questions, dd:workstreams, dd:status. Each covers related subcommands
- DIST-06 updated: "one SKILL.md per domain (6 files), prefixed dd: in runtime command namespace, each skill covers related subcommands"
- Structured content per skill: description (for runtime matching), when-to-use triggers, command reference (flags, args, examples), rules (source citations, no inventing values, gate handling), common workflows
- Parameterized with CLI binary path only (`{{DILIGENT_PATH}}` replaced at install time via `shutil.which('diligent')`). No deal directory or deal code in skills -- skills are installed globally, not per-deal
- Skill templates shipped inside the Python package (diligent/skills/ directory)
- `diligent install --claude-code` writes skills to `~/.claude/skills/` (default convention). `--antigravity` writes to Antigravity's skills directory (verify actual path before building)
- `--path` flag overrides default install directory if convention is wrong
- `diligent install --uninstall` removes installed skill files. Knows which files it wrote by naming convention (dd_*.md or similar)
- Fail with clear error if target directory doesn't exist

### PyPI and packaging (DIST-01)
- Check PyPI availability for "diligent" before first publish. If free, use it. If taken, fallback preference: (1) different real word from brief's list (tether, plumb, searchlight, bedrock, veritas, anchor), (2) diligent-dd or diligent-cli suffix, (3) dd-diligent prefix
- Whatever the package name, CLI entry point stays `diligent`
- Reserve the name on PyPI early (0.0.0 placeholder release) once confirmed
- pyproject.toml already has hatchling build backend, entry point, BSL license, and core dependencies. No new dependencies for Phase 5 features (clipboard is platform subprocess, no pyperclip)
- README: minimal + quickstart format. One-paragraph description, install command, 5-7 step quickstart (init through status), "what it is not" section (not a VDR, not a PM tool, not a replacement for Word/Excel), links to USER-GUIDE.md and LICENSE. Under 100 lines
- Full command reference goes in USER-GUIDE.md, not README
- Onboarding validation: manual smoke test on clean machine/venv. Documented checklist in README quickstart section. No automated quickstart script in v1

### Clipboard helper
- Platform subprocess wrapper, ~15 lines. clip.exe (Windows), pbcopy (macOS), wl-copy then xclip (Linux)
- Returns bool success. On failure, handoff prints warning "Clipboard not available on this system" and continues. On success, prints "Copied to clipboard."
- No new dependencies in pyproject.toml

### Claude's Discretion
- Exact section ordering within status output (workstreams first vs stale first)
- Activity event type list and rendering format details
- Handoff section ordering within the data portion
- Skill file exact content and wording (given the structured template pattern)
- Skill install path for Antigravity (needs verification of actual directory convention)
- README exact wording and quickstart step selection
- Whether `--since` accepts relative durations (7d) or only ISO dates, or both

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `read_truth`/`read_sources`/`read_artifacts`/`read_questions`/`read_workstreams` -- all 8 state file readers available for status aggregation
- `ConfigFile` model with `recent_window_days` field (default 7) -- already exists for recency configuration
- `DealFile` model with deal_code, target names, stage, LOI date -- header line data
- `StateFile` model with created field -- fallback for pre-LOI days counter
- `output_result` helper (formatting.py) -- dual text/JSON output pattern
- `output_findings` helper (formatting.py) -- diagnostic output pattern
- `LazyGroup` CLI scaffold (cli.py) -- new commands register here
- `atomic_write` (helpers/io.py) -- not directly needed for read-only commands but available
- Template rendering (templates/__init__.py) -- `render_template` with string.Template substitution, reusable for skill file parameterization

### Established Patterns
- H2 + fenced YAML per entry, replicated per state file module
- LazyGroup defers imports at group creation for <200ms startup
- Plain text default, `--json` flag for structured output, no emojis, no color
- No interactive prompts in commands (XC-07)
- Relative paths stored as posix strings for cross-platform OneDrive sync
- Exit-code gate pattern (truth set --confirm, artifact register --confirm) -- not directly used in Phase 5 but established

### Integration Points
- New commands: `status`, `handoff`, `install` registered in LazyGroup
- Status reads all 8 state files plus task directories for complete aggregation
- Handoff reads same state files with time-window filtering
- Install writes to directories outside .diligence/ (global skill install)
- pyproject.toml needs README path configured for PyPI long_description
- Skill templates need to ship as package data (include in hatchling build)

</code_context>

<specifics>
## Specific Ideas

- Status is the "morning-coffee command." The analyst runs it to answer "what's happening on this deal and what needs my attention today?" without follow-up commands
- Status header format locked: "Project Arrival -- OnTime 360 (Vesigo Studios, LLC)\nStage: post-LOI | LOI: 2026-01-15 | 57 days in diligence"
- Pre-LOI header adaptation: "Stage: pre-LOI | 12 days tracking" (different label, no LOI date shown)
- Handoff instruction header teaches the receiving agent the editorial principles that matter: source every claim, never invent values, flag discrepancies, no AI template phrasing. This is the mechanism that preserves working style across sessions
- Handoff recency is double the config value: config `recent_window_days` defaults to 7, handoff default window is 14 days. This can be adjusted independently via `--since`
- Skill files are globally installed, not per-deal. The analyst runs `diligent install --claude-code` once per machine, not once per deal
- README "what it is not" section cuts through the "is this the right tool for me" question before the reader scrolls past the install command
- Platform clipboard wrapper returns bool and never crashes the parent command

</specifics>

<deferred>
## Deferred Ideas

- Skill packages for Cursor, Windsurf, and other AI-IDE runtimes (RT-01, v2)
- Auto-suggest which facts an ingested document might affect (ING-02, v2)
- USER-GUIDE.md full command reference (ships separately from README, not blocking for v1 PyPI publish but should follow shortly)

</deferred>

---

*Phase: 05-status-handoff-distribution*
*Context gathered: 2026-04-08*
