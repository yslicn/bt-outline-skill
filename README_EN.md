<div align="center">

# BT Outline

### Interview-Outline Generator for Business Transformation Projects

**Turns "interview outlines" from one-off handwritten drafts into a deterministic production line bound by 5 required inputs, dual independent review and a user sign-off gate.**

![Type](https://img.shields.io/badge/type-Claude%20Skill-0B6E4F?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Runtime](https://img.shields.io/badge/runtime-stdlib--only-1F2937?style=for-the-badge)
![Output](https://img.shields.io/badge/output-HTML%20%2B%20docx-1F3864?style=for-the-badge)
![License](https://img.shields.io/badge/license-Apache--2.0-555555?style=for-the-badge)

</div>

<p align="right">
  <a href="README.md">中文</a>
</p>

---

## ⚠️ Usage Scope and Restrictions

> **This skill is licensed on a "limited-purpose" basis: it may be used for exactly one thing — designing interview outlines for business transformation projects. Use outside that scope is unsupported and is not covered by its quality gates.**

### ✅ Permitted use

- **Interview outlines (information-gathering design) for business transformation projects**: structured interview questions for a set of interviewees in BC / process-transformation / digital-transformation engagements.
- Interview decomposition and question layering driven by a **value stream / business capability framework / stakeholder list**.
- Producing a candidate deliverable bundle of `index + N outlines` in both HTML and docx, for human review and client discussion.
- **Structural refactoring** of existing interview outlines (completing the five-layer progression, adding capability-domain mapping, closing coverage gaps).

### ❌ Prohibited use

This skill **only designs information gathering**. The following are things it does not do — and whose output would not be trustworthy — so its output must never be delivered as any of them:

| Prohibited use | Why |
|---|---|
| Process optimisation / target process design | No target-state modelling; it produces questions, not solutions |
| System architecture / IT blueprint / implementation roadmap | Outside the methodology; no quality gate covers it |
| Organisational design and role/responsibility design | Same |
| Business diagnosis, pain-point rating, maturity assessment | Degrades into "pick the conclusion, then fit the questions" — contradicts the red lines |
| KPI dictionaries / metric-system design | Same |
| Generic questionnaires, market-research surveys, employee-satisfaction surveys | Not the transformation-interview context; the five-layer progression and capability mapping do not apply |
| **Analysis** of stakeholder demands (as opposed to designing their capture) | Analysis belongs to downstream architecture work; this skill stops at capture |

### Preconditions

- Must be driven by a **consultant with a grounding in business-architecture methodology**: the decomposition logic (`methodology/interview_split_logic.md`) is the highest-priority rule, and misusing it produces grammatically correct, business-wrong outlines.
- All 5 required input materials must be present (any missing item must be explicitly logged as a `data gap`, never silently ignored).
- **The dual review and user sign-off gates must not be bypassed**, and candidate bundles that have not been `release`d must not be delivered externally.

---

## What It Is

BT Outline is a Claude Skill built for consulting delivery. It fixes a validated method for producing "business transformation interview outlines" into a deterministic process constrained by input materials, JSON Schemas, runtime gates, dual independent review and user sign-off.

It is not "let the model write something that looks like a professional questionnaire". What it controls is: which **evidence** the model asks questions from, **which gate** an outline must clear before moving on, who performs **independent review**, which paths a rework may touch, and how the final HTML and docx are deterministically generated from **a single JSON source of truth**.

## The Problem It Solves

Interview outlines are "fast to write, hard to write well". The real difficulty is never phrasing — it is decomposition logic and coverage completeness:

- Outlines degrade into "a few questions per department", with no mutually exclusive decomposition dimension, so interviews overlap or leave gaps;
- Questions stall at fact-confirmation and lack the "current state → pain points → expectations → constraints" progression, wasting an entire hour of interview time;
- Capability frameworks and value streams often merely get "pasted" onto outline titles, while the questions do not actually correspond to them;
- Rework rounds can silently alter already-locked content, making it impossible to prove "who judged what, based on which version";
- Questions that drift away from the input materials invent business facts and interviewees that do not exist.

Design principle: **the model makes the professional judgements, the Runtime enforces the invariants; reviewers raise counter-examples, the user makes the final call.**

## Workflow

### Start gate (before `init`)

The 5 input materials and the delivery format must be confirmed first; `init` is not permitted before that:

1. **Project background** (client / industry / transformation theme / scope)
2. **Strategy materials** (strategy report PDF/PPT/doc)
3. **Value stream list**
4. **Business capability framework** (e.g. TOGAF three-tier L1/L2/L3)
5. **Stakeholder list**

Plus the delivery format: **HTML + docx**. Anything missing must be explicitly logged as a `data gap`.

### Four stages (gate by gate, never merged)

| Stage | Lead role | Key confirmation |
|---|---|---|
| **01 Input baseline** | Architect | Information baseline: value streams / capability framework / stakeholders / core strategic tensions |
| **02 Planning** | Interview Drafter | N outlines + each one's direction + expected information (**direction gate, iterable via REVISE**) |
| **03 Drafting** | Interview Drafter | Full five-layer outline text + two-level capability mapping |
| **04 Compile, render and release** | Orchestrator + Python | `index` + N candidate HTML/docx bundles |

Every stage must complete the fixed sequence, none of it skippable:

```
design → machine validation → independent Architect review → independent business-expert review → user sign-off → hash lock
```

**Stages 02 and 03 must remain separate** — decomposition logic is the iterable direction gate, and the single step most worth aligning on early.

## Deliverables

Stage 04 compiles the official bundle deterministically from `render_input.json` (the single render source):

```text
deliverables/
├── render_input.json          # single render source for both HTML and docx
├── index.html                 # overview
├── NN_<title>.html            # N outlines
├── shared-style.css           # IBM Design System
├── index.docx                 # same source as the HTML
├── NN_<title>.docx
├── quality_report.json
└── release_manifest.json      # binds every file hash
```

**HTML and docx must share one source** (the same `render_input.json`) and must not be hand-written separately.

## Quick Start

Install (as a Claude Skill):

```bash
git clone https://github.com/yslicn/bt-outline-skill.git ~/.claude/skills/bt-outline-skill
```

Start a project:

```bash
python3 scripts/ig_runtime.py init <project_dir> \
  --name <project> --client <client> --industry <industry> --theme <theme>
```

Repeat the fixed sequence for every stage:

```bash
python3 scripts/ig_runtime.py start   <project_dir> --stage <stage_id>
python3 scripts/ig_runtime.py submit  <project_dir> --stage <stage_id>
python3 scripts/ig_runtime.py review  <project_dir> --stage <stage_id> --role architect       --decision PASS
python3 scripts/ig_runtime.py review  <project_dir> --stage <stage_id> --role business_expert --decision PASS
python3 scripts/ig_runtime.py approve <project_dir> --stage <stage_id>
```

Stage 04 only (render → dual review → sign-off → release):

```bash
python3 scripts/ig_runtime.py render  <project_dir>
python3 scripts/ig_runtime.py approve <project_dir> --stage stage_04_rendering_release
python3 scripts/ig_runtime.py release <project_dir>
```

Read-only validation:

```bash
python3 scripts/ig_runtime.py validate <project_dir>
```

Full command set and state transitions: `reference/runtime_commands.md`.

## Repository Layout

```text
SKILL.md                      # entry point: workflow, role routing, red lines
agents/                       # orchestrator / architect / interview_drafter / business_expert_reviewer
stages/                       # per-stage protocols, stage_00..stage_04
methodology/                  # five-layer progression, question layering, decomposition logic, capability alignment
schemas/                      # 6 JSON Schemas
reference/                    # artifact contract, model policy, rendering spec, command reference
scripts/                      # ig_runtime.py + quick_validate / render_html / render_docx
assets/shared-style.css       # HTML stylesheet (IBM Design System)
tests/                        # offline runtime and render tests
```

## Four Quality Gates

| Gate | What it checks |
|---|---|
| **Machine gate** | Schema, stable IDs, referential integrity, five-layer structure, lead-in phrasings, hash/MD consistency |
| **Architect gate** | Decomposition self-consistency (MECE), five-layer progression compliance, no capability-domain drift across the two-level mapping, complete coverage |
| **Business-expert gate** | Questions grounded in the business, industry realism, terminology, key omissions, sensitivity and compliance |
| **User gate** | Count, direction, trade-offs and client acceptance (the direction gate may iterate via REVISE) |

Outline count and question density are **diagnostic ranges**, not absolute cross-industry hard gates; structural completeness and referential consistency are the hard gates.

## Twelve Red Lines (Summary)

The complete list is in `SKILL.md`. The four most important:

1. **No `init` before the 5 inputs are confirmed** — missing materials must be logged as explicit `data gap`s.
2. **No self-review** — a producer may not review their own artifact; any review not bound to the current `SHA-256` is void.
3. **JSON is the single source of truth** — MD/HTML/docx may only be generated deterministically by the runtime; once the JSON changes, prior reviews lapse.
4. **No release without sign-off** — a candidate bundle that has not cleared dual PASS plus user sign-off may not be `release`d, nor delivered externally.

## Requirements

- Python **3.10+**
- Runtime and HTML rendering: **standard library only**
- docx rendering: `python-docx`

## Version

- **v1.0** (2026-08-10): first release. Four stages + start gate + same-source HTML/docx rendering + deterministic runtime.

## License

Code is licensed under the [Apache License 2.0](LICENSE).

Use is additionally constrained by [Usage Scope and Restrictions](#️-usage-scope-and-restrictions) above: this skill is limited to **designing interview outlines for business transformation projects**.

## v1.1 (2026-10-08)

Neutral information collection accepts effective existing practices, no issue, not applicable, unknown, and no change as valid outcomes. Strategic tensions may be empty. Use one spoken question and conditional probes; industry observations do not establish company facts. See `methodology/neutral_questioning.md`.

Client files hide internal mappings and probes; the same JSON renders interviewer files under `interviewer/`. New guides use `content_policy=neutral-v1`; existing schema_version=1.0 artifacts remain compatible. Stage 03 revisions use `review --issues-file` to track question IDs and before/after question content. Tests do not replace semantic review.

## v1.2 (2026-10-08)

Preserve business specificity alongside neutrality. Client documents show the complete question, public context, and open-ended answer_hints; terminology explanations, answer dimensions, and neutral discussion anchors are allowed. Internal hypotheses and conditional probes remain private. Revision after snapshots can be captured automatically. Fix the HTML CLI entry point and preserve actual value-stream IDs when numbering has gaps.
