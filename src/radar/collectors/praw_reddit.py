from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from praw.exceptions import PRAWException
from prawcore.exceptions import PrawcoreException
from requests import RequestException

from radar.models import SocialRecord, SourceHealth, SourceRun


def _submission_url(submission: Any) -> str:
    url = str(getattr(submission, "url", "") or "").strip()
    if url:
        return url
    permalink = str(getattr(submission, "permalink", "") or "").strip()
    if permalink.startswith("/"):
        return f"https://www.reddit.com{permalink}"
    return permalink


def _published_at(value: Any) -> str:
    try:
        return datetime.fromtimestamp(float(value), UTC).isoformat()
    except (TypeError, ValueError, OSError):
        return ""


def collect_praw_reddit(
    keyword: str,
    client_id: str,
    client_secret: str,
    user_agent: str,
    reddit_factory: Callable[..., Any] | None = None,
    max_results: int = 20,
) -> SourceRun:
    if max_results < 1:
        raise ValueError("max_results must be at least 1")
    try:
        if reddit_factory is None:
            from praw import Reddit

            reddit_factory = Reddit
        reddit = reddit_factory(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        submissions = list(reddit.subreddit("all").search(keyword, limit=max_results))
    except (OSError, PRAWException, PrawcoreException, RequestException, TypeError, ValueError):
        return SourceRun(
            "praw_reddit", "reddit", (), SourceHealth.FAILED, 0, diagnostic="request_failed"
        )

    records = tuple(
        SocialRecord(
            platform="reddit",
            keyword=keyword,
            url=_submission_url(submission),
            title=str(getattr(submission, "title", "") or "").strip(),
            text=str(getattr(submission, "selftext", "") or "").strip(),
            author=str(getattr(submission, "author", "") or "").strip(),
            published_at=_published_at(getattr(submission, "created_utc", None)),
            engagement={
                "likes": int(getattr(submission, "score", 0) or 0),
                "favorites": 0,
                "comments": int(getattr(submission, "num_comments", 0) or 0),
            },
        )
        for submission in submissions
        if _submission_url(submission)
        and (
            str(getattr(submission, "title", "") or "").strip()
            or str(getattr(submission, "selftext", "") or "").strip()
        )
    )
    if not records:
        diagnostic = "no_records" if not submissions else "no_usable_records"
        return SourceRun("praw_reddit", "reddit", (), SourceHealth.PARTIAL, len(submissions), diagnostic=diagnostic)
    health = SourceHealth.OK if len(records) == len(submissions) else SourceHealth.PARTIAL
    return SourceRun(
        "praw_reddit",
        "reddit",
        records,
        health,
        len(submissions),
        diagnostic="ok" if health is SourceHealth.OK else "filtered_incomplete_records",
    )
