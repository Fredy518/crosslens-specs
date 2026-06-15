# SPEC-013 v0.1.2 审查修复

## 项目位置

```
E:\CodePrograms\CrossLens\crosslens-specs
```

目标文件：`SPEC-013 Fundamentals 域实现规格 v0.1.md`（当前 1498 行，最新 commit `b6e8922`）

---

## 执行方式：Team Agents

使用 team agents 模式。主 agent 负责任务分配、工作整合和最终汇报，子 agents 并行执行具体任务。

### 主 Agent 职责

1. 读取目标文件 `SPEC-013 Fundamentals 域实现规格 v0.1.md` 全文建立理解
2. 将 3 个 Task 分配给子 agents（可全部并行，互不冲突）
3. 子 agents 完成后：
   - 通读修改后的文件确认一致性
   - 运行全量测试确认无回归：`for d in spec003 spec004 spec005 spec006 spec009; do cd executable_specs/$d && python -m pytest -q && cd ../..; done`
   - 整合为一次 commit，commit message：`fix: SPEC-013 v0.1.2 — review fixes (fcf_yield, stance thresholds, variable names, validation clarity)`
4. 向用户汇报（见底部汇报模板）

### 全局约束

- **只修改一个文件**：`SPEC-013 Fundamentals 域实现规格 v0.1.md`
- **不修改任何上游 SPEC**（SPEC-003/004/005/006/007/009）
- **不修改 SPEC-REGISTRY.md**
- **不修改任何代码文件**（models.py, tests/ 等）
- **不创建新文件**

---

## Task 1：P0 必修 — fcf_yield 定义修复

**来源**：代码审查发现的 2 个必修问题。

### 1.1 JSON 语法错误（全角括号）

**位置**：§4.2 `metric://fcf_yield` 的 Metric Registry JSON 条目中，`description` 字段。

**当前文本**：
```
"description": "Derived metric: 需要 cashflow_metrics + market_data 两个 source Evidence）"
```

**问题**：末尾有一个孤立的全角右括号 `）`，没有对应的左括号。

**修复**：删除全角右括号，改为：
```
"description": "TTM FCF / 市值。Derived metric：FCF 来自 cashflow_metrics，市值来自 market_data（行情 API）。衡量以当前价格买入时，公司产生自由现金流的回报率。"
```

### 1.2 fcf_yield 在 §3.2 中重复定义

**问题**：`fcf_yield` 同时出现在：
- §3.2.4 cashflow_metrics 的 metrics 表（约第 198 行）
- §3.2.6 valuation_metrics 的 metrics 表（约第 252 行）

但 §4.1 汇总表（第 413 行）标注它为 `derived`（来源 `cashflow_metrics + market_data`），意味着它不是任何一个 Evidence Packet 类型的原生字段。

**修复方案**：

1. 在 §3.2.4 cashflow_metrics 的 metrics 表中，将 `fcf_yield` 行的说明改为：
```
| `fcf_yield` | float | ratio | FCF / Market Cap（**derived**：跨 Evidence，详见 §4.2 metric://fcf_yield） |
```

2. 在 §3.2.6 valuation_metrics 的 metrics 表中，将 `fcf_yield` 行的说明改为：
```
| `fcf_yield` | float | ratio | FCF / Market Cap（**derived**：跨 Evidence，详见 §4.2 metric://fcf_yield） |
```

3. 在两处都添加行内注释，说明这是"引用标记"而非"原生字段"：
```
// NOTE: fcf_yield 是 derived metric，不归属于单一 Evidence Packet 类型。
// 此处列出仅为完整性索引，实际计算和导出规则见 §4.2。
```

---

## Task 2：P1 关注 — Stance 阈值边界 + Confidence 来源标注

### 2.1 Stance §7.2 阈值边界显式化

**位置**：§7.2 的 score → stance 映射伪代码。

**当前文本**（约第 1276~1285 行）：
```
if score > 0.40:  stance = "positive"
elif score > 0.15: stance = "moderately_positive"
elif score > -0.15: stance = "neutral"
elif score > -0.40: stance = "moderately_negative"
else: stance = "negative"
```

**问题**：边界值 0.40、0.15、-0.15、-0.40 的归属已通过 `>` / `elif` 隐式确定，但未显式列出边界表。对单元测试来说，需要明确 `score = 0.40` 时输出什么。

**修复**：在伪代码之后添加边界值表：

```markdown
**边界值定义：**

| score 范围 | stance | 边界归属 |
|-----------|--------|---------|
| score > 0.40 | positive | 0.40 不包含（归 moderately_positive） |
| 0.15 < score ≤ 0.40 | moderately_positive | 0.40 inclusive 下界, 0.15 exclusive |
| -0.15 < score ≤ 0.15 | neutral | 两端均 exclusive |
| -0.40 < score ≤ -0.15 | moderately_negative | -0.15 inclusive 下界, -0.40 exclusive |
| score ≤ -0.40 | negative | -0.40 inclusive |
```

> 注意：上面的边界值表必须与伪代码逻辑完全一致。如果伪代码用 `>` 则边界值 exclusive，用 `>=` 则 inclusive。请仔细核对。

### 2.2 Confidence 截断 §8.3 来源标注

**位置**：§8.3 最终截断。

**当前文本**（约第 1352~1355 行）：
```
confidence = min(confidence, confidence_cap_from_quality(data_quality))
// data_quality 到 cap 的映射见 SPEC-004 §41:
//   high → 0.85, medium → 0.70, low → 0.45, unavailable → 0.20, unknown → 0.50
```

**问题**：这个映射声称来自 "SPEC-004 §41"，但 SPEC-004 §41 定义的是质量检查规则，不是 confidence cap 映射。如果这个映射是 SPEC-013 自定义的，应该明确标注。

**修复**：将注释改为：

```
confidence = min(confidence, confidence_cap_from_quality(data_quality))
// data_quality → confidence cap 映射（SPEC-013 自定义，待与 SPEC-004/009 对齐）：
//   high → 0.85, medium → 0.70, low → 0.45, unavailable → 0.20, unknown → 0.50
// 注意：此映射目前仅在 SPEC-013 中定义。如果 SPEC-004 或 SPEC-009 后续定义了
// 全局统一的 data_quality → confidence_cap 映射，本映射应被替换。
```

同时在 §12 开放问题中添加一条：

```markdown
6. **data_quality → confidence_cap 映射统一化**：§8.3 的映射为 SPEC-013 自定义。需与 SPEC-004 §41 和 SPEC-009 确认是否需要全局统一的 data_quality → confidence_cap 规则。若需要，应提升为上游 SPEC 的规范性定义。
```

---

## Task 3：P2 小修 — 变量名统一 + 验证条件澄清

### 3.1 Pipeline Step 7 残留变量名

**位置**：§5 Internal Pipeline 的 Step 7 Card Assembly 伪代码。

**当前文本**（约第 1148 行）：
```
        warnings=derive_warnings(missing_required, evidence_packets)
```

**问题**：b6e8922 已将大部分 `evidence_packets` 替换为 `available_evidence`，但此处遗漏。

**修复**：改为：
```
        warnings=derive_warnings(missing_required, available_evidence)
```

### 3.2 §10 检查项 #4 触发条件澄清

**位置**：§10 Domain Validation 表格第 4 行。

**当前文本**：
```
| 4 | 收入增速与行业增速同源 | revenue_growth_ttm 和 industry_median 来自同一 Evidence Packet | flag | 标记 lineage 风险，加入 warnings |
```

**问题**：`revenue_growth_ttm` 来自 `financial_metrics`，`industry_median_revenue_growth_ttm` 来自 `peer_comparison_metrics`——它们来自不同的 Evidence Packet 类型。正常情况下不会"来自同一个 Evidence Packet"。

**修复**：将触发条件改为更精确的描述：
```
| 4 | 收入增速与行业增速 lineage 异常 | peer_comparison_metrics 的 industry_median 不是来自独立的行业数据库，而是从公司自身 filing 推导（即 financial_metrics 和 peer_comparison_metrics 共享同一个原始数据源） | flag | 标记 lineage 风险，加入 warnings: "peer_data_not_independent" |
```

---

## 验收标准

- [ ] fcf_yield Metric Registry JSON 中无全角括号
- [ ] §3.2.4 和 §3.2.6 中 fcf_yield 标注为 derived + 引用 §4.2
- [ ] §7.2 有边界值表，且与伪代码逻辑一致
- [ ] §8.3 的 data_quality → cap 映射标注为 SPEC-013 自定义
- [ ] §12 开放问题新增第 6 条
- [ ] §5 Pipeline 中无残留 `evidence_packets` 变量名
- [ ] §10 检查项 #4 触发条件已澄清
- [ ] 全量测试无回归（197 tests all green）
- [ ] 不修改任何上游 SPEC
- [ ] 不修改 SPEC-REGISTRY.md
- [ ] 不修改任何代码文件

---

## 向用户汇报模板

```markdown
## SPEC-013 v0.1.2 修复报告

### Task 1（P0 必修）
- fcf_yield JSON 语法错误：[已修复 / 说明]
- fcf_yield 重复定义：[已修复 / 说明]

### Task 2（P1 关注）
- Stance 阈值边界表：[已添加 / 说明]
- Confidence cap 来源标注：[已修正 / 说明]
- §12 开放问题 #6：[已添加]

### Task 3（P2 小修）
- Pipeline 变量名统一：[已修复]
- §10 检查项 #4 澄清：[已修正]

### 测试结果
- spec003: X tests passed
- spec004: X tests passed
- spec005: X tests passed
- spec006: X tests passed
- spec009: X tests passed
- Total: X tests, all green

### 文件变更
- 仅修改：SPEC-013 Fundamentals 域实现规格 v0.1.md
- 上游 SPEC：未修改
- Registry：未修改

### 下一步建议
- SPEC-013 可升级为 Review 状态
- 可编写 plan/tasks-fundamentals.md 进入编码阶段
```
