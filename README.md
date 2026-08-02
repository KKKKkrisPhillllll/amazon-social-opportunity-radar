# 亚马逊社媒产品机会雷达

面向亚马逊产品开发的本地 MVP：从小红书、Instagram、TikTok、YouTube、Reddit 和亚马逊评论中收集可引用线索，完成去重、机会评分，并生成中文日报；只有显式指定时才会发送飞书。

## 工作流

```text
社媒热点 + 用户痛点 + 亚马逊评论
        ↓
字段标准化 + 证据去重 + 数据源健康诊断
        ↓
产品机会评分
        ↓
产品建议 / 改款建议 / 新品灵感
        ↓
本地 Markdown 日报 / 显式飞书推送
```

## 安装

```powershell
py -3 -m pip install -r requirements.txt
```

`config/sources.example.yaml` 只保存环境变量名，不保存 API Key、Webhook 或本机脚本路径。请按需设置：

```powershell
$env:APIFY_TOKEN="你的 Apify Token"
$env:SCRAPECREATORS_API_KEY="你的 ScrapeCreators API Key"
$env:REDDIT_CLIENT_ID="你的 Reddit Client ID"
$env:REDDIT_CLIENT_SECRET="你的 Reddit Client Secret"
$env:REDDIT_USER_AGENT="amazon-social-opportunity-radar/0.1"
$env:AMAZON_REVIEW_PRIMARY_SCRIPT="主评论脚本的本机路径"
$env:AMAZON_REVIEW_BACKUP_SCRIPT="备用评论脚本的本机路径"
$env:FEISHU_WEBHOOK_URL="飞书机器人 Webhook"
```

小红书使用 Apify Actor `zhorex/rednote-xiaohongshu-scraper`；Instagram、TikTok、YouTube、Reddit 使用 ScrapeCreators；PRAW 仅在 ScrapeCreators 的 Reddit 来源失败或未配置时，作为只读后备。亚马逊评论仅在指定 `--amazon-review-asin` 时执行，主脚本失败后自动尝试备用脚本。

## 运行

样例模式只验证本地链路，不产生真实业务结论，也不能发送飞书：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --dry-run --use-sample-data
```

真实模式默认只写入本地 `outputs/radar_report_YYYY_MM_DD.md`，不会发送飞书：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --max-keywords-per-category 1 --amazon-review-asin B0D3XTZVS5
```

确认本地报告后，使用显式开关发送飞书：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --send-feishu --max-keywords-per-category 1
```

`scripts/run_daily.ps1` 用于 Windows 任务计划程序。任务运行账户需要拥有所需的环境变量；脚本会执行真实模式并发送飞书。

## 报告说明

日报会显示每个来源的采集数、去重数、健康状态和安全诊断代码。`NOT_CONFIGURED` 代表没有对应凭据或本机脚本路径；`PARTIAL` 代表返回结果为空或存在无法形成证据的记录；`DEGRADED` 代表使用了评论备用脚本或 Reddit 后备来源；`FAILED` 代表请求或脚本执行失败。

真实数据仍需人工核验内容相关性、关键词需求、竞品、利润、合规和供应商可行性。本项目不读取 Cookie、不写入社媒平台、不绕过访问控制。

## 验证

```powershell
$env:PYTHONPATH="src"
py -3 -m pytest -v
py -3 -m compileall -q src
py -3 -m pip check
uvx pip-audit --requirement requirements.txt
```
