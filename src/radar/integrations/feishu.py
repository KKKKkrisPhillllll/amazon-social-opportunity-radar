from __future__ import annotations

import json
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
    return len(
        json.dumps(
            _payload(title, markdown), ensure_ascii=False, separators=(",", ":")
        ).encode("utf-8")
    )


def _close_code_block(markdown: str, in_code_block: bool) -> str:
    if not in_code_block:
        return markdown
    separator = "" if markdown.endswith("\n") else "\n"
    return f"{markdown}{separator}{_CODE_FENCE}\n"


def _is_code_fence(line: str) -> bool:
    return line.lstrip().startswith(_CODE_FENCE)


def _largest_fitting_prefix(
    title: str,
    prefix: str,
    value: str,
    in_code_block: bool,
) -> str:
    low = 0
    high = len(value)
    while low < high:
        middle = (low + high + 1) // 2
        candidate = _close_code_block(prefix + value[:middle], in_code_block)
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
    in_code_block = False

    def flush() -> None:
        nonlocal current
        if current:
            chunks.append(_close_code_block(current, in_code_block))
            current = _CODE_FENCE + "\n" if in_code_block else ""

    for line in markdown.splitlines(keepends=True):
        fence_line = _is_code_fence(line)
        candidate_in_code_block = not in_code_block if fence_line else in_code_block
        candidate = current + line
        if _payload_size(
            title, _close_code_block(candidate, candidate_in_code_block)
        ) <= MAX_PAYLOAD_BYTES:
            current = candidate
            in_code_block = candidate_in_code_block
            continue

        if current:
            flush()

        remaining = line
        while remaining:
            candidate_in_code_block = (
                not in_code_block if fence_line else in_code_block
            )
            piece = _largest_fitting_prefix(
                title, current, remaining, candidate_in_code_block
            )
            if not piece:
                raise ValueError("Feishu webhook payload exceeds the 20KB limit")
            current += piece
            remaining = remaining[len(piece) :]
            if remaining:
                flush()

        in_code_block = candidate_in_code_block

    if current:
        chunks.append(_close_code_block(current, in_code_block))
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
