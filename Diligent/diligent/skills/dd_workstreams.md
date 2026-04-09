# dd:workstreams

Organize deal work into workstreams with tasks.

## When to use

- Creating a new workstream to structure diligence by domain
- Reviewing workstream status and counts
- Creating tasks within a workstream
- Completing tasks with summary documentation
- Checking task progress across workstreams

## Commands

### workstream new
```bash
{{DILIGENT_PATH}} workstream new <name> [--json]
```
Create a new workstream. Pre-defined templates: financial, retention, technical,
legal, hr, integration. Custom names also accepted (lowercase-kebab format).
Creates a subdirectory with CONTEXT.md and RESEARCH.md files.

### workstream list
```bash
{{DILIGENT_PATH}} workstream list [--json]
```
List all workstreams with status, task count, and question count.

### workstream show
```bash
{{DILIGENT_PATH}} workstream show <name> [--json]
```
Display detailed workstream information: description, status, task counts,
open questions, fact count, and artifact count with staleness.

### task new
```bash
{{DILIGENT_PATH}} task new <workstream> "<task description>" [--json]
```
Create a new task within a workstream. Tasks get numbered subdirectories
under the workstream's tasks/ directory.

### task list
```bash
{{DILIGENT_PATH}} task list <workstream> [--json]
```
List all tasks in a workstream with status (open/complete).

### task complete
```bash
{{DILIGENT_PATH}} task complete <workstream> <task_id> [--json]
```
Mark a task as complete. The task_id is the 3-digit directory number (e.g., '001').
Requires SUMMARY.md in the task directory to contain real content (non-empty after
stripping HTML comments and headings).

## Rules

- Workstream names must be lowercase-kebab (e.g., "financial", "custom-ws").
- Each workstream gets a subdirectory with CONTEXT.md and RESEARCH.md.
- Tasks live in numbered subdirectories under workstream/tasks/.
- `task complete` requires substantive SUMMARY.md content. Empty summaries are rejected.
- Hand-edits to WORKSTREAMS.md are respected by the CLI.

## Common workflows

### Set up workstreams
```bash
{{DILIGENT_PATH}} workstream new financial
{{DILIGENT_PATH}} workstream new retention
{{DILIGENT_PATH}} workstream new technical
{{DILIGENT_PATH}} workstream new legal
```

### Create and complete a task
```bash
{{DILIGENT_PATH}} task new financial "Review audited financials for FY2024"
# ... edit the task's SUMMARY.md with completion notes ...
{{DILIGENT_PATH}} task complete financial 001
```

### Review workstream status
```bash
{{DILIGENT_PATH}} workstream show financial
```
