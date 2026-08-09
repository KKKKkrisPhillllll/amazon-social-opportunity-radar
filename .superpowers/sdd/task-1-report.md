# 模块一完成报告：用户研究证据模型与配置

## 修改文件

- `config/voc_tags.yaml`：新增 D01-D22 VOC 维度及五组创新/反向信号词表。
- `config/sources.example.yaml`：新增 `persona_journey` 阈值配置。
- `src/radar/models.py`：新增 `PersonaEvidence`、`UserPersona`、`JourneyStage`、`PersonaJourneyResult`。
- `src/radar/evidence.py`：新增公开 URL 证据过滤、按类目索引、稳定证据 ID、URL 去重和 ID 回溯。
- `tests/test_evidence.py`：新增证据索引测试。
- `tests/test_helpers.py`：新增后续任务复用的机会、证据和 Gate 辅助构造器。

## TDD 红绿过程

1. 先新增 `tests/test_evidence.py`，覆盖简报要求的无效 URL 过滤和稳定 ID，并补充 URL 去重、输入顺序、空文本、匿名字段边界及评论记录不计入公开证据测试。
2. 执行红灯命令：

   `py -m pytest tests/test_evidence.py::test_evidence_index_filters_invalid_urls_and_keeps_stable_ids -q`

   结果：失败，测试收集时报 `ModuleNotFoundError: No module named 'radar.evidence'`，原因符合预期的功能缺失。
3. 新增最小实现和配置后执行绿灯命令：

   `py -m pytest tests/test_evidence.py -q`

   结果：`4 passed in 0.09s`。

## 测试命令和完整结果

- `py -m pytest tests/test_evidence.py::test_evidence_index_filters_invalid_urls_and_keeps_stable_ids -q`：失败，`radar.evidence` 尚不存在，符合 TDD 红灯预期。
- `py -m pytest tests/test_evidence.py -q`：`4 passed in 0.09s`。
- `py -m pytest tests/test_evidence.py tests/test_models.py tests/test_config.py -q`：`13 passed in 0.31s`。
- `py -m pytest -q`：`49 passed in 4.25s`。

## 未解决问题

- 证据索引按简报约定暂不消费 `review_records`；亚马逊评论没有公开 URL，因此不会被加入公开 URL 证据索引。
- 未实现 VOC 匹配、Opportunity Gate、用户画像、用户旅程、报告或 CLI 集成，留给后续模块。
