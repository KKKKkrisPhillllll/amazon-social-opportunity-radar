# 亚马逊社媒产品机会雷达

面向亚马逊产品经理的社媒机会发现 MVP。项目从小红书、Instagram、TikTok、YouTube、Reddit 采集公开内容，识别热点与用户痛点，形成产品开发建议，并通过飞书机器人每日推送。

## 当前工作流

```text
Apify 小红书采集器
ScrapeCreators Instagram / TikTok / YouTube / Reddit
        ↓
统一社媒记录与数据源健康状态
        ↓
按厨房电器、厨房收纳、家居收纳生成产品机会评分
        ↓
中文日报
        ↓
飞书自定义机器人
```

真实模式不会使用样例数据。缺少凭据时不会请求对应接口，也不会虚构产品机会，而是在报告中显示“未配置”。

## 安装

项目当前要求 Python 3.14 或更高版本。

```powershell
py -3 -m pip install -r requirements.txt
```

## 环境变量

凭据只通过环境变量注入，不要写入 YAML、代码、日志或 Git 提交。

```powershell
$env:APIFY_TOKEN="你的_Apify_Token"
$env:SCRAPECREATORS_API_KEY="你的_ScrapeCreators_API_Key"
$env:FEISHU_WEBHOOK_URL="你的_飞书机器人_Webhook"
```

亚马逊评论脚本路径使用以下环境变量预留，当前真实社媒 MVP 尚未自动调用评论脚本：

```powershell
$env:AMAZON_REVIEW_PRIMARY_SCRIPT="主评论脚本绝对路径"
$env:AMAZON_REVIEW_BACKUP_SCRIPT="备用评论脚本绝对路径"
```

## 配置

- `config/keywords.yaml`：重点类目、监控关键词和痛点词。
- `config/sources.example.yaml`：数据源开关、平台列表、Actor、环境变量名和单组关键词上限。
- `collection.max_keywords_per_group`：控制每个类目每天使用多少个关键词，MVP 默认值为 `1`，用于控制接口成本。

## 运行

真实 dry-run 只在终端输出报告，不发送飞书：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --dry-run
```

真实采集并推送飞书：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli
```

显式使用确定性样例数据：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --dry-run --use-sample-data
```

指定报告日期或配置文件：

```powershell
py -3 -m radar.cli `
  --dry-run `
  --report-date 2026-07-16 `
  --keywords-config config/keywords.yaml `
  --sources-config config/sources.example.yaml
```

## Windows 每日执行

`scripts/run_daily.ps1` 默认执行真实模式。可以在 Windows 任务计划程序中每天调用该脚本；任务进程必须能读取上述环境变量。

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts/run_daily.ps1
```

## 验证

```powershell
py -3 -m pytest -q
$env:PYTHONPATH="src"
py -3 -m radar.cli --dry-run --use-sample-data --report-date 2026-07-16
py -3 -m radar.cli --dry-run --report-date 2026-07-16
```

## 接口依据

- Apify 使用 `zhorex/rednote-xiaohongshu-scraper` 的同步运行并返回数据集接口。
- ScrapeCreators 按平台分别使用 Instagram Hashtag Search、TikTok Keyword Search、YouTube Search 和 Reddit Search，不使用通用猜测路由。
- 飞书使用自定义机器人的交互式消息卡，并在发送前检查 30 KB 限制与业务返回码。

## MVP 边界

- 已完成：五个平台真实连接器、按类目编排、来源降级、中文机会报告和飞书推送。
- 未完成：亚马逊评论自动编排、Amazon Keyword/竞品数据、数据库、管理后台和云端定时服务。
- 当前机会结论属于产品发现线索；正式立项前仍需继续验证亚马逊关键词、竞品评论、利润、合规、专利和供应链。
