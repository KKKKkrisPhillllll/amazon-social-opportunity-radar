from __future__ import annotations

from collections.abc import Mapping, Sequence

from radar.evidence import EvidenceItem
from radar.models import JOURNEY_STAGE_NAMES, JourneyStage, Opportunity
from radar.opportunity_gate import OpportunityGate
from radar.persona_builder import (
    _confidence,
    _relevant_evidence,
    _themes,
    _validate_gate,
)

JOURNEY_STAGES = JOURNEY_STAGE_NAMES
PENDING_STAGE = "当前未发现直接公开证据，待后续采集验证"

_STAGE_KEYWORDS = {
    "发现需求": ("空间", "痛点", "占用", "不够", "问题"),
    "搜索方案": ("搜索", "方案", "推荐", "怎么", "替代"),
    "对比决策": ("价格", "比较", "对比", "适配", "选择"),
    "购买": ("购买", "下单", "链接", "优惠", "价格"),
    "使用": ("使用", "清洁", "耐用", "安装", "步骤", "难"),
    "反馈": ("反馈", "评价", "满意", "失望", "建议", "复购"),
}


def build_journey(
    opportunity: Opportunity,
    evidence: Sequence[EvidenceItem],
    voc: Mapping[str, tuple[str, ...]],
    gate: OpportunityGate,
) -> tuple[JourneyStage, ...]:
    relevant = _relevant_evidence(opportunity, evidence)
    confidence = _confidence(relevant)
    _validate_gate(confidence, gate)
    themes = _themes(relevant, voc)
    stage_results: list[JourneyStage] = []

    for stage_name in JOURNEY_STAGES:
        keywords = _STAGE_KEYWORDS[stage_name]
        matched = tuple(
            item
            for item in relevant
            if any(
                keyword in f"{item.summary} {' '.join(voc.get(item.evidence_id, ()))}"
                for keyword in keywords
            )
        )
        signals = tuple(
            theme
            for theme in themes
            if any(keyword in theme for keyword in keywords)
        )
        urls = tuple(item.url for item in matched)
        if matched:
            stage_confidence = confidence
            observed = signals or tuple(item.summary for item in matched)
            action = f"围绕{stage_name}阶段验证用户行为信号"
            implication = f"针对{stage_name}阶段优化产品信息与体验"
        else:
            stage_confidence = "低"
            observed = ()
            action = PENDING_STAGE
            implication = PENDING_STAGE
        stage_results.append(
            JourneyStage(
                name=stage_name,
                observed_signals=observed,
                user_need_or_action=action,
                product_implication=implication,
                evidence_urls=urls,
                confidence=stage_confidence,
            )
        )
    return tuple(stage_results)
