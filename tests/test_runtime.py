#!/usr/bin/env python3
"""End-to-end tests for the generate-bt-outline runtime (real CLI subprocess)."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
RUNTIME = SKILL / "scripts" / "ig_runtime.py"

STAGES = ["stage_01_input_baseline", "stage_02_interview_planning", "stage_03_interview_drafting"]


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["python3", str(RUNTIME), *args], capture_output=True, text=True, cwd=cwd)


class BTOutlineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="gbt-test-")
        self.ws = Path(self._tmp) / "proj"
        result = run("init", str(self.ws), "--name", "测试项目", "--client", "测试客户", "--industry", "汽车", "--theme", "营销服流程变革")
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    # ── fixture builders ────────────────────────────────────────────────

    def write_json(self, rel: str, data: dict) -> None:
        p = self.ws / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def load_json(self, rel: str) -> dict:
        return json.loads((self.ws / rel).read_text(encoding="utf-8"))

    def baseline(self) -> dict:
        return {
            "schema_version": "1.0", "stage_id": "stage_01_input_baseline", "project_name": "测试项目",
            "value_streams": [
                {"id": "vs1", "name": "品牌信任构建", "short_name": "品牌信任"},
                {"id": "vs2", "name": "产品上市", "short_name": "产品上市"},
                {"id": "vs3", "name": "客户触达", "short_name": "客户触达"},
                {"id": "vs4", "name": "交易转化", "short_name": "交易转化"},
            ],
            "capability_model": {"root": {"id": "root", "name": "营销服能力"}, "layers": [
                {"attribute": "战略", "l2_groups": [{"id": "l2-01", "name": "品牌战略", "l3": [{"id": "l3-011", "name": "品牌定位"}]}]},
                {"attribute": "核心", "l2_groups": [
                    {"id": "l2-02", "name": "GTM", "l3": [{"id": "l3-021", "name": "GTM策略"}]},
                    {"id": "l2-03", "name": "媒介投放", "l3": [{"id": "l3-031", "name": "投放管理"}]},
                    {"id": "l2-04", "name": "线索管理", "l3": [{"id": "l3-041", "name": "获取"}, {"id": "l3-042", "name": "分配"}, {"id": "l3-043", "name": "质量"}, {"id": "l3-044", "name": "分析"}]},
                ]},
            ]},
            "stakeholders": [
                {"id": "sh-01", "name": "集团高管", "type": "集团层", "role": "决策"},
                {"id": "sh-02", "name": "产品团队", "type": "团队层", "role": "GTM"},
                {"id": "sh-03", "name": "投放团队", "type": "团队层", "role": "投放"},
            ],
            "strategic_tensions": [
                {"id": "st-1", "statement": "品牌认知断层", "source_ref": "strategy#c2"},
                {"id": "st-2", "statement": "GTM与运营未分离", "source_ref": "strategy#c3"},
                {"id": "st-3", "statement": "线索漏斗断裂", "source_ref": "strategy#c4"},
            ],
            "scope_boundaries": [], "data_gaps": [],
        }

    def plan(self) -> dict:
        return {
            "schema_version": "1.0", "stage_id": "stage_02_interview_planning", "project_name": "测试项目",
            "split_logic": {"criteria": "项目制vs运营制", "rationale": "GTM项目制、投放运营制，边界互斥合并无遗漏"},
            "interviews": [
                {"id": "iv-1", "num": "01", "title": "品牌战略", "interview_direction": "品牌定位", "expected_information": ["品牌定位"], "value_stream_ids": ["vs1"], "l2_capability_ids": ["l2-01"], "stakeholder_role_ids": ["sh-01"]},
                {"id": "iv-2", "num": "02", "title": "GTM上市", "interview_direction": "上市能力", "expected_information": ["GTM"], "value_stream_ids": ["vs2"], "l2_capability_ids": ["l2-02"], "stakeholder_role_ids": ["sh-02"]},
                {"id": "iv-3", "num": "03", "title": "媒介线索", "interview_direction": "投放与线索", "expected_information": ["投放", "线索"], "value_stream_ids": ["vs3", "vs4"], "l2_capability_ids": ["l2-03", "l2-04"], "stakeholder_role_ids": ["sh-03"]},
            ],
            "coverage": {"vs_coverage": ["vs1", "vs2", "vs3", "vs4"], "capability_coverage": ["l2-01", "l2-02", "l2-03", "l2-04"], "stakeholder_coverage": ["sh-01", "sh-02", "sh-03"], "documented_exclusions": [], "gaps": []},
        }

    def _q(self, text: str, ptype: str = "追问", vs=None, caps=None) -> dict:
        return {"text": text, "probes": [{"type": ptype, "text": "为什么？"}], "vs_refs": vs or [], "capability_refs": caps or []}

    def guide_full(self) -> dict:
        def phase(n, name, layer, title, desc, blocks=None, questions=None):
            return {"phase_no": n, "name": name, "layer_type": layer, "title": title, "description": desc, "blocks": blocks, "questions": questions}

        guides = [
            {"id": "iv-1", "num": "01", "title": "品牌战略", "target_audience": "集团高管", "duration": "90 分钟",
             "meta": {"objectives": "品牌定位", "capability_coverage_summary": "品牌战略（1项L3）"},
             "phases": [
                 phase(1, "暖场破冰", "intro", "组织", "破冰", questions=[self._q("介绍团队？", vs=["vs1"], caps=["l2-01"])]),
                 phase(2, "业务全景", "panorama", "品牌全貌", "全景", blocks=[{"area_num": 1, "area_title": "品牌定位", "capability_ref": {"l2_id": "l2-01", "l2_name": "品牌战略", "l3_names": ["品牌定位"]}, "questions": [self._q("品牌定位？", vs=["vs1"], caps=["l2-01"])]}]),
                 phase(3, "流程深挖", "deepdive", "战略流程", "深挖", blocks=[{"area_num": 1, "area_title": "战略制定", "capability_ref": {"l2_id": "l2-01", "l2_name": "品牌战略", "l3_count": 1}, "questions": [self._q("决策顺序？", vs=["vs1", "vs2"], caps=["l2-01", "l2-02"])]}]),
                 phase(4, "痛点唤醒", "awaken", "挑战", "唤醒", questions=[self._q("品牌认知低是否获客难？", ptype="引导思考", vs=["vs1"], caps=["l2-01"])]),
                 phase(5, "变革期望", "expectation", "诉求", "期望", questions=[self._q("最想改变什么？", vs=["vs1"], caps=["l2-01"])]),
             ], "expected_output": ["品牌定位确认"]},
            {"id": "iv-2", "num": "02", "title": "GTM上市", "target_audience": "产品团队", "duration": "90 分钟",
             "meta": {"objectives": "GTM", "capability_coverage_summary": "GTM（1项L3）"},
             "phases": [
                 phase(1, "暖场破冰", "intro", "组织", "破冰", questions=[self._q("GTM团队？", vs=["vs2"], caps=["l2-02"])]),
                 phase(2, "业务全景", "panorama", "GTM全貌", "全景", blocks=[{"area_num": 1, "area_title": "GTM策略", "capability_ref": {"l2_id": "l2-02", "l2_name": "GTM", "l3_names": ["GTM策略"]}, "questions": [self._q("GTM流程？", vs=["vs2"], caps=["l2-02"])]}]),
                 phase(3, "流程深挖", "deepdive", "上市细节", "深挖", blocks=[{"area_num": 1, "area_title": "上市协同", "capability_ref": {"l2_id": "l2-02", "l2_name": "GTM", "l3_count": 1}, "questions": [self._q("上市节奏？", vs=["vs2"], caps=["l2-02"])]}]),
                 phase(4, "痛点唤醒", "awaken", "挑战", "唤醒", questions=[self._q("脉冲与日常协同？", ptype="引导思考", vs=["vs2"], caps=["l2-02"])]),
                 phase(5, "变革期望", "expectation", "诉求", "期望", questions=[self._q("升级什么？", vs=["vs2"], caps=["l2-02"])]),
             ], "expected_output": ["GTM流程现状"]},
            {"id": "iv-3", "num": "03", "title": "媒介线索", "target_audience": "投放团队", "duration": "90 分钟",
             "meta": {"objectives": "投放线索", "capability_coverage_summary": "媒介投放（1项L3）· 线索管理（4项L3）"},
             "phases": [
                 phase(1, "暖场破冰", "intro", "组织", "破冰", questions=[self._q("是否同一团队？", vs=["vs3"], caps=["l2-03"])]),
                 phase(2, "业务全景", "panorama", "投放线索全貌", "全景", blocks=[
                     {"area_num": 1, "area_title": "投放", "capability_ref": {"l2_id": "l2-03", "l2_name": "媒介投放", "l3_names": ["投放管理"]}, "questions": [self._q("投放策略？", vs=["vs3"], caps=["l2-03"])]},
                     {"area_num": 2, "area_title": "线索", "capability_ref": {"l2_id": "l2-04", "l2_name": "线索管理", "l3_count": 4}, "questions": [self._q("线索链路？", vs=["vs3", "vs4"], caps=["l2-04"])]},
                 ]),
                 phase(3, "流程深挖", "deepdive", "转化细节", "深挖", blocks=[{"area_num": 1, "area_title": "转化", "capability_ref": {"l2_id": "l2-04", "l2_name": "线索管理", "l3_count": 4}, "questions": [self._q("首次跟进时长？", vs=["vs3", "vs4"], caps=["l2-04"])]}]),
                 phase(4, "痛点唤醒", "awaken", "挑战", "唤醒", questions=[self._q("CPL水平？", ptype="引导思考", vs=["vs3", "vs4"], caps=["l2-03", "l2-04"])]),
                 phase(5, "变革期望", "expectation", "诉求", "期望", questions=[self._q("升级什么？", vs=["vs3", "vs4"], caps=["l2-03", "l2-04"])]),
             ], "expected_output": ["投放全景", "线索链路"]},
        ]
        return {"schema_version": "1.0", "stage_id": "stage_03_interview_drafting", "project_name": "测试项目", "plan_ref": {"plan_path": "x", "plan_sha256": "x"}, "guides": guides}

    def pass_stage(self, stage: str) -> None:
        self.assertEqual(run("start", str(self.ws), "--stage", stage).returncode, 0)
        self.assertEqual(run("submit", str(self.ws), "--stage", stage).returncode, 0)
        for role in ("architect", "business_expert"):
            r = run("review", str(self.ws), "--stage", stage, "--role", role, "--decision", "PASS")
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(run("approve", str(self.ws), "--stage", stage).returncode, 0)

    def build_stages_01_03(self) -> None:
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.write_json("stage_02_interview_planning/output/interview_plan.json", self.plan())
        self.write_json("stage_03_interview_drafting/output/interview_guide_full.json", self.guide_full())
        for stage in STAGES:
            self.pass_stage(stage)


class TestFullFlow(BTOutlineTestCase):
    def test_full_flow_happy_path(self) -> None:
        self.build_stages_01_03()
        self.assertEqual(run("render", str(self.ws)).returncode, 0)
        for role in ("architect", "business_expert"):
            r = run("review", str(self.ws), "--stage", "stage_04_rendering_release", "--role", role, "--decision", "PASS")
            self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(run("approve", str(self.ws), "--stage", "stage_04_rendering_release").returncode, 0)
        self.assertEqual(run("release", str(self.ws)).returncode, 0)
        self.assertEqual(run("validate", str(self.ws)).returncode, 0)
        dl = self.ws / "deliverables"
        for name in ("index.html", "index.docx", "shared-style.css", "render_input.json", "01_品牌战略.html", "01_品牌战略.docx", "03_媒介线索.html", "03_媒介线索.docx", "quality_report.json", "release_manifest.json"):
            self.assertTrue((dl / name).exists(), name)

    def test_missing_materials_blocked(self) -> None:
        req = self.load_json("requirement.json")
        req["scope_confirmed"] = False
        self.write_json("requirement.json", req)
        r = run("validate", str(self.ws))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("尚未由用户确认", r.stderr)


class TestGates(BTOutlineTestCase):
    def test_stage_gate_order(self) -> None:
        # 未锁定上游直接 submit 阶段03
        r = run("submit", str(self.ws), "--stage", "stage_03_interview_drafting")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("上游尚未锁定", r.stderr)

    def test_hash_change_forces_re_review(self) -> None:
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.assertEqual(run("start", str(self.ws), "--stage", "stage_01_input_baseline").returncode, 0)
        self.assertEqual(run("submit", str(self.ws), "--stage", "stage_01_input_baseline").returncode, 0)
        # 双评审 PASS 进入 user_review
        for role in ("architect", "business_expert"):
            self.assertEqual(run("review", str(self.ws), "--stage", "stage_01_input_baseline", "--role", role, "--decision", "PASS").returncode, 0)
        # 评审后改 artifact → approve 必须拒绝
        data = self.load_json("stage_01_input_baseline/output/input_baseline.json")
        data["strategic_tensions"][0]["statement"] = "被改动"
        self.write_json("stage_01_input_baseline/output/input_baseline.json", data)
        r = run("approve", str(self.ws), "--stage", "stage_01_input_baseline")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("已变化，必须重新submit", r.stderr)

    def test_coverage_gate(self) -> None:
        plan = self.plan()
        plan["coverage"]["vs_coverage"] = ["vs1", "vs2", "vs3"]  # 缺 vs4 且未排除
        self.write_json("stage_02_interview_planning/output/interview_plan.json", plan)
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.pass_stage("stage_01_input_baseline")
        r = run("submit", str(self.ws), "--stage", "stage_02_interview_planning")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("覆盖遗漏价值流", r.stderr)

    def test_five_layer_structure_required(self) -> None:
        gf = self.guide_full()
        gf["guides"][0]["phases"].pop()  # 缺 P5
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.write_json("stage_02_interview_planning/output/interview_plan.json", self.plan())
        self.write_json("stage_03_interview_drafting/output/interview_guide_full.json", gf)
        self.pass_stage("stage_01_input_baseline")
        self.pass_stage("stage_02_interview_planning")
        r = run("submit", str(self.ws), "--stage", "stage_03_interview_drafting")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("P1-P5", r.stderr)

    def test_p4_probe_word_gate(self) -> None:
        gf = self.guide_full()
        gf["guides"][0]["phases"][3]["questions"][0]["probes"][0]["type"] = "追问"
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.write_json("stage_02_interview_planning/output/interview_plan.json", self.plan())
        self.write_json("stage_03_interview_drafting/output/interview_guide_full.json", gf)
        self.pass_stage("stage_01_input_baseline")
        self.pass_stage("stage_02_interview_planning")
        r = run("submit", str(self.ws), "--stage", "stage_03_interview_drafting")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("引导词不符", r.stderr)

    def test_capability_ref_integrity(self) -> None:
        gf = self.guide_full()
        gf["guides"][0]["phases"][0]["questions"][0]["capability_refs"] = ["l2-999"]
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.write_json("stage_02_interview_planning/output/interview_plan.json", self.plan())
        self.write_json("stage_03_interview_drafting/output/interview_guide_full.json", gf)
        self.pass_stage("stage_01_input_baseline")
        self.pass_stage("stage_02_interview_planning")
        r = run("submit", str(self.ws), "--stage", "stage_03_interview_drafting")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("引用不存在的L2/L3", r.stderr)

    def test_plan_iteration_gate(self) -> None:
        # M1 7→9 场景：方向门 REVISE 后必须重审
        self.write_json("stage_01_input_baseline/output/input_baseline.json", self.baseline())
        self.pass_stage("stage_01_input_baseline")
        plan = self.plan()
        self.write_json("stage_02_interview_planning/output/interview_plan.json", plan)
        self.assertEqual(run("start", str(self.ws), "--stage", "stage_02_interview_planning").returncode, 0)
        self.assertEqual(run("submit", str(self.ws), "--stage", "stage_02_interview_planning").returncode, 0)
        # architect 先 PASS，业务专家 REVISE（模拟用户方向门拒绝）
        r = run("review", str(self.ws), "--stage", "stage_02_interview_planning", "--role", "architect", "--decision", "PASS")
        self.assertEqual(r.returncode, 0)
        r = run("review", str(self.ws), "--stage", "stage_02_interview_planning", "--role", "business_expert", "--decision", "REVISE", "--notes", "需按项目制/运营制拆分")
        self.assertEqual(r.returncode, 0)
        state = self.load_json("project_state.json")
        self.assertEqual(state["stages"]["stage_02_interview_planning"]["status"], "in_progress")
        # 修订后重提（加一份）并重审
        plan = self.plan()
        plan["interviews"].append({"id": "iv-4", "num": "04", "title": "品牌传播", "interview_direction": "内容", "expected_information": ["内容"], "value_stream_ids": ["vs1"], "l2_capability_ids": ["l2-01"], "stakeholder_role_ids": ["sh-01"]})
        self.write_json("stage_02_interview_planning/output/interview_plan.json", plan)
        self.assertEqual(run("submit", str(self.ws), "--stage", "stage_02_interview_planning").returncode, 0)
        # 旧的 PASS 已随 re-submit 清空，必须重审
        state = self.load_json("project_state.json")
        self.assertEqual(state["stages"]["stage_02_interview_planning"]["reviews"], {})
        for role in ("architect", "business_expert"):
            self.assertEqual(run("review", str(self.ws), "--stage", "stage_02_interview_planning", "--role", role, "--decision", "PASS").returncode, 0)
        self.assertEqual(run("approve", str(self.ws), "--stage", "stage_02_interview_planning").returncode, 0)

    def test_render_bundle_tamper(self) -> None:
        self.build_stages_01_03()
        self.assertEqual(run("render", str(self.ws)).returncode, 0)
        # 双评审 PASS 进入 user_review
        for role in ("architect", "business_expert"):
            self.assertEqual(run("review", str(self.ws), "--stage", "stage_04_rendering_release", "--role", role, "--decision", "PASS").returncode, 0)
        # 篡改候选 html → approve 必须拒绝
        p = self.ws / "stage_04_rendering_release/output/candidate/index.html"
        p.write_text(p.read_text(encoding="utf-8") + "\n<!-- tamper -->", encoding="utf-8")
        r = run("approve", str(self.ws), "--stage", "stage_04_rendering_release")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("候选交付件已变化", r.stderr)


if __name__ == "__main__":
    unittest.main()
