# dd:start

Guided onboarding for a new deal folder. Walk the analyst through full deal setup.

## When to use

- First time using diligent on a new deal folder
- User says "set up diligent", "initialize this deal", "get started with diligent"
- A deal folder exists with source documents but no .diligence/ directory

## Guided flow

Follow these steps in order. Do not skip steps. Ask the analyst for input at each step.

### Step 1: Initialize
Check if .diligence/ exists. If not, run:
```bash
{{DILIGENT_PATH}} init
```
Prompt the analyst for: deal name, target company, deal code, one-paragraph thesis, and key people (principal, broker, seller, counsel). Pass answers to the init command.

### Step 2: Scan and ingest source documents
List all files in the deal folder (excluding .diligence/ and common non-document files like .git, __pycache__, .DS_Store). Present the list to the analyst and ask: "Which of these are source documents from the seller or broker?"

For each file the analyst identifies, run:
```bash
{{DILIGENT_PATH}} ingest <path> [--workstream <ws>] [--note <text>]
```
Ask which workstream each document belongs to. If a document supersedes another, use --supersedes.

### Step 3: Set anchor facts
Ask the analyst: "What are the key metrics you've validated so far? These are the anchor facts that everything else depends on. Common examples: ARR, customer count, EBITDA margin, retention rate."

For each fact the analyst provides, run:
```bash
{{DILIGENT_PATH}} truth set <key> <value> --source <source-id> [--anchor] [--workstream <ws>]
```

### Step 4: Register existing artifacts
Ask: "Have you already produced any deliverables (memos, models, decks, analyses) that reference these facts?"

For each artifact, run:
```bash
{{DILIGENT_PATH}} artifact register <path> --references <key1,key2,...> [--workstream <ws>]
```

### Step 5: Verify
Run:
```bash
{{DILIGENT_PATH}} reconcile
{{DILIGENT_PATH}} status
```
Show the analyst the current state of their deal. Confirm everything looks right.

### Step 6: Suggest next actions
Tell the analyst: "Your deal is set up. From here, the daily workflow is:
- New document arrives: diligent ingest <path>
- Validate a number: diligent truth set <key> <value> --source <id>
- Produce a deliverable: diligent artifact register <path> --references <keys>
- Check for staleness: diligent reconcile
- Hand off to fresh session: diligent handoff --clip"

## Rules

- Never skip the ingest step. Source registration is the foundation.
- Every truth set must have a --source. Do not record unsourced facts.
- Ask, don't assume. Let the analyst decide which files are sources and which facts matter.
- Keep the flow conversational but efficient. Don't over-explain commands the analyst didn't ask about.
