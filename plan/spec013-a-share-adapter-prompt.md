# SPEC-013 v0.2.0 — A 股数据源重构 + Adapter 架构

## 项目位置

```
E:\CodePrograms\CrossLens\crosslens-specs
```

目标文件：`SPEC-013 Fundamentals 域实现规格 v0.1.2.md`（重命名为 v0.2.0.md）

---

## 架构背景

CrossLens 的核心用户主要做 **A 股**投资（top-down 宏观驱动，重点关注半导体/电子/AI 链、航运、资源品）。当前 SPEC-013 的 §11 和 §12 错误地写成了"US 市场，GAAP 会计准则"，需要全面修正为 A 股数据源。

本机已有两套成熟的数据基础设施：

### 数据源 1：AlphaDB / AlphaHome（离线数据库，日更新）

| 维度 | 详情 |
|------|------|
| **项目位置** | `E:\CodePrograms\alphaHome` |
| **技术栈** | PostgreSQL + Python（`alphahome` 包） |
| **更新频率** | 每天通过 Tushare 同步更新 |
| **配置** | `~/.alphahome/config.json` |
| **数据规模** | rawdata: 122 表/视图，features: 41 物化视图 |
| **访问方式** | `from alphahome.providers import AlphaDataTool` |
| **代码格式** | ts_code（`000001.SZ`, `600000.SH`） |
| **Codex Skill** | `~/.codex/skills/local-alphadb-data/SKILL.md`（完整表目录和使用手册） |

**与 Fundamentals 相关的核心表：**

| 数据需求 | AlphaDB 表 | 说明 |
|---------|-----------|------|
| 财务报表 | `rawdata.fina_income`, `rawdata.fina_balancesheet`, `rawdata.fina_cashflow` | 利润表、资产负债表、现金流量表 |
| 财务指标 | `rawdata.fina_indicator` | 综合财务指标（含 ROE、ROIC、毛利率等） |
| 行情 + 估值 | `rawdata.stock_dailybasic` | 每日 PE/PB/PS/总市值/流通市值 |
| 日线行情 | `rawdata.stock_daily` | OHLCV |
| 行业分类 | `rawdata.stock_industry_versioned` | 申万/中信行业版本化分类 |
| 行业指数 | `rawdata.index_swmember`, `rawdata.index_swdaily` | 申万行业成分+行情 |
| 分析师预测 | `rawdata.fina_forecast`, `rawdata.fina_express` | 业绩预测/快报 |
| 分析师覆盖 | `rawdata.stock_report_rc`, `rawdata.stock_analyst_rank_em` | 研报+分析师评级 |
| 分红送配 | `rawdata.stock_dividend` | 分红历史 |
| PIT 会计 | `rawdata.fina_pit_ext` | 披露日历（point-in-time） |
| 交易日历 | `rawdata.others_calendar` | A 股交易日 |

### 数据源 2：tinydata（实时数据源，天软 TS-OPI）

| 维度 | 详情 |
|------|------|
| **项目位置** | `E:\CodePrograms\tinydata` |
| **技术栈** | Python 独立库（v1.2.3），基于天软 TS-OPI HTTP API |
| **特点** | 实时/近实时行情、PIT 财务数据、支持并行抓取+缓存 |
| **配置** | 环境变量 `TINYDATA_USER` / `TINYDATA_PASSWORD` |
| **访问方式** | `import tinydata as td; td.stock_daily(...)` |
| **代码格式** | 同为 ts_code（`000001.SZ`, `600000.SH`） |
| **认证** | 环境变量（不硬编码） |
| **缓存** | 本地 parquet 缓存（`~/.tinydata/cache/`） |

**与 Fundamentals 相关的核心 API：**

| 数据需求 | tinydata API | 说明 |
|---------|-------------|------|
| 财务报表 | `td.fina_income()`, `td.fina_balancesheet()`, `td.fina_cashflow()` | 支持 `report_period` + `as_of_date`（PIT） |
| 财务指标 | `td.fina_indicator()` | InfoTable 接口，支持 `as_of_date` PIT 语义 |
| 估值指标 | `td.stock_valuation_indicator()` | ROIC 等估值字段 |
| TTM 指标 | `td.stock_ttm_indicator()` | parent_net_profit_ttm 等 |
| 日线行情 | `td.stock_daily()` | OHLCV + 复权 |
| 实时行情 | `td.realtime_snapshot()` | 最新价格（盘中/盘后） |
| 行业分类 | `td.stock_industry_versioned()` | 申万行业 |
| 业绩预测 | `td.fina_forecast()`, `td.fina_express()` | 业绩预告/快报 |
| 主营业务 | `td.fina_mainbz()` | 分产品/地区/行业主营构成 |
| 交易日历 | `td.trade_calendar()` | A 股交易日 |

### 两个数据源的分工

| 维度 | AlphaDB（离线） | tinydata（实时） |
|------|:---:|:---:|
| 历史财务数据（≥8 季度） | ✅ 主要 | ✅ 可补充 |
| 每日行情（OHLCV） | ✅ 主要 | ✅ 可补充 |
| 每日估值（PE/PB/市值） | ✅ `stock_dailybasic` | ⚠️ 需组合计算 |
| 实时/盘中行情 | ❌ | ✅ `realtime_snapshot()` |
| PIT 财务（披露日历） | ✅ `fina_pit_ext` | ✅ `as_of_date` 参数 |
| 行业对标（peer median） | ✅ 可 SQL 聚合 | ⚠️ 需应用层聚合 |
| 分析师覆盖 | ✅ `stock_report_rc` | ❌ |
| 历史估值序列（5 年） | ✅ `stock_dailybasic` | ⚠️ 需多次调用 |

**核心原则：AlphaDB 为主（历史+批量），tinydata 为辅（实时+PIT 补充）。**

---

## 执行方式：Team Agents

使用 team agents 模式。主 agent 负责任务分配、工作整合和最终汇报，子 agents 并行执行具体任务。

### 主 Agent 职责

1. 读取以下文件建立全局理解：
   - `SPEC-013 Fundamentals 域实现规格 v0.1.2.md`（当前完整内容）
   - `SPEC-REGISTRY.md`
   - `SPEC-004 五类分析能力域与 Analysis Card Schema v0.2.5.md` §17~§22（Fundamentals）
2. 分配 Task 给子 agents（可并行）
3. 子 agents 完成后：
   - 通读修改后的 SPEC-013 确认一致性
   - 运行全量测试确认无回归
   - 将文件重命名为 `SPEC-013 Fundamentals 域实现规格 v0.2.0.md`
   - 更新 SPEC-REGISTRY.md 中 SPEC-013 的版本号（v0.1.2 → v0.2.0）和状态（Draft → Review）
   - 整合为一次 commit
4. 向用户汇报（见底部模板）

---

## Task 1：§11 数据源全面重写

**完全重写 §11 Data Source Requirements**，从 US/GAAP 改为 A 股/中国会计准则（CAS）。

### 新的 §11 结构

```markdown
## 11. Data Source Requirements

### 11.1 数据架构总览

Fundamentals 域采用双数据源 Adapter 架构：

| 数据源 | 角色 | 更新频率 | 项目 | 访问方式 |
|--------|------|---------|------|---------|
| AlphaDB | 主力离线数据库 | 日更新 | E:\CodePrograms\alphaHome | AlphaDataTool / 直接 SQL |
| tinydata | 实时数据补充 | 近实时 | E:\CodePrograms\tinydata | `import tinydata as td` |

核心原则：AlphaDB 为主（历史+批量），tinydata 为辅（实时+PIT 补充）。

### 11.2 Adapter 接口

两个数据源通过统一的 Adapter 接口对接，CrossLens Fundamentals 域只消费 Adapter 输出，不直接依赖底层数据源实现。

[定义 Adapter 抽象接口 — 见 Task 2 的详细定义]

### 11.3 数据源映射表

| # | 数据需求 | AlphaDB 表/函数 | tinydata API | 更新频率 | Fallback 策略 |
|---|---------|----------------|-------------|---------|-------------|
| 1 | 利润表 | `rawdata.fina_income` | `td.fina_income()` | 季度 | tinydata 不可用 → AlphaDB only |
| 2 | 资产负债表 | `rawdata.fina_balancesheet` | `td.fina_balancesheet()` | 季度 | 同上 |
| 3 | 现金流量表 | `rawdata.fina_cashflow` | `td.fina_cashflow()` | 季度 | 同上 |
| 4 | 综合财务指标 | `rawdata.fina_indicator` | `td.fina_indicator()` | 季度 | 同上 |
| 5 | 日线行情 | `rawdata.stock_daily` | `td.stock_daily()` | 日 | AlphaDB 滞后 > 1 日 → tinydata 补充 |
| 6 | 每日估值 | `rawdata.stock_dailybasic` | 组合计算 | 日 | tinydata 补充 |
| 7 | 行业分类 | `rawdata.stock_industry_versioned` | `td.stock_industry_versioned()` | 事件驱动 | AlphaDB 为权威源 |
| 8 | 行业指数 | `rawdata.index_swmember` + `rawdata.index_swdaily` | — | 日 | AlphaDB 为唯一源 |
| 9 | 分析师预测 | `rawdata.fina_forecast` + `rawdata.fina_express` | `td.fina_forecast()` + `td.fina_express()` | 事件驱动 | AlphaDB 为主 |
| 10 | 交易日历 | `rawdata.others_calendar` | `td.trade_calendar()` | 年度 | 任一可用即可 |
| 11 | 分红送配 | `rawdata.stock_dividend` | `td.stock_dividend()` | 事件驱动 | AlphaDB 为主 |
| 12 | PIT 披露日历 | `rawdata.fina_pit_ext` | `td.fina_indicator(as_of_date=...)` | 季度 | 任一支持 PIT 即可 |

### 11.4 会计制度说明

Fundamentals 域 MVP 仅支持 **A 股上市公司（中国会计准则 CAS）**。

| 维度 | A 股 / CAS | 备注 |
|------|-----------|------|
| 财务报告周期 | 年报(12/31) + 一季报(3/31) + 半年报(6/30) + 三季报(9/30) | 与美股 Q1-Q4 不同 |
| 财报披露截止 | 年报 4/30，一季报 4/30，半年报 8/31，三季报 10/31 | 影响 data_freshness 判断 |
| 货币 | CNY（人民币元） | 不做汇率转换 |
| 代码格式 | ts_code（`000001.SZ`, `600000.SH`） | 与 AlphaDB/tinydata 一致 |
| 行业分类 | 申万行业分类（SWHY）为主 | `rawdata.stock_industry_versioned` |
| PE 计算 | PE(TTM) = 总市值 / 归母净利润(TTM) | 与 AlphaDB `stock_dailybasic.pe_ttm` 一致 |
| ROE | 加权 ROE（归母口径） | `fina_indicator.roe_dt`（扣非加权）|

### 11.5 数据新鲜度判断（A 股适配）

data_freshness 判断改为基于 A 股财报披露日历：

| 最新报告期 | 正常窗口 | 过期阈值 | stale 阈值 |
|-----------|---------|---------|-----------|
| Q4 年报 (12/31) | ≤ 4/30 披露 | > 90 天 | > 180 天 |
| Q1 季报 (3/31) | ≤ 4/30 披露 | > 90 天 | > 150 天 |
| Q2 半年报 (6/30) | ≤ 8/31 披露 | > 90 天 | > 150 天 |
| Q3 季报 (9/30) | ≤ 10/31 披露 | > 90 天 | > 150 天 |

实际判断逻辑：取 `fina_disclosure.actual_date`（实际披露日），距今 > 90 天触发 flag #1，> 180 天触发 flag #2。

### 11.6 Mock 策略（A 股适配）

MVP 阶段允许 mock 数据源（JSON/parquet fixture files），但 mock 数据必须：
- 使用真实 A 股公司（如 000001.SZ 平安银行、600519.SH 贵州茅台）
- 遵循 CAS 会计准则的字段名和数据结构
- 包含至少 8 个季度历史（满足 TTM + 3y CAGR 计算）
- 覆盖 happy path + 降级场景（见 §12 Mock 策略）
```

---

## Task 2：新增 §11A Adapter 架构规格

在 §11 之后新增 §11A，定义统一的数据源 Adapter 接口。

### §11A 内容

```markdown
## 11A. Data Source Adapter Architecture

### 11A.1 设计原则

Fundamentals 域不直接依赖 AlphaDB 或 tinydata 的实现细节。所有数据获取通过统一的 Adapter 接口完成。

```text
Fundamentals Domain
    ↓ 调用
DataAdapter Interface (abstract)
    ├── AlphaDBAdapter (离线主力)
    └── TinyDataAdapter (实时补充)
    ↓ 实现
AlphaDB PostgreSQL / tinydata TS-OPI
```

### 11A.2 Adapter 接口定义（伪代码）

```python
class FinancialDataAdapter(Protocol):
    """统一数据源适配器接口。"""

    def get_financial_statements(
        self, ts_code: str, report_periods: list[str], *, as_of_date: str | None = None
    ) -> FinancialStatements:
        """获取利润表+资产负债表+现金流量表。
        
        Args:
            ts_code: 股票代码（如 000001.SZ）
            report_periods: 报告期列表（如 ["20251231", "20250930", ...]）
            as_of_date: PIT 截止日期（可选），仅返回该日期前已披露的数据
        
        Returns:
            FinancialStatements dataclass
        """
        ...

    def get_financial_indicators(
        self, ts_code: str, report_periods: list[str]
    ) -> FinancialIndicators:
        """获取综合财务指标（ROE, ROIC, 毛利率等）。"""
        ...

    def get_daily_market_data(
        self, ts_code: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """获取日线行情（OHLCV + 复权因子）。"""
        ...

    def get_valuation_data(
        self, ts_code: str, start_date: str, end_date: str
    ) -> pd.DataFrame:
        """获取每日估值数据（PE, PB, 总市值, 流通市值）。"""
        ...

    def get_industry_peers(
        self, ts_code: str, trade_date: str
    ) -> list[str]:
        """获取同行业公司的 ts_code 列表。"""
        ...

    def get_trade_calendar(
        self, start_date: str, end_date: str
    ) -> list[str]:
        """获取交易日列表。"""
        ...

    def get_disclosure_dates(
        self, ts_code: str, report_periods: list[str]
    ) -> dict[str, str]:
        """获取各报告期的实际披露日期。PIT 语义。"""
        ...


@dataclass
class FinancialStatements:
    """三张财务报表的聚合结果。"""
    income: pd.DataFrame          # 利润表
    balance_sheet: pd.DataFrame   # 资产负债表
    cash_flow: pd.DataFrame       # 现金流量表
    source: str                   # "alphadb" | "tinydata" | "mock"
    as_of_date: str | None        # PIT 截止日期


@dataclass
class FinancialIndicators:
    """综合财务指标。"""
    indicators: pd.DataFrame      # fina_indicator 数据
    source: str
```

### 11A.3 Adapter 选择策略

```text
function select_adapter(requirement: DataRequirement) -> FinancialDataAdapter:
    // 1. 实时行情需求 → tinydata
    if requirement.is_realtime:
        return TinyDataAdapter()
    
    // 2. 历史批量需求 → AlphaDB 优先
    if requirement.date_range_days > 30:
        if AlphaDBAdapter.is_available() and AlphaDBAdapter.data_freshness_ok(requirement):
            return AlphaDBAdapter()
        else:
            return TinyDataAdapter()  // fallback
    
    // 3. 行业对标/聚合查询 → AlphaDB（SQL 聚合效率更高）
    if requirement.is_aggregate:
        return AlphaDBAdapter()
    
    // 4. 默认 → AlphaDB
    return AlphaDBAdapter()
```

### 11A.4 Adapter 实现约束

1. **不暴露底层实现细节**：Adapter 返回统一的 dataclass/DataFrame，不返回 SQLAlchemy Row 或 TSL 原始响应
2. **不硬编码连接信息**：AlphaDB 使用 `~/.alphahome/config.json`，tinydata 使用环境变量
3. **不打印敏感信息**：不暴露数据库 URL、密码、API token
4. **错误统一映射**：底层异常映射为 `DataSourceError` / `DataSourceTimeoutError` / `DataSourceUnavailableError`
5. **PIT 语义透传**：`as_of_date` 参数必须透传到底层数据源的 PIT 机制（AlphaDB `fina_pit_ext`，tinydata `as_of_date` 参数）

### 11A.5 项目依赖关系

```text
crosslens/
  fundamentals/
    adapters/
      __init__.py
      base.py          # FinancialDataAdapter Protocol
      alphadb.py       # AlphaDBAdapter
      tinydata.py      # TinyDataAdapter
      mock.py          # MockAdapter（测试用）
```

CrossLens 项目通过 `pip install -e` 或 `sys.path` 引用：
- `E:\CodePrograms\alphaHome`（`alphahome` 包）
- `E:\CodePrograms\tinydata`（`tinydata` 包）

两个依赖包均独立维护，CrossLens 不修改它们的代码。
```

---

## Task 3：§12 MVP Scope 修正

### 需要修改的部分

1. **§12 MVP Scope → MVP 不交付 第 3 条**：

将：
```
3. ❌ 多市场适配（MVP 仅支持 US 市场，GAAP 会计准则）
```
改为：
```
3. ❌ 多市场适配（MVP 仅支持 A 股市场，中国会计准则 CAS，申万行业分类）
```

2. **§12 Mock 策略**（如果存在 US 市场相关的 mock 示例）：

确保 mock 数据引用 A 股公司代码（如 `000001.SZ`、`600519.SH`）而非 US ticker（如 `AAPL`、`NVDA`）。

3. **§2 域目标与边界**：

检查是否有隐含 US 市场的描述，统一改为 A 股。

4. **§4 Metric Catalog 中每个 metric 的 Metric Registry JSON**：

将 `unit` 从 USD 语义改为 CNY 语义（如 `market_cap` 单位从 `USD` 改为 `CNY`，如果有此类标注的话）。

5. **全文搜索并替换**：

- `US` → `A 股` 或 `中国 A 股`（仅在市场上下文中）
- `GAAP` → `CAS`（中国会计准则）
- `SEC EDGAR` → `巨潮资讯 / 上交所 / 深交所`
- `Yahoo Finance` → 删除（AlphaDB + tinydata 已覆盖）
- `SEC filing` → `A 股定期报告`
- 所有 `AAPL`、`NVDA` 等 US ticker → `000001.SZ`、`600519.SH` 等 A 股代码

---

## Task 4：§3.2 Evidence Packet 定义适配

检查 §3.2 各 Evidence Packet 类型中的字段是否与 AlphaDB/tinydata 的实际字段对齐。

### 需要确认的对齐项

| SPEC-013 字段 | AlphaDB 实际字段 | tinydata 实际字段 | 说明 |
|---|---|---|---|
| `revenue_growth_ttm` | 需从 `fina_income.operating_revenue` 计算 | 需从 `td.fina_income()` 计算 | TTM = 最近 4 季度之和 |
| `gross_margin_ttm` | 需从 `fina_income.operating_revenue` - `operating_cost` 计算 | 同上 | 或直接用 `fina_indicator.grossprofit_margin` |
| `pe_percentile_5y` | 需从 `stock_dailybasic.pe_ttm` 历史序列计算 | 需多次调用 `td.stock_daily()` 计算 | 5 年 ≈ 1250 个交易日 |
| `roe_ttm` | `fina_indicator.roe_dt`（加权 ROE） | `td.fina_indicator()` 同字段 | 确认字段名一致 |
| `fcf_margin_ttm` | 需从 `fina_cashflow.n_cashflow_act` - `fina_cashflow.c_cap_ex` 计算 | 同上 | A 股现金流量表字段名需确认 |
| `net_debt_to_ebitda` | 需从 `fina_balancesheet` + `fina_indicator` 组合计算 | 同上 | EBITDA 可能需要手动计算 |

**对每个字段**：在 §3.2 对应小节的"公式"或"说明"中添加 AlphaDB 字段映射注释，例如：

```
// AlphaDB 映射：fina_income.operating_revenue（营业收入）
// tinydata 映射：td.fina_income() 返回的 operating_revenue 列
// 注意：A 股利润表的"营业收入"字段名与美股 "Revenue" 语义一致
```

不需要修改字段名或公式本身——只需要添加数据源映射注释。

---

## 全局约束

1. **不修改上游 SPEC**（SPEC-003/004/005/006/007/009）
2. **不修改 SPEC-REGISTRY.md 中 SPEC-013 以外的行**
3. **不修改任何代码文件**（这是规格文档修改，不是代码实现）
4. **不创建 Adapter 实现代码**——只定义接口规格（伪代码/Protocol）
5. **保留已有的正确内容**：§5 Internal Pipeline、§6 Determinism Map、§7 Stance Logic、§8 Confidence Model、§9 Card Assembly、§10 Domain Validation 中不涉及市场/会计准则的部分保持不变
6. **枚举一致性**：不引入新枚举值，所有枚举引用保持与 SPEC-REGISTRY 一致
7. **版本号嵌入文件名**：重命名文件为 `v0.2.0.md`

---

## 验收标准

- [ ] §11 完全重写，覆盖 5 类数据源 → AlphaDB + tinydata 双源架构
- [ ] §11A 新增 Adapter 架构规格（接口定义 + 选择策略 + 实现约束）
- [ ] §12 MVP Scope 从 "US 市场，GAAP" 改为 "A 股市场，CAS"
- [ ] 全文无 "US 市场"、"GAAP"、"SEC EDGAR"、"Yahoo Finance" 等美股引用（除非在"不做"列表中明确排除）
- [ ] 示例代码中的 ticker 全部为 A 股代码（000001.SZ、600519.SH 等）
- [ ] §3.2 Evidence Packet 定义添加了 AlphaDB/tinydata 字段映射注释
- [ ] §4 Metric Catalog 中的公式未改变（只添加数据源映射注释）
- [ ] §5~§10 不涉及市场/会计准则的部分未改变
- [ ] 全量测试无回归（197 tests all green）
- [ ] 文件重命名为 v0.2.0.md
- [ ] SPEC-REGISTRY.md 中 SPEC-013 行更新为 v0.2.0 + Review 状态

---

## 向用户汇报模板

```markdown
## SPEC-013 v0.2.0 A 股数据源重构 — 完成报告

### Task 1: §11 数据源重写
- [完成/未完成]
- AlphaDB 映射 X 个数据需求
- tinydata 映射 X 个数据需求

### Task 2: §11A Adapter 架构
- [完成/未完成]
- FinancialDataAdapter Protocol 定义
- AlphaDBAdapter + TinyDataAdapter 规格
- 选择策略 + 实现约束

### Task 3: §12 MVP Scope 修正
- US/GAAP → A 股/CAS
- 全文 ticker 替换
- 其他引用清理

### Task 4: §3.2 数据源映射注释
- X 个 Evidence Packet 类型添加了 AlphaDB/tinydata 字段映射

### 测试结果
- spec003: X tests passed
- spec004: X tests passed
- spec005: X tests passed
- spec006: X tests passed
- spec009: X tests passed
- Total: X tests, all green

### Registry 同步
- SPEC-013 行：v0.2.0, Review
- 文件重命名：v0.1.2.md → v0.2.0.md

### 下一步
- SPEC-013 已升级为 Review
- 可编写 plan/tasks-fundamentals.md（含 Adapter 实现任务）
```
