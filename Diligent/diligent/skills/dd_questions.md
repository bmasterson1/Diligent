# dd:questions

Track open questions and manage the answer lifecycle.

## When to use

- Raising a question during analysis that needs an answer from a specific party
- Answering a question with a cited source
- Reviewing open questions by owner or workstream
- Checking gate-rejected questions (auto-generated when verification gate fires)

## Commands

### ask
```bash
{{DILIGENT_PATH}} ask "<question text>" [--workstream <ws>] [--owner <owner>] [--json]
```
Record a new open question. Owner taxonomy: self, principal, seller, broker, counsel.
Questions are never deleted, only answered.

### answer
```bash
{{DILIGENT_PATH}} answer <question-id> "<answer text>" [--source <source-id>] [--json]
```
Answer an open question. `--source` optionally cites the source document that
provided the answer. Transitions question status from open to answered.

### questions list
```bash
{{DILIGENT_PATH}} questions list [--owner <owner>] [--workstream <ws>] [--json]
```
List questions filtered by owner or workstream. Shows ID, status, origin tag
([gate] or [manual]), workstream, and truncated question text.
Summary line always counts all questions regardless of active filters.

## Rules

- Owner taxonomy is case-sensitive: self, principal, seller, broker, counsel.
- Gate-rejected questions appear with [gate] tag. These are auto-generated when the verification gate fires on truth set.
- Answers optionally cite a source. Always prefer citing a source when one exists.
- Questions are never deleted, only answered.
- Gate rejection question text includes a delta description for human readability.

## Common workflows

### Raise a question
```bash
{{DILIGENT_PATH}} ask "What is the customer concentration for top 10 accounts?" --workstream retention --owner seller
```

### Answer with source
```bash
{{DILIGENT_PATH}} answer Q-003 "Top 10 accounts represent 42% of ARR per AR aging report" --source ARR-005
```

### Review open questions
```bash
{{DILIGENT_PATH}} questions list --owner seller
```
