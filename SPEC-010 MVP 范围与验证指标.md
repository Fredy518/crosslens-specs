# SPEC-010：MVP 范围与验证指标

**版本：** v0.1
**状态：** Draft
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4；SPEC-004 v0.2.5；SPEC-005 v0.2；SPEC-006 v0.3.0；SPEC-007 v0.6；SPEC-008 v0.1；SPEC-009 v0.1；SPEC-011 v0.1；SPEC-012 v0.1
**文档类型：** MVP 范围定义
**目标阶段：** MVP 范围划定 / 验证指标定义

---

## 0. 版本说明

v0.1 是 SPEC-010 初稿。本文档是 crosslens MVP 的"宪法级"范围定义——所有其他 SPEC 中分散的 MVP 决策在这里汇总为单一入口。

核心原则：

```text
Scope decides what ships.
Verification decides if it ships.
Trade-offs must be explicit.
```

中文表达：

```text
范围决定交付什么。
验证决定能否交付。
取舍必须显式声明。
```

---

## 1. 文档目标

SPEC-010 用于：

1. 汇总 crosslens MVP 的完整范围定义；
2. 明确 MVP 包括什么、不包括什么、为什么；
3. 定义 MVP 的验证标准和成功指标；
4. 提供 MVP 交付前的检查清单。

本 SPEC 不引入新机制——所有范围决策在其他 SPEC 中已定义，此处仅聚合。

---

## 2. MVP 哲学

### 2.1 MVP 是什么

crosslens MVP 是一个**最小可用投研工作流**——它能完成一次完整的单股票分析，从用户输入到 Decision Trace 输出。

MVP 的目标不是功能完整，而是**验证核心架构假设**：

```text
假设 1：Deterministic-first 架构可以正确执行投资 Playbook 的 Hard Constraint。
假设 2：对象流转型 Workflow 可以生成可审计的 Decision Trace。
假设 3：能力域隔离 + Conflict Detection 可以暴露（而非隐藏）跨维度矛盾。
假设 4：Guardrail + Evaluator + Human Review 可以在不引入黑箱的情况下控制输出安全。
```

### 2.2 MVP 不是什么

- 不是生产级系统；
- 不支持实时交易；
- 不支持多股票组合分析；
- 不支持用户自定义 Playbook（仅内置一个默认 Playbook）；
- 不支持多用户协作。

### 2.3 MVP 取舍原则

```text
1. 深度优先于广度——做一个分析做对，胜过做五个分析都半成品。
2. 确定性优先于智能——规则引擎和 Guardrail 优先于 LLM 自适应。
3. 可审计优先于自动化——Decision Trace 优先于自动决策循环。
4. 单股票优先于组合——先验证单股票 Workflow，再扩展。
```

---

## 3. MVP 范围总表

### 3.1 功能范围矩阵

| 领域 | 包括 | 不包括 |
|---|---|---|
| **任务类型** | `single_stock_buy_decision`, `research_explanation` | 多股票扫描、组合分析、卖出决策 |
| **资产类型** | 美股普通股 | ETF、期权、期货、加密货币、A 股 |
| **Playbook** | 1 个内置 `capital_cycle_fundamental_playbook` | 用户自定义 Playbook、多 Playbook 对比、Playbook 市场 |
| **分析能力域** | 5 个全部（Macro/Meso, Fundamentals, Company Event, Sentiment, Technical/Market） | 自定义能力域、能力域扩展 |
| **证据类型** | Computed, Structured, Interpreted（全部三种） | 自定义证据类型 |
| **Workflow** | `single_stock_standard_analysis_workflow`, `research_explanation_workflow` | 自定义 Workflow、Workflow 编辑器 |
| **Guardrail** | 6 条硬编码 Guardrail 规则 | 自定义 Guardrail、Guardrail 配置界面 |
| **Evaluator** | 四维质量检查（证据、推理、置信度、完整性） | 自动重生成循环 |
| **Human Review** | 信号汇聚 + Candidate 阻止 | 实时交互界面、超时自动降级 |
| **Decision Trace** | 完整四层 Trace（Run/Phase/Node/Evidence） | Trace 可视化 UI、Trace 对比 |
| **Case Library** | 匿名化写入 + 六维索引 + 基础只读查询（按 ticker/date 精确查） | 案例相似匹配、语义检索、决策建议 |
| **数据治理** | 三分类（user_private/system_generated/public_reference）、基本隔离 | 协作共享、数据导出 |
| **Capability Package** | Metric Registry（33 metrics, 6 facts, 7 labels） | 完整 Package 市场、动态加载 |
| **用户界面** | CLI + Decision Trace 文本输出 | Web UI、图表、交互式仪表盘 |

### 3.2 组件实现深度

| 组件 | MVP 深度 | 为什么 |
|---|---|---|
| Task Routing | 完整——两种 task_type 的路由 | 这是 Workflow 入口 |
| Playbook Routing | 完整——单个 Playbook 匹配 | MVP 只有一个 Playbook |
| Evidence Routing | 完整——三种 generation_type 分配 | 这是确定性优先的基础 |
| Domain Dispatch | 并行派发 5 个能力域 | 能力域独立性的核心验证 |
| Post-card Validation | 完整——8 项 schema 检查 | 确定性检查，成本极低 |
| Pre-decision Validation | 完整——6 项阈值检查 | 确保 Playbook 可执行 |
| Conflict Detection | 完整——跨域冲突检测 | 核心假设验证 |
| Playbook Evaluation | 完整——四种 evaluation_mode | 核心假设验证 |
| Guardrail Check | 6 条规则 | 覆盖核心安全场景 |
| Evaluator | 检查 + 标记（不重写） | Token 成本控制 |
| Bounds Resolution | 完整合并算法 | 所有约束的终点 |
| Candidate Generation | 完整——从 Bounds 生成 | 终端输出 |
| Decision Trace | 完整四层 + 伪代码 | 核心假设验证 |
| Case Write | 匿名化写入 + 索引（精确查不检索） | 为未来语义检索做准备 |
| Case Query | 按 ticker / date 精确查询 | 不从索引做模糊/语义匹配 |
| Research Explanation | 完整——解释性输出 | 第二个 task_type |

---

## 4. 各 SPEC MVP 范围详解

### 4.1 SPEC-001（产品定义）MVP 边界

交叉验证：MVP 产品定位与 SPEC-001 定义一致。

确认点：
- crosslens 是辅助决策系统，不是自动交易系统；
- 输出 Decision Candidate，不是交易指令；
- 完整 Decision Trace 是 MVP 硬性要求。

### 4.2 SPEC-003（架构）MVP 边界

| 项目 | 要求 |
|---|---|
| 七层架构 | 全部层必须存在，但细节可简化 |
| 核心对象链 | 全部 13 个对象必须实现 |
| 能力域隔离 | 域之间不得直接调用 |
| 两阶段 Validation | 完整实现 |
| Event Log | MVP schema 完整 |
| Decision Trace | ref-only → SPEC-008 展开 |

### 4.3 SPEC-004（能力域）MVP 边界

每个能力域必须实现（§45）：

```text
1. 输入 Evidence Packet 过滤
2. Analysis Card 生成
3. domain_status 判断
4. data_quality 判断
5. confidence 赋值
6. supporting_evidence / opposing_evidence 引用
7. constraint_exports 输出
8. warnings / limitations 输出
9. domain_payload 输出
10. Domain Event Log
```

**MVP 暂不实现的能力：**
- Technical/Market 的 investment vs trading type 区分；
- Macro/Meso 的行业供需模型扩展；
- Sentiment 的跨平台情绪聚合。

### 4.4 SPEC-005（Capability Package）MVP 边界

必须实现（§11）：

```text
Metrics: 33 个（P0）
Facts: 6 个（P0）
Labels: 7 个（P0）
```

暂不实现：
- P1 metrics（完整列表见 SPEC-005 §11.2）；
- 动态 Metric 注册；
- Package 市场。

### 4.5 SPEC-006（Playbook）MVP 边界

必须实现（§43）：

```text
1. 静态内置 Playbook × 1
2. Playbook Metadata
3. Applicability 基础检查
4. 四种 evaluation_mode
5. Hard Constraint Evaluation
6. Soft Constraint Evaluation
7. Preference 记录
8. Freshness Requirements
9. Conflict Handling
10. Playbook Evaluation Report
11. recommended_decision_bounds
12. playbook_snapshot_hash
13. Decision Trace 中的 Playbook 版本展示
14. Executable Specification + Pydantic 契约 + JSON Schema + 边界测试
```

### 4.6 SPEC-007（Orchestration）MVP 边界

必须实现（§57）：

```text
1. Run State Machine
2. Workflow Template + Node Schema
3. Run State Schema
4. Event Log Schema
5. WorkflowResult Schema
6. single_stock_standard_analysis_workflow
7. research_explanation_workflow
8. Post-card + Pre-decision Validation
9. Conflict Detection + Report
10. Playbook Evaluation 调用
11. Guardrail Check
12. Resolve Decision Bounds
13. Decision Candidate generation
14. Research Explanation generation
15. Decision Trace generation
16. Failure Trace
17. Recoverable Error handling
18. Cumulative degradation upgrade
```

### 4.7 SPEC-008（Decision Trace）MVP 边界

必须实现（§9）：

```text
1. 四层 Trace 结构（Run/Phase/Node/Evidence）
2. Evidence Links（5 类链路）
3. reasoning_chain
4. key_findings
5. observability（phase_durations, degradations, human_review_triggers）
6. Event Log summary
7. Trace 生成伪代码实现
8. CLI 最小可展示格式
9. Trace 不可变性保证
10. Failure Trace 尽力而为策略
11. trace_id → Decision Trace 展开
```

### 4.8 SPEC-009（Governance）MVP 边界

必须实现（§9.1）：

```text
1. 6 条 Guardrail 规则引擎
2. Guardrail 边界收窄算法
3. Evaluator 四维质量检查
4. confidence_cap 合并算法
5. Human Review 六来源汇聚
6. requires_human_review 阻止 Candidate
7. Guardrail Report + Evaluation Report schema
8. Governance findings → Decision Trace
9. 证据污染检测（递归 lineage）
10. Resolved Decision Bounds 完整合并
```

### 4.9 SPEC-011（Case Library）MVP 边界

必须实现：
- Case 匿名化写入
- 六维索引构建
- 基础只读查询接口

暂不实现：
- 案例相似匹配
- 案例驱动决策建议
- 语义检索

### 4.10 SPEC-012（数据治理）MVP 边界

必须实现：
- 三分类标记（user_private / system_generated / public_reference）
- `uses_user_private_data` flag
- 基本隔离规则
- 删除接口

暂不实现：
- 多用户协作
- Case Library 匿名化流水线

---

## 5. MVP 验证标准

### 5.1 功能验证：核心路径

```text
验证路径 1：正常完整流程

Input: 用户提交单股票买入分析任务（ticker: NVDA, playbook: capital_cycle_fundamental）
Expected:
  1. Task 解析正确 → task_type = single_stock_buy_decision
  2. Playbook 加载 → Applicability 检查通过
  3. Evidence Packets 生成 → 5 个能力域各有 Evidence
  4. Analysis Cards 生成 → 5 张 Card，domain_status 包含 completed/partial
  5. Post-card Validation → 无 Block 级错误
  6. Conflict Detection → 如有冲突，写入 Conflict Report
  7. Pre-decision Validation → 通过
  8. Playbook Evaluation → 生成 Playbook Evaluation Report
  9. Guardrail Check → 无 Block 级 Guardrail
  10. Evaluator → overall_quality 至少 acceptable_with_caveats
  11. Bounds Resolution → allowed_actions 非空
  12. Candidate Generation → suggested_action ∈ allowed_actions
  13. Decision Trace → 四层完整，所有引用可展开
  14. WorkflowResult → run_status = completed

Success Metric: 端到端完成率 ≥ 90%（给定合理输入）
```

```text
验证路径 2：数据不足降级

Input: 用户提交分析任务，但指定 ticker 无足够财务数据
Expected:
  1. Fundamentals Card → domain_status = partial / unavailable
  2. Validation → 检测到 required domain domain_status ∈ {partial, unavailable}
  3. Playbook Evaluation → overall_result = need_more_data
  4. Guardrail → insufficient_data_guard 触发
  5. Bounds → allowed_actions 仅包含 {wait, add_to_watchlist} 或 need_more_data
  6. WorkflowResult → user_visible_status = need_more_data
  7. Decision Trace → 完整记录降级原因

Success Metric: 降级正确率 = 100%（不产生虚假方向性建议）
```

```text
验证路径 3：Playbook Hard Constraint Fail

Input: 用户提交任务，但资产不满足 Playbook 的关键 Hard Constraint
Expected:
  1. Playbook Evaluation → Hard Constraint fail → blocking
  2. Playbook Evaluation Report → overall_result = not_passed_for_new_buy
  3. recommended_decision_bounds 不包含 buy
  4. Guardrail → 不放行被 Playbook 拒绝的动作
  5. Candidate → suggested_action ≠ buy
  6. Decision Trace → 完整记录 fail 原因和证据

Success Metric: Hard Constraint 执行正确率 = 100%
```

```text
验证路径 4：Guardrail 触发

Input: 系统产生买入建议但置信度不足
Expected:
  1. Playbook Evaluation → 通过
  2. Guardrail → no_ungrounded_strong_opinion 触发
  3. Guardrail Report → blocked_actions 包含 buy / add_position
  4. Bounds → buy / add_position 被移除
  5. Candidate → suggested_action ∉ {buy, add_position}

Success Metric: Guardrail 阻止率 = 100%（Guardrail 触发后方向性建议不出现在 Candidate）
```

```text
验证路径 5：Research Explanation

Input: 用户提交研究解释任务
Expected:
  1. Task Routing → research_explanation_workflow
  2. 不产生 Decision Candidate
  3. 产生 Research Explanation
  4. WorkflowResult → user_visible_status = research_explanation_ready

Success Metric: 解释输出包含所有引用来源
```

### 5.2 架构验证：不变量检查

```text
不变量检查清单：

□ 1. 能力域之间不得直接调用
□ 2. Candidate 只能从 Bounds 生成
□ 3. requires_human_review 不出现在 allowed_actions 中
□ 4. Guardrail 只能收窄 bounds
□ 5. Evaluator 不自动重写
□ 6. confidence_cap 由规则决定，不由 LLM 随机生成
□ 7. Evidence 的 can_support_hard_constraint 不得被下游绕过
□ 8. structured evidence 默认不支撑 Hard Constraint
□ 9. interpreted evidence 永远不支撑 Hard Constraint
□ 10. Decision Trace 是 append-only
□ 11. user_private 数据不进入 Case Library
□ 12. failure trace 是 best-effort
□ 13. schema errors → validation findings，不是 runtime crash
□ 14. all degradations → Decision Trace
```

### 5.3 质量指标

| 指标 | 目标值 | 测量方法 |
|---|---|---|
| 端到端完成率 | ≥ 90% | 正常输入下的 completed/(completed + failed) |
| Hard Constraint 正确率 | 100% | 手工验证 20 个已知结果案例 |
| Guardrail 阻止率 | 100% | Guardrail 触发后强建议不出现在 Candidate |
| 降级正确率 | 100% | 数据不足时不产生方向性建议 |
| Decision Trace 完整性 | ≥ 95% | 所有 required 字段非空 |
| 平均 Token 消耗 | 记录基线 | 单次完整分析的 Token 总量 |
| 平均执行时间 | 记录基线 | 单次完整分析的 wall-clock 时间 |
| Evaluator 不重写率 | 100% | Evaluator 输出中无重写痕迹 |

---

## 6. MVP 排除项汇总

### 6.1 功能性排除

```text
1. 多股票批量扫描
2. 组合分析（portfolio analysis）
3. 组合仓位管理（position sizing）
4. 卖出决策 Workflow（仅 buy_decision）
5. 自动交易
6. 实时市场数据流
7. 用户自定义 Playbook
8. 多 Playbook 对比
9. Playbook Marketplace
10. Playbook 自动生成/优化
11. 自定义能力域
12. 能力域动态加载
13. Case Library 语义检索/相似匹配
14. 多用户协作
15. 可视化 Workflow 编辑
16. 图表输出
17. 移动端
```

### 6.2 技术性排除

```text
1. Evaluator 自动重生成循环
2. 全量异步 Runtime
3. 自动 Retry
4. Human Review 实时交互界面
5. human_review_mode = allow_labeled_candidate
6. case 相似匹配算法
7. 自适应 Guardrail 阈值
8. 跨 Run 质量趋势分析
9. 动态 Metric 注册
10. Package 市场
11. A/B 测试框架
```

### 6.3 资产类型排除

```text
1. ETF
2. 期权
3. 期货
4. 加密货币
5. 固定收益
6. 外汇
7. A 股 / 港股
8. 私募股权
```

---

## 7. MVP 交付检查清单

### 7.1 代码制品

```text
□ SPEC-006 Executable Specification (executable_specs/spec006/)
   □ decision_logic.py — multi_rule, overall_result, 动作边界, confidence_cap
   □ models.py — Pydantic v2 契约
   □ tests/ — 边界测试（全部通过）
   □ schemas/ — 生成 JSON Schema

□ SPEC-007 Run State Machine 实现
□ SPEC-004 Analysis Card Schema 的实现和验证
□ SPEC-005 Metric Registry 的最小实现
□ SPEC-009 Guardrail 规则引擎的实现
□ SPEC-008 Decision Trace 生成器的实现
```

### 7.2 测试制品

```text
□ 5 条核心验证路径的集成测试
□ 14 条架构不变量的自动化检查
□ 20 个已知结果案例的手工验证
□ Executable Specification 的全部边界测试通过
```

### 7.3 文档制品

```text
□ SPEC-001 v0.4（产品定义）
□ SPEC-002 v0.1（目标用户与核心场景）
□ SPEC-003 v0.3.4（架构）
□ SPEC-004 v0.2.5（能力域）
□ SPEC-005 v0.2（Capability Package & Metric Registry）
□ SPEC-006 v0.3.0（Playbook）+ Executable Specification
□ SPEC-007 v0.6（Orchestration）
□ SPEC-008 v0.1（Decision Trace）
□ SPEC-009 v0.1（Governance）
□ SPEC-010 v0.1（MVP 范围——本文档）
□ SPEC-011 v0.1（Case Library）
□ SPEC-012 v0.1（数据治理）
```

---

## 8. MVP 成功定义

### 8.1 硬性通过条件

```text
1. 端到端完整流程可运行——从用户输入到 Decision Trace 输出。
2. 架构宪法不可违反——Deterministic first, Agentic when necessary, Traceable always。
3. 14 条不变量全部通过自动化检查。
4. Hard Constraint 执行正确率 = 100%。
5. Guardrail 阻止率 = 100%。
6. Decision Trace 在所有路径下完整。
```

### 8.2 软性通过条件

```text
1. 端到端完成率 ≥ 90%。
2. 平均执行时间在可接受范围内（基线记录后确定）。
3. Token 成本在预算范围内（基线记录后确定）。
4. 用户可在 Decision Trace 中手工审计决策链路。
```

### 8.3 MVP 不验证的事项

```text
1. 投资建议的准确性（MVP 是架构验证，不是策略验证）。
2. 用户满意度。
3. 长期运行稳定性。
4. 跨市场适配性。
```

---

## 9. 后续版本路线图

| 版本 | 核心新增 |
|---|---|
| v0.2 | 多股票扫描 + 第二个内置 Playbook |
| v0.3 | Case Library 检索 + 案例匹配 |
| v0.4 | 用户自定义 Playbook |
| v0.5 | 组合分析 + 仓位管理 |
| v1.0 | 生产级就绪 + Web UI |

---

## 10. v0.1 总结

SPEC-010 v0.1 是 crosslens MVP 的范围宪法。

本版本完成：

1. MVP 哲学声明——深度优先、确定性优先、可审计优先；
2. 功能范围矩阵——12 个领域 × 3 列（包括/不包括/为什么）；
3. 各 SPEC MVP 范围详解——11 个 SPEC 的精确 MVP 边界；
4. 5 条核心验证路径 + 预期结果 + 成功指标；
5. 14 条架构不变量检查清单；
6. 8 项质量指标 + 目标和测量方法；
7. 43 项功能性 + 技术性排除（含理由）；
8. MVP 交付检查清单——代码、测试、文档；
9. MVP 成功定义——硬性通过条件 + 软性通过条件；
10. 后续版本路线图。

核心结论：

```text
MVP = 单股票 × 1 Playbook × 5 能力域 × 完整 Workflow × 完整 Trace。
目标是验证架构假设，不是交付完整产品。
取舍必须显式——范围的边界就是产品的边界。
```

---

## 11. 后续 SPEC 依赖

SPEC-010 汇总所有 SPEC 的 MVP 范围，本身是终端文档。以下 SPEC 在 MVP 交付时依赖本文件的范围定义：

1. 所有 SPEC 的 MVP 实现章节（以此文件为唯一范围仲裁来源）；
2. 后续版本路线图（§9）定义了 v0.2-v1.0 的扩展方向。
