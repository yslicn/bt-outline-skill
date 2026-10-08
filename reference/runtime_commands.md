# Runtime 命令速查

所有命令以项目目录为第一个参数。命令由 `scripts/ig_runtime.py` 提供。

## 阶段运行协议（每阶段固定序列）

```bash
# 1. 启动硬门（仅在 init 时一次）
python3 scripts/ig_runtime.py init <project> --name <名称> --client <客户> --industry <行业> --theme <变革主题>

# 2. 每个阶段重复以下序列
python3 scripts/ig_runtime.py start <project> --stage <stage_id>
python3 scripts/ig_runtime.py submit <project> --stage <stage_id>     # 校验JSON+生成MD+计算SHA→进入内部评审
python3 scripts/ig_runtime.py review <project> --stage <stage_id> --role architect --decision PASS|REVISE --notes "..."
python3 scripts/ig_runtime.py review <project> --stage <stage_id> --role business_expert --decision PASS|REVISE --notes "..."
python3 scripts/ig_runtime.py approve <project> --stage <stage_id>    # 用户确认；REVISE会清评审回炉

# 3. 阶段04 专属
python3 scripts/ig_runtime.py render <project>                        # 投影render_input + 生成HTML/docx候选包 → 自动submit
python3 scripts/ig_runtime.py review <project> --stage stage_04_rendering_release --role architect --decision PASS|REVISE
python3 scripts/ig_runtime.py review <project> --stage stage_04_rendering_release --role business_expert --decision PASS|REVISE
python3 scripts/ig_runtime.py approve <project> --stage stage_04_rendering_release
python3 scripts/ig_runtime.py release <project>

# 4. 只读校验与记录
python3 scripts/ig_runtime.py validate <project> [--stage <stage_id>]
python3 scripts/ig_runtime.py log-run <project> --stage <stage_id> --role <role> --model <model> --task <task>
```

## 阶段 id

`stage_00_scope_confirmation` / `stage_01_input_baseline` / `stage_02_interview_planning` / `stage_03_interview_drafting` / `stage_04_rendering_release`

## 状态流转

- `submit`：pending/in_progress → `internal_review`
- `review`：两角色全 PASS → `user_review`；任一 REVISE → `in_progress`（清评审回炉）
- `approve`：仅 `user_review` 可确认 → `locked`；JSON/候选包在评审后变化则拒绝
- `render`：阶段04 生成候选包并自动 submit → `internal_review`
- `release`：仅阶段04 `locked` 可发布

## v1.1 逐题内容修订（阶段03）

新阶段03 JSON填 `content_policy=neutral-v1`；每题有稳定id，每个probe有when（always/confirmed/denied/unknown），confirmed还须说明condition。旧锁定成果缺省该policy仍可校验，不静默改写。

内容REVISE先准备意见JSON：

```json
{"issues":[{"issue_id":"neutral-01","question_id":"iv-1-p4-q1","status":"open","problem":"追问预设损失已发生","required_fix":"先确认现象；未确认时了解实际做法"}]}
```

```bash
python3 scripts/ig_runtime.py review <project> --stage stage_03_interview_drafting --role business_expert --decision REVISE --issues-file <issues.json>
```

修订后重新submit，复核PASS提供同一issue_id/question_id、status=resolved、resolution_note和after：

```json
{"issues":[{"issue_id":"neutral-01","question_id":"iv-1-p4-q1","status":"resolved","resolution_note":"确认前提后才问影响；否定时采集有效做法","after":{"text":"目前相关业务通常怎样安排？","probes":[{"type":"引导思考","text":"哪些做法运行有效？","when":"denied"}],"interviewer_context":""}}]}
```

after可省略，由runtime从当前问题提取并保留差异证据；若提供，须与当前text/probes/interviewer_context及已存在的context/answer_hints完全一致。before由runtime从原问题记录。正文与probe未变时不能标resolved；不适用可填not_applicable并解释，由独立评审者判断。未关闭issue不能PASS。仅修改元信息、页眉页脚不算正文修复。

## v1.1 同源双视图

runtime render自动生成根目录客户版与interviewer/访谈员版；全部文件纳入同一hash清单。直接运行render_html.py/render_docx.py时可加--audience client|interviewer，默认client。客户版保留完整主问、context/answer_hints，隐藏内部映射、Phase编码、顾问判断与条件probe；内部版另保留条件提示。分享客户文件时只使用客户HTML/docx，JSON和interviewer/为内部数据。
