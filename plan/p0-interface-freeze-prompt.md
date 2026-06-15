# CrossLens SPECs P0 接口冻结：审查修复 + 剩余接口补全

## 项目位置

```
E:\CodePrograms\CrossLens\crosslens-specs
```

Git 仓库，最新 commit `bb8a875`。Python + Pydantic v2 + pytest。

---

## 架构背景（必读）

CrossLens 是一个可编排、可审计的 Agentic 投研决策工作流系统。架构宪法：

> **Deterministic first, Agentic when necessary, Traceable always.**

核心对象链（13 个对象，数据从上游流到下游）：

```
Investment Task → Context Bundle → Evidence Packets → Analysis Domain Jobs
→ Analysis Cards → Post-card Validation Report → Conflict Reports
→ Pre-decision Validation Report → Playbook Evaluation Report → Guardrail Report
→ Resolved Decision Bounds → Decision Candidate → Decision Trace
```

5 个分析能力域：`macro_meso`, `fundamentals`, `company_event`, `sentiment`, `technical_market`

**唯一事实源**：`SPEC-REGISTRY.md` — 所有枚举、Schema、依赖关系的权威定义在此。任何 SPEC 正文与 Registry 不一致时，以 Registry 为准。

---

## 执行方式：Team Agents

使用 team agents 模式。主 agent 负责任务分配、工作整合和最终汇报，子 agents 并行执行具体任务。

### 主 Agent 职责

1. 读取本 prompt 和以下文件建立全局理解：
   - `SPEC-REGISTRY.md`
   - `README.md`
   - `executable_specs/spec003/src/crosslens_spec003/models.py`（最新代码）
2. 将任务分配给子 agents（见下方 Task 1-4）
3. 子 agents 完成后：
   - 运行全量测试：`for d in spec003 spec004 spec005 spec006 spec009; do cd executable_specs/$d && python -m pytest -v && cd ../..; done`
   - 检查跨包一致性（枚举值、字段名、引用格式）
   - 检查 SPEC-REGISTRY.md 是否需要同步更新
   - 整合为一次 commit，commit message 格式：`fix: P0 interface freeze — review fixes + remaining schemas`
4. 向用户汇报：修改了什么、为什么、测试结果、遗留项

---

## Task 1：审查修复（Code Review Fixes）

**来源**：commit `bb8a875` 的代码审查发现的问题。

### 1.1 [必修] ValidationOverallStatus 与 SPEC-003 §13.4 不一致

**问题**：
- SPEC-003 §13.4 定义 5 values：`passed`, `passed_with_notes`, `passed_with_flags`, `blocked`, `failed`
- `executable_specs/spec003/src/crosslens_spec003/models.py` 定义：`PASSED`, `PASSED_WITH_FLAGS`, `BLOCKED`, `ERROR`, `SKIPPED`
- 模型缺少 `passed_with_notes`，用 `error` 替代了 `failed`，多了 `skipped`

**要求**：
- 判断哪个是正确的设计意图
- 如果模型是对的（`error` 替代 `failed` 是为了跟 `domain_status` 统一），则更新 SPEC-003 §13.4 文档
- 如果文档是对的，则更新模型
- 无论哪种选择，`passed_with_notes` 的去留必须显式说明
- 更新对应的测试（`tests/test_models.py`）
- 同步更新 SPEC-REGISTRY.md 的枚举表（如果该枚举被收录）

### 1.2 [必修] 删除死 validator

**问题**：`AnalysisDomainJob._evidence_refs_not_empty()` 是空壳：

```python
@model_validator(mode="after")
def _evidence_refs_not_empty(self) -> "AnalysisDomainJob":
    # soft: warn but don't block — some domains may run without evidence
    return self
```

**要求**：
- 删除此 validator
- 在 `AnalysisDomainJob` 类的 docstring 或字段注释中说明 "evidence_refs may be empty for domains that generate their own evidence"
- 确认测试 `test_empty_evidence_refs_is_allowed` 仍然通过（它验证的就是这个行为）

### 1.3 [建议修] AnalysisDomainJob 扁平化文档同步

**问题**：SPEC-003 §8 的 JSON 示例是嵌套结构（`input: { ... }`），但模型是扁平的（`task`, `context_bundle_ref`, `evidence_refs` 直接在顶层）。此外 `task` 字段从引用（`investment_task_ref`）变成了完整快照（`dict[str, Any]`）。

**要求**：
- 更新 SPEC-003 §8 的 JSON 示例，使其匹配模型的扁平结构
- 在示例中添加 `run_id` 和 `created_at` 字段
- 在 §8 添加说明："`task` 字段为 Investment Task 的只读快照，非引用。能力域不应修改此对象。"

### 1.4 [建议修] DomainStatusReason 接入消费方

**问题**：`DomainStatusReason` 枚举已定义和测试，但没有被任何模型字段引用。SPEC-003 §10.1 文档提到 `reason_code` 字段但未体现在模型中。

**要求**：
- 在 `executable_specs/spec004/src/crosslens_spec004/models.py` 的 `AnalysisCard` 模型中，添加可选字段：`reason_code: DomainStatusReason | None = None`
- 需要从 spec003 导入 `DomainStatusReason`（或直接在 spec004 中定义，取决于包依赖策略）
- 添加 model_validator：当 `domain_status` 为 `error` 或 `unavailable` 时，`reason_code` 应有值（warning 级别，不阻断）
- 更新 spec004 的测试
- 或者（如果跨包导入有循环依赖风险）：在 spec003 的 `AnalysisDomainJob` 上添加 `reason_code` 字段，并在注释中说明 "当 domain 执行结果为 error/unavailable 时，由编排器或能力域填写"

### 1.5 [建议修] ValidationFinding 字段名统一

**问题**：SPEC-003 §13.3 JSON 示例用 `target_ref`，模型用 `card_ref`。

**要求**：
- 统一为 `card_ref`（更明确）
- 更新 SPEC-003 §13.3 的 JSON 示例

### 1.6 [可选] EvidencePacket 关键字段约束

**问题**：`source_type`, `source_name`, `evidence_type`, `signal`, `time_horizon` 默认空字符串，允许创建"空白" EvidencePacket。

**要求**：
- 对 `evidence_type` 添加 `min_length=1` 约束
- 更新相关测试（确保所有测试数据都提供了 evidence_type）
- 其他字段保持空字符串默认（source_type/source_name 可能在某些场景下确实为空）

---

## Task 2：Investment Task Pydantic 模型

**目标**：将 SPEC-003 §6.1 的 Investment Task 从 JSON 示例升级为 Pydantic v2 可执行规格。

**输入**：SPEC-003 §6.1 的 JSON 示例：
```json
{
  "task_id": "task_001",
  "task_type": "single_stock_buy_decision",
  "asset": {
    "symbol": "NVDA",
    "asset_type": "stock",
    "market": "US"
  },
  "user_intent": "whether_to_buy",
  "time_horizon": "3-6 months",
  "playbook_id": "capital_cycle_fundamental_playbook",
  "depth": "standard",
  "risk_preference": "medium",
  "uses_user_private_data": true,
  "user_private_data_types": ["current_position", "private_notes"],
  "created_at": "2026-06-14T00:00:00Z"
}
```

**要求**：
1. 在 `executable_specs/spec003/src/crosslens_spec003/models.py` 中添加：
   - `AssetInfo` 模型（symbol + asset_type + market）
   - `TaskType` 枚举（参考 SPEC-002 的 task_type 5 values，读取 SPEC-002 获取具体值）
   - `InvestmentTask` 模型（继承 StrictModel）
   - `Depth` 枚举或 Literal（standard / deep / quick — 从 SPEC-007 RunConfig 中确认）
   - `RiskPreference` 枚举或 Literal
2. 添加合理的 validator：
   - `symbol` 必须非空
   - `playbook_id` 必须非空（所有任务都需要 playbook）
3. 添加测试到 `tests/test_models.py`：
   - 正常创建
   - symbol 为空时拒绝
   - extra fields 被拒绝
   - 嵌套 AssetInfo 验证
4. 导出 JSON Schema 到 `schemas/` 目录
5. 更新 SPEC-REGISTRY.md Schema 表，添加 Investment Task 行

---

## Task 3：Context Bundle 最小 Schema

**目标**：为 Context Bundle 定义最小 Pydantic 模型。SPEC-003 §6.2 目前只有文字描述，没有 JSON 示例和 schema。

**背景**：Context Bundle 是执行任务所需的上下文集合，是生成 Evidence Packet 的原材料。它包含市场行情、财务数据、公司公告、新闻、宏观背景、社媒数据、技术指标原始数据、用户持仓、历史分析记录、Playbook 配置和相关历史案例。

**要求**：
1. 设计 **MVP 最小形态**的 Context Bundle 模型——不需要覆盖所有数据类型，但需要：
   - `context_bundle_id: str`
   - `task_id: str`
   - `run_id: str`
   - `sources: list[ContextSource]` — 数据来源列表
   - `created_at: datetime`
   - `data_quality_overall: DataQuality`
2. 设计 `ContextSource` 子模型：
   - `source_id: str`
   - `source_type: str`（如 "market_data", "financial_report", "news", "user_private"）
   - `source_name: str`
   - `as_of: date`
   - `data_quality: DataQuality`
   - `payload: dict[str, Any]`（具体内容因 source 而异，MVP 阶段用 Any）
3. 添加测试（至少 3 个）
4. 导出 JSON Schema
5. 更新 SPEC-REGISTRY.md Schema 表
6. **重要**：在模型注释中明确标注 "MVP 最小形态 — 完整 Context Bundle 设计由后续 SPEC 定义"

---

## Task 4：URI 解析规范文档 + Registry 同步

**目标**：将 SPEC-003 §11 的三种 URI 引用格式从"描述性规范"升级为"可执行文档"。

**三种 URI**：
```
evidence://{evidence_id}/{value_path}     — 引用 Evidence Packet 内字段
metric://{metric_id}                      — 引用 Metric Registry 条目
constraint://{playbook_id}/{version}/{constraint_id}  — 引用 Playbook Constraint
```

**要求**：
1. 在 SPEC-003 正文中（或创建独立文档 `docs/uri-resolution.md`），定义：
   - 每种 URI 的完整格式规范（正则表达式或 BNF）
   - 解析算法的伪代码（输入 URI → 输出 value + metadata）
   - 解析失败时的错误处理（insufficient_data vs error）
   - 与 Metric Registry（SPEC-005）的交互协议
2. 可选但推荐：在 spec003 中创建 `uri_resolver.py`，实现最小解析函数：
   ```python
   def parse_evidence_uri(uri: str) -> tuple[str, str]: ...
   def parse_metric_uri(uri: str) -> str: ...
   def parse_constraint_uri(uri: str) -> tuple[str, str, str]: ...
   ```
3. 如果实现了解析函数，添加测试
4. 更新 SPEC-REGISTRY.md 的"规范性 Schema"表，添加 URI 格式规范条目

---

## 全局约束

1. **枚举一致性**：所有修改完成后，遍历 SPEC-REGISTRY.md 的枚举表，确认每个枚举在代码中的定义与 Registry 完全一致。如有不一致，以代码为准更新 Registry（因为代码经过了测试验证）。

2. **跨包兼容性**：spec003 的模型被 spec004/005/006/009 消费。任何 spec003 的变更必须确认不破坏其他包的测试。运行全量测试验证。

3. **StrictModel 继承**：所有新模型必须继承 `StrictModel`（`extra="forbid"`）。

4. **commit 纪律**：
   - 所有修改整合为一次 commit
   - commit message：`fix: P0 interface freeze — review fixes + Investment Task/Context Bundle schemas + URI spec`
   - 不修改已 Approved 的 SPEC-006 和 SPEC-007 正文（除非是枚举值名称对齐这种纯文本同步）

5. **不做的事**：
   - 不开始 MVP 实现代码
   - 不修改 SPEC-007 的状态机
   - 不添加新的分析能力域定义
   - 不实现完整的 Context Bundle 数据获取逻辑
   - 不实现完整的 Decision Trace

---

## 验收标准

- [ ] `python -m pytest` 在 spec003/004/005/006/009 全部通过
- [ ] SPEC-REGISTRY.md 的枚举表、Schema 表、可执行覆盖表与代码一致
- [ ] SPEC-003 §8、§10.1、§13.3、§13.4 的 JSON 示例与模型一致
- [ ] Investment Task 模型有 ≥5 个测试
- [ ] Context Bundle 模型有 ≥3 个测试
- [ ] URI 解析有文档规范（至少伪代码级别）
- [ ] 没有死代码（空 validator、未使用的 import）
- [ ] 全量测试无回归

---

## 向用户汇报模板

完成后向用户汇报以下内容：

```markdown
## P0 接口冻结 — 完成报告

### 修改摘要
- Task 1（审查修复）：[具体修改内容]
- Task 2（Investment Task）：[模型字段 + 测试数]
- Task 3（Context Bundle）：[模型字段 + 测试数]
- Task 4（URI 规范）：[文档位置 + 解析函数状态]

### 测试结果
- spec003: X tests passed
- spec004: X tests passed
- spec005: X tests passed
- spec006: X tests passed
- spec009: X tests passed
- Total: X tests, all green

### Registry 同步状态
- 枚举表：[一致 / 已更新 X 处]
- Schema 表：[一致 / 已更新 X 处]
- 可执行覆盖表：[一致 / 已更新 X 处]

### P0 接口冻结完成度
- 修复前：29/47 (62%) 有可执行规格
- 修复后：X/47 (X%) 有可执行规格
- 剩余缺口：[列出]

### 遗留项
- [如果有]

### 下一步建议
- [能力域独立开发是否可以开始？还需要什么前置条件？]
```
