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
py -3 -m radar.cli --dry-run --use-sample-data
```
