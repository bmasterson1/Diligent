# dd:artifacts

Track deliverables and check staleness against truth facts.

## When to use

- Registering a new deliverable (memo, model, report)
- Checking which deliverables need to be refreshed after fact changes
- Running a staleness check across all artifacts
- Marking an artifact as updated after incorporating new data

## Commands

### artifact register
```bash
{{DILIGENT_PATH}} artifact register <path> --references <key1,key2,...> [--workstream <ws>] [--confirm] [--notes <text>] [--json]
```
Register a deliverable and link it to truth keys via `--references`.
For .docx files, a scanner extracts referenced keys automatically; `--references`
is optional. For other file types, `--references` is required.
Use `--confirm` to acknowledge if referenced facts are already stale.

### artifact list
```bash
{{DILIGENT_PATH}} artifact list [--stale] [--json]
```
List all registered artifacts. `--stale` filters to only those needing refresh.
Summary line always counts all artifacts regardless of active filters.

### artifact refresh
```bash
{{DILIGENT_PATH}} artifact refresh <path> [--json]
```
Mark an artifact as updated. Resets the last_refreshed timestamp so it is no
longer stale relative to its referenced facts.

### reconcile
```bash
{{DILIGENT_PATH}} reconcile [--workstream <ws>] [--strict] [--all] [--verbose] [--json]
```
The authoritative staleness engine. Checks all artifacts against TRUTH.md and
SOURCES.md for three staleness conditions: fact-changed, source-superseded,
and flagged-advisory. `--strict` exits non-zero on any staleness (for scripted
checks). `--all` includes non-stale artifacts in output. `--verbose` shows
per-fact detail.

## Rules

- Artifacts reference truth keys via `--references`. Staleness means a referenced fact changed after last refresh.
- `reconcile` is the single authoritative staleness check. Other commands defer to it.
- `--strict` exits non-zero on staleness for CI/scripted use.
- Flagged facts produce ADVISORY status, not STALE. They never affect exit codes without `--strict`.
- Source-superseded staleness fires only when the superseding source date is after artifact last_refreshed.
- ISO date string comparison (lexicographic) is used for staleness checks.

## Common workflows

### Register a deliverable
```bash
{{DILIGENT_PATH}} artifact register "./deliverables/QoE Memo.docx" --references revenue-2024,ebitda-2024 --workstream financial
```

### Check what needs refresh
```bash
{{DILIGENT_PATH}} reconcile --verbose
```

### Mark deliverable updated
```bash
{{DILIGENT_PATH}} artifact refresh "./deliverables/QoE Memo.docx"
```
