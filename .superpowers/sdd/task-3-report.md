# 模块三：Opportunity Gate 完成报告

## 状态

已完成并通过本地验证。

## 实现内容

- 新增 `OpportunityGate` 不可变结果模型及 `evaluate_opportunity_gate`。
- Gate 仅筛选与当前 `Opportunity.category` 相同的证据。
- 允许画像/旅程生成的条件：机会总分至少 60、当前类目证据至少 `min_evidence_count` 条、至少 2 个独立平台。
- `counter_evidence` 仅作为风险提示，不直接淘汰机会。
- VOC 与 `workarounds` 仅使用当前类目证据 ID，避免跨类目污染 strengths。
- 未修改 `Opportunity.score_breakdown` 或 `total_score` 的值。
- 保持匿名、仅使用传入的公开证据对象；未联网、未读取 ZIP。

## TDD 记录

1. 先新增 6 个 Gate 测试。
2. 首次运行因 `radar.opportunity_gate` 尚不存在而红灯。
3. 完成最小实现后，修正独立来源提示文案以匹配测试契约。
4. 模块测试通过：6 passed。

## 验证结果

- `py -m pytest tests/test_opportunity_gate.py -q`：6 passed。
- `py -m pytest -q`：79 passed。
- `git diff --check`：通过。

## 修改范围

- `src/radar/models.py`
- `src/radar/opportunity_gate.py`
- `tests/test_opportunity_gate.py`
- 本报告：`.superpowers/sdd/task-3-report.md`

## 风险

- Gate 假设传入的 `EvidenceItem` 已由模块一完成公开 URL 校验；Gate 不重复执行网络或 URL 解析。
- “独立来源”按 `EvidenceItem.platform` 去重，平台字段的规范化仍由上游负责。
## 修复记录

- 按 `evidence_id` 对当前类别证据去重，重复 ID 只保留首次证据，不再伪造证据数或独立平台数。
- 新增跨平台重复 ID 回归测试，以及总分恰好 60、证据恰好达到 `min_evidence_count`、评分字段不变测试。
- TDD：旧实现新增回归测试失败（1 failed, 7 passed）；最小修复后模块测试 8 passed，全量测试 81 passed。
- 未修改评分、采集器、报告生成或 CLI；`counter_evidence` 仍仅作为风险，VOC/workarounds 仍限当前类别。
