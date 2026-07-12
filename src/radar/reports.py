from __future__ import annotations

from radar.models import Opportunity, ReviewRecord, SourceHealth


def _score_lines(opportunity: Opportunity) -> list[str]:
    lines = [f"- Score: {opportunity.total_score}"]
    for name, value in opportunity.score_breakdown.items():
        lines.append(f"  - {name}: {value}")
    return lines


def build_daily_markdown(
    opportunities: list[Opportunity],
    source_health: dict[str, SourceHealth],
    report_date: str,
    focus: str,
) -> str:
    lines: list[str] = [
        "# Amazon Social Opportunity Radar",
        "",
        f"Date: {report_date}",
        f"Focus: {focus}",
        "",
        "## 1. Top Opportunities",
        "",
    ]
    if not opportunities:
        lines.append("No qualified opportunities found today.")
    for index, opportunity in enumerate(
        sorted(opportunities, key=lambda item: item.total_score, reverse=True),
        start=1,
    ):
        lines.extend(
            [
                f"### Opportunity {index}: {opportunity.title}",
                *_score_lines(opportunity),
                f"- Category: {opportunity.category}",
                f"- Source: {', '.join(opportunity.source_platforms) or 'unknown'}",
                f"- Customer pain: {opportunity.customer_pain_point}",
                f"- Product idea: {opportunity.product_idea}",
                f"- Amazon validation keywords: {', '.join(opportunity.amazon_validation_keywords) or 'not available'}",
                f"- Suggested ASIN review check: {', '.join(opportunity.suggested_asins) or 'not available'}",
                f"- Differentiation angle: {opportunity.differentiation_angle}",
                f"- Risk: {opportunity.risk_notes}",
                f"- Next action: {opportunity.next_action}",
                "",
            ]
        )
    lines.extend(
        [
            "## 2. Hot Trends",
            "See Top Opportunities sorted by total score.",
            "",
            "## 3. High-Frequency Pain Points",
            "See each opportunity's customer pain field.",
            "",
            "## 4. Product Improvement Ideas",
            "See each opportunity's differentiation angle.",
            "",
            "## 5. New Product Inspiration",
            "See each opportunity's product idea.",
            "",
            "## 6. Items Needing Amazon Review Validation",
            "Items without suggested ASINs need competitor ASIN discovery before review validation.",
            "",
            "## 7. Data Source Health",
        ]
    )
    for name, health in sorted(source_health.items()):
        lines.append(f"- {name}: {health.value}")
    return "\n".join(lines).strip() + "\n"


def build_amazon_review_markdown(
    asin: str,
    reviews: list[ReviewRecord],
    health: SourceHealth,
    report_date: str,
) -> str:
    low_rating_reviews = [review for review in reviews if review.rating <= 3]
    lines = [
        "# Amazon 评论首跑报告",
        "",
        f"- ASIN：{asin}",
        f"- 运行日期：{report_date}",
        f"- 采集状态：{health.value}",
        f"- 实际评论数量：{len(reviews)}",
        f"- 低评分评论数量：{len(low_rating_reviews)}",
    ]
    if reviews:
        lines.append(f"- 实际使用脚本：{reviews[0].source_script}")
    lines.extend(["", "## 低评分评论证据", ""])
    if not low_rating_reviews:
        lines.append("未采集到评分低于或等于 3 星的评论。")
    for index, review in enumerate(low_rating_reviews, start=1):
        lines.extend(
            [
                f"### 评论 {index}",
                f"- 评分：{review.rating}",
                f"- 标题：{review.title or '未提供'}",
                f"- 日期：{review.review_date or '未提供'}",
                f"- 内容：{review.review_text}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
