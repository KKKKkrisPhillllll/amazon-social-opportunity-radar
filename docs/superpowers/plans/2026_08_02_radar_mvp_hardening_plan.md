# Amazon Social Opportunity Radar MVP 加固实施计划

> 面向执行者：按任务顺序实施；每个功能先写失败测试，再写最小实现，再运行对应测试。

目标：将项目从样例演示升级为可安全运行的本地机会雷达。真实来源按配置采集，输出中文 Markdown；飞书只在显式许可时发送。

架构：采集器只负责平台响应；标准化层只负责字段映射；调度层负责凭据、主备、去重和类目分组；报告层不直接访问外部服务；CLI 只编排服务。

技术栈：Python 3.14、requests、PyYAML、PRAW、pytest、GitHub Actions。

## 全局约束

- 不读取 Cookie、不写入社媒平台、不绕过访问控制。
- 缺少凭据必须返回 NOT_CONFIGURED，不得使用样例数据代替。
- 只有 --send-feishu 可以发送飞书，且它与 --dry-run 互斥。
- 输出、诊断、文档不得出现 Token、Webhook 或本机私有路径。
- Apify 使用 mode、searchQuery、maxResults。
- ScrapeCreators 使用平台专用路径：Instagram /v1/instagram/search；TikTok /v1/tiktok/search/keyword；YouTube /v1/youtube/search；Reddit /v1/reddit/search。

## 任务 1：安全配置与来源运行模型

文件：
- 修改 config/sources.example.yaml、requirements.txt、src/radar/config.py、src/radar/models.py
- 修改 tests/test_config.py
- 新建 tests/test_models.py

接口：
    class SourceRun:
        source_name: str
        platform: str
        records: tuple[SocialRecord, ...]
        health: SourceHealth
        fetched_count: int
        duplicate_count: int
        diagnostic: str

    def optional_env(name: str) -> str | None

步骤：
1. 在 tests/test_config.py 写 optional_env 缺失时返回 None 的失败测试。
2. 在 tests/test_models.py 写 SourceRun 负计数和重复数超过采集数时拒绝的失败测试。
3. 运行 py -3 -m pytest tests/test_config.py tests/test_models.py -v，确认因接口不存在而失败。
4. 实现 optional_env 和带校验的 SourceRun。
5. sources.example.yaml 删除绝对脚本路径，改为 primary_script_env、backup_script_env；增加 PRAW 环境变量名称与 max_results。
6. requirements.txt 增加 praw>=8,<9。
7. 重新运行目标测试，预期全部通过。
8. 提交：feat: 增加安全来源运行配置。

## 任务 2：Apify 契约与小红书标准化

文件：
- 修改 src/radar/collectors/apify_xiaohongshu.py、src/radar/normalizers.py
- 修改 tests/test_api_collectors.py、tests/test_normalizers.py

接口：
    def normalize_apify_xiaohongshu_record(raw, keyword) -> SocialRecord
    def collect_xiaohongshu(...) -> SourceRun

步骤：
1. 写失败测试：请求 JSON 必须等于 mode=search、searchQuery=<关键词>、maxResults=20。
2. 写失败测试：postUrl、content、publishedAt、嵌套作者和互动量会映射到 SocialRecord。
3. 运行目标测试，确认旧字段 keyword、maxItems 不能满足断言。
4. 按当前 Apify Actor 契约实现采集和映射；网络错误只产生 FAILED 与安全诊断，空结果产生 PARTIAL。
5. 重新运行目标测试，预期全部通过。
6. 提交：fix: 对齐小红书采集接口契约。

## 任务 3：平台专用 ScrapeCreators 与 PRAW 只读后备

文件：
- 修改 src/radar/collectors/scrapecreators.py、src/radar/collectors/__init__.py
- 新建 src/radar/collectors/praw_reddit.py
- 修改 tests/test_api_collectors.py
- 新建 tests/test_praw_reddit.py

接口：
    def collect_scrapecreators(platform, keyword, api_key, session=None) -> SourceRun
    def collect_praw_reddit(keyword, client_id, client_secret, user_agent, reddit_factory=None) -> SourceRun

步骤：
1. 参数化失败测试，分别断言四个平台的路径、参数、响应数组键：items、search_item_list、videos、posts。
2. 写失败测试：PRAW 只读搜索映射为 SocialRecord，不允许用户名或密码参数。
3. 运行目标测试，确认 TikTok 专用端点和 PRAW 采集器尚不存在。
4. 以平台映射表实现端点和响应提取；仅保留含 URL 且含标题或正文的记录。
5. PRAW 只使用 client_id、client_secret、user_agent 创建客户端；异常返回 FAILED。
6. 重新运行目标测试，预期全部通过。
7. 提交：feat: 增加社媒专用采集和 Reddit 后备。

## 任务 4：去重和来源调度

文件：
- 新建 src/radar/dedup.py、src/radar/services/__init__.py、src/radar/services/orchestrator.py
- 新建 tests/test_dedup.py、tests/test_orchestrator.py

接口：
    def deduplicate_social_records(records) -> tuple[list[SocialRecord], int]
    def run_configured_sources(source_settings, keyword_groups, *, max_keywords_per_category, amazon_review_asin=None, session=None, reddit_factory=None, runner=None) -> tuple[dict[str, list[SocialRecord]], list[ReviewRecord], list[SourceRun]]

步骤：
1. 写失败测试：规范化 URL 去重且保留首条；无 URL 时以平台、标题、正文前 160 字符去重。
2. 写失败测试：缺少凭据不访问网络并返回 NOT_CONFIGURED。
3. 写失败测试：Reddit 主来源失败或未配置但 PRAW 已配置时，使用后备并标记 DEGRADED。
4. 运行目标测试，确认模块不存在。
5. 实现每类目最多 max_keywords_per_category 个关键词的调度；Amazon 评论只在指定 ASIN 时运行。
6. 重新运行目标测试，预期全部通过。
7. 提交：feat: 增加来源调度与证据去重。

## 任务 5：报告、飞书安全和真实 CLI

文件：
- 修改 src/radar/reports.py、src/radar/integrations/feishu.py、src/radar/cli.py
- 修改 tests/test_reports.py、tests/test_feishu.py、tests/test_cli.py

接口：
    def build_daily_markdown(..., source_runs, run_mode) -> str
    def send_feishu_markdown(webhook_url, title, markdown, post=None) -> None

步骤：
1. 写失败测试：日报包含运行模式、来源采集数、去重数、健康状态、诊断、最多三条证据 URL 和完整性提示。
2. 写失败测试：飞书请求体超过 20KB 时不发送；HTTP 200 但业务 code 非 0 时失败。
3. 写失败测试：真实模式缺少凭据只写本地报告；--dry-run 和 --send-feishu 同时使用被拒绝。
4. 运行目标测试，确认新行为尚未实现。
5. 报告改为中文；CLI 默认写 outputs/radar_report_YYYY_MM_DD.md 并打印，--dry-run 只打印，--send-feishu 才发送。
6. 飞书发送检查 UTF-8 JSON 长度与 code=0。
7. 重新运行目标测试，预期全部通过。
8. 提交：feat: 完成安全日报和飞书发送链路。

## 任务 6：公开仓库治理与交付验证

文件：
- 修改 .gitignore、README.md
- 新建 LICENSE、.github/workflows/ci.yml、docs/radar_verification_report.md

步骤：
1. 先运行 git ls-files LICENSE .github/workflows/ci.yml，确认治理文件当前缺失。
2. 添加 MIT License；.gitignore 忽略 outputs、缓存和 .worktrees。
3. 添加 Python 3.14 CI：安装 requirements、pip check、pytest、compileall、pip-audit。
4. README 改为中文，说明真实模式、样例模式、飞书显式发送、环境变量和限制。
5. 运行完整验收：
    py -3 -m pytest -v
    py -3 -m compileall -q src
    py -3 -m pip check
    uvx pip-audit --requirement requirements.txt
    py -3 -m radar.cli --dry-run --use-sample-data --report-date 2026-08-02
6. 写入验证报告，明确真实 API 只有凭据存在时才可运行。
7. 提交：chore: 完善公开仓库交付治理。

## 任务 7：真实凭据条件验收

文件：
- 修改 docs/radar_verification_report.md

步骤：
1. 只检查 APIFY_TOKEN、SCRAPECREATORS_API_KEY、REDDIT_CLIENT_ID、REDDIT_CLIENT_SECRET、REDDIT_USER_AGENT、FEISHU_WEBHOOK_URL 的配置状态，不读取或输出值。
2. 凭据存在时运行 py -3 -m radar.cli --max-keywords-per-category 1；缺少的来源必须显示 NOT_CONFIGURED。
3. 不带 --send-feishu 的真实运行不发送飞书。
4. 验证报告分别记录真实来源状态、未配置项和不可验证原因。

## 计划自检

- 任务 1 覆盖配置与安全边界。
- 任务 2、3 覆盖外部接口契约和 PRAW。
- 任务 4 覆盖主备、去重和类目分组。
- 任务 5 覆盖报告、CLI 与飞书。
- 任务 6 覆盖公开仓库治理。
- 任务 7 覆盖真实凭据边界。

