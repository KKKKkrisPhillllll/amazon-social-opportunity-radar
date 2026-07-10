# Amazon Social Opportunity Radar MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working vertical slice of Amazon Social Opportunity Radar: load configured product keywords, normalize social/review records, score opportunities, generate a Markdown daily brief, and send it to Feishu.

**Architecture:** Use a small Python package with focused modules for configuration, collectors, normalization, scoring, reporting, and integrations. Source connectors return platform-specific raw records; normalizers convert them into shared dataclasses; scoring and reporting operate only on shared records.

**Tech Stack:** Python 3.14 through `py -3`, pytest, PyYAML, requests, Windows PowerShell runner.

## Global Constraints

- Project root: `E:\vscode\amazon-social-opportunity-radar`
- Default marketplace context: Amazon US unless configured differently.
- Primary categories: kitchen appliances, kitchen storage, home storage.
- Xiaohongshu source: Apify RedNote / Xiaohongshu Scraper.
- Instagram / TikTok / YouTube / Reddit source: ScrapeCreators.
- Primary Amazon review script: `C:\Users\Administrator\.claude\skills\amazon-review-scraper\scripts\amazon_review_scraper.py`
- Backup Amazon review script: `E:\gpt\gpt-skills\qypm-005-voc-product-definition\scripts\voc_reviews.py`
- Feishu webhook must come from environment variable `FEISHU_WEBHOOK_URL`; never commit real webhooks or API keys.
- Source health values must be exactly: `OK`, `PARTIAL`, `DEGRADED`, `FAILED`, `NOT_CONFIGURED`.
- V1 does not include a web dashboard, account system, billing, automatic supplier outreach, or platform access-control circumvention.

---

## File Structure

Create and modify these files:

- Modify: `.gitignore`
  - Preserve isolated-worktree and SDD ledger ignores; add secrets, local outputs, caches, and virtual environments.
- Create: `README.md`
  - Explain MVP purpose, setup, and safe credential handling.
- Create: `pyproject.toml`
  - Define package metadata and pytest settings.
- Create: `requirements.txt`
  - Runtime and test dependencies.
- Create: `config/keywords.yaml`
  - Default kitchen appliance/storage keyword groups.
- Create: `config/sources.example.yaml`
  - Safe example source config with environment variable names only.
- Create: `src/radar/__init__.py`
  - Package marker and version.
- Create: `src/radar/models.py`
  - Shared dataclasses and enums.
- Create: `src/radar/config.py`
  - Config loading and validation.
- Create: `src/radar/normalizers.py`
  - Convert raw social/review records into shared dataclasses.
- Create: `src/radar/scoring.py`
  - Score records and produce opportunity objects.
- Create: `src/radar/reports.py`
  - Generate Markdown daily brief.
- Create: `src/radar/integrations/__init__.py`
  - Integration package marker.
- Create: `src/radar/integrations/feishu.py`
  - Feishu webhook sender.
- Create: `src/radar/collectors/__init__.py`
  - Collector package marker.
- Create: `src/radar/collectors/sample.py`
  - Offline sample records for deterministic tests and dry runs.
- Create: `src/radar/collectors/amazon_reviews.py`
  - Local script failover wrapper.
- Create: `src/radar/collectors/apify_xiaohongshu.py`
  - Apify client with injected HTTP session for tests.
- Create: `src/radar/collectors/scrapecreators.py`
  - ScrapeCreators client with injected HTTP session for tests.
- Create: `src/radar/cli.py`
  - Command-line entrypoint for daily report.
- Create: `scripts/run_daily.ps1`
  - Windows runner for manual execution or Task Scheduler.
- Create: `tests/test_config.py`
- Create: `tests/test_normalizers.py`
- Create: `tests/test_scoring.py`
- Create: `tests/test_reports.py`
- Create: `tests/test_feishu.py`
- Create: `tests/test_amazon_reviews.py`
- Create: `tests/test_api_collectors.py`
- Create: `tests/test_cli.py`

---

### Task 1: Project Scaffold And Config Loading

**Files:**
- Modify: `.gitignore`
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `config/keywords.yaml`
- Create: `config/sources.example.yaml`
- Create: `src/radar/__init__.py`
- Create: `src/radar/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `radar.config.load_keywords(path: str | Path) -> dict`
- Produces: `radar.config.load_source_settings(path: str | Path) -> dict`
- Produces: `radar.config.require_env(name: str) -> str`

- [ ] **Step 1: Write the failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

import pytest

from radar.config import load_keywords, load_source_settings, require_env


def test_load_keywords_contains_v1_categories():
    data = load_keywords(Path("config/keywords.yaml"))

    assert data["marketplace"] == "amazon_us"
    assert "kitchen_appliances" in data["keyword_groups"]
    assert "kitchen_storage" in data["keyword_groups"]
    assert "pain_keywords" in data["keyword_groups"]
    assert "厨房收纳" in data["keyword_groups"]["kitchen_storage"]


def test_load_source_settings_uses_environment_variable_names_only():
    data = load_source_settings(Path("config/sources.example.yaml"))

    assert data["feishu"]["webhook_env"] == "FEISHU_WEBHOOK_URL"
    assert data["apify"]["token_env"] == "APIFY_TOKEN"
    assert data["scrapecreators"]["api_key_env"] == "SCRAPECREATORS_API_KEY"


def test_require_env_raises_clear_error(monkeypatch):
    monkeypatch.delenv("FEISHU_WEBHOOK_URL", raising=False)

    with pytest.raises(RuntimeError, match="FEISHU_WEBHOOK_URL"):
        require_env("FEISHU_WEBHOOK_URL")


def test_require_env_returns_value(monkeypatch):
    monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://example.feishu/webhook")

    assert require_env("FEISHU_WEBHOOK_URL") == "https://example.feishu/webhook"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pytest tests/test_config.py -v
```

Expected: FAIL because `requirements.txt`, `radar.config`, and config files do not exist yet.

- [ ] **Step 3: Add scaffold files**

Update `.gitignore`:

```gitignore
.worktrees/
.worktrees
.superpowers/sdd/
__pycache__/
.pytest_cache/
.venv/
venv/
*.pyc
*.pyo
.env
outputs/
data/raw/
data/processed/
*.log
```

Create `requirements.txt`:

```text
PyYAML>=6.0.2
pytest>=8.4.0
requests>=2.32.0
```

Create `pyproject.toml`:

```toml
[project]
name = "amazon-social-opportunity-radar"
version = "0.1.0"
description = "Configuration-driven social opportunity radar for Amazon product development."
requires-python = ">=3.14"
dependencies = [
  "PyYAML>=6.0.2",
  "requests>=2.32.0",
]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `config/keywords.yaml`:

```yaml
marketplace: amazon_us
focus_categories:
  - kitchen_appliances
  - kitchen_storage
  - home_storage
keyword_groups:
  kitchen_appliances:
    - 小厨房电器
    - 厨房神器
    - 懒人厨房电器
    - 空气炸锅
    - 破壁机
    - 电蒸锅
    - 早餐机
    - 多功能料理锅
    - 厨房小家电避雷
    - 厨房小家电推荐
  kitchen_storage:
    - 厨房收纳
    - 小厨房收纳
    - 橱柜收纳
    - 调料收纳
    - 冰箱收纳
    - 水槽收纳
    - 台面收纳
    - 锅具收纳
    - 保鲜盒收纳
    - 租房收纳
    - 收纳神器
    - 家居收纳好物
  pain_keywords:
    - 不好用
    - 踩雷
    - 后悔买
    - 闲置了
    - 太占地方
    - 难清洗
    - 不耐用
    - 没必要买
    - 平替
    - 真实测评
```

Create `config/sources.example.yaml`:

```yaml
feishu:
  webhook_env: FEISHU_WEBHOOK_URL
apify:
  token_env: APIFY_TOKEN
  xiaohongshu_actor: zhorex/rednote-xiaohongshu-scraper
scrapecreators:
  api_key_env: SCRAPECREATORS_API_KEY
amazon_reviews:
  primary_script: C:\Users\Administrator\.claude\skills\amazon-review-scraper\scripts\amazon_review_scraper.py
  backup_script: E:\gpt\gpt-skills\qypm-005-voc-product-definition\scripts\voc_reviews.py
```

Create `src/radar/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `README.md`:

```markdown
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
```

- [ ] **Step 4: Implement config loading**

Create `src/radar/config.py`:

```python
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: str | Path) -> dict[str, Any]:
    resolved = Path(path)
    if not resolved.exists():
        raise FileNotFoundError(f"Config file not found: {resolved}")
    with resolved.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a mapping: {resolved}")
    return data


def load_keywords(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    groups = data.get("keyword_groups")
    if not isinstance(groups, dict) or not groups:
        raise ValueError("keywords config requires non-empty keyword_groups")
    return data


def load_source_settings(path: str | Path) -> dict[str, Any]:
    data = _load_yaml(path)
    for key in ("feishu", "apify", "scrapecreators", "amazon_reviews"):
        if key not in data:
            raise ValueError(f"sources config missing required section: {key}")
    return data


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required environment variable is not configured: {name}")
    return value
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```powershell
py -3 -m pip install -r requirements.txt
py -3 -m pytest tests/test_config.py -v
```

Expected: 4 passed.

- [ ] **Step 6: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add .gitignore README.md pyproject.toml requirements.txt config src/radar/__init__.py src/radar/config.py tests/test_config.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add project scaffold and config loading"
```

---

### Task 2: Shared Models And Normalizers

**Files:**
- Create: `src/radar/models.py`
- Create: `src/radar/normalizers.py`
- Test: `tests/test_normalizers.py`

**Interfaces:**
- Produces: `SourceHealth` enum
- Produces: `SocialRecord` dataclass
- Produces: `ReviewRecord` dataclass
- Produces: `Opportunity` dataclass
- Produces: `normalize_social_record(raw: dict, platform: str, keyword: str) -> SocialRecord`
- Produces: `normalize_review_record(raw: dict, source_script: str, raw_source_path: str) -> ReviewRecord`

- [ ] **Step 1: Write failing normalizer tests**

Create `tests/test_normalizers.py`:

```python
from radar.models import SourceHealth
from radar.normalizers import normalize_review_record, normalize_social_record


def test_normalize_social_record_maps_common_fields():
    record = normalize_social_record(
        {
            "url": "https://example.com/post/1",
            "title": "Small kitchen storage idea",
            "text": "Hard to clean but saves space",
            "likes": 120,
            "comments": [{"text": "I need this for spices"}],
        },
        platform="xiaohongshu",
        keyword="厨房收纳",
    )

    assert record.platform == "xiaohongshu"
    assert record.keyword == "厨房收纳"
    assert record.url == "https://example.com/post/1"
    assert record.title == "Small kitchen storage idea"
    assert record.engagement["likes"] == 120
    assert record.comments == ["I need this for spices"]
    assert record.health is SourceHealth.OK


def test_normalize_review_record_maps_review_fields():
    record = normalize_review_record(
        {
            "asin": "B012345678",
            "rating": 2,
            "title": "Hard to clean",
            "review_text": "The product works but cleaning is painful.",
            "date": "2026-07-01",
            "verified": True,
            "helpful": 8,
        },
        source_script="primary",
        raw_source_path="reviews.json",
    )

    assert record.asin == "B012345678"
    assert record.rating == 2.0
    assert record.title == "Hard to clean"
    assert record.verified is True
    assert record.source_script == "primary"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_normalizers.py -v
```

Expected: FAIL because `radar.models` and `radar.normalizers` do not exist yet.

- [ ] **Step 3: Implement shared models**

Create `src/radar/models.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SourceHealth(str, Enum):
    OK = "OK"
    PARTIAL = "PARTIAL"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    NOT_CONFIGURED = "NOT_CONFIGURED"


@dataclass(frozen=True)
class SocialRecord:
    platform: str
    keyword: str
    url: str
    title: str
    text: str
    author: str = ""
    published_at: str = ""
    tags: list[str] = field(default_factory=list)
    engagement: dict[str, int | float] = field(default_factory=dict)
    comments: list[str] = field(default_factory=list)
    health: SourceHealth = SourceHealth.OK


@dataclass(frozen=True)
class ReviewRecord:
    asin: str
    rating: float
    title: str
    review_text: str
    review_date: str = ""
    verified: bool | None = None
    helpful_count: int | None = None
    source_script: str = ""
    raw_source_path: str = ""
    health: SourceHealth = SourceHealth.OK


@dataclass(frozen=True)
class Opportunity:
    title: str
    category: str
    source_platforms: list[str]
    evidence_summary: str
    customer_pain_point: str
    product_idea: str
    amazon_validation_keywords: list[str]
    suggested_asins: list[str]
    differentiation_angle: str
    risk_notes: str
    next_action: str
    score_breakdown: dict[str, int]

    @property
    def total_score(self) -> int:
        return sum(self.score_breakdown.values())
```

- [ ] **Step 4: Implement normalizers**

Create `src/radar/normalizers.py`:

```python
from __future__ import annotations

from typing import Any

from radar.models import ReviewRecord, SocialRecord, SourceHealth


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _comments(raw_comments: Any) -> list[str]:
    if not isinstance(raw_comments, list):
        return []
    result: list[str] = []
    for item in raw_comments:
        if isinstance(item, dict):
            text = _text(item.get("text") or item.get("content") or item.get("comment"))
        else:
            text = _text(item)
        if text:
            result.append(text)
    return result


def normalize_social_record(raw: dict[str, Any], platform: str, keyword: str) -> SocialRecord:
    engagement = {
        "likes": _int(raw.get("likes") or raw.get("like_count")),
        "favorites": _int(raw.get("favorites") or raw.get("collect_count")),
        "comments": _int(raw.get("comment_count") or len(raw.get("comments", []))),
    }
    tags = raw.get("tags") if isinstance(raw.get("tags"), list) else []
    return SocialRecord(
        platform=platform,
        keyword=keyword,
        url=_text(raw.get("url") or raw.get("link") or raw.get("note_url")),
        title=_text(raw.get("title") or raw.get("caption")),
        text=_text(raw.get("text") or raw.get("body") or raw.get("description")),
        author=_text(raw.get("author") or raw.get("username") or raw.get("channel")),
        published_at=_text(raw.get("published_at") or raw.get("date")),
        tags=[_text(tag) for tag in tags if _text(tag)],
        engagement=engagement,
        comments=_comments(raw.get("comments")),
        health=SourceHealth.OK,
    )


def normalize_review_record(raw: dict[str, Any], source_script: str, raw_source_path: str) -> ReviewRecord:
    helpful = raw.get("helpful") if raw.get("helpful") is not None else raw.get("helpful_count")
    return ReviewRecord(
        asin=_text(raw.get("asin") or raw.get("ASIN")),
        rating=_number(raw.get("rating")),
        title=_text(raw.get("title") or raw.get("review_title")),
        review_text=_text(raw.get("review_text") or raw.get("text") or raw.get("content")),
        review_date=_text(raw.get("date") or raw.get("review_date")),
        verified=raw.get("verified") if isinstance(raw.get("verified"), bool) else None,
        helpful_count=_int(helpful) if helpful is not None else None,
        source_script=source_script,
        raw_source_path=raw_source_path,
        health=SourceHealth.OK,
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```powershell
py -3 -m pytest tests/test_normalizers.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/radar/models.py src/radar/normalizers.py tests/test_normalizers.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add shared records and normalizers"
```

---

### Task 3: Opportunity Scoring

**Files:**
- Create: `src/radar/scoring.py`
- Test: `tests/test_scoring.py`

**Interfaces:**
- Consumes: `SocialRecord`, `ReviewRecord`, `Opportunity`
- Produces: `score_opportunity(social_records: list[SocialRecord], review_records: list[ReviewRecord], category: str, keywords: list[str]) -> Opportunity`

- [ ] **Step 1: Write failing scoring tests**

Create `tests/test_scoring.py`:

```python
from radar.models import ReviewRecord, SocialRecord
from radar.scoring import score_opportunity


def test_score_opportunity_rewards_heat_pain_reviews_and_fit():
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="厨房收纳",
            url="https://example.com/a",
            title="厨房收纳神器",
            text="小厨房太占地方, 这个能解决调料乱的问题",
            engagement={"likes": 300, "favorites": 120, "comments": 30},
            comments=["难清洗吗", "我家调料也乱"],
        )
    ]
    review_records = [
        ReviewRecord(
            asin="B012345678",
            rating=2,
            title="Hard to clean",
            review_text="Useful but hard to clean and takes too much space.",
        )
    ]

    opportunity = score_opportunity(
        social_records=social_records,
        review_records=review_records,
        category="kitchen_storage",
        keywords=["kitchen organizer", "spice rack organizer"],
    )

    assert opportunity.category == "kitchen_storage"
    assert opportunity.total_score >= 60
    assert opportunity.score_breakdown["social_heat"] > 0
    assert opportunity.score_breakdown["pain_intensity"] > 0
    assert opportunity.score_breakdown["amazon_review_validation"] > 0
    assert "kitchen organizer" in opportunity.amazon_validation_keywords
    assert opportunity.suggested_asins == ["B012345678"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
py -3 -m pytest tests/test_scoring.py -v
```

Expected: FAIL because `radar.scoring` does not exist.

- [ ] **Step 3: Implement scoring**

Create `src/radar/scoring.py`:

```python
from __future__ import annotations

from radar.models import Opportunity, ReviewRecord, SocialRecord

PAIN_TERMS = [
    "不好用",
    "踩雷",
    "后悔",
    "闲置",
    "太占地方",
    "难清洗",
    "不耐用",
    "hard to clean",
    "takes too much space",
    "broke",
    "leak",
]


def _clamp(value: int, maximum: int) -> int:
    return max(0, min(value, maximum))


def _social_heat(records: list[SocialRecord]) -> int:
    raw = 0
    for record in records:
        raw += int(record.engagement.get("likes", 0))
        raw += int(record.engagement.get("favorites", 0)) * 2
        raw += int(record.engagement.get("comments", 0)) * 3
    return _clamp(raw // 20, 25)


def _pain_intensity(social_records: list[SocialRecord], review_records: list[ReviewRecord]) -> int:
    text = " ".join(
        [record.title + " " + record.text + " " + " ".join(record.comments) for record in social_records]
        + [record.title + " " + record.review_text for record in review_records]
    ).lower()
    matches = sum(1 for term in PAIN_TERMS if term.lower() in text)
    return _clamp(matches * 6, 25)


def _amazon_review_validation(review_records: list[ReviewRecord]) -> int:
    if not review_records:
        return 0
    low_rating_count = sum(1 for record in review_records if record.rating and record.rating <= 3)
    return _clamp(8 + low_rating_count * 4, 20)


def _product_fit(category: str, social_records: list[SocialRecord]) -> int:
    category_terms = {
        "kitchen_appliances": ["电器", "air fryer", "appliance", "cooker"],
        "kitchen_storage": ["收纳", "storage", "organizer", "rack"],
        "home_storage": ["家居", "storage", "organizer"],
    }
    text = " ".join(record.title + " " + record.text for record in social_records).lower()
    matches = sum(1 for term in category_terms.get(category, []) if term.lower() in text)
    return _clamp(6 + matches * 3, 15)


def _business_feasibility(keywords: list[str], review_records: list[ReviewRecord]) -> int:
    score = 5
    if keywords:
        score += 5
    if review_records:
        score += 5
    return _clamp(score, 15)


def score_opportunity(
    social_records: list[SocialRecord],
    review_records: list[ReviewRecord],
    category: str,
    keywords: list[str],
) -> Opportunity:
    platforms = sorted({record.platform for record in social_records})
    asins = sorted({record.asin for record in review_records if record.asin})
    title = social_records[0].title if social_records else "Amazon product opportunity"
    pain = "Potential user pain found in social discussion and Amazon reviews."
    if review_records:
        pain = review_records[0].title or pain
    breakdown = {
        "social_heat": _social_heat(social_records),
        "pain_intensity": _pain_intensity(social_records, review_records),
        "amazon_review_validation": _amazon_review_validation(review_records),
        "product_development_fit": _product_fit(category, social_records),
        "amazon_business_feasibility": _business_feasibility(keywords, review_records),
    }
    return Opportunity(
        title=title,
        category=category,
        source_platforms=platforms,
        evidence_summary=f"{len(social_records)} social records and {len(review_records)} review records analyzed.",
        customer_pain_point=pain,
        product_idea="Turn repeated social pain points into a differentiated Amazon offer.",
        amazon_validation_keywords=keywords,
        suggested_asins=asins,
        differentiation_angle="Improve the most repeated complaint before sourcing or listing.",
        risk_notes="Validate keyword demand, review barrier, margin, compliance, and supplier feasibility before launch.",
        next_action="Run Amazon keyword and competitor validation for this opportunity.",
        score_breakdown=breakdown,
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
py -3 -m pytest tests/test_scoring.py -v
```

Expected: 1 passed.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/radar/scoring.py tests/test_scoring.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add opportunity scoring"
```

---

### Task 4: Markdown Report And Feishu Integration

**Files:**
- Create: `src/radar/reports.py`
- Create: `src/radar/integrations/__init__.py`
- Create: `src/radar/integrations/feishu.py`
- Test: `tests/test_reports.py`
- Test: `tests/test_feishu.py`

**Interfaces:**
- Consumes: `Opportunity`, `SourceHealth`
- Produces: `build_daily_markdown(opportunities: list[Opportunity], source_health: dict[str, SourceHealth], report_date: str, focus: str) -> str`
- Produces: `send_feishu_markdown(webhook_url: str, title: str, markdown: str, post=None) -> None`

- [ ] **Step 1: Write failing report tests**

Create `tests/test_reports.py`:

```python
from radar.models import Opportunity, SourceHealth
from radar.reports import build_daily_markdown


def test_build_daily_markdown_contains_sections_and_health():
    opportunity = Opportunity(
        title="厨房收纳神器",
        category="kitchen_storage",
        source_platforms=["xiaohongshu"],
        evidence_summary="1 social record and 1 review record analyzed.",
        customer_pain_point="Hard to clean",
        product_idea="Create an easier-to-clean organizer.",
        amazon_validation_keywords=["kitchen organizer"],
        suggested_asins=["B012345678"],
        differentiation_angle="Removable washable parts",
        risk_notes="Validate margin.",
        next_action="Check Amazon reviews.",
        score_breakdown={
            "social_heat": 20,
            "pain_intensity": 18,
            "amazon_review_validation": 12,
            "product_development_fit": 10,
            "amazon_business_feasibility": 10,
        },
    )

    markdown = build_daily_markdown(
        [opportunity],
        {"xiaohongshu": SourceHealth.OK, "scrapecreators": SourceHealth.NOT_CONFIGURED},
        report_date="2026-07-10",
        focus="Kitchen appliances / kitchen storage / home storage",
    )

    assert "# Amazon Social Opportunity Radar" in markdown
    assert "## 1. Top Opportunities" in markdown
    assert "厨房收纳神器" in markdown
    assert "Score: 70" in markdown
    assert "## 7. Data Source Health" in markdown
    assert "scrapecreators: NOT_CONFIGURED" in markdown
```

Create `tests/test_feishu.py`:

```python
from radar.integrations.feishu import send_feishu_markdown


class FakeResponse:
    status_code = 200
    text = "ok"

    def raise_for_status(self):
        return None


def test_send_feishu_markdown_posts_expected_payload():
    calls = []

    def fake_post(url, json, timeout):
        calls.append({"url": url, "json": json, "timeout": timeout})
        return FakeResponse()

    send_feishu_markdown("https://example.feishu/webhook", "Daily Radar", "hello", post=fake_post)

    assert calls[0]["url"] == "https://example.feishu/webhook"
    assert calls[0]["json"]["msg_type"] == "interactive"
    assert calls[0]["json"]["card"]["header"]["title"]["content"] == "Daily Radar"
    assert calls[0]["json"]["card"]["elements"][0]["text"]["content"] == "hello"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_reports.py tests/test_feishu.py -v
```

Expected: FAIL because report and Feishu modules do not exist.

- [ ] **Step 3: Implement report generation**

Create `src/radar/reports.py`:

```python
from __future__ import annotations

from radar.models import Opportunity, SourceHealth


def _score_lines(opportunity: Opportunity) -> list[str]:
    lines = [f"- Score: {opportunity.total_score}"]
    for name, value in opportunity.score_breakdown.items():
        lines.append(f"  - {name}: {value}")
    return lines


def build_daily_markdown(
    opportunities: list[Opportunity],
    source_health: dict[str, SourceHealth],
    report_date: str,
    focus: str,
) -> str:
    lines: list[str] = [
        "# Amazon Social Opportunity Radar",
        "",
        f"Date: {report_date}",
        f"Focus: {focus}",
        "",
        "## 1. Top Opportunities",
        "",
    ]
    if not opportunities:
        lines.append("No qualified opportunities found today.")
    for index, opportunity in enumerate(sorted(opportunities, key=lambda item: item.total_score, reverse=True), start=1):
        lines.extend(
            [
                f"### Opportunity {index}: {opportunity.title}",
                *_score_lines(opportunity),
                f"- Category: {opportunity.category}",
                f"- Source: {', '.join(opportunity.source_platforms) or 'unknown'}",
                f"- Customer pain: {opportunity.customer_pain_point}",
                f"- Product idea: {opportunity.product_idea}",
                f"- Amazon validation keywords: {', '.join(opportunity.amazon_validation_keywords) or 'not available'}",
                f"- Suggested ASIN review check: {', '.join(opportunity.suggested_asins) or 'not available'}",
                f"- Differentiation angle: {opportunity.differentiation_angle}",
                f"- Risk: {opportunity.risk_notes}",
                f"- Next action: {opportunity.next_action}",
                "",
            ]
        )
    lines.extend(
        [
            "## 2. Hot Trends",
            "See Top Opportunities sorted by total score.",
            "",
            "## 3. High-Frequency Pain Points",
            "See each opportunity's customer pain field.",
            "",
            "## 4. Product Improvement Ideas",
            "See each opportunity's differentiation angle.",
            "",
            "## 5. New Product Inspiration",
            "See each opportunity's product idea.",
            "",
            "## 6. Items Needing Amazon Review Validation",
            "Items without suggested ASINs need competitor ASIN discovery before review validation.",
            "",
            "## 7. Data Source Health",
        ]
    )
    for name, health in sorted(source_health.items()):
        lines.append(f"- {name}: {health.value}")
    return "\n".join(lines).strip() + "\n"
```

- [ ] **Step 4: Implement Feishu sender**

Create `src/radar/integrations/__init__.py`:

```python
"""External service integrations."""
```

Create `src/radar/integrations/feishu.py`:

```python
from __future__ import annotations

from collections.abc import Callable
from typing import Any

import requests


def send_feishu_markdown(
    webhook_url: str,
    title: str,
    markdown: str,
    post: Callable[..., Any] | None = None,
) -> None:
    sender = post or requests.post
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": title,
                }
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": markdown,
                }
            ],
        },
    }
    response = sender(webhook_url, json=payload, timeout=20)
    response.raise_for_status()
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```powershell
py -3 -m pytest tests/test_reports.py tests/test_feishu.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/radar/reports.py src/radar/integrations tests/test_reports.py tests/test_feishu.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add daily report and feishu sender"
```

---

### Task 5: Amazon Review Script Failover Collector

**Files:**
- Create: `src/radar/collectors/__init__.py`
- Create: `src/radar/collectors/amazon_reviews.py`
- Test: `tests/test_amazon_reviews.py`

**Interfaces:**
- Consumes: `ReviewRecord`, `SourceHealth`
- Produces: `collect_amazon_reviews(asin: str, primary_script: Path, backup_script: Path, runner=None) -> tuple[list[ReviewRecord], SourceHealth]`

- [ ] **Step 1: Write failing failover tests**

Create `tests/test_amazon_reviews.py`:

```python
from pathlib import Path

from radar.collectors.amazon_reviews import collect_amazon_reviews
from radar.models import SourceHealth


class FakeCompleted:
    def __init__(self, returncode, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_collect_amazon_reviews_uses_primary_when_success(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")

    def runner(command, capture_output, text, timeout):
        return FakeCompleted(
            0,
            stdout='[{"asin":"B012345678","rating":2,"title":"Bad","review_text":"Hard to clean"}]',
        )

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.OK
    assert records[0].source_script == "primary"
    assert records[0].asin == "B012345678"


def test_collect_amazon_reviews_falls_back_to_backup_on_forbidden(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    calls = []

    def runner(command, capture_output, text, timeout):
        calls.append(command)
        if len(calls) == 1:
            return FakeCompleted(1, stdout="", stderr="HTTP 403 Forbidden")
        return FakeCompleted(
            0,
            stdout='{"reviews":[{"asin":"B012345678","rating":1,"title":"Broken","review_text":"Broke quickly"}]}',
        )

    records, health = collect_amazon_reviews("B012345678", primary, backup, runner=runner)

    assert health is SourceHealth.DEGRADED
    assert records[0].source_script == "backup"
    assert len(calls) == 2


def test_collect_amazon_reviews_reports_not_configured_when_scripts_missing(tmp_path):
    records, health = collect_amazon_reviews(
        "B012345678",
        tmp_path / "missing-primary.py",
        tmp_path / "missing-backup.py",
    )

    assert records == []
    assert health is SourceHealth.NOT_CONFIGURED
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_amazon_reviews.py -v
```

Expected: FAIL because collector does not exist.

- [ ] **Step 3: Implement collector**

Create `src/radar/collectors/__init__.py`:

```python
"""Data collectors for social and Amazon sources."""
```

Create `src/radar/collectors/amazon_reviews.py`:

```python
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from radar.models import ReviewRecord, SourceHealth
from radar.normalizers import normalize_review_record


def _extract_reviews(stdout: str) -> list[dict[str, Any]]:
    data = json.loads(stdout)
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("reviews"), list):
        return [item for item in data["reviews"] if isinstance(item, dict)]
    return []


def _run_script(script: Path, asin: str, runner) -> tuple[list[dict[str, Any]], bool]:
    command = ["py", "-3", str(script), asin]
    completed = runner(command, capture_output=True, text=True, timeout=120)
    combined = f"{completed.stdout}\n{completed.stderr}".lower()
    if completed.returncode != 0 or "403" in combined or "forbidden" in combined:
        return [], False
    try:
        reviews = _extract_reviews(completed.stdout)
    except json.JSONDecodeError:
        return [], False
    return reviews, bool(reviews)


def collect_amazon_reviews(
    asin: str,
    primary_script: Path,
    backup_script: Path,
    runner=None,
) -> tuple[list[ReviewRecord], SourceHealth]:
    runner = runner or subprocess.run
    primary_exists = primary_script.exists()
    backup_exists = backup_script.exists()
    if not primary_exists and not backup_exists:
        return [], SourceHealth.NOT_CONFIGURED

    if primary_exists:
        primary_reviews, primary_ok = _run_script(primary_script, asin, runner)
        if primary_ok:
            return [
                normalize_review_record(item, "primary", str(primary_script))
                for item in primary_reviews
            ], SourceHealth.OK

    if backup_exists:
        backup_reviews, backup_ok = _run_script(backup_script, asin, runner)
        if backup_ok:
            return [
                normalize_review_record(item, "backup", str(backup_script))
                for item in backup_reviews
            ], SourceHealth.DEGRADED

    return [], SourceHealth.FAILED
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
py -3 -m pytest tests/test_amazon_reviews.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/radar/collectors tests/test_amazon_reviews.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add amazon review failover collector"
```

---

### Task 6: API Collectors With Testable HTTP Boundaries

**Files:**
- Create: `src/radar/collectors/apify_xiaohongshu.py`
- Create: `src/radar/collectors/scrapecreators.py`
- Test: `tests/test_api_collectors.py`

**Interfaces:**
- Consumes: `normalize_social_record`
- Produces: `collect_xiaohongshu(keyword: str, token: str, actor: str, session=None) -> tuple[list[SocialRecord], SourceHealth]`
- Produces: `collect_scrapecreators(platform: str, keyword: str, api_key: str, session=None) -> tuple[list[SocialRecord], SourceHealth]`

- [ ] **Step 1: Write failing API collector tests**

Create `tests/test_api_collectors.py`:

```python
from radar.collectors.apify_xiaohongshu import collect_xiaohongshu
from radar.collectors.scrapecreators import collect_scrapecreators
from radar.models import SourceHealth


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code
        self.text = str(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.text)


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append({"method": "GET", "url": url, "kwargs": kwargs})
        return FakeResponse(self.payload)

    def post(self, url, **kwargs):
        self.calls.append({"method": "POST", "url": url, "kwargs": kwargs})
        return FakeResponse(self.payload)


def test_collect_xiaohongshu_normalizes_apify_items():
    session = FakeSession(
        [
            {
                "url": "https://xiaohongshu.com/a",
                "title": "厨房收纳",
                "text": "太占地方",
                "likes": 50,
                "comments": [{"text": "后悔买"}],
            }
        ]
    )

    records, health = collect_xiaohongshu("厨房收纳", "token", "actor/name", session=session)

    assert health is SourceHealth.OK
    assert records[0].platform == "xiaohongshu"
    assert records[0].keyword == "厨房收纳"


def test_collect_scrapecreators_normalizes_items():
    session = FakeSession(
        {
            "items": [
                {
                    "url": "https://reddit.com/r/test",
                    "title": "Kitchen storage pain",
                    "text": "hard to clean",
                    "likes": 5,
                }
            ]
        }
    )

    records, health = collect_scrapecreators("reddit", "kitchen storage", "key", session=session)

    assert health is SourceHealth.OK
    assert records[0].platform == "reddit"
    assert records[0].title == "Kitchen storage pain"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
py -3 -m pytest tests/test_api_collectors.py -v
```

Expected: FAIL because API collectors do not exist.

- [ ] **Step 3: Implement Apify Xiaohongshu collector**

Create `src/radar/collectors/apify_xiaohongshu.py`:

```python
from __future__ import annotations

from typing import Any

import requests

from radar.models import SocialRecord, SourceHealth
from radar.normalizers import normalize_social_record


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def collect_xiaohongshu(
    keyword: str,
    token: str,
    actor: str,
    session=None,
) -> tuple[list[SocialRecord], SourceHealth]:
    client = session or requests.Session()
    url = f"https://api.apify.com/v2/acts/{actor}/run-sync-get-dataset-items"
    response = client.post(
        url,
        params={"token": token},
        json={"keyword": keyword, "maxItems": 20},
        timeout=120,
    )
    response.raise_for_status()
    records = [
        normalize_social_record(item, platform="xiaohongshu", keyword=keyword)
        for item in _items(response.json())
    ]
    return records, SourceHealth.OK if records else SourceHealth.PARTIAL
```

- [ ] **Step 4: Implement ScrapeCreators collector**

Create `src/radar/collectors/scrapecreators.py`:

```python
from __future__ import annotations

from typing import Any

import requests

from radar.models import SocialRecord, SourceHealth
from radar.normalizers import normalize_social_record


def _items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("items", "data", "results", "posts"):
            if isinstance(payload.get(key), list):
                return [item for item in payload[key] if isinstance(item, dict)]
    return []


def collect_scrapecreators(
    platform: str,
    keyword: str,
    api_key: str,
    session=None,
) -> tuple[list[SocialRecord], SourceHealth]:
    client = session or requests.Session()
    url = f"https://api.scrapecreators.com/v1/{platform}/search"
    response = client.get(
        url,
        headers={"x-api-key": api_key},
        params={"query": keyword, "limit": 20},
        timeout=60,
    )
    response.raise_for_status()
    records = [
        normalize_social_record(item, platform=platform, keyword=keyword)
        for item in _items(response.json())
    ]
    return records, SourceHealth.OK if records else SourceHealth.PARTIAL
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```powershell
py -3 -m pytest tests/test_api_collectors.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/radar/collectors/apify_xiaohongshu.py src/radar/collectors/scrapecreators.py tests/test_api_collectors.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add social api collectors"
```

---

### Task 7: CLI, Sample Data, And Windows Runner

**Files:**
- Create: `src/radar/collectors/sample.py`
- Create: `src/radar/cli.py`
- Create: `scripts/run_daily.ps1`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: all previous modules.
- Produces: `build_sample_records() -> tuple[list[SocialRecord], list[ReviewRecord]]`
- Produces: CLI command `py -3 -m radar.cli --dry-run --use-sample-data`

- [ ] **Step 1: Write failing CLI test**

Create `tests/test_cli.py`:

```python
from radar.cli import main


def test_cli_dry_run_prints_report(capsys):
    exit_code = main(["--dry-run", "--use-sample-data", "--report-date", "2026-07-10"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Amazon Social Opportunity Radar" in captured.out
    assert "Data Source Health" in captured.out
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
py -3 -m pytest tests/test_cli.py -v
```

Expected: FAIL because `radar.cli` does not exist.

- [ ] **Step 3: Add sample records**

Create `src/radar/collectors/sample.py`:

```python
from __future__ import annotations

from radar.models import ReviewRecord, SocialRecord


def build_sample_records() -> tuple[list[SocialRecord], list[ReviewRecord]]:
    social_records = [
        SocialRecord(
            platform="xiaohongshu",
            keyword="厨房收纳",
            url="https://example.com/xhs/kitchen-storage",
            title="小厨房收纳神器",
            text="调料瓶太乱, 台面太占地方, 这个方案看起来更省空间",
            engagement={"likes": 320, "favorites": 140, "comments": 42},
            comments=["难清洗吗", "后悔买过类似的", "有没有平替"],
        )
    ]
    review_records = [
        ReviewRecord(
            asin="B012345678",
            rating=2,
            title="Hard to clean",
            review_text="It saves space, but it is hard to clean and feels unstable.",
            verified=True,
            source_script="sample",
            raw_source_path="sample",
        )
    ]
    return social_records, review_records
```

- [ ] **Step 4: Add CLI**

Create `src/radar/cli.py`:

```python
from __future__ import annotations

import argparse
from datetime import date

from radar.collectors.sample import build_sample_records
from radar.config import require_env
from radar.integrations.feishu import send_feishu_markdown
from radar.models import SourceHealth
from radar.reports import build_daily_markdown
from radar.scoring import score_opportunity


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Amazon Social Opportunity Radar")
    parser.add_argument("--dry-run", action="store_true", help="Print report instead of sending to Feishu.")
    parser.add_argument("--use-sample-data", action="store_true", help="Use deterministic sample data.")
    parser.add_argument("--report-date", default=date.today().isoformat())
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.use_sample_data:
        raise RuntimeError("The first CLI slice requires --use-sample-data until real connectors are wired.")

    social_records, review_records = build_sample_records()
    opportunity = score_opportunity(
        social_records=social_records,
        review_records=review_records,
        category="kitchen_storage",
        keywords=["kitchen organizer", "spice rack organizer"],
    )
    markdown = build_daily_markdown(
        opportunities=[opportunity],
        source_health={
            "xiaohongshu": SourceHealth.OK,
            "scrapecreators": SourceHealth.NOT_CONFIGURED,
            "amazon_reviews": SourceHealth.OK,
        },
        report_date=args.report_date,
        focus="Kitchen appliances / kitchen storage / home storage",
    )
    if args.dry_run:
        print(markdown)
        return 0
    webhook_url = require_env("FEISHU_WEBHOOK_URL")
    send_feishu_markdown(webhook_url, "Amazon Social Opportunity Radar", markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 5: Add PowerShell runner**

Create `scripts/run_daily.ps1`:

```powershell
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

py -3 -m radar.cli --use-sample-data
```

- [ ] **Step 6: Run CLI tests and manual dry run**

Run:

```powershell
py -3 -m pytest tests/test_cli.py -v
py -3 -m radar.cli --dry-run --use-sample-data --report-date 2026-07-10
```

Expected: pytest reports 1 passed, and the dry run prints a Markdown report containing `Amazon Social Opportunity Radar`.

- [ ] **Step 7: Commit**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add src/radar/collectors/sample.py src/radar/cli.py scripts/run_daily.ps1 tests/test_cli.py
& 'C:\Program Files\Git\cmd\git.exe' commit -m "feat: add cli dry run and daily runner"
```

---

### Task 8: Full Verification And Documentation Polish

**Files:**
- Modify: `README.md`
- Verify: all source and test files.

**Interfaces:**
- Consumes: full package.
- Produces: a verified MVP with documented commands.

- [ ] **Step 1: Add final README usage section**

Append to `README.md`:

```markdown
## Verify

```powershell
py -3 -m pytest -v
py -3 -m radar.cli --dry-run --use-sample-data --report-date 2026-07-10
```

## Feishu Send

```powershell
$env:FEISHU_WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/..."
py -3 -m radar.cli --use-sample-data
```

`scripts/run_daily.ps1` can be called manually or from Windows Task Scheduler after `FEISHU_WEBHOOK_URL` is available to the scheduled process.
```

- [ ] **Step 2: Run full test suite**

Run:

```powershell
py -3 -m pytest -v
```

Expected: all tests pass.

- [ ] **Step 3: Run CLI dry run**

Run:

```powershell
py -3 -m radar.cli --dry-run --use-sample-data --report-date 2026-07-10
```

Expected: command exits 0 and prints a Markdown report with source health.

- [ ] **Step 4: Run Git whitespace check**

Run:

```powershell
& 'C:\Program Files\Git\cmd\git.exe' diff --check
```

Expected: no whitespace errors.

- [ ] **Step 5: Commit final docs polish**

```powershell
& 'C:\Program Files\Git\cmd\git.exe' add README.md
& 'C:\Program Files\Git\cmd\git.exe' commit -m "docs: add verification and feishu usage"
```

---

## Self-Review

Spec coverage:

- Keyword configuration: Task 1.
- Xiaohongshu through Apify: Task 6.
- Overseas social source through ScrapeCreators: Task 6.
- Amazon review primary script and backup failover: Task 5.
- Unified records: Task 2.
- Opportunity score breakdown: Task 3.
- Markdown daily brief: Task 4.
- Feishu webhook sending: Task 4 and Task 7.
- Source health in daily brief: Task 4 and Task 7.
- Windows runner for daily automation: Task 7.

Placeholder scan:

- The plan uses exact file paths, exact interfaces, exact commands, and expected outputs.
- No unresolved gaps are required for the MVP slice.

Type consistency:

- `SourceHealth`, `SocialRecord`, `ReviewRecord`, and `Opportunity` are defined in Task 2 and reused by later tasks.
- `score_opportunity` returns `Opportunity`, consumed by `build_daily_markdown`.
- Feishu sender accepts Markdown generated by `build_daily_markdown`.

Execution note:

- Implement tasks in order.
- After each task, run only that task's tests first, then commit.
- Run the full suite in Task 8 before calling the MVP complete.
