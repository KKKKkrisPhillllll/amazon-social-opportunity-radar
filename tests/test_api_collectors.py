import pytest

from radar.collectors.apify_xiaohongshu import collect_xiaohongshu
from radar.collectors.scrapecreators import collect_scrapecreators
from radar.models import SourceHealth


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.text)


class RaisingResponse:
    def raise_for_status(self):
        raise RuntimeError("HTTP 500")

    def json(self):
        raise AssertionError("json should not be called after HTTP failure")


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"method": "GET", "url": url, "kwargs": kwargs})
        return FakeResponse(self.payload)

    def post(self, url, **kwargs):
        self.calls.append({"method": "POST", "url": url, "kwargs": kwargs})
        return FakeResponse(self.payload)


def test_collect_xiaohongshu_normalizes_apify_items():
    session = FakeSession(
        [
            {
                "url": "https://xiaohongshu.com/a",
                "title": "kitchen storage",
                "text": "takes too much space",
                "likes": 50,
                "comments": [{"text": "regret buying"}],
            }
        ]
    )

    records, health = collect_xiaohongshu("kitchen storage", "token", "actor/name", session=session)

    assert health is SourceHealth.OK
    assert records[0].platform == "xiaohongshu"
    assert records[0].keyword == "kitchen storage"


def test_collect_xiaohongshu_accepts_slash_actor_names():
    session = FakeSession([])

    collect_xiaohongshu(
        "kitchen storage",
        "token",
        "zhorex/rednote-xiaohongshu-scraper",
        session=session,
    )

    assert "/zhorex~rednote-xiaohongshu-scraper/" in session.calls[0]["url"]


def test_collect_xiaohongshu_uses_official_search_input():
    session = FakeSession([])

    collect_xiaohongshu(
        "厨房收纳",
        "token",
        "zhorex/rednote-xiaohongshu-scraper",
        session=session,
        max_results=12,
        include_comments=False,
    )

    call = session.calls[0]
    assert call["method"] == "POST"
    assert call["kwargs"]["params"] == {"token": "token"}
    assert call["kwargs"]["json"] == {
        "mode": "search",
        "searchQuery": "厨房收纳",
        "maxResults": 12,
        "includeComments": False,
        "maxComments": 20,
        "sortBy": "general",
    }


def test_collect_xiaohongshu_returns_failed_on_http_failure():
    class FailingSession:
        def post(self, url, **kwargs):
            return RaisingResponse()

    records, health = collect_xiaohongshu(
        "kitchen storage",
        "token",
        "actor/name",
        session=FailingSession(),
    )

    assert records == []
    assert health is SourceHealth.FAILED


@pytest.mark.parametrize(
    ("platform", "payload", "route", "params"),
    [
        (
            "instagram",
            {"posts": []},
            "/v1/instagram/search/hashtag",
            {"hashtag": "厨房收纳", "media_type": "all"},
        ),
        (
            "tiktok",
            {"search_item_list": []},
            "/v1/tiktok/search/keyword",
            {
                "query": "厨房收纳",
                "date_posted": "this-month",
                "sort_by": "relevance",
                "trim": True,
            },
        ),
        (
            "youtube",
            {"videos": []},
            "/v1/youtube/search",
            {"query": "厨房收纳", "type": "videos", "includeExtras": "true"},
        ),
        (
            "reddit",
            {"posts": []},
            "/v1/reddit/search",
            {"query": "厨房收纳", "sort": "relevance", "timeframe": "month", "trim": True},
        ),
    ],
)
def test_collect_scrapecreators_uses_official_platform_routes(platform, payload, route, params):
    session = FakeSession(payload)

    collect_scrapecreators(platform, "#厨房收纳", "key", session=session)

    call = session.calls[0]
    assert call["url"] == f"https://api.scrapecreators.com{route}"
    assert call["kwargs"]["headers"] == {"x-api-key": "key"}
    assert call["kwargs"]["params"] == params


def test_collect_scrapecreators_normalizes_reddit_posts():
    session = FakeSession(
        {
            "posts": [
                {
                    "url": "https://reddit.com/r/test",
                    "title": "Kitchen storage pain",
                    "selftext": "hard to clean",
                    "author": "product_user",
                    "score": 5,
                    "num_comments": 2,
                    "created_at_iso": "2026-07-15T08:00:00Z",
                }
            ]
        }
    )

    records, health = collect_scrapecreators("reddit", "kitchen storage", "key", session=session)

    assert health is SourceHealth.OK
    assert records[0].platform == "reddit"
    assert records[0].title == "Kitchen storage pain"
    assert records[0].text == "hard to clean"
    assert records[0].author == "product_user"
    assert records[0].published_at == "2026-07-15T08:00:00Z"
    assert records[0].engagement["likes"] == 5
    assert records[0].engagement["comments"] == 2


def test_collect_scrapecreators_normalizes_instagram_posts():
    session = FakeSession(
        {
            "posts": [
                {
                    "url": "https://www.instagram.com/reel/abc/",
                    "caption": "Tiny kitchen storage idea",
                    "owner": {"username": "storage_maker"},
                    "taken_at": "2026-07-15T09:00:00Z",
                    "like_count": 30,
                    "comment_count": 1,
                    "comments": [{"text": "Need a no-drill version"}],
                }
            ]
        }
    )

    records, health = collect_scrapecreators("instagram", "kitchen storage", "key", session=session)

    assert health is SourceHealth.OK
    assert records[0].text == "Tiny kitchen storage idea"
    assert records[0].author == "storage_maker"
    assert records[0].published_at == "2026-07-15T09:00:00Z"
    assert records[0].comments == ["Need a no-drill version"]


def test_collect_scrapecreators_normalizes_tiktok_search_items():
    session = FakeSession(
        {
            "search_item_list": [
                {
                    "aweme_info": {
                        "desc": "Countertop storage is hard to clean",
                        "author": {"unique_id": "kitchen_creator"},
                        "share_info": {"share_url": "https://www.tiktok.com/@maker/video/123"},
                        "create_time": 1721030400,
                        "statistics": {
                            "digg_count": 41,
                            "collect_count": 9,
                            "comment_count": 3,
                        },
                    }
                }
            ]
        }
    )

    records, health = collect_scrapecreators("tiktok", "kitchen storage", "key", session=session)

    assert health is SourceHealth.OK
    assert records[0].url == "https://www.tiktok.com/@maker/video/123"
    assert records[0].text == "Countertop storage is hard to clean"
    assert records[0].author == "kitchen_creator"
    assert records[0].published_at == "1721030400"
    assert records[0].engagement == {"likes": 41, "favorites": 9, "comments": 3}


def test_collect_scrapecreators_normalizes_youtube_videos():
    session = FakeSession(
        {
            "videos": [
                {
                    "url": "https://www.youtube.com/watch?v=abc",
                    "title": "Kitchen organizer review",
                    "description": "The tray wastes vertical space.",
                    "channel": {"title": "Product Lab"},
                    "viewCountInt": 1200,
                    "publishedTime": "2026-07-14T08:00:00Z",
                }
            ]
        }
    )

    records, health = collect_scrapecreators("youtube", "kitchen storage", "key", session=session)

    assert health is SourceHealth.OK
    assert records[0].title == "Kitchen organizer review"
    assert records[0].text == "The tray wastes vertical space."
    assert records[0].author == "Product Lab"
    assert records[0].published_at == "2026-07-14T08:00:00Z"


def test_collect_scrapecreators_rejects_unsupported_platform():
    with pytest.raises(ValueError, match="Unsupported ScrapeCreators platform"):
        collect_scrapecreators("facebook", "kitchen storage", "key", session=FakeSession({}))


def test_collect_scrapecreators_returns_failed_on_http_failure():
    class FailingSession:
        def get(self, url, **kwargs):
            return RaisingResponse()

    records, health = collect_scrapecreators(
        "reddit",
        "kitchen storage",
        "key",
        session=FailingSession(),
    )

    assert records == []
    assert health is SourceHealth.FAILED
