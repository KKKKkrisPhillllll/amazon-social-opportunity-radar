from radar.evidence import EvidenceItem
from radar.journey_builder import build_journey
from radar.models import ReviewRecord, SocialRecord
from radar.opportunity_gate import evaluate_opportunity_gate
from radar.persona_builder import build_persona
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


def test_score_is_unchanged_after_persona_journey_research():
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="kitchen storage",
            url="https://example.com/a",
            title="Kitchen storage organizer",
            text="This takes too much space and is hard to clean.",
            engagement={"likes": 300, "favorites": 120, "comments": 30},
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
        keywords=["kitchen organizer"],
    )
    score_before_research = (opportunity.score_breakdown.copy(), opportunity.total_score)
    evidence = [
        EvidenceItem(
            "E-0001", "reddit", "https://reddit.example/1", "kitchen_storage", "难清洗", 0
        ),
        EvidenceItem(
            "E-0002", "youtube", "https://youtube.example/2", "kitchen_storage", "占用空间", 0
        ),
    ]
    gate = evaluate_opportunity_gate(
        opportunity,
        evidence,
        {"E-0001": ("D03_清洁维护",)},
        {"workarounds": (), "counter_evidence": ()},
    )

    build_persona(opportunity, evidence, {"E-0001": ("D03_清洁维护",)}, gate)
    build_journey(opportunity, evidence, {"E-0001": ("D03_清洁维护",)}, gate)

    assert opportunity.score_breakdown == score_before_research[0]
    assert opportunity.total_score == score_before_research[1]
