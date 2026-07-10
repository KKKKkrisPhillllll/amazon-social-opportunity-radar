from __future__ import annotations

from radar.models import Opportunity, SourceHealth


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
