# Amazon 评论首跑实施计划

> **面向执行代理：** 必须使用 `superpowers:subagent-driven-development` 或 `superpowers:executing-plans` 按任务逐项执行；步骤使用 `- [ ]` 复选框跟踪。

**目标：** 为 `B0D3XTZVS5` 提供只读、本地输出的 Amazon 评论首跑命令，验证主备评论脚本与低评分评论证据。

**架构：** 复用现有 `collect_amazon_reviews` 完成主脚本到备用脚本的故障切换。CLI 新增独立首跑分支，加载来源配置后写出中文 Markdown 报告；该分支强制要求 `--dry-run`，从而不可能调用飞书发送逻辑。

**技术栈：** Python 3.14、PyYAML、pytest、现有 Amazon 评论脚本。

## 全局约束

- 所有生成的报告与说明使用中文；ASIN、路径、参数名、状态值保持原样。
- 不提交真实密钥、Webhook、原始评论数据或 `outputs/` 内容。
- 首跑只接受一个 10 位字母数字 ASIN，并且必须带 `--dry-run`。
- 主脚本失败、超时、出现 `403` 或 `forbidden` 时复用现有备用脚本逻辑。
- 无论失败还是无评论，报告只能呈现实际状态与实际评论数量，不得生成示例评论。
- 本轮不得调用 Apify、ScrapeCreators、飞书或机会评分。

---

## 文件结构

- 修改：`src/radar/collectors/amazon_reviews.py`，以当前 Python 解释器执行外部评论脚本。
- 修改：`src/radar/reports.py`，新增只读评论首跑报告渲染函数。
- 修改：`src/radar/cli.py`，新增 `--amazon-review-asin` 分支、配置加载和本地报告写入。
- 修改：`tests/test_amazon_reviews.py`，验证脚本解释器选择。
- 修改：`tests/test_reports.py`，验证低评分评论、空评论和状态展示。
- 修改：`tests/test_cli.py`，验证本地文件、强制 dry run 与飞书隔离。
- 创建：`.gitignore`，忽略本地 `outputs/`、pytest 缓存与 Python 缓存。
- 修改：`README.md`，补充中文首跑命令、输出位置和安全边界。

---

### 任务 1：评论首跑报告渲染

**文件：**
- 修改：`src/radar/reports.py`
- 修改：`tests/test_reports.py`

**接口：**
- 消费：`ReviewRecord`、`SourceHealth`。
- 产出：`build_amazon_review_markdown(asin: str, reviews: list[ReviewRecord], health: SourceHealth, report_date: str) -> str`。

- [ ] **步骤 1：先写失败测试**

在 `tests/test_reports.py` 追加以下导入与测试：

```python
from radar.models import Opportunity, ReviewRecord, SourceHealth
from radar.reports import build_amazon_review_markdown, build_daily_markdown


def test_build_amazon_review_markdown_only_uses_actual_low_rating_reviews():
    reviews = [
        ReviewRecord(
            asin="B0D3XTZVS5",
            rating=2,
            title="难清洗",
            review_text="缝隙里容易积水，清洗很麻烦。",
            review_date="2026-07-11",
            source_script="primary",
            raw_source_path="C:/scripts/primary.py",
        ),
        ReviewRecord(
            asin="B0D3XTZVS5",
            rating=5,
            title="满意",
            review_text="使用方便。",
            source_script="primary",
            raw_source_path="C:/scripts/primary.py",
        ),
    ]

    markdown = build_amazon_review_markdown(
        asin="B0D3XTZVS5",
        reviews=reviews,
        health=SourceHealth.OK,
        report_date="2026-07-12",
    )

    assert "# Amazon 评论首跑报告" in markdown
    assert "- 采集状态：OK" in markdown
    assert "- 实际评论数量：2" in markdown
    assert "- 低评分评论数量：1" in markdown
    assert "缝隙里容易积水，清洗很麻烦。" in markdown
    assert "使用方便。" not in markdown
    assert "- 实际使用脚本：primary" in markdown


def test_build_amazon_review_markdown_reports_empty_result_without_inventing_reviews():
    markdown = build_amazon_review_markdown(
        asin="B0D3XTZVS5",
        reviews=[],
        health=SourceHealth.FAILED,
        report_date="2026-07-12",
    )

    assert "- 采集状态：FAILED" in markdown
    assert "- 实际评论数量：0" in markdown
    assert "未采集到评分低于或等于 3 星的评论。" in markdown
    assert "实际使用脚本" not in markdown
```

- [ ] **步骤 2：运行测试，确认失败**

运行：

```powershell
py -3 -m pytest tests/test_reports.py -v
```

预期：因 `build_amazon_review_markdown` 尚未定义而失败。

- [ ] **步骤 3：实现最小报告函数**

在 `src/radar/reports.py` 的导入区替换为：

```python
from radar.models import Opportunity, ReviewRecord, SourceHealth
```

在 `build_daily_markdown` 之后追加：

```python
def build_amazon_review_markdown(
    asin: str,
    reviews: list[ReviewRecord],
    health: SourceHealth,
    report_date: str,
) -> str:
    low_rating_reviews = [review for review in reviews if review.rating <= 3]
    lines = [
        "# Amazon 评论首跑报告",
        "",
        f"- ASIN：{asin}",
        f"- 运行日期：{report_date}",
        f"- 采集状态：{health.value}",
        f"- 实际评论数量：{len(reviews)}",
        f"- 低评分评论数量：{len(low_rating_reviews)}",
    ]
    if reviews:
        lines.append(f"- 实际使用脚本：{reviews[0].source_script}")
    lines.extend(["", "## 低评分评论证据", ""])
    if not low_rating_reviews:
        lines.append("未采集到评分低于或等于 3 星的评论。")
    for index, review in enumerate(low_rating_reviews, start=1):
        lines.extend(
            [
                f"### 评论 {index}",
                f"- 评分：{review.rating}",
                f"- 标题：{review.title or '未提供'}",
                f"- 日期：{review.review_date or '未提供'}",
                f"- 内容：{review.review_text}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"
```

- [ ] **步骤 4：运行报告测试，确认通过**

运行：

```powershell
py -3 -m pytest tests/test_reports.py -v
```

预期：`2 passed` 或包含新增两项测试的全量通过结果。

- [ ] **步骤 5：提交任务**

```powershell
git add src/radar/reports.py tests/test_reports.py
git commit -m "feat: add amazon review first run report"
```

---

### 任务 2：稳定执行评论脚本并增加 CLI 首跑分支

**文件：**
- 修改：`src/radar/collectors/amazon_reviews.py`
- 修改：`src/radar/cli.py`
- 修改：`tests/test_amazon_reviews.py`
- 修改：`tests/test_cli.py`

**接口：**
- 消费：`config/sources.example.yaml` 的 `amazon_reviews.primary_script` 与 `amazon_reviews.backup_script`。
- 消费：`collect_amazon_reviews(asin, primary_script, backup_script)`。
- 消费：`build_amazon_review_markdown(asin, reviews, health, report_date)`。
- 产出：`main(["--amazon-review-asin", "B0D3XTZVS5", "--dry-run"]) -> 0`，并写入本地报告。

- [ ] **步骤 1：先写失败测试**

在 `tests/test_amazon_reviews.py` 增加导入与测试：

```python
import sys


def test_collect_amazon_reviews_uses_current_python_interpreter(tmp_path):
    primary = tmp_path / "primary.py"
    backup = tmp_path / "backup.py"
    primary.write_text("", encoding="utf-8")
    backup.write_text("", encoding="utf-8")
    commands = []

    def runner(command, capture_output, text, timeout):
        commands.append(command)
        return FakeCompleted(
            0,
            stdout='[{"asin":"B0D3XTZVS5","rating":2,"title":"难清洗","review_text":"边角积水"}]',
        )

    records, health = collect_amazon_reviews("B0D3XTZVS5", primary, backup, runner=runner)

    assert health is SourceHealth.OK
    assert records[0].asin == "B0D3XTZVS5"
    assert commands[0][0] == sys.executable
```

在 `tests/test_cli.py` 增加以下导入与测试：

```python
import pytest

from radar.models import ReviewRecord, SourceHealth


def test_cli_amazon_review_first_run_writes_local_report_without_feishu(
    monkeypatch,
    tmp_path,
    capsys,
):
    source_config = tmp_path / "sources.yaml"
    source_config.write_text(
        """feishu:\n  webhook_env: FEISHU_WEBHOOK_URL\napify:\n  token_env: APIFY_TOKEN\n  xiaohongshu_actor: actor\nscrapecreators:\n  api_key_env: SCRAPECREATORS_API_KEY\namazon_reviews:\n  primary_script: C:/scripts/primary.py\n  backup_script: C:/scripts/backup.py\n""",
        encoding="utf-8",
    )
    reviews = [
        ReviewRecord(
            asin="B0D3XTZVS5",
            rating=1,
            title="易损坏",
            review_text="用了两周就断了。",
            source_script="backup",
            raw_source_path="C:/scripts/backup.py",
        )
    ]
    monkeypatch.setattr(
        "radar.cli.collect_amazon_reviews",
        lambda asin, primary_script, backup_script: (reviews, SourceHealth.DEGRADED),
    )
    monkeypatch.setattr(
        "radar.cli.send_feishu_markdown",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("不应调用飞书")),
    )

    exit_code = main(
        [
            "--amazon-review-asin",
            "B0D3XTZVS5",
            "--dry-run",
            "--source-config",
            str(source_config),
            "--output-dir",
            str(tmp_path / "outputs"),
            "--report-date",
            "2026-07-12",
        ]
    )

    report_path = tmp_path / "outputs" / "amazon_review_report_B0D3XTZVS5_20260712.md"
    captured = capsys.readouterr()
    assert exit_code == 0
    assert report_path.exists()
    assert "- 采集状态：DEGRADED" in report_path.read_text(encoding="utf-8")
    assert "# Amazon 评论首跑报告" in captured.out


def test_cli_amazon_review_first_run_requires_dry_run():
    with pytest.raises(SystemExit) as error:
        main(["--amazon-review-asin", "B0D3XTZVS5"])

    assert error.value.code == 2
```

- [ ] **步骤 2：运行测试，确认失败**

运行：

```powershell
py -3 -m pytest tests/test_amazon_reviews.py tests/test_cli.py -v
```

预期：解释器命令与 CLI 参数尚未实现，新增测试失败。

- [ ] **步骤 3：修改采集器，使用当前 Python 解释器**

在 `src/radar/collectors/amazon_reviews.py` 的导入区增加：

```python
import sys
```

将 `_run_script` 中的命令构造替换为：

```python
    command = [sys.executable, str(script), asin]
```

保留现有 `-o` 输出目录参数、超时处理、`403`/`forbidden` 识别与主备切换逻辑，不改变 `collect_amazon_reviews` 的返回类型。

- [ ] **步骤 4：实现 CLI 首跑分支**

在 `src/radar/cli.py` 的导入区增加：

```python
import re
from pathlib import Path

from radar.collectors.amazon_reviews import collect_amazon_reviews
from radar.config import load_source_settings, require_env
from radar.reports import build_amazon_review_markdown, build_daily_markdown
```

在 `build_parser` 中、`--report-date` 参数之前增加：

```python
    parser.add_argument("--amazon-review-asin")
    parser.add_argument("--source-config", default="config/sources.example.yaml")
    parser.add_argument("--output-dir", default="outputs")
```

在 `main` 之前增加：

```python
def _run_amazon_review_first_run(args: argparse.Namespace, asin: str) -> int:
    source_settings = load_source_settings(args.source_config)
    review_settings = source_settings["amazon_reviews"]
    reviews, health = collect_amazon_reviews(
        asin=asin,
        primary_script=Path(review_settings["primary_script"]),
        backup_script=Path(review_settings["backup_script"]),
    )
    markdown = build_amazon_review_markdown(
        asin=asin,
        reviews=reviews,
        health=health,
        report_date=args.report_date,
    )
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"amazon_review_report_{asin}_{args.report_date.replace('-', '')}.md"
    report_path.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"报告已写入：{report_path}")
    return 0
```

在 `main` 的参数解析之后、现有 `if not args.use_sample_data:` 之前增加：

```python
    if args.amazon_review_asin:
        if args.use_sample_data:
            parser.error("--amazon-review-asin 不能与 --use-sample-data 同时使用")
        if not args.dry_run:
            parser.error("--amazon-review-asin 首跑必须使用 --dry-run")
        asin = args.amazon_review_asin.upper()
        if not re.fullmatch(r"[A-Z0-9]{10}", asin):
            parser.error("--amazon-review-asin 必须是 10 位字母数字 ASIN")
        return _run_amazon_review_first_run(args, asin)
```

该分支在写入并打印报告后立即返回，因此不会到达 `require_env("FEISHU_WEBHOOK_URL")` 或 `send_feishu_markdown`。

- [ ] **步骤 5：运行定向测试，确认通过**

运行：

```powershell
py -3 -m pytest tests/test_amazon_reviews.py tests/test_cli.py tests/test_reports.py -v
```

预期：所有相关测试通过，且 CLI 测试生成 `amazon_review_report_B0D3XTZVS5_20260712.md`。

- [ ] **步骤 6：提交任务**

```powershell
git add src/radar/collectors/amazon_reviews.py src/radar/cli.py tests/test_amazon_reviews.py tests/test_cli.py
git commit -m "feat: add amazon review first run cli"
```

---

### 任务 3：本地输出隔离与使用说明

**文件：**
- 创建：`.gitignore`
- 修改：`README.md`

**接口：**
- 消费：任务 2 生成的 `outputs/amazon_review_report_<ASIN>_<YYYYMMDD>.md`。
- 产出：可复制的首跑命令与不会提交本地报告的 Git 忽略规则。

- [ ] **步骤 1：先写失败检查**

运行：

```powershell
git check-ignore -q outputs/amazon_review_report_B0D3XTZVS5_20260712.md
```

预期：当前命令返回非零，说明输出文件尚未被忽略。

- [ ] **步骤 2：创建 Git 忽略规则**

创建 `.gitignore`：

```gitignore
__pycache__/
.pytest_cache/
outputs/
```

- [ ] **步骤 3：补充 README 中文首跑说明**

在 `README.md` 的 `## Dry Run` 之后增加：

````markdown
## Amazon 评论首跑

以下命令只采集一个 ASIN 的 Amazon 评论并写入本地报告；不会调用社媒来源或飞书：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --amazon-review-asin B0D3XTZVS5 --dry-run
```

报告保存到 `outputs/amazon_review_report_B0D3XTZVS5_YYYYMMDD.md`。`outputs/` 已被 Git 忽略，真实评论数据不会被提交到仓库。
````

- [ ] **步骤 4：运行忽略规则与全量测试**

运行：

```powershell
git check-ignore -q outputs/amazon_review_report_B0D3XTZVS5_20260712.md
py -3 -m pytest -q
```

预期：忽略规则命令返回 `0`，pytest 显示所有测试通过。

- [ ] **步骤 5：提交任务**

```powershell
git add .gitignore README.md
git commit -m "docs: document amazon review first run"
```

---

## 最终验收

- [ ] 运行完整测试：

```powershell
py -3 -m pytest -q
```

预期：所有测试通过。

- [ ] 使用真实 ASIN 运行首跑：

```powershell
$env:PYTHONPATH="src"
py -3 -m radar.cli --amazon-review-asin B0D3XTZVS5 --dry-run
```

预期：控制台与 `outputs/` 中的报告展示同一份真实采集状态；主脚本成功时为 `OK`，主脚本失败但备用成功时为 `DEGRADED`，两个脚本都失败时为 `FAILED`，两个脚本路径都不可用时为 `NOT_CONFIGURED`。命令不得发送飞书消息。

## 自检结果

- 规格覆盖：任务 1 覆盖真实评论与低评分证据；任务 2 覆盖主备脚本、CLI、本地写入和飞书隔离；任务 3 覆盖输出数据不入库与操作说明。
- 占位符扫描：计划没有未完成事项，接口说明完整。
- 接口一致性：CLI 使用 `collect_amazon_reviews` 的现有参数与返回值；报告函数只接收标准化 `ReviewRecord` 和 `SourceHealth`；报告文件名与验收命令一致。
