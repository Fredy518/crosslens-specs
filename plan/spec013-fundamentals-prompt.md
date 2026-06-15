# SPEC-REGISTRY 文档分类 + SPEC-013 Fundamentals 域实现规格

## 项目位置

```
E:\CodePrograms\CrossLens\crosslens-specs
```

Git 仓库，最新 commit `13c5515`。Python + Pydantic v2 + pytest。

---

## 架构背景（必读）

CrossLens 是一个可编排、可审计的 Agentic 投研决策工作流系统。架构宪法：

> **Deterministic first, Agentic when necessary, Traceable always.**

核心对象链（13 个对象）：
```
Investment Task → Context Bundle → Evidence Packets → Analysis Domain Jobs
→ Analysis Cards → Post-card Validation Report → Conflict Reports
→ Pre-decision Validation Report → Playbook Evaluation Report → Guardrail Report
→ Resolved Decision Bounds → Decision Candidate → Decision Trace
```

5 个分析能力域：`macro_meso`, `fundamentals`, `company_event`, `sentiment`, `technical_market`

**唯一事实源**：`SPEC-REGISTRY.md` — 所有枚举、Schema、依赖关系的权威定义在此。

**文档分层体系**（本次建立）：

| 文档类型 | 含义 | 对应 Kiro |
|:--------:|------|-----------|
| **需求** | 产品定位、用户场景、MVP 范围、数据治理 | requirements.md |
| **设计** | 架构、契约、接口、状态机、治理机制 | design.md |
| **实现** | 域内部管线、公式、数据源、confidence 模型 | design.md（详细设计） |
| **任务** | 开发任务拆解、验收标准、依赖关系 | tasks.md（不进 SPEC 编号，放 `plan/tasks-*.md`） |

---

## 执行方式：Team Agents

使用 team agents 模式。主 agent 负责任务分配、工作整合和最终汇报，子 agents 并行执行具体任务。

### 主 Agent 职责

1. 读取本 prompt 和以下文件建立全局理解：
   - `SPEC-REGISTRY.md`（全文）
   - `README.md`
   - `SPEC-004 五类分析能力域与 Analysis Card Schema v0.2.5.md`（§17~§22 Fundamentals 部分）
   - `SPEC-005 Capability Package 与 Metric Registry 规范 v0.2.md`（§2 架构概览 + §5 Metric Registry）
   - `SPEC-003 Agentic投研工作流架构 v0.3.4.md`（§6~§8 核心对象 + §11 Playbook Constraint）
   - `executable_specs/spec003/src/crosslens_spec003/models.py`（最新可执行契约）
   - `executable_specs/spec004/src/crosslens_spec004/models.py`（AnalysisCard 模型）
2. 将任务分配给子 agents（见下方 Task 1-2）
3. 子 agents 完成后：
   - 运行全量测试确认无回归
   - 检查 SPEC-REGISTRY.md 同步完整性
   - 整合为一次 commit，commit message：`feat: Registry doc classification + SPEC-013 Fundamentals implementation spec v0.1`
4. 向用户汇报（见底部汇报模板）

---

## Task 1：SPEC-REGISTRY 文档分类标注

**目标**：在 SPEC-REGISTRY.md 的 SPEC 索引表中新增 `文档类型` 列，标注每个 SPEC 属于"需求"、"设计"还是"实现"。

### 具体操作

1. 在 SPEC 索引表头增加 `文档类型` 列（放在"状态"列之后、"规范性范围"列之前）

2. 对现有 12 个 SPEC 标注如下：

| 编号 | 文档类型 | 说明 |
|------|:--------:|------|
| SPEC-001 | 需求 | 产品定义与边界 |
| SPEC-002 | 需求 | 用户画像与场景 |
| SPEC-003 | 设计 | 工作流架构 |
| SPEC-004 | 设计 | 能力域契约 |
| SPEC-005 | 设计 | 能力包与指标注册 |
| SPEC-006 | 设计 | Playbook 规则引擎 |
| SPEC-007 | 设计 | 编排状态机 |
| SPEC-008 | 设计 | 决策追踪 |
| SPEC-009 | 设计 | 护栏与评估器 |
| SPEC-010 | 需求 | MVP 范围 |
| SPEC-011 | 设计 | 案例库 |
| SPEC-012 | 需求 | 数据治理 |

3. 在"依赖关系（canonical）"图之后，新增"文档类型说明"章节：

```markdown
## 文档类型

CrossLens 规格体系采用四类文档分层：

| 类型 | 含义 | 编号范围 | 不详细定义 |
|------|------|---------|-----------|
| **需求** | 产品定位、用户场景、MVP 范围、数据治理 | SPEC-001/002/010/012 | 架构、接口、实现 |
| **设计** | 架构、契约、接口、状态机、治理机制 | SPEC-003~009/011 | 域内部管线、公式、数据源 |
| **实现** | 域内部管线、指标公式、数据源、confidence 模型 | SPEC-013~017 | 开发任务拆解 |
| **任务** | 开发任务拆解、验收标准、依赖关系 | `plan/tasks-*.md`（不进 SPEC 编号） | — |

规则：
- 实现类 SPEC 消费上游设计类 SPEC 的契约，不修改它们。
- 任务类文档不进入 SPEC-REGISTRY，不参与依赖图。
- 如果实现过程中发现设计契约有缺口，应向上游 SPEC 提变更请求，不在实现规格里打补丁。
```

4. 更新依赖关系图，加入 SPEC-013：

```
SPEC-004 (能力域) ──► SPEC-013 (Fundamentals 实现)
SPEC-005 (能力包) ──► SPEC-013
SPEC-003 (架构)   ──► SPEC-013
```

---

## Task 2：SPEC-013 Fundamentals 域实现规格 v0.1

**目标**：编写 SPEC-013，定义 Fundamentals 能力域的内部实现规格——从数据获取到 Analysis Card 生成的完整管线。

### 文件位置

```
SPEC-013 Fundamentals 域实现规格 v0.1.md
```

### 文档头

```markdown
# SPEC-013：Fundamentals 域实现规格

**版本：** v0.1
**状态：** Draft
**项目名称：** crosslens
**文档类型：** 实现
**依赖文档：** SPEC-003 v0.3.4；SPEC-004 v0.2.5；SPEC-005 v0.2
**上游契约：**
- SPEC-003 §8 (Analysis Domain Job 输入)
- SPEC-003 §6.5 (Evidence Packet schema)
- SPEC-004 §17~§22 (Fundamentals 域定义、输入、payload、constraint_exports、冲突、降级)
- SPEC-004 §4 (Analysis Card 通用 Schema)
- SPEC-004 §45 (MVP 最小实现范围)
- SPEC-005 §5 (Metric Registry)
- SPEC-005 §4.4 (Evidence Packet confidence 取值规则)
**目标阶段：** 域实现规格 / MVP 实现前置

---
```

### 章节结构（必须按此顺序）

#### §1 文档目标

说明本 SPEC 的定位：

- 定义 Fundamentals 域**内部如何工作**——从 Context Bundle + Evidence Packets 到 Analysis Card 的完整管线
- SPEC-004 §17~§22 定义了 Fundamentals 的"做什么"（WHAT），本 SPEC 定义"怎么做"（HOW）
- 本 SPEC 不修改上游契约。如果实现过程中发现上游契约有缺口，应记录在 §12 开放问题中，由后续修订向上游 SPEC 提变更请求

#### §2 域目标与边界

继承 SPEC-004 §17.1~§17.2，用一段话总结：
- Fundamentals 负责什么（基本面质量、财务表现、估值状态、长期投资基础）
- Fundamentals 不负责什么（短线择时、情绪、技术形态、宏观预测）
- 与其他 4 个域的切分边界

#### §3 Evidence Production Catalog

**这是本 SPEC 最核心的章节。**

定义 Fundamentals 域生产的所有 Evidence Packet 类型。每种类型一行：

| evidence_type | generation_type | determinism_level | can_support_hard_constraint | 字段清单（metrics/facts/labels） | 数据来源 |
|---|---|---|---|---|---|
| `financial_metrics` | computed | computed | true | revenue_growth_ttm, gross_margin_ttm, ... | 财务报表 API |
| `valuation_metrics` | computed | computed | true | pe_percentile_5y, ev_ebitda_percentile_5y, fcf_yield | 行情 API + 历史估值库 |
| `growth_quality_assessment` | structured | structured | false | growth_quality label | 规则模型 |
| ... | ... | ... | ... | ... | ... |

从 SPEC-004 §18（9 种 Evidence Packet 类型）+ §19（7 个 domain_payload 枚举）+ §20（13 个 constraint_exports metrics）反推完整的 Evidence Production Catalog。

**对每种 Evidence Packet 类型，必须定义：**

1. evidence_type 名称
2. generation_type（computed / structured / interpreted）
3. determinism_level
4. can_support_hard_constraint（true/false）
5. 完整的 metrics / facts / labels 字段清单（每个字段附单位/类型说明）
6. 数据来源（什么 API、什么数据库、什么频率）
7. confidence 赋值规则（引用 SPEC-005 §4.4）
8. 降级条件（什么情况下 confidence 降低、data_quality 降为 low/partial）

#### §4 Metric Catalog

从 SPEC-004 §20 的 13 个 constraint_exports metrics 出发，为每个 metric 定义：

| metric_id | display_name | 公式/计算逻辑 | 输入数据 | 单位 | 取值范围 | value_type | Metric Registry 条目 |
|---|---|---|---|---|---|---|---|
| `revenue_growth_ttm` | TTM 收入增速 | (当前季度收入 - 4 季度前收入) / 4 季度前收入 | 季度财务报表 revenue 字段 | percent | [-1.0, ∞) | number | 完整 JSON |
| `pe_percentile_5y` | 5 年 PE 分位 | 当前 PE 在过去 5 年 PE 序列中的百分位 | 日行情 + 季度 EPS | ratio | [0.0, 1.0] | number | 完整 JSON |
| ... | ... | ... | ... | ... | ... | ... | ... |

**每个 metric 的 Metric Registry 条目**（SPEC-005 §5.2 格式）必须给出完整 JSON。

**公式必须是确定性的伪代码或数学表达式**——不含模糊描述如"大约"、"通常"。

#### §5 Internal Pipeline

定义 Fundamentals 域的完整执行管线。使用分步骤伪代码：

```
function run_fundamentals_domain(job: AnalysisDomainJob) -> AnalysisCard:

    // Step 1: 输入过滤
    financial_evidence = filter_evidence(job.evidence_refs, types=[financial_metrics, ...])
    valuation_evidence = filter_evidence(job.evidence_refs, types=[valuation_metrics])
    if 输入不足: return unavailable_card(reason=insufficient_data)

    // Step 2: 确定性指标计算（computed）
    computed_metrics = compute_all_metrics(financial_evidence, valuation_evidence)
    // 每个指标的公式见 §4 Metric Catalog

    // Step 3: 结构化质量评估（structured）
    growth_quality = classify_growth_quality(computed_metrics)
    profitability_quality = classify_profitability(computed_metrics)
    // 每个分类器的规则见 §6 Determinism Map

    // Step 4: Evidence Packet 组装
    evidence_packets = assemble_evidence_packets(computed_metrics, structured_labels)

    // Step 5: Stance 判断
    stance = determine_stance(evidence_packets, domain_payload)
    // stance 判断规则见 §7 Stance Logic

    // Step 6: Confidence 计算
    confidence = compute_domain_confidence(evidence_packets)
    // confidence 模型见 §8 Confidence Model

    // Step 7: Analysis Card 生成
    card = build_analysis_card(job, evidence_packets, stance, confidence, domain_payload)
    // card 组装规则见 §9 Card Assembly

    // Step 8: 域级验证
    card = run_domain_validation(card)
    // 域级验证规则见 §10 Domain Validation

    return card
```

**关键约束**：
- 管线中的步骤必须标注 generation_type（computed / structured / interpreted）
- LLM 调用只能出现在 interpreted 步骤
- Hard Constraint 支撑的 metrics 必须全部来自 computed 步骤

#### §6 Determinism Map

为管线中每个步骤标注 generation_type 和 determinism_level：

| 步骤 | generation_type | determinism_level | 实现方式 | 说明 |
|------|:---:|:---:|------|------|
| 财务指标计算 | computed | computed | 确定性公式 | 可复现、可单测 |
| 估值分位计算 | computed | computed | 历史序列百分位 | 依赖历史数据完整性 |
| growth_quality 分类 | structured | structured | 规则模型/决策树 | 有明确输入输出 |
| valuation_state 分类 | structured | structured | 规则模型 | — |
| summary 生成 | interpreted | interpreted | LLM | 不可复现，不影响 Hard Constraint |
| key_findings 生成 | interpreted | interpreted | LLM | — |
| invalidating_conditions | interpreted | interpreted | LLM | — |

#### §7 Stance Logic

定义 stance 的判断规则。Fundamentals 的 stance 来自以下信号的组合：

| 信号 | 来源 | 权重方向 |
|------|------|---------|
| growth_quality | structured | strong/medium/weak → positive/neutral/negative |
| profitability_quality | structured | high/medium/low → positive/neutral/negative |
| cashflow_quality | structured | strong/medium/weak/negative → positive/neutral/negative/negative |
| valuation_state | structured | cheap/reasonable/expensive/very_expensive → positive/positive/negative/negative |
| balance_sheet_risk | structured | low/medium/high → positive/neutral/negative |

定义 stance 的聚合规则（伪代码或决策表）。明确：
- 什么条件下输出 `positive`
- 什么条件下输出 `moderately_positive`
- 什么条件下输出 `mixed`（信号冲突时）
- 什么条件下输出 `negative`
- 什么条件下输出 `unavailable`（数据不足）

#### §8 Confidence Model

定义 Fundamentals Analysis Card 的 confidence 如何从底层 Evidence Packet 聚合：

```
confidence = weighted_average(
    financial_confidence * financial_weight,
    valuation_confidence * valuation_weight,
    growth_confidence * growth_weight,
    ...
) * data_quality_factor
```

**必须定义：**
1. 每个子 confidence 的计算方式（computed evidence 默认 1.0，structured evidence 取模型自评分，interpreted evidence 取 LLM 自评分）
2. 各子项的权重
3. data_quality_factor 的取值规则（high=1.0, medium=0.8, low=0.5, unavailable=0.0）
4. 最终 confidence 的截断规则（不超过 SPEC-009 的 confidence_cap）
5. MVP 简化：如果某些子项不可用，confidence 如何降级

#### §9 Card Assembly

定义 Analysis Card 各字段的填充规则：

| 字段 | 填充来源 | 规则 |
|------|---------|------|
| `domain_status` | 管线执行结果 | completed / partial / error / unavailable |
| `domain_status_reason` | 当 status ∈ {error, unavailable} | insufficient_data / execution_failure / data_source_unavailable |
| `summary` | LLM 生成（interpreted） | 1-2 句话，必须引用 supporting/opposing evidence |
| `stance` | §7 Stance Logic | — |
| `confidence` | §8 Confidence Model | — |
| `confidence_reason` | §8 的子项明细 | 列出主要影响因素 |
| `supporting_evidence` | Evidence Packets 中 signal ∈ {positive} 的 | 必须引用 evidence_id |
| `opposing_evidence` | Evidence Packets 中 signal ∈ {negative} 的 | 必须引用 evidence_id |
| `constraint_exports` | §4 Metric Catalog 中的 computed metrics | 每个 export 必须声明 can_support_hard_constraint |
| `domain_payload` | §19 domain_payload 枚举值 | growth_quality, profitability_quality, ... |
| `data_freshness` | 所有 Evidence Packets 的 as_of 最旧/最新 | 按 SPEC-004 §4.3 规则 |
| `time_horizon` | Fundamentals 固定 medium_term / long_term | — |
| `key_risks` | 结构化规则 + LLM 补充 | — |
| `invalidating_conditions` | 结构化规则 + LLM 补充 | — |
| `warnings` | 域级验证产出 | — |

#### §10 Domain Validation

定义超出 SPEC-004 §41 通用规则的域级检查：

| 检查项 | 触发条件 | 严重度 | 处理 |
|--------|---------|:------:|------|
| 财报数据过期 >90 天 | data_freshness.oldest > 90 days ago | flag | 降低 confidence |
| 财报数据过期 >180 天 | data_freshness.oldest > 180 days ago | block | domain_status = partial |
| 估值数据缺失 | valuation_metrics Evidence Packet 不存在 | flag | 移除估值相关 constraint_exports |
| 收入增速与行业增速同源 | 两者来自同一个 Evidence Packet | flag | 标记 lineage 风险 |
| completed + 无 supporting_evidence | domain_status=completed 但 supporting_evidence=[] | flag | 检查 stance 逻辑 |

#### §11 Data Source Requirements

定义 MVP 阶段 Fundamentals 域需要的数据源：

| 数据源 | 类型 | 内容 | 获取频率 | MVP 数据源 | Fallback 策略 |
|--------|------|------|---------|-----------|-------------|
| 财务报表 | API | income_statement, balance_sheet, cash_flow | 季度 | [待定：SEC EDGAR / 商业 API] | 若不可用 → domain_status=unavailable |
| 行情数据 | API | price, market_cap, shares_outstanding | 日 | [待定：Yahoo Finance / 商业 API] | 若不可用 → 估值指标 unavailable |
| 行业对标 | API/DB | industry_median metrics | 季度 | [待定：自建或商业] | 若不可用 → 行业比较降级 |
| 历史估值序列 | DB | 5 年 PE/EV-EBITDA 序列 | 日 | [待定：自建] | 若不可用 → percentile unavailable |

**MVP 数据源标注为 [待定]**——本 SPEC 定义需要什么数据，不定义用哪个具体供应商。具体供应商选择留到 tasks.md。

**Fallback 策略**必须定义每种数据源不可用时的降级路径，与 §5 管线的 unavailable 分支对齐。

#### §12 MVP Scope

明确 Fundamentals 域 MVP 交付什么、不交付什么：

**MVP 交付：**
1. 完整的 computed Evidence 计算管线（13 个 metrics）
2. 结构化质量分类（7 个 domain_payload 枚举）
3. Analysis Card 生成（含所有必填字段）
4. constraint_exports 正确导出
5. 域级验证（§10 的 5 项检查）
6. 确定性部分可单元测试

**MVP 不交付（明确排除）：**
1. 完整 LLM summary 生成（可用模板占位）
2. 实时数据推送（MVP 用批量拉取）
3. 多市场适配（MVP 仅支持 US 市场）
4. 历史回测验证
5. 自动数据源切换

**Mock 策略：**
- MVP 阶段允许 mock 数据源（JSON fixture files）
- mock 数据必须覆盖 happy path + 至少 2 个降级场景
- mock 数据的 schema 必须与真实数据源的 schema 一致

#### §13 Testability

定义 Fundamentals 域的可测试性要求：

| 测试类型 | 覆盖范围 | 目标 |
|---------|---------|------|
| 单元测试 | 每个 computed metric 公式 | 给定输入 → 确定性输出 |
| 单元测试 | 每个 structured 分类器 | 给定指标 → 正确 label |
| 单元测试 | confidence 聚合公式 | 给定子 confidence → 正确总 confidence |
| 集成测试 | 完整管线（mock 数据） | 给定 fixture → 正确 AnalysisCard |
| 边界测试 | 数据缺失、过期、矛盾 | 正确降级 + 正确 domain_status |
| 契约测试 | AnalysisCard 符合 spec004 Pydantic 模型 | 序列化 + 反序列化无错 |

### 全局约束

1. **不修改上游 SPEC**：SPEC-003/004/005/006/007/009 的正文不做任何修改
2. **枚举一致性**：SPEC-013 中使用的所有枚举值必须与 SPEC-REGISTRY 一致
3. **不写实现代码**：本 SPEC 是设计文档，不是代码。可以有伪代码，但不创建 Python 文件
4. **引用精确**：每次引用上游 SPEC 时，必须标注章节号（如 "SPEC-004 §20"）
5. **公式确定性**：§4 Metric Catalog 中的每个公式必须是确定性的数学表达式或伪代码，不含模糊描述
6. **MVP 边界显式**：§12 中明确排除的项不在 §3~§10 中展开

### 不做的事

- 不写 Python 实现代码
- 不修改 SPEC-003/004/005/006/007/009
- 不创建 executable_specs/spec013/
- 不写 tasks.md（那是下一步）
- 不定义其他 4 个域的实现规格（SPEC-014~017）

---

## 验收标准

- [ ] SPEC-REGISTRY.md 的 SPEC 索引表有 `文档类型` 列，12 个 SPEC 全部标注
- [ ] SPEC-REGISTRY.md 有"文档类型说明"章节，定义四类文档分层
- [ ] SPEC-REGISTRY.md 的依赖关系图包含 SPEC-013
- [ ] SPEC-013 文件存在且格式正确
- [ ] SPEC-013 §3 Evidence Production Catalog 覆盖 SPEC-004 §18 的 9 种 Evidence Packet 类型
- [ ] SPEC-013 §4 Metric Catalog 覆盖 SPEC-004 §20 的 13 个 constraint_exports metrics
- [ ] SPEC-013 §4 每个 metric 有完整的 Metric Registry JSON 条目
- [ ] SPEC-013 §4 每个 metric 的公式是确定性数学表达式
- [ ] SPEC-013 §5 Internal Pipeline 伪代码覆盖从输入到输出的完整步骤
- [ ] SPEC-013 §6 Determinism Map 为每个管线步骤标注 generation_type
- [ ] SPEC-013 §8 Confidence Model 有明确的聚合公式
- [ ] SPEC-013 §12 MVP Scope 显式声明交付/不交付/排除项
- [ ] 全量测试无回归（spec003/004/005/006/009 全部通过）
- [ ] 不修改任何上游 SPEC 正文

---

## 向用户汇报模板

```markdown
## SPEC-REGISTRY 分类 + SPEC-013 完成报告

### Task 1: Registry 文档分类
- 新增 `文档类型` 列：12 个 SPEC 已标注（需求 ×4 / 设计 ×8）
- 新增"文档类型说明"章节
- 依赖关系图已更新

### Task 2: SPEC-013 Fundamentals 域实现规格
- 文件位置：`SPEC-013 Fundamentals 域实现规格 v0.1.md`
- 章节覆盖：§1~§13 全部完成
- Evidence Production Catalog：X 种 Evidence Packet 类型
- Metric Catalog：13 个 metrics，每个有完整公式 + Metric Registry JSON
- Internal Pipeline：X 步骤伪代码
- Determinism Map：computed ×X / structured ×X / interpreted ×X
- Confidence Model：聚合公式 + 权重 + 降级规则
- Domain Validation：X 项检查
- MVP Scope：交付 X 项 / 排除 X 项

### 上游 SPEC 修改情况
- 无（本 SPEC 不修改上游契约）

### 测试结果
- spec003: X tests passed
- spec004: X tests passed
- spec005: X tests passed
- spec006: X tests passed
- spec009: X tests passed
- Total: X tests, all green

### 开放问题（记录在 SPEC-013 §12 中）
- [列出发现的缺口或向上游 SPEC 的变更请求]

### 下一步建议
- SPEC-013 可进入 Review 状态
- 后续可并行编写 SPEC-014（Technical）、SPEC-015（Macro）
- SPEC-013 Review 通过后，可编写 `plan/tasks-fundamentals.md` 进入编码阶段
```
