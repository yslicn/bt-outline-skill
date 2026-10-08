<div align="center">

# BT Outline

### 变革项目访谈提纲生成器

**把"访谈提纲"从一次性手写稿，升级为受 5 类输入、双独立评审与用户确认门共同约束的确定性生产线。**

![Type](https://img.shields.io/badge/type-Claude%20Skill-0B6E4F?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Runtime](https://img.shields.io/badge/runtime-stdlib--only-1F2937?style=for-the-badge)
![Output](https://img.shields.io/badge/output-HTML%20%2B%20docx-1F3864?style=for-the-badge)
![License](https://img.shields.io/badge/license-Apache--2.0-555555?style=for-the-badge)

</div>

<p align="right">
  <a href="README_EN.md">English</a>
</p>

---

## ⚠️ 适用范围与使用限制

> **本 skill 采用「用途场景限定」的授权方式：它只能用于一个场景——变革项目的访谈提纲设计。超出该场景的使用不受支持，也不在其质量门保护范围之内。**

### ✅ 允许的使用场景

- **变革项目的访谈提纲（信息采集设计）**：BC/流程变革/数智化转型等项目中，为一批访谈对象设计结构化访谈问题。
- 基于**价值流 / 业务能力框架 / 干系人清单**做访谈拆分与问题分层。
- 输出 `index + N 份提纲` 的 HTML 与 docx 双格式候选交付包，供人工评审与客户沟通。
- 为已有访谈提纲做**结构化重构**（补齐五层递进、补齐能力域映射、发现覆盖缺口）。

### ❌ 明确禁止的使用场景

本 skill **只做信息采集设计**，以下内容它既不做、写出来也不可信，禁止把它的输出当作这些内容的交付物：

| 禁止用途 | 为什么 |
|---|---|
| 流程优化方案 / 目标流程设计 | 本 skill 无目标态建模能力，输出的是问题清单不是方案 |
| 系统架构 / IT 蓝图 / 实施路线图 | 不在方法论范围内，无对应质量门 |
| 组织设计与岗位职责设计 | 同上 |
| 业务诊断结论 / 痛点定级 / 成熟度评估 | 会退化为"先有结论再凑问题"，与方法论红线冲突 |
| KPI 词典 / 指标体系建设 | 同上 |
| 一般性问卷、市场调研问卷、员工满意度调查 | 非变革项目访谈语境，五层递进与能力映射不适用 |
| 干系人诉求的**分析**（而非采集设计） | 分析属下游架构工作，本 skill 止于采集 |

### 使用前提

- 需由**具备业务架构方法论基础的顾问**驱动：拆分逻辑（`methodology/interview_split_logic.md`）是最高优先规则，误用会产出语法正确、业务错误的提纲。
- 5 类输入材料必须齐全（缺项须显式登记为 `data gap`，不得静默忽略）。
- **不得绕过双评审与用户确认门**；不得把未经 `release` 的候选包对外交付。

---

## 这是什么

BT Outline 是一套面向咨询交付的 Claude Skill。它把已验证过的「变革项目访谈提纲」生产方法，固化为一条受输入材料、JSON Schema、运行时门禁、双独立评审与用户确认共同约束的确定性流程。

它不是"让模型写一份看起来专业的问卷"。它控制的是：模型基于**哪些证据**提问、提纲**在哪一关可以往下走**、谁做**独立复核**、返工能改动哪些路径、以及最终的 HTML 与 docx 如何从**同一个 JSON 事实源**确定性生成。

## 它解决什么问题

访谈提纲"写起来快、写好很难"。真实困难从来不是措辞，而是拆分逻辑与覆盖完整性：

- 提纲容易被写成"每个部门问几句"，缺少互斥的拆分维度，访谈之间重叠或留白；
- 问题容易停在事实确认层，缺少"现状 → 案例 → 挑战与机会 → 保留与改进"的递进，访谈白白浪费一小时；
- 能力框架与价值流常常只被"贴"在提纲标题上，问题里其实没有真正对应；
- 多轮返工可能悄悄改动已锁定内容，无法证明"谁基于哪个版本做了什么判断"；
- 问题若脱离输入材料，会凭空虚构不存在的业务事实和访谈对象。

设计原则：**模型负责专业判断，Runtime 负责不变量；评审员负责反例挑战，用户负责最终裁决。**

## 工作流程

### 启动硬门（`init` 前置）

必须先确认 5 类输入材料与交付格式，未确认不得 `init`：

1. **项目背景**（客户 / 行业 / 变革主题 / 范围）
2. **战略材料**（战略报告 PDF/PPT/doc）
3. **价值流清单**
4. **业务能力框架**（如 TOGAF 三层 L1/L2/L3）
5. **干系人清单**

以及交付格式：**HTML + docx 双格式**。缺的材料必须显式登记为 `data gap`。

### 四个阶段（逐门推进，不可合并）

| 阶段 | 主导角色 | 核心确认点 |
|---|---|---|
| **01 解析输入** | Architect | 信息基底：价值流 / 能力框架 / 干系人 / 战略关注议题（含待核实取舍） |
| **02 规划** | Interview Drafter | N 份提纲 + 每份方向 + 预期信息（**方向门，可 REVISE 迭代**） |
| **03 生成** | Interview Drafter | 每份五层提纲全文 + 两级能力标注 |
| **04 汇编渲染发布** | Orchestrator + Python | `index` + N 份 HTML+docx 候选交付包 |

每个阶段都必须走完固定序列，缺一不可：

```
设计 → 机器校验 → Architect 独立评审 → 业务专家独立评审 → 用户确认 → hash 锁定
```

其中 **02 规划与 03 生成必须分开**——拆分逻辑是可迭代的方向门，是最容易出错、也最值得先对齐的一步。

## 产出物

阶段 04 由 `render_input.json`（唯一渲染源）确定性编译出正式交付包：

```text
deliverables/
├── render_input.json          # HTML 与 docx 的唯一渲染源
├── index.html                 # 总览
├── NN_<标题>.html             # N 份提纲
├── shared-style.css           # IBM Design System
├── index.docx                 # 与 HTML 同源
├── NN_<标题>.docx
├── quality_report.json
└── release_manifest.json      # 绑定全部文件 hash
```

**HTML 与 docx 必须同源**（同一 `render_input.json`），不得分别手工编写。

## 快速开始

安装（作为 Claude Skill）：

```bash
git clone https://github.com/yslicn/bt-outline-skill.git ~/.claude/skills/bt-outline-skill
```

启动项目：

```bash
python3 scripts/ig_runtime.py init <project_dir> \
  --name <项目名> --client <客户> --industry <行业> --theme <变革主题>
```

每个阶段重复固定序列：

```bash
python3 scripts/ig_runtime.py start   <project_dir> --stage <stage_id>
python3 scripts/ig_runtime.py submit  <project_dir> --stage <stage_id>
python3 scripts/ig_runtime.py review  <project_dir> --stage <stage_id> --role architect       --decision PASS
python3 scripts/ig_runtime.py review  <project_dir> --stage <stage_id> --role business_expert --decision PASS
python3 scripts/ig_runtime.py approve <project_dir> --stage <stage_id>
```

阶段 04 专属（渲染 → 双评审 → 确认 → 发布）：

```bash
python3 scripts/ig_runtime.py render  <project_dir>
python3 scripts/ig_runtime.py approve <project_dir> --stage stage_04_rendering_release
python3 scripts/ig_runtime.py release <project_dir>
```

只读校验：

```bash
python3 scripts/ig_runtime.py validate <project_dir>
```

完整命令与状态流转见 `reference/runtime_commands.md`。

## 目录结构

```text
SKILL.md                      # 主入口：流程、角色路由、红线
agents/                       # orchestrator / architect / interview_drafter / business_expert_reviewer
stages/                       # stage_00..stage_04 各阶段运行协议
methodology/                  # 五层递进、问题分层、拆分逻辑、能力域对齐
schemas/                      # 6 份 JSON Schema
reference/                    # 产物契约、模型策略、渲染规格、命令速查
scripts/                      # ig_runtime.py + quick_validate / render_html / render_docx
assets/shared-style.css       # HTML 样式（IBM Design System）
tests/                        # runtime 与 render 离线测试
```

## 四类质量门

| 门 | 检查内容 |
|---|---|
| **机器门** | schema、稳定 ID、引用完整性、五层结构、引导词规则、hash 与 MD 一致 |
| **Architect 门** | 拆分逻辑自洽性（MECE）、五层递进合规、能力域两级映射无漂移、覆盖无遗漏 |
| **业务专家门** | 问题贴近业务、行业真实性、术语、关键缺项、敏感合规 |
| **用户门** | 份数、方向、取舍与客户认可（方向门可 REVISE 迭代） |

份数与问题密度是**诊断区间**而非跨行业硬门；结构完整性与引用一致性才是硬门。

## 十二条红线（摘要）

完整清单见 `SKILL.md`。最关键的四条：

1. **未确认 5 类输入不得 `init`**——缺材料必须显式 `data gap`。
2. **评审不得自评**——产出者不得评审自己的 artifact；未绑定当前 `SHA-256` 的评审无效。
3. **JSON 是唯一事实源**——MD/HTML/docx 只能由 runtime 确定性生成；JSON 变更后旧评审失效。
4. **未确认不发布**——未通过双评审 PASS + 用户确认的候选包不得 `release`，也不得对外交付。

## 依赖

- Python **3.10+**
- runtime 与 HTML 渲染：**仅标准库**
- docx 渲染：`python-docx`

## 版本

- **v1.0**（2026-08-10）：首个版本。4 阶段流程 + 启动硬门 + HTML/docx 同源渲染 + 确定性 runtime。

## 许可

代码采用 [Apache License 2.0](LICENSE)。

使用范围另受上方[「适用范围与使用限制」](#️-适用范围与使用限制)约束：本 skill 仅限用于**变革项目的访谈提纲设计**场景。

## v1.1（2026-10-08）

改为中立采集：无问题、不适用、未知及现有做法有效均为有效信息；战略取舍/待核实挑战可为空，不凑数量；主问只问一件事，追问按回答选用。新增 `methodology/neutral_questioning.md`。

默认客户版隐藏内部映射和追问；同一JSON生成 `interviewer/` 下的访谈员版。新提纲填 `content_policy=neutral-v1`（旧schema_version=1.0兼容）。阶段03内容返工使用 `review --issues-file`，记录问题ID、修改前后主问与probe并逐项复核。代码测试不替代独立语义评审。

## v1.2（2026-10-08）

保留中立采集，同时恢复业务颗粒度。主问描述对象与情境，客户版显示context（业务说明）与answer_hints（开放式回答维度），允许术语中文解释、枚举和中立讨论锚点。隐藏的仅是顾问内部判断与条件分支，不能隐藏回答所需信息。修订after由runtime自动提取；HTML脚本可直接运行，VS矩阵沿用基底实际ID。
