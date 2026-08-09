from pathlib import Path

from radar.evidence import EvidenceItem
from radar.voc import classify_voc, detect_innovation_signals, load_voc_config


def _item(evidence_id: str, summary: str) -> EvidenceItem:
    return EvidenceItem(
        evidence_id=evidence_id,
        platform="reddit",
        url=f"https://reddit.example/{evidence_id}",
        category="kitchen_storage",
        summary=summary,
        comment_count=0,
    )


def test_voc_classifies_space_and_cleaning_without_changing_text():
    item = _item("E-0001", "台面空间太小，而且很难清洁。")

    themes = classify_voc(
        [item], {"D06_空间占用": ["空间"], "D12_清洁维护": ["清洁"]}
    )

    assert themes["E-0001"] == ("D06_空间占用", "D12_清洁维护")
    assert item.summary == "台面空间太小，而且很难清洁。"


def test_counter_evidence_is_separate_from_pain_signal():
    item = _item("E-0002", "这个方案没问题，不需要更换。")

    signals = detect_innovation_signals([item], {"counter_evidence": ["没问题"]})

    assert signals["counter_evidence"] == ("E-0002",)
    assert signals.get("workarounds", ()) == ()


def test_english_keywords_use_token_boundaries_and_ignore_empty_words():
    items = [_item("E-0003", "wanted design"), _item("E-0004", "ad")]

    themes = classify_voc([items[0], items[1]], {"D01": ["", "ad"]})

    assert themes["E-0003"] == ()
    assert themes["E-0004"] == ("D01",)


def test_generic_but_does_not_create_tradeoff_without_second_contrast_signal():
    items = [_item("E-0005", "It works, but it is compact."), _item("E-0006", "It works, but the trade-off is capacity.")]

    signals = detect_innovation_signals(
        items, {"tradeoffs": ["but", "trade-off", "capacity"]}
    )

    assert signals["tradeoffs"] == ("E-0006",)


def test_load_voc_config_contains_22_dimensions_and_signal_groups():
    taxonomy, signals = load_voc_config(Path("config/voc_tags.yaml"))

    assert list(taxonomy) == [f"D{index:02d}_" + name for index, name in [
        (1, "功能有效性"), (2, "性能表现"), (3, "可靠耐用"), (4, "尺寸适配"),
        (5, "安装使用"), (6, "空间占用"), (7, "收纳组织"), (8, "外观设计"),
        (9, "材质做工"), (10, "价格价值"), (11, "物流包装"), (12, "清洁维护"),
        (13, "安全风险"), (14, "兼容整合"), (15, "容量效率"), (16, "噪音气味"),
        (17, "可持续性"), (18, "购买决策"), (19, "替代方案"), (20, "情绪体验"),
        (21, "售前咨询"), (22, "售后退换"),
    ]]
    assert set(signals) == {"workarounds", "tradeoffs", "over_served", "extreme_users", "counter_evidence"}
    assert all(isinstance(words, list) for words in [*taxonomy.values(), *signals.values()])
