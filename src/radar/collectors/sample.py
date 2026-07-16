from __future__ import annotations

from radar.models import ReviewRecord, SocialRecord


def build_sample_records() -> tuple[list[SocialRecord], list[ReviewRecord]]:
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="厨房收纳",
            url="https://example.com/xhs/kitchen-storage",
            title="小厨房调料收纳方案",
            text=(
                "调料罐放在台面上太占地方，这种分层收纳方案看起来更节省空间。"
            ),
            engagement={"likes": 320, "favorites": 140, "comments": 42},
            comments=[
                "会不会很难清洗？",
                "买过类似款，稳定性不够。",
                "有没有更宽的版本？",
            ],
        )
    ]
    review_records = [
        ReviewRecord(
            asin="B012345678",
            rating=2,
            title="难清洗",
            review_text="确实节省空间，但边角难清洗，而且使用时不够稳定。",
            verified=True,
            source_script="sample",
            raw_source_path="sample",
        )
    ]
    return social_records, review_records
