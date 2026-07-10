from __future__ import annotations

from typing import Any

import requests

from radar.models import SocialRecord, SourceHealth
from radar.normalizers import normalize_social_record


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def collect_xiaohongshu(
    keyword: str,
    token: str,
    actor: str,
    session=None,
) -> tuple[list[SocialRecord], SourceHealth]:
    client = session or requests.Session()
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
    try:
        response = client.post(
            url,
            params={"token": token},
            json={"keyword": keyword, "maxItems": 20},
            timeout=120,
        )
        response.raise_for_status()
        records = [
            normalize_social_record(item, platform="xiaohongshu", keyword=keyword)
            for item in _items(response.json())
        ]
    except Exception:
        return [], SourceHealth.FAILED
    return records, SourceHealth.OK if records else SourceHealth.PARTIAL
