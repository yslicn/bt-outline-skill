# 产物契约

## JSON 是唯一结构化数据源

- 每个阶段的正式 JSON 是该阶段唯一结构化数据源；材料陈述和假设仍须保留核实状态，锁定不等于事实已验证。MD/HTML/docx只能由runtime生成，禁止手工编写。
- JSON 变更后，旧评审自动失效：必须重新 `submit`（重新校验 + 重新计算 SHA-256）并重审，才可 `approve`。

## 阶段产物链

```text
requirement.json ──(scope_confirmed)──▶ input_baseline.json
                                              │ (locked)
                                              ▼
                                          interview_plan.json
                                              │ (locked，可 REVISE 迭代)
                                              ▼
                                        interview_guide_full.json
                                              │ (locked)
                                              ▼
                                        render_input.json（确定性投影，runtime 生成）
                                              │
                                              ▼
                              index.html + NN_*.html + shared-style.css
                              index.docx + NN_*.docx
```

## SHA-256 绑定

- 每个阶段 artifact 绑定 `artifact_sha256`。
- MD 投影头部 `<!-- source_sha256: <hash> -->` 绑定对应 JSON。
- 阶段04 的候选交付包：`candidate_manifest.json` 绑定全部文件（render_input + HTML + docx + css）的 hash + `source_guide_full_sha256`。

## 原子发布

- `release` 将候选包原子复制到 `deliverables/`，并写 `quality_report.json` + `release_manifest.json`。
- 未通过"双评审 PASS + 用户确认 + hash 绑定"不得 release。

## 同源约束

- HTML 与 docx 必须消费**同一** `render_input.json` 渲染，不得分别手工编写（机器门校验 source sha 一致）。

## v1.1双视图与修订

根目录HTML/docx为客户版，interviewer/为访谈员版，两版从同一render_input投影，全部文件进入candidate_manifest并绑定hash。客户版隐藏内部字段，不修改主问。

阶段03逐题意见保存在review/issues_<role>.json，重提交不清空未关闭issue。REVISE绑定问题ID与修改前正文/probe，PASS核对当前after；只有元信息改动不能标记resolved。不适用关闭须有解释，由独立评审者承担判断。格式见runtime_commands.md。
