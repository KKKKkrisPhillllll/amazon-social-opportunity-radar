import json

from radar.integrations.feishu import MAX_PAYLOAD_BYTES, send_feishu_markdown


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

    assert len(calls) == 1
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


def test_send_feishu_markdown_splits_utf8_payloads_without_breaking_code_blocks():
    calls = []

    def fake_post(url, json, timeout):
        calls.append(json)
        return FakeResponse()

    markdown = "中文画像报告\n\n```mermaid\n" + ("A --> B\n" * 5_000) + "```\n\n结论"
    send_feishu_markdown(
        "https://example.feishu/webhook", "Daily Radar", markdown, post=fake_post
    )

    contents = [call["card"]["elements"][0]["text"]["content"] for call in calls]
    assert len(calls) > 1
    assert all(
        len(json.dumps(call, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        <= MAX_PAYLOAD_BYTES
        for call in calls
    )
    assert all(content.count("```") % 2 == 0 for content in contents)
    assert any("```mermaid" in content for content in contents)


def test_send_feishu_markdown_splits_long_chinese_persona_report():
    calls = []

    def fake_post(url, json, timeout):
        calls.append(json)
        return FakeResponse()

    markdown = "中文画像报告\n" + ("公开证据：https://example.com/证据\n" * 2_000)
    send_feishu_markdown(
        "https://example.feishu/webhook", "Daily Radar", markdown, post=fake_post
    )

    assert len(markdown.encode("utf-8")) > MAX_PAYLOAD_BYTES
    assert len(calls) > 1
