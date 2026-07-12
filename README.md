# Amazon Social Opportunity Radar

Configuration-driven MVP for discovering Amazon product development opportunities from Xiaohongshu, Instagram, TikTok, YouTube, Reddit, and Amazon reviews.

## Setup

```powershell
py -3 -m pip install -r requirements.txt
```

Set credentials through environment variables:

```powershell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."
$env:APIFY_TOKEN="your-apify-token"
$env:SCRAPECREATORS_API_KEY="your-scrapecreators-key"
```

Do not commit real API keys or webhook URLs.

## Dry Run

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --dry-run --use-sample-data
```

## Amazon 评论首跑

以下命令只采集一个 ASIN 的 Amazon 评论并写入本地报告；不会调用社媒来源、飞书或机会评分：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --amazon-review-asin B0D3XTZVS5 --dry-run
```

报告保存到 `outputs/amazon_review_report_B0D3XTZVS5_YYYYMMDD.md`。`outputs/` 已被 Git 忽略，真实评论数据不会被提交到仓库。

## Verify

```powershell
py -3 -m pytest -v
$env:PYTHONPATH="src"
py -3 -m radar.cli --dry-run --use-sample-data --report-date 2026-07-10
```

## Feishu Send

```powershell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."
$env:PYTHONPATH="src"
py -3 -m radar.cli --use-sample-data
```

`scripts/run_daily.ps1` can be called manually or from Windows Task Scheduler after `FEISHU_WEBHOOK_URL` is available to the scheduled process.
