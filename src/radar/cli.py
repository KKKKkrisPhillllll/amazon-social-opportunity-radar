from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from radar.collectors.sample import build_sample_records
from radar.config import load_keywords, load_source_settings, require_env
from radar.integrations.feishu import send_feishu_markdown
from radar.models import SourceHealth
from radar.pipeline import run_real_pipeline
from radar.reports import build_daily_markdown
from radar.scoring import score_opportunity


_PROJECT_ROOT = Path(__file__).resolve().parents[2]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Amazon Social Opportunity Radar")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report instead of sending to Feishu.",
    )
    parser.add_argument(
        "--use-sample-data",
        action="store_true",
        help="Use deterministic sample data.",
    )
    parser.add_argument("--report-date", default=date.today().isoformat())
    parser.add_argument(
        "--keywords-config",
        default=str(_PROJECT_ROOT / "config" / "keywords.yaml"),
    )
    parser.add_argument(
        "--sources-config",
        default=str(_PROJECT_ROOT / "config" / "sources.example.yaml"),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    keyword_settings = load_keywords(args.keywords_config)
    source_settings = load_source_settings(args.sources_config)

    webhook_url = ""
    if not args.dry_run:
        webhook_env = str(source_settings["feishu"].get("webhook_env", "FEISHU_WEBHOOK_URL"))
        webhook_url = require_env(webhook_env)

    if args.use_sample_data:
        social_records, review_records = build_sample_records()
        opportunities = [
            score_opportunity(
                social_records=social_records,
                review_records=review_records,
                category="kitchen_storage",
                keywords=["kitchen organizer", "spice rack organizer"],
            )
        ]
        source_health = {
            "xiaohongshu": SourceHealth.OK,
            "scrapecreators": SourceHealth.NOT_CONFIGURED,
            "amazon_reviews": SourceHealth.OK,
        }
    else:
        result = run_real_pipeline(keyword_settings, source_settings)
        opportunities = result.opportunities
        source_health = result.source_health

    markdown = build_daily_markdown(
        opportunities=opportunities,
        source_health=source_health,
        report_date=args.report_date,
        focus=" / ".join(keyword_settings.get("focus_categories", [])),
    )
    if args.dry_run:
        print(markdown)
        return 0
    send_feishu_markdown(webhook_url, "Amazon Social Opportunity Radar", markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
