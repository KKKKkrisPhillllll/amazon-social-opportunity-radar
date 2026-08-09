from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import yaml

from radar.evidence import EvidenceItem


_GENERIC_CONTRAST_WORDS = {"but", "但是", "不过"}


def _hit(text: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    text = text.lower()
    if any("\u4e00" <= char <= "\u9fff" for char in keyword):
        return keyword in text
    return re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text) is not None


def classify_voc(
    items: Sequence[EvidenceItem],
    taxonomy: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    return {
        item.evidence_id: tuple(
            dimension
            for dimension, words in taxonomy.items()
            if any(_hit(item.summary, word) for word in words)
        )
        for item in items
    }


def _tradeoff_hit(text: str, candidates: Sequence[str]) -> bool:
    hits = {word.strip().lower() for word in candidates if word.strip() and _hit(text, word)}
    generic_hits = hits & _GENERIC_CONTRAST_WORDS
    return bool(hits) and (not generic_hits or len(hits - generic_hits) > 0)


def detect_innovation_signals(
    items: Sequence[EvidenceItem],
    words: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {name: [] for name in words}
    for item in items:
        for name, candidates in words.items():
            matched = (
                _tradeoff_hit(item.summary, candidates)
                if name == "tradeoffs"
                else any(_hit(item.summary, word) for word in candidates)
            )
            if matched:
                result[name].append(item.evidence_id)
    return {name: tuple(ids) for name, ids in result.items()}


def load_voc_config(path: str | Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    taxonomy = data.get("taxonomy", {})
    signals = {key: value for key, value in data.items() if key != "taxonomy"}
    return (
        {name: list(words or []) for name, words in taxonomy.items()},
        {name: list(words or []) for name, words in signals.items()},
    )
