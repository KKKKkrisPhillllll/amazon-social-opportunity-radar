from __future__ import annotations

from radar.models import ReviewRecord, SocialRecord


def build_sample_records() -> tuple[list[SocialRecord], list[ReviewRecord]]:
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="厨房收纳",
            url="https://example.com/xhs/kitchen-storage",
            title="小厨房调料收纳痛点",
            text=(
                "调料罐占用台面，现有收纳架难清洗，用户希望更省空间且可拆洗。"
            ),
            engagement={"likes": 320, "favorites": 140, "comments": 42},
            comments=[
                "清洗会不会很麻烦？",
                "买过类似款，后来闲置了。",
                "有没有更宽的版本？",
            ],
        )
    ]
    review_records = [
        ReviewRecord(
            asin="B012345678",
            rating=2,
            title="难清洗且不稳",
            review_text="产品能节省空间，但难清洗，而且不够稳定。",
            verified=True,
            source_script="sample",
            raw_source_path="sample",
        )
    ]
    return social_records, review_records
