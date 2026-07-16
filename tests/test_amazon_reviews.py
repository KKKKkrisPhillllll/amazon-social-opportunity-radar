from pathlib import Path
import subprocess
import sys

from radar.collectors.amazon_reviews import collect_amazon_reviews
from radar.models import SourceHealth


class FakeCompleted:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_collect_amazon_reviews_uses_primary_when_success(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")

    def runner(command, capture_output, text, timeout):
        return FakeCompleted(
            0,
            stdout='[{"asin":"B012345678","rating":2,"title":"Bad","review_text":"Hard to clean"}]',
        )

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.OK
    assert records[0].source_script == "primary"
    assert records[0].asin == "B012345678"


def test_collect_amazon_reviews_falls_back_to_backup_on_forbidden(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    calls = []

    def runner(command, capture_output, text, timeout):
        calls.append(command)
        if len(calls) == 1:
            return FakeCompleted(1, stdout="", stderr="HTTP 403 Forbidden")
        return FakeCompleted(
            0,
            stdout='{"reviews":[{"asin":"B012345678","rating":1,"title":"Broken","review_text":"Broke quickly"}]}',
        )

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.DEGRADED
    assert records[0].source_script == "backup"
    assert len(calls) == 2


def test_collect_amazon_reviews_falls_back_to_backup_on_timeout(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    calls = []

    def runner(command, capture_output, text, timeout):
        calls.append(command)
        if len(calls) == 1:
            raise subprocess.TimeoutExpired(command, timeout)
        return FakeCompleted(
            0,
            stdout='[{"asin":"B012345678","rating":4,"title":"Useful","review_text":"Backup worked"}]',
        )

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.DEGRADED
    assert records[0].source_script == "backup"
    assert len(calls) == 2


def test_collect_amazon_reviews_falls_back_to_backup_on_runner_exception(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    calls = []

    def runner(command, capture_output, text, timeout):
        calls.append(command)
        if len(calls) == 1:
            raise FileNotFoundError("py")
        return FakeCompleted(
            0,
            stdout='[{"asin":"B012345678","rating":3,"title":"Okay","review_text":"Backup collected"}]',
        )

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.DEGRADED
    assert records[0].source_script == "backup"
    assert len(calls) == 2


def test_collect_amazon_reviews_reads_backup_output_file(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    calls = []

    def runner(command, capture_output, text, timeout):
        calls.append(command)
        if len(calls) == 1:
            return FakeCompleted(1, stdout="", stderr="HTTP 403 Forbidden")
        output_dir = Path(command[command.index("-o") + 1])
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "B012345678_reviews.json").write_text(
            '[{"asin":"B012345678","rating":2,"title":"Too flimsy","body":"Backup file parsed"}]',
            encoding="utf-8",
        )
        return FakeCompleted(0, stdout="logs only")

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.DEGRADED
    assert records[0].source_script == "backup"
    assert records[0].review_text == "Backup file parsed"


def test_collect_amazon_reviews_reports_not_configured_when_scripts_missing(tmp_path):
    records, health = collect_amazon_reviews(
        "B012345678",
        tmp_path / "missing-primary.py",
        tmp_path / "missing-backup.py",
    )

    assert records == []
    assert health is SourceHealth.NOT_CONFIGURED


def test_collect_amazon_reviews_uses_current_python_interpreter(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    commands = []

    def runner(command, capture_output, text, timeout):
        commands.append(command)
        return FakeCompleted(
            0,
            stdout=(
                '[{"asin":"B0D3XTZVS5","rating":2,'
                '"title":"Hard to clean","review_text":"Corners trap water"}]'
            ),
        )

    records, health = collect_amazon_reviews("B0D3XTZVS5", primary, backup, runner=runner)

    assert health is SourceHealth.OK
    assert records[0].asin == "B0D3XTZVS5"
    assert commands[0][0] == sys.executable
