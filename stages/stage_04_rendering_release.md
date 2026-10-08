# Stage 04 — 汇编渲染发布（候选交付包）

- **主导角色**：Orchestrator + Python（ig_runtime.py）
- **输入**：`interview_guide_full.json`（locked）+ `requirement.json`
- **输出**：`render` 确定性生成 `render_input.json` + index.html + NN_*.html + shared-style.css + index.docx + NN_*.docx + `candidate_manifest.json`
- **确认点**：完整候选交付包（Architect + 业务专家双评审后用户确认）
- **质量门**：
  - 机器门：render_input 符合 schema；HTML 与 docx 同源（同一 render_input + source sha 一致）；候选包全文件 hash 绑定 manifest；`source_guide_full_sha256` 匹配阶段03
  - Architect 门：渲染与内容同源、五层结构在 HTML/docx 完整呈现、能力映射正确
  - 业务专家门：渲染内容与阶段03一致、无排版导致的信息丢失
  - 用户门：确认候选交付包后 `approve` → `release` 原子发布到 `deliverables/`

- v1.1内容门：遵循 `methodology/neutral_questioning.md`；输入判断保留核实状态，不把行业现象升级为企业事实。允许无问题、否定、未知与保留现状；主问单点、追问按条件；逐题修订须检查正文和probe确实改变。
