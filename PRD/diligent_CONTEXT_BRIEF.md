# diligent — Context Brief for New Sessions

**Purpose of this document:** This is a long-form context brief written to be loaded into a fresh AI session (Claude, the GSD discuss-phase agent, or any other tool) that needs to help build the `diligent` tool. The PRD (`diligent_PRD.md`) tells you *what* diligent is. This document tells you *why it exists in the shape it does*, *who the user actually is when they're frustrated*, and *what the answers are to the probing questions a good product manager would ask during a requirements-gathering conversation*. Read this end-to-end the first time. After that, treat the table of contents as a lookup index.

**How to use it:** When asked a question about diligent that isn't directly answered in the PRD, find the relevant section here. If the section gives you the answer, give it. If it doesn't, *say so explicitly* rather than guessing — the user (Bryce) values calibration over confident-sounding-but-wrong, and one of his core principles is "stop at verification gates."

---

## Contents

1. The user and the situation
2. The actual problem, in the user's own framing
3. Why existing tools fail (and the failure modes that matter)
4. The mental model: GSD applied to diligence
5. What "done" looks like — happy path walkthrough
6. The non-obvious design decisions and why they were made
7. Working style and editorial principles (these are constraints)
8. The current Project Arrival context
9. Probing questions a PM would ask, and the answers
10. Things explicitly out of scope and why
11. Things that are open and need to be decided during the build
12. Operational items the user is handling outside the build itself
13. Things to NOT suggest

---

## 1. The user and the situation

The primary user is **Bryce Masterson**. He is an MBA student at the University of Michigan, currently working as a deal apprentice for Phillip Weinstein (managing partner of Atropates Capital, a self-funded search) on Project Arrival — a search-fund-style acquisition of OnTime 360, a B2B SaaS courier dispatch platform. The deal is post-LOI at approximately $9.5M EV with about $2.4M ARR and 58% EBITDA margins. Bryce contributes roughly 10–15 hours per week across financial diligence, retention analysis, investor materials, and competitive research.

Bryce is **technically literate but not a software engineer**. He uses Antigravity IDE (Google's agentic Gemini-based IDE) as his primary work environment, points it at deal folders, and prompts the agent to write Python scripts, build Excel models, draft Word memos, and consolidate outputs. He also uses Claude (specifically Claude Cowork on the desktop, plus Claude.ai chat) as a parallel agent against the same deal folder. He runs Windows on a personal machine with deal folders living in `C:\Users\maste\OneDrive\Desktop\ProjectArrival\` — synced through OneDrive but not accessed by anyone else.

He is **building diligent for himself first**, with the explicit intent that the tool become reusable across every future deal he works on. The forward-looking model is: "I use GSD on nearly every program I start to build — I want a similar tool I'd run on every diligence engagement of my career." Secondary users are colleagues in his ETA cohort and Searchfunder network who would be granted commercial use for free at his discretion under the BSL license terms (see PRD section 6.1).

He is **not building this for partners, principals, investors, or counterparties**. They will continue to receive Word docs, Excel models, and PowerPoint decks the way they always have. diligent's job ends at producing clean inputs to those deliverables. The tool is invisible to anyone who isn't the analyst.

**Personality and working style** (extremely relevant for design decisions):

- Direct, casual tone. No em dashes. Pushes back hard on AI template phrasing, sycophancy, and unsolicited elaboration.
- Values calibration over confident-but-wrong claims. Explicitly affirms behavior like "stop at verification gates" and "honest calibration over overconfidence."
- Prefers concise, traceable answers: state the fact, then the evidence.
- Wants single consolidated prompts and instructions, not iterative clarification cycles with multiple options.
- Corrects misreads sharply and efficiently. Over-explanation is unwelcome.
- Treats document hierarchy seriously: Word for working materials and analytical deliverables, PowerPoint for investor-facing presentations, Excel for models and reconciliation. This preference is shared by Phil Weinstein and is the standard search-fund convention.

These are not stylistic preferences — they are *design constraints*. Any feature, prompt template, or output format diligent generates that contradicts them will be ripped out.

---

## 2. The actual problem, in the user's own framing

Quoting from the conversation that produced the PRD:

> "I'm having the issue of keeping everything in order, understanding what is most updated, understanding what has been learned, understanding what is the most current state of truth in the due diligence process. We start with a confidential information memorandum with the profit and loss, balance sheet, and just a bunch of initial documents. Then we do our initial analysis of V1, and then we keep looking. We might update it from time to time, and then the owner or the seller gives us new information. Now, with that new information or more updated information from the owner, we now have to update our version one into version two."

The pain is **state drift across versions of analytical work**. It is not analytical capability. Bryce can already, with AI assistance, build a fully-reconciled retention analysis, an EBITDA bridge, an industry segmentation, and a forty-slide investor deck. He has done all of these on Project Arrival, repeatedly, across versions v1 through v9. The problem is that when v3 of the retention analysis is the current truth and the investor deck is still pulling numbers from v2, *nothing in his workflow tells him that the deck is now stale*. He has to remember it. And as the deal grinds on for months, the number of these implicit dependencies grows past the point where any human can hold them in working memory.

A second framing he used, also worth holding onto:

> "The reason I would be wanting to build a similar program is so that I could do all of my due diligence within an IDE. I don't want to just manually create different folder structures. I want to be able to do everything in an IDE and create Python scripts and do my data analysis in there while simultaneously maintaining a structure and cohesiveness."

The constraint is that the tool **must live where his work already lives**, which is Antigravity IDE pointed at a local OneDrive folder. He is not going to leave the IDE to update a Notion database or click around in a web app. Anything that requires context-switching out of the IDE will lose. This is why diligent is a CLI plus skill files, not a SaaS, not a web app, not even a desktop GUI.

A third framing, on the resumability problem:

> "When context degrades, I prefer a clean handoff prompt for a fresh window over continuing in a degraded state."

This is currently a manual operation he performs himself — when an Antigravity or Claude session has accumulated too much context and answers are getting worse, he asks Claude to write a handoff prompt for a fresh session. The `diligent handoff` command formalizes what he's already doing manually.

---

## 3. Why existing tools fail (and the failure modes that matter)

This is the section to consult when anyone asks "why not just use [existing tool]?" The PRD covers this briefly in section 1.3; this is the longer version with the actual reasoning.

**Virtual data rooms (Datasite, Intralinks, Firmex, ShareFile).** These are document custody platforms. They tell you *which files exist* and who has accessed them. They do not tell you *which numbers are currently true* or which downstream artifacts depend on which sources. The seller will use a VDR; the analyst still has to download files locally to do real work on them, and at that point the VDR has dropped out of the workflow. Bryce works against local files in OneDrive, not against the VDR, because Antigravity needs filesystem access to operate.

**Diligence checklist tools (DealRoom, Midaxo, SourceScrub).** These are issue trackers for diligence questions. They track open vs. closed status. They do not version answers, do not trace facts back to source documents, and do not detect when an answer goes stale because the underlying data was updated. They are essentially Jira for deal questions, and they suffer from the same problem Jira does: the metadata is overhead, nobody updates it consistently, and the actual analysis lives somewhere else (Excel) anyway.

**Knowledge management platforms (Notion, Coda, Obsidian, Roam).** Bryce explicitly considered these and rejected them. Three reasons. First, they require him to leave the IDE every time he wants to update state, which kills the workflow loop. Second, they are unopinionated — the discipline has to come from the user, which is exactly what is failing now without a tool. Third, they store data in proprietary formats (Notion) or non-structured markdown (Obsidian), which means an AI agent reading the data has to either use an API or do fragile text parsing. The diligent design uses plain markdown with structured YAML blocks specifically because it wants both human readability *and* deterministic machine parsing, on the local filesystem the AI agent already has access to.

**Excel itself.** This is the strongest competitor and the honest answer to "why not just use a spreadsheet for state tracking?" Excel is what most search-fund analysts actually use today as their state layer — a master "tracker" workbook with tabs for sources, questions, and validated facts. The problem is that Excel is opaque to AI agents (you can read cells programmatically but reasoning over them is harder than reading markdown), it has no enforcement layer (any cell can be edited at any time, with no audit trail), and it conflates analytical workspaces with state tracking. Bryce already runs his retention analysis *in* Excel. Putting his diligence state in another Excel file would multiply the existing problem rather than solving it.

**Git itself.** This is the meta-answer. Git tracks file versions perfectly. It does not, however, have any concept of *which fact is currently true across multiple files*, which is the actual problem. You can `git log` your way to an answer about which version of `retention_v9.docx` is current, but you cannot ask git "what is the current value of `t12m_retained_customers` and which artifacts depend on it." Git is necessary plumbing but not sufficient as a state model. diligent does not replace git — Bryce can put his deal folder under git if he wants, and most of his colleagues won't.

**GSD itself.** GSD is the inspiration and the closest thing to what Bryce wants, but it is built for software engineering. Its plan/execute/verify loop assumes the verification gate is "do tests pass and does code compile," which has no analog in diligence. Its phase model assumes you are building net-new functionality on a codebase, not validating a constantly evolving set of facts about an existing business. Lifting GSD's *structural insight* (markdown state files that any agent can read) and applying it to diligence is the entire premise of diligent. Lifting GSD's actual implementation would not work — the verbs are wrong.

---

## 4. The mental model: GSD applied to diligence

If you have read the GSD README, the mental mapping is this:

| GSD concept | diligent equivalent |
|---|---|
| `PROJECT.md` (vision, always loaded) | `DEAL.md` — target name, thesis, valuation, key people, current LOI status |
| `REQUIREMENTS.md` (v1/v2/out of scope) | The set of diligence questions across all workstreams (lives inside `STATE.md` and per-workstream `CONTEXT.md`) |
| `ROADMAP.md` (phases) | `WORKSTREAMS.md` — financial, retention, technical, legal, HR, commercial |
| `STATE.md` (decisions, blockers) | `STATE.md` — current position, blocked items, open questions, what's queued next |
| Per-phase `RESEARCH.md` | Per-workstream `RESEARCH.md` — what we investigated and what we found |
| Per-phase `PLAN.md` (atomic XML task) | Per-task `PLAN.md` — atomic analysis brief: inputs, method, expected outputs, verification |
| Per-phase `SUMMARY.md` | Per-task `SUMMARY.md` — what was done, what changed in TRUTH.md, what new questions it raised |
| Per-phase `VERIFICATION.md` | Per-task `VERIFICATION.md` — reconciliation log against TRUTH.md anchors |
| Atomic git commits per task | Atomic state file updates per fact (TRUTH.md is append-only at the entry level) |

The single non-obvious addition is **`TRUTH.md` itself**. GSD does not have an analog. In coding, the "truth" is the running code — there is no need to store derived values because you can re-run the program. In diligence, the truth is a set of validated quantitative facts about a business, computed from source documents that are themselves changing. There is no equivalent of "re-run the program." You have to *cache the validated answer* and track its provenance. TRUTH.md is that cache. It is the most important file in the entire system and the one that would justify the build by itself, even if nothing else from the PRD got built.

When in doubt about a design question, ask: **does this serve the discipline of TRUTH.md being the single source of validated facts?** If yes, build it. If no, defer it.

---

## 5. What "done" looks like — happy path walkthrough

This is the scenario the design is optimized for. A new user (Bryce or a colleague) is starting diligence on a new deal. Walk through it end-to-end:

**Day 0.** User installs diligent globally on their machine with `pipx install diligent`. Optionally runs `diligent install --antigravity --global` to drop SKILL.md files into Antigravity's skills directory. This is a one-time setup, never repeated.

**Day 1, morning.** Broker emails over the initial document set: a CIM, three years of P&L, a customer list, a few contracts. User creates a folder on their Desktop named after the deal — say, `~/Desktop/ProjectAlpha/` — and saves the documents inside. User opens Antigravity and points it at the folder. So far this is exactly the user's current workflow.

**Day 1, afternoon.** User opens a terminal in the folder and runs `diligent init`. The tool prompts for deal name, target, deal code, a one-paragraph thesis, and key people. It writes `.diligence/` with the six core files populated as templates. Total time: under two minutes.

**Day 1, end of day.** User runs `diligent ingest CIM.pdf`, `diligent ingest P&L_2023-2025.xlsx`, etc., for each document the broker sent. Each ingest prompts for the document date, the parties involved, and which workstreams the document touches. The user takes maybe ten minutes to ingest the initial document set. Now `SOURCES.md` contains a clean register.

**Day 2.** User asks Antigravity to read the CIM and produce an initial summary. The agent writes a Python script and a Word memo in the deal folder. The user reviews it, and for each quantitative claim that the agent extracted, runs `diligent truth set <key> <value> --source <source-id>`. After this exercise, TRUTH.md contains the seller-claimed metrics: ARR, customer count, EBITDA margin, headcount. Each one has a source citation pointing back to a SOURCES.md entry.

**Days 3–10.** User runs analyses. For each analytical artifact the agent produces (retention analysis, customer cohort cube, EBITDA bridge), the user runs `diligent artifact register <path> --references <fact_keys>`. The artifact manifest now knows that `retention_v1.docx` depends on `t12m_cohort_size`, `t12m_retained`, and `ndr_pct`. User can run `diligent artifact list` at any time to see all registered deliverables.

**Day 11.** Seller sends an updated customer list. User runs `diligent ingest Customer_List_v2.xlsx --supersedes ARRIVAL-003` (where ARRIVAL-003 is the source ID of the original customer list). diligent automatically runs `diff_excel_versions.py` on the two files and shows what changed. User sees that customer 253's MRR went from $19,665 to $20,065. User updates the affected TRUTH.md fact: `diligent truth set customer_253_mrr 20065 --source ARRIVAL-019`. diligent records the prior value in the supersedes chain.

**Day 11, fifteen minutes later.** User runs `diligent reconcile`. diligent walks the artifact manifest, finds that `retention_v1.docx` references `customer_253_mrr` (either via a manual `--references` flag at registration or via an embedded citation tag in the document), and flags the artifact as stale. The user knows immediately which deliverable needs to be regenerated.

**Day 30.** Investor partner asks: "where did the $20,065 number for customer 253 come from?" User runs `diligent truth trace customer_253_mrr`. diligent shows the full history: original value $19,665 from ARRIVAL-003 on day 1, updated to $20,065 from ARRIVAL-019 on day 11, with the diff between the two source files attached. User has the answer in ten seconds.

**Day 60.** User's Antigravity session has been running for hours and is starting to give worse answers. User runs `diligent handoff`. diligent reads STATE.md, WORKSTREAMS.md, and the most recently touched files, and produces a markdown document the user can paste into a fresh agent session. The new session comes up to speed without re-uploading any documents.

**Day 90.** Deal closes (or dies). User commits the deal folder to a private git repo for archival. The `.diligence/` directory is part of that commit. Six months later, when a similar deal comes in, the user can reference the archived `.diligence/` to remember how they structured the workstreams and what the key questions were.

This is the happy path. Every command in the PRD exists to support some step in this walkthrough. If a proposed feature does not support some step in this walkthrough, it should be cut.

---

## 6. The non-obvious design decisions and why they were made

This is the section to consult when anyone asks "why is it built that way?"

**Why a CLI and not a TUI or GUI.** Because Bryce works inside an AI-IDE that already has its own interface, and the CLI is the one universal way to invoke a tool from inside an agent's reasoning loop. A GUI would require the agent to drive a window. A TUI would require the agent to handle interactive input. A CLI takes arguments, runs, prints output, exits — which is exactly what an LLM agent's tool-use loop can handle natively.

**Why Python and not TypeScript or Go.** Because the helper scripts (reconcile_anchors, diff_excel_versions, fact_parser) are doing data work on Excel and Word files, and Python's `openpyxl` and `python-docx` libraries are the de facto standard for this. Bryce already writes Python with AI assistance. A TypeScript implementation would force a polyglot repo. Go would force Bryce to learn a new language.

**Why markdown state files and not a SQLite database.** Because an AI agent operating in the deal folder can read markdown directly into its context window, without any tool calls or SQL queries. Markdown is the lowest-friction format for agent consumption. SQLite would require the agent to execute queries, and worse, would make the state files invisible to the human user without a viewer. Plain markdown is human-inspectable in any text editor, diff-able in git, and grep-able from the command line. The cost is that you have to define a parsing convention (YAML inside fenced code blocks, in this case), but that cost is one-time.

**Why TRUTH.md is append-only at the entry level.** Because the most common cause of state corruption in a manual workflow is accidentally overwriting a value without recording what it used to be. By making updates append a new value and push the prior value into a `supersedes` chain, you get a free audit trail with no extra discipline required. The cost is that TRUTH.md grows over time, but a typical deal will accumulate a few hundred fact entries at most, which is trivial.

**Why source documents are never moved or modified.** Because the source documents are the ground truth and any operation that touched them would create the possibility of corruption. diligent is a metadata layer over the existing files, not a filing system. The user can rip out `.diligence/` at any time and lose nothing except the metadata layer. The original work is independent. This is also what makes the tool safe to test on a real deal — Project Arrival's source documents will not be touched even if diligent has bugs in v0.1.

**Why no AI integration inside diligent itself.** This is the design decision most likely to be questioned. diligent does not call any LLM APIs. It does not have an OpenAI or Anthropic key. It does not even know that AI exists. The AI integration happens in the *other direction*: the user's IDE runtime (Antigravity, Claude Code) has the AI, and diligent provides skill files and a CLI that the runtime's agent can invoke. The reason this matters: it keeps diligent zero-config, zero-credential, zero-cost, and runtime-agnostic. The same diligent install works whether the user is on Antigravity, Claude Code, Cursor, Windsurf, or no AI at all. The AI is a *consumer* of diligent's state, not a component of diligent.

**Why a single tool that lives inside each deal folder, instead of a global registry of all deals.** Because Bryce wants the deal folder to be self-contained. If he zips up `~/Desktop/ProjectArrival/` and sends it to a colleague, the colleague gets everything — source documents, analytical work, and the diligence state layer. If state lived in a central registry on Bryce's machine, transferring a deal would require exporting and re-importing. The folder-as-portable-unit design also matches the way searchers actually work: they archive completed deals, they hand deals off to junior analysts, and they sometimes share deals with co-investors. Self-contained folders make all of these flows trivial.

**Why workstreams are named conventionally instead of being free-form tags.** Because almost every diligence engagement has the same workstreams (financial, commercial/retention, technical, legal, HR/people, integration). Pre-defined templates give the user a starting point and impose enough structure that two different deals look similar enough to be navigable by anyone familiar with one of them. Free-form tags would let users invent their own taxonomy, which is exactly the discipline failure mode we're trying to prevent. The PRD recommends shipping templates as defaults but allowing customization — this is the right call.

**Why the `dd:` prefix for skill commands.** Because `diligent:` is too long to type and `d:` would collide with too many other commands in busy skill namespaces. `dd:` is short enough to be ergonomic, distinctive enough to not collide, and mnemonically obvious (due diligence). This matches GSD's `gsd:` convention.

**Why BSL 1.1 instead of MIT or AGPL.** Because Bryce wants the option to monetize without precluding the option to give it away to friends. MIT lets anyone do anything, including build a competing commercial product. AGPL is too aggressive for this audience (search-fund analysts will not read the legal text and will be scared off). BSL gives Bryce full commercial rights, lets the source be public for inspection, allows non-commercial use freely, and converts to Apache 2.0 after four years so it eventually becomes truly open. It is the same license Sentry, CockroachDB, and HashiCorp use. The honest caveat is that BSL is technically not OSI-approved "open source" — it is "source available." Bryce should not call diligent open source in marketing materials; he should call it source-available or use Anthropic's term "shared source."

---

## 7. Working style and editorial principles (these are constraints)

These are the rules Bryce applies to his own work and to the work of any AI agent he collaborates with. They are the *defaults* diligent should bake into its prompt templates, output formats, and skill files. Violating them is not a stylistic miss — it's a feature defect.

**Source every claim.** Every quantitative statement must trace back to a source document or a script that computed it. Unsourced claims are not "draft" or "tentative" — they are *defects* that get pushed into the open questions queue until they can be sourced. This rule is the philosophical foundation of TRUTH.md and should be enforced in every command that proposes to update a fact.

**Stop at verification gates.** When a proposed update would change an existing fact value in a way that exceeds tolerance, or when two sources disagree on a fact, the system must stop and surface the discrepancy rather than proceeding. The agent must not "just pick one" or "average them" or "use the more recent one." It must hand the discrepancy back to the user and add it to the open questions queue. Bryce explicitly affirmed this behavior multiple times during Project Arrival.

**Curiosity not performance.** This was the editorial principle for Project Arrival's investor briefings, but it applies to diligent in a deeper way. The system exists to help the user *understand the business factually*, not to help them *look like they understand the business*. This means: no inferential framing, no strategic recommendations, no "talking points," no meeting playbooks. Just facts with sources. When generating output (SUMMARY.md, status reports, handoff prompts), diligent should describe what is known and what is open, not advise on what to do about it.

**Honest calibration over overconfidence.** When the system is uncertain, it should say so. When two sources disagree, it should show both. When a fact is computed by a script, it should say so and link the script. Confident-sounding but wrong claims are worse than admitting uncertainty.

**Concise output, no AI template phrasing.** Diligent's user-facing output should be direct and short. "Here's what changed since you last ran reconcile: 3 facts updated, 2 artifacts now stale (retention_v1.docx, deck_v3.pptx)." Not: "Great question! I'd be happy to help you reconcile your diligence state. Let me walk you through what I found..." Bryce will rip this kind of phrasing out wherever he sees it.

**No unsolicited elaboration.** When the user asks for X, give X. Do not also offer Y and Z. Do not add caveats unless they materially affect the answer. If the user wants more, they will ask.

**No em dashes.** This is a real preference, not a joke. Use periods, semicolons, commas, or restructured sentences. If you find yourself wanting an em dash, the sentence probably wants to be two sentences.

**Document hierarchy.** Word for analytical deliverables, PowerPoint for investor-facing presentations, Excel for models. Markdown for state and notes. JSON for structured data the human will rarely look at directly. This is convention in search-fund work and Bryce shares it.

**Fresh context windows over degraded ones.** When a session is going poorly, the right move is to dump state to a handoff document and start a new session, not to keep pushing on the degraded one. This is why `diligent handoff` exists.

---

## 8. The current Project Arrival context

This section gives a fresh agent enough context about the actual deal to make realistic design decisions and answer "would this work for the user's actual situation?" questions.

**The target.** OnTime 360 is a B2B SaaS courier dispatch and last-mile logistics platform built on .NET, owned and operated by Jeremiah Tilley through his company Vesigo Studios, LLC. About 550 active customers, ~$2.4M ARR, ~58% EBITDA margins, ~$55M/month in billing volume flowing through the platform with zero payment processing revenue captured (the primary value creation thesis). Customer base skews toward courier and logistics SMBs serving healthcare and pharmaceutical end clients.

**The deal team.** Phillip Weinstein ("Phil") is the managing partner of Atropates Capital and the deal lead. Mike Donnell is the broker. Kevin Christmas at Holland & Knight is drafting the purchase agreement. Jane Fidel is advising on embedded payments. Brenda Craig owns Craig Safety Technologies (CST), a bolt-on acquisition target. Bryce reports to Phil and contributes 10–15 hours a week.

**The status.** The deal is post-LOI at approximately $9.5M EV. Phil presented at the Wharton ETA Conference April 2–3, 2026. The most recent major work session (April 5) produced an investor-grade customer base industry briefing for Phil's April 6 meeting with Jeremiah. Bryce has built nine versions of the retention analysis, has resolved data quality issues across multiple invoice file versions from the seller, and has produced an integrated investor deck.

**The validated anchor metrics, as of the most recent reconciliation.** T12M cohort = 573 customers. T12M retained = 492. T12M churned = 81. Starting MRR = $210,688. Ending MRR = $184,704. NDR = 87.7%. GDR = 80.0%. Logo retention = 85.9%. Active tagged customers = 544. Current MRR = $196,757. Churn records = 112. **These are the numbers diligent's `truth set` command should be able to record on day one of the Milestone 2 acceptance test.**

**The pattern that justifies the build.** Bryce has manually reconciled these numbers across multiple Word docs, an Excel workbook, ten investor charts, and a deck. Every reconciliation cycle is "build → verify against raw source data → correct → re-verify before sending anything to Phil or investors." He has been doing this manually with explicit "every metric must reconcile at 0.0% variance across tabs and documents" as a personal rule. *That rule is what diligent automates.* If you are ever uncertain whether diligent should support a particular workflow, ask: "is this Bryce's manual reconciliation discipline, but in code?"

**The frustration that triggered the build.** Bryce has hit context window degradation on Project Arrival multiple times, requiring manual handoffs to fresh Antigravity sessions. He has had multiple instances of "wait, which version of the customer file are we using" requiring archaeology through OneDrive folder timestamps. He has had to retract investor-facing claims that were based on stale data because a downstream artifact didn't get refreshed. Every one of these incidents is a feature requirement.

---

## 9. Probing questions a PM would ask, and the answers

This is the heart of the document. GSD's `/gsd:new-project` discuss phase will ask questions in this style. Here are the answers, written as if Bryce were sitting next to you.

**Q: What does v1 success actually look like in concrete terms?**
A: Bryce uses diligent on Project Arrival for at least four consecutive weeks without abandoning it. `diligent reconcile` catches at least one real staleness incident he would otherwise have missed. He successfully performs one clean handoff between AI sessions using `diligent handoff`. He uses it on a second deal (probably the CST bolt-on or a future search target) with zero per-deal customization beyond `diligent init`. At least one colleague adopts it for their own deal for at least two weeks. PRD section 9 codifies this. If three of these five happen, v1 is a win.

**Q: What's the smallest possible thing that would still be valuable?**
A: A CLI that does just `diligent init`, `diligent ingest`, `diligent truth set/get/trace`, and `diligent reconcile`. No workstreams, no tasks, no questions, no handoff, no skill files. Roughly half of Milestone 1 plus all of Milestones 2 and 3. If only this got built, it would still solve the core "what is current truth and which artifacts are stale" problem. Everything else is leverage on top.

**Q: Who is the user when they're frustrated, and what are they doing in that moment?**
A: The user is Bryce, it's 11 PM, Phil has asked him a question for tomorrow morning's call that requires reconciling a number from a slide deck against a number from the most recent retention model. He doesn't remember which version of which file is current. He's grepping through his OneDrive folder by file modification date trying to figure out what supersedes what. He's about to give Phil a number and isn't sure if it's right. He wants to type one command and have a definitive answer in five seconds. *That moment* is what diligent is built for. Every design decision should be filtered through "does this help that moment?"

**Q: What does the user explicitly NOT want?**
A: A web app. A SaaS subscription. A new Notion-style workspace to maintain. Anything that requires leaving the IDE. Any feature that asks the user to fill in fields they don't immediately see the value of. Multi-user collaboration. Permissions systems. A dashboard. AI integration that requires API keys. Anything that touches the original source documents. Any output that uses AI template phrasing like "Great question!" or "I'd be happy to help." Em dashes. Sycophancy. Gantt charts. Sprint ceremonies.

**Q: What's the single most important file in the system?**
A: TRUTH.md. If TRUTH.md is wrong or unparseable, nothing else matters. Every command in diligent either reads or writes TRUTH.md, and the parser for TRUTH.md (`fact_parser.py`) is the most-used code in the entire codebase. This is the file where the build should focus its testing effort.

**Q: What's the riskiest technical assumption?**
A: That you can reliably detect which TRUTH.md facts a deliverable artifact (Word doc, Excel model, PowerPoint deck) depends on. There are two approaches: (a) the user manually flags dependencies at registration with `--references key1,key2`, and (b) the user embeds tagged citations in the document body like `{{truth:t12m_retained}}` that `artifact_scanner.py` finds by parsing. Approach (a) is simple but requires discipline. Approach (b) is powerful but requires the user to remember to insert tags as they write, and only works in formats where you can embed text. The PRD recommends supporting both. The risk is that neither approach is good enough in practice and the user finds reconciliation too noisy or too quiet to trust. This needs to be tested with real Project Arrival artifacts during Milestone 3.

**Q: What's the riskiest non-technical assumption?**
A: That Bryce will actually use the tool he builds. Everyone who builds tools for themselves overestimates how much they'll use them. The mitigation is: build Milestone 1 against an existing real deal (Project Arrival, in shadow mode), not against a hypothetical future deal. If after Milestone 1 Bryce isn't reaching for the tool naturally, the design is wrong and additional features won't fix it.

**Q: Why now?**
A: Because Bryce is currently feeling the pain on Project Arrival (which is post-LOI, deep in diligence, with Phil prepping for partner conversations), and because GSD just shipped v1.31 with Antigravity support, which makes the skill-installation pattern viable in his actual IDE. Twelve months ago Antigravity didn't exist as a target runtime. Twelve months from now, Project Arrival will be closed (or dead) and the pain will be less acute.

**Q: What's the failure mode where the tool gets built but doesn't get used?**
A: Bryce builds the full PRD over six weekends, installs it on Project Arrival, uses it for three days, finds friction in some specific command, doesn't fix the friction because he's busy with Phil's investor follow-up, gradually stops opening it, and within two weeks is back to the manual workflow. Mitigation: build in milestones, dogfood after every milestone, ruthlessly fix friction before adding new features. Acceptance tests for each milestone are run against real Project Arrival data, not synthetic fixtures.

**Q: What's the failure mode where it gets used but doesn't actually help?**
A: The tool faithfully tracks state but Bryce still makes the same mistakes because the staleness detection is too noisy (false positives every time he reconciles), or too quiet (misses the actual staleness incidents that matter). Mitigation: tune `reconcile_anchors.py` against the real Project Arrival data set. The acceptance test for Milestone 3 is "register the existing OnTime briefing, update one anchor metric, run reconcile, confirm the briefing is flagged stale." If that doesn't pass cleanly, the design is wrong.

**Q: What's the simplest version of TRUTH.md you could ship?**
A: A markdown file with a heading per fact and a YAML block under each heading containing `value`, `source`, `date`, and `supersedes` (an array of prior values). No types, no validation rules, no computed-by tracking, no tags, no workstream assignments. Add those one at a time as the need becomes apparent during dogfooding. Resist the urge to over-design the schema upfront.

**Q: How do you handle a fact that is genuinely uncertain?**
A: Set the value with a `--notes` flag describing the uncertainty, and flag the fact for review with `diligent truth flag <key> --reason "two sources disagree"`. Flagged facts show up in `diligent status` and `diligent truth list --stale`. The fact is not removed or hidden — it's tracked as known-uncertain. This is critical because diligence is full of "we think it's X but the seller says Y" situations and the system has to be able to represent them without forcing premature closure.

**Q: What happens when the user changes their mind about a workstream's structure?**
A: They edit the markdown files directly. diligent does not lock state files or require all updates to go through commands. The CLI is *one* way to update state; the text editor is the other. The only invariants are that the file remains parseable (which `diligent doctor` checks) and that semantic relationships (TRUTH.md fact keys referenced by artifacts, source IDs referenced by facts) remain valid (which `diligent reconcile` checks). This is deliberate. Forcing all state changes through a CLI would make the tool feel like a database, which is exactly the wrong vibe.

**Q: What about data loss? What if the user's laptop crashes?**
A: Not diligent's problem in v1. The user is responsible for backup, the same way they're responsible for backup of any other working files. OneDrive sync handles this for Bryce. Future colleagues might use git, Dropbox, or Time Machine. diligent does not implement any backup, sync, or cloud functionality. If the user loses their `.diligence/` directory, they lose the state layer but still have all the source documents and the analytical artifacts; they would re-init and re-register the most important facts. This is consistent with the "self-contained, portable" design.

**Q: What's the install experience like for a colleague who has never seen this before?**
A: `pipx install diligent` (or whatever the final name is). `cd` into their deal folder. `diligent init`. Answer six prompts. Done. Optionally `diligent install --antigravity --global` to get the IDE skills. The colleague should be able to get from "I have a folder of seller documents" to "I have a working diligent setup" in under five minutes. If onboarding takes longer than that, the design is wrong.

**Q: What's the documentation strategy?**
A: A README with the install command and a 10-line quickstart. A USER-GUIDE.md with the full command reference. Per-command help text accessible via `diligent <command> --help`. No video tutorials, no docs site, no Discord. The audience is small and technical; documentation should be terse and grep-able. GSD's documentation style is the model.

**Q: What does the tool look like when it grows up — what's v2?**
A: Don't know yet, and explicitly should not decide until v1 has been used on at least two real deals. Possible v2 features that have been mentioned but are firmly out of scope for v1: git integration with auto-commit on state changes, multi-deal awareness on a single machine, document OCR for automated fact extraction from PDFs, integration with a VDR API, support for additional IDE runtimes beyond Antigravity and Claude Code, a TUI mode for terminal-only users. None of these get built until v1 has been dogfooded for at least three months.

**Q: How do you handle the seller's data being wrong?**
A: TRUTH.md is *validated* facts, not raw seller claims. If the seller's CIM says ARR is $2.4M but Bryce's analysis of the invoice file says ARR is $2.36M, both can be recorded — `seller_claimed_arr` and `validated_arr` are different keys. The `--source` flag distinguishes them. This is exactly how a real diligence engagement handles seller-vs-validated discrepancies, and the system should make it natural.

**Q: How do you prevent the user from "gaming" the system by skipping the discipline?**
A: You don't. The system has no enforcement against a user who chooses to ignore it. The discipline is in the user, and the tool just makes the discipline easier and more consistent. If a user manually edits TRUTH.md to overwrite a value without recording the supersedes, the system will accept the edit. The only thing that protects against this is `diligent doctor`, which flags malformed files. This is consistent with the GSD philosophy: the tool removes friction from doing the right thing, but doesn't lock the user into anything.

**Q: What's the relationship between diligent and git?**
A: Orthogonal. Diligent does not require git. Diligent does not interact with git in v1. If the user wants to put their deal folder under git, that's fine, and the markdown state files will diff cleanly. If the user doesn't want git, that's also fine. v2 might add an optional `diligent commit` that wraps `git commit` for state file changes, but only if v1 dogfooding shows a clear need.

**Q: How does diligent know about a new file the user dropped into the deal folder?**
A: It doesn't. There's no file watcher. The user has to explicitly `diligent ingest <path>`. This is deliberate — automatic detection would create false positives (every Excel temp file would trigger an event) and would require a daemon. The PRD explicitly says "no background processes." If the user drops 20 files, they run 20 ingests (or one ingest with a glob pattern, which is a possible v2 feature).

**Q: What's the smallest shippable artifact for Milestone 1?**
A: `pipx install diligent` works. `diligent init` creates a valid `.diligence/` directory in any folder. `diligent doctor` validates the directory and exits 0. State file readers and writers round-trip cleanly. That's it. No ingest, no truth, no reconcile. The user can hand-author state files and the system can read them. Milestone 1 is the foundation; it has no user-facing value on its own.

---

## 10. Things explicitly out of scope and why

The PRD section 7.5 lists these. Elaboration on the most important ones:

- **Multi-user features.** Diligent is single-user per deal folder. If two analysts work on the same deal, they coordinate through a shared OneDrive folder or a shared git repo, the same way two developers coordinate on a codebase. Adding review queues, sign-offs, or role-based access would force a relational data model, which would force a database, which would force a sync strategy, which would force a hosted backend. The whole thing collapses into "build a SaaS." Not v1.
- **Web UI.** Same reasoning. The moment you have a web UI, you have a server, an auth system, a database, and a deployment pipeline. None of these exist in v1. The user lives in the IDE. The IDE is the UI.
- **Built-in LLM integration.** Diligent does not call OpenAI or Anthropic APIs. The user's IDE does. This keeps diligent zero-credential, zero-cost, and runtime-agnostic. v2 might add an *optional* `diligent ai` subcommand that uses an API key from the environment to do things like auto-suggest fact keys from a document, but this would be opt-in and would not be a core dependency.
- **Document OCR / automated fact extraction.** The user (with their AI agent) is the extraction engine. Diligent does not parse PDFs to find numbers. This is a deliberate design choice: automated extraction would either be too inaccurate to trust (OCR errors, false positives) or would require an LLM call (see above), and would in either case obscure the provenance of facts. Manual extraction with explicit `truth set` calls keeps the audit trail clean.
- **VDR / CRM / accounting system integration.** Out of scope. The user downloads files from the VDR to the local folder; from that point on, diligent operates on the local files. Direct integration would require maintaining API connectors for every VDR vendor, which is a treadmill.
- **Phase-level git branching like GSD does.** GSD creates a branch per phase and merges at completion. This is appropriate for code, where merges are the standard collaboration unit. It is overkill for diligence, where the analyst is the only writer and version trail comes from the supersedes chains in TRUTH.md and SOURCES.md. v1 leaves git entirely to the user.

If GSD's discuss phase pushes for any of these, the answer is: "considered, deliberately deferred to v2 or later."

---

## 11. Things that are open and need to be decided during the build

PRD section 8 lists these. Repeating with more context:

- **Final tool name.** `diligent` is a placeholder. The PyPI package `diligent` is taken (a different Python development tool, unrelated). Real candidates: `searchlight`, `bedrock`, `plumb`, `tether`, `anchor`, `veritas`. Need to verify PyPI availability and ideally also a `.com` or `.dev` domain. This decision should be made before any code is committed because the package name will be embedded in dozens of places.
- **TRUTH.md storage format.** Two options: (a) markdown headings with YAML in fenced code blocks under each, (b) a single YAML file with a separate markdown index. (a) is more human-readable; (b) is easier to parse. Recommendation: start with (a), reconsider during Milestone 1 if parsing turns out to be brittle.
- **Citation tag syntax in deliverables.** Two approaches: manual `--references` flags at registration vs. embedded `{{truth:key}}` tags in the document body. Recommendation: support both, prefer tags when the user is willing to embed them. Test with real Project Arrival artifacts during Milestone 3.
- **Workstream templates: shipped or user-defined.** Recommendation: ship a default set (financial, retention/commercial, technical, legal, HR, integration) with a one-line description of each. Allow customization during `diligent init` ("which workstreams do you want for this deal?"). This gives new users a starting point without forcing a taxonomy.
- **`config.json` vs `config.toml`.** Recommendation: JSON for compatibility with the broadest range of editors and Python tooling. TOML is prettier but introduces a parsing dependency on top of stdlib JSON.
- **Git integration.** Recommendation: none in v1. Revisit after dogfooding.
- **Where SKILL.md files get installed for Antigravity.** Per the GSD repo, Antigravity local installs go to `./.agent/`. Need to verify this against the current Antigravity docs before shipping the install command.

---

## 12. Operational items the user is handling outside the build itself

These are things Bryce needs to do that are not part of the diligent build but are prerequisites or parallel tracks. A fresh agent should know about these so it doesn't redundantly suggest them.

- **Pick a name.** See section 11.
- **BSL legal review.** Bryce needs to spend 30 minutes with a lawyer to confirm the BSL terms in PRD section 6.1 actually do what he wants. Cost: $200–500. Not optional if monetization is on the table.
- **Decide on GitHub org vs personal account.** Recommendation: personal for v1, migrate to an org if the project ever takes off and needs to be transferable.
- **Identify a first colleague to show v1 to.** Not a current task, but worth thinking about now so it creates a deadline. Probably someone in his Michigan ETA cohort.
- **Decide on Project Arrival as the test deal.** Recommendation: yes, in shadow mode, for Milestones 1–2. Make it primary for Milestone 3+.
- **Set up `pip index versions <name>` and check name availability before Milestone 1 starts.**

---

## 13. Things to NOT suggest

Tactical guidance for the agent, based on past instances of Bryce pushing back on suggestions during related conversations.

- Do not suggest adding a web dashboard "for visualization." The user explicitly does not want one.
- Do not suggest building a TUI for the same reason. The CLI is the interface.
- Do not suggest LLM-based document parsing as a feature of diligent itself. The LLM lives in the IDE, not in diligent.
- Do not suggest a database backend (SQLite, DuckDB, PostgreSQL) for state. Markdown is the backend.
- Do not suggest a syncing or collaboration feature.
- Do not suggest adding tests for the analytical correctness of the user's work. Diligent is about state, not analysis.
- Do not suggest an MIT, Apache, or AGPL license. The user has explicitly chosen BSL.
- Do not suggest using emojis in CLI output, error messages, or generated documents. The user does not use emojis and finds them distracting in professional output.
- Do not suggest ChatGPT, Cursor, or Copilot as integration targets in v1. Antigravity and Claude Code only. Other runtimes are v2.
- Do not suggest adding configuration options for things that have one obviously correct answer. Every config knob is a maintenance burden.
- Do not suggest the user "consider" a feature as a polite way of pitching it. If you have a strong opinion, state it directly with reasoning. If you don't, don't bring it up.
- Do not offer multiple alternatives when a direction is clear. Give one recommendation and the reasoning.
- Do not use AI template phrasing in any generated user-facing text. No "Great question!", no "I'd be happy to help", no "Let me walk you through". Direct statements only.
- Do not use em dashes in any generated text.

---

## End of brief

If a question comes up that this document does not answer, *say so explicitly* and ask Bryce. Do not invent an answer. Do not extrapolate beyond what's written here. The user values calibration over confident-but-wrong, and the entire point of building diligent is to make it harder to fabricate. The brief itself should embody that principle.
