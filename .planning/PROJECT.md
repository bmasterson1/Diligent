# diligent

## What This Is

A CLI and state-management layer for lower-middle-market acquisition due diligence. diligent sits inside a deal folder alongside source documents and analyst-produced artifacts, providing structured markdown state files that any AI agent can read and write through a small set of disciplined commands. The tool is built for a single analyst working inside an AI-assisted IDE (Antigravity, Claude Code) who needs to know what is currently true, where each fact came from, which artifacts are stale, and what remains open.

## Core Value

When the analyst types one command, they get a definitive answer about what is current truth and which deliverables need to be refreshed. The reconciliation discipline that currently lives in the analyst's head lives on disk instead.

## Requirements

### Validated

- INIT-01..08: CLI scaffold, state roundtrip, doctor, config, pyproject, atomic writes, schema version, lazy startup -- v1.0
- SRC-01..07: Source ingestion with auto-diff, monotonic IDs, list/show/diff, Excel/Word helpers -- v1.0
- TRUTH-01..12: Truth set/get/list/trace/flag, verification gate, tolerance config, append-only, quoted strings, computed-by/notes -- v1.0
- ART-01..09: Artifact register/list/refresh, reconcile engine, workstream filter, strict mode, docx scanner -- v1.0
- WS-01..06: Workstream new/list/show, 6 tailored templates, init customization, hand-edit support -- v1.0
- TASK-01..03: Task new/list/complete with directory-based storage -- v1.0
- Q-01..05: Ask/answer/questions list, owner taxonomy, gate rejection routing -- v1.0
- STATE-01..06: Status summary, plain text/JSON, handoff with time-window filtering, paste buffer output -- v1.0
- DIST-01..06: PyPI as diligent-dd, skill file install for Antigravity/Claude Code, parameterized paths -- v1.0
- XC-01..08: Performance (<2s/<10s), no network, read-only sources, atomic writes, --json, no prompts, BSL 1.1 -- v1.0

### Active

(No active requirements. Define next milestone with `/gsd:new-milestone`.)

### Out of Scope

- Web UI or dashboard. The IDE is the UI.
- Multi-user collaboration, permissions, or roles. Single analyst per deal folder.
- Database backend (SQLite, DuckDB). Markdown is the backend.
- Built-in LLM integration. AI lives in the IDE runtime, not in diligent.
- Document OCR or automated fact extraction from PDFs. The analyst (with AI) is the extraction engine.
- VDR, CRM, or accounting system integration.
- Git orchestration (branching, auto-commit). The analyst manages git themselves.
- TUI or GUI.
- Skill packages for runtimes other than Antigravity and Claude Code (v1.0 scope; Cursor/Windsurf deferred to v2).

## Context

diligent v1.0 shipped 2026-04-09. 17,475 lines of Python across 81 files. 504 tests passing. 70/70 requirements satisfied with 9 tech debt items tracked.

Built by Bryce Masterson for immediate dogfooding on Project Arrival, a live post-LOI acquisition of OnTime 360 (B2B SaaS courier dispatch, ~$2.4M ARR, ~$9.5M EV). The tool exists because Bryce has hit state drift repeatedly across nine versions of retention analyses, investor decks, and briefing memos. The pain point: when a source document updates, nothing in the current workflow tells the analyst which downstream artifacts are now stale.

The design is directly inspired by GSD's structural insight (markdown state files that any agent can read at session start) applied to diligence instead of software engineering. The key difference: in coding, truth is the running code; in diligence, truth is a set of validated quantitative facts about a business that must be cached and traced because there is no "re-run the program."

TRUTH.md is the most important file in the system. Every design decision should be filtered through: "does this serve the discipline of TRUTH.md being the single source of validated facts?"

**Current state:** v1.0 shipped. Package published locally as wheel (`diligent-dd-0.1.0`). PyPI upload pending manual `twine upload`. 17 CLI commands registered. Full state layer for 8 files. Reconcile engine verified at scale (200 sources, 500 facts, 100 artifacts under 10s).

**Known tech debt from v1.0:**
- doctor/config/migrate don't walk parent directories (inconsistent with 10 other commands)
- workstream show staleness undercount vs full reconcile engine
- truth trace --verbose deferred
- write_state intentionally orphaned

## Constraints

- **Platform**: Windows primary (OneDrive-synced deal folders), macOS/Linux supported. Python 3.11+.
- **Distribution**: PyPI as `diligent-dd`. Installed via pipx.
- **Dependencies**: Minimized. click, pyyaml, openpyxl, python-docx, pypdf/pdfplumber. Optional: rich.
- **License**: BSL 1.1. Individual use free; service-provider use requires commercial license. Converts to Apache 2.0 after 4 years.
- **Performance**: All commands < 2s, reconcile < 10s, no background processes.
- **Privacy**: Zero network, zero telemetry, zero credentials. Source documents are read-only.
- **Editorial**: Source every claim, stop at verification gates, no AI template phrasing, no em dashes, concise output.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI + skill files, not web app or TUI | Must live where the work already lives (IDE terminal). Agent tool-use loop needs CLI semantics. | Good -- 17 commands, 6 skill files, no UI debt |
| Python, not TypeScript or Go | Helper scripts do data work on Excel/Word files; openpyxl/python-docx are de facto standard. User already writes Python. | Good -- 17k LOC, all helpers work |
| Markdown state files, not SQLite | AI agent reads markdown directly into context window. Human-inspectable, git-diffable, grep-able. | Good -- H2+YAML pattern replicated cleanly across 8 files |
| TRUTH.md append-only at entry level | Prevents silent overwrites. Free audit trail. Most common state corruption is losing what a value used to be. | Good -- supersedes chain works, trace shows full history |
| Source documents never moved or modified | diligent is a metadata layer. User can rip out .diligence/ and lose nothing except state. Safe to test on live deal. | Good -- read-only confirmed by test and code review |
| No AI integration inside diligent | Zero-config, zero-credential, zero-cost, runtime-agnostic. AI is a consumer of state, not a component. | Good -- skill files bridge the gap without coupling |
| BSL 1.1 license | Author retains commercial rights. Source-available for inspection. Colleagues get free grants. Converts to Apache 2.0 after 4 years. | Good -- LICENSE file ships in wheel |
| PyPI name: diligent-dd | `diligent` was taken on PyPI. CLI entry point remains `diligent`. | Good -- resolved before first publish |
| H2+YAML parsing replicated per module | Readability over DRY. Each state reader is self-contained. | Good -- 6 independent readers, no shared fragility |
| Verification gate routes to questions queue | TRUTH-04 rejection writes QuestionEntry with gate context. Connects truth management to question tracking. | Good -- load-bearing behavior, fully tested |
| reconcile_anchors.py as pure function | Zero I/O imports. Maximum testability. CLI wrapper handles file reads. | Good -- 16 engine tests + 13 CLI tests |
| Domain-grouped skill files (6) vs one-per-command (14+) | Keeps skill count manageable. Each file covers a coherent domain. | Good -- all commands documented, dd: prefix |

---
*Last updated: 2026-04-09 after v1.0 milestone*
