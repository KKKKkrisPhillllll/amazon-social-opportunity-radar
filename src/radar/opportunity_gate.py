from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from radar.evidence import EvidenceItem
from radar.models import Opportunity


@dataclass(frozen=True)
class OpportunityGate:
    eligible: bool
    independent_source_count: int
    evidence_count: int
    has_counter_evidence: bool
    strengths: tuple[str, ...]
    gaps: tuple[str, ...]
    next_validation: str


def evaluate_opportunity_gate(
    opportunity: Opportunity,
    evidence: Sequence[EvidenceItem],
    voc: Mapping[str, tuple[str, ...]],
    signals: Mapping[str, tuple[str, ...]],
    min_evidence_count: int = 2,
) -> OpportunityGate:
    relevant_by_id: dict[str, EvidenceItem] = {}
    for item in evidence:
        if item.category == opportunity.category:
            relevant_by_id.setdefault(item.evidence_id, item)
    relevant = tuple(relevant_by_id.values())
    relevant_ids = {item.evidence_id for item in relevant}
    platforms = {item.platform for item in relevant}

    gaps: list[str] = []
    strengths: list[str] = []
    if opportunity.total_score < 60:
        gaps.append("机会总分低于 60 分")
    if len(relevant) < min_evidence_count:
        gaps.append(f"公开证据少于 {min_evidence_count} 条")
    if len(platforms) < 2:
        gaps.append("至少 2 个独立来源")

    if any(voc.get(evidence_id) for evidence_id in relevant_ids):
        strengths.append("存在可归类的 VOC 信号")
    if relevant_ids.intersection(signals.get("workarounds", ())):
        strengths.append("发现用户替代方案或自救行为")

    has_counter_evidence = bool(
        relevant_ids.intersection(signals.get("counter_evidence", ()))
    )
    if has_counter_evidence:
        gaps.append("存在反向证据，需要人工核验适用边界")

    score_ok = opportunity.total_score >= 60
    evidence_ok = len(relevant) >= min_evidence_count
    source_ok = len(platforms) >= 2
    return OpportunityGate(
        eligible=score_ok and evidence_ok and source_ok,
        independent_source_count=len(platforms),
        evidence_count=len(relevant),
        has_counter_evidence=has_counter_evidence,
        strengths=tuple(strengths),
        gaps=tuple(gaps),
        next_validation="补充独立来源、竞品评论和真实任务测试后再进入产品定义。",
    )
