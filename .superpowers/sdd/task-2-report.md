# 模块二：22 维 VOC 与创新信号

## 修改文件

- `config/voc_tags.yaml`
  - 保留并补充 22 个 VOC 维度及五组创新信号词表。
  - 为 `tradeoffs` 增加英文/中文对比词，支持 generic `but/但是/不过` 只有在同时命中第二个对比信号时成立。
- `src/radar/voc.py`
  - 新增 `classify_voc`、`detect_innovation_signals`、`load_voc_config`。
  - 只读取 `EvidenceItem.summary`，返回证据 ID 与主题/信号，不修改证据对象、不复制原文。
  - 英文关键词使用词边界，中文关键词使用包含匹配，空词忽略。
- `tests/test_voc.py`
  - 新增基础分类、反向证据、词边界、空词、trade-off 和配置完整性测试。

## TDD 记录

红灯命令：

```text
python -m pytest tests/test_voc.py -q
```

结果：环境没有 `python` 命令，解释器启动失败；改用可用的 `py -3` 后得到预期红灯：

```text
py -3 -m pytest tests/test_voc.py -q
ModuleNotFoundError: No module named 'radar.voc'
```

绿灯命令：

```text
py -3 -m pytest tests/test_voc.py -q
```

结果：`5 passed in 0.12s`。

## 回归测试

```text
py -3 -m pytest -q
```

结果：`62 passed in 1.74s`。

## 未解决风险

- `tradeoffs` 的“第二个对比信号”按同一信号词表中除 generic `but/但是/不过` 外的另一个命中词实现；没有联网或读取/复制 ZIP 源码，词表覆盖仍可能需要后续业务校准。
- 当前项目环境中 `python` 命令不可用，验证使用 `py -3`；Python 版本为 3.14.5。

## 本地提交

`592d98f` (`feat: 增加VOC主题与创新信号`)

## 配置边界修复（2026-08-09）

- 为损坏 YAML 增加明确的 `ValueError` 包装，保留原始解析异常作为 cause。
- 保持顶层、taxonomy、D01-D22、五组 signals 及字符串列表校验；字符串词表不会被拆成字符。
- 补充损坏 YAML 测试，并覆盖英文词边界、中文包含匹配和空词忽略；保留 `EvidenceItem.summary`、generic `but/但是/不过` 规则及现有返回接口。

验证结果：

```text
py -3 -m pytest tests/test_voc.py -q  -> 16 passed
py -3 -m pytest -q                    -> 73 passed
```
