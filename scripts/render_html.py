#!/usr/bin/env python3
"""Render render_input.json to index.html + NN_*.html (IBM blue style)."""
from __future__ import annotations

import argparse
import html
import json
import shutil
from pathlib import Path
from typing import Any

CSS_SRC = Path(__file__).resolve().parent.parent / "assets" / "shared-style.css"

PHASE_STYLE = {
    "intro": {"color": "#8E6A00", "dot": "#F1C21B"},
    "panorama": {"color": "var(--ibm-teal-50)", "dot": "var(--ibm-teal-50)"},
    "deepdive": {"color": "var(--ibm-blue-70)", "dot": "var(--ibm-blue-60)"},
    "awaken": {"color": "var(--ibm-red-60)", "dot": "var(--ibm-red-60)"},
    "expectation": {"color": "var(--ibm-green-50)", "dot": "var(--ibm-green-50)"},
}


def esc(value: Any) -> str:
    return html.escape(str(value), quote=False)


def render_questions(questions: list[dict[str, Any]]) -> str:
    items: list[str] = []
    for q in questions:
        li = f"      <li>{esc(q['text'])}"
        for probe in q.get("probes", []):
            label = f'{probe["type"]}：'
            text = probe["text"] if probe["text"].startswith(label) else label + probe["text"]
            li += f'\n        <span class="probe">{esc(text)}</span>'
        li += "\n      </li>"
        items.append(li)
    if not items:
        return ""
    return "<div class=\"question-list\">\n" + "\n".join(items) + "\n    </div>"


def render_phase(phase: dict[str, Any]) -> str:
    layer_type = phase["layer_type"]
    style = PHASE_STYLE[layer_type]
    label = (
        f'<div class="phase-label" style="color:{style["color"]};">'
        f'<span class="dot" style="background:{style["dot"]};"></span> Phase {phase["phase_no"]} · {esc(phase["name"])}</div>'
    )
    title = f'<div class="phase-title">{esc(phase.get("title", ""))}</div>'
    desc = f'<div class="phase-desc">{esc(phase.get("description", ""))}</div>' if phase.get("description") else ""
    body = ""
    for block in phase.get("blocks") or []:
        cap = block.get("capability_ref") or {}
        ref = ""
        if cap:
            if cap.get("l3_names"):
                ref = f'<span class="capability-ref">L2：{esc(cap["l2_name"])} → {" · ".join(esc(n) for n in cap["l3_names"])}</span>'
            elif cap.get("l3_count"):
                ref = f'<span class="capability-ref">L2：{esc(cap["l2_name"])} → {cap["l3_count"]}项L3</span>'
        body += (
            f'    <div class="discussion-block">\n'
            f'      <h3><span class="area-num">{block["area_num"]}</span> {esc(block["area_title"])}{ref}</h3>\n'
            f'{render_questions(block.get("questions") or [])}\n'
            f'    </div>\n'
        )
    body += render_questions(phase.get("questions") or [])
    return (
        f'  <div class="phase">\n'
        f'    {label}\n'
        f'    {title}\n'
        f'    {desc}\n'
        f'{body}'
        f'  </div>\n'
    )


def render_guide_html(guide: dict[str, Any], ri: dict[str, Any]) -> str:
    meta = guide["meta"]
    vs_tags = "".join(f'      <span class="tag tag-blue">{esc(t)}</span>\n' for t in guide.get("vs_tags", []))
    layer_tag = f'      <span class="tag tag-teal">{esc(guide["layer_tag"])}</span>\n'
    phases = "\n".join(
        f'  <hr class="phase-sep">\n{render_phase(p)}' if i else render_phase(p)
        for i, p in enumerate(guide["phases"])
    )
    outputs = "".join(f"      <li>{esc(o)}</li>\n" for o in guide["expected_output"])
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>访谈{esc(guide["num"])} — {esc(guide["title"])}</title>
<link rel="stylesheet" href="shared-style.css">
</head>
<body>

<div class="header-bar">
  <div class="proj-name">{esc(ri["meta"]["client"])} {esc(ri["meta"]["transformation_theme"])} · 访谈提纲</div>
  <div class="doc-title">{esc(guide["num"])} {esc(guide["title"])}</div>
  <a href="index.html">← 返回总览</a>
</div>

<div class="content">
  <div class="interview-header">
    <div class="interview-num">Interview {esc(guide["num"])}</div>
    <h2>{esc(guide["title"])}</h2>
    <div class="tag-row">
{vs_tags}{layer_tag}    </div>
  </div>

  <table class="meta-table">
    <tr><td>访谈对象</td><td>{esc(meta["target_audience"])}</td></tr>
    <tr><td>访谈时长</td><td>{esc(meta["duration"])}</td></tr>
    <tr><td>能力域覆盖</td><td>{esc(meta["capability_coverage_summary"])}</td></tr>
  </table>

{phases}
  <div class="output-box">
    <div class="label">本场访谈预期输出</div>
    <ul>
{outputs}    </ul>
  </div>
</div>

<div class="doc-footer">
  <p style="font-size:1rem; font-weight:600; color:var(--ibm-blue-90);">{esc(guide["num"])} {esc(guide["title"])} — 访谈提纲</p>
  <p>{esc(ri["meta"]["client"])} {esc(ri["meta"]["transformation_theme"])} &nbsp;|&nbsp; {esc(ri["meta"]["version"])} &nbsp;|&nbsp; {esc(ri["meta"]["date_text"])}</p>
</div>

</div>
</body>
</html>
"""


def render_index_html(ri: dict[str, Any]) -> str:
    cover = ri["cover"]
    meta = ri["meta"]
    background = "".join(f'    <p>{esc(p)}</p>\n' for p in ri.get("background", []))
    layer_defs = "".join(
        f'          <li><b>{esc(d["name"])}</b>（{esc(d["definition"])}）</li>\n' for d in ri["methodology"]["layer_definitions"]
    )
    toc_items = "".join(
        f'    <a class="toc-item" href="{esc(t["filename"])}">\n'
        f'      <span class="num">{esc(t["num"])}</span>\n'
        f'      <span class="info">\n'
        f'        <span class="title">{esc(t["title"])}</span>\n'
        f'        <span class="scope">{esc(t["scope_line"])} | 对象：{esc(t["target_audience"])}</span>\n'
        f'      </span>\n'
        f'    </a>\n'
        for t in ri["toc"]
    )
    matrix = ri["vs_mapping_matrix"]
    head_cells = "".join(f'      <td style="font-weight:700;">{esc(code)}</td>\n' for code in matrix["vs_codes"])
    short_cells = "".join(f"      <td>{esc(s)}</td>\n" for s in matrix["vs_short_names"])
    matrix_rows = "".join(
        f"    <tr><td>{esc(row['interview_num'])} {esc(row['title'])}</td>"
        + "".join("<td>●</td>" if m else "<td></td>" for m in row["marks"])
        + "</tr>\n"
        for row in matrix["rows"]
    )
    meta_lines_html = "".join(f'  <div class="meta-line">{esc(m)}</div>\n' for m in cover["meta_lines"])
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(meta["client"])} {esc(meta["transformation_theme"])} — 访谈提纲总览</title>
<link rel="stylesheet" href="shared-style.css">
</head>
<body>

<div class="cover">
  <div class="eyebrow">{esc(cover["eyebrow"])}</div>
  <h1>{cover["h1"]}</h1>
  <div class="divider"></div>
  <div class="subtitle">{cover["subtitle"]}</div>
  {meta_lines_html}
</div>

<div class="content">

<!-- ══ 项目背景 ══ -->
<div style="padding: 1rem 0 2rem;">
  <h2 style="font-size:1.4rem; color:var(--ibm-blue-90); margin-bottom:1rem;">项目背景</h2>
  <div class="context-box">
{background}  </div>

  <h2 style="font-size:1.4rem; color:var(--ibm-blue-90); margin-bottom:1rem;">访谈设计方法论</h2>
  <div class="context-box">
    <ul>
      <li><b>五层递进结构：</b>{esc(ri["methodology"]["progression"])}</li>
      <li><b>问题分层设计：</b>
        <ul>
{layer_defs}        </ul>
      </li>
      <li><b>能力域对齐：</b>{esc(ri["methodology"]["capability_alignment"])}</li>
    </ul>
  </div>
</div>

<hr class="section-sep">

<!-- ══ 访谈清单 ══ -->
<div class="toc">
  <h2>访谈提纲清单</h2>
  <div class="toc-grid">
{toc_items}  </div>
</div>

<hr class="section-sep">

<!-- ══ 能力域映射总览 ══ -->
<div style="padding: 1rem 0 2rem;">
  <h2 style="font-size:1.4rem; color:var(--ibm-blue-90); margin-bottom:1rem;">价值流 × 访谈主题映射</h2>
  <table class="meta-table" style="font-size:0.85rem;">
    <tr style="background:var(--ibm-blue-90);color:white;">
      <td style="font-weight:700;width:auto;">价值流</td>
{head_cells}    </tr>
    <tr>
      <td style="font-weight:600;">简称</td>
{short_cells}    </tr>
{matrix_rows}  </table>
</div>

<div class="doc-footer">
  <p style="font-size:1.1rem; font-weight:600; color:var(--ibm-blue-90); margin-bottom:0.5rem;">{esc(meta["footer_text"])}</p>
  <p>版本 {esc(meta["version"])} &nbsp;|&nbsp; {esc(meta["date_text"])} &nbsp;|&nbsp; 内部工作文件</p>
</div>

</div>
</body>
</html>
"""


def render_html_bundle(ri: dict[str, Any], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(CSS_SRC, out_dir / "shared-style.css")
    paths: list[Path] = [out_dir / "shared-style.css"]
    (out_dir / "index.html").write_text(render_index_html(ri), encoding="utf-8")
    paths.append(out_dir / "index.html")
    for guide in ri["guides"]:
        filename = f"{guide['num']}_{guide['title']}.html"
        (out_dir / filename).write_text(render_guide_html(guide, ri), encoding="utf-8")
        paths.append(out_dir / filename)
    return paths


def main() -> int:
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("render_input")
    parser.add_argument("out_dir")
    args = parser.parse_args()
    ri = json.loads(Path(args.render_input).read_text(encoding="utf-8"))
    render_html_bundle(ri, Path(args.out_dir))
    print(f"HTML bundle written to {args.out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
