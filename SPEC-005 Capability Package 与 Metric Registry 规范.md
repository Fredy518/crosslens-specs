# SPEC-005：Capability Package 与 Metric Registry 规范

**版本：** v0.2
**状态：** Review
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4；SPEC-004 v0.2.5
**文档类型：** 能力包规范
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 0. 版本说明

v0.2 在 v0.1 基础上关闭了三个阻塞 MVP 的规格缺口。状态从 Draft 升级为 Review。主要补齐：

1. **新增 §4.4 Evidence Packet `confidence` 取值规则**：关闭 SPEC-003 §6.5 NOTE。按 `generation_type` 区分 Computed（默认 1.0）、Structured（模型自评分）、Interpreted（LLM 输出）三类 confidence 赋值规则，包括降级条件与 MVP 实现指引；
2. **新增 §15.1 `metric://` / `fact://` / `label://` URI 格式规范**：关闭了 #4 open issue。MVP 使用无版本号 URI，版本锁定由 Metric Registry snapshot + Playbook `dependency_snapshot_refs` 承担；
3. **新增 §15.2 Derived Metric 映射规则表格式**：关闭了 #5 open issue。定义声明式 JSON 规则表格式，支持 `operator`、首匹配短路、强制 test_cases 和 `confidence_rule = "inherit_min"`。

v0.1 为 SPEC-005 的首个正式 Draft 版本。

本版本建立以下核心定义：

1. Capability Package 作为工具/模型/数据连接器的打包与版本管理单元；
2. Metric Registry 作为 Playbook Constraint 指标寻址的注册与解析层；
3. 工具调用链 lineage 追踪机制；
4. Metric → constraint_exports 的映射与校验规则；
5. MVP 最小实现范围。

本文件是 SPEC-004（能力域）与 SPEC-006（Playbook）之间的桥梁。

---

## 1. 文档目标

SPEC-005 回答以下核心问题：

1. 能力域需要工具、模型、数据连接器——这些如何被打包、版本化、声明依赖？
2. Playbook Constraint 引用的 `metric://` / `fact://` / `label://` 如何被解析到具体的 Evidence Packet 和 `constraint_exports`？
3. 一个指标的计算链路（数据源 → 原始数据 → 计算 → 导出）如何被追踪？
4. `confidence` 的 `determination_type` 如何确保可追溯？
5. Capability Package 的调用如何进入 Decision Trace？

---

## 2. 架构概览：Capability Package 在系统中的位置

### 2.1 决策树：Metric 从数据源到 Constraint 的路由

```
┌──────────────────────────────────────────────────────────────────────┐
│                     Capability Package 路由流程                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  数据源（Data Source）                                                │
│    │                                                                 │
│    ▼                                                                 │
│  ┌──────────────────────┐                                            │
│  │ Data Connector       │  ← Capability Package 声明依赖             │
│  │ (API/DB/File/Stream) │                                            │
│  └────────┬─────────────┘                                            │
│           │ raw_data                                                 │
│           ▼                                                          │
│  ┌──────────────────────┐                                            │
│  │ Tool / Model         │  ← 执行计算/分类/解释                      │
│  │ (computed/struct/    │                                            │
│  │  interpreted)        │                                            │
│  └────────┬─────────────┘                                            │
│           │ output (Evidence Packet)                                 │
│           ▼                                                          │
│  ┌──────────────────────┐                                            │
│  │ Metric Registry      │  ← 索引 metric_id → evidence_id +          │
│  │ (注册与查找)          │     value_path + freshness 规则            │
│  └────────┬─────────────┘                                            │
│           │ metric resolution                                        │
│           ▼                                                          │
│  ┌──────────────────────┐                                            │
│  │ Analysis Card        │  ← 能力域消费 Evidence Packet、             │
│  │ constraint_exports   │     通过 constraint_exports 导出            │
│  └────────┬─────────────┘                                            │
│           │ export_ref (metric:// / fact:// / label://)              │
│           ▼                                                          │
│  ┌──────────────────────┐                                            │
│  │ Playbook Constraint  │  ← input_refs 引用 export，                │
│  │ (Hard / Soft)        │     规则引擎解析并执行判断                  │
│  └──────────────────────┘                                            │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 路由决策伪代码：input_ref 解析全路径

```
function resolve_input_ref(input_ref: string, cards: AnalysisCard[], metric_registry: MetricRegistry) -> ResolvedRef:
    """
    解析 Playbook Constraint 的 input_ref，返回可用于规则引擎的值与元数据。
    支持三种引用格式：metric:// / fact:// / label://
    """
    
    // Step 1: 解析引用类型
    if input_ref starts with "metric://":
        ref_type = "metric"
        metric_id = input_ref.slice("metric://".len)
    else if input_ref starts with "fact://":
        ref_type = "fact"
        fact_id = input_ref.slice("fact://".len)
    else if input_ref starts with "label://":
        ref_type = "label"
        label_id = input_ref.slice("label://".len)
    else:
        return error("UNSUPPORTED_REF_FORMAT", input_ref)
    
    // Step 2: 在 Analysis Cards 的 constraint_exports 中查找
    matched_export = null
    for card in cards:
        if card.domain_status not in {"completed", "partial"}:
            continue  // 跳过不可用的 Card
        for export in card.constraint_exports:
            if export.export_ref == input_ref:
                if matched_export != null:
                    return error("AMBIGUOUS_REF", input_ref)  // 同一引用不应出现在多个 Card
                matched_export = export
                matched_card = card
    
    if matched_export == null:
        // Step 2b: 如果在 Card 中未找到，尝试 Metric Registry（仅 metric://）
        if ref_type == "metric":
            registry_entry = metric_registry.lookup(metric_id)
            if registry_entry != null:
                return error("EXPORT_NOT_REGISTERED_IN_CARD", input_ref, 
                            "Metric 已在 Registry 注册，但无 Analysis Card 导出")
        return error("UNRESOLVABLE_REF", input_ref)
    
    // Step 3: 验证 export 元数据完整性
    validation = validate_export(matched_export, ref_type)
    if validation.failed:
        return error("EXPORT_METADATA_INCOMPLETE", input_ref, validation.reason)
    
    // Step 4: 对于 metric://，解析 value_path 获取实际值
    if ref_type == "metric":
        evidence = lookup_evidence(matched_export.evidence_ref)
        if evidence == null:
            return error("EVIDENCE_NOT_FOUND", matched_export.evidence_ref)
        value = evidence.metrics[matched_export.value_path]
        if value == null:
            return error("VALUE_PATH_NOT_FOUND", matched_export.value_path)
    else if ref_type == "fact":
        value = matched_export.fact_value
    else if ref_type == "label":
        value = matched_export.label_value
    
    // Step 5: 检查 freshness
    freshness = check_freshness(matched_card.data_freshness, metric_registry)
    if freshness == "stale":
        staleness_risk = "high"
    
    // Step 6: 返回解析结果
    return ResolvedRef(
        ref=input_ref,
        ref_type=ref_type,
        value=value,
        evidence_ref=matched_export.evidence_ref,
        evidence=evidence,  // 完整 Evidence Packet
        determinism_level=matched_export.determinism_level,
        can_support_hard_constraint=matched_export.can_support_hard_constraint,
        allowed_constraint_types=matched_export.allowed_constraint_types,
        data_quality=matched_card.data_quality,
        data_freshness=matched_card.data_freshness,
        staleness_risk=staleness_risk,
        confidence=evidence.confidence if evidence.confidence != null else null,
        card_ref=matched_card.card_id,
        domain=matched_card.domain
    )


function validate_export(export: ConstraintExport, ref_type: string) -> ValidationResult:
    """验证 constraint_exports 项的元数据完整性"""
    
    errors = []
    
    if export.export_type != ref_type:
        errors.append("export_type 与引用格式不匹配")
    
    if export.export_ref == null or export.export_ref == "":
        errors.append("export_ref 缺失")
    
    if export.evidence_ref == null or export.evidence_ref == "":
        errors.append("evidence_ref 缺失")
        if ref_type == "metric" and export.can_support_hard_constraint == true:
            errors.append("Hard-capable export 缺少 evidence_ref → Post-card Validation = block")
    
    if ref_type == "metric" and (export.value_path == null or export.value_path == ""):
        errors.append("metric 类型 export 缺少 value_path")
    
    if ref_type == "fact" and export.fact_value == null:
        errors.append("fact 类型 export 缺少 fact_value")
    
    if ref_type == "label" and export.label_value == null:
        errors.append("label 类型 export 缺少 label_value")
    
    if export.determinism_level == null:
        errors.append("determinism_level 缺失")
    
    if export.can_support_hard_constraint == null:
        errors.append("can_support_hard_constraint 缺失")
    
    if export.allowed_constraint_types == null or export.allowed_constraint_types.isEmpty():
        errors.append("allowed_constraint_types 缺失或为空")
    
    return ValidationResult(
        failed=(errors.length > 0),
        reason=errors.join("; ")
    )
```

---

## 3. Capability Package 定义

### 3.1 什么是 Capability Package

Capability Package 是**工具、模型、数据连接器的打包与版本管理单元**。

它不是能力域本身——能力域是分析边界，Package 是实现手段。一个能力域可以依赖多个 Package，一个 Package 可以被多个能力域重用。

```
能力域（Domain）           Capability Package（Package）
─────────────────────      ──────────────────────────────
"分析什么"                  "用什么分析"
分析边界                    工具/模型/数据连接器的组合
SPEC-004 定义               SPEC-005 定义
向编排器返回 Analysis Card  提供 Evidence Packet 生成能力
```

一句话：

> Capability Package = 可独立版本化、可声明依赖、可追踪调用链的工具/模型/数据连接器组合。

### 3.2 Capability Package Schema

```json
{
  "package_id": "pkg_fundamentals_financial_v1",
  "package_name": "Fundamentals Financial Metrics Package",
  "version": "0.1.0",
  "package_type": "capability_package",
  "target_domain": ["fundamentals"],
  
  "description": "基本面财务指标计算包：收入增速、毛利率、FCF 等 Computed Evidence 生成",
  
  "dependencies": [
    {
      "dependency_type": "data_connector",
      "connector_id": "conn_financial_data_api_v1",
      "version": ">=0.2.0,<0.3.0",
      "required": true,
      "description": "Financial Data API 连接器，提供季度财报数据"
    },
    {
      "dependency_type": "data_connector",
      "connector_id": "conn_industry_benchmark_api_v1",
      "version": ">=0.1.0",
      "required": false,
      "description": "行业基准数据连接器，可选，缺失时 industry_median 指标不可用"
    }
  ],
  
  "capabilities": [
    {
      "capability_id": "cap_financial_metric_compute",
      "capability_type": "tool",
      "tool_id": "tool_financial_ratio_calculator",
      "tool_version": "0.1.0",
      "determinism_level": "computed",
      "description": "确定性计算财务比率：revenue_growth_ttm、gross_margin_ttm 等",
      "inputs": {
        "required": ["quarterly_financial_data"],
        "optional": ["industry_benchmark_data"]
      },
      "outputs": {
        "evidence_type": "financial_metrics",
        "generation_type": "computed",
        "can_support_hard_constraint": true,
        "metrics_produced": [
          "revenue_growth_ttm",
          "gross_margin_ttm",
          "gross_margin_qoq_change",
          "fcf_margin_ttm",
          "net_debt_to_ebitda",
          "roe_ttm",
          "growth_capex_flag"
        ]
      }
    },
    {
      "capability_id": "cap_peer_comparison",
      "capability_type": "tool",
      "tool_id": "tool_peer_comparator",
      "tool_version": "0.1.0",
      "determinism_level": "computed",
      "description": "同业比较计算：industry_median_revenue_growth_ttm 等",
      "inputs": {
        "required": ["peer_financial_data"]
      },
      "outputs": {
        "evidence_type": "peer_comparison_metrics",
        "generation_type": "computed",
        "can_support_hard_constraint": true,
        "metrics_produced": [
          "industry_median_revenue_growth_ttm"
        ]
      }
    },
    {
      "capability_id": "cap_valuation_compute",
      "capability_type": "tool",
      "tool_id": "tool_valuation_calculator",
      "tool_version": "0.1.0",
      "determinism_level": "computed",
      "description": "估值指标计算：PE 分位、EV/EBITDA 分位、FCF Yield",
      "inputs": {
        "required": ["historical_price_data", "financial_data"]
      },
      "outputs": {
        "evidence_type": "valuation_metrics",
        "generation_type": "computed",
        "can_support_hard_constraint": true,
        "metrics_produced": [
          "pe_percentile_5y",
          "ev_ebitda_percentile_5y",
          "fcf_yield"
        ]
      }
    }
  ],
  
  "lineage_config": {
    "trace_mode": "full",
    "log_inputs": true,
    "log_intermediate_values": false,
    "log_outputs": true
  },
  
  "metadata": {
    "author": "crosslens-core",
    "created_at": "2026-06-14T00:00:00Z",
    "updated_at": "2026-06-14T00:00:00Z",
    "spec_version": "SPEC-005@0.1.0"
  }
}
```

### 3.3 字段说明

| 字段 | 含义 |
|---|---|
| `package_id` | Package 全局唯一标识 |
| `package_name` | 人类可读名称 |
| `version` | SemVer 版本号 |
| `package_type` | 固定值 `capability_package` |
| `target_domain` | 该 Package 服务的能力域列表 |
| `dependencies` | 依赖的数据连接器、其他 Package |
| `capabilities` | 该 Package 包含的工具/模型列表 |
| `lineage_config` | 调用链追踪配置 |
| `metadata` | 元信息 |

### 3.4 Capability 的类型

```
capability_type ∈ {
    "tool",          // 确定性计算工具（computed）
    "model",         // 模型（structured：分类器/标签器）
    "retriever",     // 检索器（数据抓取/搜索）
    "reasoner"       // Agentic Reasoning（interpreted）
}
```

`determinism_level` 与 `capability_type` 的映射：

| capability_type | 默认 determinism_level | 说明 |
|---|---|---|
| tool | computed | 确定性计算，可复现 |
| model | structured | 有明确输入输出的模型 |
| retriever | computed/structured | 取决于检索机制 |
| reasoner | interpreted | LLM/Agentic 推理 |

---

## 4. 工具调用链 Lineage 追踪

### 4.1 追踪模型

```
┌──────────────────────────────────────────────────────────────┐
│                    Lineage 追踪链路                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  DataSource                                                    │
│    │  source_id, source_type, connection_params_hash          │
│    ▼                                                          │
│  DataConnector.fetch()                                        │
│    │  connector_id, connector_version, fetch_timestamp        │
│    ▼                                                          │
│  RawData                                                       │
│    │  raw_data_hash, as_of, data_quality                      │
│    ▼                                                          │
│  Tool/Model.execute()                                         │
│    │  capability_id, package_id, package_version              │
│    │  input_hash (input 数据的 hash)                           │
│    │  execution_timestamp                                     │
│    │  execution_duration_ms                                   │
│    ▼                                                          │
│  Evidence Packet                                               │
│    │  evidence_id, evidence_type, generation_type             │
│    │  determinism_level                                       │
│    ▼                                                          │
│  Constraint Export (via Analysis Card)                        │
│    │  export_ref, value_path, can_support_hard_constraint     │
│    ▼                                                          │
│  Playbook Constraint Evaluation                               │
│       constraint_id, evaluation_result                        │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Lineage 追踪伪代码

```
class LineageNode:
    node_id: string           // 唯一标识
    node_type: enum { DATA_SOURCE, CONNECTOR, RAW_DATA, TOOL_EXECUTION, MODEL_INFERENCE, EVIDENCE, EXPORT, CONSTRAINT_EVAL }
    timestamp: datetime       // ISO 8601
    input_refs: List<string>  // 上游 node_id 列表
    output_refs: List<string> // 下游 node_id 列表
    metadata: dict            // 节点特有元数据
    parent_lineage_id: string // 所属 lineage 链 ID


function record_tool_execution(
    package: CapabilityPackage,
    capability: Capability,
    inputs: dict,
    outputs: EvidencePacket
) -> List<LineageNode>:
    """
    记录一次工具/模型调用的完整 lineage。
    返回 lineage 链中所有新增节点。
    """
    
    lineage_id = generate_uuid("lineage_")
    nodes = []
    timestamp = utc_now()
    
    // Node 1: 输入数据溯源
    for input_key, input_value in inputs.items():
        if is_data_ref(input_value):
            raw_data_node = LineageNode(
                node_id=generate_uuid("raw_"),
                node_type="RAW_DATA",
                timestamp=input_value.fetch_timestamp,
                metadata={
                    "source_id": input_value.source_id,
                    "source_type": input_value.source_type,
                    "raw_data_hash": sha256(input_value.raw_bytes),
                    "as_of": input_value.as_of,
                    "data_quality": input_value.data_quality
                },
                parent_lineage_id=lineage_id
            )
            nodes.append(raw_data_node)
            
            // 数据连接器节点
            connector_node = LineageNode(
                node_id=generate_uuid("conn_"),
                node_type="CONNECTOR",
                timestamp=input_value.fetch_timestamp,
                input_refs=[],
                output_refs=[raw_data_node.node_id],
                metadata={
                    "connector_id": input_value.connector_id,
                    "connector_version": input_value.connector_version,
                    "connection_params_hash": sha256(input_value.connection_params)
                },
                parent_lineage_id=lineage_id
            )
            nodes.append(connector_node)
            raw_data_node.input_refs = [connector_node.node_id]
    
    // Node 2: 工具执行节点
    input_hashes = {k: sha256(serialize(v)) for k, v in inputs.items()}
    input_node_ids = [n.node_id for n in nodes if n.node_type == "RAW_DATA"]
    
    execution_node = LineageNode(
        node_id=generate_uuid("exec_"),
        node_type="TOOL_EXECUTION" if capability.capability_type == "tool" else "MODEL_INFERENCE",
        timestamp=timestamp,
        input_refs=input_node_ids,
        output_refs=[outputs.evidence_id],
        metadata={
            "package_id": package.package_id,
            "package_version": package.version,
            "capability_id": capability.capability_id,
            "capability_type": capability.capability_type,
            "determinism_level": capability.determinism_level,
            "input_hash": sha256(serialize(input_hashes)),
            "execution_duration_ms": measure_execution_time()
        },
        parent_lineage_id=lineage_id
    )
    nodes.append(execution_node)
    
    // Node 3: Evidence Packet 节点
    evidence_node = LineageNode(
        node_id=outputs.evidence_id,
        node_type="EVIDENCE",
        timestamp=timestamp,
        input_refs=[execution_node.node_id],
        output_refs=[],
        metadata={
            "evidence_type": outputs.evidence_type,
            "generation_type": outputs.generation_type,
            "determinism_level": outputs.determinism_level,
            "can_support_hard_constraint": outputs.can_support_hard_constraint,
            "confidence": outputs.confidence,
            "data_quality": outputs.data_quality,
            "as_of": outputs.as_of
        },
        parent_lineage_id=lineage_id
    )
    nodes.append(evidence_node)
    execution_node.output_refs.append(evidence_node.node_id)
    
    return nodes


function trace_lineage_to_source(
    evidence_id: string,
    lineage_store: LineageStore
) -> LineageChain:
    """
    从 Evidence Packet 向上递归追溯到原始数据源。
    返回完整 lineage 链（Data Source → ... → Evidence Packet）。
    """
    
    chain = []
    visited = set()
    queue = [evidence_id]
    
    while queue not empty:
        node_id = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        
        node = lineage_store.get(node_id)
        if node == null:
            chain.append({"warning": f"Lineage 断链：{node_id} 不可追溯"})
            continue
        
        chain.append({
            "node_id": node.node_id,
            "node_type": node.node_type,
            "timestamp": node.timestamp,
            "metadata": node.metadata
        })
        
        // 继续追溯上游
        for parent_id in node.input_refs:
            queue.append(parent_id)
    
    return LineageChain(
        evidence_id=evidence_id,
        nodes=chain,
        is_complete=(not any("warning" in n for n in chain)),
        deepest_source=find_deepest_source(chain)
    )
```

### 4.3 Lineage 进入 Decision Trace 的规则

1. 每个 Evidence Packet 的 lineage 必须完整存储；
2. Decision Trace 可折叠展示 lineage，但不得丢失链路信息；
3. 如果 lineage 中存在断链（某节点的 input_refs 不可追溯），必须在 Decision Trace 中标记 `lineage_gap`；
4. 对于支撑 Hard Constraint 的 Evidence Packet，其 lineage 必须是完整且无断链的——如果存在 lineage gap，该 Evidence Packet 不得用于 Hard Constraint；
5. `confidence` 字段的 lineage 追溯规则见 §8。

### 4.4 Evidence Packet `confidence` 取值规则

本小节关闭 SPEC-003 §6.5 NOTE 中的 open issue。Evidence Packet 的 `confidence` 字段取值规则必须根据 `generation_type` 区分：

#### 4.4.1 Computed Evidence

```text
generation_type = "computed"

confidence 默认 = 1.0

降级条件（任一触发即下调）：
  1. 数据源延迟 > freshness_requirement.staleness_threshold_days
     → confidence 取 0.0 并由 Evidence Packet 标记 data_quality = "stale"
  2. 源数据存在已知质量问题（如财报重述、数据修正中）
     → confidence 取 Registry 中 confidence_metadata.confidence_downgrade_factors 的对应幅度
  3. 跨数据源验证失败（如不同 Data Connector 返回的同一 metric 偏差 > 阈值）
     → confidence 取两数据源的最小值

MV 实现：
  - 仅实现降级条件 1（数据过期检查），条件 2 和 3 由 Capability Package 的 validator 函数提供。
  - confidence 赋值逻辑：
    ├─ 数据未过期 → 1.0
    └─ 数据已过期 → data_quality = "stale", confidence = 0.0
```

#### 4.4.2 Structured Evidence

```text
generation_type = "structured"

confidence = 模型自评分（model_self_reported）

约束：
  1. confidence 值直接取自模型输出的 confidence 字段
  2. 必须同时记录 model_id + model_version
  3. 如果模型输出不含 confidence，Evidence Packet.confidence = null，由下游 Analysis Card 自行评估
  4. 不得手动设为 1.0

MV 实现：
  - 模型输出 confidence 字段 → 直接赋值
  - 模型输出无 confidence 字段 → Evidence Packet.confidence = null
```

#### 4.4.3 Interpreted Evidence

```text
generation_type = "interpreted"

confidence = LLM 输出值（不可复现）

约束：
  1. confidence 值由 LLM 在生成时自评得出
  2. 必须同时记录 model_id + temperature + prompt_hash
  3. 如果 LLM 输出不含 confidence，evidence.confidence = null
  4. 永不得支撑 Hard Constraint（继承 SPEC-003 §12）

MV 实现：
  - LLM 输出 confidence 字段 → 直接赋值
  - LLM 输出无 confidence 字段 → Evidence Packet.confidence = null
  - 标记为 data_quality = "interpreted", determinism_level = "interpreted"
```

#### 4.4.4 跨类型通用规则

```text
1. confidence ∈ [0.0, 1.0] | null
   null 仅允许用于 MVP 阶段 Structured/Interpreted Evidence（当模型/LLM 不输出 confidence 时）
2. Computed Evidence 的 confidence = null 属于实现错误（应回退为 1.0）
3. 所有 confidence 值在进入 Analysis Card 前不降级；
   降级检查在 Post-card Validation 和 Pre-decision Validation 阶段执行（SPEC-003 §13, §14）
4. confidence = 0.0 表示证据不可用，不等于 "不可信"；
   不可信的 Computed Evidence 应升级为 data_quality 问题而不修改 confidence
```

#### 4.4.5 与 Metric Registry 的关系

Evidence Packet 中每个 metric 的 confidence 由 Registry 的 `confidence_metadata.determination_type` 继承其默认规则：

| determination_type | generation_type | confidence 来源 | 默认值 |
|---|---|---|---|
| `computed_default` | computed | 确定性计算 | 1.0 |
| `computed_with_event_lineage_check` | computed | 确定性计算 + lineage 检查 | 1.0（检查失败则继承 source_event.confidence） |
| `derived_rule` | computed | 继承输入 metric 的最小 confidence | null（由输入决定） |
| `model_output` | structured | 模型自评分 | null（模型不输出则为 null） |
| `llm_interpreted` | interpreted | LLM 上下文自评 | null（LLM 不输出则为 null） |

上述映射已在 §8.2 `determination_type` 规范中定义，本小节仅补充 Evidence Packet 层面的赋值规则。

> **SPEC-003 §6.5 NOTE 已通过本小节关闭。** MVP 实现时，Evidence Packet 的 `confidence` 字段依据本节的 generation_type 规则赋值。

### 5.1 Metric Registry 的职责

Metric Registry 是 **metric_id 到 Evidence Packet + value_path + freshness 规则的索引层**。

它不存储实际值——它只负责回答：

> "当 Playbook 引用 `metric://revenue_growth_ttm` 时，这个值应该从哪个 Evidence Packet 的哪个路径获取？该数据多久需要刷新一次？哪个能力域负责生产它？"

### 5.2 Metric Registry Schema

```json
{
  "registry_id": "metric_registry_v0.1.0",
  "registry_version": "0.1.0",
  "spec_version": "SPEC-005@0.1.0",
  "updated_at": "2026-06-14T00:00:00Z",
  
  "metrics": {
    "revenue_growth_ttm": {
      "metric_id": "revenue_growth_ttm",
      "display_name": "TTM 收入增速",
      "description": "过去四个季度的总收入同比增长率",
      "value_type": "number",
      "unit": "percent",
      "metric_category": "computed",
      
      "source_domain": "fundamentals",
      "producing_package": "pkg_fundamentals_financial_v1",
      "producing_capability": "cap_financial_metric_compute",
      
      "evidence_type": "financial_metrics",
      "generation_type": "computed",
      "determinism_level": "computed",
      "can_support_hard_constraint": true,
      
      "evidence_value_path": "revenue_growth_ttm",
      "expected_export_ref": "metric://revenue_growth_ttm",
      
      "freshness_requirement": {
        "update_frequency": "quarterly",
        "staleness_threshold_days": 120,
        "valid_until_rule": "next_quarter_end_plus_45_days",
        "description": "每季度财报发布后 45 天内有效"
      },
      
      "confidence_metadata": {
        "determination_type": "computed_default",
        "default_confidence": 1.0,
        "confidence_cap_reason": "确定性计算，公式公开可审计",
        "confidence_downgrade_factors": [
          "数据源延迟超过 staleness_threshold_days",
          "财报重述或会计方法变更"
        ]
      },
      
      "related_metrics": ["industry_median_revenue_growth_ttm"],
      "tags": ["growth", "revenue", "hard_constraint_capable"]
    },
    
    "growth_capex_flag": {
      "metric_id": "growth_capex_flag",
      "display_name": "增长型资本开支标记",
      "description": "公司级资本开支增长与对应产能/增长投入是否满足确定性条件",
      "value_type": "boolean",
      "unit": "flag",
      "metric_category": "computed",
      
      "source_domain": "fundamentals",
      "producing_package": "pkg_fundamentals_financial_v1",
      "producing_capability": "cap_financial_metric_compute",
      
      "evidence_type": "financial_metrics",
      "generation_type": "computed",
      "determinism_level": "computed",
      "can_support_hard_constraint": true,
      
      "evidence_value_path": "growth_capex_flag",
      "expected_export_ref": "metric://growth_capex_flag",
      
      "computation_constraints": {
        "must_not_infer_from_macro_label": "capex_cycle_stage",
        "required_inputs": [
          "company_capex_growth_yoy",
          "capacity_expansion_status",
          "revenue_growth_ttm"
        ],
        "description": "必须由公司级数据确定性计算，不得从 Macro/Meso 的 Structured label 推断"
      },
      
      "freshness_requirement": {
        "update_frequency": "quarterly",
        "staleness_threshold_days": 120,
        "valid_until_rule": "next_quarter_end_plus_45_days"
      },
      
      "confidence_metadata": {
        "determination_type": "computed_default",
        "default_confidence": 1.0
      },
      
      "related_metrics": ["revenue_growth_ttm", "fcf_margin_ttm"],
      "tags": ["growth", "capex", "hard_constraint_capable", "computation_constrained"]
    },
    
    "pe_percentile_5y": {
      "metric_id": "pe_percentile_5y",
      "display_name": "PE 5 年分位",
      "description": "当前 PE 在过去 5 年中的分位数（0-1）",
      "value_type": "number",
      "unit": "percentile",
      "metric_category": "computed",
      
      "source_domain": "fundamentals",
      "producing_package": "pkg_fundamentals_financial_v1",
      "producing_capability": "cap_valuation_compute",
      
      "evidence_type": "valuation_metrics",
      "generation_type": "computed",
      "determinism_level": "computed",
      "can_support_hard_constraint": true,
      
      "evidence_value_path": "pe_percentile_5y",
      "expected_export_ref": "metric://pe_percentile_5y",
      
      "freshness_requirement": {
        "update_frequency": "daily",
        "staleness_threshold_days": 5,
        "valid_until_rule": "daily_update_plus_5_days"
      },
      
      "confidence_metadata": {
        "determination_type": "computed_default",
        "default_confidence": 1.0,
        "confidence_downgrade_factors": [
          "缺失历史 PE 数据段导致分位计算不可靠",
          "公司业务结构重大变化使历史 PE 失去可比性"
        ]
      },
      
      "related_metrics": ["ev_ebitda_percentile_5y", "fcf_yield"],
      "tags": ["valuation", "hard_constraint_capable"]
    },
    
    "post_event_1d_return": {
      "metric_id": "post_event_1d_return",
      "display_name": "事件后 1 日收益率",
      "description": "公司事件发生后一个交易日的收益率",
      "value_type": "number",
      "unit": "percent",
      "metric_category": "computed",
      
      "source_domain": "company_event",
      "producing_package": "pkg_event_price_tracker_v1",
      "producing_capability": "cap_event_price_reaction",
      
      "evidence_type": "post_event_price_reaction",
      "generation_type": "computed",
      "determinism_level": "computed",
      "can_support_hard_constraint": true,
      
      "evidence_value_path": "post_event_1d_return",
      "expected_export_ref": "metric://post_event_1d_return",
      
      "lineage_constraints": {
        "requires_source_event_ref": true,
        "source_event_certainty_must_be": "confirmed",
        "source_event_generation_type_must_not_be": "interpreted",
        "description": "继承 SPEC-004 §26.1 的 lineage 约束"
      },
      
      "freshness_requirement": {
        "update_frequency": "event_driven",
        "staleness_threshold_days": 30,
        "valid_until_rule": "event_driven_30_days"
      },
      
      "confidence_metadata": {
        "determination_type": "computed_with_event_lineage_check",
        "default_confidence": 1.0,
        "confidence_downgrade_factors": [
          "source_event_certainty 非 confirmed",
          "source_event 为 Interpreted Evidence"
        ]
      },
      
      "tags": ["event", "price_reaction", "hard_constraint_capable", "lineage_constrained"]
    },
    
    "bullish_ratio": {
      "metric_id": "bullish_ratio",
      "display_name": "社交媒体多头比率",
      "description": "社交/零售渠道的多头情绪比率 (0-1)",
      "value_type": "number",
      "unit": "ratio",
      "metric_category": "structured",
      
      "source_domain": "sentiment",
      "producing_package": "pkg_sentiment_social_v1",
      "producing_capability": "cap_social_sentiment_score",
      
      "evidence_type": "social_sentiment_score",
      "generation_type": "structured",
      "determinism_level": "structured",
      "can_support_hard_constraint": false,
      
      "evidence_value_path": "bullish_ratio",
      "expected_export_ref": "metric://bullish_ratio",
      
      "freshness_requirement": {
        "update_frequency": "daily",
        "staleness_threshold_days": 3,
        "valid_until_rule": "daily_update_plus_3_days"
      },
      
      "confidence_metadata": {
        "determination_type": "model_output",
        "model_id": "model_sentiment_classifier_v1",
        "model_version": "0.2.0",
        "confidence_source": "model_self_reported",
        "default_confidence": null,
        "description": "由结构化情绪分类模型输出，confidence 取自模型自评分"
      },
      
      "related_metrics": ["discussion_volume_zscore", "news_sentiment_score"],
      "tags": ["sentiment", "social", "soft_constraint_only"]
    }
  },
  
  "facts": {
    "retail_sentiment_overheated": {
      "fact_id": "retail_sentiment_overheated",
      "display_name": "散户情绪过热",
      "description": "散户渠道情绪处于过热区域",
      "value_type": "boolean",
      "source_domain": "sentiment",
      "producing_package": "pkg_sentiment_social_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "fact://retail_sentiment_overheated"
    },
    "any_material_event_low_certainty": {
      "fact_id": "any_material_event_low_certainty",
      "display_name": "存在高重要度低确定性事件",
      "description": "存在至少一条 materiality=high 但 certainty 非 confirmed 的事件",
      "value_type": "boolean",
      "source_domain": "company_event",
      "producing_package": "pkg_event_analyzer_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "fact://any_material_event_low_certainty",
      "production_contract": "SPEC-004 §26.2"
    },
    "latest_material_event_is_confirmed": {
      "fact_id": "latest_material_event_is_confirmed",
      "display_name": "最新高重要度事件已确认",
      "description": "最新一条 materiality=high 事件的 certainty=confirmed",
      "value_type": "boolean",
      "source_domain": "company_event",
      "producing_package": "pkg_event_analyzer_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "fact://latest_material_event_is_confirmed",
      "production_contract": "SPEC-004 §26.2"
    },
    "any_material_negative_event_unresolved": {
      "fact_id": "any_material_negative_event_unresolved",
      "display_name": "存在高重要度负面未解决事件",
      "description": "存在 materiality=high、direction=negative、resolution_status=open 的事件",
      "value_type": "boolean",
      "source_domain": "company_event",
      "producing_package": "pkg_event_analyzer_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "fact://any_material_negative_event_unresolved",
      "production_contract": "SPEC-004 §26.2"
    },
    "narrative_crowded_positive": {
      "fact_id": "narrative_crowded_positive",
      "display_name": "正面叙事拥挤",
      "description": "市场叙事故意过于集中在正面方向",
      "value_type": "boolean",
      "source_domain": "sentiment",
      "producing_package": "pkg_sentiment_narrative_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "fact://narrative_crowded_positive"
    }
  },
  
  "labels": {
    "industry_cycle_stage": {
      "label_id": "industry_cycle_stage",
      "display_name": "行业周期阶段",
      "allowed_values": ["early_recovery", "expansion", "peak", "contraction", "trough", "unknown"],
      "source_domain": "macro_meso",
      "producing_package": "pkg_industry_cycle_classifier_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "label://industry_cycle_stage"
    },
    "valuation_state": {
      "label_id": "valuation_state",
      "display_name": "估值状态标签",
      "allowed_values": ["cheap", "reasonable", "expensive", "very_expensive", "unknown"],
      "source_domain": "fundamentals",
      "producing_package": "pkg_fundamentals_financial_v1",
      "can_support_hard_constraint": false,
      "expected_export_ref": "label://valuation_state",
      "derivation_rule": "由 pe_percentile_5y、ev_ebitda_percentile_5y 等 Computed metrics 确定性映射"
    }
  }
}
```

### 5.3 Computed Metric 与 Derived Metric 的区分

```
┌────────────────────────────────────────────────────────────┐
│              Metric 分类体系                                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Computed Metric（计算型指标）                               │
│  ├─ 由确定性计算（公式、规则、数据接口）直接生成               │
│  ├─ 来源：Computed Evidence                                 │
│  ├─ 示例：revenue_growth_ttm, pe_percentile_5y, rsi_14d    │
│  ├─ confidence 默认 1.0（见 §8）                             │
│  └─ 默认可以支撑 Hard Constraint（前提：can_support = true）  │
│                                                            │
│  Derived Metric（派生型指标）                                │
│  ├─ 由一个或多个 Computed/Structured Metric 确定性映射生成    │
│  ├─ 来源：规则映射表（非 LLM 推理）                           │
│  ├─ 示例：valuation_state label、growth_capex_flag          │
│  ├─ confidence 继承输入 metric 的最小 confidence              │
│  └─ 如果所有输入为 Computed，则可支撑 Hard Constraint         │
│                                                            │
│  Structured Metric（结构化模型输出）                          │
│  ├─ 由专门模型/分类器生成                                     │
│  ├─ 来源：Structured Evidence                                │
│  ├─ 示例：bullish_ratio, sentiment_state label              │
│  ├─ confidence 为模型自评分                                   │
│  └─ 默认不支撑 Hard Constraint（can_support = false）         │
│                                                            │
│  Interpreted Metric（解释型指标）                             │
│  ├─ 由 LLM/Agentic Reasoning 生成                           │
│  ├─ 来源：Interpreted Evidence                               │
│  ├─ 永远不支撑 Hard Constraint                                │
│  └─ confidence 取决于生成上下文                               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Derived Metric 确定性映射规则伪代码：**

```
function derive_valuation_state(pe_percentile: float, ev_ebitda_percentile: float) -> string:
    """
    从 Computed metrics 确定性派生 valuation_state label。
    规则化映射，不使用 LLM。
    """
    max_percentile = max(pe_percentile, ev_ebitda_percentile)
    
    if max_percentile >= 0.90:
        return "very_expensive"
    else if max_percentile >= 0.75:
        return "expensive"
    else if max_percentile <= 0.25:
        return "cheap"
    else:
        return "reasonable"


function derive_growth_capex_flag(
    company_capex_growth_yoy: float,
    capacity_expansion: string,
    revenue_growth_ttm: float
) -> bool:
    """
    从公司级数据确定性计算 growth_capex_flag。
    不得使用 Macro/Meso 的 capex_cycle_stage label。
    """
    if company_capex_growth_yoy == null or capacity_expansion == null:
        return null  // 数据不足，不导出
    
    return (
        company_capex_growth_yoy >= 0.20
        AND capacity_expansion in {"active", "planned", "underway"}
        AND revenue_growth_ttm != null
        AND revenue_growth_ttm >= 0.10
    )
```

### 5.4 Metric Registry 查询接口

```
class MetricRegistry:
    metrics: Dict<string, MetricEntry>
    facts: Dict<string, FactEntry>
    labels: Dict<string, LabelEntry>
    
    function lookup(metric_id: string) -> MetricEntry | null:
        """通过 metric_id 精确查找"""
        return self.metrics.get(metric_id)
    
    function lookup_fact(fact_id: string) -> FactEntry | null:
        """通过 fact_id 查找"""
        return self.facts.get(fact_id)
    
    function lookup_label(label_id: string) -> LabelEntry | null:
        """通过 label_id 查找"""
        return self.labels.get(label_id)
    
    function list_by_domain(domain: string) -> List<MetricEntry>:
        """列出指定能力域的所有注册 Metric"""
        return [m for m in self.metrics.values() if m.source_domain == domain]
    
    function list_hard_capable() -> List<MetricEntry>:
        """列出所有可支撑 Hard Constraint 的 Metric"""
        return [m for m in self.metrics.values() if m.can_support_hard_constraint]
    
    function list_by_package(package_id: string) -> List<MetricEntry>:
        """列出指定 Package 生产的所有 Metric"""
        return [m for m in self.metrics.values() if m.producing_package == package_id]
    
    function resolve_input_ref(input_ref: string) -> ResolvedRegistryEntry | null:
        """
        统一解析 input_ref（metric:// / fact:// / label://），
        返回 Registry 中的注册信息。
        用于 Playbook 加载时的静态校验。
        """
        if input_ref starts with "metric://":
            entry = self.lookup(input_ref.slice("metric://".len))
            return ResolvedRegistryEntry(ref_type="metric", entry=entry) if entry != null else null
        else if input_ref starts with "fact://":
            entry = self.lookup_fact(input_ref.slice("fact://".len))
            return ResolvedRegistryEntry(ref_type="fact", entry=entry) if entry != null else null
        else if input_ref starts with "label://":
            entry = self.lookup_label(input_ref.slice("label://".len))
            return ResolvedRegistryEntry(ref_type="label", entry=entry) if entry != null else null
        else:
            return null
    
    function validate_constraint_input_refs(
        constraint: PlaybookConstraint
    ) -> InputRefValidationResult:
        """
        Playbook 加载时静态校验：检查 Constraint 的 input_refs
        是否在 Registry 中存在、类型是否匹配、Hard Constraint 引用限制。
        """
        errors = []
        warnings = []
        
        for ref in constraint.input_refs:
            resolved = self.resolve_input_ref(ref)
            
            if resolved == null:
                errors.append({"ref": ref, "error": "NOT_IN_REGISTRY"})
                continue
            
            if constraint.condition_type == "hard":
                if resolved.ref_type != "metric":
                    errors.append({
                        "ref": ref,
                        "error": "HARD_CONSTRAINT_REQUIRES_METRIC_REF",
                        "actual_type": resolved.ref_type
                    })
                else if not resolved.entry.can_support_hard_constraint:
                    errors.append({
                        "ref": ref,
                        "error": "METRIC_NOT_HARD_CAPABLE",
                        "metric_id": resolved.entry.metric_id
                    })
        
        return InputRefValidationResult(
            valid=(len(errors) == 0),
            errors=errors,
            warnings=warnings
        )
    
    function check_staleness(
        metric_id: string,
        evidence_as_of: datetime
    ) -> StalenessResult:
        """
        检查 Evidence Packet 的 as_of 是否超出指标的新鲜度阈值。
        """
        entry = self.lookup(metric_id)
        if entry == null:
            return StalenessResult(status="unknown", reason="Metric 未注册")
        
        days_since = (utc_now() - evidence_as_of).days
        threshold = entry.freshness_requirement.staleness_threshold_days
        
        if days_since <= threshold:
            return StalenessResult(status="fresh", days_since=days_since)
        else:
            return StalenessResult(
                status="stale",
                days_since=days_since,
                threshold=threshold,
                reason=f"数据距今 {days_since} 天，超过 {threshold} 天阈值"
            )
```

---

## 6. Metric → constraint_exports 映射规则

### 6.1 映射流程

```
┌──────────────────────────────────────────────────────────────────┐
│            Metric Registry → constraint_exports 映射             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: 能力域生成 Evidence Packet                               │
│    │ 能力域调用 Capability Package，生成 Evidence Packet           │
│    │ Evidence Packet 包含 metrics + metadata                     │
│    ▼                                                            │
│  Step 2: 能力域构建 constraint_exports                            │
│    │ 对每个需要导出的 metric:                                      │
│    │   2a. 在 Metric Registry 中查找 metric_id                    │
│    │   2b. 从 Registry 获取 evidence_value_path                   │
│    │   2c. 从 Registry 获取 determinism_level、can_support 等     │
│    │   2d. 构建 export 对象，填入 evidence_ref 和 value_path       │
│    │   2e. 将 export 放入 Analysis Card.constraint_exports        │
│    ▼                                                            │
│  Step 3: Analysis Card 提交给编排器                               │
│    ▼                                                            │
│  Step 4: Playbook Constraint 解析                                 │
│    │ 规则引擎通过 input_refs 在 Analysis Cards 中查找 export        │
│    │ 找到后获取 value、metadata、evidence_ref                     │
│    ▼                                                            │
│  Step 5: Playbook Evaluation 报告                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 6.2 映射构建伪代码

```
function build_constraint_exports(
    evidence_packets: List<EvidencePacket>,
    metric_registry: MetricRegistry,
    domain: string
) -> List<ConstraintExport>:
    """
    能力域在生成 Analysis Card 时调用此函数，
    自动从 Evidence Packet 和 Metric Registry 构建 constraint_exports。
    """
    
    exports = []
    
    for evidence in evidence_packets:
        if evidence.domain != domain:
            continue  // 不属于当前能力域的 Evidence 跳过
        
        // 遍历 Registry 中该 Package 生产的所有 Metric
        registry_metrics = metric_registry.list_by_package(
            evidence.metadata.package_id
        )
        
        for reg_metric in registry_metrics:
            // 检查 Evidence 中是否确实包含该 metric
            if reg_metric.evidence_value_path not in evidence.metrics:
                continue  // 该 Evidence 未生成此 metric
            
            // 检查 lineage 约束（如 Company Event metrics）
            if reg_metric.lineage_constraints != null:
                lineage_check = check_lineage_constraints(
                    evidence, reg_metric.lineage_constraints
                )
                if not lineage_check.passed:
                    // lineage 约束不满足 → 降级
                    actual_can_support = false
                    actual_allowed = ["soft"]
                    exports.append(ConstraintExport(
                        export_type="metric",
                        export_ref=reg_metric.expected_export_ref,
                        evidence_ref=evidence.evidence_id,
                        value_path=reg_metric.evidence_value_path,
                        determinism_level=reg_metric.determinism_level,
                        can_support_hard_constraint=false,
                        allowed_constraint_types=["soft"],
                        lineage_constraint_failure=lineage_check.reason
                    ))
                    continue
            
            exports.append(ConstraintExport(
                export_type="metric",
                export_ref=reg_metric.expected_export_ref,
                evidence_ref=evidence.evidence_id,
                value_path=reg_metric.evidence_value_path,
                determinism_level=reg_metric.determinism_level,
                can_support_hard_constraint=reg_metric.can_support_hard_constraint,
                allowed_constraint_types=(
                    ["hard", "soft"] if reg_metric.can_support_hard_constraint else ["soft"]
                )
            ))
    
    return exports
```

### 6.3 映射一致性检查

```
function validate_export_against_registry(
    export: ConstraintExport,
    registry: MetricRegistry
) -> ConsistencyResult:
    """
    运行时检查：验证 Analysis Card 的 constraint_exports 
    是否与 Metric Registry 的声明一致。
    不一致时触发 Post-card Validation。
    """
    
    errors = []
    
    if export.export_type == "metric":
        metric_id = export.export_ref.slice("metric://".len)
        reg_entry = registry.lookup(metric_id)
        
        if reg_entry == null:
            errors.append(f"Metric {metric_id} 未在 Registry 注册")
        else:
            if export.can_support_hard_constraint and not reg_entry.can_support_hard_constraint:
                errors.append(
                    f"Metric {metric_id}: export 声明 can_support_hard_constraint=true，"
                    f"但 Registry 声明为 false"
                )
            if export.determinism_level != reg_entry.determinism_level:
                errors.append(
                    f"Metric {metric_id}: determinism_level 不一致 "
                    f"(export={export.determinism_level}, registry={reg_entry.determinism_level})"
                )
    
    return ConsistencyResult(
        consistent=(len(errors) == 0),
        errors=errors
    )
```

---

## 7. Capability Package 版本管理与依赖声明

### 7.1 版本策略

```
Package 版本号遵循 SemVer：MAJOR.MINOR.PATCH

MAJOR: 不兼容的输出 schema 变更
  - Evidence Packet schema 变更（字段重命名/删除/类型变化）
  - metric_id 语义变更
  - determinism_level 变更
  - 依赖的 data connector 不兼容升级

MINOR: 向后兼容的新功能
  - 新增 metric / tool / capability
  - 新增可选依赖
  - 优化计算精度（不改变 schema）

PATCH: 向后兼容的修复
  - Bug 修复
  - 性能优化
  - 文档更新
```

### 7.2 依赖声明与解析

```
function resolve_dependencies(
    package: CapabilityPackage,
    registry: PackageRegistry
) -> DependencyResolutionResult:
    """
    解析 Package 的依赖闭包。
    返回完整依赖列表或冲突。
    """
    
    resolved = []
    unresolved = []
    queue = copy(package.dependencies)
    
    while queue not empty:
        dep = queue.pop(0)
        
        // 查找已安装的依赖版本
        installed = registry.find(dep.connector_id)
        
        if installed == null:
            if dep.required:
                unresolved.append({
                    "dependency": dep.connector_id,
                    "error": "NOT_FOUND",
                    "required": true
                })
            else:
                resolved.append({
                    "dependency": dep.connector_id,
                    "status": "NOT_FOUND_BUT_OPTIONAL",
                    "warning": "可选依赖未安装，相关功能不可用"
                })
            continue
        
        // 版本兼容性检查
        if not semver_satisfies(installed.version, dep.version):
            unresolved.append({
                "dependency": dep.connector_id,
                "error": "VERSION_MISMATCH",
                "required_version": dep.version,
                "installed_version": installed.version
            })
            continue
        
        resolved.append({
            "dependency": dep.connector_id,
            "installed_version": installed.version,
            "status": "RESOLVED"
        })
        
        // 递归解析传递依赖
        if installed.dependencies != null:
            for trans_dep in installed.dependencies:
                queue.append(trans_dep)
    
    return DependencyResolutionResult(
        success=(len(unresolved) == 0),
        resolved=resolved,
        unresolved=unresolved
    )
```

### 7.3 Package 版本锁定与 Playbook 兼容性

Playbook 引用的 `metric://` ref 不直接指定 Package 版本。解析路径为：

```
metric://revenue_growth_ttm
  → Metric Registry 查找
  → 获取 producing_package + producing_capability
  → Package Registry 解析当前安装版本
  → 若 installed_version 与 Playbook 编写时锁定的版本不兼容
     → 触发 Playbook Applicability Evaluator（SPEC-006）
     → 若无法判定，降级为 insufficient_data
```

Playbook 的 `dependency_snapshot_refs` 应包含：

```json
{
  "dependency_snapshot_refs": {
    "analysis_card_schema_version": "SPEC-004@0.2.5",
    "metric_registry_version": "0.1.0",
    "constraint_export_registry_snapshot_hash": "sha256:abc123...",
    "package_versions": {
      "pkg_fundamentals_financial_v1": "0.1.0",
      "pkg_sentiment_social_v1": "0.1.0"
    }
  }
}
```

---

## 8. 置信度传播链

### 8.1 传播模型

```
┌──────────────────────────────────────────────────────────────────┐
│                    置信度传播链                                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  数据源 quality                                                   │
│    │  data_quality: high / medium / low / unavailable / unknown  │
│    ▼                                                             │
│  数据新鲜度                                                       │
│    │  freshness_level, staleness_risk                            │
│    ▼                                                             │
│  计算/模型 Confidence                                            │
│    │  determination_type + default / model_output                │
│    ▼                                                             │
│  Evidence Packet.confidence                                      │
│    │  传播到 Analysis Card                                       │
│    ▼                                                             │
│  Analysis Card.confidence                                        │
│    │  能力域自评（受 dual cap 约束）                               │
│    ▼                                                             │
│  Constraint Evaluation                                           │
│    │  confidence 影响 Constraint 的可靠度                          │
│    ▼                                                             │
│  Decision Candidate.confidence                                   │
│    │  受 confidence_cap 约束                                      │
│    ▼                                                             │
│  Decision Trace                                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.2 `confidence` 的 `determination_type` 规范

每个 Metric 在 Registry 中必须声明 `determination_type`，且该类型必须可追溯到具体的计算/模型来源：

```
determination_type ∈ {
    "computed_default",
        → confidence 默认为 1.0
        → 由公开公式/规则计算
        → 可审计、可复现
        → 示例：revenue_growth_ttm, pe_percentile_5y

    "computed_with_event_lineage_check",
        → 基础 confidence 为 1.0
        → 但需要 lineage 检查（source_event 已确认 + 非 Interpreted）
        → 检查失败时降级为 conditional，confidence 取 source_event.confidence
        → 示例：post_event_1d_return, days_since_event

    "model_output",
        → confidence 为模型自评分
        → 必须记录 model_id + model_version
        → 示例：bullish_ratio, sentiment_state

    "derived_rule",
        → confidence 继承输入 metric 的最小 confidence
        → 规则化映射，不引入额外不确定性
        → 示例：valuation_state, growth_capex_flag

    "llm_interpreted",
        → confidence 取决于 LLM 上下文
        → 必须记录 model_id + temperature + prompt_hash
        → 永远不支撑 Hard Constraint
        → 示例：复杂事件影响路径解释
}
```

### 8.3 Confidence 追溯伪代码

```
function trace_confidence(
    evidence: EvidencePacket,
    metric_registry: MetricRegistry
) -> ConfidenceTrace:
    """
    从 Evidence Packet 的 confidence 向上追溯到 determination 来源。
    """
    
    trace = ConfidenceTrace(evidence_id=evidence.evidence_id)
    
    // Step 1: 获取 evidence 的 generation_type
    gen_type = evidence.generation_type
    
    // Step 2: 根据 generation_type 确定 determination 来源
    if gen_type == "computed":
        // 找到证据中所有 metric，查 Registry 获取 determination_type
        for metric_name in evidence.metrics.keys():
            reg_entry = metric_registry.lookup(metric_name)
            if reg_entry != null:
                trace.add_node(ConfidenceNode(
                    metric_id=metric_name,
                    determination_type=reg_entry.confidence_metadata.determination_type,
                    confidence=evidence.confidence,
                    source=reg_entry.confidence_metadata,
                    lineage=reg_entry.producing_package + "@" + reg_entry.version
                ))
        
        trace.confidence_level = "high"
        trace.auditable = true
    
    else if gen_type == "structured":
        trace.add_node(ConfidenceNode(
            determination_type="model_output",
            confidence=evidence.confidence,
            source={
                "model_id": evidence.source_name,
                "model_version": evidence.model_version
            }
        ))
        trace.confidence_level = "medium"
        trace.auditable = false  // 模型内部不可审计
        trace.audit_note = "模型输出的 confidence 由模型自评，黑箱内部不可审计"
    
    else if gen_type == "interpreted":
        trace.add_node(ConfidenceNode(
            determination_type="llm_interpreted",
            confidence=evidence.confidence,
            source={
                "model_id": evidence.source_name,
                "prompt_hash": evidence.metadata.get("prompt_hash"),
                "temperature": evidence.metadata.get("temperature")
            }
        ))
        trace.confidence_level = "low"
        trace.auditable = false
        trace.audit_note = "LLM 解释性输出，confidence 不可复现"
    
    // Step 3: 检查 confidence 是否有降级因素
    if evidence.data_quality in {"low", "unavailable"}:
        trace.downgrade_factors.append({
            "factor": "data_quality_low",
            "actual": evidence.data_quality,
            "impact": "confidence 应下调，但下调幅度由 Valuation / Conflict Detection 决定"
        })
    
    return trace
```

---

## 9. 与 SPEC-004 的接口契约

### 9.1 Capability Package → 能力域

| 契约项 | SPEC-005 提供 | SPEC-004 消费 |
|---|---|---|
| Package 版本与依赖 | `package.version` + `dependencies[]` | 能力域在实例化时声明使用哪个 Package 版本 |
| Evidence 生成能力 | `capabilities[].outputs` | 能力域据此调用 Package 生成 Evidence Packet |
| Lineage 配置 | `lineage_config` | 能力域按配置记录调用链 |
| Metric 注册 | Metric Registry 中的 `producing_package` 字段 | 能力域据此查找应导出的 metric |

### 9.2 Metric Registry → constraint_exports

| 契约项 | SPEC-005 提供 | SPEC-004 消费 |
|---|---|---|
| `evidence_value_path` | Registry 中的 `evidence_value_path` | Analysis Card `constraint_exports[].value_path` |
| `can_support_hard_constraint` | Registry 中声明 | export 中继承 |
| `determinism_level` | Registry 中声明 | export 中继承 |
| `expected_export_ref` | Registry 中声明 | export 中 `export_ref` |
| Freshness 规则 | `freshness_requirement` | Analysis Card `data_freshness` |
| Confidence 元数据 | `confidence_metadata` | 能力域在生成 Evidence Packet 时应用 |

### 9.3 约束边界

SPEC-005 为 SPEC-004 定义以下硬边界：

1. **export 不得脱离 Registry 注册**：Analysis Card 的 `constraint_exports` 中出现的 `export_ref` 必须在 Metric Registry（或 Fact/Label Registry）中有对应注册项；
2. **`can_support_hard_constraint` 以上游声明为准**：export 的 `can_support_hard_constraint` 不得高于 Registry 中声明的值；
3. **`determinism_level` 不可升级**：export 的 `determinism_level` 不得高于 Registry 中声明的级别（例如，Registry 中声明 `structured`，export 不得标记为 `computed`）；
4. **Structured Evidence 默认不得直接支撑 Hard Constraint**（继承 SPEC-003 §12 + SPEC-004 §2.4）；
5. **Interpreted Evidence 永远不得支撑 Hard Constraint**（继承 SPEC-003 §12 + SPEC-004 §2.4）。

---

## 10. 与 SPEC-006 的接口契约

### 10.1 Metric Registry → Playbook Constraint

| 契约项 | SPEC-005 提供 | SPEC-006 消费 |
|---|---|---|
| input_ref 静态校验 | `MetricRegistry.validate_constraint_input_refs()` | Playbook 加载时的 Schema Validation |
| input_ref 运行时解析 | 通过 Analysis Card `constraint_exports` + Registry 解析 | §18 input_refs 解析规则 |
| Freshness 检查 | `check_staleness()` | Constraint 评估时的 `on_stale_data` 触发 |
| Confidence 追溯 | `trace_confidence()` | Decision Trace 中的置信度说明 |
| Registry 版本快照 | `registry_version` + snapshot hash | Playbook `dependency_snapshot_refs` |

### 10.2 Capability Package → Playbook

| 契约项 | SPEC-005 提供 | SPEC-006 消费 |
|---|---|---|
| Package 版本锁定 | Package version | Playbook `dependency_snapshot_refs.package_versions` |
| 版本不兼容处理 | `DependencyResolutionResult` | Playbook Applicability Evaluator |
| Lineage 完整链 | `trace_lineage_to_source()` | Decision Trace |
| Hard Constraint 输入限制 | `can_support_hard_constraint` + `determinism_level` | §20.1 输入限制规则 |

### 10.3 约束边界

1. **Hard Constraint 引用必须可解析到 Computed Evidence**：Playbook 的 Hard Constraint 的 `input_refs` 必须能通过 Registry → constraint_exports → Evidence Packet 完整解析链定位到 `determinism_level = computed` 的 Evidence；
2. **Structured/Interpreted Evidence 不得通过 Registry 绕过限制**：即使 Metric Registry 中存在某个 metric 的注册，如果其 `can_support_hard_constraint = false`，Playbook 的 Hard Constraint 不得引用；
3. **Lineage 断链阻止 Hard Constraint**：如果某个 metric 的 lineage 不完整（存在 `lineage_gap`），Playbook Evaluation 必须将其状态标记为 `insufficient_data`；
4. **Confidence 默认为 1.0 仅限 Computed**：Computed Evidence 的 confidence 默认为 1.0 是 SPEC-005 的定义，Playbook Evaluation 不得将 Structured/Interpreted Evidence 的 confidence 默认设为 1.0。

---

## 11. MVP 最小实现范围

### 11.1 MVP 必须实现

| 组件 | 最小形态 | 优先级 |
|---|---|---|
| Capability Package Schema | JSON 文件定义，手动维护 | P0 |
| Metric Registry | 静态 JSON 映射表，包含 §5.2 中列出的所有 MVP metric | P0 |
| Fact Registry | 静态 JSON，包含 derived facts | P0 |
| Label Registry | 静态 JSON，包含 label 枚举 | P1 |
| `resolve_input_ref()` | 实现 metric:// / fact:// / label:// 的解析 | P0 |
| `validate_export_against_registry()` | 运行时校验 export 与 Registry 一致性 | P0 |
| Lineage 记录 | 每次工具/模型调用记录 LineageNode | P1 |
| `trace_lineage_to_source()` | 向上递归追踪 | P1 |
| Freshness 检查 | 根据 Registry 的 `staleness_threshold_days` 判断 | P0 |
| Confidence 元数据 | 在 Registry 中声明 `determination_type` | P0 |
| Package 版本解析 | 简单的 SemVer 匹配 | P1 |

### 11.2 MVP 可以推迟

| 组件 | 推迟理由 |
|---|---|
| 完整 Lineage UI 展示 | 可在 Decision Trace UI (SPEC-008) 中统一处理 |
| 自动依赖解析器 | MVP 中依赖手动检查 |
| 多个 Package 版本共存 | MVP 只支持每个 Package 一个版本 |
| Capability Package 热更新 | MVP 通过重启加载 |
| 完整 `determination_type = llm_interpreted` 的 prompt_hash 追溯 | MVP 先记录 model_id + temperature |
| 跨能力域 lineage 间接污染检测 | 已知局限（见 SPEC-004 §26.1 NOTE），推迟到 SPEC-009 |

### 11.3 MVP Metric Registry 必须注册的指标

继承 SPEC-004 各能力域的 `constraint_exports` 声明，MVP 必须注册以下 metric：

**Fundamentals（P0 — 13 metrics）：**
```
metric://revenue_growth_ttm
metric://industry_median_revenue_growth_ttm
metric://gross_margin_ttm
metric://gross_margin_qoq_change
metric://operating_margin_ttm
metric://fcf_margin_ttm
metric://net_debt_to_ebitda
metric://roe_ttm
metric://roic_ttm
metric://pe_percentile_5y
metric://ev_ebitda_percentile_5y
metric://fcf_yield
metric://growth_capex_flag
```

**Macro / Meso（P0 — 5 metrics）：**
```
metric://policy_rate_change_6m
metric://real_yield_change_6m
metric://industry_capacity_utilization
metric://industry_capex_growth_yoy
metric://commodity_input_cost_change
```

**Company Event / Catalyst（P1 — 4 metrics）：**
```
metric://post_event_1d_return
metric://post_event_volume_vs_20d_average
metric://days_since_event
metric://event_frequency_90d
```

**Technical / Market（P1 — 8 metrics）：**
```
metric://rsi_14d
metric://price_above_50d_ma
metric://price_above_200d_ma
metric://volume_vs_20d_average
metric://atr_14d
metric://drawdown_from_52w_high
metric://average_dollar_volume_20d
metric://bid_ask_spread_proxy
```

**Sentiment（P1 — 3 metrics）：**
```
metric://bullish_ratio
metric://discussion_volume_zscore
metric://news_sentiment_score
```

### 11.4 MVP 必须注册的 Fact 和 Label

**Facts（P0 — 6 facts）：**
```
fact://retail_sentiment_overheated
fact://narrative_crowded_positive
fact://any_material_event_low_certainty
fact://latest_material_event_is_confirmed
fact://any_material_negative_event_unresolved
```

**Labels（P1 — 主要 labels）：**
```
label://industry_cycle_stage
label://valuation_state
label://market_regime
label://sentiment_state
label://narrative_state
label://trend_state
label://momentum_state
```

---

## 12. 实现参考：Capability Package 注册表最小结构

```json
{
  "package_registry_version": "0.1.0",
  "packages": {
    "pkg_fundamentals_financial_v1": {
      "package_id": "pkg_fundamentals_financial_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/fundamentals_financial_v1/",
      "checksum": "sha256:def456..."
    },
    "pkg_valuation_v1": {
      "package_id": "pkg_valuation_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/valuation_v1/"
    },
    "pkg_event_price_tracker_v1": {
      "package_id": "pkg_event_price_tracker_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/event_price_tracker_v1/"
    },
    "pkg_sentiment_social_v1": {
      "package_id": "pkg_sentiment_social_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/sentiment_social_v1/"
    },
    "pkg_technical_indicators_v1": {
      "package_id": "pkg_technical_indicators_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/technical_indicators_v1/"
    },
    "pkg_macro_metrics_v1": {
      "package_id": "pkg_macro_metrics_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/macro_metrics_v1/"
    },
    "pkg_industry_cycle_classifier_v1": {
      "package_id": "pkg_industry_cycle_classifier_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/industry_cycle_classifier_v1/"
    },
    "pkg_event_analyzer_v1": {
      "package_id": "pkg_event_analyzer_v1",
      "version": "0.1.0",
      "status": "active",
      "path": "./packages/event_analyzer_v1/"
    }
  },
  "data_connectors": {
    "conn_financial_data_api_v1": {
      "connector_id": "conn_financial_data_api_v1",
      "version": "0.2.0",
      "status": "active"
    },
    "conn_industry_benchmark_api_v1": {
      "connector_id": "conn_industry_benchmark_api_v1",
      "version": "0.1.0",
      "status": "active"
    }
  }
}
```

---

## 13. 关键设计原则总结

### 13.1 核心原则

```
Deterministic first, Agentic when necessary, Traceable always.
```

在 Capability Package 与 Metric Registry 层面的表达：

1. **确定性优先**：Computed metrics 的 confidence 默认为 1.0，公式公开可审计；Hard Constraint 默认只引用 Computed Evidence；
2. **Agentic 必要时用**：Structured 模型输出和 Interpreted LLM 推理只在 Soft Constraint 层面参与，且必须标记不确定性；
3. **始终可追踪**：每个 metric 从数据源到 Constraint Evaluation 的 lineage 必须完整记录。

### 13.2 设计约束链

```
Registry declares what metrics exist.
    ↓
Registry declares which are hard-capable.
    ↓
Domain packages produce evidence containing metrics.
    ↓
Domain cards export metrics via constraint_exports.
    ↓
Export metadata must match Registry declaration.
    ↓
Playbook Constraints reference exports.
    ↓
Rule engine validates reference against Registry.
    ↓
Lineage traces every value back to its source.
    ↓
Decision Trace preserves the full chain.
```

中文表达：

```
Registry 声明存在哪些指标；
Registry 声明哪些可支撑 Hard Constraint；
能力域 Package 生成包含指标的 Evidence；
能力域 Card 通过 constraint_exports 导出指标；
export 元数据必须与 Registry 声明一致；
Playbook Constraint 引用 export；
规则引擎根据 Registry 验证引用；
Lineage 将每个值追溯到数据源；
Decision Trace 保存完整链路。
```

### 13.3 不可绕过的硬约束

| # | 约束 | 来源 |
|---|---|---|
| 1 | Structured Evidence 默认不得直接支撑 Hard Constraint | SPEC-003 §12 |
| 2 | Interpreted Evidence 永远不得支撑 Hard Constraint | SPEC-003 §12 |
| 3 | `can_support_hard_constraint` 不得高于 Registry 声明 | SPEC-005 |
| 4 | `determinism_level` 不可升级 | SPEC-005 |
| 5 | Hard Constraint 输入仅限 `metric://` | SPEC-006 §18.1 |
| 6 | Lineage 断链阻止 Hard Constraint 引用 | SPEC-005 |
| 7 | `confidence` 的 `determination_type` 必须可追溯 | SPEC-003 §6.5 NOTE + SPEC-005 §8 |
| 8 | Computed Evidence 的 confidence 默认为 1.0（非 Computed 不得） | SPEC-005 §8.2 |

---

## 14. 后续 SPEC 依赖

SPEC-005 依赖和影响以下文档：

1. SPEC-003：Agentic 投研工作流架构（Evidence Packet 生成机制、Hard Constraint 确定性污染）；
2. SPEC-004：五类分析能力域（constraint_exports 多态结构、各能力域导出指标）；
3. SPEC-006：Investment Playbook 规范（input_refs 解析、Hard Constraint 规则、Playbook Applicability Evaluator）；
4. SPEC-007：Orchestration 与执行路径（Package 加载与能力域调度）；
5. SPEC-008：Decision Trace 与 Observability（Lineage UI 展示）；
6. SPEC-009：Governance、Guardrails、Evaluator 与人工介入（lineage 间接污染检测、confidence 跨域比较统一算法）；
7. SPEC-012：数据治理与用户私有数据；
8. SPEC-010：MVP 范围与验证指标（Metric Registry 的最小实现范围）；
9. SPEC-011：Case Library 与历史案例记忆（案例索引中引用 Metric 值）。

---

## 15. 开放问题

1. Metric Registry 的完整管理工具（CLI/API）是否需要独立 SPEC？
2. Capability Package 的沙箱执行环境（容器化/进程隔离）应在哪个 SPEC 定义？
3. 多个 Package 版本共存（例如同一能力域使用不同版本 Package 对比）是否进入 MVP？
4. ~~`metric://` URI 是否需要支持带版本号的形式（如 `metric://revenue_growth_ttm@0.1.0`）以支持多版本共存？~~ 已关闭。MVP 使用无版本号 URI（`metric://revenue_growth_ttm`）；版本号由 Registry 的 `registry_version` + Playbook 的 `dependency_snapshot_refs` 锁定，不在 URI 中表达。URI 格式见 §15.1。
5. ~~Derived Metric 的映射规则表是否需要独立可测试的规则文件格式？~~ 已关闭。Derived Metric 的映射规则使用声明式 JSON 规则表，格式见 §15.2。
6. Fact Registry 和 Label Registry 是否应拆分为独立 Registry 对象，还是合并进统一的 Metric Registry？

### 15.1 `metric://` / `fact://` / `label://` URI 格式规范

MVP 统一使用无版本号的 URI 格式。版本锁定由 Metric Registry 的 `registry_version` 字段和 Playbook 的 `dependency_snapshot_refs` 共同承担，不在 URI 中表达。

```
格式：
  metric://<metric_id>
  fact://<fact_id>
  label://<label_id>

约束：
  1. <metric_id> / <fact_id> / <label_id> 必须在对应的 Registry 中存在
  2. URI 大小写敏感，全部小写，使用下划线分隔
  3. 不接受 query string（?version=...）——版本锁定通过 Registry snapshot 实现
  4. 不接受 fragment（#suffix）——如需引用 metric 的子属性，使用 value_path 而非 URI fragment

示例：
  metric://revenue_growth_ttm
  metric://pe_percentile_5y
  fact://capital_cycle_expansion
  label://market_regime

有效来源：
  - Playbook Constraint.input_refs[] 中引用
  - Analysis Card.constraint_exports[].export_ref 中声明
  - Metric Registry.metrics.<id>.expected_export_ref 中注册

校验规则：
  1. Resolution: registry.resolve(uri) → MetricRegistryEntry | Error
  2. 未注册的 metric_id → resolution error，Constraint 标记为 INSUFFICIENT_DATA
  3. 已注册但 producing_package 版本与 Playbook dependency_snapshot 不匹配 → 标记为 INSUFFICIENT_DATA
```

### 15.2 Derived Metric 映射规则表格式

Derived Metric 的映射使用声明式 JSON 规则表，每条规则定义输入条件与输出值之间的确定性关系。

```json
{
  "rule_table_id": "rule_valuation_state_v1",
  "derived_metric_id": "valuation_state",
  "description": "将 PE 分位数映射为估值状态",
  "spec_version": "SPEC-005@0.1.0",
  "rules": [
    {
      "rule_id": "r001",
      "condition": {
        "input_ref": "metric://pe_percentile_5y",
        "operator": "gte",
        "value": 0.80
      },
      "output": {
        "fact_value": true,
        "label": "expensive"
      },
      "description": "PE 5年分位数 ≥ 80% → expensive"
    },
    {
      "rule_id": "r002",
      "condition": {
        "input_ref": "metric://pe_percentile_5y",
        "operator": "between",
        "value": [0.30, 0.80]
      },
      "output": {
        "fact_value": true,
        "label": "fair"
      },
      "description": "30% ≤ PE 分位数 < 80% → fair"
    },
    {
      "rule_id": "r003",
      "condition": {
        "input_ref": "metric://pe_percentile_5y",
        "operator": "lt",
        "value": 0.30
      },
      "output": {
        "fact_value": true,
        "label": "cheap"
      },
      "description": "PE 分位数 < 30% → cheap"
    }
  ],
  "default_output": {
    "fact_value": false,
    "label": "unavailable"
  },
  "determinism_level": "computed",
  "confidence_rule": "inherit_min",
  "test_cases": [
    {
      "input": {"metric://pe_percentile_5y": 0.85},
      "expected_output": {"label": "expensive", "fact_value": true}
    },
    {
      "input": {"metric://pe_percentile_5y": 0.50},
      "expected_output": {"label": "fair", "fact_value": true}
    },
    {
      "input": {"metric://pe_percentile_5y": 0.15},
      "expected_output": {"label": "cheap", "fact_value": true}
    },
    {
      "input": {"metric://pe_percentile_5y": null},
      "expected_output": {"label": "unavailable", "fact_value": false}
    }
  ]
}
```

规则表约束：
1. 规则按 rule_id 顺序匹配，**首匹配短路**（first-match wins）
2. `operator` 支持: `eq`, `neq`, `gt`, `gte`, `lt`, `lte`, `between`, `in`, `not_in`
3. `between` 的 value 为 `[lower, upper)`，左闭右开
4. 输入为 null 时不匹配任何规则，返回 `default_output`
5. `test_cases` 为强制项——每条规则表必须附带至少覆盖所有 rule_id 的边界测试
6. Derived Metric 的 confidence 继承所有输入 metric 的最小 confidence（`confidence_rule = "inherit_min"`）

> **已关闭的 SPEC-005 开放问题 #5：** Derived Metric 的映射规则表使用上述 JSON 格式，可独立测试、可版本化、可审计。

---

## 16. v0.1 总结

SPEC-005 v0.1 建立了 Capability Package 与 Metric Registry 的核心定义。

本版本完成以下约束：

1. Capability Package 作为工具/模型/数据连接器的打包与版本管理单元；
2. Capability Package Schema 定义（dependencies、capabilities、lineage_config）；
3. Metric Registry Schema（metric_id → evidence_value_path + freshness + confidence 元数据）；
4. Computed / Derived / Structured / Interpreted Metric 的四层分类体系；
5. 工具调用链 Lineage 追踪机制（LineageNode → trace_lineage_to_source）；
6. Metric → constraint_exports 的映射构建与一致性校验；
7. Confidence 传播链与 `determination_type` 的五类枚举；
8. Package 版本管理（SemVer）与 Playbook 兼容性检查；
9. 与 SPEC-004（能力域）和 SPEC-006（Playbook）的接口契约；
10. MVP 最小实现范围（33 metrics + 6 facts + 7 labels）；
11. 8 条不可绕过的硬约束，确保确定性优先原则在实现层落地。

SPEC-005 的核心设计原则是：

```
Package provides capability.
Registry declares metrics.
Domain exports evidence.
Constraint resolves references.
Lineage preserves the chain.
Decision Trace keeps accountability.
```

中文表达：

```
Package 提供能力；
Registry 声明指标；
Domain 导出证据；
Constraint 解析引用；
Lineage 保存链路；
Decision Trace 维持责任。
```
