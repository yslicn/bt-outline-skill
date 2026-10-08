#!/usr/bin/env python3
"""Generate BT Outline runtime: state, validation, review and release.

Standard-library only by design. JSON Schema files document the public
contract; this runtime enforces the cross-artifact invariants that JSON
Schema cannot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = "1.0"
SKILL_VERSION = "v1.2"
S00 = "stage_00_scope_confirmation"
S01 = "stage_01_input_baseline"
S02 = "stage_02_interview_planning"
S03 = "stage_03_interview_drafting"
S04 = "stage_04_rendering_release"
STAGE_ORDER = [S00, S01, S02, S03, S04]

ARTIFACTS = {
    S01: "stage_01_input_baseline/output/input_baseline.json",
    S02: "stage_02_interview_planning/output/interview_plan.json",
    S03: "stage_03_interview_drafting/output/interview_guide_full.json",
    S04: "stage_04_rendering_release/output/render_input.json",
}

PREREQUISITES = {
    S01: [],
    S02: [S01],
    S03: [S01, S02],
    S04: [S01, S02, S03],
}

REVIEWERS = ["architect", "business_expert"]

PHASE_LAYER_RULES = {
    1: "intro",
    2: "panorama",
    3: "deepdive",
    4: "awaken",
    5: "expectation",
}
PROBE_TYPE_BY_LAYER = {"intro": "追问", "panorama": "追问", "deepdive": "追问", "awaken": "引导思考", "expectation": "追问"}


class ContractError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ContractError(f"文件不存在: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ContractError(f"JSON无效: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"顶层必须是object: {path}")
    return value


def atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, path)


def atomic_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(value, encoding="utf-8")
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_keys(obj: dict[str, Any], keys: Iterable[str], where: str) -> None:
    missing = [key for key in keys if key not in obj]
    if missing:
        raise ContractError(f"{where} 缺少字段: {', '.join(missing)}")


def unique_ids(items: list[dict[str, Any]], where: str) -> set[str]:
    result: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict) or not item.get("id"):
            raise ContractError(f"{where}[{index}] 缺少id")
        item_id = str(item["id"])
        if item_id in result:
            raise ContractError(f"{where} 重复id: {item_id}")
        result.add(item_id)
    return result


def relpath(project: Path, path: Path) -> str:
    return str(path.resolve().relative_to(project.resolve()))


def state_paths(project: Path) -> tuple[Path, Path]:
    return project / "requirement.json", project / "project_state.json"


def load_project(project: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    req_path, state_path = state_paths(project)
    requirement = load_json(req_path)
    state = load_json(state_path)
    validate_requirement(requirement)
    validate_state(requirement, state)
    return requirement, state


# ── requirement / state ──────────────────────────────────────────────────

def validate_requirement(req: dict[str, Any]) -> None:
    require_keys(req, ["schema_version", "stage_id", "project_name", "client", "industry", "transformation_theme", "materials", "delivery_formats", "scope_confirmed", "scope_confirmed_at"], "requirement")
    if req["schema_version"] != SCHEMA_VERSION:
        raise ContractError("requirement.schema_version 必须为1.0")
    if req["scope_confirmed"] is not True:
        raise ContractError("输入材料尚未由用户确认")
    formats = req.get("delivery_formats", [])
    if "html" not in formats or "docx" not in formats:
        raise ContractError("delivery_formats 必须包含 html 与 docx")


def validate_state(req: dict[str, Any], state: dict[str, Any]) -> None:
    require_keys(state, ["schema_version", "project_name", "client", "industry", "transformation_theme", "created_at", "current_stage", "stages", "runs"], "project_state")
    for key in ("project_name", "client", "industry", "transformation_theme"):
        if state[key] != req[key]:
            raise ContractError(f"requirement与project_state的{key}不一致")
    for stage_id in STAGE_ORDER:
        if stage_id not in state["stages"]:
            raise ContractError(f"project_state缺少阶段: {stage_id}")
    valid_status = {"pending", "in_progress", "internal_review", "user_review", "locked"}
    for stage_id, item in state["stages"].items():
        if item.get("status") not in valid_status:
            raise ContractError(f"{stage_id}状态无效: {item.get('status')}")
        if stage_id in ARTIFACTS and item.get("status") != "locked":
            if item.get("required_reviewers") != REVIEWERS:
                raise ContractError(f"{stage_id}必须依次经过Architect与业务专家内部评审")


def default_stage_entry(reviewers: list[str], status: str = "pending") -> dict[str, Any]:
    return {
        "status": status,
        "artifact": None,
        "artifact_sha256": None,
        "human_view": None,
        "required_reviewers": reviewers,
        "reviews": {},
        "user_approval": None,
    }


def cmd_init(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    if project.exists() and any(project.iterdir()):
        raise ContractError(f"项目目录非空，拒绝覆盖: {project}")
    project.mkdir(parents=True, exist_ok=True)
    requirement = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": S00,
        "project_name": args.name,
        "client": args.client,
        "industry": args.industry,
        "transformation_theme": args.theme,
        "scope_statement": "",
        "materials": [],
        "delivery_formats": ["html", "docx"],
        "scope_confirmed": True,
        "scope_confirmed_at": now(),
        "data_gaps": [],
    }
    stages = {
        S00: default_stage_entry([], "locked"),
        S01: default_stage_entry(REVIEWERS),
        S02: default_stage_entry(REVIEWERS),
        S03: default_stage_entry(REVIEWERS),
        S04: default_stage_entry(REVIEWERS),
    }
    stages[S00]["user_approval"] = {"status": "APPROVED", "approved_at": now()}
    state = {
        "schema_version": SCHEMA_VERSION,
        "project_name": args.name,
        "client": args.client,
        "industry": args.industry,
        "transformation_theme": args.theme,
        "created_at": now(),
        "current_stage": S01,
        "stages": stages,
        "runs": [],
    }
    atomic_json(project / "requirement.json", requirement)
    atomic_json(project / "project_state.json", state)
    for stage_id in ARTIFACTS:
        (project / Path(ARTIFACTS[stage_id]).parent).mkdir(parents=True, exist_ok=True)
        (project / stage_id / "review").mkdir(parents=True, exist_ok=True)
    print(f"已初始化 {args.name}: 输入材料与HTML/docx双格式已确认")


# ── artifact helpers ─────────────────────────────────────────────────────

def artifact_path(project: Path, stage_id: str) -> Path:
    if stage_id not in ARTIFACTS:
        raise ContractError(f"阶段没有正式artifact: {stage_id}")
    return project / ARTIFACTS[stage_id]


def check_prerequisites(state: dict[str, Any], stage_id: str) -> None:
    for prereq in PREREQUISITES.get(stage_id, []):
        if state["stages"][prereq]["status"] != "locked":
            raise ContractError(f"{stage_id}的上游尚未锁定: {prereq}")


def common_stage_checks(data: dict[str, Any], state: dict[str, Any], stage_id: str) -> None:
    require_keys(data, ["schema_version", "stage_id", "project_name"], stage_id)
    if data["schema_version"] != SCHEMA_VERSION or data["stage_id"] != stage_id:
        raise ContractError(f"{stage_id}的schema_version或stage_id错误")
    if data["project_name"] != state["project_name"]:
        raise ContractError(f"{stage_id}.project_name与项目状态不一致")


# ── stage validators ─────────────────────────────────────────────────────

def _l3_l2_sets(baseline: dict[str, Any]) -> tuple[set[str], set[str], set[str]]:
    vs_ids = {v["id"] for v in baseline.get("value_streams", [])}
    l2_ids: set[str] = set()
    l3_ids: set[str] = set()
    for layer in baseline.get("capability_model", {}).get("layers", []):
        for group in layer.get("l2_groups", []):
            l2_ids.add(group["id"])
            for item in group.get("l3", []):
                l3_ids.add(item["id"])
    return vs_ids, l2_ids, l3_ids


def validate_stage01(data: dict[str, Any], requirement: dict[str, Any]) -> None:
    vs_ids = unique_ids(data["value_streams"], "value_streams")
    for v in data["value_streams"]:
        require_keys(v, ["id", "name", "short_name"], "value_stream")
    stakeholders = unique_ids(data["stakeholders"], "stakeholders")
    for s in data["stakeholders"]:
        require_keys(s, ["id", "name", "type", "role"], "stakeholder")
    tensions = data.get("strategic_tensions", [])
    unique_ids(tensions, "strategic_tensions")
    for t in tensions:
        if not t.get("source_ref"):
            raise ContractError(f"strategic_tensions[{t.get('id')}] 缺少 source_ref（须溯源到输入材料）")
        if "verification_status" in t:
            if t["verification_status"] not in {"reported", "verified", "hypothesis"}:
                raise ContractError("战略议题核实状态无效")
            material_id, separator, locator = t["source_ref"].partition("#")
            if material_id not in {m["id"] for m in requirement.get("materials", [])} or not separator or not locator:
                raise ContractError("战略议题source_ref须引用已登记材料ID及具体位置")
            if t["verification_status"] == "verified" and not t.get("verification_note"):
                raise ContractError("已核实议题缺少verification_note")
    model = data.get("capability_model", {})
    if not model.get("root") or not isinstance(model.get("layers"), list) or not model["layers"]:
        raise ContractError("capability_model 必须包含 root 与非空 layers")
    _, l2_ids, _ = _l3_l2_sets(data)
    if not l2_ids:
        raise ContractError("capability_model 至少需要一项L2能力")


def validate_stage02(data: dict[str, Any], baseline: dict[str, Any]) -> None:
    vs_ids, l2_ids, _ = _l3_l2_sets(baseline)
    interviews = data["interviews"]
    unique_ids(interviews, "interviews")
    nums: set[str] = set()
    for iv in interviews:
        require_keys(iv, ["id", "num", "title", "interview_direction", "expected_information", "value_stream_ids", "l2_capability_ids", "stakeholder_role_ids"], "interview")
        if iv["num"] in nums:
            raise ContractError(f"重复编号: {iv['num']}")
        nums.add(iv["num"])
        for ref in iv["value_stream_ids"]:
            if ref not in vs_ids:
                raise ContractError(f"interview {iv['id']} 引用不存在的价值流: {ref}")
        for ref in iv["l2_capability_ids"]:
            if ref not in l2_ids:
                raise ContractError(f"interview {iv['id']} 引用不存在的L2: {ref}")
    coverage = data.get("coverage", {})
    merged_vs = set(coverage.get("vs_coverage", []))
    documented = set(coverage.get("documented_exclusions", []))
    missing = vs_ids - merged_vs - documented
    if missing:
        raise ContractError(f"规划合并覆盖遗漏价值流（且未显式排除）: {sorted(missing)}")
    if not coverage.get("vs_coverage"):
        raise ContractError("coverage.vs_coverage 为空")


def _probe_type_ok(question: dict[str, Any], layer_type: str) -> bool:
    expected = PROBE_TYPE_BY_LAYER[layer_type]
    for probe in question.get("probes", []):
        if probe.get("type") != expected:
            return False
    return True


def validate_stage03(data: dict[str, Any], plan: dict[str, Any], baseline: dict[str, Any]) -> None:
    policy = data.get("content_policy")
    if policy not in {None, "neutral-v1"}:
        raise ContractError("content_policy无效")
    neutral = policy == "neutral-v1"
    question_ids: set[str] = set()
    premises = {t["id"] for t in baseline.get("strategic_tensions", [])}
    vs_ids, l2_ids, l3_ids = _l3_l2_sets(baseline)
    plan_ids = {iv["id"] for iv in plan["interviews"]}
    plan_nums = {iv["id"]: iv["num"] for iv in plan["interviews"]}
    guides = data["guides"]
    unique_ids(guides, "guides")
    guide_ids = {g["id"] for g in guides}
    if guide_ids != plan_ids:
        raise ContractError(f"guides id集与plan不一致: 多出={guide_ids - plan_ids} 缺少={plan_ids - guide_ids}")
    for guide in guides:
        if guide["num"] != plan_nums[guide["id"]]:
            raise ContractError(f"guide {guide['id']} 编号与plan不一致")
        phases = guide["phases"]
        if len(phases) != 5 or [p["phase_no"] for p in phases] != [1, 2, 3, 4, 5]:
            raise ContractError(f"guide {guide['id']} 必须含 P1-P5 且顺序正确")
        for phase in phases:
            layer_type = phase["layer_type"]
            if layer_type != PHASE_LAYER_RULES[phase["phase_no"]]:
                raise ContractError(f"guide {guide['id']} phase{phase['phase_no']} 的 layer_type 应为 {PHASE_LAYER_RULES[phase['phase_no']]}，实际 {layer_type}")
            blocks = phase.get("blocks") or []
            questions = phase.get("questions") or []
            if phase["phase_no"] == 2 and not blocks:
                raise ContractError(f"guide {guide['id']} P2 必须使用 discussion-block")
            if phase["phase_no"] in (1, 4, 5) and blocks:
                raise ContractError(f"guide {guide['id']} P{phase['phase_no']} 不得使用 discussion-block")
            all_q = [q for b in blocks for q in b.get("questions", [])] + questions
            for q in all_q:
                require_keys(q, ["text", "probes"], "question")
                if "context" in q and not isinstance(q["context"], str):
                    raise ContractError("question.context须为字符串")
                if "answer_hints" in q and (not isinstance(q["answer_hints"], list) or any(not isinstance(hint, str) or not hint.strip() for hint in q["answer_hints"])):
                    raise ContractError("question.answer_hints须为非空字符串数组")
                if neutral:
                    if not q.get("id") or q["id"] in question_ids:
                        raise ContractError("中立提纲每题须有唯一稳定id")
                    question_ids.add(q["id"])
                    if not q.get("vs_refs") or not q.get("capability_refs"):
                        raise ContractError("中立提纲每题须同时有价值流和能力引用")
                    for ref in q.get("premise_refs", []):
                        if ref not in premises:
                            raise ContractError(f"问题前提引用不存在: {ref}")
                    for probe in q["probes"]:
                        if probe.get("when") not in {"always", "confirmed", "denied", "unknown"}:
                            raise ContractError("中立提纲probe须有合法when条件")
                        if probe["when"] == "confirmed" and not probe.get("condition"):
                            raise ContractError("confirmed追问须说明具体condition")
                if not _probe_type_ok(q, layer_type):
                    raise ContractError(f"guide {guide['id']} P{phase['phase_no']} 存在引导词不符的问题（{layer_type} 层应为 {PROBE_TYPE_BY_LAYER[layer_type]}）")
                if not q.get("vs_refs") and not q.get("capability_refs"):
                    raise ContractError(f"guide {guide['id']} 存在无任何能力引用的问题: {q['text'][:30]}")
                for ref in q.get("vs_refs", []):
                    if ref not in vs_ids:
                        raise ContractError(f"guide {guide['id']} 引用不存在的价值流: {ref}")
                for ref in q.get("capability_refs", []):
                    if ref not in l2_ids and ref not in l3_ids:
                        raise ContractError(f"guide {guide['id']} 引用不存在的L2/L3: {ref}")
        if not guide.get("expected_output"):
            raise ContractError(f"guide {guide['id']} 缺少 expected_output")


# ── render_input projection (stage 04) ──────────────────────────────────

def _layer_for_l2(l2_id: str, baseline: dict[str, Any]) -> str:
    for layer in baseline["capability_model"]["layers"]:
        if any(g["id"] == l2_id for g in layer["l2_groups"]):
            return layer["attribute"]
    return ""


def guide_l3_by_l2(guide: dict[str, Any], l2_by_id: dict[str, dict[str, Any]]) -> tuple[set[str], dict[str, int]]:
    """Return (l2_ids covered, l3 count per l2) using the canonical dedup口径."""
    l3_of_l2: dict[str, dict[str, str]] = {}
    for _l2_id, group in l2_by_id.items():
        l3_of_l2[_l2_id] = {it["id"]: it["name"] for it in group.get("l3", [])}
    l2_ids: set[str] = set()
    name_covered: dict[str, set[str]] = {}
    nominal: dict[str, int] = {}
    for phase in guide["phases"]:
        for b in phase.get("blocks") or []:
            cap = b.get("capability_ref") or {}
            if cap.get("l2_id"):
                l2_ids.add(cap["l2_id"])
                if cap.get("l3_names"):
                    name_covered.setdefault(cap["l2_id"], set()).update(cap["l3_names"])
                if cap.get("l3_count"):
                    nominal[cap["l2_id"]] = max(nominal.get(cap["l2_id"], 0), cap["l3_count"])
        for q in [q for b in phase.get("blocks") or [] for q in b.get("questions", [])] + (phase.get("questions") or []):
            for ref in q.get("capability_refs", []):
                if ref in l2_by_id:
                    l2_ids.add(ref)
                else:
                    for _l2, mapping in l3_of_l2.items():
                        if ref in mapping:
                            l2_ids.add(_l2)
                            name_covered.setdefault(_l2, set()).add(mapping[ref])
    counts: dict[str, int] = {}
    for _l2 in l2_ids:
        count = len(name_covered.get(_l2, set()))
        if nominal.get(_l2, 0) > count:
            count = nominal[_l2]
        if count > 0:
            counts[_l2] = count
    return set(counts), counts


def project_render_input(guide_full: dict[str, Any], baseline: dict[str, Any], requirement: dict[str, Any], source_hash: str) -> dict[str, Any]:
    guides_in = guide_full["guides"]
    vs_by_id = {v["id"]: v for v in baseline["value_streams"]}
    l2_by_id: dict[str, dict[str, Any]] = {}
    for layer in baseline["capability_model"]["layers"]:
        for group in layer["l2_groups"]:
            l2_by_id[group["id"]] = group
    l3_count_total = sum(len(g.get("l3", [])) for g in l2_by_id.values())

    toc: list[dict[str, Any]] = []
    guides_out: list[dict[str, Any]] = []
    for g in guides_in:
        l2_ids, l3_by_l2 = guide_l3_by_l2(g, l2_by_id)
        l3_total = sum(l3_by_l2.values())
        vs_ids = set()
        for phase in g["phases"]:
            for q in [q for b in phase.get("blocks") or [] for q in b.get("questions", [])] + (phase.get("questions") or []):
                vs_ids.update(q.get("vs_refs", []))
        layer_tags = {_layer_for_l2(i, baseline) for i in l2_ids if _layer_for_l2(i, baseline)}
        layer_name = " / ".join(sorted(layer_tags)) if layer_tags else "核心"
        layer_tag = f"{layer_name} · {len(l2_ids)}项L2 · {l3_total}项L3"
        vs_tags = [f"{v.upper()} {vs_by_id[v]['name']}" for v in sorted(vs_ids) if v in vs_by_id]
        filename = f"{g['num']}_{g['title']}.html"
        toc.append({
            "num": g["num"], "title": g["title"], "scope_line": layer_tag,
            "target_audience": g["target_audience"], "filename": filename,
        })
        guides_out.append({
            "num": g["num"], "title": g["title"], "vs_tags": vs_tags, "layer_tag": layer_tag,
            "meta": {"target_audience": g["target_audience"], "duration": g["duration"], "capability_coverage_summary": g["meta"]["capability_coverage_summary"]},
            "phases": g["phases"], "expected_output": g["expected_output"],
        })

    vs_codes = [v["id"].upper() for v in baseline["value_streams"]]
    vs_short_names = [v["short_name"] for v in baseline["value_streams"]]
    vs_index = {v["id"]: i for i, v in enumerate(baseline["value_streams"])}
    matrix_rows: list[dict[str, Any]] = []
    for g in guides_in:
        marks = [False] * len(vs_codes)
        for phase in g["phases"]:
            for q in [q for b in phase.get("blocks") or [] for q in b.get("questions", [])] + (phase.get("questions") or []):
                for ref in q.get("vs_refs", []):
                    if ref in vs_index:
                        marks[vs_index[ref]] = True
        matrix_rows.append({"interview_num": g["num"], "title": g["title"], "marks": marks})

    interview_count = len(guides_in)
    meta = {
        "client": requirement["client"],
        "transformation_theme": requirement["transformation_theme"],
        "subtitle": f"{requirement['transformation_theme']} — 访谈提纲总览",
        "version": SKILL_VERSION,
        "date_text": _date_text(requirement),
        "basis_meta": {"vs_count": len(vs_codes), "l2_count": len(l2_by_id), "l3_count": l3_count_total, "interview_count": interview_count},
        "footer_text": f"{requirement['client']} {requirement['transformation_theme']} — 访谈提纲总览",
    }
    cover_h1 = f"{requirement['client']}<br>{requirement['transformation_theme']}"
    return {
        "schema_version": SCHEMA_VERSION,
        "stage_id": S04,
        "project_name": requirement["project_name"],
        "source_guide_full_sha256": source_hash,
        "meta": meta,
        "cover": {
            "eyebrow": "Management Consulting · Interview Guide",
            "h1": cover_h1,
            "subtitle": f"{requirement['transformation_theme']} — 访谈提纲总览<br>{' · '.join([f'{len(vs_codes)} 大价值流', f'{interview_count} 场专题访谈'])}",
            "meta_lines": [
                f"版本 {meta['version']}  |  {meta['date_text']}  |  内部工作文件",
                f"基于 {_basis_text(len(vs_codes), len(l2_by_id), l3_count_total)}，结合干系人分析",
            ],
        },
        "background": [
            f"本项目聚焦{requirement['client']}{requirement['transformation_theme']}。通过{_scope_text(requirement)}访谈，了解业务现状、有效机制、挑战与机会，以及保留与改进期望。",
            f"访谈提纲覆盖{_scope_text(requirement)}全业务域，对齐{_basis_text(len(vs_codes), len(l2_by_id), l3_count_total)}，通过{interview_count}场专题访谈开展信息采集。",
        ],
        "methodology": {
            "progression": "暖场与职责了解 → 业务全景 → 运行机制与具体案例 → 挑战与机会探索 → 保留与改进期望；没有问题、不适用、未知与暂不调整均为有效信息",
            "layer_definitions": [
                {"name": "破冰问题", "definition": "组织架构/人员规模/协同模式概览——建立信任，获取结构信息"},
                {"name": "全景问题", "definition": "业务目标/核心流程/关键指标——让客户\"有话说\""},
                {"name": "案例问题", "definition": "了解实际流转、正常与例外处理、协作接口与信息使用"},
                {"name": "探索问题", "definition": "核实挑战、机会、适用边界和其他解释；不预设问题存在"},
                {"name": "期望问题", "definition": "了解保留、改进、条件与暂不调整的理由"},
            ],
            "capability_alignment": "每个问题标注所属价值流（VS）和业务能力域（L2/L3），确保信息收集与能力架构一一对应",
        },
        "toc": toc,
        "vs_mapping_matrix": {"vs_codes": vs_codes, "vs_short_names": vs_short_names, "rows": matrix_rows},
        "guides": guides_out,
    }


def _date_text(requirement: dict[str, Any]) -> str:
    s = requirement.get("scope_confirmed_at", "")[:7]
    if len(s) == 7 and s[4] == "-":
        year, month = s.split("-")
        return f"{int(year)} 年 {int(month)} 月"
    return "内部工作文件"


def _basis_text(vs_count: int, l2_count: int, l3_count: int) -> str:
    return f"三层能力架构（{l2_count}个L2 · {l3_count}项L3）· {vs_count}大价值流"


def _scope_text(requirement: dict[str, Any]) -> str:
    return requirement.get("scope_statement") or requirement.get("transformation_theme") or "业务"


def validate_stage04(data: dict[str, Any], state: dict[str, Any]) -> None:
    require_keys(data, ["schema_version", "stage_id", "project_name", "source_guide_full_sha256", "meta", "cover", "background", "methodology", "toc", "vs_mapping_matrix", "guides"], S04)
    source_entry = state["stages"][S03]
    if source_entry.get("artifact_sha256") != data.get("source_guide_full_sha256"):
        raise ContractError("render_input 未绑定当前阶段03正式JSON的sha256")


# ── validation dispatch ─────────────────────────────────────────────────

def validate_artifact(project: Path, state: dict[str, Any], stage_id: str) -> dict[str, Any]:
    data = load_json(artifact_path(project, stage_id))
    common_stage_checks(data, state, stage_id)
    if stage_id == S01:
        validate_stage01(data, load_json(project / "requirement.json"))
    elif stage_id == S02:
        baseline = load_json(artifact_path(project, S01))
        validate_stage02(data, baseline)
    elif stage_id == S03:
        plan = load_json(artifact_path(project, S02))
        baseline = load_json(artifact_path(project, S01))
        validate_stage03(data, plan, baseline)
    elif stage_id == S04:
        validate_stage04(data, state)
    return data


# ── MD projection ───────────────────────────────────────────────────────

def pipe(value: Any) -> str:
    return str(value).replace("|", "\\|")


def render_stage(stage_id: str, data: dict[str, Any], source_hash: str) -> str:
    head = f"<!-- source_sha256: {source_hash} -->\n"
    if stage_id == S01:
        return head + render_stage01(data)
    if stage_id == S02:
        return head + render_stage02(data)
    if stage_id == S03:
        return head + render_stage03(data)
    if stage_id == S04:
        return head + render_stage04(data)
    raise ContractError(f"未知阶段: {stage_id}")


def render_stage01(data: dict[str, Any]) -> str:
    lines = ["# 信息基底（阶段01）\n"]
    lines.append("## 价值流")
    for v in data["value_streams"]:
        lines.append(f"- {v['id']} {pipe(v['name'])}（{v.get('short_name', '')}）")
    model = data["capability_model"]
    lines.append("\n## 能力框架")
    for layer in model["layers"]:
        l2 = [f"{g['name']}({len(g.get('l3', []))}项L3)" for g in layer["l2_groups"]]
        lines.append(f"- {layer['attribute']}层: {'; '.join(l2)}")
    lines.append("\n## 干系人")
    for s in data["stakeholders"]:
        lines.append(f"- {pipe(s['name'])}（{s['type']}）: {s['role']}")
    lines.append("\n## 战略关注议题（允许为空）")
    for t in data["strategic_tensions"]:
        lines.append(f"- {pipe(t['statement'])}（来源: {pipe(t.get('source_ref', ''))}；核实状态: {pipe(t.get('verification_status', 'reported'))}）")
    return "\n".join(lines) + "\n"


def render_stage02(data: dict[str, Any]) -> str:
    lines = ["# 访谈规划（阶段02）\n"]
    logic = data.get("split_logic", {})
    lines.append(f"**拆分判据**: {pipe(logic.get('criteria', ''))}")
    lines.append(f"\n**自洽性论证**: {pipe(logic.get('rationale', ''))}\n")
    lines.append("\n## 访谈清单")
    for iv in data["interviews"]:
        lines.append(f"\n### {iv['num']} {iv['title']}")
        lines.append(f"- 方向: {iv['interview_direction']}")
        lines.append(f"- 预期信息: {'；'.join(iv['expected_information'])}")
        if iv.get("split_rationale"):
            lines.append(f"- 拆分理由: {iv['split_rationale']}")
    coverage = data.get("coverage", {})
    lines.append(f"\n## 覆盖: 价值流{len(coverage.get('vs_coverage', []))}项 ｜ L2 {len(coverage.get('capability_coverage', []))}项 ｜ 干系人{len(coverage.get('stakeholder_coverage', []))}项")
    if coverage.get("documented_exclusions"):
        lines.append(f"- 显式排除: {'；'.join(coverage['documented_exclusions'])}")
    if coverage.get("gaps"):
        lines.append(f"- 缺口: {'；'.join(coverage['gaps'])}")
    return "\n".join(lines) + "\n"


def render_stage03(data: dict[str, Any]) -> str:
    from render_views import probe_text
    lines = ["# 访谈提纲全文（阶段03）\n"]
    for g in data["guides"]:
        lines.append(f"\n## {g['num']} {g['title']}")
        lines.append(f"- 对象: {g['target_audience']} ｜ 时长: {g['duration']}")
        lines.append(f"- 能力域覆盖: {g['meta'].get('capability_coverage_summary', '')}")
        for phase in g["phases"]:
            lines.append(f"\n### Phase {phase['phase_no']} · {phase['name']}")
            if phase.get("description"):
                lines.append(f"*{phase['description']}*")
            for b in phase.get("blocks") or []:
                cap = b.get("capability_ref") or {}
                ref_text = f"（{cap.get('l2_name', '')}）" if cap.get("l2_name") else ""
                lines.append(f"\n**{b['area_num']}. {b['area_title']}**{ref_text}")
                for q in b.get("questions", []):
                    lines.append(f"- [{pipe(q.get('id', 'legacy'))}] {pipe(q['text'])}")
                    if q.get("interviewer_context"):
                        lines.append(f"  - 访谈员提示: {pipe(q['interviewer_context'])}")
                    if q.get("context"):
                        lines.append(f"  - 说明: {pipe(q['context'])}")
                    for hint in q.get("answer_hints", []):
                        lines.append(f"  - 回答参考: {pipe(hint)}")
                    for p in q.get("probes", []):
                        lines.append(f"  - {pipe(probe_text(p))}")
            for q in phase.get("questions") or []:
                lines.append(f"- [{pipe(q.get('id', 'legacy'))}] {pipe(q['text'])}")
                if q.get("interviewer_context"):
                    lines.append(f"  - 访谈员提示: {pipe(q['interviewer_context'])}")
                if q.get("context"):
                    lines.append(f"  - 说明: {pipe(q['context'])}")
                for hint in q.get("answer_hints", []):
                    lines.append(f"  - 回答参考: {pipe(hint)}")
                for p in q.get("probes", []):
                    lines.append(f"  - {pipe(probe_text(p))}")
        lines.append("\n**本场访谈预期输出**")
        for o in g["expected_output"]:
            lines.append(f"- {pipe(o)}")
    return "\n".join(lines) + "\n"


def render_stage04(data: dict[str, Any]) -> str:
    lines = ["# 渲染输入（阶段04）\n"]
    meta = data["meta"]
    lines.append(f"**{meta['client']}（eπ）{meta['transformation_theme']}** — {meta['subtitle']}")
    lines.append(f"版本 {meta['version']} ｜ {meta['date_text']} ｜ 内部工作文件\n")
    lines.append("\n## 访谈清单")
    for item in data["toc"]:
        lines.append(f"- {item['num']} {item['title']}（{item['scope_line']} ｜ 对象: {item['target_audience']}）")
    matrix = data["vs_mapping_matrix"]
    lines.append(f"\n## 价值流 × 访谈主题映射（{len(matrix['vs_codes'])} 大价值流）")
    header = " | ".join(["访谈"] + list(matrix["vs_codes"]))
    lines.append(f"- {header}")
    for row in matrix["rows"]:
        marks = "".join("●" if m else "·" for m in row["marks"])
        lines.append(f"- {row['interview_num']} {row['title']}: {marks}")
    return "\n".join(lines) + "\n"


def write_stage_md(project: Path, stage_id: str, data: dict[str, Any], digest: str) -> Path:
    md_path = project / stage_id / "output" / f"{stage_id}_view.md"
    atomic_text(md_path, render_stage(stage_id, data, digest))
    return md_path


# ── review binding / release bundle ─────────────────────────────────────

def verify_current_hash(project: Path, entry: dict[str, Any]) -> None:
    if not entry.get("artifact") or not entry.get("artifact_sha256"):
        raise ContractError("阶段尚未提交artifact")
    path = project / entry["artifact"]
    if sha256(path) != entry["artifact_sha256"]:
        raise ContractError("artifact在提交或评审后已变化，必须重新submit并重审")


def expected_release_paths(project: Path, manifest: dict[str, Any]) -> set[str]:
    paths = {"render_input.json", "index.html", "shared-style.css", "index.docx"}
    for item in manifest.get("toc", []):
        paths.add(f"{item['num']}_{item['title']}.html")
        paths.add(f"{item['num']}_{item['title']}.docx")
    if "interviewer" in manifest.get("audiences", []):
        paths |= {"interviewer/" + p for p in paths if p != "render_input.json"}
    return paths


def write_candidate_bundle(project: Path, data: dict[str, Any], source_hash: str) -> Path:
    """Render HTML + docx + render_input from render_input data; write candidate_manifest."""
    candidate_dir = project / S04 / "output" / "candidate"
    if candidate_dir.exists():
        shutil.rmtree(candidate_dir)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    render_input_path = candidate_dir / "render_input.json"
    atomic_json(render_input_path, data)
    render_input_path_src = artifact_path(project, S04)
    atomic_json(render_input_path_src, data)

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from render_html import render_html_bundle  # noqa: E402
        from render_docx import render_docx_bundle  # noqa: E402
    except ImportError as exc:
        raise ContractError(f"渲染模块缺失: {exc}") from exc

    html_files = render_html_bundle(data, candidate_dir)
    docx_files = render_docx_bundle(data, candidate_dir)
    html_files += render_html_bundle(data, candidate_dir / "interviewer", audience="interviewer")
    docx_files += render_docx_bundle(data, candidate_dir / "interviewer", audience="interviewer")

    files: list[dict[str, str]] = []
    all_files = [relpath(project, render_input_path)] + [relpath(project, p) for p in html_files] + [relpath(project, p) for p in docx_files]
    for candidate in all_files:
        p = project / candidate
        release_path = str(p.relative_to(candidate_dir))
        files.append({"candidate_path": candidate, "release_path": release_path, "sha256": sha256(p)})
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "stage_id": S04,
        "project_name": data["project_name"],
        "source_guide_full_sha256": data.get("source_guide_full_sha256") or source_hash,
        "render_input_sha256": sha256(render_input_path),
        "toc": data["toc"],
        "required_reviewers": REVIEWERS,
        "audiences": ["client", "interviewer"],
        "files": files,
    }
    manifest_path = project / S04 / "output" / "candidate_manifest.json"
    atomic_json(manifest_path, manifest)
    return manifest_path


def verify_review_target(project: Path, entry: dict[str, Any]) -> str:
    verify_current_hash(project, entry)
    if not entry.get("review_bundle"):
        return entry["artifact_sha256"]
    manifest_path = project / entry["review_bundle"]
    if not manifest_path.exists() or sha256(manifest_path) != entry.get("review_bundle_sha256"):
        raise ContractError("候选交付清单已变化，必须重新render并重审")
    manifest = load_json(manifest_path)
    if manifest.get("render_input_sha256") != entry["artifact_sha256"]:
        raise ContractError("候选交付清单未绑定当前render_input.json")
    _, state = load_project(project)
    if manifest.get("source_guide_full_sha256") != state["stages"][S03].get("artifact_sha256"):
        raise ContractError("候选交付清单未绑定当前阶段03正式JSON")
    expected = expected_release_paths(project, manifest)
    actual = {item.get("release_path") for item in manifest["files"]}
    if actual != expected or len(actual) != len(manifest["files"]):
        raise ContractError("候选交付文件集合不完整或存在重复")
    for item in manifest["files"]:
        require_keys(item, ["candidate_path", "release_path", "sha256"], "candidate file")
        path = project / item["candidate_path"]
        if not path.exists() or sha256(path) != item["sha256"]:
            raise ContractError(f"候选交付件已变化，必须重新render并重审: {item['release_path']}")
    return entry["review_bundle_sha256"]


def next_current_stage(state: dict[str, Any]) -> str | None:
    for stage_id in STAGE_ORDER:
        if stage_id in ARTIFACTS and state["stages"][stage_id]["status"] != "locked":
            return stage_id
    return None


# ── commands ────────────────────────────────────────────────────────────

def cmd_start(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    stage_id = args.stage
    check_prerequisites(state, stage_id)
    entry = state["stages"][stage_id]
    if entry["status"] not in {"pending", "in_progress"}:
        raise ContractError(f"当前状态不可开始: {entry['status']}")
    entry["status"] = "in_progress"
    state["current_stage"] = stage_id
    atomic_json(project / "project_state.json", state)
    print(f"已开始 {stage_id}")


def submit_stage(project: Path, state: dict[str, Any], stage_id: str) -> None:
    check_prerequisites(state, stage_id)
    entry = state["stages"][stage_id]
    if entry["status"] == "locked":
        raise ContractError("已锁定阶段不可重新提交")
    data = validate_artifact(project, state, stage_id)
    path = artifact_path(project, stage_id)
    digest = sha256(path)
    md_path = write_stage_md(project, stage_id, data, digest)
    update: dict[str, Any] = {
        "status": "internal_review",
        "artifact": relpath(project, path),
        "artifact_sha256": digest,
        "human_view": relpath(project, md_path),
        "reviews": {},
        "user_approval": None,
        "submitted_at": now(),
    }
    if stage_id == S04:
        manifest_path = write_candidate_bundle(project, data, digest)
        candidate_manifest = load_json(manifest_path)
        update.update({
            "review_bundle": relpath(project, manifest_path),
            "review_bundle_sha256": sha256(manifest_path),
            "human_views": [item["candidate_path"] for item in candidate_manifest["files"] if item["release_path"].endswith(".md")] or None,
        })
    else:
        entry.pop("review_bundle", None)
        entry.pop("review_bundle_sha256", None)
        entry.pop("human_views", None)
    entry.update(update)
    state["current_stage"] = stage_id
    atomic_json(project / "project_state.json", state)
    print(f"已提交 {stage_id}: sha256={digest}")


def cmd_submit(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    submit_stage(project, state, args.stage)


def question_content(q: dict[str, Any]) -> dict[str, Any]:
    content = {"text": q["text"], "probes": q.get("probes", []), "interviewer_context": q.get("interviewer_context", "")}
    for field in ("context", "answer_hints"):
        if field in q:
            content[field] = q[field]
    return content


def review_content_issues(project: Path, stage: str, role: str, decision: str, issues_file: str | None, digest: str) -> list[dict[str, Any]]:
    """Keep issue closure across resubmissions; unchanged questions cannot be fixed."""
    if stage != S03:
        if issues_file:
            raise ContractError("--issues-file目前用于阶段03逐题内容评审")
        return []
    guide = load_json(artifact_path(project, S03))
    ledger_path = project / stage / "review" / f"issues_{role}.json"
    prior = load_json(ledger_path).get("issues", []) if ledger_path.exists() else []
    incoming = load_json(Path(issues_file)).get("issues", []) if issues_file else []
    if guide.get("content_policy") == "neutral-v1" and decision == "REVISE" and not incoming:
        raise ContractError("中立提纲REVISE须提供--issues-file逐题意见")
    unique_ids([{ "id": item.get("issue_id") } for item in incoming], "review issues")
    questions = {q.get("id"): q for g in guide["guides"] for p in g["phases"] for q in (p.get("questions") or []) + [q for b in p.get("blocks") or [] for q in b.get("questions", [])] if q.get("id")}
    updated = {item["issue_id"]: item for item in prior}
    for item in incoming:
        require_keys(item, ["issue_id", "question_id", "status"], "review issue")
        qid = item["question_id"]
        if qid not in questions:
            raise ContractError(f"评审问题ID不存在: {qid}")
        current = question_content(questions[qid])
        old = updated.get(item["issue_id"])
        if decision == "REVISE":
            require_keys(item, ["problem", "required_fix"], "REVISE issue")
            if item["status"] != "open" or not item["problem"] or not item["required_fix"]:
                raise ContractError("REVISE意见须为open并说明问题和修改要求")
            updated[item["issue_id"]] = {**item, "before": current, "opened_sha256": digest}
        else:
            if not old or old["question_id"] != qid:
                raise ContractError("关闭意见须引用同一问题的既有issue")
            if item["status"] not in {"resolved", "not_applicable"} or not item.get("resolution_note"):
                raise ContractError("关闭意见须注明resolved/not_applicable及理由")
            if item["status"] == "resolved" and current == old["before"]:
                raise ContractError("问题正文和probe未修改，不能标记已修复")
            if "after" in item and item["after"] != current:
                raise ContractError("关闭意见after须匹配当前问题正文及probe")
            updated[item["issue_id"]] = {**old, **item, "after": current, "closed_sha256": digest}
    if decision == "PASS" and any(i["status"] == "open" for i in updated.values()):
        raise ContractError("仍有未关闭的逐题评审意见，不可PASS")
    if incoming or prior:
        atomic_json(ledger_path, {"review_target_sha256": digest, "issues": list(updated.values())})
    return list(updated.values())


def cmd_review(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    entry = state["stages"][args.stage]
    if args.role not in entry["required_reviewers"]:
        raise ContractError(f"{args.stage}不需要{args.role}评审")
    if entry["status"] not in {"internal_review", "user_review"}:
        raise ContractError(f"当前状态不可评审: {entry['status']}")
    review_target_sha256 = verify_review_target(project, entry)
    issues = review_content_issues(project, args.stage, args.role, args.decision, args.issues_file, review_target_sha256)
    entry["reviews"][args.role] = {
        "decision": args.decision,
        "artifact_sha256": entry["artifact_sha256"],
        "review_target_sha256": review_target_sha256,
        "reviewed_at": now(),
        "notes": args.notes,
        "issues": issues,
    }
    review_path = project / args.stage / "review" / f"{args.role}_{review_target_sha256[:12]}.json"
    atomic_json(review_path, entry["reviews"][args.role])
    if args.decision == "REVISE":
        entry["status"] = "in_progress"
    elif all(
        entry["reviews"].get(role, {}).get("decision") == "PASS"
        and entry["reviews"].get(role, {}).get("review_target_sha256") == review_target_sha256
        for role in entry["required_reviewers"]
    ):
        entry["status"] = "user_review"
    atomic_json(project / "project_state.json", state)
    print(f"已记录 {args.role} {args.decision}; status={entry['status']}")


def cmd_approve(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    entry = state["stages"][args.stage]
    if entry["status"] != "user_review":
        raise ContractError(f"只有user_review阶段可由用户确认，当前为{entry['status']}")
    review_target_sha256 = verify_review_target(project, entry)
    for role in entry["required_reviewers"]:
        review = entry["reviews"].get(role, {})
        if review.get("decision") != "PASS" or review.get("review_target_sha256") != review_target_sha256:
            raise ContractError(f"缺少绑定当前hash的{role} PASS")
    entry["user_approval"] = {
        "status": "APPROVED",
        "artifact_sha256": entry["artifact_sha256"],
        "review_target_sha256": review_target_sha256,
        "approved_at": now(),
    }
    entry["status"] = "locked"
    entry["locked_at"] = now()
    state["current_stage"] = next_current_stage(state)
    atomic_json(project / "project_state.json", state)
    print(f"用户已确认并锁定 {args.stage}")


def cmd_render(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    guide_full = validate_artifact(project, state, S03)
    baseline = load_json(artifact_path(project, S01))
    requirement = load_json(project / "requirement.json")
    source_hash = sha256(artifact_path(project, S03))
    render_input = project_render_input(guide_full, baseline, requirement, source_hash)
    atomic_json(artifact_path(project, S04), render_input)
    submit_stage(project, state, S04)


def validate_project(project: Path, requested_stage: str | None = None) -> list[str]:
    requirement, state = load_project(project)
    messages = [f"project={state['project_name']}"]
    stages = [requested_stage] if requested_stage else [s for s in ARTIFACTS]
    for stage_id in stages:
        entry = state["stages"][stage_id]
        path = artifact_path(project, stage_id)
        should_exist = requested_stage is not None or entry["status"] in {"internal_review", "user_review", "locked"}
        if should_exist:
            validate_artifact(project, state, stage_id)
            messages.append(f"{stage_id}: artifact PASS")
        if entry["status"] in {"internal_review", "user_review", "locked"}:
            review_target_sha256 = verify_review_target(project, entry)
        if entry["status"] == "locked":
            approval = entry.get("user_approval") or {}
            if approval.get("review_target_sha256") != review_target_sha256:
                raise ContractError(f"锁定阶段缺少匹配hash的用户确认: {stage_id}")
    return messages


def cmd_validate(args: argparse.Namespace) -> None:
    for message in validate_project(Path(args.project).resolve(), args.stage):
        print(message)
    print("VALIDATION PASSED")


def cmd_release(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    entry = state["stages"][S04]
    if entry["status"] != "locked":
        raise ContractError("阶段04未锁定，禁止发布")
    review_target_sha256 = verify_review_target(project, entry)
    approval = entry.get("user_approval") or {}
    if approval.get("review_target_sha256") != review_target_sha256:
        raise ContractError("用户确认未绑定当前候选交付包")
    for role in entry["required_reviewers"]:
        review = entry["reviews"].get(role, {})
        if review.get("decision") != "PASS" or review.get("review_target_sha256") != review_target_sha256:
            raise ContractError(f"正式发布缺少{role}对当前候选交付包的PASS")
    candidate_manifest = load_json(project / entry["review_bundle"])
    deliverables = project / "deliverables"
    if deliverables.exists():
        shutil.rmtree(deliverables)
    deliverables.mkdir(parents=True, exist_ok=True)
    released: list[dict[str, str]] = []
    for item in candidate_manifest["files"]:
        source = project / item["candidate_path"]
        target = deliverables / item["release_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        temp = target.with_suffix(target.suffix + ".tmp")
        shutil.copy2(source, temp)
        os.replace(temp, target)
        released.append({"path": item["release_path"], "sha256": sha256(target)})
    quality = {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "source_sha256": entry["artifact_sha256"],
        "review_bundle_sha256": review_target_sha256,
        "required_reviewers": entry["required_reviewers"],
        "checks": ["scope", "schema", "referential_integrity", "candidate_file_set", "architect_review_hash", "business_expert_review_hash", "user_approval_hash", "html_docx_same_source"],
        "generated_at": now(),
    }
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "release_status": "PASS",
        "review_bundle_sha256": review_target_sha256,
        "review_phases": [
            {"phase": "internal_review", "required": ["architect", "business_expert"]},
            {"phase": "user_review", "required": ["user"]},
        ],
        "artifacts": released,
        "released_at": now(),
    }
    atomic_json(deliverables / "quality_report.json", quality)
    atomic_json(deliverables / "release_manifest.json", manifest)
    print(f"已发布正式交付包: {deliverables}")


def cmd_log_run(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    _, state = load_project(project)
    state["runs"].append({
        "stage_id": args.stage,
        "role": args.role,
        "model": args.model,
        "task": args.task,
        "recorded_at": now(),
    })
    atomic_json(project / "project_state.json", state)
    print("已记录模型路由")


# ── CLI ─────────────────────────────────────────────────────────────────

def parser() -> argparse.ArgumentParser:
    parse = argparse.ArgumentParser(prog="ig_runtime")
    sub = parse.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("project")
    init.add_argument("--name", required=True)
    init.add_argument("--client", required=True)
    init.add_argument("--industry", required=True)
    init.add_argument("--theme", required=True)

    start = sub.add_parser("start")
    start.add_argument("project")
    start.add_argument("--stage", required=True, choices=list(ARTIFACTS))

    submit = sub.add_parser("submit")
    submit.add_argument("project")
    submit.add_argument("--stage", required=True, choices=list(ARTIFACTS))

    review = sub.add_parser("review")
    review.add_argument("project")
    review.add_argument("--stage", required=True, choices=list(ARTIFACTS))
    review.add_argument("--role", required=True, choices=REVIEWERS)
    review.add_argument("--decision", required=True, choices=["PASS", "REVISE"])
    review.add_argument("--notes", default="")
    review.add_argument("--issues-file", help="阶段03逐题意见JSON，含issues数组")

    approve = sub.add_parser("approve")
    approve.add_argument("project")
    approve.add_argument("--stage", required=True, choices=list(ARTIFACTS))

    render = sub.add_parser("render")
    render.add_argument("project")

    release = sub.add_parser("release")
    release.add_argument("project")

    validate = sub.add_parser("validate")
    validate.add_argument("project")
    validate.add_argument("--stage", choices=list(ARTIFACTS))

    log = sub.add_parser("log-run")
    log.add_argument("project")
    log.add_argument("--stage", required=True)
    log.add_argument("--role", required=True)
    log.add_argument("--model", required=True)
    log.add_argument("--task", required=True)

    return parse


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "init":
            cmd_init(args)
        elif args.command == "start":
            cmd_start(args)
        elif args.command == "submit":
            cmd_submit(args)
        elif args.command == "review":
            cmd_review(args)
        elif args.command == "approve":
            cmd_approve(args)
        elif args.command == "render":
            cmd_render(args)
        elif args.command == "release":
            cmd_release(args)
        elif args.command == "validate":
            cmd_validate(args)
        elif args.command == "log-run":
            cmd_log_run(args)
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
