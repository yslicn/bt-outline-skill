# 能力域对齐规则（两级映射）

访谈提纲的信息收集必须与业务能力架构一一对应。采用**场级 + 块级**两级标注，禁止逐题堆标签。

## 场级标注（interview-header）

每场标题下挂：
- **VS tag**：该场覆盖的价值流，格式 `VS<n> <价值流全名>`（tag-blue）。
- **层 tag**：该场覆盖的层 + L2/L3 计数，格式 `<层> · <N>项L2 · <N>项L3`（tag-teal）。层取"战略/核心/支持"。

计数口径：该场所有 discussion-block 引用的 L2 去重数、L3 去重数（L3 枚举的算名称数，L3 计数的算 count）。

## 块级标注（discussion-block）

P2/P3 的每个 discussion-block 挂 `capability-ref`：
- L3 ≤ 4 个：枚举 L3 名称，如 `L2：售后服务 → 维修作业管理 · 配件管理`。
- L3 > 4 个：用计数，如 `L2：线索管理 → 4项L3`。

块级 capability-ref 的 L2 必须与块标题语义一致（块标题是对该能力域的展开）。

## 引用完整性（机器门）

- 每个问题 `vs_refs` / `capability_refs` 引用的 id 必须存在于阶段01基底（`value_streams` / `capability_model` 的 L2/L3）。
- 场级 tag 计数与块级引用去重后的结果必须一致（Architect 门核对无漂移）。
- 引用不存在的 id = 机器校验拒绝。

## 双视图

以上标注保留在JSON与访谈员版；客户版默认隐藏VS/L2/L3、计数和能力域映射，使用自然业务标题。映射只证明覆盖，不能证明客户存在该团队或采用该机制。
