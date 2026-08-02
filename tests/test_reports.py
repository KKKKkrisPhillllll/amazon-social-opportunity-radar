from radar.models import Opportunity, SocialRecord, SourceHealth, SourceRun
from radar.reports import build_daily_markdown


def _opportunity() -> Opportunity:
    return Opportunity(
        title="可拆洗调料收纳架",
        category="kitchen_storage",
        source_platforms=["xiaohongshu"],
        evidence_summary="已分析 1 条社媒记录和 1 条评论记录。",
        customer_pain_point="难清洗",
        product_idea="制作可拆洗收纳架。",
        amazon_validation_keywords=["kitchen organizer"],
        suggested_asins=["B012345678"],
        differentiation_angle="可拆洗组件",
        risk_notes="需要验证利润率。",
        next_action="检查亚马逊评论。",
        score_breakdown={
            "social_heat": 20,
            "pain_intensity": 18,
            "amazon_review_validation": 12,
            "product_development_fit": 10,
            "amazon_business_feasibility": 10,
        },
    )


def test_build_daily_markdown_contains_chinese_sections_source_counts_and_evidence():
    markdown = build_daily_markdown(
        opportunities=[_opportunity()],
        source_runs=[
            SourceRun(
                "apify_xiaohongshu",
                "xiaohongshu",
                (),
                SourceHealth.OK,
                fetched_count=4,
                duplicate_count=1,
                diagnostic="ok",
            ),
            SourceRun(
                "scrapecreators_reddit",
                "reddit",
                (),
                SourceHealth.NOT_CONFIGURED,
                fetched_count=0,
                diagnostic="missing_credentials",
            ),
        ],
        report_date="2026-07-10",
        focus="厨房电器 / 厨房收纳 / 家居收纳",
        run_mode="真实数据",
        evidence_by_category={
            "kitchen_storage": [
                SocialRecord(
                    platform="xiaohongshu",
                    keyword="厨房收纳",
                    url="https://www.xiaohongshu.com/explore/1",
                    title="证据一",
                    text="正文",
                ),
                SocialRecord(
                    platform="reddit",
                    keyword="kitchen storage",
                    url="https://www.reddit.com/r/example/2",
                    title="证据二",
                    text="body",
                ),
            ]
        },
    )

    assert "# 亚马逊社媒产品机会雷达" in markdown
    assert "运行模式：真实数据" in markdown
    assert "## 1. 产品机会排序" in markdown
    assert "可拆洗调料收纳架" in markdown
    assert "总分：70" in markdown
    assert "https://www.xiaohongshu.com/explore/1" in markdown
    assert "## 7. 数据源健康状态" in markdown
    assert "采集 4 条，去重 1 条" in markdown
    assert "missing_credentials" in markdown


def test_build_daily_markdown_marks_sample_mode_as_non_business_evidence():
    markdown = build_daily_markdown(
        opportunities=[],
        source_runs=[],
        report_date="2026-07-10",
        focus="厨房收纳",
        run_mode="样例数据",
        evidence_by_category={},
    )

    assert "样例数据仅用于验证链路" in markdown
