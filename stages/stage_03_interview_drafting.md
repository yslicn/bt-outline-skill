# Stage 03 — 生成（每份五层递进全文）

- **主导角色**：Interview Drafter
- **输入**：`interview_plan.json` + `input_baseline.json`（均 locked）
- **输出**：`interview_guide_full.json`
- **确认点**：每份可读、无敏感问题
- **质量门**：
  - 机器门：guides id 集 == plan interviews id 集；P1-P5 齐全且顺序正确；P2 必含 discussion-block；P4 引导词 == "引导思考"、P1/2/3/5 == "追问"；每问题至少 1 个 vs_ref/capability_ref 且引用存在于基底；expected_output 非空
  - Architect 门：五层递进逻辑、各层写作规则、能力标注与块标题一致
  - 业务专家门：问题贴近业务、被访对象答得出、挑战与机会探索踩真实行业场景
  - 用户门：每份可读、无敏感问题

- v1.1内容门：遵循 `methodology/neutral_questioning.md`；输入判断保留核实状态，不把行业现象升级为企业事实。允许无问题、否定、未知与保留现状；主问单点、追问按条件；逐题修订须检查正文和probe确实改变。

- v1.2可答性门：以用户认可的详细业务描述为颗粒度参考；只看客户版能否知道对象、情境和回答范围。不以字数短、术语少或无枚举判高质量。中立但空泛须REVISE。具体采集维度（如系统支撑、换型时间、统计口径、承诺与执行对照）不能在中立化中丢失；按角色解释术语，未知机制先求证。
