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
机会门槛 / 用户画像 / 六阶段用户旅程
        ↓
产品建议 / 改款建议 / 新品灵感
        ↓
本地 Markdown 日报 / 显式飞书推送
```

## 用户研究输出

研究层只解释和筛选已完成评分的机会，不会修改机会总分。日报只为总分至少 60 分、通过 Gate 的机会生成行为型用户画像与旅程；Gate 要求至少 2 条有效公开 URL，且来自至少 2 个独立来源。低置信度是 persona/journey builder 在证据不足时返回的结构化结果，不代表它会进入日报。CLI 日报在 Gate 不合格时不渲染画像/旅程章节；59 分及以下机会同样不会生成画像。

日报中的旅程使用 Mermaid 展示以下六阶段：

```mermaid
flowchart LR
    A[发现需求] --> B[搜索方案] --> C[对比决策] --> D[购买] --> E[使用] --> F[反馈]
```

六阶段顺序：发现需求 -> 搜索方案 -> 对比决策 -> 购买 -> 使用 -> 反馈。

画像只保留平台、公开 URL 和摘要，不包含作者、账号或其他个人身份字段。日报会列出公开证据链接；链接仅用于回溯采集到的线索，不能单独证明真实市场需求或产品可行性。

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
cd E:\vscode\amazon-social-opportunity-radar
$env:PYTHONPATH='src'
py -3 -m radar.cli --use-sample-data --output-dir outputs
```

样例报告会写入 `outputs/radar_report_YYYY_MM_DD.md`；它包含 1 个机会、1 条公开 URL、0 个画像/旅程，这是单证据未通过 Gate 时的预期行为。其中的名称、分数、证据 URL 和文案均为链路测试数据，不代表真实市场需求、市场热度或产品立项结论。

真实模式默认只写入本地 `outputs/radar_report_YYYY_MM_DD.md`，不会发送飞书：

```powershell
$env:PYTHONPATH='src'
py -3 -m radar.cli --max-keywords-per-category 1 --amazon-review-asin B0D3XTZVS5
```

确认本地报告后，使用显式开关发送飞书：

```powershell
$env:PYTHONPATH='src'
py -3 -m radar.cli --send-feishu --max-keywords-per-category 1
```

`scripts/run_daily.ps1` 用于 Windows 任务计划程序。任务运行账户需要拥有所需的环境变量；脚本会执行真实模式并发送飞书。

## 报告说明

日报会显示每个来源的采集数、去重数、健康状态和安全诊断代码。`NOT_CONFIGURED` 代表没有对应凭据或本机脚本路径；`PARTIAL` 代表返回结果为空或存在无法形成证据的记录；`DEGRADED` 代表使用了评论备用脚本或 Reddit 后备来源；`FAILED` 代表请求或脚本执行失败。

真实数据仍需人工核验内容相关性、关键词需求、竞品、利润、合规和供应商可行性。本项目不读取 Cookie、不写入社媒平台、不绕过访问控制。

## 验证

```powershell
$env:PYTHONPATH='src'
py -3 -m pytest -q
py -3 -m compileall -q src tests
py -3 -m ruff check src tests
py -3 -m pip check
git diff --check
```
