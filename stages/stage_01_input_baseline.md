# Stage 01 — 解析输入（信息基底）

- **主导角色**：Architect
- **输入**：5 类材料（经 pdf/pptx/docx/Read 工具读取）+ `requirement.json`
- **输出**：`input_baseline.json`
- **确认点**：信息基底（价值流/能力框架/干系人/战略核心矛盾）准确、无关键缺项
- **质量门**：
  - 机器门：schema、id 唯一、L2/L3 归属一致、属性合法、干系人引用完整、`strategic_tensions` 3-7 条且有 `source_ref`
  - Architect 门：忠实于输入材料、战略核心矛盾可溯源、不得编造
  - 业务专家门：术语、干系人角色、价值流简称
  - 用户门：基底准确、无关键缺项
