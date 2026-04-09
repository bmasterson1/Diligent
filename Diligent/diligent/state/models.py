"""Dataclass definitions for all 8 state file types.

All models use stdlib types only. No external dependencies.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SupersededValue:
    """A prior value that was replaced in the supersedes chain."""

    value: str
    source: str
    date: str  # ISO 8601


@dataclass
class FactEntry:
    """A single validated fact in TRUTH.md."""

    key: str
    value: str  # Always stored as quoted string in YAML
    source: str  # Source ID, required
    date: str  # ISO 8601, auto-recorded
    workstream: str  # Must match WORKSTREAMS.md entry
    supersedes: list[SupersededValue] = field(default_factory=list)
    computed_by: Optional[str] = None
    notes: Optional[str] = None
    flagged: Optional[dict] = None  # {reason: str, date: str}
    anchor: bool = False


@dataclass
class TruthFile:
    """TRUTH.md state file: keyed dict of validated facts."""

    facts: dict[str, FactEntry] = field(default_factory=dict)


@dataclass
class SourceEntry:
    """A single source document entry in SOURCES.md."""

    id: str
    path: str
    date_received: str  # ISO 8601
    parties: list[str] = field(default_factory=list)
    workstream_tags: list[str] = field(default_factory=list)
    supersedes: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SourcesFile:
    """SOURCES.md state file: list of registered source documents."""

    sources: list[SourceEntry] = field(default_factory=list)


@dataclass
class WorkstreamEntry:
    """A single workstream entry."""

    name: str
    status: str
    description: str = ""
    created: str = ""  # ISO 8601


@dataclass
class WorkstreamsFile:
    """WORKSTREAMS.md state file: list of workstreams."""

    workstreams: list[WorkstreamEntry] = field(default_factory=list)


@dataclass
class DealFile:
    """DEAL.md state file: deal metadata frontmatter."""

    deal_code: str
    target_legal_name: str
    target_common_name: str
    deal_stage: str
    loi_date: str
    principal: str
    principal_role: str
    seller: str
    broker: str
    thesis: str
    workstreams: list[str] = field(default_factory=list)


@dataclass
class StateFile:
    """STATE.md state file: timestamps for deal state."""

    created: str  # ISO 8601
    last_modified: str  # ISO 8601


@dataclass
class ConfigFile:
    """config.json: deal configuration and schema version."""

    schema_version: int
    deal_code: str
    created: str  # ISO 8601
    anchor_tolerance_pct: float
    recent_window_days: int
    workstreams: list[str] = field(default_factory=list)


@dataclass
class QuestionEntry:
    """A single question entry in QUESTIONS.md."""

    id: str
    question: str
    workstream: str
    owner: str  # self, principal, seller, broker, counsel
    status: str  # open, answered, deferred
    date_raised: str  # ISO 8601
    context: Optional[dict] = None  # Gate rejection context: key, old_value, new_value, etc.
    answer: Optional[str] = None
    answer_source: Optional[str] = None
    date_answered: Optional[str] = None  # ISO 8601


@dataclass
class QuestionsFile:
    """QUESTIONS.md state file: list of open/answered questions."""

    questions: list[QuestionEntry] = field(default_factory=list)


@dataclass
class ArtifactEntry:
    """A single artifact entry in ARTIFACTS.md."""

    path: str  # Relative posix path from deal root (H2 heading)
    workstream: str
    registered: str  # ISO 8601 date
    last_refreshed: str  # ISO 8601 date
    references: list[str] = field(default_factory=list)  # Truth keys
    scanner_findings: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class ArtifactsFile:
    """ARTIFACTS.md state file: list of registered artifacts."""

    artifacts: list[ArtifactEntry] = field(default_factory=list)
