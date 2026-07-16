from __future__ import annotations

from radar.models import Opportunity, SourceHealth


_SCORE_NAMES = {
    "social_heat": "社媒热度",
    "pain_intensity": "痛点强度",
    "amazon_review_validation": "亚马逊评论验证",
    "product_development_fit": "产品开发匹配度",
    "amazon_business_feasibility": "亚马逊商业可行性",
}
_HEALTH_NAMES = {
    SourceHealth.OK: "正常",
    SourceHealth.PARTIAL: "部分可用",
    SourceHealth.DEGRADED: "降级",
    SourceHealth.FAILED: "失败",
    SourceHealth.NOT_CONFIGURED: "未配置",
}


def _score_lines(opportunity: Opportunity) -> list[str]:
    lines = [f"- 总分：{opportunity.total_score}"]
    for name, value in opportunity.score_breakdown.items():
        lines.append(f"  - {_SCORE_NAMES.get(name, name)}：{value}")
    return lines


def build_daily_markdown(
    opportunities: list[Opportunity],
    source_health: dict[str, SourceHealth],
    report_date: str,
    focus: str,
) -> str:
    lines: list[str] = [
        "# 亚马逊社媒产品机会雷达",
        "",
        f"日期：{report_date}",
        f"重点类目：{focus}",
        "",
        "## 1. 今日优先机会",
        "",
    ]
    if not opportunities:
        lines.append("今日未发现达到输出条件的产品机会。")
    for index, opportunity in enumerate(
        sorted(opportunities, key=lambda item: item.total_score, reverse=True),
        start=1,
    ):
        lines.extend(
            [
                f"### 机会 {index}：{opportunity.title}",
                *_score_lines(opportunity),
                f"- 类目：{opportunity.category}",
                f"- 数据来源：{', '.join(opportunity.source_platforms) or '未知'}",
                f"- 用户痛点：{opportunity.customer_pain_point}",
                f"- 产品建议：{opportunity.product_idea}",
                f"- 亚马逊验证关键词：{', '.join(opportunity.amazon_validation_keywords) or '暂无'}",
                f"- 建议复核 ASIN：{', '.join(opportunity.suggested_asins) or '暂无'}",
                f"- 差异化方向：{opportunity.differentiation_angle}",
                f"- 风险：{opportunity.risk_notes}",
                f"- 下一步：{opportunity.next_action}",
                "",
            ]
        )
    lines.extend(
        [
            "## 2. 社媒热点",
            "参见按总分排序的今日优先机会。",
            "",
            "## 3. 高频用户痛点",
            "参见各机会的用户痛点字段。",
            "",
            "## 4. 产品改款建议",
            "参见各机会的差异化方向。",
            "",
            "## 5. 新品灵感",
            "参见各机会的产品建议。",
            "",
            "## 6. 待做亚马逊评论验证",
            "没有建议 ASIN 的机会，需要先发现竞品 ASIN，再进行评论验证。",
            "",
            "## 7. 数据源健康状态",
        ]
    )
    for name, health in sorted(source_health.items()):
        lines.append(f"- {name}: {_HEALTH_NAMES[health]}")
    return "\n".join(lines).strip() + "\n"
