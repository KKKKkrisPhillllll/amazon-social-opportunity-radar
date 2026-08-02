# Amazon Social Opportunity Radar MVP 加固设计

## 目标

将现有仅支持 `--use-sample-data` 的命令行入口升级为可安全运行的本地 MVP：按配置调度社媒与 Amazon 评论来源，输出可追溯的中文 Markdown 日报；只有显式指定时才发送飞书。

## 已知现状

- Apify 小红书、ScrapeCreators、Amazon 评论主备采集器已存在，但 CLI 未编排真实来源。
- 当前评分把所有记录汇总为单一机会，不能按类目分别排序。
- 配置示例含本机绝对脚本路径，不适合提交或迁移。
- 飞书发送已有单元测试，但当前默认行为会在未指定 `--dry-run` 时发送。

## MVP 边界

本轮只完成本地命令行闭环，不引入数据库、Web 后台、任务队列、浏览器 Cookie 自动读取、绕过访问控制或自动安装外部 CLI。

真实 API 只在调用方已提供对应环境变量时执行。缺少凭据、网络失败、返回空数据均必须以来源健康状态和报告说明呈现，禁止用样例数据填充真实运行结果。

## 架构

### 1. 配置与凭据

`config/sources.example.yaml` 仅保存环境变量名称、来源开关、请求上限和可选脚本路径环境变量名称。真实路径、API Key、Webhook 只从环境变量读取。

新增运行配置加载函数，分别解析：

- Apify 小红书：`APIFY_TOKEN`。
- ScrapeCreators：`SCRAPECREATORS_API_KEY`，用于 Instagram、TikTok、YouTube、Reddit。
- PRAW 后备：`REDDIT_CLIENT_ID`、`REDDIT_CLIENT_SECRET`、`REDDIT_USER_AGENT`；只用于 ScrapeCreators Reddit 来源失败或未配置时的可选后备。
- Amazon 评论：主、备脚本路径环境变量。
- 飞书：`FEISHU_WEBHOOK_URL`，且仅在 `--send-feishu` 下要求存在。

### 2. 来源路由与健康状态

新增独立调度服务。每个来源返回记录、健康状态和结构化诊断信息。

- 小红书固定使用 Apify。
- Instagram、TikTok、YouTube 固定使用 ScrapeCreators。
- Reddit 优先使用 ScrapeCreators；失败或未配置时，只有 PRAW 凭据完整才尝试 PRAW。
- Amazon 评论继续采用现有主脚本、备用脚本故障切换。
- 单一来源失败不得中止整个日报；只有配置解析错误和无效 CLI 参数应返回非零退出码。

健康状态沿用 `OK`、`PARTIAL`、`DEGRADED`、`FAILED`、`NOT_CONFIGURED`。`DEGRADED` 专门表示已启用后备来源并获得结果。

### 2.1 已确认的外部契约

- Apify `zhorex/rednote-xiaohongshu-scraper` 搜索调用使用 `mode: search`、`searchQuery`、`maxResults`，不使用旧的 `keyword`、`maxItems` 字段。
- ScrapeCreators 必须按平台拆分端点与响应提取器：Instagram 使用 `/v1/instagram/search`；TikTok 使用关键词搜索端点并读取 `search_item_list`；YouTube 使用搜索端点并读取 `videos`；Reddit 使用 `/v1/reddit/search` 并读取 `posts`。仅当记录带有可用 URL 和文本或标题时，才生成社媒证据。
- 各来源适配器只把已识别的公开响应字段映射为 `SocialRecord`。未知字段、空 URL 或空正文不得被伪造为内容。
- PRAW 只使用只读 OAuth，不支持用户名、密码、发帖、投票或其他写入行为。

### 3. 去重与证据保留

新增纯函数去重层。

1. 优先按规范化 URL 去重。
2. URL 缺失时按平台、规范化标题、正文前 160 个字符去重。
3. 保留第一条记录，不拼接、不改写正文。
4. 输出原始数量、去重后数量和重复数量；不输出伪造的来源内容。

### 4. 机会分组与评分

按关键词配置中的类目分别评分。每个类目只使用匹配该类目关键词的社媒记录；Amazon 评论作为共同验证证据但必须保留实际 ASIN 和来源脚本。

无社媒记录的类目不生成机会；只有真实记录或明确传入的样例数据才能参与评分。结果按总分降序排列。

### 5. 报告与飞书

日报保持 Markdown 输出，并新增：

- 运行模式：样例或真实。
- 每个来源的采集、去重数量与健康状态。
- 每个机会的来源 URL 列表和证据摘要。
- 无数据、后备使用、失败和未配置说明。
- 数据完整性提示，禁止把不完整来源描述为全量市场结论。

默认命令只打印并写入本地报告。只有 `--send-feishu` 才允许请求飞书 Webhook；`--dry-run` 与 `--send-feishu` 互斥。

飞书发送前必须检查 UTF-8 请求体不超过 20KB。HTTP 成功后还必须解析 JSON 中的业务 `code`；非 `0` 视为发送失败。Webhook 值、错误响应中的凭据片段和完整本机路径不得进入控制台或报告。

### 6. CLI

新增或调整参数：

- `--config`：来源配置路径，默认 `config/sources.example.yaml`。
- `--keywords`：关键词配置路径，默认 `config/keywords.yaml`。
- `--use-sample-data`：确定性测试模式，不访问外部网络。
- `--dry-run`：打印报告，不发送飞书。
- `--send-feishu`：明确允许发送飞书。
- `--amazon-review-asin`：可选；存在时才调用评论采集器。
- `--report-date`：报告日期。

真实运行不再要求 `--use-sample-data`。调用外部服务前必须先判断配置是否完整。

## 数据模型

新增不可变的来源运行结果类型，字段为 `source_name`、`records`、`health`、`fetched_count`、`deduplicated_count`、`diagnostic`。

`Opportunity` 不存放原始正文；报告层从已保留的 `SocialRecord` 中生成最多三个 URL 和简短证据说明，避免输出大量未处理内容。

## 错误处理

- HTTP、超时、PRAW 异常和脚本失败转换为来源健康状态与诊断，不吞掉配置错误。
- 错误文本不得包含 Token、Webhook、完整环境变量值或本机私有路径。
- 对 PRAW 和 Webhook 使用显式超时；不增加无限重试。

## 测试与验收

新增单元和集成测试，至少覆盖：

1. 无凭据来源返回 `NOT_CONFIGURED`。
2. Reddit 主来源失败时启用 PRAW 后备并标记 `DEGRADED`。
3. URL 与无 URL 两类去重。
4. 类目分组后只生成有证据的机会。
5. 报告展示来源数量、健康状态、URL 和不完整提示。
6. 默认 CLI 不发送飞书；只有 `--send-feishu` 才调用发送函数。
7. `--dry-run` 与 `--send-feishu` 同时出现时拒绝执行。
8. 现有评论主备、Apify、ScrapeCreators、评分和飞书测试持续通过。

真实 API 测试为条件测试：只在用户已配置对应凭据时运行；测试报告必须分别说明哪些来源未配置，不能将其视为通过的真实采集。

## 不在本轮范围内

- 直接嵌入 Agent-Reach、AutoCLI、SurfSense、RSSHub 或 OpenBiliClaw 的代码。
- 自动处理浏览器 Cookie、验证码、登录或付费服务账户。
- 历史数据存储、长期趋势曲线、Web 管理后台。
- 自动发布社媒内容。
- 旧格式 Office 文档处理或 `DocAlign` 功能修改。
