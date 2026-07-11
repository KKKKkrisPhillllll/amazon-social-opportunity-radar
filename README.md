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
