from radar.evidence import EvidenceItem
from radar.opportunity_gate import evaluate_opportunity_gate
from test_helpers import make_opportunity


def _evidence(evidence_id: str, platform: str, category: str = "kitchen_storage") -> EvidenceItem:
    return EvidenceItem(
        evidence_id,
        platform,
        f"https://{platform}.example/{evidence_id}",
        category,
        "占空间",
        0,
    )


def test_gate_requires_two_independent_public_sources():
    evidence = [_evidence("E-0001", "reddit"), _evidence("E-0002", "reddit")]

    gate = evaluate_opportunity_gate(
        opportunity=make_opportunity(total_score=75),
        evidence=evidence,
        voc={"E-0001": ("D06_空间占用",), "E-0002": ("D06_空间占用",)},
        signals={},
    )

    assert gate.eligible is False
    assert "至少 2 个独立来源" in "；".join(gate.gaps)
    assert gate.independent_source_count == 1


def test_gate_accepts_high_score_with_two_platforms_and_exposes_counter_evidence():
    evidence = [_evidence("E-0001", "reddit"), _evidence("E-0002", "youtube")]

    gate = evaluate_opportunity_gate(
        opportunity=make_opportunity(total_score=75),
        evidence=evidence,
        voc={"E-0001": ("D06_空间占用",), "E-0002": ("D06_空间占用",)},
        signals={"counter_evidence": ("E-0002",)},
    )

    assert gate.eligible is True
    assert gate.has_counter_evidence is True
    assert gate.next_validation


def test_gate_rejects_score_below_threshold():
    gate = evaluate_opportunity_gate(
        make_opportunity(total_score=59),
        [_evidence("E-0001", "reddit"), _evidence("E-0002", "youtube")],
        {},
        {},
    )

    assert gate.eligible is False
    assert "机会总分低于 60 分" in gate.gaps


def test_gate_counts_only_current_category_evidence():
    gate = evaluate_opportunity_gate(
        make_opportunity(category="kitchen_storage"),
        [_evidence("E-0001", "reddit", "other"), _evidence("E-0002", "youtube", "other")],
        {"E-0001": ("D06_空间占用",)},
        {},
    )

    assert gate.evidence_count == 0
    assert gate.independent_source_count == 0
    assert gate.eligible is False


def test_gate_workaround_strengths_use_only_current_category_ids():
    gate = evaluate_opportunity_gate(
        make_opportunity(),
        [_evidence("E-0001", "reddit"), _evidence("E-0002", "youtube")],
        {},
        {"workarounds": ("E-OTHER",)},
    )

    assert "发现用户替代方案或自救行为" not in gate.strengths


def test_gate_counter_evidence_is_a_risk_not_an_exclusion():
    gate = evaluate_opportunity_gate(
        make_opportunity(),
        [_evidence("E-0001", "reddit"), _evidence("E-0002", "youtube")],
        {},
        {"counter_evidence": ("E-0002",)},
    )

    assert gate.eligible is True
    assert gate.has_counter_evidence is True
    assert any("反向证据" in gap for gap in gate.gaps)

def test_gate_deduplicates_same_evidence_id_across_platforms():
    evidence = [_evidence("E-DUP", "reddit"), _evidence("E-DUP", "youtube")]

    gate = evaluate_opportunity_gate(
        make_opportunity(total_score=75),
        evidence,
        {},
        {},
        min_evidence_count=2,
    )

    assert gate.eligible is False
    assert gate.evidence_count == 1
    assert gate.independent_source_count == 1


def test_gate_accepts_exact_score_and_minimum_evidence_without_mutating_score():
    opportunity = make_opportunity(total_score=60)
    score_breakdown_before = opportunity.score_breakdown.copy()
    total_score_before = opportunity.total_score

    gate = evaluate_opportunity_gate(
        opportunity,
        [_evidence("E-0001", "reddit"), _evidence("E-0002", "youtube")],
        {},
        {},
        min_evidence_count=2,
    )

    assert gate.eligible is True
    assert gate.evidence_count == 2
    assert opportunity.score_breakdown == score_breakdown_before
    assert opportunity.total_score == total_score_before
