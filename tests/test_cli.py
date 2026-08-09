import os
import subprocess
import sys
from pathlib import Path

import pytest

from radar.cli import main
from radar.models import SocialRecord, SourceHealth, SourceRun
from radar.reports import build_daily_markdown


def test_cli_builds_persona_journeys_only_for_gate_qualified_opportunities(
    monkeypatch, tmp_path
):
    records = [
        SocialRecord(
            platform="reddit",
            keyword="\u53a8\u623f\u6536\u7eb3",
            url="https://reddit.example/1",
            title="\u7a7a\u95f4\u95ee\u9898",
            text="storage organizer hard to clean not durable broke",
            engagement={"likes": 500, "favorites": 100, "comments": 50},
        ),
        SocialRecord(
            platform="youtube",
            keyword="\u53a8\u623f\u6536\u7eb3",
            url="https://youtube.example/2",
            title="\u6536\u7eb3\u65b9\u6848",
            text="storage organizer hard to clean not durable broke",
            engagement={"likes": 500, "favorites": 100, "comments": 50},
        ),
    ]

    monkeypatch.setattr(
        "radar.cli.run_configured_sources",
        lambda *args, **kwargs: (
            {"kitchen_storage": records},
            [],
            [SourceRun("test", "social", tuple(records), SourceHealth.OK, 2)],
        ),
    )

    captured = {}

    def capture_persona_journeys(**kwargs):
        captured["persona_journeys"] = kwargs["persona_journeys"]
        return build_daily_markdown(**kwargs)

    monkeypatch.setattr("radar.cli.build_daily_markdown", capture_persona_journeys)
    exit_code = main(
        ["--output-dir", str(tmp_path), "--report-date", "2026-08-09"]
    )

    report = (tmp_path / "radar_report_2026_08_09.md").read_text(encoding="utf-8")
    assert exit_code == 0
    assert "## \u7528\u6237\u753b\u50cf\u4e0e\u7528\u6237\u65c5\u7a0b\u56fe" in report
    assert "```mermaid" in report
    assert all(result.gate_eligible for result in captured["persona_journeys"])


def test_cli_dry_run_prints_report(capsys):
    exit_code = main(["--dry-run", "--use-sample-data", "--report-date", "2026-07-10"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# 亚马逊社媒产品机会雷达" in captured.out
    assert "数据源健康状态" in captured.out
    assert "## 用户画像与用户旅程图" not in captured.out
    assert "```mermaid" not in captured.out


def test_cli_subprocess_dry_run_uses_project_src_path():
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "radar.cli",
            "--dry-run",
            "--use-sample-data",
            "--report-date",
            "2026-07-10",
        ],
        cwd=project_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "# 亚马逊社媒产品机会雷达" in result.stdout
    assert "数据源健康状态" in result.stdout


def test_cli_real_mode_writes_local_report_without_sending(monkeypatch, tmp_path, capsys):
    record = SocialRecord(
        platform="xiaohongshu",
        keyword="厨房收纳",
        url="https://www.xiaohongshu.com/explore/1",
        title="小厨房收纳",
        text="难清洗",
    )

    def fake_run(*args, **kwargs):
        return (
            {
                "kitchen_appliances": [],
                "kitchen_storage": [record],
                "home_storage": [],
            },
            [],
            [
                SourceRun(
                    "apify_xiaohongshu",
                    "xiaohongshu",
                    (record,),
                    SourceHealth.OK,
                    fetched_count=1,
                )
            ],
        )

    monkeypatch.setattr("radar.cli.run_configured_sources", fake_run)
    exit_code = main(
        [
            "--output-dir",
            str(tmp_path),
            "--report-date",
            "2026-08-02",
            "--max-keywords-per-category",
            "1",
        ]
    )

    captured = capsys.readouterr()
    report_path = tmp_path / "radar_report_2026_08_02.md"
    assert exit_code == 0
    assert report_path.exists()
    assert "已写入本地报告" in captured.out
    assert "运行模式：真实数据" in report_path.read_text(encoding="utf-8")


def test_cli_rejects_dry_run_and_send_feishu_together():
    with pytest.raises(SystemExit):
        main(["--dry-run", "--send-feishu"])


def test_cli_rejects_sending_sample_data_to_feishu():
    with pytest.raises(SystemExit):
        main(["--use-sample-data", "--send-feishu"])
