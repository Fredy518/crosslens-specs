# URI Resolution Specification

> 本文件定义 CrossLens 中 Playbook Constraint `input_refs` 使用的三种 URI 引用格式的解析与解析规范。
>
> 规范性范围：URI 解析规则、验证规则、错误处理语义、解析元数据 schema。
>
> 上游定义：SPEC-003 §11（Playbook Constraint 与 input_refs）、SPEC-005 §15.1（`metric://` / `fact://` / `label://` URI 格式规范）、SPEC-006（Playbook Constraint 执行语义）。
>
> 实现：`executable_specs/spec003/src/crosslens_spec003/uri_resolver.py`

---

## 1. Evidence URI

### 1.1 Format

```text
evidence://{evidence_id}/{value_path}
```

| 组成部分 | 约束 | 示例 |
|----------|------|------|
| `evidence_id` | 非空字符串，允许字母数字 + 下划线 + 连字符 | `ev_financial_001` |
| `value_path` | 点分隔路径，指向 EvidencePacket 内部字段 | `metrics.revenue_growth_ttm` |

### 1.2 Value Path Semantics

`value_path` 使用 dot-notation 访问 EvidencePacket 的嵌套字段：

- `metrics.revenue_growth_ttm` — 访问 `EvidencePacket.metrics["revenue_growth_ttm"]`
- `facts.0` — 访问 `EvidencePacket.facts[0]`
- `labels.sector` — 访问 `EvidencePacket.labels["sector"]`

### 1.3 Parsing Algorithm

```text
function parse_evidence_uri(uri: string) -> (evidence_id, value_path):

    // Step 1: Validate prefix
    if not uri.startswith("evidence://"):
        raise URIParseError("URI does not start with evidence://")

    // Step 2: Extract remainder
    remainder = uri[len("evidence://"):]

    // Step 3: Split on first "/" to get evidence_id and value_path
    first_slash = remainder.find("/")
    if first_slash == -1:
        // No value_path present — error
        raise URIParseError("evidence:// URI must contain value_path: evidence://<evidence_id>/<value_path>")

    evidence_id = remainder[0:first_slash]
    value_path = remainder[first_slash + 1:]

    // Step 4: Validate evidence_id non-empty
    if evidence_id is empty or only whitespace:
        raise URIParseError("evidence_id must be non-empty")

    // Step 5: Validate value_path non-empty
    if value_path is empty or only whitespace:
        raise URIParseError("value_path must be non-empty")

    // Step 6: Validate evidence_id characters
    if not evidence_id matches /^[a-zA-Z0-9_-]+$/:
        raise URIParseError("evidence_id contains invalid characters")

    return (evidence_id, value_path)
```

### 1.4 Error Handling

| 条件 | 结果 |
|------|------|
| evidence_id 为空 | `URIParseError` |
| value_path 为空 | `URIParseError` |
| evidence_id 含非法字符 | `URIParseError` |
| 缺少 value_path（无 `/` 分隔） | `URIParseError` |
| URI 不以 `evidence://` 开头 | `URIParseError` |
| evidence_id 对应 Evidence Packet 不存在 | `URIResolutionError("insufficient_data")` — 由解析层处理 |

### 1.5 Return Value

解析层返回 `EvidenceURI(evidence_id, value_path)`。完整解析（lookup 实际值）由编排层实现。

---

## 2. Metric URI

### 2.1 Format

```text
metric://{metric_id}
```

| 组成部分 | 约束 | 示例 |
|----------|------|------|
| `metric_id` | 非空字符串，匹配 Metric Registry 条目 | `revenue_growth_ttm` |

### 2.2 Parsing Algorithm

```text
function parse_metric_uri(uri: string) -> metric_id:

    // Step 1: Validate prefix
    if not uri.startswith("metric://"):
        raise URIParseError("URI does not start with metric://")

    // Step 2: Extract metric_id
    metric_id = uri[len("metric://"):]

    // Step 3: Validate non-empty
    if metric_id is empty or only whitespace:
        raise URIParseError("metric_id must be non-empty")

    // Step 4: Validate no path separators (metric URI has no sub-path)
    if "/" in metric_id:
        raise URIParseError("metric:// URI must not contain path separators")

    return metric_id
```

### 2.3 Error Handling

| 条件 | 结果 |
|------|------|
| metric_id 为空 | `URIParseError` |
| metric_id 含 `/` | `URIParseError` |
| URI 不以 `metric://` 开头 | `URIParseError` |
| metric_id 未在 Metric Registry 中注册 | `URIResolutionError("insufficient_data")` — 由解析层处理 |

### 2.4 Interaction with SPEC-005 Metric Registry

Metric URI 的完整解析需要 Metric Registry 支持：

1. 解析层提取 `metric_id`
2. 解析层查询 Metric Registry，将 `metric_id` 映射为 `(evidence_id, value_path, confidence metadata)`
3. 解析层从 Evidence Packet 获取实际值

Metric Registry 的最小 MVP 形态是一个静态 JSON 映射表（见 SPEC-003 §11.3，SPEC-005 §5.2）。

### 2.5 Return Value

解析层返回 `metric_id` 字符串。完整解析（lookup Metric Registry + Evidence Packet 值）由编排层实现。

---

## 3. Constraint URI

### 3.1 Format

```text
constraint://{playbook_id}/{version}/{constraint_id}
```

| 组成部分 | 约束 | 示例 |
|----------|------|------|
| `playbook_id` | 非空字符串 | `capital_cycle_fundamental_playbook` |
| `version` | semver-like 版本号（如 `0.1.0`） | `0.1.0` |
| `constraint_id` | 非空字符串 | `growth_001` |

### 3.2 Parsing Algorithm

```text
function parse_constraint_uri(uri: string) -> (playbook_id, version, constraint_id):

    // Step 1: Validate prefix
    if not uri.startswith("constraint://"):
        raise URIParseError("URI does not start with constraint://")

    // Step 2: Extract remainder
    remainder = uri[len("constraint://"):]

    // Step 3: Split on "/" — expect exactly 3 parts
    parts = remainder.split("/")
    if len(parts) != 3:
        raise URIParseError(
            "constraint:// URI must have exactly 3 path segments: "
            "constraint://<playbook_id>/<version>/<constraint_id>"
        )

    playbook_id, version, constraint_id = parts[0], parts[1], parts[2]

    // Step 4: Validate all parts non-empty
    if playbook_id is empty or only whitespace:
        raise URIParseError("playbook_id must be non-empty")
    if version is empty or only whitespace:
        raise URIParseError("version must be non-empty")
    if constraint_id is empty or only whitespace:
        raise URIParseError("constraint_id must be non-empty")

    return (playbook_id, version, constraint_id)
```

### 3.3 Error Handling

| 条件 | 结果 |
|------|------|
| 任何一个部分为空 | `URIParseError` |
| 分割后不足 3 个部分 | `URIParseError` |
| 分割后超过 3 个部分 | `URIParseError` |
| URI 不以 `constraint://` 开头 | `URIParseError` |
| Constraint 在 Playbook 中不存在 | `URIResolutionError("insufficient_data")` — 由解析层处理 |

### 3.4 Return Value

解析层返回 `ConstraintURI(playbook_id, version, constraint_id)`。完整解析（lookup Playbook Constraint 定义）由编排层实现。

---

## 4. General Resolution Protocol

### 4.1 Resolution Chain

```text
Input: URI string

1. classify_uri(uri)        → scheme: "evidence" | "metric" | "constraint"
2. dispatch to parser       → parse_{scheme}_uri(uri)
3. validate format          → raise URIParseError on malformed URI
4. resolve references       → lookup entity in respective registry/store
5. fetch value              → extract actual value from resolved entity
6. return                   → (value, metadata) or error

Each step may produce:
  - URIParseError: URI is syntactically invalid
  - URIResolutionError: URI is valid but entity not found → maps to insufficient_data
  - (value, metadata): successful resolution
```

### 4.2 Resolution Metadata

每当解析成功，返回的元数据必须包含：

| 字段 | 类型 | 来源 | 说明 |
|------|------|------|------|
| `evidence_id` | `str` | EvidencePacket | 证据来源标识 |
| `source_name` | `str` | EvidencePacket | 数据源名称 |
| `source_type` | `str` | EvidencePacket | 数据源类型 |
| `generation_type` | `GenerationType` | EvidencePacket | 生成方式 |
| `determinism_level` | `DeterminismLevel` | EvidencePacket | 确定性级别 |
| `data_quality` | `DataQuality` | EvidencePacket | 数据质量 |
| `as_of` | `date \| None` | EvidencePacket | 数据截至日期 |
| `freshness_level` | `str` | Metric Registry | 新鲜度 |
| `confidence` | `float \| None` | EvidencePacket | 置信度 (0.0-1.0) |

### 4.3 URI Classification

```text
function classify_uri(uri: string) -> scheme:

    for scheme in ["evidence://", "metric://", "constraint://"]:
        if uri.startswith(scheme):
            return scheme without "://"

    raise URIParseError(f"Unknown URI scheme in: {uri}")
```

---

## 5. Error Type Hierarchy

```text
URIError (base)
  ├── URIParseError       — URI 格式无效（语法错误）
  └── URIResolutionError  — URI 格式有效但引用实体不可解析（语义错误）
```

| 错误类型 | 触发条件 | 下游处理 |
|----------|----------|----------|
| `URIParseError` | 格式不合法、必需部分为空 | 终止当前 Constraint 评估，记录 error |
| `URIResolutionError` | 实体未找到 | 将 Constraint 状态设为 `insufficient_data`，触发 `on_insufficient_data` 路径 |

---

## 6. 规范性引用

| 引用 | 位置 |
|------|------|
| Evidence URI 定义 | SPEC-003 §11.1 |
| Metric URI 定义 | SPEC-003 §11.1, SPEC-005 §15.1 |
| Constraint URI 定义 | SPEC-003 §11, SPEC-006 |
| 引用解析要求 | SPEC-003 §11.2 |
| Metric Registry | SPEC-005 §5.2 |
| Playbook Constraint 执行 | SPEC-006 |
| URI 格式规范（metric/fact/label） | SPEC-005 §15.1 |
