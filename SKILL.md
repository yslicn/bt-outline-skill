---
name: generate-bt-outline
description: 变革项目访谈提纲生成器（BT=business transformation）。启动时先确认5类输入材料（项目背景/战略材料/价值流/业务能力框架/干系人）与HTML+docx双交付格式，再按解析输入、规划、生成、汇编渲染逐阶段执行独立评审与用户确认。直接输出 index + N 份访谈提纲的 HTML 与 docx（IBM 蓝风格）。只做信息采集设计，不输出流程优化方案或诊断结论。
---

# Generate BT Outline

本 skill 将已实战验证过的"变革项目访谈提纲"生产方法固化为确定性流程：输入 5 类标准材料，经 4 个带用户确认门的阶段，输出 index + N 份访谈提纲的 HTML + docx 双格式。它只做**信息采集设计**（访谈提纲），不输出流程优化方案、系统架构、实施路线图或诊断结论。

## 中立采集约束（v1.1）

先读 `methodology/neutral_questioning.md`。五层结构不要求找出痛点；材料没有战略矛盾时允许空集合。行业参考不等于企业事实，否定、未知、有效做法与暂不变革均为有效信息。每题用稳定id和描述清楚的主问；客户可见context与answer_hints交代业务情境和回答维度，条件追问只在对应回答后选用。

客户版保留完整主问、业务说明、术语中文括注与开放式回答维度，默认隐藏内部编码和顾问判断；同一render_input生成 `interviewer/` 中的访谈员版。阶段03修订用 `review --issues-file` 逐题登记和复核，不能只改页眉后关闭正文意见。旧schema_version=1.0保持兼容；新提纲填content_policy=neutral-v1以启用id、分支和前提引用硬门，旧锁定成果不静默改写。

## 启动硬门：先确认输入材料与交付格式

首次启用时，必须先向用户确认 5 类输入材料是否齐全，并确认交付格式；未确认不得 `init`：

1. **项目背景**（客户、行业、变革主题、范围）
2. **战略材料**（战略报告 PDF/PPT/doc）
3. **价值流清单**
4. **业务能力框架**（如 TOGAF 三层 L1/L2/L3）
5. **干系人清单**

推荐提问原文：

> 请确认本次访谈提纲项目输入：1) 项目背景（客户/行业/变革主题/范围）2) 战略材料 3) 价值流清单 4) 业务能力框架（L1/L2/L3）5) 干系人清单，是否齐全？交付格式确认 HTML + docx 双格式？缺少的材料请列出，我会标记为 data gap。

必须把选择写入 `requirement.json`（`scope_confirmed=true` + `materials[]` + `delivery_formats` + `data_gaps[]`）。缺材料必须显式登记 data gap，不得静默忽略。用户确认后运行：

```bash
python3 scripts/ig_runtime.py init <project_dir> \
  --name <project_name> --client <客户> --industry <行业> --theme <变革主题>
```

## 不可改变的咨询流程

| 阶段 | 主导角色 | 核心确认点 | 是否必做 |
|---|---|---|---|
| 00 启动硬门 | Orchestrator | 5 类输入材料齐全 + HTML/docx 双格式 + 项目元信息 | 必做（init 前置） |
| 01 解析输入 | Architect | 信息基底：价值流/能力框架/干系人/战略关注议题（含待核实取舍） | 必做 |
| 02 规划 | Interview Drafter | N 份提纲 + 每份方向 + 预期信息（**方向门，可迭代**） | 必做 |
| 03 生成 | Interview Drafter | 每份五层提纲全文 + 两级能力标注 | 必做 |
| 04 汇编渲染发布 | Orchestrator + Python | index + N 份 HTML+docx 候选交付包 | 必做 |

不得把阶段1-3合并为一次性生成，尤其**规划（02）与生成（03）必须分开**（拆分逻辑是用户可迭代的方向门）。每个范围内阶段都必须完成：设计 → 机器校验 → Architect 独立评审 → 业务专家独立评审 → 用户确认 → hash 锁定。阶段04 的评审对象是包含 render_input、HTML 与 docx 的同一候选交付包；Architect 与业务专家均 PASS 后才可进入用户评审。

## 每次恢复项目

1. 读取 `requirement.json` 与 `project_state.json`。
2. 运行 `python3 scripts/ig_runtime.py validate <project_dir>`。
3. 从首个未锁定的阶段恢复。
4. 只读取该阶段列明的输入 JSON、对应 agent 文件和方法论；不注入完整历史对话。
5. 锁定成果只从 JSON 读取。MD/HTML/docx 是 JSON 的确定性投影，不得手写修改。

## 阶段运行协议

1. 读取 `stages/stage_0X_*.md`。
2. 激活主导角色，按固定 schema 生成该阶段正式 JSON。
3. 运行 `python3 scripts/ig_runtime.py submit <project_dir> --stage <stage_id>`；命令会校验 JSON、生成 MD、计算 SHA-256 并进入内部评审。
4. Architect 与业务专家分别在隔离上下文评审同一 SHA-256；用 `review` 命令记录。
5. 两类评审均 PASS 后，状态自动进入 `user_review`，向用户呈现生成的 MD。
6. 用户确认后运行 `approve`；若 JSON 在评审后变化，命令必须拒绝锁定并要求重审。
7. 阶段04 使用 `render` 直接生成候选交付包；Architect 与业务专家通过后用户确认，再用 `release` 原子发布。

命令示例见 `reference/runtime_commands.md`。

## 角色与模型路由

| 工作 | 默认执行 | 说明 |
|---|---|---|
| 编排、启动硬门、阶段推进、用户确认门 | 当前对话模型 | 少量高价值判断 |
| 信息基底解析、规划初稿、提纲初稿 | 强推理模型（Claude 强档） | 拆分逻辑与五层质量高度依赖推理 |
| Architect 独立评审（方法论门） | 隔离上下文 subagent（强推理模型） | 不得产出者自评 |
| 业务专家 Reviewer（内容门） | 隔离上下文 subagent | 高风险冲突升级当前对话模型 |
| MD、统计、引用完整性、状态门、HTML/docx 渲染 | Python（ig_runtime.py） | 禁止交给模型手工同步 |

完整策略见 `reference/model_policy.md`。模型不可用时可使用当前模型，但必须在 `project_state.json.runs[]` 记录实际模型，不得降低质量门。

## 正式数据源与交付

阶段 JSON 是各阶段唯一结构化数据源（记录材料陈述与核实状态，不等于事实已验证）。阶段04 编译出正式交付包：

```text
deliverables/render_input.json
deliverables/index.html
deliverables/NN_<标题>.html          # N 份，编号 01..NN
deliverables/shared-style.css
deliverables/index.docx
deliverables/NN_<标题>.docx
deliverables/interviewer/index.html
deliverables/interviewer/NN_<标题>.html
deliverables/interviewer/shared-style.css
deliverables/interviewer/index.docx
deliverables/interviewer/NN_<标题>.docx
deliverables/quality_report.json
deliverables/release_manifest.json
```

`render_input.json` 是 HTML 与 docx 的唯一渲染源。HTML/docx 由 `ig_runtime.py render` 确定性生成；每个候选文件绑定 hash，候选清单再绑定全部文件 hash 与 `source_guide_full_sha256`。**HTML 与 docx 必须同源（同一 render_input），不得分别手工编写。**

## 四类质量门

- **机器门**：schema、稳定 ID、引用完整性（vs/capability 引用存在于基底）、五层结构、引导词规则、hash 与 MD 一致。
- **Architect 门**：拆分逻辑自洽性（MECE）、五层递进合规、能力域两级映射无漂移、覆盖无遗漏。
- **业务专家门**：问题贴近业务、行业真实性、术语、关键缺项、敏感合规。
- **用户门**：份数、方向、取舍和客户认可（方向门可 REVISE 迭代）。

份数与问题密度是诊断区间，不是跨行业绝对硬门；偏离时记录理由，由 Architect 判断。结构完整性和引用一致性才是硬门。

## 方法论与规则来源

- 中立提问与现场可用性：`methodology/neutral_questioning.md`
- 五层递进结构：`methodology/five_layer_progression.md`
- 问题分层与引导词：`methodology/question_layer_design.md`
- 能力域两级对齐：`methodology/capability_alignment.md`
- 访谈拆分逻辑（最高优先）：`methodology/interview_split_logic.md`
- 产物契约：`reference/artifact_contract.md`
- 阶段 JSON 结构速查：`reference/stage_json_contracts.md`
- 渲染规格：`reference/rendering_spec.md`

Agent、Stage 和评审清单只引用这些规则，不复制另一套阈值或定义。冲突时以 schema 和上述方法论文件为准，并登记冲突，不得静默选择。

## 红线

1. 未确认 5 类输入材料不得 `init`（启动硬门；缺材料必须显式 data gap）。
2. 不合并阶段：4 个阶段逐门推进，尤其规划（02）与生成（03）必须分开，拆分逻辑须经用户方向门。
3. 评审不得自评：产出者不得评审自己产出的 artifact；双评审隔离上下文，未绑定当前 artifact SHA-256 的评审无效。
4. JSON 是唯一事实源：MD/HTML/docx 只能由 runtime 确定性生成；JSON 变更后旧评审失效，必须重新 `submit` + 重审。
5. 内容不得编造：提纲问题必须基于输入材料（战略报告/价值流/能力框架/干系人）；无法支撑处标注 data gap，不得凭空虚构业务事实或访谈对象。
6. 拆分逻辑必须自洽：访谈拆分必须有明确互斥维度（M1 教训：GTM vs 营销推广、渠道 vs 销售是两套能力体系），不得"先定数量再凑理由"；REVISE 时记录理由。
7. 未确认不发布：未通过双评审 PASS + 用户确认的候选包不得 `release`，也不得对外交付（含共享目录/GitHub）。
8. 敏感问题红线：不写入让被访者不适或泄露顾问内部判断的问题；P4引导词用"引导思考"；不得用标签替代前提审查，全文及probe均须允许否定回答。
9. 五层结构不可裁剪：任何一份提纲必须含 P1-P5（用户明确豁免并记录例外除外）。
10. 不输出范围外内容：本 skill 只做信息采集设计，不输出流程优化方案、系统架构、实施路线图、KPI 词典或诊断结论。
11. 渲染与内容同源：HTML 与 docx 必须同源（同一 `render_input.json`），不得分别手工编写。
12. 模型路由必须记录：`runs[]` 记录实际模型，不得因换模型降低质量门。

## 版本记录

- v1.2（2026-10-08）：纠正过度短问和客户版回答提示丢失；允许可见业务情境、专业术语括注、枚举维度及中立锚点；降低修订录入成本，修复HTML直接运行与VS缺号重编号。

- v1.1（2026-10-08）：中立采集规则、短主问与条件追问、取消战略矛盾最低数量、客户/访谈员同源双视图、逐题修订证据门。

- v1.0（2026-08-10）：首个版本。从汽车行业流程变革项目实战固化 4 阶段流程 + HTML/docx 渲染 + 确定性 runtime。
