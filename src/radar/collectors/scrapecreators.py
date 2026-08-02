from __future__ import annotations

from typing import Any

import requests

from radar.models import SourceHealth, SourceRun
from radar.normalizers import normalize_social_record

PLATFORM_SPECS = {
    "instagram": ("/v1/instagram/search", "items"),
    "tiktok": ("/v1/tiktok/search/keyword", "search_item_list"),
    "youtube": ("/v1/youtube/search", "videos"),
    "reddit": ("/v1/reddit/search", "posts"),
}


def _items(payload: Any, item_key: str) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        values = payload.get(item_key)
        if isinstance(values, list):
            return [item for item in values if isinstance(item, dict)]
    return []


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _common_item(item: dict[str, Any], platform: str) -> dict[str, Any]:
    if platform == "tiktok":
        video = item.get("aweme_info") if isinstance(item.get("aweme_info"), dict) else item
        author = video.get("author") if isinstance(video.get("author"), dict) else {}
        statistics = video.get("statistics") if isinstance(video.get("statistics"), dict) else {}
        return {
            "url": video.get("share_url") or video.get("url"),
            "title": video.get("title"),
            "text": video.get("desc") or video.get("description"),
            "author": author.get("nickname") or author.get("unique_id"),
            "published_at": video.get("create_time") or video.get("published_at"),
            "likes": statistics.get("digg_count") or video.get("like_count"),
            "comment_count": statistics.get("comment_count") or video.get("comment_count"),
        }
    if platform == "youtube":
        return {
            "url": item.get("url") or item.get("video_url") or item.get("link"),
            "title": item.get("title"),
            "text": item.get("description"),
            "author": item.get("channel_title") or item.get("channel"),
            "published_at": item.get("published_at") or item.get("publishedAt"),
            "likes": item.get("like_count") or item.get("likeCount"),
            "comment_count": item.get("comment_count") or item.get("commentCount"),
        }
    if platform == "reddit":
        return {
            "url": item.get("url") or item.get("permalink") or item.get("link"),
            "title": item.get("title"),
            "text": item.get("selftext") or item.get("body") or item.get("text"),
            "author": item.get("author") or item.get("username"),
            "published_at": item.get("created_at") or item.get("published_at"),
            "likes": item.get("score") or item.get("likes"),
            "comment_count": item.get("num_comments") or item.get("comment_count"),
        }
    return {
        "url": item.get("url") or item.get("postUrl") or item.get("link"),
        "title": item.get("title") or item.get("caption"),
        "text": item.get("text") or item.get("caption") or item.get("description"),
        "author": item.get("username") or item.get("author"),
        "published_at": item.get("published_at") or item.get("publishedAt"),
        "likes": item.get("likes") or item.get("like_count"),
        "comment_count": item.get("comment_count"),
    }


def collect_scrapecreators(
    platform: str,
    keyword: str,
    api_key: str,
    session=None,
) -> SourceRun:
    spec = PLATFORM_SPECS.get(platform)
    if spec is None:
        return SourceRun(
            f"scrapecreators_{platform}",
            platform,
            (),
            SourceHealth.FAILED,
            0,
            diagnostic="unsupported_platform",
        )
    endpoint, item_key = spec
    client = session or requests.Session()
    url = f"https://api.scrapecreators.com{endpoint}"
    try:
        response = client.get(
            url,
            headers={"x-api-key": api_key},
            params={"query": keyword},
            timeout=60,
        )
        response.raise_for_status()
        raw_items = _items(response.json(), item_key)
    except (requests.RequestException, TypeError, ValueError):
        return SourceRun(
            f"scrapecreators_{platform}",
            platform,
            (),
            SourceHealth.FAILED,
            0,
            diagnostic="request_failed",
        )
    records = tuple(
        record
        for item in raw_items
        if (record := normalize_social_record(_common_item(item, platform), platform, keyword)).url
        and (record.title or record.text)
    )
    if not records:
        diagnostic = "no_records" if not raw_items else "no_usable_records"
        return SourceRun(
            f"scrapecreators_{platform}", platform, (), SourceHealth.PARTIAL, len(raw_items), diagnostic=diagnostic
        )
    health = SourceHealth.OK if len(records) == len(raw_items) else SourceHealth.PARTIAL
    return SourceRun(
        f"scrapecreators_{platform}",
        platform,
        records,
        health,
        len(raw_items),
        diagnostic="ok" if health is SourceHealth.OK else "filtered_incomplete_records",
    )
