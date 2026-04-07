# Feature Landscape

**Domain:** CLI state-management for acquisition due diligence (single analyst, AI-assisted IDE)
**Researched:** 2026-04-07
**Confidence:** MEDIUM (training data domain knowledge; web search unavailable for verification)

## Table Stakes

Features the analyst expects. Missing any of these and the tool fails to replace the Excel tracker it is competing with.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Init/scaffold deal folder** | Every DD tool starts with project setup. Analyst must get from zero to working state in one command. | Low | `diligent init` with sane defaults for .diligence/ directory |
| **Source document registry** | Analyst tracks 50-200 documents per deal. Must know what exists, when received, from whom. Every DD platform (DealRoom, Datasite, Ansarada) has this as core. | Medium | Supersedes-chain logic (v2 replaces v1) is the key differentiator over a flat list |
| **Fact storage with provenance** | The entire value proposition. Every validated number must trace to a source document, page, and date. Without this, TRUTH.md is just a notes file. | Medium | Append-only entry semantics with supersedes chain. This is the soul of the tool. |
| **Staleness detection / reconciliation** | The core pain point: source doc updates but downstream artifacts (models, memos, decks) are not flagged. This is why diligent exists. | High | Dependency graph walk: source -> fact -> artifact. Most complex feature. |
| **Artifact tracking** | Analyst produces 10-30 deliverables per deal. Must know which are current vs stale. Excel trackers do this via a "last updated" column. | Low | Register artifact, associate with facts it depends on, flag when upstream changes |
| **Full status / dashboard command** | Analyst opens terminal, types one command, knows the state of the deal. This is the "morning standup" equivalent. | Medium | Aggregates across all state files. Must be fast (<2s). |
| **Workstream and task tracking** | DD is organized into streams (financial, legal, commercial, technical). Tasks within streams have owners and status. Every DD checklist tool does this. | Low | Lightweight. Not a project management tool -- just enough to know what is open. |
| **Open questions tracking** | During DD, analysts accumulate questions for management, advisors, and sellers. Must track question -> answer -> source linkage. | Low | Questions are a first-class entity because unanswered questions are blockers. |
| **Session handoff / context restore** | AI sessions die. The analyst must be able to resume with a new session that has full context. This is table stakes for AI-assisted workflows. | Medium | Generates structured prompt summarizing current state, recent changes, open items |
| **Data integrity validation** | State files will get corrupted by hand-edits, merge conflicts, or bugs. Must detect and report. | Medium | `diligent doctor` validates all files, reports issues, suggests fixes |
| **Atomic file writes** | OneDrive-synced folders + concurrent access = corruption risk. Write-temp-fsync-rename is mandatory. | Low | Infrastructure concern but table stakes for trust. Analyst must never lose state. |
| **Zero network / zero config** | DD data is confidential. Tool must never phone home, require API keys, or leak data. This is a trust prerequisite for adoption on live deals. | Low | Explicit design constraint. No telemetry, no analytics, no update checks. |

## Differentiators

Features that set diligent apart from DealRoom/Midaxo (web platforms) and Excel trackers (manual workflows). Not expected, but create competitive advantage.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Supersedes chains on facts** | When a revenue number changes from $2.1M to $2.4M, you see the full history: what it was, when it changed, why, and which source drove the change. Excel trackers overwrite. DD platforms track document versions but not fact versions. | Medium | Append-only at entry level. Prior values pushed to supersedes array. Free audit trail. |
| **Dependency graph (source -> fact -> artifact)** | No DD tool connects the chain end-to-end. DealRoom tracks documents. Excel tracks numbers. Neither tells you "the retention analysis is stale because the revenue figure it uses was updated yesterday." | High | This is the hardest feature and the biggest value. Graph must be fast to walk. |
| **Markdown-native state (AI-readable)** | State files are the AI context window. No API adapter, no export, no translation layer. Claude/Antigravity reads TRUTH.md directly. Web DD tools require API integration that does not exist for IDE agents. | Low | Design choice, not a feature to build. But it drives every other decision. |
| **IDE skill file installation** | `diligent install --claude-code` drops a SKILL.md that teaches the AI agent how to use diligent commands. Zero manual agent configuration. | Low | Unique to AI-native workflow. No DD tool does this because they are not CLI tools. |
| **Diff-based source comparison** | `diligent sources diff` shows what changed between v1 and v2 of a source document. Excel tracker analysts do this manually with two windows open. | Medium | Requires text extraction from PDF/DOCX/XLSX. Helper scripts handle the heavy lifting. |
| **Structured reconcile output** | `diligent reconcile` does not just say "stale." It says "TRUTH.md entry revenue_arr was updated 2026-04-05 from source financials-v3.xlsx. Artifact retention_analysis.xlsx last refreshed 2026-04-01. 4 days stale." | Medium | Actionable output. Tells analyst exactly what to fix and why. |
| **Git-diffable state** | Every state change is a meaningful diff. Analyst can `git log` the .diligence/ directory and see the history of the deal's validated truth evolving over time. | Low | Free from markdown format choice. But must be intentional: stable sort order, consistent formatting. |
| **Offline-first by design** | Works in air-gapped environments, on planes, in VDR viewing rooms where network access is restricted. Web DD tools fail here. | Low | Already guaranteed by zero-network constraint. Worth marketing explicitly. |
| **Helper scripts for data extraction** | fact_parser.py, diff_excel_versions.py, extract_text.py -- these bridge the gap between raw source documents and structured facts. No DD CLI tool exists to compare two Excel versions programmatically. | Medium | These are the "glue" that makes the CLI workflow practical. Without them, analyst still needs Excel open. |

## Anti-Features

Features to explicitly NOT build. Each is tempting but would compromise the tool's core value or violate design constraints.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Web UI or dashboard** | The IDE IS the UI. Building a web layer splits attention, adds dependencies, and moves the analyst away from where AI agents live. DealRoom already does web dashboards better than diligent ever could. | Use `diligent status` for summary. Rich terminal output via optional `rich` dependency. |
| **Built-in LLM integration** | Adding AI inside the tool creates credential requirements, API cost, vendor lock-in, and network dependency. Violates zero-network constraint. The AI agent in the IDE is already the consumer. | Expose clean CLI semantics. Let IDE agents call diligent commands. Skill files teach agents how. |
| **Multi-user collaboration** | Adds permissions, conflict resolution, locking, merge logic. Massively increases complexity for a single-analyst use case. DealRoom/Midaxo own this space. | Single analyst per deal folder. Collaboration via git (analyst manages). |
| **Database backend (SQLite/DuckDB)** | Destroys AI-readability of state. Agent cannot `cat TRUTH.md` if truth lives in a database. Also adds migration complexity, query language, and tooling dependencies. | Markdown files. Human-readable, grep-able, git-diffable, agent-readable. |
| **Document OCR / automated extraction** | Scope explosion. PDF parsing is a deep domain. Quality varies wildly. Wrong extractions are worse than no extractions because they pollute TRUTH.md. | Analyst + AI agent extract facts together. diligent records the validated result. |
| **VDR / CRM / accounting integration** | Every deal uses different systems. Integration maintenance is unbounded. Each connector is a security surface. | diligent reads files from disk. Analyst exports from VDR to deal folder manually. |
| **Auto-commit / git orchestration** | Git workflow is personal and opinionated. Auto-commits create noise. Wrong commit granularity is worse than no commits. | Analyst manages git. diligent writes files atomically. State is always consistent on disk. |
| **TUI (interactive terminal UI)** | Adds curses/textual dependency. Breaks AI agent tool-use loop (agents call CLI commands, not interactive UIs). Accessibility and testing complexity. | CLI with structured output. Rich formatting via `--format` flag if needed. |
| **Notification system / alerts** | Implies polling, background processes, or daemon. Violates simplicity constraint. Analyst runs `diligent status` when they want to know. | Pull-based: analyst asks, tool answers. `diligent reconcile` is the "check for staleness" command. |
| **Template library for deliverables** | Every deal is different. Templates become opinionated about deal structure. Maintenance burden. Scope creep into consulting methodology. | Analyst creates their own artifacts. diligent tracks them. Skill files can suggest structure via AI. |
| **Scoring or risk assessment** | Quantifying DD risk is subjective and deal-specific. Baking in a scoring model is opinionated in the wrong way. | Track facts with provenance. Track open questions. Let the analyst synthesize risk. |

## Feature Dependencies

```
diligent init
  --> Source document registry (SOURCES.md exists)
  --> Fact storage (TRUTH.md exists)
  --> Workstream/task tracking (WORKSTREAMS.md exists)
  --> State file (STATE.md exists)

Source document registry
  --> Source ingestion (diligent ingest)
  --> Source comparison (diligent sources diff)
  --> Supersedes chain logic

Fact storage with provenance
  --> Requires: Source document registry (facts cite sources)
  --> Supersedes chain on facts
  --> Enables: Staleness detection

Artifact tracking
  --> Requires: Fact storage (artifacts depend on facts)
  --> Enables: Staleness detection / reconciliation

Staleness detection / reconciliation
  --> Requires: Fact storage + Artifact tracking + Source registry
  --> Dependency graph walk (source -> fact -> artifact)
  --> Structured reconcile output

Session handoff
  --> Requires: All state files populated
  --> Reads: TRUTH.md, SOURCES.md, WORKSTREAMS.md, STATE.md

IDE skill file installation
  --> Independent (can ship early)
  --> Enhanced by: All CLI commands being stable

Data integrity validation (doctor)
  --> Requires: All state file formats finalized
  --> Should ship alongside or after core file operations

Helper scripts
  --> Independent of CLI (can be developed in parallel)
  --> diff_excel_versions.py enhances: Source comparison
  --> fact_parser.py enhances: Fact storage workflow
  --> extract_text.py enhances: Source ingestion
```

## MVP Recommendation

Prioritize in this order:

1. **Init + state file round-trip** -- Foundation. Nothing else works without it.
2. **Source document registry with ingest** -- First state file that provides value. Analyst can track what documents they have.
3. **Fact storage with provenance (TRUTH.md)** -- The soul of the tool. Once facts are stored with citations, the analyst has replaced their Excel tracker.
4. **Artifact tracking** -- Register deliverables and their fact dependencies.
5. **Reconciliation** -- The killer feature. Once sources, facts, and artifacts are linked, staleness detection unlocks the core value proposition.
6. **Status command** -- The "one command to know the state" promise.
7. **Session handoff** -- Critical for AI-assisted workflow continuity.

Defer:
- **Workstream/task tracking**: Low urgency. Analyst already has task management elsewhere. Add after core truth-tracking loop works.
- **Open questions**: Useful but not blocking. Can be a text file initially.
- **IDE skill files**: Ship early as a standalone deliverable (low complexity, high perceived value), but not blocking for core functionality.
- **Helper scripts**: Develop in parallel as needed. diff_excel_versions.py is highest value because it directly feeds the source comparison workflow.
- **Source diff**: Nice-to-have after ingest works. Requires helper scripts.

## Comparison: Existing DD Tools vs diligent

| Capability | DealRoom/Midaxo | Excel Tracker | diligent |
|------------|-----------------|---------------|----------|
| Document tracking | Full VDR with permissions | Manual file list | Source registry with supersedes chains |
| Fact versioning | None (document-level only) | Overwrite in cell | Append-only with full history |
| Staleness detection | None | Manual "last updated" column | Automated dependency graph walk |
| AI agent integration | API (if it exists) | None | Native (markdown state = context window) |
| Collaboration | Multi-user, roles, permissions | Shared spreadsheet | Single analyst (by design) |
| Offline access | No (web-based) | Yes | Yes (zero network) |
| Cost | $20K-100K+/year | Free | Free (BSL 1.1) |
| Setup time | Days-weeks (IT involvement) | Minutes | One command |
| Audit trail | Document access logs | None | Git history of state files |
| Customization | Limited to platform features | Unlimited (manual) | Extensible via helper scripts + AI |

## Sources

- Domain knowledge from training data on DealRoom, Midaxo, Datasite, Ansarada DD platforms (MEDIUM confidence)
- PROJECT.md design document and requirements (HIGH confidence -- primary source)
- GSD tool architecture as structural analog (HIGH confidence -- referenced in project context)
- General M&A due diligence analyst workflow patterns (MEDIUM confidence)

*Note: Web search was unavailable during this research session. Feature landscape is based on training data domain knowledge of DD tools and analyst workflows. Recommend verifying competitor feature sets against current DealRoom/Midaxo marketing pages in a follow-up session.*
