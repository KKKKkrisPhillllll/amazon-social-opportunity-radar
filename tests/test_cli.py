import os
import subprocess
import sys
from pathlib import Path

from radar.cli import main


def test_cli_sample_dry_run_prints_report(capsys):
    exit_code = main(["--dry-run", "--use-sample-data", "--report-date", "2026-07-10"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# 亚马逊社媒产品机会雷达" in captured.out
    assert "数据源健康状态" in captured.out
    assert "小厨房调料收纳方案" in captured.out
    assert "用户痛点：难清洗" in captured.out


def test_cli_defaults_to_real_pipeline_without_credentials(monkeypatch, capsys):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    monkeypatch.delenv("SCRAPECREATORS_API_KEY", raising=False)

    exit_code = main(["--dry-run", "--report-date", "2026-07-16"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "今日未发现达到输出条件的产品机会" in captured.out
    assert "xiaohongshu: 未配置" in captured.out
    assert "scrapecreators: 未配置" in captured.out


def test_daily_script_uses_real_mode_by_default():
    project_root = Path(__file__).resolve().parents[1]
    script = (project_root / "scripts" / "run_daily.ps1").read_text(encoding="utf-8")

    assert "-m radar.cli" in script
    assert "--use-sample-data" not in script


def test_cli_subprocess_dry_run_uses_project_src_path():
    project_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root / "src")
    env["PYTHONIOENCODING"] = "utf-8"

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
        encoding="utf-8",
    )

    assert "# 亚马逊社媒产品机会雷达" in result.stdout
    assert "数据源健康状态" in result.stdout
