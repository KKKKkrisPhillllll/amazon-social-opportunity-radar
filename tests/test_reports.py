from dataclasses import replace

from radar.models import Opportunity, SocialRecord, SourceHealth, SourceRun
from radar.reports import build_daily_markdown
from radar.journey_builder import JOURNEY_STAGES
from radar.models import JourneyStage, PersonaEvidence, PersonaJourneyResult, UserPersona
from test_helpers import make_opportunity


def _persona_journey_result() -> PersonaJourneyResult:
    persona = UserPersona(
        opportunity_title="\u53f0\u9762\u6536\u7eb3\u673a\u4f1a",
        category="kitchen_storage",
        opportunity_score=75,
        behavioral_segment="\u5c0f\u7a7a\u95f4\u6548\u7387\u578b",
        scenario="\u5c0f\u53a8\u623f\u53f0\u9762\u6536\u7eb3",
        core_goal="\u51cf\u5c11\u53d6\u653e\u548c\u6e05\u6d01\u6b65\u9aa4",
        pain_points=("\u7a7a\u95f4\u4e0d\u8db3",),
        purchase_triggers=("\u53cd\u590d\u51fa\u73b0\u7684\u53f0\u9762\u62e5\u6324",),
        concerns=("\u5c3a\u5bf8\u9002\u914d",),
        evidence=(
            PersonaEvidence("reddit", "https://reddit.example/1", "\u53f0\u9762\u7a7a\u95f4\u592a\u5c0f"),
            PersonaEvidence("youtube", "https://youtube.example/2", "\u5f88\u96be\u6e05\u6d01"),
        ),
        confidence="\u4e2d",
    )
    stages = tuple(
        JourneyStage(
            name=name,
            observed_signals=("\u516c\u5f00\u8bc1\u636e\u4e2d\u7684\u76f8\u5173\u4fe1\u53f7",),
            user_need_or_action="\u5b8c\u6210\u5f53\u524d\u9636\u6bb5\u4efb\u52a1",
            product_implication="\u4f18\u5148\u9a8c\u8bc1\u5bf9\u5e94\u9636\u6bb5\u7684\u6469\u64e6",
            evidence_urls=("https://reddit.example/1",),
            confidence="\u4e2d",
        )
        for name in JOURNEY_STAGES
    )
    return PersonaJourneyResult(persona=persona, stages=stages)


def test_report_renders_persona_journey_mermaid_and_public_evidence_links():
    markdown = build_daily_markdown(
        opportunities=[make_opportunity(total_score=75)],
        source_runs=[],
        report_date="2026-08-09",
        focus="\u53a8\u623f\u6536\u7eb3",
        run_mode="\u793a\u4f8b\u6570\u636e",
        evidence_by_category={},
        persona_journeys=[_persona_journey_result()],
    )

    assert "## \u7528\u6237\u753b\u50cf\u4e0e\u7528\u6237\u65c5\u7a0b\u56fe" in markdown
    assert "```mermaid" in markdown
    assert "reddit" in markdown
    assert "https://reddit.example/1" in markdown
    assert "\u53f0\u9762\u7a7a\u95f4\u592a\u5c0f" in markdown
    assert JOURNEY_STAGES[0] in markdown
    assert JOURNEY_STAGES[-1] in markdown
    assert "author" not in markdown


def test_report_does_not_render_persona_section_without_qualified_results():
    markdown = build_daily_markdown(
        opportunities=[], source_runs=[], report_date="2026-08-09",
        focus="\u53a8\u623f\u6536\u7eb3", run_mode="\u793a\u4f8b\u6570\u636e", evidence_by_category={},
    )

    assert "## \u7528\u6237\u753b\u50cf\u4e0e\u7528\u6237\u65c5\u7a0b\u56fe" not in markdown


def test_report_does_not_render_persona_section_for_low_score_result():
    result = _persona_journey_result()
    low_score = replace(result, persona=replace(result.persona, opportunity_score=59))

    markdown = build_daily_markdown(
        opportunities=[], source_runs=[], report_date="2026-08-09",
        focus="\u53a8\u623f\u6536\u7eb3", run_mode="\u771f\u5b9e\u6570\u636e", evidence_by_category={},
        persona_journeys=[low_score],
    )

    assert "## \u7528\u6237\u753b\u50cf\u4e0e\u7528\u6237\u65c5\u7a0b\u56fe" not in markdown
    assert "```mermaid" not in markdown


def test_report_does_not_render_persona_section_for_gate_ineligible_result():
    result = replace(_persona_journey_result(), gate_eligible=False)

    markdown = build_daily_markdown(
        opportunities=[], source_runs=[], report_date="2026-08-09",
        focus="\u53a8\u623f\u6536\u7eb3", run_mode="\u771f\u5b9e\u6570\u636e", evidence_by_category={},
        persona_journeys=[result],
    )

    assert "## \u7528\u6237\u753b\u50cf\u4e0e\u7528\u6237\u65c5\u7a0b\u56fe" not in markdown
    assert "```mermaid" not in markdown


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
