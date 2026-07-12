from radar.models import Opportunity, ReviewRecord, SourceHealth
from radar.reports import build_amazon_review_markdown, build_daily_markdown


def test_build_daily_markdown_contains_sections_and_health():
    opportunity = Opportunity(
        title="鍘ㄦ埧鏀剁撼绁炲櫒",
        category="kitchen_storage",
        source_platforms=["xiaohongshu"],
        evidence_summary="1 social record and 1 review record analyzed.",
        customer_pain_point="Hard to clean",
        product_idea="Create an easier-to-clean organizer.",
        amazon_validation_keywords=["kitchen organizer"],
        suggested_asins=["B012345678"],
        differentiation_angle="Removable washable parts",
        risk_notes="Validate margin.",
        next_action="Check Amazon reviews.",
        score_breakdown={
            "social_heat": 20,
            "pain_intensity": 18,
            "amazon_review_validation": 12,
            "product_development_fit": 10,
            "amazon_business_feasibility": 10,
        },
    )

    markdown = build_daily_markdown(
        [opportunity],
        {"xiaohongshu": SourceHealth.OK, "scrapecreators": SourceHealth.NOT_CONFIGURED},
        report_date="2026-07-10",
        focus="Kitchen appliances / kitchen storage / home storage",
    )

    assert "# Amazon Social Opportunity Radar" in markdown
    assert "## 1. Top Opportunities" in markdown
    assert "鍘ㄦ埧鏀剁撼绁炲櫒" in markdown
    assert "Score: 70" in markdown
    assert "## 7. Data Source Health" in markdown
    assert "scrapecreators: NOT_CONFIGURED" in markdown


def test_build_amazon_review_markdown_only_uses_actual_low_rating_reviews():
    reviews = [
        ReviewRecord(
            asin="B0D3XTZVS5",
            rating=2,
            title="难清洗",
            review_text="缝隙里容易积水，清洗很麻烦。",
            review_date="2026-07-11",
            source_script="primary",
            raw_source_path="C:/scripts/primary.py",
        ),
        ReviewRecord(
            asin="B0D3XTZVS5",
            rating=5,
            title="满意",
            review_text="使用方便。",
            source_script="primary",
            raw_source_path="C:/scripts/primary.py",
        ),
    ]

    markdown = build_amazon_review_markdown(
        asin="B0D3XTZVS5",
        reviews=reviews,
        health=SourceHealth.OK,
        report_date="2026-07-12",
    )

    assert "# Amazon 评论首跑报告" in markdown
    assert "- 采集状态：OK" in markdown
    assert "- 实际评论数量：2" in markdown
    assert "- 低评分评论数量：1" in markdown
    assert "缝隙里容易积水，清洗很麻烦。" in markdown
    assert "使用方便。" not in markdown
    assert "- 实际使用脚本：primary" in markdown


def test_build_amazon_review_markdown_reports_empty_result_without_inventing_reviews():
    markdown = build_amazon_review_markdown(
        asin="B0D3XTZVS5",
        reviews=[],
        health=SourceHealth.FAILED,
        report_date="2026-07-12",
    )

    assert "- 采集状态：FAILED" in markdown
    assert "- 实际评论数量：0" in markdown
    assert "未采集到评分低于或等于 3 星的评论。" in markdown
    assert "实际使用脚本" not in markdown
