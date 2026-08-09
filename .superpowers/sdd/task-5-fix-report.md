# 模块五审查修复报告

## 修复范围

已按 `task-5-fix-brief.md` 修复全部 2 个 Important 和 1 个 Minor，修改仅涉及：

- `src/radar/integrations/feishu.py`
- `src/radar/models.py`
- `src/radar/reports.py`
- `src/radar/cli.py`
- `tests/test_feishu.py`
- `tests/test_reports.py`
- `tests/test_cli.py`

未修改采集器、评分算法或公开证据边界；未推送 GitHub。

## TDD 记录

先补充失败测试并运行：

```powershell
py -3 -m pytest tests/test_feishu.py tests/test_reports.py tests/test_cli.py -q
```

红灯结果：`6 failed, 10 passed`。失败分别证明：

1. 超过 20KB 的飞书 Markdown 仍直接抛出 `ValueError`，未分片。
2. 画像公开证据未渲染匿名摘要。
3. 低于 60 分的画像仍渲染 Mermaid。
4. `PersonaJourneyResult` 没有 `gate_eligible` 字段，CLI 也未传递 Gate 资格。

完成最小实现后，同一组定向测试转绿：`16 passed`。

## 实施内容

### Important：飞书 UTF-8 安全分片

- 保持 `send_feishu_markdown(webhook_url, title, markdown, post=None)` 签名兼容。
- 按完整飞书 JSON payload 的 UTF-8 序列化字节数判断上限，确保每个请求不超过 `MAX_PAYLOAD_BYTES`。
- 短消息保持一次发送。
- 长消息按行分片；超长单行按字符边界切分，不截断 UTF-8 字符。
- 跨片的 Markdown 围栏代码块在前片闭合、后片重开，避免发送无效代码块。
- 覆盖 Mermaid 代码块与超长中文画像报告场景。

### Important：画像公开证据

- 画像的“公开证据”条目现在输出 `平台`、`URL` 和匿名 `摘要`。
- 渲染仅引用 `PersonaEvidence` 的公开字段，未引入 author、账户、评论正文或其他个人信息字段。

### Minor：报告 Gate 防御与资格传递

- `PersonaJourneyResult` 新增 `gate_eligible: bool = True`，默认值确保既有构造方式兼容。
- CLI 构建画像结果时写入真实 Gate 资格。
- `build_daily_markdown` 仅渲染 `gate_eligible` 且 `opportunity_score >= 60` 的画像结果；非空的低分或 Gate 不合格输入均不渲染画像章节与 Mermaid 图。

## 验证

```powershell
py -3 -m pytest tests/test_feishu.py tests/test_reports.py tests/test_cli.py -q
# 16 passed

py -3 -m compileall -q src tests
# 退出码 0

py -3 -m pytest -q
# 96 passed

git diff --check
# 退出码 0
```

## 不确定项与剩余项

无已知未解决项。飞书 webhook 的真实远端可用性未在测试中调用，HTTP 响应处理沿用既有实现并由注入的发送器回归测试覆盖。
