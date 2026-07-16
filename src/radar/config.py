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
        raise ValueError(f"Config file must contain a mapping: {resolved}")
    return data


def load_keywords(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    groups = data.get("keyword_groups")
    if not isinstance(groups, dict) or not groups:
        raise ValueError("keywords config requires non-empty keyword_groups")
    categories = data.get("focus_categories")
    if not isinstance(categories, list) or not categories:
        raise ValueError("keywords config requires non-empty focus_categories")
    missing_groups = [category for category in categories if category not in groups]
    if missing_groups:
        raise ValueError(f"keywords config missing groups for: {', '.join(missing_groups)}")
    return data


def load_source_settings(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    for key in ("feishu", "apify", "scrapecreators", "amazon_reviews", "collection"):
        if key not in data:
            raise ValueError(f"sources config missing required section: {key}")
    return data


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not configured: {name}")
    return value
