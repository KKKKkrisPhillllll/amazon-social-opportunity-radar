# Amazon Social Opportunity Radar Design

Date: 2026-07-09
Status: Draft for user review

## 1. Goal

Build a configuration-driven MVP that helps an Amazon product manager discover and validate product development opportunities from social media and Amazon review signals, then pushes a daily opportunity brief to Feishu.

The tool is not a generic social media monitoring dashboard. It is a product development radar for kitchen appliances, kitchen storage, and home storage opportunities.

## 2. User Outcomes

The V1 system should help the user:

1. Find product development inspiration from social media trends.
2. Validate whether a social trend maps to real customer pain points.
3. Use Amazon review complaints to support product improvement and new product decisions.
4. Produce a daily Feishu brief with clear product actions.

## 3. V1 Scope

V1 uses a configuration-driven pipeline:

```text
config/keywords.yaml
        |
        v
Xiaohongshu: Apify RedNote / Xiaohongshu Scraper
Instagram / TikTok / YouTube / Reddit: ScrapeCreators
Amazon Review: primary script + backup script
Amazon Keyword / competitor data: later PM agent integration
        |
        v
Unified social and review records
        |
        v
Trend, pain point, complaint, and demand scoring
        |
        v
Product development suggestions / improvement ideas / new product inspiration
        |
        v
Daily Feishu push
```

## 4. Primary Categories

V1 focuses on:

- Kitchen appliances
- Kitchen storage
- Home storage

Default Xiaohongshu keyword groups:

- Kitchen appliances: `小厨房电器`, `厨房神器`, `懒人厨房电器`, `空气炸锅`, `破壁机`, `电蒸锅`, `早餐机`, `多功能料理锅`, `厨房小家电避雷`, `厨房小家电推荐`
- Kitchen and home storage: `厨房收纳`, `小厨房收纳`, `橱柜收纳`, `调料收纳`, `冰箱收纳`, `水槽收纳`, `台面收纳`, `锅具收纳`, `保鲜盒收纳`, `租房收纳`, `收纳神器`, `家居收纳好物`
- Pain keywords: `不好用`, `踩雷`, `后悔买`, `闲置了`, `太占地方`, `难清洗`, `不耐用`, `没必要买`, `平替`, `真实测评`

## 5. Data Sources

### 5.1 Xiaohongshu

Provider: Apify RedNote / Xiaohongshu Scraper.

Role:

- Discover lifestyle trends.
- Find usage scenarios and emotional buying triggers.
- Mine comments for unmet needs and product complaints.
- Identify content angles that may become Amazon listing or ad creative angles.

Expected fields:

- Platform
- Keyword
- Note URL
- Title
- Body text
- Tags
- Author
- Published time if available
- Like count
- Collect/favorite count
- Comment count
- Comments if available

### 5.2 Instagram / TikTok / YouTube / Reddit

Provider: ScrapeCreators.

Role:

- Instagram: visual trend, aesthetic positioning, product styling, bundle inspiration.
- TikTok: fast-moving product demonstrations and viral use cases.
- YouTube: deeper review and tutorial comments.
- Reddit: authentic pain points, objections, and unmet needs from English-speaking consumers.

Expected fields:

- Platform
- Keyword or source URL
- Post/video/thread URL
- Title or caption
- Body text
- Hashtags
- Author or channel
- Published time if available
- Engagement metrics
- Comments if available

### 5.3 Amazon Reviews

Primary local script:

```text
C:\Users\Administrator\.claude\skills\amazon-review-scraper\scripts\amazon_review_scraper.py
```

Backup local script:

```text
C:\Users\Administrator\Downloads\gpt\gpt-skills\qypm-005-voc-product-definition\scripts\voc_reviews.py
```

Current local check on 2026-07-09 found the primary script path, but did not find the backup script path. V1 should keep the backup path configurable and show a setup warning if the file is missing.

Role:

- Validate whether social media pain points exist in real purchase reviews.
- Extract product defects, packaging issues, quality complaints, missing accessories, cleaning problems, and use-case gaps.
- Support product improvement decisions and Amazon listing angles.

Failover behavior:

1. Run the primary script first.
2. If the primary script returns 403, timeout, non-JSON content, zero reviews with an upstream error, or an execution failure, mark the primary source as degraded.
3. Run the backup script if it exists.
4. Normalize output from either script into the same review schema.
5. If both fail, keep the opportunity item but mark Amazon review validation as unavailable.

Unified review fields:

- ASIN
- Rating
- Review title
- Review text
- Review date
- Verified purchase flag if available
- Helpful count if available
- Source script
- Raw source path

### 5.4 Amazon Keyword / Competitor Data

V1 keeps this as a later integration with the existing Amazon PM agent.

Role:

- Convert social opportunity into Amazon validation keywords.
- Identify likely competitor ASINs.
- Support later market screening, review barrier, price band, margin, and launch feasibility checks.

## 6. Unified Opportunity Model

Each opportunity item should contain:

- Opportunity title
- Category
- Source platforms
- Evidence summary
- Customer pain point
- Product development idea
- Amazon validation keywords
- Suggested ASINs to review
- Differentiation angle
- Risk notes
- Next action
- Score breakdown

## 7. Scoring Model

V1 should score each opportunity from 0 to 100.

Recommended scoring:

- Social heat: 0-25
- Pain intensity: 0-25
- Amazon review validation: 0-20
- Product development fit: 0-15
- Amazon business feasibility: 0-15

Score interpretation:

- 80-100: High-priority opportunity. Validate Amazon keywords and ASIN reviews immediately.
- 60-79: Worth watching. Needs more review or keyword evidence.
- 40-59: Low-confidence inspiration. Keep in backlog.
- Below 40: Do not act unless repeated signals appear.

## 8. Feishu Daily Brief

Delivery method: Feishu bot webhook.

Default cadence: once per day.

Suggested report sections:

```md
# Amazon Social Opportunity Radar

Date: YYYY-MM-DD
Focus: Kitchen appliances / kitchen storage / home storage

## 1. Top Opportunities

### Opportunity 1
- Score:
- Category:
- Source:
- Customer pain:
- Product idea:
- Amazon validation keywords:
- Suggested ASIN review check:
- Risk:
- Next action:

## 2. Hot Trends

## 3. High-Frequency Pain Points

## 4. Product Improvement Ideas

## 5. New Product Inspiration

## 6. Items Needing Amazon Review Validation

## 7. Data Source Health
```

## 9. Error Handling

V1 should not silently hide data failures.

Required source health states:

- OK
- PARTIAL
- DEGRADED
- FAILED
- NOT_CONFIGURED

Daily Feishu reports should include data source health so the user knows whether the result is complete.

## 10. Non-Goals

V1 will not include:

- A full web dashboard.
- User account management.
- Multi-user permission control.
- Paid SaaS billing.
- Automatic purchasing or supplier outreach.
- Full Amazon market screening automation.
- Circumvention of platform access controls.

## 11. Acceptance Criteria

V1 is acceptable when:

1. A user can configure kitchen appliance and storage keywords in one config file.
2. The system can ingest at least one Xiaohongshu source through Apify.
3. The system can ingest at least one overseas social source through ScrapeCreators.
4. The system can call the primary Amazon review script when given an ASIN.
5. The system warns clearly if the backup Amazon review script path is missing.
6. The system can normalize social posts and Amazon reviews into consistent records.
7. The system can generate opportunity scores with visible score breakdowns.
8. The system can produce a Markdown daily brief.
9. The system can send the daily brief to Feishu through a webhook.
10. The daily brief includes source health and next actions.

## 12. Implementation Direction

Recommended MVP structure:

```text
amazon-social-opportunity-radar/
  config/
    keywords.yaml
    sources.example.yaml
  docs/
    superpowers/
      specs/
        2026-07-09-amazon-social-opportunity-radar-design.md
  scripts/
    run_daily.ps1
  src/
    collectors/
    normalizers/
    scoring/
    reports/
    integrations/
  tests/
```

The first implementation plan should build a thin vertical slice:

1. Config loading.
2. Mock or sample records for each source shape.
3. Normalization.
4. Scoring.
5. Markdown report generation.
6. Feishu webhook sending.
7. Real source connectors added one by one.

## 13. Open Decisions Before Implementation

The user should confirm these before code implementation starts:

1. Daily push time and timezone.
2. Feishu webhook storage method.
3. Whether the first real connector should be Apify Xiaohongshu or ScrapeCreators.
4. Correct backup Amazon review script path if the current path is outdated.
