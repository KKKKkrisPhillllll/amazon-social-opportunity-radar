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
        keyword="厨房收纳",
    )

    assert record.platform == "xiaohongshu"
    assert record.keyword == "厨房收纳"
    assert record.url == "https://example.com/post/1"
    assert record.title == "Small kitchen storage idea"
    assert record.engagement["likes"] == 120
    assert record.comments == ["I need this for spices"]
    assert record.health is SourceHealth.OK


def test_normalize_social_record_preserves_explicit_zero_engagement_values():
    record = normalize_social_record(
        {
            "likes": 0,
            "like_count": 5,
            "favorites": 0,
            "collect_count": 7,
            "comment_count": 0,
            "comments": ["alias should not override explicit zero"],
        },
        platform="xiaohongshu",
        keyword="厨房收纳",
    )

    assert record.engagement["likes"] == 0
    assert record.engagement["favorites"] == 0
    assert record.engagement["comments"] == 0


def test_normalize_social_record_maps_apify_rednote_fields():
    record = normalize_social_record(
        {
            "postUrl": "https://www.xiaohongshu.com/explore/abc",
            "title": "小厨房收纳",
            "content": "台面太乱，希望更省空间。",
            "authorName": "厨房用户",
            "publishedAt": "2026-07-15T08:00:00Z",
            "likes": 18,
            "saves": 7,
            "comments": [
                {"content": "希望容易清洗"},
                {"content": "安装不要打孔"},
            ],
        },
        platform="xiaohongshu",
        keyword="厨房收纳",
    )

    assert record.url == "https://www.xiaohongshu.com/explore/abc"
    assert record.text == "台面太乱，希望更省空间。"
    assert record.author == "厨房用户"
    assert record.published_at == "2026-07-15T08:00:00Z"
    assert record.engagement == {"likes": 18, "favorites": 7, "comments": 2}
    assert record.comments == ["希望容易清洗", "安装不要打孔"]


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
