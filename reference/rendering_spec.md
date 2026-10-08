# 渲染规格

HTML 与 docx 由 `render_input.json` 确定性渲染。CSS 复用 `assets/shared-style.css`（IBM Design System）。

## index.html 结构（顺序固定）

1. cover：eyebrow → h1（含 <br> 换行）→ divider → subtitle（含 <br>）→ meta-line × N
2. 项目背景：h2 + context-box（段落数组 background[]）
3. 访谈设计方法论：h2 + context-box（progression 一条 + layer_definitions 每条 + capability_alignment 一条）
4. 访谈提纲清单：`.toc-grid`，每项 toc-item（num + title + scope_line + 对象），href 指向 filename
5. 价值流 × 访谈主题映射：meta-table（表头 VS 编码、简称行、每场一行 mark ●）
6. doc-footer

## 单场 html 结构（顺序固定）

1. header-bar：proj-name + doc-title（"NN 标题"）+ "← 返回总览" 链接
2. interview-header：interview-num（"Interview NN"）+ h2 + tag-row（vs_tags[] tag-blue + layer_tag tag-teal）
3. meta-table 3 行：访谈对象 / 访谈时长 / 能力域覆盖
4. Phase 1-5，每个：
   - phase-label（圆点 + "Phase N · 名称"，颜色按 layer_type：intro黄/panorama青/deepdive蓝/awaken红/expectation绿）
   - phase-title + phase-desc
   - P2/P3：blocks[] 每个 discussion-block（h3: area-num + area_title + capability-ref；内嵌 question-list）
   - P1/P2/P3/P5 也可能直列 question-list；P4 直列（probe 一律"引导思考"）
5. output-box："本场访谈预期输出" + ul
6. doc-footer：标题 + "项目名 | v1.0 | 日期"

## question 渲染

- 每个问题 `<li>`：问题正文 + probe `<span class="probe">`（"追问：..."或"引导思考：..."）
- 题号"Q"由 CSS `li::before` 伪元素生成，不写死数字。

## docx 渲染（render_docx.py）

- python-docx 程序化生成，**同一 render_input 同源**。
- 表驱动布局：index 用表格承载封面/背景/方法论/清单/矩阵；单场用表承载 header-bar/interview-header/meta-table。
- 问题前缀：正文 "Q "，追问 "↳ "（对齐母本 docx）。
- Phase 段落：`● Phase N · 名称` → 标题 → desc。
- CJK 字体：`detect_cjk_font()`（PingFang SC 兜底），`_set_run_font` 设置 ascii/hAnsi/eastAsia/cs。

## 页脚与元信息

- cover/单场 footer 的版本、日期来自 `render_input.meta`。
- HTML 与 docx 均内嵌/绑定 `source_guide_full_sha256`（机器门校验同源）。
