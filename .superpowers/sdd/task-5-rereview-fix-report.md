# 模块五二次复审修复报告

## 修复范围

修复 `task-5-rereview.md` 指出的飞书 Markdown 分片问题：

1. 分片预算改为使用 `requests.Request(..., json=payload).prepare()` 生成的真实请求体字节数。
2. 跨分片代码围栏保存原始开栏行和反引号长度；关闭与重开均使用相同标记。三反引号 Mermaid 保持兼容，四反引号和更长围栏得到覆盖。

## TDD 记录

先在 `tests/test_feishu.py` 新增两组回归测试并运行：

```text
py -3 -m pytest -q tests/test_feishu.py
2 failed, 4 passed
```

失败分别证明：

- 6800 个中文字符的第一片在真实 `requests` JSON 序列化后超过 `MAX_PAYLOAD_BYTES`。
- 四反引号围栏的续片使用了固定三反引号，未保留原始开栏标记。

实现最小修复后，增加五反引号参数化覆盖，并得到以下结果。

## 验证结果

```text
py -3 -m pytest -q tests/test_feishu.py tests/test_reports.py tests/test_cli.py
19 passed

py -3 -m pytest -q
99 passed

py -3 -m compileall -q src tests
exit 0

git diff --check
exit 0
```

## 变更文件

- `src/radar/integrations/feishu.py`
- `tests/test_feishu.py`
