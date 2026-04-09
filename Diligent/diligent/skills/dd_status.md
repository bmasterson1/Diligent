# dd:status

Get full deal state summary and generate AI session handoff documents.

## When to use

- Starting the day's work and need a quick deal overview
- Checking what needs attention (stale artifacts, open questions)
- Handing off to a fresh AI session with full context
- Getting a structured snapshot of deal state for reporting

## Commands

### status
```bash
{{DILIGENT_PATH}} status [--verbose] [--json]
```
Display a sectioned deal summary: header (deal name, stage, days in diligence),
workstreams with counts, stale artifacts, open questions, and recent activity.
Each section shows top 5 items with "and N more" truncation by default.
`--verbose` expands all sections to show every item.
Status is read-only and never modifies deal state.

### handoff
```bash
{{DILIGENT_PATH}} handoff [--since <duration-or-date>] [--everything] [--clip] [--json]
```
Generate an AI session handoff document. Output includes an instruction header
(what diligent is, key concepts, editorial principles), followed by deal state:
DEAL.md, WORKSTREAMS.md, recent facts, recent sources, all open questions,
all stale/flagged artifacts, and most recent task summaries.

Default window: 14 days (double the config `recent_window_days`). `--since`
overrides the window (e.g., `--since 7d`, `--since 2026-03-15`).
`--everything` bypasses the time window and dumps complete state.
`--clip` copies the output to the system clipboard.

## Rules

- `status` is read-only. It aggregates from all state files but never writes.
- `handoff` output is a paste buffer, not a file reference. Copy and paste it into your AI session.
- Handoff default window is 14 days. All open questions, flagged facts, and stale artifacts are always included regardless of the time window.
- `--clip` uses platform-native clipboard (clip.exe, pbcopy, xclip). If clipboard is unavailable, a warning is printed and output continues to stdout.
- `--everything` is for deep-dive sessions. It produces a large document.

## Common workflows

### Morning check-in
```bash
{{DILIGENT_PATH}} status
```

### Hand off to a new AI session
```bash
{{DILIGENT_PATH}} handoff --clip
```
Paste the clipboard contents into the new session's context.

### Deep dive on everything
```bash
{{DILIGENT_PATH}} status --verbose
```
