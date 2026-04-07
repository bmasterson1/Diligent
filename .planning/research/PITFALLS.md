# Domain Pitfalls

**Domain:** CLI state-management tool for acquisition due diligence (structured markdown files, YAML-in-fenced-blocks parsing, atomic writes on Windows/OneDrive)
**Researched:** 2026-04-07
**Overall confidence:** MEDIUM (training-data-derived; search verification unavailable)

---

## Critical Pitfalls

Mistakes that cause data loss, state corruption, or forced rewrites.

---

### Pitfall 1: `os.rename()` Is Not Atomic on Windows

**What goes wrong:** The classic Unix atomic-write pattern (write temp file, fsync, `os.rename()` over target) does not work on Windows. `os.rename()` raises `FileExistsError` if the destination already exists. Developers switch to `os.replace()`, which does work cross-platform in Python 3.3+, but even `os.replace()` can fail with `PermissionError` or `OSError: [WinError 5]` when another process holds an open handle on the target file -- which OneDrive's sync agent routinely does.

**Why it happens:** Windows file locking semantics differ fundamentally from POSIX. Any process that has the file open (including OneDrive's FileCoAuth service, antivirus scanners, or the user's editor) can block rename/replace operations. This is not a theoretical risk: OneDrive polls modified files aggressively.

**Consequences:** Silent write failure. The temp file is left orphaned, the state file is not updated, and the next read returns stale data. If the tool swallows the exception, the analyst believes a fact was recorded when it was not.

**Prevention:**
1. Use `os.replace()` (not `os.rename()`) as the baseline.
2. Wrap the replace in a retry loop with exponential backoff (3 attempts, 100ms/500ms/2s delays) specifically catching `PermissionError` and `OSError` with `winerror` codes 5 (access denied) and 32 (sharing violation).
3. If all retries fail, leave the temp file in place with a `.diligent-pending` suffix and log a clear error the user can act on. Never silently discard the write.
4. On the read path, check for `.diligent-pending` files and offer recovery via `diligent doctor`.
5. Call `os.fsync()` on the temp file's file descriptor before closing, then `os.replace()`.

**Detection:** Unit test that opens the target file with a read handle in another thread, then attempts the atomic write. Must pass on Windows CI.

**Phase:** Phase 1 (core file I/O layer). This must be correct before any state file reader/writer is built on top.

**Confidence:** HIGH -- this is well-documented Windows behavior in Python's own docs.

---

### Pitfall 2: OneDrive Sync Creates Conflict Copies That Corrupt State

**What goes wrong:** OneDrive detects file modifications and syncs them. When diligent writes a file while OneDrive is mid-sync (or when the folder syncs across two machines), OneDrive creates a conflict copy named like `TRUTH-BryceMasterson.md` or `TRUTH (1).md`. The original file may contain a partial or old version. The analyst now has two copies of truth with no indication which is canonical.

**Why it happens:** OneDrive's conflict resolution is designed for Office documents (which use co-authoring locks), not for CLI tools that do rapid read-modify-write cycles on plain text files. OneDrive has no API for "please don't touch this file for the next 200ms."

**Consequences:** State divergence. TRUTH.md on disk disagrees with what the analyst last wrote. Downstream reconciliation produces wrong results. In the worst case, facts are silently lost when OneDrive picks the wrong version.

**Prevention:**
1. Write temp files inside the `.diligence/` directory (not in a system temp dir) so the rename is on the same filesystem and same OneDrive scope -- cross-volume renames are not atomic.
2. Add a file-level integrity marker: include a checksum (CRC32 or SHA256 of content) in a comment at the end of each state file (e.g., `<!-- checksum:a1b2c3d4 -->`). On read, verify the checksum. If it fails, the file was corrupted or partially synced.
3. `diligent doctor` should scan for OneDrive conflict copies (`*-*.md` patterns matching state file names, `* (1).md` patterns) and alert the user.
4. Document for users: "Pin the `.diligence/` folder to 'Always keep on this device' in OneDrive settings" to avoid Files On-Demand dehydration issues.
5. Consider adding a `.diligence/.lock` file with PID and timestamp, checked on every write. Not for multi-user locking -- for detecting if OneDrive has synced a lock from another machine.

**Detection:** `diligent doctor` runs checksum verification on every state file. Warns on conflict copies.

**Phase:** Phase 1 (file I/O layer) for checksums and write strategy. Phase 2 for `diligent doctor` conflict detection.

**Confidence:** HIGH -- OneDrive conflict copies are extremely well-known and are the single most common complaint from developers working in synced folders.

---

### Pitfall 3: YAML-in-Fenced-Code-Block Parsing Is Fragile and Non-Standard

**What goes wrong:** TRUTH.md embeds YAML inside markdown fenced code blocks (triple-backtick blocks). There is no standard parser for this format. Developers write regex-based extraction (`re.findall(r'```yaml\n(.*?)\n```', text, re.DOTALL)`) which breaks when:
- The YAML itself contains triple backticks (in string values)
- Indentation uses tabs vs spaces inconsistently
- The fenced block uses tildes (`~~~`) instead of backticks
- There are extra spaces after the language identifier
- A human editor auto-wraps long lines inside the block
- The file has Windows line endings (`\r\n`) and the regex expects `\n`

**Why it happens:** Markdown's fenced code block syntax has edge cases defined in CommonMark spec that naive regex ignores. Meanwhile, PyYAML has its own parsing quirks (implicit type coercion, multiline string handling).

**Consequences:** A fact is written correctly but cannot be read back. Or worse, a fact is read back with wrong values due to YAML type coercion (see Pitfall 4). Since TRUTH.md is the centerpiece of the entire system, any parse failure is a total system failure.

**Prevention:**
1. Define a strict, minimal subset of the format: always triple-backtick (never tilde), always `yaml` language tag (lowercase, no spaces after), always LF line endings inside the block (normalize on read).
2. Write a dedicated parser, not a regex. Use a state machine: scan for opening fence, accumulate lines until closing fence, pass accumulated text to `yaml.safe_load()`. Handle the CommonMark rule that closing fence must have at least as many backticks as opening.
3. Round-trip testing: for every write, immediately read back and assert equality. This is cheap (in-memory) and catches serialization bugs before they hit disk.
4. Normalize line endings on read: `content.replace('\r\n', '\n')` before any parsing.
5. Add a `diligent doctor` check that parses every YAML block in every state file and reports parse errors with line numbers.

**Detection:** Round-trip assertion on every write operation. `diligent doctor` full-file parse validation.

**Phase:** Phase 1. The parser is the foundation. Get it wrong and everything built on top is unreliable.

**Confidence:** HIGH -- these are well-understood markdown/YAML parsing issues.

---

### Pitfall 4: PyYAML Implicit Type Coercion Silently Corrupts Data

**What goes wrong:** PyYAML's `safe_load()` applies implicit type resolution per the YAML 1.1 spec. Values like `1.2e3` become float `1200.0`, `yes`/`no`/`on`/`off` become boolean `True`/`False`, `1_000` becomes integer `1000`, and critically, values that look like dates (e.g., `2024-01-15`) become `datetime.date` objects. In a diligence context:
- Revenue of `$2.4M` stored as a bare `2.4` becomes float with precision issues
- A contract date `2024-01-15` becomes a Python date object that serializes differently on round-trip
- A company ID like `0123` becomes octal integer `83`
- The answer `no` to "Is there pending litigation?" becomes boolean `False`

**Why it happens:** YAML 1.1 (which PyYAML implements) has aggressive implicit typing. YAML 1.2 (which PyYAML does not fully support) reduced this but PyYAML hasn't caught up.

**Consequences:** Facts are silently transformed between write and read. The analyst sets a fact to `"no"` and reads back `False`. Financial figures lose precision. The audit trail shows different values than what was entered.

**Prevention:**
1. Always quote string values in YAML output. When serializing, use `yaml.dump()` with `default_flow_style=False` and explicitly type all values as strings unless they are known-numeric fields.
2. Better: use a custom YAML representer that quotes every scalar value. Or use `ruamel.yaml` which preserves quoting and supports YAML 1.2.
3. Define a schema for each YAML block type. Validate types on read. If a field that should be a string comes back as a bool or date, raise an error immediately.
4. Store all fact values as quoted strings. Let the application layer (not YAML) handle type interpretation.
5. Test with a "YAML type coercion torture test" file containing: `yes`, `no`, `on`, `off`, `1.0`, `1_000`, `0123`, `2024-01-15`, `1.2e3`, `null`, `~`, `true`, `.inf`.

**Detection:** Round-trip assertion (write then read, assert string equality). Schema validation on read. The torture test in CI.

**Phase:** Phase 1. Must be solved at the same time as the parser (Pitfall 3).

**Confidence:** HIGH -- this is one of the most notorious YAML pitfalls, well-documented across the ecosystem.

---

### Pitfall 5: Append-Only Semantics Break Under Concurrent AI Agent Writes

**What goes wrong:** TRUTH.md is designed as append-only at the entry level. But when an AI agent in the IDE runs multiple `diligent truth set` commands in rapid succession (or the user scripts a batch operation), two processes may read the same TRUTH.md, both append their entry, and the second write overwrites the first append. This is the classic lost-update problem.

**Why it happens:** There is no file-level locking. The tool reads the entire file, appends in memory, writes back. If two invocations overlap, the second read does not see the first write.

**Consequences:** A validated fact silently disappears from TRUTH.md. The analyst believes it was recorded. The supersedes chain is broken.

**Prevention:**
1. Use a file-level lock (e.g., `filelock` library or a `.diligence/.lock` file with `msvcrt.locking()` on Windows / `fcntl.flock()` on POSIX). Acquire before read, release after write.
2. Keep the lock duration minimal: read-modify-write should take <50ms for a typical TRUTH.md.
3. If the lock cannot be acquired within 5 seconds, fail loudly with a clear message ("Another diligent command is writing to TRUTH.md").
4. Add a sequence number or last-modified timestamp to each state file header. On write, verify the sequence matches what was read. If not, fail with "file was modified by another process."
5. The `filelock` library is cross-platform and handles Windows/POSIX differences.

**Detection:** Integration test that spawns two concurrent `diligent truth set` commands and verifies both entries exist in the result.

**Phase:** Phase 1 (file I/O layer). The locking mechanism must exist before any write command is built.

**Confidence:** HIGH -- classic concurrency issue; especially relevant because AI agents in IDEs can fire rapid sequential commands.

---

## Moderate Pitfalls

---

### Pitfall 6: Excel/Word/PDF Parsing Libraries Fail Silently on Edge Cases

**What goes wrong:** `openpyxl` silently returns `None` for cells with certain formula types, merged cell ranges, or data validation dropdowns. `python-docx` cannot read headers/footers in all cases, loses track of revision marks, and ignores content in text boxes or SmartArt. `pdfplumber`/`pypdf` produce garbled text from scanned PDFs (no OCR), multi-column layouts, or PDF forms.

**Why it happens:** These libraries parse file formats (OOXML, PDF) that are enormously complex. Edge cases are infinite. Financial documents from accounting firms and legal documents from law firms are particularly prone to unusual formatting.

**Prevention:**
1. Never assume parse success. Always validate that extracted data is non-empty and structurally reasonable.
2. For Excel: check for merged cells explicitly (`sheet.merged_cells.ranges`), handle `None` cell values, verify sheet names exist before accessing.
3. For Word: extract text paragraph-by-paragraph and log any paragraphs that parse to empty when the surrounding context suggests content should be there.
4. For PDF: detect scanned-image PDFs (page has no extractable text) and warn the user immediately rather than producing empty results. This is explicitly out of scope per PROJECT.md (no OCR), so the correct behavior is a clear error message.
5. Log extraction statistics: "Extracted 47 cells from 3 sheets" so the analyst can sanity-check.

**Detection:** `diligent ingest` should report extraction statistics. `diligent doctor` should re-verify that ingested sources still parse correctly (catch library upgrade regressions).

**Phase:** Phase 2 (document ingestion). Build extraction with validation from the start.

**Confidence:** MEDIUM -- specific failure modes depend on the actual documents in the deal room, which are unpredictable.

---

### Pitfall 7: Windows Path Length and Character Encoding Issues

**What goes wrong:** Windows has a default 260-character path limit (MAX_PATH). Deal folders inside OneDrive paths can easily exceed this: `C:\Users\BryceMasterson\OneDrive - Company\Deals\Project Arrival\Due Diligence\Financial\Adjustments\`.diligence\TRUTH.md` is already 120+ characters before any nested content. Python operations fail with `FileNotFoundError` or `OSError` on long paths.

Additionally, source document filenames from deal rooms often contain special characters (parentheses, ampersands, em dashes, non-ASCII characters) that cause encoding issues on Windows with `open()` if not handled correctly.

**Why it happens:** Windows long path support requires either a registry key (`LongPathsEnabled`) or the `\\?\` path prefix. Most Python file operations work with long paths on Python 3.6+ if the Windows setting is enabled, but not all users have it enabled.

**Consequences:** The tool works on the developer's machine but fails on the user's machine. Or it works for the first deal but fails when the folder structure gets deeper.

**Prevention:**
1. Use `pathlib.Path` throughout (not string concatenation). It handles separators and some normalization.
2. Keep `.diligence/` internal paths short: flat structure, no deep nesting, short filenames.
3. On startup, check total path length of the `.diligence/` directory. If close to 260 chars, warn the user.
4. Use `encoding='utf-8'` explicitly on every `open()` call. Never rely on the system default encoding (which on Windows may be cp1252).
5. Test with paths containing spaces, parentheses, unicode characters, and paths approaching 260 characters.

**Detection:** `diligent init` checks path length and warns. CI tests include a long-path scenario.

**Phase:** Phase 1. Path handling is foundational.

**Confidence:** HIGH -- well-known Windows development issue.

---

### Pitfall 8: Markdown Structure Drift When Humans Edit State Files

**What goes wrong:** State files are designed to be human-readable and human-inspectable. Inevitably, the analyst (or an AI agent) will hand-edit TRUTH.md or another state file directly in their editor. They might:
- Add a blank line inside a YAML block
- Change heading levels
- Reorder sections
- Add ad-hoc notes outside the expected structure
- Use a different markdown editor that reformats the file (e.g., Prettier, auto-formatters)

The parser then fails or silently skips the modified sections.

**Why it happens:** Markdown is designed for human authoring. The moment you treat it as a structured data format, you inherit the tension between human editability and machine parseability.

**Consequences:** Facts silently disappear from the parsed view. The analyst sees them in the file but `diligent truth list` does not show them. Trust in the tool erodes.

**Prevention:**
1. Design the parser to be lenient on read: tolerate extra blank lines, inconsistent heading levels, trailing whitespace. Be strict on write.
2. Add a `diligent doctor` command (already planned) that parses all state files and reports any structural issues with line numbers and suggested fixes.
3. Define "canonical" and "tolerated" formats. Document what hand-edits are safe and which will break parsing.
4. When the parser encounters an unparseable section, do NOT silently skip it. Emit a warning with the line number and include the raw content in a "parse errors" collection that `diligent status` surfaces.
5. Consider adding a `diligent fmt` command (lower priority) that rewrites state files to canonical format.

**Detection:** `diligent doctor` structural validation. Parser warnings on every read operation.

**Phase:** Phase 1 for lenient parsing. Phase 2 for `diligent doctor` validation. Phase 3 for `diligent fmt`.

**Confidence:** HIGH -- this tension is inherent in the "markdown as database" design choice.

---

### Pitfall 9: Supersedes Chain Corruption Breaks Audit Trail

**What goes wrong:** TRUTH.md's append-only design means updating a fact pushes the old value into a supersedes chain. If the chain references are implemented as in-file pointers (e.g., referencing by position or by a generated ID), any file rewrite, reorder, or corruption breaks the chain. The analyst can no longer trace how a revenue figure evolved from $2.1M to $2.4M across three source documents.

**Why it happens:** In-file references are fragile. Unlike a database with stable row IDs, markdown content shifts when edited.

**Consequences:** The audit trail -- one of the core value propositions -- becomes unreliable. The analyst cannot defend fact provenance to investors or legal counsel.

**Prevention:**
1. Use stable, content-derived identifiers for facts: e.g., a composite key of `(workstream, metric_name)` or a UUID assigned at creation time and stored in the YAML block.
2. Never use line numbers or positional references.
3. The supersedes chain should be stored within each fact's YAML block (e.g., `supersedes: [uuid-of-previous-entry]`), not as cross-references to other parts of the file.
4. `diligent doctor` should validate that every supersedes reference points to an entry that actually exists in the file.
5. Write an invariant test: after any TRUTH.md mutation, walk every supersedes chain and verify it terminates at an entry with no predecessor.

**Detection:** `diligent doctor` chain integrity validation. Invariant test in CI.

**Phase:** Phase 1 (data model design). The identifier scheme and supersedes structure must be designed correctly from day one.

**Confidence:** HIGH -- this is a design-level decision with no easy retrofit.

---

### Pitfall 10: Click/Typer CLI Framework Mismatches with AI Agent Usage Patterns

**What goes wrong:** CLI frameworks like Click and Typer are designed for human interactive use: they prompt for confirmation, use color output, paginate long results, and format tables for terminal width. AI agents running in IDE tool-use loops need structured, parseable, non-interactive output. If the CLI prompts "Are you sure? [y/N]" during an agent loop, the agent hangs.

**Why it happens:** The developer builds and tests the CLI manually, then an AI agent invokes it programmatically. The usage patterns diverge.

**Consequences:** AI agent workflows break unpredictably. The IDE integration (the primary use case) is unreliable.

**Prevention:**
1. Never use interactive prompts in any command. All destructive operations require explicit flags (e.g., `--force`, `--yes`).
2. Support a `--json` output flag on every command that returns data. AI agents parse JSON; humans read the default formatted output.
3. Send color/formatting to stderr (or use `rich`'s console detection to disable when not a TTY).
4. Exit codes must be meaningful: 0 = success, 1 = user error (bad arguments, validation failure), 2 = system error (file corruption, I/O failure).
5. All output that an agent might parse goes to stdout. Progress messages, warnings, and diagnostics go to stderr.

**Detection:** Integration tests that invoke every command with `--json` flag and parse the output. Test with stdin not connected to a TTY.

**Phase:** Phase 1 (CLI scaffolding). The output contract must be established before commands are built.

**Confidence:** HIGH -- this is the core use case per PROJECT.md (AI agent in IDE terminal).

---

## Minor Pitfalls

---

### Pitfall 11: PyPI Name Conflict (`diligent`)

**What goes wrong:** PROJECT.md notes a PyPI name conflict. If the name `diligent` is taken, the tool cannot be published under that name. Discovering this late means changing the package name after documentation, imports, and user muscle memory are established.

**Prevention:** Resolve the PyPI name before writing any code. Check `pip index versions diligent` and the PyPI web interface. If taken, choose the name now and commit to it. Alternatives: `diligent-cli`, `diligent-dd`, `dili`.

**Phase:** Pre-Phase 1. Must be resolved before `pyproject.toml` is written.

**Confidence:** HIGH -- PROJECT.md explicitly flags this.

---

### Pitfall 12: `pipx` Installation Edge Cases on Windows

**What goes wrong:** `pipx` on Windows sometimes has PATH issues where the installed script is not found after installation. Also, `pipx` creates isolated venvs, so dependencies like `openpyxl` are correctly isolated, but if the user also has a system-level Python with conflicting packages, confusion arises.

**Prevention:**
1. Test the full `pipx install` flow on a fresh Windows machine (or in CI with a clean Windows image).
2. Include a post-install verification command: `diligent --version` in installation docs.
3. Consider supporting `uv tool install` as an alternative to `pipx` (uv is becoming the standard Python installer in 2025-2026).

**Phase:** Phase 3 (distribution/packaging). Not urgent for dogfooding (can run from source during early phases).

**Confidence:** MEDIUM -- based on general Windows Python packaging experience.

---

### Pitfall 13: Performance Degrades as TRUTH.md Grows

**What goes wrong:** If every fact update appends a new YAML block and the old one stays (supersedes chain), TRUTH.md grows monotonically. After 200+ facts with multiple revisions each, the file could reach thousands of lines. Parsing the entire file for every `diligent truth get` becomes slow, violating the <2s requirement.

**Prevention:**
1. Benchmark early: create a synthetic TRUTH.md with 500 facts and 3 revisions each. Measure parse time.
2. If parsing is slow, add an index file (`.diligence/truth.index.json`) that maps fact keys to byte offsets for fast lookup, rebuilt on any write.
3. Alternatively, use `diligent compact` to archive old superseded entries into a `TRUTH-archive.md` while keeping only current values in TRUTH.md.
4. Profile before optimizing -- for a typical deal with 50-100 key facts, this may never be an issue.

**Phase:** Phase 2 or Phase 3 depending on actual deal size. Monitor during dogfooding.

**Confidence:** MEDIUM -- depends on actual usage volume.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: File I/O layer | Atomic writes fail on Windows/OneDrive (Pitfalls 1, 2) | Retry loop with backoff, checksum verification, `.diligent-pending` recovery |
| Phase 1: TRUTH.md parser | YAML coercion and fenced-block parsing (Pitfalls 3, 4) | Dedicated state-machine parser, quote all strings, round-trip assertions, torture test |
| Phase 1: Data model | Supersedes chain fragility (Pitfall 9) | UUID-based fact identifiers, in-block chain references, never positional |
| Phase 1: CLI scaffolding | Agent-hostile output (Pitfall 10) | `--json` on all commands, no interactive prompts, stdout/stderr separation |
| Phase 1: Foundation | File locking for concurrent writes (Pitfall 5) | `filelock` library, sequence-number optimistic concurrency |
| Phase 2: Document ingestion | Silent parse failures in Excel/Word/PDF (Pitfall 6) | Extraction statistics, explicit warnings for empty/suspicious results |
| Phase 2: Doctor command | OneDrive conflict detection (Pitfall 2) | Scan for conflict-copy filename patterns |
| Phase 2: State validation | Human edits break structure (Pitfall 8) | Lenient parser, structural warnings with line numbers |
| Phase 3: Distribution | PyPI name conflict (Pitfall 11) | Resolve before any code; check now |
| Phase 3: Packaging | pipx/Windows PATH issues (Pitfall 12) | Test full install flow on clean Windows |
| Phase 3: Scale | TRUTH.md performance at scale (Pitfall 13) | Benchmark with synthetic data; index file if needed |

---

## Sources

- Python documentation: `os.replace()` behavior on Windows (docs.python.org)
- CommonMark specification: fenced code block parsing rules (spec.commonmark.org)
- PyYAML documentation: implicit type resolution (pyyaml.org)
- OneDrive sync conflict behavior: Microsoft support documentation
- `filelock` library documentation (pypi.org/project/filelock)
- Windows MAX_PATH documentation (Microsoft Learn)

**Note:** Web search was unavailable during this research session. All findings are derived from training data knowledge of Python, Windows, OneDrive, YAML, and markdown ecosystems. Confidence levels reflect this: findings marked HIGH are well-established, widely-documented issues that are unlikely to have changed. Verify specific library version behaviors against current documentation during implementation.
