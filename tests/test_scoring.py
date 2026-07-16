from radar.models import ReviewRecord, SocialRecord
from radar.scoring import score_opportunity


def test_score_opportunity_rewards_heat_pain_reviews_and_fit():
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="kitchen storage",
            url="https://example.com/a",
            title="Kitchen storage organizer",
            text="Small kitchens take too much space. This solves messy spice storage.",
            engagement={"likes": 300, "favorites": 120, "comments": 30},
            comments=["Hard to clean?", "My spices are messy too"],
        )
    ]
    review_records = [
        ReviewRecord(
            asin="B012345678",
            rating=2,
            title="Hard to clean",
            review_text="Useful but hard to clean and takes too much space.",
        )
    ]

    opportunity = score_opportunity(
        social_records=social_records,
        review_records=review_records,
        category="kitchen_storage",
        keywords=["kitchen organizer", "spice rack organizer"],
    )

    assert opportunity.category == "kitchen_storage"
    assert opportunity.total_score >= 60
    assert opportunity.score_breakdown["social_heat"] > 0
    assert opportunity.score_breakdown["pain_intensity"] > 0
    assert opportunity.score_breakdown["amazon_review_validation"] > 0
    assert "kitchen organizer" in opportunity.amazon_validation_keywords
    assert opportunity.suggested_asins == ["B012345678"]


def test_score_opportunity_recognizes_chinese_pain_terms():
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="厨房收纳",
            url="https://example.com/a",
            title="厨房收纳真实体验",
            text="这个产品太占地方，而且难清洗，用几次就闲置了。",
        )
    ]

    opportunity = score_opportunity(
        social_records=social_records,
        review_records=[],
        category="kitchen_storage",
        keywords=["厨房收纳"],
    )

    assert opportunity.score_breakdown["pain_intensity"] >= 18
    assert "社媒" in opportunity.customer_pain_point
    assert "亚马逊关键词" in opportunity.next_action
