# Amazon 评论首跑设计

## 目标

为 `B0D3XTZVS5` 提供一次可审计的 Amazon 评论首跑。首跑只验证评论采集链路与评论证据输出，不调用社媒来源、不发送飞书、不生成跨来源机会评分。

## 输入与边界

- 输入 ASIN：`B0D3XTZVS5`。
- 复用 `config/sources.example.yaml` 中已有的主脚本与备用脚本配置结构。
- 真实密钥、Webhook 和评论原始数据不得写入 Git 仓库。
- 主脚本失败、超时、出现 `403` 或 `forbidden` 时，自动改用备用脚本。
- 两个脚本都不可用时，只报告真实状态，不创建示例评论替代结果。

## 命令与输出

新增仅用于评论首跑的命令参数：

```powershell
py -3 -m radar.cli --amazon-review-asin B0D3XTZVS5 --dry-run
```

命令读取来源配置，调用现有 `collect_amazon_reviews`，并生成本地 Markdown 报告。报告文件使用英文下划线命名：

```text
outputs/amazon_review_report_B0D3XTZVS5_YYYYMMDD.md
```

报告必须包含：

- ASIN 与运行日期。
- 评论来源状态：`OK`、`DEGRADED`、`FAILED` 或 `NOT_CONFIGURED`。
- 实际采集到的评论数量。
- 主脚本或备用脚本的实际使用结果。
- 评分低于或等于 3 星的评论证据；不足时明确显示实际条数。
- 不生成任何虚构的评分、评论、产品结论或机会分数。

## 组件职责

`src/radar/collectors/amazon_reviews.py` 继续只负责执行主备脚本、解析输出和返回标准化评论。

`src/radar/reports.py` 新增评论首跑报告渲染函数，只接收标准化评论与来源状态，不执行脚本。

`src/radar/cli.py` 负责解析 `--amazon-review-asin`，加载配置，调用采集器，将报告写入本地，并在 `--dry-run` 下打印报告内容。该路径不得调用飞书发送函数。

## 错误处理

- 配置文件、脚本路径或 ASIN 缺失：终止并显示明确错误。
- 主脚本受 AWS WAF 或其他错误影响：尝试备用脚本。
- 备用脚本也失败：生成状态为 `FAILED` 的本地报告，保留失败事实，不伪造评论。
- 报告目录不存在：程序负责创建目录。

## 测试与验收

- 使用模拟脚本结果测试主脚本成功、主脚本失败后备用成功、两个脚本均失败、脚本未配置。
- 测试报告仅展示真实输入评论，且在无评论时显示零条。
- 测试 CLI 写入英文下划线命名的本地报告，且不触发飞书请求。
- 真实验收命令使用 `B0D3XTZVS5`，输出的来源状态与实际脚本运行结果一致。

## 不在本轮范围内

- 小红书、Instagram、TikTok、YouTube、Reddit 采集。
- 飞书推送、Windows 定时任务与失败重试。
- 基于社媒和评论的产品机会评分。
