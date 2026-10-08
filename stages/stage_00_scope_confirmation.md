# Stage 00 — 启动硬门（范围确认）

- **主导角色**：Orchestrator
- **输入**：5 类材料（① 项目背景 ② 战略材料 ③ 价值流清单 ④ 业务能力框架 ⑤ 干系人清单）+ 用户确认交付格式
- **输出**：`requirement.json`（`scope_confirmed=true`，materials inventory 带路径与格式，data_gaps[]）
- **确认点**：材料齐全 + HTML/docx 双格式 + 项目元信息（未确认不得 init）
- **质量门**：材料缺失必须显式 data gap；`scope_confirmed` 非 true 不得 init；`init` 拒绝覆盖非空项目目录
