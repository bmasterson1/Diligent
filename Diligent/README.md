# diligent

A CLI for due diligence state management. Tracks facts, sources, artifacts, and
questions across a deal lifecycle so analysts always know what is current truth
and which deliverables need to be refreshed.

## Install

Requires Python 3.11+.

```
pipx install diligent-dd
```

Or: `pip install diligent-dd`. The CLI command is `diligent`.

## Quickstart

1. **Scaffold a deal folder**

   ```
   diligent init
   ```
   Creates a `.diligence/` directory with state files for truth, sources,
   artifacts, questions, and workstreams.

2. **Ingest a source document**

   ```
   diligent ingest path/to/document.xlsx
   ```
   Registers the file in SOURCES.md with a unique source ID and metadata.

3. **Record a fact**

   ```
   diligent truth set "revenue_2024" "142.5M" --source S-001
   ```
   Stores the value with source citation. Updating an existing fact triggers
   a verification gate that surfaces discrepancies before overwriting.

4. **Register an artifact**

   ```
   diligent artifact register path/to/model.xlsx --references revenue_2024
   ```
   Links a deliverable to specific truth keys so staleness is trackable.

5. **Check what is stale**

   ```
   diligent reconcile
   ```
   Walks the source-fact-artifact dependency graph and reports which
   deliverables need to be refreshed, why, and how many days stale.

6. **See full deal state**

   ```
   diligent status
   ```
   One-command summary: truth counts, stale artifacts, recent ingests,
   open questions, and workstream progress.

7. **Restore AI context in a new session**

   ```
   diligent handoff --clip
   ```
   Generates a paste-ready markdown document with deal context, recent
   changes, and open questions. Copies it to the clipboard.

## AI agent setup

Install skill files for your IDE so AI agents understand diligent commands:

```
diligent install --claude-code
diligent install --antigravity
```

## What it is not

- Not a virtual data room. It tracks state, not files.
- Not a project management tool. Use your existing PM software.
- Not a replacement for Word or Excel. It tracks what those files contain.
- Not a database. State lives in human-readable markdown files.
- Not a web app. It is a local CLI that works with OneDrive/SharePoint sync.

## License

Business Source License 1.1. Free for individual, non-commercial due
diligence analysis. Commercial service-provider use requires a separate
license. See [LICENSE](LICENSE) for full terms.
