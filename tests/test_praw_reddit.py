from prawcore.exceptions import PrawcoreException

from radar.collectors.praw_reddit import collect_praw_reddit
from radar.models import SourceHealth


class FakeSubmission:
    title = "Kitchen storage pain"
    selftext = "Hard to clean and takes too much space"
    url = "https://www.reddit.com/r/example/comments/1"
    author = "example_user"
    created_utc = 1_754_000_000
    score = 15
    num_comments = 4


class FakeSubreddit:
    def __init__(self):
        self.calls = []

    def search(self, query, limit):
        self.calls.append({"query": query, "limit": limit})
        return [FakeSubmission()]


class FakeReddit:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.subreddit_instance = FakeSubreddit()

    def subreddit(self, name):
        assert name == "all"
        return self.subreddit_instance


def test_collect_praw_reddit_uses_read_only_credentials_and_searches():
    captured = {}

    def factory(**kwargs):
        captured.update(kwargs)
        return FakeReddit(**kwargs)

    source_run = collect_praw_reddit(
        "kitchen storage",
        "client-id",
        "client-secret",
        "radar-test/1.0",
        reddit_factory=factory,
    )

    assert source_run.health is SourceHealth.OK
    assert source_run.records[0].author == "example_user"
    assert captured == {
        "client_id": "client-id",
        "client_secret": "client-secret",
        "user_agent": "radar-test/1.0",
    }


def test_collect_praw_reddit_returns_failed_when_client_errors():
    def factory(**kwargs):
        raise PrawcoreException("network failure")

    source_run = collect_praw_reddit(
        "kitchen storage", "id", "secret", "agent", reddit_factory=factory
    )

    assert source_run.health is SourceHealth.FAILED
    assert source_run.records == ()
