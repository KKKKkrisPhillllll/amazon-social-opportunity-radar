from radar.integrations.feishu import send_feishu_markdown


class FakeResponse:
    status_code = 200
    text = "ok"

    def raise_for_status(self):
        return None

    def json(self):
        return {"code": 0}


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


def test_send_feishu_markdown_rejects_nonzero_business_code():
    class FailedResponse(FakeResponse):
        def json(self):
            return {"code": 19001, "msg": "invalid"}

    def fake_post(url, json, timeout):
        return FailedResponse()

    try:
        send_feishu_markdown("https://example.feishu/webhook", "Daily Radar", "hello", post=fake_post)
    except RuntimeError as error:
        assert "code" in str(error)
    else:
        raise AssertionError("Expected a nonzero Feishu code to fail")


def test_send_feishu_markdown_rejects_payload_over_20kb_before_post():
    called = False

    def fake_post(url, json, timeout):
        nonlocal called
        called = True
        return FakeResponse()

    try:
        send_feishu_markdown(
            "https://example.feishu/webhook", "Daily Radar", "测" * 10_000, post=fake_post
        )
    except ValueError as error:
        assert "20KB" in str(error)
    else:
        raise AssertionError("Expected an oversized payload to fail")

    assert called is False
