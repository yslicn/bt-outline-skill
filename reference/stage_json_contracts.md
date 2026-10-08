# 阶段 JSON 结构速查

本文件只做字段速查；权威定义在 `schemas/*.schema.json`。冲突时以 schema 为准。

## requirement.json（阶段00）

`schema_version=1.0` · `stage_id=stage_00_scope_confirmation` · `project_name` · `client` · `industry` · `transformation_theme` · `scope_statement` · `materials[]{id,type,path,format,title}` · `delivery_formats["html","docx"]` · `scope_confirmed=true` · `scope_confirmed_at` · `data_gaps[]`

## input_baseline.json（阶段01）

`value_streams[]{id,name,short_name,trigger?,outcome?}` · `capability_model{root{id,name}, layers[]{attribute(战略|核心|支持), l2_groups[]{id,name,l3[]{id,name}}}}` · `stakeholders[]{id,name,type,role,focus_areas[]}` · `strategic_tensions[]{id,statement,source_ref}`（可为空，不凑数量）· `scope_boundaries[]` · `data_gaps[]`

## interview_plan.json（阶段02）

`split_logic{criteria,rationale}` · `interviews[]{id,num(01..NN),title,interview_direction,expected_information[],value_stream_ids[],l2_capability_ids[],stakeholder_role_ids[],split_rationale?,duration_min?}` · `coverage{vs_coverage[],capability_coverage[],stakeholder_coverage[],documented_exclusions[],gaps[]}`

## interview_guide_full.json（阶段03）

`plan_ref{plan_path,plan_sha256}` · `guides[]{id,num,title,target_audience,duration,meta{objectives,capability_coverage_summary},phases[5],expected_output[]}`

phase：`phase_no(1-5)` · `name` · `layer_type(intro|panorama|deepdive|awaken|expectation)` · `title` · `description` · `blocks[]`（P2必填、P3可选）· `questions[]`

block：`area_num` · `area_title` · `capability_ref{l2_id,l2_name,l3_names[]|l3_count}` · `questions[]`

question：`id` · `text`（完整主问） · `context?`（可见业务情境） · `answer_hints[]?`（可见回答范围/例子） · `interviewer_context?` · `premise_refs[]?` · `probes[]{type(追问|引导思考),text,when(always|confirmed|denied|unknown),condition?}` · `vs_refs[]` · `capability_refs[]`

新提纲根级填 `content_policy=neutral-v1` 启用ID、双引用和分支硬门；旧锁定数据可缺省。战略议题新增 `verification_status(reported|verified|hypothesis)`、`verification_note?`；新议题有核实状态时检查来源材料ID与位置，verified须有说明。字段名strategic_tensions保持兼容，不要求凑数量。

## render_input.json（阶段04，runtime 投影生成）

`source_guide_full_sha256` · `meta{client,transformation_theme,subtitle,version,date_text,basis_meta{vs_count,l2_count,l3_count,interview_count},footer_text}` · `cover{eyebrow,h1,subtitle,meta_lines[]}` · `background[]` · `methodology{progression,layer_definitions[]{name,definition},capability_alignment}` · `toc[]{num,title,scope_line,target_audience,filename}` · `vs_mapping_matrix{vs_codes[],vs_short_names[],rows[]{interview_num,title,marks[]}}` · `guides[]{num,title,vs_tags[],layer_tag,meta{target_audience,duration,capability_coverage_summary},phases[],expected_output[]}`
