from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Config file not found: {resolved}")
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise TypeError(f"Config file must contain a mapping: {resolved}")
    return data


def load_keywords(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    groups = data.get("keyword_groups")
    if not isinstance(groups, dict) or not groups:
        raise ValueError("keywords config requires non-empty keyword_groups")
    return data


def load_source_settings(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    for key in ("feishu", "apify", "scrapecreators", "praw_reddit", "amazon_reviews"):
        if key not in data:
            raise ValueError(f"sources config missing required section: {key}")
    persona_journey = data.get("persona_journey")
    if persona_journey is not None:
        if not isinstance(persona_journey, dict):
            raise ValueError("persona_journey must be a mapping")
        for field in (
            "min_opportunity_score",
            "max_opportunities_per_report",
            "min_evidence_count",
        ):
            value = persona_journey.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"persona_journey.{field} must be a positive integer")
    return data


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not configured: {name}")
    return value


def optional_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None
