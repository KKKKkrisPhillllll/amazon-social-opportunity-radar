import pytest
from test_helpers import (
    make_eligible_gate,
    make_low_evidence_gate,
    make_opportunity,
    make_two_platform_evidence,
)

from radar.evidence import EvidenceItem
from radar.journey_builder import build_journey
from radar.models import PersonaEvidence
from radar.persona_builder import build_persona


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
    assert [stage.name for stage in stages] == [
        "发现需求",
        "搜索方案",
        "对比决策",
        "购买",
        "使用",
        "反馈",
    ]


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


def test_low_confidence_summary_with_space_uses_neutral_behavioral_segment():
    opportunity = make_opportunity()
    evidence = [
        EvidenceItem(
            "E-0001",
            "reddit",
            "https://reddit.example/1",
            "kitchen_storage",
            "小厨房空间占用明显，用户正在寻找更省空间的方案",
            1,
        )
    ]

    persona = build_persona(
        opportunity,
        evidence,
        {},
        make_low_evidence_gate(),
    )

    assert persona.confidence == "低"
    assert persona.behavioral_segment == "待验证用户类型"


def test_blank_summaries_do_not_consume_evidence_quota_or_confidence():
    opportunity = make_opportunity()
    evidence = [
        *make_two_platform_evidence(),
        EvidenceItem("E-0003", "reddit", "https://reddit.example/3", "kitchen_storage", "   ", 0),
        EvidenceItem("E-0004", "youtube", "https://youtube.example/4", "kitchen_storage", "", 0),
    ]

    persona = build_persona(opportunity, evidence, {}, make_eligible_gate())

    assert persona.confidence == "中"
    assert len(persona.evidence) == 2
    assert all(item.summary.strip() for item in persona.evidence)


def test_low_confidence_uses_neutral_unverified_persona_fields():
    opportunity = make_opportunity()
    voc = {"E-0001": ("空间占用",)}

    persona = build_persona(
        opportunity,
        make_two_platform_evidence()[:1],
        voc,
        make_low_evidence_gate(),
    )

    assert persona.confidence == "低"
    assert persona.scenario == "证据不足，待验证"
    assert persona.core_goal == "证据不足，待验证"
    assert persona.purchase_triggers == ("证据不足，待验证",)
    assert persona.concerns == ("证据不足，待验证",)
    assert persona.pain_points == ("空间占用", "证据不足，待验证")


def test_non_eligible_gate_rejects_build_when_evidence_is_not_low_confidence():
    opportunity = make_opportunity()
    evidence = make_two_platform_evidence()
    gate = make_low_evidence_gate()
    gate = gate.__class__(False, 2, 2, False, (), ("需要人工复核",), "继续验证")

    with pytest.raises(ValueError):
        build_persona(opportunity, evidence, {}, gate)
    with pytest.raises(ValueError):
        build_journey(opportunity, evidence, {}, gate)


def test_persona_evidence_contract_exposes_only_public_fields():
    assert {field.name for field in PersonaEvidence.__dataclass_fields__.values()} == {
        "platform",
        "url",
        "summary",
    }
    evidence = make_two_platform_evidence()
    persona = build_persona(
        make_opportunity(), evidence, {}, make_eligible_gate()
    )

    assert all(
        set(item.__dict__) == {"platform", "url", "summary"}
        for item in persona.evidence
    )
    assert not any(
        field in item.__dict__
        for item in persona.evidence
        for field in ("author", "account", "comments", "review_text")
    )


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
