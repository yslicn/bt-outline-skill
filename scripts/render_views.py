"""Audience projections of the same render_input; never mutate its source."""
from __future__ import annotations

import copy
from typing import Any

WHEN_LABELS = {"always": "按需", "confirmed": "前提确认后", "denied": "前提否定后", "unknown": "尚不清楚时"}


def probe_text(probe: dict[str, Any]) -> str:
    label = f'{probe["type"]}：'
    text = probe["text"] if probe["text"].startswith(label) else label + probe["text"]
    if probe.get("when"):
        text = f'[{WHEN_LABELS[probe["when"]]}{": " + probe["condition"] if probe.get("condition") else ""}] ' + text
    return text


def prepare_view(source: dict[str, Any], audience: str) -> dict[str, Any]:
    if audience not in {"client", "interviewer"}:
        raise ValueError(f"Unknown audience: {audience}")
    ri = copy.deepcopy(source)
    ri["audience"] = audience
    if audience == "interviewer":
        return ri
    ri["cover"]["meta_lines"] = [f'版本 {ri["meta"]["version"]} | {ri["meta"]["date_text"]} | 访谈提纲']
    ri["cover"]["subtitle"] = f'{ri["meta"]["transformation_theme"]} — {len(ri["guides"])}场专题访谈'
    ri["background"] = [f'本项目围绕{ri["meta"]["transformation_theme"]}，了解业务现状、有效做法、挑战与机会，以及保留和改进期望。']
    ri["methodology"]["capability_alignment"] = "按业务主题组织问题，了解实际做法；没有问题、不适用和暂不调整均为有效信息。"
    ri["vs_mapping_matrix"]["vs_codes"] = ri["vs_mapping_matrix"]["vs_short_names"]
    for item in ri["toc"]:
        item["scope_line"] = item["title"]
    for guide in ri["guides"]:
        guide["vs_tags"] = []
        guide["layer_tag"] = ""
        guide["meta"]["capability_coverage_summary"] = ""
        for phase in guide["phases"]:
            for block in phase.get("blocks") or []:
                block.pop("capability_ref", None)
            questions = (phase.get("questions") or []) + [q for b in phase.get("blocks") or [] for q in b.get("questions", [])]
            for question in questions:
                question["probes"] = []
                question.pop("interviewer_context", None)
    return ri
