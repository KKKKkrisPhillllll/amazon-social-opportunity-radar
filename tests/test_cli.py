from radar.cli import main


def test_cli_dry_run_prints_report(capsys):
    exit_code = main(["--dry-run", "--use-sample-data", "--report-date", "2026-07-10"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Amazon Social Opportunity Radar" in captured.out
    assert "Data Source Health" in captured.out
