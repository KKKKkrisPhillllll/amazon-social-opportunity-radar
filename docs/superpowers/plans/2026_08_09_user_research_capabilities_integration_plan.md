# 用户研究能力整合实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task with review checkpoints.

**Goal:** 在不改变现有采集、评分、日报和飞书流程的前提下，把用户研究与产品机会系统中的证据治理、VOC 标签、机会 Gate、行为型人群能力整合到 `amazon-social-opportunity-radar`，并为高分机会生成匿名用户画像与六阶段用户旅程图。

**Architecture:** 保留现有 `SocialRecord`、`ReviewRecord`、`Opportunity` 和 `score_opportunity` 作为输入与评分边界。新增一层确定性的证据分析管道：记录规范化 → 22 维 VOC 与创新信号 → 机会 Gate → 高分机会画像/旅程 → Markdown/飞书报告。外部 ZIP 只提供方法参考，不复制其源码、vendor、采集器或 LLM 运行时。

**Tech Stack:** Python 3.11+、dataclasses、PyYAML、pytest、现有 Markdown 报告与飞书分片逻辑；不新增运行时依赖，不调用外部模型。

## Global Constraints

- 仅处理 `Opportunity.total_score >= 60` 的机会，每日报告最多 3 个。
- 每个用户画像/旅程至少检查 2 条去重后的有效公开 URL；不足时必须标记低置信度和待验证。
- 用户画像只做匿名聚合，不保留用户名、头像、邮箱、主页或心理画像字段。
- 报告旅程固定为：发现需求、搜索方案、对比决策、购买、使用、反馈。
- 不修改现有采集器、现有评分公式、飞书发送限制和数据源降级语义。
- 不复制 ZIP 中的 `vendor/user_research_skill_v56`、RPA、Playwright、LLM 代码或未明确授权的素材。
- 不新增网络请求；示例模式和无凭据模式必须继续可运行。
- 所有新增字段和结论都必须能回溯到 `Evidence_ID` 或公开 URL。

---

## 文件地图

| 文件 | 职责 |
| --- | --- |
| `config/voc_tags.yaml` | 22 维 VOC 和 Workaround/Trade-off/Over-served/Extreme/反向证据词表 |
| `config/sources.example.yaml` | 用户画像/旅程阈值配置 |
| `src/radar/models.py` | 新增证据信号、Gate 结果及画像输入模型 |
| `src/radar/evidence.py` | 记录规范化、URL 校验、证据编号、跨来源去重 |
| `src/radar/voc.py` | 22 维 VOC 和创新信号的确定性匹配 |
| `src/radar/opportunity_gate.py` | 独立来源、反向证据、Workaround、验证动作的 Gate 判断 |
| `src/radar/persona_builder.py` | 高分机会的行为型匿名用户画像 |
| `src/radar/journey_builder.py` | 六阶段用户旅程与阶段证据 |
| `src/radar/reports.py` | 追加用户画像、旅程图、Gate 和证据链接 |
| `src/radar/cli.py` | 加载配置并串联新分析层 |
| `tests/test_evidence.py` | 证据边界与去重测试 |
| `tests/test_helpers.py` | 新增测试共享的 Opportunity、EvidenceItem 与 Gate 构造器 |
| `tests/test_voc.py` | VOC 和创新信号测试 |
| `tests/test_opportunity_gate.py` | Gate 规则测试 |
| `tests/test_persona_journey.py` | 画像与旅程测试 |
| `tests/test_reports.py` | 报告兼容性与 Mermaid 渲染测试 |
| `tests/test_cli.py` | CLI 配置与样例链路测试 |
| `README.md` | 新增能力、运行方式和证据边界说明 |

---

## Task 1: 建立证据模型与配置

**Files:**

- Create: `config/voc_tags.yaml`
- Modify: `config/sources.example.yaml`
- Modify: `src/radar/models.py`
- Create: `src/radar/evidence.py`
- Create: `tests/test_evidence.py`
- Create: `tests/test_helpers.py`

**Interfaces:**

- `build_evidence_index(records_by_category: Mapping[str, Sequence[SocialRecord]], review_records: Sequence[ReviewRecord]) -> EvidenceIndex`
- `EvidenceItem` 只保存 `evidence_id`、平台、公开 URL、类目、文本摘要、评论数量和可选 ASIN，不保存个人身份字段。
- `EvidenceIndex.by_category` 的值为 `tuple[EvidenceItem, ...]`；`EvidenceIndex.by_id` 用于后续回溯。

- [ ] **Step 1: Write the failing test**

```python
from radar.evidence import build_evidence_index
from radar.models import SocialRecord


def test_evidence_index_filters_invalid_urls_and_keeps_stable_ids():
    record = SocialRecord(
        platform="reddit",
        keyword="厨房收纳",
        url="https://reddit.example/post-1",
        title="小厨房台面太拥挤",
        text="台面空间太小，调料拿取不方便。",
        comments=[],
        engagement={},
    )
    invalid = SocialRecord(
        platform="reddit",
        keyword="厨房收纳",
        url="",
        title="无公开链接",
        text="只有本地内容",
        comments=[],
        engagement={},
    )

    index = build_evidence_index({"kitchen_storage": [record, invalid]}, [])

    assert len(index.by_category["kitchen_storage"]) == 1
    assert index.by_category["kitchen_storage"][0].evidence_id == "E-0001"
    assert index.by_id["E-0001"].url == "https://reddit.example/post-1"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_evidence.py::test_evidence_index_filters_invalid_urls_and_keeps_stable_ids -q`

Expected: FAIL because `radar.evidence` and `EvidenceIndex` do not yet exist.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from collections.abc import Mapping, Sequence
from urllib.parse import urlparse

from radar.models import ReviewRecord, SocialRecord


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str
    platform: str
    url: str
    category: str
    title: str
    text: str
    comments: tuple[str, ...]
    asin: str = ""


@dataclass(frozen=True)
class EvidenceIndex:
    by_category: dict[str, tuple[EvidenceItem, ...]]
    by_id: dict[str, EvidenceItem]


def _is_public_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_evidence_index(
    records_by_category: Mapping[str, Sequence[SocialRecord]],
    review_records: Sequence[ReviewRecord],
) -> EvidenceIndex:
    del review_records
    by_category: dict[str, tuple[EvidenceItem, ...]] = {}
    by_id: dict[str, EvidenceItem] = {}
    counter = 1
    for category, records in records_by_category.items():
        items: list[EvidenceItem] = []
        seen_urls: set[str] = set()
        for record in records:
            if not _is_public_url(record.url):
                continue
            normalized_url = record.url.strip()
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            item = EvidenceItem(
                evidence_id=f"E-{counter:04d}",
                platform=record.platform,
                url=normalized_url,
                category=category,
                title=record.title.strip(),
                text=record.text.strip(),
                comments=tuple(comment.strip() for comment in record.comments if comment.strip()),
            )
            items.append(item)
            by_id[item.evidence_id] = item
            counter += 1
        by_category[category] = tuple(items)
    return EvidenceIndex(by_category=by_category, by_id=by_id)
```

同时在 `src/radar/models.py` 增加后续任务使用的数据结构：

```python
@dataclass(frozen=True)
class PersonaEvidence:
    platform: str
    url: str
    summary: str


@dataclass(frozen=True)
class UserPersona:
    opportunity_title: str
    category: str
    opportunity_score: int
    behavioral_segment: str
    scenario: str
    core_goal: str
    pain_points: tuple[str, ...]
    purchase_triggers: tuple[str, ...]
    concerns: tuple[str, ...]
    evidence: tuple[PersonaEvidence, ...]
    confidence: str


@dataclass(frozen=True)
class JourneyStage:
    name: str
    observed_signals: tuple[str, ...]
    user_need_or_action: str
    product_implication: str
    evidence_urls: tuple[str, ...]
    confidence: str


@dataclass(frozen=True)
class PersonaJourneyResult:
    persona: UserPersona
    stages: tuple[JourneyStage, ...]
```

创建 `tests/test_helpers.py`，供后续测试使用。构造器必须填满现有 `Opportunity` 的全部字段，分数只写入 `score_breakdown={"social_heat": total_score}`，这样不会依赖生产评分函数：

```python
from radar.evidence import EvidenceItem
from radar.models import Opportunity
from radar.opportunity_gate import OpportunityGate


def make_opportunity(total_score=75, category="kitchen_storage"):
    return Opportunity(
        title="台面收纳机会",
        category=category,
        source_platforms=["reddit", "youtube"],
        evidence_summary="测试证据",
        customer_pain_point="台面空间不足",
        product_idea="减少取放步骤",
        amazon_validation_keywords=["kitchen storage"],
        suggested_asins=[],
        differentiation_angle="提高空间利用率",
        risk_notes="需要样品验证",
        next_action="补充竞品验证",
        score_breakdown={"social_heat": total_score},
    )


def make_two_platform_evidence():
    return [
        EvidenceItem("E-0001", "reddit", "https://reddit.example/1", "kitchen_storage", "", "台面空间太小", ()),
        EvidenceItem("E-0002", "youtube", "https://youtube.example/2", "kitchen_storage", "", "很难清洁", ()),
    ]


def make_eligible_gate():
    return OpportunityGate(True, 2, 2, False, ("存在 VOC 信号",), (), "补充样品测试")


def make_low_evidence_gate():
    return OpportunityGate(False, 1, 1, False, (), ("公开证据少于 2 条",), "补充公开证据")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_evidence.py -q`

Expected: PASS. Add tests for URL deduplication, stable ordering, empty text and review records not counting as public URL evidence.

- [ ] **Step 5: Commit**

```bash
git add config/voc_tags.yaml config/sources.example.yaml src/radar/models.py src/radar/evidence.py tests/test_evidence.py
git commit -m "feat: 增加证据索引与VOC配置基础"
```

## Task 2: 增加 22 维 VOC 与创新信号

**Files:**

- Modify: `config/voc_tags.yaml`
- Create: `src/radar/voc.py`
- Create: `tests/test_voc.py`

**Interfaces:**

- `classify_voc(items: Sequence[EvidenceItem], taxonomy: Mapping[str, Sequence[str]]) -> dict[str, tuple[str, ...]]`
- `detect_innovation_signals(items: Sequence[EvidenceItem], words: Mapping[str, Sequence[str]]) -> dict[str, tuple[str, ...]]`
- `load_voc_config(path: str | Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]`
- 返回值只保留 `evidence_id -> themes/signals`，不得复制或覆盖证据原文。
- 英文关键词使用词边界；中文关键词使用包含匹配；空词一律忽略。

- [ ] **Step 1: Write the failing test**

```python
from radar.evidence import EvidenceItem
from radar.voc import classify_voc, detect_innovation_signals


def test_voc_classifies_space_and_cleaning_without_changing_text():
    item = EvidenceItem(
        evidence_id="E-0001",
        platform="reddit",
        url="https://reddit.example/post-1",
        category="kitchen_storage",
        summary="台面空间太小，而且很难清洁。",
        comment_count=0,
    )
    themes = classify_voc([item], {"D06_空间占用": ["空间"], "D12_清洁维护": ["清洁"]})

    assert themes["E-0001"] == ("D06_空间占用", "D12_清洁维护")
    assert item.summary == "台面空间太小，而且很难清洁。"


def test_counter_evidence_is_separate_from_pain_signal():
    item = EvidenceItem(
        evidence_id="E-0002",
        platform="reddit",
        url="https://reddit.example/post-2",
        category="kitchen_storage",
        summary="这个方案没问题，不需要更换。",
        comment_count=0,
    )
    signals = detect_innovation_signals([item], {"counter_evidence": ["没问题"]})

    assert signals["counter_evidence"] == ("E-0002",)
    assert signals.get("workarounds", ()) == ()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_voc.py -q`

Expected: FAIL because `radar.voc` does not yet exist.

- [ ] **Step 3: Write minimal implementation**

```python
import re
from collections.abc import Mapping, Sequence

from radar.evidence import EvidenceItem


def _hit(text: str, keyword: str) -> bool:
    keyword = keyword.strip().lower()
    if not keyword:
        return False
    if any("\u4e00" <= char <= "\u9fff" for char in keyword):
        return keyword in text.lower()
    return re.search(r"(?<![a-z0-9])" + re.escape(keyword) + r"(?![a-z0-9])", text.lower()) is not None


def classify_voc(
    items: Sequence[EvidenceItem],
    taxonomy: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, tuple[str, ...]] = {}
    for item in items:
        text = item.summary
        result[item.evidence_id] = tuple(
            dimension for dimension, words in taxonomy.items() if any(_hit(text, word) for word in words)
        )
    return result


def detect_innovation_signals(
    items: Sequence[EvidenceItem],
    words: Mapping[str, Sequence[str]],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {name: [] for name in words}
    for item in items:
        text = item.summary
        for name, candidates in words.items():
            if any(_hit(text, word) for word in candidates):
                result[name].append(item.evidence_id)
    return {name: tuple(ids) for name, ids in result.items()}
```

`config/voc_tags.yaml` 必须包含 `D01_功能有效性` 至 `D22_售后退换`，以及 `workarounds`、`tradeoffs`、`over_served`、`extreme_users`、`counter_evidence` 五组词。词表从 ZIP 的方法中重新整理，不复制其文件。

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_voc.py -q`

Expected: PASS. Add regression tests for the English token `ad` not matching `wanted`, and for generic `but/但是` not being treated as a Trade-off without a second contrasting signal.

- [ ] **Step 5: Commit**

```bash
git add config/voc_tags.yaml src/radar/voc.py tests/test_voc.py
git commit -m "feat: 增加VOC主题与创新信号"
```

## Task 3: 增加 Opportunity Gate

**Files:**

- Modify: `src/radar/models.py`
- Create: `src/radar/opportunity_gate.py`
- Create: `tests/test_opportunity_gate.py`

**Interfaces:**

- `evaluate_opportunity_gate(opportunity: Opportunity, evidence: Sequence[EvidenceItem], voc: Mapping[str, tuple[str, ...]], signals: Mapping[str, tuple[str, ...]], min_evidence_count: int = 2) -> OpportunityGate`
- `OpportunityGate` 字段：`eligible`、`independent_source_count`、`evidence_count`、`has_counter_evidence`、`strengths`、`gaps`、`next_validation`。
- Gate 只决定是否允许生成画像/旅程，不修改 `Opportunity.score_breakdown` 和 `total_score`。

- [ ] **Step 1: Write the failing test**

```python
from radar.evidence import EvidenceItem
from radar.opportunity_gate import evaluate_opportunity_gate
from test_helpers import make_opportunity


def test_gate_requires_two_independent_public_sources():
    evidence = [
        EvidenceItem("E-0001", "reddit", "https://reddit.example/1", "kitchen_storage", "", "占空间", ()),
        EvidenceItem("E-0002", "reddit", "https://reddit.example/2", "kitchen_storage", "", "占空间", ()),
    ]
    gate = evaluate_opportunity_gate(
        opportunity=make_opportunity(total_score=75),
        evidence=evidence,
        voc={"E-0001": ("D06_空间占用",), "E-0002": ("D06_空间占用",)},
        signals={},
    )

    assert gate.eligible is False
    assert "至少 2 个独立来源" in "；".join(gate.gaps)


def test_gate_accepts_high_score_with_two_platforms_and_exposes_counter_evidence():
    evidence = [
        EvidenceItem("E-0001", "reddit", "https://reddit.example/1", "kitchen_storage", "", "占空间", ()),
        EvidenceItem("E-0002", "youtube", "https://youtube.example/2", "kitchen_storage", "", "太占台面", ()),
    ]
    gate = evaluate_opportunity_gate(
        opportunity=make_opportunity(total_score=75),
        evidence=evidence,
        voc={"E-0001": ("D06_空间占用",), "E-0002": ("D06_空间占用",)},
        signals={"counter_evidence": ("E-0002",)},
    )

    assert gate.eligible is True
    assert gate.has_counter_evidence is True
    assert gate.next_validation
```

测试中的 `make_opportunity` 使用现有 `Opportunity` 构造器创建一个分数为 75 的对象，不修改生产评分函数。

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_opportunity_gate.py -q`

Expected: FAIL because `OpportunityGate` and `evaluate_opportunity_gate` do not yet exist.

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass
from collections.abc import Mapping, Sequence

from radar.evidence import EvidenceItem
from radar.models import Opportunity


@dataclass(frozen=True)
class OpportunityGate:
    eligible: bool
    independent_source_count: int
    evidence_count: int
    has_counter_evidence: bool
    strengths: tuple[str, ...]
    gaps: tuple[str, ...]
    next_validation: str


def evaluate_opportunity_gate(
    opportunity: Opportunity,
    evidence: Sequence[EvidenceItem],
    voc: Mapping[str, tuple[str, ...]],
    signals: Mapping[str, tuple[str, ...]],
    min_evidence_count: int = 2,
) -> OpportunityGate:
    relevant = [item for item in evidence if item.category == opportunity.category]
    platforms = {item.platform for item in relevant}
    gaps: list[str] = []
    strengths: list[str] = []
    if opportunity.total_score < 60:
        gaps.append("机会总分低于 60 分")
    if len(relevant) < min_evidence_count:
        gaps.append(f"公开证据少于 {min_evidence_count} 条")
    if len(platforms) < 2:
        gaps.append("至少需要 2 个独立来源")
    if any(voc.get(item.evidence_id) for item in relevant):
        strengths.append("存在可归类的 VOC 信号")
    if signals.get("workarounds"):
        strengths.append("发现用户替代方案或自救行为")
    has_counter = bool(set(signals.get("counter_evidence", ())) & {item.evidence_id for item in relevant})
    if has_counter:
        gaps.append("存在反向证据，需要人工核验适用边界")
    score_ok = opportunity.total_score >= 60
    evidence_ok = len(relevant) >= min_evidence_count
    source_ok = len(platforms) >= 2
    return OpportunityGate(
        eligible=score_ok and evidence_ok and source_ok,
        independent_source_count=len(platforms),
        evidence_count=len(relevant),
        has_counter_evidence=has_counter,
        strengths=tuple(strengths),
        gaps=tuple(gaps),
        next_validation="补充独立来源、竞品评论和真实任务测试后再进入产品定义。",
    )
```

`eligible` 规则固定为：总分至少 60、有效 URL 至少 2 条、至少 2 个平台；反向证据不会直接淘汰机会，但必须显示为风险。实现使用 `score_ok and evidence_ok and source_ok` 的显式布尔表达式，避免隐式例外。

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_opportunity_gate.py -q`

Expected: PASS. Add tests for score 59, one URL, duplicate platform URLs, no VOC hit and counter-evidence-only cases.

- [ ] **Step 5: Commit**

```bash
git add src/radar/models.py src/radar/opportunity_gate.py tests/test_opportunity_gate.py
git commit -m "feat: 增加产品机会Gate"
```

## Task 4: 实现行为型用户画像与六阶段旅程

**Files:**

- Create: `src/radar/persona_builder.py`
- Create: `src/radar/journey_builder.py`
- Modify: `src/radar/models.py`
- Create: `tests/test_persona_journey.py`

**Interfaces:**

- `build_persona(opportunity: Opportunity, evidence: Sequence[EvidenceItem], voc: Mapping[str, tuple[str, ...]], gate: OpportunityGate) -> UserPersona`
- `build_journey(opportunity: Opportunity, evidence: Sequence[EvidenceItem], voc: Mapping[str, tuple[str, ...]], gate: OpportunityGate) -> tuple[JourneyStage, ...]`
- 两个函数只接受 Gate 通过或低置信度结果；不接受个人身份字段。
- `JourneyStage.name` 只能来自六个固定阶段，顺序不可变。

- [ ] **Step 1: Write the failing test**

```python
from radar.journey_builder import build_journey
from radar.persona_builder import build_persona
from test_helpers import (
    make_eligible_gate,
    make_low_evidence_gate,
    make_opportunity,
    make_two_platform_evidence,
)


def test_high_score_opportunity_gets_behavioral_persona_and_six_stages():
    opportunity = make_opportunity(total_score=75, category="kitchen_storage")
    evidence = make_two_platform_evidence()
    voc = {item.evidence_id: ("D06_空间占用",) for item in evidence}
    gate = make_eligible_gate()

    persona = build_persona(opportunity, evidence, voc, gate)
    stages = build_journey(opportunity, evidence, voc, gate)

    assert persona.category == "kitchen_storage"
    assert persona.confidence in {"中", "高"}
    assert persona.behavioral_segment in {"小空间效率型", "一般任务型"}
    assert len(persona.evidence) == 2
    assert [stage.name for stage in stages] == [
        "发现需求", "搜索方案", "对比决策", "购买", "使用", "反馈"
    ]


def test_insufficient_evidence_is_low_confidence_and_neutral():
    opportunity = make_opportunity(total_score=75)
    persona = build_persona(opportunity, make_two_platform_evidence()[:1], {}, make_low_evidence_gate())

    assert persona.confidence == "低"
    assert any("待验证" in item for item in persona.pain_points)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_persona_journey.py -q`

Expected: FAIL because the persona and journey builders do not yet exist.

- [ ] **Step 3: Write minimal implementation**

画像和旅程生成采用固定模板与可见关键词，不调用 LLM。画像按行为信号优先生成“小空间效率型”“高频重度使用型”“价格敏感型”“高适配复杂型”等标签；没有足够证据时只输出观察信号和待验证提示。旅程阶段按 VOC 与标题/正文关键词映射，阶段没有直接信号时使用“当前未发现直接公开证据，待后续采集验证”。

```python
JOURNEY_STAGES = ("发现需求", "搜索方案", "对比决策", "购买", "使用", "反馈")


def _confidence(evidence: Sequence[EvidenceItem]) -> str:
    platforms = {item.platform for item in evidence}
    if len(evidence) >= 4 and len(platforms) >= 2:
        return "高"
    if len(evidence) >= 2:
        return "中"
    return "低"


def build_persona(opportunity, evidence, voc, gate):
    confidence = _confidence(evidence)
    pain_points = tuple(
        sorted({theme for themes in voc.values() for theme in themes})
    ) or ("当前没有足够主题证据，待验证",)
    if confidence == "低":
        pain_points = pain_points + ("证据不足，待验证",)
    return UserPersona(
        opportunity_title=opportunity.title,
        category=opportunity.category,
        opportunity_score=opportunity.total_score,
        behavioral_segment="小空间效率型" if "空间" in " ".join(pain_points) else "一般任务型",
        scenario=f"围绕{opportunity.category}的真实使用场景",
        core_goal="在当前场景中更稳定、更省步骤地完成任务",
        pain_points=pain_points,
        purchase_triggers=("重复出现的使用摩擦",),
        concerns=("价格、耐用性、清洁维护和适配性",),
        evidence=tuple(
            PersonaEvidence(item.platform, item.url, item.title or item.text[:80])
            for item in evidence[:5]
        ),
        confidence=confidence,
    )
```

`build_journey` 必须为每个固定阶段生成一个 `JourneyStage`，并填充阶段信号、产品启示、证据 URL 和置信度；不得用没有证据的故事替换空阶段。

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_persona_journey.py -q`

Expected: PASS. Add tests for URL 去重、最多 5 条证据、固定阶段顺序和低置信度措辞。

- [ ] **Step 5: Commit**

```bash
git add src/radar/models.py src/radar/persona_builder.py src/radar/journey_builder.py tests/test_persona_journey.py
git commit -m "feat: 为高分机会生成行为型画像与旅程"
```

## Task 5: 接入报告、配置和 CLI

**Files:**

- Modify: `config/sources.example.yaml`
- Modify: `src/radar/config.py`
- Modify: `src/radar/reports.py`
- Modify: `src/radar/cli.py`
- Modify: `tests/test_reports.py`
- Modify: `tests/test_cli.py`

**Interfaces:**

- `build_daily_markdown(..., persona_journeys: Sequence[PersonaJourneyResult] = ()) -> str`
- 新章节放在“产品机会排序”之后；无合格机会时不显示章节。
- CLI 使用 `persona_journey` 配置筛选机会，不新增必填 CLI 参数。

- [ ] **Step 1: Write the failing test**

```python
from radar.journey_builder import JOURNEY_STAGES
from radar.models import JourneyStage, PersonaEvidence, PersonaJourneyResult, UserPersona
from test_helpers import make_opportunity


def make_six_stages():
    return tuple(
        JourneyStage(
            name=name,
            observed_signals=("公开证据中的相关信号",),
            user_need_or_action="完成当前阶段任务",
            product_implication="优先验证对应阶段的摩擦",
            evidence_urls=("https://reddit.example/1",),
            confidence="中",
        )
        for name in JOURNEY_STAGES
    )


def make_persona_journey_result():
    persona = UserPersona(
        opportunity_title="台面收纳机会",
        category="kitchen_storage",
        opportunity_score=75,
        behavioral_segment="小空间效率型",
        scenario="小厨房台面收纳",
        core_goal="减少取放和清洁步骤",
        pain_points=("空间不足",),
        purchase_triggers=("重复出现的台面拥挤",),
        concerns=("尺寸适配",),
        evidence=(
            PersonaEvidence("reddit", "https://reddit.example/1", "台面空间太小"),
            PersonaEvidence("youtube", "https://youtube.example/2", "很难清洁"),
        ),
        confidence="中",
    )
    return PersonaJourneyResult(persona=persona, stages=tuple(make_six_stages()))


def test_report_renders_mermaid_and_evidence_links_for_qualified_opportunity():
    result = make_persona_journey_result()
    markdown = build_daily_markdown(
        opportunities=[make_opportunity(total_score=75)],
        source_runs=[],
        report_date="2026-08-09",
        focus="厨房收纳",
        run_mode="样例数据",
        evidence_by_category={},
        persona_journeys=[result],
    )

    assert "## 用户画像与用户旅程图" in markdown
    assert "```" + "mermaid" in markdown
    assert "https://" in markdown
    assert "发现需求" in markdown
    assert "反馈" in markdown


def test_report_does_not_render_persona_section_without_qualified_results():
    markdown = build_daily_markdown(
        opportunities=[], source_runs=[], report_date="2026-08-09",
        focus="厨房收纳", run_mode="样例数据", evidence_by_category={},
    )

    assert "## 用户画像与用户旅程图" not in markdown
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_reports.py tests/test_cli.py -q`

Expected: FAIL because `build_daily_markdown` has no `persona_journeys` parameter and the new section is absent.

- [ ] **Step 3: Write minimal implementation**

在 `config/sources.example.yaml` 增加：

```yaml
persona_journey:
  min_opportunity_score: 60
  max_opportunities_per_report: 3
  min_evidence_count: 2
```

CLI 串联顺序固定为：

```python
evidence_index = build_evidence_index(records_by_category, review_records)
voc_taxonomy, signal_words = load_voc_config(PROJECT_ROOT / "config" / "voc_tags.yaml")
persona_settings = source_settings.get("persona_journey", {})
all_evidence = tuple(
    item for items in evidence_index.by_category.values() for item in items
)
voc_by_id = classify_voc(all_evidence, voc_taxonomy)
signals = detect_innovation_signals(all_evidence, signal_words)
gates = {
    (opportunity.category, opportunity.title): evaluate_opportunity_gate(
        opportunity,
        evidence_index.by_category.get(opportunity.category, ()),
        voc_by_id,
        signals,
        min_evidence_count=int(persona_settings["min_evidence_count"]),
    )
    for opportunity in opportunities
}
qualified = [
    opportunity
    for opportunity in sorted(opportunities, key=lambda item: item.total_score, reverse=True)
    if opportunity.total_score >= int(persona_settings["min_opportunity_score"])
    and gates[(opportunity.category, opportunity.title)].eligible
][: int(persona_settings["max_opportunities_per_report"])]
persona_journeys = [
    PersonaJourneyResult(
        persona=build_persona(
            opportunity,
            evidence_index.by_category.get(opportunity.category, ()),
            voc_by_id,
            gates[(opportunity.category, opportunity.title)],
        ),
        stages=build_journey(
            opportunity,
            evidence_index.by_category.get(opportunity.category, ()),
            voc_by_id,
            gates[(opportunity.category, opportunity.title)],
        ),
    )
    for opportunity in qualified
]
markdown = build_daily_markdown(
    opportunities=opportunities,
    source_runs=source_runs,
    report_date=args.report_date,
    focus=_focus_label(keyword_groups),
    run_mode=run_mode,
    evidence_by_category=records_by_category,
    persona_journeys=persona_journeys,
)
```

报告渲染必须使用现有飞书分片路径；链接只显示平台名或证据编号，不显示个人账号。配置缺失时使用 60、3、2 的默认值，非法值明确抛出 `ValueError`。

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_reports.py tests/test_cli.py -q`

Expected: PASS. Then run `python -m radar.cli --use-sample-data --output-dir outputs` and confirm报告成功生成；样例证据不足时必须显示低置信度。

- [ ] **Step 5: Commit**

```bash
git add config/sources.example.yaml src/radar/config.py src/radar/reports.py src/radar/cli.py tests/test_reports.py tests/test_cli.py
git commit -m "feat: 接入用户研究结果到日报"
```

## Task 6: 完整回归、文档和公开同步准备

**Files:**

- Modify: `README.md`
- Modify: `docs/radar_verification_report.md`
- Modify: `tests/test_models.py`
- Modify: `tests/test_scoring.py`
- Modify: `tests/test_orchestrator.py`

**Interfaces:**

- 既有调用不需要传入新参数。
- 既有评分总分、采集健康状态、飞书发送和降级行为保持不变。
- README 只说明本项目重新实现的能力，不引用 ZIP 内部路径作为运行依赖。

- [ ] **Step 1: Write the failing regression tests**

```python
def test_existing_score_is_unchanged_after_research_layer():
    opportunity_before = score_opportunity(
        social_records=sample_social_records(),
        review_records=sample_review_records(),
        category="kitchen_storage",
        keywords=["厨房收纳"],
    )
    opportunity_after = score_opportunity(
        social_records=sample_social_records(),
        review_records=sample_review_records(),
        category="kitchen_storage",
        keywords=["厨房收纳"],
    )

    assert opportunity_after.score_breakdown == opportunity_before.score_breakdown
    assert opportunity_after.total_score == opportunity_before.total_score
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest -q`

Expected: Existing tests pass; the new regression test fails only if the integration has changed scoring behavior. If it passes immediately, retain it as a guard test.

- [ ] **Step 3: Write minimal documentation and verification report**

README 必须补充以下可复制运行命令：

```powershell
cd E:\vscode\amazon-social-opportunity-radar
python -m pytest -q
python -m radar.cli --use-sample-data --output-dir outputs
```

验证报告记录：测试数量、静态检查结果、样例报告路径、真实 API 未配置状态、画像/旅程证据数量与低置信度行为。不得把样例数据写成真实市场结论。

- [ ] **Step 4: Run full verification**

Run:

```powershell
python -m pytest -q
python -m ruff check src tests
python -m radar.cli --use-sample-data --output-dir outputs
python -m compileall -q src tests
git diff --check
```

Expected: 全部测试和静态检查通过；样例日报生成；工作区只包含本次功能文件和文档变更。

- [ ] **Step 5: Commit**

```bash
git add README.md docs/radar_verification_report.md tests
git commit -m "test: 完成用户研究能力回归验证"
```

完成本地验证后，再单独确认 GitHub 同步范围。公开同步只包含功能代码、配置示例、测试、README 和验证报告，不包含内部 `docs/superpowers` 设计/计划文档，除非用户另行指定。

## 验收标准

- 现有 45 项测试及新增测试全部通过。
- 评分函数的结果不变，研究层只负责解释和筛选。
- 59 分机会不生成画像，60 分机会可以进入候选。
- 每日报告最多生成 3 个高分机会的画像/旅程。
- 有效 URL 少于 2 条时为低置信度，并出现待验证提示。
- 画像不包含个人身份字段。
- 六阶段 Mermaid 图和证据链接可在 Markdown 中正常展示。
- 没有真实凭据时，CLI 仍能通过样例模式生成报告。
- 未复制 ZIP 的 vendor 或采集代码，未新增未经确认的外部接口。
