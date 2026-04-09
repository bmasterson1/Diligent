# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 -- MVP

**Shipped:** 2026-04-09
**Phases:** 6 | **Plans:** 22 | **Sessions:** ~10

### What Was Built
- Complete CLI with 17 commands for due diligence state management
- 8 state file types with typed models, atomic writes, and round-trip fidelity
- Verification gate (TRUTH-04): the load-bearing behavior connecting truth to questions
- Dependency-graph reconcile engine detecting staleness across source -> fact -> artifact chain
- PyPI-ready package (diligent-dd) with 6 skill files for AI IDE integration
- 504 tests, 17,475 LOC Python

### What Worked
- H2+YAML parsing pattern replicated per module kept each state reader self-contained and debuggable
- Pure function reconcile engine (zero I/O imports) made staleness logic trivially testable
- Phase 6 gap-closure pattern: running audit before milestone close caught 5 integration issues that were fixed in a single focused phase
- Atomic write with validate_fn (re-parse before commit) caught format bugs during development that would have been silent data corruption
- LazyGroup for CLI startup kept import time under 200ms despite growing command count

### What Was Inefficient
- SUMMARY.md one_liner field never populated across any of 22 plans, making accomplishment extraction manual
- Phase 5 verification blocked by sandbox, producing 3 "human_needed" items that remain unconfirmed
- ROADMAP.md plan checkbox tracking fell out of sync (phases 2-6 show unchecked plans despite completion) because plan execution happens in submodule, not in .planning/
- No shared _find_diligence_dir utility caused the same parent-walk bug to appear independently in sources_cmd (caught by first audit) and to remain unfixed in doctor/config/migrate (caught by second audit)

### Patterns Established
- H2+fenced YAML as the canonical markdown state file format (human-readable, grep-able, agent-parseable)
- Replicate parsing per module rather than sharing utility (Phase 1 decision, validated across 6 readers)
- DILIGENT_CWD env var for test isolation across all command modules
- Lazy imports inside function bodies for heavy deps (openpyxl, python-docx, pdfplumber)
- Domain-grouped skill files (6 files covering 17 commands) rather than one-per-command
- Reconcile engine as pure function with CLI wrapper handling I/O

### Key Lessons
1. Run the milestone audit before declaring done. Phase 6 existed entirely because the first audit caught real integration gaps.
2. Replicating a pattern across modules is cheaper than debugging a shared utility, but the replication itself can drift (sources_cmd vs truth_cmd _find_diligence_dir implementations diverged).
3. The verification gate (TRUTH-04) is the most complex single behavior in the CLI and justified its own plan. Every other plan could be parallelized; the gate plan needed sequential attention.
4. Performance benchmarks with deterministic random seeds make scale tests reproducible. Worth the setup cost.
5. Skill file signatures must match actual CLI signatures exactly. A phantom argument in documentation creates a hard failure for AI agents.

### Cost Observations
- Model mix: ~40% opus, ~50% sonnet, ~10% haiku (estimated from GSD agent profiles)
- Sessions: ~10 across 2 days
- Notable: 22 plans in 2 days (~5.5 min/plan average) with full verification. Phase 6 cleanup phase added ~15 min total.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | ~10 | 6 | First milestone. Established H2+YAML, atomic writes, pure function engine pattern. |

### Cumulative Quality

| Milestone | Tests | LOC | Commands |
|-----------|-------|-----|----------|
| v1.0 | 504 | 17,475 | 17 |

### Top Lessons (Verified Across Milestones)

1. Audit before archiving. The gap-closure phase pattern works.
2. Pure function engines + CLI wrappers = testable + usable.
