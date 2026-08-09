# 任务 4 完成报告

## 实现

- 新增 `build_persona`：仅使用当前 `opportunity.category` 的匿名证据，按规范化 URL 去重并最多保留 5 条 `PersonaEvidence`。
- 新增 `build_journey`：固定输出“发现需求、搜索方案、对比决策、购买、使用、反馈”六阶段；没有直接证据的阶段明确标记待后续采集验证。
- `JourneyStage.name` 增加固定阶段名称校验。
- Gate 仅接受通过结果或低置信度结果；未满足条件时不构建中置信度以上结果。

## TDD 与验证

- 先新增失败测试并确认因 builder 不存在而失败。
- 模块测试：`4 passed`
- 全量回归：`85 passed`
- `git diff --check`：通过

## 范围与限制

- 未调用网络、ZIP、LLM。
- 未修改报告生成逻辑或 CLI。
- 画像与旅程未读取 author、账号、评论原文等身份字段。

