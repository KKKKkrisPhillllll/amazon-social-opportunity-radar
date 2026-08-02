# 雷达 MVP 验收记录

日期：2026-08-02

## 已完成范围

- 小红书 Apify 搜索契约与字段映射。
- Instagram、TikTok、YouTube、Reddit 的 ScrapeCreators 专用端点。
- PRAW 只读 Reddit 后备来源。
- 跨来源 URL / 内容指纹去重、来源健康状态和安全诊断。
- 亚马逊评论主脚本与备用脚本的条件调度。
- 中文 Markdown 日报、证据链接、数据完整性提示与本地文件输出。
- 仅在 `--send-feishu` 时发送飞书，并校验 20KB 请求体上限和业务返回码。
- MIT 许可、中文 README、每日 PowerShell 入口和本地 GitHub Actions CI 配置。

## 本地验证结果

| 检查项 | 结果 |
| --- | --- |
| 单元测试 | 45 项通过 |
| 静态检查 | `ruff check .` 通过 |
| 编译检查 | `python -m compileall -q src` 通过 |
| 依赖一致性 | `python -m pip check` 通过 |
| 漏洞扫描 | `pip-audit --requirement requirements.txt` 未发现已知漏洞 |
| GitHub Actions 配置 | 本地 `ci.yml` 已验证为合法 YAML；远端发布需要 Token 的 `workflow` scope |
| 样例 CLI | `--dry-run --use-sample-data` 通过 |
| 无凭据真实 CLI | 正常生成本地报告，数据源显示 `NOT_CONFIGURED` |
| 凭据与路径泄露扫描 | 未发现本机私有路径或真实 Webhook |

## 凭据状态

本次只检查是否配置，未读取或输出任何值。以下变量均未配置：

- `APIFY_TOKEN`
- `SCRAPECREATORS_API_KEY`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`
- `REDDIT_USER_AGENT`
- `FEISHU_WEBHOOK_URL`
- `AMAZON_REVIEW_PRIMARY_SCRIPT`
- `AMAZON_REVIEW_BACKUP_SCRIPT`

因此本次没有发起真实社媒、Reddit、亚马逊评论或飞书网络请求，也没有产生外部服务费用。

## 尚未进行的外部验证

- 使用真实 Apify、ScrapeCreators 和 Reddit 凭据验证各供应商当前返回字段。
- 使用真实飞书 Webhook 验证消息实际送达。
- 在 Windows 任务计划程序中实际运行 `scripts/run_daily.ps1`。

这些项目需要相应凭据和外部服务可用，代码已在缺凭据时安全降级，不会以样例数据冒充真实结果。

## GitHub 同步限制

当前 GitHub Token 具备仓库写入权限，但没有 `workflow` scope，且 Git HTTPS 传输被当前网络重置。因此远端同步时不能发布 `.github/workflows/ci.yml`；其余可执行代码、配置、测试、README、许可和验收记录可以通过 GitHub API 安全同步。网络恢复并完成 `workflow` 授权后，再补传该 CI 文件即可。
