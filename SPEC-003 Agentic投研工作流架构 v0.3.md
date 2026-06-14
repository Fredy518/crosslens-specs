# SPEC-003：Agentic 投研工作流架构

**版本：** v0.3  
**状态：** Draft  
**项目名称：** crosslens  
**依赖文档：** SPEC-001 v0.3  
**文档类型：** 架构规格  
**目标阶段：** 产品机制设计 / MVP 架构定义  

---

## 1. 文档目标

SPEC-003 用于定义 crosslens 的 Agentic 投研工作流架构。

本 SPEC 重点回答：

1. 用户输入如何被标准化为系统任务；
2. 编排器调度的基本单元是什么；
3. 全局 Workflow 节点如何组织；
4. 编排器与五个分析能力域之间如何交互；
5. Evidence Packet、Analysis Card、Validation Report、Conflict Report、Playbook Evaluation Report、Guardrail Report、Resolved Decision Bounds、Decision Candidate、Decision Trace 如何流转；
6. Investment Playbook 在工作流中如何介入；
7. Evaluator、Guardrail、Human-in-the-loop 在哪里介入；
8.