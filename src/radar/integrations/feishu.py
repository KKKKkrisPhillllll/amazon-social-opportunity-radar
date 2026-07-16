from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import requests


_MAX_CARD_BYTES = 30 * 1024


def build_feishu_payload(title: str, markdown: str) -> dict[str, Any]:
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
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(encoded) > _MAX_CARD_BYTES:
        raise ValueError("飞书消息卡超过 30 KB 限制。")
    return payload


def _validate_business_response(response: Any) -> None:
    parser = getattr(response, "json", None)
    if not callable(parser):
        return
    try:
        payload = parser()
    except Exception:
        raise RuntimeError("飞书 Webhook 返回了无效的 JSON。") from None
    if not isinstance(payload, dict):
        raise RuntimeError("飞书 Webhook 返回了无效的业务响应。")
    code = payload.get("code") if "code" in payload else payload.get("StatusCode")
    if code is not None and code not in (0, "0"):
        raise RuntimeError(f"飞书 Webhook 业务响应失败，code={code}。")


def send_feishu_markdown(
    webhook_url: str,
    title: str,
    markdown: str,
    post: Callable[..., Any] | None = None,
) -> None:
    sender = post or requests.post
    payload = build_feishu_payload(title, markdown)
    try:
        response = sender(webhook_url, json=payload, timeout=20)
    except Exception:
        raise RuntimeError("飞书 Webhook 请求失败。") from None
    try:
        response.raise_for_status()
    except Exception:
        status_code = getattr(response, "status_code", "unknown")
        raise RuntimeError(f"飞书 Webhook HTTP 请求失败，status={status_code}。") from None
    _validate_business_response(response)
