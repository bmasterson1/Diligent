# diligent

## What This Is

A CLI and state-management layer for lower-middle-market acquisition due diligence. diligent sits inside a deal folder alongside source documents and analyst-produced artifacts, providing structured markdown state files that any AI agent can read and write through a small set of disciplined commands. The tool is built for a single analyst working inside an AI-assisted IDE (Antigravity, Claude Code) who needs to know what is currently true, where each fact came from, which artifacts are stale, and what remains open.

## Core Value

When the analyst types one command, they get a definitive answer about what is current truth and which deliverables need to be refreshed. The reconciliation discipline that currently lives in the analyst's head lives on disk instead.

## Requirements

### Validated

(None yet. Ship to validate.)

### Active

- [ ] CLI scaffolds `.diligence/` directory with all core state files via `diligent init`
- [ ] State file readers/writers round-trip all six core files (DEAL.md, TRUTH.md, SOURCES.md, WORKSTREAMS.md, STATE.md, config.json)
- [ ] `diligent doctor` validates file integrity and reports corruption
- [ ] `diligent ingest` logs source documents with supersedes chain logic
- [ ] `diligent sources list/show/diff` commands for source document management
- [ ] `diligent truth set/get/list/trace/flag` commands for fact management with citation tracking
- [ ] TRUTH.md is append-only at the entry level: updates push prior values into supersedes chain
- [ ] `diligent artifact register/list/refresh` commands for deliverable tracking
- [ ] `diligent reconcile` detects stale artifacts by walking the dependency graph against TRUTH.md
- [ ] `diligent workstream new/list/show` and `diligent task new/list/complete` commands
- [ ] `diligent ask/answer/questions` commands for open question tracking
- [ ] `diligent status` provides full state summary across all files
- [ ] `diligent handoff` generates structured prompt for clean AI session restoration
- [ ] `diligent install --antigravity/--claude-code` installs SKILL.md files into IDE runtimes
- [ ] Python helper scripts: fact_parser.py, reconcile_anchors.py, diff_excel_versions.py, extract_text.py, artifact_scanner.py
- [ ] All commands return in under 2 seconds for typical deal folder; reconcile under 10 seconds
- [ ] Atomic file writes (write to temp, fsync, rename) for crash safety
- [ ] No network requests, no API keys, no telemetry
- [ ] Distributed via PyPI, installed via pipx

### Out of Scope

- Web UI or dashboard. The IDE is the UI.
- Multi-user collaboration, permissions, or roles. Single analyst per deal folder.
- Database backend (SQLite, DuckDB). Markdown is the backend.
- Built-in LLM integration. AI lives in the IDE runtime, not in diligent.
- Document OCR or automated fact extraction from PDFs. The analyst (with AI) is the extraction engine.
- VDR, CRM, or accounting system integration.
- Git orchestration (branching, auto-commit). The analyst manages git themselves.
- TUI or GUI.
- Skill packages for runtimes other than Antigravity and Claude Code.

## Context

diligent is being built by Bryce Masterson for immediate dogfooding on Project Arrival, a live post-LOI acquisition of OnTime 360 (B2B SaaS courier dispatch, ~$2.4M ARR, ~$9.5M EV). The tool exists because Bryce has hit state drift repeatedly across nine versions of retention analyses, investor decks, and briefing memos. The pain point: when a source document updates, nothing in the current workflow tells the analyst which downstream artifacts are now stale.

The design is directly inspired by GSD's structural insight (markdown state files that any agent can read at session start) applied to diligence instead of software engineering. The key difference: in coding, truth is the running code; in diligence, truth is a set of validated quantitative facts about a business that must be cached and traced because there is no "re-run the program."

TRUTH.md is the most important file in the system. Every design decision should be filtered through: "does this serve the discipline of TRUTH.md being the single source of validated facts?"

## Constraints

- **Platform**: Windows primary (OneDrive-synced deal folders), macOS/Linux supported. Python 3.11+.
- **Distribution**: PyPI under `diligent` (name conflict to resolve). Installed via pipx.
- **Dependencies**: Minimized. click/typer, pyyaml, openpyxl, python-docx, pypdf/pdfplumber. Optional: rich.
- **License**: BSL 1.1. Individual use free; service-provider use requires commercial license. Converts to Apache 2.0 after 4 years.
- **Performance**: All commands < 2s, reconcile < 10s, no background processes.
- **Privacy**: Zero network, zero telemetry, zero credentials. Source documents are read-only.
- **Editorial**: Source every claim, stop at verification gates, no AI template phrasing, no em dashes, concise output.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI + skill files, not web app or TUI | Must live where the work already lives (IDE terminal). Agent tool-use loop needs CLI semantics. | Pending |
| Python, not TypeScript or Go | Helper scripts do data work on Excel/Word files; openpyxl/python-docx are de facto standard. User already writes Python. | Pending |
| Markdown state files, not SQLite | AI agent reads markdown directly into context window. Human-inspectable, git-diffable, grep-able. | Pending |
| TRUTH.md append-only at entry level | Prevents silent overwrites. Free audit trail. Most common state corruption is losing what a value used to be. | Pending |
| Source documents never moved or modified | diligent is a metadata layer. User can rip out .diligence/ and lose nothing except state. Safe to test on live deal. | Pending |
| No AI integration inside diligent | Zero-config, zero-credential, zero-cost, runtime-agnostic. AI is a consumer of state, not a component. | Pending |
| BSL 1.1 license | Author retains commercial rights. Source-available for inspection. Colleagues get free grants. Converts to Apache 2.0 after 4 years. | Pending |
| Name: diligent | Working name locked. PyPI conflict to resolve before first publish. | Pending |

---
*Last updated: 2026-04-07 after initialization*
