from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from radar.collectors.sample import build_sample_records
from radar.config import (
    get_persona_journey_settings,
    load_keywords,
    load_source_settings,
    require_env,
)
from radar.evidence import build_evidence_index
from radar.integrations.feishu import send_feishu_markdown
from radar.journey_builder import build_journey
from radar.models import PersonaJourneyResult, SourceHealth, SourceRun
from radar.opportunity_gate import evaluate_opportunity_gate
from radar.persona_builder import build_persona
from radar.reports import build_daily_markdown
from radar.scoring import score_opportunity
from radar.services.orchestrator import run_configured_sources
from radar.voc import classify_voc, detect_innovation_signals, load_voc_config

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATEGORY_LABELS = {
    "kitchen_appliances": "厨房电器",
    "kitchen_storage": "厨房收纳",
    "home_storage": "家居收纳",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="亚马逊社媒产品机会雷达")
    send_mode = parser.add_mutually_exclusive_group()
    send_mode.add_argument("--dry-run", action="store_true", help="仅打印报告，不写文件或发送飞书。")
    send_mode.add_argument("--send-feishu", action="store_true", help="写入报告后发送到飞书机器人。")
    parser.add_argument("--use-sample-data", action="store_true", help="使用固定样例，仅验证链路。")
    parser.add_argument("--report-date", default=datetime.now(UTC).date().isoformat())
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "sources.example.yaml")
    parser.add_argument("--keywords", type=Path, default=PROJECT_ROOT / "config" / "keywords.yaml")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "outputs")
    parser.add_argument("--amazon-review-asin", help="可选：本轮需要分析的竞品 ASIN。")
    parser.add_argument("--max-keywords-per-category", type=int, default=1)
    return parser


def _selected_keyword_groups(keyword_settings: dict[str, Any]) -> dict[str, list[str]]:
    groups = keyword_settings["keyword_groups"]
    focus_categories = keyword_settings.get("focus_categories", list(groups))
    selected = {
        category: [str(keyword) for keyword in groups.get(category, []) if str(keyword).strip()]
        for category in focus_categories
        if isinstance(groups.get(category), list)
    }
    if not selected:
        raise ValueError("关键词配置没有可执行的关注类目")
    return selected


def _focus_label(keyword_groups: dict[str, list[str]]) -> str:
    return " / ".join(CATEGORY_LABELS.get(category, category) for category in keyword_groups)


def _sample_source_runs() -> tuple[dict[str, list], list, list[SourceRun]]:
    social_records, review_records = build_sample_records()
    return (
        {"kitchen_storage": social_records},
        review_records,
        [
            SourceRun(
                "sample_social",
                "sample",
                tuple(social_records),
                SourceHealth.OK,
                fetched_count=len(social_records),
                diagnostic="sample_data",
            ),
            SourceRun(
                "sample_amazon_reviews",
                "amazon",
                (),
                SourceHealth.OK,
                fetched_count=len(review_records),
                diagnostic="sample_data",
            ),
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_keywords_per_category < 1:
        parser.error("--max-keywords-per-category 必须大于等于 1")
    if args.use_sample_data and args.send_feishu:
        parser.error("样例数据不能发送到飞书")

    keyword_settings = load_keywords(args.keywords)
    keyword_groups = _selected_keyword_groups(keyword_settings)
    source_settings = load_source_settings(args.config)
    if args.use_sample_data:
        records_by_category, review_records, source_runs = _sample_source_runs()
        run_mode = "样例数据"
    else:
        records_by_category, review_records, source_runs = run_configured_sources(
            source_settings,
            keyword_groups,
            max_keywords_per_category=args.max_keywords_per_category,
            amazon_review_asin=args.amazon_review_asin,
        )
        run_mode = "真实数据"

    opportunities = [
        score_opportunity(
            social_records=records,
            review_records=review_records,
            category=category,
            keywords=keyword_groups[category],
        )
        for category, records in records_by_category.items()
        if records
    ]
    evidence_index = build_evidence_index(records_by_category, review_records)
    voc_taxonomy, signal_words = load_voc_config(PROJECT_ROOT / "config" / "voc_tags.yaml")
    persona_settings = get_persona_journey_settings(source_settings)
    all_evidence = tuple(
        item for items in evidence_index.by_category.values() for item in items
    )
    voc_by_id = classify_voc(all_evidence, voc_taxonomy)
    signals = detect_innovation_signals(all_evidence, signal_words)
    gates = {
        (opportunity.category, opportunity.title): evaluate_opportunity_gate(
            opportunity,
            evidence_index.by_category.get(opportunity.category, ()),
            voc_by_id,
            signals,
            min_evidence_count=persona_settings["min_evidence_count"],
        )
        for opportunity in opportunities
    }
    qualified = [
        opportunity
        for opportunity in sorted(
            opportunities, key=lambda item: item.total_score, reverse=True
        )
        if opportunity.total_score >= persona_settings["min_opportunity_score"]
        and gates[(opportunity.category, opportunity.title)].eligible
    ][: persona_settings["max_opportunities_per_report"]]
    persona_journeys = [
        PersonaJourneyResult(
            persona=build_persona(
                opportunity,
                evidence_index.by_category.get(opportunity.category, ()),
                voc_by_id,
                gates[(opportunity.category, opportunity.title)],
            ),
            stages=build_journey(
                opportunity,
                evidence_index.by_category.get(opportunity.category, ()),
                voc_by_id,
                gates[(opportunity.category, opportunity.title)],
            ),
            gate_eligible=gates[(opportunity.category, opportunity.title)].eligible,
        )
        for opportunity in qualified
    ]
    markdown = build_daily_markdown(
        opportunities=opportunities,
        source_runs=source_runs,
        report_date=args.report_date,
        focus=_focus_label(keyword_groups),
        run_mode=run_mode,
        evidence_by_category=records_by_category,
        persona_journeys=persona_journeys,
    )
    if args.dry_run:
        print(markdown)
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    report_name = f"radar_report_{args.report_date.replace('-', '_')}.md"
    report_path = args.output_dir / report_name
    report_path.write_text(markdown, encoding="utf-8")
    print(f"已写入本地报告：{report_path}")
    if args.send_feishu:
        webhook_env = str(source_settings["feishu"].get("webhook_env", "FEISHU_WEBHOOK_URL"))
        send_feishu_markdown(require_env(webhook_env), "亚马逊社媒产品机会雷达", markdown)
        print("飞书发送成功。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
