from __future__ import annotations

import ipaddress
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit

from radar.models import ReviewRecord, SocialRecord


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    platform: str
    url: str
    category: str
    summary: str
    comment_count: int
    asin: str = ""


@dataclass(frozen=True)
class EvidenceIndex:
    by_category: dict[str, tuple[EvidenceItem, ...]]
    by_id: dict[str, EvidenceItem]


def _normalize_public_url(value: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = urlsplit(value.strip())
        hostname = parsed.hostname
        if parsed.scheme.casefold() not in {"http", "https"} or not hostname:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            return None
    except ValueError:
        return None

    normalized_host = hostname.rstrip(".").casefold()
    if (
        normalized_host == "localhost"
        or normalized_host.endswith(".localhost")
        or normalized_host == "localhost.localdomain"
        or normalized_host.endswith(".localdomain")
    ):
        return None
    try:
        host_ip = ipaddress.ip_address(normalized_host)
    except ValueError:
        host_ip = None
    if host_ip is not None and not host_ip.is_global:
        return None

    host = f"[{normalized_host}]" if ":" in normalized_host else normalized_host
    netloc = host if parsed.port is None else f"{host}:{parsed.port}"
    path = parsed.path.rstrip("/") or "/"
    return urlunsplit((parsed.scheme.casefold(), netloc, path, parsed.query, ""))


def _summary(record: SocialRecord) -> str:
    return " ".join(part.strip() for part in (record.title, record.text) if part.strip())


def _comment_count(record: SocialRecord) -> int:
    value = record.engagement.get("comments")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return len(record.comments)
    return max(0, int(value))


def build_evidence_index(
    records_by_category: Mapping[str, Sequence[SocialRecord]],
    review_records: Sequence[ReviewRecord],
) -> EvidenceIndex:
    del review_records
    items_by_category: dict[str, list[EvidenceItem]] = {}
    by_id: dict[str, EvidenceItem] = {}

    candidates: dict[tuple[str, str], SocialRecord] = {}
    for category in sorted(records_by_category):
        for record in records_by_category[category]:
            normalized_url = _normalize_public_url(record.url)
            if normalized_url is None:
                continue
            key = (category, normalized_url)
            existing = candidates.get(key)
            if existing is None or _candidate_sort_key(record) < _candidate_sort_key(existing):
                candidates[key] = record

    for index, (category, normalized_url) in enumerate(sorted(candidates), start=1):
        record = candidates[(category, normalized_url)]
        item = EvidenceItem(
            evidence_id=f"E-{index:04d}",
            platform=record.platform,
            url=normalized_url,
            category=category,
            summary=_summary(record),
            comment_count=_comment_count(record),
            asin=str(getattr(record, "asin", "") or ""),
        )
        items_by_category.setdefault(category, []).append(item)
        by_id[item.evidence_id] = item

    by_category: dict[str, tuple[EvidenceItem, ...]] = {
        category: tuple(items)
        for category, items in items_by_category.items()
    } | {
        category: ()
        for category in sorted(records_by_category)
        if category not in items_by_category
    }

    return EvidenceIndex(by_category=by_category, by_id=by_id)


def _candidate_sort_key(record: SocialRecord) -> tuple[str, ...]:
    return (record.platform, _summary(record), str(record.engagement.get("comments", "")))
