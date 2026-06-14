# SPEC-011：Case Library 与历史案例记忆

**版本：** v0.1
**状态：** Draft
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4；SPEC-012 v0.1
**文档类型：** 案例管理规范
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 1. 文档目标

SPEC-011 定义 crosslens 的 Case Library（案例库）结构和历史案例记忆机制，重点回答：

1. Case 是什么，包含哪些数据；
2. Case 如何存储和索引；
3. 案例检索与相似匹配算法；
4. Case Library 与用户隐私的边界；
5. 匿名化规则；
6. MVP 阶段的最小实现范围；
7. 与 SPEC-012（数据治理）的接口契约。

本 SPEC 不定义：

1. 具体数据库选型或存储引擎；
2. 案例库 UI 展示；
3. 案例驱动的自动决策建议（MVP 不实现）；
4. 跨用户案例聚合分析；
5. 案例回测或绩效归因。

---

## 2. Case 的定义

### 2.1 一句话定义

> **Case = 一次完整 Run 的不可变快照。**

### 2.2 Case 的构成

一个 Case 是一次 `single_stock_standard_analysis_workflow`（或未来其他 Workflow）从 `run_started` 到 `run_completed`（或 `run_failed`/`analysis_incomplete`）的完整记录。

Case **包含**：

1. **Investment Task** — 原始任务的标准化表达（SPEC-003 §6.1）；
2. **所有 Analysis Cards** — 五个能力域返回的分析卡片（SPEC-003 §10）；
3. **Playbook Evaluation Report** — Playbook 条件评估结果（SPEC-003 §15）；
4. **Decision Candidate** — 系统生成的投资判断候选（SPEC-003 §18）；
5. **Decision Trace** — 面向用户的投研证据链（SPEC-003 §19）；
6. **Run-level Metadata** — 运行时间、状态、Playbook 版本等。

Case **不包含**（硬规则）：

1. 用户的私有数据（`user_private`），包括持仓、笔记、反馈——除非用户显式授权且经匿名化；
2. 未授权的 `system_generated` 数据；
3. 用户的 `user_feedback` 具体内容。

### 2.3 Case 的不可变性

```
┌──────────────────────────────────────────────┐
│              Case 不可变性规则                  │
├──────────────────────────────────────────────┤
│  1. Case 一旦写入，永不修改。                    │
│  2. 如果同一 task_id 多次执行，每次 Run 生成     │
│     独立的 Case（以 run_id 区分）。              │
│  3. 用户数据删除时，已入库 Case 不受影响          │
│     （匿名化后已切断与用户的关联）。              │
│  4. Case 的删除权限归属系统管理员，               │
│     用户无权直接删除公共案例库中的 Case。          │
└──────────────────────────────────────────────┘
```

---

## 3. Case 完整 Schema

### 3.1 顶层结构

```json
{
  "case_id": "case_nvda_20260614_001",
  "case_version": "1.0",

  "run": {
    "run_id": "run_001",
    "task_id": "task_001",
    "workflow_name": "single_stock_standard_analysis_workflow",
    "run_status": "completed",
    "started_at": "2026-06-14T10:30:00Z",
    "completed_at": "2026-06-14T10:35:00Z",
    "duration_ms": 300000
  },

  "task": {
    "task_type": "single_stock_buy_decision",
    "asset": {
      "symbol": "NVDA",
      "asset_type": "stock",
      "market": "US"
    },
    "ticker": "NVDA",
    "user_intent": "whether_to_buy",
    "time_horizon": "3-6 months",
    "playbook_id": "capital_cycle_fundamental_playbook",
    "playbook_version": "0.1.0",
    "depth": "standard",
    "risk_preference": "medium",
    "created_at": "2026-06-14T00:00:00Z"
  },

  "playbook": {
    "playbook_id": "capital_cycle_fundamental_playbook",
    "playbook_version": "0.1.0",
    "playbook_source": "built_in_static",
    "playbook_snapshot_hash": "sha256:abc123..."
  },

  "analysis_cards": [
    {
      "card_id": "card_fundamentals_001",
      "domain": "fundamentals",
      "domain_status": "completed",
      "stance": "moderately_positive",
      "confidence": 0.66,
      "data_quality": "medium",
      "summary": "基本面偏正面，但估值压力较高。"
    }
  ],

  "playbook_evaluation": {
    "playbook_evaluation_report_id": "pbe_001",
    "overall_result": "not_passed_for_new_buy",
    "recommended_decision_bounds": [
      "wait",
      "add_to_watchlist",
      "hold_if_already_owned"
    ],
    "blocking_conditions": [
      "估值安全边际不足"
    ]
  },

  "decision": {
    "decision_candidate_id": "dc_001",
    "suggested_action": "wait",
    "confidence": 0.58
  },

  "trace_summary": {
    "decision_trace_version": "1.0",
    "total_evidence_packets": 12,
    "total_analysis_cards": 5,
    "total_validation_findings": 3,
    "total_conflicts": 1,
    "guardrail_triggered": true,
    "requires_human_review": false
  },

  "index": {
    "ticker": "NVDA",
    "task_type": "single_stock_buy_decision",
    "playbook_id": "capital_cycle_fundamental_playbook",
    "date": "2026-06-14",
    "outcome": {
      "suggested_action": "wait",
      "overall_result": "not_passed_for_new_buy"
    }
  },

  "anonymization": {
    "applied": true,
    "applied_at": "2026-06-14T10:36:00Z",
    "rules_version": "1.0",
    "removed_fields": [
      "user_id",
      "user_private_data_refs",
      "user_feedback_content"
    ]
  },

  "provenance": {
    "source_run_id": "run_001",
    "source_task_id": "task_001",
    "contributed_by_user_id_hash": "sha256:salted_user_abc",
    "contribution_authorized_at": "2026-06-14T00:05:00Z",
    "authorization_scope": "case_library_contribution"
  }
}
```

### 3.2 字段说明

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `case_id` | string | 是 | 全局唯一，格式 `case_{ticker}_{date}_{seq}` |
| `case_version` | string | 是 | Case schema 版本 |
| `run` | object | 是 | Run 级摘要（run_status, duration, timestamps） |
| `task` | object | 是 | 任务的去私有化版本（不含 `uses_user_private_data` 和 `user_private_data_types`） |
| `playbook` | object | 是 | Playbook 标识与版本快照 |
| `analysis_cards` | array | 是 | 所有能力域 Analysis Card 的摘要（至少包含 domain, stance, confidence, data_quality） |
| `playbook_evaluation` | object | 是 | Playbook Evaluation Report 摘要 |
| `decision` | object | 是 | Decision Candidate 摘要（suggested_action + confidence） |
| `trace_summary` | object | 是 | Decision Trace 的统计摘要，不包含完整 Trace 正文 |
| `index` | object | 是 | 扁平化索引字段，用于检索 |
| `anonymization` | object | 是 | 匿名化处理记录 |
| `provenance` | object | 是 | 来源追溯（含匿名化的 contributor hash） |

---

## 4. Case 存储与索引

### 4.1 存储结构

```text
Case Library 存储布局
═══════════════════════════════════════════════

/case-library/
├── cases/
│   ├── {ticker}/
│   │   ├── {date}/
│   │   │   ├── {case_id}.json          ← 完整 Case JSON
│   │   │   └── {case_id}.checksum      ← 完整性校验
│   │   └── ...
│   └── ...
├── indices/
│   ├── by_ticker.json                   ← ticker → [case_id, ...]
│   ├── by_task_type.json                ← task_type → [case_id, ...]
│   ├── by_playbook.json                 ← playbook_id → [case_id, ...]
│   ├── by_date.json                     ← date → [case_id, ...]
│   └── by_outcome.json                  ← suggested_action → [case_id, ...]
└── metadata/
    ├── case_count.json                  ← 按维度统计
    └── last_updated.json                ← 最后更新时间
```

### 4.2 索引维度

| 索引维度 | 索引键 | 类型 | 说明 |
|---|---|---|---|
| Ticker | `index.ticker` | string | 股票代码，如 NVDA |
| Task Type | `task.task_type` | string | 任务类型枚举 |
| Playbook | `playbook.playbook_id` | string | 使用的 Playbook ID |
| Date | `run.started_at` | date | Run 启动日期 |
| Outcome | `decision.suggested_action` | string | 建议动作 |
| Overall Result | `playbook_evaluation.overall_result` | string | Playbook 评估总体结果 |

### 4.3 索引更新策略

```
Case 写入 → 同步更新所有相关索引
  ├── by_ticker:    追加 case_id 到 ticker 列表
  ├── by_task_type: 追加 case_id 到 task_type 列表
  ├── by_playbook:  追加 case_id 到 playbook 列表
  ├── by_date:      追加 case_id 到 date 列表
  └── by_outcome:   追加 case_id 到 outcome 列表
```

---

## 5. 案例检索与相似匹配

### 5.1 检索流程图

```text
                        ┌──────────────────────┐
                        │  接收检索请求          │
                        │  query = {            │
                        │    ticker,            │
                        │    task_type,         │
                        │    playbook_id,       │
                        │    date_range?,        │
                        │    outcome_filter?,    │
                        │    limit              │
                        │  }                    │
                        └──────────┬───────────┘
                                   │
                                   ▼
                  ┌────────────────────────────────┐
                  │  Step 1: 精确匹配过滤            │
                  │  candidates = []               │
                  │  IF query.ticker:              │
                  │    candidates = by_ticker[t]    │
                  │  IF query.task_type:           │
                  │    candidates &= by_task_type   │
                  │  IF query.playbook_id:          │
                  │    candidates &= by_playbook    │
                  └──────────────┬─────────────────┘
                                 │
                                 ▼
                  ┌────────────────────────────────┐
                  │  Step 2: 范围过滤               │
                  │  IF query.date_range:          │
                  │    candidates = filter_date()   │
                  │  IF query.outcome_filter:       │
                  │    candidates = filter_outcome()│
                  └──────────────┬─────────────────┘
                                 │
                                 ▼
                  ┌────────────────────────────────┐
                  │  Step 3: 相似度评分             │
                  │  FOR each candidate:           │
                  │    score = compute_similarity(  │
                  │      query, candidate           │
                  │    )                            │
                  └──────────────┬─────────────────┘
                                 │
                                 ▼
                  ┌────────────────────────────────┐
                  │  Step 4: 排序 + 截断            │
                  │  ranked = sort(candidates,      │
                  │    key=score, reverse=True)     │
                  │  RETURN ranked[:limit]          │
                  └────────────────────────────────┘
```

### 5.2 相似度评分伪代码

```python
# ============================================================
# SPEC-011 案例相似度评分算法 v0.1
# ============================================================

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

class MatchDimension(Enum):
    """匹配维度及其权重"""
    TICKER_EXACT       = 0.30   # 同 ticker 精确匹配
    PLAYBOOK_EXACT     = 0.20   # 同 playbook 精确匹配
    TASK_TYPE_EXACT    = 0.15   # 同 task_type 精确匹配
    OUTCOME_SIMILAR    = 0.15   # 结果相似度
    DATE_PROXIMITY     = 0.10   # 时间接近度
    CONFIDENCE_SIMILAR = 0.05   # 置信度相似度
    DATA_QUALITY_SIMILAR = 0.05 # 数据质量相似度

WEIGHTS = {d: d.value for d in MatchDimension}
assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001


@dataclass
class CaseQuery:
    """检索请求"""
    ticker: str
    task_type: str
    playbook_id: str
    date: datetime | None = None
    suggested_action: str | None = None
    limit: int = 10


def compute_similarity(query: CaseQuery, case: dict) -> float:
    """
    计算 query 与 case 的相似度，返回 0.0 ~ 1.0。
    MVP 版本使用加权线性组合，不涉及向量嵌入或语义匹配。
    """
    score = 0.0

    # ── Dimension 1: Ticker 精确匹配 (weight: 0.30) ──
    if query.ticker == case["index"]["ticker"]:
        score += WEIGHTS[MatchDimension.TICKER_EXACT]
    # ticker 不匹配直接返回 0（MVP 阶段不跨股票匹配）
    else:
        return 0.0

    # ── Dimension 2: Playbook 精确匹配 (weight: 0.20) ──
    if query.playbook_id == case["playbook"]["playbook_id"]:
        score += WEIGHTS[MatchDimension.PLAYBOOK_EXACT]

    # ── Dimension 3: Task Type 精确匹配 (weight: 0.15) ──
    if query.task_type == case["task"]["task_type"]:
        score += WEIGHTS[MatchDimension.TASK_TYPE_EXACT]

    # ── Dimension 4: 结果相似度 (weight: 0.15) ──
    score += WEIGHTS[MatchDimension.OUTCOME_SIMILAR] * _outcome_similarity(
        query.suggested_action,
        case["decision"]["suggested_action"]
    )

    # ── Dimension 5: 日期接近度 (weight: 0.10) ──
    score += WEIGHTS[MatchDimension.DATE_PROXIMITY] * _date_proximity(
        query.date,
        case["run"]["started_at"]
    )

    # ── Dimension 6: 置信度相似度 (weight: 0.05) ──
    # query 本身没有 confidence，此维度在 query 侧为 0；
    # 用于 case-vs-case 比较时才有值。
    score += WEIGHTS[MatchDimension.CONFIDENCE_SIMILAR] * _confidence_similarity(
        None,  # query 无 confidence
        case["decision"]["confidence"]
    )

    # ── Dimension 7: 数据质量相似度 (weight: 0.05) ──
    score += WEIGHTS[MatchDimension.DATA_QUALITY_SIMILAR] * _data_quality_similarity(
        None,  # query 无 data_quality
        case.get("trace_summary", {})
    )

    return round(score, 4)


def _outcome_similarity(
    query_action: str | None,
    case_action: str
) -> float:
    """
    Outcome 相似度映射表。
    基于动作语义距离而非字符串匹配。
    """
    if query_action is None:
        return 0.5  # 无倾向时为中性

    # 动作语义分组
    ACTION_GROUPS = {
        "positive": {"buy", "strong_buy", "add_position"},
        "neutral":  {"hold", "wait", "hold_if_already_owned"},
        "negative": {"avoid", "reduce", "strong_sell"},
        "watch":    {"add_to_watchlist"},
        "unknown":  {"need_more_data"},
    }

    def group_of(action: str) -> str:
        for g, actions in ACTION_GROUPS.items():
            if action in actions:
                return g
        return "unknown"

    qg = group_of(query_action)
    cg = group_of(case_action)

    if qg == cg:
        return 1.0
    elif (qg == "positive" and cg == "neutral") or (qg == "neutral" and cg == "positive"):
        return 0.5
    elif (qg == "negative" and cg == "neutral") or (qg == "neutral" and cg == "negative"):
        return 0.5
    elif qg == "positive" and cg == "negative":
        return 0.0
    elif qg == "negative" and cg == "positive":
        return 0.0
    else:
        return 0.3  # watch/unknown 与其他


def _date_proximity(
    query_date: datetime | None,
    case_date_str: str
) -> float:
    """
    日期接近度：越近得分越高。
    1 天内 = 1.0，线性衰减到 90 天 = 0.0。
    """
    if query_date is None:
        return 0.5  # 无日期约束时为中性

    case_date = datetime.fromisoformat(case_date_str.replace("Z", "+00:00"))
    delta_days = abs((query_date - case_date).days)

    if delta_days <= 1:
        return 1.0
    elif delta_days >= 90:
        return 0.0
    else:
        return 1.0 - (delta_days / 90.0)


def _confidence_similarity(
    query_conf: float | None,
    case_conf: float
) -> float:
    """置信度接近度：差值越小得分越高。"""
    if query_conf is None:
        return 0.5
    diff = abs(query_conf - case_conf)
    return max(0.0, 1.0 - diff)


def _data_quality_similarity(
    query_quality: str | None,
    case_trace: dict
) -> float:
    """数据质量相似度。query 无质量信息时返回中性。"""
    if query_quality is None:
        return 0.5

    QUALITY_ORDER = {"high": 4, "medium": 3, "low": 2, "unavailable": 1, "unknown": 0}
    qv = QUALITY_ORDER.get(query_quality, 0)
    # case 侧取所有 Analysis Card 中 data_quality 的众数或中位数
    # MVP 简化：使用 trace_summary 中的 data_quality 标记
    cv = 3  # 默认 medium
    diff = abs(qv - cv) / 4.0
    return max(0.0, 1.0 - diff)


# ============================================================
# 检索入口
# ============================================================

def search_cases(query: CaseQuery, index: dict) -> list[dict]:
    """
    案例检索入口。按 §5.1 流程图执行 4 步检索。
    """
    # Step 1: 精确匹配过滤
    candidates = set(index["by_ticker"].get(query.ticker, []))

    if query.task_type:
        candidates &= set(index["by_task_type"].get(query.task_type, []))

    if query.playbook_id:
        candidates &= set(index["by_playbook"].get(query.playbook_id, []))

    # Step 2: 范围过滤（date_range 等）
    if query.date:
        candidates = {
            cid for cid in candidates
            if _date_in_range(index["cases"][cid], query.date)
        }

    # Step 3: 相似度评分
    scored = []
    for cid in candidates:
        case = index["cases"][cid]
        score = compute_similarity(query, case)
        scored.append((cid, score, case))

    # Step 4: 排序 + 截断
    scored.sort(key=lambda x: x[1], reverse=True)
    return [
        {"case_id": cid, "score": score, "case": case}
        for cid, score, case in scored[:query.limit]
    ]


def _date_in_range(case: dict, query_date: datetime) -> bool:
    """检查 case 是否在 query_date 前后 90 天内。"""
    case_date = datetime.fromisoformat(
        case["run"]["started_at"].replace("Z", "+00:00")
    )
    return abs((query_date - case_date).days) <= 90
```

### 5.3 匹配度评分解释

| 分数区间 | 含义 | 典型场景 |
|---|---|---|
| 0.80–1.00 | 高度相似 | 同 ticker + 同 playbook + 同 task_type + 同方向结果 + 近期 |
| 0.50–0.79 | 中等相似 | 同 ticker + 同 playbook，但 task_type 或结果不同 |
| 0.20–0.49 | 弱相似 | 同 ticker 但 playbook/task_type 不匹配 |
| 0.00–0.19 | 几乎无关 | ticker 不匹配（直接归 0） |

---

## 6. 隐私边界（与 SPEC-012 的接口）

### 6.1 数据进入 Case Library 的决策路径

```text
                    ┌──────────────────────┐
                    │   Run 完成            │
                    │   run_status ∈ {       │
                    │     completed,         │
                    │     completed_with_     │
                    │       warnings,         │
                    │     failed,             │
                    │     analysis_incomplete │
                    │   }                    │
                    └──────────┬───────────┘
                               │
                               ▼
                  ┌────────────────────────────┐
                  │  用户是否授权贡献到          │
                  │  Case Library？             │
                  │  (authorization.scope =     │
                  │   "case_library_contribution")│
                  └──────────┬─────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │ 否                           │ 是
              ▼                              ▼
    ┌──────────────────┐        ┌──────────────────────────┐
    │ 不进入 Case Library │        │  数据分类检查              │
    │ （仅保留在用户私有    │        │  check_data_access() per  │
    │   存储中）           │        │  SPEC-012 §3.2            │
    └──────────────────┘        └──────────┬───────────────┘
                                           │
                                           ▼
                              ┌────────────────────────────┐
                              │  user_private 数据？        │
                              │  → DENY（硬规则，永不进入）   │
                              ├────────────────────────────┤
                              │  system_generated 数据？    │
                              │  → ALLOW_WITH_ANONYMIZATION│
                              ├────────────────────────────┤
                              │  public_reference 数据？    │
                              │  → ALLOW（无限制）           │
                              └──────────┬─────────────────┘
                                         │
                                         ▼
                              ┌────────────────────────────┐
                              │  执行匿名化                  │
                              │  anonymize(data) per §7     │
                              └──────────┬─────────────────┘
                                         │
                              ┌──────────┼──────────┐
                              │ 成功                 │ 失败
                              ▼                      ▼
                    ┌──────────────────┐  ┌──────────────────┐
                    │  写入 Case Library │  │  拒绝写入          │
                    │  记录 provenance   │  │  记录匿名化失败事件  │
                    └──────────────────┘  └──────────────────┘
```

### 6.2 隐私边界声明

1. **`user_private` 数据绝不进入 Case Library。** 这是硬规则，无例外路径。即使有用户授权，`user_private` 数据也只在用户私有存储中存在（SPEC-012 §3.2 Rule 2c）。

2. **`system_generated` 数据需用户显式授权 + 匿名化后才可进入。** 授权范围为 `case_library_contribution`，缺省为关闭。匿名化处理包括移除 user_id、task_id 中可关联用户的片段、Evidence Packet 隐私标记部分、Decision Trace 中私有数据引用和 user_feedback 内容（详见 §7）。

3. **`public_reference` 数据无限制进入。** 公开行情、财报、新闻等数据不包含用户信息，可全局共享。

4. **匿名化后的数据不可逆向关联到具体用户。** `provenance` 中仅保留 user_id 的 salted hash，用于未来可能的去重或反作弊，不用于重识别。

5. **Case Library 是公共资产。** 一旦 Case 入库，用户无权删除（因匿名化已切断关联）。系统管理员保留对 Case Library 的管理权限。

---

## 7. 匿名化规则

### 7.1 匿名化处理清单

```python
# ============================================================
# SPEC-011 匿名化处理器 v0.1
# ============================================================

def anonymize_for_case_library(run_data: dict) -> tuple[dict, list[str]]:
    """
    对完整 Run 数据执行匿名化，返回 (anonymized_case, removed_fields)。

    匿名化规则（MVP 最小集，与 SPEC-012 §6.2 对齐）：
      R1: 移除 user_id 和用户可识别信息
      R2: 移除 task_id 中可关联用户的片段
      R3: 移除 Evidence Packet 中 privacy.contains_user_private_data=true 的部分
      R4: 移除 Decision Trace 中引用 user_private_data_types 的具体值
      R5: 移除 user_feedback 具体内容（保留结构类型）
    """
    removed = []
    case = {}

    # ── R1: 移除 user_id ──
    if "user_id" in run_data:
        removed.append("user_id")
    # provenance 中仅保留 salted hash
    case["provenance"] = {
        "contributed_by_user_id_hash": _salted_hash(
            run_data.get("user_id", "unknown")
        ),
        "contribution_authorized_at": run_data.get("authorized_at"),
        "authorization_scope": "case_library_contribution"
    }

    # ── R2: Task 去私有化 ──
    task = run_data.get("task", {})
    case["task"] = {
        k: v for k, v in task.items()
        if k not in ("uses_user_private_data", "user_private_data_types")
    }
    removed.extend(["task.uses_user_private_data", "task.user_private_data_types"])

    # ── R3: Evidence Packet 隐私字段剥离 ──
    # Case 中只保留 evidence_packet 的统计摘要，不存储完整 evidence
    # 若未来需要存储 Evidence Packet 摘要，必须检查 privacy 字段
    case["trace_summary"] = _build_trace_summary(
        run_data,
        strip_private_evidence=True
    )
    removed.append("evidence_packets[*].privacy.contains_user_private_data=true")

    # ── R4: Decision Trace 私有引用脱敏 ──
    # MVP 阶段 Case 不存储完整 Decision Trace，仅存储 trace_summary
    # 若未来存储完整 Trace，必须对 user_private_data_types 引用进行脱敏
    removed.append("decision_trace.user_private_refs")

    # ── R5: 移除 user_feedback 内容 ──
    # user_feedback 内容的任何引用均移除
    removed.append("user_feedback_content")

    # ── 构建匿名化记录 ──
    case["anonymization"] = {
        "applied": True,
        "applied_at": _now_iso(),
        "rules_version": "1.0",
        "removed_fields": removed
    }

    # ── 复制经匿名化的其他字段 ──
    case.update(_copy_safe_fields(run_data))

    return case, removed


def _salted_hash(value: str) -> str:
    """对敏感值进行 salted hash。"""
    # 实际实现应使用 HMAC-SHA256 + 系统级盐值
    return f"sha256:salted_{value}"


def _build_trace_summary(run_data: dict, strip_private_evidence: bool) -> dict:
    """构建 Trace 统计摘要，不包含原始数据。"""
    return {
        "decision_trace_version": "1.0",
        "total_evidence_packets": len(run_data.get("evidence_packets", [])),
        "total_analysis_cards": len(run_data.get("analysis_cards", [])),
        "total_validation_findings": _count_findings(run_data.get("validation_reports", [])),
        "total_conflicts": len(run_data.get("conflict_reports", [])),
        "guardrail_triggered": _guardrail_triggered(run_data.get("guardrail_report")),
        "requires_human_review": run_data.get("requires_human_review", False)
    }


def _copy_safe_fields(run_data: dict) -> dict:
    """复制经审查的安全字段。"""
    return {
        "run": run_data.get("run", {}),
        "playbook": run_data.get("playbook", {}),
        "analysis_cards": _summarize_cards(run_data.get("analysis_cards", [])),
        "playbook_evaluation": _summarize_playbook_eval(
            run_data.get("playbook_evaluation_report")
        ),
        "decision": _summarize_decision(run_data.get("decision_candidate")),
        "index": _build_index(run_data)
    }


def _summarize_cards(cards: list) -> list:
    """Card 摘要：只保留 domain, stance, confidence, data_quality, summary。"""
    return [
        {
            "card_id": c.get("card_id"),
            "domain": c.get("domain"),
            "domain_status": c.get("domain_status"),
            "stance": c.get("stance"),
            "confidence": c.get("confidence"),
            "data_quality": c.get("data_quality"),
            "summary": c.get("summary")
        }
        for c in cards
    ]


def _summarize_playbook_eval(pbe: dict | None) -> dict | None:
    if pbe is None:
        return None
    return {
        "playbook_evaluation_report_id": pbe.get("playbook_evaluation_report_id"),
        "overall_result": pbe.get("overall_result"),
        "recommended_decision_bounds": pbe.get("recommended_decision_bounds"),
        "blocking_conditions": pbe.get("blocking_conditions")
    }


def _summarize_decision(dc: dict | None) -> dict | None:
    if dc is None:
        return None
    return {
        "decision_candidate_id": dc.get("decision_candidate_id"),
        "suggested_action": dc.get("suggested_action"),
        "confidence": dc.get("confidence")
    }


def _build_index(run_data: dict) -> dict:
    """构建扁平化索引。"""
    task = run_data.get("task", {})
    dc = run_data.get("decision_candidate", {})
    pbe = run_data.get("playbook_evaluation_report", {})
    return {
        "ticker": (task.get("asset", {}) or {}).get("symbol", ""),
        "task_type": task.get("task_type", ""),
        "playbook_id": task.get("playbook_id", ""),
        "date": (run_data.get("run", {}) or {}).get("started_at", "")[:10],
        "outcome": {
            "suggested_action": dc.get("suggested_action", ""),
            "overall_result": pbe.get("overall_result", "")
        }
    }


# ── 辅助函数（占位） ──
def _count_findings(reports): return sum(len(r.get("findings", [])) for r in reports)
def _guardrail_triggered(gr): return gr.get("triggered", False) if gr else False
def _now_iso(): return "2026-06-14T00:00:00Z"
```

### 7.2 匿名化验证

Case 写入前必须通过以下验证：

```python
def verify_anonymization(case: dict) -> bool:
    """验证 Case 已完成匿名化处理。"""
    checks = [
        case.get("anonymization", {}).get("applied") == True,
        "user_id" not in str(case.get("task", {})),
        "user_private" not in str(case),
        "user_feedback" not in str(case.get("decision", {})),
        case.get("provenance", {}).get("contributed_by_user_id_hash", "").startswith("sha256:"),
    ]
    return all(checks)
```

---

## 8. MVP 最小实现范围

### 8.1 MVP 必须实现

| 序号 | 功能 | 优先级 | 说明 |
|---|---|---|---|
| 1 | Case 数据结构定义 | P0 | §3 中的完整 JSON Schema |
| 2 | 用户授权入口 | P0 | 用户可勾选"允许贡献到案例库"（缺省关闭） |
| 3 | 匿名化处理器 | P0 | §7.1 的 R1–R5 五条规则 |
| 4 | 匿名化验证 | P0 | §7.2 的验证函数，写入前强制检查 |
| 5 | Case 写入流程 | P0 | Run 完成 → 检查授权 → 匿名化 → 验证 → 写入 |
| 6 | 索引构建 | P1 | 六维索引（ticker, task_type, playbook, date, outcome, overall_result） |
| 7 | 基础查询接口 | P1 | 按 ticker + task_type + playbook 精确过滤 |
| 8 | 案例不可变性保证 | P1 | 写入后不可修改 |

### 8.2 MVP 暂不实现

| 序号 | 功能 | 说明 |
|---|---|---|
| 1 | 自动相似案例匹配 | 不自动触发案例检索，不将历史案例注入当前 Task 上下文 |
| 2 | 案例驱动的决策建议 | 不基于历史案例生成推荐或修改 Decision Candidate |
| 3 | `compute_similarity()` 实际调用 | 相似度算法已定义但 MVP 不调用，仅保留接口 |
| 4 | 跨股票案例检索 | MVP 阶段 ticker 不匹配直接归 0 |
| 5 | 语义/向量检索 | MVP 仅支持结构化字段精确匹配 |
| 6 | 案例删除 | 系统管理员功能，不暴露给用户 |
| 7 | 案例统计面板 | 按 ticker/playbook/outcome 的统计视图 |
| 8 | 案例版本迁移 | Case schema 升级时的向后兼容 |
| 9 | 批量案例导入/导出 | 从外部系统导入历史决策记录 |

### 8.3 MVP 一句话总结

> **MVP 阶段的 Case Library 是"只写不读"的归档。** 系统在 Run 完成时（经用户授权后）将匿名化 Case 写入库中，但不主动读取、不主动匹配、不基于历史案例影响当前决策。

---

## 9. 与 SPEC-012 的接口契约

### 9.1 契约总览

```text
┌─────────────────────────────────────────────────────────────────┐
│            SPEC-011 ←→ SPEC-012 数据治理契约                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  允许进入 Case Library：                                          │
│    1. public_reference 数据（无限制）                               │
│    2. system_generated 数据（用户授权 + 匿名化后）                   │
│                                                                  │
│  禁止进入 Case Library：                                          │
│    1. user_private 数据（硬规则，永不进入）                         │
│    2. 未授权的 system_generated 数据                               │
│    3. 匿名化处理失败的 system_generated 数据                        │
│                                                                  │
│  Case Library 入口必须实现的接口：                                  │
│    - privacy_check(data) → AccessDecision                        │
│    - anonymize(system_generated_data) → anonymized_data           │
│    - verify_authorization(user_id, data_id) → bool               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 SPEC-011 对 SPEC-012 的依赖接口

| 接口函数 | 调用方 | 说明 |
|---|---|---|
| `check_data_access(data_type, access_context)` | Case Library 写入入口 | SPEC-012 §3.2 决策树，caller=`"case_library"` |
| `ALLOW_WITH_ANONYMIZATION` | Case Library | 返回此决策后，Case Library 执行 §7 匿名化 |
| `verify_authorization(user_id, data_id)` | Case Library 写入入口 | 验证用户是否有 `case_library_contribution` 授权 |
| `AccessDecision.DENY`（user_private） | Case Library | 硬规则，私有数据直接拒绝 |

### 9.3 SPEC-012 对 SPEC-011 的接口要求

来自 SPEC-012 §6.2：

| 接口函数 | 实现方 | 说明 |
|---|---|---|
| `privacy_check(data)` | Case Library | 对即将入库数据执行隐私检查，返回 AccessDecision |
| `anonymize(system_generated_data)` | Case Library | 对 system_generated 数据执行 §7 匿名化规则 |
| `verify_authorization(user_id, data_id)` | Case Library | 验证用户授权状态，返回 bool |

### 9.4 数据流入 Case Library 的完整时序

```text
SPEC-003 Run 完成
    │
    ▼
SPEC-012: check_data_access(          ← 检查是否允许写入
    data_type=SYSTEM_GENERATED,
    access_context={
        caller="case_library",
        authorization=user_auth
    }
)
    │
    ├─ DENY → 不写入，记录事件
    │
    ▼
SPEC-011: anonymize(run_data)          ← 执行匿名化
    │
    ├─ 匿名化失败 → 不写入，记录事件
    │
    ▼
SPEC-011: verify_anonymization(case)  ← 验证匿名化完整性
    │
    ├─ 验证失败 → 不写入，记录事件
    │
    ▼
Case Library: write(case)             ← 写入案例库
    │
    ▼
Case Library: update_indices(case)    ← 更新索引
```

---

## 10. 开放问题

1. **案例库中 Evidence Packet 的存储粒度？** MVP 阶段 Case 只存储 `trace_summary`（统计摘要），不存储完整 Evidence Packets。后续版本是否需要更细粒度？（代价：存储膨胀 + 匿名化复杂度增加。）

2. **相似度算法何时启用？** `compute_similarity()` 伪代码已定义，但 MVP 不启用。是否在 MVP v1.1 或 v2.0 中引入"用户手动触发相似案例查询"？

3. **多 Playbook 对比场景下的 Case 结构？** SPEC-003 §32 提到未来 Run State 可能支持 `playbook_evaluation_reports: []`（多 Playbook 对比）。届时一个 Run 可能产生多套结论，如何映射到 Case？

4. **案例去重策略？** 同一 task 多次重新执行（如修改参数后重跑）是否视为不同 Case？目前以 `run_id` 区分，是否需要在索引层面标记父子关系？

5. **Case 的过期/下线？** Case 是否有时效性限制？例如 Playbook 重大变更后，基于旧 Playbook 的 Case 是否应标记为 deprecated？

6. **匿名化的可重识别风险评估？** 在极端情况下（如某 ticker 只有极少 Case），匿名化的 `trace_summary` 是否仍可推断出用户身份？是否需要引入 k-anonymity 等更严格的保护？

---

## 11. v0.1 总结

SPEC-011 v0.1 定义了 crosslens Case Library 的基础框架：

1. **Case 定义**：Case = 一次完整 Run 的不可变快照，包含 Investment Task、Analysis Cards、Playbook Evaluation Report、Decision Candidate、Decision Trace 摘要和 Run Metadata。**不含用户私有数据。**

2. **完整 Schema**：§3 定义了 Case 的 JSON 结构，含 `run`、`task`（去私有化）、`playbook`、`analysis_cards`（摘要）、`playbook_evaluation`、`decision`、`trace_summary`、`index`、`anonymization`、`provenance` 十个模块。

3. **检索与相似匹配**：§5 先以流程图定义 4 步检索流程（精确过滤 → 范围过滤 → 相似评分 → 排序截断），再用完整伪代码定义 `compute_similarity()`（7 维度加权评分，MVP 不启用）。

4. **隐私边界**：§6 定义数据进入 Case Library 的决策路径，明确三层规则——user_private 永禁、system_generated 需授权+匿名化、public_reference 无限制。

5. **匿名化规则**：§7 以伪代码定义五条匿名化规则（R1–R5）及写入前验证，与 SPEC-012 §6.2 完全对齐。

6. **MVP 最小范围**：§8 明确 MVP 阶段 Case Library 为"只写不读"的归档。必须实现：匿名化写入、索引构建、基础查询接口。**不实现：自动匹配、决策建议、语义检索。**

7. **接口契约**：§9 明确定义 SPEC-011 ↔ SPEC-012 的双向接口（`privacy_check`、`anonymize`、`verify_authorization`），以及数据流入 Case Library 的完整时序。

本 SPEC 坚持 crosslens 架构宪法：

```text
Deterministic first, Agentic when necessary, Traceable always.
```

在 Case Library 语境下，这意味着：

> 案例的存入和检索使用确定性规则和结构化索引；匿名化规则是可审计的确定性算法；每一项 Case 的来源和变更全程可追踪。

---

## 附录 A：术语对照

| 中文 | English | 缩写 |
|---|---|---|
| 案例库 | Case Library | CL |
| 案例 | Case | — |
| 运行 | Run | — |
| 匿名化 | Anonymization | — |
| 来源追溯 | Provenance | — |
| 相似度评分 | Similarity Scoring | — |
| 只写不读 | Write-Only Archive | — |
| 索引 | Index | — |

---

## 附录 B：版本历史

| 版本 | 日期 | 变更说明 |
|---|---|---|
| v0.1 | 2026-06-14 | 初始草案：Case 定义与 Schema、存储与索引、检索算法、隐私边界、匿名化规则、MVP 范围、SPEC-012 接口契约 |
