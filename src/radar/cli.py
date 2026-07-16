from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

from radar.collectors.amazon_reviews import collect_amazon_reviews
from radar.collectors.sample import build_sample_records
from radar.config import load_source_settings, require_env
from radar.integrations.feishu import send_feishu_markdown
from radar.models import SourceHealth
from radar.reports import build_amazon_review_markdown, build_daily_markdown
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
    parser.add_argument("--amazon-review-asin")
    parser.add_argument("--source-config", default="config/sources.example.yaml")
    parser.add_argument("--output-dir", default="outputs")
    parser.add_argument("--report-date", default=date.today().isoformat())
    return parser


def _run_amazon_review_first_run(args: argparse.Namespace, asin: str) -> int:
    source_settings = load_source_settings(args.source_config)
    review_settings = source_settings["amazon_reviews"]
    reviews, health = collect_amazon_reviews(
        asin=asin,
        primary_script=Path(review_settings["primary_script"]),
        backup_script=Path(review_settings["backup_script"]),
    )
    markdown = build_amazon_review_markdown(
        asin=asin,
        reviews=reviews,
        health=health,
        report_date=args.report_date,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"amazon_review_report_{asin}_{args.report_date.replace('-', '')}.md"
    report_path.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"报告已写入：{report_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.amazon_review_asin:
        if args.use_sample_data:
            parser.error("--amazon-review-asin 不能与 --use-sample-data 同时使用")
        if not args.dry_run:
            parser.error("--amazon-review-asin 首跑必须使用 --dry-run")
        asin = args.amazon_review_asin.upper()
        if not re.fullmatch(r"[A-Z0-9]{10}", asin):
            parser.error("--amazon-review-asin 必须是 10 位字母数字 ASIN")
        return _run_amazon_review_first_run(args, asin)
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
