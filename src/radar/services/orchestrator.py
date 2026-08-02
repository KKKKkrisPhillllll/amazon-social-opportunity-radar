from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import Any

from radar.collectors.amazon_reviews import collect_amazon_reviews
from radar.collectors.apify_xiaohongshu import collect_xiaohongshu
from radar.collectors.praw_reddit import collect_praw_reddit
from radar.collectors.scrapecreators import collect_scrapecreators
from radar.config import optional_env
from radar.dedup import record_identity
from radar.models import ReviewRecord, SocialRecord, SourceHealth, SourceRun


def _source_not_configured(source_name: str, platform: str) -> SourceRun:
    return SourceRun(
        source_name, platform, (), SourceHealth.NOT_CONFIGURED, 0, diagnostic="missing_credentials"
    )


def _is_enabled(settings: Mapping[str, Any]) -> bool:
    return bool(settings.get("enabled", True))


def _required_settings(settings: Mapping[str, Any], *names: str) -> list[str] | None:
    values = [optional_env(str(settings.get(name, ""))) for name in names]
    return values if all(values) else None


def _deduplicate_source_run(source_run: SourceRun, seen: set[tuple[str, ...]]) -> SourceRun:
    unique: list[SocialRecord] = []
    duplicate_count = 0
    for record in source_run.records:
        identity = record_identity(record)
        if identity in seen:
            duplicate_count += 1
            continue
        seen.add(identity)
        unique.append(record)
    if not duplicate_count:
        return source_run
    diagnostic = source_run.diagnostic or "ok"
    return replace(
        source_run,
        records=tuple(unique),
        duplicate_count=source_run.duplicate_count + duplicate_count,
        diagnostic=f"{diagnostic};deduplicated",
    )


def run_configured_sources(
    source_settings: Mapping[str, Any],
    keyword_groups: Mapping[str, list[str]],
    *,
    max_keywords_per_category: int,
    amazon_review_asin: str | None = None,
    session=None,
    reddit_factory=None,
    runner=None,
    collectors: Mapping[str, Callable[..., SourceRun]] | None = None,
) -> tuple[dict[str, list[SocialRecord]], list[ReviewRecord], list[SourceRun]]:
    if max_keywords_per_category < 1:
        raise ValueError("max_keywords_per_category must be at least 1")
    collector_map = {
        "apify": collect_xiaohongshu,
        "scrapecreators": collect_scrapecreators,
        "praw_reddit": collect_praw_reddit,
    }
    collector_map.update(collectors or {})
    records_by_category = {category: [] for category in keyword_groups}
    source_runs: list[SourceRun] = []
    apify_settings = source_settings.get("apify", {})
    scrape_settings = source_settings.get("scrapecreators", {})
    praw_settings = source_settings.get("praw_reddit", {})
    seen: set[tuple[str, ...]] = set()

    for category, keywords in keyword_groups.items():
        for keyword in keywords[:max_keywords_per_category]:
            if _is_enabled(apify_settings):
                apify_token = _required_settings(apify_settings, "token_env")
                if apify_token:
                    source_run = collector_map["apify"](
                        keyword=keyword,
                        token=apify_token[0],
                        actor=str(apify_settings.get("xiaohongshu_actor", "")),
                        max_results=int(apify_settings.get("max_results", 20)),
                        session=session,
                    )
                else:
                    source_run = _source_not_configured("apify_xiaohongshu", "xiaohongshu")
                source_run = _deduplicate_source_run(source_run, seen)
                source_runs.append(source_run)
                records_by_category[category].extend(source_run.records)

            platforms = scrape_settings.get("platforms", []) if _is_enabled(scrape_settings) else []
            for platform in platforms:
                scrape_key = _required_settings(scrape_settings, "api_key_env")
                if scrape_key:
                    source_run = collector_map["scrapecreators"](
                        platform=platform,
                        keyword=keyword,
                        api_key=scrape_key[0],
                        session=session,
                    )
                else:
                    source_run = _source_not_configured(f"scrapecreators_{platform}", platform)
                source_run = _deduplicate_source_run(source_run, seen)
                source_runs.append(source_run)
                records_by_category[category].extend(source_run.records)

                if platform != "reddit" or source_run.health not in {
                    SourceHealth.FAILED,
                    SourceHealth.NOT_CONFIGURED,
                }:
                    continue
                praw_credentials = _required_settings(
                    praw_settings, "client_id_env", "client_secret_env", "user_agent_env"
                )
                if not _is_enabled(praw_settings) or not praw_credentials:
                    fallback = _source_not_configured("praw_reddit", "reddit")
                else:
                    fallback = collector_map["praw_reddit"](
                        keyword=keyword,
                        client_id=praw_credentials[0],
                        client_secret=praw_credentials[1],
                        user_agent=praw_credentials[2],
                        max_results=int(praw_settings.get("max_results", 20)),
                        reddit_factory=reddit_factory,
                    )
                    if fallback.health in {SourceHealth.OK, SourceHealth.PARTIAL}:
                        fallback = replace(fallback, health=SourceHealth.DEGRADED)
                fallback = _deduplicate_source_run(fallback, seen)
                source_runs.append(fallback)
                records_by_category[category].extend(fallback.records)

    review_records: list[ReviewRecord] = []
    if amazon_review_asin:
        amazon_settings = source_settings.get("amazon_reviews", {})
        primary_script = optional_env(str(amazon_settings.get("primary_script_env", "")))
        backup_script = optional_env(str(amazon_settings.get("backup_script_env", "")))
        if primary_script or backup_script:
            review_records, health = collect_amazon_reviews(
                amazon_review_asin,
                Path(primary_script) if primary_script else Path("__missing_primary_script__.py"),
                Path(backup_script) if backup_script else Path("__missing_backup_script__.py"),
                runner=runner,
            )
            source_runs.append(
                SourceRun(
                    "amazon_reviews",
                    "amazon",
                    (),
                    health,
                    len(review_records),
                    diagnostic="ok" if health is not SourceHealth.FAILED else "collection_failed",
                )
            )
        else:
            source_runs.append(_source_not_configured("amazon_reviews", "amazon"))
    return records_by_category, review_records, source_runs
