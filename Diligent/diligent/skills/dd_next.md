# dd:next

Check deal state and recommend the highest-priority next action.

## When to use

- User asks "what should I do next?", "what needs attention?", "where was I?"
- Starting a new work session on an existing deal
- User seems unsure what diligent command to run

## Guided flow

### Step 1: Read current state
Run:
```bash
{{DILIGENT_PATH}} status --json
```
Parse the output to understand: stale artifact count, open question count, flagged facts, workstream progress, recent activity.

### Step 2: Prioritize and recommend

Apply this priority order:

1. **Stale artifacts exist**: "You have N stale artifact(s). Run 'diligent reconcile' to see which ones, then update them."
2. **Flagged facts exist**: "N fact(s) are flagged for review. Run 'diligent truth list --stale' to see them."
3. **Open questions with owner=self**: "You have N open question(s) assigned to you. Run 'diligent questions list --owner self' to see them."
4. **Unregistered files detected**: Scan the deal folder for files not in SOURCES.md or the artifact manifest. If found: "I see N file(s) in the deal folder that aren't registered. Want to ingest them?"
5. **Workstreams with no recent activity**: "The <ws> workstream hasn't been touched in N days. Is that intentional?"
6. **Everything is clean**: "Deal state looks current. No stale artifacts, no open questions, no flagged facts. You're in good shape."

### Step 3: Offer to execute
After recommending, ask: "Want me to help with this now?" If yes, run the relevant commands.

## Rules

- Always run status first. Never guess at deal state.
- Present ONE recommendation at a time, starting with the highest priority.
- If the deal has no .diligence/ directory, redirect to dd:start.
- Keep output concise. The analyst wants to know what to do, not get a lecture.
