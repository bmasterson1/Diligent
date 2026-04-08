# Phase 6: Integration and Cleanup - Research

**Researched:** 2026-04-08
**Domain:** Cross-phase integration fixes and tech debt cleanup (Python/Click CLI)
**Confidence:** HIGH

## Summary

Phase 6 is a gap closure phase with 6 discrete fixes identified by the v1.0 milestone audit. There is no new functionality to build. Every fix targets existing code with known locations, known bugs, and known correct patterns already implemented elsewhere in the codebase. The risk is low and the scope is narrow.

The fixes break into three categories: (1) consistency fixes where one module deviates from a pattern followed by all others (INT-01, INT-02), (2) a documentation bug that breaks an AI agent workflow (INT-03), and (3) cosmetic/hygiene items (reconcile flagged reason, stale REQUIREMENTS.md wording, orphaned write_state). All code changes have existing test infrastructure that can be extended with minimal scaffolding.

**Primary recommendation:** Execute as a single plan with 6 tasks, each self-contained and independently testable. No new dependencies, no architecture changes, no new modules.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SRC-01 | `diligent ingest <path>` logs a source document | INT-01 fix: sources_cmd._find_diligence_dir must walk parent dirs + support DILIGENT_CWD, matching all 10 other command modules |
| SRC-03 | `diligent sources list` shows all registered sources | INT-01 fix: same _find_diligence_dir consistency fix |
| SRC-04 | `diligent sources show <source-id>` displays full record | INT-01 fix: same _find_diligence_dir consistency fix |
| SRC-05 | `diligent sources diff <id-a> <id-b>` diffs two source files | INT-01 fix: same _find_diligence_dir consistency fix |
| STATE-05 | "Recent" is configurable in config.json | INT-02 fix: status_cmd._build_recent_activity must read config.recent_window_days instead of hardcoding 14 |
| TASK-03 | `diligent task complete <ws> <task_id>` prompts for summary | INT-03 fix: dd_workstreams.md skill file must document correct signature (no summary arg) |
| DIST-05 | SKILL.md files parameterized with absolute path at install time | INT-03 fix: dd_workstreams.md must reflect actual CLI interface so AI agents succeed |
</phase_requirements>

## Standard Stack

No new libraries needed. All fixes use the existing stack:

### Core (already installed)
| Library | Version | Purpose | Already Used |
|---------|---------|---------|--------------|
| click | >=8.1 | CLI framework | Yes, all command modules |
| pyyaml | >=6.0 | YAML parsing | Yes, state layer |
| pytest | >=8.0 | Test framework | Yes, 530+ tests |

### Supporting
| Tool | Purpose |
|------|---------|
| click.testing.CliRunner | Integration test harness (already used in all test files) |
| monkeypatch.setenv | DILIGENT_CWD env injection for testing (already used) |

## Architecture Patterns

### The _find_diligence_dir Pattern (reference implementation)

Every command module except sources_cmd.py follows this exact pattern. This is the **canonical** version from truth_cmd.py, reconcile_cmd.py, status_cmd.py, task_cmd.py, handoff_cmd.py, etc.:

```python
def _find_diligence_dir(env_cwd: Optional[str] = None) -> Path:
    """Locate the .diligence/ directory.

    Checks DILIGENT_CWD env override first (for testing), then walks
    up from cwd.

    Raises:
        click.ClickException: If .diligence/ not found.
    """
    if env_cwd:
        candidate = Path(env_cwd) / ".diligence"
        if candidate.is_dir():
            return candidate

    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        candidate = parent / ".diligence"
        if candidate.is_dir():
            return candidate

    raise click.ClickException(
        "No .diligence/ directory found. Run 'diligent init' first."
    )
```

**Broken version in sources_cmd.py (line 23-31):**
```python
def _find_diligence_dir() -> Path:
    d = Path.cwd() / ".diligence"
    if not d.is_dir():
        click.echo("ERROR: .diligence/ directory not found in current directory.")
        raise SystemExit(1)
    return d
```

Issues: (1) no `env_cwd` parameter, (2) no parent directory walk, (3) uses `SystemExit(1)` instead of `click.ClickException`, (4) uses `click.echo` for error instead of exception message.

### The Config Read Pattern for Recent Window

handoff_cmd.py reads config correctly:
```python
config = read_config(config_path)
default_days = config.recent_window_days * 2  # handoff doubles the window
```

status_cmd.py hardcodes instead:
```python
def _build_recent_activity(diligence: Path, window_days: int = 14) -> list[dict]:
```

The fix: read config in status_cmd and pass the value to `_build_recent_activity`.

### Caller Sites in sources_cmd.py

The broken `_find_diligence_dir()` is called at 4 locations:
- Line 98: `ingest_cmd` 
- Line 213: `sources_list`
- Line 247: `sources_show`
- Line 346: `sources_diff`

After fixing the function signature to accept `env_cwd`, all 4 callers need updating to pass `os.environ.get("DILIGENT_CWD")`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parent dir walk | Custom recursive search | Copy exact pattern from truth_cmd.py | 10 other modules already use it; consistency is the point |
| Config read for window | New config abstraction | `read_config(diligence / "config.json").recent_window_days` | Pattern already exists in handoff_cmd.py |
| STATE.md updates | New state management layer | Either wire write_state into existing mutations or remove the orphaned export | v2 concern; for now, honest removal or minimal wiring is correct |

## Common Pitfalls

### Pitfall 1: Forgetting to Update All Caller Sites
**What goes wrong:** Fix `_find_diligence_dir` signature but miss one of the 4 call sites in sources_cmd.py.
**Why it happens:** The function is called from `ingest_cmd`, `sources_list`, `sources_show`, and `sources_diff` -- easy to miss one.
**How to avoid:** Grep for `_find_diligence_dir()` (no args) after the fix. Zero matches = correct.
**Warning signs:** Tests pass in deal root directory but fail from subdirectories.

### Pitfall 2: Skill File Signature Has Interleaved Args
**What goes wrong:** Fix the documented signature but still get the argument description wrong.
**Why it happens:** The current skill file says `task complete <ws> <task-number> "<summary>"` but the actual CLI is `task complete <workstream> <task_id>` with no summary argument. The task_id is a 3-digit string like "001", not a plain number.
**How to avoid:** Check the actual Click definition in task_cmd.py line 241-243:
```python
@task_cmd.command("complete")
@click.argument("workstream")
@click.argument("task_id")
```
**Warning signs:** AI agent gets "Error: Got unexpected extra arguments" from Click.

### Pitfall 3: Reconcile Flagged Reason Bug
**What goes wrong:** The `_format_flagged_line` function (reconcile_cmd.py line 93) uses `info.key` for the display text instead of the actual reason.
**Current code:** `return f"    {info.key:<{key_width}}  flagged: \"{info.key}\""` -- displays the fact key twice.
**Root cause:** The `StaleFactInfo` dataclass for flagged facts does not carry the reason text. The fact's `flagged` dict `{"reason": str, "date": str}` is available in `reconcile_anchors.py` at line 157 where `fact.flagged` is accessed, but the reason is not propagated into `StaleFactInfo`.
**Fix approach:** Either (a) add a `reason` field to `StaleFactInfo` and populate it in the engine, or (b) pass the reason through an existing field (e.g., `new_value` or `old_value` which are empty strings for flagged entries). Option (a) is cleaner.

### Pitfall 4: write_state Orphan Decision
**What goes wrong:** Removing `write_state` breaks the test that exercises round-trip fidelity (test_state_roundtrip.py line 500-511).
**Why it happens:** The function is tested for round-trip correctness even though no production code calls it.
**How to avoid:** Two valid approaches: (1) Keep write_state for the round-trip guarantee and add a minimal wiring (e.g., update last_modified in status_cmd or another high-frequency path), or (2) remove write_state entirely and update the round-trip test. The audit flags it as orphaned; the cleanest fix is to wire it into at least one mutation path so STATE.md's `last_modified` stays current.

## Code Examples

### Fix 1: sources_cmd._find_diligence_dir (INT-01)

Replace the existing function (lines 23-31) with the canonical pattern. Add `import os` at the top. Update all 4 caller sites:

```python
# Before (each caller):
diligence_dir = _find_diligence_dir()

# After (each caller):
env_cwd = os.environ.get("DILIGENT_CWD")
diligence_dir = _find_diligence_dir(env_cwd)
```

For `ingest_cmd`, `deal_root` remains `diligence_dir.parent` (unchanged).

### Fix 2: status_cmd config read (INT-02)

In `status_cmd` function body (line 357), pass config window to `_build_recent_activity`:

```python
# Read config for recent_window_days
config_path = diligence / "config.json"
if config_path.exists():
    from diligent.state.config import read_config
    config = read_config(config_path)
    window_days = config.recent_window_days
else:
    window_days = 14

recent_activity = _build_recent_activity(diligence, window_days=window_days)
```

The `_build_recent_activity` function already accepts `window_days` as a parameter (line 206), so only the caller needs to change.

### Fix 3: dd_workstreams.md skill file (INT-03)

Replace the incorrect `task complete` section:

```markdown
### task complete
\```bash
{{DILIGENT_PATH}} task complete <workstream> <task_id> [--json]
\```
Mark a task as complete. Requires SUMMARY.md to contain real content
(non-empty after stripping HTML comments and headings). The task_id
is the 3-digit number from the task directory (e.g., "001").
```

Also fix the "Common workflows" example:
```markdown
### Create and complete a task
\```bash
{{DILIGENT_PATH}} task new financial "Review audited financials for FY2024"
# ... write SUMMARY.md content in the task directory ...
{{DILIGENT_PATH}} task complete financial 001
\```
```

### Fix 4: reconcile_cmd flagged reason display

In `reconcile_anchors.py`, add reason to StaleFactInfo propagation:

```python
# In compute_staleness, flagged facts section (~line 157):
if fact.flagged is not None:
    flagged_date = fact.flagged.get("date", fact.date)
    reason = fact.flagged.get("reason", "")
    days = (today - date.fromisoformat(flagged_date)).days
    flagged_list.append(
        StaleFactInfo(
            key=ref_key,
            old_value=reason,   # Carry reason in old_value
            new_value="",
            source_id=fact.source,
            days_stale=days,
            category="flagged",
            fact_date=flagged_date,
        )
    )
```

Then in `reconcile_cmd.py _format_flagged_line`:
```python
def _format_flagged_line(info: StaleFactInfo, key_width: int) -> str:
    reason = info.old_value if info.old_value else "no reason given"
    return f"    {info.key:<{key_width}}  flagged: \"{reason}\""
```

Alternatively, add a dedicated `reason` field to `StaleFactInfo` for cleaner semantics. The planner should decide which approach is better given the field overloading tradeoff.

### Fix 5: REQUIREMENTS.md wording

ART-02 (line 49): Change "manifest.json" reference to match actual "ARTIFACTS.md (H2+YAML format, consistent with other state files)". Current wording already says this -- verify no stale reference remains.

ART-09 (line 56): Adjust wording to reflect auto-scan behavior. Current wording already reflects the implementation. Verify this is accurate.

### Fix 6: Orphaned write_state

Simplest wiring: after any state-mutating command (e.g., truth set, ingest, artifact register), update STATE.md last_modified. The lightest approach: add a utility function that reads STATE.md, updates last_modified to now, and writes it back. Call it at the end of mutation commands.

Alternative: remove write_state from state_file.py and update the round-trip test.

## State of the Art

Not applicable. This is a bugfix/consistency phase, not a technology adoption phase.

## Open Questions

1. **write_state: wire or remove?**
   - What we know: `write_state` exists, tested for round-trip, but never called in production. STATE.md `last_modified` field is frozen at init time.
   - What's unclear: Does Bryce want STATE.md to track real last_modified, or is it a vestigial field?
   - Recommendation: Wire it minimally (update on truth set, ingest, artifact register) since the field exists and users/AI agents will expect it to be current. If the planner prefers removal, that's also valid -- just update the test.

2. **StaleFactInfo: overload old_value or add reason field?**
   - What we know: `old_value` is empty string for flagged entries, so overloading it works but is semantically impure.
   - Recommendation: Add an `Optional[str] = None` reason field to `StaleFactInfo`. It's a dataclass with no serialization concerns, and it's cleaner than field overloading.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` (if present) or pytest defaults |
| Quick run command | `cd Diligent && python -m pytest tests/ -x -q` |
| Full suite command | `cd Diligent && python -m pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SRC-01 (INT-01) | sources_cmd finds .diligence from subdirectory | integration | `python -m pytest tests/test_sources_cmd.py -x -k "subdir or parent"` | Needs new tests |
| SRC-03 (INT-01) | sources list works with DILIGENT_CWD | integration | `python -m pytest tests/test_sources_cmd.py -x -k "env_cwd"` | Needs new tests |
| SRC-04 (INT-01) | sources show works with DILIGENT_CWD | integration | `python -m pytest tests/test_sources_cmd.py -x -k "env_cwd"` | Needs new tests |
| SRC-05 (INT-01) | sources diff works with DILIGENT_CWD | integration | `python -m pytest tests/test_sources_cmd.py -x -k "env_cwd"` | Needs new tests |
| STATE-05 (INT-02) | status reads config.recent_window_days | integration | `python -m pytest tests/test_status_cmd.py -x -k "window"` | Needs new tests |
| TASK-03 (INT-03) | skill file documents correct task complete signature | unit | `python -m pytest tests/test_install_cmd.py -x -k "skill"` | Partial (install tests exist, content verification needed) |
| DIST-05 (INT-03) | skill file parameterized correctly | unit | `python -m pytest tests/test_install_cmd.py -x` | Exists |

### Sampling Rate
- **Per task commit:** `cd Diligent && python -m pytest tests/ -x -q`
- **Per wave merge:** `cd Diligent && python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_sources_cmd.py` -- add tests for DILIGENT_CWD and parent-dir walk (new test functions in existing file)
- [ ] `tests/test_status_cmd.py` -- add test verifying config.recent_window_days is read (new test function in existing file)
- [ ] `tests/test_reconcile.py` -- add test for flagged reason display text (new test function in existing file)

No new test files or framework config needed. All new tests go into existing test files.

## Sources

### Primary (HIGH confidence)
- Direct source code inspection of all affected files:
  - `Diligent/diligent/commands/sources_cmd.py` (lines 23-31: broken _find_diligence_dir)
  - `Diligent/diligent/commands/status_cmd.py` (line 206-207: hardcoded 14-day window)
  - `Diligent/diligent/commands/reconcile_cmd.py` (line 93: flagged key displayed as reason)
  - `Diligent/diligent/helpers/reconcile_anchors.py` (line 157-169: flagged StaleFactInfo creation)
  - `Diligent/diligent/commands/task_cmd.py` (lines 241-243: actual task complete signature)
  - `Diligent/diligent/skills/dd_workstreams.md` (line 51-52: wrong documented signature)
  - `Diligent/diligent/state/state_file.py` (lines 26-63: orphaned write_state)
  - `Diligent/diligent/state/models.py` (line 31: FactEntry.flagged = Optional[dict])
- v1.0-MILESTONE-AUDIT.md (integration gaps INT-01, INT-02, INT-03 with evidence)
- Reference implementations in truth_cmd.py, handoff_cmd.py, reconcile_cmd.py (correct patterns)

### Secondary (MEDIUM confidence)
- REQUIREMENTS.md: current wording for ART-02 (line 49) and ART-09 (line 56) already appears to reflect implementation; visual diff needed during execution

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new libraries, all changes in existing codebase
- Architecture: HIGH -- all patterns are copy-from-reference, no design decisions needed
- Pitfalls: HIGH -- every bug is identified with line numbers and root cause

**Research date:** 2026-04-08
**Valid until:** 2026-05-08 (stable; no external dependencies)
