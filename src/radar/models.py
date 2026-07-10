from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


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
