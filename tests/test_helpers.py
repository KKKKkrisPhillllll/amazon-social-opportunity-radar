from radar.evidence import EvidenceItem
from radar.models import Opportunity


def make_opportunity(total_score=75, category="kitchen_storage"):
    return Opportunity(
        title="台面收纳机会",
        category=category,
        source_platforms=["reddit", "youtube"],
        evidence_summary="测试证据",
        customer_pain_point="台面空间不足",
        product_idea="减少取放步骤",
        amazon_validation_keywords=["kitchen storage"],
        suggested_asins=[],
        differentiation_angle="提高空间利用率",
        risk_notes="需要样品验证",
        next_action="补充竞品验证",
        score_breakdown={"social_heat": total_score},
    )


def make_two_platform_evidence():
    return [
        EvidenceItem("E-0001", "reddit", "https://reddit.example/1", "kitchen_storage", "", "台面空间太小", ()),
        EvidenceItem("E-0002", "youtube", "https://youtube.example/2", "kitchen_storage", "", "很难清洁", ()),
    ]


def make_eligible_gate():
    from radar.opportunity_gate import OpportunityGate

    return OpportunityGate(True, 2, 2, False, ("存在 VOC 信号",), (), "补充样品测试")


def make_low_evidence_gate():
    from radar.opportunity_gate import OpportunityGate

    return OpportunityGate(False, 1, 1, False, (), ("公开证据少于 2 条",), "补充公开证据")
