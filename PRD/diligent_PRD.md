# diligent

*A context-engineering and state-management system for lower-middle-market acquisition due diligence*

**Product Requirements Document**
**Version 0.1 (Draft)**
**April 7, 2026**
**Author: Bryce Masterson**

---

## Contents

1. [Background and Problem](#1-background-and-problem)
2. [Goals and Non-Goals](#2-goals-and-non-goals)
3. [Users and Workflow](#3-users-and-workflow)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Licensing and Distribution](#6-licensing-and-distribution)
7. [Build Plan](#7-build-plan)
8. [Open Questions](#8-open-questions)
9. [Success Criteria](#9-success-criteria)

---

## 1. Background and Problem

### 1.1 Context

Lower-middle-market acquisition due diligence is a months-long, multi-workstream investigation that produces a constantly evolving picture of a target business. A single deal generates dozens of source documents from the seller and broker (CIMs, financial statements, customer lists, contracts, technical documentation), dozens of derived analytical artifacts produced by the buy-side team (financial models, retention analyses, customer cohort cubes, EBITDA bridges, investor decks, briefing memos), and hundreds of open questions that get answered, partially answered, superseded, or invalidated over time.

The buy-side analyst's central problem is not analytical capability. Modern AI-assisted IDEs (Antigravity, Claude Code, Windsurf, Cursor) and agentic chat tools (Claude Cowork, ChatGPT) have made it trivial to write Python scripts that compute cohort retention, build financial models in Excel, and draft investor-grade Word documents. The central problem is state management: knowing what is currently true, where each fact came from, what document supersedes what, which derived artifacts have gone stale because their source data was updated, and what remains open.

### 1.2 The failure mode

A typical diligence engagement degrades along a predictable path. Week one: the seller delivers an initial document set; the analyst builds a v1 retention analysis. Week two: the seller sends an updated invoice file that changes three customers' MRR; the analyst builds v2 of the retention analysis but does not update the investor deck pulled from v1, because the dependency is implicit and lives only in the analyst's head. Week four: a partner asks a question that requires reconciling a number from the v1 deck against a number from the v2 model; the analyst spends two hours figuring out which is current truth. Week six: a new analyst joins the deal team and cannot reconstruct which assumptions are still load-bearing.

This is the same problem the software engineering community calls context rot: as the working set grows, an unaided human (or unaided LLM) loses the ability to hold all the dependencies in memory and silently begins producing inconsistent output. The Get Shit Done (GSD) framework solves this problem for AI-assisted coding by enforcing a structured set of markdown state files that the agent reads at the start of every action. The structure forces context to live on disk in known locations rather than implicitly in chat history. diligent applies the same insight to acquisition diligence.

### 1.3 Why a DD-specific tool, not generic project management

Existing categories of tools touch this problem but none solve it:

- **Virtual data rooms** (Datasite, Intralinks, Firmex) provide document custody and access control. They do not version analytical conclusions or detect when a derived artifact has gone stale because a source document was updated.
- **Diligence checklist tools** (DealRoom, Midaxo) track question status as open or closed but do not version the answers or trace facts back to source documents.
- **Knowledge management platforms** (Notion, Coda, Obsidian) are flexible but unopinionated. The analyst must invent and enforce the discipline themselves, which is what they are already failing at.
- **Generic AI-IDE tooling** (Antigravity, Claude Code) provides the analytical capability but no persistent state model. Every session starts cold; the agent must be re-briefed by uploading documents and explaining where work left off.

diligent fills the gap by sitting in the deal folder alongside source documents and analyst-produced artifacts, providing a structured state layer that any AI agent can read and write through a small set of disciplined commands.

---

## 2. Goals and Non-Goals

### 2.1 Goals

- **Single source of truth.** Every quantitative fact about the target lives in one structured file (TRUTH.md), with a citation to its source document and a record of what value it superseded.
- **Immutable source register.** Every document received from the seller, broker, or any other external party is logged in SOURCES.md with a date and a supersedes chain. New versions never overwrite old versions.
- **Stale artifact detection.** When a TRUTH.md fact is updated, the system identifies every artifact in the artifact registry that referenced the prior value and flags it as stale until manually refreshed.
- **Workstream-level discipline.** Diligence is organized into named workstreams (financial, retention, technical, legal, HR, commercial) each with their own context, research, atomic analysis tasks, and reconciliation log.
- **Runtime-agnostic state.** The .diligence/ directory is plain text (markdown, JSON, YAML) and is readable by any AI agent operating against the deal folder. The analyst can use Antigravity for one task and Claude Cowork for another against the same state.
- **IDE-native operation.** diligent runs as a CLI invokable from any terminal and as a skill installable into AI-IDE runtimes. The analyst never leaves the IDE.
- **Reusable across deals.** Install once on a workstation; use on every deal. New deals are initialized by running diligent init inside the deal folder.
- **Survives context window limits.** The analyst can run a clean handoff between AI sessions by invoking a single command that summarizes current state for the next session.

### 2.2 Non-goals

- **Not a web application.** diligent is a local CLI plus skill files. There is no server, no hosted UI, no shared backend. The deal folder lives on the analyst's local filesystem (or a synced cloud folder like OneDrive) and the tool operates against it from a local IDE.
- **Not a multi-user collaboration platform.** diligent assumes a single analyst per deal folder. The tool itself has no concept of users, permissions, or roles.
- **Not a replacement for deliverable formats.** Principals, investors, and counterparties continue to receive Word documents, PowerPoint decks, and Excel models. diligent's job ends at producing clean, consistent inputs to those deliverables. There is no proprietary viewer or dashboard.
- **Not a virtual data room.** diligent does not host source documents for external parties or manage access permissions. The seller still uses their VDR; diligent manages the analyst's local working copy.
- **Not an analytical engine.** diligent does not compute retention, build financial models, or write memos. The analyst (with AI assistance) does all of that. diligent provides the structure that makes the work consistent, traceable, and resumable.
- **Not a project management system.** There are no Gantt charts, story points, sprint ceremonies, or Kanban boards. The unit of work is the analytical task, not the calendar week.

---

## 3. Users and Workflow

### 3.1 Primary user

A self-funded searcher, search fund principal, ETA MBA student, lower-middle-market private equity associate, or independent sponsor conducting diligence on a single target acquisition. The user is technically literate enough to operate an IDE, write or read Python, and use AI coding assistants, but is not a professional software engineer. The user owns one deal at a time per workstation folder but conducts diligence on many deals over their career.

### 3.2 Current workflow without diligent

The user receives a batch of source documents from the seller (typically 10 to 50 files including financial statements, customer lists, contracts, and technical documentation). The user creates a local folder for the deal and saves the documents inside. The user opens an AI-assisted IDE (Antigravity) and points it at the deal folder, which makes the folder a project the AI agent can read. The user issues prompts that direct the agent to analyze documents, write Python scripts, build Excel models, and produce Word memos. Outputs land in the same folder. The user reviews outputs, takes findings to the principal or investor, and iterates.

When the seller sends an updated document, the user adds it to the folder (often without an explicit naming discipline, sometimes overwriting the prior version). The user prompts the agent to update affected analyses. The agent has no persistent memory of which prior analyses are affected, which assumptions were locked in, or which downstream artifacts referenced the prior data, so the user must remember and re-brief. Over weeks, the user accumulates dozens of files in the deal folder with no enforced naming convention, no version trail, and no machine-readable record of which file is current truth for any given fact.

### 3.3 Target workflow with diligent

#### Initial setup, once per workstation

```
$ pipx install diligent

# Optional: install AI-IDE skill files for tighter integration
$ diligent install --antigravity --global
$ diligent install --claude-code --global
```

#### Per-deal setup

```
$ cd ~/Desktop/ProjectArrival
$ diligent init
  Deal name: Project Arrival
  Target: OnTime 360 (Vesigo Studios, LLC)
  Deal code: ARRIVAL
  Investment thesis (one paragraph): ...

  Created .diligence/ with:
    DEAL.md, TRUTH.md, SOURCES.md, WORKSTREAMS.md, STATE.md, config.json
```

#### Daily use

The analyst works inside the IDE as before, prompting the AI agent to read source documents, write Python scripts, and build outputs. The difference is that the agent and the analyst now route through diligent commands at key points:

- **When a new source document arrives:** `diligent ingest path/to/file.xlsx` logs the document, asks what it supersedes, and prompts the analyst to identify which TRUTH.md facts it might affect.
- **When the analyst computes or validates a quantitative fact:** `diligent truth set <key> <value> --source <doc>` records the fact with citation. If the key already exists with a different value, the command surfaces the discrepancy and forces a reconciliation entry.
- **When the analyst produces a deliverable artifact:** `diligent artifact register path/to/file.docx --references <fact_keys>` records which TRUTH.md facts the artifact depends on. Subsequent updates to those facts will flag this artifact as stale.
- **When the analyst wants to know where a number came from:** `diligent truth trace <key>` walks the supersedes chain back to the original source document and shows every value that fact has held over time.
- **When the analyst wants to verify nothing is stale:** `diligent reconcile` scans all registered artifacts and reports any whose referenced TRUTH.md facts have been updated since the artifact was last refreshed.
- **When the AI session is degrading and a clean handoff is needed:** `diligent handoff` produces a structured prompt the analyst can paste into a new agent session to restore full context.

### 3.4 Deal folder layout

After `diligent init` has been run inside an existing deal folder, the layout looks like this. Files that were already in the folder before init was run are not moved; diligent only adds the .diligence/ subdirectory and asks the analyst to optionally register existing files as sources.

```
ProjectArrival/
  CIM.pdf                          # pre-existing seller document
  Customer_List_2026-02.xlsx       # pre-existing seller document
  Financials_TTM.xlsx               # pre-existing seller document
  retention_analysis_v9.docx       # pre-existing analyst output
  ...                              # any other files already present
  .diligence/
    DEAL.md                        # vision, thesis, key people
    TRUTH.md                       # validated facts with citations
    SOURCES.md                     # all source documents, dated
    WORKSTREAMS.md                 # workstream roadmap and status
    STATE.md                       # current position, blockers, open Qs
    config.json                    # deal code, paths, anchor metric defs
    workstreams/
      01-financial/
        CONTEXT.md
        RESEARCH.md
        tasks/
          01-rebuild-ebitda-bridge/
            PLAN.md
            SUMMARY.md
            VERIFICATION.md
      02-retention/
        ...
    artifacts/
      manifest.json                # registered deliverables
    scripts/
      reconcile_anchors.py
      diff_excel_versions.py
      compute_retention.py
```

Critical design point: diligent does not move, copy, or take custody of source documents or analyst-produced files. They stay where the analyst already put them inside the deal folder. The .diligence/ directory only contains pointers (relative paths), metadata, and helper scripts. This means the analyst can rip out .diligence/ at any time and lose nothing except the state layer. The work itself is independent.

---

## 4. Functional Requirements

### 4.1 Command surface

diligent exposes its functionality through a CLI with subcommands. The same commands are also exposed as IDE skill triggers (one SKILL.md per command, prefixed `dd:` in the runtime's command namespace) so the analyst can invoke them through natural language inside Antigravity or Claude Code.

#### 4.1.1 Initialization and configuration

```
diligent init                          # scaffold .diligence/ in current folder
diligent install --antigravity         # install skill files for Antigravity
diligent install --claude-code         # install skill files for Claude Code
diligent install --uninstall           # remove installed skills
diligent config get <key>              # read config value
diligent config set <key> <value>      # write config value
diligent doctor                        # validate .diligence/ integrity
```

#### 4.1.2 Source document management

```
diligent ingest <path>                 # log a new source document
    --supersedes <source-id>           # mark as superseding a prior doc
    --workstream <name>                # tag with relevant workstreams
    --note <text>                      # free-form note
diligent sources list                  # list all registered sources
diligent sources show <source-id>      # show full record
diligent sources diff <id-a> <id-b>    # diff two source files
    --as excel|text                    # specify file type
```

#### 4.1.3 Truth management

```
diligent truth set <key> <value>       # set or update a fact
    --source <source-id>               # citation (required)
    --computed-by <script-path>        # optional: script that produced it
    --notes <text>                     # optional context
diligent truth get <key>               # show current value
diligent truth list                    # list all facts
    --workstream <name>                # filter by workstream
    --stale                            # show only facts marked stale
diligent truth trace <key>             # show full supersedes history
diligent truth flag <key> --reason     # mark a fact as needing review
```

#### 4.1.4 Workstream and task management

```
diligent workstream new <name>         # create a workstream
diligent workstream list               # list workstreams with status
diligent workstream show <name>
diligent task new <workstream> <desc>  # create an atomic analysis task
diligent task list <workstream>
diligent task complete <ws> <task-id>  # mark complete, write SUMMARY.md
```

#### 4.1.5 Artifact registration and reconciliation

```
diligent artifact register <path>      # register a deliverable
    --references <key1,key2,...>       # TRUTH.md keys it depends on
    --workstream <name>
diligent artifact list                 # show all registered artifacts
    --stale                            # show only stale ones
diligent artifact refresh <path>       # mark artifact as refreshed
diligent reconcile                     # full system check
    --workstream <name>                # scope to one workstream
    --strict                           # fail on any staleness
```

#### 4.1.6 Questions and state

```
diligent ask <text>                    # add an open question
    --workstream <name>
    --owner self|principal|seller|broker|counsel
diligent answer <q-id> <text>          # close a question
    --source <source-id>               # cite if it produced a fact
diligent questions list                # show open questions
    --owner <name>                     # filter by who owes the answer
diligent status                        # full state summary
diligent handoff                       # generate clean session handoff
```

### 4.2 State files

Each file in .diligence/ has a defined schema. The schemas are versioned in config.json so that future versions of diligent can migrate older deal folders forward.

#### 4.2.1 DEAL.md

Markdown with a YAML frontmatter block. Frontmatter contains structured metadata (deal code, target name, dates, status, key people). Body contains the prose investment thesis. Always loaded by every diligent command as ambient context.

#### 4.2.2 TRUTH.md

The most important file in the system. Markdown with structured fact entries. Each entry contains a key (snake_case identifier), a current value, a source citation, a computed-by reference, a date, and a supersedes chain showing all prior values. The file is append-only at the entry level: updates write a new value and push the prior value into the supersedes chain rather than overwriting. Format must be both human-readable and parseable by Python helpers without ambiguity. Recommended format is YAML inside fenced code blocks under each fact heading.

#### 4.2.3 SOURCES.md

Markdown with one entry per registered source document. Each entry contains a source ID (auto-generated), the relative path to the document inside the deal folder, the date it was received, the date it was registered with diligent, the parties who provided it, an optional supersedes pointer to a prior source ID, the workstreams it touches, and free-form notes. Source documents themselves are never moved or modified by diligent.

#### 4.2.4 WORKSTREAMS.md

Markdown listing all workstreams in the deal with their status (not started, in progress, complete, blocked), the task count, and a one-line summary. Each workstream has its own subdirectory under .diligence/workstreams/ containing CONTEXT.md, RESEARCH.md, and a tasks/ directory.

#### 4.2.5 STATE.md

Markdown capturing the current position of the analyst across the deal: what was last worked on, what is currently in progress, what is blocked, what open questions exist, and what is queued next. Updated by most diligent commands as a side effect. Read first by the handoff command to construct continuity prompts.

#### 4.2.6 config.json

JSON file containing deal code, schema version, AI runtime preferences, anchor metric definitions (the small set of facts that must always reconcile across artifacts), reconciliation tolerance, and paths.

### 4.3 Python helper library

diligent ships with a small library of Python helpers in .diligence/scripts/ that perform deterministic computations the CLI commands invoke. These are versioned with the tool but copied into each deal folder so the analyst can modify them per-deal without affecting other deals.

- **reconcile_anchors.py:** reads TRUTH.md and the artifact manifest, walks every registered artifact, and reports stale references and internal variance against anchor metric tolerances.
- **diff_excel_versions.py:** given two Excel files in the deal folder, reports which sheets, named ranges, and cells differ. Used by `diligent sources diff` and invoked automatically when an ingested file supersedes a known prior version.
- **extract_text.py:** wrapper around pandoc, pdftotext, openpyxl, and python-docx that returns the textual content of any common deal document format for AI agent consumption.
- **fact_parser.py:** parses TRUTH.md into a Python dictionary and serializes back. Used by every CLI command that reads or writes facts.
- **artifact_scanner.py:** scans a registered artifact for references to TRUTH.md fact keys (looking for tagged citations the analyst inserted) and reports the dependency graph.

### 4.4 Skill files for AI runtimes

`diligent install` copies a set of SKILL.md files into the runtime's skills directory. Each command in section 4.1 has a corresponding skill file with a description that triggers the agent to invoke the CLI on the analyst's behalf when the analyst makes a relevant natural-language request.

Example: when the analyst types into Antigravity that a new customer file from the seller just landed in their downloads folder, the `dd:ingest` skill triggers and the agent runs `diligent ingest` with appropriate flags, prompting the analyst for missing information.

Skill files must be parameterized at install time with the absolute path to the diligent CLI binary so the runtime knows what to invoke.

### 4.5 Editorial enforcement rules

diligent commands embed enforcement rules into the prompts they generate for the agent. These rules encode the analytical discipline that the analyst would otherwise have to remember manually.

- **Source every claim.** When the agent writes a SUMMARY.md or proposes a TRUTH.md update, every quantitative claim must include a citation to a source ID or a script path. Unsourced claims are rejected and pushed into STATE.md as open questions.
- **Stop at verification gates.** When a TRUTH.md update would change an existing fact value beyond tolerance, the agent must stop and surface the discrepancy rather than overwriting.
- **Read context before planning.** Before drafting a task plan, the agent must read DEAL.md, the relevant workstream's CONTEXT.md, and any TRUTH.md facts tagged with that workstream.
- **Reconcile before declaring done.** Tasks cannot be marked complete until `diligent reconcile` passes for any artifacts they produced.

---

## 5. Non-Functional Requirements

### 5.1 Platform

- **Operating systems:** Windows 10/11, macOS 12+, Linux (any modern distribution). Primary development target is Windows because the primary user works on Windows with OneDrive-synced deal folders.
- **Python version:** 3.11 or higher. Uses modern type hints and pattern matching.
- **Distribution:** Published to PyPI under the package name diligent (or alternative if taken). Installed via pipx for isolation. No system Python pollution.
- **Dependencies:** Minimized. Required: click or typer (CLI framework), pyyaml, openpyxl, python-docx, pypdf or pdfplumber. Optional: rich (pretty terminal output).

### 5.2 Performance

- All commands must return in under 2 seconds for a typical deal folder (50 to 200 source documents, 50 to 500 TRUTH.md facts, 20 to 100 registered artifacts) on a modern laptop.
- `diligent reconcile` against a typical deal must complete in under 10 seconds.
- No background processes, daemons, or watchers. The tool only runs when invoked.

### 5.3 Reliability

- All state file writes must be atomic (write to temp file, fsync, rename) to survive crashes mid-write.
- Every state-mutating command must validate the resulting file structure before committing the write. If validation fails, the prior state is preserved.
- `diligent doctor` must detect and report (and where possible auto-repair) corruption in any .diligence/ file.

### 5.4 Privacy and security

- All data lives on the analyst's local filesystem. No telemetry, no analytics, no phone-home, no cloud sync built into the tool itself. (The analyst may store the deal folder in OneDrive or Dropbox at their own choice.)
- diligent never makes outbound network requests during normal operation.
- Source documents are read-only from diligent's perspective. The tool never modifies a file the analyst placed in the deal folder.
- The CLI does not require API keys or credentials. Any AI agent integration happens through the IDE runtime's existing credentials, not through diligent.

### 5.5 Versioning and migration

- Schema version is recorded in config.json. New versions of diligent must be able to read deal folders created by older versions, with a `diligent migrate` command if the schema has changed.
- Semantic versioning. Breaking changes to the CLI surface or state file format require a major version bump.

---

## 6. Licensing and Distribution

### 6.1 License

diligent is published under the Business Source License 1.1 (BSL), the same license used by Sentry, CockroachDB, and other commercial open-source companies. BSL is a source-available license that grants broad permissions for non-production use while reserving commercial rights to the licensor.

Specific terms for diligent:

- **Licensed Work:** the diligent source code, including the CLI, helper scripts, skill files, and documentation, as published in the official repository.
- **Additional Use Grant:** any individual or entity may use diligent for diligence on their own acquisition activity. Use by a service provider (consultant, advisor, accounting firm, law firm, search-fund-as-a-service provider) on behalf of clients requires a commercial license from the author.
- **Change Date:** four years after the release date of each version. After the Change Date, that version automatically converts to the Apache License 2.0 (the Change License).
- **Restrictions:** redistribution of the source code is permitted only with the BSL preserved and the same Additional Use Grant. Forks intended for commercial redistribution are prohibited without a commercial license. Removing or altering the license header is prohibited.

This structure gives the author full control over commercial monetization while still allowing the source to be public for inspection, audit, and personal use. Colleagues can be granted free commercial use on a case-by-case basis through a separate license file in their fork or installation. Code-copying is legally actionable under BSL even though the code is technically readable.

### 6.2 Repository structure

```
diligent/                          # repo root
  LICENSE                          # BSL 1.1 with project-specific terms
  LICENSE-COMMERCIAL.md            # template for granting commercial use
  README.md                        # what it is, install, quickstart
  pyproject.toml                   # build config, dependencies, version
  diligent/                        # Python package
    __init__.py
    cli.py                         # entry point, subcommand routing
    commands/                      # one module per subcommand
      init.py
      ingest.py
      truth.py
      sources.py
      workstream.py
      task.py
      artifact.py
      reconcile.py
      ask.py
      status.py
      handoff.py
      install.py
      doctor.py
    state/                         # state file readers and writers
      deal.py
      truth.py
      sources.py
      workstreams.py
      state_file.py
      config.py
    helpers/                       # Python helpers copied into deals
      reconcile_anchors.py
      diff_excel_versions.py
      extract_text.py
      fact_parser.py
      artifact_scanner.py
    skills/                        # SKILL.md templates
      antigravity/
      claude_code/
    templates/                     # markdown templates for init
      DEAL.md.tmpl
      TRUTH.md.tmpl
      SOURCES.md.tmpl
      WORKSTREAMS.md.tmpl
      STATE.md.tmpl
  tests/
  docs/
```

### 6.3 Distribution channels

- **PyPI:** `pipx install diligent`. Primary distribution channel.
- **GitHub:** source repository, releases, issue tracker. Public, source-available under BSL.
- **Direct grant:** for colleagues to whom the author wishes to grant free commercial use, a personalized LICENSE-GRANT.md file is provided alongside their copy specifying the granted scope.

---

## 7. Build Plan

The build is structured as four milestones, each producing a working tool that the author can use on Project Arrival. The principle: never spend a weekend building something that has not yet earned its place in the actual workflow.

### 7.1 Milestone 1: Skeleton and state files

Goal: a CLI that can scaffold a .diligence/ directory and round-trip its state files.

- Project scaffold: pyproject.toml, package layout, click-based CLI entry point, BSL license header.
- `diligent init` command that creates the .diligence/ directory and writes empty templates for DEAL.md, TRUTH.md, SOURCES.md, WORKSTREAMS.md, STATE.md, and config.json.
- State file readers and writers for all six core files. YAML frontmatter parsing for DEAL.md. Structured fact parsing for TRUTH.md.
- `diligent doctor` command that validates file integrity.
- Tests for state file round-trips with realistic fixture data.
- Acceptance test: hand-author the .diligence/ directory for Project Arrival from existing materials and have `diligent doctor` pass clean.

### 7.2 Milestone 2: Truth and sources

Goal: the analyst can ingest documents, set facts, and trace history.

- `diligent ingest` command with supersedes chain logic.
- `diligent sources list`, `show`, `diff` commands.
- `diligent truth set`, `get`, `list`, `trace`, `flag` commands.
- diff_excel_versions.py helper, invoked from sources diff and from ingest when superseding.
- fact_parser.py helper, the canonical TRUTH.md reader/writer used by every other command.
- Acceptance test: ingest five real Project Arrival source documents, set the validated anchor metrics (T12M cohort 573, retained 492, NDR 87.7 percent, GDR 80.0 percent), and run truth trace on each to confirm history is intact.

### 7.3 Milestone 3: Artifacts and reconciliation

Goal: the analyst can register deliverables and detect when they go stale.

- `diligent artifact register`, `list`, `refresh` commands. Manifest stored in .diligence/artifacts/manifest.json.
- `diligent reconcile` command with strict and workstream-scoped variants.
- reconcile_anchors.py helper, the deterministic engine behind reconcile.
- artifact_scanner.py helper for inferring fact dependencies from tagged citations in deliverables.
- Acceptance test: register the existing OnTime Customer Base Industry Briefing as an artifact referencing the validated anchor metrics. Update one anchor metric (e.g. T12M retained from 492 to 491). Run reconcile and confirm the briefing is flagged stale.

### 7.4 Milestone 4: Workstreams, tasks, questions, handoff, and skills

Goal: full surface complete; install into Antigravity and use for one full week of Project Arrival work.

- `diligent workstream` and `diligent task` commands.
- `diligent ask`, `answer`, `questions` commands. Question state lives in STATE.md.
- `diligent status` command, summarizing state across all files.
- `diligent handoff` command, generating a clean session restoration prompt.
- `diligent install` command for Antigravity; SKILL.md templates parameterized with CLI binary path.
- Acceptance test: dogfood for one full week on Project Arrival. Track every friction point. Decide which (if any) belong in a v0.2.

### 7.5 Out of scope for v1

- Multi-user features (review queues, sign-offs, role-based access).
- Web UI of any kind.
- Hosted service or cloud sync.
- Built-in AI agent calls (no LLM API integration; agents reach diligent through the IDE runtime, not the other way around).
- Document OCR or automated extraction of facts from PDFs. The analyst (with AI assistance) is the extraction engine.
- Integration with VDRs, CRMs, or accounting systems.
- Phase-level git branching and atomic-commit orchestration. The analyst can use git on the deal folder normally; diligent does not orchestrate it.
- Skill packages for runtimes other than Antigravity and Claude Code.

---

## 8. Open Questions

Items the author needs to decide before or during the build:

- Final tool name. diligent is a placeholder. Alternatives: searchlight, anchor, veritas, dealroom (likely taken), bedrock, plumb, tether.
- Whether TRUTH.md should store facts as YAML inside fenced code blocks under markdown headers, or as a single YAML file with markdown rendered separately. The former is more human-readable; the latter is easier to parse.
- Whether the artifact manifest should be JSON (machine-friendly) or markdown (human-friendly). Recommendation: JSON, with `diligent artifact list` rendering as a clean table.
- Whether to enforce a citation tag syntax inside deliverables that artifact_scanner.py can detect, or rely on manual --references flags at registration. Recommendation: support both, prefer tags.
- Whether to ship pre-defined workstream templates (financial, retention, technical, legal, HR, commercial) or let each analyst define their own. Recommendation: ship templates as a starting point but allow free-form.
- Whether config.json or a TOML equivalent. Recommendation: JSON for compatibility.
- Whether to include git integration as a v1 feature (auto-commit state file changes) or leave git entirely to the analyst. Recommendation: leave to the analyst in v1; revisit in v2.

---

## 9. Success Criteria

v1 is successful if:

- The author uses diligent as the primary state-management tool on Project Arrival for at least four consecutive weeks without abandoning it.
- `diligent reconcile` catches at least one real staleness incident on Project Arrival that would otherwise have been missed.
- The author can perform a clean handoff between AI sessions using `diligent handoff` and have the new session pick up work without re-uploading documents or re-explaining context.
- The author can use diligent on a second deal with no per-deal customization beyond running `diligent init`.
- At least one colleague is granted access and uses diligent on their own deal for at least two weeks.
