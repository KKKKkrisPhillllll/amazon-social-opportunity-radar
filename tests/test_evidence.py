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


def test_evidence_index_deduplicates_normalized_urls():
    records = [
        _record(" https://REDDIT.example/first/#fragment ", title=" first "),
        _record("https://reddit.example/first", title="duplicate"),
        _record("http://reddit.example/second", title=" second "),
    ]

    index = build_evidence_index({"kitchen_storage": records}, [])

    assert [item.url for item in index.by_category["kitchen_storage"]] == [
        "http://reddit.example/second",
        "https://reddit.example/first",
    ]


def test_evidence_ids_are_stable_when_records_and_categories_are_reordered():
    records = {
        "kitchen_storage": [_record("https://reddit.example/b")],
        "kitchen_appliances": [_record("https://reddit.example/a")],
    }
    reordered = {
        "kitchen_appliances": list(reversed(records["kitchen_appliances"])),
        "kitchen_storage": list(reversed(records["kitchen_storage"])),
    }

    first = build_evidence_index(records, [])
    second = build_evidence_index(reordered, [])

    first_ids = {(item.category, item.url): item.evidence_id for item in first.by_id.values()}
    second_ids = {(item.category, item.url): item.evidence_id for item in second.by_id.values()}
    assert first_ids == second_ids


def test_evidence_item_keeps_only_anonymous_aggregate_fields():
    record = _record(
        "https://reddit.example/post-1",
        title="标题",
        text="正文",
        comments=["private comment", "another private comment"],
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

    assert item.summary == "标题 正文"
    assert item.comment_count == 2
    assert set(item.__dataclass_fields__) == {
        "evidence_id",
        "platform",
        "url",
        "category",
        "summary",
        "comment_count",
        "asin",
    }
    assert not hasattr(item, "author")
    assert not hasattr(item, "comments")


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


def test_public_url_rejects_local_or_credential_bearing_urls():
    invalid_urls = [
        "",
        "   ",
        "ftp://reddit.example/post",
        "https://localhost/post",
        "https://localhost.localdomain/post",
        "https://127.0.0.1/post",
        "https://10.0.0.2/post",
        "https://172.16.0.2/post",
        "https://192.168.1.2/post",
        "https://169.254.10.2/post",
        "https://0.0.0.0/post",
        "https://[::1]/post",
        "https://user:password@reddit.example/post",
    ]

    index = build_evidence_index(
        {"kitchen_storage": [_record(url) for url in invalid_urls]}, []
    )

    assert index.by_category["kitchen_storage"] == ()


def test_public_url_accepts_http_https_public_hosts():
    records = [_record("https://reddit.example/post"), _record("http://8.8.8.8/post")]

    index = build_evidence_index({"kitchen_storage": records}, [])

    assert len(index.by_category["kitchen_storage"]) == 2
