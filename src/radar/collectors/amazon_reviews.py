from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from radar.models import ReviewRecord, SourceHealth
from radar.normalizers import normalize_review_record


def _extract_reviews(stdout: str) -> list[dict[str, Any]]:
    data = json.loads(stdout)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("reviews"), list):
        return [item for item in data["reviews"] if isinstance(item, dict)]
    return []


def _run_script(script: Path, asin: str, runner) -> tuple[list[dict[str, Any]], bool]:
    command = ["py", "-3", str(script), asin]
    try:
        completed = runner(command, capture_output=True, text=True, timeout=120)
    except Exception:
        return [], False
    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    if completed.returncode != 0 or "403" in combined or "forbidden" in combined:
        return [], False
    try:
        reviews = _extract_reviews(completed.stdout)
    except json.JSONDecodeError:
        return [], False
    return reviews, bool(reviews)


def collect_amazon_reviews(
    asin: str,
    primary_script: Path,
    backup_script: Path,
    runner=None,
) -> tuple[list[ReviewRecord], SourceHealth]:
    runner = runner or subprocess.run
    primary_exists = primary_script.exists()
    backup_exists = backup_script.exists()
    if not primary_exists and not backup_exists:
        return [], SourceHealth.NOT_CONFIGURED

    if primary_exists:
        primary_reviews, primary_ok = _run_script(primary_script, asin, runner)
        if primary_ok:
            return [
                normalize_review_record(item, "primary", str(primary_script))
                for item in primary_reviews
            ], SourceHealth.OK

    if backup_exists:
        backup_reviews, backup_ok = _run_script(backup_script, asin, runner)
        if backup_ok:
            return [
                normalize_review_record(item, "backup", str(backup_script))
                for item in backup_reviews
            ], SourceHealth.DEGRADED

    return [], SourceHealth.FAILED
