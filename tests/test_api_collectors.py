import requests

from radar.collectors.apify_xiaohongshu import collect_xiaohongshu
from radar.collectors.scrapecreators import collect_scrapecreators
from radar.models import SourceHealth, SourceRun


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
        raise requests.RequestException("HTTP 500")

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
                "postUrl": "https://xiaohongshu.com/a",
                "content": "takes too much space",
                "likeCount": 50,
                "comments": [{"text": "regret buying"}],
            }
        ]
    )

    source_run = collect_xiaohongshu(
        "kitchen storage", "token", "actor/name", session=session
    )

    assert isinstance(source_run, SourceRun)
    assert source_run.health is SourceHealth.OK
    assert source_run.records[0].platform == "xiaohongshu"
    assert source_run.records[0].keyword == "kitchen storage"
    assert session.calls[0]["kwargs"]["json"] == {
        "mode": "search",
        "searchQuery": "kitchen storage",
        "maxResults": 20,
    }


def test_collect_xiaohongshu_accepts_slash_actor_names():
    session = FakeSession([])

    collect_xiaohongshu(
        "kitchen storage",
        "token",
        "zhorex/rednote-xiaohongshu-scraper",
        session=session,
    )

    assert "/zhorex~rednote-xiaohongshu-scraper/" in session.calls[0]["url"]


def test_collect_xiaohongshu_returns_failed_on_http_failure():
    class FailingSession:
        def post(self, url, **kwargs):
            return RaisingResponse()

    source_run = collect_xiaohongshu(
        "kitchen storage",
        "token",
        "actor/name",
        session=FailingSession(),
    )

    assert source_run.records == ()
    assert source_run.health is SourceHealth.FAILED
    assert source_run.diagnostic == "request_failed"


def test_collect_scrapecreators_normalizes_items():
    session = FakeSession(
        {
            "posts": [
                {
                    "url": "https://reddit.com/r/test",
                    "title": "Kitchen storage pain",
                    "text": "hard to clean",
                    "likes": 5,
                }
            ]
        }
    )

    source_run = collect_scrapecreators("reddit", "kitchen storage", "key", session=session)

    assert source_run.health is SourceHealth.OK
    assert source_run.records[0].platform == "reddit"
    assert source_run.records[0].title == "Kitchen storage pain"
    assert session.calls[0]["url"].endswith("/v1/reddit/search")
    assert session.calls[0]["kwargs"]["params"] == {"query": "kitchen storage"}


def test_collect_scrapecreators_uses_tiktok_endpoint_and_response_list():
    session = FakeSession(
        {
            "search_item_list": [
                {
                    "aweme_info": {
                        "share_url": "https://www.tiktok.com/@a/video/1",
                        "desc": "hard to clean organizer",
                        "author": {"nickname": "tester"},
                        "statistics": {"digg_count": 8, "comment_count": 2},
                    }
                }
            ]
        }
    )

    source_run = collect_scrapecreators("tiktok", "organizer", "key", session=session)

    assert source_run.health is SourceHealth.OK
    assert source_run.records[0].url == "https://www.tiktok.com/@a/video/1"
    assert source_run.records[0].text == "hard to clean organizer"
    assert session.calls[0]["url"].endswith("/v1/tiktok/search/keyword")
    assert session.calls[0]["kwargs"]["params"] == {"query": "organizer"}


def test_collect_scrapecreators_marks_records_without_evidence_as_partial():
    session = FakeSession({"videos": [{"title": "Missing URL"}]})

    source_run = collect_scrapecreators("youtube", "organizer", "key", session=session)

    assert source_run.health is SourceHealth.PARTIAL
    assert source_run.records == ()
    assert source_run.fetched_count == 1


def test_collect_scrapecreators_returns_failed_on_http_failure():
    class FailingSession:
        def get(self, url, **kwargs):
            return RaisingResponse()

    source_run = collect_scrapecreators(
        "reddit",
        "kitchen storage",
        "key",
        session=FailingSession(),
    )

    assert source_run.records == ()
    assert source_run.health is SourceHealth.FAILED
