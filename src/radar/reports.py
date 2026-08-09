from __future__ import annotations

from collections.abc import Mapping, Sequence
from itertools import pairwise

from radar.models import (
    Opportunity,
    PersonaJourneyResult,
    SocialRecord,
    SourceHealth,
    SourceRun,
)

SCORE_LABELS = {
    "social_heat": "社媒热度",
    "pain_intensity": "痛点强度",
    "amazon_review_validation": "亚马逊评论验证",
    "product_development_fit": "产品开发匹配度",
    "amazon_business_feasibility": "亚马逊商业可行性",
}


def _score_lines(opportunity: Opportunity) -> list[str]:
    lines = [f"- 总分：{opportunity.total_score}"]
    for name, value in opportunity.score_breakdown.items():
        lines.append(f"- {SCORE_LABELS.get(name, name)}：{value}")
    return lines


def _evidence_lines(records: Sequence[SocialRecord]) -> list[str]:
    urls = [record.url for record in records if record.url][:3]
    if not urls:
        return ["- 证据链接：本轮无可公开引用的链接。"]
    return [f"- 证据链接：{url}" for url in urls]


def _source_run_line(source_run: SourceRun) -> str:
    diagnostic = source_run.diagnostic or "无"
    return (
        f"- {source_run.source_name}：{source_run.health.value}；"
        f"采集 {source_run.fetched_count} 条，去重 {source_run.duplicate_count} 条；"
        f"诊断：`{diagnostic}`"
    )


def _mermaid_label(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ").replace("\r", " ")


def _persona_journey_lines(result: PersonaJourneyResult, index: int) -> list[str]:
    persona = result.persona
    lines = [
        f"### 画像 {index}：{persona.opportunity_title}",
        f"- 行为型画像：{persona.behavioral_segment}",
        f"- 使用场景：{persona.scenario}",
        f"- 核心目标：{persona.core_goal}",
        f"- 主要痛点：{'; '.join(persona.pain_points)}",
        f"- 购买触发：{'; '.join(persona.purchase_triggers)}",
        f"- 主要顾虑：{'; '.join(persona.concerns)}",
        f"- 置信度：{persona.confidence}",
        "- 公开证据：",
    ]
    lines.extend(
        f"  - 平台：{evidence.platform}；URL：{evidence.url}；摘要：{evidence.summary}"
        for evidence in persona.evidence
    )
    lines.extend(["", "```mermaid", "flowchart LR"])
    node_ids = [f"stage_{index}_{stage_index}" for stage_index, _ in enumerate(result.stages)]
    for node_id, stage in zip(node_ids, result.stages):
        label = _mermaid_label(stage.name)
        lines.append(f'    {node_id}["{label}"]')
    lines.extend(
        f"    {left} --> {right}"
        for left, right in pairwise(node_ids)
    )
    lines.extend(["```", ""])
    for stage in result.stages:
        evidence = ", ".join(stage.evidence_urls) or "待后续采集验证"
        lines.extend(
            [
                (
                    f"- {stage.name}：{stage.user_need_or_action}；产品含义：{stage.product_implication}；"
                    f"置信度：{stage.confidence}；Evidence URL：{evidence}"
                ),
            ]
        )
    lines.append("")
    return lines


def build_daily_markdown(
    opportunities: Sequence[Opportunity],
    source_runs: Sequence[SourceRun],
    report_date: str,
    focus: str,
    run_mode: str,
    evidence_by_category: Mapping[str, Sequence[SocialRecord]],
    persona_journeys: Sequence[PersonaJourneyResult] = (),
) -> str:
    lines: list[str] = [
        "# 亚马逊社媒产品机会雷达",
        "",
        f"- 日期：{report_date}",
        f"- 运行模式：{run_mode}",
        f"- 关注范围：{focus}",
        "",
        "## 1. 产品机会排序",
        "",
    ]
    if not opportunities:
        lines.append("本轮没有形成可评分的产品机会；请先检查数据源健康状态和关键词覆盖。")
    for index, opportunity in enumerate(
        sorted(opportunities, key=lambda item: item.total_score, reverse=True), start=1
    ):
        lines.extend(
            [
                f"### 机会 {index}：{opportunity.title}",
                *_score_lines(opportunity),
                f"- 类目：{opportunity.category}",
                f"- 来源：{', '.join(opportunity.source_platforms) or '未知'}",
                f"- 证据摘要：{opportunity.evidence_summary}",
                *_evidence_lines(evidence_by_category.get(opportunity.category, ())),
                f"- 用户痛点：{opportunity.customer_pain_point}",
                f"- 产品建议：{opportunity.product_idea}",
                f"- 亚马逊验证关键词：{', '.join(opportunity.amazon_validation_keywords) or '暂无'}",
                f"- 建议核验 ASIN：{', '.join(opportunity.suggested_asins) or '暂无'}",
                f"- 差异化方向：{opportunity.differentiation_angle}",
                f"- 风险提示：{opportunity.risk_notes}",
                f"- 下一步：{opportunity.next_action}",
                "",
            ]
        )
    qualified_persona_journeys = [
        result
        for result in persona_journeys
        if result.gate_eligible and result.persona.opportunity_score >= 60
    ]
    if qualified_persona_journeys:
        lines.extend(["## 用户画像与用户旅程图", ""])
        for index, result in enumerate(qualified_persona_journeys, start=1):
            lines.extend(_persona_journey_lines(result, index))
    lines.extend(
        [
            "## 2. 热点趋势",
            "热点按上述机会总分排序；仅作为选品研究线索，不构成需求结论。",
            "",
            "## 3. 高频痛点",
            "请优先核验机会中的用户痛点，避免把单条内容当作普遍需求。",
            "",
            "## 4. 改款建议",
            "请结合差异化方向、合规、成本和供应链能力进行立项判断。",
            "",
            "## 5. 新品灵感",
            "请先完成亚马逊关键词、竞品和评论验证，再进入打样或采购。",
            "",
            "## 6. 数据完整性提示",
        ]
    )
    if run_mode == "样例数据":
        lines.append("样例数据仅用于验证链路，不可作为真实用户需求、市场热度或产品立项证据。")
    elif any(source_run.health is not SourceHealth.OK for source_run in source_runs):
        lines.append("本轮存在未配置、降级、部分返回或失败的数据源；报告只反映已成功采集的证据。")
    else:
        lines.append("所有已启用数据源本轮返回正常；仍需人工核验内容相关性与商业可行性。")
    lines.extend(["", "## 7. 数据源健康状态"])
    if not source_runs:
        lines.append("- 本轮没有执行数据源。")
    else:
        lines.extend(_source_run_line(source_run) for source_run in source_runs)
    return "\n".join(lines).strip() + "\n"
