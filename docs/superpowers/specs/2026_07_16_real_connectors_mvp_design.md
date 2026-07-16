# 社媒真实连接器 MVP 设计

日期：2026-07-16  
状态：已批准执行

## 1. 目标

把现有“样例数据纵向切片”升级为可运行的真实每日管线：从 Apify 小红书与 ScrapeCreators 海外社媒采集公开内容，统一标准化、生成产品机会报告，并在配置飞书 Webhook 后推送到群聊。

本阶段不追求全量监控。默认限制关键词数量，先证明接口、数据边界、健康状态和每日运行链路完整可用。

## 2. 已确认的官方接口

### 2.1 Apify 小红书

- Actor：`zhorex/rednote-xiaohongshu-scraper`
- 同步数据集端点：`POST /v2/acts/{actor}/run-sync-get-dataset-items`
- 搜索输入：`mode=search`、`searchQuery`、`maxResults`
- 可选输入：`includeComments`、`maxComments`、`sortBy`
- 官方资料：
  - `https://apify.com/zhorex/rednote-xiaohongshu-scraper`
  - `https://apify.com/zhorex/rednote-xiaohongshu-scraper/api/openapi`

### 2.2 ScrapeCreators

所有请求使用 `x-api-key` 请求头，但不同平台必须使用不同端点和参数：

| 平台 | 端点 | 查询参数 |
| --- | --- | --- |
| Instagram | `/v1/instagram/search/hashtag` | `hashtag`、`media_type=all` |
| TikTok | `/v1/tiktok/search/keyword` | `query`、`trim=true` |
| YouTube | `/v1/youtube/search` | `query`、`type=videos`、`includeExtras=true` |
| Reddit | `/v1/reddit/search` | `query`、`sort=relevance`、`timeframe=month`、`trim=true` |

官方资料：`https://docs.scrapecreators.com/llms-full.txt`

### 2.3 飞书

- 使用群自定义机器人 Webhook。
- 消息类型继续使用 `interactive` 卡片。
- HTTP 成功后还必须检查飞书业务响应码。
- 单张卡片整体不超过 30 KB；本阶段发送前执行大小校验，超限时明确失败，不静默截断产品证据。

## 3. 方案选择

### 方案 A：平台路由表加统一 ScrapeCreators 采集器（采用）

一个模块保存端点、参数构造器和响应提取器，对外保持现有 `collect_scrapecreators()` 接口。优点是改动集中、测试容易、适合四个平台的小规模 MVP；缺点是平台差异继续增大时需要再拆分文件。

### 方案 B：每个平台一个采集器

边界最清晰，但本阶段会增加四组重复的 HTTP、错误处理和测试代码，不符合最小可用范围。

### 方案 C：直接调用 ScrapeCreators CLI 或 MCP

能减少 REST 代码，但会引入 Node/MCP 运行时、进程调用和版本管理，难以在当前 Python 管线中稳定测试。

## 4. 架构

```text
keywords.yaml + sources.example.yaml + 环境变量
                     |
                     v
             radar.pipeline
          /          |          \
       Apify   ScrapeCreators   Amazon Review（保留现有边界）
          \          |          /
                     v
              SocialRecord / ReviewRecord
                     |
                     v
          score_opportunity + source health
                     |
                     v
              Markdown 日报
                     |
              dry-run 或飞书推送
```

新增 `src/radar/pipeline.py` 作为唯一编排层。采集器只负责单次请求与标准化，不读取环境变量、不生成报告、不发送飞书。

## 5. 配置与调用预算

`config/sources.example.yaml` 增加：

- `apify.enabled`
- `apify.max_results`
- `apify.include_comments`
- `scrapecreators.enabled`
- `scrapecreators.platforms`
- `collection.max_keywords_per_group`

默认 `max_keywords_per_group=1`。真实模式只处理 `focus_categories` 对应的关键词组，不把 `pain_keywords` 当作产品搜索词。

环境变量：

- `APIFY_TOKEN`
- `SCRAPECREATORS_API_KEY`
- `FEISHU_WEBHOOK_URL`

凭据不存在时不发起网络请求，对应来源标记为 `NOT_CONFIGURED`。飞书凭据缺失只阻止发送，不阻止 `--dry-run` 生成真实健康报告。

## 6. 数据标准化

Apify 输出补充识别：

- `postUrl`
- `content`
- `authorName` 或嵌套 `author.nickname`
- `publishedAt`
- `likes`、`saves`、`comments`

ScrapeCreators 分平台提取：

- Instagram：`posts`
- TikTok：`search_item_list[].aweme_info`
- YouTube：`videos`
- Reddit：`posts`

各平台先转换成规范化原始字段，再调用现有 `normalize_social_record()`，避免评分与报告依赖供应商响应结构。

## 7. CLI 行为

保留：

- `--use-sample-data`
- `--dry-run`
- `--report-date`

新增：

- `--keywords-config`
- `--sources-config`

行为：

1. 显式 `--use-sample-data` 才使用样例数据。
2. 默认进入真实管线。
3. `--dry-run` 打印报告，不要求飞书 Webhook。
4. 非 dry-run 先生成报告，再读取 `FEISHU_WEBHOOK_URL` 并发送。
5. 单个来源失败不终止其他来源；配置文件无效则立即失败。

## 8. 错误与健康状态

- 缺少来源凭据：`NOT_CONFIGURED`
- 请求成功但无记录：`PARTIAL`
- 请求或解析失败：`FAILED`
- 部分关键词成功：`PARTIAL`
- 全部已启用关键词成功且有数据：`OK`

报告始终列出每个平台的健康状态。错误信息不得包含 API Key、Token 或飞书 Webhook。

## 9. 测试策略

- 所有 HTTP 连接继续通过注入会话或发送函数测试。
- 为四个平台分别验证端点、参数、响应提取和字段标准化。
- 为 Apify 验证官方搜索输入。
- 为管线验证：无凭据降级、部分失败继续、按类别生成机会。
- 为 CLI 验证：真实 dry-run 不使用样例、样例模式仍可用、发送模式调用飞书。
- 为飞书验证 HTTP 错误、业务错误和 30 KB 限制。

## 10. 验收标准

1. Apify 请求使用官方搜索字段。
2. ScrapeCreators 四个平台使用各自官方端点。
3. CLI 不再强制 `--use-sample-data`。
4. 无凭据的真实 dry-run 正常退出，并显示 `NOT_CONFIGURED`。
5. 注入测试凭据和假 HTTP 后，四个平台记录进入统一报告。
6. 飞书发送检查 HTTP 与业务响应，并拒绝超过 30 KB 的卡片。
7. 完整测试、CLI dry-run 和 `git diff --check` 全部通过。

## 11. 非目标

- 不绕过平台登录、风控或访问控制。
- 不创建 Web 仪表盘。
- 不自动购买 API 点数。
- 不保存真实 Token、API Key 或 Webhook。
- 不在缺少凭据时伪造“真实采集成功”。
