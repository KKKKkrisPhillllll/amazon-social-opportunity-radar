from radar.models import Opportunity, SourceHealth
from radar.reports import build_daily_markdown


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
