from __future__ import annotations

import argparse
from datetime import date

from radar.collectors.sample import build_sample_records
from radar.config import require_env
from radar.integrations.feishu import send_feishu_markdown
from radar.models import SourceHealth
from radar.reports import build_daily_markdown
from radar.scoring import score_opportunity


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
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.use_sample_data:
        raise RuntimeError(
            "The first CLI slice requires --use-sample-data until real connectors are wired."
        )

    social_records, review_records = build_sample_records()
    opportunity = score_opportunity(
        social_records=social_records,
        review_records=review_records,
        category="kitchen_storage",
        keywords=["kitchen organizer", "spice rack organizer"],
    )
    markdown = build_daily_markdown(
        opportunities=[opportunity],
        source_health={
            "xiaohongshu": SourceHealth.OK,
            "scrapecreators": SourceHealth.NOT_CONFIGURED,
            "amazon_reviews": SourceHealth.OK,
        },
        report_date=args.report_date,
        focus="Kitchen appliances / kitchen storage / home storage",
    )
    if args.dry_run:
        print(markdown)
        return 0
    webhook_url = require_env("FEISHU_WEBHOOK_URL")
    send_feishu_markdown(webhook_url, "Amazon Social Opportunity Radar", markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
