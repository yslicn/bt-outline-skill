# Stage 02 — 规划（N 份提纲 + 方向 + 预期信息）

- **主导角色**：Interview Drafter（Architect 复核拆分逻辑）
- **输入**：`input_baseline.json`（locked）
- **输出**：`interview_plan.json`
- **确认点**：做几份 + 每份方向 + 预期收集信息（**方向门，可迭代 REVISE**；M1 7→9 教训落点）
- **质量门**：
  - 机器门：每份覆盖非空、合并覆盖全部价值流与关键 L2、引用存在、id 唯一
  - Architect 门：拆分逻辑自洽性（维度同一/边界互斥/MECE）、预期信息与战略关注议题（含待核实取舍）对应
  - 业务专家门：访谈方向业务上可答、被访对象对得上
  - 用户门：份数与方向；REVISE 时记录 `split_rationale` 变更

- v1.1内容门：遵循 `methodology/neutral_questioning.md`；输入判断保留核实状态，不把行业现象升级为企业事实。允许无问题、否定、未知与保留现状；主问单点、追问按条件；逐题修订须检查正文和probe确实改变。
