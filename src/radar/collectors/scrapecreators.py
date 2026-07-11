from __future__ import annotations

from typing import Any

import requests

from radar.models import SocialRecord, SourceHealth
from radar.normalizers import normalize_social_record


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "posts"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def collect_scrapecreators(
    platform: str,
    keyword: str,
    api_key: str,
    session=None,
) -> tuple[list[SocialRecord], SourceHealth]:
    client = session or requests.Session()
    url = f"https://api.scrapecreators.com/v1/{platform}/search"
    try:
        response = client.get(
            url,
            headers={"x-api-key": api_key},
            params={"query": keyword, "limit": 20},
            timeout=60,
        )
        response.raise_for_status()
        records = [
            normalize_social_record(item, platform=platform, keyword=keyword)
            for item in _items(response.json())
        ]
    except Exception:
        return [], SourceHealth.FAILED
    return records, SourceHealth.OK if records else SourceHealth.PARTIAL
