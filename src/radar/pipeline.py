from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from radar.collectors.apify_xiaohongshu import collect_xiaohongshu
from radar.collectors.scrapecreators import collect_scrapecreators
from radar.models import Opportunity, SocialRecord, SourceHealth
from radar.scoring import score_opportunity


@dataclass(frozen=True)
class DailyPipelineResult:
    social_records: list[SocialRecord]
    opportunities: list[Opportunity]
    source_health: dict[str, SourceHealth]


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _aggregate_health(statuses: list[SourceHealth]) -> SourceHealth:
    if not statuses or all(status is SourceHealth.NOT_CONFIGURED for status in statuses):
        return SourceHealth.NOT_CONFIGURED
    if all(status is SourceHealth.OK for status in statuses):
        return SourceHealth.OK
    if all(status is SourceHealth.FAILED for status in statuses):
        return SourceHealth.FAILED
    return SourceHealth.PARTIAL


def _collect_safely(
    collector: Callable[..., tuple[list[SocialRecord], SourceHealth]],
    *args: Any,
    **kwargs: Any,
) -> tuple[list[SocialRecord], SourceHealth]:
    try:
        records, health = collector(*args, **kwargs)
    except Exception:
        return [], SourceHealth.FAILED
    return list(records), health


def run_real_pipeline(
    keyword_settings: dict[str, Any],
    source_settings: dict[str, Any],
    *,
    environ: Mapping[str, str] | None = None,
    apify_collector: Callable[..., tuple[list[SocialRecord], SourceHealth]] = collect_xiaohongshu,
    social_collector: Callable[..., tuple[list[SocialRecord], SourceHealth]] = collect_scrapecreators,
) -> DailyPipelineResult:
    environment = os.environ if environ is None else environ
    focus_categories = _string_list(keyword_settings.get("focus_categories"))
    keyword_groups = _mapping(keyword_settings.get("keyword_groups"))
    collection_settings = _mapping(source_settings.get("collection"))
    keyword_limit = _positive_int(collection_settings.get("max_keywords_per_group"), 1)
    category_keywords = {
        category: _string_list(keyword_groups.get(category))[:keyword_limit]
        for category in focus_categories
    }
    category_records: dict[str, list[SocialRecord]] = {
        category: [] for category in focus_categories
    }
    source_health: dict[str, SourceHealth] = {
        "amazon_reviews": SourceHealth.NOT_CONFIGURED,
    }

    apify_settings = _mapping(source_settings.get("apify"))
    apify_enabled = bool(apify_settings.get("enabled", True))
    apify_token_name = str(apify_settings.get("token_env", "APIFY_TOKEN"))
    apify_token = str(environment.get(apify_token_name, "")).strip()
    if not apify_enabled or not apify_token:
        source_health["xiaohongshu"] = SourceHealth.NOT_CONFIGURED
    else:
        actor = str(apify_settings.get("xiaohongshu_actor", "")).strip()
        max_results = _positive_int(apify_settings.get("max_results"), 20)
        include_comments = bool(apify_settings.get("include_comments", True))
        statuses: list[SourceHealth] = []
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                records, health = _collect_safely(
                    apify_collector,
                    keyword,
                    apify_token,
                    actor,
                    max_results=max_results,
                    include_comments=include_comments,
                )
                category_records[category].extend(records)
                statuses.append(health)
        source_health["xiaohongshu"] = _aggregate_health(statuses)

    social_settings = _mapping(source_settings.get("scrapecreators"))
    social_enabled = bool(social_settings.get("enabled", True))
    platforms = [item.lower() for item in _string_list(social_settings.get("platforms"))]
    api_key_name = str(social_settings.get("api_key_env", "SCRAPECREATORS_API_KEY"))
    api_key = str(environment.get(api_key_name, "")).strip()
    platform_health: dict[str, SourceHealth] = {}
    if not social_enabled or not api_key:
        platform_health = {platform: SourceHealth.NOT_CONFIGURED for platform in platforms}
    else:
        for platform in platforms:
            statuses = []
            for category, keywords in category_keywords.items():
                for keyword in keywords:
                    records, health = _collect_safely(
                        social_collector,
                        platform,
                        keyword,
                        api_key,
                    )
                    category_records[category].extend(records)
                    statuses.append(health)
            platform_health[platform] = _aggregate_health(statuses)
    source_health.update(platform_health)
    source_health["scrapecreators"] = _aggregate_health(list(platform_health.values()))

    social_records = [
        record
        for category in focus_categories
        for record in category_records.get(category, [])
    ]
    opportunities = [
        score_opportunity(
            social_records=category_records[category],
            review_records=[],
            category=category,
            keywords=category_keywords[category],
        )
        for category in focus_categories
        if category_records.get(category)
    ]
    return DailyPipelineResult(
        social_records=social_records,
        opportunities=opportunities,
        source_health=source_health,
    )
