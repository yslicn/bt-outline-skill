#!/usr/bin/env python3
"""Quick validation: JSON Schema well-formedness, py_compile, frontmatter, unittest."""
import json
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent


def check_schemas() -> bool:
    ok = True
    for schema in sorted((SKILL / "schemas").glob("*.schema.json")):
        try:
            json.loads(schema.read_text(encoding="utf-8"))
            print(f"OK schema {schema.name}")
        except Exception as exc:
            print(f"FAIL schema {schema.name}: {exc}")
            ok = False
    return ok


def check_py() -> bool:
    import py_compile
    ok = True
    for script in sorted((SKILL / "scripts").glob("*.py")) + sorted((SKILL / "tests").glob("*.py")):
        try:
            py_compile.compile(str(script), doraise=True)
            print(f"OK py {script.name}")
        except Exception as exc:
            print(f"FAIL py {script.name}: {exc}")
            ok = False
    return ok


def check_skill_md() -> bool:
    path = SKILL / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    checks = {
        "frontmatter-name": "name:" in text,
        "frontmatter-desc": "description:" in text,
        "红线": "红线" in text,
        "流程表": "不可改变的咨询流程" in text,
        "阶段引用": "汇编渲染发布" in text,
        "运行协议": "阶段运行协议" in text,
    }
    ok = True
    for name, passed in checks.items():
        print(f"{'OK' if passed else 'FAIL'} skillmd {name}")
        ok = ok and passed
    return ok


def main() -> int:
    results = [check_schemas(), check_py(), check_skill_md()]
    if all(results):
        print("QUICK VALIDATE PASSED")
        return 0
    print("QUICK VALIDATE FAILED")
    return 1


if __name__ == "__main__":
    sys.exit(main())
