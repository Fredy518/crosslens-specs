# SPEC-001：产品定义与边界

**版本：** v0.4  
**状态：** Draft  
**项目名称：** crosslens  
**产品类型：** 可编排、可审计的 Agentic 投研决策工作流系统  
**目标阶段：** 产品定义 / 概念验证前置规格  
**关联文档：** SPEC-003 v0.3.4

---

## 1. v0.4 修订目标

SPEC-001 v0.4 的目标不是扩展产品细节，而是对齐 SPEC-003 v0.3.4 中已经稳定下来的架构定义。

v0.4 主要修订：

1. 将产品级架构从早期六层描述更新为与 SPEC-003 v0.3.4 一致的七层职责分层；
2. 增加核心对象链占位，明确 crosslens 不是 LLM 直接输出建议，而是对象流转型投研工作流；
3. 将 Evidence Packet、Analysis Card、Validation Report、Conflict Report、Playbook Evaluation Report、Guardrail Report、Resolved Decision Bounds、Decision Candidate、Decision Trace 纳入产品级心智模型；
4. 明确 SPEC-001 只定义产品定位、边界和核心概念，执行架构以 SPEC-003 为准；
5. 将后续 SPEC 列表与 SPEC-003 v0.3.4 对齐。

---

## 2. 产品一句话定义

crosslens 是一个 **可编排、可审计、可复盘的 Agentic 投研决策工作流系统**。

它通过数据连接器、模型、工具、工作流、Agent、Investment Playbook、案例记忆、护栏、评估体系和 Decision Trace，帮助用户对股票或资产形成结构化、可解释、可复盘的投资判断。

crosslens 不是让 Agent 直接替用户做投资决策，而是让用户清楚看到：

```text
系统理解了什么任务；
使用了哪些数据；
生成了哪些证据；
哪些分析能力域参与了判断；
哪些证据支持；
哪些证据反对；
哪些冲突存在；
哪些 Playbook 条件被触发；
哪些 Guardrail 生效；
为什么生成当前 Decision Candidate；
哪些条件会让结论失效；
用户下一步应该检查什么。
```

---

## 3. 产品定位

### 3.1 产品是什么

crosslens 是面向投资研究和投资决策辅助的 Agentic Workflow System。

它的核心能力是：

1. 组织复杂投研任务；
2. 调用合适的数据、模型和工具；
3. 根据任务类型选择执行路径；
4. 通过工作流和能力域生成结构化分析；
5. 按照 Investment Playbook 形成决策候选；
6. 展示完整 Decision Trace；
7. 支持用户审阅、反馈和复盘。

### 3.2 产品不是什么

crosslens 不是：

1. 自动交易机器人；
2. 黑箱荐股系统；
3. 收益承诺工具；
4. 纯新闻摘要产品；
5. 纯财报问答产品；
6. 纯多 Agent 角色扮演系统；
7. 纯量化因子平台；
8. 直接替代持牌投顾或合规投资建议的系统；
9. 直接替用户决定买入、卖出或持仓的系统。

crosslens 的核心定位不是：

> 直接告诉用户买什么。

而是：

> 帮助用户按照清晰、透明、可复盘的投研流程，判断一项投资决策是否成立。

---

## 4. 核心用户

### 4.1 专业个人投资者

具备自主投资决策需求，愿意研究股票、行业和市场，但缺少系统化工具来组织自己的分析流程。

典型需求：

1. 快速形成一只股票的结构化分析；
2. 检查投资逻辑是否完整；
3. 获取反方观点；
4. 按自己的投资风格判断是否值得买入、持有、等待或回避；
5. 记录和复盘每次投资判断；
6. 避免被单条新闻、社媒情绪或短期价格波动带偏。

### 4.2 小型投研团队

来自小型基金、家办、独立研究团队或投资社群，需要更高效覆盖股票池，并生成标准化研究底稿。

典型需求：

1. 标准化单股票研究流程；
2. 对候选股票进行初筛和深度分析；
3. 生成投委会前置材料；
4. 保留分析链路和证据；
5. 复盘历史判断质量；
6. 在不同成员之间统一分析框架。

### 4.3 AI-native 投资工作流探索者

关注如何把 LLM、Agent、模型、工具和投资流程结合起来，希望基于 crosslens 搭建自己的投研系统。

典型需求：

1. 配置 Investment Playbook；
2. 接入不同模型和数据源；
3. 观察 Agentic Workflow 如何执行；
4. 建立个人或团队的投资方法论资产；
5. 迭代能力包、案例库和评估集。

---

## 5. 核心问题

crosslens 要解决的核心问题是：

> 投资者在面对复杂市场信息时，缺少一个可编排、可解释、可定制、可复盘的 AI 投研决策工作流。

具体包括：

1. 信息过载；
2. 分析方法不稳定；
3. 模型输出、事实证据和主观判断混杂；
4. 决策链不透明；
5. 用户投资风格难以表达为可执行流程；
6. 研究与风控割裂；
7. 多分析模块之间缺少统一编排；
8. 历史判断难以复盘。

---

## 6. 核心原则

crosslens 的架构宪法是：

> **Deterministic first, Agentic when necessary, Traceable always.**

中文表达：

> **确定性优先；必要时才使用 Agentic 推理；全过程必须可追踪。**

这意味着：

1. 能用确定性流程、规则、指标、模型或工具解决的问题，不强行使用 Agent；
2. Agent 不应直接基于模糊上下文自由分析，而应基于明确证据解释和推理；
3. Playbook Hard Constraint 应优先由规则引擎或确定性逻辑执行；
4. 系统应暴露冲突，而不是把冲突平均成一个黑箱分数；
5. 每次建议都必须生成可审计的 Decision Trace；
6. 用户保留最终判断权。

---

## 7. 七层职责分层

crosslens 在 SPEC-003 中采用七层职责分层。

```text
1. User Interaction Layer
2. Task Understanding & Routing Layer
3. Context & Evidence Layer
4. Orchestration Layer
5. Execution Layer
6. Review & Governance Layer
7. Decision & Trace Layer
```

SPEC-001 只描述产品级架构边界；详细执行架构以 SPEC-003 为准。

### 7.1 User Interaction Layer

负责接收用户输入、展示分析结果、承接用户反馈和复盘入口。

### 7.2 Task Understanding & Routing Layer

负责将用户自然语言请求转为 Investment Task，并选择合适的工作流。

### 7.3 Context & Evidence Layer

负责构建 Context Bundle，并生成 Evidence Packets。

### 7.4 Orchestration Layer

负责驱动全流程，调度全局 Workflow 节点和能力域级 Analysis Domain Job。

### 7.5 Execution Layer

负责运行五个分析能力域，以及能力域内部的模型、工具、工作流和必要的 Agentic Reasoning。

### 7.6 Review & Governance Layer

负责 Validation、Conflict Detection、Playbook Evaluation、Guardrail、Human-in-the-loop 和质量控制。

### 7.7 Decision & Trace Layer

负责生成 Resolved Decision Bounds、Decision Candidate 和 Decision Trace。

---

## 8. 核心流转对象

crosslens 的标准单股票分析对象链如下：

```text
Investment Task
  ↓
Context Bundle
  ↓
Evidence Packets
  ↓
Analysis Domain Jobs
  ↓
Analysis Cards
  ↓
Post-card Validation Report
  ↓
Conflict Reports
  ↓
Pre-decision Validation Report
  ↓
Playbook Evaluation Report
  ↓
Guardrail Report
  ↓
Resolved Decision Bounds
  ↓
Decision Candidate
  ↓
Decision Trace
```

这些对象的完整定义见 SPEC-003。

### 8.1 Investment Task

系统对用户请求的标准化表达。

### 8.2 Context Bundle

执行任务所需的上下文集合，包括行情、财务、公告、新闻、宏观/中观、情绪、技术数据和用户私有上下文。

### 8.3 Evidence Packet

模型、工具、检索或解释过程生成的结构化证据对象。

Evidence Packet 必须区分：

1. Computed Evidence；
2. Structured Evidence；
3. Interpreted Evidence。

### 8.4 Analysis Domain Job

编排器调度能力域的基本单元。

### 8.5 Analysis Card

每个分析能力域向编排器返回的标准化分析结果。

### 8.6 Validation Report

Evaluator 对 Analysis Cards 或 Decision Context 的质量检查结果。

### 8.7 Conflict Report

记录不同能力域之间的冲突，并影响最终建议边界。

### 8.8 Playbook Evaluation Report

系统根据 Investment Playbook 对 Analysis Cards、Evidence Packets 和 Conflict Reports 进行条件检查后的结果。

### 8.9 Guardrail Report

系统边界检查结果，用于防止越界、不可靠或过度自信的建议。

### 8.10 Resolved Decision Bounds

汇总 Validation、Conflict、Playbook 和 Guardrail 后得到的允许动作集合、禁止动作集合和置信度上限。

### 8.11 Decision Candidate

系统在某个 Playbook 和约束边界下生成的投资判断候选，不等于用户最终决策。

### 8.12 Decision Trace

面向用户的投研证据链，用于解释系统如何从任务、证据和约束走到当前判断。

---

## 9. 五个分析能力域

crosslens MVP 保留五个分析能力域：

1. Macro / Meso；
2. Fundamentals；
3. Company Event / Catalyst；
4. Sentiment；
5. Technical / Market。

五个能力域不是五个固定 Agent，而是由数据、模型、工具、Workflow、Agent 和 Evaluator 组合而成的 Analysis Domain Runtime。

能力域内部实现由 SPEC-004 定义。

---

## 10. Investment Playbook

Investment Playbook 是用户或系统定义的投资决策手册，用于表达投资风格、决策偏好、风险约束和判断流程。

Playbook 不等同于 prompt，也不等同于 Skill。

Playbook 可以包含：

1. 投资风格；
2. 资产范围；
3. 时间周期；
4. Hard Constraint；
5. Soft Constraint；
6. 禁止条件；
7. 冲突处理偏好；
8. 人工复核条件；
9. 输出表达要求。

Playbook 的完整结构、版本管理、Constraint 表达、Metric Registry 和执行机制由 SPEC-006 定义。

---

## 11. Decision Trace 与 Observability

系统底层维护统一 Event Log。

Event Log 可以生成两个视图：

### 11.1 Observability

面向开发者、运维人员和系统评估人员。

关注：

1. 模型调用；
2. 工具调用；
3. 执行路径；
4. 延迟；
5. 成本；
6. 错误；
7. 重试；
8. Guardrail 触发；
9. Evaluator 结果；
10. 系统稳定性。

### 11.2 Decision Trace

面向投资用户和投研复盘。

关注：

1. 使用了哪些数据；
2. 哪些证据支持结论；
3. 哪些证据反对结论；
4. 哪些冲突存在；
5. 哪些 Playbook 条件被触发；
6. 哪些 Guardrail 生效；
7. 为什么生成当前 Decision Candidate；
8. 用户下一步应该检查什么。

Observability 和 Decision Trace 共享底层 Event Log，但二者的受众、展示目标、筛选规则和信息粒度不同。

---

## 12. MVP 范围

### 12.1 MVP 应实现

MVP 应实现：

1. 单股票标准分析 Workflow；
2. Investment Task 解析；
3. 默认 Investment Playbook；
4. Context Bundle 构建；
5. Evidence Packet 生成；
6. 五个分析能力域返回 Analysis Card；
7. Post-card Validation；
8. Conflict Detection；
9. Pre-decision Validation；
10. Playbook Evaluation；
11. Guardrail Check；
12. Resolved Decision Bounds；
13. Decision Candidate；
14. Decision Trace Level 1 和 Level 2；
15. 基础 Event Log。

### 12.2 MVP 暂不实现

MVP 暂不实现：

1. 用户自由编辑复杂 Playbook；
2. 多股票批量扫描；
3. 组合优化；
4. 自动交易；
5. 实盘订单接入；
6. Bull / Bear 多 Agent 辩论；
7. Evaluator 自动重写；
8. 完整 Observability Dashboard；
9. 完整 Case Library；
10. Playbook Applicability Evaluator；
11. 复杂宏观预测系统；
12. 完整行业供需模型。

### 12.3 MVP 用户定位

MVP 优先面向：

1. 资本周期投资者；
2. 产业周期投资者；
3. 中长期基本面投资者；
4. 价值与成长结合型投资者；
5. 关注宏观/中观与公司基本面关系的主动投资者。

因此，Macro / Meso 在 MVP 中保留为一级能力域，但不做完整宏观研究系统。

---

## 13. 用户私有数据声明

系统可能使用用户私有数据，包括：

1. 用户持仓；
2. 用户交易记录；
3. 用户历史分析记录；
4. 用户自定义 Playbook；
5. 用户反馈；
6. 用户复盘笔记。

所有用户私有数据必须明确标记为 `user_private`。

用户私有数据不得默认用于公共案例库、公共评估集或其他用户的模型上下文。

用户私有数据的权限、存储、调用和删除机制由 SPEC-012 定义。

---

## 14. 已知局限性

### 14.1 Playbook 适用性局限

系统早期版本只能判断某个资产是否符合指定 Playbook，不能充分判断该 Playbook 本身是否适合当前市场环境。

未来需要 Playbook Applicability Evaluator。

### 14.2 置信度传播局限

MVP 阶段需要最小置信度规则，但完整置信度传播模型由 SPEC-006 或 SPEC-009 定义。

### 14.3 Metric Registry 局限

MVP 阶段需要最小 Metric Registry 支撑 Playbook Hard Constraint 执行，完整设计由 SPEC-005 或 SPEC-006 定义。

### 14.4 投资建议边界

crosslens 输出 Decision Candidate，不输出收益承诺，不替代用户最终决策。

---

## 15. 后续 SPEC

1. SPEC-002：目标用户与核心场景；
2. SPEC-003：Agentic 投研工作流架构；
3. SPEC-004：五类分析能力域与 Analysis Card Schema；
4. SPEC-005：Capability Package 与 Metric Registry 规范；
5. SPEC-006：Investment Playbook 规范；
6. SPEC-007：Orchestration 与执行路径；
7. SPEC-008：Decision Trace 与 Observability；
8. SPEC-009：Governance、Guardrails、Evaluator 与人工介入；
9. SPEC-010：MVP 范围与验证指标；
10. SPEC-011：Case Library 与历史案例记忆；
11. SPEC-012：数据治理与用户私有数据。

---

## 16. SPEC-001 v0.4 总结

SPEC-001 v0.4 将 crosslens 的产品定义与 SPEC-003 v0.3.4 的执行架构对齐。

核心结论：

> crosslens 是一个以 Orchestrator 和状态化 Workflow 为核心的 Agentic 投研决策工作流系统。

它不是多 Agent 群聊系统，也不是黑箱买卖信号生成器。

其核心价值是：

> 让投研判断从“LLM 直接给结论”升级为“任务解析、证据生成、能力域分析、质量检查、冲突暴露、Playbook 约束、护栏检查和决策链展示”的可审计工作流。

crosslens 的架构宪法是：

> **Deterministic first, Agentic when necessary, Traceable always.**
