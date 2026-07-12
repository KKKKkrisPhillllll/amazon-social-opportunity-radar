import os
import subprocess
import sys
from pathlib import Path

import pytest

from radar.cli import main
from radar.models import ReviewRecord, SourceHealth


def test_cli_dry_run_prints_report(capsys):
    exit_code = main(["--dry-run", "--use-sample-data", "--report-date", "2026-07-10"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Amazon Social Opportunity Radar" in captured.out
    assert "Data Source Health" in captured.out


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


def test_cli_amazon_review_first_run_writes_local_report_without_feishu(
    monkeypatch,
    tmp_path,
    capsys,
):
    source_config = tmp_path / "sources.yaml"
    source_config.write_text(
        """feishu:
  webhook_env: FEISHU_WEBHOOK_URL
apify:
  token_env: APIFY_TOKEN
  xiaohongshu_actor: actor
scrapecreators:
  api_key_env: SCRAPECREATORS_API_KEY
amazon_reviews:
  primary_script: C:/scripts/primary.py
  backup_script: C:/scripts/backup.py
""",
        encoding="utf-8",
    )
    reviews = [
        ReviewRecord(
            asin="B0D3XTZVS5",
            rating=1,
            title="Easy to break",
            review_text="It broke after two weeks.",
            source_script="backup",
            raw_source_path="C:/scripts/backup.py",
        )
    ]
    monkeypatch.setattr(
        "radar.cli.collect_amazon_reviews",
        lambda asin, primary_script, backup_script: (reviews, SourceHealth.DEGRADED),
    )
    monkeypatch.setattr(
        "radar.cli.send_feishu_markdown",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Feishu must not be called")),
    )

    exit_code = main(
        [
            "--amazon-review-asin",
            "B0D3XTZVS5",
            "--dry-run",
            "--source-config",
            str(source_config),
            "--output-dir",
            str(tmp_path / "outputs"),
            "--report-date",
            "2026-07-12",
        ]
    )

    report_path = tmp_path / "outputs" / "amazon_review_report_B0D3XTZVS5_20260712.md"
    captured = capsys.readouterr()
    assert exit_code == 0
    assert report_path.exists()
    assert "- 采集状态：DEGRADED" in report_path.read_text(encoding="utf-8")
    assert "# Amazon 评论首跑报告" in captured.out


def test_cli_amazon_review_first_run_requires_dry_run(capsys):
    with pytest.raises(SystemExit) as error:
        main(["--amazon-review-asin", "B0D3XTZVS5"])

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert "--amazon-review-asin 首跑必须使用 --dry-run" in captured.err
