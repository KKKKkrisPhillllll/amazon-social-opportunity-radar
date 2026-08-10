from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests

MAX_PAYLOAD_BYTES = 20 * 1024
_CODE_FENCE = "```"


def _payload(title: str, markdown: str) -> dict[str, Any]:
    return {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title,
                }
            },
            "elements": [
                {
                    "tag": "markdown",
                    "text": {
                        "content": markdown,
                    },
                }
            ],
        },
    }


def _payload_size(title: str, markdown: str) -> int:
    body = requests.Request(
        "POST", "https://example.invalid", json=_payload(title, markdown)
    ).prepare().body
    return len(body.encode("utf-8") if isinstance(body, str) else body or b"")


def _close_code_block(markdown: str, code_fence: tuple[str, str] | None) -> str:
    if code_fence is None:
        return markdown
    separator = "" if markdown.endswith("\n") else "\n"
    return f"{markdown}{separator}{code_fence[1]}\n"


def _reopen_code_block(code_fence: tuple[str, str]) -> str:
    opening_line = code_fence[0]
    return opening_line if opening_line.endswith("\n") else f"{opening_line}\n"


def _fence_marker(line: str) -> str | None:
    stripped = line.lstrip()
    if not stripped.startswith(_CODE_FENCE):
        return None
    length = len(stripped) - len(stripped.lstrip("`"))
    return stripped[:length]


def _next_code_fence(
    line: str, code_fence: tuple[str, str] | None
) -> tuple[str, str] | None:
    marker = _fence_marker(line)
    if code_fence is None:
        return (line, marker) if marker else None
    if marker is None:
        return code_fence

    stripped = line.lstrip().rstrip("\r\n")
    if len(marker) >= len(code_fence[1]) and not stripped[len(marker) :].strip():
        return None
    return code_fence


def _largest_fitting_prefix(
    title: str,
    prefix: str,
    value: str,
    code_fence: tuple[str, str] | None,
) -> str:
    low = 0
    high = len(value)
    while low < high:
        middle = (low + high + 1) // 2
        candidate = _close_code_block(prefix + value[:middle], code_fence)
        if _payload_size(title, candidate) <= MAX_PAYLOAD_BYTES:
            low = middle
        else:
            high = middle - 1
    return value[:low]


def _split_markdown(title: str, markdown: str) -> tuple[str, ...]:
    if _payload_size(title, "") > MAX_PAYLOAD_BYTES:
        raise ValueError("Feishu webhook payload exceeds the 20KB limit")

    chunks: list[str] = []
    current = ""
    code_fence: tuple[str, str] | None = None

    def flush() -> None:
        nonlocal current
        if current:
            chunks.append(_close_code_block(current, code_fence))
            current = _reopen_code_block(code_fence) if code_fence else ""

    for line in markdown.splitlines(keepends=True):
        candidate_code_fence = _next_code_fence(line, code_fence)
        candidate = current + line
        if _payload_size(
            title, _close_code_block(candidate, candidate_code_fence)
        ) <= MAX_PAYLOAD_BYTES:
            current = candidate
            code_fence = candidate_code_fence
            continue

        if current:
            flush()

        remaining = line
        while remaining:
            piece = _largest_fitting_prefix(
                title, current, remaining, candidate_code_fence
            )
            if not piece:
                raise ValueError("Feishu webhook payload exceeds the 20KB limit")
            current += piece
            remaining = remaining[len(piece) :]
            if remaining:
                flush()

        code_fence = candidate_code_fence

    if current:
        chunks.append(_close_code_block(current, code_fence))
    return tuple(chunks or ("",))


def send_feishu_markdown(
    webhook_url: str,
    title: str,
    markdown: str,
    post: Callable[..., Any] | None = None,
) -> None:
    sender = post or requests.post
    for chunk in _split_markdown(title, markdown):
        response = sender(webhook_url, json=_payload(title, chunk), timeout=20)
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict) or body.get("code") != 0:
            code = body.get("code") if isinstance(body, dict) else "invalid_response"
            raise RuntimeError(f"Feishu webhook returned nonzero code: {code}")
