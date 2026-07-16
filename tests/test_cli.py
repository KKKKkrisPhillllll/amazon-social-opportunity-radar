import os
import subprocess
import sys
from pathlib import Path

from radar.cli import main


def test_cli_sample_dry_run_prints_report(capsys):
    exit_code = main(["--dry-run", "--use-sample-data", "--report-date", "2026-07-10"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Amazon Social Opportunity Radar" in captured.out
    assert "Data Source Health" in captured.out


def test_cli_defaults_to_real_pipeline_without_credentials(monkeypatch, capsys):
    monkeypatch.delenv("APIFY_TOKEN", raising=False)
    monkeypatch.delenv("SCRAPECREATORS_API_KEY", raising=False)

    exit_code = main(["--dry-run", "--report-date", "2026-07-16"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "No qualified opportunities found today." in captured.out
    assert "xiaohongshu: NOT_CONFIGURED" in captured.out
    assert "scrapecreators: NOT_CONFIGURED" in captured.out


def test_daily_script_uses_real_mode_by_default():
    project_root = Path(__file__).resolve().parents[1]
    script = (project_root / "scripts" / "run_daily.ps1").read_text(encoding="utf-8")

    assert "-m radar.cli" in script
    assert "--use-sample-data" not in script


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

    assert "# Amazon Social Opportunity Radar" in result.stdout
    assert "Data Source Health" in result.stdout
