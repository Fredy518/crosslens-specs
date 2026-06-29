# SPEC-008：Decision Trace 与 Observability

**版本：** v0.2
**状态：** Draft
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4；SPEC-007 v0.6
**文档类型：** Trace 与可观测性规范
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 0. 版本说明

本文件为 SPEC-008 v0.2（Draft），定义 crosslens 的 Decision Trace、Trace Store Runtime v1 和 Observability 规范。

v0.2 在 v0.1 的 Decision Trace 概念模型上，新增 Trace Store Runtime v1 的可执行落地边界：

1. Trace Store v1 四层 artifact 结构；
2. v0 → v1 兼容读取边界；
3. `trace inspect` / `trace replay --mode structural` CLI 契约；
4. weak structural replay / regression 不变量；
5. 与 real-standard baseline、reviewed deep-shadow corpus 的 artifact 接入规则。

v0.1 已建立以下内容：

1. Decision Trace 完整 JSON Schema；
2. Trace 生成流程的完整伪代码；
3. Trace 与 Event Log 的关系模型；
4. Trace 的四层层级结构（Run / Phase / Node / Evidence）；
5. Trace 展示契约（最小可展示格式、分层折叠策略）；
6. Failure Trace 策略；
7. MVP 最小实现范围。

---

## 1. 文档目标

SPEC-008 负责定义：

```text
trace_id → Decision Trace object
```

的生成、结构、读取、展示与展开方式。

本 SPEC 回答以下问题：

1. Decision Trace 的完整结构是什么？
2. Trace 如何从 WorkflowResult 中的 ref-only `decision_trace` 展开？
3. Trace 的四层层级（Run → Phase → Node → Evidence）如何组织？
4. 如何从 Analysis Card 追溯至 Evidence Packet 再至数据源的完整链路？
5. Trace 与 Event Log 的关系是什么？
6. Observability 关键指标如何暴露？
7. Failure Trace 如何生成？
8. 前端 / CLI 应如何消费和展示 Trace？

本 SPEC 不定义：

1. 前端 UI 的具体实现；
2. 特定图表库或可视化组件；
3. 生产环境日志基础设施（ELK / Grafana 等）；
4. 实时监控告警规则。

---

## 2. 架构定位：Trace 与 Event Log 的分工

### 2.1 数据流图

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Runtime                         │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────┐ │
│  │  Node A  │──▶│  Node B  │──▶│  Node C  │──▶│    ...       │ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └──────┬───────┘ │
│       │              │              │                 │          │
│       ▼              ▼              ▼                 ▼          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Event Log (append-only, raw)                 │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │   │
│  │  │ evt_01 │ │ evt_02 │ │ evt_03 │ │ evt_04 │  ...       │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘            │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                       │
│                         │ Trace Building Phase                  │
│                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Decision Trace (structured view)             │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │              Observability View                  │     │   │
│  │  │  (developer / operator / SRE)                    │     │   │
│  │  │  ─ phase durations                              │     │   │
│  │  │  ─ degradation metrics                          │     │   │
│  │  │  ─ human_review triggers                        │     │   │
│  │  │  ─ error rates                                  │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  │                                                           │   │
│  │  ┌─────────────────────────────────────────────────┐     │   │
│  │  │              Decision Trace View                 │     │   │
│  │  │  (investor / auditor / reviewer)                 │     │   │
│  │  │  ─ Run summary                                   │     │   │
│  │  │  ─ Phase-level execution narrative               │     │   │
│  │  │  ─ Node-level input/output refs                  │     │   │
│  │  │  ─ Evidence chain (Packet → Card → Decision)     │     │   │
│  │  │  ─ Reasoning chain (why this conclusion?)        │     │   │
│  │  │  ─ Supporting / opposing evidence                │     │   │
│  │  └─────────────────────────────────────────────────┘     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心区别

| 维度 | Event Log | Decision Trace |
|------|-----------|----------------|
| **写入时机** | 运行时实时写入 | Trace Building 阶段生成 |
| **可变性** | Append-only，不可后处理重写 | 一次生成，不可变 |
| **受众** | 开发者 / 运维 / 审计 | 投资者 / 审计者 / 复盘者 |
| **粒度** | 每条事件独立 | 聚合、排序、压缩、解释 |
| **结构** | 扁平事件序列 | 四层层级结构 |
| **引用关系** | object_refs 列表 | 完整展开的对象摘要 + 引用链 |
| **可读性** | 机器可读优先 | 人类可读优先 |

### 2.3 不变量（来自 SPEC-007 §47.3）

```text
Every degradation must be in Event Log.
Decision Trace must reference or summarize relevant degradation events.
Decision Trace cannot be the only record of runtime state changes.
```

### 2.4 Trace Store Runtime v1 四层 artifact

Trace Store Runtime v1 是 SPEC-008 在本地文件系统中的最小可执行形态。它不要求完整前端 UI，也不要求实时抓取或生产日志平台；它要求一次 workflow run 结束后，能把 Trace 以可审计、可检查、可结构化 replay 的方式持久化。

v1 trace store 的一个 `trace_dir` 必须至少包含以下四层 artifact：

| 层级 | 文件 | 目标 | 最小字段 |
|------|------|------|----------|
| Run Manifest | `manifest.json` | 固定 run/task/playbook/source/release gate 的顶层事实 | `schema_version`、`trace_store_version`、`trace_id`、`run_id`、`task_id`、`trace_status`、`route_status`、`task`、`playbook`、`data_source`、`source_profile`、`release_gate`、`files` |
| Workflow Event Log | `events.jsonl` | 记录域调度、验证、治理、bounds、routing、human-review 触发等可复放事件 | `schema_version`、`trace_id`、`run_id`、`sequence`、`phase`、`status`、`object_refs`、`summary`、`warnings` |
| Object Snapshot Store | `objects.jsonl` | 保存 workflow 对象的结构摘要和 refs，不做真实数值 golden snapshot | `schema_version`、`object_type`、`object_id`、`trace_id`、`run_id`、`refs`、`status`、`snapshot` |
| Source / Artifact Lineage | `lineage.jsonl` | 记录 adapter/source/artifact/redaction 状态，区分 reviewed source、AlphaDB、baseline artifact | `schema_version`、`lineage_type`、`trace_id`、`run_id`、`source_ref`、`source_kind`、`source_profile`、`redaction_status` |

v1 writer 可以继续写 `cards.jsonl` 作为兼容视图，但 replay/inspect 的规范性输入是 `manifest.json`、`events.jsonl`、`objects.jsonl`、`lineage.jsonl`。

### 2.5 v0 兼容读取边界

历史 v0 trace store 只有：

```text
manifest.json
events.jsonl
cards.jsonl
```

v1 runtime 必须能读取 v0 trace store，并把 `cards.jsonl` 作为 `analysis_card` object snapshot 的兼容来源。v0 兼容读取只承诺结构检查和摘要展示，不要求补造 v1 中不存在的 lineage 细节；缺失项必须标记为 `compat_missing` 或 `lineage_gap`，不得静默声明完整。

### 2.6 Trace Store v1 与真实数据 promotion 边界

Trace Store v1 的通过只证明 runtime trace 可审计，不证明真实数据路径可 promotion。特别是：

1. `default_user_path` 保持 `mock`，除非 SPEC-010 promotion gate 明确放行；
2. reviewed deep-shadow trace 即使五域 object chain 完整，也只能标记为 `deep-shadow-validation`；
3. Event/Sentiment reviewed source lineage 可以证明本地结构化来源可追溯，但不等于实时 source feed 或情绪 P1 已上线；
4. real report / trace store 不得把 deterministic baseline 文案混入真实路径正文；
5. trace artifact 不得打印 DB URL、password、token、API key 或本地密钥。

---

## 3. Decision Trace 完整 Schema

### 3.1 顶层结构

```json
{
  "trace_id": "trace_001",
  "run_id": "run_001",
  "task_id": "task_001",
  "trace_status": "complete",
  "created_at": "2026-06-14T10:05:00Z",

  "run_summary": {},
  "phases": [],
  "nodes": [],
  "evidence_links": [],
  "reasoning_chain": [],
  "key_findings": {},
  "failure_info": null,
  "observability": {},

  "event_log_ref": "event_log://run_001",
  "event_log_summary": {}
}
```

### 3.2 `run_summary`

```json
{
  "run_id": "run_001",
  "task_id": "task_001",
  "workflow_id": "single_stock_standard_analysis_workflow",
  "workflow_version": "0.1.0",
  "run_status": "COMPLETED",
  "user_visible_status": "decision_candidate_ready",
  "user_visible_reason": "decision_candidate_ready",
  "task_summary": "分析 AAPL 是否值得在当前价位买入",
  "asset_identifier": "AAPL",
  "task_type": "single_stock_buy_decision",
  "started_at": "2026-06-14T10:00:00Z",
  "completed_at": "2026-06-14T10:04:30Z",
  "total_duration_ms": 270000,
  "degradation_count": 2,
  "human_review_triggered": false,
  "analysis_incomplete": false,
  "need_more_data": false
}
```

### 3.3 `trace_status` 枚举

```text
complete    — 正常路径，全部信息可用
partial     — 部分信息缺失（降级、可选数据缺失、失败 trace 成功）
failure_only — 仅记录 fatal error，无完整 decision 内容
```

### 3.4 `phases` — Phase Level

```json
{
  "phase_id": "phase_evidence",
  "phase_order": 3,
  "phase_type": "evidence",
  "phase_name": "证据收集",
  "phase_status": "completed",
  "started_at": "2026-06-14T10:00:30Z",
  "completed_at": "2026-06-14T10:01:45Z",
  "duration_ms": 75000,
  "degradation_count": 1,
  "human_review_triggered": false,
  "node_count": 3,
  "collapsed_by_default": true,
  "summary": "成功收集基本面、技术面证据。Sentiment 数据部分缺失（降级 1 次）。"
}
```

### 3.5 `phase_type` 枚举（对齐 SPEC-007 phase 枚举）

```text
init
routing
context
evidence
analysis
validation
fusion
decision
trace
terminal
```

### 3.6 `phase_status` 枚举

```text
completed       — 所有节点成功
completed_with_warnings — 有降级但继续
partial         — 部分节点跳过/失败
failed          — 关键节点失败
skipped         — 该 phase 被跳过（如 research path 跳过 analysis）
```

### 3.7 `nodes` — Node Level

```json
{
  "node_id": "node_generate_evidence_packets",
  "node_name": "生成证据包",
  "node_type": "evidence_collect",
  "phase_id": "phase_evidence",
  "phase_type": "evidence",
  "execution_order": 7,
  "status": "completed",
  "started_at": "2026-06-14T10:00:35Z",
  "completed_at": "2026-06-14T10:01:40Z",
  "duration_ms": 65000,
  "input_refs": [
    {
      "ref_type": "context_bundle",
      "ref_id": "ctx_001",
      "summary": "AAPL 上下文包（行情、财务、新闻、宏观）"
    }
  ],
  "output_refs": [
    {
      "ref_type": "evidence_packet",
      "ref_id": "ev_financial_001",
      "summary": "AAPL 财务证据包（包含 12 项财务指标，来源：最新季报）"
    },
    {
      "ref_type": "evidence_packet",
      "ref_id": "ev_technical_001",
      "summary": "AAPL 技术面证据包（MA/MACD/RSI/成交量，日线）"
    },
    {
      "ref_type": "evidence_packet",
      "ref_id": "ev_sentiment_001",
      "summary": "AAPL 情绪证据包（部分缺失，数据质量：low）"
    }
  ],
  "error": null,
  "warnings": [
    "Sentiment 数据源超时，部分指标不可用"
  ],
  "degradation": {
    "degradation_id": "deg_001",
    "reason": "sentiment_data_timeout",
    "origin_domain": "sentiment",
    "origin_requirement": "optional",
    "decision_impact": "dt_note",
    "severity": "warning",
    "recoverable": true
  },
  "event_log_refs": [
    "evt_007",
    "evt_008",
    "evt_009"
  ],
  "collapsed_by_default": true
}
```

### 3.8 `node_status` 枚举（在 Trace 中）

```text
completed       — 成功执行
failed          — 执行失败
skipped         — 跳过
degraded        — 降级后继续
timed_out       — 超时
blocked         — 被前置条件阻止
```

### 3.9 `input_refs` / `output_refs` 元素结构

```json
{
  "ref_type": "context_bundle | evidence_packet | analysis_card | validation_report | conflict_report | playbook_evaluation_report | guardrail_report | resolved_decision_bounds | decision_candidate | investment_task | playbook_snapshot | research_explanation",
  "ref_id": "ctx_001",
  "summary": "人类可读的单行摘要",
  "status": "available | partial | missing | stale"
}
```

### 3.10 `evidence_links` — Evidence Level

```json
{
  "link_id": "el_001",
  "source_type": "evidence_packet",
  "source_ref": "ev_financial_001",
  "source_summary": "AAPL 财务证据包：ROE 35%/PE 28x/FCF Yield 3.5%",
  "target_type": "analysis_card",
  "target_ref": "card_fundamentals_001",
  "target_summary": "AAPL 基本面分析卡：质量评分 8.2/10",
  "relationship": "supports",
  "confidence_contribution": 0.35,
  "evidence_freshness": {
    "as_of": "2026-03-31",
    "freshness_level": "quarterly",
    "staleness_risk": "low"
  }
}
```

### 3.11 `relationship` 枚举

```text
supports        — 证据支持目标判断
opposes         — 证据反对目标判断
constrains      — 约束限制了目标判断的边界
informs         — 证据提供信息但不直接支持或反对
invalidates     — 证据使目标判断失效
```

### 3.12 `reasoning_chain` — 推理链路

```json
{
  "step_number": 3,
  "step_type": "bounds_determination",
  "step_label": "合并约束边界",
  "input_refs": [
    {
      "ref_type": "playbook_evaluation_report",
      "ref_id": "pbe_001",
      "summary": "Playbook 评估：Hard Constraint「PE ≤ 30」触发"
    }
  ],
  "output_refs": [
    {
      "ref_type": "resolved_decision_bounds",
      "ref_id": "rdb_001",
      "summary": "决策边界：allowed_actions=[hold, watch]，PE 超限收窄 buy"
    }
  ],
  "reasoning_text": "PE=28x 触及 Hard Constraint「PE ≤ 30」，但未触发「PE > 30 → exclude buy」。allowed_actions 收窄为 [hold, watch]。buy 因估值约束被排除。",
  "confidence_after_step": 0.72
}
```

### 3.13 `step_type` 枚举

```text
task_parsing            — 任务解析
playbook_loading         — Playbook 加载
evidence_evaluation      — 证据评估
constraint_evaluation    — 约束评估
validation               — 验证
conflict_resolution      — 冲突解决
bounds_determination     — 边界确定
candidate_selection      — 候选选择
guardrail_check          — 护栏检查
```

### 3.14 `key_findings`

```json
{
  "primary_conclusion": "当前建议：Hold。AAPL 基本面优秀但估值偏高，不适合新买入。",
  "suggested_action": "hold",
  "confidence_level": "medium",

  "supporting_reasons": [
    {
      "reason": "ROE 35% 处于行业前 10%",
      "source_refs": ["ev_financial_001", "card_fundamentals_001"],
      "strength": "strong"
    },
    {
      "reason": "FCF Yield 3.5%，现金流健康",
      "source_refs": ["ev_financial_001", "card_fundamentals_001"],
      "strength": "moderate"
    }
  ],

  "opposing_reasons": [
    {
      "reason": "PE=28x 高于历史中位数 22x，估值偏贵",
      "source_refs": ["ev_financial_001", "card_valuation_001"],
      "strength": "strong"
    },
    {
      "reason": "技术面 RSI 超买，短期回调风险",
      "source_refs": ["ev_technical_001", "card_technical_001"],
      "strength": "moderate"
    }
  ],

  "uncertainties": [
    {
      "description": "Sentiment 数据不完整，无法判断市场情绪是否过热",
      "source_refs": ["ev_sentiment_001"],
      "impact": "low"
    },
    {
      "description": "下季度指引尚未发布，业绩不确定性存在",
      "source_refs": [],
      "impact": "medium"
    }
  ],

  "missing_information": [
    {
      "item": "管理层最新指引",
      "importance": "high",
      "suggested_source": "下一季度财报电话会议"
    },
    {
      "item": "完整 Sentiment 指标（数据源超时）",
      "importance": "low",
      "suggested_source": "重试或切换数据源"
    }
  ],

  "next_steps": [
    "等待下一季度财报以评估业绩趋势",
    "关注 PE 是否回归至 25x 以下的历史合理区间",
    "若回撤至技术支撑位，重新评估买入时机",
    "补充 Sentiment 数据后复核情绪维度的判断"
  ],

  "conditions_that_would_invalidate": [
    {
      "condition": "PE 超过 35x（Hard Constraint 上限）",
      "effect": "allowed_actions 收窄为仅 watch"
    },
    {
      "condition": "ROE 降至 20% 以下",
      "effect": "基本面评分降级，confidence_level 降至 low"
    }
  ]
}
```

### 3.15 `failure_info`

```json
{
  "has_failure": true,
  "fatal_error": {
    "error_code": "fundamentals_card_generation_failed",
    "error_message": "基本面分析卡生成失败：数据源不可达",
    "error_location": {
      "phase": "analysis",
      "node_id": "node_fundamentals_domain",
      "node_type": "domain_execution"
    },
    "severity": "critical"
  },
  "error_chain": [
    {
      "event_id": "evt_025",
      "event_type": "DOMAIN_JOB_FAILED",
      "timestamp": "2026-06-14T10:03:00Z",
      "message": "Fundamentals domain job failed: data source unreachable"
    },
    {
      "event_id": "evt_026",
      "event_type": "FATAL_ERROR",
      "timestamp": "2026-06-14T10:03:01Z",
      "message": "Fatal error: fundamentals card is required, cannot proceed"
    }
  ],
  "partial_data_available": [
    "Context Bundle 已构建完成",
    "Evidence Packet 已部分生成（技术面、情绪可用）",
    "其他四个 Domain Card 未生成（因 fundamentals 失败而终止）"
  ],
  "recommended_remediation": "检查基本面数据源连接，确认 API key 有效后重试"
}
```

### 3.16 `observability`

```json
{
  "phase_durations": {
    "init": 500,
    "routing": 1200,
    "context": 3500,
    "evidence": 75000,
    "analysis": 120000,
    "validation": 15000,
    "fusion": 25000,
    "decision": 20000,
    "trace": 5000
  },
  "phase_durations_ms_total": 265200,

  "degradation_summary": {
    "total_count": 2,
    "by_severity": {
      "warning": 2,
      "error": 0,
      "critical": 0
    },
    "by_impact": {
      "dt_note": 2,
      "analysis_incomplete": 0,
      "need_more_data": 0,
      "requires_human_review": 0
    },
    "by_origin_domain": {
      "sentiment": 1,
      "macro_meso": 1
    },
    "degradation_details": [
      {
        "degradation_id": "deg_001",
        "reason": "sentiment_data_timeout",
        "impact": "dt_note",
        "origin_domain": "sentiment",
        "origin_requirement": "optional"
      },
      {
        "degradation_id": "deg_002",
        "reason": "macro_context_stale",
        "impact": "dt_note",
        "origin_domain": "macro_meso",
        "origin_requirement": "optional"
      }
    ]
  },

  "human_review_triggers": [],
  "human_review_trigger_count": 0,

  "constraint_evaluation_summary": {
    "total_constraints_evaluated": 8,
    "hard_constraints_triggered": 1,
    "soft_constraints_triggered": 2,
    "constraint_violations": [
      {
        "constraint_id": "hc_pe_30",
        "constraint_type": "hard",
        "description": "PE ≤ 30",
        "triggered": true,
        "effect": "allowed_actions 收窄，排除 buy"
      }
    ]
  },

  "data_freshness_summary": {
    "data_objects_total": 15,
    "stale_count": 1,
    "missing_count": 1,
    "stale_details": [
      {
        "ref_id": "ev_macro_001",
        "ref_type": "evidence_packet",
        "freshness_level": "daily",
        "as_of": "2026-06-10",
        "staleness_risk": "medium"
      }
    ]
  },

  "confidence_trajectory": [
    {
      "stage": "after_evidence",
      "confidence": 0.85
    },
    {
      "stage": "after_analysis",
      "confidence": 0.78
    },
    {
      "stage": "after_validation",
      "confidence": 0.75
    },
    {
      "stage": "after_bounds",
      "confidence": 0.72
    }
  ]
}
```

### 3.17 `event_log_summary`

```json
{
  "total_events": 42,
  "event_log_ref": "event_log://run_001",
  "event_type_counts": {
    "NODE_STARTED": 15,
    "NODE_SUCCEEDED": 13,
    "NODE_DEGRADED": 2,
    "EVIDENCE_READY": 3,
    "DOMAIN_CARD_READY": 5,
    "CONFLICT_DETECTION_DONE": 1,
    "PLAYBOOK_EVALUATION_DONE": 1,
    "GUARDRAIL_CHECK_DONE": 1,
    "TRACE_READY": 1
  },
  "severity_counts": {
    "info": 35,
    "warning": 4,
    "error": 0,
    "critical": 0
  }
}
```

### 3.18 必填字段规则

| 字段 | 规则 |
|------|------|
| `trace_id` | 必填 |
| `run_id` | 必填 |
| `task_id` | 必填 |
| `trace_status` | 必填 |
| `created_at` | 必填 |
| `run_summary` | 必填 |
| `phases` | 必填 |
| `nodes` | 必填 |
| `evidence_links` | `trace_status != "failure_only"` 时必填 |
| `reasoning_chain` | `trace_status != "failure_only"` 时必填 |
| `key_findings` | `trace_status = "complete"` 时必填 |
| `failure_info` | `trace_status = "failure_only"` 或存在 fatal error 时必填 |
| `observability` | 必填 |
| `event_log_ref` | 必填 |
| `event_log_summary` | 必填 |

---

## 4. Trace 层级结构

### 4.1 四层模型

```text
┌──────────────────────────────────────────────┐
│ Level 1: Run Level                           │
│ ┌──────────────────────────────────────────┐ │
│ │ run_summary: 任务摘要、状态、耗时、降级数  │ │
│ │ key_findings: 主要结论、支持/反对理由      │ │
│ └──────────────────────────────────────────┘ │
│                    ↕ 展开                     │
│ Level 2: Phase Level                         │
│ ┌────────┐ ┌────────┐ ┌────────┐            │
│ │ Phase  │ │ Phase  │ │ Phase  │  ...       │
│ │ init   │ │evidence│ │analysis│            │
│ └───┬────┘ └───┬────┘ └───┬────┘            │
│     ↕          ↕          ↕                   │
│ Level 3: Node Level                          │
│ ┌──────┐ ┌──────┐ ┌──────┐                  │
│ │ Node │ │ Node │ │ Node │  ...             │
│ └──┬───┘ └──┬───┘ └──┬───┘                  │
│    ↕         ↕         ↕                      │
│ Level 4: Evidence Level                      │
│ ┌──────────────┐ ┌──────────────┐           │
│ │ evidence_link│ │ evidence_link│  ...      │
│ │ Packet→Card  │ │ Card→Bounds  │           │
│ └──────────────┘ └──────────────┘           │
└──────────────────────────────────────────────┘
```

### 4.2 各层职责

| 层级 | 职责 | 默认展示状态 |
|------|------|-------------|
| Run Level | 任务全貌、最终结论、整体指标 | 始终展示 |
| Phase Level | 各阶段执行摘要、耗时、降级概览 | 无警告的 Phase 折叠 |
| Node Level | 单个节点的输入/输出 refs、事件引用 | 折叠，按需展开 |
| Evidence Level | 证据→分析卡→决策 的完整溯源链路 | 折叠，按需展开 |

### 4.3 折叠策略（展示契约）

```text
默认展开：
  1. Run Level → 始终展开
  2. Phase Level → 仅展开有警告/降级/失败的 Phase
  3. key_findings → 始终展开

默认折叠（可手动展开）：
  1. Phase Level → 状态为 completed 且无警告的 Phase
  2. Node Level → 所有 Node（仅在 Phase 展开时可见）
  3. Evidence Level → 所有 evidence_link
  4. reasoning_chain → 展开第一步，其余折叠
  5. observability → 折叠为一行总览
  6. event_log_summary → 折叠
```

### 4.4 最小可展示格式

前端或 CLI 必须能渲染以下最小视图：

```text
┌──────────────────────────────────────────────────┐
│ Decision Trace: AAPL 单股票分析                    │
│ Status: decision_candidate_ready                  │
│ Duration: 270s | Degradations: 2 | Confidence: 72%│
│                                                   │
│ ▶ 建议：Hold                                      │
│   • ROE 35% 行业领先 (支持)                       │
│   • PE=28x 高于历史中位数 (反对)                    │
│   • ⚠ Sentiment 数据部分缺失                      │
│   → 下一季度财报前维持持有                         │
│                                                   │
│ ▼ 执行阶段 (7 phases, 点击展开)                    │
│   init ✓ · routing ✓ · context ✓                 │
│   evidence ⚠ (1 degradation)                     │
│   analysis ✓ · validation ✓                      │
│   fusion ✓ · decision ✓ · trace ✓                │
│                                                   │
│ ▼ Observability                                  │
│   Phase durations · Degradation details           │
│                                                   │
│ ▶ 查看完整 Event Log (42 events)                  │
└──────────────────────────────────────────────────┘
```

CLI 渲染规则：

1. 第一行：标题（asset + task type）
2. 第二行：状态 + 耗时 + 降级数 + 置信度
3. `▶` 展开/折叠指示器
4. `✓` 正常完成 / `⚠` 有降级 / `✗` 失败
5. 每行缩进表示层级

---

## 5. Trace 生成流程

### 5.1 `generate_decision_trace()` — 完整伪代码

```python
def generate_decision_trace(
    run: RunState,
    user_visible_status: str,
    user_visible_reason: str | None = None,
    reason: str | None = None,
    task: InvestmentTask | None = None,
    cards: list[AnalysisCard] | None = None,
    bounds: ResolvedDecisionBounds | None = None,
    candidate: DecisionCandidate | None = None,
    explanation: ResearchExplanation | None = None,
    playbook_eval: PlaybookEvaluationReport | None = None,
    validation_reports: list[ValidationReport] | None = None,
    conflict_report: ConflictReport | None = None,
    guardrail_report: GuardrailReport | None = None,
    evidence_gaps: list[EvidenceGap] | None = None,
    error: dict | None = None
) -> DecisionTrace:
    """
    从 RunState 和所有运行时对象生成完整的 Decision Trace。

    SPEC-007 调用方：
      - complete_with_trace()   → 正常 / 降级 / 非 Candidate 完成
      - build_failure_trace()   → FATAL ERROR 后
    """

    # ── Step 1: 收集 Event Log ──
    events = load_event_log(run.event_log_ref)

    # ── Step 2: 构建 run_summary ──
    run_summary = build_run_summary(
        run=run,
        task=task,
        user_visible_status=user_visible_status,
        user_visible_reason=user_visible_reason,
        events=events
    )

    # ── Step 3: 确定 trace_status ──
    trace_status = determine_trace_status(
        run_status=run.run_status,
        user_visible_status=user_visible_status,
        error=error
    )

    # ── Step 4: 构建 Phases ──
    phases = build_phases(
        run=run,
        events=events
    )

    # ── Step 5: 构建 Nodes ──
    nodes = build_nodes(
        run=run,
        events=events,
        phases=phases
    )

    # ── Step 6: 构建 Evidence Links ──
    evidence_links = []
    if trace_status != "failure_only":
        evidence_links = build_evidence_links(
            cards=cards,
            candidate=candidate,
            bounds=bounds,
            playbook_eval=playbook_eval,
            guardrail_report=guardrail_report
        )

    # ── Step 7: 构建 Reasoning Chain ──
    reasoning_chain = []
    if trace_status != "failure_only":
        reasoning_chain = build_reasoning_chain(
            run=run,
            task=task,
            cards=cards,
            bounds=bounds,
            candidate=candidate,
            validation_reports=validation_reports,
            conflict_report=conflict_report,
            playbook_eval=playbook_eval,
            guardrail_report=guardrail_report
        )

    # ── Step 8: 构建 Key Findings ──
    key_findings = {}
    if trace_status == "complete" and candidate:
        key_findings = build_key_findings(
            candidate=candidate,
            cards=cards,
            bounds=bounds,
            conflict_report=conflict_report,
            evidence_gaps=evidence_gaps
        )

    # ── Step 9: 构建 Failure Info ──
    failure_info = None
    if trace_status == "failure_only" or error:
        failure_info = build_failure_info(
            run=run,
            error=error,
            events=events,
            partial_data=collect_partial_data(run)
        )

    # ── Step 10: 构建 Observability ──
    observability = build_observability(
        run=run,
        events=events,
        phases=phases,
        nodes=nodes,
        bounds=bounds,
        cards=cards,
        evidence_gaps=evidence_gaps
    )

    # ── Step 11: 构建 Event Log Summary ──
    event_log_summary = build_event_log_summary(events)

    # ── Step 12: 组装并返回 ──
    trace = DecisionTrace(
        trace_id=generate_trace_id(),
        run_id=run.run_id,
        task_id=run.task_id,
        trace_status=trace_status,
        created_at=now_iso(),
        run_summary=run_summary,
        phases=phases,
        nodes=nodes,
        evidence_links=evidence_links,
        reasoning_chain=reasoning_chain,
        key_findings=key_findings,
        failure_info=failure_info,
        observability=observability,
        event_log_ref=run.event_log_ref,
        event_log_summary=event_log_summary
    )

    persist_trace(trace)
    return trace
```

### 5.2 `expand_trace_node()` — 节点展开

```python
def expand_trace_node(
    trace: DecisionTrace,
    node_id: str
) -> ExpandedNodeView:
    """
    按需展开单个 Node 的完整内容。

    当用户在 UI 中点击折叠的 Node 时需要调用此函数。
    返回该 Node 的完整 input_refs/output_refs 详情、
    关联的 Event Log 条目摘要、以及该 Node 产出的
    所有下游 Evidence Link。
    """

    node = find_node_by_id(trace.nodes, node_id)
    if node is None:
        raise TraceNodeNotFound(f"node_id={node_id} not found in trace {trace.trace_id}")

    # 展开 input_refs → 查询实际对象并返回摘要
    expanded_inputs = []
    for ref in node.input_refs:
        obj_summary = fetch_object_summary(ref.ref_type, ref.ref_id)
        expanded_inputs.append({
            "ref": ref,
            "object_summary": obj_summary,
            "data_source_lineage": trace_data_source(obj_summary)
        })

    # 展开 output_refs
    expanded_outputs = []
    for ref in node.output_refs:
        obj_summary = fetch_object_summary(ref.ref_type, ref.ref_id)
        expanded_outputs.append({
            "ref": ref,
            "object_summary": obj_summary,
            "downstream_consumers": find_downstream_consumers(
                trace=trace,
                ref_id=ref.ref_id
            )
        })

    # 展开关联的 Event Log 条目
    event_details = []
    for event_id in node.event_log_refs:
        event = load_event_by_id(trace.event_log_ref, event_id)
        event_details.append({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "event_time": event.event_time,
            "severity": event.severity,
            "message": event.message,
            "run_status_before": event.run_status_before,
            "run_status_after": event.run_status_after
        })

    # 查找该 Node 参与的证据链路
    node_evidence_links = [
        link for link in trace.evidence_links
        if link.source_ref == node_id
        or link.target_ref == node_id
        or any(
            ref.ref_id in [link.source_ref, link.target_ref]
            for ref in node.output_refs
        )
    ]

    return ExpandedNodeView(
        node=node,
        expanded_inputs=expanded_inputs,
        expanded_outputs=expanded_outputs,
        event_details=event_details,
        evidence_links=node_evidence_links,
        degradation_detail=expand_degradation_detail(node.degradation) if node.degradation else None
    )
```

### 5.3 `trace_data_source()` — 数据源溯源

```python
def trace_data_source(obj_summary: dict) -> DataSourceLineage:
    """
    追溯一个对象到其原始数据源的完整链路。

    链式追溯：
      Analysis Card → Evidence Packet → Data Collection → Raw Data Source

    返回一个层级化溯源：
      ┌─ card_fundamentals_001 (Analysis Card)
      │  └─ ev_financial_001 (Evidence Packet)
      │     ├─ 财务数据源: Yahoo Finance API
      │     │  └─ 原始调用: GET /v11/finance/quoteSummary/AAPL
      │     │     as_of: 2026-03-31
      │     ├─ 财务数据源: SEC EDGAR
      │     │  └─ Filing: 10-Q 2026Q1
      │     │     as_of: 2026-03-31
      │     └─ 计算指标: ROE, PE, FCF Yield (确定性计算)
    """

    lineage = DataSourceLineage(object_ref=obj_summary["ref_id"])

    if obj_summary.get("ref_type") == "analysis_card":
        card_id = obj_summary["ref_id"]
        card = load_analysis_card(card_id)
        for evidence_ref in card.evidence_refs:
            packet_node = trace_data_source_for_packet(evidence_ref)
            lineage.add_child(packet_node)

    elif obj_summary.get("ref_type") == "evidence_packet":
        packet_node = trace_data_source_for_packet(obj_summary["ref_id"])
        lineage = packet_node

    return lineage


def trace_data_source_for_packet(packet_id: str) -> DataSourceNode:
    packet = load_evidence_packet(packet_id)
    node = DataSourceNode(
        object_ref=packet_id,
        object_type="evidence_packet",
        computation_method=packet.computation_method,
        freshness=packet.freshness
    )

    for source in packet.data_sources:
        source_node = DataSourceNode(
            object_ref=source.source_id,
            object_type="data_source",
            source_name=source.source_name,
            source_type=source.source_type,
            raw_query=source.raw_query,
            as_of=source.as_of,
            collected_at=source.collected_at
        )
        node.add_child(source_node)

    return node
```

### 5.4 `build_evidence_links()` — 证据链路构建

```python
def build_evidence_links(
    cards: list[AnalysisCard] | None,
    candidate: DecisionCandidate | None,
    bounds: ResolvedDecisionBounds | None,
    playbook_eval: PlaybookEvaluationReport | None,
    guardrail_report: GuardrailReport | None
) -> list[EvidenceLink]:
    """
    构建跨对象的 evidence_links 网络。

    链路方向：
      evidence_packet → analysis_card
      analysis_card   → validation_report
      analysis_card   → conflict_report (opposing cards)
      analysis_card   → playbook_evaluation_report (constraint input)
      playbook_eval   → resolved_decision_bounds
      guardrail       → resolved_decision_bounds
      bounds          → decision_candidate
    """

    links = []

    if not cards:
        return links

    # 1. Evidence → Card
    for card in cards:
        for evidence_ref in card.evidence_refs:
            links.append(EvidenceLink(
                source_type="evidence_packet",
                source_ref=evidence_ref,
                target_type="analysis_card",
                target_ref=card.card_id,
                relationship="supports",
                confidence_contribution=estimate_confidence_contribution(card, evidence_ref)
            ))

    # 2. Card → Validation
    for card in cards:
        if card.validation_result:
            rel = "opposes" if card.validation_result.get("failed") else "supports"
            links.append(EvidenceLink(
                source_type="analysis_card",
                source_ref=card.card_id,
                target_type="validation_report",
                target_ref=card.validation_result.get("validation_report_id"),
                relationship=rel
            ))

    # 3. Card → Conflict (card vs card)
    if cards and len(cards) > 1:
        for conflict in find_inter_card_conflicts(cards):
            links.append(EvidenceLink(
                source_type="analysis_card",
                source_ref=conflict.card_a,
                target_type="analysis_card",
                target_ref=conflict.card_b,
                relationship="opposes",
                confidence_contribution=-abs(conflict.severity_score)
            ))

    # 4. Playbook / Guardrail → Bounds
    if bounds and playbook_eval:
        links.append(EvidenceLink(
            source_type="playbook_evaluation_report",
            source_ref=playbook_eval.playbook_evaluation_report_id,
            target_type="resolved_decision_bounds",
            target_ref=bounds.resolved_decision_bounds_id,
            relationship="constrains"
        ))

    if bounds and guardrail_report:
        links.append(EvidenceLink(
            source_type="guardrail_report",
            source_ref=guardrail_report.guardrail_report_id,
            target_type="resolved_decision_bounds",
            target_ref=bounds.resolved_decision_bounds_id,
            relationship="constrains"
        ))

    # 5. Bounds → Candidate
    if bounds and candidate:
        links.append(EvidenceLink(
            source_type="resolved_decision_bounds",
            source_ref=bounds.resolved_decision_bounds_id,
            target_type="decision_candidate",
            target_ref=candidate.decision_candidate_id,
            relationship="constrains"
        ))

    return links
```

### 5.5 `build_phases()` — Phase 构建

```python
def build_phases(run: RunState, events: list[Event]) -> list[TracePhase]:
    """
    从 Event Log 推断 Phase 边界。

    依据 SPEC-007 §30 的 phase 枚举：
      init → routing → context → evidence → analysis
      → validation → fusion → decision → trace → terminal

    Phase 边界通过 Event Log 中的 run_status 迁移推断。
    """

    # Phase 定义：每个 phase 有对应的开始/结束 run_status
    PHASE_DEFINITIONS = [
        ("init",   "CREATED",           "TASK_PARSED"),
        ("routing", "TASK_PARSED",       "ROUTED"),
        ("context", "ROUTED",            "CONTEXT_BUILT"),
        ("evidence","CONTEXT_BUILT",     "EVIDENCE_READY"),
        ("analysis","EVIDENCE_READY",    "CARDS_READY"),
        ("validation","CARDS_READY",     "VALIDATION_BLOCKED",
         "POST_CARD_VALIDATING",         "CONFLICT_DETECTING"),
        ("fusion",   "CONFLICT_DETECTING","BOUNDS_RESOLVING"),
        ("decision", "BOUNDS_RESOLVING",  "CANDIDATE_GENERATING",
         "COMPLETED"),
        ("trace",    "TRACE_BUILDING",    "COMPLETED"),
    ]

    phases = []
    phase_order = 0

    for phase_def in PHASE_DEFINITIONS:
        phase_type = phase_def[0]
        start_statuses = phase_def[1:-1]  # 所有中间的 run_status
        end_status = phase_def[-1]

        # 从 Event Log 查找该 Phase 的时间边界
        start_event = find_first_status_event(events, start_statuses)
        end_event = find_first_status_event(events, [end_status])

        if start_event is None:
            # 该 Phase 被跳过
            phases.append(TracePhase(
                phase_id=f"phase_{phase_type}",
                phase_order=phase_order,
                phase_type=phase_type,
                phase_status="skipped",
                collapse_by_default=True
            ))
            phase_order += 1
            continue

        phase_nodes = find_nodes_in_phase(events, start_event, end_event)
        phase_degradations = count_phase_degradations(phase_nodes)

        phases.append(TracePhase(
            phase_id=f"phase_{phase_type}",
            phase_order=phase_order,
            phase_type=phase_type,
            phase_name=PHASE_NAME_MAP[phase_type],
            phase_status=determine_phase_status(phase_nodes),
            started_at=start_event.event_time if start_event else None,
            completed_at=end_event.event_time if end_event else None,
            duration_ms=calc_duration(start_event, end_event),
            degradation_count=phase_degradations,
            human_review_triggered=any(
                n.get("human_review_triggered") for n in phase_nodes
            ),
            node_count=len(phase_nodes),
            collapsed_by_default=(
                phase_degradations == 0
                and not any(n.get("status") == "failed" for n in phase_nodes)
            ),
            summary=build_phase_summary(phase_type, phase_nodes)
        ))
        phase_order += 1

    return phases
```

### 5.6 `build_observability()` — Observability 指标构建

```python
def build_observability(
    run: RunState,
    events: list[Event],
    phases: list[TracePhase],
    nodes: list[TraceNode],
    bounds: ResolvedDecisionBounds | None,
    cards: list[AnalysisCard] | None,
    evidence_gaps: list | None
) -> Observability:

    # Phase durations
    phase_durations = {
        p.phase_type: p.duration_ms
        for p in phases
        if p.duration_ms is not None
    }

    # Degradation summary
    all_degradations = [
        n.degradation for n in nodes
        if n.degradation is not None
    ]

    degradation_summary = {
        "total_count": len(all_degradations),
        "by_severity": count_by(all_degradations, "severity"),
        "by_impact": count_by(all_degradations, "decision_impact"),
        "by_origin_domain": count_by(all_degradations, "origin_domain"),
        "degradation_details": [
            {
                "degradation_id": d.degradation_id,
                "reason": d.reason,
                "impact": d.decision_impact,
                "origin_domain": d.origin_domain,
                "origin_requirement": d.origin_requirement
            }
            for d in all_degradations
        ]
    }

    # Human review triggers
    human_review_events = [
        e for e in events
        if e.event_type in (
            "PLAYBOOK_REQUIRES_HUMAN_REVIEW",
        )
        or (
            e.event_type == "STATUS_CHANGED"
            and e.run_status_after == "HUMAN_REVIEW_REQUIRED"
        )
    ]

    # Constraint evaluation
    constraint_violations = []
    if bounds:
        for rule in bounds.applied_rules:
            if rule.get("effect") != "none":
                constraint_violations.append({
                    "constraint_id": rule.get("constraint_id"),
                    "constraint_type": rule.get("constraint_type"),
                    "description": rule.get("description"),
                    "triggered": True,
                    "effect": rule.get("effect")
                })

    # Confidence trajectory
    confidence_trajectory = build_confidence_trajectory(events, cards, bounds)

    # Data freshness
    data_freshness = build_data_freshness_summary(cards, evidence_gaps)

    return Observability(
        phase_durations=phase_durations,
        phase_durations_ms_total=sum(phase_durations.values()),
        degradation_summary=degradation_summary,
        human_review_triggers=human_review_events,
        human_review_trigger_count=len(human_review_events),
        constraint_evaluation_summary={
            "total_constraints_evaluated": len(bounds.applied_rules) if bounds else 0,
            "hard_constraints_triggered": count_triggered(bounds, "hard") if bounds else 0,
            "soft_constraints_triggered": count_triggered(bounds, "soft") if bounds else 0,
            "constraint_violations": constraint_violations
        },
        data_freshness_summary=data_freshness,
        confidence_trajectory=confidence_trajectory
    )
```

---

## 6. Failure Trace 策略

### 6.1 概述

Failure Trace 是系统在发生 fatal error 后生成的、尽力而为的 Decision Trace。

规则（来自 SPEC-007 §52）：

```text
FAILED 状态已成立；
failure trace 构建成功则附加 decision_trace；
failure trace 构建失败则 decision_trace = null；
不再改变 run_status。
```

### 6.2 `build_failure_trace()` 流程

（此函数定义在 SPEC-007 §52.2，SPEC-008 仅描述其内部 Trace 构建行为。）

```python
def build_failure_trace(run, err):
    """
    SPEC-007 §52.2 定义外层函数。
    SPEC-008 定义其内部 generate_decision_trace 调用行为。
    """

    # Step 1: 记录 FATAL_ERROR（SPEC-007）
    log_event(run, "FATAL_ERROR", severity="critical", error=serialize_error(err))

    # Step 2: 迁移到 FAILED（SPEC-007）
    if run.run_status != "FAILED":
        set_status(run, "FAILED")

    # Step 3: 尝试生成 Decision Trace
    try:
        trace = generate_decision_trace(
            run=run,
            user_visible_status="failed",
            user_visible_reason="fatal_error",
            reason="fatal_error",
            error=err,
            # 以下参数传 None —— 失败时可能没有完整数据
            task=run.runtime_context.get("task"),
            cards=run.runtime_context.get("cards"),
            bounds=None,
            candidate=None,
            explanation=None,
            playbook_eval=None,
            validation_reports=run.runtime_context.get("validation_reports"),
            conflict_report=None,
            guardrail_report=None,
            evidence_gaps=run.runtime_context.get("evidence_gaps")
        )

        # 成功 → trace_status 自动为 "failure_only" 或 "partial"
        run.object_refs["decision_trace"] = trace.trace_id
        log_event(run, "TRACE_READY", object_refs=[trace.trace_id])
        return trace

    except Exception as trace_err:
        # 失败 → decision_trace = null
        log_event(run, "TRACE_BUILD_FAILED",
                  severity="critical", error=serialize_error(trace_err))
        return None
```

### 6.3 Failure Trace 内容策略

| 数据类别 | Failure Trace 行为 |
|----------|-------------------|
| `run_summary` | 始终包含（基本信息不依赖运行时对象） |
| `phases` | 包含到失败点为止的所有已完成 Phase |
| `nodes` | 包含到失败点为止的所有已完成 Node |
| `evidence_links` | 仅包含失败前已完成的链路 |
| `reasoning_chain` | 可能为空或仅包含失败前的步骤 |
| `key_findings` | 空（failure 状态下无结论） |
| `failure_info` | 必填且完整 |
| `observability` | 包含失败前的指标 |
| `event_log_summary` | 始终包含 |

### 6.4 Failure Trace 的 `trace_status` 判定

```python
def determine_trace_status(
    run_status: str,
    user_visible_status: str,
    error: dict | None
) -> str:

    if run_status == "FAILED":
        return "failure_only"

    if run_status == "COMPLETED":
        if user_visible_status in (
            "analysis_incomplete",
            "need_more_data",
            "requires_human_review"
        ):
            return "partial"
        return "complete"

    # 不应到达
    return "failure_only"
```

### 6.5 Failure Trace 的前端展示契约

Failure Trace 在前端必须：

1. 明确标注「该 Trace 对应一次失败运行」
2. 展示失败原因和错误链
3. 展示失败前已完成的数据（Phases/Nodes）
4. 提供`recommended_remediation`作为用户下一步行动建议
5. 不展示 `key_findings`（因为无结论）

---

## 7. Trace 展示契约

### 7.1 核心原则

1. **渐进展开**：默认折叠不重要信息，用户点击展开
2. **状态可读**：使用符号（✓/⚠/✗）直观表示节点/Phase 状态
3. **溯源可点击**：每个 ref 可点击跳转到对应对象的详细视图
4. **证据方向明确**：用 `→ supports` / `→ opposes` / `→ constrains` 标注方向
5. **置信度可视化**：用数值 + 趋势箭头展示置信度变化

### 7.2 前端消费契约

```typescript
// Trace 的最小消费接口
interface TraceConsumer {
  // 1. 获取 Trace 顶层层级（Run + Phases）
  getTraceOverview(traceId: string): TraceOverview;

  // 2. 按需展开 Phase
  expandPhase(traceId: string, phaseId: string): ExpandedPhase;

  // 3. 按需展开 Node
  expandNode(traceId: string, nodeId: string): ExpandedNodeView;

  // 4. 获取证据链路
  getEvidenceLinks(traceId: string, filters?: EvidenceLinkFilter): EvidenceLink[];

  // 5. 获取推理链路
  getReasoningChain(traceId: string): ReasoningStep[];

  // 6. 数据源溯源
  traceDataSource(objectRef: string): DataSourceLineage;

  // 7. 获取 Observability 指标
  getObservability(traceId: string): Observability;
}
```

### 7.3 CLI 消费契约

CLI v1 必须支持目录级 inspect/replay；trace-id 级 show/evidence/lineage/export 可作为后续 UI 或 trace registry 的扩展。

```bash
# 检查本地 trace store 目录
crosslens trace inspect --trace-dir path/to/trace_dir

# 输出 JSON，供 regression gate 消费
crosslens trace inspect --trace-dir path/to/trace_dir --format json

# 只做结构 replay，不重跑数据源、不重算数值
crosslens trace replay --trace-dir path/to/trace_dir --mode structural

# strict 模式：任一 replay check fail 时退出非零
crosslens trace replay --trace-dir path/to/trace_dir --mode structural --strict
```

`trace inspect` 最少输出：

1. schema version / trace store version；
2. run_id、task_id、data_source、playbook、route_status；
3. domain status 分布；
4. warning / limitation 摘要；
5. source lineage 与 redaction 状态；
6. v0 compatibility gap（如有）。

`trace replay --mode structural` 最少验证：

1. required files 存在，或 v0 兼容读取路径可用；
2. event sequence 单调递增；
3. domain execution、conflict、playbook、governance、bounds、routing phases 至少可追溯；
4. 三域 `standard` 或五域 `deep` object refs 与 card snapshots 一致；
5. route_status、trace_status、human_review_triggers 可由 object/event 摘要解释；
6. source lineage 中 redaction_status 不为 `failed`；
7. artifact 明确 `not_numeric_snapshot=true` 或等价策略；
8. 无 secret pattern 命中。

trace replay 是 structural replay：它只复核对象链和路由不变量，不访问 AlphaDB/tinydata，不重跑域计算，不比较真实行情/财务数值。

### 7.4 Trace 存储与读取

```text
Trace 是一次生成、不可变的 artifact。

存储位置：
  DecisionTrace 对象和 object snapshots 持久化到 trace store
  trace_id 在 WorkflowResult.decision_trace 中引用

读取路径：
  WorkflowResult → trace_id / trace_dir → load_trace_store(trace_dir) → TraceStoreBundle

不可变性：
  Trace 生成后不允许修改
  若需要补充注释或用户标记，通过独立的 Annotation 机制实现
```

---

## 8. Trace 与 Event Log 的关系（总结）

### 8.1 数据流

```text
Runtime Execution
       │
       ├──▶ Event Log (实时写入，每条事件独立)
       │      │
       │      ├── STATUS_CHANGED 事件 → Run State Machine 迁移记录
       │      ├── NODE_STARTED/SUCCEEDED/FAILED → 节点生命周期
       │      ├── DOMAIN_* 事件 → 能力域执行轨迹
       │      ├── EVIDENCE_* 事件 → 证据收集状态
       │      └── TRACE_* 事件 → Trace 自身构建状态
       │
       └──▶ Run State (运行时对象容器)
              │
              └──▶ Decision Trace (Trace Building Phase 生成)
                     │
                     ├── 读取 Event Log 构建 Phases / Nodes
                     ├── 读取 Run State 的对象引用构建 Evidence Links
                     ├── 读取分析结果构建 Reasoning Chain
                     └── 汇总 Observability 指标
```

### 8.2 引用关系

```text
Decision Trace 中的每个 Node：
  └─ event_log_refs: [evt_007, evt_008, evt_009]
       │
       └─ 指向 Event Log 中该 Node 的生命周期事件

Decision Trace 中的每个 Phase：
  └─ 通过 Event Log 中的 STATUS_CHANGED 事件推断边界

Observability 指标：
  └─ 从 Event Log 聚合计算，不额外存储
```

### 8.3 审计完整性

```text
给定一个 Decision Trace，审计者必须能够：
  1. 通过 trace_id 找到 Event Log → 验证 Trace 内容
  2. 通过 event_log_refs → 追溯到原始运行时事件
  3. 通过 object refs → 读取原始对象（Analysis Card / Evidence Packet 等）
  4. 通过 data_source_lineage → 追溯到原始数据源和 API 调用

任何 Trace 中的声明必须有 Event Log + 原始对象作为依据。
```

---

## 9. MVP 最小实现范围

### 9.1 必须实现

| 项目 | 说明 |
|------|------|
| Trace Store v1 writer | 写入 `manifest.json`、`events.jsonl`、`objects.jsonl`、`lineage.jsonl`，可保留 `cards.jsonl` 兼容视图 |
| v0 compatible reader | 能读取 v0 `manifest/events/cards`，并显式标记兼容缺口 |
| `trace inspect` | 对 trace_dir 输出 summary、domain status、warnings、lineage、redaction 检查 |
| `trace replay --mode structural` | 不访问数据源、不重算数值，只验证 object chain、route、lineage、redaction、snapshot policy |
| weak trace regression | 可用于 real-standard baseline 和 reviewed deep-shadow corpus 的结构回归 |
| Run Manifest 层 | 固定 task/playbook/data_source/as_of/repo/release gate |
| Workflow Event Log 层 | 固定 phase/event sequence 与 human-review triggers |
| Object Snapshot Store 层 | 保存 cards、constraint exports、bounds、candidate、conflict/governance/playbook 摘要 |
| Source / Artifact Lineage 层 | 保存 adapter/source/artifact refs、reviewed source 标记、redaction status |
| Secret redaction | trace artifact 不得泄漏 URL password、token、API key、本地密钥 |

### 9.2 MVP 暂不实现

| 项目 | 说明 |
|------|------|
| 完整 Observability Dashboard | 仅提供 JSON 指标，不做 Grafana 等可视化 |
| 多 Trace 对比 | 不实现跨 Run 的 Trace 对比视图 |
| 实时 Trace 更新 | Trace 仅在 Run 完成后一次性生成 |
| Annotation 机制 | 用户标注/注释暂不实现 |
| Trace 导出格式（PDF/HTML） | 仅支持 JSON 和 CLI 文本视图 |
| 多层级数据源溯源 | 仅追溯一级（Evidence → Data Source），不做递归多级溯源 |
| Evidence Link 权重可视化 | 仅输出 `relationship` + `confidence_contribution` 数值，不做图表 |
| 数值 replay | 不重跑市场/财务/宏观计算，不做 exact numeric snapshot |
| 实时 Event source / Sentiment P1 | reviewed source ingestion 之外的实时抓取和情绪模型不属于 SPEC-008 v1 runtime |

### 9.3 MVP Trace 输出路径

```text
正常路径 (COMPLETED):
  WorkflowResult.decision_trace.trace_id → DecisionTrace(trace_status="complete")
  包含：完整 Phases、Nodes、Evidence Links、Reasoning Chain、Key Findings

降级路径 (COMPLETED with analysis_incomplete / need_more_data / requires_human_review):
  WorkflowResult.decision_trace.trace_id → DecisionTrace(trace_status="partial")
  包含：Phases、Nodes（到降级点）、部分 Evidence Links、Observability
  不包含：Key Findings（无完整结论）

失败路径 (FAILED):
  WorkflowResult.decision_trace.trace_id → DecisionTrace(trace_status="failure_only")
  或 WorkflowResult.decision_trace = null
  包含：Failure Info、部分 Phases/Nodes、Observability（失败前指标）
  不包含：Key Findings、Evidence Links（失败点之后的内容）

研究路径 (COMPLETED with research_explanation_ready):
  WorkflowResult.decision_trace.trace_id → DecisionTrace(trace_status="complete")
  包含：Phases（不含 analysis/fusion）、Nodes、Explanation 链路
  不包含：Evidence Links to Cards、Reasoning Chain to Bounds
```

---

## 10. 核心不变量

```text
1. 每个 Run 有且仅有一个 Decision Trace。
2. Decision Trace 在 Trace Building Phase 一次性生成，不可变。
3. Decision Trace 必须引用 Event Log，但不能替代 Event Log。
4. 每个 Evidence Link 的方向必须明确（supports / opposes / constrains / informs / invalidates）。
5. key_findings 中的每条 supporting_reason / opposing_reason 必须引用至少一个 source_ref。
6. Failure Trace 中的 failure_info 必须包含 error_chain。
7. Observability 中的 degradation_summary 必须与 Event Log 中的降级事件一致。
8. Trace 生成失败不应阻止 WorkflowResult 返回其他字段。
9. Trace 中的 phase / node 时间边界必须与 Event Log 中的 STATUS_CHANGED 事件一致。
10. evidence_links 中的 confidence_contribution 是估算值，必须在 Trace 中标注「估值，非精确计算」。
11. v1 trace store 必须包含 Run Manifest、Workflow Event Log、Object Snapshot Store、Source / Artifact Lineage 四层 artifact。
12. v1 structural replay 不得访问外部数据源，不得重算真实行情、财务、宏观或情绪数值。
13. v0 compatible reader 不得把缺失 lineage 伪装为完整 lineage。
14. real-standard 和 reviewed deep-shadow trace artifact 必须继续声明非数值 snapshot policy。
15. deep-shadow trace artifact 不得被解释为 MVP-1 ready；promotion 由 SPEC-010 gate 决定。
16. trace artifact 中的 secret redaction 必须先于写盘或 inspect 输出。
```

---

## 11. 与上下游 SPEC 的接口

### 11.1 上游依赖（SPEC-007）

| 接口 | 说明 |
|------|------|
| `WorkflowResult.decision_trace` | ref-only `{trace_id}`，SPEC-008 负责展开 |
| `complete_with_trace()` | 调用 `generate_decision_trace()` 的入口 |
| `build_failure_trace()` | 调用 `generate_decision_trace()` 的失败路径入口 |
| Event Log Schema | SPEC-008 消费 Event Log 构建 Phase/Node 边界 |
| RunState.object_refs | SPEC-008 从中获取运行时对象引用 |
| Degradation Schema | SPEC-008 在 observability 中汇总降级信息 |

### 11.2 下游消费

| 消费者 | 消费内容 |
|--------|---------|
| 前端 UI | 完整 Decision Trace（渐进展开） |
| CLI | 完整 Decision Trace（文本视图） |
| 审计系统 | Trace + Event Log 的交叉验证 |
| Case Library (SPEC-011) | Trace 中的 key_findings 作为案例摘要 |

### 11.3 未来扩展点

1. **Multi-Trace 对比**：多个 Run 的 Trace 对比视图（比较不同时间点的分析）
2. **Annotation Layer**：用户在 Trace 上添加注释和标记
3. **Trace Diff**：两次 Run 之间的 Trace 差异对比
4. **Streaming Trace**：运行时逐步构建 Trace（而非一次性生成）
5. **Confidence Trajectory 可视化**：置信度变化曲线图
6. **多级数据源溯源**：递归追溯多级数据血缘

---

## 12. 后续 SPEC 依赖

SPEC-008 依赖和影响以下文档：

1. SPEC-010：MVP 范围与验证指标（Decision Trace 在 MVP 中的实现深度）；
2. SPEC-011：Case Library 与历史案例记忆（Trace 中的 key_findings 作为案例摘要输入）；
3. SPEC-012：数据治理与用户私有数据（Trace 中 user_private 数据的展示脱敏）。

---

## 13. 开放问题

1. Trace 持久化存储应使用文件系统还是轻量数据库（SQLite）？
2. 前端 UI 应在何时加载完整 Trace vs 仅加载 Run Level？
3. `confidence_contribution` 的计算公式应由 SPEC-004 还是 SPEC-008 定义？
4. 多 Playbook 对比时（未来），`reasoning_chain` 应如何组织多条并行推理路径？
5. Evidence Link 的去重规则：同一对 source/target 可能有多条 link？
6. Trace 体积上限：大规模 Run（数百 Nodes）时 Trace JSON 可能过大，是否需要分页加载？

---

## 13. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v0.2 | 2026-06-29 | 新增 Trace Store Runtime v1 四层 artifact、v0 兼容读取、inspect/replay CLI、weak structural replay 与 real-standard/deep-shadow 接入边界 |
| v0.1 | 2026-06-14 | 初稿：完整 Schema、生成伪代码、展示契约、MVP 范围 |
