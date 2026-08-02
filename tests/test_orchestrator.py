from radar.models import SocialRecord, SourceHealth, SourceRun
from radar.services.orchestrator import run_configured_sources


def _settings() -> dict:
    return {
        "apify": {"enabled": True, "token_env": "APIFY_TOKEN", "xiaohongshu_actor": "actor"},
        "scrapecreators": {
            "enabled": True,
            "api_key_env": "SCRAPECREATORS_API_KEY",
            "platforms": ["reddit"],
        },
        "praw_reddit": {
            "enabled": True,
            "client_id_env": "REDDIT_CLIENT_ID",
            "client_secret_env": "REDDIT_CLIENT_SECRET",
            "user_agent_env": "REDDIT_USER_AGENT",
        },
        "amazon_reviews": {
            "primary_script_env": "AMAZON_REVIEW_PRIMARY_SCRIPT",
            "backup_script_env": "AMAZON_REVIEW_BACKUP_SCRIPT",
        },
    }


def test_run_configured_sources_returns_not_configured_without_credentials(monkeypatch):
    for name in (
        "APIFY_TOKEN",
        "SCRAPECREATORS_API_KEY",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
    ):
        monkeypatch.delenv(name, raising=False)

    records_by_category, review_records, source_runs = run_configured_sources(
        _settings(), {"kitchen_storage": ["kitchen storage"]}, max_keywords_per_category=1
    )

    assert records_by_category == {"kitchen_storage": []}
    assert review_records == []
    assert {item.health for item in source_runs} == {SourceHealth.NOT_CONFIGURED}


def test_run_configured_sources_deduplicates_results_and_uses_praw_fallback(monkeypatch):
    monkeypatch.setenv("APIFY_TOKEN", "token")
    monkeypatch.delenv("SCRAPECREATORS_API_KEY", raising=False)
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("REDDIT_USER_AGENT", "agent")
    shared = SocialRecord(
        platform="xiaohongshu",
        keyword="kitchen storage",
        url="https://example.com/post/1",
        title="Storage pain",
        text="hard to clean",
    )

    def apify_collector(**kwargs):
        return SourceRun("apify_xiaohongshu", "xiaohongshu", (shared, shared), SourceHealth.OK, 2)

    def scrape_collector(**kwargs):
        return SourceRun("scrapecreators_reddit", "reddit", (), SourceHealth.FAILED, 0)

    def praw_collector(**kwargs):
        return SourceRun("praw_reddit", "reddit", (), SourceHealth.PARTIAL, 0)

    records_by_category, _, source_runs = run_configured_sources(
        _settings(),
        {"kitchen_storage": ["kitchen storage"]},
        max_keywords_per_category=1,
        collectors={
            "apify": apify_collector,
            "scrapecreators": scrape_collector,
            "praw_reddit": praw_collector,
        },
    )

    assert len(records_by_category["kitchen_storage"]) == 1
    assert any(item.duplicate_count == 1 for item in source_runs)
    assert any(item.source_name == "praw_reddit" and item.health is SourceHealth.DEGRADED for item in source_runs)


def test_run_configured_sources_keeps_failed_praw_fallback_as_failed(monkeypatch):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    monkeypatch.delenv("SCRAPECREATORS_API_KEY", raising=False)
    monkeypatch.setenv("REDDIT_CLIENT_ID", "id")
    monkeypatch.setenv("REDDIT_CLIENT_SECRET", "secret")
    monkeypatch.setenv("REDDIT_USER_AGENT", "agent")

    def praw_collector(**kwargs):
        return SourceRun("praw_reddit", "reddit", (), SourceHealth.FAILED, 0)

    _, _, source_runs = run_configured_sources(
        _settings(),
        {"kitchen_storage": ["kitchen storage"]},
        max_keywords_per_category=1,
        collectors={"praw_reddit": praw_collector},
    )

    assert any(item.source_name == "praw_reddit" and item.health is SourceHealth.FAILED for item in source_runs)


def test_run_configured_sources_allows_backup_review_script_without_primary(monkeypatch, tmp_path):
    backup_script = tmp_path / "backup.py"
    backup_script.write_text("", encoding="utf-8")
    monkeypatch.delenv("AMAZON_REVIEW_PRIMARY_SCRIPT", raising=False)
    monkeypatch.setenv("AMAZON_REVIEW_BACKUP_SCRIPT", str(backup_script))
    settings = _settings()
    settings["apify"]["enabled"] = False
    settings["scrapecreators"]["enabled"] = False

    class Completed:
        returncode = 0
        stdout = '[{"asin":"B012345678","rating":2,"title":"Bad","review_text":"Hard to clean"}]'
        stderr = ""

    _, reviews, source_runs = run_configured_sources(
        settings,
        {"kitchen_storage": ["kitchen storage"]},
        max_keywords_per_category=1,
        amazon_review_asin="B012345678",
        runner=lambda *args, **kwargs: Completed(),
    )

    assert reviews[0].source_script == "backup"
    assert source_runs[-1].health is SourceHealth.DEGRADED
