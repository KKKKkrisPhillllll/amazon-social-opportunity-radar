from __future__ import annotations

from radar.models import ReviewRecord, SocialRecord


def build_sample_records() -> tuple[list[SocialRecord], list[ReviewRecord]]:
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="kitchen storage",
            url="https://example.com/xhs/kitchen-storage",
            title="Small kitchen storage helper",
            text=(
                "Spice jars take too much space on the counter, and this organizer "
                "idea looks more space saving."
            ),
            engagement={"likes": 320, "favorites": 140, "comments": 42},
            comments=[
                "Is it hard to clean?",
                "I regret buying a similar one.",
                "Does it have a wider version?",
            ],
        )
    ]
    review_records = [
        ReviewRecord(
            asin="B012345678",
            rating=2,
            title="Hard to clean",
            review_text="It saves space, but it is hard to clean and feels unstable.",
            verified=True,
            source_script="sample",
            raw_source_path="sample",
        )
    ]
    return social_records, review_records
