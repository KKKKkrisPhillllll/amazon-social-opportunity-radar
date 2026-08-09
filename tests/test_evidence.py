from radar.evidence import build_evidence_index
from radar.models import ReviewRecord, SocialRecord


def _record(url: str, *, title: str = "标题", text: str = "正文", comments=None) -> SocialRecord:
    return SocialRecord(
        platform="reddit",
        keyword="厨房收纳",
        url=url,
        title=title,
        text=text,
        comments=[] if comments is None else comments,
        engagement={},
    )


def test_evidence_index_filters_invalid_urls_and_keeps_stable_ids():
    record = _record(
        "https://reddit.example/post-1",
        title="小厨房台面太拥挤",
        text="台面空间太小，调料拿取不方便。",
    )
    invalid = _record("", title="无公开链接", text="只有本地内容")

    index = build_evidence_index({"kitchen_storage": [record, invalid]}, [])

    assert len(index.by_category["kitchen_storage"]) == 1
    assert index.by_category["kitchen_storage"][0].evidence_id == "E-0001"
    assert index.by_id["E-0001"].url == "https://reddit.example/post-1"


def test_evidence_index_deduplicates_urls_and_preserves_input_order():
    records = [
        _record(" https://reddit.example/first ", title=" first "),
        _record("https://reddit.example/first", title="duplicate"),
        _record("http://reddit.example/second", title=" second "),
    ]

    index = build_evidence_index({"kitchen_storage": records}, [])

    assert tuple(item.evidence_id for item in index.by_category["kitchen_storage"]) == (
        "E-0001",
        "E-0002",
    )
    assert [item.title for item in index.by_category["kitchen_storage"]] == ["first", "second"]
    assert list(index.by_id) == ["E-0001", "E-0002"]


def test_evidence_item_keeps_empty_text_and_only_public_evidence_fields():
    record = _record(
        "https://reddit.example/post-1",
        title=" ",
        text=" ",
        comments=[" useful comment ", "   "],
    )
    record = SocialRecord(
        platform=record.platform,
        keyword=record.keyword,
        url=record.url,
        title=record.title,
        text=record.text,
        author="private-user-id",
        comments=record.comments,
    )

    item = build_evidence_index({"kitchen_storage": [record]}, []).by_id["E-0001"]

    assert item.title == ""
    assert item.text == ""
    assert item.comments == ("useful comment",)
    assert set(item.__dataclass_fields__) == {
        "evidence_id",
        "platform",
        "url",
        "category",
        "title",
        "text",
        "comments",
        "asin",
    }
    assert not hasattr(item, "author")


def test_review_records_do_not_count_as_public_url_evidence():
    review = ReviewRecord(
        asin="B012345678",
        rating=2,
        title="难清洁",
        review_text="产品没有公开评论 URL。",
    )

    index = build_evidence_index({}, [review])

    assert index.by_category == {}
    assert index.by_id == {}
