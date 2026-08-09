from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_public_docs_describe_the_runnable_windows_sample_flow():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    verification_report = (
        PROJECT_ROOT / "docs" / "radar_verification_report.md"
    ).read_text(encoding="utf-8")

    assert "$env:PYTHONPATH='src'" in readme
    assert "py -3 -m pytest -q" in readme
    assert "py -3 -m radar.cli --use-sample-data --output-dir outputs" in readme
    assert "发现需求 -> 搜索方案 -> 对比决策 -> 购买 -> 使用 -> 反馈" in readme
    assert "公开证据链接" in readme
    assert "ruff" in verification_report
    assert "未执行" in verification_report
    assert "outputs/radar_report_" in verification_report
    assert "真实 API 凭据" in verification_report
    assert "画像/旅程" in verification_report
    assert "低置信度" in verification_report


def test_public_docs_distinguish_builder_low_confidence_from_cli_gate_filter():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    verification_report = (
        PROJECT_ROOT / "docs" / "radar_verification_report.md"
    ).read_text(encoding="utf-8")
    builder_statement = (
        "低置信度是 persona/journey builder "
        "在证据不足时返回的结构化结果"
    )
    cli_statement = "CLI 日报在 Gate 不合格时不渲染画像/旅程章节"
    sample_statement = "1 个机会、1 条公开 URL、0 个画像/旅程"

    assert builder_statement in readme
    assert cli_statement in readme
    assert builder_statement in verification_report
    assert cli_statement in verification_report
    assert sample_statement in verification_report
    assert "不代表真实市场需求" in readme
