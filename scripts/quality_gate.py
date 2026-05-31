#!/usr/bin/env python3
"""
质量门禁脚本。

用法：
  quality_gate.py <skill目录路径> [--config gate.json]

检查 skill 是否满足通过条件。返回 exit code 0=通过, 1=不通过。

默认门禁条件（可通过 --config 自定义）：
  - SKILL.md ≤ 200 行
  - 每个 step 文件有 checklist
  - 总分 ≥ 80
  - 无严重问题
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# 复用 analyze_skill 的分析逻辑
from analyze_skill import analyze_skill


DEFAULT_GATE = {
    "max_skill_md_lines": 200,
    "min_score": 80,
    "max_critical_issues": 0,
    "max_high_issues": 2,
    "require_step_checklists": True,
    "require_frontmatter": True,
}


def load_gate_config(config_path: str | None) -> dict:
    """加载门禁配置。"""
    if config_path and os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_GATE


def check_gate(skill_dir: str, gate: dict, content_score: int | None = None) -> dict:
    """检查是否满足门禁条件。

    Args:
        content_score: LLM 内容评估分数（满分 30）。如果提供，门禁检查合并分数。
    """
    result = analyze_skill(skill_dir)
    checks = []
    passed = True

    # 检查 SKILL.md 行数
    skill_md = Path(skill_dir) / "SKILL.md"
    if skill_md.exists():
        line_count = len(skill_md.read_text(encoding="utf-8").split("\n"))
        max_lines = gate.get("max_skill_md_lines", 200)
        check_passed = line_count <= max_lines
        checks.append({
            "name": "SKILL.md 行数",
            "condition": f"≤ {max_lines}",
            "actual": line_count,
            "passed": check_passed,
        })
        if not check_passed:
            passed = False

    # 计算总分：结构分（脚本满分100→映射到70）+ 内容分（满分30）
    raw_score = result["score"]
    structure_score = round(raw_score * 0.7)  # 映射到 70 分制
    if content_score is not None:
        total_score = structure_score + content_score
        score_label = f"{total_score}/100（结构{structure_score}/70+内容{content_score}/30，原始{raw_score}）"
    else:
        total_score = structure_score
        score_label = f"{total_score}/70（仅结构分，原始{raw_score}）"

    # 检查总分
    min_score = gate.get("min_score", 80)
    score_passed = total_score >= min_score
    checks.append({
        "name": "总分",
        "condition": f"≥ {min_score}",
        "actual": score_label,
        "passed": score_passed,
    })
    if not score_passed:
        passed = False

    # 检查严重问题数
    max_critical = gate.get("max_critical_issues", 0)
    critical_count = sum(1 for i in result["issues"] if i["severity"] == "critical")
    critical_passed = critical_count <= max_critical
    checks.append({
        "name": "严重问题数",
        "condition": f"≤ {max_critical}",
        "actual": critical_count,
        "passed": critical_passed,
    })
    if not critical_passed:
        passed = False

    # 检查高危问题数
    max_high = gate.get("max_high_issues", 2)
    high_count = sum(1 for i in result["issues"] if i["severity"] == "high")
    high_passed = high_count <= max_high
    checks.append({
        "name": "高危问题数",
        "condition": f"≤ {max_high}",
        "actual": high_count,
        "passed": high_passed,
    })
    if not high_passed:
        passed = False

    # 检查 step 文件 checklist
    if gate.get("require_step_checklists", True):
        steps_dir = Path(skill_dir) / "steps"
        if steps_dir.exists():
            step_files = list(steps_dir.glob("step*.md"))
            missing = []
            for sf in step_files:
                content = sf.read_text(encoding="utf-8")
                if "- [ ]" not in content and "- [x]" not in content:
                    missing.append(sf.name)
            checklist_passed = len(missing) == 0
            checks.append({
                "name": "step 文件 checklist",
                "condition": "全部有",
                "actual": f"{len(missing)} 个缺失" if missing else "全部有",
                "passed": checklist_passed,
            })
            if not checklist_passed:
                passed = False

    return {"passed": passed, "score": total_score, "structure_score": structure_score, "checks": checks}


def format_report(gate_result: dict) -> str:
    """格式化门禁报告。"""
    lines = []

    if gate_result["passed"]:
        lines.append("门禁结果: 通过 [PASS]")
    else:
        lines.append("门禁结果: 不通过 [FAIL]")

    lines.append(f"总分: {gate_result['score']}/100")
    lines.append("")

    for check in gate_result["checks"]:
        status = "[PASS]" if check["passed"] else "[FAIL]"
        lines.append(f"  {status} {check['name']}: {check['actual']}（要求 {check['condition']}）")

    return "\n".join(lines)


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: quality_gate.py <skill目录路径> [--config gate.json] [--content-score N]")
        return 1

    skill_dir = sys.argv[1]
    config_path = None
    content_score = None

    if "--config" in sys.argv:
        idx = sys.argv.index("--config")
        if idx + 1 < len(sys.argv):
            config_path = sys.argv[idx + 1]

    if "--content-score" in sys.argv:
        idx = sys.argv.index("--content-score")
        if idx + 1 < len(sys.argv):
            content_score = int(sys.argv[idx + 1])

    if not os.path.isdir(skill_dir):
        print(f"[错误] 目录不存在: {skill_dir}")
        return 1

    gate = load_gate_config(config_path)
    result = check_gate(skill_dir, gate, content_score)
    print(format_report(result))

    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
