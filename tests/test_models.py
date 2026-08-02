import pytest

from radar.models import SocialRecord, SourceHealth, SourceRun


def _record() -> SocialRecord:
    return SocialRecord(
        platform="reddit",
        keyword="kitchen storage",
        url="https://www.reddit.com/r/example/1",
        title="Example",
        text="Useful evidence",
    )


def test_source_run_rejects_negative_counts():
    with pytest.raises(ValueError, match="fetched_count"):
        SourceRun(
            source_name="reddit",
            platform="reddit",
            records=(),
            health=SourceHealth.OK,
            fetched_count=-1,
        )


def test_source_run_rejects_duplicate_count_above_fetched_count():
    with pytest.raises(ValueError, match="duplicate_count"):
        SourceRun(
            source_name="reddit",
            platform="reddit",
            records=(_record(),),
            health=SourceHealth.OK,
            fetched_count=1,
            duplicate_count=2,
        )


def test_source_run_keeps_safe_diagnostic_and_counts():
    source_run = SourceRun(
        source_name="reddit",
        platform="reddit",
        records=(_record(),),
        health=SourceHealth.OK,
        fetched_count=1,
        duplicate_count=0,
        diagnostic="ok",
    )

    assert source_run.records[0].platform == "reddit"
    assert source_run.diagnostic == "ok"
