from radar.journey_builder import JOURNEY_STAGES, build_journey
from radar.persona_builder import build_persona
from radar.evidence import EvidenceItem
from test_helpers import (
    make_eligible_gate,
    make_low_evidence_gate,
    make_opportunity,
    make_two_platform_evidence,
)


def test_high_score_opportunity_gets_behavioral_persona_and_six_stages():
    opportunity = make_opportunity(total_score=75, category="kitchen_storage")
    evidence = make_two_platform_evidence()
    voc = {item.evidence_id: ("D06_空间占用",) for item in evidence}

    persona = build_persona(opportunity, evidence, voc, make_eligible_gate())
    stages = build_journey(opportunity, evidence, voc, make_eligible_gate())

    assert persona.category == "kitchen_storage"
    assert persona.confidence in {"中", "高"}
    assert persona.behavioral_segment in {"小空间效率型", "一般任务型"}
    assert len(persona.evidence) == 2
    assert [stage.name for stage in stages] == list(JOURNEY_STAGES)


def test_insufficient_evidence_is_low_confidence_and_neutral():
    opportunity = make_opportunity(total_score=75)
    persona = build_persona(
        opportunity,
        make_two_platform_evidence()[:1],
        {},
        make_low_evidence_gate(),
    )

    assert persona.confidence == "低"
    assert any("待验证" in item for item in persona.pain_points)


def test_builders_filter_category_deduplicate_urls_and_cap_evidence():
    opportunity = make_opportunity(category="kitchen_storage")
    evidence = [
        EvidenceItem(
            f"E-{index:04d}",
            "reddit" if index % 2 else "youtube",
            url,
            category,
            f"摘要 {index}",
            0,
        )
        for index, (url, category) in enumerate(
            [
                ("https://example.com/post/1/", "kitchen_storage"),
                ("https://example.com/post/1", "kitchen_storage"),
                ("https://example.com/post/2", "kitchen_storage"),
                ("https://example.com/post/3", "kitchen_storage"),
                ("https://example.com/post/4", "kitchen_storage"),
                ("https://example.com/post/5", "kitchen_storage"),
                ("https://example.com/post/6", "kitchen_storage"),
                ("https://example.com/other", "bathroom_storage"),
            ],
            start=1,
        )
    ]

    persona = build_persona(opportunity, evidence, {}, make_eligible_gate())
    stages = build_journey(opportunity, evidence, {}, make_eligible_gate())

    assert len(persona.evidence) == 5
    assert len({item.url for item in persona.evidence}) == 5
    assert all(item.platform and item.url and item.summary for item in persona.evidence)
    assert all(url.startswith("https://example.com/") for stage in stages for url in stage.evidence_urls)
    assert len(stages) == 6


def test_journey_marks_unobserved_stages_as_pending_validation():
    opportunity = make_opportunity()
    stages = build_journey(
        opportunity,
        make_two_platform_evidence()[:1],
        {},
        make_low_evidence_gate(),
    )

    assert len(stages) == 6
    assert any("待后续采集验证" in stage.user_need_or_action for stage in stages)
    assert all(stage.confidence == "低" for stage in stages)
