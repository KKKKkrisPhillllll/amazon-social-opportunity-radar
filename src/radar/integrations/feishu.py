from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import requests

MAX_PAYLOAD_BYTES = 20 * 1024


def send_feishu_markdown(
    webhook_url: str,
    title: str,
    markdown: str,
    post: Callable[..., Any] | None = None,
) -> None:
    sender = post or requests.post
    payload = {
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
    payload_size = len(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    )
    if payload_size > MAX_PAYLOAD_BYTES:
        raise ValueError("Feishu webhook payload exceeds the 20KB limit")
    response = sender(webhook_url, json=payload, timeout=20)
    response.raise_for_status()
    body = response.json()
    if not isinstance(body, dict) or body.get("code") != 0:
        code = body.get("code") if isinstance(body, dict) else "invalid_response"
        raise RuntimeError(f"Feishu webhook returned nonzero code: {code}")
