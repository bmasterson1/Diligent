# dd:truth

Manage validated facts in the deal's TRUTH.md file.

## When to use

- Recording a data point, metric, or finding from a source document
- Checking or verifying an existing fact
- Viewing the history of a value (who set it, when, from what source)
- Flagging a fact for review due to discrepancy or uncertainty
- Listing stale or workstream-scoped facts

## Commands

### truth set
```bash
{{DILIGENT_PATH}} truth set <key> <value> --source <source-id> [--workstream <ws>] [--anchor] [--confirm] [--computed-by <formula>] [--notes <text>] [--json]
```
Record or update a validated fact. `--source` is required on every set.
Values are stored as quoted strings to prevent YAML type coercion.
If the value changes beyond the anchor tolerance, a verification gate fires.
Use `--confirm` to override the gate. `--anchor` marks the fact as an anchor value.

### truth get
```bash
{{DILIGENT_PATH}} truth get <key> [--json]
```
Retrieve a single fact by key. Shows current value, source, date, and metadata.

### truth list
```bash
{{DILIGENT_PATH}} truth list [--workstream <ws>] [--stale] [--json]
```
List all facts, optionally filtered by workstream or staleness.
Summary line always counts all facts regardless of active filters.

### truth trace
```bash
{{DILIGENT_PATH}} truth trace <key> [--json]
```
Show the full history of a fact: current value, source chain, supersedes history,
and flag events. Use this to investigate discrepancies.

### truth flag
```bash
{{DILIGENT_PATH}} truth flag <key> --reason <text> [--clear] [--json]
```
Flag a fact for review. Flagged facts are advisory -- they appear in reconcile
output but do not trigger staleness. Use `--clear` to remove a flag.

## Rules

- `--source` is required on every `truth set`. Never record a fact without citing its source.
- Values are quoted strings. Do not rely on YAML type inference for financial data.
- The verification gate fires when a value changes beyond the configured tolerance. Use `--confirm` to acknowledge and override.
- Flagged facts are strictly advisory. They do not set `is_stale` or affect exit codes.
- Never invent values. If a fact cannot be sourced, do not record it.

## Common workflows

### Record a new fact
```bash
{{DILIGENT_PATH}} truth set revenue-2024 "12,500,000" --source ARR-001 --workstream financial --notes "From audited financials"
```

### Investigate a discrepancy
```bash
{{DILIGENT_PATH}} truth trace revenue-2024
{{DILIGENT_PATH}} truth flag revenue-2024 --reason "CIM shows 12.8M vs audited 12.5M"
```

### Review stale facts
```bash
{{DILIGENT_PATH}} truth list --stale
```
