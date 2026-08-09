from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


JOURNEY_STAGE_NAMES = ("发现需求", "搜索方案", "对比决策", "购买", "使用", "反馈")


class SourceHealth(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True)
class SocialRecord:
    platform: str
    keyword: str
    url: str
    title: str
    text: str
    author: str = ""
    published_at: str = ""
    tags: list[str] = field(default_factory=list)
    engagement: dict[str, int | float] = field(default_factory=dict)
    comments: list[str] = field(default_factory=list)
    health: SourceHealth = SourceHealth.OK


@dataclass(frozen=True)
class SourceRun:
    """A single source invocation with safe operational diagnostics."""

    source_name: str
    platform: str
    records: tuple[SocialRecord, ...]
    health: SourceHealth
    fetched_count: int
    duplicate_count: int = 0
    diagnostic: str = ""

    def __post_init__(self) -> None:
        if self.fetched_count < 0:
            raise ValueError("fetched_count must be non-negative")
        if self.duplicate_count < 0 or self.duplicate_count > self.fetched_count:
            raise ValueError("duplicate_count must be between zero and fetched_count")


@dataclass(frozen=True)
class ReviewRecord:
    asin: str
    rating: float
    title: str
    review_text: str
    review_date: str = ""
    verified: bool | None = None
    helpful_count: int | None = None
    source_script: str = ""
    raw_source_path: str = ""
    health: SourceHealth = SourceHealth.OK


@dataclass(frozen=True)
class Opportunity:
    """A scored opportunity; downstream gates must not mutate its score."""

    title: str
    category: str
    source_platforms: list[str]
    evidence_summary: str
    customer_pain_point: str
    product_idea: str
    amazon_validation_keywords: list[str]
    suggested_asins: list[str]
    differentiation_angle: str
    risk_notes: str
    next_action: str
    score_breakdown: dict[str, int]

    @property
    def total_score(self) -> int:
        return sum(self.score_breakdown.values())


@dataclass(frozen=True)
class PersonaEvidence:
    platform: str
    url: str
    summary: str


@dataclass(frozen=True)
class UserPersona:
    opportunity_title: str
    category: str
    opportunity_score: int
    behavioral_segment: str
    scenario: str
    core_goal: str
    pain_points: tuple[str, ...]
    purchase_triggers: tuple[str, ...]
    concerns: tuple[str, ...]
    evidence: tuple[PersonaEvidence, ...]
    confidence: str


@dataclass(frozen=True)
class JourneyStage:
    name: str
    observed_signals: tuple[str, ...]
    user_need_or_action: str
    product_implication: str
    evidence_urls: tuple[str, ...]
    confidence: str

    def __post_init__(self) -> None:
        if self.name not in JOURNEY_STAGE_NAMES:
            raise ValueError(f"unknown journey stage: {self.name}")


@dataclass(frozen=True)
class PersonaJourneyResult:
    persona: UserPersona
    stages: tuple[JourneyStage, ...]
