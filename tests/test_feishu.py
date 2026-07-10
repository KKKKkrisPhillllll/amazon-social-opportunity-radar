from radar.integrations.feishu import send_feishu_markdown


class FakeResponse:
    status_code = 200
    text = "ok"

    def raise_for_status(self):
        return None


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
