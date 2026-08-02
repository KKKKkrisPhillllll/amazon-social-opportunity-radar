from __future__ import annotations

from urllib.parse import urlsplit, urlunsplit

from radar.models import SocialRecord


def _compact(value: str) -> str:
    return " ".join(value.casefold().split())


def record_identity(record: SocialRecord) -> tuple[str, ...]:
    raw_url = record.url.strip()
    if raw_url:
        parsed = urlsplit(raw_url)
        if parsed.scheme and parsed.netloc:
            path = parsed.path.rstrip("/") or "/"
            normalized_url = urlunsplit(
                (parsed.scheme.casefold(), parsed.netloc.casefold(), path, parsed.query, "")
            )
        else:
            normalized_url = raw_url.rstrip("/").casefold()
        return ("url", normalized_url)
    return ("content", record.platform.casefold(), _compact(record.title), _compact(record.text)[:160])


def deduplicate_social_records(records: list[SocialRecord]) -> tuple[list[SocialRecord], int]:
    unique: list[SocialRecord] = []
    seen: set[tuple[str, ...]] = set()
    duplicate_count = 0
    for record in records:
        identity = record_identity(record)
        if identity in seen:
            duplicate_count += 1
            continue
        seen.add(identity)
        unique.append(record)
    return unique, duplicate_count
