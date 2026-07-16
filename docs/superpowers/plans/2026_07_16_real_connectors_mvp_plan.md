# 社媒真实连接器 MVP 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for progress tracking.

**目标：** 将现有样例数据流程升级为可运行的真实数据 MVP，按官方接口采集小红书、Instagram、TikTok、YouTube、Reddit，生成产品机会，并可推送到飞书。

**架构：** 连接器只负责官方请求与字段归一化；`pipeline.py` 负责编排、来源健康状态和机会生成；CLI 负责读取配置与环境变量；飞书模块负责消息构建和业务响应校验。无凭据时不得发起网络请求，并明确返回 `NOT_CONFIGURED`。

**技术栈：** Python 3.11+、`requests`、`PyYAML`、`pytest`、PowerShell、GitHub Actions。

## 全局约束

- [x] 不在代码、日志、测试或提交历史中写入 API Key、Token、Webhook。
- [x] 所有外部接口均以官方文档为准，并通过可注入会话进行离线测试。
- [x] 每项功能先写失败测试，再写最小实现，最后运行目标测试和全量测试。
- [x] 样例模式仅由 `--use-sample-data` 显式启用；默认执行真实模式。
- [x] MVP 不实现数据库、定时服务、监控后台和 Amazon Keyword/竞品数据接入。

## 任务 1：修正 Apify 小红书连接器

**文件：**

- 修改：`src/radar/collectors/apify_xiaohongshu.py`
- 修改：`src/radar/normalizers.py`
- 修改：`tests/test_api_collectors.py`
- 修改：`tests/test_normalizers.py`

- [x] 新增失败测试，断言调用 `/v2/acts/{actor}/run-sync-get-dataset-items`，并发送 `mode=search`、`searchQuery`、`maxResults`、`includeComments`、`maxComments`、`sortBy`。
- [x] 新增失败测试，覆盖 `postUrl`、`content`、`authorName`、`publishedAt`、`likes`、`saves`、`comments` 的归一化。
- [x] 运行 `python -m pytest tests/test_api_collectors.py tests/test_normalizers.py -q`，确认测试因当前请求体或字段映射失败。
- [x] 实现最小修正，保留 actor 名称中的 `/` 到 `~` 编码。
- [x] 再次运行目标测试，预期全部通过。
- [x] 提交：`fix: align apify xiaohongshu connector`

## 任务 2：按平台实现 ScrapeCreators 官方路由

**文件：**

- 修改：`src/radar/collectors/scrapecreators.py`
- 修改：`src/radar/normalizers.py`
- 修改：`tests/test_api_collectors.py`
- 修改：`tests/test_normalizers.py`

- [x] 新增参数化失败测试，覆盖 Instagram `/v1/instagram/search/hashtag`、TikTok `/v1/tiktok/search/keyword`、YouTube `/v1/youtube/search`、Reddit `/v1/reddit/search`。
- [x] 断言请求使用 `x-api-key`，并为不同平台发送 `hashtag` 或 `query` 等官方参数。
- [x] 新增响应提取测试，覆盖 `posts`、`search_item_list[].aweme_info`、`videos`、`posts` 四种结构。
- [x] 新增归一化测试，覆盖作者、文本、URL、发布时间和互动数据。
- [x] 运行目标测试，确认因当前通用猜测路由失败。
- [x] 实现明确的平台路由表、参数构造器和响应提取器；不支持的平台抛出 `ValueError`。
- [x] 运行 `python -m pytest tests/test_api_collectors.py tests/test_normalizers.py -q`，预期全部通过。
- [x] 提交：`fix: use official scrapecreators routes`

## 任务 3：实现真实每日管线与降级状态

**文件：**

- 新增：`src/radar/pipeline.py`
- 新增：`tests/test_pipeline.py`
- 修改：`src/radar/models.py`（仅在现有模型不足时）

- [x] 新增失败测试：缺少 `APIFY_TOKEN` 时不调用 Apify，并返回 `NOT_CONFIGURED`。
- [x] 新增失败测试：缺少 `SCRAPECREATORS_API_KEY` 时不调用对应平台，并返回 `NOT_CONFIGURED`。
- [x] 新增失败测试：部分平台成功、部分失败时返回 `PARTIAL`，同时保留已采集记录。
- [x] 新增失败测试：有真实记录时按类目生成机会；无记录时不虚构机会。
- [x] 实现 `DailyPipelineResult` 和 `run_real_pipeline(...)`，允许注入连接器用于测试。
- [x] 运行 `python -m pytest tests/test_pipeline.py -q`，预期全部通过。
- [x] 提交：`feat: add real collection pipeline`

## 任务 4：接通配置、CLI 与每日脚本

**文件：**

- 修改：`src/radar/cli.py`
- 修改：`src/radar/config.py`
- 修改：`config/sources.example.yaml`
- 修改：`config/keywords.yaml`
- 修改：`scripts/run_daily.ps1`
- 修改：`tests/test_cli.py`
- 修改：`tests/test_config.py`

- [x] 新增失败测试：CLI 默认走真实管线，`--use-sample-data` 才走样例管线。
- [x] 新增失败测试：无凭据真实 dry-run 成功结束，并在报告中标记来源未配置。
- [x] 新增配置测试，覆盖连接器开关、平台列表、单组关键词上限和 `home_storage` 关键词组。
- [x] 实现 CLI 编排与环境变量读取；非 dry-run 缺少飞书 Webhook 时给出明确错误。
- [x] 将 `run_daily.ps1` 调整为默认真实运行，不嵌入秘密。
- [x] 运行 `python -m pytest tests/test_cli.py tests/test_config.py -q`，预期全部通过。
- [x] 提交：`feat: wire real daily workflow`

## 任务 5：加强飞书推送校验

**文件：**

- 修改：`src/radar/integrations/feishu.py`
- 修改：`tests/test_feishu.py`

- [x] 新增失败测试：消息卡 UTF-8 编码超过 30 KB 时拒绝发送。
- [x] 新增失败测试：HTTP 200 但飞书业务码非 0 时抛出不泄露 Webhook 的错误。
- [x] 新增成功测试：兼容 `code == 0` 与 `StatusCode == 0` 的成功响应。
- [x] 实现消息构建、大小校验和业务响应校验。
- [x] 运行 `python -m pytest tests/test_feishu.py -q`，预期全部通过。
- [x] 提交：`fix: validate feishu webhook responses`

## 任务 6：文档、验证与 Draft PR

**文件：**

- 修改：`README.md`

- [x] 用中文补充真实运行配置、环境变量、样例模式、dry-run 和飞书推送说明。
- [x] 运行 `python -m pytest -q`，预期全量测试通过。
- [x] 运行样例 dry-run，确认原有演示路径未回归。
- [x] 在无凭据环境运行真实 dry-run，确认不联网、不造数据，并输出 `NOT_CONFIGURED`。
- [x] 运行 `git diff --check` 和 `git status --short`，确认无格式错误和意外文件。
- [x] 推送 `agent/real-connectors-mvp`，创建独立 Draft PR，不合并 `master`。
- [x] 在交付说明中列出真实凭据联调阻塞、未纳入 MVP 的边界及官方接口依据。
