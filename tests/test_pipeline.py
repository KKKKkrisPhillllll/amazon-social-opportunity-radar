from radar.models import SocialRecord, SourceHealth
from radar.pipeline import run_real_pipeline


def keyword_settings():
    return {
        "focus_categories": ["kitchen_storage", "home_storage"],
        "keyword_groups": {
            "kitchen_storage": ["厨房收纳"],
            "home_storage": ["家居收纳"],
        },
    }


def source_settings():
    return {
        "apify": {
            "enabled": True,
            "token_env": "APIFY_TOKEN",
            "xiaohongshu_actor": "zhorex/rednote-xiaohongshu-scraper",
            "max_results": 10,
            "include_comments": True,
        },
        "scrapecreators": {
            "enabled": True,
            "api_key_env": "SCRAPECREATORS_API_KEY",
            "platforms": ["instagram", "reddit"],
        },
        "collection": {"max_keywords_per_group": 1},
    }


def social_record(platform: str, keyword: str) -> SocialRecord:
    return SocialRecord(
        platform=platform,
        keyword=keyword,
        url=f"https://example.com/{platform}/{keyword}",
        title=f"{keyword} 产品痛点",
        text="hard to clean and takes too much space",
        engagement={"likes": 40, "favorites": 10, "comments": 4},
    )


def test_run_real_pipeline_does_not_call_apify_without_token():
    def forbidden_apify(*args, **kwargs):
        raise AssertionError("Apify must not be called without a token")

    settings = source_settings()
    settings["scrapecreators"]["enabled"] = False

    result = run_real_pipeline(
        keyword_settings(),
        settings,
        environ={},
        apify_collector=forbidden_apify,
    )

    assert result.source_health["xiaohongshu"] is SourceHealth.NOT_CONFIGURED
    assert result.social_records == []
    assert result.opportunities == []


def test_run_real_pipeline_does_not_call_scrapecreators_without_key():
    def forbidden_social(*args, **kwargs):
        raise AssertionError("ScrapeCreators must not be called without an API key")

    settings = source_settings()
    settings["apify"]["enabled"] = False

    result = run_real_pipeline(
        keyword_settings(),
        settings,
        environ={},
        social_collector=forbidden_social,
    )

    assert result.source_health["instagram"] is SourceHealth.NOT_CONFIGURED
    assert result.source_health["reddit"] is SourceHealth.NOT_CONFIGURED
    assert result.source_health["scrapecreators"] is SourceHealth.NOT_CONFIGURED


def test_run_real_pipeline_keeps_successful_records_when_one_platform_fails():
    settings = source_settings()
    settings["apify"]["enabled"] = False

    def fake_social(platform, keyword, api_key):
        assert api_key == "secret"
        if platform == "instagram":
            return [social_record(platform, keyword)], SourceHealth.OK
        return [], SourceHealth.FAILED

    result = run_real_pipeline(
        keyword_settings(),
        settings,
        environ={"SCRAPECREATORS_API_KEY": "secret"},
        social_collector=fake_social,
    )

    assert len(result.social_records) == 2
    assert result.source_health["instagram"] is SourceHealth.OK
    assert result.source_health["reddit"] is SourceHealth.FAILED
    assert result.source_health["scrapecreators"] is SourceHealth.PARTIAL
    assert {item.category for item in result.opportunities} == {"kitchen_storage", "home_storage"}


def test_run_real_pipeline_passes_apify_limits_and_builds_evidence_based_opportunity():
    settings = source_settings()
    settings["scrapecreators"]["enabled"] = False
    calls = []

    def fake_apify(keyword, token, actor, max_results, include_comments):
        calls.append((keyword, token, actor, max_results, include_comments))
        if keyword == "厨房收纳":
            return [social_record("xiaohongshu", keyword)], SourceHealth.OK
        return [], SourceHealth.PARTIAL

    result = run_real_pipeline(
        keyword_settings(),
        settings,
        environ={"APIFY_TOKEN": "token"},
        apify_collector=fake_apify,
    )

    assert calls[0] == (
        "厨房收纳",
        "token",
        "zhorex/rednote-xiaohongshu-scraper",
        10,
        True,
    )
    assert result.source_health["xiaohongshu"] is SourceHealth.PARTIAL
    assert [item.category for item in result.opportunities] == ["kitchen_storage"]


def test_run_real_pipeline_does_not_invent_opportunities_when_sources_are_empty():
    settings = source_settings()
    settings["apify"]["enabled"] = False

    def empty_social(platform, keyword, api_key):
        return [], SourceHealth.PARTIAL

    result = run_real_pipeline(
        keyword_settings(),
        settings,
        environ={"SCRAPECREATORS_API_KEY": "secret"},
        social_collector=empty_social,
    )

    assert result.social_records == []
    assert result.opportunities == []
