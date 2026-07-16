from pathlib import Path

import pytest

from radar.config import load_keywords, load_source_settings, require_env


def test_load_keywords_contains_v1_categories():
    data = load_keywords(Path("config/keywords.yaml"))

    assert data["marketplace"] == "amazon_us"
    assert "kitchen_appliances" in data["keyword_groups"]
    assert "kitchen_storage" in data["keyword_groups"]
    assert "home_storage" in data["keyword_groups"]
    assert "pain_keywords" in data["keyword_groups"]
    assert "厨房收纳" in data["keyword_groups"]["kitchen_storage"]


def test_load_source_settings_uses_environment_variable_names_only():
    data = load_source_settings(Path("config/sources.example.yaml"))

    assert data["feishu"]["webhook_env"] == "FEISHU_WEBHOOK_URL"
    assert data["apify"]["token_env"] == "APIFY_TOKEN"
    assert data["scrapecreators"]["api_key_env"] == "SCRAPECREATORS_API_KEY"
    assert data["apify"]["enabled"] is True
    assert data["apify"]["max_results"] == 20
    assert data["apify"]["include_comments"] is True
    assert data["scrapecreators"]["enabled"] is True
    assert data["scrapecreators"]["platforms"] == ["instagram", "tiktok", "youtube", "reddit"]
    assert data["collection"]["max_keywords_per_group"] == 1


def test_require_env_raises_clear_error(monkeypatch):
    monkeypatch.delenv("FEISHU_WEBHOOK_URL", raising=False)

    with pytest.raises(RuntimeError, match="FEISHU_WEBHOOK_URL"):
        require_env("FEISHU_WEBHOOK_URL")


def test_require_env_returns_value(monkeypatch):
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://example.feishu/webhook")

    assert require_env("FEISHU_WEBHOOK_URL") == "https://example.feishu/webhook"
