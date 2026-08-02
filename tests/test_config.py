from pathlib import Path

import pytest

from radar.config import load_keywords, load_source_settings, optional_env, require_env


def test_load_keywords_contains_v1_categories():
    data = load_keywords(Path("config/keywords.yaml"))

    assert data["marketplace"] == "amazon_us"
    assert "kitchen_appliances" in data["keyword_groups"]
    assert "kitchen_storage" in data["keyword_groups"]
    assert "pain_keywords" in data["keyword_groups"]
    assert "厨房收纳" in data["keyword_groups"]["kitchen_storage"]


def test_load_source_settings_uses_environment_variable_names_only():
    data = load_source_settings(Path("config/sources.example.yaml"))

    assert data["feishu"]["webhook_env"] == "FEISHU_WEBHOOK_URL"
    assert data["apify"]["token_env"] == "APIFY_TOKEN"
    assert data["scrapecreators"]["api_key_env"] == "SCRAPECREATORS_API_KEY"
    assert data["amazon_reviews"]["primary_script_env"] == "AMAZON_REVIEW_PRIMARY_SCRIPT"
    assert data["amazon_reviews"]["backup_script_env"] == "AMAZON_REVIEW_BACKUP_SCRIPT"
    assert data["praw_reddit"]["client_id_env"] == "REDDIT_CLIENT_ID"


def test_require_env_raises_clear_error(monkeypatch):
    monkeypatch.delenv("FEISHU_WEBHOOK_URL", raising=False)

    with pytest.raises(RuntimeError, match="FEISHU_WEBHOOK_URL"):
        require_env("FEISHU_WEBHOOK_URL")


def test_require_env_returns_value(monkeypatch):
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://example.feishu/webhook")

    assert require_env("FEISHU_WEBHOOK_URL") == "https://example.feishu/webhook"


def test_optional_env_returns_none_when_value_is_missing(monkeypatch):
    monkeypatch.delenv("OPTIONAL_VALUE", raising=False)

    assert optional_env("OPTIONAL_VALUE") is None


def test_optional_env_strips_value(monkeypatch):
    monkeypatch.setenv("OPTIONAL_VALUE", "  configured  ")

    assert optional_env("OPTIONAL_VALUE") == "configured"
