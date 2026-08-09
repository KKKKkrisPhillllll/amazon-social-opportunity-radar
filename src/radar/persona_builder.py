from __future__ import annotations

from collections.abc import Mapping, Sequence

from radar.evidence import EvidenceItem, _normalize_public_url
from radar.models import Opportunity, PersonaEvidence, UserPersona
from radar.opportunity_gate import OpportunityGate


PENDING_VALIDATION = "证据不足，待验证"


def _relevant_evidence(
    opportunity: Opportunity, evidence: Sequence[EvidenceItem]
) -> tuple[EvidenceItem, ...]:
    selected: list[EvidenceItem] = []
    seen_urls: set[str] = set()
    for item in evidence:
        if item.category != opportunity.category:
            continue
        normalized_url = _normalize_public_url(item.url)
        if normalized_url is None or normalized_url in seen_urls:
            continue
        seen_urls.add(normalized_url)
        selected.append(
            EvidenceItem(
                evidence_id=item.evidence_id,
                platform=item.platform,
                url=normalized_url,
                category=item.category,
                summary=item.summary,
                comment_count=item.comment_count,
                asin=item.asin,
            )
        )
        if len(selected) == 5:
            break
    return tuple(selected)


def _confidence(evidence: Sequence[EvidenceItem]) -> str:
    platforms = {item.platform for item in evidence}
    if len(evidence) >= 4 and len(platforms) >= 2:
        return "高"
    if len(evidence) >= 2:
        return "中"
    return "低"


def _themes(
    evidence: Sequence[EvidenceItem], voc: Mapping[str, tuple[str, ...]]
) -> tuple[str, ...]:
    return tuple(sorted({theme for item in evidence for theme in voc.get(item.evidence_id, ())}))


def _validate_gate(confidence: str, gate: OpportunityGate) -> None:
    if not gate.eligible and confidence != "低":
        raise ValueError("builders require an eligible or low-confidence gate result")


def build_persona(
    opportunity: Opportunity,
    evidence: Sequence[EvidenceItem],
    voc: Mapping[str, tuple[str, ...]],
    gate: OpportunityGate,
) -> UserPersona:
    relevant = _relevant_evidence(opportunity, evidence)
    confidence = _confidence(relevant)
    _validate_gate(confidence, gate)
    themes = _themes(relevant, voc)
    searchable = " ".join(themes) + " " + " ".join(item.summary for item in relevant)

    if "空间" in searchable or "收纳" in searchable:
        segment = "小空间效率型"
    elif "价格" in searchable or "贵" in searchable:
        segment = "价格敏感型"
    elif "频繁" in searchable or "每天" in searchable:
        segment = "高频重度使用型"
    else:
        segment = "一般任务型"

    pain_points = themes or ("当前没有足够主题证据，待验证",)
    if confidence == "低" and PENDING_VALIDATION not in pain_points:
        pain_points = pain_points + (PENDING_VALIDATION,)

    return UserPersona(
        opportunity_title=opportunity.title,
        category=opportunity.category,
        opportunity_score=opportunity.total_score,
        behavioral_segment=segment,
        scenario=f"围绕{opportunity.category}的真实使用场景",
        core_goal="在当前场景中更稳定、更省步骤地完成任务",
        pain_points=tuple(pain_points),
        purchase_triggers=("重复出现的使用摩擦",),
        concerns=("价格、耐用性、清洁维护和适配性",),
        evidence=tuple(PersonaEvidence(item.platform, item.url, item.summary) for item in relevant),
        confidence=confidence,
    )
