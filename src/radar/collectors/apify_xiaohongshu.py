from __future__ import annotations

from typing import Any

import requests

from radar.models import SourceHealth, SourceRun
from radar.normalizers import normalize_apify_xiaohongshu_record


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def _actor_id(actor: str) -> str:
    return actor.strip().replace("/", "~")


def collect_xiaohongshu(
    keyword: str,
    token: str,
    actor: str,
    session=None,
    max_results: int = 20,
) -> SourceRun:
    if max_results < 1:
        raise ValueError("max_results must be at least 1")
    client = session or requests.Session()
    url = (
        f"https://api.apify.com/v2/acts/{_actor_id(actor)}"
        "/run-sync-get-dataset-items"
    )
    try:
        response = client.post(
            url,
            params={"token": token},
            json={
                "mode": "search",
                "searchQuery": keyword,
                "maxResults": max_results,
            },
            timeout=120,
        )
        response.raise_for_status()
        raw_items = _items(response.json())
    except (requests.RequestException, TypeError, ValueError):
        return SourceRun(
            source_name="apify_xiaohongshu",
            platform="xiaohongshu",
            records=(),
            health=SourceHealth.FAILED,
            fetched_count=0,
            diagnostic="request_failed",
        )
    records = tuple(
        record
        for item in raw_items
        if (record := normalize_apify_xiaohongshu_record(item, keyword)).url
        and (record.title or record.text)
    )
    if not records:
        diagnostic = "no_records" if not raw_items else "no_usable_records"
        return SourceRun(
            "apify_xiaohongshu", "xiaohongshu", (), SourceHealth.PARTIAL, len(raw_items), diagnostic=diagnostic
        )
    health = SourceHealth.OK if len(records) == len(raw_items) else SourceHealth.PARTIAL
    return SourceRun(
        "apify_xiaohongshu",
        "xiaohongshu",
        records,
        health,
        len(raw_items),
        diagnostic="ok" if health is SourceHealth.OK else "filtered_incomplete_records",
    )
