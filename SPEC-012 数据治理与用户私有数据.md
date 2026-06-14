# SPEC-012：数据治理与用户私有数据

**版本：** v0.1
**状态：** Draft
**项目名称：** crosslens
**依赖文档：** SPEC-001 v0.4；SPEC-003 v0.3.4
**文档类型：** 数据治理规范
**目标阶段：** 产品机制设计 / MVP 架构定义

---

## 1. 文档目标

SPEC-012 定义 crosslens 的数据治理策略，重点回答：

1. 数据如何分类（user_private / system_generated / public_reference）；
2. 用户私有数据的访问权限如何通过伪代码决策树表达；
3. 用户私有数据的存储、保留、删除和导出策略；
4. MVP 最小实现范围；
5. 与 SPEC-003（Task Schema）和 SPEC-011（Case Library）的接口契约。

本 SPEC 不定义：

1. 具体数据库选型或存储引擎；
2. 加密算法实现细节；
3. 多租户架构的完整设计；
4. Case Library 的内部结构（由 SPEC-011 定义）；
5. 第三方数据源接入协议。

---

## 2. 数据分类

### 2.1 三类数据

crosslens 中所有数据归入三类：

```text
┌──────────────────────────────────────────────────────────────────┐
│                    crosslens 数据分类                              │
├──────────────────┬──────────────────┬─────────────────────────────┤
│  user_private    │ system_generated │ public_reference            │
│  用户私有数据      │ 系统生成数据       │ 公开参考数据                  │
├──────────────────┼──────────────────┼─────────────────────────────┤
│ 所有权：用户       │ 所有权：用户       │ 所有权：无（公开）              │
│ 可见性：用户隔离    │ 可见性：用户隔离    │ 可见性：全局                   │
│ 可删除：是         │ 可删除：是         │ 可删除：否                    │
│ 可导出：是         │ 可导出：是         │ 可导出：是（原始来源）           │
└──────────────────┴──────────────────┴─────────────────────────────┘
```

### 2.2 user_private（用户私有数据）

由用户直接提供或系统在用户授权下采集的数据。**所有权归用户，默认不可被任何其他用户或公共资源访问。**

| 数据类型 | 说明 | 示例 |
|---|---|---|
| `watchlist` | 自选股列表 | 用户关注的股票代码、分组标签 |
| `private_notes` | 私有笔记 | 用户对某只股票的笔记、研究草稿 |
| `position` | 持仓信息 | 当前持仓股票、数量、成本价 |
| `trade_history` | 交易历史 | 历史买卖记录、交易时间、价格 |
| `investment_memo` | 投资备忘录 | 买入/卖出/持有决策的理由记录 |
| `review_notes` | 复盘笔记 | 对历史决策的复盘和反思 |
| `custom_playbook` | 自定义 Playbook | 用户创建的投资决策手册 |
| `user_feedback` | 用户反馈 | 对 Analysis Card、Decision Candidate 的评分和修正 |

### 2.3 system_generated（系统生成数据）

由 crosslens 在用户任务执行过程中生成的数据。**所有权归用户，默认用户级隔离。**

| 数据类型 | 说明 | 是否可匿名化后进入公共案例库 |
|---|---|---|
| `analysis_card` | Analysis Card | 需用户明确授权 |
| `decision_candidate` | Decision Candidate | 需用户明确授权 |
| `decision_trace` | Decision Trace | 需用户明确授权 |
| `evidence_packet` | Evidence Packet（不含私有数据部分） | 需用户明确授权 |
| `event_log` | 系统 Event Log | 需用户明确授权 |

### 2.4 public_reference（公开参考数据）

来自公开市场的数据，不包含任何用户私有信息。**全局共享，不计入数据隔离范围。**

| 数据类型 | 说明 | 来源 |
|---|---|---|
| `market_data` | 行情数据 | 交易所、数据供应商 |
| `financial_data` | 财报数据 | 公开披露 |
| `news` | 新闻 | 公开媒体 |
| `macro_data` | 宏观数据 | 统计局、央行等 |
| `sentiment_data` | 情绪数据 | 社媒公开内容 |
| `technical_data` | 技术指标派生数据 | 基于公开行情的计算 |

---

## 3. 数据权限决策树

### 3.1 核心原则

> 用户私有数据不得默认用于公共案例库、公共评估集或其他用户的模型上下文。
>
> —— SPEC-001 §13

### 3.2 决策树伪代码

以下伪代码定义所有数据访问路径的核心路由逻辑：

```python
# ============================================================
# SPEC-012 数据权限决策树 v0.1
# 调用入口：每次 Task 执行、Case Library 写入、数据导出时触发
# ============================================================

def check_data_access(
    data_type: DataType,
    access_context: AccessContext
) -> AccessDecision:
    """
    data_type:       目标数据的分类 (user_private | system_generated | public_reference)
    access_context:  访问上下文，包含：
      - caller:            调用者身份（"task_executor" | "case_library" | "user_export" | "admin"）
      - requesting_user_id: 发起请求的用户 ID（null 表示系统级调用）
      - data_owner_id:      数据所属用户 ID
      - task_id:            关联 Task ID（若有）
      - task_uses_private:  关联 Task 的 uses_user_private_data flag
      - authorization:      用户显式授权记录（可选）
    """

    # ------------------------------------------------------------------
    # RULE 0: 公开参考数据 — 无限制
    # ------------------------------------------------------------------
    if data_type == DataType.PUBLIC_REFERENCE:
        return AccessDecision.ALLOW  # 公开数据，无访问限制

    # ------------------------------------------------------------------
    # RULE 1: 系统生成数据 — 用户级隔离
    # ------------------------------------------------------------------
    if data_type == DataType.SYSTEM_GENERATED:
        # 1a. 用户访问自己的系统生成数据：允许
        if access_context.requesting_user_id == access_context.data_owner_id:
            return AccessDecision.ALLOW

        # 1b. 系统内部 Task 执行器访问：需当前 Task 属于数据所有者
        if access_context.caller == "task_executor":
            if access_context.requesting_user_id == access_context.data_owner_id:
                return AccessDecision.ALLOW
            return AccessDecision.DENY

        # 1c. Case Library 写入：需用户显式授权
        if access_context.caller == "case_library":
            auth = access_context.authorization
            if auth is None:
                return AccessDecision.DENY
            if auth.scope != "case_library_contribution":
                return AccessDecision.DENY
            if auth.status != "active":
                return AccessDecision.DENY
            if auth.data_owner_id != access_context.data_owner_id:
                return AccessDecision.DENY
            # 通过授权后还需匿名化处理（由调用方执行）
            return AccessDecision.ALLOW_WITH_ANONYMIZATION

        # 1d. 其他情况：拒绝
        return AccessDecision.DENY

    # ------------------------------------------------------------------
    # RULE 2: 用户私有数据 — 最严格隔离
    # ------------------------------------------------------------------
    if data_type == DataType.USER_PRIVATE:

        # 2a. 用户访问自己的私有数据：允许
        if access_context.requesting_user_id == access_context.data_owner_id:
            return AccessDecision.ALLOW

        # 2b. Task 执行器访问：必须满足三重条件
        if access_context.caller == "task_executor":
            # 条件 1：Task 显式声明使用私有数据
            if not access_context.task_uses_private:
                return AccessDecision.DENY

            # 条件 2：Task 属于数据所有者
            if access_context.requesting_user_id != access_context.data_owner_id:
                return AccessDecision.DENY

            # 条件 3：目标数据类型在 Task 声明的 user_private_data_types 中
            if data_type.name not in access_context.task_private_data_types:
                return AccessDecision.DENY

            # 允许访问，但写入 Evidence 时必须脱敏
            return AccessDecision.ALLOW_WITH_PRIVACY_MARKER

        # 2c. Case Library：禁止（任何情况下私有数据不进入公共案例库）
        if access_context.caller == "case_library":
            return AccessDecision.DENY  # 硬规则：私有数据永不进入案例库

        # 2d. 用户导出：只允许导出自己的
        if access_context.caller == "user_export":
            if access_context.requesting_user_id == access_context.data_owner_id:
                return AccessDecision.ALLOW
            return AccessDecision.DENY

        # 2e. 其他用户访问：禁止
        return AccessDecision.DENY

    # 未知分类：保守拒绝
    return AccessDecision.DENY


# ============================================================
# 共享路径：用户明确授权
# ============================================================

def check_share_authorization(
    owner_id: str,
    target_user_id: str,
    share_scope: ShareScope,
    authorization_record: Authorization | None
) -> AccessDecision:
    """
    用户主动将自身私有数据或分析结果分享给其他用户的决策路径。

    share_scope 可以是：
      - "single_decision":   单次 Decision Trace
      - "analysis_card":     单张 Analysis Card
      - "case_contribution": 贡献到公共案例库（仅限 system_generated，且需匿名化）
      - "collaboration":     协作模式（团队共享）
    """

    if authorization_record is None:
        return AccessDecision.DENY

    # Rule S1: 授权必须由数据所有者发起
    if authorization_record.granted_by != owner_id:
        return AccessDecision.DENY

    # Rule S2: 授权范围必须包含目标
    if share_scope not in authorization_record.allowed_scopes:
        return AccessDecision.DENY

    # Rule S3: 授权未过期
    if authorization_record.expired:
        return AccessDecision.DENY

    # Rule S4: 授权未被撤销
    if authorization_record.revoked:
        return AccessDecision.DENY

    # Rule S5: 协作模式需双方确认
    if share_scope == "collaboration":
        if target_user_id not in authorization_record.collaborators:
            return AccessDecision.DENY

    # Rule S6: 案例库贡献只能是系统生成数据，且必须匿名化
    if share_scope == "case_contribution":
        return AccessDecision.ALLOW_WITH_ANONYMIZATION

    # Rule S7: 私有数据共享 — 目标用户获得只读访问
    return AccessDecision.ALLOW_READ_ONLY
```

### 3.3 决策路径图

```text
用户发起请求
    │
    ▼
┌─────────────────────────┐
│ 判断 data_type           │
│                         │
│ public_reference ───────┼──► ALLOW（无限制）
│                         │
│ system_generated ───────┼──► 见分支 A
│                         │
│ user_private ───────────┼──► 见分支 B
└─────────────────────────┘

分支 A（system_generated）：
    ├─ 自己访问自己 ──► ALLOW
    ├─ Task 执行器（同用户）──► ALLOW
    ├─ Case Library 写入
    │     ├─ 有授权 + 匿名化 ──► ALLOW_WITH_ANONYMIZATION
    │     └─ 无授权 ──► DENY
    └─ 其他 ──► DENY

分支 B（user_private）：
    ├─ 自己访问自己 ──► ALLOW
    ├─ Task 执行器
    │     ├─ Task 声明 uses_user_private_data + 用户匹配 + 类型匹配
    │     │     └─► ALLOW_WITH_PRIVACY_MARKER
    │     └─ 任一条件不满足 ──► DENY
    ├─ Case Library ──► DENY（硬规则，永不进入案例库）
    ├─ 用户导出（自己）──► ALLOW
    └─ 其他 ──► DENY
```

### 3.4 `uses_user_private_data` flag 的生成逻辑

`uses_user_private_data` 是 Investment Task 的布尔字段，由 Task Understanding Layer 在解析用户请求时生成。

```python
def determine_uses_user_private_data(
    user_intent: str,
    task_type: str,
    user_request: str
) -> tuple[bool, list[str]]:
    """
    返回 (uses_user_private_data, user_private_data_types)
    """

    # 以下意图类型默认触发私有数据使用
    INTENTS_REQUIRING_PRIVATE = [
        "review_my_position",         # 审查我的持仓
        "check_portfolio_risk",       # 检查组合风险
        "compare_with_holdings",      # 与我当前持仓对比
        "replay_past_decision",       # 复盘过去决策
        "personalized_analysis",      # 个性化分析
    ]

    # 以下 Task 类型默认触发私有数据使用
    TASK_TYPES_REQUIRING_PRIVATE = [
        "portfolio_review",           # 组合审查
        "position_sizing_review",     # 仓位审查
        "trade_review",               # 交易复盘
        "personal_playbook_backtest", # 个人 Playbook 回测
    ]

    uses_private = False
    private_types = []

    if user_intent in INTENTS_REQUIRING_PRIVATE:
        uses_private = True

    if task_type in TASK_TYPES_REQUIRING_PRIVATE:
        uses_private = True

    if uses_private:
        # 根据意图推断所需私有数据类型
        private_types = infer_private_data_types(user_intent, task_type, user_request)

    return (uses_private, private_types)
```

---

## 4. 数据隐私标记

### 4.1 Evidence Packet 中的隐私标记

当 Evidence Packet 中引用了用户私有数据时，必须添加 `privacy` 标记：

```json
{
  "evidence_id": "ev_position_001",
  "privacy": {
    "contains_user_private_data": true,
    "private_data_types": ["position"],
    "anonymization_applied": false,
    "anonymization_method": null
  },
  "facts": [
    "user_currently_holds_position_above_5_percent"
  ],
  "metrics": {}
}
```

### 4.2 Decision Trace 中的隐私标记

Decision Trace 展示给用户自身时可以包含完整私有数据引用。若 Trace 被用户授权分享给其他用户，必须展示脱敏后的版本：

```text
Decision Trace（自身视图）：
  "用户当前持有 NVDA，仓位占比 12.3%，成本价 $85.40"

Decision Trace（分享视图）：
  "用户当前持有该股票"（具体仓位信息已脱敏）
```

---

## 5. 数据生命周期

### 5.1 存储位置

```text
┌──────────────────┬────────────────────────────────────────┐
│ 数据分类           │ 存储策略                                 │
├──────────────────┼────────────────────────────────────────┤
│ user_private     │ 用户级隔离存储                            │
│                  │ - 物理/逻辑隔离于其他用户数据                 │
│                  │ - 加密存储（at rest）                      │
│                  │ - 访问日志记录                             │
├──────────────────┼────────────────────────────────────────┤
│ system_generated │ 用户级隔离存储                            │
│                  │ - 与用户私有数据同级别隔离                    │
│                  │ - 匿名化后可进入公共存储（需授权）             │
├──────────────────┼────────────────────────────────────────┤
│ public_reference │ 全局共享存储                              │
│                  │ - 按时间分片                              │
│                  │ - 无用户级隔离                             │
└──────────────────┴────────────────────────────────────────┘
```

### 5.2 保留策略

| 数据类型 | 默认保留期 | 用户可配置 | 说明 |
|---|---|---|---|
| `user_private` | 永久（直到用户删除） | 是 | 用户可设置自动过期 |
| `system_generated`（关联 Task） | 永久（直到用户删除） | 是 | 保留完整 Decision Trace |
| `system_generated`（匿名化入案例库） | 永久 | 否 | 公共资产，不可删除 |
| `public_reference` | 按数据源策略 | 否 | 遵循数据供应商协议 |

### 5.3 删除机制

```python
def delete_user_data(user_id: str, scope: DeleteScope) -> DeleteResult:
    """
    scope 可选值：
      - "all":              删除用户所有数据
      - "private_only":     仅删除私有数据，保留系统生成数据
      - "task_related":     删除指定 Task 关联的所有数据
      - "date_range":       删除指定时间范围内的数据
    """

    # Step 1: 确定删除范围
    target_data = resolve_delete_targets(user_id, scope)

    # Step 2: 级联处理
    for item in target_data:
        if item.type == USER_PRIVATE:
            # 2a. 私有数据：硬删除
            hard_delete(item)

            # 2b. 级联：使用该私有数据生成的 Evidence Packet 标记为 degraded
            cascade_mark_evidence_degraded(item.id, reason="source_data_deleted")

            # 2c. 级联：关联的 Analysis Card 标记为 data_stale
            cascade_mark_cards_stale(item.id)

        elif item.type == SYSTEM_GENERATED:
            # 2d. 系统生成数据：硬删除
            hard_delete(item)

            # 2e. 但如果已匿名化进入案例库，案例库副本保留
            #    （匿名化后已切断与用户的关联）

    # Step 3: 审计日志
    log_deletion_event(user_id, scope, len(target_data))

    # Step 4: 返回删除报告
    return DeleteResult(
        deleted_count=len(target_data),
        cascaded_evidence_count=count_cascaded_evidence(),
        cascaded_card_count=count_cascaded_cards()
    )
```

### 5.4 导出机制

用户可导出自身数据，格式为结构化 JSON：

```json
{
  "export_version": "1.0",
  "exported_at": "2026-06-14T00:00:00Z",
  "user_id": "user_abc",
  "scope": "all",
  "data": {
    "user_private": {
      "watchlist": [...],
      "private_notes": [...],
      "position": [...],
      "trade_history": [...],
      "investment_memos": [...],
      "review_notes": [...],
      "custom_playbooks": [...]
    },
    "system_generated": {
      "analysis_cards": [...],
      "decision_candidates": [...],
      "decision_traces": [...]
    }
  },
  "checksum": "sha256:abc123..."
}
```

导出约束：

1. 只能导出自己的数据；
2. 导出不包含 public_reference 数据（用户可从原始来源获取）；
3. 导出包含完整文件和校验和；
4. MVP 阶段支持一次性全量导出。

---

## 6. 接口契约

### 6.1 与 SPEC-003（Investment Task）的契约

SPEC-003 Investment Task 中的两个字段由本 SPEC 统一定义枚举：

```json
{
  "uses_user_private_data": true,
  "user_private_data_types": [
    "current_position",
    "historical_analysis_notes"
  ]
}
```

**`user_private_data_types` 枚举：**

```text
current_position       → 对应 position
trade_history          → 对应 trade_history
watchlist              → 对应 watchlist
private_notes          → 对应 private_notes
investment_memo        → 对应 investment_memo
review_notes           → 对应 review_notes
custom_playbook        → 对应 custom_playbook
user_feedback          → 对应 user_feedback
```

**约束：**

1. `uses_user_private_data = true` 时，`user_private_data_types` 不得为空；
2. `user_private_data_types` 中的每个值必须在上表枚举中；
3. Task Execution Layer 在执行前必须验证此 flag 与 `user_private_data_types` 的一致性；
4. 若 `uses_user_private_data = false` 但执行过程中发现必须使用私有数据，系统应 `fail fast`，不降级执行；
5. 若 `uses_user_private_data = true` 但执行过程中发现私有数据不可用（如用户已删除），按 §5.3 级联降级处理。

### 6.2 与 SPEC-011（Case Library）的契约

SPEC-011 Case Library 的数据入口受以下规则约束：

```text
┌─────────────────────────────────────────────────────────────────┐
│            SPEC-012 ←→ SPEC-011 数据治理契约                      │
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

**匿名化要求（MVP 最小集）：**

匿名化处理应从 system_generated 数据中移除以下内容：

1. `user_id` 和用户可识别信息；
2. `task_id` 中可关联用户的片段；
3. Evidence Packet 中 `privacy.contains_user_private_data = true` 的部分；
4. Decision Trace 中引用 `user_private_data_types` 的具体值；
5. 所有 `user_feedback` 的具体内容（保留反馈结构类型）。

---

## 7. MVP 最小实现范围

### 7.1 MVP 必须实现

| 序号 | 功能 | 优先级 | 说明 |
|---|---|---|---|
| 1 | 数据分类标记 | P0 | 所有数据入库时打上 `user_private` / `system_generated` / `public_reference` 标签 |
| 2 | Task 级 `uses_user_private_data` flag | P0 | Investment Task 必须包含此字段 |
| 3 | 用户级数据隔离 | P0 | user_private 和 system_generated 数据物理/逻辑隔离 |
| 4 | 私有数据访问决策 | P0 | 执行 §3.2 中 RULE 2 的核心路径（Task 执行器三重检查） |
| 5 | `user_private_data_types` 枚举校验 | P0 | Task 中的声明必须匹配枚举 |
| 6 | 私有数据删除 | P1 | 用户可删除自己的私有数据 |
| 7 | 导出机制（全量） | P1 | 用户可导出所有自身数据 |

### 7.2 MVP 暂不实现

| 序号 | 功能 | 说明 |
|---|---|---|
| 1 | 数据共享与协作 | 用户间共享分析结果 |
| 2 | Case Library 匿名化流水线 | 自动化匿名化 + 审核流程 |
| 3 | 细粒度授权管理 | 分数据类型的共享授权 |
| 4 | 定时自动删除策略 | 用户可配置 TTL |
| 5 | 增量导出 | 仅导出增量变更 |
| 6 | 合规审计面板 | 管理员审计视图 |
| 7 | 加密密钥轮换 | 自动密钥管理 |

### 7.3 MVP 决策简化

MVP 阶段，以下决策路径简化处理：

```text
1. 无多用户协作 → 所有 user_private 和 system_generated 仅当前用户可见
2. 无 Case Library → 匿名化路径暂不实现
3. 无分享功能 → check_share_authorization() 不调用
4. 权限决策树简化为：
   - 是否为当前用户的数据？→ ALLOW（含 uses_user_private_data 三重检查）
   - 否则 → DENY
```

---

## 8. Implementation Notes

### 8.1 数据标记时机

```text
┌─────────────────────┬─────────────────────────────────┐
│ 数据类型              │ 标记时机                          │
├─────────────────────┼─────────────────────────────────┤
│ user_private        │ 用户创建/导入时                    │
│ system_generated    │ 对象生成时（Analysis Card 等）     │
│ public_reference    │ 数据接入层标记                     │
└─────────────────────┴─────────────────────────────────┘
```

### 8.2 跨层数据流中的隐私保护

数据在七层架构中流转时，每层必须保持隐私标记：

```text
Layer 3 (Context & Evidence):
  → 私有数据不出 Context Bundle 的 user_private 分区

Layer 5 (Execution):
  → Evidence Packet 包含 privacy 字段（§4.1）

Layer 6 (Review & Governance):
  → Guardrail 可以检查是否越权使用了私有数据

Layer 7 (Decision & Trace):
  → Decision Trace 区分自身视图和分享视图（§4.2）
```

### 8.3 错误处理

```python
class DataGovernanceError(Exception):
    """数据治理相关错误基类"""
    pass

class PrivateDataAccessDeniedError(DataGovernanceError):
    """尝试访问未授权的私有数据"""
    pass

class PrivacyMarkerMissingError(DataGovernanceError):
    """使用私有数据的 Evidence Packet 缺少 privacy 标记"""
    pass

class TaskPrivateDataMismatchError(DataGovernanceError):
    """Task 声明的 user_private_data_types 与实际使用不一致"""
    pass
```

---

## 9. 开放问题

1. **多用户协作的数据共享模型？** 未来小型投研团队场景下，私有 Playbook 和 Decision Trace 如何共享？（关联 SPEC-002 团队用户场景）

2. **私有数据与公共案例库的灰度边界？** system_generated 数据匿名化后进入案例库时，什么程度的聚合足以保证不可重识别？（关联 SPEC-011）

3. **数据保留的合规要求？** 若未来涉及持牌机构使用，是否需满足 SEC / CSRC 等监管保留期限？

4. **模型训练使用用户数据？** 用户私有数据是否可用于模型微调？MVP 阶段默认为否，但需在 SPEC-012 后续版本中明确条款。

5. **跨区域数据驻留？** 若用户分布在多个司法管辖区，私有数据的物理存储位置如何约束？

6. **`user_private_data_types` 枚举的扩展机制？** 未来用户自定义数据类型时，枚举如何扩展？

---

## 10. v0.1 总结

SPEC-012 v0.1 定义了 crosslens 的数据治理基础框架：

1. **三类数据分类**：user_private / system_generated / public_reference，每类有明确的所有权、可见性和操作权限；
2. **权限决策树**：以伪代码形式定义了所有数据访问路径的核心路由逻辑，包括 Task 执行器的三重检查（flag + 用户匹配 + 类型匹配）以及 Case Library 的硬拒绝规则；
3. **`uses_user_private_data` 生成逻辑**：定义了 Task Understanding Layer 如何根据用户意图和 Task 类型自动判断；
4. **数据生命周期**：定义了存储位置、保留策略、级联删除和用户导出机制；
5. **接口契约**：明确了与 SPEC-003（Task Schema）和 SPEC-011（Case Library）的边界约定；
6. **MVP 最小范围**：MVP 只实现单用户隔离和基本删除/导出，Case Library 匿名化和多用户协作不在 MVP 中。

本 SPEC 坚持 crosslens 架构宪法：

```text
Deterministic first, Agentic when necessary, Traceable always.
```

在数据治理语境下，这意味着：

> 数据权限是确定性规则，不依赖 Agent 自行判断；私有数据的每一次访问都有审计日志；数据流向全程可追踪。

---

---

## 11. 后续 SPEC 依赖

SPEC-012 依赖和影响以下文档：

1. SPEC-003：Agentic 投研工作流架构（`uses_user_private_data` flag 和 `user_private_data_types` 枚举）；
2. SPEC-011：Case Library 与历史案例记忆（数据流入 Case Library 的权限检查与匿名化接口）；
3. SPEC-010：MVP 范围与验证指标（MVP 阶段仅实现单用户隔离）。

---

## 附录 A：术语对照

| 中文 | English | 缩写 |
|---|---|---|
| 用户私有数据 | User Private Data | UPD |
| 系统生成数据 | System Generated Data | SGD |
| 公开参考数据 | Public Reference Data | PRD |
| 数据治理 | Data Governance | DG |
| 匿名化 | Anonymization | — |
| 级联删除 | Cascade Deletion | — |
| 脱敏 | Data Masking | — |

---

## 附录 B：版本历史

| 版本 | 日期 | 变更说明 |
|---|---|---|
| v0.1 | 2026-06-14 | 初始草案：数据分类、权限决策树、生命周期、MVP范围、接口契约 |
