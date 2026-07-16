from __future__ import annotations

from typing import Any

from radar.models import ReviewRecord, SocialRecord, SourceHealth


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _comments(raw_comments: Any) -> list[str]:
    if not isinstance(raw_comments, list):
        return []
    result: list[str] = []
    for item in raw_comments:
        if isinstance(item, dict):
            text = _text(item.get("text") or item.get("content") or item.get("comment"))
        else:
            text = _text(item)
        if text:
            result.append(text)
    return result


def _first_present(raw: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in raw:
            return raw[key]
    return default


def normalize_social_record(raw: dict[str, Any], platform: str, keyword: str) -> SocialRecord:
    raw_comments = raw.get("comments")
    comment_count = len(raw_comments) if isinstance(raw_comments, list) else _int(raw_comments)
    engagement = {
        "likes": _int(_first_present(raw, "likes", "like_count")),
        "favorites": _int(_first_present(raw, "favorites", "collect_count", "saves")),
        "comments": _int(_first_present(raw, "comment_count", default=comment_count)),
    }
    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    return SocialRecord(
        platform=platform,
        keyword=keyword,
        url=_text(raw.get("url") or raw.get("link") or raw.get("note_url") or raw.get("postUrl")),
        title=_text(raw.get("title") or raw.get("caption")),
        text=_text(raw.get("text") or raw.get("body") or raw.get("description") or raw.get("content")),
        author=_text(
            raw.get("author") or raw.get("username") or raw.get("channel") or raw.get("authorName")
        ),
        published_at=_text(raw.get("published_at") or raw.get("date") or raw.get("publishedAt")),
        tags=[_text(tag) for tag in tags if _text(tag)],
        engagement=engagement,
        comments=_comments(raw.get("comments")),
        health=SourceHealth.OK,
    )


def normalize_review_record(raw: dict[str, Any], source_script: str, raw_source_path: str) -> ReviewRecord:
    helpful = raw.get("helpful") if raw.get("helpful") is not None else raw.get("helpful_count")
    return ReviewRecord(
        asin=_text(raw.get("asin") or raw.get("ASIN")),
        rating=_number(raw.get("rating")),
        title=_text(raw.get("title") or raw.get("review_title")),
        review_text=_text(
            raw.get("review_text") or raw.get("text") or raw.get("content") or raw.get("body")
        ),
        review_date=_text(raw.get("date") or raw.get("review_date")),
        verified=raw.get("verified") if isinstance(raw.get("verified"), bool) else None,
        helpful_count=_int(helpful) if helpful is not None else None,
        source_script=source_script,
        raw_source_path=raw_source_path,
        health=SourceHealth.OK,
    )
