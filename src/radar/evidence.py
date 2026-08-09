from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from urllib.parse import urlparse

from radar.models import ReviewRecord, SocialRecord


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    platform: str
    url: str
    category: str
    title: str
    text: str
    comments: tuple[str, ...]
    asin: str = ""


@dataclass(frozen=True)
class EvidenceIndex:
    by_category: dict[str, tuple[EvidenceItem, ...]]
    by_id: dict[str, EvidenceItem]


def _is_public_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_evidence_index(
    records_by_category: Mapping[str, Sequence[SocialRecord]],
    review_records: Sequence[ReviewRecord],
) -> EvidenceIndex:
    del review_records
    by_category: dict[str, tuple[EvidenceItem, ...]] = {}
    by_id: dict[str, EvidenceItem] = {}
    counter = 1

    for category, records in records_by_category.items():
        items: list[EvidenceItem] = []
        seen_urls: set[str] = set()
        for record in records:
            if not _is_public_url(record.url):
                continue
            normalized_url = record.url.strip()
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            item = EvidenceItem(
                evidence_id=f"E-{counter:04d}",
                platform=record.platform,
                url=normalized_url,
                category=category,
                title=record.title.strip(),
                text=record.text.strip(),
                comments=tuple(comment.strip() for comment in record.comments if comment.strip()),
            )
            items.append(item)
            by_id[item.evidence_id] = item
            counter += 1
        by_category[category] = tuple(items)

    return EvidenceIndex(by_category=by_category, by_id=by_id)
