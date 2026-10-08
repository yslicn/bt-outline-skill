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
