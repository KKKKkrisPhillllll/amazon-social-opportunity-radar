import pytest

from radar.integrations.feishu import send_feishu_markdown


class FakeResponse:
    def __init__(self, payload=None, status_code=200):
        self.payload = {"code": 0} if payload is None else payload
        self.status_code = status_code
        self.text = str(self.payload)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("HTTP request failed")

    def json(self):
        return self.payload


def test_send_feishu_markdown_posts_expected_payload():
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()

    send_feishu_markdown("https://example.feishu/webhook", "Daily Radar", "hello", post=fake_post)

    assert calls[0]["url"] == "https://example.feishu/webhook"
    assert calls[0]["json"]["msg_type"] == "interactive"
    assert calls[0]["json"]["card"]["header"]["title"]["content"] == "Daily Radar"
    assert calls[0]["json"]["card"]["elements"][0]["text"]["content"] == "hello"


def test_send_feishu_markdown_rejects_cards_over_30_kb_before_posting():
    def forbidden_post(*args, **kwargs):
        raise AssertionError("Oversized card must not be sent")

    with pytest.raises(ValueError, match="30 KB"):
        send_feishu_markdown(
            "https://example.feishu/webhook",
            "Daily Radar",
            "中" * 11_000,
            post=forbidden_post,
        )


@pytest.mark.parametrize("payload", [{"code": 0}, {"StatusCode": 0}])
def test_send_feishu_markdown_accepts_supported_success_codes(payload):
    def fake_post(url, json, timeout):
        return FakeResponse(payload)

    send_feishu_markdown("https://example.feishu/webhook", "Daily Radar", "hello", post=fake_post)


@pytest.mark.parametrize(
    "payload",
    [
        {"code": 19001, "msg": "bad request"},
        {"StatusCode": 19001, "StatusMessage": "bad request"},
    ],
)
def test_send_feishu_markdown_rejects_business_errors_without_leaking_webhook(payload):
    webhook = "https://example.feishu/webhook/secret-token"

    def fake_post(url, json, timeout):
        return FakeResponse(payload)

    with pytest.raises(RuntimeError) as error:
        send_feishu_markdown(webhook, "Daily Radar", "hello", post=fake_post)

    assert "19001" in str(error.value)
    assert webhook not in str(error.value)


def test_send_feishu_markdown_sanitizes_http_errors():
    webhook = "https://example.feishu/webhook/secret-token"

    def fake_post(url, json, timeout):
        return FakeResponse(status_code=500)

    with pytest.raises(RuntimeError) as error:
        send_feishu_markdown(webhook, "Daily Radar", "hello", post=fake_post)

    assert webhook not in str(error.value)
