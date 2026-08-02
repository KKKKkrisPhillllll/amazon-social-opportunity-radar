from radar.dedup import deduplicate_social_records
from radar.models import SocialRecord


def _record(url: str, title: str = "Title", text: str = "Body") -> SocialRecord:
    return SocialRecord(
        platform="reddit",
        keyword="kitchen storage",
        url=url,
        title=title,
        text=text,
    )


def test_deduplicate_social_records_normalizes_trailing_slash_urls():
    records, duplicate_count = deduplicate_social_records(
        [_record("https://example.com/post/1/"), _record("https://example.com/post/1")]
    )

    assert len(records) == 1
    assert duplicate_count == 1


def test_deduplicate_social_records_uses_content_fallback_when_url_is_missing():
    records, duplicate_count = deduplicate_social_records(
        [_record("", "Same title", "Same body"), _record("", "Same title", "Same body")]
    )

    assert len(records) == 1
    assert duplicate_count == 1
