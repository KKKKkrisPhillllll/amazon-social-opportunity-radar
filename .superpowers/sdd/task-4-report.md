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

## 复审修复记录

- `_relevant_evidence` 现在排除空白摘要，避免占用证据配额、证据计数和置信度计算。
- 低置信度 Persona 的场景、核心目标、购买触发和顾虑改为“证据不足，待验证”，痛点主题保留并追加待验证提示。
- 补充空摘要、低置信度中性字段、Gate 拒绝、PersonaEvidence 字段契约与隐私边界回归测试；阶段顺序改用六个字面量名称断言。
- 修复本报告格式并通过 `git diff --check`。
