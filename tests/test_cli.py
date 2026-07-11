import os
import subprocess
import sys
from pathlib import Path

from radar.cli import main


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
