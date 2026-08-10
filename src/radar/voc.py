from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from pathlib import Path

import yaml

from radar.evidence import EvidenceItem

_GENERIC_CONTRAST_WORDS = {"but", "但是", "不过"}
_REQUIRED_SIGNAL_GROUPS = (
    "workarounds",
    "tradeoffs",
    "over_served",
    "extreme_users",
    "counter_evidence",
)
_REQUIRED_DIMENSION_CODES = {f"D{index:02d}" for index in range(1, 23)}


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
        try:
            data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise ValueError(f"invalid YAML in VOC config: {exc}") from exc
    if not isinstance(data, Mapping):
        raise ValueError("top-level YAML must be a mapping")  # noqa: TRY004

    taxonomy = data.get("taxonomy")
    if not isinstance(taxonomy, Mapping):
        raise ValueError("taxonomy must be a mapping")  # noqa: TRY004

    dimension_codes: set[str] = set()
    for name, words in taxonomy.items():
        if not isinstance(name, str) or not re.match(r"^D\d{2}(?:_|$)", name):
            raise ValueError(f"taxonomy dimension name is invalid: {name!r}")
        code = name[:3]
        if code in dimension_codes:
            raise ValueError(f"taxonomy contains duplicate dimension code: {code}")
        dimension_codes.add(code)
        _validate_word_list(words, f"taxonomy dimension {name}")

    missing_dimensions = _REQUIRED_DIMENSION_CODES - dimension_codes
    extra_dimensions = dimension_codes - _REQUIRED_DIMENSION_CODES
    if missing_dimensions or extra_dimensions:
        raise ValueError(
            "taxonomy must contain all dimensions D01-D22"
            + (f"; missing: {sorted(missing_dimensions)}" if missing_dimensions else "")
            + (f"; unexpected: {sorted(extra_dimensions)}" if extra_dimensions else "")
        )

    signals = {key: value for key, value in data.items() if key != "taxonomy"}
    missing_signals = set(_REQUIRED_SIGNAL_GROUPS) - set(signals)
    extra_signals = set(signals) - set(_REQUIRED_SIGNAL_GROUPS)
    if missing_signals or extra_signals:
        raise ValueError(
            "signals must contain exactly workarounds, tradeoffs, over_served, extreme_users, counter_evidence"
            + (f"; missing: {sorted(missing_signals)}" if missing_signals else "")
            + (f"; unexpected: {sorted(extra_signals)}" if extra_signals else "")
        )
    for name in _REQUIRED_SIGNAL_GROUPS:
        _validate_word_list(signals[name], f"signals group {name}")

    return ({name: list(words) for name, words in taxonomy.items()},
            {name: list(signals[name]) for name in _REQUIRED_SIGNAL_GROUPS})


def _validate_word_list(words: object, label: str) -> None:
    if not isinstance(words, list) or not words or not all(isinstance(word, str) for word in words):
        raise ValueError(f"{label} must be a non-empty list of strings")
