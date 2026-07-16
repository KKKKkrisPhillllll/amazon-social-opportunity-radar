from __future__ import annotations

from radar.models import Opportunity, ReviewRecord, SocialRecord

PAIN_TERMS = [
    "not useful",
    "awkward",
    "regret",
    "unused",
    "takes too much space",
    "hard to clean",
    "not durable",
    "broke",
    "leak",
    "不好用",
    "踩雷",
    "后悔买",
    "闲置",
    "太占地方",
    "难清洗",
    "不耐用",
    "漏水",
]


def _clamp(value: int, maximum: int) -> int:
    return max(0, min(value, maximum))


def _social_heat(records: list[SocialRecord]) -> int:
    raw = 0
    for record in records:
        raw += int(record.engagement.get("likes", 0))
        raw += int(record.engagement.get("favorites", 0)) * 2
        raw += int(record.engagement.get("comments", 0)) * 3
    return _clamp(raw // 20, 25)


def _pain_intensity(
    social_records: list[SocialRecord],
    review_records: list[ReviewRecord],
) -> int:
    text = " ".join(
        [
            record.title + " " + record.text + " " + " ".join(record.comments)
            for record in social_records
        ]
        + [record.title + " " + record.review_text for record in review_records]
    ).lower()
    matches = sum(1 for term in PAIN_TERMS if term.lower() in text)
    return _clamp(matches * 6, 25)


def _amazon_review_validation(review_records: list[ReviewRecord]) -> int:
    if not review_records:
        return 0
    low_rating_count = sum(
        1 for record in review_records if record.rating and record.rating <= 3
    )
    return _clamp(8 + low_rating_count * 4, 20)


def _product_fit(category: str, social_records: list[SocialRecord]) -> int:
    category_terms = {
        "kitchen_appliances": ["appliance", "air fryer", "cooker", "厨房电器", "空气炸锅"],
        "kitchen_storage": ["storage", "organizer", "rack", "厨房收纳", "收纳架"],
        "home_storage": ["home", "storage", "organizer", "家居收纳", "小户型收纳"],
    }
    text = " ".join(
        record.title + " " + record.text for record in social_records
    ).lower()
    matches = sum(1 for term in category_terms.get(category, []) if term in text)
    return _clamp(6 + matches * 3, 15)


def _business_feasibility(
    keywords: list[str],
    review_records: list[ReviewRecord],
) -> int:
    score = 5
    if keywords:
        score += 5
    if review_records:
        score += 5
    return _clamp(score, 15)


def score_opportunity(
    social_records: list[SocialRecord],
    review_records: list[ReviewRecord],
    category: str,
    keywords: list[str],
) -> Opportunity:
    platforms = sorted({record.platform for record in social_records})
    asins = sorted({record.asin for record in review_records if record.asin})
    title = "亚马逊产品机会"
    pain = "社媒讨论和亚马逊评论中出现了潜在用户痛点。"
    if social_records:
        title = social_records[0].title or social_records[0].text[:60] or title
        evidence = social_records[0].text or " ".join(social_records[0].comments)
        if evidence:
            pain = f"社媒证据显示：{evidence[:120]}"
    if review_records:
        pain = review_records[0].title or pain
    breakdown = {
        "social_heat": _social_heat(social_records),
        "pain_intensity": _pain_intensity(social_records, review_records),
        "amazon_review_validation": _amazon_review_validation(review_records),
        "product_development_fit": _product_fit(category, social_records),
        "amazon_business_feasibility": _business_feasibility(keywords, review_records),
    }
    return Opportunity(
        title=title,
        category=category,
        source_platforms=platforms,
        evidence_summary=(
            f"已分析 {len(social_records)} 条社媒记录和 "
            f"{len(review_records)} 条亚马逊评论。"
        ),
        customer_pain_point=pain,
        product_idea=(
            "围绕重复出现的用户痛点，定义有明确差异化的亚马逊产品方案。"
        ),
        amazon_validation_keywords=keywords,
        suggested_asins=asins,
        differentiation_angle=(
            "在采购和上架前，优先解决重复频率最高的投诉。"
        ),
        risk_notes=(
            "上线前仍需验证关键词需求、评论门槛、利润、合规和供应商可行性。"
        ),
        next_action="对该机会执行亚马逊关键词与竞品验证。",
        score_breakdown=breakdown,
    )
