from __future__ import annotations

from typing import Any

import requests

from radar.models import SocialRecord, SourceHealth
from radar.normalizers import normalize_social_record


_BASE_URL = "https://api.scrapecreators.com"
_ROUTES = {
    "instagram": "/v1/instagram/search/hashtag",
    "tiktok": "/v1/tiktok/search/keyword",
    "youtube": "/v1/youtube/search",
    "reddit": "/v1/reddit/search",
}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _params(platform: str, keyword: str) -> dict[str, Any]:
    clean_keyword = keyword.strip().lstrip("#").strip()
    if platform == "instagram":
        return {"hashtag": clean_keyword, "media_type": "all"}
    if platform == "tiktok":
        return {
            "query": clean_keyword,
            "date_posted": "this-month",
            "sort_by": "relevance",
            "trim": True,
        }
    if platform == "youtube":
        return {"query": clean_keyword, "type": "videos", "includeExtras": "true"}
    return {"query": clean_keyword, "sort": "relevance", "timeframe": "month", "trim": True}


def _items(payload: Any, platform: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    if platform == "tiktok":
        search_items = payload.get("search_item_list")
        if not isinstance(search_items, list):
            return []
        return [
            item["aweme_info"]
            for item in search_items
            if isinstance(item, dict) and isinstance(item.get("aweme_info"), dict)
        ]
    payload_key = {"instagram": "posts", "youtube": "videos", "reddit": "posts"}[platform]
    items = payload.get(payload_key)
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


def _canonical_item(platform: str, raw: dict[str, Any]) -> dict[str, Any]:
    if platform == "instagram":
        owner = _dict(raw.get("owner"))
        return {
            **raw,
            "title": raw.get("caption"),
            "text": raw.get("caption"),
            "author": owner.get("username") or owner.get("full_name"),
            "published_at": raw.get("taken_at"),
        }
    if platform == "tiktok":
        author = _dict(raw.get("author"))
        share_info = _dict(raw.get("share_info"))
        statistics = _dict(raw.get("statistics"))
        return {
            "url": share_info.get("share_url"),
            "title": raw.get("desc"),
            "text": raw.get("desc"),
            "author": author.get("unique_id") or author.get("nickname"),
            "published_at": raw.get("create_time_utc") or raw.get("create_time"),
            "likes": statistics.get("digg_count"),
            "favorites": statistics.get("collect_count"),
            "comment_count": statistics.get("comment_count"),
            "comments": raw.get("comments", []),
        }
    if platform == "youtube":
        channel = _dict(raw.get("channel"))
        return {
            **raw,
            "text": raw.get("description"),
            "author": channel.get("title"),
            "published_at": raw.get("publishedTime"),
            "likes": raw.get("likeCountInt"),
            "comment_count": raw.get("commentCountInt"),
        }
    return {
        **raw,
        "text": raw.get("selftext"),
        "published_at": raw.get("created_at_iso"),
        "likes": raw.get("score"),
        "comment_count": raw.get("num_comments"),
    }


def collect_scrapecreators(
    platform: str,
    keyword: str,
    api_key: str,
    session=None,
) -> tuple[list[SocialRecord], SourceHealth]:
    platform = platform.strip().lower()
    if platform not in _ROUTES:
        raise ValueError(f"Unsupported ScrapeCreators platform: {platform}")

    client = session or requests.Session()
    url = f"{_BASE_URL}{_ROUTES[platform]}"
    try:
        response = client.get(
            url,
            headers={"x-api-key": api_key},
            params=_params(platform, keyword),
            timeout=60,
        )
        response.raise_for_status()
        records = [
            normalize_social_record(_canonical_item(platform, item), platform=platform, keyword=keyword)
            for item in _items(response.json(), platform)
        ]
    except Exception:
        return [], SourceHealth.FAILED
    return records, SourceHealth.OK if records else SourceHealth.PARTIAL
