from radar.models import SourceHealth
from radar.normalizers import normalize_review_record, normalize_social_record


def test_normalize_social_record_maps_common_fields():
    record = normalize_social_record(
        {
            "url": "https://example.com/post/1",
            "title": "Small kitchen storage idea",
            "text": "Hard to clean but saves space",
            "likes": 120,
            "comments": [{"text": "I need this for spices"}],
        },
        platform="xiaohongshu",
        keyword="鍘ㄦ埧鏀剁撼",
    )

    assert record.platform == "xiaohongshu"
    assert record.keyword == "鍘ㄦ埧鏀剁撼"
    assert record.url == "https://example.com/post/1"
    assert record.title == "Small kitchen storage idea"
    assert record.engagement["likes"] == 120
    assert record.comments == ["I need this for spices"]
    assert record.health is SourceHealth.OK


def test_normalize_review_record_maps_review_fields():
    record = normalize_review_record(
        {
            "asin": "B012345678",
            "rating": 2,
            "title": "Hard to clean",
            "review_text": "The product works but cleaning is painful.",
            "date": "2026-07-01",
            "verified": True,
            "helpful": 8,
        },
        source_script="primary",
        raw_source_path="reviews.json",
    )

    assert record.asin == "B012345678"
    assert record.rating == 2.0
    assert record.title == "Hard to clean"
    assert record.verified is True
    assert record.source_script == "primary"
