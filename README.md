# diligent

A context-engineering and state-management CLI for lower-middle-market acquisition due diligence.

## The problem

Due diligence on a small business acquisition generates a constantly evolving set of source documents, analytical artifacts, and validated facts spread across dozens of files. The analysis itself is not the hard part. The hard part is keeping track of what is currently true, where each number came from, and which downstream deliverables need to be updated when the seller sends new data.

Over a few months and six workstreams, that tracking problem gets away from you. The investor memo references last week's retention numbers. The EBITDA bridge uses a customer count that was updated two versions ago. Nobody catches it until someone tries to reconcile two figures that no longer agree.

diligent solves this by sitting in your deal folder and managing the state layer: which facts are current, what source they came from, what superseded what, and which of your deliverables have gone stale.

## Who it's for

Self-funded searchers, search fund principals, ETA students, and lower-middle-market PE associates who do their own diligence work inside an AI-assisted IDE. You're already using Cursor, Claude Code, Antigravity, or Windsurf to write Python scripts, build Excel models, and draft Word memos. diligent gives that workflow a persistent memory.

## What it is not

- Not a web application. No server, no login, no dashboard.
- Not a virtual data room. It tracks state, not files.
- Not a project management tool. No Gantt charts, no sprints.
- Not a database. State lives in human-readable markdown files.
- Not a replacement for Word or Excel. It tracks what those files contain.

Your deal folder stays yours. Source documents are never moved or modified. You can remove `.diligence/` at any time and lose nothing except the tracking layer.

## Install

Requires Python 3.11+.

```
pipx install diligent-dd
```

Or `pip install diligent-dd`. The CLI command is `diligent`.

## Quickstart

**1. Scaffold a deal folder**

```
cd ~/Desktop/ProjectAlpha
diligent init
```

Creates a `.diligence/` directory alongside your existing files with state files for truth, sources, artifacts, questions, and workstreams.

**2. Ingest source documents**

```
diligent ingest CIM.pdf
diligent ingest Financials_TTM.xlsx
diligent ingest Customer_List.xlsx --workstream financial
```

Registers each file in SOURCES.md with a unique source ID, date, and metadata. Files stay where they are.

**3. Record validated facts**

```
diligent truth set "arr" "2.4M" --source S-001
diligent truth set "t12m_retained" "492" --source S-003 --workstream retention
```

Stores each value with a source citation. Updating an existing fact triggers a verification gate that surfaces discrepancies before overwriting. Prior values are preserved in a supersedes chain.

**4. Register deliverables**

```
diligent artifact register investor_deck_v1.pptx --references arr,ndr,gdr
diligent artifact register retention_v3.docx --references t12m_retained,t12m_churned
```

Links artifacts to specific truth keys so staleness is trackable.

**5. Check what's stale**

```
diligent reconcile
```

Walks the source-to-fact-to-artifact dependency graph and reports which deliverables need to be refreshed, why, and how many days stale.

**6. When new data arrives**

```
diligent ingest Customer_List_v2.xlsx --supersedes S-003
diligent truth set "t12m_retained" "491" --source S-019
diligent reconcile
```

The updated fact triggers staleness flags on every artifact that referenced the old value.

**7. Trace any number back to its source**

```
diligent truth trace t12m_retained
```

Shows the full history: every value the fact has held, which source document produced it, and when it changed.

**8. Hand off to a fresh AI session**

```
diligent handoff --clip
```

Generates a paste-ready markdown document with deal context, recent changes, and open questions. Copies it to the clipboard so you can start a new session without re-uploading documents or re-explaining context.

## Full command reference

```
diligent init                              # scaffold .diligence/ in current folder
diligent doctor                            # validate .diligence/ integrity
diligent config get|set <key> [value]      # read or write config values
diligent migrate                           # migrate older deal folders forward

diligent ingest <path>                     # log a new source document
diligent sources list                      # list all registered sources
diligent sources show <id>                 # show full source record
diligent sources diff <id-a> <id-b>        # diff two source files

diligent truth set <key> <value>           # set or update a validated fact
diligent truth get <key>                   # show current value
diligent truth list                        # list all facts
diligent truth trace <key>                 # show full supersedes history
diligent truth flag <key> --reason <text>  # mark a fact as needing review

diligent workstream new <name>             # create a workstream
diligent workstream list                   # list workstreams with status
diligent workstream show <name>            # show workstream detail

diligent task new <workstream> <desc>      # create an atomic analysis task
diligent task list <workstream>            # list tasks in a workstream
diligent task complete <ws> <task-id>      # mark complete, write summary

diligent artifact register <path>          # register a deliverable
diligent artifact list                     # show all registered artifacts
diligent artifact refresh <path>           # mark artifact as refreshed
diligent reconcile                         # full staleness check

diligent ask <text>                        # add an open question
diligent answer <q-id> <text>              # close a question
diligent questions list                    # show open questions

diligent status                            # full deal state summary
diligent handoff                           # generate session handoff document
```

## AI agent integration

Install skill files so your IDE's AI agent understands diligent commands:

```
diligent install --claude-code
diligent install --antigravity
```

The agent can then invoke diligent on your behalf when you mention ingesting a document, setting a fact, or checking for staleness in natural language.

## Deal folder layout

After `diligent init`, the layout looks like this. Existing files are not moved.

```
ProjectAlpha/
  CIM.pdf                           # your existing seller documents
  Financials_TTM.xlsx
  retention_v3.docx                  # your analytical artifacts
  .diligence/
    DEAL.md                          # deal name, thesis, key people
    TRUTH.md                         # validated facts with citations
    SOURCES.md                       # all source documents, dated
    WORKSTREAMS.md                   # workstream roadmap and status
    STATE.md                         # current position, blockers
    QUESTIONS.md                     # open and closed questions
    ARTIFACTS.md                     # registered deliverables
    config.json                      # deal code, schema version
    workstreams/
      01-financial/
        CONTEXT.md
        RESEARCH.md
        tasks/
      02-retention/
        ...
```

## License

Business Source License 1.1. Free for individual use on your own acquisition activity. Commercial use by service providers (consultants, advisors, accounting firms) requires a separate license. Each version converts to Apache 2.0 four years after release. See [LICENSE](Diligent/LICENSE) for full terms.
