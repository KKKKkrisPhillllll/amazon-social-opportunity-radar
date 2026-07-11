from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests


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
    response = sender(webhook_url, json=payload, timeout=20)
    response.raise_for_status()
