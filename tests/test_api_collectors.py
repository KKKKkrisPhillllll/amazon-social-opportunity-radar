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


def test_collect_scrapecreators_normalizes_items():
    session = FakeSession(
        {
            "items": [
                {
                    "url": "https://reddit.com/r/test",
                    "title": "Kitchen storage pain",
                    "text": "hard to clean",
                    "likes": 5,
                }
            ]
        }
    )

    records, health = collect_scrapecreators("reddit", "kitchen storage", "key", session=session)

    assert health is SourceHealth.OK
    assert records[0].platform == "reddit"
    assert records[0].title == "Kitchen storage pain"
